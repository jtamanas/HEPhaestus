"""
test_dd_guard_exit3.py — RUNTIME-driven Exit[3] discipline for the box
DD-expansion guards (PR #35 review F5 / DESIGN-ITEM4-AMENDMENT.md stage-0c).

These tests actually DRIVE the guard code paths via
scripts/run_dd_guard_check.wls — they do not source-grep for Exit[3] (review
finding F5: a source grep cannot prove the guard fires, and a numeric-args
D0i auto-evaluates through an Install[]ed MathLink into a Gram-poled NUMBER
before any pattern can match it, which is why the symbolic pre-mkNum stage
exists at all).

Gated ONLY on wolframscript being present: the guard is pure structure and
needs no LoopTools MathLink, no FormCalc, and no HEPPH_RUN_WOLFRAM_TESTS
opt-in beyond the kernel itself being available.  (Same single-gate pattern
as the doubled-offset hard error: a bare kernel suffices.)

Modes and required outcomes:
  survivor -> rc 3, stderr contains SD-DD-EXPANSION-INCOMPLETE
              (raw tensor D0i with SYMBOLIC args at the pre-mkNum stage)
  boxhead  -> rc 3, stderr contains SD-DD-EXPANSION-INCOMPLETE
              (inert ddBoxHead leftover at the evaluated stage)
  doubled  -> rc 3, stderr contains SD-DD-DOUBLED-OFFSET-UNSUPPORTED
              (coincident collinear offsets: excised-branch hard error, F4)
  clean    -> rc 0 (scalar dd0 passthrough + triangles must NOT trip anything)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
RUNNER = SCRIPTS_DIR / "run_dd_guard_check.wls"

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
        capture_output=True, text=True, timeout=300,
    )


@pytest.mark.parametrize(
    "mode,marker",
    [
        ("survivor", "SD-DD-EXPANSION-INCOMPLETE"),
        ("boxhead", "SD-DD-EXPANSION-INCOMPLETE"),
        ("doubled", "SD-DD-DOUBLED-OFFSET-UNSUPPORTED"),
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


def test_guard_stage_is_named_in_survivor_marker():
    """The blocker line must carry the stage tag so a log reader can tell the
    symbolic pre-mkNum stage from the evaluated stage."""
    res = _run("survivor")
    assert res.returncode == 3
    assert "stage=symbolic-pre-eval-terms" in res.stderr, res.stderr


def test_clean_expression_passes_both_stages():
    res = _run("clean")
    assert res.returncode == 0, (
        f"clean: expected Exit[0], got rc={res.returncode}\n"
        f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    )
    assert "SD-DD-EXPANSION-INCOMPLETE" not in res.stderr
    assert "SD-DD-DOUBLED-OFFSET-UNSUPPORTED" not in res.stderr


def test_rewritten_symbolic_state_passes_symbolic_stage():
    """Regression for a LIVE false positive: after the D0i -> ddBoxHead rewrite
    the pre-eval amplitude legitimately carries inert ddBoxHead[dd_ij, <symbolic
    args>] heads (they numericize only under mkNum), so the SYMBOLIC-stage guard
    must treat only raw D0i tensors as survivors.  The first stage-unaware guard
    Exit[3]'d every valid canonical run; this mode pins the fix."""
    res = _run("symbolic-clean")
    assert res.returncode == 0, (
        f"symbolic-clean: expected Exit[0], got rc={res.returncode}\n"
        f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    )
    assert "SD-DD-EXPANSION-INCOMPLETE" not in res.stderr
