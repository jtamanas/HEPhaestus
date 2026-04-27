"""_make_log_parse.py — parse make log for error diagnostics.

Adapted from /spheno-build pattern.

Public API:
    tail_lines(log_text: str, n: int = 40) -> str
        Returns the last n lines of the make log.

    first_error(log_text: str) -> str | None
        Returns the first 'error:' line from the log, or None.
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


def tail_lines(log_text: str, n: int = 40) -> str:
    """Return last n lines of log_text."""
    lines = log_text.splitlines()
    return "\n".join(lines[-n:])


def first_error(log_text: str) -> str | None:
    """Return the first line containing 'error:' (case-insensitive), or None."""
    for line in log_text.splitlines():
        if "error:" in line.lower():
            return line.strip()
    return None


def make_log_tail_json_safe(log_text: str, n: int = 40) -> str:
    """Return last n lines, JSON-safe (escaped quotes, no newlines)."""
    tail = tail_lines(log_text, n)
    return tail.replace('"', '\\"').replace("\n", "|")
