"""
Tests for tools/check_plan.py (T-SF-8).
Covers ≥10 cases: 3 per rule + integration + fixture tests.
"""
import pathlib
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECK_PLAN = REPO_ROOT / "tools" / "check_plan.py"
FIXTURES_DIR = REPO_ROOT / "tools" / "tests" / "fixtures"
SHARED_DIR = REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared"


def run_check(args: list, input_text: str = None) -> subprocess.CompletedProcess:
    if input_text is not None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(input_text)
            tmp_path = f.name
        args = [str(CHECK_PLAN)] + args + [tmp_path]
    else:
        args = [str(CHECK_PLAN)] + args
    return subprocess.run(
        [sys.executable] + args,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# R-1 tests: jq filter path vs schema
# ---------------------------------------------------------------------------

def test_r1_fires_on_provenance_in_summary(tmp_path):
    """R-1: .provenance.run_id in summary.json should fire."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "```bash\n"
        "jq -e '.provenance.run_id == $rid' summary.json\n"
        "```\n"
        "Also check provenance.json exists.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-1" in result.stderr
    assert "provenance" in result.stderr
    assert "summary.json" in result.stderr


def test_r1_fires_on_unknown_top_key(tmp_path):
    """R-1: .nonexistent_key in summary.json should fire."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "```bash\n"
        "jq -e '.nonexistent_key == 42' summary.json\n"
        "```\n"
        "Also check provenance.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-1" in result.stderr


def test_r1_passes_on_valid_summary_path(tmp_path):
    """R-1: .model and .omega_h2 not in summary core — .omega_h2 would fail but .model is valid."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "```bash\n"
        "# fixture: plugins/hep-ph-toolkit/skills/singlet-doublet/benchmarks/canonical-2026/expectations.json\n"
        "jq -e '.model == \"singlet-doublet\"' summary.json\n"
        "```\n"
        "Also check provenance.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    # .model is a valid top-level key in core schema
    assert "R-1" not in result.stderr or "model" not in result.stderr


def test_r1_passes_on_provenance_json_filter(tmp_path):
    """R-1: jq filter on provenance.json (not summary.json) is not checked."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "```bash\n"
        "jq -e '.run_id == $rid' provenance.json\n"
        "```\n"
        "Also check summary.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    # R-1 only checks summary.json; provenance.json filter should not trigger R-1
    assert "R-1" not in result.stderr


# ---------------------------------------------------------------------------
# R-2 tests: schema purity
# ---------------------------------------------------------------------------

def test_r2_passes_on_core_summary_schema():
    """R-2: core summary schema must be purity-clean."""
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(SHARED_DIR / "summary.core.schema.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "[PASS]" in result.stdout


def test_r2_passes_on_provenance_schema():
    """R-2: provenance schema must be purity-clean."""
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(SHARED_DIR / "provenance.schema.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "[PASS]" in result.stdout


def test_r2_would_fail_on_polluted_schema(tmp_path):
    """R-2: R-2 check triggers when plan references a schema path containing bbx."""
    # R-2 checks the actual shared schemas for channel token pollution.
    # Simulate a plan that, when run, would have the shared schema emit R-2 if polluted.
    # Since the actual shared schemas are clean, verify R-2 import works correctly.
    import sys
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from check_plan import LintResult, check_r2
    import importlib

    result = LintResult()
    # Write a temp schema with a bbx token and test check_r2 directly
    import json
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "bbx_fraction": {"type": "number"}
        }
    }
    schema_path = tmp_path / "polluted.schema.json"
    schema_path.write_text(json.dumps(schema, indent=2))
    check_r2(schema_path, result)
    assert len(result.violations) > 0
    assert any("R-2" in v[0] for v in result.violations)


# ---------------------------------------------------------------------------
# R-3 tests: fixture citation for numeric thresholds
# ---------------------------------------------------------------------------

def test_r3_fires_on_omega_h2_without_citation(tmp_path):
    """R-3: omega_h2 == 0.292 without fixture citation should fire."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "Check omega_h2 == 0.292 is in band.\n"
        "Also check provenance.json.\n"
        "Also check summary.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-3" in result.stderr


def test_r3_passes_with_fixture_citation(tmp_path):
    """R-3: omega_h2 with fixture citation 3 lines above should pass."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "# fixture: plugins/hep-ph-toolkit/skills/singlet-doublet/benchmarks/canonical-2026/expectations.json\n"
        "Check omega_h2 == 0.292 is in band.\n"
        "Also check provenance.json and summary.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert "R-3" not in result.stderr


def test_r3_fires_on_threshold_without_citation(tmp_path):
    """R-3: fraction threshold 0.909 without citation should fire."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "Check fraction >= 0.909 passes.\n"
        "Also check provenance.json and summary.json.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-3" in result.stderr


# ---------------------------------------------------------------------------
# R-4 tests: atomic-write coupling
# ---------------------------------------------------------------------------

def test_r4_fires_when_summary_without_provenance(tmp_path):
    """R-4: task block with summary.json but no provenance.json should fire."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "Check that summary.json exists and is valid.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-4" in result.stderr


def test_r4_passes_when_both_asserted(tmp_path):
    """R-4: task block with both summary.json and provenance.json should pass R-4."""
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## T-1\n"
        "Check that summary.json and provenance.json both exist.\n"
    )
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(plan)],
        capture_output=True, text=True
    )
    # R-4 should not fire
    assert "R-4" not in result.stderr


# ---------------------------------------------------------------------------
# Integration tests: fixture files
# ---------------------------------------------------------------------------

def test_integration_buggy_fixture_fails():
    """Integration: plan-with-bug.md must exit non-zero with R-1 error."""
    fixture = FIXTURES_DIR / "plan-with-bug.md"
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(fixture)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "R-1" in result.stderr
    assert "provenance" in result.stderr
    assert "summary.json" in result.stderr


def test_integration_amended_fixture_passes():
    """Integration: plan-amended.md must exit 0."""
    fixture = FIXTURES_DIR / "plan-amended.md"
    result = subprocess.run(
        [sys.executable, str(CHECK_PLAN), str(fixture)],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "[PASS]" in result.stdout
