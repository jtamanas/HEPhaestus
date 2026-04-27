#!/usr/bin/env python3
"""Validate ~/.config/hephaestus/config.json for the four tools /demo needs.

Called by /demo's preflight step. Prints one pass/fail line per tool; exits 0
iff all four tools validate cleanly.

Exit codes (bitfield so callers can see exactly which tools failed):
  0  all four tools OK
  1  wolfram failed
  2  sarah failed
  4  spheno failed
  8  mg5 failed
  16 config file missing or unreadable
  32 unexpected internal error (argparse/IO) OR verify-infra failure (B7 fix)

So e.g. exit 3 means wolfram AND sarah both failed.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


CONFIG_PATH = Path(
    os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
) / "hephaestus" / "config.json"

# tool -> (path_key, version_key, bitmask, human_label)
PATH_VER_MASK_LABEL: dict[str, tuple[str, str, int, str]] = {
    "wolfram": ("wolfram_engine_path", "wolfram_engine_version", 1, "Wolfram Engine"),
    "sarah":   ("sarah_path",          "sarah_version",          2, "SARAH"),
    "spheno":  ("spheno_path",         "spheno_version",         4, "SPheno"),
    "mg5":     ("madgraph_path",       "madgraph_version",       8, "MadGraph5_aMC@NLO"),
}

TOOL_ORDER = ["wolfram", "sarah", "spheno", "mg5"]

SCRIPT_FOR: dict[str, str] = {
    "wolfram": "install_wolfram.sh",
    "sarah":   "install_sarah.sh",
    "spheno":  "install_spheno.sh",
    "mg5":     "install_mg5.sh",
}

SCRIPTS_DIR = Path(
    os.environ.get("HEPPH_SCRIPTS_DIR", "") or str(Path(__file__).resolve().parent)
)  # override via HEPPH_SCRIPTS_DIR for testing

# Python-side timeout = shell timeout + 10 s slack.
PY_TIMEOUT_FOR: dict[str, int] = {"wolfram": 25, "sarah": 55, "spheno": 30, "mg5": 20}


def _run(cmd: list[str], timeout: float = 30.0) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return p.returncode, p.stdout, p.stderr
    except (FileNotFoundError, PermissionError) as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"


def verify_tool(tool: str, cfg: dict) -> dict:
    """Shell out to install_<tool>.sh verify and return the parsed payload dict.

    For not_configured (empty path), synthesises the payload in Python
    to avoid the ~30 ms subprocess overhead on the hot /demo startup path.
    """
    path_key, ver_key, _bitmask, _label = PATH_VER_MASK_LABEL[tool]
    path    = cfg.get(path_key, "") or ""
    version = cfg.get(ver_key, "")  or ""

    if not path:
        return {
            "schema_version": 1,
            "tool": tool, "ok": False, "status": "not_configured",
            "path": "", "version": "",
            "detail": f"{path_key} not set in config.json",
            "hints": [],
        }

    script = SCRIPTS_DIR / SCRIPT_FOR[tool]
    argv = [str(script), "verify", "--path", path, "--json"]
    if version:
        argv += ["--expected-version", version]
    if tool == "sarah":
        w = cfg.get("wolfram_engine_path", "") or ""
        if w:
            argv += ["--wolfram-path", w]

    rc, out, err = _run(argv, timeout=PY_TIMEOUT_FOR[tool])

    # Try to parse the last line of stdout as JSON.
    lines = out.strip().splitlines()
    payload = None
    if lines:
        try:
            payload = json.loads(lines[-1])
        except Exception:
            payload = None

    if payload is None:
        # Verify-infra failure: script missing, crash before emitting JSON,
        # timeout-kill with no prior JSON, etc.  → bit 32 (B7 fix).
        return {
            "schema_version": 1,
            "tool": tool, "ok": False, "status": "internal_error",
            "path": path, "version": version,
            "detail": f"{script.name} rc={rc}: {(err or out).strip()[:160]}",
            "hints": [],
        }

    # schema_version gate: unknown schema → treat as internal_error (plan-final §7.8)
    if payload.get("schema_version") != 1:
        return {
            "schema_version": 1,
            "tool": tool, "ok": False, "status": "internal_error",
            "path": path, "version": version,
            "detail": f"{script.name}: unsupported schema_version {payload.get('schema_version')!r}",
            "hints": [],
        }

    # Successful parse — trust the payload. (The shell is the truth-source.)
    return payload


def bitmask_for(tool: str) -> int:
    return {"wolfram": 1, "sarah": 2, "spheno": 4, "mg5": 8}[tool]


def update_exit_code(exit_code: int, payload: dict, tool: str) -> int:
    """Merge payload result into the running exit bitfield.

    B7 fix: internal_error → bit 32 only (NOT the tool's specific bit).
    All other non-ok statuses → tool's specific bit.
    """
    status = payload.get("status")
    if payload.get("ok"):
        return exit_code
    if status == "internal_error":
        return exit_code | 32  # maintenance failure
    # All other non-ok statuses map to the tool's specific bit.
    return exit_code | bitmask_for(tool)


def _human_line(tool: str, payload: dict) -> str:
    """Format a single human-readable status line per design-final §5.4."""
    _path_key, _ver_key, _bitmask, label = PATH_VER_MASK_LABEL[tool]
    status = payload.get("status", "")
    ok = payload.get("ok", False)
    version = payload.get("version", "") or ""
    expected_version = payload.get("expected_version", "") or ""
    detail = payload.get("detail", "") or ""

    # Version column: show drift as "vX -> Y on disk" for WARN
    if ok and expected_version and version != expected_version:
        # WARN: version drift (non-strict)
        ver_col = f"v{expected_version} -> {version} on disk"
        tag = "WARN"
        detail_text = detail if detail else "ok (version drift)"
    elif version:
        ver_col = f"v{version}"
        if ok:
            tag = "PASS"
        elif status == "not_configured":
            tag = "SKIP"
        elif status == "internal_error":
            tag = "INTERNAL ERROR"
        else:
            tag = "FAIL"
        detail_text = detail if detail else status
    else:
        ver_col = "v?"
        if ok:
            tag = "PASS"
        elif status == "not_configured":
            tag = "SKIP"
        elif status == "internal_error":
            tag = "INTERNAL ERROR"
        else:
            tag = "FAIL"
        detail_text = detail if detail else status

    # Column widths per plan-final §2.5 WS5-T2:
    #   status + 2 spaces, tool name: 22 chars, 1 space, version: 23 chars, detail: free
    # All tags have 2 spaces before the tool name (including INTERNAL ERROR).
    return f"{tag}  {label:<22} {ver_col:<23} {detail_text}"


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON report instead of human lines")
    ap.add_argument("--config", type=Path, default=CONFIG_PATH, help="config path")
    args = ap.parse_args()

    if not args.config.is_file():
        msg = f"config not found: {args.config}"
        if args.json:
            print(json.dumps({"ok": False, "error": msg}))
        else:
            print(f"FAIL: {msg}")
        return 16

    try:
        cfg = load_config(args.config)
    except (OSError, json.JSONDecodeError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"FAIL: {exc}")
        return 16

    exit_code = 0
    payloads = []

    for tool in TOOL_ORDER:
        payload = verify_tool(tool, cfg)
        payloads.append(payload)
        exit_code = update_exit_code(exit_code, payload, tool)

    if args.json:
        print(json.dumps({"ok": exit_code == 0, "tools": payloads}))
    else:
        for tool, payload in zip(TOOL_ORDER, payloads):
            print(_human_line(tool, payload))
        print(f"Config: {args.config}")
        if exit_code == 0:
            print("All tools OK.")
        else:
            print("One or more tools FAIL/INTERNAL ERROR.")

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"INTERNAL ERROR: {exc}", file=sys.stderr)
        sys.exit(32)
