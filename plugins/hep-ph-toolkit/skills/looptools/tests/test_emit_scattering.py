"""Tier-1 — emit_scattering assembles + validates scattering/v1."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import emit_scattering as es

GOOD_SIGMAS = {
    "sigma_si_proton_cm2": 3.12e-45,
    "sigma_si_neutron_cm2": 2.90e-45,
    "sigma_sd_proton_cm2": None,
    "sigma_sd_neutron_cm2": None,
}


def test_build_has_required_fields():
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x")
    for k in ("schema_version", "m_dm_gev", "sigma_si_proton_cm2", "sigma_si_neutron_cm2",
              "sigma_sd_proton_cm2", "sigma_sd_neutron_cm2", "source", "source_run",
              "nucleon_form_factors"):
        assert k in doc
    assert doc["schema_version"] == "scattering/v1"
    assert doc["source"] == "looptools"


def test_build_valid_passes_schema():
    pytest.importorskip("jsonschema")
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x")
    assert es.validate(doc) == []


def test_extra_provenance_keys_allowed():
    pytest.importorskip("jsonschema")
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x",
                   extra={"model_source": "hand_crafted_sarah_model"})
    assert es.validate(doc) == []
    assert doc["model_source"] == "hand_crafted_sarah_model"


def test_negative_sigma_rejected():
    pytest.importorskip("jsonschema")
    bad = dict(GOOD_SIGMAS, sigma_si_proton_cm2=-1.0)
    doc = es.build(100.0, bad, source_run="run/x")
    assert es.validate(doc)  # non-empty errors


def test_bad_source_run_rejected():
    pytest.importorskip("jsonschema")
    doc = es.build(100.0, GOOD_SIGMAS, source_run="")
    assert es.validate(doc)  # minLength 1 violation


def test_bad_form_factor_preset_rejected():
    pytest.importorskip("jsonschema")
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x", form_factor_preset="bogus")
    assert es.validate(doc)


def test_ddcalc_validator_accepts_output():
    """The downstream /ddcalc validate_scattering must accept our document."""
    pytest.importorskip("jsonschema")
    ddcalc_scripts = TESTS_DIR.parent.parent / "ddcalc" / "scripts"
    sys.path.insert(0, str(ddcalc_scripts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "validate_scattering", str(ddcalc_scripts / "validate_scattering.py")
    )
    vs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vs)
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x")
    # Raises on invalid; returns dict on success.
    assert vs.validate_sigma_json(doc)["source"] == "looptools"


def test_write_round_trips(tmp_path):
    import json
    doc = es.build(100.0, GOOD_SIGMAS, source_run="run/x")
    dest = tmp_path / "scattering.json"
    es.write(dest, doc)
    assert json.loads(dest.read_text())["source"] == "looptools"
