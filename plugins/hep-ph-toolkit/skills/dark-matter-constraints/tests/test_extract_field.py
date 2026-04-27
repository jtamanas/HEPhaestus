"""test_extract_field.py — WS-2 tests for scripts/extract_field.py helper.

9 functions (+ 1 conditional PIN test for nested-pointer v1 behavior).

Float values compared via pytest.approx(value, rel=1e-9) — WS-2 binding decision
per synthesis §1.3 critic D6. This is NOT an xfail; it is a WS-2-owned precision choice.

Pre-flight CLI-shape check (critic item 5):
  python scripts/extract_field.py --help must expose: --json, --key, --schema-version
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST  # noqa: F401

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DMC = _HERE.parent
_SCRIPTS = _DMC / "scripts"
_HELPER = _SCRIPTS / "extract_field.py"
_FIXTURES = _HERE / "fixtures" / "helpers" / "extract_field"
_SHARED_SCHEMAS = _REPO_ROOT / "plugins" / "shared" / "schemas"

# ---------------------------------------------------------------------------
# Pre-flight: CLI shape (per plan T7 critic item 5)
# ---------------------------------------------------------------------------
_help_text = subprocess.run([sys.executable, str(_HELPER), "--help"], capture_output=True, text=True).stdout  # sys.executable
_help_text += subprocess.run([sys.executable, str(_HELPER), "--help"], capture_output=True, text=True).stderr  # sys.executable

for _f in ["--json", "--key", "--schema-version"]:
    assert _f in _help_text, f"PREFLIGHT FAIL: --help missing flag {_f!r}"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run(
    fixture_name: str,
    key: str,
    schema_version: str = "relic/v1",
    schema_root: pathlib.Path | None = None,
    json_path: pathlib.Path | None = None,
) -> subprocess.CompletedProcess:
    """Run extract_field.py as a subprocess and return the CompletedProcess."""
    if json_path is None:
        json_path = _FIXTURES / fixture_name
    args = [
        sys.executable, str(_HELPER),
        "--json", str(json_path),
        "--key", key,
        "--schema-version", schema_version,
    ]
    if schema_root is not None:
        args += ["--schema-root", str(schema_root)]
    return subprocess.run(args, capture_output=True, text=True)  # sys.executable (args[0])


# ---------------------------------------------------------------------------
# Tests — 9 functions
# ---------------------------------------------------------------------------


def test_extract_field_present_number_returns_zero():
    """relic_present_number.json, --key omega_h2 → exit 0; value is a number.

    Float precision binding: WS-2 uses pytest.approx(rel=1e-9) for any float comparison.
    This is a WS-2-owned decision per synthesis §1.3 critic D6.
    """
    cp = _run("relic_present_number.json", key="omega_h2")
    assert cp.returncode == 0
    result = json.loads(cp.stdout)
    assert result["key"] == "omega_h2"
    assert result["value"] == pytest.approx(0.12, rel=1e-9)


def test_extract_field_present_null_returns_zero():
    """relic_present_null.json, --key omega_h2 → exit 0; value is null (schema permits null).

    Distinguishes absent key (KEY_ABSENT, exit 1) from null value (schema-permitted, exit 0).
    """
    cp = _run("relic_present_null.json", key="omega_h2")
    assert cp.returncode == 0
    result = json.loads(cp.stdout)
    assert result["key"] == "omega_h2"
    assert result["value"] is None


def test_extract_field_key_absent_exits_one_KEY_ABSENT():
    """relic_present_number.json, --key nonexistent_key → exit 1, code=KEY_ABSENT."""
    cp = _run("relic_present_number.json", key="nonexistent_key")
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "KEY_ABSENT"


def test_extract_field_schema_version_drift_in_data_exits_one_VERSION_DRIFT():
    """relic_schema_version_v2.json (schema_version='relic/v2'), --schema-version relic/v1 → exit 1, VERSION_DRIFT.

    Data claims relic/v2 but caller requests relic/v1.
    """
    cp = _run("relic_schema_version_v2.json", key="omega_h2", schema_version="relic/v1")
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "VERSION_DRIFT"


def test_extract_field_schema_id_drift_in_file_exits_one_VERSION_DRIFT():
    """tampered_schema_root/relic.schema.json ($id=relic/v2) with --schema-version relic/v1 → exit 1, VERSION_DRIFT.

    Exercises the $id self-check ordering per synthesis §1.3:
    schema file's $id does not end with /relic/v1 → VERSION_DRIFT before validation.
    """
    tampered_root = _FIXTURES / "tampered_schema_root"
    # Use a valid relic/v1 data file but a tampered schema that claims to be v2
    cp = _run("relic_present_number.json", key="omega_h2",
              schema_version="relic/v1", schema_root=tampered_root)
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "VERSION_DRIFT"


def test_extract_field_type_mismatch_exits_one_SCHEMA_MISMATCH():
    """relic_schema_mismatch.json (omega_h2='not-a-number') → exit 1, SCHEMA_MISMATCH.

    JSON schema_version matches but value type violates the schema.
    """
    cp = _run("relic_schema_mismatch.json", key="omega_h2")
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "SCHEMA_MISMATCH"


def test_extract_field_unreadable_file_exits_two_internal(tmp_path):
    """Non-existent file → exit 2, code=EXTRACT_FIELD_INTERNAL."""
    missing = tmp_path / "does_not_exist.json"
    cp = _run("", key="omega_h2", json_path=missing)
    assert cp.returncode == 2
    err = json.loads(cp.stderr)
    assert err["code"] == "EXTRACT_FIELD_INTERNAL"


def test_extract_field_malformed_json_exits_two_internal():
    """relic_malformed.json (unparseable JSON) → exit 2, code=EXTRACT_FIELD_INTERNAL."""
    cp = _run("relic_malformed.json", key="omega_h2")
    assert cp.returncode == 2
    err = json.loads(cp.stderr)
    assert err["code"] == "EXTRACT_FIELD_INTERNAL"


def test_extract_field_disallowed_null_on_scattering_v1_exits_one_SCHEMA_MISMATCH():
    """summary_disallowed_null.json (sigma_si_proton_cm2=null) with scattering/v1 → exit 1, SCHEMA_MISMATCH.

    Cross-validates scattering.schema.json (different schema family from relic/v1 mismatch test).
    The scattering/v1 schema does NOT permit null for sigma_si_proton_cm2 (type: number, minimum: 0).
    """
    cp = _run("summary_disallowed_null.json", key="sigma_si_proton_cm2",
              schema_version="scattering/v1", schema_root=_SHARED_SCHEMAS)
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "SCHEMA_MISMATCH"


# ---------------------------------------------------------------------------
# Conditional 10th PIN test (synthesis §1.3 mandatory docstring)
# ---------------------------------------------------------------------------

def test_extract_field_v1_does_not_support_nested_pointer_PIN():
    """This pins v1 behavior: `--key channel_fractions.bb` is treated as a literal top-level key and exits with KEY_ABSENT. If a future v1.1 adds `--json-pointer`, this test MUST be intentionally rewritten, not deleted — the v1 contract still applies when `--json-pointer` is not passed."""  # noqa: E501
    # relic/v1 has no top-level key named 'channel_fractions.bb'
    cp = _run("relic_present_number.json", key="channel_fractions.bb")
    assert cp.returncode == 1
    err = json.loads(cp.stderr)
    assert err["code"] == "KEY_ABSENT"
