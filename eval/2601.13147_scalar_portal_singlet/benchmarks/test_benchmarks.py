"""
Benchmark tests for arXiv:2601.13147 (Singlet Fermion DM + Scalar Portal).

37 pinned tests covering:
  - Mass matrix diagonalization (T01-T13)
  - Mixing angle sign convention (T14-T15)
  - sigma_SI internal consistency (T16-T18)
  - Amplitude sign (T19)
  - Proton/neutron ratio as structural identity (T20-T22)
  - Blind-spot exact zero (T23-T24)
  - Signal strength (T25-T26)
  - Lagrangian round-trip (T27-T29)
  - Stability/unitarity LHS pins (T30-T35)
  - V_H convention guard (T36)
  - Cross-paper Eq. 31 -> single-Higgs limit (T37)

Run with:
    cd eval/2601.13147_scalar_portal_singlet
    python -m pytest benchmarks/test_benchmarks.py -v
"""

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import (
    V_H, M_H, M_P, GEV2_TO_CM2, reduced_mass,
    F_U_P, F_D_P, F_S_P, F_U_N, F_D_N, F_S_N,
    M_U, M_D, M_S, M_C, M_B, M_T,
    G_F,
)
from models.scalar_portal_singlet import (
    mass_matrix_CPeven, m_h1_h2_analytical, diagonalize_numerical,
    lagrangian_params_from_physical,
    vacuum_stability_lhs, perturbative_unitarity_lhs,
    coupling_chichi_h1, coupling_chichi_h2,
    coupling_qq_h1, coupling_qq_h2,
    sigma_pp_h2, mu_signal, amplitude_SI,
    f_N_proton, f_N_neutron,
)
from cross_sections.si_tree_level import (
    sigma_SI_scalar_portal, _reduce_eq31_to_single_higgs_limit,
)
from benchmarks.benchmark_points import BP1, BP_mid, BP9, PINNED_BPS

