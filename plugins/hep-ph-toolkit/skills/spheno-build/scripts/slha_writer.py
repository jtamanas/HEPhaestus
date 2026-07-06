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


def _param_lha_map(spec: dict | None) -> dict[str, tuple[str, int]]:
    """name -> (block, code) from spec.parameters[*].les_houches.

    Accepts both the param ``name`` and its ``output_name`` as keys so the
    caller's ``params`` dict resolves regardless of which the backend used.
    """
    out: dict[str, tuple[str, int]] = {}
    if not spec:
        return out
    for p in spec.get("parameters", []) or []:
        lh = p.get("les_houches")
        if not lh or len(lh) != 2:
            continue  # matrix/mixing entries (len>2 or symbolic codes) are
                      # emitted via result["mixing"], not here.
        try:
            code = int(lh[1])
        except (TypeError, ValueError):
            continue  # non-numeric code (e.g. a named mixing block) — skip.
        dest = (str(lh[0]), code)
        for key in (p.get("name"), p.get("output_name")):
            if key:
                out[key] = dest
    return out


# SM fermion rotation matrices and the SARAH field-redefinition phase are
# declared as external params in SARAH UFOs but default to 0. When they are
# trivial (identity / unity) SPheno — and this analytic writer — historically
# omitted them, so MG5 read 0, i.e. the ZERO matrix, which silently deletes
# the Higgs-quark Yukawa (ZDL†·Yd·ZDR) and thus the DD Higgs t-channel. Emit
# them explicitly as identity/unity so the SLHA is self-consistent for every
# downstream consumer (not only the MadDM path, which also has a safety-net in
# maddm/scripts/slha_complete.py).
_SM_IDENTITY_ROTATIONS = ("UDLMIX", "UDRMIX", "UULMIX", "UURMIX",
                          "UELMIX", "UERMIX")


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

    # Input-parameter blocks. Route each param to the LesHouches block/code
    # the spec declares for it (spec.parameters[*].les_houches = [BLOCK, code]),
    # so BSM inputs land in the block the UFO actually reads (e.g. yh1 ->
    # BSMPARAMS 3). Historically this echoed everything into MINPAR by
    # insertion order; MG5 then silently defaulted the real block (BSMPARAMS)
    # to 0 because the UFO reads yh1/yh2 from BSMPARAMS, not MINPAR — zeroing
    # the Higgs-portal coupling. Params without a declared block fall back to a
    # MINPAR echo (previous behaviour).
    routed_blocks: set[str] = set()
    if params:
        lha_map = _param_lha_map(spec)
        routed: dict[str, list[tuple[int, float, str]]] = {}
        minpar_fallback: list[tuple[float, str]] = []
        for k, v in params.items():
            dest = lha_map.get(k)
            if dest is not None:
                block, code = dest
                routed.setdefault(block.upper(), []).append((int(code), float(v), k))
            else:
                minpar_fallback.append((float(v), k))
        for block, entries in routed.items():
            lines = [f"Block {block}"]
            for code, v, name in sorted(entries):
                # A field-redefinition phase of exactly 0 is unphysical (a
                # phase has unit modulus); it is SARAH's Set_All_Parameters_0
                # sentinel leaking through the analytic model's param store.
                # Emitting it verbatim zeroes every conjg(PhaseFS)-carrying
                # coupling downstream (relic 0.166-instead-of-0.0717 symptom).
                if block == "PHASES" and v == 0.0:
                    v = 1.0
                    name = f"{name} (coerced 0->1: zero phase unphysical)"
                lines.append(f"   {code}   {v:E}   # {name}")
            sections.append("\n".join(lines) + "\n")
        routed_blocks = set(routed)
        if minpar_fallback:
            lines = ["Block MINPAR"]
            for idx, (v, name) in enumerate(minpar_fallback, start=1):
                lines.append(f"   {idx}   {v:E}   # {name}")
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
    present = {name.upper() for name in mixing} | routed_blocks
    for name, entries in mixing.items():
        lines = [f"Block {name}"]
        for (i, j), v in sorted(entries.items()):
            lines.append(f"   {int(i)} {int(j)}  {_fmt_val(float(v))}")
        sections.append("\n".join(lines) + "\n")

    # SM fermion rotations (identity) + field-redefinition phase (unity), only
    # for blocks the model did not itself provide. Skipped if the analytic
    # module already emitted a non-trivial rotation of the same name.
    for name in _SM_IDENTITY_ROTATIONS:
        if name in present:
            continue
        real = "\n".join(f"   {d} {d}   1.00000000E+00" for d in (1, 2, 3))
        imag = "\n".join(f"   {d} {d}   0.00000000E+00" for d in (1, 2, 3))
        sections.append(f"Block {name}\n{real}\n")
        sections.append(f"Block IM{name}\n{imag}\n")
    if "PHASES" not in present:
        sections.append("Block PHASES\n   1   1.00000000E+00\n")
        sections.append("Block IMPHASES\n   1   0.00000000E+00\n")

    return "\n".join(sections)
