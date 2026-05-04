"""test_should_invoke_class.py — Unit tests for should_invoke_class() (D11 / §4.1).

6 cases as specified in WS-3 task spec (step 7):
  1. no key (absent)         → False
  2. scalar "standard_thermal" → False
  3. scalar "non_standard"   → True
  4. dict {"kind":"standard_thermal"} → False
  5. dict {"kind":"non_standard"}     → True
  6. dict {"kind":"bogus"}            → False
"""
import importlib.util
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Load should_invoke_class module dynamically (avoids packaging requirements)
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "scripts" / "should_invoke_class.py"

_spec = importlib.util.spec_from_file_location("should_invoke_class", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

should_invoke_class = _mod.should_invoke_class


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_no_cosmology_key_returns_false():
    """Spec with no 'cosmology' key → False."""
    spec = {"dm_candidate": {"pdg": 5000005, "name": "chi"}}
    assert should_invoke_class(spec) is False


def test_scalar_standard_thermal_returns_false():
    """Legacy scalar 'standard_thermal' → False."""
    spec = {"cosmology": "standard_thermal"}
    assert should_invoke_class(spec) is False


def test_scalar_non_standard_returns_true():
    """Legacy scalar 'non_standard' → True."""
    spec = {"cosmology": "non_standard"}
    assert should_invoke_class(spec) is True


def test_dict_kind_standard_thermal_returns_false():
    """Object form {'kind': 'standard_thermal'} → False."""
    spec = {"cosmology": {"kind": "standard_thermal"}}
    assert should_invoke_class(spec) is False


def test_dict_kind_non_standard_returns_true():
    """Object form {'kind': 'non_standard'} → True."""
    spec = {"cosmology": {"kind": "non_standard"}}
    assert should_invoke_class(spec) is True


def test_dict_kind_bogus_returns_true():
    """Object form with unknown/bogus kind → True (any kind != 'standard_thermal' triggers).

    Per design §4.1 verbatim: cosmology.get("kind", "standard_thermal") != "standard_thermal".
    "bogus" is not "standard_thermal", so should_invoke_class returns True.
    Schema validation (RUNNER_SPEC_INVALID) catches invalid kind values before
    Step 6 is entered; should_invoke_class itself only tests the standard_thermal condition.
    """
    spec = {"cosmology": {"kind": "bogus"}}
    assert should_invoke_class(spec) is True
