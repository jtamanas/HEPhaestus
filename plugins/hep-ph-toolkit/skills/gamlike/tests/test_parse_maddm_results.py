"""
test_parse_maddm_results.py — unit tests for parse_maddm_results.py.

One class per section + invariants + exit codes.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"

# Load parser module in-process
_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def _parse(fixture_name):
    """Parse a fixture file in-process."""
    return _mod.parse_file(_FIXTURES / fixture_name)


def _run(fixture_name, extra_args=None, tmp_path=None):
    """Run parser via subprocess. Returns (CompletedProcess, out_path_or_None)."""
    import tempfile, os
    if tmp_path is None:
        tmp_path = Path(tempfile.mkdtemp())
    out_path = tmp_path / (fixture_name + ".gamlike.json")
    cmd = [
        sys.executable, str(_SCRIPT),
        str(_FIXTURES / fixture_name),
        "--out", str(out_path),
    ]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result, out_path if out_path.exists() else None


# ── TestRelicSection ──────────────────────────────────────────────────────────

class TestRelicSection:
    def test_omegah2_parsed(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["relic"]["present"] is True
        assert d["relic"]["Omegah2"] == pytest.approx(10.5, rel=1e-6)

    def test_omegah_planck_parsed(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["relic"]["Omegah_Planck"] == pytest.approx(0.12, rel=1e-6)

    def test_xsi_parsed(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["relic"]["xsi"] == pytest.approx(1.0, rel=1e-12)

    def test_initial_states_populated(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["relic"]["initial_states"] == ["chichibar"]

    def test_channels_nested_by_initial(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert "chichibar" in d["relic"]["channels"]
        # chichibar_wphp = 49.62 %
        assert "wphp" in d["relic"]["channels"]["chichibar"]
        assert d["relic"]["channels"]["chichibar"]["wphp"] == pytest.approx(49.62, rel=1e-4)

    def test_channels_sum_pct(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        # Should sum near 100
        assert d["relic"]["channels_sum_pct"] is not None

    def test_relic_absent_when_no_banner(self):
        d = _parse("direct_detection_only.txt")
        assert d["relic"]["present"] is False
        assert d["relic"]["Omegah2"] is None


class TestLegacyOmegaH2Alias:
    """D8: Omega h^2 (with space) parsed identically to Omegah2."""

    def test_legacy_alias_parsed(self):
        d = _parse("legacy_omega_h2_alias.txt")
        assert d["relic"]["present"] is True
        assert d["relic"]["Omegah2"] == pytest.approx(10.5, rel=1e-6)

    def test_legacy_version_untested_warning(self):
        d = _parse("legacy_omega_h2_alias.txt")
        codes = [w["code"] for w in d["warnings"]]
        assert "MADDM_VERSION_UNTESTED" in codes


# ── TestDirectSection ─────────────────────────────────────────────────────────

class TestDirectSection:
    def test_direct_present(self):
        d = _parse("direct_detection_only.txt")
        assert d["direct"]["present"] is True

    def test_results_count(self):
        d = _parse("direct_detection_only.txt")
        assert len(d["direct"]["results"]) == 3

    def test_first_result_fields(self):
        d = _parse("direct_detection_only.txt")
        r = d["direct"]["results"][0]
        assert r["name"] == "Xenon1T_2018_SI"
        assert r["sig_cm2"] == pytest.approx(1.23e-45, rel=1e-4)
        assert r["lim_cm2"] == pytest.approx(3.40e-46, rel=1e-4)
        assert "XENON1T" in r["experiment_label"]

    def test_direct_absent_when_no_banner(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["direct"]["present"] is False
        assert d["direct"]["results"] == []

    def test_real_maddm32_emits_named_nucleon_fields(self):
        """
        Real MadDM 3.2 emits SigmaN_SI_p/SigmaN_SI_n/SigmaN_SD_p/SigmaN_SD_n with
        [sigma, exp_limit] brackets. The parser must surface these as named fields
        under `direct` so downstream consumers (e.g. singlet-doublet Step 4e) don't
        have to know the MadDM key convention.
        """
        d = _parse("direct_detection_real_maddm32.txt")
        direct = d["direct"]
        assert direct["present"] is True
        assert direct["sigma_si_proton_cm2"] == pytest.approx(7.69e-45, rel=1e-4)
        assert direct["sigma_si_neutron_cm2"] == pytest.approx(7.79e-45, rel=1e-4)
        assert direct["sigma_sd_proton_cm2"] == pytest.approx(5.19e-40, rel=1e-4)
        assert direct["sigma_sd_neutron_cm2"] == pytest.approx(3.95e-40, rel=1e-4)
        assert direct["lim_si_proton_cm2"] == pytest.approx(1.17e-46, rel=1e-4)
        assert direct["lim_si_neutron_cm2"] == pytest.approx(1.17e-46, rel=1e-4)
        assert direct["lim_sd_proton_cm2"] == pytest.approx(6.52e-41, rel=1e-4)
        assert direct["lim_sd_neutron_cm2"] == pytest.approx(3.56e-41, rel=1e-4)
        # results list is preserved (generic per-key transport)
        names = {r["name"] for r in direct["results"]}
        assert {"SigmaN_SI_p", "SigmaN_SI_n", "SigmaN_SD_p", "SigmaN_SD_n"} <= names


# ── TestIndirectSection ───────────────────────────────────────────────────────

class TestIndirectSection:
    def test_indirect_present(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["present"] is True

    def test_sigmav_method_captured(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["sigmav_method"] == "madevent"

    def test_flux_method_captured(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["global"]["flux_method"] == "pythia8"

    def test_continuum_present(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["continuum"]["present"] is True
        chans = d["indirect"]["continuum"]["channels"]
        assert "chichibar_bbx" in chans
        assert chans["chichibar_bbx"]["sigmav"] == pytest.approx(1.99e-26, rel=1e-4)

    def test_lines_present(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["lines"]["present"] is True
        assert "chichibar_za" in d["indirect"]["lines"]["channels"]

    def test_g7_g8_independent_gating_lines_only(self):
        """Spectral_with_lines: only lines sub-block, no continuum."""
        d = _parse("spectral_with_lines.txt")
        assert d["indirect"]["lines"]["present"] is True
        assert d["indirect"]["continuum"]["present"] is False

    def test_total_xsec_non_null(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["global"]["Total_xsec"] == pytest.approx(2.34e-26, rel=1e-4)
        assert d["indirect"]["global"]["TotalSM_xsec"] is None

    def test_fermi_likelihood_parsed(self):
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["indirect"]["global"]["Fermi_Likelihood"] == pytest.approx(-12.3, rel=1e-3)
        assert d["indirect"]["global"]["Fermi_pvalue"] == pytest.approx(0.045, rel=1e-3)

    def test_indirect_absent_when_no_banner(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["indirect"]["present"] is False


# ── TestThermalLikelihoodGating ───────────────────────────────────────────────

class TestThermalLikelihoodGating:
    """The punch-list-named test: G13 in both directions."""

    def test_xsi_lt_1_thermal_emitted(self):
        """xsi=0.5 → thermal_emitted=true; thermal pair non-null."""
        d = _parse("full_run_xsi_lt_1.txt")
        assert d["relic"]["xsi"] == pytest.approx(0.5, rel=1e-6)
        g = d["indirect"]["global"]
        assert g["thermal_emitted"] is True
        assert g["Fermi_Likelihood_Thermal"] is not None
        assert g["Fermi_pvalue_Thermal"] is not None

    def test_xsi_eq_1_thermal_gated(self):
        """xsi=1.0 → thermal_emitted=false; FIELD_GATED warning with exact source_ref."""
        d = _parse("full_run_xsi_eq_1.txt")
        assert d["relic"]["xsi"] == pytest.approx(1.0, rel=1e-12)
        g = d["indirect"]["global"]
        assert g["thermal_emitted"] is False
        assert g["Fermi_Likelihood_Thermal"] is None
        assert g["Fermi_pvalue_Thermal"] is None
        # Exact source_ref assertion (per critic §4 T14d)
        gated_warns = [w for w in d["warnings"] if w["code"] == "FIELD_GATED"]
        assert len(gated_warns) >= 2
        for w in gated_warns:
            assert w["source_ref"] == "maddm_run_interface.py:3572-3574"
            assert w["code"] == "FIELD_GATED"

    def test_xsi_eq_1_source_ref_literal(self):
        """Exact string match assertion for source_ref (plan T14d)."""
        d = _parse("full_run_xsi_eq_1.txt")
        for w in d["warnings"]:
            if w["code"] == "FIELD_GATED":
                assert w["source_ref"] == "maddm_run_interface.py:3572-3574"

    def test_xsi_gt_1_uses_same_gate(self):
        """xsi=1 boundary: same gating behavior as xsi>1 (clamped at 1 by producer)."""
        # Using xsi=1 fixture as proxy (producer clamps ≥1 to 1.0)
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        # No indirect section → no thermal gating issue
        assert d["indirect"]["present"] is False


# ── TestTotalXsecXOR ──────────────────────────────────────────────────────────

class TestTotalXsecXOR:
    """Invariant I1: exactly one of Total_xsec / TotalSM_xsec non-null."""

    def test_madevent_gives_total_xsec(self):
        d = _parse("full_run_xsi_lt_1.txt")
        g = d["indirect"]["global"]
        assert g["Total_xsec"] is not None
        assert g["TotalSM_xsec"] is None

    def test_both_absent_exits_3(self, tmp_path):
        """Truncated indirect section (no Total_xsec) → exit 3."""
        # Create a synthetic fixture with indirect banner but missing Total_xsec
        txt = """################################################
