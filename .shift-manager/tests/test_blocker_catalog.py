"""S2: Test the central blocker catalog.

Invariants tested:
  - Invariant #2: every catalog entry parses without schema error
  - Invariant #3: every class in the 5-class enum
  - fix_locality required when class == missing-tool-feature
  - At least 57 entries total
"""
from __future__ import annotations
from pathlib import Path
import yaml
import pytest

try:
    import jsonschema
    import json
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
CATALOG_PATH = SHARED / "blocker_catalog.yaml"
CATALOG_SCHEMA_PATH = SHARED / "blocker_catalog.schema.json"

VALID_CLASSES = {
    "missing-skill",
    "missing-tool-feature",
    "fundamental-group-theory-gap",
    "regime-mismatch",
    "spec-authoring-gap",
    "informational",
    "analytic-exception",
}
VALID_SEVERITIES = {"fatal", "recoverable", "informational"}
VALID_FIX_LOCALITIES = {"upstream", "local_patch", "both"}


@pytest.fixture
def catalog():
    return yaml.safe_load(CATALOG_PATH.read_text())


class TestCatalogStructure:
    def test_catalog_loads(self, catalog):
        assert catalog is not None
        assert "blockers" in catalog

    def test_schema_version_1(self, catalog):
        assert catalog["schema_version"] == 1

    def test_at_least_57_entries(self, catalog):
        n = len(catalog["blockers"])
        assert n >= 57, f"Expected >= 57 blocker codes, got {n}"

    def test_all_entries_have_required_fields(self, catalog):
        required = {"class", "severity", "description", "owned_by"}
        for code, entry in catalog["blockers"].items():
            for field in required:
                assert field in entry, f"{code}: missing required field '{field}'"

    def test_all_classes_in_enum(self, catalog):
        """Invariant #3: every class must be in the 5-class enum (+ informational + analytic-exception)."""
        for code, entry in catalog["blockers"].items():
            cls = entry["class"]
            assert cls in VALID_CLASSES, (
                f"{code}: invalid class '{cls}'. Valid: {VALID_CLASSES}"
            )

    def test_all_severities_in_enum(self, catalog):
        for code, entry in catalog["blockers"].items():
            sev = entry["severity"]
            assert sev in VALID_SEVERITIES, (
                f"{code}: invalid severity '{sev}'. Valid: {VALID_SEVERITIES}"
            )

    def test_missing_tool_feature_has_fix_locality(self, catalog):
        """If class == missing-tool-feature, fix_locality must be present."""
        for code, entry in catalog["blockers"].items():
            if entry["class"] == "missing-tool-feature":
                assert "fix_locality" in entry, (
                    f"{code}: class=missing-tool-feature but missing fix_locality"
                )
                assert entry["fix_locality"] in VALID_FIX_LOCALITIES, (
                    f"{code}: invalid fix_locality '{entry['fix_locality']}'"
                )

    def test_owned_codes_present(self, catalog):
        """Spot-check: key WS2-owned codes must be present."""
        owned_codes = [
            "MG5_DARK_COLOR_TENSOR_WALL",
            "ANALYTIC_EXCEPTION_TRIGGER",
            "ANALYTIC_MODULE_MISSING",
            "CALCHEP_MDL_MISSING",
            "SARAH_MATTER_REP_UNSUPPORTED",
            "LOOP_DD_TOOLING_PLANNED",
            "HIGGSTOOLS_CPV_NOT_SUPPORTED",
            "SPHENO_NOT_REQUESTED",
        ]
        for code in owned_codes:
            assert code in catalog["blockers"], f"Missing owned code: {code}"

    def test_mirrored_codes_present(self, catalog):
        """Spot-check: mirrored DMC codes must be present."""
        mirrored = [
            "MADDM_MISSING",
            "UFO_MISSING",
            "ANALYTIC_BACKEND_PATH",
            "DDCALC_INPUT_INVALID",
            "HIGGSTOOLS_SLHA_MISSING_BLOCKS",
            "DRAKE_NOT_INSTALLED",
        ]
        for code in mirrored:
            assert code in catalog["blockers"], f"Missing mirrored code: {code}"

    def test_mirrored_codes_have_dmc_owner(self, catalog):
        """Mirrored codes should be owned_by dark-matter-constraints."""
        mirrored = [
            "MADDM_MISSING", "UFO_MISSING", "SLHA_MISSING",
            "ANALYTIC_BACKEND_PATH", "DRAKE_MISSING",
        ]
        for code in mirrored:
            if code in catalog["blockers"]:
                assert catalog["blockers"][code]["owned_by"] == "dark-matter-constraints", (
                    f"{code}: expected owned_by=dark-matter-constraints"
                )


@pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
class TestCatalogSchemaValidation:
    """Invariant #2: every catalog entry parses without schema error."""

    def test_catalog_validates_against_schema(self, catalog):
        schema = json.loads(CATALOG_SCHEMA_PATH.read_text())
        # Validate the catalog object itself
        jsonschema.validate(instance=catalog, schema=schema)

    def test_invalid_class_rejected(self):
        """Negative: an entry with invalid class should fail validation."""
        schema = json.loads(CATALOG_SCHEMA_PATH.read_text())
        bad_catalog = {
            "schema_version": 1,
            "blockers": {
                "BAD_CODE_HERE": {
                    "class": "invented-class",   # INVALID
                    "severity": "fatal",
                    "description": "test",
                    "owned_by": "this-ws",
                }
            }
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_catalog, schema=schema)
