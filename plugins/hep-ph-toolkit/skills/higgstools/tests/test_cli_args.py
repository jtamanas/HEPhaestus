"""
test_cli_args.py — test run_higgstools.py argparse surface.

Tests:
- required --model flag (or --slha)
- mutex --mode options
- env-var override for backend
- --delta-chi2 float
- --dMh scalar and JSON object
- --scan-dir semantics
- aggregate subcommand
"""
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@pytest.fixture
def run_mod():
    """Import run_higgstools module."""
    import importlib.util
    import sys as _sys
    spec = importlib.util.spec_from_file_location(
        "run_higgstools",
        SKILL_DIR / "scripts" / "run_higgstools.py",
    )
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["run_higgstools"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestRunArgparse:
    """Test run subcommand argument parsing."""

    def test_run_subcommand_present(self, run_mod):
        """run subcommand is recognized."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "/tmp/test.slha"])
        assert args.subcommand == "run"
        assert args.slha == "/tmp/test.slha"

    def test_mode_choices(self, run_mod):
        """--mode accepts both, hb, hs."""
        parser = run_mod.build_parser()
        for mode in ("both", "hb", "hs"):
            args = parser.parse_args(["run", "--slha", "x.slha", "--mode", mode])
            assert args.mode == mode

    def test_mode_invalid(self, run_mod):
        """--mode with invalid value causes parse error."""
        parser = run_mod.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--slha", "x.slha", "--mode", "invalid"])

    def test_backend_default_is_not_unified(self, run_mod):
        """--backend default is None or 'legacy', never 'unified'."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha"])
        assert args.backend != "unified", \
            "backend default must not be 'unified'; unified is opt-in only"

    def test_backend_unified_explicit(self, run_mod):
        """--backend=unified can be explicitly set."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha", "--backend", "unified"])
        assert args.backend == "unified"

    def test_backend_legacy_explicit(self, run_mod):
        """--backend=legacy can be explicitly set."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha", "--backend", "legacy"])
        assert args.backend == "legacy"

    def test_delta_chi2_float(self, run_mod):
        """--delta-chi2 accepts a float."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha", "--delta-chi2", "9.21"])
        assert abs(args.delta_chi2 - 9.21) < 1e-9

    def test_delta_chi2_default(self, run_mod):
        """--delta-chi2 default is 6.18."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha"])
        assert abs(args.delta_chi2 - 6.18) < 1e-9

    def test_dMh_scalar(self, run_mod):
        """--dMh as scalar float parsed correctly."""
        dMh = run_mod._parse_dMh("3.5")
        assert dMh == {"h0": 3.5, "heavy": 3.5}

    def test_dMh_json(self, run_mod):
        """--dMh as JSON object parsed correctly."""
        dMh = run_mod._parse_dMh('{"h0": 2.0, "H0": 5.0}')
        assert dMh == {"h0": 2.0, "H0": 5.0}

    def test_dMh_invalid_raises(self, run_mod):
        """--dMh with invalid value raises ValueError."""
        with pytest.raises(ValueError):
            run_mod._parse_dMh("notanumber")

    def test_scan_dir_argument(self, run_mod):
        """--scan-dir argument parsed correctly."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--scan-dir", "/tmp/scan"])
        assert args.scan_dir == "/tmp/scan"

    def test_model_argument(self, run_mod):
        """--model argument parsed correctly."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--model", "2HDM"])
        assert args.model == "2HDM"
        assert args.slha is None

    def test_workers_argument(self, run_mod):
        """--workers argument parsed correctly."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha", "--workers", "4"])
        assert args.workers == 4

    def test_channels_default_all(self, run_mod):
        """--channels default is 'all'."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["run", "--slha", "x.slha"])
        assert args.channels == "all"


class TestAggregateArgparse:
    """Test aggregate subcommand argument parsing."""

    def test_aggregate_subcommand_recognized(self, run_mod):
        """aggregate subcommand recognized."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["aggregate", "/tmp/results"])
        assert args.subcommand == "aggregate"
        assert args.dir == "/tmp/results"

    def test_aggregate_default_output(self, run_mod):
        """aggregate --output defaults to higgstools_index.csv."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["aggregate", "/tmp/results"])
        assert args.output == "higgstools_index.csv"

    def test_aggregate_custom_output(self, run_mod):
        """aggregate --output accepts custom path."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["aggregate", "/tmp/results", "--output", "custom.csv"])
        assert args.output == "custom.csv"

    def test_aggregate_workers(self, run_mod):
        """aggregate --workers accepts int."""
        parser = run_mod.build_parser()
        args = parser.parse_args(["aggregate", "/tmp/results", "--workers", "4"])
        assert args.workers == 4


class TestDMhParsing:
    """Test _parse_dMh edge cases."""

    def test_none_returns_none(self, run_mod):
        assert run_mod._parse_dMh(None) is None

    def test_integer_string_parsed(self, run_mod):
        dMh = run_mod._parse_dMh("2")
        assert dMh == {"h0": 2.0, "heavy": 2.0}

    def test_empty_json_object(self, run_mod):
        dMh = run_mod._parse_dMh("{}")
        assert dMh == {}

    def test_invalid_json_raises(self, run_mod):
        with pytest.raises(ValueError):
            run_mod._parse_dMh("{bad json}")
