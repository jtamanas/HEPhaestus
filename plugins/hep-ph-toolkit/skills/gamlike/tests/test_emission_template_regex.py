"""
test_emission_template_regex.py — D14 whitespace-tolerance matrix.

Each row of the producer emission template → test that the canonical KV regex
captures (key, value, comment) correctly.

Scope: REGEX CAPTURE ONLY (per critic §3 issue 4 / T13). Not JSON conversion.
"""
import importlib.util
from pathlib import Path

import pytest

# Load the parser module
_SCRIPT = Path(__file__).parent.parent / "scripts" / "parse_maddm_results.py"
_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_parse_kv = _mod._parse_kv


# ── Test matrix ────────────────────────────────────────────────────────────────
# Each tuple: (producer_line, expected_key, expected_value, expected_comment_substr)

MATRIX = [
    # Clean numeric
    (
        "Omegah2                       = 1.05e+01",
        "Omegah2", "1.05e+01", "",
    ),
    # Trailing space + \t # comment (xsi line, :3475)
    (
        "xsi                           = 1.00e+00 \t # xsi = (Omega/Omega_Planck)",
        "xsi", "1.00e+00", "xsi",
    ),
    # Trailing space + \t # comment (sigmav_xf line, :3477)
    (
        "sigmav_xf                     = 8.42e-27 \t # cm^3 s^-1",
        "sigmav_xf", "8.42e-27", "cm^3",
    ),
    # Fermi_pvalue(Thermal) trailing \n  quirk (:3574)
    (
        "Fermi_pvalue(Thermal)         = 1.23e-01 \n ",
        "Fermi_pvalue(Thermal)", "1.23e-01", "",
    ),
    # Bracketed pair + space-padded comment (:3493-3497)
    (
        "Xenon1T_2018_SI               = [1.23e-45,3.40e-46]   # XENON1T 2018 (SI)",
        "Xenon1T_2018_SI", "[1.23e-45,3.40e-46]", "XENON1T",
    ),
    # String label value (peak states, :3589)
    (
        "peak_0(states)                = chichibar_zh",
        "peak_0(states)", "chichibar_zh", "",
    ),
    # taacsID# key (:3531)
    (
        "chichibar_bbx                 = [1.20e-30,2.30e-29]",
        "chichibar_bbx", "[1.20e-30,2.30e-29]", "",
    ),
    # Percent suffix (:3479-3480)
    (
        "%_relic_chichibar_wphm        = 17.84 %",
        "%_relic_chichibar_wphm", "17.84", "",
    ),
    # NaN value (D15 edge case)
    (
        "Total_xsec                    = nan",
        "Total_xsec", "nan", "",
    ),
    # Legacy Omega h^2 alias (D8)
    (
        "Omega h^2                     = 1.05e+01",
        "Omega h^2", "1.05e+01", "",
    ),
    # nan % (real sd fixture)
    (
        "%_chi1chi1_zz                 = nan %",
        "%_chi1chi1_zz", "nan %", "",
    ),
    # -2*log(Likelihood)_0 (spectral)
    (
        "-2*log(Likelihood)_0          = 4.56e+00",
        "-2*log(Likelihood)_0", "4.56e+00", "",
    ),
    # p-value_0
    (
        "p-value_0                     = 1.02e-01",
        "p-value_0", "1.02e-01", "",
    ),
    # Negative numeric
    (
        "Fermi_Likelihood              = -1.23e+01",
        "Fermi_Likelihood", "-1.23e+01", "",
    ),
]


@pytest.mark.parametrize("line, exp_key, exp_val, exp_comment_substr", MATRIX)
def test_kv_regex_captures(line, exp_key, exp_val, exp_comment_substr):
    result = _parse_kv(line)
    assert result is not None, f"KV regex returned None for line: {line!r}"
    key, val, comment = result
    assert key.strip() == exp_key.strip(), f"Key mismatch: {key!r} != {exp_key!r}"
    assert val.strip() == exp_val.strip(), f"Value mismatch: {val!r} != {exp_val!r}"
    if exp_comment_substr:
        assert exp_comment_substr in comment, (
            f"Comment '{comment!r}' does not contain '{exp_comment_substr!r}'"
        )
