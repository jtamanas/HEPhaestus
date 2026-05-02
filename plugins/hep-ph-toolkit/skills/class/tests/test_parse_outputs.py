"""
test_parse_outputs.py — unit tests for scripts/parse_outputs.py.

No network, no classy required. Tests use synthetic classy result dicts.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"


def _load_parse_outputs():
    spec = importlib.util.spec_from_file_location(
        "parse_outputs", SCRIPTS_DIR / "parse_outputs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def parse_outputs():
    return _load_parse_outputs()


@pytest.fixture
def tmp_run_dir(tmp_path):
    run_dir = tmp_path / "run_20260502T0000Z"
    run_dir.mkdir()
    return run_dir


class TestBackgroundOutput:
    """Test background subcommand output writing."""

    def test_writes_background_dat(self, parse_outputs, tmp_run_dir):
        result = {
            "subcommand": "background",
            "background": {
                "z": ["0.0000000000e+00", "1.0000000000e+00"],
                "H [1/Mpc]": ["6.7320000000e+01", "1.4000000000e+02"],
            },
            "age_gyr": "1.3797000000e+01",
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="background",
        )
        assert "background" in output_files
        dat = output_files["background"]
        assert dat.exists()
        text = dat.read_text()
        assert text.startswith("# z")

    def test_background_header_format(self, parse_outputs, tmp_run_dir):
        result = {
            "subcommand": "background",
            "background": {
                "z": ["0.0000000000e+00"],
                "conf. time [Mpc]": ["4.4100000000e+04"],
            },
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="background",
        )
        text = output_files["background"].read_text()
        first_line = text.splitlines()[0]
        assert first_line.startswith("# ")
        # Spaces replaced with underscores in column names
        assert "conf._time_Mpc" in first_line

    def test_background_missing_key_raises(self, parse_outputs, tmp_run_dir):
        with pytest.raises(parse_outputs.ParseOutputError, match="missing 'background'"):
            parse_outputs.write_outputs(
                classy_result={"subcommand": "background"},
                run_dir=tmp_run_dir,
                subcommand="background",
            )


class TestCmbOutput:
    """Test cmb subcommand output writing."""

    def _make_cmb_result(self):
        ell = [str(float(l)) for l in range(2, 6)]
        tt = ["1.0000000000e-09"] * 4
        return {
            "subcommand": "cmb",
            "cls": {
                "ell": ell,
                "tt": tt,
                "ee": tt,
            },
            "lmax": 5,
        }

    def test_writes_cls_dat(self, parse_outputs, tmp_run_dir):
        result = self._make_cmb_result()
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="cmb",
        )
        assert "cmb" in output_files
        assert output_files["cmb"].exists()
        text = output_files["cmb"].read_text()
        assert "# ell" in text

    def test_cmb_header_has_spectra_keys(self, parse_outputs, tmp_run_dir):
        result = self._make_cmb_result()
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="cmb",
        )
        header = output_files["cmb"].read_text().splitlines()[0]
        assert "tt" in header
        assert "ee" in header

    def test_cmb_ell_formatted_as_integer(self, parse_outputs, tmp_run_dir):
        result = self._make_cmb_result()
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="cmb",
        )
        lines = output_files["cmb"].read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
        # First data column should be integer-like
        first_ell = data_lines[0].split()[0]
        assert first_ell == "2", f"Expected '2', got {first_ell!r}"

    def test_cmb_missing_cls_raises(self, parse_outputs, tmp_run_dir):
        with pytest.raises(parse_outputs.ParseOutputError, match="missing 'cls'"):
            parse_outputs.write_outputs(
                classy_result={"subcommand": "cmb"},
                run_dir=tmp_run_dir,
                subcommand="cmb",
            )


class TestPkOutput:
    """Test pk subcommand output writing."""

    def _make_pk_result(self):
        k = ["1.0000000000e-04", "2.0000000000e-04"]
        pk = ["1.0000000000e+03", "9.0000000000e+02"]
        return {
            "subcommand": "pk",
            "k_h": k,
            "pk_by_z": {"0": pk},
            "z_list": ["0"],
        }

    def test_writes_pk_dat(self, parse_outputs, tmp_run_dir):
        result = self._make_pk_result()
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="pk",
        )
        assert "pk" in output_files
        assert output_files["pk"].exists()

    def test_pk_header_format(self, parse_outputs, tmp_run_dir):
        result = self._make_pk_result()
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="pk",
        )
        header = output_files["pk"].read_text().splitlines()[0]
        assert header.startswith("# k_h/Mpc")
        assert "Pk_z0" in header

    def test_pk_multi_z(self, parse_outputs, tmp_run_dir):
        k = ["1.0000000000e-04"]
        result = {
            "subcommand": "pk",
            "k_h": k,
            "pk_by_z": {"0": ["1.0e+03"], "1": ["5.0e+02"]},
            "z_list": ["0", "1"],
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="pk",
        )
        header = output_files["pk"].read_text().splitlines()[0]
        assert "Pk_z0" in header
        assert "Pk_z1" in header

    def test_pk_missing_keys_raises(self, parse_outputs, tmp_run_dir):
        with pytest.raises(parse_outputs.ParseOutputError):
            parse_outputs.write_outputs(
                classy_result={"subcommand": "pk"},
                run_dir=tmp_run_dir,
                subcommand="pk",
            )


class TestTransferOutput:
    """Test transfer subcommand output writing."""

    def test_writes_tk_dat(self, parse_outputs, tmp_run_dir):
        result = {
            "subcommand": "transfer",
            "k_h": ["1.0000000000e-04"],
            "tk_by_z": {"0": ["1.0000000000e+00"]},
            "z_list": ["0"],
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="transfer",
        )
        assert "transfer" in output_files
        assert output_files["transfer"].name == "tk.dat"

    def test_transfer_header_format(self, parse_outputs, tmp_run_dir):
        result = {
            "subcommand": "transfer",
            "k_h": ["1.0000000000e-04"],
            "tk_by_z": {"0": ["1.0000000000e+00"]},
            "z_list": ["0"],
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="transfer",
        )
        header = output_files["transfer"].read_text().splitlines()[0]
        assert header.startswith("# k_h/Mpc")
        assert "Tk_z0" in header


class TestUnknownSubcommand:
    """Test that unknown subcommand raises properly."""

    def test_unknown_subcommand_raises(self, parse_outputs, tmp_run_dir):
        with pytest.raises(parse_outputs.ParseOutputError, match="Unknown subcommand"):
            parse_outputs.write_outputs(
                classy_result={},
                run_dir=tmp_run_dir,
                subcommand="bogus",
            )


class TestDeterministicFormatting:
    """Test that float formatting is deterministic."""

    def test_float_formatting_consistent(self, parse_outputs, tmp_run_dir):
        """Values stored as f'{x:.10e}' strings must round-trip consistently."""
        val = 1.234567890123456789e-9
        formatted = f"{val:.10e}"
        # Must always be 10 decimal places in scientific notation
        assert "e" in formatted
        mantissa, exp = formatted.split("e")
        assert len(mantissa.split(".")[1]) == 10

    def test_background_data_matches_input(self, parse_outputs, tmp_run_dir):
        """Values written to TSV match the input strings exactly."""
        input_val = "1.2345678901e-09"
        result = {
            "subcommand": "background",
            "background": {
                "z": [input_val],
            },
        }
        output_files = parse_outputs.write_outputs(
            classy_result=result,
            run_dir=tmp_run_dir,
            subcommand="background",
        )
        lines = output_files["background"].read_text().splitlines()
        data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
        assert data_lines[0] == input_val
