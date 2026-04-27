"""
Synthetic data generators and metadata for the 12 A/B test cases.

Each case is a dict with:
    id: str              — kebab-case identifier
    description: str     — physics description (shared by both agents)
    skill_category: str  — which skill applies ('hep-plot', 'exclusion-contour', 'theory-data-comparison')
    generate: Callable   — function(data_dir: Path) -> Path to .npz file
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


# ── Case 1: Z mass peak ─────────────────────────────────────────────────────

def _gen_z_mass_peak(data_dir: Path) -> Path:
    """Breit-Wigner signal + flat background for Z→μμ invariant mass."""
    rng = np.random.default_rng(42)
    m = np.linspace(60, 120, 200)

    # Breit-Wigner: Γ=2.5 GeV, M=91.2 GeV
    gamma = 2.5
    mz = 91.2
    bw = (gamma / 2) ** 2 / ((m - mz) ** 2 + (gamma / 2) ** 2)
    signal = 5000 * bw / bw.max()

    # Flat combinatorial background
    background = 200 + rng.normal(0, 8, len(m))
    background = np.clip(background, 0, None)

    # "Data" = signal + background + Poisson noise
    data = signal + background
    data_observed = rng.poisson(data).astype(float)
    data_errors = np.sqrt(np.clip(data_observed, 1, None))

    out = data_dir / "z_mass_peak.npz"
    np.savez(out, mass=m, signal=signal, background=background,
             data=data_observed, data_errors=data_errors)
    return out


CASE_Z_MASS_PEAK = {
    "id": "z_mass_peak",
    "description": (
        "Plot the dimuon invariant mass distribution showing the Z boson resonance peak. "
        "The data contains: 'mass' (GeV) as x-axis, 'signal' (Breit-Wigner Z peak), "
        "'background' (flat combinatorial), 'data' (observed counts), and 'data_errors' "
        "(statistical uncertainties). Show the data as points with error bars, and overlay "
        "the signal and background components. X-axis: m_μμ [GeV], Y-axis: Events / 0.3 GeV."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_z_mass_peak,
}


# ── Case 2: pT spectrum ─────────────────────────────────────────────────────

def _gen_pt_spectrum(data_dir: Path) -> Path:
    """Steeply falling jet pT spectrum with power-law tail."""
    rng = np.random.default_rng(43)

    pt = np.logspace(np.log10(20), np.log10(2000), 80)
    # Power-law: dN/dpT ~ pT^{-5} at high pT, exponential at low pT
    spectrum = 1e8 * np.exp(-pt / 50) + 1e12 * pt ** (-5)

    # Add realistic statistical fluctuations
    data = rng.poisson(np.clip(spectrum, 1, None).astype(int)).astype(float)
    data_errors = np.sqrt(np.clip(data, 1, None))

    out = data_dir / "pt_spectrum.npz"
    np.savez(out, pt=pt, spectrum=spectrum, data=data, data_errors=data_errors)
    return out


CASE_PT_SPECTRUM = {
    "id": "pt_spectrum",
    "description": (
        "Plot the inclusive jet transverse momentum spectrum from pp collisions at 13 TeV. "
        "The data contains: 'pt' (GeV) as x-axis, 'spectrum' (theory prediction), "
        "'data' (observed counts), 'data_errors' (statistical). This spans several orders "
        "of magnitude and needs a log-log or log-y scale. X-axis: p_T [GeV], "
        "Y-axis: dN/dp_T [GeV^{-1}]."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_pt_spectrum,
}


# ── Case 3: Stacked backgrounds ─────────────────────────────────────────────

def _gen_stacked_backgrounds(data_dir: Path) -> Path:
    """H→γγ signal peak on γγ, γj, jj backgrounds."""
    rng = np.random.default_rng(44)
    m = np.linspace(100, 160, 120)

    # Narrow Higgs signal at 125 GeV
    signal = 80 * np.exp(-0.5 * ((m - 125) / 1.5) ** 2)

    # Backgrounds: smooth falling distributions
    bg_diphoton = 600 * np.exp(-0.02 * (m - 100))  # γγ continuum
    bg_photon_jet = 300 * np.exp(-0.015 * (m - 100))  # γj
    bg_dijet = 100 * np.exp(-0.025 * (m - 100))  # jj (fake photons)

    total = signal + bg_diphoton + bg_photon_jet + bg_dijet
    data = rng.poisson(np.clip(total, 1, None).astype(int)).astype(float)
    data_errors = np.sqrt(np.clip(data, 1, None))

    out = data_dir / "stacked_backgrounds.npz"
    np.savez(out, mass=m, signal=signal, bg_diphoton=bg_diphoton,
             bg_photon_jet=bg_photon_jet, bg_dijet=bg_dijet,
             data=data, data_errors=data_errors)
    return out


CASE_STACKED_BACKGROUNDS = {
    "id": "stacked_backgrounds",
    "description": (
        "Plot the diphoton invariant mass distribution showing the Higgs boson signal "
        "at 125 GeV on top of stacked backgrounds. The data contains: 'mass' (GeV), "
        "'signal' (H→γγ), 'bg_diphoton' (γγ continuum), 'bg_photon_jet' (γ+jet), "
        "'bg_dijet' (dijet with fake photons), 'data' (observed), 'data_errors'. "
        "Show backgrounds as stacked filled histograms (largest on bottom), signal as "
        "a separate filled or line component, and data as points with error bars. "
        "X-axis: m_γγ [GeV], Y-axis: Events / 0.5 GeV."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_stacked_backgrounds,
}


# ── Case 4: Exclusion contour (pre-interpolated) ────────────────────────────

def _gen_exclusion_contour(data_dir: Path) -> Path:
    """Pre-interpolated exclusion contour: stop pair production in (m_stop, m_neutralino) plane."""
    # Observed limit contour
    m_stop_obs = np.linspace(200, 1200, 100)
    m_neu_obs = 0.45 * m_stop_obs - 40 + 15 * np.sin(m_stop_obs / 200)

    # Expected limit (slightly weaker)
    m_neu_exp = 0.42 * m_stop_obs - 35 + 12 * np.sin(m_stop_obs / 200)

    # Brazil bands: +/-1σ and +/-2σ around expected
    m_neu_exp_p1 = m_neu_exp + 25
    m_neu_exp_m1 = m_neu_exp - 25
    m_neu_exp_p2 = m_neu_exp + 50
    m_neu_exp_m2 = m_neu_exp - 50

    # Kinematic boundary: m_neutralino = m_stop - m_top
    m_top = 173.0
    m_stop_kin = np.linspace(200, 1200, 100)
    m_neu_kin = m_stop_kin - m_top

    out = data_dir / "exclusion_contour.npz"
    np.savez(out,
             m_stop_obs=m_stop_obs, m_neu_obs=m_neu_obs,
             m_stop_exp=m_stop_obs, m_neu_exp=m_neu_exp,
             m_neu_exp_p1=m_neu_exp_p1, m_neu_exp_m1=m_neu_exp_m1,
             m_neu_exp_p2=m_neu_exp_p2, m_neu_exp_m2=m_neu_exp_m2,
             m_stop_kin=m_stop_kin, m_neu_kin=m_neu_kin)
    return out


CASE_EXCLUSION_CONTOUR = {
    "id": "exclusion_contour",
    "description": (
        "Plot an exclusion contour for direct stop pair production in the "
        "(m_stop, m_neutralino) plane at 13 TeV LHC with 139 fb^{-1}. "
        "The data contains pre-interpolated contour coordinates:\n"
        "- 'm_stop_obs', 'm_neu_obs': observed 95% CL exclusion boundary\n"
        "- 'm_stop_exp', 'm_neu_exp': expected exclusion boundary\n"
        "- 'm_neu_exp_p1/m1': +/-1σ expected band boundaries\n"
        "- 'm_neu_exp_p2/m2': +/-2σ expected band boundaries\n"
        "- 'm_stop_kin', 'm_neu_kin': kinematic boundary (m_neutralino = m_stop - m_top)\n"
        "Draw: observed limit as solid line, expected as dashed, green (+/-1σ) and "
        "yellow (+/-2σ) Brazil bands as filled regions between the band boundaries, "
        "shade the excluded region (below observed), and show the kinematic boundary. "
        "X-axis: m_stop [GeV], Y-axis: m_neutralino [GeV]."
    ),
    "skill_category": "exclusion-contour",
    "generate": _gen_exclusion_contour,
}


# ── Case 5: Theory vs data with ratio panel ─────────────────────────────────

def _gen_theory_data_ratio(data_dir: Path) -> Path:
    """NLO differential cross section vs binned CMS measurement."""
    rng = np.random.default_rng(46)

    # 15 bins in top quark pT
    bin_edges = np.array([0, 40, 80, 120, 160, 200, 250, 300, 350, 400,
                          500, 600, 700, 800, 1000, 1200])
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_widths = np.diff(bin_edges)

    # NLO theory prediction (falling spectrum)
    theory = 50.0 * np.exp(-bin_centers / 200.0)
    theory_scale_up = theory * (0.05 + 0.03 * bin_centers / 1000)  # 5-8% scale unc
    theory_scale_down = theory * (0.04 + 0.025 * bin_centers / 1000)
    theory_pdf_up = theory * 0.03  # 3% PDF unc
    theory_pdf_down = theory * 0.03

    # Data: theory + noise + small systematic shift
    data = theory * (1 + rng.normal(0, 0.05, len(theory))) + rng.normal(0, 0.5, len(theory))
    data = np.clip(data, 0.01, None)
    stat_err = data * (0.02 + 0.05 * bin_centers / 1000)  # 2-7% stat
    syst_err = data * 0.03  # 3% syst

    out = data_dir / "theory_data_ratio.npz"
    np.savez(out, bin_edges=bin_edges, bin_centers=bin_centers, bin_widths=bin_widths,
             theory=theory, theory_scale_up=theory_scale_up, theory_scale_down=theory_scale_down,
             theory_pdf_up=theory_pdf_up, theory_pdf_down=theory_pdf_down,
             data=data, stat_err=stat_err, syst_err=syst_err)
    return out


CASE_THEORY_DATA_RATIO = {
    "id": "theory_data_ratio",
    "description": (
        "Plot an NLO QCD prediction vs CMS data for the top quark pT differential cross "
        "section at 13 TeV. The data contains:\n"
        "- 'bin_edges', 'bin_centers', 'bin_widths': binning in pT [GeV]\n"
        "- 'theory': NLO central prediction [pb/GeV]\n"
        "- 'theory_scale_up/down': scale uncertainty (μR, μF variation)\n"
        "- 'theory_pdf_up/down': PDF uncertainty\n"
        "- 'data': measured values, 'stat_err': statistical, 'syst_err': systematic\n"
        "Create a two-panel figure: main panel with data points (error bars) and theory "
        "curve (with scale and PDF uncertainty bands), plus a ratio panel below showing "
        "Data/Theory with a reference line at 1.0. "
        "X-axis: p_T^t [GeV], Y-axis: dσ/dp_T [pb/GeV]."
    ),
    "skill_category": "theory-data-comparison",
    "generate": _gen_theory_data_ratio,
}


# ── Case 6: 2D parameter scan ───────────────────────────────────────────────

def _gen_parameter_scan_2d(data_dir: Path) -> Path:
    """χ² heatmap over (tan β, m_A) plane for MSSM Higgs search."""
    tan_beta = np.linspace(1, 60, 80)
    m_a = np.linspace(200, 2000, 80)
    TB, MA = np.meshgrid(tan_beta, m_a)

    # Fake χ² landscape with a minimum around tan_beta=10, m_A=800
    chi2 = (
        ((TB - 10) / 15) ** 2
        + ((MA - 800) / 400) ** 2
        + 0.5 * np.sin(TB / 5) * np.cos(MA / 300)
    )
    # Normalize to have minimum near 0
    chi2 = chi2 - chi2.min() + 0.1

    out = data_dir / "parameter_scan_2d.npz"
    np.savez(out, tan_beta=tan_beta, m_a=m_a, chi2=chi2)
    return out


CASE_PARAMETER_SCAN_2D = {
    "id": "parameter_scan_2d",
    "description": (
        "Plot a 2D chi-squared heatmap from an MSSM Higgs sector fit in the "
        "(tan β, m_A) parameter plane. The data contains:\n"
        "- 'tan_beta': 1D array of tan β values\n"
        "- 'm_a': 1D array of m_A values [GeV]\n"
        "- 'chi2': 2D array of Δχ² values (shape: len(m_a) × len(tan_beta))\n"
        "Show as a color heatmap with contour lines at Δχ² = 2.30 (68% CL) and "
        "Δχ² = 5.99 (95% CL). Mark the best-fit point. "
        "X-axis: tan β, Y-axis: m_A [GeV]."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_parameter_scan_2d,
}


# ── Case 7: Running couplings ───────────────────────────────────────────────

def _gen_running_couplings(data_dir: Path) -> Path:
    """α₁, α₂, α₃ RGE running from M_Z to M_GUT (SM one-loop)."""
    mu = np.logspace(np.log10(91.2), 16, 300)  # 91.2 GeV to 10^16 GeV
    log_mu = np.log(mu / 91.2)

    # SM one-loop beta coefficients: b_i = (41/10, -19/6, -7)
    alpha1_inv_0 = 1 / 0.01017  # α₁(MZ) ≈ 0.01017
    alpha2_inv_0 = 1 / 0.03378  # α₂(MZ) ≈ 0.03378
    alpha3_inv_0 = 1 / 0.1181   # α₃(MZ) ≈ 0.1181

    b1, b2, b3 = 41 / 10, -19 / 6, -7
    two_pi = 2 * np.pi

    alpha1_inv = alpha1_inv_0 - b1 / two_pi * log_mu
    alpha2_inv = alpha2_inv_0 - b2 / two_pi * log_mu
    alpha3_inv = alpha3_inv_0 - b3 / two_pi * log_mu

    out = data_dir / "running_couplings.npz"
    np.savez(out, mu=mu, alpha1_inv=alpha1_inv, alpha2_inv=alpha2_inv, alpha3_inv=alpha3_inv)
    return out


CASE_RUNNING_COUPLINGS = {
    "id": "running_couplings",
    "description": (
        "Plot the running of the three SM gauge couplings from M_Z to the GUT scale. "
        "The data contains:\n"
        "- 'mu': energy scale array [GeV], from 91.2 to 10^{16} GeV\n"
        "- 'alpha1_inv', 'alpha2_inv', 'alpha3_inv': inverse couplings α_i^{-1}(μ)\n"
        "Plot all three as lines vs μ on a log x-axis (linear y). "
        "Label each curve: α₁⁻¹ (U(1)), α₂⁻¹ (SU(2)), α₃⁻¹ (SU(3)). "
        "X-axis: μ [GeV] (log scale), Y-axis: α_i^{-1}(μ)."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_running_couplings,
}


# ── Case 8: Angular distribution ────────────────────────────────────────────

def _gen_angular_distribution(data_dir: Path) -> Path:
    """dσ/d cos θ for e⁺e⁻→μ⁺μ⁻ at √s = 91.2 GeV (Z pole)."""
    rng = np.random.default_rng(49)
    cos_theta = np.linspace(-0.95, 0.95, 50)

    # QED + Z: (1 + cos²θ) + A_FB * cos θ
    a_fb = 0.0169  # forward-backward asymmetry at Z pole
    dsigma = 1.0 + cos_theta ** 2 + 8 / 3 * a_fb * cos_theta
    dsigma = dsigma / dsigma.max() * 450  # normalize to ~450 events at peak

    data = rng.poisson(np.clip(dsigma, 1, None).astype(int)).astype(float)
    data_errors = np.sqrt(np.clip(data, 1, None))

    out = data_dir / "angular_distribution.npz"
    np.savez(out, cos_theta=cos_theta, theory=dsigma, data=data, data_errors=data_errors)
    return out


CASE_ANGULAR_DISTRIBUTION = {
    "id": "angular_distribution",
    "description": (
        "Plot the angular distribution dσ/d cos θ for e⁺e⁻→μ⁺μ⁻ at the Z pole "
        "(√s = 91.2 GeV). The data contains:\n"
        "- 'cos_theta': cos θ values from -0.95 to 0.95\n"
        "- 'theory': theoretical prediction (1 + cos²θ + forward-backward asymmetry)\n"
        "- 'data': measured values, 'data_errors': statistical uncertainties\n"
        "Show theory as a smooth curve and data as points with error bars. "
        "X-axis: cos θ, Y-axis: dσ/d cos θ [pb]."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_angular_distribution,
}


# ── Case 9: Cross section vs √s ─────────────────────────────────────────────

def _gen_cross_section_vs_sqrt_s(data_dir: Path) -> Path:
    """σ(pp→tt̄) measurements at multiple √s energies with NNLO theory band."""
    # Measured points at different √s
    sqrt_s = np.array([7.0, 8.0, 13.0, 13.6, 14.0])
    data = np.array([173.3, 241.5, 831.8, 900.2, 950.0])
    stat_err = np.array([2.3, 3.1, 6.2, 12.0, 25.0])
    syst_err = np.array([7.8, 10.5, 25.0, 30.0, 40.0])

    # NNLO theory curve (continuous)
    sqrt_s_theory = np.linspace(6, 15, 200)
    # Approximate parametrization: σ ~ (√s)^{2.5} normalized
    theory = 3.0 * sqrt_s_theory ** 2.5
    theory_unc_up = theory * 0.04  # ~4% scale uncertainty
    theory_unc_down = theory * 0.035

    out = data_dir / "cross_section_vs_sqrt_s.npz"
    np.savez(out, sqrt_s_data=sqrt_s, data=data, stat_err=stat_err, syst_err=syst_err,
             sqrt_s_theory=sqrt_s_theory, theory=theory,
             theory_unc_up=theory_unc_up, theory_unc_down=theory_unc_down)
    return out


CASE_CROSS_SECTION_VS_SQRT_S = {
    "id": "cross_section_vs_sqrt_s",
    "description": (
        "Plot the total tt̄ production cross section as a function of √s, comparing "
        "measurements at different LHC energies to the NNLO QCD prediction. The data contains:\n"
        "- 'sqrt_s_data': center-of-mass energies [TeV] of measurements\n"
        "- 'data': measured σ(pp→tt̄) [pb], 'stat_err', 'syst_err'\n"
        "- 'sqrt_s_theory': continuous √s array, 'theory': NNLO prediction [pb]\n"
        "- 'theory_unc_up/down': scale uncertainty on theory\n"
        "Show data as points with error bars (inner=stat, outer=total), theory as a "
        "curve with uncertainty band. X-axis: √s [TeV], Y-axis: σ(pp→tt̄) [pb]."
    ),
    "skill_category": "theory-data-comparison",
    "generate": _gen_cross_section_vs_sqrt_s,
}


# ── Case 10: Missing ET ─────────────────────────────────────────────────────

def _gen_missing_et(data_dir: Path) -> Path:
    """MET distribution: W→ℓν signal + QCD multijet + Z→νν backgrounds."""
    rng = np.random.default_rng(51)
    met = np.linspace(0, 500, 100)

    # W→ℓν: Jacobian peak around 40 GeV
    w_signal = 8000 * np.exp(-0.5 * ((met - 40) / 15) ** 2) + 200 * np.exp(-met / 80)

    # QCD multijet: steeply falling
    qcd_bg = 20000 * np.exp(-met / 30)

    # Z→νν: broad
    z_bg = 500 * np.exp(-met / 100)

    total = w_signal + qcd_bg + z_bg
    data = rng.poisson(np.clip(total, 1, None).astype(int)).astype(float)
    data_errors = np.sqrt(np.clip(data, 1, None))

    out = data_dir / "missing_et.npz"
    np.savez(out, met=met, w_signal=w_signal, qcd_bg=qcd_bg, z_bg=z_bg,
             data=data, data_errors=data_errors)
    return out


CASE_MISSING_ET = {
    "id": "missing_et",
    "description": (
        "Plot the missing transverse energy (MET) distribution showing the W→ℓν signal "
        "and backgrounds. The data contains:\n"
        "- 'met': missing ET values [GeV]\n"
        "- 'w_signal': W→ℓν component, 'qcd_bg': QCD multijet, 'z_bg': Z→νν\n"
        "- 'data': observed, 'data_errors': statistical\n"
        "Show backgrounds as stacked filled histograms (QCD on bottom, Z above, W on top) "
        "with data as points. Use log y-axis — the distribution spans several orders of "
        "magnitude. X-axis: MET [GeV], Y-axis: Events / 5 GeV."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_missing_et,
}


# ── Case 11: Branching ratios ───────────────────────────────────────────────

def _gen_branching_ratios(data_dir: Path) -> Path:
    """SM Higgs branching ratios vs m_H for the main decay channels."""
    m_h = np.linspace(80, 200, 200)

    # Approximate SM branching ratios (qualitatively correct shapes)
    br_bb = 0.6 * np.exp(-0.5 * ((m_h - 120) / 50) ** 2) * (m_h < 160) + 0.001
    br_ww = np.clip(0.01 * (m_h - 130) ** 2 / 2000, 0, 0.95) * (m_h > 130)
    br_zz = np.clip(0.005 * (m_h - 130) ** 2 / 2000, 0, 0.3) * (m_h > 130)
    br_tautau = 0.07 * np.exp(-0.5 * ((m_h - 120) / 40) ** 2)
    br_gamgam = 0.0025 * np.exp(-0.5 * ((m_h - 125) / 20) ** 2)
    br_gg = 0.08 * np.exp(-0.5 * ((m_h - 120) / 50) ** 2) * (m_h < 160)

    # Normalize so they roughly sum to <=1 at each mass point
    total = br_bb + br_ww + br_zz + br_tautau + br_gamgam + br_gg
    total = np.clip(total, 1.0, None)
    br_bb /= total
    br_ww /= total
    br_zz /= total
    br_tautau /= total
    br_gamgam /= total
    br_gg /= total

    out = data_dir / "branching_ratios.npz"
    np.savez(out, m_h=m_h, br_bb=br_bb, br_ww=br_ww, br_zz=br_zz,
             br_tautau=br_tautau, br_gamgam=br_gamgam, br_gg=br_gg)
    return out


CASE_BRANCHING_RATIOS = {
    "id": "branching_ratios",
    "description": (
        "Plot the Standard Model Higgs boson branching ratios as a function of m_H. "
        "The data contains:\n"
        "- 'm_h': Higgs mass values [GeV], from 80 to 200\n"
        "- 'br_bb': BR(H→bb̄), 'br_ww': BR(H→WW), 'br_zz': BR(H→ZZ)\n"
        "- 'br_tautau': BR(H→ττ), 'br_gamgam': BR(H→γγ), 'br_gg': BR(H→gg)\n"
        "Plot each channel as a separate line. Label each curve directly on the plot "
        "(no legend box). Use log y-axis since BR(γγ) is ~10^{-3} while BR(bb̄) is ~0.6. "
        "X-axis: m_H [GeV], Y-axis: Branching Ratio."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_branching_ratios,
}


# ── Case 12: Multi-panel comparison ─────────────────────────────────────────

def _gen_multi_panel_comparison(data_dir: Path) -> Path:
    """Same jet pT distribution at 8 TeV and 13 TeV for side-by-side comparison."""
    rng = np.random.default_rng(53)
    pt = np.linspace(50, 800, 60)

    # 8 TeV
    theory_8 = 3e4 * np.exp(-pt / 120)
    data_8 = rng.poisson(np.clip(theory_8, 1, None).astype(int)).astype(float)
    err_8 = np.sqrt(np.clip(data_8, 1, None))

    # 13 TeV (higher cross section, harder spectrum)
    theory_13 = 8e4 * np.exp(-pt / 160)
    data_13 = rng.poisson(np.clip(theory_13, 1, None).astype(int)).astype(float)
    err_13 = np.sqrt(np.clip(data_13, 1, None))

    out = data_dir / "multi_panel_comparison.npz"
    np.savez(out, pt=pt, theory_8=theory_8, data_8=data_8, err_8=err_8,
             theory_13=theory_13, data_13=data_13, err_13=err_13)
    return out


CASE_MULTI_PANEL_COMPARISON = {
    "id": "multi_panel_comparison",
    "description": (
        "Plot the inclusive jet pT distribution at two different center-of-mass energies "
        "as side-by-side panels for comparison. The data contains:\n"
        "- 'pt': transverse momentum [GeV]\n"
        "- 'theory_8', 'data_8', 'err_8': 8 TeV prediction, data, errors\n"
        "- 'theory_13', 'data_13', 'err_13': 13 TeV prediction, data, errors\n"
        "Create a two-panel figure (left: 8 TeV, right: 13 TeV) with shared y-axis. "
        "Each panel: theory curve + data points with error bars. Log y-axis. "
        "X-axis: p_T [GeV], Y-axis: dσ/dp_T [pb/GeV]. Label each panel with its √s."
    ),
    "skill_category": "hep-plot",
    "generate": _gen_multi_panel_comparison,
}


# ── Registry ────────────────────────────────────────────────────────────────

ALL_CASES = [
    CASE_Z_MASS_PEAK,
    CASE_PT_SPECTRUM,
    CASE_STACKED_BACKGROUNDS,
    CASE_EXCLUSION_CONTOUR,
    CASE_THEORY_DATA_RATIO,
    CASE_PARAMETER_SCAN_2D,
    CASE_RUNNING_COUPLINGS,
    CASE_ANGULAR_DISTRIBUTION,
    CASE_CROSS_SECTION_VS_SQRT_S,
    CASE_MISSING_ET,
    CASE_BRANCHING_RATIOS,
    CASE_MULTI_PANEL_COMPARISON,
]
