"""
test_sd_binding.py — HERMETIC tests for the singlet-doublet eval driver
(STEP3-DESIGN.md Decision 4): binding-table completeness, model dispatch, and
the R2 projection chain-block disjointness.  No Wolfram/LoopTools required.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
SD_DRIVER = SCRIPTS_DIR / "run_eval_sd.wls"
SD_PROJ = SCRIPTS_DIR / "sd_projection.wl"


# ── Binding-table completeness ──────────────────────────────────────────────────

# The SD amplitude symbols that MUST be bound to a numeric value before any PV /
# LoopTools call.  This is the SD-side inverse of the 20-name bindGuard list
# (STEP2.md "what step 3 needs" + Decision 4 table), verified here against the
# actual mkNum substitution rules in run_eval_sd.wls — not trusted from the doc.
REQUIRED_SD_SYMBOLS = [
    # masses (SD PDG codes / Feynman-gauge Goldstones)
    "MassFChi", "MassFChiM", "Masshh", "MassAh", "MassHp",
    "MassVWp", "MassVZ", "MassFu", "MassFd",
    # mixings / couplings
    "ZN", "UM", "UP", "ZDL", "ZDR", "ZUL", "ZUR", "Yu", "Yd",
    "yh1", "yh2", "g1", "g2", "g3", "Lam", "PhaseFS", "vvSM", "CTW", "STW",
]


def _driver_src() -> str:
    return SD_DRIVER.read_text()


def test_sd_driver_exists():
    assert SD_DRIVER.exists(), "run_eval_sd.wls must be committed"
    assert SD_PROJ.exists(), "sd_projection.wl must be committed"


@pytest.mark.parametrize("sym", REQUIRED_SD_SYMBOLS)
def test_every_sd_amplitude_symbol_is_bound(sym):
    """Each SD amplitude symbol appears on the LHS of a mkNum substitution rule.

    Completeness guard: an unbound symbol would reach LoopTools non-numeric and
    abort the MathLink (the STEP2 subtask-3a failure mode).  We assert the rule
    exists in the driver source (mkNum), matching either `Sym ->` or `Sym[..] :>`.
    """
    src = _driver_src()
    # `MassFChi ->`  or  `MassFChi[i_] :>`  or  `ZN[i_, j_] :>`
    pat = re.compile(rf"\b{re.escape(sym)}\b\s*(\[[^\]]*\]\s*)?:?->|"
                     rf"\b{re.escape(sym)}\b\s*(\[[^\]]*\]\s*)?:>")
    assert pat.search(src), f"SD symbol {sym!r} is not bound in run_eval_sd.wls mkNum"


def test_znmix_phase_convention_resolved():
    """[VERIFY] resolution: ZN binds to ZNMIX + I*IMZNMIX (not ZNMIX alone)."""
    src = _driver_src()
    assert "IMZNMIX" in src, "ZN must include the imaginary part (IMZNMIX)"
    assert re.search(r'ZNMIX:.*\+\s*I\s*\*\s*Lookup\[params,\s*"IMZNMIX', src, re.S), \
        "ZN must be bound as ZNMIX + I*IMZNMIX"


def test_yh_block_resolved_bsmparams_with_minpar_fallback():
    """[VERIFY] resolution: yh1/yh2 from BSMPARAMS(3,4) with MINPAR fallback."""
    src = _driver_src()
    assert re.search(r'getParamAny\[\{"BSMPARAMS:3",\s*"MINPAR:3"\}\]', src)
    assert re.search(r'getParamAny\[\{"BSMPARAMS:4",\s*"MINPAR:4"\}\]', src)


def test_uses_shared_common_include_and_projector():
    src = _driver_src()
    assert "run_eval_common.wl" in src, "SD driver must consume the shared include"
    assert "sd_projection.wl" in src, "SD driver must use the chain-coefficient projector"


def test_no_static_spin_summed_collapse():
    """Decision 3: SD driver must NOT reuse the 2HDM+a Fsame/Fdiff spin-summed
    collapse (that folds twist-2 into scalar).  It projects F-symbolically."""
    src = _driver_src()
    assert "Fsame" not in src and "Fdiff" not in src, \
        "SD driver must not use the static spin-summed collapse (Fsame/Fdiff)"
    assert "projectOperators" in src


def test_driver_passes_abbr_table_to_projector():
    """F1 fix: the projector reads each chain's operator content from its ACTUAL
    Abbr[] WeylChain definition, so the driver must extract the abbr table and pass
    it to projectOperators (no hard-coded index blocks)."""
    src = _driver_src()
    assert re.search(r'abbrF\s*=\s*Cases\[abbr,\s*HoldPattern\[_ -> _WeylChain\]\]', src), \
        "driver must extract the Abbr[] WeylChain table"
    assert re.search(r'projectOperators\[Mnum,\s*abbrF,', src), \
        "projectOperators must receive the abbr table (F1 fix)"


def test_driver_has_completeness_guard():
    """F2 fix: the driver must fail loudly when the projection is incomplete
    (unrecognized structure / non-spanning residual), not silently drop content."""
    src = _driver_src()
    assert "SD-PROJECTION-INCOMPLETE" in src, "completeness guard must be present"
    assert "SD-PROJECTION-FAILED" in src, "structural-failure guard must be present"
    assert 'proj["completeness_ok"]' in src


# ── Model dispatch ──────────────────────────────────────────────────────────────

def _import_run_looptools():
    import importlib
    import sys
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    for stale in ("run_looptools",):
        sys.modules.pop(stale, None)
    return importlib.import_module("run_looptools")


def test_dispatch_table_maps_singlet_doublet_to_sd_driver():
    rl = _import_run_looptools()
    assert rl.MODEL_DRIVERS["2hdma"] == "run_eval.wls"
    assert rl.MODEL_DRIVERS["singlet_doublet"] == "run_eval_sd.wls"
    # SD default DM PDG is chi1 (STEP2.md).
    assert rl.MODEL_DM_PDG["singlet_doublet"] == 9958431


def test_parse_args_accepts_model_flag_default_2hdma():
    rl = _import_run_looptools()
    args = rl.parse_args(["eval", "--amp-reduced", "a.m", "--point", "p.slha"])
    assert args.model == "2hdma", "default model must stay 2hdma (byte-untouched path)"
    args_sd = rl.parse_args(
        ["eval", "--amp-reduced", "a.m", "--point", "p.slha", "--model", "singlet_doublet"])
    assert args_sd.model == "singlet_doublet"


def test_run_driver_signature_selects_driver_script():
    """run_driver must accept driver_script_name so dispatch can pick the SD driver."""
    import inspect
    rl = _import_run_looptools()
    sig = inspect.signature(rl.run_driver)
    assert "driver_script_name" in sig.parameters


# ── Projector method: real-Abbr basis-vector solve, no hard-coded blocks ────────

def test_projector_has_no_hardcoded_index_blocks():
    """F1 [MAJOR] fix: PR #31 hard-coded {F1..F4}=scalar / {F5..F8}=twist-2 index
    blocks — an UNPROVEN convention, wrong for the real SD process (whose scalar
    chains are F1,F4 (chi) + F2,F3 (quark) and whose twist-2 chains are F15,F16).
    The projector must NOT carry those contiguous-block assignments anymore."""
    src = SD_PROJ.read_text()
    assert "$scalarChains" not in src, "hard-coded $scalarChains block must be gone"
    assert "$twist2Chains" not in src, "hard-coded $twist2Chains block must be gone"
    assert "$mixedChains" not in src


def test_projector_classifies_from_real_weylchains():
    """The projector reads each chain's operator content from its ACTUAL WeylChain
    definition (fermion line + rank + chirality), via a numerical spinor-basis
    solve (Decision 3.2) — not an index block."""
    src = SD_PROJ.read_text()
    assert "classifyChain" in src and "chainClass" in src, "structural classifier required"
    assert "WeylChain" in src and "Spinor" in src, "must inspect WeylChain/Spinor structure"
    assert "LeastSquares" in src, "must solve for operator coefficients numerically"
    # signature takes the abbr table
    assert re.search(r"projectOperators\[M_,\s*abbr_List,\s*mchi_,\s*mq_,\s*vscale_:1\.0\]", src)  # vscale: amendment Ruling 3 velocity-stability knob


def test_projector_has_completeness_and_taxonomy_guards():
    """F2 [MAJOR] fix: content outside the recognized set must fail loudly, named —
    not be silently dropped with an empty residual (PR #31's silent fall-through)."""
    src = SD_PROJ.read_text()
    assert "unrecognizedChains" in src, "structural taxonomy guard required"
    assert "UNRECOGNIZED-CHAIN-STRUCTURE" in src
    assert "completeness_rel_residual" in src and "$completenessTol" in src


def test_residual_symbols_scans_function_form_subs():
    """F3 [MINOR] fix: the Sub#### guard must catch function-form Sub####[args]
    (real amp has e.g. Sub3131[I3G2,I3G4,I3G5]) — scan HEADS, not only bare
    symbols."""
    src = SD_PROJ.read_text()
    assert re.search(r"residualSymbols.*Heads\s*->\s*True", src, re.S), \
        "residualSymbols must scan heads (Heads -> True) to catch Sub####[args]"
