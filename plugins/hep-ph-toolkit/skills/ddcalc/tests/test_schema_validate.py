"""
Unit test: validate_scattering.py against scattering/v1 schema.
Tests: happy path (micromegas + looptools fixtures), invalid input, NREFT rejection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))
from validate_scattering import validate_sigma_json  # noqa: E402


class TestSchemaValidate:
    def test_micromegas_sample_valid(self):
        """sigma_micromegas_sample.json must pass schema validation."""
        path = FIXTURES_DIR / "sigma_micromegas_sample.json"
        doc = validate_sigma_json(path)
        assert doc["source"] == "micromegas"
        assert doc["m_dm_gev"] == pytest.approx(100.0)

    def test_looptools_sample_valid(self):
        """sigma_looptools_sample.json must pass schema validation."""
        path = FIXTURES_DIR / "sigma_looptools_sample.json"
        doc = validate_sigma_json(path)
        assert doc["source"] == "looptools"
        assert doc["nucleon_form_factors"]["preset"] == "A1"

    def test_invalid_negative_mass_rejected(self):
        """blocker_invalid_input.json has m_dm_gev=-100 → should raise ValueError."""
        path = FIXTURES_DIR / "blocker_invalid_input.json"
        with pytest.raises(ValueError):
            validate_sigma_json(path)

    def test_missing_required_key_rejected(self):
        """Missing m_dm_gev → ValueError."""
        doc = {
            "schema_version": "scattering/v1",
            "sigma_si_proton_cm2": 1e-46,
            "sigma_si_neutron_cm2": 1e-46,
            "sigma_sd_proton_cm2": 0.0,
            "sigma_sd_neutron_cm2": 0.0,
            "source": "micromegas",
            "source_run": "test",
            "nucleon_form_factors": {"preset": "default_2018"},
        }
        with pytest.raises(ValueError):
            validate_sigma_json(doc)

    def test_negative_sigma_rejected(self):
        """sigma_si_proton_cm2 < 0 → ValueError."""
        doc = {
            "schema_version": "scattering/v1",
            "m_dm_gev": 100.0,
            "sigma_si_proton_cm2": -1e-46,
            "sigma_si_neutron_cm2": 1e-46,
            "sigma_sd_proton_cm2": 0.0,
            "sigma_sd_neutron_cm2": 0.0,
            "source": "micromegas",
            "source_run": "test",
            "nucleon_form_factors": {"preset": "default_2018"},
        }
        with pytest.raises(ValueError):
            validate_sigma_json(doc)

    def test_nreft_coefficients_rejected(self):
        """nreft_coefficients present → ValueError (schema additionalProperties=false
        OR explicit NREFT_NOT_SUPPORTED guard). Either way, the input is rejected."""
        doc = {
            "schema_version": "scattering/v1",
            "m_dm_gev": 100.0,
            "sigma_si_proton_cm2": 1e-46,
            "sigma_si_neutron_cm2": 1e-46,
            "sigma_sd_proton_cm2": 0.0,
            "sigma_sd_neutron_cm2": 0.0,
            "source": "micromegas",
            "source_run": "test",
            "nucleon_form_factors": {"preset": "default_2018"},
            "nreft_coefficients": {"O1": 1.0},
        }
        # Schema has additionalProperties=false → rejected at schema level
        # OR explicit NREFT guard fires if schema allows it.
        # Both cases produce ValueError.
        with pytest.raises(ValueError):
            validate_sigma_json(doc)

    def test_halo_null_valid(self):
        """halo: null is valid (uses SHM defaults)."""
        doc = {
            "schema_version": "scattering/v1",
            "m_dm_gev": 100.0,
            "sigma_si_proton_cm2": 1e-46,
            "sigma_si_neutron_cm2": 1e-46,
            "sigma_sd_proton_cm2": 0.0,
            "sigma_sd_neutron_cm2": 0.0,
            "source": "micromegas",
            "source_run": "test",
            "halo": None,
            "nucleon_form_factors": {"preset": "default_2018"},
        }
        result = validate_sigma_json(doc)
        assert result["halo"] is None

    def test_halo_shm_valid(self):
        """halo with SHM fields in km_per_s convention is valid."""
        doc = {
            "schema_version": "scattering/v1",
            "m_dm_gev": 100.0,
            "sigma_si_proton_cm2": 1e-46,
            "sigma_si_neutron_cm2": 1e-46,
            "sigma_sd_proton_cm2": 0.0,
            "sigma_sd_neutron_cm2": 0.0,
            "source": "micromegas",
            "source_run": "test",
            "halo": {
                "model": "shm",
                "v0_km_per_s": 238.0,
                "vesc_km_per_s": 544.0,
                "rho0_gev_per_cm3": 0.3,
            },
            "nucleon_form_factors": {"preset": "default_2018"},
        }
        result = validate_sigma_json(doc)
        assert result["halo"]["v0_km_per_s"] == pytest.approx(238.0)
