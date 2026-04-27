"""resolve_process.py — dual-syntax process parser for /feynarts generate.

Two forms:
  - Raw FeynArts tuple: auto-detected when process string starts with '['.
  - Alias form: human-readable labels resolved via tables/<builtin>.json or
    $STATE_ROOT/models/<name>/sarah/particles.m.

Returns a dict with:
  - raw: bool
  - n_in, n_out: int
  - feynarts_tuple: str (the FeynArts-ready tuple string)
  - processspec: dict conforming to processspec/v1 schema
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

# Particle data for known aliases (PDG code + mass symbol for processspec)
# Key: label, Value: (pdg, mass_symbol)
_PARTICLE_META: dict[str, tuple[int, str]] = {
    "e-": (11, "ME"),
    "e+": (-11, "ME"),
    "mu-": (13, "MMU"),
    "mu+": (-13, "MMU"),
    "tau-": (15, "MTAU"),
    "tau+": (-15, "MTAU"),
    "nu_e": (12, "0"),
    "anti-nu_e": (-12, "0"),
    "nu_mu": (14, "0"),
    "anti-nu_mu": (-14, "0"),
    "nu_tau": (16, "0"),
    "anti-nu_tau": (-16, "0"),
    "u": (2, "0"),
    "ubar": (-2, "0"),
    "c": (4, "MC"),
    "cbar": (-4, "MC"),
    "t": (6, "MT"),
    "tbar": (-6, "MT"),
    "d": (1, "0"),
    "dbar": (-1, "0"),
    "s": (3, "MS"),
    "sbar": (-3, "MS"),
    "b": (5, "MB"),
    "bbar": (-5, "MB"),
    "g": (21, "0"),
    "gluon": (21, "0"),
    "gamma": (22, "0"),
    "A": (22, "0"),
    "photon": (22, "0"),
    "Z": (23, "MZ"),
    "W+": (24, "MW"),
    "W-": (-24, "MW"),
    "H": (25, "MH"),
    "Higgs": (25, "MH"),
    "h": (25, "MH"),
    "A0": (36, "MA0"),
    "H+": (37, "MHC"),
    "H-": (-37, "MHC"),
}


class ProcessResolutionError(Exception):
    """Raised when process specification cannot be resolved."""

    def __init__(self, code: str, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def _load_table(model: str, tables_dir: Optional[Path] = None) -> dict[str, str]:
    """Load alias table for builtin model."""
    if tables_dir is None:
        tables_dir = Path(__file__).parent.parent / "tables"
    table_path = tables_dir / f"{model}.json"
    if not table_path.exists():
        raise ProcessResolutionError(
            "FEYNARTS_ABSENT",
            f"No alias table found for model '{model}' at {table_path}.",
            {"model": model, "table_path": str(table_path)},
        )
    with open(table_path) as f:
        raw = json.load(f)
    # Strip _comment and _schema keys
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _parse_alias_particles(process_str: str) -> tuple[list[str], list[str]]:
    """Parse 'p1 p2 -> p3 p4' into (in_labels, out_labels)."""
    if "->" not in process_str:
        raise ProcessResolutionError(
            "FEYNARTS_ABSENT",
            f"Process string '{process_str}' must contain '->'.",
        )
    lhs, rhs = process_str.split("->", 1)
    in_labels = lhs.strip().split()
    out_labels = rhs.strip().split()
    return in_labels, out_labels


def _resolve_alias(label: str, table: dict[str, str]) -> str:
    """Resolve one particle alias to a FeynArts tuple string."""
    if label in table:
        return table[label]
    raise ProcessResolutionError(
        "FEYNARTS_ABSENT",
        f"unknown particle: '{label}' not in alias table.",
        {"label": label},
    )


def _particle_entry(label: str) -> dict:
    """Build a processspec particle entry for a label."""
    pdg, mass_sym = _PARTICLE_META.get(label, (0, "M" + label.upper()))
    return {"label": label, "pdg": pdg, "mass_symbol": mass_sym}


def _build_processspec(
    in_labels: list[str],
    out_labels: list[str],
    loop_order: int = 0,
    excludes: Optional[list[str]] = None,
) -> dict:
    return {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [_particle_entry(l) for l in in_labels],
            "out": [_particle_entry(l) for l in out_labels],
        },
        "loop_order": loop_order,
        "kinematic_limit": "general",
        "excludes": sorted(excludes or []),
    }


def _build_tuple_str(in_tuples: list[str], out_tuples: list[str]) -> str:
    """Build a FeynArts-ready process specification string."""
    in_str = "{" + ", ".join(in_tuples) + "}"
    out_str = "{" + ", ".join(out_tuples) + "}"
    return f"{{{in_str}, {out_str}}}"


def resolve_process(
    process: str,
    model: str = "SM",
    tables_dir: Optional[Path] = None,
    loop_order: int = 0,
    excludes: Optional[list[str]] = None,
    state_root: Optional[str] = None,
) -> dict:
    """Resolve a process specification string.

    Args:
        process: Either raw form '[...]' or alias form 'e+ e- -> mu+ mu-'.
        model: Built-in model name (SM/SMQCD/THDM/MSSM) or SARAH model name.
        tables_dir: Override path to tables/ directory.
        loop_order: Loop order (0=tree, 1=one-loop, ...).
        excludes: List of topology classes to exclude.
        state_root: SARAH state root for SARAH-model particle lookups.

    Returns:
        dict with: raw, n_in, n_out, feynarts_tuple, processspec
    """
    process = process.strip()

    # Raw form: starts with '{'
    if process.startswith("{") or process.startswith("[{"):
        return {
            "raw": True,
            "n_in": _count_particles_in_raw(process, "in"),
            "n_out": _count_particles_in_raw(process, "out"),
            "feynarts_tuple": process,
            "processspec": _build_processspec([], [], loop_order, excludes),
        }

    # Alias form
    in_labels, out_labels = _parse_alias_particles(process)
    table = _load_table(model, tables_dir)

    in_tuples = [_resolve_alias(l, table) for l in in_labels]
    out_tuples = [_resolve_alias(l, table) for l in out_labels]

    tuple_str = _build_tuple_str(in_tuples, out_tuples)
    processspec = _build_processspec(in_labels, out_labels, loop_order, excludes)

    return {
        "raw": False,
        "n_in": len(in_labels),
        "n_out": len(out_labels),
        "feynarts_tuple": tuple_str,
        "processspec": processspec,
    }


def _count_particles_in_raw(process: str, direction: str) -> int:
    """Roughly count particles in a raw FeynArts tuple (best-effort for n_in/n_out)."""
    # Raw form: {{p1, p2}, {p3, p4}} or [{p1, p2}, {p3, p4}]
    # Strip outer brackets
    s = process.strip().lstrip("[{").rstrip("]}").strip()
    # Find the two groups separated by '}, {'
    # Simple heuristic: count F[/S[/V[/U[ tokens in each half
    # Split by '},' or '},' with spaces
    parts = re.split(r'\},\s*\{', s)
    if len(parts) < 2:
        return 1
    idx = 0 if direction == "in" else 1
    target = parts[idx] if idx < len(parts) else ""
    # Count particle entries (split by comma-separated items, each is a particle)
    # Count F[, S[, V[, U[ occurrences
    count = len(re.findall(r'[FSVU]\[', target))
    return max(1, count)
