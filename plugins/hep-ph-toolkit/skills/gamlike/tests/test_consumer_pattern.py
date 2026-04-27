"""
test_consumer_pattern.py — E2E consumer pattern test (T16, Path X / O6).

Drives parse_maddm_results.py via subprocess, then reads the JSON
via in-process json.loads (NO extract_field.py invocation).
"""
import json
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"

_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_subprocess_then_json_loads_relic_field(tmp_path):
    """Parse via subprocess, then read Omegah2 via in-process json.loads (top-level key)."""
    fixture = _FIXTURES / "relic_only_xsi_eq_1_2hdma.txt"
    out_path = tmp_path / "out.json"
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), str(fixture), "--out", str(out_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert out_path.exists()

    # In-process json.loads (Path X — no extract_field.py)
    data = json.loads(out_path.read_text())
    omega_h2_subprocess = data["relic"]["Omegah2"]

    # Compare against in-process parse
    doc_inprocess = _mod.parse_file(fixture)
    omega_h2_inprocess = doc_inprocess["relic"]["Omegah2"]

    assert omega_h2_subprocess == pytest.approx(omega_h2_inprocess, rel=1e-12)


def test_subprocess_then_json_loads_nested_channel(tmp_path):
    """Parse via subprocess, then read nested channel value via dict access."""
    fixture = _FIXTURES / "relic_only_xsi_eq_1_2hdma.txt"
    out_path = tmp_path / "out2.json"
    subprocess.run(
        [sys.executable, str(_SCRIPT), str(fixture), "--out", str(out_path)],
        capture_output=True, text=True, check=True,
    )

    data = json.loads(out_path.read_text())

    # Nested dict access: data["relic"]["channels"]["chichibar"]["wphp"]
    wphp = data["relic"]["channels"]["chichibar"]["wphp"]
    assert wphp == pytest.approx(49.62, rel=1e-3)

    # Verify the stdout output is the absolute path to the JSON
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), str(fixture), "--out", str(out_path)],
        capture_output=True, text=True,
    )
    stdout_path = result.stdout.strip()
    assert Path(stdout_path).exists()
    assert stdout_path == str(out_path.resolve())
