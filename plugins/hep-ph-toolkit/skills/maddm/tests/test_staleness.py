"""test_staleness.py — Task 1b: loud frozen-SI staleness guard.

Covers:
  * detector fires on the frozen sentinel value;
  * detector fires on bit-identical SI across genuinely different params;
  * detector stays SILENT on a responsive / changed SI;
  * the emitted blocker validates against blocker.schema.json;
  * MADDM_STALE_DD_RESULT exists in blocker_catalog.yaml.

FAILS if the staleness guard (staleness.py) or its catalog entry is reverted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import staleness

_HERE = Path(__file__).parent.resolve()
_SHARED = _HERE.parents[1] / "_shared"
_SCHEMA = _SHARED / "blocker.schema.json"
_CATALOG = _SHARED / "blocker_catalog.yaml"

SENTINEL = 2.4258097266847696e-31


# ── Detector: positive cases ────────────────────────────────────────────────

def test_fires_on_frozen_sentinel():
    b = staleness.detect_stale_dd(SENTINEL)
    assert b is not None
    assert b["code"] == "MADDM_STALE_DD_RESULT"
    assert b["mode"] == "recoverable"
    assert "frozen_sentinel" in b["context"]["reasons"]
    assert b["context"]["si_value"] == SENTINEL
    assert "fresh" in b["user_instruction"].lower()


def test_sentinel_constant_matches_documented_value():
    assert staleness.FROZEN_SI_SENTINEL == SENTINEL
    assert staleness.is_frozen_sentinel(SENTINEL)


def test_fires_on_bit_identical_across_different_params():
    """Same SI, different param-card hashes → stale (unresponsive)."""
    si = 7.68e-45
    b = staleness.detect_stale_dd(
        si,
        previous_si=si,
        previous_params_hash="hashA",
        current_params_hash="hashB",
    )
    assert b is not None
    assert "unresponsive_to_param_change" in b["context"]["reasons"]
    assert b["context"]["responded_to_param_change"] is False


# ── Detector: negative (silent) cases ───────────────────────────────────────

def test_silent_on_responsive_si():
    """SI changed when params changed → no staleness."""
    b = staleness.detect_stale_dd(
        9.0e-45,
        previous_si=7.68e-45,
        previous_params_hash="hashA",
        current_params_hash="hashB",
    )
    assert b is None


def test_silent_on_identical_si_same_params():
    """Bit-identical SI but SAME param hash is not staleness — genuine repeat."""
    si = 7.68e-45
    b = staleness.detect_stale_dd(
        si,
        previous_si=si,
        previous_params_hash="hashA",
        current_params_hash="hashA",
    )
    assert b is None


def test_silent_on_plain_value_no_history():
    """A normal SI with no previous run and not the sentinel → silent."""
    assert staleness.detect_stale_dd(7.68e-45) is None


# ── emit / check_and_emit ───────────────────────────────────────────────────

def test_check_and_emit_writes_stderr_when_stale(capsys):
    b = staleness.check_and_emit(SENTINEL)
    assert b is not None
    err = capsys.readouterr().err
    payload = json.loads(err.strip().splitlines()[-1])
    assert payload["code"] == "MADDM_STALE_DD_RESULT"


def test_check_and_emit_silent_when_responsive(capsys):
    b = staleness.check_and_emit(9.0e-45, previous_si=7.68e-45,
                                 previous_params_hash="a",
                                 current_params_hash="b")
    assert b is None
    assert capsys.readouterr().err.strip() == ""


# ── Blocker validates against schema ────────────────────────────────────────

def _load_schema():
    return json.loads(_SCHEMA.read_text())


def test_emitted_blocker_validates_against_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = _load_schema()
    b = staleness.detect_stale_dd(SENTINEL)
    jsonschema.validate(b, schema)  # raises on failure


def test_blocker_manual_shape():
    """Schema-independent guard: required fields + SCREAMING_SNAKE code."""
    import re
    b = staleness.detect_stale_dd(SENTINEL)
    for k in ("code", "mode", "message"):
        assert k in b and b[k]
    assert re.match(r"^[A-Z][A-Z0-9_]+$", b["code"])
    assert b["mode"] == "recoverable"


# ── Catalog registration ────────────────────────────────────────────────────

def test_catalog_has_stale_dd_entry():
    yaml = pytest.importorskip("yaml")
    cat = yaml.safe_load(_CATALOG.read_text())
    entry = cat["blockers"].get("MADDM_STALE_DD_RESULT")
    assert entry is not None, "MADDM_STALE_DD_RESULT missing from blocker_catalog.yaml"
    assert entry["severity"] == "recoverable"
    assert "maddm" in entry["emitted_by"]
    # class must be in the closed catalog enum
    allowed = {
        "missing-skill", "missing-tool-feature", "fundamental-group-theory-gap",
        "regime-mismatch", "spec-authoring-gap", "informational",
        "analytic-exception",
    }
    assert entry["class"] in allowed
