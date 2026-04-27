"""
test_recoverable_handling.py — Deterministic recoverable-failure test.

Uses the synthetic scan_recoverable_trigger.spc fixture to verify:
    1. The fixture parses to status=recoverable with blocker_code=SPHENO_SPECTRUM_PROBLEM.
    2. In a 3-point scan where one point hits the recoverable fixture,
       the scan continues past it and records status=recoverable in scan_index.csv.
    3. The other two points are unaffected.

This test does NOT depend on physics accidents of a real scan.
It is deterministic: the recoverable-trigger fixture always contains Block PROBLEM 1.

Test isolation: uses HEPPH_STATE_ROOT and XDG_CONFIG_HOME per global invariant §2.3.
"""

import csv
import importlib.util
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_FIXTURES = _HERE / "fixtures" / "slha"
_RECOVERABLE_FIXTURE = _FIXTURES / "scan_recoverable_trigger.spc"
_CLEAN_FIXTURE = _FIXTURES / "clean_spectrum.spc"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def scan_mod():
    return _load_module("scan", _SCRIPTS / "scan.py")


@pytest.fixture(scope="module")
def parse_slha_mod():
    return _load_module("parse_slha", _SCRIPTS / "parse_slha.py")


@pytest.fixture(scope="module")
def run_point_mod():
    return _load_module("run_point", _SCRIPTS / "run_point.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# ---------------------------------------------------------------------------
# Test 1: fixture itself parses as recoverable
# ---------------------------------------------------------------------------
class TestRecoverableFixtureParses:
    def test_parse_yields_problem_code_1(self, parse_slha_mod):
        result = parse_slha_mod.parse(_RECOVERABLE_FIXTURE)
        assert 1 in result["problems"], (
            f"Expected problem code 1 in {_RECOVERABLE_FIXTURE}, got {result['problems']}"
        )

    def test_parse_triggers_spectrum_problem(self, parse_slha_mod):
        result = parse_slha_mod.parse(_RECOVERABLE_FIXTURE)
        assert set(result["problems"]) & {1, 2, 3}, (
            "Expected at least one of {1,2,3} in problems"
        )


# ---------------------------------------------------------------------------
# Test 2: scan continues past recoverable row
# ---------------------------------------------------------------------------
class TestScanContinuesPastRecoverable:
    """
    Monkeypatch scan_worker to route one point through the recoverable fixture
    and the other two through the clean fixture. Verify:
    - scan_index.csv has 3 rows.
    - Exactly one row has status=recoverable and blocker_code=SPHENO_SPECTRUM_PROBLEM.
    - The other two rows have status=ok.
    """

    def _make_worker(self, recoverable_idx: int, parse_slha_mod):
        """Return a scan_worker mock that uses the recoverable fixture for one point."""

        def _worker(point: dict, out_dir: Path, model_name: str, spec: dict) -> dict:
            # Determine which fixture to use based on point index
            point_idx = int(out_dir.name)
            if point_idx == recoverable_idx:
                src = _RECOVERABLE_FIXTURE
            else:
                src = _CLEAN_FIXTURE

            spc_dest = out_dir / "SPheno.spc"
            shutil.copy2(str(src), str(spc_dest))

            summary = parse_slha_mod.parse(spc_dest)
            problems = summary.get("problems", [])

            if set(problems) & {1, 2, 3}:
                return {
                    "status": "recoverable",
                    "blocker_code": "SPHENO_SPECTRUM_PROBLEM",
                    "slha_path": str(spc_dest),
                    "timing_s": 0.001,
                }
            return {
                "status": "ok",
                "blocker_code": None,
                "slha_path": str(spc_dest),
                "timing_s": 0.001,
            }

        return _worker

    def test_3_point_scan_one_recoverable(self, scan_mod, parse_slha_mod, tmp_path):
        spec = {
            "name": "test_recoverable",
            "parameters": [
                {"name": "MpsiD", "default": 500.0},
            ],
        }
        axes = [("MpsiD", 300.0, 500.0, 100.0)]  # 3 values: 300, 400, 500

        worker_fn = self._make_worker(recoverable_idx=1, parse_slha_mod=parse_slha_mod)
        with patch.object(scan_mod, "scan_worker", side_effect=worker_fn):
            csv_path = scan_mod.scan("test_recoverable", axes, tmp_path / "scan", spec=spec)

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"

        statuses = [r["status"] for r in rows]
        blocker_codes = [r["blocker_code"] for r in rows]

        # Exactly one recoverable row
        recoverable_rows = [r for r in rows if r["status"] == "recoverable"]
        assert len(recoverable_rows) == 1, (
            f"Expected exactly 1 recoverable row, got {len(recoverable_rows)}: {statuses}"
        )

        # Recoverable row has correct blocker code
        rec_row = recoverable_rows[0]
        assert rec_row["blocker_code"] == "SPHENO_SPECTRUM_PROBLEM", (
            f"Expected SPHENO_SPECTRUM_PROBLEM, got {rec_row['blocker_code']!r}"
        )

        # Other two rows are ok
        ok_rows = [r for r in rows if r["status"] == "ok"]
        assert len(ok_rows) == 2, f"Expected 2 ok rows, got {len(ok_rows)}: {statuses}"

    def test_scan_does_not_abort_on_recoverable(self, scan_mod, parse_slha_mod, tmp_path):
        """The scan completes all 3 points even when one is recoverable."""
        spec = {
            "name": "test_no_abort",
            "parameters": [{"name": "x", "default": 1.0}],
        }
        axes = [("x", 1.0, 3.0, 1.0)]  # 3 points

        worker_fn = self._make_worker(recoverable_idx=0, parse_slha_mod=parse_slha_mod)
        call_count = [0]
        original_fn = worker_fn

        def counting_worker(*args, **kwargs):
            call_count[0] += 1
            return original_fn(*args, **kwargs)

        with patch.object(scan_mod, "scan_worker", side_effect=counting_worker):
            csv_path = scan_mod.scan("test_no_abort", axes, tmp_path / "scan_na", spec=spec)

        assert call_count[0] == 3, (
            f"Expected scan_worker called 3 times (all points), got {call_count[0]}"
        )

        rows = _read_csv_rows(csv_path)
        assert len(rows) == 3


def _read_csv_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))
