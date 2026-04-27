"""
test_blocker_schema.py — validates blocker.schema.json against examples.

Tests:
    - One valid instance per mode (fatal, recoverable, reference_only)
    - All known SCREAMING codes validated
    - reference_only missing caveats is rejected
    - reference_only with empty caveats is rejected
    - fatal with empty message is rejected
"""
import json
from pathlib import Path

import pytest
import jsonschema

FIXTURES = Path(__file__).parent / "fixtures"
SHARED = Path(__file__).parent.parent
SCHEMA_PATH = SHARED / "blocker.schema.json"


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def examples():
    with open(FIXTURES / "blocker_examples.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Valid examples (from fixture)
# ---------------------------------------------------------------------------

def test_valid_fatal_example(schema, examples):
    """The fixture fatal blocker validates."""
    fatal = examples[0]
    assert fatal["mode"] == "fatal"
    jsonschema.validate(fatal, schema)


def test_valid_recoverable_example(schema, examples):
    """The fixture recoverable blocker validates."""
    rec = examples[1]
    assert rec["mode"] == "recoverable"
    jsonschema.validate(rec, schema)


def test_valid_reference_only_example(schema, examples):
    """The fixture reference_only blocker validates (PR-D canonical shape)."""
    ref = examples[2]
    assert ref["status"] == "reference_only"
    jsonschema.validate(ref, schema)


# ---------------------------------------------------------------------------
# All known SCREAMING codes
# ---------------------------------------------------------------------------

FATAL_CODES = [
    "SARAH_DOWNLOAD_FAILED",
    "SARAH_SMOKE_TEST_FAILED",
    "SARAH_OUTPUT_MISSING",
    "SARAH_OUTPUT_CORRUPT",
    "ANOMALY_CANCELLATION_FAILED",
    "MODELSPEC_INVALID",
    "WOLFRAM_KERNEL_ABSENT",
    "GFORTRAN_ABSENT",
    "SPHENO_DOWNLOAD_FAILED",
    "SPHENO_BASE_BUILD_FAILED",
    "SPHENO_PATH_INVALID",
    "SPHENO_COMPILE_FAILED",
    "SPHENO_NO_OUTPUT",
]

RECOVERABLE_CODES = [
    "SPHENO_SPECTRUM_PROBLEM",
    "SPHENO_RGE_NONCONVERGENT",
]


@pytest.mark.parametrize("code", FATAL_CODES)
def test_fatal_code_valid(schema, code):
    """Every known fatal code validates against the schema."""
    blocker = {"code": code, "mode": "fatal", "message": "test error"}
    jsonschema.validate(blocker, schema)


@pytest.mark.parametrize("code", RECOVERABLE_CODES)
def test_recoverable_code_valid(schema, code):
    """Every known recoverable code validates against the schema."""
    blocker = {"code": code, "mode": "recoverable", "message": "test warning"}
    jsonschema.validate(blocker, schema)


# ---------------------------------------------------------------------------
# Negative cases
# ---------------------------------------------------------------------------

def test_reference_only_missing_caveats_rejected(schema):
    """reference_only without caveats must be rejected."""
    blocker = {
        "status": "reference_only",
        "reference_method": "some method",
        # missing caveats
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_reference_only_empty_caveats_rejected(schema):
    """reference_only with empty caveats array must be rejected (minItems 1)."""
    blocker = {
        "status": "reference_only",
        "reference_method": "some method",
        "caveats": [],  # minItems: 1
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_reference_only_empty_reference_method_rejected(schema):
    """reference_only with empty reference_method must be rejected."""
    blocker = {
        "status": "reference_only",
        "reference_method": "",  # minLength: 1
        "caveats": ["a caveat"],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_fatal_empty_message_rejected(schema):
    """fatal blocker with empty message must be rejected."""
    blocker = {"code": "GFORTRAN_ABSENT", "mode": "fatal", "message": ""}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_fatal_lowercase_code_rejected(schema):
    """fatal blocker with lowercase code must be rejected (pattern requires SCREAMING)."""
    blocker = {"code": "sarah_download_failed", "mode": "fatal", "message": "oops"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_fatal_with_user_instruction(schema):
    """fatal blocker with optional user_instruction validates."""
    blocker = {
        "code": "WOLFRAM_KERNEL_ABSENT",
        "mode": "fatal",
        "message": "wolframscript not found.",
        "user_instruction": "Install Wolfram Engine from https://wolfram.com/engine/",
    }
    jsonschema.validate(blocker, schema)


def test_fatal_with_context(schema):
    """fatal blocker with optional context object validates."""
    blocker = {
        "code": "SPHENO_COMPILE_FAILED",
        "mode": "fatal",
        "message": "make failed with exit code 2.",
        "context": {"make_output": "error: undeclared identifier 'foo'"},
    }
    jsonschema.validate(blocker, schema)


def test_mode_mix_rejected(schema):
    """A blocker carrying both status=reference_only and mode=fatal must be rejected.

    The schema uses oneOf: the reference_only branch forbids mode/code/message,
    and the fatal branch forbids status/caveats/reference_method.
    A mixed document satisfies neither branch and must fail validation.
    """
    blocker = {
        "status": "reference_only",
        "mode": "fatal",
        "code": "SARAH_DOWNLOAD_FAILED",
        "message": "mixed fields",
        "reference_method": "some method",
        "caveats": ["a caveat"],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(blocker, schema)


def test_sarah_output_corrupt_example_validates(schema):
    """The canonical SARAH_OUTPUT_CORRUPT blocker (plan §5) validates."""
    with open(FIXTURES / "sarah_output_corrupt_example.json") as f:
        blocker = json.load(f)
    jsonschema.validate(blocker, schema)
    assert blocker["code"] == "SARAH_OUTPUT_CORRUPT"
    assert blocker["mode"] == "fatal"
