"""test_detector.py — detector unit tests (S3a/S3c).

Tests:
  S3a (initial 4):
    test_singlet_doublet_clear          — SD spec → CLEAR
    test_2hdma_halt_for_signoff         — 2HDM+a spec → HALT_FOR_SIGNOFF
    test_dsu3_route_to_analytic         — dark-su3 spec → ROUTE_TO_ANALYTIC
    test_synthetic_confining_hard_halt  — confining synthetic → HARD_HALT

  S3c (additional):
    test_lint_gate_fires_when_module_unjustified
    test_ws1_axis_input_path
    test_ws1_axis_fallback_when_none
    test_multi_component_recorded_in_evidence
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile

import pytest
import yaml

# ---------------------------------------------------------------------------
# Probe analytic_models/stub_unimplemented.py existence (Decision 8).
# This determines which lint_warnings assertion to use for 2HDM+a.
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
# tests/ -> analytic-exception-detector/ -> skills/ -> workflow/ -> plugins/ -> repo root
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent
_STUB_PATH = (
    _REPO_ROOT
    / "plugins" / "hep-ph-toolkit" / "skills" / "spheno-build"
    / "scripts" / "analytic_models" / "stub_unimplemented.py"
)
_STUB_EXISTS = _STUB_PATH.exists()

_SHARED_ASSETS = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "assets"
_DARK_SU3_SPEC = _SHARED_ASSETS / "dark_su3.yaml"
_TWO_HDMA_SPEC = _SHARED_ASSETS / "two_hdm_a.yaml"
_SINGLET_DOUBLET_SPEC = _SHARED_ASSETS / "_archive" / "singlet_doublet.yaml"
_CONFINING_SPEC = _HERE / "fixtures" / "confining_synthetic.yaml"

_REGISTRY_PATH = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)

# ---------------------------------------------------------------------------
# Import detector (this will FAIL until S3b creates the module — TDD red)
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = _HERE.parent / "scripts"
_DETECTOR_MODULE = _SCRIPTS_DIR / "detect_analytic_exception.py"


def _load_detector():
    """Load the detector module via importlib; raises ImportError if not yet implemented."""
    if not _DETECTOR_MODULE.exists():
        raise ImportError(
            f"detect_analytic_exception.py not yet implemented at {_DETECTOR_MODULE}"
        )
    spec = importlib.util.spec_from_file_location("detect_analytic_exception", _DETECTOR_MODULE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["detect_analytic_exception"] = mod
    spec.loader.exec_module(mod)
    return mod


_detector_mod = _load_detector()
detect = _detector_mod.detect
Verdict = _detector_mod.Verdict
SignalInputs = _detector_mod.SignalInputs


def _load_spec(path: pathlib.Path) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# S3a tests (initial 4)
# ---------------------------------------------------------------------------


def test_singlet_doublet_clear():
    """Singlet-doublet spec (SM-only gauge groups) → verdict CLEAR."""
    spec = _load_spec(_SINGLET_DOUBLET_SPEC)
    v = detect(spec, registry_path=_REGISTRY_PATH)
    assert v.verdict == "CLEAR", f"Expected CLEAR, got {v.verdict!r}. evidence={v.evidence}"
    assert v.disclosure_required is False
    assert v.exception_id is None


def test_2hdma_halt_for_signoff():
    """2HDM+a spec (SC_ANALYTIC_DECLARED=True, SC_ANALYTIC_MODULE_WIRED=False) → HALT_FOR_SIGNOFF."""
    spec = _load_spec(_TWO_HDMA_SPEC)
    v = detect(spec, registry_path=_REGISTRY_PATH)
    assert v.verdict == "HALT_FOR_SIGNOFF", (
        f"Expected HALT_FOR_SIGNOFF, got {v.verdict!r}. evidence={v.evidence}"
    )
    assert v.disclosure_required is False
    assert v.exception_id is None
    # Per Decision 8: conditional lint_warnings assertion
    if _STUB_EXISTS:
        assert "module_wired_without_declaration" in v.lint_warnings, (
            f"Expected 'module_wired_without_declaration' in lint_warnings when stub exists. "
            f"lint_warnings={v.lint_warnings}"
        )
    else:
        assert v.lint_warnings == [], (
            f"Expected empty lint_warnings when stub absent. lint_warnings={v.lint_warnings}"
        )


def test_dsu3_route_to_analytic():
    """Dark-su3 spec (SC_ANALYTIC_DECLARED=True, SC_ANALYTIC_MODULE_WIRED=True) → ROUTE_TO_ANALYTIC."""
    spec = _load_spec(_DARK_SU3_SPEC)
    v = detect(spec, registry_path=_REGISTRY_PATH)
    assert v.verdict == "ROUTE_TO_ANALYTIC", (
        f"Expected ROUTE_TO_ANALYTIC, got {v.verdict!r}. evidence={v.evidence}"
    )
    assert v.disclosure_required is True
    assert v.exception_id == "dsu3-002", (
        f"Expected exception_id 'dsu3-002', got {v.exception_id!r}"
    )
    assert v.analytic_module is not None


def test_synthetic_confining_hard_halt():
    """Confining synthetic spec (S_CONFINING_DARK via confining: true) → HARD_HALT."""
    spec = _load_spec(_CONFINING_SPEC)
    v = detect(spec, registry_path=_REGISTRY_PATH)
    assert v.verdict == "HARD_HALT", (
        f"Expected HARD_HALT, got {v.verdict!r}. evidence={v.evidence}"
    )
    assert v.disclosure_required is False
    assert v.exception_id is None


# ---------------------------------------------------------------------------
# S3c tests (additional edge cases)
# ---------------------------------------------------------------------------


def test_lint_gate_fires_when_module_unjustified():
    """Lint gate fires when SC_ANALYTIC_MODULE_WIRED=True but no structural signal fires.

    Build a synthetic spec with SC_ANALYTIC_DECLARED=True,
    backends.analytic_module pointing to dark_su3.py (which IS registered for
    dark-su3), but using a different model name so the registry entry doesn't
    match (model name mismatch → SC_ANALYTIC_MODULE_WIRED=False by registry check).

    Actually: use dark-su3 spec as base but create a temp registry entry for
    dark-su3 BUT with no structural signals in the spec (SM-only gauge groups).
    The lint gate fires when SC_ANALYTIC_MODULE_WIRED is True but no structural
    signal fires (synthesis §3.3 lint gate).

    Simplest approach: create a spec with SM-only gauge groups but
    backends.spectrum='analytic' and analytic_module pointing to dark_su3.py,
    then create a temp registry with an entry for that model name.
    """
    import tempfile

    # SM-only spec with analytic declared — no dark gauge groups
    synthetic_spec = {
        "spec_version": 1,
        "name": "sm_with_analytic_declared",
        "claim_source": "Test only",
        "gauge_groups": [
            {"symbol": "B",  "group": "U1",  "kind": "hypercharge"},
            {"symbol": "WB", "group": "SU2", "kind": "left"},
            {"symbol": "G",  "group": "SU3", "kind": "color"},
        ],
        "fermions": [],
        "scalars": [],
        "lagrangian": {"mass_terms": [], "yukawa_terms": [], "scalar_potential": []},
        "backends": {
            "spectrum": "analytic",
            "analytic_module": "analytic_models.dark_su3",  # real file in the repo
        },
        "outputs": ["ufo"],
    }

    # Create a temp registry that has an entry for "sm_with_analytic_declared"
    # referencing dark_su3.py as the analytic_module
    analytic_module_path = str(
        _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "spheno-build"
        / "scripts" / "analytic_models" / "dark_su3.py"
    )
    temp_registry_content = {
        "schema_version": 1,
        "disclosure_version": 1,
        "exceptions": [
            {
                "id": "sm-analytic-lint-001",
                "kind": "analytic",
                "model": "sm_with_analytic_declared",
                "status": "active",
                "analytic_module": str(
                    pathlib.Path("plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py")
                ),
                "signals_recorded": [],  # no signals — this is what triggers the lint gate
                "placements": {
                    "P1": "plugins/hep-ph-toolkit/skills/dark-matter-constraints/SKILL.md",
                    "P2": "plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md",
                    "P3": "plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/dark_su3.py",
                },
                "banner": (
                    "**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (sm-analytic-lint-001).** "
                    "Test lint gate. "
                    "MUST embed this banner verbatim — do not silently strip it.\n"
                ),
                "deprecated_in": None,
                "retired_in": None,
            }
        ],
        "proxy_runs": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml as _yaml
        _yaml.dump(temp_registry_content, f, allow_unicode=True)
        temp_reg_path = pathlib.Path(f.name)

    try:
        v = detect(synthetic_spec, registry_path=temp_reg_path)
        # SC_ANALYTIC_DECLARED=True, SC_ANALYTIC_MODULE_WIRED=True (file exists + registry entry),
        # but no structural signal fires → ROUTE_TO_ANALYTIC with lint_warning
        assert v.verdict == "ROUTE_TO_ANALYTIC", (
            f"Expected ROUTE_TO_ANALYTIC for SM-only spec with analytic declared+wired. "
            f"Got {v.verdict!r}"
        )
        assert "analytic_module_without_structural_justification" in v.lint_warnings, (
            f"Expected lint_warning 'analytic_module_without_structural_justification'. "
            f"lint_warnings={v.lint_warnings}"
        )
    finally:
        temp_reg_path.unlink(missing_ok=True)


def test_ws1_axis_input_path():
    """WS1 axis inputs produce same verdict as direct ModelSpec inspection for dark-su3."""
    spec = _load_spec(_DARK_SU3_SPEC)
    ws1_inputs = SignalInputs(
        gauge_extension_class="dark",
        dm_candidate_uv_provenance="broken_generator",
        stabilizing_symmetry=None,
        raw_modelspec=spec,
    )
    v = detect(spec, signal_inputs=ws1_inputs, registry_path=_REGISTRY_PATH)
    assert v.verdict == "ROUTE_TO_ANALYTIC", (
        f"WS1 input path: expected ROUTE_TO_ANALYTIC, got {v.verdict!r}"
    )


def test_ws1_axis_fallback_when_none():
    """signal_inputs=None falls back to direct ModelSpec inspection for dark-su3."""
    spec = _load_spec(_DARK_SU3_SPEC)
    v = detect(spec, signal_inputs=None, registry_path=_REGISTRY_PATH)
    assert v.verdict == "ROUTE_TO_ANALYTIC", (
        f"Direct inspection fallback: expected ROUTE_TO_ANALYTIC, got {v.verdict!r}"
    )


def test_multi_component_recorded_in_evidence():
    """evidence['multi_component'] is populated; verdict is independent of its value."""
    spec = _load_spec(_DARK_SU3_SPEC)
    v = detect(spec, registry_path=_REGISTRY_PATH)
    assert "multi_component" in v.evidence, (
        f"Expected 'multi_component' in evidence. evidence={v.evidence}"
    )
    # Verdict is ROUTE_TO_ANALYTIC regardless of multi_component value
    assert v.verdict == "ROUTE_TO_ANALYTIC"
