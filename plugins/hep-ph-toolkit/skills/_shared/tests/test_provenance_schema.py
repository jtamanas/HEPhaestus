"""
Tests for _shared/provenance.schema.json (T-SF-2).
Covers: 1 positive valid stub, 3 missing-required fields, 1 banned-extra-key,
1 valid extensions object, and 3 live cycle-1 provenance.json artifacts.
"""
import json
import pathlib
import pytest
import jsonschema

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "provenance.schema.json"
REPO_ROOT = pathlib.Path(__file__).parents[5]  # hephaestus/
LIVE_RUNS_BASE = (
    REPO_ROOT
    / ".shift-manager/run-20260425-current/workstreams/singlet-doublet/playtest/runs"
)


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def validate(schema, instance):
    """Return None on pass; raise ValidationError on fail."""
    jsonschema.Draft7Validator(schema).validate(instance)


# ---------------------------------------------------------------------------
# Case 1: positive valid stub (all required + optional fields)
# ---------------------------------------------------------------------------
def test_valid_full_stub(schema):
    doc = {
        "schema_version": "1",
        "run_id": "20260425T122317Z-55c01ea",
        "git_sha": "55c01ea",
        "run_at": "2026-04-25T12:23:36Z",
        "wallclock_seconds": 45,
        "practitioner_script": "plugins/hep-ph-toolkit/skills/singlet-doublet/practitioner_script.md",
        "matrix_name": "ZN",
        "constraint": "relic",
    }
    validate(schema, doc)  # must not raise


# ---------------------------------------------------------------------------
# Case 2: valid minimal stub (required fields only)
# ---------------------------------------------------------------------------
def test_valid_minimal_stub(schema):
    doc = {
        "schema_version": "1",
        "run_id": "abc12345",
        "git_sha": "deadbeef",
        "run_at": "2026-01-01T00:00:00Z",
    }
    validate(schema, doc)


# ---------------------------------------------------------------------------
# Cases 3–5: missing each required field
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("missing_key", ["run_id", "git_sha", "run_at"])
def test_missing_required_field(schema, missing_key):
    doc = {
        "schema_version": "1",
        "run_id": "abc12345",
        "git_sha": "deadbeef",
        "run_at": "2026-01-01T00:00:00Z",
    }
    del doc[missing_key]
    with pytest.raises(jsonschema.ValidationError):
        validate(schema, doc)


# ---------------------------------------------------------------------------
# Case 6: missing schema_version fails
# ---------------------------------------------------------------------------
def test_missing_schema_version(schema):
    doc = {
        "run_id": "abc12345",
        "git_sha": "deadbeef",
        "run_at": "2026-01-01T00:00:00Z",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate(schema, doc)


# ---------------------------------------------------------------------------
# Case 7: banned extra key at root fails (additionalProperties: false)
# ---------------------------------------------------------------------------
def test_banned_extra_key(schema):
    doc = {
        "schema_version": "1",
        "run_id": "abc12345",
        "git_sha": "deadbeef",
        "run_at": "2026-01-01T00:00:00Z",
        "unexpected_field_xyz": "should fail",
    }
    with pytest.raises(jsonschema.ValidationError):
        validate(schema, doc)


# ---------------------------------------------------------------------------
# Case 8: valid extensions object passes (forward-compat escape hatch)
# ---------------------------------------------------------------------------
def test_valid_extensions_object(schema):
    doc = {
        "schema_version": "1",
        "run_id": "abc12345",
        "git_sha": "deadbeef",
        "run_at": "2026-01-01T00:00:00Z",
        "extensions": {
            "future_field": "some_value",
            "another": 42,
        },
    }
    validate(schema, doc)  # must not raise


# ---------------------------------------------------------------------------
# Cases 9–11: live cycle-1 provenance.json artifacts (parametrized)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("run_num", [1, 2, 3])
def test_live_provenance_artifact(schema, run_num):
    prov_path = LIVE_RUNS_BASE / f"run-{run_num}" / "provenance.json"
    if not prov_path.exists():
        pytest.skip(f"Live provenance artifact not found: {prov_path}")
    doc = json.loads(prov_path.read_text())
    # Live artifacts don't have schema_version — inject it for validation
    # (schema_version was added by this schema-fix; live files predate it)
    doc_with_version = {"schema_version": "1", **doc}
    validate(schema, doc_with_version)
