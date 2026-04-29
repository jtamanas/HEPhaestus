"""test_blocker_schema_valid.py — validate all fixtures/blockers/*.json against blocker.schema.json."""
import json
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_BLOCKERS_DIR = _SCRIPT_DIR / "fixtures" / "blockers"
_SCHEMA_PATH = (
    _SCRIPT_DIR.parent.parent.parent.parent
    / "skills" / "_shared" / "blocker.schema.json"
)


def _load_schema() -> dict:
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def _get_blocker_files() -> list[Path]:
    return sorted(_BLOCKERS_DIR.glob("*.json"))


@pytest.mark.parametrize("blocker_path", _get_blocker_files(), ids=lambda p: p.stem)
def test_blocker_validates_against_schema(blocker_path):
    pytest.importorskip("jsonschema")
    import jsonschema

    schema = _load_schema()
    with open(blocker_path) as f:
        blocker = json.load(f)

    # Validate
    jsonschema.validate(blocker, schema)


def test_schema_symlink_resolves():
    assert _SCHEMA_PATH.exists(), (
        f"blocker.schema.json symlink does not resolve: {_SCHEMA_PATH}"
    )


def test_all_blockers_have_code():
    for bf in _get_blocker_files():
        with open(bf) as f:
            b = json.load(f)
        assert "code" in b, f"{bf.name} missing 'code' field"
        assert "mode" in b, f"{bf.name} missing 'mode' field"
        assert b["mode"] in ("fatal", "recoverable"), (
            f"{bf.name} has unexpected mode: {b['mode']!r}"
        )
