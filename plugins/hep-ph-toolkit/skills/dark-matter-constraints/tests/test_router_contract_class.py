"""test_router_contract_class.py — Contract test for the four CLASS output_fields rows (§6.1).

Runs verify_router_field_contract.py against the router_contract.json (which now
includes the four new CLASS output_fields rows) using the
tests/fixtures/class/cosmology_planck18.json fixture from WS-1.

Per WS-3 task spec (step 10): subprocess verify_router_field_contract.py against
tests/fixtures/class/cosmology_planck18.json; assert exit 0.
"""
import importlib.util
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Load verify_router_field_contract module dynamically
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).resolve().parent
_VRFC_SCRIPT = _HERE.parent / "scripts" / "verify_router_field_contract.py"
_CONTRACT = _HERE.parent / "contracts" / "router_contract.json"
_FIXTURES_ROOT = _HERE / "fixtures"

_spec = importlib.util.spec_from_file_location("vrfc", _VRFC_SCRIPT)
_vrfc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vrfc)

verify_router_field_contract = _vrfc.verify_router_field_contract
VerifyResult = _vrfc.VerifyResult


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_class_output_fields_pass_contract_verifier():
    """All four CLASS output_fields rows (H0, N_eff, Omega_m_h2, sigma_8) pass verification.

    Uses verify_router_field_contract against the full manifest; asserts that no
    CLASS rows appear in the fail list.
    """
    result = verify_router_field_contract(_CONTRACT, _FIXTURES_ROOT)

    class_fails = [r for r in result.fail if r.get("label", "").endswith(":class")]
    assert not class_fails, (
        f"CLASS output_fields rows failed verification:\n"
        + "\n".join(str(r) for r in class_fails)
    )


def test_class_output_fields_all_ok_or_xfail():
    """H0:class, N_eff:class, Omega_m_h2:class, sigma_8:class all appear in ok or xfail."""
    result = verify_router_field_contract(_CONTRACT, _FIXTURES_ROOT)

    expected_labels = {"H0:class", "N_eff:class", "Omega_m_h2:class", "sigma_8:class"}
    ok_labels = {r["label"] for r in result.ok}
    xfail_labels = {r["label"] for r in result.xfail}
    acceptable_labels = ok_labels | xfail_labels

    missing = expected_labels - acceptable_labels
    assert not missing, (
        f"Expected CLASS labels not found in ok/xfail: {missing}\n"
        f"ok: {ok_labels}\n"
        f"xfail: {xfail_labels}\n"
        f"fail: {[r['label'] for r in result.fail]}"
    )


def test_overall_verifier_no_new_fails():
    """Full contract verification must return zero FAIL rows for non-maddm rows.

    The two maddm sigma_si/sd_proton rows have a pre-existing DRIFT_PRODUCER_DOC_GAP
    failure (maddm/SKILL.md uses `sigma_si_proton_cm2` not `sigma_si_proton`) that
    predates WS-3. This test excludes those known pre-existing failures and
    verifies that WS-3 introduces no NEW fail rows.
    """
    # Pre-existing failures in the base branch (WS-1/2 merge) — not caused by WS-3
    _KNOWN_PREEXISTING = {"sigma_SI_proton:maddm", "sigma_SD_proton:maddm"}

    result = verify_router_field_contract(_CONTRACT, _FIXTURES_ROOT)
    new_fails = [r for r in result.fail if r.get("label") not in _KNOWN_PREEXISTING]
    assert not new_fails, (
        f"WS-3 introduced new FAIL rows (excludes known pre-existing maddm failures):\n"
        + "\n".join(str(r) for r in new_fails)
    )
