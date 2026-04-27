"""
test_run_point_cwd.py — regression test for SPheno cwd isolation.

Background
----------
SPheno writes several auxiliary output files (BR_*.dat, *_GammaTot.dat,
effC.dat, …) into its *current working directory* while it runs. Before
the cwd fix, ``run_point.run`` invoked the SPheno binary via
``subprocess.run`` without passing ``cwd=out_dir``, so these droppings
ended up wherever the caller happened to be — typically the repo root
or the user's demo output dir — instead of landing in the per-run
``out_dir`` alongside ``LesHouches.in`` and ``SPheno.spc``.

This test drives ``run_point.run`` with a *stub* SPheno binary (a shell
script installed at the exact ``state_root/models/<name>/spheno_bin``
location that run_point probes). The stub:

    1. Writes a few mock droppings to its own ``$PWD`` (mimicking real
       SPheno behaviour), and
    2. Copies the clean_spectrum.spc fixture to the second positional
       argument (which run_point passes as an absolute path).

We then assert:

    - the droppings land in ``out_dir`` (not in the test's cwd), and
    - the test's cwd is *clean* of those droppings after the call.

Isolation: uses HEPPH_STATE_ROOT / XDG_CONFIG_HOME per the project
invariant.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_CLEAN_FIXTURE = _HERE / "fixtures" / "slha" / "clean_spectrum.spc"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def run_point_mod():
    return _load("run_point", _SCRIPTS / "run_point.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# The list of dropping filenames we expect SPheno to emit into cwd.
# Matches what 1fb8ad8 added to .gitignore.
_EXPECTED_DROPPINGS = [
    "BR_H_NP.dat",
    "BR_Hplus.dat",
    "BR_t.dat",
    "MH_GammaTot.dat",
    "MHplus_GammaTot.dat",
    "effC.dat",
]


def _install_stub_spheno(state_root: Path, model_name: str, sarah_name: str) -> Path:
    """Install a shell-script stub at the location run_point probes.

    The stub writes the expected droppings into its ``$PWD`` and copies
    the clean_spectrum.spc fixture to ``$2`` (the SPheno.spc path). It
    exits 0.
    """
    bin_dir = state_root / "models" / model_name / "spheno_bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub_path = bin_dir / f"SPheno{sarah_name}"

    droppings_cmds = "\n".join(
        f'printf "stub" > "$PWD/{name}"' for name in _EXPECTED_DROPPINGS
    )
    # $2 is an absolute path (run_point resolves before passing); write
    # clean_spectrum.spc contents to it so run_point's SLHA parse succeeds.
    stub_body = f"""#!/usr/bin/env bash
set -e
{droppings_cmds}
cp "{_CLEAN_FIXTURE}" "$2"
exit 0
"""
    stub_path.write_text(stub_body)
    stub_path.chmod(stub_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return stub_path


class TestDroppingsLandInOutDir:
    """After the cwd fix, SPheno's droppings must land in out_dir, not cwd."""

    def test_droppings_land_in_out_dir(self, run_point_mod, tmp_path, monkeypatch):
        # singlet_doublet → SingletDoublet per _shared/sarah_name.py rules.
        model_name = "singlet_doublet"
        sarah_name = "SingletDoublet"

        state_root = Path(os.environ["HEPPH_STATE_ROOT"])
        _install_stub_spheno(state_root, model_name, sarah_name)

        # Set the test's cwd to a fresh dir we can inspect afterwards to
        # confirm nothing was written there. This is the dir SPheno
        # *would* have polluted under the old cwd=caller-cwd behaviour.
        caller_cwd = tmp_path / "caller_cwd"
        caller_cwd.mkdir()
        monkeypatch.chdir(caller_cwd)

        # Stage an input card — run_point expects a real LesHouches.in
        # that it can copy into out_dir.
        input_card = tmp_path / "staged_lh" / "LesHouches.in"
        input_card.parent.mkdir()
        input_card.write_text("Block MODSEL\n   1   0\n")

        out_dir = tmp_path / "runs" / "20260101T000000Z"
        result = run_point_mod.run(
            model_name=model_name,
            input_card=input_card,
            out_dir=out_dir,
        )

        # Sanity: the stub succeeded and the SLHA parse produced ok.
        assert result["status"] == "ok", result
        assert (out_dir / "SPheno.spc").exists()

        # Primary assertion: every dropping landed in out_dir.
        for name in _EXPECTED_DROPPINGS:
            assert (out_dir / name).exists(), (
                f"Dropping {name!r} did not land in out_dir {out_dir!s}. "
                f"Contents: {sorted(p.name for p in out_dir.iterdir())}"
            )

        # Defense-in-depth: the caller's cwd must be clean.
        caller_leaks = sorted(p.name for p in caller_cwd.iterdir())
        assert caller_leaks == [], (
            f"SPheno polluted caller cwd with: {caller_leaks}. "
            "cwd=out_dir argument is missing from subprocess.run."
        )

    def test_droppings_do_not_pollute_parent(self, run_point_mod, tmp_path, monkeypatch):
        """Extra paranoia: no dropping leaks up to out_dir's parent either."""
        model_name = "singlet_doublet"
        sarah_name = "SingletDoublet"
        state_root = Path(os.environ["HEPPH_STATE_ROOT"])
        _install_stub_spheno(state_root, model_name, sarah_name)

        caller_cwd = tmp_path / "caller_cwd"
        caller_cwd.mkdir()
        monkeypatch.chdir(caller_cwd)

        input_card = tmp_path / "LesHouches.in"
        input_card.write_text("Block MODSEL\n   1   0\n")

        parent = tmp_path / "runs"
        out_dir = parent / "20260101T000000Z"
        run_point_mod.run(
            model_name=model_name,
            input_card=input_card,
            out_dir=out_dir,
        )

        parent_entries = sorted(p.name for p in parent.iterdir())
        assert parent_entries == ["20260101T000000Z"], (
            f"Expected parent to contain only the run dir, got: {parent_entries}"
        )
