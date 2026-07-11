"""test_fresh_recompute.py — Task 1a: runner forces a fresh DD recompute.

The fresh-recompute discipline (clear the output dir before MadDM reads a new
param card, so a direct-detection rerun can never reuse compiled/cached DD
matrix elements that ignore param-card changes -- the frozen-SI hazard) must
apply at RUN time, not at script-GENERATION time. Generating a script is a
pure operation on script text; it must never delete a live output directory
as a side effect (e.g. during a preview, dry run, or a script that is built
but never handed to mg5_aMC). These tests FAIL if either half of that
contract regresses: if generation stops being side-effect-free, or if the
emitted script stops carrying the cleanup line that actually performs the
fresh recompute when mg5_aMC executes it.
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


def test_generate_maddm_script_is_filesystem_side_effect_free(tmp_path):
    """Generating a script must NOT touch the filesystem at all.

    This is the core regression test for the bug this module fixes: on
    unfixed code, merely calling `generate_maddm_script` (fresh=True, the
    default) deletes a pre-existing out_dir via `prepare_output_dir` before
    ever returning the script text -- even if the script is a preview that
    is never run, or if a second generation call fires while another step
    still needs the directory. On fixed code the directory must survive
    generation untouched; the cleanup instead travels inside the returned
    script text and only fires when that script is executed by mg5_aMC.
    """
    out = _seed_stale_dir(tmp_path)
    stale_file = out / "SubProcesses" / "matrix_dd.o"
    assert out.exists()

    script = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="Chi1",
        out_dir=out,
        observables=["direct_detection"],
    )

    assert out.exists(), (
        "generate_maddm_script must be side-effect-free on the filesystem: "
        "it must not delete out_dir merely by being called"
    )
    assert stale_file.exists(), "pre-existing contents must survive generation"
    assert isinstance(script, str)
    assert f"output {out}" in script
    assert "launch -f" in script


def test_generated_script_contains_cleanup_prelude_when_fresh(tmp_path):
    """fresh=True (default): the emitted script carries the run-time cleanup.

    The deletion must be encoded as a shell-escape line inside the script
    (executed by mg5_aMC's cmd interpreter, which runs a `!`-prefixed line
    as a raw shell command), positioned immediately before `output <out_dir>`
    so it fires right when MG5 is about to need a clean directory.
    """
    out = _seed_stale_dir(tmp_path)

    script = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="Chi1",
        out_dir=out,
        observables=["direct_detection"],
    )

    lines = script.splitlines()
    cleanup_idx = next(
        i for i, line in enumerate(lines) if line.strip() == f"!rm -rf {out}"
    )
    output_idx = next(i for i, line in enumerate(lines) if line == f"output {out}")
    assert cleanup_idx < output_idx, (
        "cleanup line must appear before the `output` line so it runs first"
    )
    # Generation itself must still be a no-op on the filesystem.
    assert out.exists()


def test_generated_script_omits_cleanup_prelude_when_fresh_false(tmp_path):
    """fresh=False: no cleanup line at all -- the caller accepts reuse risk."""
    out = _seed_stale_dir(tmp_path)

    script = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="chi1",
        out_dir=out,
        observables=["direct_detection"],
        fresh=False,
    )

    assert f"!rm -rf {out}" not in script
    assert "!rm -rf" not in script
    assert out.exists(), "fresh=False must NOT clear the dir"
    assert (out / "SubProcesses" / "matrix_dd.o").exists()
    assert isinstance(script, str)


def test_prepare_output_dir_removes_dir(tmp_path):
    """prepare_output_dir remains a standalone utility for imperative callers."""
    out = _seed_stale_dir(tmp_path)
    maddm_run.prepare_output_dir(out, fresh=True)
    assert not out.exists()


def test_prepare_output_dir_safe_when_absent(tmp_path):
    """Clearing a non-existent dir is a no-op, never raises."""
    out = tmp_path / "does_not_exist"
    maddm_run.prepare_output_dir(out, fresh=True)  # must not raise
    assert not out.exists()


def test_split_path_cleanup_lives_in_setup_script(tmp_path):
    """The split-for-overlay path: cleanup belongs in the setup half.

    The setup script ends with `output <out_dir>`, so the cleanup line
    (which must run before `output`) is emitted there. The launch script is
    just `launch <out_dir> -f` and carries no cleanup. Generation is still
    side-effect-free: the pre-existing dir survives the call.
    """
    out = _seed_stale_dir(tmp_path)
    setup, launch = maddm_run.generate_maddm_script(
        ufo_path="/fake/ufo/SingletDoublet",
        dm_candidate="chi1",
        out_dir=out,
        observables=["direct_detection"],
        split_for_param_overlay=True,
    )
    assert out.exists(), "generation must not delete the dir even when split"
    assert f"!rm -rf {out}" in setup
    assert f"output {out}" in setup
    assert f"launch {out} -f" in launch
    assert "!rm -rf" not in launch