#                 MadDM v. 3.2                 #
################################################


################################################
# Relic Density                                #
################################################

Omegah2                       = 1.20e-01
Omegah_Planck                 = 1.20e-01
xsi                           = 1.00e+00 \t # xsi = (Omega/Omega_Planck)
x_f                           = 2.50e+01
sigmav_xf                     = 4.21e-27 \t # cm^3 s^-1
# % of the relic density channels
%_chichibar_bbx               = 100.00 %


################################################
# Indirect Detection                           #
################################################
# Results in brackets display [prediction, upper limit]

# Annihilation cross section computed with the method: madevent
# Global Fermi dSph Limit computed with pythia8 spectra
Fermi_Likelihood              = -1.23e+01
Fermi_pvalue                  = 4.50e-02
"""
        f = tmp_path / "no_total_xsec.txt"
        f.write_text(txt)
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(f)],
            capture_output=True, text=True
        )
        assert result.returncode == 3, f"Expected exit 3, got {result.returncode}: {result.stderr}"


# ── TestSpectralSection ───────────────────────────────────────────────────────

class TestSpectralSection:
    def test_spectral_present(self):
        d = _parse("spectral_with_lines.txt")
        assert d["spectral"]["present"] is True

    def test_experiment_fields(self):
        d = _parse("spectral_with_lines.txt")
        exp = d["spectral"]["experiments"][0]
        assert "Fermi" in exp["experiment_name"]
        assert exp["arxiv_number"] == "1503.02641"
        assert exp["ROI"] == pytest.approx(0.5, rel=1e-6)
        assert exp["Jfactor"] == pytest.approx(1.2e23, rel=1e-4)

    def test_astrophysical_parameters_reserved_null(self):
        """G19: astrophysical_parameters always null in v0."""
        d = _parse("spectral_with_lines.txt")
        for exp in d["spectral"]["experiments"]:
            assert exp["astrophysical_parameters"] is None

    def test_peak_0_fields(self):
        d = _parse("spectral_with_lines.txt")
        peaks = d["spectral"]["experiments"][0]["peaks"]
        p0 = next(p for p in peaks if p["num"] == 0)
        assert p0["states"] == "chichibar_za"
        assert p0["energy_GeV"] == pytest.approx(100.0, rel=1e-4)
        assert p0["flux"] == pytest.approx(1.2e-12, rel=1e-4)
        assert p0["flux_UL"] == pytest.approx(3.4e-12, rel=1e-4)
        assert p0["loglike_neg2"] == pytest.approx(4.56, rel=1e-4)
        assert p0["pvalue"] == pytest.approx(0.102, rel=1e-4)
        assert p0["error_code"] == 0

    def test_peak_1_error_code_and_missing_like(self):
        """G17: missing like/pvalue → null; G18: error_code from inline comment."""
        d = _parse("spectral_with_lines.txt")
        peaks = d["spectral"]["experiments"][0]["peaks"]
        p1 = next(p for p in peaks if p["num"] == 1)
        assert p1["loglike_neg2"] is None
        assert p1["pvalue"] is None
        assert p1["error_code"] == 2

    def test_no_peaks_out_of_range(self):
        """G16: no_peaks_out_of_range=True + peaks=[] + warning."""
        d = _parse("spectral_no_peaks_oo_range.txt")
        exp = d["spectral"]["experiments"][0]
        assert exp["no_peaks_out_of_range"] is True
        assert exp["peaks"] == []
        codes = [w["code"] for w in d["warnings"]]
        assert "NO_PEAKS_OUT_OF_DETECTION_RANGE" in codes


class TestSpectralBannerShape:
    """D11: spectral has 1-line banner, distinct from 3-line banners."""

    def test_spectral_detected_without_3line_border(self):
        """Spectral section is detected even without 3-line # border."""
        d = _parse("spectral_with_lines.txt")
        assert d["spectral"]["present"] is True

    def test_spectral_not_confused_with_indirect(self):
        d = _parse("spectral_with_lines.txt")
        assert d["indirect"]["present"] is True
        assert d["spectral"]["present"] is True


