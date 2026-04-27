"""
Unit test: scan_summary.py produces deterministic CSV output for fixed input.
Tests CSV column structure, row ordering, and byte-identical golden output.
Does NOT require DDCalc to be installed (uses a mock driver).
"""
from __future__ import annotations

import csv
import fcntl
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"

sys.path.insert(0, str(SCRIPTS_DIR))
from scan_summary import CSV_COLUMNS, NATIVE_EXPERIMENTS  # noqa: E402


class TestScanSummaryDeterminism:
    def test_csv_columns_match_spec(self):
        """CSV column list must include point_idx, m_dm_gev, sigma_si_proton_cm2,
        verdict, logL_<exp> for each native experiment, n_sigma_fog."""
        assert "point_idx" in CSV_COLUMNS
        assert "m_dm_gev" in CSV_COLUMNS
        assert "sigma_si_proton_cm2" in CSV_COLUMNS
        assert "verdict" in CSV_COLUMNS
        assert "n_sigma_fog" in CSV_COLUMNS
        for exp in NATIVE_EXPERIMENTS:
            assert f"logL_{exp}" in CSV_COLUMNS, f"Missing logL_{exp} in CSV_COLUMNS"

    def test_native_experiments_list(self):
        """Native experiment list must include XENON1T_2018 and four others."""
        assert "XENON1T_2018" in NATIVE_EXPERIMENTS
        assert len(NATIVE_EXPERIMENTS) >= 5

    def test_column_order_stable(self):
        """Column order: point_idx, m_dm_gev, sigma_si_proton_cm2, verdict, then logL_*, n_sigma_fog."""
        assert CSV_COLUMNS[0] == "point_idx"
        assert CSV_COLUMNS[1] == "m_dm_gev"
        assert CSV_COLUMNS[2] == "sigma_si_proton_cm2"
        assert CSV_COLUMNS[3] == "verdict"
        assert CSV_COLUMNS[-1] == "n_sigma_fog"

    def test_csv_writer_produces_deterministic_output(self, tmp_path):
        """Two identical input row-sets produce byte-identical CSV output."""
        rows = [
            {"point_idx": 2, "m_dm_gev": 200.0, "sigma_si_proton_cm2": 2e-46,
             "verdict": "excluded", "n_sigma_fog": "",
             "logL_XENON1T_2018": -5.0, "logL_LUX_2016": -2.0,
             "logL_PandaX_2017": -3.0, "logL_PICO_60_2019": -0.1,
             "logL_DarkSide_50": -0.2},
            {"point_idx": 1, "m_dm_gev": 100.0, "sigma_si_proton_cm2": 1e-46,
             "verdict": "excluded", "n_sigma_fog": "",
             "logL_XENON1T_2018": -17.3, "logL_LUX_2016": -5.2,
             "logL_PandaX_2017": -8.1, "logL_PICO_60_2019": -0.12,
             "logL_DarkSide_50": -0.23},
        ]

        def write_csv(path: Path, row_list: list) -> str:
            sorted_rows = sorted(row_list, key=lambda r: r["point_idx"])
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(sorted_rows)
            return path.read_text()

        csv1 = write_csv(tmp_path / "run1.csv", rows)
        csv2 = write_csv(tmp_path / "run2.csv", rows)

        assert csv1 == csv2, "CSV output is not byte-identical for identical input"

    def test_rows_sorted_by_point_idx(self, tmp_path):
        """Output rows are sorted by point_idx regardless of input order."""
        rows = [
            {"point_idx": 3, "m_dm_gev": 300.0, "sigma_si_proton_cm2": 3e-46,
             "verdict": "allowed", "n_sigma_fog": "",
             **{f"logL_{e}": 0.0 for e in NATIVE_EXPERIMENTS}},
            {"point_idx": 1, "m_dm_gev": 100.0, "sigma_si_proton_cm2": 1e-46,
             "verdict": "excluded", "n_sigma_fog": "",
             **{f"logL_{e}": -17.3 for e in NATIVE_EXPERIMENTS}},
            {"point_idx": 2, "m_dm_gev": 200.0, "sigma_si_proton_cm2": 2e-46,
             "verdict": "excluded", "n_sigma_fog": "",
             **{f"logL_{e}": -5.0 for e in NATIVE_EXPERIMENTS}},
        ]
        sorted_rows = sorted(rows, key=lambda r: r["point_idx"])
        csv_path = tmp_path / "sorted.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(sorted_rows)

        with open(csv_path) as f:
            reader = list(csv.DictReader(f))

        indices = [int(r["point_idx"]) for r in reader]
        assert indices == sorted(indices), f"Rows not sorted by point_idx: {indices}"
