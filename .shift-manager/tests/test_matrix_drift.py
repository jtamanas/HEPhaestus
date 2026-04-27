"""S17: Bidirectional drift detection between matrix and SKILL.md files.

Per WS2 plan D9:
  1. Canonical section header set (7 headers)
  2. Tightened blocker-code regex: \\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]{2,}){2,}\\b
  3. Exclusion list for false positives

Forward drift (hard): SKILL.md mentions a code in canonical section, matrix omits → fail.
Inverse drift (warn): matrix cites evidence path that no longer contains the code → warn.
"""
from __future__ import annotations
import re
import sys
import warnings
from pathlib import Path
from typing import Set

import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))


# ── Canonical section headers (7 per plan D9) ─────────────────────────────
CANONICAL_HEADERS = {
    "## sharp edges",
    "## sharp edges & failure modes",
    "## sharp edges & gotchas",
    "## limits",
    "## known issues",
    "## failure modes",
    "## blocker codes",
}

# ── Tightened blocker-code regex ─────────────────────────────────────────────
# ≥3 underscored words, each segment ≥3 alphanumerics (uppercase-led)
BLOCKER_REGEX = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]{2,}){2,}\b")

# ── Exclusion list (false positives) ─────────────────────────────────────────
# These look like blocker codes but are not registered codes.
EXCLUSION_LIST = {
    "MG5_AMC_NLO",
    "WRITE_HIGGSBOUNDS_BLOCKS",
    "WRITE_CALCHEP_MDL",
    "LD_LIBRARY_PATH",
    "SARAH_4_15_3",
    "SARAH_BSM_GROUP",
    "MG5_DARK_SU",
    "SARAH_CHECK_MODEL",
    "UFO_FILE",
    "SLHA_2",
    "SLHA_SM_REF",
    "SARAH_WRITE_UFO",
    "SARAH_WRITE_CALCHEP",
    "SARAH_WRITE_SPHENO",
    "SARAH_CHECK_FILES",
}


def _find_skill_md_files() -> list[Path]:
    """Find all SKILL.md files in the plugins directory."""
    return list((REPO_ROOT / "plugins").rglob("SKILL.md"))


def _extract_blocker_codes_from_skill_md(path: Path) -> Set[str]:
    """Extract blocker codes from canonical sections of a SKILL.md file."""
    codes = set()
    content = path.read_text(errors="replace")
    lines = content.splitlines()

    in_canonical_section = False
    for line in lines:
        # Check for section headers
        stripped = line.strip().lower()
        if stripped.startswith("##"):
            in_canonical_section = stripped in CANONICAL_HEADERS
        if in_canonical_section:
            found = BLOCKER_REGEX.findall(line)
            for code in found:
                if code not in EXCLUSION_LIST:
                    codes.add(code)
    return codes


def _get_matrix_blocker_codes(constraints_data: dict) -> Set[str]:
    """Get all blocker codes referenced in the matrix."""
    codes = set()
    for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
        caps = prereq.get("capabilities")
        if not caps:
            continue
        for rule in _flatten_all(caps.get("support", [])):
            if "blocker" in rule:
                codes.add(rule["blocker"])
    return codes


def _get_catalog_codes(catalog_data: dict) -> Set[str]:
    """Get all codes in the blocker catalog."""
    return set(catalog_data["blockers"].keys())


def _flatten_all(rules: list) -> list:
    """Flatten and/or rules to leaf rules."""
    result = []
    for rule in rules:
        if "and" in rule:
            result.extend(_flatten_all(rule["and"]))
        elif "or" in rule:
            result.extend(_flatten_all(rule["or"]))
        else:
            result.append(rule)
    return result


@pytest.fixture(scope="module")
def constraints_data():
    return yaml.safe_load((SHARED / "constraints.yaml").read_text())


@pytest.fixture(scope="module")
def catalog_data():
    return yaml.safe_load((SHARED / "blocker_catalog.yaml").read_text())


def _get_ws2_owned_codes(catalog_data: dict) -> Set[str]:
    """Return codes owned by this workstream (owned_by: this-ws).

    Codes with owned_by != 'this-ws' (e.g. mirrored from dark-matter-constraints)
    are not required to appear in the matrix — they belong to the upstream SKILL.md.
    """
    return {
        code
        for code, entry in catalog_data["blockers"].items()
        if entry.get("owned_by") == "this-ws"
    }