# Import sigma_SI_higgs_portal from 2506.19062 for the cross-paper regression test (T37)
# Use a temporary sys.path manipulation to avoid shadowing our local cross_sections module.
# We import the module by full path and extract the function to avoid import conflicts.
def _import_ref_sigma():
    import importlib.util
    _ref_dir = Path(__file__).parent.parent.parent / "2506.19062_wimps_blind_spots"
    spec = importlib.util.spec_from_file_location(
        "ref_si_tree_level",
        str(_ref_dir / "cross_sections" / "si_tree_level.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    # Add ref_dir to path temporarily so the module can import its own constants
    sys.path.insert(0, str(_ref_dir))
    try:
        spec.loader.exec_module(mod)
    finally:
        if str(_ref_dir) in sys.path:
            sys.path.remove(str(_ref_dir))
    return mod.sigma_SI_higgs_portal

_ref_sigma = _import_ref_sigma()


# ============================================================================
# Helper: hand-calculation of sigma_SI (S-3 fix: independent implementation)
# ============================================================================

def _sigma_SI_by_hand(bp: object, f_u=F_U_P, f_d=F_D_P, f_s=F_S_P) -> float:
    """
    Independent hand calculation of sigma_SI via the amplitude path (S-2 fix).

    This implementation is INDEPENDENT of sigma_SI_scalar_portal: it routes
    through amplitude_SI (which is separately tested in T19) rather than
    duplicating the closed-form formula. If sigma_SI_scalar_portal has a
    factor-of-2 bug, this helper will NOT share that bug.

    Steps:
      1. Compute f_N = f_u + f_d + f_s + (2/9)*(1 - f_u - f_d - f_s)
      2. Compute amplitude A = amplitude_SI(m_chi, g_chi, sin_theta, m_h1, m_h2, m_q)
         for each light quark (u, d, s), weighting by f_q
      3. Effective nucleon amplitude: A_N = sum_q A_q / (m_q/V_H) * (f_q/f_N_factor)
         Equivalently: factored form sigma = (mu^2/pi) * A_per_mq^2 * f_N^2 * GEV2_TO_CM2
         where A_per_mq = amplitude_SI(..., m_q=1) is independent of m_q.

    Since amplitude_SI = sqrt(1-s^2)*s*g_chi*(m_q/V_H)*(1/m_h1^2 - 1/m_h2^2),
    we have A_per_mq = sqrt(1-s^2)*s*g_chi*(1/V_H)*(1/m_h1^2 - 1/m_h2^2),
    and sigma = (mu^2/pi) * m_p^2 * A_per_mq^2 * f_N^2 * GEV2_TO_CM2.
    """
    m_chi = bp.m_chi
    g_chi = bp.g_chi
    sin_theta = bp.sin_theta
    m_h1 = bp.m_h1
    m_h2 = bp.m_h2

    # f_N: nucleon form factor (proton by default)
    f_light = f_u + f_d + f_s
    f_N = f_light + (2.0 / 9.0) * (1.0 - f_light)

    mu = m_chi * M_P / (m_chi + M_P)

    # amplitude_SI with m_q=1.0 to extract the m_q-independent prefactor
    # amplitude_SI = sqrt(1-s^2)*s*g_chi*(m_q/V_H)*(1/m_h1^2 - 1/m_h2^2)
    # so amplitude_SI / (m_q/V_H) is constant for all quarks
    # We use m_q=1.0 GeV as a proxy; f_N already encodes the quark-mass weighting
    A_per_mq_times_V_H = amplitude_SI(m_chi, g_chi, sin_theta, m_h1, m_h2, 1.0) * V_H
    # A_N (nucleon) = A_per_mq * (m_p/V_H) * f_N  (standard formula)
    A_N = A_per_mq_times_V_H * (M_P / V_H) * f_N

    sigma_gev2 = (mu**2 / np.pi) * A_N**2
    return sigma_gev2 * GEV2_TO_CM2


def _eq15_lhs_by_hand(lambda_h: float, lambda_s: float, lambda_hs: float) -> float:
    """
    Hand calculation of vacuum stability LHS (Eq. 15, binding condition 3).
    Transcribed from paper-1-numerics.md:
      LHS = lambda_hs + 2*sqrt(lambda_h * lambda_s)
    """
    return lambda_hs + 2.0 * np.sqrt(lambda_h * lambda_s)


def _eq16_lhs_by_hand(lambda_h: float, lambda_s: float, lambda_hs: float) -> float:
    """
    Hand calculation of perturbative unitarity LHS (Eq. 16, binding condition).
    Transcribed from paper-1-numerics.md:
      LHS = 8*pi - |3*lambda_h + 2*lambda_s + sqrt((3*lambda_h - 2*lambda_s)^2 + 2*lambda_hs^2)|
    """
    delta = np.sqrt((3.0 * lambda_h - 2.0 * lambda_s)**2 + 2.0 * lambda_hs**2)
    eig_plus = abs(3.0 * lambda_h + 2.0 * lambda_s + delta)
    eig_minus = abs(3.0 * lambda_h + 2.0 * lambda_s - delta)
    return 8.0 * np.pi - max(eig_plus, eig_minus)


def _get_lagrangian(bp):
    """Get Lagrangian params for a BP (uses lagrangian_params_from_physical)."""
    return lagrangian_params_from_physical(
        bp.m_h1, bp.m_h2, bp.sin_theta, bp.lambda_s, bp.mu_3
    )


# ============================================================================
# T01-T04: TestMassMatrix — stored BP field values
# ============================================================================

class TestMassMatrix:
    """T01-T04: Verify stored benchmark point mass values against expected targets.

    These tests confirm the BP objects were instantiated correctly.
    T01: BP1.m_h2 == 200.0 GeV
    T02: BP_mid.m_h2 == 300.0 GeV
    T03: BP9.m_h2 == 70.0 GeV
    T04: BP1.m_h1 == 125.25 GeV
    """

    def test_m_h2_bp1(self):
        """T01: BP1.m_h2 = 200.0 GeV (Paper Table 1, pin input)."""
        assert abs(BP1.m_h2 - 200.0) / 200.0 < 1e-10

    def test_m_h2_bp_mid(self):
        """T02: BP_mid.m_h2 = 300.0 GeV (Synthetic)."""
        assert abs(BP_mid.m_h2 - 300.0) / 300.0 < 1e-10

    def test_m_h2_bp9(self):
        """T03: BP9.m_h2 = 70.0 GeV (paper-1-numerics.md, Paper Table 1)."""
        assert abs(BP9.m_h2 - 70.0) / 70.0 < 1e-10

    def test_m_h1_bp1(self):
        """T04: BP1.m_h1 = 125.25 GeV (= M_H constant)."""
        assert abs(BP1.m_h1 - 125.25) / 125.25 < 1e-10


# ============================================================================
# T05-T13: TestMassTwoRoute — two independent routes for eigenvalues
# ============================================================================

class TestMassTwoRoute:
    """T05-T13: Two-route mass computation: analytical vs numerical.

    Route A: m_h1_h2_analytical(M_hh, M_ss, M_hs)
    Route B: diagonalize_numerical(M_sq)

    Both routes use the same mass matrix but different algorithms.
    Differences must be < 1e-10 abs.
    """

    def _two_routes(self, bp):
        """Compute eigenvalues via both routes for a benchmark point."""
        p = _get_lagrangian(bp)
        M = mass_matrix_CPeven(
            p["lambda_h"], p["lambda_hs"], p["mu_hs"], p["mu_s_sq"],
            bp.lambda_s, bp.mu_3,
        )
        m1a, m2a, sta = m_h1_h2_analytical(M[0, 0], M[1, 1], M[0, 1])
        m1n, m2n, stn = diagonalize_numerical(M)
        return m1a, m2a, sta, m1n, m2n, stn

    def test_diff_m_h1_bp1(self):
        """T05: Route A vs B for m_h1 at BP1, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP1)
        assert abs(m1a - m1n) < 1e-10, f"m_h1 diff = {abs(m1a-m1n):.2e}"

    def test_diff_m_h2_bp1(self):
        """T06: Route A vs B for m_h2 at BP1, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP1)
        assert abs(m2a - m2n) < 1e-10, f"m_h2 diff = {abs(m2a-m2n):.2e}"

    def test_diff_sin_theta_bp1(self):
        """T07: Route A vs B for sin_theta at BP1, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP1)
        assert abs(sta - stn) < 1e-10, f"sin_theta diff = {abs(sta-stn):.2e}"

    def test_diff_m_h1_bp_mid(self):
        """T08: Route A vs B for m_h1 at BP_mid, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP_mid)
        assert abs(m1a - m1n) < 1e-10

    def test_diff_m_h2_bp_mid(self):
        """T09: Route A vs B for m_h2 at BP_mid, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP_mid)
        assert abs(m2a - m2n) < 1e-10

    def test_diff_sin_theta_bp_mid(self):
        """T10: Route A vs B for sin_theta at BP_mid, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP_mid)
        assert abs(sta - stn) < 1e-10

    def test_diff_m_h1_bp9(self):
        """T11: Route A vs B for m_h1 at BP9, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP9)
        assert abs(m1a - m1n) < 1e-10

    def test_diff_m_h2_bp9(self):
        """T12: Route A vs B for m_h2 at BP9, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP9)
        assert abs(m2a - m2n) < 1e-10

    def test_diff_sin_theta_bp9(self):
        """T13: Route A vs B for sin_theta at BP9, tol 1e-10 abs."""
        m1a, m2a, sta, m1n, m2n, stn = self._two_routes(BP9)
        assert abs(sta - stn) < 1e-10


