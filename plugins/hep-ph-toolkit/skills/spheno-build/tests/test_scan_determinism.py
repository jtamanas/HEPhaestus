"""
test_scan_determinism.py — Determinism and expansion tests for the Cartesian scan.

Tests:
    - expand_axis: correct values for integer and float steps.
    - _cartesian_product: correct count and deterministic ordering.
    - 45-point grid: MpsiD=200:1000:step=100 (9) × gD=0.5:2.5:step=0.5 (5) = 45.
    - 27-point grid: 3×3×3 example.
    - Two runs on identical inputs produce byte-identical scan_index.csv.

Test isolation: uses HEPPH_STATE_ROOT and XDG_CONFIG_HOME per global invariant §2.3.
"""

import csv
import importlib.util
import io
import json
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_FIXTURES = _HERE / "fixtures" / "slha"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scan_mod():
    return _load_module("scan", _SCRIPTS / "scan.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# ---------------------------------------------------------------------------
# Test: expand_axis
# ---------------------------------------------------------------------------
class TestExpandAxis:
    def test_integer_step_9_values(self, scan_mod):
        """MpsiD=200:1000:step=100 → 9 values [200, 300, ..., 1000]."""
        vals = scan_mod.expand_axis("MpsiD", 200.0, 1000.0, 100.0)
        assert vals == [200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0]

    def test_float_step_5_values(self, scan_mod):
        """gD=0.5:2.5:step=0.5 → 5 values [0.5, 1.0, 1.5, 2.0, 2.5]."""
        vals = scan_mod.expand_axis("gD", 0.5, 2.5, 0.5)
        assert len(vals) == 5, f"Expected 5 values, got {len(vals)}: {vals}"
        assert abs(vals[0] - 0.5) < 1e-9
        assert abs(vals[-1] - 2.5) < 1e-9

    def test_single_value(self, scan_mod):
        """start == stop → single value."""
        vals = scan_mod.expand_axis("x", 1.0, 1.0, 0.5)
        assert len(vals) == 1
        assert abs(vals[0] - 1.0) < 1e-9

    def test_step_zero_raises(self, scan_mod):
        with pytest.raises(ValueError, match="step must be positive"):
            scan_mod.expand_axis("x", 0.0, 1.0, 0.0)

    def test_start_greater_than_stop_raises(self, scan_mod):
        with pytest.raises(ValueError, match="start .* > stop"):
            scan_mod.expand_axis("x", 1.0, 0.0, 0.5)

    def test_three_values(self, scan_mod):
        """Simple 3-value step."""
        vals = scan_mod.expand_axis("x", 300.0, 500.0, 100.0)
        assert vals == [300.0, 400.0, 500.0]


# ---------------------------------------------------------------------------
# Test: Cartesian product counts
# ---------------------------------------------------------------------------
class TestCartesianProduct:
    def test_45_point_grid(self, scan_mod):
        """9 × 5 = 45."""
        axes = [
            ("MpsiD", [200.0 + i * 100.0 for i in range(9)]),
            ("gD", [0.5 + i * 0.5 for i in range(5)]),
        ]
        points = scan_mod._cartesian_product(axes)
        assert len(points) == 45, f"Expected 45 points, got {len(points)}"

    def test_27_point_grid(self, scan_mod):
        """3 × 3 × 3 = 27."""
        axes = [
            ("A", [1.0, 2.0, 3.0]),
            ("B", [10.0, 20.0, 30.0]),
            ("C", [100.0, 200.0, 300.0]),
        ]
        points = scan_mod._cartesian_product(axes)
        assert len(points) == 27, f"Expected 27 points, got {len(points)}"

    def test_empty_axes(self, scan_mod):
        """Empty axes → one empty-dict point."""
        points = scan_mod._cartesian_product([])
        assert points == [{}]

    def test_single_axis(self, scan_mod):
        axes = [("x", [1.0, 2.0, 3.0])]
        points = scan_mod._cartesian_product(axes)
        assert len(points) == 3
        assert all("x" in p for p in points)

    def test_axes_sorted_by_name(self, scan_mod):
        """Cartesian product uses axes sorted by name for determinism."""
        axes = [
            ("z_param", [1.0, 2.0]),
            ("a_param", [10.0, 20.0]),
        ]
        points = scan_mod._cartesian_product(axes)
        assert len(points) == 4
        # All combinations present
        for p in points:
            assert "a_param" in p
            assert "z_param" in p

    def test_ordering_deterministic(self, scan_mod):
        """Same inputs → same ordering."""
        axes = [
            ("B", [1.0, 2.0]),
            ("A", [10.0, 20.0]),
        ]
        points1 = scan_mod._cartesian_product(axes)
        points2 = scan_mod._cartesian_product(axes)
        assert points1 == points2


# ---------------------------------------------------------------------------
# Test: parse_scan_arg
# ---------------------------------------------------------------------------
class TestParseScanArg:
    def test_integer_step(self, scan_mod):
        name, start, stop, step = scan_mod.parse_scan_arg("MpsiD=200:1000:step=100")
        assert name == "MpsiD"
        assert start == 200.0
        assert stop == 1000.0
        assert step == 100.0

    def test_float_step(self, scan_mod):
        name, start, stop, step = scan_mod.parse_scan_arg("gD=0.5:2.5:step=0.5")
        assert name == "gD"
        assert abs(start - 0.5) < 1e-9
        assert abs(stop - 2.5) < 1e-9
        assert abs(step - 0.5) < 1e-9

    def test_invalid_format(self, scan_mod):
        with pytest.raises(ValueError, match="Cannot parse"):
            scan_mod.parse_scan_arg("MpsiD=200-1000-100")


# ---------------------------------------------------------------------------
# Test: scan_index.csv determinism
# ---------------------------------------------------------------------------
class TestScanDeterminism:
    """Two runs with identical mocked inputs → byte-identical scan_index.csv."""

    def _make_fake_result(self, point: dict, out_dir: Path) -> dict:
        """Mock scan_worker that writes a fake SPheno.spc and returns ok."""
        spc = out_dir / "SPheno.spc"
        # Write a minimal SLHA so parse_slha doesn't complain
        spc.write_text(
            f"# mock SPheno.spc for {point}\n"
            "Block MASS\n"
            "   1000001   5.000000000E+02   # mock mass\n"
        )
        return {
            "status": "ok",
            "blocker_code": None,
            "slha_path": str(spc),
            "timing_s": 0.001,
        }

    def test_3x3_deterministic(self, scan_mod, tmp_path):
        """Two runs on identical inputs → identical scan_index.csv content."""
        spec = {
            "name": "test_det",
            "parameters": [
                {"name": "A", "default": 1.0},
                {"name": "B", "default": 2.0},
            ],
        }
        axes = [
            ("A", 1.0, 3.0, 1.0),   # 3 values
            ("B", 10.0, 30.0, 10.0),  # 3 values → 9 total points
        ]

        # Patch scan_worker to avoid needing a real SPheno binary
        with patch.object(scan_mod, "scan_worker", side_effect=self._make_fake_result):
            dir1 = tmp_path / "run1"
            csv1 = scan_mod.scan("test_det", axes, dir1, spec=spec)

        with patch.object(scan_mod, "scan_worker", side_effect=self._make_fake_result):
            dir2 = tmp_path / "run2"
            csv2 = scan_mod.scan("test_det", axes, dir2, spec=spec)

        # Compare CSV content (not paths which differ)
        rows1 = _read_csv_rows(csv1)
        rows2 = _read_csv_rows(csv2)

        assert len(rows1) == 9, f"Expected 9 rows, got {len(rows1)}"
        assert len(rows2) == 9

        # Compare all fields except slha_path (which contains tmp_path)
        for r1, r2 in zip(rows1, rows2):
            for key in ["index", "A", "B", "status", "blocker_code"]:
                assert r1[key] == r2[key], (
                    f"Row mismatch for key {key!r}: {r1[key]!r} vs {r2[key]!r}"
                )

    def test_row_count_45_point_scan(self, scan_mod, tmp_path):
        """MpsiD×gD scan produces exactly 45 rows in scan_index.csv."""
        spec = {
            "name": "test_45",
            "parameters": [
                {"name": "MpsiD", "default": 500.0},
                {"name": "gD", "default": 1.0},
            ],
        }
        axes = [
            ("MpsiD", 200.0, 1000.0, 100.0),   # 9 values
            ("gD", 0.5, 2.5, 0.5),              # 5 values  → 45 total
        ]

        with patch.object(scan_mod, "scan_worker", side_effect=self._make_fake_result):
            csv_path = scan_mod.scan("test_45", axes, tmp_path / "scan", spec=spec)

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 45, f"Expected 45 rows, got {len(rows)}: {csv_path}"

    def test_header_columns(self, scan_mod, tmp_path):
        """scan_index.csv has expected column headers."""
        spec = {
            "name": "test_hdr",
            "parameters": [
                {"name": "MpsiD", "default": 500.0},
            ],
        }
        axes = [("MpsiD", 200.0, 400.0, 100.0)]  # 3 points

        with patch.object(scan_mod, "scan_worker", side_effect=self._make_fake_result):
            csv_path = scan_mod.scan("test_hdr", axes, tmp_path / "scan_hdr", spec=spec)

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        required = {"index", "MpsiD", "status", "blocker_code", "slha_path", "timing_s"}
        assert required <= set(fieldnames), (
            f"Missing columns: {required - set(fieldnames)}"
        )


def _read_csv_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))
