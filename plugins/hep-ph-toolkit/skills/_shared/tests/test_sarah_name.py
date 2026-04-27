"""
test_sarah_name.py — unit tests for the SARAH-name canonicalizer.

Tests per plan W0 item 16:
    - dark_su3   → DarkSU3
    - singlet_doublet → SingletDoublet
    - 2hdm_a → "2hdmA" (leading-digit segment kept as-is, trailing "a" uppercased)
"""
import pytest
from sarah_name import modelspec_name_to_sarah, MODEL_NAME_REGEX


def test_dark_su3():
    """dark_su3 must canonicalize to DarkSU3 (plan acceptance criterion 3)."""
    assert modelspec_name_to_sarah("dark_su3") == "DarkSU3"


def test_singlet_doublet():
    """singlet_doublet must canonicalize to SingletDoublet."""
    assert modelspec_name_to_sarah("singlet_doublet") == "SingletDoublet"


def test_leading_digit_valid():
    """2hdm_a is now valid — regex accepts leading digit (broadened for 2hdm_a fixture).

    _title_part("2hdm"): no alpha prefix → returned as-is → "2hdm"
    _title_part("a"): 1-char alpha → uppercased → "A"
    Result: "2hdmA"
    """
    assert modelspec_name_to_sarah("2hdm_a") == "2hdmA"


def test_leading_underscore_raises():
    """_bad must raise ValueError — regex rejects leading underscore."""
    with pytest.raises(ValueError, match="invalid model name"):
        modelspec_name_to_sarah("_bad")


def test_uppercase_input_raises():
    """DarkSU3 is not a valid modelspec name (uppercase)."""
    with pytest.raises(ValueError, match="invalid model name"):
        modelspec_name_to_sarah("DarkSU3")


def test_single_segment():
    """A single segment with no underscores: 'darksu3' → 'Darksu3'."""
    # No underscore split, so _title_part("darksu3"): alpha prefix "darksu" has
    # len 6 > 2 → capitalize → "Darksu3".
    result = modelspec_name_to_sarah("darksu3")
    assert result == "Darksu3"


def test_triple_segment():
    """Three segments: sm_extended_dark → SMExtendedDark.

    'sm' is a 2-char alpha prefix → uppercased (same rule as 'su' in DarkSU3).
    'extended' and 'dark' are >2 chars → capitalized.
    """
    assert modelspec_name_to_sarah("sm_extended_dark") == "SMExtendedDark"


def test_u1_group():
    """u1 → U1 (len 1 alpha prefix → uppercase)."""
    # model name must match regex: '^[a-z][a-z0-9_]{1,30}$', min length 2
    result = modelspec_name_to_sarah("dark_u1")
    assert result == "DarkU1"


def test_su2_group():
    """su2 → SU2."""
    result = modelspec_name_to_sarah("dark_su2")
    assert result == "DarkSU2"


def test_name_too_short_raises():
    """A one-character name should fail the regex (requires at least 2 chars)."""
    with pytest.raises(ValueError, match="invalid model name"):
        modelspec_name_to_sarah("a")


def test_regex_constant():
    """MODEL_NAME_REGEX is exported and rejects invalid names."""
    assert MODEL_NAME_REGEX.match("dark_su3") is not None
    assert MODEL_NAME_REGEX.match("2hdm_a") is not None   # leading digit now valid
    assert MODEL_NAME_REGEX.match("_bad") is None          # leading underscore invalid
    assert MODEL_NAME_REGEX.match("DarkSU3") is None


# ---------------------------------------------------------------------------
# Known provisional limitations  (DO NOT "fix" without W3 probe data)
# ---------------------------------------------------------------------------
# The current _title_part() only uppercases 1–2-char alpha prefixes.
# Multi-char acronyms (mssm, nmssm, hdm) are NOT handled — they fall back
# to simple capitalize().  These outputs are WRONG by HEP convention but are
# the CORRECT behavior of the provisional rule.
#
# Each test is a separate function so pytest counts them individually and W3
# can override them one-at-a-time with minimal diff noise.
#
# Pin them here so that:
#   (a) a future fixer cannot silently change the heuristic without breaking
#       a visible test, and
#   (b) W3's Day-1 probe has a clean, known baseline to override.


def test_provisional_mssm():
    """mssm → 'Mssm' (provisional; should be 'MSSM' — 4-char alpha not uppercased).

    # TODO(W3): verify against real SARAH — current impl may be wrong
    """
    assert modelspec_name_to_sarah("mssm") == "Mssm"


def test_provisional_nmssm():
    """nmssm → 'Nmssm' (provisional; should be 'NMSSM' — 5-char alpha not uppercased).

    # TODO(W3): verify against real SARAH — current impl may be wrong
    """
    assert modelspec_name_to_sarah("nmssm") == "Nmssm"


def test_provisional_two_hdm():
    """two_hdm → 'TwoHdm' (provisional; should be 'TwoHDM' — 3-char 'hdm' not uppercased).

    # TODO(W3): verify against real SARAH — current impl may be wrong
    """
    assert modelspec_name_to_sarah("two_hdm") == "TwoHdm"


def test_provisional_a_su2_b():
    """a_su2_b → 'ASU2B' (provisional; 1-char 'a' and 'b' are uppercased, 'su2' → 'SU2').

    # TODO(W3): verify against real SARAH — current impl may be wrong
    """
    assert modelspec_name_to_sarah("a_su2_b") == "ASU2B"
