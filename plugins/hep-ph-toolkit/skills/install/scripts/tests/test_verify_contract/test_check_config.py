"""
Contract tests for check_config.py's delegation to install_*.sh verify.

Tests:
  (a) Exit bitfield bits are set correctly per tool verify verdict.
  (b) internal_error → bit 32 (NOT the tool's specific bit).
  (c) JSON report structure passes the verify schema for each tool payload.
  (d) WARN line emitted for non-strict version drift (ok=true, expected_version present).
  (e) SKIP line emitted for not_configured tools.

Uses mock install_*.sh scripts via HEPPH_SCRIPTS_DIR override (same mechanism
as test_check_config_golden.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _schema import validate  # noqa: E402

_SCRIPTS_DIR = _HERE.parent.parent  # plugins/.../install/scripts/
_CHECK_CONFIG = _SCRIPTS_DIR / "check_config.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK_HEADER = """\
#!/bin/sh
subcommand="${1:-}"
shift || true
path=''
expected_version=''
wolfram_path=''
while [ $# -gt 0 ]; do
  case "$1" in
    --path) path="$2"; shift 2 ;;
    --expected-version) expected_version="$2"; shift 2 ;;
    --wolfram-path) wolfram_path="$2"; shift 2 ;;
    --json) shift ;;
    *) shift ;;
  esac
done
"""


def _make_ok_mock(tool: str, version: str = "1.0.0") -> str:
    """Return a mock install_<tool>.sh that emits a passing JSON payload."""
    return (
        _MOCK_HEADER
        + f"""python3 - "$path" "$expected_version" << 'PYEOF'
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else ''
ev = sys.argv[2] if len(sys.argv) > 2 else ''
payload = {{'schema_version':1,'tool':'{tool}','ok':True,'status':'ok',
           'path':path,'version':'{version}','detail':'ok','hints':[],'duration_ms':1}}
if ev:
    payload['expected_version'] = ev
print(json.dumps(payload))
PYEOF
exit 0
"""
    )


def _make_fail_mock(tool: str, status: str = "installed_broken", detail: str = "probe failed") -> str:
    """Return a mock install_<tool>.sh that emits a failing JSON payload."""
    return (
        _MOCK_HEADER
        + f"""python3 - "$path" "$expected_version" << 'PYEOF'
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else ''
ev = sys.argv[2] if len(sys.argv) > 2 else ''
payload = {{'schema_version':1,'tool':'{tool}','ok':False,'status':'{status}',
           'path':path,'version':'','detail':'{detail}','hints':[],'duration_ms':1}}
if ev:
    payload['expected_version'] = ev
print(json.dumps(payload))
PYEOF
exit 15
"""
    )


def _make_drift_mock(tool: str, observed: str, expected_in_cfg: str) -> str:
    """Return a mock that emits ok=true with version drift (non-strict)."""
    return (
        _MOCK_HEADER
        + f"""python3 - "$path" << 'PYEOF'
import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else ''
payload = {{'schema_version':1,'tool':'{tool}','ok':True,'status':'ok',
           'path':path,'version':'{observed}','expected_version':'{expected_in_cfg}',
           'detail':'version {observed} on disk, expected {expected_in_cfg}',
           'hints':[],'duration_ms':1}}
print(json.dumps(payload))
PYEOF
exit 0
"""
    )


def _make_crash_mock() -> str:
    """Return a mock install script that exits 127 with no stdout (infra failure)."""
    return "#!/bin/sh\nexit 127\n"


def _write_mock(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


def _stub_bin(d: Path, name: str) -> Path:
    p = d / name
    p.write_text("#!/bin/sh\necho stub\n")
    p.chmod(0o755)
    return p


def _run_check_config(
    cfg_path: Path,
    mock_scripts_dir: Path,
    json_mode: bool = True,
) -> tuple[int, str]:
    env = {**os.environ, "HEPPH_SCRIPTS_DIR": str(mock_scripts_dir)}
    cmd = [sys.executable, str(_CHECK_CONFIG), "--config", str(cfg_path)]
    if json_mode:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout


def _build_config(
    d: Path,
    *,
    wolfram_path: str = "",
    wolfram_version: str = "",
    sarah_path: str = "",
    sarah_version: str = "",
    spheno_path: str = "",
    spheno_version: str = "",
    mg5_path: str = "",
    mg5_version: str = "",
) -> Path:
    cfg = {
        "wolfram_engine_path": wolfram_path,
        "wolfram_engine_version": wolfram_version,
        "sarah_path": sarah_path,
        "sarah_version": sarah_version,
        "spheno_path": spheno_path,
        "spheno_version": spheno_version,
        "madgraph_path": mg5_path,
        "madgraph_version": mg5_version,
    }
    p = d / "config.json"
    p.write_text(json.dumps(cfg))
    return p


# ---------------------------------------------------------------------------
# Tests — bitfield correctness
# ---------------------------------------------------------------------------


def test_all_pass_exit_0(tmp_path: Path) -> None:
    """All four tools pass → exit 0."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",     "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 0, f"Expected exit 0, got {rc}. output={output}"
    report = json.loads(output)
    assert report["ok"] is True


