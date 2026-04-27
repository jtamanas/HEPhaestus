"""
test_mg5.py — Tier-C contract tests for install_mg5.sh verify JSON output.

Mirrors WS1's test_wolfram.py pattern. Each case invokes install_mg5.sh verify
with a mock mg5_aMC binary, parses the one-line JSON stdout, and asserts both
the _schema contract and the tool-specific invariants.

Plan-final.md §2.2 cases: happy banner, stale banner, tier-2 disagreement.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Make _schema importable from the same directory.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from _schema import validate  # noqa: E402

# Path to the scripts directory.
# _HERE is .../scripts/tests/test_verify_contract/
# _HERE.parent.parent is .../scripts/
_SCRIPTS_DIR = _HERE.parent.parent
_MG5_SCRIPT = _SCRIPTS_DIR / "install_mg5.sh"


def _make_mock(tmp_path: Path, stdout: str, exit_code: int = 0) -> Path:
    """Create a mock mg5_aMC executable in tmp_path/bin/."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "mg5_aMC"
    stdout_escaped = stdout.replace("'", "'\\''")
    body = textwrap.dedent(f"""\
        #!/usr/bin/env bash
        printf '%s' '{stdout_escaped}'
        exit {exit_code}
    """)
    script.write_text(body)
    script.chmod(
        stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    )
    return script


def _run_verify(tmp_path: Path, extra_args: list[str]) -> tuple[int, dict]:
    """Run install_mg5.sh verify with extra_args; return (exit_code, parsed_json)."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")
    result = subprocess.run(
        ["bash", str(_MG5_SCRIPT), "verify"] + extra_args,
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = result.stdout.strip()
    assert stdout, (
        f"stdout was empty (exit {result.returncode}); stderr: {result.stderr[:400]}"
    )
    payload = json.loads(stdout)
    return result.returncode, payload


# ─────────────────────────────────────────────────────────────────────────────
# Case 1: happy banner → ok, version=3.5.6
# ─────────────────────────────────────────────────────────────────────────────

def test_happy_banner(tmp_path: Path) -> None:
    banner = "MadGraph5_aMC@NLO  v3.5.6\nUsage: mg5_aMC ...\n"
    mock = _make_mock(tmp_path, banner, exit_code=0)

    rc, payload = _run_verify(tmp_path, ["--path", str(mock)])

    assert rc == 0, f"Expected exit 0, got {rc}; payload={payload}"
    errors = validate(payload)
    assert errors == [], errors

    assert payload["tool"] == "mg5"
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["version"] == "3.5.6"


# ─────────────────────────────────────────────────────────────────────────────
# Case 2: stale banner (no MadGraph5_aMC@NLO) → installed_broken + hint
# ─────────────────────────────────────────────────────────────────────────────

def test_stale_banner(tmp_path: Path) -> None:
    banner = "Usage: mg5_aMC [options]\n"
    mock = _make_mock(tmp_path, banner, exit_code=0)

    rc, payload = _run_verify(tmp_path, ["--path", str(mock)])

    assert rc == 15, f"Expected exit 15, got {rc}; payload={payload}"
    errors = validate(payload)
    assert errors == [], errors

    assert payload["ok"] is False
    assert payload["status"] == "installed_broken"
    hint_codes = [h["code"] for h in payload.get("hints", [])]
    assert "mg5_version_probe_stale" in hint_codes, f"hint_codes={hint_codes}"


# ─────────────────────────────────────────────────────────────────────────────
# Case 3: tier-2 VERSION disagreement → ok, version from banner, detail notes both
# ─────────────────────────────────────────────────────────────────────────────

def test_tier2_version_disagreement(tmp_path: Path) -> None:
    banner = "MadGraph5_aMC@NLO  v3.5.6\nUsage: mg5_aMC ...\n"
    mock = _make_mock(tmp_path, banner, exit_code=0)
    # Place a VERSION file that disagrees with the banner.
    (tmp_path / "VERSION").write_text("3.5.7\n")

    rc, payload = _run_verify(tmp_path, ["--path", str(mock)])

    assert rc == 0, f"Expected exit 0, got {rc}; payload={payload}"
    errors = validate(payload)
    assert errors == [], errors

    assert payload["ok"] is True
    assert payload["status"] == "ok"
    # Banner version wins.
    assert payload["version"] == "3.5.6", f"version={payload['version']}"
    # Detail must note the discrepancy.
    detail = payload.get("detail", "")
    assert "3.5.6" in detail and "3.5.7" in detail, (
        f"detail should mention both versions but got: {detail!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Case 4: not_configured (no --path, no config) → exit 17
# ─────────────────────────────────────────────────────────────────────────────

def test_not_configured(tmp_path: Path) -> None:
    rc, payload = _run_verify(tmp_path, [])

    assert rc == 17, f"Expected exit 17, got {rc}; payload={payload}"
    errors = validate(payload)
    assert errors == [], errors

    assert payload["ok"] is False
    assert payload["status"] == "not_configured"


# ─────────────────────────────────────────────────────────────────────────────
# Case 5: bad path → exit 16, missing, hint=path_not_found
# ─────────────────────────────────────────────────────────────────────────────

def test_bad_path(tmp_path: Path) -> None:
    rc, payload = _run_verify(
        tmp_path, ["--path", "/does/not/exist/mg5_aMC"]
    )

    assert rc == 16, f"Expected exit 16, got {rc}; payload={payload}"
    errors = validate(payload)
    assert errors == [], errors

    assert payload["ok"] is False
    assert payload["status"] == "missing"
    hint_codes = [h["code"] for h in payload.get("hints", [])]
    assert "path_not_found" in hint_codes, f"hint_codes={hint_codes}"
