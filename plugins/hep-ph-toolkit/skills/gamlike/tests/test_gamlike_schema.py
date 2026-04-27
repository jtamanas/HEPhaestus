"""
test_gamlike_schema.py — JSON-schema validation for all fixtures (T15).
"""
import importlib.util
import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"
_SCHEMA_PATH = _HERE.parent / "contracts" / "gamlike_v1.schema.json"

_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_SCHEMA = json.loads(_SCHEMA_PATH.read_text())

# All successfully-parseable fixtures (excludes malformed_truncated which exits 3)
VALID_FIXTURES = [
    "relic_only_xsi_eq_1_2hdma.txt",
    "relic_only_xsi_eq_1_sd.txt",
    "full_run_xsi_lt_1.txt",
    "full_run_xsi_eq_1.txt",
    "direct_detection_only.txt",
    "spectral_with_lines.txt",
    "spectral_no_peaks_oo_range.txt",
    "fluxes_source.txt",
    "coannihilation_two_initial_states.txt",
    "legacy_omega_h2_alias.txt",
    "malformed_unknown_section.txt",
]


@pytest.mark.parametrize("fixture_name", VALID_FIXTURES)
def test_fixture_validates_against_schema(fixture_name):
    """Each fixture's parsed output validates against gamlike_v1.schema.json."""
    d = _mod.parse_file(_FIXTURES / fixture_name)
    jsonschema.validate(d, _SCHEMA)


def test_schema_is_valid_meta():
    """The schema document itself is valid Draft 2019-09 JSON Schema."""
    jsonschema.Draft201909Validator.check_schema(_SCHEMA)


def test_schema_version_const_enforced():
    """schema_version must be exactly 'gamlike/v1'."""
    d = _mod.parse_file(_FIXTURES / "relic_only_xsi_eq_1_2hdma.txt")
    d["schema_version"] = "gamlike/v2"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(d, _SCHEMA)
