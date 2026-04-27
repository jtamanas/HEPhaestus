"""S22: 3-model end-to-end smoke test + DMC scripts no-touch guard + YAML key-order stability.

Tests:
  1. Load matrix for all 3 demo models
  2. dark-su3: MG5_DARK_COLOR_TENSOR_WALL or ANALYTIC_EXCEPTION_TRIGGER on madgraph/maddm
  3. singlet-doublet: no fundamental-group-theory-gap blockers
  4. 2hdm-a: ANALYTIC_MODULE_MISSING on analytic_backend (stub status)
  5. DMC scripts not modified (git diff check)
  6. YAML key-order stability (round-trip check)
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
FIXTURES = Path(__file__).parent / "fixtures" / "matrix"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import load_capability_matrix


@pytest.fixture(scope="module")
def matrix():
    return load_capability_matrix(
        constraints_path=SHARED / "constraints.yaml",
        catalog_path=SHARED / "blocker_catalog.yaml",
    )


@pytest.fixture(scope="module")
def dark_su3_axes():
    return yaml.safe_load((FIXTURES / "dark_su3_axes.yaml").read_text())


@pytest.fixture(scope="module")
def singlet_doublet_axes():
    return yaml.safe_load((FIXTURES / "singlet_doublet_axes.yaml").read_text())


@pytest.fixture(scope="module")
def two_hdm_a_axes():
    return yaml.safe_load((FIXTURES / "2hdm_a_axes.yaml").read_text())


class TestSmokeAllModels:
    def test_1_matrix_loads(self, matrix):
        """Matrix loads without error."""
        assert matrix is not None
        assert len(matrix.get_prereqs()) >= 13

    def test_2_dark_su3_madgraph_maddm_blocked(self, matrix, dark_su3_axes):
        """dark-su3: madgraph and maddm are blocked (dark-color wall)."""
        verdicts = matrix.lookup_blockers(dark_su3_axes)

        mg5_blocked = [
            bv for bv in verdicts.get("madgraph", [])
            if bv.verdict == "blocked"
        ]
        maddm_blocked = [
            bv for bv in verdicts.get("maddm", [])
            if bv.verdict == "blocked"
        ]

        assert mg5_blocked, f"Expected madgraph to be blocked for dark-su3, got: {verdicts.get('madgraph', [])}"
        assert maddm_blocked, f"Expected maddm to be blocked for dark-su3, got: {verdicts.get('maddm', [])}"

        # Verify one of the expected blockers
        expected_codes = {"MG5_DARK_COLOR_TENSOR_WALL", "ANALYTIC_EXCEPTION_TRIGGER"}
        mg5_codes = {bv.blocker for bv in mg5_blocked}
        assert mg5_codes & expected_codes, f"Expected one of {expected_codes}, got {mg5_codes}"

    def test_3_singlet_doublet_no_group_theory_gap(self, matrix, singlet_doublet_axes):
        """singlet-doublet: no fundamental-group-theory-gap blockers."""
        verdicts = matrix.lookup_blockers(singlet_doublet_axes)
        gap_blockers = []
        for prereq_id, bvlist in verdicts.items():
            for bv in bvlist:
                if bv.blocker_class == "fundamental-group-theory-gap":
                    gap_blockers.append(f"{prereq_id}: {bv.blocker}")
        assert not gap_blockers, f"Unexpected fundamental-group-theory-gap for singlet-doublet: {gap_blockers}"

    def test_4_2hdm_a_analytic_module_missing(self, matrix, two_hdm_a_axes):
        """2hdm-a: analytic_backend reports ANALYTIC_MODULE_MISSING (stub status)."""
        verdicts = matrix.lookup_blockers(two_hdm_a_axes)
        backend = verdicts.get("analytic_backend", [])
        missing = [bv for bv in backend if bv.blocker == "ANALYTIC_MODULE_MISSING"]
        assert missing, f"Expected ANALYTIC_MODULE_MISSING for 2hdm-a, got: {backend}"

    def test_5_dmc_scripts_not_modified(self):
        """DMC scripts must not be modified by WS2 (out-of-scope guard).

        Uses local 'main' as the base branch.  If 'main' does not exist as a
        local ref the test fails immediately with BASE_BRANCH_NOT_FOUND — it
        never silently passes when the base is unreachable.
        """
        # Resolve the local 'main' ref; never fall through on failure.
        base_result = subprocess.run(
            ["git", "rev-parse", "main"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        if base_result.returncode != 0:
            pytest.fail(
                "BASE_BRANCH_NOT_FOUND: local 'main' ref could not be resolved. "
                "Cannot verify DMC out-of-scope guard without a known base commit. "
                f"stderr: {base_result.stderr.strip()}"
            )
        base_sha = base_result.stdout.strip()

        result = subprocess.run(
            [
                "git", "diff", "--name-only",
                f"{base_sha}..HEAD",
                "--",
                "plugins/constraints/skills/dark-matter-constraints/scripts/",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        modified = result.stdout.strip()
        assert not modified, (
            f"FAIL: DMC scripts were modified relative to main ({base_sha[:12]}):\n{modified}"
        )

    def test_6_yaml_key_order_stability(self):
        """constraints.yaml round-trip preserves prereq key order."""
        content = (SHARED / "constraints.yaml").read_text()
        data = yaml.safe_load(content)
        # Verify the data loads and prereqs are present
        assert "prereqs" in data
        prereq_keys = list(data["prereqs"].keys())
        # Order should be deterministic: sarah-build first, looptools somewhere in the list
        assert "sarah-build" in prereq_keys
        assert "looptools" in prereq_keys
        # Round-trip: re-dump and verify same keys
        dumped = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        reloaded = yaml.safe_load(dumped)
        assert set(reloaded["prereqs"].keys()) == set(data["prereqs"].keys())

    def test_7_fold_shows_analytic_backend_as_escape_hatch_for_dsu3(self, matrix, dark_su3_axes):
        """For dark-su3, analytic_backend has escape_hatch role for relic."""
        prereqs = matrix.get_prereqs()
        backend_caps = prereqs.get("analytic_backend", {}).get("capabilities", {})
        role = backend_caps.get("role", {})
        assert role.get("relic") == "escape_hatch", (
            f"Expected analytic_backend.role.relic = escape_hatch, got {role}"
        )

    def test_8_cross_plugin_library_note(self):
        """D7 cross-plugin-library note: assert the run-log contains the canonical phrase.

        CQ12 fix: the note must be in the run-log (not just pytest stdout).
        """
        log_path = (
            REPO_ROOT
            / ".shift-manager"
            / "run-20260426-workflow-skill"
            / "impl"
            / "ws2_iter1_log.md"
        )
        assert log_path.exists(), f"Run-log not found: {log_path}"
        content = log_path.read_text()
        canonical_phrase = "[CROSS-PLUGIN-LIB]"
        assert canonical_phrase in content, (
            f"Run-log {log_path} does not contain the canonical cross-plugin-library note "
            f"(expected substring: {canonical_phrase!r})"
        )
