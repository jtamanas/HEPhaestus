"""test_fresh_recompute.py — Task 1a: runner forces a fresh DD recompute.

FAILS if the fresh-by-default behavior is reverted: a stale output dir must be
cleared before a MadDM run so a direct-detection rerun cannot reuse compiled/
cached DD matrix elements that ignore param-card changes (the frozen-SI hazard).
"""
from __future__ import annotations

from pathlib import Path

import pytest

import maddm_run


def _seed_stale_dir(tmp_path: Path) -> Path:
    """Create an output dir carrying 'previously compiled' stale state."""
    out = tmp_path / "maddm_out"
    (out / "SubProcesses").mkdir(parents=True)
    stale = out / "SubProcesses" / "matrix_dd.o"
    stale.write_text("STALE COMPILED DD STATE")
    return out


def test_generate_maddm_script_clears_stale_dir_by_default(tmp_path):
    """fresh defaults to True: the pre-existing output dir is wiped."""
    out = _seed_stale_dir(tmp_path)
    assert out.exists()

    script = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="Chi1",
        out_dir=out,
        observables=["direct_detection"],
    )
    # The stale directory (and its compiled artifact) must be gone so MG5's
    # `output` recreates it and MadDM recompiles from the current param card.
    assert not out.exists(), "fresh=True must rmtree the stale output dir"
    assert isinstance(script, str)
    assert f"output {out}" in script
    assert "launch -f" in script


def test_prepare_output_dir_removes_dir(tmp_path):
    out = _seed_stale_dir(tmp_path)
    maddm_run.prepare_output_dir(out, fresh=True)
    assert not out.exists()


def test_fresh_false_preserves_dir(tmp_path):
    """Backward-compatible opt-out: fresh=False leaves the dir untouched."""
    out = _seed_stale_dir(tmp_path)
    script = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="chi1",
        out_dir=out,
        observables=["direct_detection"],
        fresh=False,
    )
    assert out.exists(), "fresh=False must NOT clear the dir"
    assert (out / "SubProcesses" / "matrix_dd.o").exists()
    assert isinstance(script, str)


def test_prepare_output_dir_safe_when_absent(tmp_path):
    """Clearing a non-existent dir is a no-op, never raises."""
    out = tmp_path / "does_not_exist"
    maddm_run.prepare_output_dir(out, fresh=True)  # must not raise
    assert not out.exists()


def test_split_path_also_clears(tmp_path):
    """The split-for-overlay path clears too (both callers are covered)."""
    out = _seed_stale_dir(tmp_path)
    setup, launch = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="chi1",
        out_dir=out,
        observables=["direct_detection"],
        split_for_param_overlay=True,
    )
    assert not out.exists()
    assert f"output {out}" in setup
    assert f"launch {out} -f" in launch
