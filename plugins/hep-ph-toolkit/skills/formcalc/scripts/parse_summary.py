"""
parse_summary.py — parse amp_reduced.m to detect PV heads and IR/UV flags.

Counts PV integral heads (B0i, C0i, D0i) and detects IR-divergent patterns
such as B0[0,0,0], C0[0,...], etc.

No Wolfram execution — pure text-level pattern detection on the .m file.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Union


# PV head patterns (FormCalc-native)
_PV_PATTERN = re.compile(r'\b(A0i|B0i|C0i|D0i)\b')

# IR-divergent patterns: massless PV integrals
# B0[0,0,0] = IR divergent; B0i[bb0, 0, 0, 0] similarly
_IR_PATTERN = re.compile(
    r'\b(?:B0|B0i)\s*\[\s*0\s*,\s*0\s*,\s*0\s*\]'
    r'|\b(?:C0|C0i)\s*\[\s*0\s*,',
    re.IGNORECASE,
)

# UV patterns: presence of any PV integral → UV-regularized
_UV_PATTERN = re.compile(r'\b(A0i?|B0i?|C0i?|D0i?)\b')


def parse_summary(amp_reduced_path: Union[str, Path]) -> dict:
    """
    Read amp_reduced.m and return a summary dict:
      {
        "pv_heads": ["B0i", "C0i", ...],   # distinct heads found
        "ir_divergent": bool,
        "uv_regularized": bool,
        "n_pv_calls": int,
      }
    """
    path = Path(amp_reduced_path)
    if not path.exists():
        return {
            "pv_heads": [],
            "ir_divergent": False,
            "uv_regularized": False,
            "n_pv_calls": 0,
        }

    content = path.read_text(encoding="utf-8", errors="replace")

    pv_matches = _PV_PATTERN.findall(content)
    pv_heads = sorted(set(pv_matches))
    n_pv = len(pv_matches)

    ir_divergent = bool(_IR_PATTERN.search(content))
    uv_regularized = bool(_UV_PATTERN.search(content))

    return {
        "pv_heads": pv_heads,
        "ir_divergent": ir_divergent,
        "uv_regularized": uv_regularized,
        "n_pv_calls": n_pv,
    }
