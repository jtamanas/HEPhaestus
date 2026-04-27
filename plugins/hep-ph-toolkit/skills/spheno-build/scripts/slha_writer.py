"""slha_writer.py — Render an analytic-module result dict to SLHA text.

The result dict schema (see backends/analytic.py docstring):
    {
      "masses":   {pdg_id_int: mass_float},
      "mixing":   {block_name: {(i, j): value}},
      "minpar":   [(idx, value, name)],
      "problem":  [int],
      "diagnostics": {...},
    }

The emitted SLHA is parse_slha.parse()-compatible.
"""

from __future__ import annotations

from typing import Iterable

# Copy of leshouches_template._SMINPUTS_LINES bytes for exact-match downstream.
_SMINPUTS = """\
Block SMINPUTS
   1   1.279340000E+02   # alpha_em^{-1}(MZ)
   2   1.166380000E-05   # G_F [GeV^-2]
   3   1.184000000E-01   # alpha_s(MZ)
   4   9.118760000E+01   # MZ [GeV]
   5   4.180000000E+00   # m_b(m_b) [GeV]
   6   1.734000000E+02   # m_t [GeV]
   7   1.776820000E+00   # m_tau [GeV]
"""

_MODSEL = """\
Block MODSEL
   1   0   # non-SUSY (v1)
"""


def _fmt_val(v: float) -> str:
    return f"{v: .8E}"


def render(result: dict, spec: dict | None = None,
           params: dict | None = None) -> str:
    """Render the result dict to a single SLHA text block."""
    params = params or {}
    sections: list[str] = [_MODSEL, _SMINPUTS]

    # SPINFO
    sections.append(
        "Block SPINFO\n"
        "   1   hephaestus analytic\n"
        "   2   WS-A\n"
    )

    # MINPAR echo from params (idx per insertion order).
    if params:
        lines = ["Block MINPAR"]
        for idx, (k, v) in enumerate(params.items(), start=1):
            lines.append(f"   {idx}   {v:E}   # {k}")
        sections.append("\n".join(lines) + "\n")

    # PROBLEM
    probs = result.get("problem") or []
    if probs:
        lines = ["Block PROBLEM"]
        for p in probs:
            lines.append(f"   {p}   analytic-flagged")
        sections.append("\n".join(lines) + "\n")

    # MASS
    masses = result.get("masses") or {}
    if masses:
        lines = ["Block MASS"]
        for pdg, m in sorted(masses.items(), key=lambda kv: int(kv[0])):
            lines.append(f"   {int(pdg)}  {_fmt_val(float(m))}  # pdg={pdg}")
        sections.append("\n".join(lines) + "\n")

    # Mixing blocks
    mixing = result.get("mixing") or {}
    for name, entries in mixing.items():
        lines = [f"Block {name}"]
        for (i, j), v in sorted(entries.items()):
            lines.append(f"   {int(i)} {int(j)}  {_fmt_val(float(v))}")
        sections.append("\n".join(lines) + "\n")

    return "\n".join(sections)
