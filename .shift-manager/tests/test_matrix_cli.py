"""S16: CLI subprocess tests for matrix_lookup.py.

Tests:
  - CLI runs without error for dark-su3
  - JSON output is valid JSON
  - JSON output contains verdicts_by_prereq + ranked_chains
  - ranked_chains structure is correct
  - Markdown output works
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
FIXTURES = Path(__file__).parent / "fixtures" / "matrix"


def run_cli(*args):
    """Run matrix_lookup.py CLI with the given args."""
    cmd = [
        sys.executable,
        str(SHARED / "matrix_lookup.py"),
    ] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    return result


class TestMatrixCLI:
    def test_cli_runs_for_dark_su3(self):
        """CLI runs without error for dark-su3."""
        result = run_cli(
            "--model", "dark-su3",
            "--observables", "relic", "dd", "id",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"

    def test_cli_json_is_valid(self):
        """CLI JSON output is valid JSON."""
        result = run_cli(
            "--model", "dark-su3",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert isinstance(data, dict)

    def test_cli_json_has_required_keys(self):
        """CLI JSON output has verdicts_by_prereq and ranked_chains."""
        result = run_cli(
            "--model", "dark-su3",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        data = json.loads(result.stdout)
        assert "verdicts_by_prereq" in data, "Missing verdicts_by_prereq"
        assert "ranked_chains" in data, "Missing ranked_chains"
        assert "fold_by_prereq" in data, "Missing fold_by_prereq"

    def test_cli_json_ranked_chains_are_lists(self):
        """ranked_chains entries are lists."""
        result = run_cli(
            "--model", "dark-su3",
            "--observables", "relic", "dd", "id",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        data = json.loads(result.stdout)
        for obs, chain in data["ranked_chains"].items():
            assert isinstance(chain, list), f"ranked_chains[{obs}] is not a list"

    def test_cli_singlet_doublet_json(self):
        """CLI works for singlet-doublet."""
        result = run_cli(
            "--model", "singlet-doublet",
            "--output", "json",
            "--axes-path", str(FIXTURES / "singlet_doublet_axes.yaml"),
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "verdicts_by_prereq" in data

    def test_cli_markdown_output(self):
        """Markdown output mode doesn't crash."""
        result = run_cli(
            "--model", "dark-su3",
            "--output", "md",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
        # Markdown output should start with #
        assert result.stdout.strip().startswith("#"), f"Expected markdown header, got: {result.stdout[:50]}"

    def test_cli_verdicts_include_maddm(self):
        """verdicts_by_prereq includes maddm (key prereq)."""
        result = run_cli(
            "--model", "dark-su3",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        data = json.loads(result.stdout)
        assert "maddm" in data["verdicts_by_prereq"], "maddm missing from verdicts"

    def test_cli_dsu3_analytic_backend_escape_hatch_role(self):
        """Plan S16 acceptance criterion: analytic_backend has escape_hatch role for relic.

        When WS4 registry is absent, analytic_backend is blocked (ANALYTIC_MODULE_MISSING)
        and therefore absent from ranked_chains.  The S16 acceptance criterion is that
        analytic_backend is *routed as the escape hatch when viable*.  We verify this
        via fold_by_prereq.analytic_backend.role.relic == escape_hatch — the structural
        claim, independent of registry presence.
        """
        result = run_cli(
            "--model", "dark-su3",
            "--observables", "relic", "dd", "id",
            "--output", "json",
            "--axes-path", str(FIXTURES / "dark_su3_axes.yaml"),
        )
        assert result.returncode == 0, f"CLI failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        fold = data.get("fold_by_prereq", {})
        backend_fold = fold.get("analytic_backend", {})
        role = backend_fold.get("role", {})
        assert role.get("relic") == "escape_hatch", (
            f"Plan S16: analytic_backend.role.relic should be escape_hatch "
            f"(structural claim, registry-independent), got: {role}"
        )
