"""parse_slha_mass_block.py — read the SLHA MASS block from a spectrum file.

Public API:
    read_masses(path: str | Path) -> dict[int, float]
        Returns {pdg_id: mass_gev} for all entries in Block MASS.

Usage:
    from parse_slha_mass_block import read_masses
    masses = read_masses("SPheno.spc")
    print(masses[1000022])  # lightest neutralino mass
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import re
from pathlib import Path


class SLHAParseError(Exception):
    """Raised when the SLHA file cannot be parsed."""


def read_masses(path: str | Path) -> dict[int, float]:
    """Parse Block MASS from an SLHA file.

    Args:
        path: Path to the SLHA spectrum file.

    Returns:
        Dict mapping PDG id (int) → mass in GeV (float, absolute value).

    Raises:
        SLHAParseError: if no MASS block is found or a line is malformed.
        FileNotFoundError: if the file does not exist.
    """
    path = Path(path)
    text = path.read_text(errors="replace")
    return _parse_mass_block(text, str(path))


def _parse_mass_block(text: str, filename: str = "<input>") -> dict[int, float]:
    """Parse Block MASS content from raw SLHA text.

    Args:
        text:     Full content of the SLHA file.
        filename: Used in error messages.

    Returns:
        Dict mapping PDG id → |mass| in GeV.

    Raises:
        SLHAParseError: if no MASS block is present.
    """
    masses: dict[int, float] = {}
    in_mass = False

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        # Strip comments
        line = raw_line.split("#")[0].rstrip()
        if not line.strip():
            continue

        # Block header detection
        block_match = re.match(r"^\s*[Bb][Ll][Oo][Cc][Kk]\s+(\S+)", line)
        if block_match:
            block_name = block_match.group(1).upper()
            in_mass = (block_name == "MASS")
            continue

        if not in_mass:
            continue

        # Entry: <pdg_id> <mass>
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            pdg_id = int(parts[0])
            mass = float(parts[1])
        except ValueError as e:
            raise SLHAParseError(
                f"{filename}:{lineno}: malformed MASS entry {line!r}: {e}"
            ) from e

        masses[pdg_id] = abs(mass)

    if not masses and "MASS" not in text.upper():
        raise SLHAParseError(
            f"{filename}: no Block MASS section found"
        )

    return masses


if __name__ == "__main__":
    import json
    if len(sys.argv) < 2:
        print("Usage: parse_slha_mass_block.py <spectrum.spc>", file=sys.stderr)
        sys.exit(1)
    try:
        m = read_masses(sys.argv[1])
        print(json.dumps({str(k): v for k, v in sorted(m.items())}))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
