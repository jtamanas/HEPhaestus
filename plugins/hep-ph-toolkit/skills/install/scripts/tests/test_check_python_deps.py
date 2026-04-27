"""Tests for check_python_deps.py — matplotlib + numpy enforcement.

Three scenarios per the install-skill bug spec:

  1. matplotlib + numpy already importable → versions recorded, no pip call.
  2. matplotlib missing → pip install runs, succeeds, versions recorded.
  3. pip install fails → PythonDepsError raised with a clear message;
     failure is NOT swallowed.

Tests use tmp_path for the config file and monkeypatch to inject a fake
``subprocess.run``. No real subprocesses are spawned, so the interpreter at
``config.python`` doesn't need matplotlib/numpy installed for the tests to
pass — which is exactly the point: we're exercising the install skill's
behavior, not physically installing packages on the reviewer's system.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Make check_python_deps importable.
_HERE = Path(__file__).parent
_SCRIPTS_DIR = _HERE.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import check_python_deps as cpd  # noqa: E402


# ---------------------------------------------------------------------------
# Fake subprocess.run — dispatches on argv to emulate a probe or a pip install.
# ---------------------------------------------------------------------------


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_runner(
    *,
    initial_versions: dict[str, str | None],
    after_install_versions: dict[str, str | None] | None = None,
    pip_returncode: int = 0,
):
    """Return a fake ``subprocess.run`` that records every invocation.

    Probe calls (argv[1] == "-c") emit the stated versions as JSON.
    Pip calls (argv[1:3] == ["-m", "pip"]) return ``pip_returncode`` and
    flip the probe state to ``after_install_versions`` for subsequent probes.
    """
    calls: list[list[str]] = []
    state = {"versions": dict(initial_versions)}

    def runner(argv, capture_output=True, text=True, check=False):
        calls.append(list(argv))
        # Probe: python -c '<probe script>'
        if len(argv) >= 2 and argv[1] == "-c":
            return FakeCompletedProcess(
                returncode=0,
                stdout=json.dumps(state["versions"]) + "\n",
            )
        # Pip install: python -m pip install <specs...>
        if len(argv) >= 3 and argv[1:3] == ["-m", "pip"]:
            if pip_returncode == 0 and after_install_versions is not None:
                state["versions"] = dict(after_install_versions)
            return FakeCompletedProcess(
                returncode=pip_returncode,
                stdout="install log\n",
                stderr="install warn\n" if pip_returncode != 0 else "",
            )
        raise AssertionError(f"Unexpected subprocess call: {argv!r}")

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cfg_path(tmp_path: Path) -> Path:
    """Seed a minimal config.json that points at a fake python interpreter."""
    fake_python = tmp_path / "bin" / "python3"
    fake_python.parent.mkdir(parents=True, exist_ok=True)
    fake_python.write_text("#!/bin/sh\nexit 0\n")
    fake_python.chmod(0o755)

    p = tmp_path / "config.json"
    p.write_text(json.dumps({"python": str(fake_python)}, indent=2))
    return p


# ---------------------------------------------------------------------------
# Scenario 1: both deps already importable → no pip, versions recorded.
# ---------------------------------------------------------------------------


def test_deps_already_installed_records_versions_without_pip(
    cfg_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = make_runner(
        initial_versions={"matplotlib": "3.9.2", "numpy": "2.0.1"},
    )
    monkeypatch.setattr(cpd, "iso_now", lambda: "2026-04-22T21:25:00Z")

    cfg = cpd.ensure_python_deps(python=None, config_path=cfg_path, runner=runner)

    assert cfg["matplotlib_version"] == "3.9.2"
    assert cfg["numpy_version"] == "2.0.1"
    assert cfg["python_deps_checked_at"] == "2026-04-22T21:25:00Z"

    on_disk = json.loads(cfg_path.read_text())
    assert on_disk["matplotlib_version"] == "3.9.2"
    assert on_disk["numpy_version"] == "2.0.1"
    assert on_disk["python_deps_checked_at"] == "2026-04-22T21:25:00Z"

    # Exactly one probe call, zero pip calls.
    pip_calls = [c for c in runner.calls if len(c) >= 3 and c[1:3] == ["-m", "pip"]]
    assert pip_calls == [], f"Expected no pip calls; got {pip_calls}"
    probe_calls = [c for c in runner.calls if len(c) >= 2 and c[1] == "-c"]
    assert len(probe_calls) == 1


# ---------------------------------------------------------------------------
# Scenario 2: matplotlib missing → pip installs, then versions recorded.
# ---------------------------------------------------------------------------


def test_matplotlib_missing_triggers_pip_and_records_versions(
    cfg_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = make_runner(
        initial_versions={"matplotlib": None, "numpy": "2.0.1"},
        after_install_versions={"matplotlib": "3.9.2", "numpy": "2.0.1"},
        pip_returncode=0,
    )
    monkeypatch.setattr(cpd, "iso_now", lambda: "2026-04-22T21:30:00Z")

    cfg = cpd.ensure_python_deps(python=None, config_path=cfg_path, runner=runner)

    assert cfg["matplotlib_version"] == "3.9.2"
    assert cfg["numpy_version"] == "2.0.1"
    assert cfg["python_deps_checked_at"] == "2026-04-22T21:30:00Z"

    # Exactly one pip call, and it only asks for the missing package (matplotlib).
    pip_calls = [c for c in runner.calls if len(c) >= 3 and c[1:3] == ["-m", "pip"]]
    assert len(pip_calls) == 1, f"Expected 1 pip call; got {pip_calls}"
    specs = pip_calls[0][4:]  # after [python, -m, pip, install]
    assert any("matplotlib" in s for s in specs), specs
    assert not any(s == "numpy" or s.startswith("numpy") for s in specs), (
        f"numpy was already importable; pip spec list should not include it: {specs}"
    )

    # Probe ran twice: once before pip, once after.
    probe_calls = [c for c in runner.calls if len(c) >= 2 and c[1] == "-c"]
    assert len(probe_calls) == 2


# ---------------------------------------------------------------------------
# Scenario 3: pip install fails → PythonDepsError with exit_code=1.
# ---------------------------------------------------------------------------


def test_pip_install_failure_raises_clear_error(
    cfg_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = make_runner(
        initial_versions={"matplotlib": None, "numpy": None},
        pip_returncode=1,
    )

    with pytest.raises(cpd.PythonDepsError) as excinfo:
        cpd.ensure_python_deps(python=None, config_path=cfg_path, runner=runner)

    assert excinfo.value.exit_code == 1
    msg = str(excinfo.value)
    assert "pip install failed" in msg
    assert "exit 1" in msg

    # Config must NOT have been touched with version keys on failure.
    on_disk = json.loads(cfg_path.read_text())
    assert "matplotlib_version" not in on_disk
    assert "numpy_version" not in on_disk
    assert "python_deps_checked_at" not in on_disk


# ---------------------------------------------------------------------------
# Bonus: pip returns 0 but reprobe still missing → exit_code=2.
# ---------------------------------------------------------------------------


def test_pip_success_but_reprobe_still_missing_raises(
    cfg_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = make_runner(
        initial_versions={"matplotlib": None, "numpy": None},
        after_install_versions={"matplotlib": None, "numpy": None},
        pip_returncode=0,
    )

    with pytest.raises(cpd.PythonDepsError) as excinfo:
        cpd.ensure_python_deps(python=None, config_path=cfg_path, runner=runner)

    assert excinfo.value.exit_code == 2
    assert "still not" in str(excinfo.value)


# ---------------------------------------------------------------------------
# CLI smoke: main() returns correct exit code on pip failure.
# ---------------------------------------------------------------------------


def test_cli_returns_exit_1_on_pip_failure(
    cfg_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = make_runner(
        initial_versions={"matplotlib": None, "numpy": None},
        pip_returncode=1,
    )
    monkeypatch.setattr(subprocess, "run", runner)

    rc = cpd.main(["--config", str(cfg_path)])
    assert rc == 1
