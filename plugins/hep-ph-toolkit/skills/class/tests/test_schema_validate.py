"""
test_schema_validate.py — unit tests for scripts/schema_validate.py.

Tests that valid documents pass and invalid documents raise SchemaValidationError.
Uses the real cosmology.schema.json from plugins/shared/schemas/ (WS-C merged it).

No network, no classy required.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "plugins" / "shared" / "schemas" / "cosmology.schema.json"


def _load_schema_validate():
    spec = importlib.util.spec_from_file_location(
        "schema_validate", SCRIPTS_DIR / "schema_validate.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def schema_validate():
    return _load_schema_validate()


# ---------------------------------------------------------------------------
# Valid documents
# ---------------------------------------------------------------------------

_VALID_LCDM = {
    "schema_version": "cosmology/v1",
    "cosmology_preset": "planck18",
    "outputs": ["cmb"],
    "class_version": "3.3.4",
    "source_run": "2026-05-02T0000Z",
    "bsm_extension": None,
}

_VALID_DCDM = {
    "schema_version": "cosmology/v1",
    "cosmology_preset": "planck18",
    "outputs": ["cmb", "pk"],
    "class_version": "3.3.4",
    "source_run": "2026-05-02T0000Z",
    "bsm_extension": {
        "kind": "dcdm",
        "params": {"Gamma_dcdm": "1.0e-29"},
    },
}

_VALID_BACKGROUND = {
    "schema_version": "cosmology/v1",
    "cosmology_preset": "planck18_act",
    "outputs": ["background"],
    "class_version": "3.3.4",
    "source_run": "test-run-001",
    "bsm_extension": None,
    "results": {
        "background": {
            "output_file": "/tmp/run/background.dat",
        }
    },
}


class TestValidDocuments:
    """Valid documents must pass without raising."""

    def test_valid_lcdm_passes(self, schema_validate):
        schema_validate.validate(_VALID_LCDM, SCHEMA_PATH)

    def test_valid_dcdm_passes(self, schema_validate):
        schema_validate.validate(_VALID_DCDM, SCHEMA_PATH)

    def test_valid_background_passes(self, schema_validate):
        schema_validate.validate(_VALID_BACKGROUND, SCHEMA_PATH)

    def test_all_outputs_passes(self, schema_validate):
        doc = {
            "schema_version": "cosmology/v1",
            "cosmology_preset": "custom",
            "outputs": ["background", "cmb", "pk", "transfer"],
            "class_version": "3.3.4",
            "source_run": "multi-output-run",
        }
        schema_validate.validate(doc, SCHEMA_PATH)

    def test_all_bsm_kinds_pass(self, schema_validate):
        kinds = [
            "dcdm", "idm_baryon", "idm_dr", "idm_photon",
            "exotic_injection", "ncdm_extra",
        ]
        for kind in kinds:
            doc = {
                "schema_version": "cosmology/v1",
                "cosmology_preset": "planck18",
                "outputs": ["cmb"],
                "class_version": "3.3.4",
                "source_run": f"test-{kind}",
                "bsm_extension": {"kind": kind, "params": {}},
            }
            schema_validate.validate(doc, SCHEMA_PATH)


class TestInvalidDocuments:
    """Invalid documents must raise SchemaValidationError."""

    def test_missing_schema_version_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        del doc["schema_version"]
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_wrong_schema_version_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["schema_version"] = "cosmology/v2"
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_missing_outputs_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        del doc["outputs"]
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_empty_outputs_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["outputs"] = []
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_invalid_output_value_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["outputs"] = ["montepython"]
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_missing_class_version_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        del doc["class_version"]
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_invalid_class_version_format_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["class_version"] = "v3.3.4"  # must not have 'v' prefix
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_missing_source_run_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        del doc["source_run"]
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_invalid_preset_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["cosmology_preset"] = "planck15"
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)

    def test_invalid_bsm_kind_raises(self, schema_validate):
        doc = dict(_VALID_LCDM)
        doc["bsm_extension"] = {"kind": "montepython", "params": {}}
        with pytest.raises(schema_validate.SchemaValidationError):
            schema_validate.validate(doc, SCHEMA_PATH)


class TestSchemaPath:
    """Test that the schema file is accessible and valid JSON Schema."""

    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self):
        import json
        data = json.loads(SCHEMA_PATH.read_text())
        assert isinstance(data, dict)

    def test_schema_version_is_cosmology_v1(self):
        import json
        data = json.loads(SCHEMA_PATH.read_text())
        # The const should be cosmology/v1
        props = data.get("properties", {})
        sv = props.get("schema_version", {})
        assert sv.get("const") == "cosmology/v1"
