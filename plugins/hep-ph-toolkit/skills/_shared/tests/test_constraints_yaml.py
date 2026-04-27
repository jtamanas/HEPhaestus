"""
test_constraints_yaml.py — validate constraints.yaml schema and internal consistency.

Done-criteria assertions:
  - top-level keys: schema_version, prereqs, constraints, models
  - every prereq in constraints.*.chain exists in prereqs:
  - every models.*.time_overrides key ∈ {relic, dd, id}
  - every models.*.multi_component_prereq ∈ prereqs (when present)
  - every prereq has status ∈ {exists, planned} and hours.cold + hours.cached as 2-element lists
"""

import pathlib
import pytest
import yaml

_YAML = pathlib.Path(__file__).parent.parent / "constraints.yaml"


@pytest.fixture(scope="module")
def data():
    with open(_YAML) as fh:
        return yaml.safe_load(fh)


def test_top_level_keys(data):
    """Top-level keys must be schema_version, prereqs, constraints, models."""
    required = {"schema_version", "prereqs", "constraints", "models"}
    assert required <= set(data.keys()), (
        f"Missing top-level keys: {required - set(data.keys())}"
    )


def test_schema_version(data):
    # WS2 plan S1 / commit a5f33af bumped schema_version 1→2
    assert data["schema_version"] == 2


def test_prereq_entries(data):
    """Every prereq must have status ∈ {exists, planned} and hours with 2-element lists."""
    for name, meta in data["prereqs"].items():
        assert "status" in meta, f"prereq '{name}' missing 'status'"
        assert meta["status"] in {"exists", "planned"}, (
            f"prereq '{name}' status must be 'exists' or 'planned', got {meta['status']!r}"
        )
        assert "hours" in meta, f"prereq '{name}' missing 'hours'"
        hours = meta["hours"]
        assert "cold" in hours and "cached" in hours, (
            f"prereq '{name}' hours must have 'cold' and 'cached'"
        )
        assert len(hours["cold"]) == 2, f"prereq '{name}' hours.cold must be a 2-element list"
        assert len(hours["cached"]) == 2, f"prereq '{name}' hours.cached must be a 2-element list"
        assert isinstance(hours["cold"][0], (int, float)), (
            f"prereq '{name}' hours.cold[0] must be numeric"
        )
        assert isinstance(hours["cold"][1], (int, float)), (
            f"prereq '{name}' hours.cold[1] must be numeric"
        )


def test_constraint_chains_reference_known_prereqs(data):
    """Every prereq in constraints.*.chain must exist in the prereqs map."""
    known_prereqs = set(data["prereqs"].keys())
    for cid, cmeta in data["constraints"].items():
        chain = cmeta.get("chain", [])
        for prereq in chain:
            assert prereq in known_prereqs, (
                f"Constraint '{cid}' chain references unknown prereq '{prereq}'"
            )


def test_constraint_default_time(data):
    """Non-placeholder constraints must have default_time with cold and cached 2-element lists."""
    for cid, cmeta in data["constraints"].items():
        if cmeta.get("placeholder"):
            continue
        assert "default_time" in cmeta, f"Constraint '{cid}' missing default_time"
        dt = cmeta["default_time"]
        assert "cold" in dt and "cached" in dt, (
            f"Constraint '{cid}' default_time missing cold or cached"
        )
        assert len(dt["cold"]) == 2 and len(dt["cached"]) == 2, (
            f"Constraint '{cid}' default_time.cold/cached must be 2-element lists"
        )


def test_model_time_overrides_valid_keys(data):
    """Every models.*.time_overrides key must be in {relic, dd, id}."""
    valid_constraints = {"relic", "dd", "id"}
    for model_id, mmeta in data["models"].items():
        overrides = mmeta.get("time_overrides", {})
        for k in overrides:
            assert k in valid_constraints, (
                f"Model '{model_id}' time_overrides has invalid key '{k}' "
                f"(must be in {valid_constraints})"
            )


def test_model_multi_component_prereq_in_prereqs(data):
    """When multi_component_prereq is present, it must reference a known prereq."""
    known_prereqs = set(data["prereqs"].keys())
    for model_id, mmeta in data["models"].items():
        mcp = mmeta.get("multi_component_prereq")
        if mcp is not None:
            assert mcp in known_prereqs, (
                f"Model '{model_id}' multi_component_prereq '{mcp}' "
                f"not found in prereqs"
            )


def test_all_three_models_present(data):
    """All three Profumo benchmark models must be declared."""
    required_models = {"singlet-doublet", "2hdm-a", "dark-su3"}
    assert required_models <= set(data["models"].keys()), (
        f"Missing models: {required_models - set(data['models'].keys())}"
    )


def test_collider_constraint_is_placeholder(data):
    """Collider constraint must be marked placeholder with a message."""
    collider = data["constraints"].get("collider", {})
    assert collider.get("placeholder") is True, "constraints.collider must have placeholder: true"
    assert "message" in collider, "constraints.collider must have a message field"
    assert len(collider["message"]) > 0


def test_dark_su3_multi_component(data):
    """dark-su3 must be multi_component and reference dark-matter-constraints."""
    dark = data["models"]["dark-su3"]
    assert dark["multi_component"] is True
    assert dark.get("multi_component_prereq") == "dark-matter-constraints"


def test_singlet_doublet_not_multi_component(data):
    """singlet-doublet must not be multi_component."""
    sd = data["models"]["singlet-doublet"]
    assert sd["multi_component"] is False


def test_dm_candidates_structure(data):
    """Each dm_candidates entry must have name, spin, notes."""
    for model_id, mmeta in data["models"].items():
        candidates = mmeta.get("dm_candidates", [])
        assert len(candidates) >= 1, f"Model '{model_id}' must have at least one DM candidate"
        for c in candidates:
            for field in ("name", "spin", "notes"):
                assert field in c, (
                    f"Model '{model_id}' dm_candidate missing field '{field}': {c}"
                )
