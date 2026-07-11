"""
slha_adapter.py — Parse SLHA2 files and extract HiggsBounds/HiggsSignals input data.

Required blocks:
- MASS: Higgs masses
- HMIX: mixing angles
- HiggsBoundsInputHiggsCouplingsFermions (preferred)
- HiggsBoundsInputHiggsCouplingsBosons (preferred)
- DECAY tables for neutral + charged Higgs

Falls back to legacy HiggsBounds block with a warning if the new-style blocks absent.
Fatal HIGGSTOOLS_SLHA_MISSING_BLOCKS if both absent.

v1 scope: CP-conserving scalar sectors only. CPV/complex mixing deferred to v1.1.
"""
from __future__ import annotations

import re
import sys
import warnings
from typing import Any

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


class SlhaMissingBlocksError(Exception):
    """Raised when required HiggsBounds input blocks are absent from the SLHA."""

    def __init__(self, message: str, user_instruction: str = ""):
        super().__init__(message)
        self.code = "HIGGSTOOLS_SLHA_MISSING_BLOCKS"
        self.message = message
        self.user_instruction = user_instruction


class SlhaMassBlockMissingError(Exception):
    """Raised when the MASS block is absent."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = "HIGGSTOOLS_SLHA_MISSING_BLOCKS"


def _parse_mass_block(text: str) -> dict[int, float]:
    """Parse Block MASS → {pdg_id: mass_gev}."""
    masses: dict[int, float] = {}
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Detect block start
        if re.match(r"^Block\s+MASS", stripped, re.IGNORECASE):
            in_block = True
            continue
        # Detect new block start
        if re.match(r"^Block\s+", stripped, re.IGNORECASE) or re.match(r"^DECAY\s+", stripped, re.IGNORECASE):
            if in_block:
                in_block = False
            continue
        if in_block:
            # Remove inline comments
            data_part = stripped.split("#")[0].strip()
            parts = data_part.split()
            if len(parts) >= 2:
                try:
                    pdg_id = int(parts[0])
                    mass = float(parts[1])
                    masses[pdg_id] = mass
                except (ValueError, IndexError):
                    pass
    return masses


def _parse_decay_blocks(text: str) -> dict[int, float]:
    """Parse DECAY blocks → {pdg_id: total_width_gev}."""
    widths: dict[int, float] = {}
    for m in re.finditer(
        r"^DECAY\s+(-?\d+)\s+([0-9.eE+\-]+)", text, re.MULTILINE | re.IGNORECASE
    ):
        pdg_id = int(m.group(1))
        width = float(m.group(2))
        widths[pdg_id] = width
    return widths


def _parse_coupling_block(
    text: str, block_name: str
) -> dict[int, dict[str, Any]]:
    """
    Parse HiggsBoundsInputHiggsCouplingsX block.

    Boson columns: n_Higgs n_neutral n_charged CP ww zz hh aa gg
    Fermion columns: n_Higgs n_neutral n_charged CP tt bb tautau

    Returns dict keyed by Higgs mass entry index (1-based row number),
    but we need to map to PDG IDs via the MASS block externally.
    """
    couplings: dict[int, dict[str, Any]] = {}
    in_block = False
    row_index = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if re.match(r"^Block\s+" + re.escape(block_name), stripped, re.IGNORECASE):
            in_block = True
            row_index = 0
            continue

        if re.match(r"^Block\s+", stripped, re.IGNORECASE) or re.match(r"^DECAY\s+", stripped, re.IGNORECASE):
            if in_block:
                in_block = False
            continue

        if in_block:
            data_part = stripped.split("#")[0].strip()
            parts = data_part.split()
            if len(parts) < 4:
                continue

            # Format detection: SPheno row-index vs FeynHiggs PDG-triplet.
            # SPheno: parts[0] is an integer row index (no decimal point).
            # PDG-triplet (FeynHiggs/HB-5 native): parts[0] is a float coupling
            # value (has decimal point), parts[1] is nPDG (int), parts[2..] are PDGs.
            is_spheno_format = False
            try:
                int(parts[0])
                # If it parsed as int AND has enough trailing numeric fields, treat as SPheno.
                if len(parts) >= 5:
                    [float(p) for p in parts[4:]]
                    is_spheno_format = True
            except (ValueError, IndexError):
                pass

            if is_spheno_format:
                try:
                    row_num = int(parts[0])
                    n_neutral = int(parts[1])
                    n_charged = int(parts[2])
                    cp_flag = int(parts[3])
                    vals = [float(p) for p in parts[4:]]
                except (ValueError, IndexError):
                    continue
            else:
                # Try PDG-triplet format. Two SPheno row shapes occur:
                #   Bosons:   <coupling> <ncomb> PDG1 PDG2 [...]
                #   Fermions: <scalar> <pseudoscalar> <ncomb> PDG1 PDG2 [...]
                # The fermion row carries TWO leading coupling values (scalar +
                # pseudoscalar) before the integer ``ncomb``. Distinguish by
                # whether parts[1] parses as an integer (ncomb → boson shape)
                # or a float (pseudoscalar coupling → fermion shape). We key
                # named couplings off the scalar (parts[0]) value.
                try:
                    coupling_val = float(parts[0])
                    try:
                        n_pdg = int(parts[1])
                        pdg_start = 2
                    except ValueError:
                        # Fermion 2-value row: parts[1] is the pseudoscalar
                        # coupling, parts[2] is ncomb.
                        n_pdg = int(parts[2])
                        pdg_start = 3
                    pdg_codes = [int(p) for p in parts[pdg_start:pdg_start + n_pdg]]
                except (ValueError, IndexError):
                    continue

                import logging as _logging
                _logging.info(
                    "slha_adapter: PDG-triplet row detected in %s: coupling=%.4g nPDG=%d PDGs=%s",
                    block_name, coupling_val, n_pdg, pdg_codes
                )

                # In PDG-triplet format each line is one coupling for one vertex.
                # Map to our row-keyed structure by the first PDG code (Higgs PDG).
                higgs_pdg = pdg_codes[0] if pdg_codes else 0
                row_num = higgs_pdg  # use PDG as key for PDG-triplet entries
                n_neutral = 1  # placeholder; caller uses PDG key directly
                n_charged = 0
                cp_flag = 1
                vals = [coupling_val]

                # Merge into existing entry for this Higgs PDG
                existing = couplings.get(row_num)
                if existing is None:
                    existing = {
                        "row": row_num,
                        "n_neutral": n_neutral,
                        "n_charged": n_charged,
                        "cp": cp_flag,
                        "raw_values": [],
                        "pdg_triplet": True,
                        "couplings_by_vertex": [],
                    }
                existing["couplings_by_vertex"].append({
                    "val": coupling_val,
                    "pdg": pdg_codes,
                })
                couplings[row_num] = existing

                # Populate named coupling fields from PDG vertex information
                # using standard HB-5 PDG codes for WW/ZZ/gg/bb/tt/tautau
                vertex_set = frozenset(abs(p) for p in pdg_codes)
                entry_for_named = existing
                if vertex_set == {25, 24} or vertex_set == {35, 24} or vertex_set == {36, 24}:
                    # H-W-W vertex: single boson coupling (no separate pseudoscalar)
                    entry_for_named["ww"] = coupling_val
                elif vertex_set == {25, 23} or vertex_set == {35, 23} or vertex_set == {36, 23}:
                    entry_for_named["zz"] = coupling_val
                elif vertex_set == {25, 21} or vertex_set == {35, 21} or vertex_set == {36, 21}:
                    entry_for_named["gg"] = coupling_val
                elif vertex_set == {25, 22} or vertex_set == {35, 22} or vertex_set == {36, 22}:
                    entry_for_named["aa"] = coupling_val
                elif 5 in vertex_set and len(vertex_set) <= 3:
                    entry_for_named.setdefault("bb", coupling_val)
                elif 6 in vertex_set and len(vertex_set) <= 3:
                    entry_for_named.setdefault("tt", coupling_val)
                elif 15 in vertex_set and len(vertex_set) <= 3:
                    entry_for_named.setdefault("tautau", coupling_val)
                continue

            row_index += 1
            entry = {
                "row": row_num,
                "n_neutral": n_neutral,
                "n_charged": n_charged,
                "cp": cp_flag,
                "raw_values": vals,
            }

            if "Fermion" in block_name or "fermion" in block_name.lower():
                if len(vals) >= 3:
                    entry["tt"] = vals[0]
                    entry["bb"] = vals[1]
                    entry["tautau"] = vals[2]
            else:
                if len(vals) >= 5:
                    entry["ww"] = vals[0]
                    entry["zz"] = vals[1]
                    entry["hh"] = vals[2]
                    entry["aa"] = vals[3]
                    entry["gg"] = vals[4]

            couplings[row_num] = entry

    return couplings


def _parse_legacy_higgsbounds_block(text: str) -> dict | None:
    """Parse legacy 'Block HiggsBounds' if present. Returns None if absent."""
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^Block\s+HiggsBounds\b", stripped, re.IGNORECASE):
            return {"legacy": True}
    return None


def _map_row_couplings_to_pdg(
    couplings: dict[int, dict[str, Any]], masses: dict[int, float]
) -> dict[int, dict[str, Any]]:
    """
    Map row-indexed couplings to PDG IDs.

    The coupling block rows are ordered: first n_neutral neutral Higgses
    (in mass order), then n_charged charged Higgses. We need to figure out
    which PDG IDs correspond to which rows.

    Neutral Higgs PDG IDs in 2HDM: 25 (h), 35 (H), 36 (A)
    Charged Higgs PDG ID: 37 (H+)
    """
    # Collect neutral and charged PDG IDs from masses
    neutral_pdg = sorted(
        [pdg for pdg in masses if pdg in (25, 35, 36)],
        key=lambda p: masses[p]
    )
    charged_pdg = [pdg for pdg in masses if abs(pdg) == 37]

    all_pdg = neutral_pdg + charged_pdg

    result: dict[int, dict[str, Any]] = {}
    for row_num, entry in couplings.items():
        if 1 <= row_num <= len(all_pdg):
            pdg = all_pdg[row_num - 1]
            result[pdg] = entry
        else:
            # Can't map — use row_num as key with warning
            result[row_num] = entry

    return result


def parse_slha(
    text: str,
    allow_legacy: bool = False,
) -> dict[str, Any]:
    """
    Parse an SLHA2 text and extract HiggsBounds/HiggsSignals input data.

    Parameters
    ----------
    text : str
        Full SLHA file text.
    allow_legacy : bool
        If True, accept the legacy HiggsBounds block as fallback.

    Returns
    -------
    dict with keys:
        masses: {pdg_id: mass_gev}
        widths: {pdg_id: total_width_gev}
        boson_couplings: {pdg_id: {ww, zz, hh, aa, gg, ...}}
        fermion_couplings: {pdg_id: {tt, bb, tautau, ...}}
        n_neutral: int
        n_charged: int
        used_legacy_block: bool (only if legacy block used)

    Raises
    ------
    SlhaMissingBlocksError
        If HiggsBoundsInput coupling blocks (and legacy block) are absent.
    SlhaMassBlockMissingError
        If Block MASS is absent.
    """
    masses = _parse_mass_block(text)
    if not masses:
        raise SlhaMassBlockMissingError(
            "Block MASS not found in SLHA file. Cannot proceed without Higgs masses."
        )

    widths = _parse_decay_blocks(text)

    # Try new-style coupling blocks first. HiggsBounds5 canonical block names
    # are ``HiggsBoundsInputHiggsCouplings{Bosons,Fermions}``, but this SARAH/
    # SPheno build (WriteHiggsBoundsBlocks via SPhenoInput 520/76) emits the
    # shorter ``HiggsCouplings{Bosons,Fermions}`` names (plus EFFHIGGSCOUPLINGS).
    # Accept either spelling — the binary does not contain the HiggsBoundsInput*
    # strings at all, so aliasing is the correct fix (no rewrite needed).
    boson_rows = (
        _parse_coupling_block(text, "HiggsBoundsInputHiggsCouplingsBosons")
        or _parse_coupling_block(text, "HiggsCouplingsBosons")
    )
    fermion_rows = (
        _parse_coupling_block(text, "HiggsBoundsInputHiggsCouplingsFermions")
        or _parse_coupling_block(text, "HiggsCouplingsFermions")
    )

    used_legacy = False

    if not boson_rows and not fermion_rows:
        # Try legacy fallback
        legacy = _parse_legacy_higgsbounds_block(text)
        if legacy and allow_legacy:
            warnings.warn(
                "Legacy 'Block HiggsBounds' used instead of "
                "HiggsBoundsInputHiggsCouplingsX blocks. "
                "Rerun SPheno with WriteHiggsBoundsBlocks=True for full support.",
                UserWarning,
                stacklevel=2,
            )
            used_legacy = True
        else:
            raise SlhaMissingBlocksError(
                "Required HiggsBounds input blocks absent from SLHA: "
                "HiggsBoundsInputHiggsCouplingsBosons and "
                "HiggsBoundsInputHiggsCouplingsFermions not found.",
                user_instruction=(
                    "Re-run SPheno with WriteHiggsBoundsBlocks=True in the "
                    "SARAH-generated SPheno.m model directive, then re-run "
                    "/spheno-build to regenerate the SLHA output."
                ),
            )

    # Map row indices to PDG IDs
    boson_couplings = _map_row_couplings_to_pdg(boson_rows, masses) if boson_rows else {}
    fermion_couplings = _map_row_couplings_to_pdg(fermion_rows, masses) if fermion_rows else {}

    # Determine n_neutral and n_charged from coupling block entries
    n_neutral = 0
    n_charged = 0
    all_rows = boson_rows or fermion_rows
    for entry in all_rows.values():
        if entry.get("n_charged", 0) == 1:
            n_charged += 1
        elif entry.get("n_neutral", 0) == 1:
            n_neutral += 1

    result: dict[str, Any] = {
        "masses": masses,
        "widths": widths,
        "boson_couplings": boson_couplings,
        "fermion_couplings": fermion_couplings,
        "n_neutral": n_neutral,
        "n_charged": n_charged,
    }
    if used_legacy:
        result["used_legacy_block"] = True

    return result
