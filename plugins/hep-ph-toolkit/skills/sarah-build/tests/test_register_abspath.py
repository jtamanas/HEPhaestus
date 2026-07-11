"""test_register_abspath.py — _register_model_safe must persist ABSOLUTE paths.

Background (PR #21, θ-scan friction #2): a demo replay run with a relative
``--model-dir ./demo_output/singlet-doublet/`` used to register a CWD-relative,
worktree-scoped ``config.models.<name>.ufo`` that (a) broke when the recording
worktree was deleted and (b) MG5 ``import model`` rejected (hyphenated relative
path mis-tokenized as a flag). The register site now anchors both ``ufo`` and
``spec`` with os.path.abspath before persisting.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"


@pytest.fixture()
def run_sarah_mod(tmp_path, monkeypatch):
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    (tmp_path / "state").mkdir()
    (tmp_path / "cfg").mkdir()
    spec = importlib.util.spec_from_file_location("run_sarah", _SCRIPTS / "run_sarah.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # run_sarah imported config_helpers at module load; re-point its roots at
    # the temp env (documented test hook).
    mod.config_helpers._reload_roots()
    return mod


def test_register_model_safe_persists_absolute_paths(run_sarah_mod, tmp_path, monkeypatch):
    """A RELATIVE model_dir must still register absolute ufo/spec paths."""
    monkeypatch.chdir(tmp_path)
    sarah_name = "SingletDoublet"
    # Relative model_dir, like a replay run from ./demo_output/... would use.
    model_dir = Path("demo_state")
    ufo_target = model_dir / "sarah_output" / "UFO" / sarah_name
    ufo_target.mkdir(parents=True)
    (model_dir / sarah_name).symlink_to(Path("sarah_output") / "UFO" / sarah_name)
    (model_dir / "spec.yaml").write_text("model: {name: SingletDoublet}\n")

    spec = {"model": {"name": sarah_name, "slug": "singlet_doublet"}}
    run_sarah_mod._register_model_safe(spec, model_dir, sarah_name)

    cfg = json.loads(
        (tmp_path / "cfg" / "hephaestus" / "config.json").read_text())
    entry = cfg["models"]["singlet_doublet"]
    assert os.path.isabs(entry["ufo"]), f"ufo not absolute: {entry['ufo']!r}"
    assert os.path.isabs(entry["spec"]), f"spec not absolute: {entry['spec']!r}"
    # And they anchor to the CWD the (relative) model_dir was resolved from.
    assert entry["ufo"] == str(tmp_path / "demo_state" / sarah_name)
    assert entry["spec"] == str(tmp_path / "demo_state" / "spec.yaml")
    # The symlink itself keeps the canonical <sarah_name> basename MG5 needs.
    assert Path(entry["ufo"]).name == sarah_name
