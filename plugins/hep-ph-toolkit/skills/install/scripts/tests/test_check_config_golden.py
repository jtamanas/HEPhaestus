"""Golden-file tests for check_config.py — C7 delegation shape.

C7 rewrote check_config.py to delegate to install_<tool>.sh verify.
These goldens capture the output of that delegation with hermetic mock
install_*.sh scripts.

Note: the mg5_internal_error scenario MUST produce exit code 32 (bit 32 = internal
error, NOT bit 8 = mg5 tool bit). This is the B7 fix.

Usage
-----
  # Run tests (compare against stored goldens):
  python3 -m pytest tests/test_check_config_golden.py -q

  # Regenerate goldens from current check_config.py output:
  python3 -m pytest tests/test_check_config_golden.py --regen -q
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_SCRIPTS_DIR = _HERE.parent
_CHECK_CONFIG = _SCRIPTS_DIR / "check_config.py"
_GOLDENS_DIR = _HERE / "goldens" / "check_config"

# --regen option is registered in conftest.py at the same directory level.

# ---------------------------------------------------------------------------
# Path-normalization helpers
# ---------------------------------------------------------------------------


def _normalize(text: str, root: str) -> str:
    """Replace transient host-specific paths with stable placeholders.

    Substitutions applied (in order):
      1. The tmp fixture root     → $TMPDIR
      2. $HOME literal            → $HOME  (idempotent for already-subst text)
      3. $XDG_CONFIG_HOME literal → $XDG_CONFIG_HOME
      4. macOS /private/var/folders/…/T → $TMPDIR  (covers pytest's own tmpdir)
    """
    # 1. Fixture root (longest/most-specific first)
    text = text.replace(root, "$TMPDIR")
    # 2. HOME
    home = str(Path.home())
    text = text.replace(home, "$HOME")
    # 3. XDG_CONFIG_HOME (if set)
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        text = text.replace(xdg, "$XDG_CONFIG_HOME")
    # 4. macOS sandbox temp paths not already caught by (1)
    text = re.sub(r"/private/var/folders/[^/]+/[^/]+/T", "$TMPDIR", text)
    # Also handle /var/folders without /private prefix
    text = re.sub(r"/var/folders/[^/]+/[^/]+/T", "$TMPDIR", text)
    return text


# ---------------------------------------------------------------------------
# Mock install_*.sh factory
# ---------------------------------------------------------------------------

# Mock scripts use Python to emit JSON — avoids shell quoting pitfalls.
# They parse --path, --expected-version, --wolfram-path, --json.

_MOCK_SCRIPT_HEADER = """\
#!/bin/sh
# Mock install script for testing check_config.py delegation.
# Parses verify subcommand args and delegates to embedded Python for JSON output.
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

_PYTHON_EMIT = """\
python3 - "$path" "$expected_version" "$wolfram_path" << 'PYEOF'
"""

_PYTHON_EMIT_SUFFIX = """
PYEOF
"""


def _make_mock_script(tool: str, payload_fn_body: str, exit_code: int = 0) -> str:
    """Build a mock install_<tool>.sh script body.

    payload_fn_body is Python code that assigns `payload` dict.
    It receives path/expected_version/wolfram_path as sys.argv[1:4].
    """
    return (
        _MOCK_SCRIPT_HEADER
        + _PYTHON_EMIT
        + f"""import json, sys
path = sys.argv[1] if len(sys.argv) > 1 else ''
expected_version = sys.argv[2] if len(sys.argv) > 2 else ''
wolfram_path = sys.argv[3] if len(sys.argv) > 3 else ''
{payload_fn_body}
print(json.dumps(payload))
"""
        + _PYTHON_EMIT_SUFFIX
        + f"exit {exit_code}\n"
    )


def _write_mock_script(path: Path, body: str) -> Path:
    path.write_text(body)
    path.chmod(0o755)
    return path


# ---------------------------------------------------------------------------
# Per-tool mock script bodies
# ---------------------------------------------------------------------------

_WOLFRAM_OK = (
    "payload = {'schema_version':1,'tool':'wolfram','ok':True,'status':'ok',"
    "'path':path,'version':'14.1','detail':'ok (2+2 -> 4)','hints':[],'duration_ms':1}"
)

_WOLFRAM_OK_NO_EV = _WOLFRAM_OK  # no expected_version in config for wolfram

_WOLFRAM_BROKEN = (
    "payload = {'schema_version':1,'tool':'wolfram','ok':False,'status':'installed_broken',"
    "'path':path,'version':'','detail':'wolframscript exit 1: some error','hints':[],'duration_ms':1}"
)

_SARAH_OK = (
    "payload = {'schema_version':1,'tool':'sarah','ok':True,'status':'ok',"
    "'path':path,'version':'4.15.3','expected_version':expected_version or '4.15.3',"
    "'detail':'version 4.15.3','hints':[],'duration_ms':1}"
)

_SARAH_WOLFRAM_MISSING = (
    "payload = {'schema_version':1,'tool':'sarah','ok':False,'status':'installed_broken',"
    "'path':path,'version':'','detail':'wolframscript not found (wolfram_engine_missing)',"
    "'hints':[{'code':'wolfram_engine_missing','message':'No Wolfram Engine path configured'}],"
    "'duration_ms':1}"
)

_SARAH_MISSING = (
    "payload = {'schema_version':1,'tool':'sarah','ok':False,'status':'missing',"
    "'path':path,'version':'','detail':'missing SARAH.m in path',"
    "'hints':[],'duration_ms':1}"
)

_SPHENO_OK = (
    "payload = {'schema_version':1,'tool':'spheno','ok':True,'status':'ok',"
    "'path':path,'version':'4.0.5','expected_version':expected_version or '4.0.5',"
    "'detail':'usage banner present','hints':[],'duration_ms':1}"
)

_MG5_OK_36 = (
    "payload = {'schema_version':1,'tool':'mg5','ok':True,'status':'ok',"
    "'path':path,'version':'3.5.6','expected_version':expected_version or '3.5.6',"
    "'detail':'ok (3.5.6)','hints':[],'duration_ms':1}"
)

_MG5_OK_37 = (
    "payload = {'schema_version':1,'tool':'mg5','ok':True,'status':'ok',"
    "'path':path,'version':'3.5.7','expected_version':expected_version or '3.5.7',"
    "'detail':'ok (3.5.7)','hints':[],'duration_ms':1}"
)

_MG5_DRIFT = (
    "payload = {'schema_version':1,'tool':'mg5','ok':True,'status':'ok',"
    "'path':path,'version':'3.5.7','expected_version':'3.5.6',"
    "'detail':'version 3.5.7 on disk, expected 3.5.6','hints':[],'duration_ms':1}"
)


def _stub_bin(d: Path, name: str) -> Path:
    """Create a stub executable (used for tool paths that must exist on disk)."""
    p = d / name
    p.write_text("#!/bin/sh\necho mock\n")
    p.chmod(0o755)
    return p


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------


def _scenario_all_pass(d: Path) -> tuple[Path, Path]:
    """All four tools configured; all mock verify scripts return ok."""
    bin_dir = d / "bin"
    bin_dir.mkdir()

    wolf_bin = _stub_bin(bin_dir, "wolframscript")
    sarah_dir = d / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    _write_mock_script(bin_dir / "install_wolfram.sh", _make_mock_script("wolfram", _WOLFRAM_OK))
    _write_mock_script(bin_dir / "install_sarah.sh",   _make_mock_script("sarah",   _SARAH_OK))
    _write_mock_script(bin_dir / "install_spheno.sh",  _make_mock_script("spheno",  _SPHENO_OK))
    _write_mock_script(bin_dir / "install_mg5.sh",     _make_mock_script("mg5",     _MG5_OK_36))

    cfg = {
        "wolfram_engine_path": str(wolf_bin),
        "wolfram_engine_version": "14.1",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        "madgraph_version": "3.5.6",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


def _scenario_sarah_no_wolfram(d: Path) -> tuple[Path, Path]:
    """sarah_path set; wolfram_engine_path empty → wolfram SKIP, sarah FAIL."""
    bin_dir = d / "bin"
    bin_dir.mkdir()

    sarah_dir = d / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    # wolfram: not in config → Python synthesises not_configured (no script needed)
    # sarah: wolfram_engine_path empty → installed_broken (wolfram_engine_missing)
    _write_mock_script(bin_dir / "install_sarah.sh",  _make_mock_script("sarah",  _SARAH_WOLFRAM_MISSING, 15))
    _write_mock_script(bin_dir / "install_spheno.sh", _make_mock_script("spheno", _SPHENO_OK))
    _write_mock_script(bin_dir / "install_mg5.sh",    _make_mock_script("mg5",    _MG5_OK_37))

    cfg = {
        "wolfram_engine_path": "",
        "wolfram_engine_version": "",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        "madgraph_version": "3.5.7",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


def _scenario_mg5_internal_error(d: Path) -> tuple[Path, Path]:
    """madgraph_path set; mock install_mg5.sh exits 127 with empty stdout → bit 32."""
    bin_dir = d / "bin"
    bin_dir.mkdir()

    wolf_bin = _stub_bin(bin_dir, "wolframscript")
    sarah_dir = d / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    _write_mock_script(bin_dir / "install_wolfram.sh", _make_mock_script("wolfram", _WOLFRAM_OK))
    _write_mock_script(bin_dir / "install_sarah.sh",   _make_mock_script("sarah",   _SARAH_OK))
    _write_mock_script(bin_dir / "install_spheno.sh",  _make_mock_script("spheno",  _SPHENO_OK))
    # install_mg5.sh exits 127 with no stdout → internal_error → bit 32
    _write_mock_script(
        bin_dir / "install_mg5.sh",
        "#!/bin/sh\n# Simulates a broken verify script — exits 127, no stdout\nexit 127\n",
    )

    cfg = {
        "wolfram_engine_path": str(wolf_bin),
        "wolfram_engine_version": "14.1",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        "madgraph_version": "3.5.7",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


def _scenario_wolfram_not_configured(d: Path) -> tuple[Path, Path]:
    """wolfram_engine_path empty → wolfram SKIP (not_configured)."""
    bin_dir = d / "bin"
    bin_dir.mkdir()

    sarah_dir = d / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    # wolfram: not configured → Python synthesises not_configured (no script needed)
    # sarah: wolfram_engine_path empty → installed_broken (wolfram_engine_missing)
    _write_mock_script(bin_dir / "install_sarah.sh",  _make_mock_script("sarah",  _SARAH_WOLFRAM_MISSING, 15))
    _write_mock_script(bin_dir / "install_spheno.sh", _make_mock_script("spheno", _SPHENO_OK))
    _write_mock_script(bin_dir / "install_mg5.sh",    _make_mock_script("mg5",    _MG5_OK_37))

    cfg = {
        "wolfram_engine_path": "",
        "wolfram_engine_version": "",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        "madgraph_version": "3.5.7",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


def _scenario_two_tools_fail(d: Path) -> tuple[Path, Path]:
    """Wolfram (installed_broken) and SARAH (missing) both fail: exit 1|2 = 3."""
    bin_dir = d / "bin"
    bin_dir.mkdir()

    wolf_bin = _stub_bin(bin_dir, "wolframscript")
    sarah_dir = d / "sarah_broken"
    sarah_dir.mkdir()
    # Intentionally no SARAH.m
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    _write_mock_script(bin_dir / "install_wolfram.sh", _make_mock_script("wolfram", _WOLFRAM_BROKEN, 15))
    _write_mock_script(bin_dir / "install_sarah.sh",   _make_mock_script("sarah",   _SARAH_MISSING, 16))
    _write_mock_script(bin_dir / "install_spheno.sh",  _make_mock_script("spheno",  _SPHENO_OK))
    _write_mock_script(bin_dir / "install_mg5.sh",     _make_mock_script("mg5",     _MG5_OK_37))

    cfg = {
        "wolfram_engine_path": str(wolf_bin),
        "wolfram_engine_version": "14.0",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        "madgraph_version": "3.5.7",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


def _scenario_mg5_drift(d: Path) -> tuple[Path, Path]:
    """madgraph_version in config (3.5.6) differs from what verify observes (3.5.7).

    Non-strict drift: ok=true, WARN human line, detail notes the drift.
    """
    bin_dir = d / "bin"
    bin_dir.mkdir()

    wolf_bin = _stub_bin(bin_dir, "wolframscript")
    sarah_dir = d / "sarah"
    sarah_dir.mkdir()
    (sarah_dir / "SARAH.m").touch()
    spheno_bin = _stub_bin(bin_dir, "SPheno")
    mg5_bin = _stub_bin(bin_dir, "mg5_aMC")

    _write_mock_script(bin_dir / "install_wolfram.sh", _make_mock_script("wolfram", _WOLFRAM_OK))
    _write_mock_script(bin_dir / "install_sarah.sh",   _make_mock_script("sarah",   _SARAH_OK))
    _write_mock_script(bin_dir / "install_spheno.sh",  _make_mock_script("spheno",  _SPHENO_OK))
    # mg5: config 3.5.6, observed 3.5.7 → ok=true with expected_version + drift detail
    _write_mock_script(bin_dir / "install_mg5.sh", _make_mock_script("mg5", _MG5_DRIFT))

    cfg = {
        "wolfram_engine_path": str(wolf_bin),
        "wolfram_engine_version": "14.1",
        "sarah_path": str(sarah_dir),
        "sarah_version": "4.15.3",
        "spheno_path": str(spheno_bin),
        "spheno_version": "4.0.5",
        "madgraph_path": str(mg5_bin),
        # Config says 3.5.6 but mock reports 3.5.7 → drift
        "madgraph_version": "3.5.6",
    }
    cfg_path = d / "config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    return cfg_path, bin_dir


# Map slug → scenario function
_SCENARIOS: dict[str, object] = {
    "all_pass": _scenario_all_pass,
    "sarah_no_wolfram": _scenario_sarah_no_wolfram,
    "mg5_internal_error": _scenario_mg5_internal_error,
    "wolfram_not_configured": _scenario_wolfram_not_configured,
    "two_tools_fail": _scenario_two_tools_fail,
    "mg5_drift": _scenario_mg5_drift,
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _run_check_config(
    cfg_path: Path, json_mode: bool, mock_scripts_dir: Path | None = None
) -> tuple[int, str]:
    """Invoke check_config.py and return (exit_code, stdout).

    If mock_scripts_dir is provided, sets HEPPH_SCRIPTS_DIR so that
    check_config.py's SCRIPTS_DIR points to the mock scripts instead of
    the real install_*.sh files.
    """
    env = os.environ.copy()
    if mock_scripts_dir is not None:
        env["HEPPH_SCRIPTS_DIR"] = str(mock_scripts_dir)
    cmd = [sys.executable, str(_CHECK_CONFIG), "--config", str(cfg_path)]
    if json_mode:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout


# ---------------------------------------------------------------------------
# Parametrised golden test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("slug", list(_SCENARIOS.keys()))
def test_golden(slug: str, tmp_path: Path, request: pytest.FixtureRequest) -> None:
    """For each scenario: run check_config.py (human + JSON), diff against golden.

    With --regen: write the golden files instead of comparing.
    """
    regen = request.config.getoption("--regen")

    scenario_fn = _SCENARIOS[slug]
    scenario_dir = tmp_path / slug
    scenario_dir.mkdir()

    cfg_path, mock_scripts_dir = scenario_fn(scenario_dir)
    root = str(scenario_dir)  # normalisation anchor

    golden_dir = _GOLDENS_DIR / slug
    golden_dir.mkdir(parents=True, exist_ok=True)

    for mode_label, json_mode in [("human", False), ("json", True)]:
        golden_file = golden_dir / f"{mode_label}.txt"
        rc, raw_output = _run_check_config(cfg_path, json_mode, mock_scripts_dir)
        normalised = _normalize(raw_output, root)

        if regen:
            golden_file.write_text(normalised)
            print(f"  [regen] wrote {golden_file}")
        else:
            if not golden_file.exists():
                pytest.fail(
                    f"Golden file missing: {golden_file}\n"
                    f"Run with --regen to create it."
                )
            expected = golden_file.read_text()
            if normalised != expected:
                import difflib
                diff = difflib.unified_diff(
                    expected.splitlines(keepends=True),
                    normalised.splitlines(keepends=True),
                    fromfile=f"golden/{slug}/{mode_label}.txt",
                    tofile=f"actual/{slug}/{mode_label}.txt",
                )
                diff_text = "".join(diff)
                pytest.fail(
                    f"Golden mismatch for scenario={slug!r} mode={mode_label!r}:\n"
                    f"{diff_text}"
                )


# ---------------------------------------------------------------------------
# Additional assertions for specific scenarios (spec-mandated)
# ---------------------------------------------------------------------------


def test_mg5_internal_error_exit_code(tmp_path: Path) -> None:
    """mg5_internal_error scenario MUST exit 32 (bit 32), NOT 8 (bit 8).

    B7 fix: install script infra failure → bit 32, not the tool's bit.
    """
    scenario_dir = tmp_path / "mg5_internal_error"
    scenario_dir.mkdir()
    cfg_path, mock_scripts_dir = _scenario_mg5_internal_error(scenario_dir)
    rc, _ = _run_check_config(cfg_path, json_mode=True, mock_scripts_dir=mock_scripts_dir)
    assert rc == 32, (
        f"mg5_internal_error must exit 32 (internal error bit), got {rc}. "
        f"B7 fix: internal_error → bit 32, not bit 8."
    )


def test_two_tools_fail_exit_code(tmp_path: Path) -> None:
    """two_tools_fail scenario MUST exit 3 (bits 1|2 = wolfram + sarah)."""
    scenario_dir = tmp_path / "two_tools_fail"
    scenario_dir.mkdir()
    cfg_path, mock_scripts_dir = _scenario_two_tools_fail(scenario_dir)
    rc, _ = _run_check_config(cfg_path, json_mode=True, mock_scripts_dir=mock_scripts_dir)
    assert rc == 3, (
        f"two_tools_fail must exit 3 (wolfram=1 | sarah=2), got {rc}."
    )


def test_wolfram_not_configured_has_skip_line(tmp_path: Path) -> None:
    """wolfram_not_configured human output must contain a SKIP line for Wolfram."""
    scenario_dir = tmp_path / "wolfram_not_configured"
    scenario_dir.mkdir()
    cfg_path, mock_scripts_dir = _scenario_wolfram_not_configured(scenario_dir)
    _rc, output = _run_check_config(cfg_path, json_mode=False, mock_scripts_dir=mock_scripts_dir)
    assert "SKIP" in output, (
        f"wolfram_not_configured human output must contain 'SKIP'. Got:\n{output}"
    )


def test_mg5_drift_ok_true(tmp_path: Path) -> None:
    """mg5_drift JSON must have the mg5 tool ok == true (non-strict drift does not fail)."""
    scenario_dir = tmp_path / "mg5_drift"
    scenario_dir.mkdir()
    cfg_path, mock_scripts_dir = _scenario_mg5_drift(scenario_dir)
    _rc, output = _run_check_config(cfg_path, json_mode=True, mock_scripts_dir=mock_scripts_dir)
    report = json.loads(output)
    mg5_tool = next(t for t in report["tools"] if t.get("tool") == "mg5")
    assert mg5_tool["ok"] is True, (
        f"mg5_drift: ok must be true for non-strict version drift. Got: {mg5_tool}"
    )
