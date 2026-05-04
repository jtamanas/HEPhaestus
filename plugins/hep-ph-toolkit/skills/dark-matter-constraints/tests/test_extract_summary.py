"""test_extract_summary.py — WS-5 § 7.

Runs extract_field.py --key summary against the cosmology_planck18.json fixture.
Asserts:
  - exit code 0
  - stdout parses to JSON with {"value": <dict>}
  - the "value" dict has exactly the contracted summary keys
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts" / "extract_field.py"
_FIXTURE = _HERE / "fixtures" / "class" / "cosmology_planck18.json"

_EXPECTED_SUMMARY_KEYS = {
    "H0",
    "omega_b",
    "omega_cdm",
    "Omega_m_h2",
    "N_eff",
    "tau_reio",
    "sigma_8",
    "z_eq",
}


def test_extract_summary_happy_path():
    """extract_field.py --key summary exits 0; stdout is a JSON dict with expected keys."""
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPTS),
            "--json",
            str(_FIXTURE),
            "--key",
            "summary",
            "--schema-version",
            "cosmology/v1",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}. "
        f"stderr={result.stderr!r}"
    )

    parsed = json.loads(result.stdout)
    assert isinstance(parsed, dict), f"stdout should be a JSON object, got {type(parsed)}"

    value = parsed["value"]
    assert isinstance(value, dict), (
        f"'value' field should be a dict (the summary block), got {type(value)}: {value!r}"
    )

    actual_keys = set(value.keys())
    assert actual_keys == _EXPECTED_SUMMARY_KEYS, (
        f"Summary keys mismatch.\n"
        f"  expected: {sorted(_EXPECTED_SUMMARY_KEYS)}\n"
        f"  actual:   {sorted(actual_keys)}"
    )
