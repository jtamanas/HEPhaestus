"""test_materialize_template.py — Tests for materialize_template (D8 / §4.4).

Tests as specified in WS-3 task spec (step 9):
  - Round-trip a 5-line template with two {{X}} placeholders + matching overrides;
    assert text equality.
  - Negative: missing override → SystemExit(2).
  - Negative: extra override key not in template → SystemExit(2).
"""
import importlib.util
import pathlib
import pytest

# ---------------------------------------------------------------------------
# Load materialize_template module dynamically
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_SCRIPT = _HERE.parent / "scripts" / "materialize_template.py"

_spec = importlib.util.spec_from_file_location("materialize_template", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

materialize_template = _mod.materialize_template

# ---------------------------------------------------------------------------
# Inline template text
# ---------------------------------------------------------------------------

_TEMPLATE_5_LINE = """\
# CLASS configuration template
H0 = {{H0_value}}
omega_b = 0.02238
Gamma_dcdm = {{Gamma_dcdm}}
# end of template
"""

_EXPECTED_RESULT = """\
# CLASS configuration template
H0 = 67.32
omega_b = 0.02238
Gamma_dcdm = 1e-29
# end of template
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_round_trip_two_placeholders():
    """5-line template with two {{X}} placeholders materialises correctly."""
    overrides = {"H0_value": 67.32, "Gamma_dcdm": 1e-29}
    result = materialize_template(_TEMPLATE_5_LINE, overrides)
    assert result == _EXPECTED_RESULT, (
        f"Materialised text does not match expected.\n"
        f"Expected:\n{_EXPECTED_RESULT!r}\n"
        f"Got:\n{result!r}"
    )


def test_missing_override_raises_systemexit():
    """Template placeholder with no matching override key → SystemExit(2)."""
    overrides = {"H0_value": 67.32}  # Gamma_dcdm is missing
    with pytest.raises(SystemExit) as exc_info:
        materialize_template(_TEMPLATE_5_LINE, overrides)
    assert exc_info.value.code == 2, (
        f"Expected SystemExit(2) for missing override, got exit code {exc_info.value.code}"
    )


def test_extra_override_key_raises_systemexit():
    """Override key not used in template → SystemExit(2)."""
    overrides = {
        "H0_value": 67.32,
        "Gamma_dcdm": 1e-29,
        "UNUSED_KEY": 42,  # not present in template
    }
    with pytest.raises(SystemExit) as exc_info:
        materialize_template(_TEMPLATE_5_LINE, overrides)
    assert exc_info.value.code == 2, (
        f"Expected SystemExit(2) for extra override key, got exit code {exc_info.value.code}"
    )