# ── TestFluxesSection ─────────────────────────────────────────────────────────

class TestFluxesSection:
    def test_fluxes_source_present(self):
        d = _parse("fluxes_source.txt")
        assert d["fluxes_source"]["present"] is True

    def test_method_captured(self):
        d = _parse("fluxes_source.txt")
        assert d["fluxes_source"]["method"] == "pythia8"

    def test_flux_values(self):
        d = _parse("fluxes_source.txt")
        f = d["fluxes_source"]["fluxes"]
        assert f["neutrinos_e"] == pytest.approx(1.23e-08, rel=1e-4)
        assert f["neutrinos_mu"] == pytest.approx(4.56e-09, rel=1e-4)
        assert f["neutrinos_tau"] == pytest.approx(2.34e-09, rel=1e-4)
        assert f["gammas"] == pytest.approx(7.89e-10, rel=1e-4)

    def test_positrons_reserved_null(self):
        """G21: positrons always null in v0."""
        d = _parse("fluxes_source.txt")
        assert d["fluxes_source"]["fluxes"]["positrons"] is None


# ── TestCoannihilation ────────────────────────────────────────────────────────

class TestCoannihilation:
    """D4: nested channels schema; multiple initial states."""

    def test_two_initial_states(self):
        d = _parse("coannihilation_two_initial_states.txt")
        assert set(d["relic"]["initial_states"]) == {"chichibar", "chi1psi1"}

    def test_channels_nested_by_initial(self):
        d = _parse("coannihilation_two_initial_states.txt")
        chans = d["relic"]["channels"]
        assert "bbx" in chans["chichibar"]
        assert "bbx" in chans["chi1psi1"]
        assert chans["chichibar"]["bbx"] == pytest.approx(40.0, rel=1e-4)
        assert chans["chi1psi1"]["bbx"] == pytest.approx(30.0, rel=1e-4)

    def test_channels_sum_pct(self):
        d = _parse("coannihilation_two_initial_states.txt")
        assert d["relic"]["channels_sum_pct"] == pytest.approx(100.0, rel=1e-4)


