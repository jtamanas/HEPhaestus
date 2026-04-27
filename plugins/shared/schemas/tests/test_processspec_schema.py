"""Tests for plugins/shared/schemas/processspec.schema.json (processspec/v1)."""
import json
import pathlib

import jsonschema
import pytest

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "processspec.schema.json"


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_self_valid(schema):
    """The schema itself must be valid JSON Schema draft-2020-12."""
    jsonschema.Draft202012Validator.check_schema(schema)


def test_positive_canonical_feynarts_example(schema):
    """The canonical example from the /feynarts plan final Phase-0 item 4 must validate."""
    doc = {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [
                {"label": "e-", "pdg": 11, "mass_symbol": "me"},
                {"label": "e+", "pdg": -11, "mass_symbol": "me"},
            ],
            "out": [
                {"label": "mu-", "pdg": 13, "mass_symbol": "mmu"},
                {"label": "mu+", "pdg": -13, "mass_symbol": "mmu"},
            ],
        },
        "loop_order": 1,
        "kinematic_limit": "general",
        "excludes": [],
        "mandelstam": {"s": "s", "t": "t", "u": "u"},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_positive_minimal(schema):
    """Minimal required-only processspec/v1 document must validate."""
    doc = {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [{"label": "chi", "pdg": 1000022, "mass_symbol": "mchi"}],
            "out": [{"label": "chi", "pdg": 1000022, "mass_symbol": "mchi"}],
        },
        "loop_order": 0,
        "kinematic_limit": "heavy_mediator",
        "excludes": [],
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_negative_missing_particles(schema):
    """Document missing required 'particles' must be rejected."""
    doc = {
        "schema_version": "processspec/v1",
        "loop_order": 1,
        "kinematic_limit": "general",
        "excludes": [],
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for missing particles"
    codes = {e.validator for e in errors}
    assert "required" in codes


def test_negative_loop_order_negative(schema):
    """loop_order = -1 must be rejected (minimum: 0)."""
    doc = {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [{"label": "e-", "pdg": 11, "mass_symbol": "me"}],
            "out": [{"label": "e+", "pdg": -11, "mass_symbol": "me"}],
        },
        "loop_order": -1,
        "kinematic_limit": "general",
        "excludes": [],
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for loop_order=-1"


def test_negative_loop_order_too_large(schema):
    """loop_order = 3 must be rejected (maximum: 2)."""
    doc = {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [{"label": "e-", "pdg": 11, "mass_symbol": "me"}],
            "out": [{"label": "e+", "pdg": -11, "mass_symbol": "me"}],
        },
        "loop_order": 3,
        "kinematic_limit": "general",
        "excludes": [],
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for loop_order=3"


def test_negative_invalid_kinematic_limit(schema):
    """An unknown kinematic_limit value must be rejected."""
    doc = {
        "schema_version": "processspec/v1",
        "particles": {
            "in": [{"label": "e-", "pdg": 11, "mass_symbol": "me"}],
            "out": [{"label": "e+", "pdg": -11, "mass_symbol": "me"}],
        },
        "loop_order": 1,
        "kinematic_limit": "ultrasoft",
        "excludes": [],
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for unknown kinematic_limit"
