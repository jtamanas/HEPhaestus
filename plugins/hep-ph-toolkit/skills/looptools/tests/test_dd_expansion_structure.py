"""
test_dd_expansion_structure.py — plain-environment (NO Wolfram) structural tests
for the box DD-expansion (sd_dd_expansion.wl) wiring and guards.  These keep the
default suite meaningful: they assert the module is committed, correctly wired
into run_eval_sd.wls, that the loud guards + blocker-catalog entries exist, and
that triangle-continuity holds BY CONSTRUCTION (the expansion touches only D0i
box heads, never the C0i/B0i triangle/bubble heads).

Everything here is source/registry inspection — no kernel required — so a wrong
wiring surfaces in the default `python -m pytest` run, not only under the gated
HEPPH_RUN_WOLFRAM_TESTS smoke.  The Exit[3] paths themselves are RUNTIME-driven
in test_dd_guard_exit3.py (review F5: grepping for Exit[3] proves nothing).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
SHARED_DIR = TESTS_DIR.parent.parent / "_shared"
REPO_ROOT = TESTS_DIR.parent.parent.parent.parent.parent
EVAL_DIR = REPO_ROOT / "eval" / "2506.19062_wimps_blind_spots"
DESIGN_DOC = EVAL_DIR / "DESIGN-ITEM4.md"
AMENDMENT_DOC = EVAL_DIR / "DESIGN-ITEM4-AMENDMENT.md"

MODULE = SCRIPTS_DIR / "sd_dd_expansion.wl"
DRIVER = SCRIPTS_DIR / "run_eval_sd.wls"
PROJECTION = SCRIPTS_DIR / "sd_projection.wl"
CHECK_RUNNER = SCRIPTS_DIR / "run_dd_expansion_check.wls"
GUARD_RUNNER = SCRIPTS_DIR / "run_dd_guard_check.wls"
CATALOG = SHARED_DIR / "blocker_catalog.yaml"


def _read(p: Path) -> str:
    return p.read_text()


# ---------------------------------------------------------------- assets present
def test_module_and_runners_committed():
    assert MODULE.exists(), "sd_dd_expansion.wl must be committed"
    assert CHECK_RUNNER.exists(), "run_dd_expansion_check.wls (A1-V/F2 runner) must be committed"
    assert GUARD_RUNNER.exists(), "run_dd_guard_check.wls (F5 exit-3 driver) must be committed"


def test_design_doc_committed():
    """DESIGN-ITEM4.md is part of this PR (like STEP3-DESIGN.md was)."""
    assert DESIGN_DOC.exists(), "DESIGN-ITEM4.md must be committed into the eval dir"
    txt = _read(DESIGN_DOC)
    for decision in ("Decision A1", "Decision A2", "Decision A3", "Decision A6"):
        assert decision in txt, f"{decision} missing from committed design doc"


def test_amendment_doc_committed():
    """DESIGN-ITEM4-AMENDMENT.md (post-review rulings) ships next to the design
    doc — the code cites it for the F4 excision, F2 contracted-level check and
    the Ruling-3 amended acceptance bars."""
    assert AMENDMENT_DOC.exists(), \
        "DESIGN-ITEM4-AMENDMENT.md must be committed into the eval dir"
    txt = _read(AMENDMENT_DOC)
    for marker in ("Ruling 1", "Ruling 3", "F4", "F2"):
        assert marker in txt, f"{marker} missing from committed amendment doc"


# ---------------------------------------------------------------- module content
def test_module_defines_reduction_api():
    src = _read(MODULE)
    for sym in ("boxGram", "boxCollinearOffsets", "boxDegeneracyMonitor",
                "ddIntOffsetExact", "ddIntU", "ddBasisComponents",
                "ddTraceScalar", "ddBoxHead", "ddExpandRule",
                "ddTensorSurvivors", "ddBoxSectorClean", "ddAssertNoSurvivors",
                "ddMonitorSummary", "writeAmpDdSidecar"):
        assert sym in src, f"sd_dd_expansion.wl must define {sym}"


def test_derivative_branch_excised():
    """PR #35 review F4 + amendment stage-0c ruling: the finite-difference
    mass-derivative branch was EXCISED (it differentiated an integral from which
    the perturbed propagator had already been removed — a silent ~0).  The
    doubled-offset case must instead hard-error."""
    src = _read(MODULE)
    for dead in ("ddMassDerivInt", "ddCentralDeriv", "$ddDerivDiagnostics",
                 "$ddDerivTol", "SD-DD-DERIVATIVE-NONCONVERGENT"):
        assert dead not in src, f"excised symbol {dead} must not reappear (F4)"
    assert "SD-DD-DOUBLED-OFFSET-UNSUPPORTED" in src, \
        "doubled-offset case must hard-error loudly (amendment F4 ruling)"


def test_module_reads_no_looptools_symbol_at_read_time():
    """The header contract: the file Get[]s cleanly; it must NOT Install LoopTools
    or Needs FormCalc itself (the common include does that first)."""
    src = _read(MODULE)
    # actual install/needs CALLS take an argument; the header comment mentions
    # "Install[]ed" in prose, which must not trip this.
    assert "Install[$" not in src and 'Install["' not in src, \
        "module must not Install LoopTools (driver/common does)"
    assert 'Needs["FormCalc`"]' not in src, "module must not Needs FormCalc"


def test_expand_rule_touches_only_boxes_triangle_continuity_by_construction():
    """Triangle-continuity (validation #2), proven structurally: the expansion
    rewrite is exactly `D0i -> ddBoxHead`, so C0i (triangle) and B0i (bubble) heads
    — which carry the item-3 triangle-only content C_scalar = -1.28e-7 — are left
    byte-identical.  A rewrite that also matched C0i/B0i would break this."""
    src = _read(MODULE)
    assert "ddExpandRule = D0i -> ddBoxHead" in src, \
        "ddExpandRule must rewrite ONLY the box head D0i -> ddBoxHead"
    # the scalar box passes through; only tensor ids are reduced
    assert "ddBoxHead[dd0, args__] := D0i[dd0, args]" in src, \
        "dd0 (scalar box) must pass through untouched"


def test_no_retracted_velocity_gap_narrative():
    """PR #35 review F1 + re-review RN1: the 'residual ~= 1.0 is the A-R2
    velocity gap; round-2 O(v) twist-2 resolves it' claim was empirically
    refuted and RETRACTED — including the HYPHENATED spelling the first grep
    missed (RN1).  Likewise the round-2 'confirms/supports frozen-kinematics'
    reading was refuted by the second re-review (fixed scalar coefficients
    cannot create content orthogonal to a complete local basis); the shipped
    sources may DESCRIBE the retraction but must not assert the claim."""
    for path in (MODULE, DRIVER, PROJECTION, CHECK_RUNNER, GUARD_RUNNER):
        src = _read(path)
        for phrase in ("velocity gap", "velocity-gap", "A-R2 velocity",
                       "resolves it", "confirms the frozen-kinematics",
                       "confirms frozen-kinematics",
                       "supports frozen-kinematics",
                       "supports the frozen-kinematics"):
            assert phrase not in src, \
                f"retracted narrative phrase {phrase!r} found in {path.name}"


# ---------------------------------------------------------------- driver wiring
def test_driver_loads_module_and_applies_expansion():
    src = _read(DRIVER)
    assert 'Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]]' in src, \
        "run_eval_sd.wls must Get[] sd_dd_expansion.wl"
    assert "ddExpandRule" in src, "driver must apply the ddExpandRule interception"
    assert "$ddExpansion" in src, "driver must gate the expansion on $ddExpansion"


def test_driver_guards_at_both_stages():
    """Review F5: the survivor check must run on the SYMBOLIC amplitude BEFORE
    numericisation (a numeric-args tensor D0i auto-evaluates through the
    MathLink to a Gram-poled number and is invisible afterwards), and again on
    the evaluated amplitude for inert ddBoxHead leftovers.  Both go through
    ddAssertNoSurvivors — the same function test_dd_guard_exit3.py drives to a
    real Exit[3]."""
    src = _read(DRIVER)
    assert 'ddAssertNoSurvivors[ddTerms, "symbolic-pre-eval-terms"]' in src, \
        "symbolic-stage guard on the term bodies is load-bearing (F5)"
    assert 'ddAssertNoSurvivors[ddSubexpr, "symbolic-pre-eval-subexpr"]' in src, \
        "symbolic-stage guard on the Subexpr table is load-bearing (F5)"
    assert 'ddAssertNoSurvivors[Mnum, "evaluated"]' in src, \
        "evaluated-stage guard catches inert symbolic leftovers"


def test_module_guard_emits_marker_and_exit3():
    """The marker + Exit[3] live in ddAssertNoSurvivors (module), shared by the
    driver and the runtime guard test."""
    src = _read(MODULE)
    idx = src.index("SD-DD-EXPANSION-INCOMPLETE stage=")
    assert "Exit[3]" in src[idx:idx + 2000], \
        "ddAssertNoSurvivors must Exit[3] on survivors"


def test_driver_writes_sidecar_and_gram_monitor():
    src = _read(DRIVER)
    assert "writeAmpDdSidecar" in src, "driver must persist the amp_dd.m sidecar (Decision A3)"
    assert "amp_dd.m" in src, "sidecar filename must be amp_dd.m"
    assert "GRAM-MONITOR" in src, "driver must emit the Gram/degeneracy monitor line"
    assert '"dd_expansion"' in src, "eval output metadata must carry a dd_expansion block"


def test_driver_enforces_amended_ruling3_bars():
    """AMENDMENT3 Ruling 1/2 driver gates: full-basis completeness stays; the
    SI-extraction gate is SUPERSEDED (history note must remain, si_shift is
    report-only); velocity stability moves to the green-guarded production
    legs + the reopen adjudication; the A5 contraction and its named refusals
    exist."""
    src = _read(DRIVER)
    for marker in ("SD-PROJECTION-INCOMPLETE", "SD-VELOCITY-UNSTABLE",
                   '"a6_amended"',
                   # superseded gate: history note + report-only line
                   "SD-SI-EXTRACTION-UNSTABLE", "REPORT ONLY",
                   # AMENDMENT3 production path
                   "SD-KINEMATICS-REOPEN-TRIGGERED", "SD-TRIANGLE-SECTOR-EMPTY",
                   "sigma_SI_cm2_with_CG", "sigma_SI_cm2_without_CG",
                   "looptools_sd_coefficients/v2", "productionVLeg",
                   "threeOpFit", "C_Q_universal"):
        assert marker in src, f"driver must carry {marker} (AMENDMENT3)"
    assert "looptools_sd_coefficients/v1" not in src, \
        "schema must be bumped to /v2 (nucleon block added)"
    assert '"nucleon_matching" -> "deferred_item4"' not in src, \
        "nucleon matching is no longer deferred (AMENDMENT3 Ruling 1)"


# ---------------------------------------------------------------- projection layer
def test_projection_reference_instrument_is_diagnostics_only():
    """AMENDMENT2 Rulings 1/2: the ROTATED-COMPLETE reference instrument (the
    27-column contracted basis and its $opRefsDiag table are GONE — rank 12 of
    27, re-review) is measurement instrumentation.  Only {C_q, C_q^(1,2), C_G}
    may flow to nucleon matching; instrument coefficients ship as sidecar
    diagnostics."""
    src = _read(PROJECTION)
    assert "$opRefsDiag" not in src, \
        "the retired rank-deficient 27-column basis must not come back"
    assert "$refNames" in src and "refRow[" in src, \
        "the 256-column line-product dictionary must be defined"
    assert "referenceBasisGuards" in src, \
        "fatal pre-fit guards must be defined (AMENDMENT2 Ruling 1)"
    assert "crossedRotValue" in src and "crossedRotAlgebraic" in src, \
        "the Majorana C-conjugate rotation must be machine-evaluated both ways"
    assert "rotated-complete" in src.lower(), \
        "the instrument label is 'rotated-complete' (Ruling 4 rename)"
    assert "full_basis_completeness_rel_residual" in src
    assert "absorbed_norm_shares" in src
    assert "$fullCompletenessTol" in src
    assert "$fierzRotationTol" in src and "$monomialContribTol" in src
    # si_shift stays MEASURED (report-only after AMENDMENT3 Ruling 1)
    assert "si_shift_rel" in src, \
        "3-op-vs-full C_scalar shift must be measured (continuity report)"
    # AMENDMENT3 Ruling 1 production machinery
    assert "$opRefs2" in src and "twist2Ref1" in src and "twist2Ref2" in src, \
        "contracted Hisano twist-2 reference operators must be defined"
    assert "C_twist2_sum" in src and "C_twist2_dif" in src, \
        "the orthogonalized sum/dif twist-2 fit basis must be defined"
    assert "forwardScalarInstrument" in src and "productionVLeg" in src
    assert "SD-SI-CROSS-INSTRUMENT-DISAGREE" in src, \
        "the three-instrument shipping guard must be defined"
    assert "$crossInstrTolRel" in src and "$crossInstrTolAbs" in src


def test_projection_instrument_guard_markers_and_exit3():
    """Every instrument guard has a named marker, and the shared assert
    (projInstrumentAssert, called by the driver) carries the Exit[3]."""
    src = _read(PROJECTION)
    for marker in (
        "SD-FIERZ-ROTATION-INEXACT",
        "SD-PROJECTION-BASIS-RANK-DEFICIENT",
        "SD-PROJECTION-BASIS-ILLCONDITIONED",
        "SD-PROJECTION-BASIS-UNIDENTIFIABLE",
        "SD-PROJECTION-MONOMIAL-OUT-OF-SPAN",
    ):
        assert marker in src, f"instrument marker {marker} must be defined"
    idx = src.index("projInstrumentAssert[proj_Association]")
    assert "Exit[3]" in src[idx:idx + 600], \
        "projInstrumentAssert must Exit[3] on instrument failures"
    assert "projInstrumentAssert[proj]" in _read(DRIVER), \
        "run_eval_sd.wls must route projection failures through projInstrumentAssert"


def test_amendment2_design_docs_are_committed():
    """The round-3 rulings must live in-repo, next to the earlier design docs."""
    for doc in ("DESIGN-ITEM4-AMENDMENT2.md", "DESIGN-ITEM4-AMENDMENT2R1.md"):
        assert (EVAL_DIR / doc).exists(), f"{doc} must be committed in eval/"


# ---------------------------------------------------------------- blocker catalog
@pytest.fixture(scope="module")
def catalog():
    return yaml.safe_load(_read(CATALOG))["blockers"]


@pytest.mark.parametrize("code", [
    "SD_DD_EXPANSION_INCOMPLETE",
    "SD_DD_DOUBLED_OFFSET_UNSUPPORTED",
    "SD_SI_EXTRACTION_UNSTABLE",
    "SD_VELOCITY_UNSTABLE",
    "SD_FIERZ_ROTATION_INEXACT",
    "SD_PROJECTION_BASIS_RANK_DEFICIENT",
    "SD_PROJECTION_BASIS_ILLCONDITIONED",
    "SD_PROJECTION_BASIS_UNIDENTIFIABLE",
    "SD_PROJECTION_MONOMIAL_OUT_OF_SPAN",
    "SD_SI_CROSS_INSTRUMENT_DISAGREE",
    "SD_KINEMATICS_REOPEN_TRIGGERED",
    "SD_TRIANGLE_SECTOR_EMPTY",
])
def test_blocker_entries_registered_and_well_shaped(catalog, code):
    assert code in catalog, f"{code} must be registered in blocker_catalog.yaml"
    entry = catalog[code]
    for field in ("class", "severity", "description", "owned_by"):
        assert field in entry, f"{code} missing required field {field}"
    assert entry["owned_by"] == "looptools"
    assert entry["severity"] == "recoverable", "a loud, recoverable blocker (nothing ships)"
    assert "looptools" in entry["emitted_by"]


def test_derivative_blocker_retired(catalog):
    """The blocker for the excised branch must be gone with the branch (F4):
    leaving it registered would advertise a code that can never be emitted."""
    assert "SD_DD_DERIVATIVE_NONCONVERGENT" not in catalog


def test_incomplete_blocker_description_names_the_mechanism(catalog):
    desc = catalog["SD_DD_EXPANSION_INCOMPLETE"]["description"]
    assert "Gram" in desc, \
        "the blocker description must name the Gram-pole mechanism"
    assert "stage" in desc, "the two-stage (symbolic/evaluated) design must be described"
