"""Tier-1 — every /looptools blocker fixture validates against blocker.schema.json.

Mirrors micromegas/tests/test_blocker_shape.py.
"""
import json
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_BLOCKERS_DIR = Path(__file__).resolve().parent / "fixtures" / "blockers"
_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "_shared" / "blocker.schema.json"


def _get_blocker_files() -> list[Path]:
    return sorted(_BLOCKERS_DIR.glob("*.json"))


def test_schema_present():
    assert _SCHEMA_PATH.exists(), f"blocker.schema.json not found at {_SCHEMA_PATH}"


def test_at_least_one_blocker():
    assert _get_blocker_files(), "no blocker fixtures found"


@pytest.mark.parametrize("blocker_path", _get_blocker_files(), ids=lambda p: p.stem)
def test_blocker_validates_against_schema(blocker_path):
    pytest.importorskip("jsonschema")
    import jsonschema

    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(blocker_path) as f:
        blocker = json.load(f)

    jsonschema.validate(blocker, schema)


def test_all_have_valid_mode():
    for bf in _get_blocker_files():
        b = json.loads(bf.read_text())
        assert b.get("mode") in ("fatal", "recoverable"), f"{bf.name}: bad mode {b.get('mode')!r}"


def test_codes_in_looptools_namespace():
    allowed = {
        "LOOPTOOLS_INPUT_MISSING", "LOOPTOOLS_NOT_CONFIGURED",
        "LOOPTOOLS_MATHLINK_UNAVAILABLE", "WOLFRAM_KERNEL_ABSENT",
        "LOOPTOOLS_META_INCOMPATIBLE", "LOOPTOOLS_DRIVER_FAILED",
        "LOOPTOOLS_AMPLITUDE_NONFINITE", "LOOPTOOLS_SCHEMA_INVALID",
        "LOOPTOOLS_MASS_DEGENERATE", "LOOPTOOLS_EVAL_NO_OUTPUT",
    }
    for bf in _get_blocker_files():
        code = json.loads(bf.read_text())["code"]
        assert code in allowed, f"{bf.name}: code {code!r} not a known runtime blocker"
