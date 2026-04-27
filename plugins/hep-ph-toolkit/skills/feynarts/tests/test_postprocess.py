"""Tests for postprocess.py."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from postprocess import (
    PostprocessError,
    postprocess_output,
)


@pytest.fixture
def run_dir(tmp_path):
    """Create a fake run directory with a minimal FeynAmpList.m."""
    fa = tmp_path / "FeynAmpList.m"
    # Minimal valid FeynAmpList.m content (just needs to be parseable as non-empty)
    fa.write_text(
        '{{schema_version -> 1, feynarts_version -> "3.11", '
        'model_hash -> "abc123", '
        'amp -> {FeynAmp[GraphID[Topology == 1], ...]}}}' + "\n"
    )
    return tmp_path


@pytest.fixture
def run_dir_with_meta(run_dir):
    """FeynAmpList.m that simulates 1 diagram."""
    return run_dir


class TestSidecarSchema:
    def test_meta_json_written(self, run_dir):
        result = postprocess_output(
            run_dir=str(run_dir),
            n_diagrams=1,
            feynarts_version="3.11",
            model_hash="abc123",
            processspec={
                "schema_version": "processspec/v1",
                "particles": {
                    "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"}],
                    "out": [{"label": "mu+", "pdg": 13, "mass_symbol": "MMU"}],
                },
                "loop_order": 0,
                "kinematic_limit": "general",
                "excludes": [],
            },
            loop_order=0,
            wall_clock_s=1.23,
            model_name="SM",
        )
        meta_path = Path(run_dir) / "FeynAmpList.meta.json"
        assert meta_path.exists()
        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["schema_version"] == "processspec/v1"
        assert meta["feynarts_version"] == "3.11"
        assert meta["n_diagrams"] == 1
        # loop_order is now inside processspec sub-object
        assert meta["processspec"]["loop_order"] == 0
        assert meta["processspec"]["kinematic_limit"] == "general"
        assert meta["processspec"]["particles"]["in"][0]["label"] == "e+"
        assert meta["processspec"]["particles"]["out"][0]["label"] == "mu+"

    def test_summary_json_written(self, run_dir):
        postprocess_output(
            run_dir=str(run_dir),
            n_diagrams=1,
            feynarts_version="3.11",
            model_hash="abc123",
            processspec={
                "schema_version": "processspec/v1",
                "particles": {
                    "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"}],
                    "out": [{"label": "mu+", "pdg": 13, "mass_symbol": "MMU"}],
                },
                "loop_order": 0,
                "kinematic_limit": "general",
                "excludes": [],
            },
            loop_order=0,
            wall_clock_s=2.5,
            model_name="SM",
        )
        summary_path = Path(run_dir) / "summary.json"
        assert summary_path.exists()
        with open(summary_path) as f:
            summary = json.load(f)
        assert summary["n_diagrams"] == 1
        assert summary["loop_order"] == 0
        assert summary["model"] == "SM"
        assert isinstance(summary["cached"], bool)


class TestSizeCapGuard:
    def test_amp_size_cap_triggers(self, run_dir):
        """Mock FeynAmpList.m to appear as 201 MB, expect fatal error."""
        with patch("os.stat") as mock_stat:
            mock_stat.return_value.st_size = 201 * 1024 * 1024
            with pytest.raises(PostprocessError) as exc_info:
                postprocess_output(
                    run_dir=str(run_dir),
                    n_diagrams=50,
                    feynarts_version="3.11",
                    model_hash="abc123",
                    processspec={
                        "schema_version": "processspec/v1",
                        "particles": {"in": [], "out": []},
                        "loop_order": 0,
                        "kinematic_limit": "general",
                        "excludes": [],
                    },
                    loop_order=0,
                    wall_clock_s=10.0,
                    model_name="SM",
                    amp_size_cap_mb=200,
                )
        assert exc_info.value.code == "FEYNARTS_AMP_TOO_LARGE"
        assert exc_info.value.context["amp_size_mb"] == 201
        assert exc_info.value.context["cap"] == 200
        # FeynAmpList.m must remain on disk for inspection
        assert (Path(run_dir) / "FeynAmpList.m").exists()

    def test_amp_size_ok(self, run_dir):
        """Under cap: no error."""
        with patch("os.stat") as mock_stat:
            mock_stat.return_value.st_size = 1 * 1024 * 1024  # 1 MB
            result = postprocess_output(
                run_dir=str(run_dir),
                n_diagrams=1,
                feynarts_version="3.11",
                model_hash="abc123",
                processspec={
                    "schema_version": "processspec/v1",
                    "particles": {
                        "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"}],
                        "out": [{"label": "mu+", "pdg": 13, "mass_symbol": "MMU"}],
                    },
                    "loop_order": 0,
                    "kinematic_limit": "general",
                    "excludes": [],
                },
                loop_order=0,
                wall_clock_s=1.0,
                model_name="SM",
                amp_size_cap_mb=200,
            )
        assert result is not None


class TestTopologiesJson:
    def test_topologies_json_written(self, run_dir):
        postprocess_output(
            run_dir=str(run_dir),
            n_diagrams=1,
            feynarts_version="3.11",
            model_hash="abc123",
            processspec={
                "schema_version": "processspec/v1",
                "particles": {
                    "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"}],
                    "out": [{"label": "mu+", "pdg": 13, "mass_symbol": "MMU"}],
                },
                "loop_order": 0,
                "kinematic_limit": "general",
                "excludes": [],
            },
            loop_order=0,
            wall_clock_s=1.0,
            model_name="SM",
        )
        topo_path = Path(run_dir) / "topologies.json"
        assert topo_path.exists()
        with open(topo_path) as f:
            topo = json.load(f)
        assert "n_topologies" in topo
