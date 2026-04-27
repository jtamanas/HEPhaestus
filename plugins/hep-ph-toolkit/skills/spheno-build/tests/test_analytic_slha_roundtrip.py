"""test_analytic_slha_roundtrip.py — WS-A §8.2.

Verifies analytic_module.compute → slha_writer.render → parse_slha.parse
is a lossless round-trip for masses + SARAH mixing blocks.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"


def _load(name: str, p: Path):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def sd():
    return _load("sd", _SCRIPTS / "analytic_models" / "singlet_doublet.py")


@pytest.fixture(scope="module")
def sw():
    return _load("sw", _SCRIPTS / "slha_writer.py")


@pytest.fixture(scope="module")
def ps():
    return _load("ps", _SCRIPTS / "parse_slha.py")


PARAMS = {"MS": 150.0, "MPsi": 500.0, "yh1": 0.5, "yh2": 0.3}


def test_masses_round_trip(sd, sw, ps, tmp_path):
    r = sd.compute(spec={}, params=PARAMS)
    text = sw.render(r, spec={}, params=PARAMS)
    spc = tmp_path / "rt.spc"
    spc.write_text(text)
    summary = ps.parse(spc)
    for pdg in ("9958431", "9956206", "9979223", "9984071"):
        assert pdg in summary["masses"], (
            f"expected PDG {pdg} in masses, got {sorted(summary['masses'].keys())}"
        )
    assert summary["problems"] == []


def test_znmix_3x3(sd, sw, ps, tmp_path):
    r = sd.compute(spec={}, params=PARAMS)
    text = sw.render(r, spec={}, params=PARAMS)
    spc = tmp_path / "rt.spc"
    spc.write_text(text)
    summary = ps.parse(spc)
    zn = summary["mixing"]["ZNMIX"]
    assert len(zn) == 3
    for i in ("1", "2", "3"):
        for j in ("1", "2", "3"):
            assert j in zn[i]


def test_ummix_upmix_identity(sd, sw, ps, tmp_path):
    r = sd.compute(spec={}, params=PARAMS)
    text = sw.render(r, spec={}, params=PARAMS)
    spc = tmp_path / "rt.spc"
    spc.write_text(text)
    summary = ps.parse(spc)
    assert summary["mixing"]["UMMIX"]["1"]["1"] == 1.0
    assert summary["mixing"]["UPMIX"]["1"]["1"] == 1.0
