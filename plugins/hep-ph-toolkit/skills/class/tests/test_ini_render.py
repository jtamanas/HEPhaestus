"""
test_ini_render.py — unit tests for scripts/ini_render.py.

No network, no classy required.
"""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
TEMPLATES_DIR = SKILL_DIR / "templates"


def _load_ini_render():
    spec = importlib.util.spec_from_file_location(
        "ini_render", SCRIPTS_DIR / "ini_render.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def ini_render():
    return _load_ini_render()


class TestPresets:
    """Test that preset parameters are correctly populated."""

    def test_planck18_h0(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "H0 = 67.32" in text

    def test_planck18_act_h0(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18_act",
            config_path=None,
            bsm_extension=None,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "H0 = 67.9" in text

    def test_planck18_omega_b(self, ini_render):
        text = ini_render.render(
            subcommand="background",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "omega_b = 0.02238" in text

    def test_custom_preset_empty_base(self, ini_render):
        """custom preset starts with no cosmological parameters."""
        # This should fail if no config_path is given because output= will be set
        # but cosmological params will be absent
        text = ini_render.render(
            subcommand="pk",
            preset="custom",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        # Should not have planck18 H0
        assert "H0 = 67.32" not in text
        # Should have output key
        assert "output = mPk" in text


class TestSubcommandOutputKeys:
    """Test that each subcommand sets the correct CLASS output keys."""

    def test_cmb_output_key(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "output = tCl,pCl,lCl" in text
        assert "lensing = yes" in text

    def test_cmb_lmax(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=1500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "l_max_scalars = 1500" in text

    def test_pk_output_key(self, ini_render):
        text = ini_render.render(
            subcommand="pk",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0,1",
            k_min=1e-4,
            k_max=2.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "output = mPk" in text
        assert "z_pk = 0,1" in text
        assert "P_k_max_h/Mpc = 2.0" in text

    def test_transfer_output_key(self, ini_render):
        text = ini_render.render(
            subcommand="transfer",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "output = mTk" in text

    def test_background_output_key(self, ini_render):
        text = ini_render.render(
            subcommand="background",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "output = mPk" in text
        assert "background = yes" not in text
        assert "thermodynamics = yes" not in text


class TestBsmExtension:
    """Test that BSM extension params are injected into the ini."""

    def test_dcdm_params_injected(self, ini_render):
        bsm = {
            "kind": "dcdm",
            "params": {
                "Omega_ini_dcdm": "0.25",
                "Gamma_dcdm": "1.0e-29",
            },
        }
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=bsm,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "Omega_ini_dcdm = 0.25" in text
        assert "Gamma_dcdm = 1.0e-29" in text

    def test_unknown_bsm_kind_raises(self, ini_render):
        bsm = {"kind": "bogus_extension", "params": {}}
        with pytest.raises(ini_render.IniRenderError, match="Unknown BSM kind"):
            ini_render.render(
                subcommand="cmb",
                preset="planck18",
                config_path=None,
                bsm_extension=bsm,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )

    def test_null_bsm_no_injection(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        # No BSM keys should appear
        for kind in ini_render.BSM_KINDS:
            assert kind not in text.lower() or kind == "cmb"  # 'cmb' is a subcommand

    def test_all_supported_bsm_kinds(self, ini_render):
        """All BSM kinds in BSM_KINDS are accepted without error."""
        for kind in ini_render.BSM_KINDS:
            bsm = {"kind": kind, "params": {"test_param": "1.0"}}
            text = ini_render.render(
                subcommand="cmb",
                preset="planck18",
                config_path=None,
                bsm_extension=bsm,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )
            assert "test_param = 1.0" in text


class TestCustomConfig:
    """Test YAML config file loading and merging."""

    def test_config_override_h0(self, ini_render, tmp_path):
        cfg = tmp_path / "custom.yaml"
        cfg.write_text("H0: 70.0\nomega_b: 0.022\n")
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=cfg,
            bsm_extension=None,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert "H0 = 70.0" in text

    def test_missing_config_raises(self, ini_render, tmp_path):
        missing = tmp_path / "nonexistent.yaml"
        with pytest.raises(ini_render.IniRenderError, match="Failed to load config"):
            ini_render.render(
                subcommand="cmb",
                preset="planck18",
                config_path=missing,
                bsm_extension=None,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )

    def test_invalid_config_type_raises(self, ini_render, tmp_path):
        cfg = tmp_path / "bad.yaml"
        cfg.write_text("- a list, not a mapping\n")
        with pytest.raises(ini_render.IniRenderError, match="must be a YAML mapping"):
            ini_render.render(
                subcommand="cmb",
                preset="planck18",
                config_path=cfg,
                bsm_extension=None,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )


class TestIniFormat:
    """Test that the generated ini text is correctly formatted."""

    def test_header_comment(self, ini_render):
        text = ini_render.render(
            subcommand="cmb",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=100,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        assert text.startswith("# CLASS ini file")

    def test_key_equals_value_format(self, ini_render):
        text = ini_render.render(
            subcommand="background",
            preset="planck18",
            config_path=None,
            bsm_extension=None,
            lmax=2500,
            z_pk="0",
            k_min=1e-4,
            k_max=1.0,
            templates_dir=TEMPLATES_DIR,
        )
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assert " = " in line, f"Line not in 'key = value' format: {line!r}"

    def test_unknown_subcommand_raises(self, ini_render):
        with pytest.raises(ini_render.IniRenderError, match="Unknown subcommand"):
            ini_render.render(
                subcommand="bogus",
                preset="planck18",
                config_path=None,
                bsm_extension=None,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )

    def test_unknown_preset_raises(self, ini_render):
        with pytest.raises(ini_render.IniRenderError, match="Unknown preset"):
            ini_render.render(
                subcommand="cmb",
                preset="bogus_preset",
                config_path=None,
                bsm_extension=None,
                lmax=100,
                z_pk="0",
                k_min=1e-4,
                k_max=1.0,
                templates_dir=TEMPLATES_DIR,
            )
