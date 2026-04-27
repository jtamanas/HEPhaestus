"""
parse_slha.py — Parse an SLHA file into a structured summary dict.

Usage (library):
    from parse_slha import parse
    result = parse(Path("SPheno.spc"))

Usage (CLI):
    python3 parse_slha.py <SPheno.spc>   → writes summary.json to stdout
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import re
from pathlib import Path


def parse(spc_path: Path) -> dict:
    """Parse an SLHA spectrum file.

    Returns a dict with keys:
        masses       : {pdg_id_str: mass_float}  — from Block MASS
        widths       : {pdg_id_str: width_float}  — from DECAY headers
        problems     : [int]                       — from Block PROBLEM
        mixing       : {block_name: {i_str: {j_str: float}}}
                       or {block_name: {i_str: float}} for 1-index blocks
        spinfo       : {index_str: value_str}      — from Block SPINFO
        spinfo_warnings : [str]                    — Block SPINFO item 4 entries

    The caller maps:
        problems containing any of {1,2,3} → SPHENO_SPECTRUM_PROBLEM (recoverable)
        spinfo_warnings non-empty           → SPHENO_RGE_NONCONVERGENT (recoverable)
    """
    text = spc_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    masses: dict[str, float] = {}
    widths: dict[str, float] = {}
    problems: list[int] = []
    mixing: dict[str, dict] = {}
    spinfo: dict[str, str] = {}
    spinfo_warnings: list[str] = []

    current_block: str | None = None
    mixing_blocks = {"NMIX", "UMIX", "VMIX", "STOPMIX", "SBOTMIX", "STAUMIX",
                     "ALPHA", "HMIX", "GAUGE", "MSOFT",
                     # SARAH-emitted neutralino/chargino mixing block names.
                     # SARAH writes ZNMIX / UMMIX / UPMIX (and imaginary parts)
                     # instead of the SLHA-standard NMIX / UMIX / VMIX.
                     "ZNMIX", "UMMIX", "UPMIX",
                     "IMZNMIX", "IMUMMIX", "IMUPMIX"}

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Check for BLOCK header
        block_match = re.match(r"^Block\s+(\S+)", stripped, re.IGNORECASE)
        if block_match:
            current_block = block_match.group(1).upper()
            # Initialize mixing blocks
            if current_block in mixing_blocks:
                mixing.setdefault(current_block, {})
            i += 1
            continue

        # Check for DECAY header
        decay_match = re.match(r"^DECAY\s+(\S+)\s+(\S+)", stripped, re.IGNORECASE)
        if decay_match:
            current_block = None
            pdg_id = decay_match.group(1)
            try:
                widths[pdg_id] = float(decay_match.group(2))
            except ValueError:
                pass
            i += 1
            continue

        # Skip lines starting with # (inline comments) — already handled above
        # Process block data lines
        if current_block is None:
            i += 1
            continue

        # Strip inline comments
        data_part = stripped.split("#")[0].strip()
        if not data_part:
            i += 1
            continue

        tokens = data_part.split()

        if current_block == "MASS":
            # Format: <pdg_id>  <mass>
            if len(tokens) >= 2:
                try:
                    masses[tokens[0]] = float(tokens[1])
                except ValueError:
                    pass

        elif current_block == "PROBLEM":
            # Format: <code>  <value_or_message>
            if len(tokens) >= 1:
                try:
                    problems.append(int(tokens[0]))
                except ValueError:
                    pass

        elif current_block == "SPINFO":
            # Format: <index>  <value>
            if len(tokens) >= 2:
                idx = tokens[0]
                val = " ".join(tokens[1:])
                spinfo[idx] = val
                if idx == "4":
                    spinfo_warnings.append(val)
            elif len(tokens) == 1:
                # Some SPheno versions write just the index for certain entries
                spinfo[tokens[0]] = ""

        elif current_block in mixing_blocks:
            # Format: <i>  <j>  <value>  or  <i>  <value>  (for 1-index blocks)
            block_dict = mixing[current_block]
            if len(tokens) == 3:
                row, col, val = tokens[0], tokens[1], tokens[2]
                try:
                    row_dict = block_dict.setdefault(row, {})
                    row_dict[col] = float(val)
                except ValueError:
                    pass
            elif len(tokens) == 2:
                idx, val = tokens[0], tokens[1]
                try:
                    block_dict[idx] = float(val)
                except ValueError:
                    pass

        i += 1

    return {
        "masses": masses,
        "widths": widths,
        "problems": problems,
        "mixing": mixing,
        "spinfo": spinfo,
        "spinfo_warnings": spinfo_warnings,
    }


def _classify_status(result: dict) -> str:
    """Return a human-readable status string from a parse result."""
    if not result["masses"]:
        return "no_output"
    if result["problems"]:
        codes = set(result["problems"])
        if codes & {1, 2, 3}:
            return "spectrum_problem"
    if result["spinfo_warnings"]:
        return "rge_nonconvergent"
    return "ok"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <SPheno.spc>", file=sys.stderr)
        sys.exit(2)

    spc_path = Path(sys.argv[1])
    if not spc_path.exists():
        print(f"error: file not found: {spc_path}", file=sys.stderr)
        sys.exit(1)

    result = parse(spc_path)
    result["status"] = _classify_status(result)
    print(json.dumps(result, indent=2))
