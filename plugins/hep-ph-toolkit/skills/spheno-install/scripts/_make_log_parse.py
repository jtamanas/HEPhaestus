#!/usr/bin/env python3
"""_make_log_parse.py — Parse a SPheno make.log and return a blocker dict.

Pure-Python helper called by install_spheno.sh when `make` fails.

Usage (CLI):
    python3 _make_log_parse.py < /tmp/spheno_make.log
    # Prints JSON to stdout.

Library:
    from _make_log_parse import parse
    result = parse(log_text)
"""
import sys

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import re


def parse(log_text: str) -> dict:
    """Parse make.log text and return a SPHENO_BASE_BUILD_FAILED blocker dict.

    Returns:
        dict with keys: code, mode, message, context
        context contains: make_log_tail (last 40 lines, newline-joined),
                          likely_cause ("lapack" or "generic")
    """
    lines = log_text.splitlines()
    tail_lines = lines[-40:] if len(lines) >= 40 else lines
    make_log_tail = "\n".join(tail_lines)

    # Detect LAPACK-related failure
    lapack_pattern = re.compile(r"lapack|liblapack|-llapack", re.IGNORECASE)
    likely_cause = "lapack" if lapack_pattern.search(log_text) else "generic"

    if likely_cause == "lapack":
        message = "SPheno base build failed: missing LAPACK library."
    else:
        message = "SPheno base build failed: see make_log_tail for details."

    return {
        "code": "SPHENO_BASE_BUILD_FAILED",
        "mode": "fatal",
        "message": message,
        "context": {
            "make_log_tail": make_log_tail,
            "likely_cause": likely_cause,
        },
    }


def main() -> None:
    log_text = sys.stdin.read()
    result = parse(log_text)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
