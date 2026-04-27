"""
Shared JSON schema for install_<tool>.sh verify stdout.

Lifted verbatim from design-final.md §2.2 / §2.3 / §2.4.

Usage:
    from _schema import validate
    errors = validate(payload_dict)
    assert errors == [], errors
"""

from __future__ import annotations

# ── Enumerations ──────────────────────────────────────────────────────────────

TOOL_ENUM = {"wolfram", "sarah", "spheno", "mg5"}

STATUS_ENUM = {
    "ok",
    "not_configured",
    "missing",
    "installed_broken",
    "version_mismatch",
    "timeout",
    "internal_error",
}

HINT_CODE_ENUM = {
    "kernel_init_m_path",
    "wolfram_not_activated",
    "wolfram_engine_missing",
    "shared_library_missing",
    "mg5_version_probe_stale",
    "disk_full",
    "path_not_found",
}

# ── Required / forbidden keys ─────────────────────────────────────────────────

# Keys that must always be present.
REQUIRED_KEYS = {"schema_version", "tool", "ok", "status", "path", "version", "detail"}

# Keys whose presence is conditional (validated separately).
CONDITIONAL_KEYS = {"expected_version"}

# Keys that must never appear (privacy / leakage concerns — design-final §2.2).
FORBIDDEN_KEYS = {"probe"}


# ── Validator ─────────────────────────────────────────────────────────────────

def validate(payload: dict) -> list[str]:
    """Validate a parsed verify JSON payload.

    Returns a list of error strings (empty list means valid).
    Accepts both snake_case and the design-final field names.
    """
    errors: list[str] = []

    # 1. Required keys present.
    for key in REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"Missing required key: {key!r}")

    # 2. Forbidden keys absent.
    for key in FORBIDDEN_KEYS:
        if key in payload:
            errors.append(f"Forbidden key present: {key!r}")

    # 3. schema_version == 1.
    sv = payload.get("schema_version")
    if sv is not None and sv != 1:
        errors.append(f"schema_version must be 1, got {sv!r}")

    # 4. tool is in TOOL_ENUM.
    tool = payload.get("tool")
    if tool is not None and tool not in TOOL_ENUM:
        errors.append(f"tool {tool!r} not in {sorted(TOOL_ENUM)}")

    # 5. ok is bool.
    ok = payload.get("ok")
    if ok is not None and not isinstance(ok, bool):
        errors.append(f"ok must be bool, got {type(ok).__name__}")

    # 6. status is in STATUS_ENUM.
    status = payload.get("status")
    if status is not None and status not in STATUS_ENUM:
        errors.append(f"status {status!r} not in {sorted(STATUS_ENUM)}")

    # 7. ok must be True iff status == "ok".
    if ok is not None and status is not None:
        expected_ok = status == "ok"
        if ok != expected_ok:
            errors.append(
                f"ok={ok!r} inconsistent with status={status!r} "
                f"(expected ok={expected_ok})"
            )

    # 8. path is string.
    path = payload.get("path")
    if path is not None and not isinstance(path, str):
        errors.append(f"path must be str, got {type(path).__name__}")

    # 9. version is string.
    version = payload.get("version")
    if version is not None and not isinstance(version, str):
        errors.append(f"version must be str, got {type(version).__name__}")

    # 10. expected_version: if present must be string.
    ev = payload.get("expected_version")
    if ev is not None and not isinstance(ev, str):
        errors.append(f"expected_version must be str, got {type(ev).__name__}")

    # 11. detail is string, ≤200 chars, no newlines.
    detail = payload.get("detail")
    if detail is not None:
        if not isinstance(detail, str):
            errors.append(f"detail must be str, got {type(detail).__name__}")
        else:
            if len(detail) > 200:
                errors.append(f"detail exceeds 200 chars (len={len(detail)})")
            if "\n" in detail:
                errors.append("detail must not contain newlines")

    # 12. hints: if present, must be list of {code, message} dicts with code in HINT_CODE_ENUM.
    hints = payload.get("hints")
    if hints is not None:
        if not isinstance(hints, list):
            errors.append(f"hints must be list, got {type(hints).__name__}")
        else:
            for i, hint in enumerate(hints):
                if not isinstance(hint, dict):
                    errors.append(f"hints[{i}] must be dict, got {type(hint).__name__}")
                    continue
                if "code" not in hint:
                    errors.append(f"hints[{i}] missing 'code'")
                elif hint["code"] not in HINT_CODE_ENUM:
                    errors.append(
                        f"hints[{i}].code {hint['code']!r} not in {sorted(HINT_CODE_ENUM)}"
                    )
                if "message" not in hint:
                    errors.append(f"hints[{i}] missing 'message'")
                elif not isinstance(hint["message"], str):
                    errors.append(
                        f"hints[{i}].message must be str, got {type(hint['message']).__name__}"
                    )

    # 13. duration_ms: if present, must be int >= 0.
    duration_ms = payload.get("duration_ms")
    if duration_ms is not None:
        if not isinstance(duration_ms, int):
            errors.append(f"duration_ms must be int, got {type(duration_ms).__name__}")
        elif duration_ms < 0:
            errors.append(f"duration_ms must be >= 0, got {duration_ms}")

    return errors