# ============================================================================
# T14: TestSinThetaSignConvention
# ============================================================================

class TestSinThetaSignConvention:
    """T14: Verify sign(sin_theta) == -sign(M_hs_sq) (Eq. 11 derivation).

    This tests the U[0,0]>0 convention using a non-trivial mixing angle.
    At BP_mid (sin_theta=0.2), M_hs from the reconstructed matrix must have
    opposite sign to sin_theta.
    """

    def test_sign_sin_theta_matches_Mhs(self):
        """T14: sign(sin_theta_diag) * sign(M_hs_sq) <= 0 (covers zero case).

        The mass matrix for BP_mid has sin_theta=0.2 (positive) as input.
        lagrangian_params_from_physical reconstructs M_hs = (m_h1^2 - m_h2^2)*sin*cos
        which is negative for m_h1 < m_h2.
        After diagonalize_numerical, the recovered sin_theta should match
        sign(sin_theta) == -sign(M_hs).
        """
        p = _get_lagrangian(BP_mid)
        M = mass_matrix_CPeven(
            p["lambda_h"], p["lambda_hs"], p["mu_hs"], p["mu_s_sq"],
            BP_mid.lambda_s, BP_mid.mu_3,
        )
        M_hs_sq = float(M[0, 1])
        _, _, sin_theta = diagonalize_numerical(M)
        # sign(sin_theta) * sign(M_hs_sq) must be <= 0
        assert np.sign(sin_theta) * np.sign(M_hs_sq) <= 0, (
            f"sign(sin_theta)={np.sign(sin_theta)}, sign(M_hs)={np.sign(M_hs_sq)}"
        )


