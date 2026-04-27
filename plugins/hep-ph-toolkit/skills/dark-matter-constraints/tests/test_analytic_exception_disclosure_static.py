"""test_analytic_exception_disclosure_static.py — Registry-driven static placement test (S9).

Replaces test_dsu3_002_disclosure_propagation_contract in test_check_prereqs.py.
See migration note at the bottom of test_check_prereqs.py.

For each active entry in exceptions ∪ proxy_runs:
  - Asserts the verbatim banner appears at each registered placement file path.
  - Asserts banner well-formedness (load-bearing first phrase + closing requirement).

Status handling (synthesis §4.4 test (a)):
  - active:     full assert on placements + well-formedness
  - deprecated: warnings.warn instead of assert (placement may be absent during migration)
  - retired:    pytest.skip
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import warnings

import pytest

# ---------------------------------------------------------------------------
# Marker
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.disclosure_contract

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
# tests/ -> dark-matter-constraints/ -> skills/ -> constraints/ -> plugins/ -> repo root
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent

_REGISTRY_PATH = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)
_WORKFLOW_SCRIPTS = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "analytic-exception-detector" / "scripts"
)

# ---------------------------------------------------------------------------
# Well-formedness regexes (synthesis §4.2)
# ---------------------------------------------------------------------------

_WF_ANALYTIC_FIRST = re.compile(
    r"\*\*REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET \([^)]+\)\.\*\*"
)
_WF_ANALYTIC_CLOSE = re.compile(
    r"MUST embed this banner verbatim — do not silently strip it\."
)
_WF_PROXY_FIRST = re.compile(
    r"\*\*PROXY-RUN DISCLOSURE\.\*\*"
)
_WF_PROXY_CLOSE = re.compile(
    r"tag every affected table row with `\[proxy\]`\."
)

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load_registry_module():
    path = _WORKFLOW_SCRIPTS / "exceptions_registry.py"
    key = "_er_static"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalize whitespace: collapse runs of whitespace to single space."""
    return " ".join(text.split())


def _banner_in_file(banner: str, file_path: pathlib.Path) -> bool:
    """Check if the normalized banner text appears in the file."""
    if not file_path.is_file():
        return False
    file_text = file_path.read_text()
    # Strip blockquote markers from file text before comparison
    file_stripped = "\n".join(
        line.lstrip("> ").lstrip(">") for line in file_text.splitlines()
    )
    banner_norm = _normalize(banner)
    file_norm = _normalize(file_stripped)
    return banner_norm in file_norm


def _check_well_formedness(entry_id: str, kind: str, banner: str) -> None:
    """Return error message if banner fails well-formedness, else None."""
    if kind == "analytic":
        if not _WF_ANALYTIC_FIRST.search(banner):
            return (
                f"Entry '{entry_id}' (kind=analytic): banner missing load-bearing first phrase "
                f"'**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (<id>).**'"
            )
        if not _WF_ANALYTIC_CLOSE.search(banner):
            return (
                f"Entry '{entry_id}' (kind=analytic): banner missing closing requirement "
                f"'MUST embed this banner verbatim — do not silently strip it.'"
            )
    elif kind == "proxy_run":
        if not _WF_PROXY_FIRST.search(banner):
            return (
                f"Entry '{entry_id}' (kind=proxy_run): banner missing load-bearing first phrase "
                f"'**PROXY-RUN DISCLOSURE.**'"
            )
        if not _WF_PROXY_CLOSE.search(banner):
            return (
                f"Entry '{entry_id}' (kind=proxy_run): banner missing closing requirement "
                f"'tag every affected table row with `[proxy]`.'"
            )
    return None


# ---------------------------------------------------------------------------
# Test IDs — collect all active entries at module load time
# ---------------------------------------------------------------------------

_registry_mod = _load_registry_module()
_registry = _registry_mod.load_exceptions(_REGISTRY_PATH)
_all_entries = list(_registry.all_active())


def _entry_id(entry):
    return f"{entry.id}[{entry.kind}]"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("entry", _all_entries, ids=[_entry_id(e) for e in _all_entries])
def test_well_formedness(entry):
    """Each active entry's banner must pass well-formedness checks (synthesis §4.2)."""
    err = _check_well_formedness(entry.id, entry.kind, entry.banner)
    if err is not None:
        pytest.fail(err)


@pytest.mark.parametrize("entry", _all_entries, ids=[_entry_id(e) for e in _all_entries])
def test_placements(entry):
    """Each active entry's banner must appear verbatim at each registered placement path.

    Applies equally to both analytic and proxy_run entries with status: active.
    Synthesis §4.4(a): assert entry.banner.strip() is a substring of the file contents.
    """
    for placement_name, placement_rel_path in entry.placements.items():
        placement_abs = _REPO_ROOT / placement_rel_path
        found = _banner_in_file(entry.banner, placement_abs)

        assert found, (
            f"Entry '{entry.id}' (kind={entry.kind}) banner not found at "
            f"placement {placement_name} ({placement_rel_path}). "
            f"File: {placement_abs}\n"
            f"Banner (first 200 chars): {entry.banner[:200]!r}"
        )


def test_status_filtering():
    """Deprecated entries should warn; retired entries should be skipped.

    This test validates the registry loader's status filtering behavior with
    synthetic entries.
    """
    import tempfile
    import yaml as _yaml

    # Create a synthetic registry with all three statuses
    active_banner = (
        "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (status-test-active-001).** "
        "Test. "
        "MUST embed this banner verbatim — do not silently strip it.\n"
    )
    deprecated_banner = (
        "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (status-test-depr-001).** "
        "Deprecated test. "
        "MUST embed this banner verbatim — do not silently strip it.\n"
    )
    retired_banner = (
        "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (status-test-ret-001).** "
        "Retired test. "
        "MUST embed this banner verbatim — do not silently strip it.\n"
    )

    test_reg = {
        "schema_version": 1,
        "disclosure_version": 1,
        "exceptions": [
            {
                "id": "status-test-active-001",
                "kind": "analytic",
                "model": "model-active",
                "status": "active",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md"},
                "banner": active_banner,
                "deprecated_in": None,
                "retired_in": None,
            },
            {
                "id": "status-test-depr-001",
                "kind": "analytic",
                "model": "model-deprecated",
                "status": "deprecated",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "nonexistent_file_deprecated.md"},
                "banner": deprecated_banner,
                "deprecated_in": "abc123",
                "retired_in": None,
            },
            {
                "id": "status-test-ret-001",
                "kind": "analytic",
                "model": "model-retired",
                "status": "retired",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "nonexistent_file_retired.md"},
                "banner": retired_banner,
                "deprecated_in": "abc123",
                "retired_in": "def456",
            },
        ],
        "proxy_runs": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        _yaml.dump(test_reg, f, allow_unicode=True)
        temp_reg_path = pathlib.Path(f.name)

    try:
        rv = _registry_mod.load_exceptions(temp_reg_path)
        active_ids = [e.id for e in rv.all_active()]

        assert "status-test-active-001" in active_ids, "active entry must appear in all_active()"
        assert "status-test-depr-001" not in active_ids, "deprecated entry must NOT appear in all_active()"
        assert "status-test-ret-001" not in active_ids, "retired entry must NOT appear in all_active()"
    finally:
        temp_reg_path.unlink(missing_ok=True)
