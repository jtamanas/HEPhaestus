"""test_dd_provenance_check.py — wire read_latest_slha into the DD run path.

Asserts ``maddm_run.check_slha_provenance`` verifies the SLHA/param card about
to feed a MadDM direct_detection run against the registered ``latest_slha``:

  * silent + ok on an exact fingerprint match;
  * loud WARNING + ok=False on a sha256 mismatch (wrong/older spectrum);
  * loud WARNING + ok=False when nothing is registered for the model;
  * loud WARNING but non-fatal (ok=True, unverifiable) on a pre-guard config;
  * skipped for non-DD observables (relic-only);
  * fatal=True raises SlhaProvenanceMismatch on a genuine mismatch;
  * non-fatal by default (never raises).

Uses only temp dirs + env-isolated config (no live MadDM / SPheno). FAILS if
the DD provenance wiring is reverted.
"""
from __future__ import annotations

import pytest

import config_helpers
import maddm_run


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


# ── Match: silent + ok ──────────────────────────────────────────────────────

def test_matching_card_is_ok_and_silent(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha(
        "singlet_doublet", str(slha), point="BP1", params={"MS": 200.0},
    )
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(slha), observables=["direct_detection"],
    )
    assert res["ok"] is True
    assert res["reason"] is None
    assert res["used_sha"] == res["registered_sha"]
    assert capsys.readouterr().err.strip() == "", "no warning on a clean match"


# ── Mismatch: loud warning, non-fatal ───────────────────────────────────────

def test_mismatched_card_warns_and_flags(tmp_path, capsys):
    registered = _write_slha(tmp_path, "registered.spc")
    config_helpers.register_latest_slha(
        "singlet_doublet", str(registered), point="BP1",
    )
    # A DIFFERENT card is about to be overlaid for the DD run.
    other = _write_slha(tmp_path, "other.spc", body="BLOCK MASS\n 25 999.0\n")
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(other), observables=["direct_detection"],
    )
    assert res["ok"] is False
    assert res["reason"] == "sha256_mismatch"
    err = capsys.readouterr().err
    assert "WARNING" in err and "does NOT match" in err
    # Both paths + a remediation pointer are surfaced.
    assert str(other) in err and str(registered.resolve()) in err
    assert "Re-run SPheno" in err


def test_default_is_non_fatal(tmp_path):
    """The default path must never raise, even on a mismatch."""
    config_helpers.register_latest_slha(
        "singlet_doublet", str(_write_slha(tmp_path, "a.spc")),
    )
    other = _write_slha(tmp_path, "b.spc", body="different\n")
    # Should return, not raise.
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(other), observables=["direct_detection"],
    )
    assert res["ok"] is False


# ── Missing registration ────────────────────────────────────────────────────

def test_no_registration_warns(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(slha), observables=["direct_detection"],
    )
    assert res["ok"] is False
    assert res["reason"] == "no_registration"
    err = capsys.readouterr().err
    assert "WARNING" in err and "no latest_slha" in err


# ── Pre-guard config: warn but stay non-fatal / unverifiable ────────────────

def test_pre_guard_config_is_unverifiable_not_mismatch(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    # Old-style registration: pointer but no provenance fingerprint.
    config_helpers.register_model("singlet_doublet", latest_slha=str(slha))
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(slha), observables=["direct_detection"],
    )
    assert res["ok"] is True
    assert res["reason"] == "unverifiable"
    assert "WARNING" in capsys.readouterr().err


# ── Unreadable card ─────────────────────────────────────────────────────────

def test_unreadable_card_warns(tmp_path, capsys):
    config_helpers.register_latest_slha(
        "singlet_doublet", str(_write_slha(tmp_path)),
    )
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(tmp_path / "nope.spc"),
        observables=["direct_detection"],
    )
    assert res["ok"] is False
    assert res["reason"] == "used_card_unreadable"
    assert "WARNING" in capsys.readouterr().err


# ── Non-DD observables are skipped ──────────────────────────────────────────

def test_relic_only_is_skipped(tmp_path, capsys):
    other = _write_slha(tmp_path, "other.spc", body="whatever\n")
    config_helpers.register_latest_slha(
        "singlet_doublet", str(_write_slha(tmp_path, "reg.spc")),
    )
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(other), observables=["relic"],
    )
    assert res["ok"] is True
    assert res["skipped"] is True
    assert capsys.readouterr().err.strip() == "", "relic-only run: no DD check"


def test_observables_none_still_checks(tmp_path, capsys):
    """No observables passed → be conservative and still check (not skipped)."""
    config_helpers.register_latest_slha(
        "singlet_doublet", str(_write_slha(tmp_path, "reg.spc")),
    )
    other = _write_slha(tmp_path, "other.spc", body="mismatch\n")
    res = maddm_run.check_slha_provenance("singlet_doublet", str(other))
    assert res["skipped"] is False
    assert res["ok"] is False


# ── fatal=True opt-in ───────────────────────────────────────────────────────

def test_fatal_raises_on_mismatch(tmp_path):
    config_helpers.register_latest_slha(
        "singlet_doublet", str(_write_slha(tmp_path, "reg.spc")),
    )
    other = _write_slha(tmp_path, "other.spc", body="mismatch\n")
    with pytest.raises(maddm_run.SlhaProvenanceMismatch):
        maddm_run.check_slha_provenance(
            "singlet_doublet", str(other),
            observables=["direct_detection"], fatal=True,
        )


def test_fatal_does_not_raise_on_match(tmp_path):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha("singlet_doublet", str(slha))
    res = maddm_run.check_slha_provenance(
        "singlet_doublet", str(slha),
        observables=["direct_detection"], fatal=True,
    )
    assert res["ok"] is True


# ── read_latest_slha's own drift warning is surfaced too ────────────────────

def test_underlying_read_warns_on_point_mismatch(tmp_path, capsys):
    slha = _write_slha(tmp_path)
    config_helpers.register_latest_slha("singlet_doublet", str(slha), point="BP1")
    maddm_run.check_slha_provenance(
        "singlet_doublet", str(slha),
        observables=["direct_detection"], expected_point="BP2",
    )
    # read_latest_slha emits the point-mismatch warning; sha still matches.
    err = capsys.readouterr().err
    assert "BP2" in err and "BP1" in err