# ============================================================================
# T15: TestSinThetaPaperPin
# ============================================================================

class TestSinThetaPaperPin:
    """T15: Paper-verbatim pin of sin_theta for BP1."""

    def test_sin_theta_bp1_verbatim(self):
        """T15: BP1.sin_theta == 0.001 from Paper Table 1, tol 1e-13 abs."""
        assert abs(BP1.sin_theta - 0.001) < 1e-13


# ============================================================================
# T16-T18: TestSigmaSIInternal (S-3: helper vs library)
# ============================================================================

class TestSigmaSIInternal:
    """T16-T18: sigma_SI library vs independent hand-calculation helper.

    Each test calls both _sigma_SI_by_hand(bp) and sigma_SI_scalar_portal(...)
    and asserts they agree to 1e-10 rel.

    T16 additionally checks within 1% of the hand-calc target 6.17e-50 cm² (BP1):

    §T16-calc (locked):
      mu = 222*0.93827/(222+0.93827) = 0.93432 GeV
      mu^2/pi = 0.27785
      (m_p/v)^2 = (0.93827/246.22)^2 = 1.4528e-5
      g_chi^2 = 0.57^2 = 0.3249
      sin^2*cos^2 ≈ sin^2 = 0.001^2 = 1e-6 (cos^2≈1)
      blind = (200^2-125.25^2)/(125.25^2*200^2) = 24312/(15688*40000) = 3.876e-5 GeV^-2
      blind^2 = 1.502e-9 GeV^-4
      f_N^2 ≈ 0.28374^2 = 0.08051
      sigma = 0.27785 * 1.4528e-5 * 0.3249 * 1e-6 * 1.502e-9 * 0.08051 * 3.894e-28
            ≈ 6.17e-50 cm^2
    """

    def test_sigma_SI_bp1(self):
        """T16: sigma_SI at BP1 = helper(BP1) ~ 6.17e-50 cm^2 (tol 1e-10 rel)."""
        expected = _sigma_SI_by_hand(BP1)
        actual = sigma_SI_scalar_portal(
            BP1.m_chi, BP1.g_chi, BP1.sin_theta, BP1.m_h1, BP1.m_h2,
        )
        # Check helper vs library (1e-10 rel)
        assert abs(actual - expected) / expected < 1e-10
        # Additionally: within 1% of 6.17e-50 (§T16-calc target)
        assert abs(actual / 6.17e-50 - 1.0) < 0.01, (
            f"BP1 sigma_SI = {actual:.3e}, expected within 1% of 6.17e-50"
        )

    def test_sigma_SI_bp_mid(self):
        """T17: sigma_SI at BP_mid = helper(BP_mid) (tol 1e-10 rel, S-3)."""
        expected = _sigma_SI_by_hand(BP_mid)
        actual = sigma_SI_scalar_portal(
            BP_mid.m_chi, BP_mid.g_chi, BP_mid.sin_theta, BP_mid.m_h1, BP_mid.m_h2,
        )
        assert abs(actual - expected) / expected < 1e-10

    def test_sigma_SI_bp9(self):
        """T18: sigma_SI at BP9 = helper(BP9) (tol 1e-10 rel, S-3)."""
        expected = _sigma_SI_by_hand(BP9)
        actual = sigma_SI_scalar_portal(
            BP9.m_chi, BP9.g_chi, BP9.sin_theta, BP9.m_h1, BP9.m_h2,
        )
        assert abs(actual - expected) / expected < 1e-10


# ============================================================================
# T19: TestAmplitudeSign
# ============================================================================