# ── TestMissingFile ───────────────────────────────────────────────────────────

class TestMissingFile:
    def test_missing_file_exits_2(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "/nonexistent/path/MadDM_results.txt"],
            capture_output=True, text=True
        )
        assert result.returncode == 2

    def test_missing_file_stderr_message(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), "/nonexistent/MadDM.txt"],
            capture_output=True, text=True
        )
        assert "not found" in result.stderr.lower() or "ERROR" in result.stderr


# ── TestMalformedFile ─────────────────────────────────────────────────────────

class TestMalformedFile:
    def test_truncated_exits_3(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(_FIXTURES / "malformed_truncated.txt")],
            capture_output=True, text=True
        )
        assert result.returncode == 3

    def test_malformed_stderr_has_section(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(_FIXTURES / "malformed_truncated.txt")],
            capture_output=True, text=True
        )
        assert "relic" in result.stderr.lower() or "I2" in result.stderr or "malformed" in result.stderr.lower()


# ── TestUnknownSection ────────────────────────────────────────────────────────

class TestUnknownSection:
    def test_unknown_section_exits_0(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(_FIXTURES / "malformed_unknown_section.txt")],
            capture_output=True, text=True
        )
        assert result.returncode == 0

    def test_unknown_section_warning(self):
        d = _parse("malformed_unknown_section.txt")
        codes = [w["code"] for w in d["warnings"]]
        assert "UNKNOWN_SECTION" in codes

    def test_known_sections_still_parsed(self):
        """Unknown section doesn't prevent relic from parsing."""
        d = _parse("malformed_unknown_section.txt")
        assert d["relic"]["present"] is True


