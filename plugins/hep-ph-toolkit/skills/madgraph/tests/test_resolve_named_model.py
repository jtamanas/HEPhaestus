"""Tests for resolve_named_model.py.

All tests use XDG_CONFIG_HOME + HEPPH_STATE_ROOT env isolation so they
never touch the real ~/.config/hephaestus/config.json.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT = Path(__file__).parent.parent / "scripts" / "resolve_named_model.py"

FAKE_CONFIG = {
    "models": {
        "dark_su3": {
            "ufo": "/tmp/dark_su3_ufo",
            "latest_slha": "/tmp/dark_su3_slha",
            "spheno_bin": "/tmp/spheno_bin",
        }
    }
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_config(cfg_dir: Path, data: dict) -> Path:
    """Write data as config.json under cfg_dir/hephaestus/."""
    config_dir = cfg_dir / "hephaestus"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"
    config_path.write_text(json.dumps(data))
    return config_path


def load_resolver(config_path: Path):
    """Load resolve_named_model.py as a module with CONFIG_PATH patched."""
    spec = importlib.util.spec_from_file_location("_resolve_named_model", SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    # Patch CONFIG_PATH after loading so resolve() uses our fake config.
    mod.CONFIG_PATH = config_path
    return mod


def run_cli(*args, env_overrides=None):
    """Run the CLI script in a subprocess; return (stdout, stderr, returncode)."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


# ---------------------------------------------------------------------------
# Tests for the resolve() library function
# ---------------------------------------------------------------------------


def test_resolve_returns_dict(tmp_path):
    config_path = write_config(tmp_path, FAKE_CONFIG)
    mod = load_resolver(config_path)

    result = mod.resolve("dark_su3")
    assert result is not None
    assert result["ufo"] == "/tmp/dark_su3_ufo"
    assert result["latest_slha"] == "/tmp/dark_su3_slha"


def test_resolve_returns_none_for_unknown(tmp_path):
    config_path = write_config(tmp_path, FAKE_CONFIG)
    mod = load_resolver(config_path)

    assert mod.resolve("unknown_model") is None


def test_resolve_returns_none_when_config_missing(tmp_path):
    # Point at a path that doesn't exist
    missing_path = tmp_path / "hephaestus" / "config.json"
    mod = load_resolver(missing_path)

    assert mod.resolve("dark_su3") is None


# ---------------------------------------------------------------------------
# Tests for the CLI
# ---------------------------------------------------------------------------


def test_cli_prints_json_for_registered_model(tmp_path):
    write_config(tmp_path, FAKE_CONFIG)
    stdout, stderr, code = run_cli(
        "dark_su3",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 0, f"stderr: {stderr}"
    parsed = json.loads(stdout)
    assert parsed["ufo"] == "/tmp/dark_su3_ufo"
    assert parsed["latest_slha"] == "/tmp/dark_su3_slha"


def test_cli_key_ufo(tmp_path):
    write_config(tmp_path, FAKE_CONFIG)
    stdout, stderr, code = run_cli(
        "dark_su3", "--key", "ufo",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 0, f"stderr: {stderr}"
    assert stdout == "/tmp/dark_su3_ufo"


def test_cli_key_latest_slha(tmp_path):
    write_config(tmp_path, FAKE_CONFIG)
    stdout, stderr, code = run_cli(
        "dark_su3", "--key", "latest_slha",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 0, f"stderr: {stderr}"
    assert stdout == "/tmp/dark_su3_slha"


def test_cli_exits_1_for_unknown_model(tmp_path):
    write_config(tmp_path, FAKE_CONFIG)
    stdout, stderr, code = run_cli(
        "not_registered", "--key", "ufo",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 1
    assert "not_registered" in stderr


def test_cli_exits_1_when_config_absent(tmp_path):
    # No config.json written — tmp_path exists but no hephaestus subdir
    stdout, stderr, code = run_cli(
        "dark_su3", "--key", "ufo",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 1
    assert "config not found" in stderr


def test_cli_exits_2_for_missing_key(tmp_path):
    # Model registered but requested key is absent
    cfg = {"models": {"dark_su3": {"ufo": "/tmp/ufo"}}}  # no latest_slha
    write_config(tmp_path, cfg)
    stdout, stderr, code = run_cli(
        "dark_su3", "--key", "latest_slha",
        env_overrides={
            "XDG_CONFIG_HOME": str(tmp_path),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert code == 2
    assert "latest_slha" in stderr


def test_cli_help(tmp_path):
    stdout, stderr, code = run_cli("--help")
    assert code == 0


# ---------------------------------------------------------------------------
# MG5 smoke test — deferred until W3 UFO exists
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    "HEPPH_RUN_MG5_TESTS" not in os.environ,
    reason=(
        "MG5 integration test requires HEPPH_RUN_MG5_TESTS=1 "
        "and a real UFO from W3"
    ),
)
def test_mg5_script_file_invocation(tmp_path):
    """Verify mg5_aMC accepts a script-file positional argument (NOT -c).

    Day-1 probe W6 / spec §6 probe #4.  Only runs when
    HEPPH_RUN_MG5_TESTS=1 is set in the environment.
    """
    import shutil

    mg5 = shutil.which("mg5_aMC")
    assert mg5 is not None, "mg5_aMC not on PATH"

    script = tmp_path / "probe.mg5"
    script.write_text("display particles\nexit\n")
    result = subprocess.run([mg5, str(script)], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"mg5_aMC exited {result.returncode}:\n{result.stderr}"
    )
