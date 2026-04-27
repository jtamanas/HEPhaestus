"""test_scan_determinism.py — verify scan produces deterministic byte-identical CSV."""
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from scan import scan, expand_axis, parse_scan_arg


_DM = {"pdg": 9000001, "name": "S", "mass_gev": 100.0}


class TestScanDeterminism:
    def test_two_invocations_byte_identical(self, tmp_path):
        """Two scan runs with same inputs produce byte-identical scan_index.csv."""
        axes = [("lhs", 50.0, 200.0, 50.0)]
        dir1 = tmp_path / "run1"
        dir2 = tmp_path / "run2"

        csv1 = scan("singletDM", "relic", _DM, axes, dir1)
        csv2 = scan("singletDM", "relic", _DM, axes, dir2)

        content1 = csv1.read_text()
        content2 = csv2.read_text()

        # Remove run_dir column (paths differ between runs) for comparison
        def normalize(text: str) -> list[str]:
            lines = text.splitlines()
            result = []
            for line in lines:
                parts = line.split(",")
                # Remove run_dir (second-to-last field) and timing_s (last field)
                if len(parts) > 2:
                    parts = parts[:-2] + ["RUN_DIR", "TIMING"]
                result.append(",".join(parts))
            return result

        assert normalize(content1) == normalize(content2), (
            f"Scan outputs differ:\nRun1: {content1[:500]}\nRun2: {content2[:500]}"
        )

    def test_scan_produces_correct_points(self, tmp_path):
        """Scan with 2 axes produces correct number of points."""
        axes = [("m_s", 100.0, 200.0, 50.0), ("lhs", 0.1, 0.2, 0.05)]
        csv_path = scan("singletDM", "relic", _DM, axes, tmp_path / "scan")

        content = csv_path.read_text()
        lines = content.strip().splitlines()
        # Header + 3*3 = 9 points (100, 150, 200) x (0.1, 0.15, 0.2)
        assert len(lines) == 1 + 9, f"Expected 10 lines (1 header + 9 points), got {len(lines)}"

    def test_scan_axis_sorted_lexically(self, tmp_path):
        """Axes are sorted lexically in CSV header."""
        axes = [("z_param", 1.0, 2.0, 1.0), ("a_param", 10.0, 20.0, 10.0)]
        csv_path = scan("singletDM", "relic", _DM, axes, tmp_path / "scan")

        header = csv_path.read_text().splitlines()[0]
        cols = header.split(",")
        # a_param should come before z_param
        a_idx = cols.index("a_param")
        z_idx = cols.index("z_param")
        assert a_idx < z_idx, f"Expected a_param before z_param in header: {cols}"


class TestExpandAxis:
    def test_simple_range(self):
        vals = expand_axis("x", 0.0, 1.0, 0.5)
        assert vals == [0.0, 0.5, 1.0]

    def test_single_point(self):
        vals = expand_axis("x", 5.0, 5.0, 1.0)
        assert vals == [5.0]

    def test_step_zero_raises(self):
        with pytest.raises(ValueError):
            expand_axis("x", 0.0, 1.0, 0.0)


class TestParseScanArg:
    def test_basic_parse(self):
        name, start, stop, step = parse_scan_arg("m_s=100:300:step=50")
        assert name == "m_s"
        assert start == 100.0
        assert stop == 300.0
        assert step == 50.0

    def test_float_values(self):
        name, start, stop, step = parse_scan_arg("lhs=0.01:0.1:step=0.01")
        assert name == "lhs"
        assert abs(start - 0.01) < 1e-12
        assert abs(step - 0.01) < 1e-12

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_scan_arg("bad format")
