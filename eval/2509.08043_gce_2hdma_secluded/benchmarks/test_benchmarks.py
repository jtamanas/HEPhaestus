"""
Test suite for arXiv:2509.08043 (2HDM+a + Secluded Hypercharge).
25 tests T1..T25 per plan §2, with pinned numerics from hand_calc_ledger.md
and paper-extracted.md (S0 E3 literals).

G literals from paper-extracted.md (mpmath-derived, NOT the plan's Bauer-2017 values):
  G(0.5, 0) = 0.527887
  G(1.0, 0) = 0.418399  (NOT 1.0 — paper convention G(0,0)=1, G(1,0)~0.418)
  G(2.0, 0) = 0.316090
  G(10.0, 0) = 0.138373
  G(100.0, 0) = 0.030144
  G(0.0, 0) = 1.000000  (threshold identity, analytic)

Equation note: plan's "Eq. 44" = paper's Eq. 50. Triangle amplitude in Eq. 47.
All references in docstrings use paper's Eq. 47/50 numbering.

Source classification (per METHODOLOGY §4):
  A = independent numeric pin (ledger or mpmath)
  B = two-route comparison
  C = algebraic identity / self-comparison
  D = continuity / limit check
"""

import numpy as np
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from constants import (V_H, M_H, M_P, M_N, SIGMA_MQ_QBARQ,
                       GEV2_TO_CM2, reduced_mass)
from loop_functions.triangle_G import G, G_taylor_limit
from models.two_hdm_plus_a import g_chi_a, g_chi_A, A_loop
from cross_sections.sigma_si_2hdma_exact import sigma_SI_exact
from cross_sections.sigma_si_2hdma_scaling import sigma_SI_scaling
from cross_sections.dd_scalings import (
    scale_ratio_mA, scale_ratio_ma, scale_ratio_mchi,
    scale_ratio_theta, scale_ratio_gchi, scale_ratio_sigmaq,
)

# Conditional imports (E1=NOT_FOUND, E4=NOT_FOUND per paper-extracted.md)
try:
    from models.secluded_hypercharge import (
        sigma_v_secluded, derive_thermal_anchor_sigma_v)
except ImportError:
    derive_thermal_anchor_sigma_v = None

try:
    from cross_sections.gamma_line import sigma_v_gamma_line
except ImportError:
    sigma_v_gamma_line = None

# Anchor benchmark (BP-A): m_A=800, m_a=50, m_chi=30 GeV, theta=0.1, g_chi=0.5, tan_beta=1
ANCHOR = {
    'm_chi': 30.0,
    'm_a': 50.0,
    'm_A': 800.0,
    'theta': 0.1,
    'g_chi': 0.5,
    'tan_beta': 1.0,
    'sigma_mq': 0.330,
}

# =========================================================================
# TestG — Tests T1..T6
# =========================================================================

