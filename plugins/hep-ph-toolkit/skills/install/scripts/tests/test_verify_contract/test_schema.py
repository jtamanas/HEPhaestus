"""
Smoke tests for _schema.validate.

Proves the harness is importable and the validator accepts a known-good
payload before any tool-specific tests land in WS1-WS4.
"""

from __future__ import annotations

from _schema import validate


VALID_PAYLOAD = {
    "schema_version": 1,
    "tool": "wolfram",
    "ok": True,
    "status": "ok",
    "path": "/usr/local/bin/wolframscript",
    "version": "14.1.0",
    "detail": "probe returned 4; version extracted",
    "hints": [],
    "duration_ms": 312,
}


def test_valid_payload_passes():
    errors = validate(VALID_PAYLOAD)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_ok_false_not_configured():
    payload = {
        "schema_version": 1,
        "tool": "sarah",
        "ok": False,
        "status": "not_configured",
        "path": "",
        "version": "",
        "detail": "no path supplied and no config entry found",
    }
    errors = validate(payload)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_forbidden_probe_key_rejected():
    payload = dict(VALID_PAYLOAD)
    payload["probe"] = "/usr/local/bin/wolframscript -code Print[2+2]"
    errors = validate(payload)
    assert any("probe" in e for e in errors), f"Expected probe to be rejected, got: {errors}"


def test_invalid_status_rejected():
    payload = dict(VALID_PAYLOAD, status="bogus_status")
    # ok=True but status is not "ok" → two errors (unknown status + ok inconsistency)
    errors = validate(payload)
    assert len(errors) >= 1, f"Expected at least one error, got: {errors}"


def test_hint_unknown_code_rejected():
    payload = dict(VALID_PAYLOAD)
    payload["hints"] = [{"code": "unknown_hint_code", "message": "something"}]
    errors = validate(payload)
    assert any("hints" in e for e in errors), f"Expected hint code error, got: {errors}"
