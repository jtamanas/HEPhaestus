"""test_legacy_hb_slha_results.py — pin the HB-5 SLHA result-block parse.

HiggsBounds-5 in SLHA mode writes its verdict into ``Block HiggsBoundsResults``
inside the SLHA file; stdout carries only BR diagnostics. legacy_driver used to
parse stdout, reporting a vacuous ``obsratio_max = 0.0`` /
``most_sensitive_channel = None`` while the allow/exclude flag looked fine.

Fixture: ``fixtures/singlet_doublet_hb_results.slha`` — the VERBATIM block
HiggsBounds-5.10.2 (LandH) appended to the singlet_doublet SPheno.spc at the
canonical benchmark (MS=150, MPsi=500, yh1=1, theta=0). Real run evidence:
HBresult=1 (allowed), global obsratio 0.6063, most sensitive channel 85 =
(pp)->h1->ZZ->4l (CMS 1312.5353). Note HB-5 semantics: the global obsratio is
that of the most statistically SENSITIVE channel, not the numeric max — the
rank-2 WW channel carries a higher raw obsratio (0.956) but lower sensitivity.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "singlet_doublet_hb_results.slha"


@pytest.fixture(scope="module")
def driver():
    spec = importlib.util.spec_from_file_location(
        "legacy_driver", SKILL_DIR / "scripts" / "legacy_driver.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parsed(driver):
    return driver._parse_hb_slha_results(FIXTURE.read_text())


def test_block_parses(parsed):
    assert parsed is not None, "HiggsBoundsResults block not recognised"


def test_global_verdict_allowed(parsed):
    ms = parsed.most_sensitive_channel
    assert ms is not None
    assert ms.hb_result == 1  # HBresult=1: allowed


def test_global_obsratio_is_sensitive_channel_not_max(parsed):
    """obsratio_max must be the rank-0 (global) 0.6063, NOT the raw per-channel
    max 0.956 (WW, less sensitive) and NOT the pre-fix vacuous 0.0."""
    assert abs(parsed.obsratio_max - 0.60629644976076968) < 1e-12, (
        parsed.obsratio_max
    )
    assert parsed.obsratio_max != 0.0


def test_most_sensitive_channel_identity(parsed):
    ms = parsed.most_sensitive_channel
    assert ms.id == 85
    assert "Z Z" in ms.expref and "1312.5353" in ms.expref


def test_ranked_channels_extracted(parsed):
    assert len(parsed.channels) == 3
    assert [ch.id for ch in parsed.channels] == [85, 59, 197]
    assert abs(parsed.channels[1].obsratio - 0.95644486565298792) < 1e-12
    # All allowed at this point.
    assert all(ch.hb_result == 1 for ch in parsed.channels)


def test_compute_hb_allowed_on_parsed_channels(parsed):
    spec = importlib.util.spec_from_file_location(
        "exclusion", SKILL_DIR / "scripts" / "exclusion.py"
    )
    excl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(excl)
    assert excl.compute_hb_allowed(parsed.channels) is True


def test_absent_block_returns_none(driver):
    """SLHA without the block -> None, so run_higgsbounds falls back to the
    legacy stdout parse instead of fabricating an empty result."""
    assert driver._parse_hb_slha_results("Block MASS\n  25  125.0  # hh\n") is None