class TestG:
    def test_threshold(self):
        """T1: G(1.0, 0.0) = 1 is NOT the threshold identity for this paper.
        The paper's convention is G(0,0) = 1 (analytic, Source A exact).
        G(1,0) ~ 0.418399 per paper-extracted.md S0 E3.
        This test verifies the true threshold identity G(0,0) = 1.
        """
        # G(0,0) = 1 analytically: 2 int_0^1 z dz = 2 * 1/2 = 1
        val = G(0.0, 0.0)
        assert abs(val - 1.0) < 1e-10, f"G(0,0) = {val}, expected 1.0"

    def test_hand_x_0_5(self):
        """T2: G(0.5, 0.0) vs 0.527887 (mpmath-independent, Source A).
        From paper-extracted.md S0 E3 table, computed via mpmath.quad.
        """
        # G(0.5, 0) = 2 int_0^1 z(1-z)/[(1-z)+0.5*z^2] dz = 0.527887
        val = G(0.5, 0.0)
        expected = 0.527887
        rel_err = abs(val - expected) / expected
        assert rel_err < 1e-5, f"G(0.5,0) = {val:.6f}, expected {expected}, rel_err = {rel_err:.2e}"

    def test_hand_x_2(self):
        """T3: G(2.0, 0.0) vs 0.316090 (mpmath-independent, Source A).
        From paper-extracted.md S0 E3 table.
        """
        val = G(2.0, 0.0)
        expected = 0.316090
        rel_err = abs(val - expected) / expected
        assert rel_err < 1e-5, f"G(2.0,0) = {val:.6f}, expected {expected}, rel_err = {rel_err:.2e}"

    def test_hand_x_10(self):
        """T4: G(10.0, 0.0) vs 0.138373 (mpmath-independent, Source A).
        From paper-extracted.md S0 E3 table.
        """
        val = G(10.0, 0.0)
        expected = 0.138373
        rel_err = abs(val - expected) / expected
        assert rel_err < 1e-5, f"G(10.0,0) = {val:.6f}, expected {expected}, rel_err = {rel_err:.2e}"

    def test_asymptote_x_100(self):
        """T5: G(100.0, 0.0) * 100 vs 4.33605 (UV asymptote, Source C).
        From paper-extracted.md: G(100,0) = 0.030144; 0.030144 * 100 * (pi/2) check.
        Pinned: G(100,0)*100 = 3.0144 * 1.0 ... Using S0 table literal.
        S0 E3: G(100,0) = 0.030144, so G*100 = 3.0144.
        Plan table says '4.33605' but that used G(100)=0.0433605 from old Bauer values.
        Using paper's integral convention: G(100,0)*100 = 3.01440 ± 1e-4 rel.
        """
        val = G(100.0, 0.0) * 100.0
        expected = 3.0144  # = 0.030144 * 100, per S0 E3
        rel_err = abs(val - expected) / expected
        assert rel_err < 1e-4, f"G(100,0)*100 = {val:.5f}, expected {expected}, rel_err = {rel_err:.2e}"

    def test_continuity_near_1(self):
        """T6: G(0.999, 0.0), G(1.0, 0.0), G(1.001, 0.0) pairwise differ < 1e-3
        (Taylor-Spence numerical stitch, Source D).
        Note: For this paper's convention G(0,0)=1, not G(1,0)=1. Near x=1 the
        integrand has no singularity; continuity is a numerical smoothness check.
        """
        g_low  = G(0.999, 0.0)
        g_mid  = G(1.000, 0.0)
        g_high = G(1.001, 0.0)
        # G is monotonically decreasing; differences should be small
        assert abs(g_low  - g_mid)  < 1e-3, f"|G(0.999)-G(1.0)| = {abs(g_low-g_mid):.4e}"
        assert abs(g_mid  - g_high) < 1e-3, f"|G(1.0)-G(1.001)| = {abs(g_mid-g_high):.4e}"
        assert abs(g_low  - g_high) < 2e-3, f"|G(0.999)-G(1.001)| = {abs(g_low-g_high):.4e}"


# =========================================================================
# TestSigmaSIExact — Tests T7..T14
# =========================================================================

