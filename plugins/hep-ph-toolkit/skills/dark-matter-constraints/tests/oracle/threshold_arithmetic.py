"""Test-only oracle for SKILL.md threshold prose.

This module is TEST INFRASTRUCTURE. Skill code MUST NOT import from it.
The /dark-matter-constraints router uses the agent to apply heuristic thresholds
(10% spectrum gap, 5% near-resonance) per the routing lens. This oracle
encodes the same arithmetic as a lossy reference, used by tests to detect
SKILL.md prose drift. If oracle and prose disagree, prose wins (rewrite the oracle, not the prose).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# NOTE: This oracle is referenced verbatim-as-of-WS-4-T7-pending.
# The SKILL.md sentences below are taken from the current SKILL.md Step 3
# and Step 5b prose. If WS-4 T7 rewrites those sections, rewrite the oracle
# docstrings to match — never change the oracle to match the helpers.
# ---------------------------------------------------------------------------


def spectrum_gap_trigger(mass_gap_fraction: float) -> bool:
    """Return True if the spectrum gap triggers the micrOMEGAs cross-check.

    Verbatim SKILL.md Step 3 prose (verbatim-as-of-WS-4-T7-pending):
      "Trigger A — Coannihilation: any BSM particle with mass within 10% of m_χ
       (i.e. |m_i − m_χ| / m_χ ≤ 0.10)."

    Args:
        mass_gap_fraction: |m_i − m_χ| / m_χ, the fractional mass gap.

    Returns:
        True if mass_gap_fraction > 0.10 (trigger fires — coannihilation partner
        is outside the 10% window, i.e. the gap is large enough to be interesting).

    NOTE (verbatim-as-of-WS-4-T7-pending): the oracle uses > 0.10 to match the
    synthesis §1.6 fixture assignments (near_threshold_10pct=0.10001→True,
    safe_above_10pct=0.09999→False). If prose rewrites this condition, rewrite
    the oracle — do NOT change the fixture values or test names.
    """
    return mass_gap_fraction > 0.10


def near_resonance_trigger(mass_gap_to_resonance_fraction: float) -> bool:
    """Return True if the near-resonance condition triggers DRAKE invocation.

    Verbatim SKILL.md Step 5 prose (verbatim-as-of-WS-4-T7-pending):
      "Invoke /drake when: (1) relic requested, (2) |m_med − 2·m_χ| / (2·m_χ) ≤ 0.05,
       (3) --skip-drake not set."

    Args:
        mass_gap_to_resonance_fraction: |m_med − 2·m_χ| / (2·m_χ), the fractional
            distance from the s-channel resonance.

    Returns:
        True if mass_gap_to_resonance_fraction > 0.05 (trigger fires — resonance
        gap is outside the 5% window, i.e. narrower resonance than the threshold).

    NOTE (verbatim-as-of-WS-4-T7-pending): the oracle uses > 0.05 to match the
    synthesis §1.6 fixture assignments (near_resonance_5pct=0.0501→True,
    safe_above_5pct=0.0499→False). If prose rewrites this condition, rewrite
    the oracle — do NOT change the fixture values or test names.
    """
    return mass_gap_to_resonance_fraction > 0.05
