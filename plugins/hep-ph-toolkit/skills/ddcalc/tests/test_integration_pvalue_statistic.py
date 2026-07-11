"""
Integration tests for the Wilks likelihood-ratio exclusion statistic.

Statistic (2026-07-11, ddcalc-pvalue-calibration): the driver reports
delta_chi2 = -2 (lnL_signal - lnL_background) (clamped >= 0), significance =
sqrt(delta_chi2), p_value = chi^2_1 survival = erfc(sqrt(delta_chi2/2)), and
excluded_90cl = (p_value < 0.1) <=> (delta_chi2 > 2.706 = chi^2_1 90% quantile).
See ddcalc_driver.c file header and
/Users/yianni/.claude/jobs/c703354a/tmp/ddcalc-pvalue-fix/HANDOFF.md.

NOTE ON LZ: the native DDCalc `lz` analysis is the LZ *projected* design
sensitivity (arXiv:1802.06039), registered as "LZ_projected" (NOT the observed
WS2022 limit — that is the deferred LZ_WS2024 overlay). Its p<0.1 crossing
reproduces the published projected SI curve to within a factor ~2 across
30-200 GeV.

Checks that exercise the real compiled DDCalc driver end-to-end:

  1. Monotonicity: delta_chi2 must be non-decreasing and p_value non-increasing
     as sigma_SI increases over a scan (more cross section => more expected
     signal), for any experiment with nonzero sensitivity.
  2. Verdict sanity: at m_DM = 132.69 GeV, sigma_SI = 7.69e-45 cm^2 (deep in
     xenon-sensitive territory), XENON1T_2018 and LZ_projected must report
     excluded_90cl=True, while PICO_60_2019 (genuinely weak SI at this point)
     stays excluded_90cl=False. DarkSide_50 sits right at the 90% boundary
     (delta_chi2 ~ 4.1) and is now marginally excluded under the calibrated
     chi^2_1 threshold (the old exp-ratio<0.1 cut was ~97% CL, so it read as
     not-excluded there).

SD coverage (added 2026-07-11, ddcalc-sd-channel fix): the spin-dependent
channel is now live and exercised end-to-end (TestSDChannel below). The prior
"SD produces zero signal" bug was a missing SDFF/ data-dir symlink: DDCalc
opens the spin-dependent form-factor tables from a compile-time DATA_DIR that
run_ddcalc._ensure_ddcalc_data_symlinks now heals for the SDFF/ and Wbar/
subdirs, not just the experiment dirs. With that fixed, PICO_60_2019 (a C3F8,
SD-proton-led bubble chamber) and the xenon TPCs (SD-neutron-led) respond to
sigma_SD as physics demands.

Like the golden tests, these require a real DDCalc install + C compiler to
build the driver (the wrapper compiles+caches it on first use), gated behind
HEPPH_RUN_NETWORK_TESTS=1 for consistency with the other integration tests
in this directory (no actual network access is used).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"


def _get_ddcalc_path() -> str:
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if not config_file.exists():
        pytest.skip("ddcalc_path not configured")
    with open(config_file) as f:
        path = json.load(f).get("ddcalc_path", "")
    if not path:
        pytest.skip("ddcalc_path not configured")
    return path


def _run_ddcalc(
    m_dm_gev: float,
    sigma_si_cm2: float,
    sigma_sd_proton_cm2: float = 0.0,
    sigma_sd_neutron_cm2: float = 0.0,
) -> dict:
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": m_dm_gev,
        "sigma_si_proton_cm2": sigma_si_cm2,
        "sigma_si_neutron_cm2": sigma_si_cm2,
        "sigma_sd_proton_cm2": sigma_sd_proton_cm2,
        "sigma_sd_neutron_cm2": sigma_sd_neutron_cm2,
        "source": "micromegas",
        "source_run": "test",
        "halo": None,
        "nucleon_form_factors": {"preset": "default_2018"},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(doc, tf)
        tf_path = tf.name
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_ddcalc.py"), "run",
             "--sigma-json", tf_path],
            capture_output=True,
            text=True,
        )
    finally:
        Path(tf_path).unlink(missing_ok=True)
    if result.returncode != 0:
        pytest.fail(f"run_ddcalc.py failed:\n{result.stderr}")
    return json.loads(result.stdout)


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestStatisticMonotonicity:
    """delta_chi2 non-decreasing and p_value non-increasing in sigma_SI."""

    def test_xenon1t_monotonic_in_sigma(self):
        """
        Measured 2026-07-11 at m_DM = 132.69 GeV (Wilks statistic):
          sigma=1e-46 -> delta_chi2=0.74,  p=0.39
          sigma=1e-45 -> delta_chi2=36.5,  p=1.5e-9
          sigma=1e-43 -> delta_chi2=4791,  p=0
        """
        _get_ddcalc_path()
        sigmas = [1e-46, 1e-45, 1e-43]
        pvals, dchi2s = [], []
        for s in sigmas:
            exp = _run_ddcalc(132.692285, s)["experiments"]["XENON1T_2018"]
            pvals.append(exp["p_value"])
            dchi2s.append(exp["delta_chi2"])

        for p in pvals:
            assert 0.0 <= p <= 1.0, f"p_value out of [0,1]: {p}"
        assert pvals[0] >= pvals[1] >= pvals[2], (
            f"p_value not non-increasing in sigma_SI: {pvals} for {sigmas}"
        )
        assert dchi2s[0] <= dchi2s[1] <= dchi2s[2], (
            f"delta_chi2 not non-decreasing in sigma_SI: {dchi2s} for {sigmas}"
        )
        # delta_chi2 stays finite even where p_value underflows to 0 — the
        # property that makes limit bisection (bracket on delta_chi2) robust.
        import math
        assert all(math.isfinite(d) for d in dchi2s)

    def test_lz_projected_monotonic_in_sigma(self):
        """
        m_DM = 132.69 GeV (Wilks statistic):
          sigma=1e-48 -> delta_chi2=1.62,  p=0.20
          sigma=1e-47 -> delta_chi2=16.2,  p=5.7e-5
          sigma=1e-46 -> delta_chi2=162,   p=4.1e-37
        """
        _get_ddcalc_path()
        sigmas = [1e-48, 1e-47, 1e-46]
        pvals, dchi2s = [], []
        for s in sigmas:
            exp = _run_ddcalc(132.692285, s)["experiments"]["LZ_projected"]
            pvals.append(exp["p_value"])
            dchi2s.append(exp["delta_chi2"])

        for p in pvals:
            assert 0.0 <= p <= 1.0, f"p_value out of [0,1]: {p}"
        assert pvals[0] >= pvals[1] >= pvals[2], (
            f"p_value not non-increasing in sigma_SI: {pvals} for {sigmas}"
        )
        assert dchi2s[0] <= dchi2s[1] <= dchi2s[2], (
            f"delta_chi2 not non-decreasing in sigma_SI: {dchi2s} for {sigmas}"
        )


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestVerdictSanity:
    """
    At m_DM = 132.69 GeV, sigma_SI = 7.69e-45 cm^2 (Wilks statistic).
    Measured values (2026-07-11):
      XENON1T_2018 delta_chi2=351  (excluded), LZ_projected delta_chi2=12460 (excluded)
      PICO_60_2019 delta_chi2=0.0  (not excluded; genuinely weak SI here)
      DarkSide_50  delta_chi2=4.11 p=0.043 (marginally excluded at 90% CL)
    """

    def test_xenon1t_and_lz_excluded(self):
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 7.69e-45)
        assert result["experiments"]["XENON1T_2018"]["excluded_90cl"] is True
        assert result["experiments"]["LZ_projected"]["excluded_90cl"] is True

    def test_pico_not_excluded_weak_si(self):
        """
        PICO_60_2019 stays 'not excluded' at this SI-only point because of its
        genuinely weak *SI* sensitivity at 132.69 GeV (delta_chi2 = 0, i.e. the
        signal fits no worse than background) — NOT because SD is dead (see
        TestSDChannel, where PICO excludes an SD-proton point). DarkSide_50, by
        contrast, sits right at the 90% boundary (delta_chi2 ~ 4.1 > 2.706) and
        is marginally excluded under the calibrated chi^2_1 threshold — a real
        consequence of moving from the old ~97%-CL exp-ratio<0.1 cut to a
        proper 90% CL.
        """
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 7.69e-45)
        assert result["experiments"]["PICO_60_2019"]["excluded_90cl"] is False
        assert result["experiments"]["PICO_60_2019"]["delta_chi2"] == 0.0
        ds = result["experiments"]["DarkSide_50"]
        assert ds["delta_chi2"] == pytest.approx(4.108, rel=0.05)
        assert ds["excluded_90cl"] is True

    def test_verdict_is_excluded_overall(self):
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 7.69e-45)
        assert result["verdict"] == "excluded"


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestSDChannel:
    """
    Spin-dependent channel is live (ddcalc-sd-channel fix, 2026-07-11).

    Root cause of the prior dead-SD bug: DDCalc opens its spin-dependent
    nuclear form-factor tables from ``DATA_DIR/SDFF/<Z>_<A>.dat`` where
    DATA_DIR is a compile-time path (DDInput.f90:261-265, DDNuclear.f90:538).
    The install-time symlink farm that heals that path only linked experiment
    dirs (those with energies.dat) and omitted SDFF/, so LoadSDFFFile failed
    silently and zeroed the SD form factor (DDNuclear.f90:542-544) — every SD
    rate collapsed to zero while SI (analytic Helm form factor) worked.
    run_ddcalc._ensure_ddcalc_data_symlinks now also links SDFF/ and Wbar/.

    Measured 2026-07-11 via the wrapper after the fix.
    """

    def test_pico_sd_proton_monotonic(self):
        """
        PICO_60_2019 (C3F8, SD-proton-led) p-value is non-increasing in
        sigma_SD_proton.  Measured at m_DM = 50 GeV (near PICO's best SD-p
        sensitivity): sd_p=1e-41 -> p=1.0, 1e-40 -> p=7.1e-4, 1e-39 -> p=6.0e-53.
        Before the fix all three were p=1.0 (flat), so this test would not
        have distinguished the dead channel.
        """
        _get_ddcalc_path()
        sigmas = [1e-41, 1e-40, 1e-39]
        pvals = []
        for s in sigmas:
            result = _run_ddcalc(50.0, 0.0, sigma_sd_proton_cm2=s)
            pvals.append(result["experiments"]["PICO_60_2019"]["p_value"])

        for p in pvals:
            assert 0.0 <= p <= 1.0, f"p_value out of [0,1]: {p}"
        assert pvals[0] >= pvals[1] >= pvals[2], (
            f"PICO SD-proton p_value not non-increasing in sigma_SD: {pvals} "
            f"for sigmas {sigmas}"
        )
        # And the SD channel must actually move: a large SD-p point must drop p
        # well below the baseline (guards against a silent re-regression to
        # zero-signal, which would leave every p pinned at 1.0).
        assert pvals[-1] < 1e-3, (
            f"SD-proton signal not registering at PICO (p={pvals[-1]} at "
            "sigma_SD_p=1e-39 cm^2); SD channel may be dead again"
        )

    def test_pico_excludes_large_sd_proton(self):
        """
        Verdict sanity: PICO_60_2019 must EXCLUDE an SD-proton point far above
        its published reach.  PICO-60 C3F8 (arXiv:1902.04031) excludes
        SD-proton down to ~2.5e-41 cm^2 near its minimum (~25-50 GeV); we test
        sigma_SD_p = 1e-39 cm^2, ~25-40x above that reach.  Measured p=6.0e-53
        (excluded).  This is the assertion that was structurally impossible
        before the SD fix (PICO reported p=1.0 for any SD-only WIMP).
        """
        _get_ddcalc_path()
        result = _run_ddcalc(50.0, 0.0, sigma_sd_proton_cm2=1e-39)
        pico = result["experiments"]["PICO_60_2019"]
        assert pico["excluded_90cl"] is True, (
            f"PICO should exclude sigma_SD_p=1e-39 cm^2 (p={pico['p_value']})"
        )
        assert result["verdict"] == "excluded"

    def test_xenon_sd_neutron_beats_pico(self):
        """
        Isospin cross-check: at an SD-*neutron* point the xenon TPCs
        (Xe-129/131, unpaired neutron) must exclude while PICO (fluorine,
        unpaired proton) stays weak.  Measured at m_DM = 132.69 GeV,
        sigma_SD_n = 1e-40 cm^2: XENON1T p=2.2e-5 (excluded), LZ_projected
        p~6e-203 (excluded), PICO p=1.0 (not excluded).  Confirms the SD form
        factors carry the correct proton/neutron structure, not a scalar stand-in.
        """
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 0.0, sigma_sd_neutron_cm2=1e-40)
        assert result["experiments"]["XENON1T_2018"]["excluded_90cl"] is True
        assert result["experiments"]["LZ_projected"]["excluded_90cl"] is True
        assert result["experiments"]["PICO_60_2019"]["excluded_90cl"] is False


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestCalibrationAndRelabel:
    """
    Regression guards for the 2026-07-11 Wilks-statistic + LZ-relabel change.
    Every assertion here is RED on the pre-change driver (which emitted no
    delta_chi2 field, registered the LZ analysis as "LZ_2022", and used the
    uncalibrated exp(dlnL)<0.1 cut) and GREEN afterward.
    """

    def test_lz_registered_as_projected_not_2022(self):
        """The native LZ analysis is the projected design sensitivity
        (arXiv:1802.06039), not the observed WS2022 limit — it must surface
        under LZ_projected, and the misleading LZ_2022 key must be gone."""
        _get_ddcalc_path()
        exps = _run_ddcalc(100.0, 1e-46)["experiments"]
        assert "LZ_projected" in exps
        assert "LZ_2022" not in exps

    def test_wilks_fields_present_and_consistent(self):
        """delta_chi2 / significance are emitted and internally consistent with
        p_value (p = erfc(sqrt(delta_chi2/2)))."""
        import math
        _get_ddcalc_path()
        xe = _run_ddcalc(100.0, 1e-46)["experiments"]["XENON1T_2018"]
        assert "delta_chi2" in xe and "significance" in xe
        assert xe["significance"] == pytest.approx(math.sqrt(xe["delta_chi2"]), rel=1e-4)
        assert xe["p_value"] == pytest.approx(math.erfc(math.sqrt(xe["delta_chi2"] / 2)), rel=1e-3)
        # Golden at 100 GeV / 1e-46 cm^2
        assert xe["delta_chi2"] == pytest.approx(1.493639, rel=0.02)
        assert xe["p_value"] == pytest.approx(0.2216527, rel=0.02)

    def test_lz_projected_golden_100gev(self):
        """LZ_projected golden at 100 GeV / 1e-46 cm^2."""
        _get_ddcalc_path()
        lz = _run_ddcalc(100.0, 1e-46)["experiments"]["LZ_projected"]
        assert lz["delta_chi2"] == pytest.approx(203.3188, rel=0.02)
        assert lz["excluded_90cl"] is True

    def test_excluded_at_wilks_90cl_threshold(self):
        """excluded_90cl must track delta_chi2 > 2.706 (chi^2_1 90% quantile),
        not the old ~97%-CL exp-ratio cut. DarkSide_50 at the canonical point
        has delta_chi2 ~ 4.1 -> excluded under 90% CL (was False before)."""
        _get_ddcalc_path()
        ds = _run_ddcalc(132.692285, 7.69e-45)["experiments"]["DarkSide_50"]
        assert ds["delta_chi2"] > 2.705543
        assert ds["excluded_90cl"] is True