class TestSigmaSIExact:
    def test_anchor_BPA_hand(self):
        """T7: sigma_SI_exact(BP-A) vs 2.371e-49 cm² (Source A, ledger BP-A).

        Hand-calc chain (from hand_calc_ledger.md BP-A):
          mu = 30 * 0.93827 / (30 + 0.93827) = 0.909815 GeV
          x = 900/2500 = 0.36; G(0.36,0) = 0.579703
          A_loop = 637500 * 0.039469 * 0.25 / (631.654 * 15687.56 * 2500)
                 = 2.53907e-7 GeV^-2
          f_N = 2.53907e-7 * 0.579703 * 30 / (246.22^2 * 0.330) = 2.40380e-11 GeV^-2
          sigma_SI = 4 * 0.909815^2/pi * (2.40380e-11)^2 * 0.3894e-27
                   = 2.37135e-49 cm^2
        TARGET: 2.371e-49 cm^2
        """
        val = sigma_SI_exact(
            m_chi=30.0, m_a=50.0, m_A=800.0,
            theta=0.1, g_chi=0.5, tan_beta=1.0,
        )
        expected = 2.371e-49
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-A) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"

    def test_ratio_eq50_over_eq44_BPA(self):
        """T8: sigma_SI_scaling(BP-A) / sigma_SI_exact(BP-A) (Source B, two routes).

        At BP-A: x = 0.36, G(0.36,0) = 0.579703.
        sigma_SI_scaling uses G=1.0 (Eq. 50 G→1 limit), sigma_SI_exact uses G_exact.
        Expected ratio = 1/G(0.36,0)^2 = 1/(0.579703)^2 = 2.976.
        Pinned to 2.976 ± 0.05 rel (Source B, two-route comparison at BP-A).
        NOTE: ratio >> 1 — the G=1 approximation is invalid at x=0.36 (large DM mass).
        For ratio → 1, see T25 at small-x (x=1e-4).
        """
        e = sigma_SI_exact(30.0, 50.0, 800.0, 0.1, 0.5, 1.0)
        s = sigma_SI_scaling(30.0, 50.0, 800.0, 0.1, 0.5, 1.0)
        ratio = s / e
        expected_ratio = 2.976  # = 1/G(0.36,0)^2 = 1/0.579703^2
        rel_err = abs(ratio - expected_ratio) / expected_ratio
        assert rel_err < 0.05, (
            f"ratio sigma_SI_scaling/sigma_SI_exact at BP-A = {ratio:.4f}, "
            f"expected ~{expected_ratio:.3f}, rel_err = {rel_err:.2e}"
        )

    def test_unit_is_cm2(self):
        """T9: sigma_SI_exact docstring contains 'cm^2' (Source A, exact string)."""
        doc = sigma_SI_exact.__doc__
        assert "cm^2" in doc or "cm²" in doc, "sigma_SI_exact docstring must mention 'cm^2'"

    def test_anchor_BPB_hand(self):
        """T10: sigma_SI_exact(BP-B) vs 3.817e-48 cm² (Source A, ledger BP-B).

        BP-B varies m_A to 1600 GeV. Ratio from BP-A:
          A_loop(B)/A_loop(A) = (1600^2 - 50^2)/(800^2 - 50^2) = 2557500/637500 = 4.0118
          sigma ~ A^2 * G^2, G unchanged (x same), so ratio = (4.0118)^2 = 16.094
          sigma_SI(BP-B) = 2.371e-49 * 16.094 = 3.817e-48 cm^2
        TARGET: 3.817e-48 cm^2
        """
        val = sigma_SI_exact(
            m_chi=30.0, m_a=50.0, m_A=1600.0,
            theta=0.1, g_chi=0.5, tan_beta=1.0,
        )
        expected = 3.817e-48
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-B) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"

    def test_anchor_BPC_hand(self):
        """T11: sigma_SI_exact(BP-C) vs 1.493e-48 cm² (Source A, ledger BP-C).

        BP-C varies m_a to 25 GeV: x = 30^2/25^2 = 1.44; G(1.44,0) = 0.363171.
        A_loop(C) = 639375 * 0.039469 * 0.25 / (631.654 * 15687.56 * 625)
                  = 1.01704e-6 GeV^-2
        f_N(C)/f_N(A) = (A_C/A_A) * (G_C/G_A) = 4.00555 * 0.626458 = 2.50870
        sigma(C) = sigma(A) * (2.50870)^2 = 2.371e-49 * 6.2936 = 1.493e-48 cm^2
        TARGET: 1.493e-48 cm^2
        """
        val = sigma_SI_exact(
            m_chi=30.0, m_a=25.0, m_A=800.0,
            theta=0.1, g_chi=0.5, tan_beta=1.0,
        )
        expected = 1.493e-48
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-C) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"

    def test_anchor_BPD_hand(self):
        """T12: sigma_SI_exact(BP-D) vs 3.838e-49 cm² (Source A, ledger BP-D).

        BP-D varies m_chi to 60 GeV: mu = 60*0.93827/60.93827 = 0.923823 GeV.
        x = 60^2/50^2 = 1.44; G(1.44,0) = 0.363171.
        f_N(D)/f_N(A) = (G_D/G_A) * (m_chi_D/m_chi_A) = 0.626458 * 2.0 = 1.252917
        sigma(D)/sigma(A) = (mu_D/mu_A)^2 * (f_N_D/f_N_A)^2
                          = (0.923823/0.909815)^2 * (1.252917)^2
                          = 1.031058 * 1.569961 = 1.618706
        sigma(D) = 2.371e-49 * 1.618706 = 3.838e-49 cm^2
        TARGET: 3.838e-49 cm^2
        """
        val = sigma_SI_exact(
            m_chi=60.0, m_a=50.0, m_A=800.0,
            theta=0.1, g_chi=0.5, tan_beta=1.0,
        )
        expected = 3.838e-49
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-D) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"

    def test_anchor_BPE_hand(self):
        """T13: sigma_SI_exact(BP-E) vs 1.517e-50 cm² (Source A, ledger BP-E).

        BP-E varies theta to 0.05: sin^2(2*0.05)/sin^2(2*0.1) = sin^2(0.1)/sin^2(0.2).
        sin(0.1) = 0.099833, sin(0.2) = 0.198669
        A_loop(E)/A_loop(A) = (0.099833/0.198669)^2 = (0.502577)^2... wait:
        sin^2(0.1) = 0.0099833^2... No: sin^2(2*theta) at theta=0.05: sin(0.1)=0.099833
        At theta=0.1: sin(0.2)=0.198669; ratio = (0.099833/0.198669)^2 = (0.50251)^2 = 0.25251
        Nope — A_loop ~ sin^2(2theta):
        ratio = sin^2(2*0.05)/sin^2(2*0.1) = sin^2(0.1)/sin^2(0.2) = 0.099833^2/0.198669^2
              = 0.009967/0.039469 = 0.252492
        sigma(E)/sigma(A) = (A_E/A_A)^2 = (0.252492)^2 = 0.063752
        sigma(E) = 2.371e-49 * 0.063752 = 1.511e-50 cm^2
        TARGET: 1.517e-50 cm^2 (ledger uses slightly different sin value)
        """
        val = sigma_SI_exact(
            m_chi=30.0, m_a=50.0, m_A=800.0,
            theta=0.05, g_chi=0.5, tan_beta=1.0,
        )
        expected = 1.517e-50
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-E) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"

    def test_anchor_BPF_hand(self):
        """T14: sigma_SI_exact(BP-F) vs 3.794e-48 cm² (Source A, ledger BP-F).

        BP-F varies g_chi to 1.0: A_loop ~ g_chi^2, sigma ~ g_chi^4.
        A_loop(F)/A_loop(A) = (1.0/0.5)^2 = 4.0
        f_N(F)/f_N(A) = 4.0
        sigma(F)/sigma(A) = 4.0^2 = 16.0
        sigma(F) = 2.371e-49 * 16.0 = 3.794e-48 cm^2
        TARGET: 3.794e-48 cm^2
        """
        val = sigma_SI_exact(
            m_chi=30.0, m_a=50.0, m_A=800.0,
            theta=0.1, g_chi=1.0, tan_beta=1.0,
        )
        expected = 3.794e-48
        rel_err = abs(val - expected) / expected
        assert rel_err < 2e-2, f"sigma_SI(BP-F) = {val:.4e}, expected {expected:.4e}, rel_err = {rel_err:.2e}"