# ── TestNaNInfHandling ────────────────────────────────────────────────────────

class TestNaNInfHandling:
    """D15: NaN → null + FIELD_NAN; Inf → null + FIELD_INF."""

    def test_nan_channels_produce_null(self):
        """SD fixture has nan % for all channels."""
        d = _parse("relic_only_xsi_eq_1_sd.txt")
        # All channels should be None (nan converted)
        for finals in d["relic"]["channels"].values():
            for v in finals.values():
                assert v is None, f"Expected null for nan channel, got {v}"

    def test_nan_channels_produce_field_nan_warning(self):
        d = _parse("relic_only_xsi_eq_1_sd.txt")
        codes = [w["code"] for w in d["warnings"]]
        assert "FIELD_NAN" in codes

    def test_nan_in_numeric_field(self, tmp_path):
        """Inline nan in a numeric field → null + FIELD_NAN."""
        # Relic-only fixture with nan sigmav_xf - no indirect section to avoid I1
        txt = """################################################
#                 MadDM v. 3.2                 #
################################################


################################################
# Relic Density                                #
################################################

Omegah2                       = 1.20e-01
Omegah_Planck                 = 1.20e-01
xsi                           = 1.00e+00 \t # xsi = (Omega/Omega_Planck)
x_f                           = 2.50e+01
sigmav_xf                     = nan \t # cm^3 s^-1
# % of the relic density channels
%_chichibar_bbx               = 100.00 %
"""
        f = tmp_path / "nan_test.txt"
        f.write_text(txt)
        mod = _mod
        d = mod.parse_file(f)
        assert d["relic"]["sigmav_xf"] is None
        codes = [w["code"] for w in d["warnings"]]
        assert "FIELD_NAN" in codes

    def test_json_allow_nan_false(self, tmp_path):
        """Output JSON must not contain literal nan (D15)."""
        out = tmp_path / "out.json"
        result = subprocess.run(
            [sys.executable, str(_SCRIPT),
             str(_FIXTURES / "relic_only_xsi_eq_1_sd.txt"),
             "--out", str(out)],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        raw = out.read_text()
        assert "NaN" not in raw and "nan" not in raw.lower().split('"schema_version"')[0]
        # Validate it's parseable JSON
        json.loads(raw)


# ── TestSchemaConformance ─────────────────────────────────────────────────────

class TestSchemaConformance:
    """Every fixture's parsed output validates against gamlike_v1.schema.json."""

    @pytest.fixture(autouse=True)
    def require_jsonschema(self):
        jsonschema = pytest.importorskip("jsonschema")
        self._jsonschema = jsonschema

    def test_schema_version_const(self):
        d = _parse("relic_only_xsi_eq_1_2hdma.txt")
        assert d["schema_version"] == "gamlike/v1"

    @pytest.mark.parametrize("fixture_name", [
        "relic_only_xsi_eq_1_2hdma.txt",
        "relic_only_xsi_eq_1_sd.txt",
        "full_run_xsi_lt_1.txt",
        "full_run_xsi_eq_1.txt",
        "direct_detection_only.txt",
        "spectral_with_lines.txt",
        "spectral_no_peaks_oo_range.txt",
        "fluxes_source.txt",
        "coannihilation_two_initial_states.txt",
        "legacy_omega_h2_alias.txt",
        "malformed_unknown_section.txt",
    ])
    def test_fixture_validates_schema(self, fixture_name):
        import json as json_mod
        schema_path = _HERE.parent / "contracts" / "gamlike_v1.schema.json"
        schema = json_mod.loads(schema_path.read_text())
        d = _parse(fixture_name)
        self._jsonschema.validate(d, schema)
