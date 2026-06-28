"""Tier-1 — prepare_point SLHA reader for /looptools eval."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import prepare_point as pp

SLHA = FIXTURES_DIR / "two_hdm_a_point.slha"


def test_reads_dm_mass():
    pt = pp.prepare_point(SLHA)
    assert pt["m_dm_gev"] == pytest.approx(100.0)
    assert pt["dm_pdg"] == pp.DM_PDG_2HDMA


def test_mediator_mass_in_masses():
    pt = pp.prepare_point(SLHA)
    # Map P: physical mediator a is PDG 9931569 (Ah[2]); physical H+- is 9920911
    # (Hm[2]).  PDG 36/37 are the neutral/charged GOLDSTONE slots (~M_Z/~M_W).
    assert pt["masses"][str(pp.MEDIATOR_PDG_2HDMA)] == pytest.approx(400.0)
    assert pt["masses"][str(pp.HPM_PDG_2HDMA)] == pytest.approx(500.0)
    assert pt["masses"]["36"] == pytest.approx(91.1876)   # G0 Goldstone
    assert pt["masses"]["37"] == pytest.approx(80.379)    # G+- Goldstone


def test_params_flattened_and_exclude_mass():
    pt = pp.prepare_point(SLHA)
    # SARAH scheme: gchi is DMSECTOR:2; vd is HMIX:102; MASS entries NOT in params.
    assert pt["params"]["DMSECTOR:2"] == pytest.approx(1.0)   # gchi
    assert pt["params"]["DMSECTOR:1"] == pytest.approx(100.0)  # mchi
    assert pt["params"]["HMIX:102"] == pytest.approx(24.478)   # vd
    assert pt["params"]["ZAMIX:2,3"] == pytest.approx(0.936749700)  # mediator-a row
    assert not any(k.startswith("MASS:") for k in pt["params"])


def test_parse_slha_skips_decay_and_comments():
    text = (
        "BLOCK MASS\n"
        "   9989932  100.0  # chi\n"
        "DECAY 36 1.5\n"
        "   1.0  2  36 -36  # a branching\n"
        "BLOCK FOO\n"
        "   1  7.0\n"
    )
    blocks = pp.parse_slha(text)
    assert blocks["MASS"][(9989932,)] == 100.0
    assert blocks["FOO"][(1,)] == 7.0
    # DECAY body must not leak into a block.
    assert "DECAY" not in blocks


def test_missing_dm_pdg_raises(tmp_path):
    card = tmp_path / "p.slha"
    card.write_text("BLOCK MASS\n   36  400.0\n")
    with pytest.raises(ValueError):
        pp.prepare_point(card, dm_pdg=9989932)


def test_canonical_point_deterministic():
    pt = pp.prepare_point(SLHA)
    assert pp.canonical_point(pt) == pp.canonical_point(pt)