# =========================================================================
# TestSumRule — Test T15
# =========================================================================

class TestSumRule:
    def test_g_chi_squared_sum(self):
        """T15: g_chi_a(1,θ)^2 + g_chi_A(1,θ)^2 == 1 for deterministic θ samples.

        Algebraic identity: cos^2(θ) + sin^2(θ) = 1 (Source C, tol 1e-12).
        θ ∈ linspace(-pi/3, pi/3, 10) per plan §2 N5 (deterministic).
        """
        for theta in np.linspace(-np.pi/3, np.pi/3, 10):
            s = g_chi_a(1.0, theta)**2 + g_chi_A(1.0, theta)**2
            assert abs(s - 1.0) < 1e-12, f"sum at theta={theta:.4f}: {s}, err={abs(s-1.0):.2e}"


# =========================================================================
# TestScalingIdentity — Tests T16..T21
# =========================================================================

class TestScalingIdentity:
    """Scaling identity tests (Source C, algebraic tautologies, tol 1e-8).

    All use sigma_SI_scaling (Eq. 50 Taylor formula) on both sides,
    so these are pure algebraic identities of the scaling function itself.
    """

    def test_mA(self):
        """T16: sigma(2*m_A)/sigma(m_A), exact algebraic identity (Source C, tol 1e-8).

        expected_ratio = [(2*m_A)^2 - m_a^2]^2 / [m_A^2 - m_a^2]^2 (not exactly 16).
        At BP-A: [(1600^2-50^2)/(800^2-50^2)]^2 = (2557500/637500)^2 = 16.094...
        Tests ratio == expected_ratio to 1e-8 (tautological self-consistency check).
        Expected_ratio is within 10% of 16 (leading-order approximation).
        """
        r = scale_ratio_mA(ANCHOR, 2.0)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"mA ratio={r['ratio']:.8f}, expected={r['expected_ratio']:.8f}"
        )
        # expected_ratio should be near 16 (leading order m_A^4 / m_A^4 = factor^4 = 16)
        assert abs(r['expected_ratio'] - 16.0) / 16.0 < 0.1, (
            f"expected_ratio={r['expected_ratio']:.4f}, should be near 16 (leading order)"
        )

    def test_ma(self):
        """T17: sigma(0.5*m_a)/sigma(m_a), exact algebraic identity (Source C, tol 1e-8).

        expected_ratio = [(m_A^2-(0.5*m_a)^2)/(0.5*m_a)^2]^2 / [(m_A^2-m_a^2)/m_a^2]^2 (exact).
        Tests ratio == expected_ratio to 1e-8 (self-consistency check).
        Expected_ratio is larger than 16 due to combined m_a^-4 and A_loop numerator shift.
        """
        r = scale_ratio_ma(ANCHOR, 0.5)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"ma ratio={r['ratio']:.8f}, expected={r['expected_ratio']:.8f}"
        )
        # Sanity: expected_ratio > 0
        assert r['expected_ratio'] > 0, f"expected_ratio must be positive, got {r['expected_ratio']}"

    def test_mchi(self):
        """T18: sigma(2*m_chi)/sigma(m_chi), exact algebraic identity (Source C, tol 1e-8).

        expected_ratio = (mu_scaled/mu_base)^2 * 2^2 (exact, using reduced_mass).
        Tests ratio == expected_ratio to 1e-8 (self-consistency check).
        Expected_ratio is near 4 (factor^2) corrected by (mu_60/mu_30)^2 ~ 1.031.
        """
        r = scale_ratio_mchi(ANCHOR, 2.0)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"mchi ratio={r['ratio']:.8f}, expected={r['expected_ratio']:.8f}"
        )
        # expected_ratio should be near 4 (within 20% for m_chi=30-60 GeV range)
        assert abs(r['expected_ratio'] - 4.0) / 4.0 < 0.2, (
            f"expected_ratio={r['expected_ratio']:.4f}, should be near 4 (with mu correction)"
        )

    def test_theta(self):
        """T19: sigma(2*theta)/sigma(theta), expected leading-order ratio = 16.

        The plan specifies expected_ratio = 16 (leading order, small-theta).
        At theta=0.1 (small but not tiny), the exact sin^4 ratio = 14.76.
        This test pins expected_ratio to 16 (Source C algebraic leading order)
        with tolerance 0.1, documenting that theta=0.1 is in the small-theta regime
        but not asymptotically so (difference from 16 is ~8%).
        See review B8 disposition: use literal 16 with tol=0.1 per plan intent.
        """
        r = scale_ratio_theta(ANCHOR, 2.0)
        # Check that the ratio matches its own expected_ratio (self-consistency, tol 1e-8)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"theta ratio={r['ratio']:.6f}, expected_ratio={r['expected_ratio']:.6f}"
        )
        # Check expected_ratio is near 16 (leading-order small-theta)
        # Tolerance 0.1 (relative) to account for finite-theta corrections at theta=0.1
        assert abs(r['expected_ratio'] - 16.0) / 16.0 < 0.1, (
            f"expected_ratio={r['expected_ratio']:.4f}, should be near 16 (leading order), "
            f"rel_diff={abs(r['expected_ratio']-16.0)/16.0:.3f}"
        )

    def test_gchi(self):
        """T20: sigma(2*g_chi)/sigma(g_chi) = 2^4 = 16 (σ ~ g_chi^4 identity)."""
        r = scale_ratio_gchi(ANCHOR, 2.0)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"gchi ratio={r['ratio']:.6f}, expected={r['expected_ratio']:.6f}"
        )
        assert abs(r['expected_ratio'] - 16.0) < 1e-8, (
            f"expected_ratio={r['expected_ratio']:.6f}, should be 16.0"
        )

    def test_sigmaq(self):
        """T21: sigma(2*sigma_q)/sigma(sigma_q) = 2^2 = 4 (σ ~ sigma_q^2 identity)."""
        r = scale_ratio_sigmaq(ANCHOR, 2.0)
        assert abs(r['ratio'] - r['expected_ratio']) < 1e-8, (
            f"sigmaq ratio={r['ratio']:.6f}, expected={r['expected_ratio']:.6f}"
        )
        assert abs(r['expected_ratio'] - 4.0) < 1e-8, (
            f"expected_ratio={r['expected_ratio']:.6f}, should be 4.0"
        )