class TestAmplitudeSign:
    """T19: Amplitude sign convention (Eq. 29).

    For BP1 (sin_theta=0.001 > 0, m_h2=200 > m_h1=125.25):
    A = sqrt(1-s^2)*s*g_chi*(m_q/v)*(1/m_h1^2 - 1/m_h2^2) > 0.
    Sign flips when sin_theta < 0.

    B2 fix: no range assertions. Expected value computed from the locked
    formula A = sqrt(1-sin^2)*sin*g_chi*(m_q/v)*(1/m_h1^2 - 1/m_h2^2),
    then asserted to 1e-12 rel tolerance.
    """

    def test_amplitude_sign_bp1(self):
        """T19: amplitude_SI matches locked formula at BP1 (implies > 0 and pinned value)."""
        A = amplitude_SI(BP1.m_chi, BP1.g_chi, BP1.sin_theta,
                         BP1.m_h1, BP1.m_h2, M_U)
        # Expected from locked formula (plan §2.10):
        # A = sqrt(1 - sin^2) * sin * g_chi * (m_q/V_H) * (1/m_h1^2 - 1/m_h2^2)
        A_expected = (
            np.sqrt(1.0 - BP1.sin_theta**2) * BP1.sin_theta
            * BP1.g_chi * (M_U / V_H)
            * (1.0 / BP1.m_h1**2 - 1.0 / BP1.m_h2**2)
        )
        assert abs(A - A_expected) / abs(A_expected) < 1e-12, (
            f"amplitude_SI at BP1 = {A:.6e}, expected {A_expected:.6e}"
        )

    def test_amplitude_sign_negative_theta(self):
        """T19b: amplitude_SI matches locked formula with negative sin_theta (sign flip)."""
        A_neg = amplitude_SI(BP1.m_chi, BP1.g_chi, -BP1.sin_theta,
                             BP1.m_h1, BP1.m_h2, M_U)
        # Expected: same formula with -sin_theta gives negative result
        A_neg_expected = (
            np.sqrt(1.0 - BP1.sin_theta**2) * (-BP1.sin_theta)
            * BP1.g_chi * (M_U / V_H)
            * (1.0 / BP1.m_h1**2 - 1.0 / BP1.m_h2**2)
        )
        assert abs(A_neg - A_neg_expected) / abs(A_neg_expected) < 1e-12, (
            f"amplitude_SI at -sin_theta = {A_neg:.6e}, expected {A_neg_expected:.6e}"
        )


# ============================================================================
# T20-T22: TestProtonNeutronRatio (S-4: structural identity)
# ============================================================================

class TestProtonNeutronRatio:
    """T20-T22: sigma_SI_p / sigma_SI_n = (f_N_proton / f_N_neutron)^2.

    This is a structural identity: the ratio depends only on form factors,
    not on m_chi, g_chi, etc. Tol 1e-10 rel.
    """

    def _test_ratio(self, bp):
        sig_p = sigma_SI_scalar_portal(
            bp.m_chi, bp.g_chi, bp.sin_theta, bp.m_h1, bp.m_h2,
            f_u=F_U_P, f_d=F_D_P, f_s=F_S_P,
        )
        sig_n = sigma_SI_scalar_portal(
            bp.m_chi, bp.g_chi, bp.sin_theta, bp.m_h1, bp.m_h2,
            f_u=F_U_N, f_d=F_D_N, f_s=F_S_N,
        )
        expected = (f_N_proton() / f_N_neutron())**2
        assert abs((sig_p / sig_n) - expected) / expected < 1e-10, (
            f"p/n ratio = {sig_p/sig_n:.10f}, expected {expected:.10f}"
        )

    def test_ratio_bp1(self):
        """T20: p/n ratio at BP1 = (f_N_p/f_N_n)^2 from constants, tol 1e-10 rel."""
        self._test_ratio(BP1)

    def test_ratio_bp_mid(self):
        """T21: p/n ratio at BP_mid = same structural identity."""
        self._test_ratio(BP_mid)

    def test_ratio_bp9(self):
        """T22: p/n ratio at BP9 = same structural identity."""
        self._test_ratio(BP9)


# ============================================================================
# T23-T24: TestBlindSpot
# ============================================================================

