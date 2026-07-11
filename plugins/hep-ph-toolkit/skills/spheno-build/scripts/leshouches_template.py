"""
leshouches_template.py — Build LesHouches input cards from a ModelSpec.

Usage (library):
    from leshouches_template import build, patch_minpar
    card = build(spec, overrides={"MpsiD": 300.0})
    patched = patch_minpar(card, {"MpsiD": 300.0})

Usage (CLI):
    python3 leshouches_template.py <spec.yaml> [--override name=value ...]
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import re
from pathlib import Path


# ---------------------------------------------------------------------------
# SPheno scalar-input blocks.
#
# A ModelSpec parameter is a *card input* iff it declares a list-form
# ``les_houches: [BLOCK, N]`` metadata whose BLOCK names one of these
# scalar-input blocks. Its value is then written at index N (honouring the
# spec's declared index) into both ``Block MINPAR`` and ``Block BSMPARAMSIN``
# (SPheno's Read_MINPAR seed + SARAH's Read_BSMPARAMSIN LOW-branch input).
#
# Everything else in ``spec.parameters`` is NOT a card input and is excluded
# by design (documented fallback): SM couplings/Yukawas (no ``les_houches``
# key, computed internally from SMINPUTS), mixing matrices (string-form
# ``les_houches`` like ``ZNMIX`` — OUTPUT blocks), and any list-form
# ``les_houches`` pointing at a block this template does not emit (e.g.
# ``PHASES`` — phase inputs default to zero and are not required for the mass
# spectrum). Excluding is not the same as *misplacing*: the pre-fix code
# enumerated ALL parameters into MINPAR by declaration order, silently landing
# the BSM inputs (MS/MPsi/yh1/yh2) at indices 24-27 where SARAH never reads
# them → zero-mass spectrum, FChi1 = -0.0, no error. Honouring the declared
# index and excluding non-inputs kills that silent-misplacement class.
# ---------------------------------------------------------------------------
_INPUT_SCALAR_BLOCKS = frozenset({"MINPAR", "BSMPARAMS", "BSMPARAMSIN"})


def input_scalar_params(spec: dict) -> dict[str, int]:
    """Return ``{param_name: minpar_index}`` for the card's scalar inputs.

    A parameter qualifies iff it carries a list-form
    ``les_houches: [BLOCK, N]`` whose BLOCK is one of ``_INPUT_SCALAR_BLOCKS``.
    Callers (e.g. run_spheno) use this to loudly reject user overrides that
    name a parameter which would never reach the generated card.

    Raises:
        ValueError: if two placed parameters collide on the same index.
    """
    placed: dict[int, str] = {}
    out: dict[str, int] = {}
    for param in spec.get("parameters", []):
        name = param["name"]
        lh = param.get("les_houches")
        if (
            isinstance(lh, (list, tuple))
            and len(lh) == 2
            and str(lh[0]).upper() in _INPUT_SCALAR_BLOCKS
        ):
            idx = int(lh[1])
            if idx in placed and placed[idx] != name:
                raise ValueError(
                    f"les_houches index collision at MINPAR[{idx}]: "
                    f"{placed[idx]!r} and {name!r} both declare it. "
                    "Fix the spec's les_houches keys."
                )
            placed[idx] = name
            out[name] = idx
    return out


# ---------------------------------------------------------------------------
# SM Input values (PDG 2020 defaults — hardcoded per spec §5)
# ---------------------------------------------------------------------------
_SMINPUTS_LINES = """\
Block SMINPUTS
   1   1.279340000E+02   # alpha_em^{-1}(MZ)
   2   1.166380000E-05   # G_F [GeV^-2]
   3   1.184000000E-01   # alpha_s(MZ)
   4   9.118760000E+01   # MZ [GeV]
   5   4.180000000E+00   # m_b(m_b) [GeV]
   6   1.734000000E+02   # m_t [GeV]
   7   1.776820000E+00   # m_tau [GeV]
"""

# ---------------------------------------------------------------------------
# MODSEL (non-SUSY, v1 only)
# ---------------------------------------------------------------------------
_MODSEL_LINES = """\
Block MODSEL
   1   0   # non-SUSY (v1)
