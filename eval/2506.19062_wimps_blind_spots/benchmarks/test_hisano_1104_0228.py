"""
test_hisano_1104_0228.py — VALIDATION-ONLY tests for the P3 Hisano anchor.

These test the ANALYTIC TRANSCRIPTION and the comparison harness plumbing — NOT
the production pipeline (which is exercised by the Wolfram driver + p3_extract).
No Wolfram kernel is needed here (pure Python).
"""
import math

import pytest

import hisano_1104_0228 as H
import p3_compare as C


# ---------------------------------------------------------------------------
# Loop-function analytic limits (Eq. 33), x -> 0  (arctan(2 b_x/sqrt x) -> pi/2)
# ---------------------------------------------------------------------------
def test_loop_function_limits():
    x = 1e-8
    assert math.isclose(H.g_H(x), -2 * math.pi, rel_tol=2e-3)
    assert math.isclose(H.g_S(x), math.pi / 2, rel_tol=2e-3)
    assert math.isclose(H.g_T1(x), math.pi / 3, rel_tol=2e-3)
    assert abs(H.g_T2(x)) < 2e-3   # -> 0


def test_selfcheck_passes():
    """The mandatory Ruling-4 self-check must pass before any comparison."""
    res = H.selfcheck(verbose=False)
    assert res["loop_function_limits_ok"] is True
    assert res["sigma_SI_in_paper_range"] is True
    assert res["passed"] is True


def test_sigma_SI_in_paper_range():
    """Higgsino sigma_SI (scalar+twist2, no gluon) lands in O(10^-46..-48) cm^2."""
    ew = H.EWInputs()
    sig = H.sigma_SI_scalar_twist2(1000.0, 2, 0.5, ew)
    assert 1e-49 <= sig <= 1e-45


def test_pure_doublet_isospin_factor():
    """n=2, Y=1/2 gives n^2-(4Y^2+1) = 2 (the Higgsino W-loop factor)."""
    n, Y = 2, 0.5
    assert n * n - (4 * Y * Y + 1) == 2


def test_scalar_coeff_is_fq_times_mq():
    """C_scalar^Hisano == f_q * m_q (the decisive convention)."""
    ew = H.EWInputs()
    M, mq = 500.0, C.M_D
    assert math.isclose(H.C_scalar_hisano(M, mq, "d", 2, 0.5, ew),
                        H.f_q(M, "d", 2, 0.5, ew) * mq, rel_tol=1e-12)


def test_quark_couplings_eq22():
    """a_q^V = T3/2 - Q sw2 ; a_q^A = -T3/2 (Eq. 22)."""
    sw2 = 0.23122
    # down quark: T3=-1/2, Q=-1/3
    assert math.isclose(H.a_qV("d", sw2), -0.25 + (1.0 / 3.0) * sw2, rel_tol=1e-12)
    assert math.isclose(H.a_qA("d"), 0.25, rel_tol=1e-12)


def test_compare_harness_shape():
    """The comparison harness produces both axes with ratio+sign, given a
    synthetic C_ours and a minimal spectrum point."""
    point = {
        "m_dm_gev": 498.0,
        "masses": {"23": 91.1876, "24": 80.3485, "25": 125.2456},
        "params": {"GAUGE:2": 0.6488},
    }
    cours = {
        "C_scalar_full_re": 1.66e-10, "C_scalar_full_im": 5.3e-11,
        "C_twist2_re": 4.2e-7, "si_shift_rel": 1.0,
        "full_basis_completeness_rel_residual": 3.1e-9,
        "C_scalar_3op_re": -1.28e-7, "C_chi_vector_re": 1e-15,
    }
    r = C.compare_leg(cours, point, 498.0)
    assert "ratio_ours_over_hisano" in r["scalar"]
    assert "sign_agree" in r["scalar"]
    assert "ratio_ours_over_hisano_gM" in r["twist2"]
    # Hisano scalar coefficient must be nonzero (pure-doublet gH is definitively
    # nonzero — the P3 denominator is valid, per Ruling 4).
    assert r["scalar"]["C_hisano"] != 0.0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
