"""Tests for plugins/shared/schemas/scattering.schema.json (scattering/v1)."""
import json
import pathlib

import jsonschema
import pytest

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "scattering.schema.json"


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def test_schema_self_valid(schema):
    """The schema itself must be valid JSON Schema draft-2020-12."""
    jsonschema.Draft202012Validator.check_schema(schema)


def test_positive_full_document(schema):
    """A fully populated scattering/v1 document must validate."""
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": 100.0,
        "sigma_si_proton_cm2": 1e-46,
        "sigma_si_neutron_cm2": 1e-46,
        "sigma_sd_proton_cm2": 1e-40,
        "sigma_sd_neutron_cm2": 1e-40,
        "source": "micromegas",
        "source_run": "run_20240101_abc123",
        "nucleon_form_factors": {"preset": "default_2018"},
        "halo": {
            "model": "shm",
            "v0_km_per_s": 220.0,
            "vesc_km_per_s": 544.0,
            "rho0_gev_per_cm3": 0.3,
        },
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_positive_minimal_document(schema):
    """A minimal required-only scattering/v1 document must validate."""
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": 50.0,
        "sigma_si_proton_cm2": 0.0,
        "sigma_si_neutron_cm2": 0.0,
        "sigma_sd_proton_cm2": 0.0,
        "sigma_sd_neutron_cm2": 0.0,
        "source": "looptools",
        "source_run": "run-abc",
        "nucleon_form_factors": {"preset": "A1"},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert errors == [], f"Unexpected validation errors: {errors}"


def test_negative_missing_m_dm_gev(schema):
    """Document missing required m_dm_gev must be rejected."""
    doc = {
        "schema_version": "scattering/v1",
        "sigma_si_proton_cm2": 1e-46,
        "sigma_si_neutron_cm2": 1e-46,
        "sigma_sd_proton_cm2": 1e-40,
        "sigma_sd_neutron_cm2": 1e-40,
        "source": "micromegas",
        "source_run": "run-xyz",
        "nucleon_form_factors": {"preset": "default_2018"},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for missing m_dm_gev"
    codes = {e.validator for e in errors}
    assert "required" in codes


def test_negative_sigma_si_negative(schema):
    """sigma_si_proton_cm2 = -1e-46 must be rejected (minimum: 0)."""
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": 100.0,
        "sigma_si_proton_cm2": -1e-46,
        "sigma_si_neutron_cm2": 1e-46,
        "sigma_sd_proton_cm2": 1e-40,
        "sigma_sd_neutron_cm2": 1e-40,
        "source": "micromegas",
        "source_run": "run-xyz",
        "nucleon_form_factors": {"preset": "default_2018"},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for negative sigma_si_proton_cm2"


def test_negative_m_dm_gev_zero(schema):
    """m_dm_gev = 0 must be rejected (exclusiveMinimum: 0)."""
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": 0,
        "sigma_si_proton_cm2": 1e-46,
        "sigma_si_neutron_cm2": 1e-46,
        "sigma_sd_proton_cm2": 1e-40,
        "sigma_sd_neutron_cm2": 1e-40,
        "source": "micromegas",
        "source_run": "run-xyz",
        "nucleon_form_factors": {"preset": "default_2018"},
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    assert len(errors) > 0, "Expected validation error for m_dm_gev=0"