class TestBlindSpot:
    """T23-T24: sigma_SI == 0.0 exactly at m_h1 == m_h2 (S5 numerator form)."""

    def test_zero_at_degeneracy(self):
        """T23: sigma_SI = 0.0 (bit-exact) at BP1 with m_h2 = m_h1."""
        sigma = sigma_SI_scalar_portal(
            BP1.m_chi, BP1.g_chi, BP1.sin_theta, BP1.m_h1, m_h2=BP1.m_h1
        )
        assert sigma == 0.0, f"Degeneracy not exact zero: {sigma}"

    def test_zero_parametrized(self):
        """T24: sigma_SI = 0.0 for 5 random parameter sets with m_h2 = m_h1."""
        rng = np.random.default_rng(2601)
        for _ in range(5):
            m_chi = rng.uniform(50.0, 500.0)
            g_chi = rng.uniform(0.01, 2.0)
            sin_theta = rng.uniform(-0.2, 0.2)
            m_h1 = rng.uniform(50.0, 400.0)
            sigma = sigma_SI_scalar_portal(m_chi, g_chi, sin_theta, m_h1, m_h2=m_h1)
            assert sigma == 0.0, f"Random degeneracy not exact zero: {sigma}, m_h1={m_h1}"


# ============================================================================
# T25-T26: TestMuSignal
# ============================================================================

class TestMuSignal:
    """T25-T26: Signal strength and Eq. 18 / Eq. 22 consistency."""

    def test_theta_zero(self):
        """T25: mu_signal(0) == 1.0 exactly, tol 1e-15 abs."""
        assert abs(mu_signal(0.0) - 1.0) < 1e-15

    def test_eq18_eq22_consistency(self):
        """T26 (N-4 strengthened): sigma_pp_h2(sigma_SM, 0.2) + mu_signal(0.2)*sigma_SM == sigma_SM.

        At sin_theta=0.2, checks:
          sin^2*sigma_SM + cos^2*sigma_SM = sigma_SM  (probability conservation)
        The production times branching must sum to the SM total.
        tol 1e-15 abs.
        """
        sigma_SM = 1.0
        st = 0.2
        total = sigma_pp_h2(sigma_SM, st) + mu_signal(st) * sigma_SM
        assert abs(total - sigma_SM) < 1e-15, f"Total = {total:.16f}, expected 1.0"


# ============================================================================
# T27-T29: TestRoundTrip
# ============================================================================

class TestRoundTrip:
    """T27-T29: physical -> Lagrangian -> mass_matrix -> diagonalize roundtrip.

    Note: diagonalize_numerical returns eigenvalues in ASCENDING order.
    For BP1 and BP_mid: m_h1 < m_h2, so the ascending order matches the BP.
    For BP9: m_h2=70 < m_h1=125.25, so the ascending order is (70, 125.25).
    T29 compares to sorted (min, max) of BP9's masses.
    """

    def _roundtrip(self, bp):
        """Physical -> Lagrangian -> mass_matrix -> diagonalize."""
        p = lagrangian_params_from_physical(
            bp.m_h1, bp.m_h2, bp.sin_theta, bp.lambda_s, bp.mu_3
        )
        M = mass_matrix_CPeven(
            p["lambda_h"], p["lambda_hs"], p["mu_hs"], p["mu_s_sq"],
            bp.lambda_s, bp.mu_3,
        )
        return diagonalize_numerical(M)

    def test_roundtrip_bp1(self):
        """T27: Round-trip recovers (125.25, 200, 0.001) at BP1, tol 1e-10 rel."""
        m1r, m2r, str_ = self._roundtrip(BP1)
        assert abs(m1r - BP1.m_h1) / BP1.m_h1 < 1e-10
        assert abs(m2r - BP1.m_h2) / BP1.m_h2 < 1e-10
        assert abs(str_ - BP1.sin_theta) / abs(BP1.sin_theta) < 1e-10

    def test_roundtrip_bp_mid(self):
        """T28: Round-trip recovers (125.25, 300, 0.2) at BP_mid, tol 1e-10 rel."""
        m1r, m2r, str_ = self._roundtrip(BP_mid)
        assert abs(m1r - BP_mid.m_h1) / BP_mid.m_h1 < 1e-10
        assert abs(m2r - BP_mid.m_h2) / BP_mid.m_h2 < 1e-10
        assert abs(str_ - BP_mid.sin_theta) / abs(BP_mid.sin_theta) < 1e-10

    def test_roundtrip_bp9(self):
        """T29: Round-trip at BP9.

        BP9.m_h2=70 < BP9.m_h1=125.25 (singlet lighter).
        diagonalize_numerical returns ascending eigenvalues (70, 125.25).
        We compare to sorted masses: light=70, heavy=125.25, and recover sin_theta.
        """
        m1r, m2r, str_ = self._roundtrip(BP9)
        m_light = min(BP9.m_h1, BP9.m_h2)  # 70.0
        m_heavy = max(BP9.m_h1, BP9.m_h2)  # 125.25
        assert abs(m1r - m_light) / m_light < 1e-10, f"m_light = {m1r:.6f} vs {m_light}"
        assert abs(m2r - m_heavy) / m_heavy < 1e-10, f"m_heavy = {m2r:.6f} vs {m_heavy}"
        assert abs(str_ - BP9.sin_theta) / abs(BP9.sin_theta) < 1e-10, (
            f"sin_theta = {str_:.6f} vs {BP9.sin_theta}"
        )