def test_wolfram_fail_exit_1(tmp_path: Path) -> None:
    """Wolfram verify returns installed_broken → exit bit 1."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_fail_mock("wolfram", "installed_broken"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",     "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 1, f"Expected exit 1 (wolfram bit), got {rc}."
    report = json.loads(output)
    assert report["ok"] is False
    wolfram_payload = next(t for t in report["tools"] if t.get("tool") == "wolfram")
    assert wolfram_payload["status"] == "installed_broken"


def test_sarah_fail_exit_2(tmp_path: Path) -> None:
    """SARAH verify returns installed_broken → exit bit 2."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_fail_mock("sarah", "installed_broken"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",     "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 2, f"Expected exit 2 (sarah bit), got {rc}."


def test_wolfram_and_sarah_fail_exit_3(tmp_path: Path) -> None:
    """Wolfram + SARAH both fail → exit 1|2 = 3 (two_tools_fail scenario)."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_fail_mock("wolfram"))
    _write_mock(mocks / "install_sarah.sh",   _make_fail_mock("sarah"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno", "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",    "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, _ = _run_check_config(cfg, mocks)
    assert rc == 3, f"Expected exit 3 (wolfram|sarah), got {rc}."


def test_mg5_installed_broken_exit_8(tmp_path: Path) -> None:
    """MG5 verify returns installed_broken JSON → exit bit 8 (NOT 32)."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    # install_mg5.sh emits installed_broken JSON (not infra crash)
    _write_mock(mocks / "install_mg5.sh", _make_fail_mock("mg5", "installed_broken"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 8, (
        f"MG5 installed_broken must set bit 8, not 32. Got exit {rc}.\n{output}"
    )
    report = json.loads(output)
    mg5_payload = next(t for t in report["tools"] if t.get("tool") == "mg5")
    assert mg5_payload["status"] == "installed_broken"


# ---------------------------------------------------------------------------
# Tests — B7: internal_error → bit 32, NOT tool bit
# ---------------------------------------------------------------------------


def test_mg5_script_crash_exit_32_not_8(tmp_path: Path) -> None:
    """B7 fix: install_mg5.sh exits 127 (infra crash, no JSON) → bit 32, NOT bit 8."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_crash_mock())

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 32, (
        f"B7: install_mg5.sh infra crash must exit 32 (not 8). Got {rc}.\n{output}"
    )
    assert rc != 8, "B7: bit 8 (mg5 tool bit) must NOT be set for an infra crash."
    report = json.loads(output)
    mg5_payload = next(t for t in report["tools"] if t.get("tool") == "mg5")
    assert mg5_payload["status"] == "internal_error", (
        f"B7: status must be 'internal_error' for infra crash. Got: {mg5_payload['status']!r}"
    )


def test_wolfram_script_malformed_json_exit_32_not_1(tmp_path: Path) -> None:
    """B7 fix: install_wolfram.sh emits malformed JSON → bit 32, NOT bit 1."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    # Emits invalid JSON — parse failure → internal_error → bit 32
    _write_mock(mocks / "install_wolfram.sh",
                "#!/bin/sh\necho 'this is not json'\nexit 0\n")
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",     "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 32, (
        f"B7: malformed JSON from wolfram script must exit 32 (not 1). Got {rc}.\n{output}"
    )
    report = json.loads(output)
    wolfram_payload = next(t for t in report["tools"] if t.get("tool") == "wolfram")
    assert wolfram_payload["status"] == "internal_error"


# ---------------------------------------------------------------------------
# Tests — JSON report schema correctness
# ---------------------------------------------------------------------------


def test_json_report_structure(tmp_path: Path) -> None:
    """check_config.py --json output has ok bool and tools list with schema-valid payloads."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_ok_mock("mg5",     "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    rc, output = _run_check_config(cfg, mocks)
    assert rc == 0

    report = json.loads(output)
    assert "ok" in report, "Top-level 'ok' key required"
    assert isinstance(report["ok"], bool), "'ok' must be bool"
    assert "tools" in report, "Top-level 'tools' key required"
    assert isinstance(report["tools"], list), "'tools' must be list"
    assert len(report["tools"]) == 4, "Expected exactly 4 tool payloads"

    # Each tool payload must pass the schema validator
    for payload in report["tools"]:
        errors = validate(payload)
        assert errors == [], f"Schema errors in payload for {payload.get('tool')!r}: {errors}"


def test_json_not_configured_schema(tmp_path: Path) -> None:
    """Python-synthesised not_configured payloads must pass schema validation."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    # wolfram and spheno not configured — Python synthesises their payloads
    _write_mock(mocks / "install_sarah.sh",  _make_ok_mock("sarah",  "4.15.3"))
    _write_mock(mocks / "install_mg5.sh",    _make_ok_mock("mg5",    "3.5.6"))

    cfg = _build_config(
        tmp_path,
        sarah_path=str(sarah_dir), sarah_version="4.15.3",
        mg5_path=str(mg5_bin),     mg5_version="3.5.6",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
    )
    # spheno has a path so it gets delegated — need a mock for it
    _write_mock(mocks / "install_spheno.sh", _make_ok_mock("spheno", "4.0.5"))

    rc, output = _run_check_config(cfg, mocks)
    report = json.loads(output)
    wolfram_payload = next(t for t in report["tools"] if t.get("tool") == "wolfram")
    assert wolfram_payload["status"] == "not_configured"
    assert wolfram_payload["ok"] is False
    errors = validate(wolfram_payload)
    assert errors == [], f"Schema errors in not_configured payload: {errors}"


# ---------------------------------------------------------------------------
# Tests — human output format
# ---------------------------------------------------------------------------


def test_skip_line_for_not_configured(tmp_path: Path) -> None:
    """not_configured → human line starts with 'SKIP'."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_sarah.sh",  _make_ok_mock("sarah",  "4.15.3"))
    _write_mock(mocks / "install_spheno.sh", _make_ok_mock("spheno", "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",    _make_ok_mock("mg5",    "3.5.6"))

    cfg = _build_config(
        tmp_path,
        sarah_path=str(sarah_dir), sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    _rc, output = _run_check_config(cfg, mocks, json_mode=False)
    lines = output.splitlines()
    wolfram_line = next(l for l in lines if "Wolfram" in l)
    assert wolfram_line.startswith("SKIP"), (
        f"Wolfram not_configured line must start with 'SKIP'. Got: {wolfram_line!r}"
    )


def test_warn_line_for_version_drift(tmp_path: Path) -> None:
    """ok=true with version drift → human line starts with 'WARN' and uses '->'."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    # mg5 drifted: config=3.5.6, observed=3.5.7
    _write_mock(mocks / "install_mg5.sh", _make_drift_mock("mg5", "3.5.7", "3.5.6"))

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    _rc, output = _run_check_config(cfg, mocks, json_mode=False)
    assert _rc == 0, f"Version drift (non-strict) should exit 0. Got {_rc}.\n{output}"
    lines = output.splitlines()
    mg5_line = next(l for l in lines if "MadGraph" in l)
    assert mg5_line.startswith("WARN"), (
        f"MG5 version drift line must start with 'WARN'. Got: {mg5_line!r}"
    )
    assert "->" in mg5_line, (
        f"WARN line must contain '->' (ASCII arrow). Got: {mg5_line!r}"
    )


def test_internal_error_line_in_human_output(tmp_path: Path) -> None:
    """internal_error → human line starts with 'INTERNAL ERROR'."""
    mocks = tmp_path / "mocks"
    mocks.mkdir()
    wolf_bin = _stub_bin(tmp_path, "wolframscript")
    sarah_dir = tmp_path / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(tmp_path, "SPheno")
    mg5_bin = _stub_bin(tmp_path, "mg5_aMC")

    _write_mock(mocks / "install_wolfram.sh", _make_ok_mock("wolfram", "14.1"))
    _write_mock(mocks / "install_sarah.sh",   _make_ok_mock("sarah",   "4.15.3"))
    _write_mock(mocks / "install_spheno.sh",  _make_ok_mock("spheno",  "4.0.5"))
    _write_mock(mocks / "install_mg5.sh",     _make_crash_mock())

    cfg = _build_config(
        tmp_path,
        wolfram_path=str(wolf_bin), wolfram_version="14.1",
        sarah_path=str(sarah_dir),  sarah_version="4.15.3",
        spheno_path=str(spheno_bin), spheno_version="4.0.5",
        mg5_path=str(mg5_bin),       mg5_version="3.5.6",
    )
    _rc, output = _run_check_config(cfg, mocks, json_mode=False)
    assert _rc == 32
    lines = output.splitlines()
    mg5_line = next(l for l in lines if "MadGraph" in l)
    assert mg5_line.startswith("INTERNAL ERROR"), (
        f"MG5 internal_error line must start with 'INTERNAL ERROR'. Got: {mg5_line!r}"
    )
