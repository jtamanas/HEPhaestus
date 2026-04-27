"""
test_blocker_class_map.py — S16 unit tests for blocker_class_map.yaml.

Three assertions per plan S16:
1. All blocker_code values are unique (no duplicates).
2. All mapping class values are in the declared blocker_classes closed set.
3. Every mapping entry has required keys: axis_predicate, blocker_code, class, description.
"""

from pathlib import Path
import pytest

_MAP_PATH = Path(__file__).resolve().parent.parent / "blocker_class_map.yaml"


@pytest.fixture(scope="module")
def blocker_map():
    try:
        import yaml  # type: ignore[import]
    except ModuleNotFoundError:
        pytest.skip("pyyaml not installed")
    with open(_MAP_PATH) as f:
        return yaml.safe_load(f)


def test_no_duplicate_blocker_codes(blocker_map):
    """S16: every blocker_code must be unique across all mapping rows."""
    codes = [m["blocker_code"] for m in blocker_map["mappings"]]
    seen = set()
    duplicates = []
    for code in codes:
        if code in seen:
            duplicates.append(code)
        seen.add(code)
    assert not duplicates, (
        f"Duplicate blocker_code values found in blocker_class_map.yaml: {duplicates}"
    )


def test_all_classes_in_closed_set(blocker_map):
    """S16: every mapping class must be in the declared blocker_classes list."""
    closed_set = set(blocker_map["blocker_classes"])
    bad_entries = [
        (m["blocker_code"], m["class"])
        for m in blocker_map["mappings"]
        if m.get("class") not in closed_set
    ]
    assert not bad_entries, (
        f"blocker_class_map.yaml has entries with class not in closed set: {bad_entries}"
    )


def test_all_mappings_have_required_keys(blocker_map):
    """S16: every mapping row must have axis_predicate, blocker_code, class, description."""
    required = {"axis_predicate", "blocker_code", "class", "description"}
    bad_entries = []
    for m in blocker_map["mappings"]:
        missing = required - set(m.keys())
        if missing:
            bad_entries.append((m.get("blocker_code", "?"), missing))
    assert not bad_entries, (
        f"blocker_class_map.yaml entries missing required keys: {bad_entries}"
    )
