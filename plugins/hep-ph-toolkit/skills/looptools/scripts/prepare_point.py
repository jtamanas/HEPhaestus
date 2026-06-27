"""
prepare_point.py — SLHA / param_card / runner-spec → numeric model point.

Produces an ordered, JSON-serialisable numeric substitution dict that the
Wolfram driver binds onto the symbolic FormCalc amplitude, plus the DM mass.

This module owns NO physics — it is a pure parameter-card reader.  The only
"interpretation" it performs is pulling the DM mass out of the SLHA MASS block
by PDG id and exposing the remaining numeric entries verbatim.

SLHA support is intentionally minimal: BLOCK <name> / "<idx...> <value> # comment"
lines.  Unknown / non-numeric lines are ignored.  DECAY blocks are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def parse_slha(text: str) -> dict:
    """Parse SLHA text into {block_name_upper: {(idx,...): value}}.

    Indices are a tuple of ints; value is a float.  Lines that are not
    parseable numeric entries are skipped.  DECAY blocks are skipped entirely
    (their header line carries a width, not an index/value pair we model here).
    """
    blocks: dict[str, dict] = {}
    current: Optional[str] = None
    in_decay = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        head = line.strip().upper()
        if head.startswith("BLOCK"):
            parts = line.split()
            current = parts[1].upper() if len(parts) > 1 else None
            in_decay = False
            if current is not None:
                blocks.setdefault(current, {})
            continue
        if head.startswith("DECAY"):
            current = None
            in_decay = True
            continue
        if current is None or in_decay:
            continue
        toks = line.split()
        # Last token is the value; preceding tokens are integer indices.
        try:
            value = float(toks[-1])
        except (ValueError, IndexError):
            continue
        idx_tokens = toks[:-1]
        try:
            idx = tuple(int(t) for t in idx_tokens)
        except ValueError:
            # Non-integer index tokens (e.g. a stray label) → skip.
            continue
        blocks[current][idx] = value
    return blocks


# 2HDM+a (TwoHdmAfix) PDG ids — match the hand-crafted SARAH fixture
# (plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md §4b).
DM_PDG_2HDMA = 9989932   # chi (Dirac DM)
MEDIATOR_PDG_2HDMA = 36  # a (CP-odd pseudoscalar mediator, lightest Ah)


def prepare_point(
    card_path: Path,
    dm_pdg: int = DM_PDG_2HDMA,
) -> dict:
    """Read an SLHA/param card and return an ordered numeric point dict.

    Returns
    -------
    dict with keys:
        m_dm_gev:   DM mass (float) read from MASS block by ``dm_pdg``.
        masses:     {pdg(int): mass(float)} from the MASS block.
        params:     {"<BLOCK>:<i,j,...>": value} flat ordered numeric map of
                    every non-MASS block entry, for the driver substitution.
        dm_pdg:     echo of the PDG id used.
    """
    card_path = Path(card_path)
    blocks = parse_slha(card_path.read_text())

    mass_block = blocks.get("MASS", {})
    masses = {pdg[0]: val for pdg, val in mass_block.items() if len(pdg) == 1}
    if dm_pdg not in masses:
        raise ValueError(
            f"DM PDG {dm_pdg} not found in MASS block of {card_path} "
            f"(have {sorted(masses)})"
        )

    params: dict[str, float] = {}
    for block_name in sorted(blocks):
        if block_name == "MASS":
            continue
        for idx, val in sorted(blocks[block_name].items()):
            key = f"{block_name}:" + ",".join(str(i) for i in idx)
            params[key] = val

    return {
        "m_dm_gev": masses[dm_pdg],
        "masses": {str(k): v for k, v in sorted(masses.items())},
        "params": params,
        "dm_pdg": dm_pdg,
    }


def canonical_point(point: dict) -> str:
    """Canonical JSON of a point (for cache-key hashing)."""
    return json.dumps(point, sort_keys=True, separators=(",", ":"))
