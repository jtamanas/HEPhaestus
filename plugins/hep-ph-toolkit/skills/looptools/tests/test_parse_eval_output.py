"""Tier-1 — parse_eval_output (driver output transport + finiteness gate)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import parse_eval_output as peo

FIXTURE = FIXTURES_DIR / "eval_output.json"


def _load():
    return json.loads(FIXTURE.read_text())


def test_fixture_parses():
    doc = peo.parse(FIXTURE)
    assert doc["m_dm_gev"] == 100.0
    assert doc["effective_couplings"]["f_p_si_gev_minus2"] == pytest.approx(-5.2450498456709965e-11)


def test_accepts_dict_and_path_and_string():
    d = _load()
    assert peo.parse(d)["point_id"] == d["point_id"]
    assert peo.parse(str(FIXTURE))["point_id"] == d["point_id"]
    assert peo.parse(json.dumps(d))["point_id"] == d["point_id"]


def test_wrong_schema_rejected():
    d = _load()
    d["schema"] = "wrong/v1"
    with pytest.raises(ValueError):
        peo.parse(d)


def test_missing_key_rejected():
    d = _load()
    del d["effective_couplings"]
    with pytest.raises(ValueError):
        peo.parse(d)


def test_nonfinite_flag_raises():
    d = _load()
    d["amplitude"]["finite"] = False
    with pytest.raises(peo.AmplitudeNonFinite):
        peo.parse(d)


def test_residual_uv_pole_raises():
    d = _load()
    d["amplitude"]["uv_pole_residue"] = 1.0
    with pytest.raises(peo.AmplitudeNonFinite):
        peo.parse(d)


def test_gauge_dependence_raises():
    d = _load()
    d["amplitude"]["gauge_parameter_dependence"] = 0.5
    with pytest.raises(peo.AmplitudeNonFinite):
        peo.parse(d)


def test_nan_coupling_raises():
    d = _load()
    d["effective_couplings"]["f_p_si_gev_minus2"] = float("nan")
    with pytest.raises(peo.AmplitudeNonFinite):
        peo.parse(d)
