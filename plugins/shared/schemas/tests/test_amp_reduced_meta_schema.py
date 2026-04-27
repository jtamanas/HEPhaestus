"""Tests for plugins/shared/schemas/amp_reduced.meta.schema.json (amp_reduced.meta/v1)."""
import json
import pathlib

import jsonschema
import pytest

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "amp_reduced.meta.schema.json"

# A valid SHA-256 hex string (64 lowercase hex chars)
VALID_SHA256 = "a" * 64


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _valid_doc():
    return {
        "schema_version": "amp_reduced.meta/v1",
        "formcalc_version": "9.9",
        "form_version": "4.3",
        "looptools_version": "2.16",
        "gamma5_scheme": "naive",
        "pv_heads": "formcalc-native",
        "abbreviations_manifest": "abbr.m",
        "input_hashes": {
            "feynamplist_m": VALID_SHA256,
            "processspec_json": VALID_SHA256,
        },
        "kinematic_limit": "general",
        "ir_flags": {
            "ir_divergent": False,
            "uv_regularized": True,
        },
        "caveats": [],
        "produced_at": "2024-01-01T00:00:00Z",
        "wolfram_version_major_minor": "14.1",
    }


def test_schema_self_valid(schema):
    """The schema itself must be valid JSON Schema draft-2020-12."""
    jsonschema.Draft202012Validator.check_schema(schema)


def test_positive_full_document(schema):
    """A fully populated amp_reduced.meta/v1 document must validate."""
    doc = _valid_doc()
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_positive_pv_heads_formcalc_native(schema):
    """pv_heads: 'formcalc-native' is the only accepted value."""
    doc = _valid_doc()
    doc["pv_heads"] = "formcalc-native"
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_negative_wrong_pv_heads(schema):
    """pv_heads with a value other than 'formcalc-native' must be rejected."""
    doc = _valid_doc()
    doc["pv_heads"] = "custom"
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for wrong pv_heads"


def test_negative_missing_feynamplist_m(schema):
    """Document missing input_hashes.feynamplist_m must be rejected."""
    doc = _valid_doc()
    doc["input_hashes"] = {"processspec_json": VALID_SHA256}
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for missing feynamplist_m"
    codes = {e.validator for e in errors}
    assert "required" in codes


def test_negative_bad_sha256_pattern(schema):
    """input_hashes.feynamplist_m with wrong length must be rejected."""
    doc = _valid_doc()
    doc["input_hashes"]["feynamplist_m"] = "deadbeef"  # too short
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for bad SHA256 pattern"


def test_negative_invalid_gamma5_scheme(schema):
    """Unknown gamma5_scheme value must be rejected."""
    doc = _valid_doc()
    doc["gamma5_scheme"] = "chiral"
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for unknown gamma5_scheme"


def test_negative_bad_wolfram_version_pattern(schema):
    """wolfram_version_major_minor not matching ^[0-9]+\\.[0-9]+$ must be rejected."""
    doc = _valid_doc()
    doc["wolfram_version_major_minor"] = "14"  # missing minor
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for bad wolfram version format"