class TestBidirectionalDrift:
    def test_forward_drift_skill_codes_in_matrix(self, constraints_data, catalog_data):
        """Forward drift (hard-error per plan D9): codes in SKILL.md canonical sections
        that are WS2-owned (owned_by: this-ws) must appear in the matrix support rules.

        Codes owned by dark-matter-constraints (owned_by != 'this-ws') are excluded —
        they live in the DMC SKILL.md and are never expected in this matrix.

        Also checks that all SKILL.md codes are registered in the catalog (belt+suspenders).
        """
        matrix_codes = _get_matrix_blocker_codes(constraints_data)
        catalog_codes = _get_catalog_codes(catalog_data)
        ws2_owned_codes = _get_ws2_owned_codes(catalog_data)
        skill_files = _find_skill_md_files()

        not_in_catalog = []
        in_catalog_not_matrix = []

        for skill_md in skill_files:
            codes = _extract_blocker_codes_from_skill_md(skill_md)
            for code in codes:
                # Belt+suspenders: every extracted code must be in catalog
                if code not in catalog_codes:
                    not_in_catalog.append(f"{skill_md.relative_to(REPO_ROOT)}: {code}")
                    continue
                # Forward drift: WS2-owned codes must also appear in the matrix
                if code in ws2_owned_codes and code not in matrix_codes:
                    in_catalog_not_matrix.append(f"{skill_md.relative_to(REPO_ROOT)}: {code}")

        assert not not_in_catalog, (
            "SKILL.md mentions codes not in blocker_catalog.yaml:\n"
            + "\n".join(not_in_catalog)
        )
        assert not in_catalog_not_matrix, (
            "SKILL.md mentions WS2-owned codes that are absent from the matrix support rules "
            "(plan D9 forward-drift violation):\n"
            + "\n".join(in_catalog_not_matrix)
        )

    def test_canonical_header_set_covers_existing_skills(self):
        """Verify at least one SKILL.md uses a canonical header."""
        skill_files = _find_skill_md_files()
        found_canonical = False
        for skill_md in skill_files:
            content = skill_md.read_text(errors="replace").lower()
            for header in CANONICAL_HEADERS:
                if header in content:
                    found_canonical = True
                    break
        assert found_canonical, "No SKILL.md files found with canonical section headers"

    def test_exclusion_list_contains_no_real_catalog_codes(self, catalog_data):
        """CQ8: No item in EXCLUSION_LIST should be a registered blocker code.

        The exclusion list is a false-positive suppressor — if an exclusion item
        is a real registered code, the drift check would silently miss drift on it.
        This test catches that accident.
        """
        catalog_codes = _get_catalog_codes(catalog_data)
        accidental_suppressions = [exc for exc in EXCLUSION_LIST if exc in catalog_codes]
        assert not accidental_suppressions, (
            "These items are in EXCLUSION_LIST but are also real catalog codes — "
            "they would be silently excluded from drift checks:\n"
            + "\n".join(accidental_suppressions)
        )
        assert len(EXCLUSION_LIST) > 5, "EXCLUSION_LIST should have at least 6 entries"

    def test_inverse_drift_evidence_paths(self, constraints_data, catalog_data):
        """Inverse drift (warn): matrix evidence paths should ideally still contain the blocker codes."""
        catalog_codes = _get_catalog_codes(catalog_data)
        warnings_found = []

        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in caps.get("support", []):
                evidence = rule.get("evidence", "")
                blocker = rule.get("blocker")
                if not evidence or not blocker:
                    continue
                # Extract path part
                path_part = evidence.split(":")[0].split("(")[0].split("§")[0].strip()
                if path_part and "/" in path_part:
                    full_path = REPO_ROOT / path_part
                    if full_path.exists():
                        content = full_path.read_text(errors="replace")
                        if blocker not in content:
                            warnings_found.append(
                                f"{prereq_id}: evidence '{path_part}' doesn't contain '{blocker}'"
                            )

        # Inverse drift is warning-only
        for msg in warnings_found:
            warnings.warn(f"[DRIFT#13] Possible inverse drift: {msg}", stacklevel=2)
        assert True  # warning tier only

    def test_matrix_codes_all_in_catalog(self, constraints_data, catalog_data):
        """Verify all matrix blocker codes appear in the catalog (cross-check with invariant #2)."""
        catalog_codes = _get_catalog_codes(catalog_data)
        matrix_codes = _get_matrix_blocker_codes(constraints_data)
        missing = matrix_codes - catalog_codes
        assert not missing, f"Matrix codes not in catalog: {missing}"
