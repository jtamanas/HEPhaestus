"""
test_dd_expansion_structure.py — plain-environment (NO Wolfram) structural tests
for the box DD-expansion (sd_dd_expansion.wl) wiring and guards.  These keep the
default suite meaningful: they assert the module is committed, correctly wired
into run_eval_sd.wls, that the loud guards + blocker-catalog entries exist, and
that triangle-continuity holds BY CONSTRUCTION (the expansion touches only D0i
box heads, never the C0i/B0i triangle/bubble heads).

Everything here is source/registry inspection — no kernel required — so a wrong
wiring surfaces in the default `python -m pytest` run, not only under the gated
HEPPH_RUN_WOLFRAM_TESTS smoke.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
SHARED_DIR = TESTS_DIR.parent.parent / "_shared"
REPO_ROOT = TESTS_DIR.parent.parent.parent.parent.parent
DESIGN_DOC = REPO_ROOT / "eval" / "2506.19062_wimps_blind_spots" / "DESIGN-ITEM4.md"

MODULE = SCRIPTS_DIR / "sd_dd_expansion.wl"
DRIVER = SCRIPTS_DIR / "run_eval_sd.wls"
CHECK_RUNNER = SCRIPTS_DIR / "run_dd_expansion_check.wls"
CATALOG = SHARED_DIR / "blocker_catalog.yaml"


def _read(p: Path) -> str:
    return p.read_text()


# ---------------------------------------------------------------- assets present
def test_module_and_runner_committed():
    assert MODULE.exists(), "sd_dd_expansion.wl must be committed"
    assert CHECK_RUNNER.exists(), "run_dd_expansion_check.wls (A1-V runner) must be committed"


def test_design_doc_committed():
    """DESIGN-ITEM4.md is part of this PR (like STEP3-DESIGN.md was)."""
    assert DESIGN_DOC.exists(), "DESIGN-ITEM4.md must be committed into the eval dir"
    txt = _read(DESIGN_DOC)
    for decision in ("Decision A1", "Decision A2", "Decision A3", "Decision A6"):
        assert decision in txt, f"{decision} missing from committed design doc"


# ---------------------------------------------------------------- module content
def test_module_defines_reduction_api():
    src = _read(MODULE)
    for sym in ("boxGram", "boxCollinearOffsets", "boxDegeneracyMonitor",
                "ddIntOffsetExact", "ddTraceScalar", "ddBoxHead", "ddExpandRule",
                "ddTensorSurvivors", "ddBoxSectorClean", "ddMonitorSummary",
                "writeAmpDdSidecar", "ddCentralDeriv"):
        assert sym in src, f"sd_dd_expansion.wl must define {sym}"


def test_module_reads_no_looptools_symbol_at_read_time():
    """The header contract: the file Get[]s cleanly; it must NOT Install LoopTools
    or Needs FormCalc itself (the common include does that first)."""
    src = _read(MODULE)
    # actual install/needs CALLS take an argument; the header comment mentions
    # "Install[]ed" in prose, which must not trip this.
    assert "Install[$" not in src and 'Install["' not in src, \
        "module must not Install LoopTools (driver/common does)"
    assert 'Needs["FormCalc`"]' not in src, "module must not Needs FormCalc"


def test_expand_rule_touches_only_boxes_triangle_continuity_by_construction():
    """Triangle-continuity (validation #2), proven structurally: the expansion
    rewrite is exactly `D0i -> ddBoxHead`, so C0i (triangle) and B0i (bubble) heads
    — which carry the item-3 triangle-only content C_scalar = -1.28e-7 — are left
    byte-identical.  A rewrite that also matched C0i/B0i would break this."""
    src = _read(MODULE)
    assert "ddExpandRule = D0i -> ddBoxHead" in src, \
        "ddExpandRule must rewrite ONLY the box head D0i -> ddBoxHead"
    # the scalar box passes through; only tensor ids are reduced
    assert "ddBoxHead[dd0, args__] := D0i[dd0, args]" in src, \
        "dd0 (scalar box) must pass through untouched"


# ---------------------------------------------------------------- driver wiring
def test_driver_loads_module_and_applies_expansion():
    src = _read(DRIVER)
    assert 'Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]]' in src, \
        "run_eval_sd.wls must Get[] sd_dd_expansion.wl"
    assert "ddExpandRule" in src, "driver must apply the ddExpandRule interception"
    assert "$ddExpansion" in src, "driver must gate the expansion on $ddExpansion"


def test_driver_emits_incomplete_guard_and_exits_3():
    src = _read(DRIVER)
    assert "SD-DD-EXPANSION-INCOMPLETE" in src, "driver must emit the structural guard marker"
    assert "ddTensorSurvivors[Mnum]" in src, "guard must check survivors on the evaluated amp"
    # the guard must be a hard exit-3 (nothing ships)
    idx = src.index("SD-DD-EXPANSION-INCOMPLETE")
    assert "Exit[3]" in src[idx:idx + 2000], "SD-DD-EXPANSION-INCOMPLETE must Exit[3]"


def test_driver_writes_sidecar_and_gram_monitor():
    src = _read(DRIVER)
    assert "writeAmpDdSidecar" in src, "driver must persist the amp_dd.m sidecar (Decision A3)"
    assert "amp_dd.m" in src, "sidecar filename must be amp_dd.m"
    assert "GRAM-MONITOR" in src, "driver must emit the Gram/degeneracy monitor line"
    assert '"dd_expansion"' in src, "eval output metadata must carry a dd_expansion block"


# ---------------------------------------------------------------- blocker catalog
@pytest.fixture(scope="module")
def catalog():
    return yaml.safe_load(_read(CATALOG))["blockers"]


@pytest.mark.parametrize("code", ["SD_DD_EXPANSION_INCOMPLETE", "SD_DD_DERIVATIVE_NONCONVERGENT"])
def test_blocker_entries_registered_and_well_shaped(catalog, code):
    assert code in catalog, f"{code} must be registered in blocker_catalog.yaml"
    entry = catalog[code]
    for field in ("class", "severity", "description", "owned_by"):
        assert field in entry, f"{code} missing required field {field}"
    assert entry["owned_by"] == "looptools"
    assert entry["severity"] == "recoverable", "a loud, recoverable blocker (nothing ships)"
    assert "looptools" in entry["emitted_by"]


def test_incomplete_blocker_description_names_the_mechanism(catalog):
    desc = catalog["SD_DD_EXPANSION_INCOMPLETE"]["description"]
    assert "Gram" in desc and "rank-1" in desc, \
        "the blocker description must name the Gram-pole / rank-1 mechanism"
