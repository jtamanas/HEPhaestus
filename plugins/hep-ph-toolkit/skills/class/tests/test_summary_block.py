"""
test_summary_block.py — unit tests for parse_outputs.compute_summary()
and the summary block written to cosmology.json by run_class.py.

No network, no CLASS binary required. All tests use unittest.mock.MagicMock
to stand in for the classy Cosmology object.

Methods compute_summary calls on the classy_result object:
  .Hubble(0)    → H0 in km/s/Mpc
  .h()          → dimensionless Hubble parameter
  .omega_b()    → physical baryon density ω_b
  .Omega0_cdm() → Ω_cdm (dimensionless); converted to ω_cdm = Ω_cdm * h²
  .Neff()       → effective relativistic degrees of freedom
  .z_eq()       → redshift of matter-radiation equality
  .tau_reio()   → optical depth to reionisation (cmb subcommand only)
  .sigma8()     → σ_8 (pk subcommand only)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Module loaders
# ---------------------------------------------------------------------------

def _load_parse_outputs():
    spec = importlib.util.spec_from_file_location(
        "parse_outputs_sb", SCRIPTS_DIR / "parse_outputs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_run_class():
    spec = importlib.util.spec_from_file_location(
        "run_class_sb", SCRIPTS_DIR / "run_class.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parse_outputs():
    return _load_parse_outputs()


# ---------------------------------------------------------------------------
# Mock factory
# ---------------------------------------------------------------------------

def _make_mock_classy(
    H0=67.32,
    h=0.6732,
    omega_b=0.02238,
    Omega0_cdm=0.2651,
    Neff=3.046,
    z_eq=3402.0,
    tau_reio=0.0543,
    sigma8=0.811,
):
    """Build a MagicMock that mimics the classy Cosmology object methods."""
    mock = MagicMock()
    mock.Hubble.return_value = H0
    mock.h.return_value = h
    mock.omega_b.return_value = omega_b
    mock.Omega0_cdm.return_value = Omega0_cdm
    mock.Neff.return_value = Neff
    mock.z_eq.return_value = z_eq
    mock.tau_reio.return_value = tau_reio
    mock.sigma8.return_value = sigma8
    return mock


# ---------------------------------------------------------------------------
# Tests for compute_summary
# ---------------------------------------------------------------------------

class TestSummaryKeysCompleteForBackground:
    """background subcommand: 8 keys, sigma_8 and tau_reio are None."""

    def test_summary_keys_complete_for_background(self, parse_outputs):
        mock = _make_mock_classy()
        summary = parse_outputs.compute_summary(mock, {}, "background")

        assert set(summary.keys()) == {
            "H0", "omega_b", "omega_cdm", "Omega_m_h2",
            "N_eff", "tau_reio", "sigma_8", "z_eq",
        }, f"Wrong keys: {set(summary.keys())}"

        # sigma_8 and tau_reio must be None for background
        assert summary["sigma_8"] is None, "sigma_8 should be None for background"
        assert summary["tau_reio"] is None, "tau_reio should be None for background"

    def test_background_non_null_values_are_numbers(self, parse_outputs):
        mock = _make_mock_classy()
        summary = parse_outputs.compute_summary(mock, {}, "background")

        for key in ("H0", "omega_b", "omega_cdm", "Omega_m_h2", "N_eff", "z_eq"):
            assert summary[key] is not None, f"{key} should not be None for background"
            assert isinstance(summary[key], (int, float)), f"{key} should be a number"

    def test_transfer_same_as_background(self, parse_outputs):
        mock = _make_mock_classy()
        summary = parse_outputs.compute_summary(mock, {}, "transfer")
        assert summary["sigma_8"] is None
        assert summary["tau_reio"] is None


class TestSummaryPkPopulatesSigma8:
    """pk subcommand: sigma_8 must be non-null, tau_reio must be null."""

    def test_summary_pk_populates_sigma_8(self, parse_outputs):
        mock = _make_mock_classy(sigma8=0.811)
        summary = parse_outputs.compute_summary(mock, {}, "pk")

        assert summary["sigma_8"] is not None, "sigma_8 should be populated for pk"
        assert abs(summary["sigma_8"] - 0.811) < 1e-9
        assert summary["tau_reio"] is None, "tau_reio should be None for pk"

    def test_summary_pk_still_has_all_8_keys(self, parse_outputs):
        mock = _make_mock_classy()
        summary = parse_outputs.compute_summary(mock, {}, "pk")
        assert len(summary) == 8


class TestSummaryCmbPopulatesTauReio:
    """cmb subcommand: tau_reio must be non-null, sigma_8 must be null."""

    def test_summary_cmb_populates_tau_reio(self, parse_outputs):
        mock = _make_mock_classy(tau_reio=0.0543)
        summary = parse_outputs.compute_summary(mock, {}, "cmb")

        assert summary["tau_reio"] is not None, "tau_reio should be populated for cmb"
        assert abs(summary["tau_reio"] - 0.0543) < 1e-9
        assert summary["sigma_8"] is None, "sigma_8 should be None for cmb"

    def test_summary_cmb_still_has_all_8_keys(self, parse_outputs):
        mock = _make_mock_classy()
        summary = parse_outputs.compute_summary(mock, {}, "cmb")
        assert len(summary) == 8


class TestSummaryAllSubcommandsPopulatesEverything:
    """When subcommand covers all outputs (pk chosen here for sigma_8), check
    that Omega_m_h2 = omega_b + omega_cdm."""

    def test_summary_all_subcommands_populates_everything(self, parse_outputs):
        h = 0.6732
        Omega0_cdm = 0.2651
        omega_b = 0.02238
        omega_cdm_expected = Omega0_cdm * h * h

        mock = _make_mock_classy(h=h, Omega0_cdm=Omega0_cdm, omega_b=omega_b)
        summary = parse_outputs.compute_summary(mock, {}, "pk")

        assert summary["H0"] is not None
        assert summary["omega_b"] is not None
        assert summary["omega_cdm"] is not None
        assert summary["N_eff"] is not None
        assert summary["z_eq"] is not None
        assert summary["sigma_8"] is not None  # pk populates this
        # tau_reio still None for pk
        assert summary["tau_reio"] is None

        # Check Omega_m_h2 calculation
        assert summary["Omega_m_h2"] is not None
        expected_Omega_m_h2 = omega_b + omega_cdm_expected
        assert abs(summary["Omega_m_h2"] - expected_Omega_m_h2) < 1e-9

    def test_omega_cdm_conversion(self, parse_outputs):
        """omega_cdm = Omega0_cdm * h^2."""
        h = 0.6732
        Omega0_cdm = 0.2651
        mock = _make_mock_classy(h=h, Omega0_cdm=Omega0_cdm)
        summary = parse_outputs.compute_summary(mock, {}, "background")
        expected = Omega0_cdm * h * h
        assert abs(summary["omega_cdm"] - expected) < 1e-9


# ---------------------------------------------------------------------------
# Test for run_class.py embedding summary in cosmology.json
# ---------------------------------------------------------------------------

class TestRunClassEmbedsSummaryInCosmologyJson:
    """Test that run_class.main() writes summary into cosmology.json."""

    def test_run_class_embeds_summary_in_cosmology_json(self, tmp_path, monkeypatch):
        """
        Monkeypatch classy-related imports so no CLASS binary is needed.
        Assert that cosmology.json contains the expected summary dict.
        """
        # --- Set up mock classy result ---
        h = 0.6732
        Omega0_cdm = 0.2651
        omega_b_val = 0.02238

        mock_classy_obj = _make_mock_classy(
            H0=67.32,
            h=h,
            omega_b=omega_b_val,
            Omega0_cdm=Omega0_cdm,
            Neff=3.046,
            z_eq=3402.0,
            tau_reio=0.0543,
            sigma8=0.811,
        )

        # Expected summary (background subcommand — tau_reio and sigma_8 are null)
        expected_omega_cdm = Omega0_cdm * h * h
        expected_summary = {
            "H0": 67.32,
            "omega_b": omega_b_val,
            "omega_cdm": expected_omega_cdm,
            "Omega_m_h2": omega_b_val + expected_omega_cdm,
            "N_eff": 3.046,
            "tau_reio": None,
            "sigma_8": None,
            "z_eq": 3402.0,
        }

        # --- Build fake config so run_class can find class_path ---
        config_dir = tmp_path / "config" / "hephaestus"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text(json.dumps({
            "class_path": "/opt/class_public-3.3.4",
            "class_version": "3.3.4",
            "python": sys.executable,
        }))

        # --- Build a minimal planck18-style config YAML (for custom preset) ---
        config_yaml = tmp_path / "test_config.yaml"
        config_yaml.write_text(
            "H0: 67.32\n"
            "omega_b: 0.02238\n"
            "omega_cdm: 0.1201\n"
        )

        # --- Fake classy driver module ---
        fake_driver = types.ModuleType("classy_driver_sb")
        fake_driver.ClassRuntimeError = Exception
        fake_driver.ClassSubprocessError = Exception

        # run() returns the mock_classy_obj directly (as if it were the live object)
        def _fake_run(**kwargs):
            return mock_classy_obj

        fake_driver.run = _fake_run

        # Fake ini_render module
        fake_ini_render = types.ModuleType("ini_render_sb")
        fake_ini_render.render = lambda **kwargs: "H0 = 67.32\nomega_b = 0.02238\n"

        # Fake parse_outputs — write_outputs just creates an empty file,
        # compute_summary uses the real implementation.
        real_parse_outputs_for_summary = _load_parse_outputs()
        fake_parse_outputs = types.ModuleType("parse_outputs_sb2")
        fake_parse_outputs.ParseOutputError = Exception

        def _fake_write_outputs(*, classy_result, run_dir, subcommand):
            # Create a minimal output file so run_class doesn't error
            out_file = Path(run_dir) / "background.dat"
            out_file.write_text("# z H\n")
            return {"background": out_file}

        fake_parse_outputs.write_outputs = _fake_write_outputs
        fake_parse_outputs.compute_summary = real_parse_outputs_for_summary.compute_summary

        # Fake schema_validate that always passes
        fake_schema_validate = types.ModuleType("schema_validate_sb")
        fake_schema_validate.SchemaValidationError = Exception
        fake_schema_validate.validate = lambda doc, path: None

        # --- Monkeypatch XDG_CONFIG_HOME so run_class reads our config ---
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
        monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))

        # --- Monkeypatch _load_module in run_class to return our fakes ---
        run_class_mod = _load_run_class()

        original_load_module = run_class_mod._load_module

        def _patched_load_module(name: str, path):
            if "classy_driver" in str(path):
                return fake_driver
            if "ini_render" in str(path):
                return fake_ini_render
            if "parse_outputs" in str(path):
                return fake_parse_outputs
            if "schema_validate" in str(path):
                return fake_schema_validate
            return original_load_module(name, path)

        monkeypatch.setattr(run_class_mod, "_load_module", _patched_load_module)

        # Also monkeypatch jsonschema to always pass (Draft7Validator)
        fake_jsonschema = types.ModuleType("jsonschema")

        class _FakeDraft7Validator:
            def __init__(self, schema):
                pass

            def iter_errors(self, doc):
                return iter([])

        fake_jsonschema.Draft7Validator = _FakeDraft7Validator
        monkeypatch.setitem(sys.modules, "jsonschema", fake_jsonschema)

        # --- Run main() ---
        output_dir = tmp_path / "state" / "cosmology_runs" / "test-run"
        output_dir.mkdir(parents=True)

        ret = run_class_mod.main([
            "background",
            "custom",
            "--config", str(config_yaml),
            "--output-dir", str(output_dir),
        ])

        assert ret == 0, f"run_class.main() returned non-zero: {ret}"

        # --- Check cosmology.json ---
        cosmology_json_path = output_dir / "cosmology.json"
        assert cosmology_json_path.exists(), "cosmology.json was not written"

        with open(cosmology_json_path) as f:
            doc = json.load(f)

        assert "summary" in doc, "cosmology.json missing 'summary' key"
        actual_summary = doc["summary"]

        for key, expected_val in expected_summary.items():
            assert key in actual_summary, f"summary missing key {key!r}"
            actual_val = actual_summary[key]
            if expected_val is None:
                assert actual_val is None, (
                    f"summary[{key!r}] expected None, got {actual_val!r}"
                )
            else:
                assert isinstance(actual_val, (int, float)), (
                    f"summary[{key!r}] expected number, got {type(actual_val)}"
                )
                assert abs(actual_val - expected_val) < 1e-9, (
                    f"summary[{key!r}]: expected {expected_val}, got {actual_val}"
                )
