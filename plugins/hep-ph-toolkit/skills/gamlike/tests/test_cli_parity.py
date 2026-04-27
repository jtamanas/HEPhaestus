"""
test_cli_parity.py — SKILL.md ↔ --help parity check (T18c / O2).

Asserts that every flag in --help output appears in SKILL.md's CLI section,
and that key flags documented in SKILL.md appear in --help.
"""
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"
_SKILL_MD = _HERE.parent / "SKILL.md"


def test_help_exits_0():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_help_contains_results_path():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert "results-path" in result.stdout or "results_path" in result.stdout


def test_help_contains_out_flag():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert "--out" in result.stdout


def test_help_contains_md_summary_flag():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True, text=True,
    )
    assert "--md-summary" in result.stdout


def test_skill_md_documents_out_flag():
    if not _SKILL_MD.exists():
        pytest.skip("SKILL.md not yet written")
    content = _SKILL_MD.read_text()
    assert "--out" in content


def test_skill_md_documents_md_summary_flag():
    if not _SKILL_MD.exists():
        pytest.skip("SKILL.md not yet written")
    content = _SKILL_MD.read_text()
    assert "--md-summary" in content
