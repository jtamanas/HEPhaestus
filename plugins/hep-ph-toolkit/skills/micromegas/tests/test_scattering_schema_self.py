"""test_scattering_schema_self.py — Phase-0 schema consumer test.

Asserts the scattering/v1 schema authored in Phase-0 is valid
Draft 2020-12. Does NOT author or modify the schema.
"""
import json
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA_PATH = _REPO_ROOT / "plugins" / "shared" / "schemas" / "scattering.schema.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_file_exists():
    assert _SCHEMA_PATH.exists(), f"scattering.schema.json not found at {_SCHEMA_PATH}"


def test_schema_parses_as_json():
    schema = _load_schema()
    assert isinstance(schema, dict)


def test_schema_is_draft_2020_12():
    schema = _load_schema()
    assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema"


def test_schema_is_valid_draft_2020_12():
    pytest.importorskip("jsonschema")
    import jsonschema
    schema = _load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)


def test_schema_id():
    schema = _load_schema()
    assert schema.get("$id") == "https://hep-ph-agents/schemas/scattering/v1"


def test_schema_required_fields():
    schema = _load_schema()
    required = schema.get("required", [])
    for field in ("schema_version", "m_dm_gev", "sigma_si_proton_cm2",
                  "sigma_si_neutron_cm2", "sigma_sd_proton_cm2",
                  "sigma_sd_neutron_cm2", "source", "source_run",
                  "nucleon_form_factors"):
        assert field in required, f"Expected required field {field!r} in schema"
