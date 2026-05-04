"""test_runner_spec_schema.py — Schema validation tests for runner_spec/v1 (D2 / §8).

INLINE minimal fixtures — does NOT depend on WS-5 fixture files.
Tests as specified in WS-3 task spec (step 8):
  1. valid scalar form
  2. valid object standard_thermal
  3. valid object non_standard + class_template
  4. valid object non_standard + class_config
  5. INVALID object non_standard missing class_preset
  6. INVALID {"Kind":"non_standard"} (wrong capitalisation)
"""
import json
import pathlib

import jsonschema
import pytest

# ---------------------------------------------------------------------------
# Schema path
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
# tests/ → dark-matter-constraints/ → skills/ → hep-ph-toolkit/ → plugins/ → repo
_REPO_ROOT = _HERE.parents[4]
_SCHEMA_PATH = _REPO_ROOT / "plugins" / "shared" / "schemas" / "runner_spec.schema.json"


def _schema() -> dict:
    with open(_SCHEMA_PATH) as fh:
        return json.load(fh)


def _validator() -> jsonschema.Draft7Validator:
    return jsonschema.Draft7Validator(_schema())


# ---------------------------------------------------------------------------
# Valid fixtures (inline)
# ---------------------------------------------------------------------------

_VALID_SCALAR = {
    "dm_candidate": {"pdg": 5000005, "name": "chi"},
    "halo": "shm",
    "cosmology": "standard_thermal",
}

_VALID_OBJECT_STANDARD = {
    "dm_candidate": {"pdg": 5000005, "name": "chi"},
    "cosmology": {"kind": "standard_thermal"},
}

_VALID_OBJECT_NON_STANDARD_TEMPLATE = {
    "dm_candidate": {"pdg": 9000001, "name": "chi", "mass_gev": 100.0},
    "halo": "shm",
    "cosmology": {
        "kind": "non_standard",
        "class_preset": "custom",
        "class_template": "dcdm_minimal",
        "overrides": {"Gamma_dcdm": 1.0e-29, "M_dcdm": 100.0},
        "invoke": ["background"],
    },
}

_VALID_OBJECT_NON_STANDARD_CONFIG = {
    "dm_candidate": {"pdg": 9000001, "name": "chi"},
    "cosmology": {
        "kind": "non_standard",
        "class_preset": "custom",
        "class_config": "/path/to/my_class.ini",
        "invoke": ["background"],
    },
}

# ---------------------------------------------------------------------------
# Invalid fixtures (inline)
# ---------------------------------------------------------------------------

# non_standard but missing class_preset → fails allOf[0] rule
_INVALID_MISSING_CLASS_PRESET = {
    "dm_candidate": {"pdg": 9000001, "name": "chi"},
    "cosmology": {
        "kind": "non_standard",
        # class_preset intentionally absent
        "class_config": "/path/to/my_class.ini",
    },
}

# Wrong capitalisation: "Kind" instead of "kind" → fails schema (enum constraint on "kind")
_INVALID_WRONG_CAPITALISATION = {
    "dm_candidate": {"pdg": 9000001, "name": "chi"},
    "cosmology": {
        "Kind": "non_standard",  # capital K — should fail
    },
}


# ---------------------------------------------------------------------------
# Tests — valid cases
# ---------------------------------------------------------------------------

def test_valid_scalar_form():
    """Legacy scalar 'standard_thermal' passes runner_spec/v1 schema."""
    v = _validator()
    errors = list(v.iter_errors(_VALID_SCALAR))
    assert not errors, f"Valid scalar spec should pass schema, got errors: {errors}"


def test_valid_object_standard_thermal():
    """Object form {kind: standard_thermal} passes runner_spec/v1 schema."""
    v = _validator()
    errors = list(v.iter_errors(_VALID_OBJECT_STANDARD))
    assert not errors, f"Valid standard_thermal object should pass schema, got errors: {errors}"


def test_valid_object_non_standard_with_template():
    """non_standard + class_template (no class_config required) passes schema."""
    v = _validator()
    errors = list(v.iter_errors(_VALID_OBJECT_NON_STANDARD_TEMPLATE))
    assert not errors, f"Valid non_standard+template should pass schema, got errors: {errors}"


def test_valid_object_non_standard_with_class_config():
    """non_standard + class_preset==custom + class_config passes schema."""
    v = _validator()
    errors = list(v.iter_errors(_VALID_OBJECT_NON_STANDARD_CONFIG))
    assert not errors, f"Valid non_standard+class_config should pass schema, got errors: {errors}"


# ---------------------------------------------------------------------------
# Tests — invalid cases
# ---------------------------------------------------------------------------

def test_invalid_non_standard_missing_class_preset():
    """non_standard without class_preset must fail schema validation (allOf required-iff)."""
    v = _validator()
    errors = list(v.iter_errors(_INVALID_MISSING_CLASS_PRESET))
    assert errors, (
        "Expected schema validation errors for non_standard without class_preset, "
        "but no errors were raised."
    )


def test_invalid_wrong_capitalisation():
    """Cosmology dict with 'Kind' (capital K) instead of 'kind' must fail schema validation."""
    v = _validator()
    errors = list(v.iter_errors(_INVALID_WRONG_CAPITALISATION))
    assert errors, (
        "Expected schema validation errors for {Kind: non_standard} (wrong capitalisation), "
        "but no errors were raised."
    )