# ============================================================================
# T30-T32: TestStabilityPin
# ============================================================================

class TestStabilityPin:
    """T30-T32: Vacuum stability LHS (Eq. 15) hand-calc pin.

    For each BP, compute lambda_h from the Lagrangian inversion,
    then check that vacuum_stability_lhs matches the hand-calc helper.
    Tol 1e-10 rel.
    """

    def _test_stability(self, bp):
        p = _get_lagrangian(bp)
        lambda_h = p["lambda_h"]
        # For lambda_hs: the paper BPs have specific lambda_hs values in Table 1.
        # Since our lagrangian_params_from_physical sets lambda_hs=0 (by construction),
        # we use the library value for the stability test.
        # For BP1 and BP9 (paper BPs), lambda_hs is given in Table 1;
        # for BP_mid (synthetic), we use the internal reconstruction.
        lambda_hs = p["lambda_hs"]
        lambda_s = bp.lambda_s

        expected = _eq15_lhs_by_hand(lambda_h, lambda_s, lambda_hs)
        actual = vacuum_stability_lhs(lambda_h, lambda_s, lambda_hs)
        # Skip relative test if expected is near zero
        if abs(expected) < 1e-30:
            assert abs(actual - expected) < 1e-10
        else:
            assert abs(actual - expected) / abs(expected) < 1e-10

    def test_eq15_lhs_bp1(self):
        """T30: vacuum_stability_lhs at BP1 matches hand-calc, tol 1e-10 rel."""
        self._test_stability(BP1)

    def test_eq15_lhs_bp_mid(self):
        """T31: vacuum_stability_lhs at BP_mid matches hand-calc, tol 1e-10 rel."""
        self._test_stability(BP_mid)

    def test_eq15_lhs_bp9(self):
        """T32: vacuum_stability_lhs at BP9 matches hand-calc, tol 1e-10 rel."""
        self._test_stability(BP9)


# ============================================================================
# T33-T35: TestUnitarityPin
# ============================================================================

class TestUnitarityPin:
    """T33-T35: Perturbative unitarity LHS (Eq. 16) hand-calc pin.

    Tol 1e-10 rel.
    """

    def _test_unitarity(self, bp):
        p = _get_lagrangian(bp)
        lambda_h = p["lambda_h"]
        lambda_hs = p["lambda_hs"]
        lambda_s = bp.lambda_s

        expected = _eq16_lhs_by_hand(lambda_h, lambda_s, lambda_hs)
        actual = perturbative_unitarity_lhs(lambda_h, lambda_s, lambda_hs)
        if abs(expected) < 1e-30:
            assert abs(actual - expected) < 1e-10
        else:
            assert abs(actual - expected) / abs(expected) < 1e-10

    def test_eq16_lhs_bp1(self):
        """T33: perturbative_unitarity_lhs at BP1 matches hand-calc, tol 1e-10 rel."""
        self._test_unitarity(BP1)

    def test_eq16_lhs_bp_mid(self):
        """T34: perturbative_unitarity_lhs at BP_mid matches hand-calc, tol 1e-10 rel."""
        self._test_unitarity(BP_mid)

    def test_eq16_lhs_bp9(self):
        """T35: perturbative_unitarity_lhs at BP9 matches hand-calc, tol 1e-10 rel."""
        self._test_unitarity(BP9)


# ============================================================================
# T36: TestVHConvention
# ============================================================================

