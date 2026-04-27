"""test_exceptions_registry.py — unit tests for the registry loader (S2).

Tests:
  test_loader_parses_seed         — seed registry has ≥1 active analytic + ≥1 proxy_run
  test_by_id_lookup               — by_id('dsu3-002').banner contains REGRESSION-ANCHOR ONLY
  test_by_model_lookup            — by_model('dark-su3') returns dsu3-002 entry
  test_by_kind_filter             — by_kind('analytic') ≥1; by_kind('proxy_run') ≥1
  test_well_formedness_negative_case — malformed banner → ExceptionRegistryMalformed
  test_status_filter              — all_active() excludes deprecated + retired entries
"""
from __future__ import annotations

import pathlib
import textwrap

import pytest
import yaml

# Path constants — inlined to avoid package-namespace collision between test dirs
_HERE_REG = pathlib.Path(__file__).parent
_REPO_ROOT_REG = _HERE_REG.parent.parent.parent.parent.parent
_REGISTRY_PATH = (
    _REPO_ROOT_REG / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)

# ---------------------------------------------------------------------------
# Import loader (module under test)
# ---------------------------------------------------------------------------

import importlib.util
import sys

_SCRIPTS_DIR = pathlib.Path(__file__).parent.parent / "scripts"
_REGISTRY_MODULE = _SCRIPTS_DIR / "exceptions_registry.py"

_spec = importlib.util.spec_from_file_location("exceptions_registry", _REGISTRY_MODULE)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["exceptions_registry"] = _mod
_spec.loader.exec_module(_mod)
load_exceptions = _mod.load_exceptions
ExceptionRegistryMalformed = _mod.ExceptionRegistryMalformed


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_loader_parses_seed():
    """Seed registry must have ≥1 active analytic and ≥1 active proxy_run entry."""
    rv = load_exceptions(_REGISTRY_PATH)
    active = list(rv.all_active())
    analytic_active = [e for e in active if e.kind == "analytic"]
    proxy_active = [e for e in active if e.kind == "proxy_run"]
    assert len(analytic_active) >= 1, "Expected ≥1 active analytic entry in seed registry"
    assert len(proxy_active) >= 1, "Expected ≥1 active proxy_run entry in seed registry"

    # dsu3-002 should be accessible
    entry = rv.by_id("dsu3-002")
    assert entry is not None, "dsu3-002 not found in registry"
    # Well-formedness already enforced by loader; no assertion needed here


def test_by_id_lookup():
    """by_id('dsu3-002').banner must contain 'REGRESSION-ANCHOR ONLY'."""
    rv = load_exceptions(_REGISTRY_PATH)
    entry = rv.by_id("dsu3-002")
    assert entry is not None
    assert "REGRESSION-ANCHOR ONLY" in entry.banner


def test_by_model_lookup():
    """by_model('dark-su3') must return the dsu3-002 entry."""
    rv = load_exceptions(_REGISTRY_PATH)
    results = rv.by_model("dark-su3")
    assert len(results) >= 1
    ids = [e.id for e in results]
    assert "dsu3-002" in ids


def test_by_kind_filter():
    """by_kind('analytic') and by_kind('proxy_run') must each return ≥1 entry."""
    rv = load_exceptions(_REGISTRY_PATH)
    analytic = rv.by_kind("analytic")
    proxy = rv.by_kind("proxy_run")
    assert len(analytic) >= 1
    assert len(proxy) >= 1


def test_well_formedness_negative_case(tmp_path: pathlib.Path):
    """A registry with a malformed banner must raise ExceptionRegistryMalformed
    with the entry id in the message."""
    bad_registry = tmp_path / "bad_exceptions.yaml"
    bad_content = {
        "schema_version": 1,
        "disclosure_version": 1,
        "exceptions": [
            {
                "id": "bad-model-001",
                "kind": "analytic",
                "model": "bad-model",
                "status": "active",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {
                    "P1": "plugins/hep-ph-toolkit/skills/dark-matter-constraints/SKILL.md",
                    "P2": "plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md",
                },
                # MALFORMED: missing load-bearing first phrase AND closing requirement
                "banner": "This is a malformed banner without the required phrases.\n",
                "deprecated_in": None,
                "retired_in": None,
            }
        ],
        "proxy_runs": [],
    }
    with open(bad_registry, "w") as fh:
        yaml.dump(bad_content, fh, allow_unicode=True)

    with pytest.raises(ExceptionRegistryMalformed) as exc_info:
        load_exceptions(bad_registry)

    assert "bad-model-001" in str(exc_info.value), (
        f"Expected entry id 'bad-model-001' in exception message, got: {exc_info.value}"
    )


def test_status_filter(tmp_path: pathlib.Path):
    """all_active() must exclude deprecated and retired entries."""
    test_registry = tmp_path / "status_test.yaml"
    content = {
        "schema_version": 1,
        "disclosure_version": 1,
        "exceptions": [
            {
                "id": "active-001",
                "kind": "analytic",
                "model": "model-a",
                "status": "active",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "some/file.md"},
                "banner": (
                    "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (active-001).** "
                    "Test active entry. "
                    "MUST embed this banner verbatim — do not silently strip it.\n"
                ),
                "deprecated_in": None,
                "retired_in": None,
            },
            {
                "id": "deprecated-001",
                "kind": "analytic",
                "model": "model-b",
                "status": "deprecated",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "some/file.md"},
                "banner": (
                    "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (deprecated-001).** "
                    "Test deprecated entry. "
                    "MUST embed this banner verbatim — do not silently strip it.\n"
                ),
                "deprecated_in": "abc1234",
                "retired_in": None,
            },
            {
                "id": "retired-001",
                "kind": "analytic",
                "model": "model-c",
                "status": "retired",
                "analytic_module": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                "signals_recorded": ["S_GAUGE_DARK_NONABELIAN"],
                "placements": {"P1": "some/file.md"},
                "banner": (
                    "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (retired-001).** "
                    "Test retired entry. "
                    "MUST embed this banner verbatim — do not silently strip it.\n"
                ),
                "deprecated_in": "abc1234",
                "retired_in": "def5678",
            },
        ],
        "proxy_runs": [],
    }
    with open(test_registry, "w") as fh:
        yaml.dump(content, fh, allow_unicode=True)

    rv = load_exceptions(test_registry)
    active_ids = [e.id for e in rv.all_active()]
    assert "active-001" in active_ids
    assert "deprecated-001" not in active_ids
    assert "retired-001" not in active_ids