"""

# ---------------------------------------------------------------------------
# SM LOW-boundary defaults (SARAH reads these into module-level *IN
# variables through ``Read_GAUGEIN``, ``Read_SMIN``, ``Read_HMIXIN``).
# When ``HighScaleModel = "LOW"`` AND ``MatchingOrder = -1`` (auto-selected
# in ``SPheno<Name>.f90`` whenever ``CalculateOneLoopMasses = False``),
# SPheno pulls ``g1IN``, ``g2IN``, ``g3IN``, ``vvSMIN``, ``LamIN``,
# ``m2SMIN`` into the model variables before any SM matching runs. Missing
# blocks default to zero, which collapses the Higgs quartic and every
# vev-coupled BSM mass in Block MASS to zero. See sarah-workarounds.md §16
# for the full rationale.
#
# Numerical values:
#   g1 = sqrt(3/5)*sqrt(20*pi*alpha_em/(3*(1-sinW^2))) at MZ ~ 0.4626
#   g2 = sqrt(4*pi*alpha_em/sinW^2)                    at MZ ~ 0.6488
#   g3 = sqrt(4*pi*alpha_s(MZ))                        at MZ ~ 1.2197
# These match the values SPheno's internal SM computation derives from
# SMINPUTS (alpha_em, G_F, MZ, alpha_s) and are supplied here so the
# pole-matching branch (MatchingOrder == -1) starts from consistent seeds.
# vvSM = 246.22 GeV is the physical SM VEV.
# Lam = m_h^2 / v^2 = 125.25^2 / 246.22^2 ≈ 0.2587 is the SM tree-level
# Higgs quartic in SARAH's convention (``Mhh^2 = m2SM + 3 v^2 Lam / 2`` at
# tree level, with tadpole ``m2SM = -v^2 Lam / 2``, giving
# ``Mhh^2 = Lam v^2``). m2SM is computed by ``SolveTadpoleEquations`` and
# therefore only needs a consistent seed.
# ---------------------------------------------------------------------------
_GAUGEIN_LINES = """\
Block GAUGEIN
   1   4.626000000E-01   # g1(M_Z) — hypercharge, GUT-unnormalised
   2   6.488000000E-01   # g2(M_Z) — SU(2)_L
   3   1.219780000E+00   # g3(M_Z) — SU(3)_C
"""

_HMIXIN_LINES = """\
Block HMIXIN
   3   2.462195140E+02   # vvSM — SM EW VEV [GeV]
"""

_SMIN_LINES = """\
Block SMIN
   1  -7.828282000E+03   # m2SMIN = -Lam * v^2 / 2 [GeV^2] (tadpole-consistent)
   2   2.587500000E-01   # LamIN  = m_h^2 / v^2 (SM tree-level Higgs quartic)
