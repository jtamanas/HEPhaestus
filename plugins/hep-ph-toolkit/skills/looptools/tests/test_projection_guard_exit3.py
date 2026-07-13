"""
test_projection_guard_exit3.py — RUNTIME-driven Exit[3] discipline for the
rotated-complete instrument guards (DESIGN-ITEM4-AMENDMENT2.md Ruling 1 +
DESIGN-ITEM4-AMENDMENT2R1.md).

These tests actually DRIVE the guard code paths via
scripts/run_projection_guard_check.wls — referenceBasisGuards /
projectOperators / projInstrumentAssert, the SAME functions run_eval_sd.wls
calls — they do not source-grep for Exit[3] (the F5 discipline).

Gated ONLY on wolframscript being present: the instrument is pure spinor
numerics (no LoopTools MathLink, no FormCalc).

Modes and required outcomes:
  rank-deficient   -> rc 3, SD-PROJECTION-BASIS-RANK-DEFICIENT, and the exact
                      linear-combination column is NAMED (the D_Vq_Ac ==
                      D_Aq_Vc defect class from the PR #35 re-review)
  null-column      -> rc 3, SD-PROJECTION-BASIS-ILLCONDITIONED naming the null
                      column (the 7-forward-null-pseudoscalar class)
  collinear        -> rc 3, SD-PROJECTION-BASIS-ILLCONDITIONED naming the pair
  illconditioned   -> rc 3, SD-PROJECTION-BASIS-ILLCONDITIONED with cond value
  unidentifiable   -> rc 3, SD-PROJECTION-BASIS-UNIDENTIFIABLE (driven with
                      Block-adjusted bars — see the runner's documented
                      rationale: a natural identifiability failure sits behind
                      the cond bar)
  rotation-inexact -> rc 3, SD-FIERZ-ROTATION-INEXACT via a WRONG-SIGN
                      fierzDress injection (proves the guard compares two
                      independent evaluations of the Majorana rotation
                      identity, phase convention included)
  monomial-out-of-span -> rc 3, SD-PROJECTION-MONOMIAL-OUT-OF-SPAN naming a
                      single-barred-chi crossed monomial that is neither
                      rotatable nor plain-Fierz-reachable
  pass             -> rc 0 on a synthetic amplitude with a GENUINE
                      Majorana-crossed pair: rotation + all pre-fit guards +
                      the per-monomial diagnostic green end-to-end at the
                      canonical masses.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
RUNNER = SCRIPTS_DIR / "run_projection_guard_check.wls"

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        shutil.which("wolframscript") is None,
        reason="wolframscript not on PATH (bare kernel is all this needs)",
    ),
]


def _run(mode: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["wolframscript", "-script", str(RUNNER), mode],
        capture_output=True, text=True, timeout=560,
    )


@pytest.mark.parametrize(
    "mode,marker",
    [
        ("rank-deficient", "SD-PROJECTION-BASIS-RANK-DEFICIENT"),
        ("null-column", "SD-PROJECTION-BASIS-ILLCONDITIONED"),
        ("collinear", "SD-PROJECTION-BASIS-ILLCONDITIONED"),
        ("illconditioned", "SD-PROJECTION-BASIS-ILLCONDITIONED"),
        ("unidentifiable", "SD-PROJECTION-BASIS-UNIDENTIFIABLE"),
        ("rotation-inexact", "SD-FIERZ-ROTATION-INEXACT"),
        ("monomial-out-of-span", "SD-PROJECTION-MONOMIAL-OUT-OF-SPAN"),
    ],
)
def test_guard_fires_with_exit_3_and_marker(mode, marker):
    res = _run(mode)
    assert res.returncode == 3, (
        f"{mode}: expected Exit[3], got rc={res.returncode}\n"
        f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    )
    assert marker in res.stderr, (
        f"{mode}: marker {marker!r} missing from stderr:\n{res.stderr}"
    )


def test_rank_deficient_names_the_null_space_combination():
    """AMENDMENT2 Ruling 1 guard 1: the failure must NAME the null-space
    combination, not just report a rank number."""
    res = _run("rank-deficient")
    assert res.returncode == 3
    assert "null-space combinations" in res.stderr, res.stderr
    assert "c6combo" in res.stderr, res.stderr


def test_null_column_is_named():
    res = _run("null-column")
    assert res.returncode == 3
    assert "cNULL" in res.stderr, res.stderr


def test_out_of_span_monomial_is_named():
    """probe8-made-permanent: the failing monomial is named, with both the
    contribution and the raw in-span residual in the marker line."""
    res = _run("monomial-out-of-span")
    assert res.returncode == 3
    assert "FA*FX" in res.stderr, res.stderr
    assert "raw in-span residual" in res.stderr, res.stderr


def test_pass_mode_runs_green_end_to_end():
    res = _run("pass")
    assert res.returncode == 0, (
        f"pass: expected Exit[0], got rc={res.returncode}\n"
        f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    )
    assert "rank 256/256" in res.stdout, res.stdout
    for marker in (
        "SD-FIERZ-ROTATION-INEXACT",
        "SD-PROJECTION-BASIS-RANK-DEFICIENT",
        "SD-PROJECTION-BASIS-ILLCONDITIONED",
        "SD-PROJECTION-BASIS-UNIDENTIFIABLE",
        "SD-PROJECTION-MONOMIAL-OUT-OF-SPAN",
    ):
        assert marker not in res.stderr
