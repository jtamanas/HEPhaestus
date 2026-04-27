"""S1: Test that constraints.yaml schema v2 shape is correct and that the
matrix_capabilities.schema.json rejects invalid verdict values.

These tests cover:
  - schema_version == 2 in constraints.yaml
  - Three pointer fields present (blocker_catalog_ref, taxonomy_ref, analytic_exceptions_ref)
  - matrix_capabilities.schema.json rejects verdict: unknown
  - matrix_capabilities.schema.json rejects verdict: blocked without blocker:
"""
from __future__ import annotations
import json
from pathlib import Path
import yaml
import pytest

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
CONSTRAINTS_YAML = SHARED / "constraints.yaml"
SCHEMA_PATH = SHARED / "matrix_capabilities.schema.json"


def load_constraints():
    return yaml.safe_load(CONSTRAINTS_YAML.read_text())


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


class TestConstraintsV2Structure:
    def test_schema_version_is_2(self):
        c = load_constraints()
        assert c["schema_version"] == 2, f"Expected schema_version 2, got {c['schema_version']}"

    def test_blocker_catalog_ref_present(self):
        c = load_constraints()
        assert "blocker_catalog_ref" in c
        assert "path" in c["blocker_catalog_ref"]
        assert "version" in c["blocker_catalog_ref"]

    def test_taxonomy_ref_present(self):
        c = load_constraints()
        assert "taxonomy_ref" in c
        assert "path" in c["taxonomy_ref"]

    def test_analytic_exceptions_ref_present(self):
        c = load_constraints()
        assert "analytic_exceptions_ref" in c
        assert "path" in c["analytic_exceptions_ref"]

    def test_prereqs_still_present(self):
        c = load_constraints()
        assert "prereqs" in c
        assert "madgraph" in c["prereqs"]

    def test_models_still_present(self):
        c = load_constraints()
        assert "models" in c
        assert "dark-su3" in c["models"]


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestCapabilitySchemaRejectsInvalid:
    """Test that the JSON Schema correctly rejects invalid capability blocks."""

    def _validate(self, obj):
        """Validate obj against matrix_capabilities.schema.json."""
        schema = load_schema()
        jsonschema.validate(instance=obj, schema=schema)

    def _valid_blocked_rule(self):
        return {
            "axis": "A1",
            "match": "SM + extra SU(N)",
            "verdict": "blocked",
            "blocker": "MG5_DARK_COLOR_TENSOR_WALL",
            "evidence": "intel/digest.md §52"
        }

    def _valid_supported_rule(self):
        return {
            "axis": "A1",
            "match": "*",
            "verdict": "supported"
        }

    def _minimal_valid_block(self):
        return {
            "description": "Test prereq",
            "role": {"relic": "primary"},
            "support": [self._valid_supported_rule()]
        }

    def test_valid_block_passes(self):
        self._validate(self._minimal_valid_block())

    def test_valid_blocked_verdict_passes(self):
        block = {
            "description": "Test",
            "role": {"relic": "primary"},
            "support": [self._valid_blocked_rule()]
        }
        self._validate(block)

    def test_verdict_unknown_rejected(self):
        """'unknown' is not in the verdict enum; must be rejected."""
        block = {
            "description": "Test",
            "role": {"relic": "primary"},
            "support": [
                {
                    "axis": "A1",
                    "match": "*",
                    "verdict": "unknown"  # INVALID
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate(block)

    def test_blocked_without_blocker_rejected(self):
        """verdict: blocked without blocker: must be rejected."""
        block = {
            "description": "Test",
            "role": {"relic": "primary"},
            "support": [
                {
                    "axis": "A1",
                    "match": "SM + extra SU(N)",
                    "verdict": "blocked",
                    # Missing: blocker and evidence
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate(block)

    def test_supported_with_caveat_without_caveat_rejected(self):
        """verdict: supported_with_caveat without caveat: must be rejected."""
        block = {
            "description": "Test",
            "role": {"relic": "primary"},
            "support": [
                {
                    "axis": "A1",
                    "match": "*",
                    "verdict": "supported_with_caveat",
                    # Missing: caveat and evidence
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate(block)

    def test_not_applicable_passes(self):
        """not_applicable does not require blocker or caveat."""
        block = {
            "description": "Test",
            "role": {"relic": "primary"},
            "support": [
                {
                    "axis": "A4.n_higgs_doublets",
                    "match": ">=2",
                    "verdict": "not_applicable"
                }
            ]
        }
        self._validate(block)


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestChainOverrideSchema:
    """Blocker 7: Verify ChainOverride + MatrixAcknowledgement schema shape is enforced."""

    def _validate_chain_override(self, obj):
        # Must validate in context of the full schema so $ref to MatrixAcknowledgement resolves
        schema = load_schema()
        co_schema = {"$ref": "#/$defs/ChainOverride", "$defs": schema["$defs"]}
        jsonschema.validate(instance=obj, schema=co_schema)

    def test_valid_chain_override_no_ack_passes(self):
        """A chain_override with chain + reason (no acknowledgement) is valid."""
        override = {
            "chain": ["sarah-build", "analytic_backend"],
            "reason": "Test override without ack",
        }
        self._validate_chain_override(override)

    def test_valid_chain_override_with_ack_passes(self):
        """A chain_override with a well-formed matrix_acknowledgement passes."""
        override = {
            "chain": ["analytic_backend"],
            "reason": "Full analytic path",
            "matrix_acknowledgement": {
                "accepted_blockers": ["MG5_DARK_COLOR_TENSOR_WALL", "ANALYTIC_EXCEPTION_TRIGGER"],
                "accepted_workaround": "ANALYTIC_BACKEND_PATH",
                "authority": "WS4 dsu3-002",
                "last_audited": "2026-04-26",
            },
        }
        self._validate_chain_override(override)

    def test_malformed_accepted_blockers_string_rejected(self):
        """accepted_blockers as a string (not a list) must be rejected (Blocker 7)."""
        override = {
            "chain": ["analytic_backend"],
            "reason": "Malformed ack",
            "matrix_acknowledgement": {
                "accepted_blockers": "MG5_DARK_COLOR_TENSOR_WALL",  # INVALID: must be list
                "authority": "test",
                "last_audited": "2026-04-26",
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate_chain_override(override)

    def test_missing_chain_rejected(self):
        """chain_override without 'chain' must be rejected."""
        override = {
            "reason": "No chain provided",
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate_chain_override(override)

    def test_missing_reason_rejected(self):
        """chain_override without 'reason' must be rejected."""
        override = {
            "chain": ["analytic_backend"],
        }
        with pytest.raises(jsonschema.ValidationError):
            self._validate_chain_override(override)

    def test_malformed_fixture_detected_by_loader(self):
        """load_capability_matrix rejects malformed_acknowledgement.yaml fixture."""
        import sys
        REPO_ROOT = Path(__file__).parent.parent.parent
        SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
        if str(SHARED) not in sys.path:
            sys.path.insert(0, str(SHARED))
        from matrix_lookup import load_capability_matrix

        NEGATIVE = Path(__file__).parent / "fixtures" / "matrix" / "negative"
        malformed = NEGATIVE / "malformed_acknowledgement.yaml"
        with pytest.raises((ValueError, jsonschema.ValidationError)):
            load_capability_matrix(
                constraints_path=malformed,
                catalog_path=SHARED / "blocker_catalog.yaml",
            )