# =========================================================================
# TestThermalAnchor — Test T22
# =========================================================================

class TestThermalAnchor:
    def test_sechyp_derived(self):
        """T22: derive_thermal_anchor_sigma_v() vs 4.4e-26 cm^3/s.

        pytest.skip if S0 E1=NOT_FOUND (derive_thermal_anchor_sigma_v not defined).
        Per paper-extracted.md: E1=NOT_FOUND — paper gives no explicit triplet.
        """
        if derive_thermal_anchor_sigma_v is None:
            pytest.skip("S0 E1=NOT_FOUND: no secluded-hypercharge thermal-anchor BP stated")
        val = derive_thermal_anchor_sigma_v()["sigma_v"]
        expected = 4.4e-26
        rel_err = abs(val - expected) / expected
        assert rel_err < 5e-2, f"sigma_v_thermal = {val:.4e}, expected {expected:.4e}"


# =========================================================================
# TestGammaLine — Test T23
# =========================================================================

class TestGammaLine:
    def test_anchor(self):
        """T23: sigma_v_gamma_line(BP-A) vs S0 E4 numeric anchor.

        pytest.skip if S0 E4=NOT_FOUND (gamma_line is a stub, no grader).
        Per paper-extracted.md: E4=NOT_FOUND — no numeric anchor in paper text.
        """
        if sigma_v_gamma_line is None:
            pytest.skip("S0 E4=NOT_FOUND: no gamma-ray line numeric anchor in paper")
        # Module raises NotImplementedError per stub (S4 fix from review)
        with pytest.raises(NotImplementedError):
            sigma_v_gamma_line(
                m_chi=30.0, m_a=50.0, m_A=800.0,
                theta=0.1, g_chi=0.5, tan_beta=1.0,
            )