"""


def build(spec: dict, overrides: dict[str, float] | None = None) -> str:
    """Build a LesHouches input card string from a ModelSpec dict.

    Blocks generated:
        Block MODSEL       — fixed non-SUSY flag.
        Block SMINPUTS     — PDG 2020 defaults (hardcoded).
        Block GAUGEIN      — g1/g2/g3 at M_Z (LOW-boundary seed values;
                             overwritten by SMINPUTS-derived SM matching but
                             required by the MatchingOrder == -1 pole-matching
                             branch in SPheno<Name>.f90).
        Block HMIXIN       — vvSMIN = 246.22 GeV (SM EW VEV seed).
        Block SMIN         — Lam (Higgs quartic) and m2SM (Higgs mass-squared).
                             LamIN is the only *IN value that actually
                             propagates through SolveTadpoleEquations and
                             OneLoopMasses into the Higgs / neutralino tree-
                             level spectrum; m2SMIN is a consistent seed that
                             the tadpole solver overwrites.
        Block MINPAR       — one entry per *card-input* parameter, placed at
                             the index N declared in that parameter's
                             ``les_houches: [BLOCK, N]`` metadata (BLOCK in
                             ``_INPUT_SCALAR_BLOCKS``). Parameters without such
                             metadata are excluded (see module docstring) —
                             NOT enumerated by declaration order (the pre-fix
                             bug that misplaced BSM inputs to indices 24-27).
        Block BSMPARAMSIN  — same entries as MINPAR; SARAH's Boundaries branch
                             reads these through ``Read_BSMPARAMSIN`` into the
                             per-parameter ``<name>IN`` variables.
        Block SPHENOINPUT  — NOT generated here; callers must append from SARAH
                             output (see run_spheno.py which reads the SARAH-
                             generated block).

    Args:
        spec: A ModelSpec dict (loaded from spec.yaml).
        overrides: Optional dict mapping parameter name → override value.

    Returns:
        The full LesHouches input string.
        Callers append Block SPHENOINPUT separately.
    """
    overrides = overrides or {}
    sections: list[str] = [
        _MODSEL_LINES,
        _SMINPUTS_LINES,
        _GAUGEIN_LINES,
        _HMIXIN_LINES,
        _SMIN_LINES,
    ]

    params = spec.get("parameters", [])
    indices = input_scalar_params(spec)  # {name: index}, honours les_houches
    # Build rows keyed by declared index so MINPAR/BSMPARAMSIN come out sorted
    # (1..N) regardless of the parameter's position in spec.parameters.
    by_name = {p["name"]: p for p in params}
    rows: dict[int, tuple[str, float, str]] = {}
    for name, idx in indices.items():
        param = by_name[name]
        value = overrides.get(name, param.get("default", 0.0))
        latex = param.get("latex", name)
        rows[idx] = (name, value, latex)

    if rows:
        minpar_lines = ["Block MINPAR"]
        bsm_lines = ["Block BSMPARAMSIN"]
        for idx in sorted(rows):
            name, value, latex = rows[idx]
            minpar_lines.append(
                f"   {idx}   {value:E}   # {name} ({latex})"
            )
            # SARAH-generated Boundaries_<Name>.f90 overwrites the
            # MINPAR-read parameters with ``<name>IN`` values in its
            # HighScaleModel.LOW branch, which is the branch
            # ``SPheno<Name>.f90`` pins via ``HighScaleModel = "LOW"``.
            # The ``<name>IN`` values come from ``Block BSMPARAMSIN`` —
            # if we omit that block, ``MSIN`` / ``MPsiIN`` / etc. stay
            # at their module-level zero default and Block MASS reports
            # every BSM eigenstate as 0. Duplicate the MINPAR values
            # here so the EWSB-scale input flows through the LOW branch.
            bsm_lines.append(
                f"   {idx}   {value:E}   # {name} ({latex})"
            )
        sections.append("\n".join(minpar_lines) + "\n")
        sections.append("\n".join(bsm_lines) + "\n")

    return "\n".join(sections)


def patch_minpar(text: str, params: dict[str, float]) -> str:
    """Patch MINPAR entries in an existing LesHouches card by name lookup.

    Looks for comment annotations of the form `# <name>` or `# <name> (...)` on
    MINPAR data lines, then replaces the numeric value on matching lines.

    Only lines inside Block MINPAR are modified. Other blocks are left unchanged.

    Args:
        text: Full LesHouches input card text.
        params: Dict mapping parameter name → new value.

    Returns:
        Patched card text.
    """
    if not params:
        return text

    lines = text.splitlines(keepends=True)
    in_minpar = False
    result: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect block transitions
        block_match = re.match(r"^Block\s+(\S+)", stripped, re.IGNORECASE)
        if block_match:
            in_minpar = block_match.group(1).upper() == "MINPAR"
            result.append(line)
            continue

        if in_minpar and stripped and not stripped.startswith("#"):
            # Try to match: <idx>  <value>  # <name> [...]
            m = re.match(
                r"^(\s*\d+\s+)([0-9Ee.+\-]+)(\s+#\s*)(\S+)(.*)",
                line
            )
            if m:
                pre_idx, _old_val, hash_part, name_in_comment, rest = (
                    m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
                )
                # Strip trailing parenthetical from the name token to get bare name
                bare_name = re.sub(r"\(.*", "", name_in_comment).strip()
                if bare_name in params:
                    new_val = params[bare_name]
                    line = f"{pre_idx}{new_val:E}{hash_part}{name_in_comment}{rest}\n"

        result.append(line)

    return "".join(result)


def _load_spec(spec_path: Path) -> dict:
    """Load a spec YAML file. Requires pyyaml."""
    try:
        import yaml
    except ImportError:
        print("error: pyyaml required to load spec files", file=sys.stderr)
        sys.exit(1)
    with open(spec_path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate a LesHouches input card from a ModelSpec YAML."
    )
    parser.add_argument("spec_yaml", help="Path to spec.yaml")
    parser.add_argument(
        "--override", action="append", default=[],
        metavar="NAME=VALUE",
        help="Override a MINPAR parameter value (repeatable)."
    )
    args = parser.parse_args()

    spec = _load_spec(Path(args.spec_yaml))
    overrides: dict[str, float] = {}
    for kv in args.override:
        if "=" not in kv:
            print(f"error: --override must be NAME=VALUE, got: {kv!r}", file=sys.stderr)
            sys.exit(2)
        k, v = kv.split("=", 1)
        try:
            overrides[k.strip()] = float(v.strip())
        except ValueError:
            print(f"error: invalid value for {k!r}: {v!r}", file=sys.stderr)
            sys.exit(2)

    print(build(spec, overrides))
