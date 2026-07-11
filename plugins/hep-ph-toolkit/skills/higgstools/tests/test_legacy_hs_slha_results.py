"""test_legacy_hs_slha_results.py — pin the HS-2 SLHA result-block parse and
the loud no-result guard.

HiggsSignals-2 in SLHA mode writes its chi^2 into ``Block HiggsSignalsResults``
inside the SLHA file (parallel to HB's ``HiggsBoundsResults``); nothing lands on
stdout. The as-shipped driver (a) invoked HS with 5 args instead of the required
6, so HS printed "Incorrect number of parameters given on command line" and did
a Fortran STOP that EXITS 0, and (b) regex-grepped stdout for chi^2 that HS
never prints — silently returning a hardcoded chi2_total=0.0/ndf=0, making
``hs_consistent`` vacuously True for EVERY model. These tests pin the fix:

* the real block parses to chi^2_total=118.84 over 111 observables (the live
  HS-2.6.2 verdict on the canonical singlet_doublet SPheno.spc, p~=0.288);
* the fake-χ²=0 shape (HS exits 0, writes no block) now RAISES
  HIGGSTOOLS_HS_NO_RESULT instead of returning a vacuous "consistent".
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "singlet_doublet_hs_results.slha"
FIXTURE_FULL_SLHA = Path(__file__).parent / "fixtures" / "singlet_doublet_spheno.slha"


@pytest.fixture(scope="module")
def driver():
    import sys
    # p_value lives alongside legacy_driver and is imported inside it.
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "legacy_driver", SKILL_DIR / "scripts" / "legacy_driver.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parsed(driver):
    return driver._parse_hs_slha_results(FIXTURE.read_text())


# ── the real block parses to the real chi^2, not the fake 0 ────────────────
def test_block_parses(parsed):
    assert parsed is not None, "HiggsSignalsResults block not recognised"


def test_chi2_total_is_real_not_zero(parsed):
    assert parsed.chi2_total != 0.0
    assert abs(parsed.chi2_total - 118.83753990) < 1e-6, parsed.chi2_total


def test_chi2_rates_and_masses(parsed):
    assert abs(parsed.chi2_rates - 118.41693901) < 1e-6
    assert abs(parsed.chi2_masses - 0.42060089) < 1e-6


def test_ndf_from_observable_counts(parsed):
    # signal-strength observables = 34 (peak) + 56 (STXS) + 20 (Run-1) = 110
    assert parsed.ndf_rates == 110
    # Higgs mass observables = 1
    assert parsed.ndf_masses == 1


def test_total_p_value_matches_hs(parsed):
    # HS's own Probability(total) for chi2=118.838 over 111 obs is 0.28820622.
    import scipy.stats
    p_total = float(scipy.stats.chi2.sf(parsed.chi2_total, parsed.ndf_rates + parsed.ndf_masses))
    assert abs(p_total - 0.28820622) < 1e-4, p_total


def test_absent_block_returns_none(driver):
    """SLHA without the block -> None, so run_higgssignals raises the loud
    no-result blocker instead of fabricating a chi2=0 'consistent'."""
    assert driver._parse_hs_slha_results("Block MASS\n  25  125.0  # hh\n") is None


def test_last_block_wins(driver):
    """HS appends a fresh block on each invocation; the parser must take the
    LAST (most recent) one."""
    two = (
        "BLOCK HiggsSignalsResults\n"
        "    8   111   # total\n"
        "   17   999.0   # chi^2 (total)  -- STALE prior run\n"
        "\n"
        + FIXTURE.read_text()
    )
    parsed = driver._parse_hs_slha_results(two)
    assert abs(parsed.chi2_total - 118.83753990) < 1e-6


# ── hermetic: the fake-χ²=0 (exit-0, no-block) shape now RAISES ─────────────
def _fake_hs_build(tmp_path: Path) -> Path:
    build = tmp_path / "hs_build"
    build.mkdir(exist_ok=True)
    binary = build / "HiggsSignals"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    return build


class TestHsNoResultGuard:
    def test_correct_args_and_block_readback(self, driver, tmp_path, monkeypatch):
        """Pin the 6-arg invocation shape AND the block read-back: real chi^2,
        not the vacuous 0."""
        hs_build = _fake_hs_build(tmp_path)
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        slha = run_dir / "SPheno.spc"
        slha.write_text("Block MASS\n  25  125.09  # hh\n")

        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["cwd"] = kwargs.get("cwd")
            # Simulate HS-2: append the results block to the SLHA in cwd.
            target = Path(kwargs["cwd"]) / cmd[-1]
            target.write_text(target.read_text() + "\n" + FIXTURE.read_text())

            class P:
                returncode = 0
                stdout = " BR(h 1 ->WW)= 0.22\n"
                stderr = ""
            return P()

        monkeypatch.setattr(driver.subprocess, "run", fake_run)
        result = driver.run_higgssignals(str(hs_build), str(slha), 1, 0)

        # 6 positional args: expdata pdf whichinput nHzero nHplus prefix.
        assert captured["cmd"][1:] == ["latestresults", "2", "SLHA", "1", "0", "SPheno.spc"], captured["cmd"]
        assert captured["cwd"] == str(run_dir)
        assert abs(result.chi2_total - 118.83753990) < 1e-6
        assert result.chi2_total != 0.0

    def test_wrong_arg_count_exit0_raises(self, driver, tmp_path, monkeypatch):
        """HS exiting 0 after the 'Incorrect number of parameters' banner,
        writing no block, must raise HIGGSTOOLS_HS_NO_RESULT — not return a
        vacuous chi2=0 'consistent'."""
        hs_build = _fake_hs_build(tmp_path)
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        slha = run_dir / "SPheno.spc"
        slha.write_text("Block MASS\n  25  125.09  # hh\n")

        def fake_run(cmd, **kwargs):
            class P:
                returncode = 0
                stdout = " Incorrect number of parameters given on command line\n"
                stderr = ""
            return P()

        monkeypatch.setattr(driver.subprocess, "run", fake_run)
        with pytest.raises(driver.HiggsSignalsNoResultError) as ei:
            driver.run_higgssignals(str(hs_build), str(slha), 1, 0)
        assert ei.value.code == "HIGGSTOOLS_HS_NO_RESULT"
        assert ei.value.mode == "recoverable"
        assert ei.value.context.get("bad_arg_count") is True


# ── gated live-binary test: real HiggsSignals on the canonical spectrum ─────
def _hs_build_dir() -> Path | None:
    import json as _json
    import os as _os
    cfg = (
        Path(_os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "hephaestus" / "config.json"
    )
    if not cfg.exists():
        return None
    try:
        path = _json.loads(cfg.read_text()).get("higgssignals_path", "")
    except Exception:
        return None
    if not path:
        return None
    build = Path(path)
    for cand in (build / "HiggsSignals", build / "bin" / "HiggsSignals"):
        if cand.is_file():
            return build
    return None


_HS_BUILD = _hs_build_dir()


@pytest.mark.skipif(
    _HS_BUILD is None,
    reason="HiggsSignals legacy binary not registered in "
    "~/.config/hephaestus/config.json (higgssignals_path)",
)
def test_real_hs_yields_real_chi2(driver, tmp_path):
    """Live regression for the silent no-op: the real HS-2.6.2 binary, invoked
    with the corrected 6-arg command line on the canonical singlet_doublet
    SPheno.spc, must return the real chi^2 (~118.84 over 111 obs, p~=0.288) —
    NOT the pre-fix vacuous chi2_total=0.0/ndf=0."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    slha = run_dir / "SPheno.spc"
    slha.write_text(FIXTURE_FULL_SLHA.read_text())

    result = driver.run_higgssignals(str(_HS_BUILD), str(slha), 1, 0)

    assert result.chi2_total != 0.0, "vacuous chi2=0 — HS silent no-op not fixed"
    assert abs(result.chi2_total - 118.84) < 0.5, result.chi2_total
    assert result.ndf_rates + result.ndf_masses == 111
    # p(total) ~ 0.288
    import scipy.stats
    p_total = float(scipy.stats.chi2.sf(result.chi2_total, result.ndf_rates + result.ndf_masses))
    assert abs(p_total - 0.288) < 0.02, p_total
