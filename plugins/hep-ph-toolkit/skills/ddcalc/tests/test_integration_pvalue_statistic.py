"""
Integration tests for the likelihood-ratio p-value statistic.

Added 2026-07-11 alongside the ddcalc_driver.c fix for the p-value/exclusion
bug (see plugins/hep-ph-toolkit/skills/ddcalc/scripts/ddcalc_driver.c file
header and /Users/yianni/.claude/jobs/c703354a/tmp/ddcalc-diag/DIAGNOSIS.md).

Two checks that exercise the real compiled DDCalc driver end-to-end:

  1. Monotonicity: p_value must be non-increasing as sigma_SI increases over
     a 3-point scan (more cross section => more expected signal => lower
     likelihood-ratio p, for any experiment with nonzero sensitivity).
  2. Verdict sanity: at m_DM = 132.69 GeV, sigma_SI = 7.69e-45 cm^2 (a point
     deep in XENON1T/LZ sensitive territory), XENON1T_2018 and LZ_2022 must
     both report excluded_90cl=True, while PICO_60_2019 and DarkSide_50 (weak
     SI sensitivity) must remain excluded_90cl=False — matching the physics
     table in DIAGNOSIS.md and probe2.c/probe3.c.

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
class TestPValueMonotonicity:
    """p_value must be non-increasing in sigma_SI over a 3-point scan."""

    def test_xenon1t_pvalue_monotonic_in_sigma(self):
        """
        Measured 2026-07-11 at m_DM = 132.69 GeV:
          sigma=1e-46 -> p=6.9e-1 (from probe2.c table)
          sigma=1e-45 -> p=1.2e-8
          sigma=1e-43 -> p=0
        Re-measured here via the wrapper to catch regressions.
        """
        _get_ddcalc_path()
        sigmas = [1e-46, 1e-45, 1e-43]
        pvals = []
        for s in sigmas:
            result = _run_ddcalc(132.692285, s)
            pvals.append(result["experiments"]["XENON1T_2018"]["p_value"])

        for p in pvals:
            assert 0.0 <= p <= 1.0, f"p_value out of [0,1]: {p}"

        assert pvals[0] >= pvals[1] >= pvals[2], (
            f"p_value not monotonically non-increasing in sigma_SI: {pvals} "
            f"for sigmas {sigmas}"
        )

    def test_lz2022_pvalue_monotonic_in_sigma(self):
        _get_ddcalc_path()
        sigmas = [1e-48, 1e-47, 1e-46]
        pvals = []
        for s in sigmas:
            result = _run_ddcalc(132.692285, s)
            pvals.append(result["experiments"]["LZ_2022"]["p_value"])

        for p in pvals:
            assert 0.0 <= p <= 1.0, f"p_value out of [0,1]: {p}"

        assert pvals[0] >= pvals[1] >= pvals[2], (
            f"p_value not monotonically non-increasing in sigma_SI: {pvals} "
            f"for sigmas {sigmas}"
        )


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestVerdictSanity:
    """
    At m_DM = 132.69 GeV, sigma_SI = 7.69e-45 cm^2: XENON1T/LZ excluded,
    PICO/DarkSide (weak SI sensitivity) unchanged/not excluded.
    Measured values (2026-07-11, DIAGNOSIS.md probe2.c):
      XENON1T_2018 p=5.9e-77 (excluded), LZ_2022 p=0 (excluded)
      PICO_60_2019 p=1.0 (not excluded), DarkSide_50 p=0.13 (not excluded)
    """

    def test_xenon1t_and_lz_excluded(self):
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 7.69e-45)
        assert result["experiments"]["XENON1T_2018"]["excluded_90cl"] is True
        assert result["experiments"]["LZ_2022"]["excluded_90cl"] is True

    def test_pico_and_darkside_unchanged(self):
        """
        PICO_60_2019 and DarkSide_50 stay 'not excluded' at this SI-only point
        because of their genuinely weak *SI* sensitivity at 132.69 GeV — NOT
        because SD is dead.  (Before the ddcalc-sd-channel fix this assertion
        also held vacuously for any SD-active WIMP; it no longer does — see
        TestSDChannel, where PICO excludes an SD-proton point.)  Numbers are
        unchanged by the SD fix: the SD channel does not touch SI rates, so the
        SI-only golden values are identical before and after.
        """
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 7.69e-45)
        assert result["experiments"]["PICO_60_2019"]["excluded_90cl"] is False
        assert result["experiments"]["DarkSide_50"]["excluded_90cl"] is False

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
        sensitivity): sd_p=1e-41 -> p=1.0, 1e-40 -> p=3.3e-3, 1e-39 -> p=1.1e-51.
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
        sigma_SD_p = 1e-39 cm^2, ~25-40x above that reach.  Measured p=1.1e-51
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
        sigma_SD_n = 1e-40 cm^2: XENON1T p=1.2e-4 (excluded), LZ p~1e-201
        (excluded), PICO p=1.0 (not excluded).  Confirms the SD form factors
        carry the correct proton/neutron structure, not a scalar stand-in.
        """
        _get_ddcalc_path()
        result = _run_ddcalc(132.692285, 0.0, sigma_sd_neutron_cm2=1e-40)
        assert result["experiments"]["XENON1T_2018"]["excluded_90cl"] is True
        assert result["experiments"]["LZ_2022"]["excluded_90cl"] is True
        assert result["experiments"]["PICO_60_2019"]["excluded_90cl"] is False
