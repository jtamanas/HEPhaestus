"""test_blocker_shape.py — validate all /micromegas blocker fixtures against blocker.schema.json."""
import json
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_BLOCKERS_DIR = Path(__file__).resolve().parent / "fixtures" / "blockers"
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "_shared" / "blocker.schema.json"


def _get_blocker_files() -> list[Path]:
    return sorted(_BLOCKERS_DIR.glob("*.json"))


@pytest.mark.parametrize("blocker_path", _get_blocker_files(), ids=lambda p: p.stem)
def test_blocker_validates_against_schema(blocker_path):
    pytest.importorskip("jsonschema")
    import jsonschema

    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(blocker_path) as f:
        blocker = json.load(f)

    jsonschema.validate(blocker, schema)


def test_schema_symlink_resolves():
    assert _SCHEMA_PATH.exists(), (
        f"blocker.schema.json not found at {_SCHEMA_PATH}"
    )


def test_all_have_mode():
    for bf in _get_blocker_files():
        with open(bf) as f:
            b = json.load(f)
        assert "mode" in b, f"{bf.name} missing 'mode'"
        assert b["mode"] in ("fatal", "recoverable"), f"{bf.name}: unexpected mode {b['mode']!r}"
