"""S11c: Warning-tier invariants (#13, #14, #15).

These tests warn but do NOT fail the build.

#13 Inverse drift: for each matrix rule with evidence: <path>:L<n>, the path
    should exist on disk.
#14 match: "*" forward-compat: rules using match:"*" without match_all_current_values
    should warn.
#15 Observable coverage: every non-placeholder observable has at least one primary
    or escape_hatch prereq.
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path

import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))


@pytest.fixture(scope="module")
def constraints_data():
    return yaml.safe_load((SHARED / "constraints.yaml").read_text())


def _all_leaf_rules(caps: dict):
    for rule in caps.get("support", []):
        yield from _flatten_leaf(rule)


def _flatten_leaf(rule: dict):
    if "and" in rule:
        for sub in rule["and"]:
            yield from _flatten_leaf(sub)
    elif "or" in rule:
        for sub in rule["or"]:
            yield from _flatten_leaf(sub)
    else:
        yield rule


class TestWarningTierInvariants:
    def test_invariant_13_inverse_drift_evidence_paths_exist(self, constraints_data):
        """#13: For each evidence: path, the referenced file should exist on disk.

        Missing evidence path → warning (not failure).
        """
        missing_paths = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_leaf_rules(caps):
                evidence = rule.get("evidence", "")
                if not evidence:
                    continue
                # Extract file path from evidence string (strip :Ln suffixes and descriptions)
                # Evidence format: "path/to/file:line-range (description)" or "path/to/file §N"
                path_part = evidence.split(":")[0].split("(")[0].split("§")[0].strip()
                if path_part and "/" in path_part:
                    full_path = REPO_ROOT / path_part
                    # Only warn; don't fail
                    if not full_path.exists():
                        missing_paths.append(f"{prereq_id}: evidence path '{path_part}' not found")

        if missing_paths:
            for msg in missing_paths:
                warnings.warn(f"[INV#13] Possible inverse drift: {msg}", stacklevel=2)
        # Test always passes (warning tier)
        assert True

    def test_invariant_14_wildcard_match_forward_compat(self, constraints_data):
        """#14: Rules using match:"*" without match_all_current_values: true → warn."""
        missing_annotation = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_leaf_rules(caps):
                if rule.get("match") == "*" and not rule.get("match_all_current_values"):
                    missing_annotation.append(
                        f"{prereq_id}: axis={rule.get('axis')} has match:'*' "
                        f"without match_all_current_values:true"
                    )

        if missing_annotation:
            for msg in missing_annotation:
                warnings.warn(f"[INV#14] Forward-compat annotation missing: {msg}", stacklevel=2)
        # Test always passes (warning tier)
        assert True

    def test_invariant_15_observable_coverage(self, constraints_data):
        """#15: Every non-placeholder observable has ≥1 primary or escape_hatch prereq."""
        observables_cfg = constraints_data.get("constraints", {})
        prereqs = constraints_data.get("prereqs", {})
        uncovered = []

        for obs_id, obs_cfg in observables_cfg.items():
            if obs_cfg.get("placeholder"):
                continue
            # Check for primary or escape_hatch role
            has_primary = any(
                prereq.get("capabilities", {}).get("role", {}).get(obs_id) in ("primary", "escape_hatch")
                for prereq in prereqs.values()
                if prereq.get("capabilities")
            )
            if not has_primary:
                uncovered.append(obs_id)

        if uncovered:
            for obs in uncovered:
                warnings.warn(
                    f"[INV#15] Observable '{obs}' has no primary or escape_hatch prereq",
                    stacklevel=2
                )
        # Test always passes (warning tier)
        assert True
