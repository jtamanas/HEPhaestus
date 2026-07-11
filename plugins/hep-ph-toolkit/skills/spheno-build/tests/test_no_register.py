"""test_no_register.py — regression tests for the latest_slha register/no-register split.

Background (PR #21, θ-scan friction #4): ``run_spheno.py`` registers
``latest_slha`` on every successful run, so a parameter scan rewrote the
global pointer once per point and left it stuck at whichever point ran last —
poisoning the next DD consumer that trusts the convenience cache.
``--no-register`` skips the pointer move (the per-run SLHA is still written
and echoed in stdout).

These tests pin BOTH sides:
  * default single run still moves latest_slha WITH provenance
    (PR #13/#20 provenance semantics depend on this), and
  * ``--no-register`` leaves the config untouched while the SLHA exists.

End-to-end via subprocess against a hermetic temp config/state root
(HEPPH_STATE_ROOT / XDG_CONFIG_HOME — the documented test isolation), never
the user's real ~/.config.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_RUN_SPHENO = _HERE.parent / "scripts" / "run_spheno.py"

_MINIMAL_SPEC = """\
model:
  name: SingletDoublet
  slug: singlet_doublet
parameters:
  - { name: MS,   default: 150.0, real: true, les_houches: [BSMPARAMS, 1] }
  - { name: MPsi, default: 500.0, real: true, les_houches: [BSMPARAMS, 2] }
  - { name: yh1,  default: 1.0,   real: true, les_houches: [BSMPARAMS, 3] }
  - { name: yh2,  default: 0.0,   real: true, les_houches: [BSMPARAMS, 4] }
backends:
  spectrum: analytic
"""


@pytest.fixture()
def isolated_roots(tmp_path):
    state = tmp_path / "state"
    cfg = tmp_path / "cfg"
    model_dir = state / "models" / "singlet_doublet"
    model_dir.mkdir(parents=True)
    cfg.mkdir()
    (model_dir / "spec.yaml").write_text(_MINIMAL_SPEC)
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(state)
    env["XDG_CONFIG_HOME"] = str(cfg)
    return {"env": env, "config_json": cfg / "hephaestus" / "config.json"}


def _run(env, *extra_args):
    proc = subprocess.run(
        [sys.executable, str(_RUN_SPHENO), "singlet_doublet", "--skip-compile",
         "--params", "MS=150,MPsi=500,yh1=1,yh2=0", *extra_args],
        env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [json.loads(l) for l in proc.stdout.strip().splitlines()]
    run_result = next(l for l in lines if l.get("stage") == "run")
    assert run_result["status"] == "ok", run_result
    return lines, run_result


def test_default_run_registers_latest_slha_with_provenance(isolated_roots):
    """The registering path is the default and must keep PR #13 provenance."""
    _, run_result = _run(isolated_roots["env"])
    cfg = json.loads(isolated_roots["config_json"].read_text())
    entry = cfg["models"]["singlet_doublet"]
    assert entry["latest_slha"] == str(Path(run_result["slha_path"]).resolve())
    prov = entry["latest_slha_provenance"]
    assert prov["sha256"], "provenance must carry a content fingerprint"
    assert prov["params"]["MS"] == 150.0
    assert prov["params"]["yh1"] == 1.0


def test_no_register_leaves_pointer_untouched(isolated_roots):
    """--no-register: SLHA written + echoed, config pointer NOT moved."""
    lines, run_result = _run(isolated_roots["env"], "--no-register")
    # SLHA still produced and echoed via the explicit skipped-register line.
    assert Path(run_result["slha_path"]).exists()
    skipped = next(l for l in lines if l.get("stage") == "register")
    assert skipped["status"] == "skipped"
    assert skipped["reason"] == "--no-register"
    assert skipped["slha_path"] == run_result["slha_path"]
    # Fresh config: nothing may have been written at all.
    cfg_path = isolated_roots["config_json"]
    if cfg_path.exists():
        entry = json.loads(cfg_path.read_text()).get("models", {}).get(
            "singlet_doublet", {})
        assert "latest_slha" not in entry
        assert "latest_slha_provenance" not in entry


def test_no_register_does_not_move_existing_pointer(isolated_roots):
    """Scan shape: a prior registered point survives later --no-register runs."""
    env = isolated_roots["env"]
    _, first = _run(env)  # canonical point, registers
    before = isolated_roots["config_json"].read_bytes()
    _run(env, "--no-register")  # scan point
    after = isolated_roots["config_json"].read_bytes()
    assert before == after, "--no-register run modified the config"
    entry = json.loads(after)["models"]["singlet_doublet"]
    assert entry["latest_slha"] == str(Path(first["slha_path"]).resolve())
