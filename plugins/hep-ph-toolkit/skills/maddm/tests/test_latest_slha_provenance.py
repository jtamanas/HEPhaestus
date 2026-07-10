"""test_latest_slha_provenance.py — Task 2: latest_slha provenance guard.

Asserts:
  * provenance (path/sha256/point/params/recorded_at) is recorded on write;
  * read warns loudly on hash mismatch (card changed under the pointer);
  * read warns loudly on point/param mismatch;
  * read is silent on a full match;
  * backward compatible with configs lacking provenance (no crash, warns).

FAILS if register_latest_slha / read_latest_slha guard is reverted.
"""
from __future__ import annotations

import hashlib

import pytest

import config_helpers


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))
    config_helpers._reload_roots()
    yield
    config_helpers._reload_roots()


def _write_slha(tmp_path, name="spectrum.spc", body="BLOCK MASS\n 25 125.0\n"):
    p = tmp_path / name
    p.write_text(body)
    return p


# ── Write records provenance ────────────────────────────────────────────────

def test_register_latest_slha_records_provenance(tmp_path):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha(
        "singlet_doublet", str(slha),
        point="BP1", params={"MS": 200.0, "MPsi": 400.0, "theta": 0.1},
    )
    entry = config_helpers.get_model("singlet_doublet")
    assert entry["latest_slha"] == str(slha.resolve())
    prov = entry["latest_slha_provenance"]
    assert prov["point"] == "BP1"
    assert prov["params"]["MS"] == 200.0
    assert prov["sha256"] == hashlib.sha256(slha.read_bytes()).hexdigest()
    assert "recorded_at" in prov


def test_register_latest_slha_upserts_extra_fields(tmp_path):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha(
        "singlet_doublet", str(slha), point="BP1",
        spheno_bin="/fake/spheno", latest_run="run_01",
    )
    entry = config_helpers.get_model("singlet_doublet")
    assert entry["spheno_bin"] == "/fake/spheno"
    assert entry["latest_run"] == "run_01"


# ── Read: silent on a match ─────────────────────────────────────────────────

def test_read_silent_on_full_match(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha(
        "singlet_doublet", str(slha), point="BP1",
        params={"MS": 200.0},
    )
    path = config_helpers.read_latest_slha(
        "singlet_doublet", expected_point="BP1", expected_params={"MS": 200.0},
    )
    assert path == str(slha.resolve())
    assert capsys.readouterr().err.strip() == "", "no warning on a clean match"


# ── Read: warns on hash mismatch ────────────────────────────────────────────

def test_read_warns_on_hash_mismatch(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha("singlet_doublet", str(slha), point="BP1")
    # Mutate the file under the pointer.
    slha.write_text("BLOCK MASS\n 25 130.0\n")
    path = config_helpers.read_latest_slha("singlet_doublet")
    assert path == str(slha.resolve())  # still returns the path
    err = capsys.readouterr().err
    assert "WARNING" in err and "changed under the pointer" in err


# ── Read: warns on point / param mismatch ───────────────────────────────────

def test_read_warns_on_point_mismatch(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha("singlet_doublet", str(slha), point="BP1")
    config_helpers.read_latest_slha("singlet_doublet", expected_point="BP2")
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "BP2" in err and "BP1" in err


def test_read_warns_on_param_mismatch(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha(
        "singlet_doublet", str(slha), point="BP1", params={"MS": 200.0},
    )
    config_helpers.read_latest_slha(
        "singlet_doublet", expected_params={"MS": 999.0},
    )
    err = capsys.readouterr().err
    assert "WARNING" in err


# ── Read: backward compatibility with pre-guard configs ─────────────────────

def test_read_backward_compatible_no_provenance(tmp_path, capsys):
    """A config that set latest_slha the old way (no provenance) must not crash;
    it warns that provenance is unavailable."""
    slha = _write_slha(tmp_path)
    config_helpers.register_model("singlet_doublet", latest_slha=str(slha))
    path = config_helpers.read_latest_slha("singlet_doublet")
    assert path == str(slha)
    err = capsys.readouterr().err
    assert "WARNING" in err and "no provenance" in err


def test_read_absent_model_returns_none(capsys):
    assert config_helpers.read_latest_slha("no_such_model") is None
    assert "WARNING" in capsys.readouterr().err


def test_read_no_pointer_returns_none(tmp_path, capsys):
    config_helpers.register_model("singlet_doublet", ufo_path="/fake/ufo")
    assert config_helpers.read_latest_slha("singlet_doublet") is None
    assert "WARNING" in capsys.readouterr().err
