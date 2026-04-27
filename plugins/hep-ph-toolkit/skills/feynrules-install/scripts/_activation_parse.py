#!/usr/bin/env python3
"""Pure-Python helper: wolframscript stdout + exit code → status JSON.

CLI usage:
    echo "<wolframscript stdout>" | python3 _activation_parse.py <exit_code>

The exit_code argument is the integer exit code from wolframscript (0 or non-zero).
Prints a single JSON object to stdout. Self-contained copy for feynrules-install.
"""

import sys
import json
import re

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

# Activation-required detection patterns.
# Conservative union of known Wolfram Engine activation-prompt substrings.
ACTIVATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"activate", re.IGNORECASE),
    re.compile(r"wolfram\s+id", re.IGNORECASE),
    re.compile(r"not\s+activated", re.IGNORECASE),
    re.compile(r"activation\s+required", re.IGNORECASE),
    re.compile(r"no\s+valid\s+license|license\s+(not\s+found|expired|required|invalid)", re.IGNORECASE),
    re.compile(r"no\s+valid\s+password", re.IGNORECASE),
]

ACTIVATION_USER_INSTRUCTION = (
    "Run `wolframscript --activate` in your terminal; it opens a browser for a "
    "free Wolfram ID signup. Then rerun /feynrules-install."
)


def classify(stdout: str, exit_code: int) -> dict:
    """Return a status dict based on wolframscript output.

    Returns one of:
        {"status": "ok"}
        {"status": "activation_required", "message": "...", "user_instruction": "..."}
        {"status": "error", "detail": "<first 200 chars of stdout>"}
    """
    stripped = stdout.strip()

    for pat in ACTIVATION_PATTERNS:
        if pat.search(stripped):
            return {
                "status": "activation_required",
                "message": "Wolfram Engine is installed but needs activation.",
                "user_instruction": ACTIVATION_USER_INSTRUCTION,
            }

    # Happy path: exit 0 and output contains "2" (from `1+1`).
    if exit_code == 0 and re.search(r"^\s*2\s*$", stripped, re.MULTILINE):
        return {"status": "ok"}

    return {"status": "error", "detail": stripped[:200]}


def main() -> None:
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {"status": "error", "detail": "usage: _activation_parse.py <exit_code>"}
            )
        )
        sys.exit(1)
    try:
        exit_code = int(sys.argv[1])
    except ValueError:
        print(
            json.dumps(
                {"status": "error", "detail": f"invalid exit_code: {sys.argv[1]!r}"}
            )
        )
        sys.exit(1)

    stdout_text = sys.stdin.read()
    result = classify(stdout_text, exit_code)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
