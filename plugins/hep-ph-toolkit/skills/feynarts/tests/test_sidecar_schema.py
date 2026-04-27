"""test_sidecar_schema.py — validate FeynAmpList.meta.json sidecar against processspec/v1.

Ensures the sidecar written by postprocess.py embeds a processspec that validates
against plugins/shared/schemas/processspec.schema.json (Phase-0 canonical schema).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest

# Paths
TESTS_DIR = Path(__file__).parent
GOLDENS_DIR = TESTS_DIR / "goldens"
SCHEMA_PATH = (
    Path(__file__).parents[4] / "shared" / "schemas" / "processspec.schema.json"
)

# Also resolve from worktree root via scripts path
_SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def processspec_schema():
    """Load the canonical processspec/v1 JSON schema."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"processspec schema not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestSidecarConformsToProcessspec:
    """The FeynAmpList.meta.json sidecar must embed a valid processspec/v1 object."""

    def test_golden_sidecar_has_processspec_key(self):
        """Golden sidecar must have a top-level 'processspec' key."""
        meta_path = GOLDENS_DIR / "sm_ee_mumu_tree" / "FeynAmpList.meta.json"
        with open(meta_path) as f:
            meta = json.load(f)
        assert "processspec" in meta, "FeynAmpList.meta.json must contain 'processspec' key"

    def test_golden_sidecar_schema_version(self):
        """Top-level schema_version must be 'processspec/v1'."""
        meta_path = GOLDENS_DIR / "sm_ee_mumu_tree" / "FeynAmpList.meta.json"
        with open(meta_path) as f:
            meta = json.load(f)
        assert meta["schema_version"] == "processspec/v1"

    def test_golden_processspec_validates_against_schema(self, processspec_schema):
        """The embedded processspec object must validate against processspec/v1 schema."""
        meta_path = GOLDENS_DIR / "sm_ee_mumu_tree" / "FeynAmpList.meta.json"
        with open(meta_path) as f:
            meta = json.load(f)
        processspec = meta["processspec"]
        # Must not raise
        jsonschema.validate(instance=processspec, schema=processspec_schema)

    def test_postprocess_writes_valid_processspec_sidecar(self, processspec_schema, tmp_path):
        """postprocess_output must write a meta.json whose 'processspec' validates."""
        from postprocess import postprocess_output

        # Create a minimal FeynAmpList.m
        (tmp_path / "FeynAmpList.m").write_text(
            'FeynAmpList[{FeynAmp[GraphID[Topology == 1], ...]}]\n'
        )

        postprocess_output(
            run_dir=str(tmp_path),
            n_diagrams=1,
            feynarts_version="3.11",
            model_hash="abc123",
            processspec={
                "schema_version": "processspec/v1",
                "particles": {
                    "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"},
                           {"label": "e-", "pdg": 11, "mass_symbol": "ME"}],
                    "out": [{"label": "mu+", "pdg": -13, "mass_symbol": "MMU"},
                            {"label": "mu-", "pdg": 13, "mass_symbol": "MMU"}],
                },
                "loop_order": 0,
                "kinematic_limit": "general",
                "excludes": [],
            },
            loop_order=0,
            wall_clock_s=1.23,
            model_name="SM",
        )

        meta_path = tmp_path / "FeynAmpList.meta.json"
        assert meta_path.exists()
        with open(meta_path) as f:
            meta = json.load(f)

        assert meta["schema_version"] == "processspec/v1"
        assert "processspec" in meta
        # Validate the embedded processspec against the canonical schema
        jsonschema.validate(instance=meta["processspec"], schema=processspec_schema)
