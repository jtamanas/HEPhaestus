"""test_summary_schema.py — validate summary.json against scattering/v1 schema."""
import json
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_SCHEMA_PATH = Path(__file__).resolve().parents[4] / "shared" / "schemas" / "scattering.schema.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def _load_summary() -> dict:
    with open(_FIXTURES / "summary_singletDM.json") as f:
        return json.load(f)


class TestSummarySchemaValidation:
    def test_fixture_validates(self):
        pytest.importorskip("jsonschema")
        import jsonschema
        schema = _load_schema()
        summary = _load_summary()
        jsonschema.validate(summary, schema)

    def test_negative_sigma_rejected(self):
        pytest.importorskip("jsonschema")
        import jsonschema
        schema = _load_schema()
        summary = _load_summary()
        summary["sigma_si_proton_cm2"] = -1e-46
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(summary, schema)

    def test_missing_m_dm_gev_rejected(self):
        pytest.importorskip("jsonschema")
        import jsonschema
        schema = _load_schema()
        summary = _load_summary()
        del summary["m_dm_gev"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(summary, schema)


