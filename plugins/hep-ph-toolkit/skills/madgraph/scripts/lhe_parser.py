"""LHE (Les Houches Event) file parser.

Parse events from LHE XML files, extract cross-sections, and compute kinematics.
Library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import gzip
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def _open_lhe(path: str | Path):
    """Open an LHE file, handling .gz compression transparently."""
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt")
    return open(path, "r")


def parse_lhe(path: str | Path) -> list[dict]:
    """Parse events from an LHE XML file.

    Each event dict contains:
        - 'particles': list of particle dicts with keys:
            pdgid, status, mother1, mother2, color1, color2,
            px, py, pz, energy, mass, lifetime, spin
        - 'weight': event weight
        - 'scale': factorization scale
        - 'aqed': alpha_QED
        - 'aqcd': alpha_QCD

    Handles both plain .lhe and gzip-compressed .lhe.gz files.
    """
    with _open_lhe(path) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    events = []
    for event_elem in root.iter("event"):
        text = event_elem.text.strip()
        lines = [
            l.strip()
            for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        if not lines:
            continue

        header = lines[0].split()
        n_particles = int(header[0])
        event = {
            "weight": float(header[2]),
            "scale": float(header[3]),
            "aqed": float(header[4]),
            "aqcd": float(header[5]),
            "particles": [],
        }

        for i in range(1, min(n_particles + 1, len(lines))):
            parts = lines[i].split()
            if len(parts) < 13:
                continue
            event["particles"].append(
                {
                    "pdgid": int(parts[0]),
                    "status": int(parts[1]),
                    "mother1": int(parts[2]),
                    "mother2": int(parts[3]),
                    "color1": int(parts[4]),
                    "color2": int(parts[5]),
                    "px": float(parts[6]),
                    "py": float(parts[7]),
                    "pz": float(parts[8]),
                    "energy": float(parts[9]),
                    "mass": float(parts[10]),
                    "lifetime": float(parts[11]),
                    "spin": float(parts[12]),
                }
            )

        events.append(event)

    return events


def extract_cross_section(path: str | Path) -> tuple[float, float]:
    """Extract cross-section and error from the LHE <init> block.

    Returns:
        Tuple of (cross_section_pb, error_pb).
    """
    with _open_lhe(path) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    init_elem = root.find("init")
    if init_elem is None:
        raise ValueError(f"No <init> block found in {path}")

    text = init_elem.text.strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        raise ValueError(f"Malformed <init> block in {path}")

    # Second line: XSECUP XERRUP XMAXUP LPRUP
    parts = lines[1].split()
    return (float(parts[0]), float(parts[1]))


def event_kinematics(event: dict) -> dict:
    """Compute kinematic variables for final-state particles in an event.

    Returns dict with:
        - 'final_state': list of dicts with pdgid, pt, eta, phi, mass, rapidity
        - 'invariant_masses': dict of (i, j) -> m_ij for all final-state pairs
    """
    final = []
    for p in event["particles"]:
        if p["status"] != 1:
            continue

        px, py, pz, e = p["px"], p["py"], p["pz"], p["energy"]
        pt = math.sqrt(px**2 + py**2)

        p_mag = math.sqrt(px**2 + py**2 + pz**2)
        if p_mag > abs(pz):
            eta = 0.5 * math.log((p_mag + pz) / (p_mag - pz))
        else:
            eta = math.copysign(float("inf"), pz)

        phi = math.atan2(py, px)

        if e > abs(pz):
            rapidity = 0.5 * math.log((e + pz) / (e - pz))
        else:
            rapidity = math.copysign(float("inf"), pz)

        final.append(
            {
                "pdgid": p["pdgid"],
                "pt": pt,
                "eta": eta,
                "phi": phi,
                "mass": p["mass"],
                "rapidity": rapidity,
                "_4vec": (px, py, pz, e),
            }
        )

    inv_masses = {}
    for i in range(len(final)):
        for j in range(i + 1, len(final)):
            px = final[i]["_4vec"][0] + final[j]["_4vec"][0]
            py = final[i]["_4vec"][1] + final[j]["_4vec"][1]
            pz = final[i]["_4vec"][2] + final[j]["_4vec"][2]
            e = final[i]["_4vec"][3] + final[j]["_4vec"][3]
            m2 = e**2 - px**2 - py**2 - pz**2
            inv_masses[(i, j)] = math.sqrt(max(0.0, m2))

    for f in final:
        del f["_4vec"]

    return {"final_state": final, "invariant_masses": inv_masses}