class TestVHConvention:
    """T36: V_H^2 * G_F * sqrt(2) ≈ 1 (S2 guard).

    V_H = 246.22 GeV is rounded to 2 decimal places; the exact value is
    246.2196 GeV, so the identity holds to ~3e-6 (tol 5e-6 used here,
    documented as deviation from plan's 1e-6).
    """

    def test_G_F_identity(self):
        """T36: |V_H^2 * G_F * sqrt(2) - 1| < 5e-6 (tol 5e-6, see deviation log)."""
        residual = abs(V_H**2 * G_F * np.sqrt(2.0) - 1.0)
        assert residual < 5e-6, f"V_H–G_F identity: {residual:.2e} >= 5e-6"


# ============================================================================
# T37: TestEq31ReducesToSingleHiggs (B-2 lock, cross-paper regression)
# ============================================================================

class TestEq31ReducesToSingleHiggs:
    """T37: sigma_SI(Eq. 31) at m_h2 -> infinity agrees with 2506.19062's
    sigma_SI_higgs_portal with y_h_eff = g_chi * sin_theta * sqrt(1 - sin_theta^2).

    This is the B-2 lock: the y_h_eff formula is FIXED and cannot be changed.
    Tolerance 1e-8 rel (B-2 requires 1e-8, not relaxed).

    Algebraic derivation in _reduce_eq31_to_single_higgs_limit docstring:
      1. (m_h2^2 - m_h1^2)/(m_h1^2 * m_h2^2) -> 1/m_h1^2 as m_h2 -> inf
      2. So sigma_31 -> (mu^2/pi)*(m_N/v)^2 * g_chi^2*sin^2*cos^2/m_h1^4 * f_N^2
      3. This equals sigma_higgs_portal(m_chi, y_h_eff, m_h1) with y_h_eff = g_chi*sin*cos
    """

    def test_heavy_second_scalar_limit(self):
        """T37: |sigma_31(m_h2=1e6) / sigma_higgs_portal(y_h_eff) - 1| < 1e-8.

        B-2 LOCKED: y_h_eff = g_chi * sin_theta * sqrt(1 - sin_theta^2)
        """
        # m_h2=1e7 chosen: at m_h2=1e6 residual is 3.14e-8 (marginally above 1e-8)
        # due to finite-m_h2 corrections; at 1e7 it's 3.14e-10 (well within 1e-8).
        m_chi, g_chi, sin_theta, m_h1, m_h2 = 222.0, 0.57, 0.001, 125.25, 1.0e7
        ours = sigma_SI_scalar_portal(m_chi, g_chi, sin_theta, m_h1, m_h2)
        y_h_eff = g_chi * sin_theta * np.sqrt(1.0 - sin_theta**2)
        ref = _ref_sigma(m_chi, y_h_eff, m_h=m_h1)
        ratio_minus_one = abs(ours / ref - 1.0)
        assert ratio_minus_one < 1e-8, (
            f"Cross-paper regression: |ours/ref - 1| = {ratio_minus_one:.2e} >= 1e-8"
        )


# ============================================================================
# S3 fix: BP9 eigenvalue ordering test
# ============================================================================

class TestBP9EigenvalueOrdering:
    """S3 fix: BP9 species-labeling vs mass-ordering convention.

    BP9 stores m_h1=125.25 (SM-like, heavier) and m_h2=70.0 (singlet-like,
    lighter). This violates the m_h1 <= m_h2 mass-ordering convention used
    by diagonalize_numerical/m_h1_h2_analytical. The stored fields label
    eigenstates by SPECIES (SM-like vs singlet-like), not by mass ordering.

    This test verifies that the diagonalized eigenvalues DO respect ascending
    mass ordering (m_h1_eig <= m_h2_eig), even though BP9.m_h1 > BP9.m_h2.
    """

    def test_bp9_diagonalized_eigenvalues_ascending(self):
        """BP9: diagonalized eigenvalues are ascending (m_h1_eig <= m_h2_eig)."""
        p = _get_lagrangian(BP9)
        M = mass_matrix_CPeven(
            p["lambda_h"], p["lambda_hs"], p["mu_hs"], p["mu_s_sq"],
            BP9.lambda_s, BP9.mu_3,
        )
        m1_eig, m2_eig, _ = diagonalize_numerical(M)
        assert m1_eig <= m2_eig + 1e-12, (
            f"BP9: diagonalized eigenvalues not ascending: m_h1_eig={m1_eig:.4f}, "
            f"m_h2_eig={m2_eig:.4f}"
        )
