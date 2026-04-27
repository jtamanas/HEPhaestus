"""test_oracle_thresholds.py — WS-2 oracle arithmetic tests.

Skill code MUST NOT import from tests.oracle — this module is TEST INFRASTRUCTURE only.
The /dark-matter-constraints router uses the agent (not this oracle) to apply thresholds.

See: tests/oracle/threshold_arithmetic.py for the oracle module.
See: tests/fixtures/spectra/ for the synthetic spectrum fixtures consumed here.
"""
from __future__ import annotations

import json
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Import oracle (test infra only — skill code must never import this path)
# ---------------------------------------------------------------------------
# Use conftest canonical _HERE (single source of truth) instead of redefining here.
from .conftest import _HERE  # noqa: E402
_SPECTRA = _HERE / "fixtures" / "spectra"

from tests.oracle.threshold_arithmetic import (  # noqa: E402
    near_resonance_trigger,
    spectrum_gap_trigger,
)


# ---------------------------------------------------------------------------
# Tests — 4 cases, no equality-boundary case (per synthesis §1.6)
# ---------------------------------------------------------------------------


def test_oracle_threshold_above_fires():
    """mass_gap_fraction = 0.10001 => spectrum_gap_trigger returns True (fires).

    This pins the coannihilation-trigger direction: a spectrum gap fraction
    just above 0 but within 10% of m_chi must fire the cross-check.
    Verbatim oracle header: 'Skill code MUST NOT import from it.'
    """
    fixture = json.loads((_SPECTRA / "near_threshold_10pct.json").read_text())
    gap = fixture["mass_gap_fraction"]
    assert gap == pytest.approx(0.10001, rel=1e-9)
    assert spectrum_gap_trigger(gap) is True


def test_oracle_threshold_below_does_not_fire():
    """mass_gap_fraction = 0.09999 => spectrum_gap_trigger returns False (silent).

    This pins the coannihilation-trigger direction: a spectrum gap fraction
    safely below 10% must NOT fire the cross-check.
    Verbatim oracle header: 'Skill code MUST NOT import from it.'
    """
    fixture = json.loads((_SPECTRA / "safe_above_10pct.json").read_text())
    gap = fixture["mass_gap_fraction"]
    assert gap == pytest.approx(0.09999, rel=1e-9)
    assert spectrum_gap_trigger(gap) is False


def test_oracle_resonance_5pct_above_fires():
    """mass_gap_to_resonance_fraction = 0.0501 => near_resonance_trigger returns True.

    This pins the DRAKE-invocation direction: a resonance gap fraction
    just above 0 but within 5% fires the narrow-resonance branch.
    Verbatim oracle header: 'Skill code MUST NOT import from it.'
    """
    fixture = json.loads((_SPECTRA / "near_resonance_5pct.json").read_text())
    res_gap = fixture["mass_gap_to_resonance_fraction"]
    assert res_gap == pytest.approx(0.0501, rel=1e-9)
    assert near_resonance_trigger(res_gap) is True


def test_oracle_resonance_5pct_below_does_not_fire():
    """mass_gap_to_resonance_fraction = 0.0499 => near_resonance_trigger returns False.

    This pins the DRAKE-invocation direction: a resonance gap fraction
    safely below 5% must NOT fire the narrow-resonance branch.
    Verbatim oracle header: 'Skill code MUST NOT import from it.'
    """
    fixture = json.loads((_SPECTRA / "safe_above_5pct.json").read_text())
    res_gap = fixture["mass_gap_to_resonance_fraction"]
    assert res_gap == pytest.approx(0.0499, rel=1e-9)
    assert near_resonance_trigger(res_gap) is False
