"""
test_cli_args.py — test run_class.py argparse surface + blocker code coverage.

Tests:
- subcommand choices (background|cmb|pk|transfer)
- preset choices (planck18|planck18_act|custom)
- all optional flags
- invalid choices cause SystemExit
- custom preset + missing --config causes blocker
- blocker codes in SKILL.md match those emitted by scripts

No network, no classy required.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _load_run_class():
    spec = importlib.util.spec_from_file_location(
        "run_class", SCRIPTS_DIR / "run_class.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Prevent sys.exit on import
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def run_class():
    return _load_run_class()


class TestSubcommandChoices:
    """Test that all four subcommands are accepted."""

    @pytest.mark.parametrize("sub", ["background", "cmb", "pk", "transfer"])
    def test_valid_subcommand_accepted(self, run_class, sub):
        parser = run_class.build_parser()
        args = parser.parse_args([sub, "planck18"])
        assert args.subcommand == sub

    def test_invalid_subcommand_rejected(self, run_class):
        parser = run_class.build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["montepython", "planck18"])
        assert exc_info.value.code == 2

    def test_no_subcommand_exits(self, run_class):
        parser = run_class.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestPresetChoices:
    """Test that all three presets are accepted."""

    @pytest.mark.parametrize("preset", ["planck18", "planck18_act", "custom"])
    def test_valid_preset_accepted(self, run_class, preset):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", preset])
        assert args.preset == preset

    def test_invalid_preset_rejected(self, run_class):
        parser = run_class.build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["cmb", "planck15"])
        assert exc_info.value.code == 2


class TestOptionalFlags:
    """Test optional flag parsing."""

    def test_lmax_default(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18"])
        assert args.lmax == 2500

    def test_lmax_custom(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18", "--lmax", "1000"])
        assert args.lmax == 1000

    def test_z_pk_default(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["pk", "planck18"])
        assert args.z_pk == "0"

    def test_z_pk_custom(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["pk", "planck18", "--z-pk", "0,1,2"])
        assert args.z_pk == "0,1,2"

    def test_k_min_default(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["pk", "planck18"])
        assert abs(args.k_min - 1e-4) < 1e-10

    def test_k_max_default(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["pk", "planck18"])
        assert abs(args.k_max - 1.0) < 1e-10

    def test_output_dir_default_is_none(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18"])
        assert args.output_dir is None

    def test_output_dir_custom(self, run_class, tmp_path):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18", "--output-dir", str(tmp_path)])
        assert args.output_dir == tmp_path

    def test_config_default_is_none(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18"])
        assert args.config is None

    def test_bsm_default_is_none(self, run_class):
        parser = run_class.build_parser()
        args = parser.parse_args(["cmb", "planck18"])
        assert args.bsm is None


class TestCustomPresetValidation:
    """Test that custom preset requires --config (checked at runtime in main)."""

    def test_custom_without_config_causes_fatal_blocker(self, run_class, tmp_path, capsys):
        """main() with custom+no config must emit CLASS_CONFIG_INVALID and return 2."""
        # Use a tmp XDG_CONFIG_HOME to avoid picking up real config
        import os
        env_backup = os.environ.copy()
        os.environ["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
        try:
            result = run_class.main(["cmb", "custom"])
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

        captured = capsys.readouterr()
        assert result == 2
        blocker = json.loads(captured.err.strip())
        assert blocker["code"] == "CLASS_CONFIG_INVALID"
        assert blocker["mode"] == "fatal"

    def test_class_not_configured_causes_fatal_blocker(self, run_class, tmp_path, capsys):
        """main() with no class_path in config must emit CLASS_NOT_CONFIGURED."""
        import os
        env_backup = os.environ.copy()
        os.environ["XDG_CONFIG_HOME"] = str(tmp_path / "cfg_empty")
        (tmp_path / "cfg_empty" / "hephaestus").mkdir(parents=True)
        (tmp_path / "cfg_empty" / "hephaestus" / "config.json").write_text("{}")
        try:
            result = run_class.main(["cmb", "planck18"])
        finally:
            os.environ.clear()
            os.environ.update(env_backup)

        captured = capsys.readouterr()
        assert result == 2
        blocker = json.loads(captured.err.strip())
        assert blocker["code"] == "CLASS_NOT_CONFIGURED"
        assert blocker["mode"] == "fatal"


class TestBlockerCodeCoverage:
    """Verify all blocker codes in SKILL.md appear in scripts/."""

    def _get_skill_md_blocker_codes(self):
        """Extract blocker codes from the Recoverable vs fatal table in SKILL.md."""
        text = SKILL_MD.read_text()
        import re
        # Find lines like: | `CLASS_NOT_CONFIGURED`   | fatal | ...
        codes = re.findall(r"\|\s*`([A-Z_]+)`\s*\|", text)
        return set(codes)

    def _get_script_blocker_codes(self):
        """Find blocker code strings in all scripts/."""
        codes = set()
        import re
        for py_file in SCRIPTS_DIR.glob("*.py"):
            text = py_file.read_text()
            # Match string literals that look like blocker codes (ALL_CAPS_WITH_UNDERSCORES)
            found = re.findall(r'"([A-Z][A-Z_]+[A-Z])"', text)
            codes.update(found)
        return codes

    def test_skill_md_blocker_codes_exist_in_scripts(self):
        """Every blocker code in SKILL.md must appear in at least one script."""
        md_codes = self._get_skill_md_blocker_codes()
        script_codes = self._get_script_blocker_codes()

        missing = []
        for code in md_codes:
            # Only check codes that look like blocker codes (CLASS_* or CLASSY_*)
            if code.startswith(("CLASS_", "CLASSY_")):
                if code not in script_codes:
                    missing.append(code)

        assert not missing, (
            f"Blocker codes in SKILL.md not found in any script:\n"
            + "\n".join(f"  - {c}" for c in sorted(missing))
        )


class TestHelpOutput:
    """Test that --help exits 0 (acceptance gate §4.4 #3)."""

    def test_help_exits_zero(self, run_class):
        parser = run_class.build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0