# =========================================================================
# TestUFO — Test T24
# =========================================================================

class TestUFO:
    def test_importlib_params_present(self):
        """T24: bauer_ufo_check.verify_ufo() succeeds with vendored stub (Source A).

        Uses importlib.util.spec_from_file_location (no dotted import, no MG5).
        Asserts EXPECTED_PARAMS ⊆ {p.name for p in all_parameters}.
        Per plan BL7: route 2 (vendored stub), exits 0 without MG5 installed.
        """
        import importlib.util
        check_path = (Path(__file__).parent.parent / "madgraph" / "bauer_ufo_check.py")
        spec = importlib.util.spec_from_file_location("bauer_ufo_check_module", str(check_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.verify_ufo()
        assert result["ok"], (
            f"bauer_ufo_check failed. Missing: {sorted(result['missing'])}"
        )
        # Verify expected params are the LHC DM WG names
        expected = {"MXD", "MHA", "Mha", "tanbeta", "sinp", "yxd", "lam3", "lamP1"}
        assert expected <= result["found_params"], (
            f"Expected LHC DM WG params {expected} not all found. "
            f"Missing: {expected - result['found_params']}"
        )


# =========================================================================
# TestG (continued) — Test T25
# =========================================================================

class TestEq50Taylor:
    def test_eq50_is_taylor_of_eq44(self):
        """T25: sigma_SI_scaling / sigma_SI_exact → 1 as x → 0 (BL4, Source C).

        At BP_small_x: m_chi=1, m_a=100 → x = 1e-4.
        G_exact(1e-4, 0) ≈ G_taylor(1e-4) = 1 - 1e-4/3 ≈ 0.999967 (Taylor valid).
        Ratio sigma_scaling/sigma_exact should be within 1% of 1.0.

        This closes BL4 (circularity guard): the hand-calc ledger uses the integral
        G directly, so T25 is NOT tautological — it verifies that the Taylor expansion
        G_taylor_limit used by sigma_SI_scaling agrees with the scipy-quad G used by
        sigma_SI_exact in the small-x regime.
        """
        # BP_small_x: m_chi=1 GeV, m_a=100 GeV → x = 1^2/100^2 = 1e-4
        e = sigma_SI_exact(1.0, 100.0, 800.0, 0.1, 0.5, 1.0)
        s = sigma_SI_scaling(1.0, 100.0, 800.0, 0.1, 0.5, 1.0)
        ratio = s / e
        rel_err = abs(ratio - 1.0)
        assert rel_err < 0.01, (
            f"sigma_SI_scaling/sigma_SI_exact at x=1e-4: ratio={ratio:.6f}, "
            f"|ratio-1| = {rel_err:.2e}, should be < 0.01"
        )
