"""MadGraph card I/O utilities.

Read and write MadGraph param_card.dat (SLHA format) and run_card.dat files.
These are library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import re
from pathlib import Path


def read_param_card(path: str | Path) -> dict:
    """Parse an SLHA-format param_card.dat into a nested dict.

    Returns:
        Dict keyed by block name (lowercase). Each block is a dict
        mapping particle ID (int) or tuple of ints to float values.
        Special key '_decay' holds decay block entries.

    Example:
        card = read_param_card("param_card.dat")
        mt = card["mass"][6]          # top mass
        alpha_s = card["sminputs"][3] # alpha_s(MZ)
    """
    path = Path(path)
    card: dict = {}
    current_block = None

    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue

        block_match = re.match(r"block\s+(\w+)", line, re.IGNORECASE)
        if block_match:
            current_block = block_match.group(1).lower()
            card[current_block] = {}
            continue

        decay_match = re.match(
            r"decay\s+(-?\d+)\s+([\d.eE+-]+)", line, re.IGNORECASE
        )
        if decay_match:
            pid = int(decay_match.group(1))
            width = float(decay_match.group(2))
            card.setdefault("_decay", {})[pid] = {
                "width": width,
                "channels": [],
            }
            current_block = ("_decay", pid)
            continue

        if isinstance(current_block, tuple) and current_block[0] == "_decay":
            parts = line.split()
            if len(parts) >= 3:
                br = float(parts[0])
                n_daughters = int(parts[1])
                daughters = [int(p) for p in parts[2 : 2 + n_daughters]]
                card["_decay"][current_block[1]]["channels"].append(
                    {"br": br, "daughters": daughters}
                )
            continue

        if current_block and isinstance(current_block, str):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    if len(parts) == 2:
                        key = int(parts[0])
                        val = float(parts[1])
                    else:
                        key = tuple(int(p) for p in parts[:-1])
                        val = float(parts[-1])
                    card[current_block][key] = val
                except ValueError:
                    continue

    return card


def write_param_card(card: dict, path: str | Path) -> None:
    """Write a param_card dict back to SLHA format.

    Args:
        card: Dict as returned by read_param_card.
        path: Output file path.
    """
    path = Path(path)
    lines = []

    for block_name, entries in card.items():
        if block_name == "_decay":
            continue

        lines.append(f"BLOCK {block_name.upper()}")
        for key, val in sorted(
            entries.items(),
            key=lambda x: (x[0],) if isinstance(x[0], int) else x[0],
        ):
            if isinstance(key, tuple):
                key_str = "  ".join(f"{k:>4d}" for k in key)
            else:
                key_str = f"{key:>6d}"
            lines.append(f"  {key_str}  {val:16.8E}")
        lines.append("")

    if "_decay" in card:
        for pid, info in sorted(card["_decay"].items()):
            lines.append(f"DECAY  {pid:>6d}  {info['width']:16.8E}")
            for ch in info["channels"]:
                daughters_str = "  ".join(f"{d:>6d}" for d in ch["daughters"])
                lines.append(
                    f"  {ch['br']:16.8E}  {len(ch['daughters'])}  {daughters_str}"
                )
            lines.append("")

    path.write_text("\n".join(lines) + "\n")


def update_param(
    card: dict, block: str, pid: int | tuple[int, ...], value: float
) -> dict:
    """Modify a single parameter in a param_card dict in-place.

    Args:
        card: Dict as returned by read_param_card.
        block: Block name (case-insensitive, stored lowercase).
        pid: Particle ID or tuple of indices.
        value: New value.

    Returns:
        The modified card dict.

    Raises:
        KeyError: If block doesn't exist in the card.
    """
    block = block.lower()
    if block not in card:
        raise KeyError(
            f"Block '{block}' not found. Available: {list(card.keys())}"
        )
    card[block][pid] = value
    return card


def read_run_card(path: str | Path) -> dict:
    """Parse a MadGraph run_card.dat into a dict.

    MG5 run_card format: ``value = key  # comment``

    Returns:
        Dict mapping parameter names to values
        (auto-typed as int, float, bool, or str).

    Example:
        rc = read_run_card("run_card.dat")
        nevents = rc["nevents"]     # 100000
        ebeam1 = rc["ebeam1"]      # 6800.0
    """
    path = Path(path)
    card: dict = {}

    for line in path.read_text().splitlines():
        # Strip comments (! or #)
        for comment_char in ("#", "!"):
            line = line.split(comment_char)[0]
        line = line.strip()
        if not line or "=" not in line:
            continue

        parts = line.split("=", 1)
        if len(parts) != 2:
            continue

        value_str = parts[0].strip()
        key = parts[1].strip().split()[0]  # Take first word after =

        if value_str.lower() in (".true.", "true", "t"):
            value = True
        elif value_str.lower() in (".false.", "false", "f"):
            value = False
        else:
            try:
                value = int(value_str)
            except ValueError:
                try:
                    value = float(
                        value_str.replace("d", "e").replace("D", "E")
                    )
                except ValueError:
                    value = value_str

        card[key] = value

    return card


def update_run_card(card: dict, key: str, value) -> dict:
    """Modify a single run_card setting in-place.

    Args:
        card: Dict as returned by read_run_card.
        key: Parameter name.
        value: New value.

    Returns:
        The modified card dict.
    """
    card[key] = value
    return card
