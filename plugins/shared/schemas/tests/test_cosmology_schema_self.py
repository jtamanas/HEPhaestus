"""Tests for plugins/shared/schemas/cosmology.schema.json (cosmology/v1)."""
import json
import pathlib

import jsonschema
import pytest

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "cosmology.schema.json"


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_self_valid(schema):
    """The schema itself must be valid JSON Schema draft-2020-12."""
    jsonschema.Draft202012Validator.check_schema(schema)


def test_positive_lcdm(schema):
    """A good LCDM cosmology/v1 document must validate."""
    doc = {
        "schema_version": "cosmology/v1",
        "cosmology_preset": "planck18",
        "outputs": ["cmb", "background"],
        "class_version": "3.3.4",
        "source_run": "run_20260502_abc123",
        "bsm_extension": None,
        "results": {
            "cmb": {"cls_file": "cls.dat", "lmax": 2500},
            "background": {"bg_file": "background.dat"},
        },
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_positive_dcdm(schema):
    """A good DCDM BSM-extension cosmology/v1 document must validate."""
    doc = {
        "schema_version": "cosmology/v1",
        "cosmology_preset": "planck18",
        "outputs": ["cmb", "pk"],
        "class_version": "3.3.4",
        "source_run": "run_20260502_dcdm_001",
        "bsm_extension": {
            "kind": "dcdm",
            "params": {
                "Gamma_dcdm": 1e-3,
                "f_dcdm": 0.1,
            },
        },
        "results": {},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_negative_missing_required(schema):
    """A document missing required fields must be rejected."""
    doc = {
        "schema_version": "cosmology/v1",
        # missing: cosmology_preset, outputs, class_version, source_run
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation errors for missing required fields"
    codes = {e.validator for e in errors}
    assert "required" in codes
