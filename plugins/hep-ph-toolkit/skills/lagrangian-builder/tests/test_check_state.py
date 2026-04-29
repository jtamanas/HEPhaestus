"""
test_check_state.py — unit tests for scripts/check_state.py.

After the install-skill refactor, check_state.py only probes model
registration. SARAH/SPheno/Wolfram install state is now self-detected by
the runner skills (`/sarah-build`, `/spheno-build`) via their
`_shared/installs/<tool>/detect.sh` preflight.

Each test uses isolated XDG_CONFIG_HOME and HEPPH_STATE_ROOT directories.
No real tools required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "check_state.py"
)


def _write_config(cfg_root: Path, data: dict) -> None:
    hep_dir = cfg_root / "hephaestus"
    hep_dir.mkdir(parents=True, exist_ok=True)
    (hep_dir / "config.json").write_text(json.dumps(data))


def _run_check_state(
    cfg_root: Path,
    state_root: Path,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_SCRIPT)] + (extra_args or [])
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(cfg_root)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestEmptyConfig:
    def test_no_model_arg_returns_missing(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        cfg.mkdir()
        state = tmp_path / "state"
        state.mkdir()
        result = _run_check_state(cfg, state)
        assert result.returncode == 0
        out = json.loads(result.stdout)
        # Install status keys are intentionally absent post-refactor.
        assert "sarah_install" not in out
        assert "spheno_install" not in out
        assert "wolfram_install" not in out
        assert out["model"]["status"] == "missing"
        assert out["model"]["name"] is None


class TestModelFlag:
    def test_model_present_when_spec_path_exists(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        spec = tmp_path / "spec.yaml"
        spec.write_text("spec_version: 1\n")

        _write_config(
            cfg,
            {"models": {"dark_su3": {"spec": str(spec), "ufo": "/some/path"}}},
        )
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "present"
        assert out["model"]["name"] == "dark_su3"

    def test_model_missing_when_not_registered(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()
        _write_config(cfg, {})
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "missing"

    def test_model_missing_when_spec_file_absent(self, tmp_path: Path) -> None:
        """Registered but spec file deleted → status missing."""
        cfg = tmp_path / "cfg"
        state = tmp_path / "state"
        state.mkdir()

        _write_config(
            cfg,
            {"models": {"dark_su3": {"spec": "/nonexistent/spec.yaml"}}},
        )
        result = _run_check_state(cfg, state, extra_args=["--model", "dark_su3"])
        out = json.loads(result.stdout)
        assert out["model"]["status"] == "missing"
