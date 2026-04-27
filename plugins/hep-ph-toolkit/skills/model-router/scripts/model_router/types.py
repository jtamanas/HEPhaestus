"""
model_router/types.py — all dataclasses and exception classes for WS3.

stdlib only: dataclasses, typing. No Pydantic.

WS4 re-export contract (manager D4): try-import ExceptionVerdict and SignalInputs
from WS4's detect_analytic_exception module; on ImportError, define local stubs
matching WS4 §3.4 verdict shape (per plan critique S4 — commit to re-export-with-stub-fallback).
"""
from __future__ import annotations

import sys
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# WS4 re-export with local stub fallback (per plan S4 + critique S4)
# ---------------------------------------------------------------------------

def _ws4_path() -> pathlib.Path:
    """Return the path prefix for WS4 analytic-exception-detector scripts."""
    # Relative to this file: scripts/model_router/types.py
    # WS4 scripts live at: plugins/hep-ph-toolkit/skills/analytic-exception-detector/scripts/
    _here = pathlib.Path(__file__).resolve()
    _plugin_root = _here.parents[4]  # plugins/hep-ph-toolkit/ (post-consolidation)
    return _plugin_root / "skills" / "analytic-exception-detector" / "scripts"


_ws4_scripts = _ws4_path()
if str(_ws4_scripts) not in sys.path:
    sys.path.insert(0, str(_ws4_scripts))

try:
    from detect_analytic_exception import Verdict as ExceptionVerdict, SignalInputs  # type: ignore
    _WS4_AVAILABLE = True
except ImportError:
    _WS4_AVAILABLE = False

    @dataclass
    class SignalInputs:
        """Stub matching WS4 §3.4 SignalInputs shape."""
        gauge_extension_class: Optional[str] = None
        dm_candidate_uv_provenance: Optional[str] = None
        stabilizing_symmetry: Optional[str] = None
        raw_modelspec: Optional[dict] = None
        analytic_module_status: Optional[str] = None

    @dataclass
    class ExceptionVerdict:
        """Stub matching WS4 §3.4 Verdict shape (four verdicts)."""
        verdict: str = "CLEAR"  # CLEAR | ROUTE_TO_ANALYTIC | HALT_FOR_SIGNOFF | HARD_HALT
        exception_id: Optional[str] = None
        disclosure_required: bool = False
        rationale: Optional[str] = None
        detector_unavailable: bool = False


# ---------------------------------------------------------------------------
# Router option types
# ---------------------------------------------------------------------------

@dataclass
class RouterOptions:
    """Options passed through the pipeline from the CLI / public API."""
    strict: bool = False
    output: str = "md"           # "md" | "json" | "both"
    output_dir: Optional[str] = None
    config_path: Optional[str] = None
    explain: Optional[str] = None   # prereq-id for --explain flag
    user_preferences: Optional[Dict[str, int]] = None  # {prereq_id: priority; lower wins}


# ---------------------------------------------------------------------------
# P0 output
# ---------------------------------------------------------------------------

@dataclass
class LoadedContext:
    """Output of stage_p0_load."""
    model_id: str
    observables: List[str]
    options: RouterOptions
    model_meta: dict             # constraints.yaml models.<model_id> block
    model_spec: dict             # parsed ModelSpec YAML
    prereqs: dict                # constraints.yaml prereqs block (all)
    constraints_raw: dict        # full constraints.yaml
    blocker_catalog: dict        # blocker_catalog.yaml (may be {})
    analytic_exceptions: dict    # analytic_exceptions.yaml (may be {})
    config: dict                 # ~/.config/hephaestus/config.json (may be {})
    absent_registries: List[str] = field(default_factory=list)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# P1 output
# ---------------------------------------------------------------------------

@dataclass
class CandidateSpec:
    """Single DM candidate extracted from the model spec."""
    name: str
    field_type: Optional[str] = None
    mediator_regime: Optional[str] = None
    uv_provenance: Optional[str] = None


@dataclass
class AxisBundle:
    """
    Output of stage_p1_validate_and_extract — the eight WS1 taxonomy axes
    plus derived model-level properties.
    """
    # WS1 A1-A8 axes (raw values from taxonomy.read_axes)
    A1: Optional[str] = None    # gauge extension class
    A2: Optional[str] = None    # dark gauge group ordinal
    A3: Optional[Dict] = None   # fermion structure dict
    A4: Optional[Dict] = None   # scalar sector dict
    A5: Optional[str] = None    # DM type
    A6: Optional[str] = None    # mediator regime
    A7: Optional[str] = None    # collider signature class
    A8: Optional[str] = None    # model lifecycle (active | archived)

    # DM candidates (parsed from dm_phenomenology.candidates[])
    candidates: List[CandidateSpec] = field(default_factory=list)

    # Derived model-level properties (computed by P1 adapter)
    model_props: Dict[str, Any] = field(default_factory=dict)
    # model_props["analytic_module_status"] — six-value closed enum (synthesis D6)

    # Axis extraction diagnostics (missing axes, coercion warnings)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# P3 output
# ---------------------------------------------------------------------------

@dataclass
class PrereqFold:
    """Per-prereq matrix verdict for a single observable."""
    prereq_id: str
    overall_verdict: str         # supported | supported_with_caveat | blocked | not_applicable
    blockers: List[str] = field(default_factory=list)
    blocker_classes: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    role_for_observable: str = "none"   # primary | validator | specialty | escape_hatch | none
    priority_tiebreak: int = 100
    runtime_install_required: bool = False
    no_coverage: bool = False    # True if no matrix rule matched the model's axes


@dataclass
class MatrixVerdicts:
    """Output of stage_p3_matrix_lookup — per-prereq verdicts for each observable."""
    by_observable: Dict[str, List[PrereqFold]] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# P4 output
# ---------------------------------------------------------------------------

@dataclass
class ActiveChain:
    """The selected active tool chain for one observable (or per-candidate)."""
    prereq_id: str               # winning prereq's ID, or "analytic_backend", or "BLOCKED"
    role: str                    # primary | validator | specialty | escape_hatch | BLOCKED
    status: str                  # ROUTED | BLOCKED | HALT | HARD_HALT
    blockers: List[str] = field(default_factory=list)
    blocker_classes: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    runtime_install_required: bool = False
    matrix_acknowledgement_missing: bool = False


@dataclass
class PerCandidateRouting:
    """Per-candidate chain inside ROUTE_TO_ANALYTIC (synthesis Decision 1)."""
    candidate_name: str
    candidate_field_type: Optional[str] = None
    candidate_mediator_regime: Optional[str] = None
    candidate_uv_provenance: Optional[str] = None
    active_chain: Optional[ActiveChain] = None
    expected_observable_label: str = ""


@dataclass
class ObservableRouting:
    """Per-observable composed routing result."""
    observable: str
    status: str                  # ROUTED | BLOCKED | HALT | HARD_HALT | PLACEHOLDER
    active_chain: Optional[ActiveChain] = None
    ranked_alternatives: List[ActiveChain] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    blocker_classes: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)
    per_candidate: List[PerCandidateRouting] = field(default_factory=list)
    matrix_acknowledgement_warnings: List[str] = field(default_factory=list)


@dataclass
class BlockerVerdict:
    """Structured blocker entry for JSON output."""
    code: str
    blocker_class: str           # missing-skill | missing-tool-feature | fundamental-group-theory-gap | regime-mismatch | spec-authoring-gap | analytic-exception
    prereq_id: str
    observable: str
    description: Optional[str] = None
    workaround: Optional[str] = None
    follow_up: Optional[str] = None


@dataclass
class ComposedRouting:
    """Output of stage_p4_compose_and_rank — full per-observable results.

    axes_snapshot: optional AxisBundle carried through P4 so the renderer can
    emit `axis_snapshot` into the JSON report without an extra plumbing arg.
    Per iter-3 review recommendation: consistent with how exception_verdict
    is carried (D1).
    """
    model_id: str
    observables: List[str]
    exception_verdict: Optional[ExceptionVerdict] = None
    exception_verdict_by_observable: Dict[str, ExceptionVerdict] = field(default_factory=dict)
    per_observable: Dict[str, ObservableRouting] = field(default_factory=dict)
    all_blockers: List[BlockerVerdict] = field(default_factory=list)
    exit_code: int = 0
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    axes_snapshot: Optional["AxisBundle"] = None


# ---------------------------------------------------------------------------
# P5 output
# ---------------------------------------------------------------------------

@dataclass
class Placement:
    """A single banner or prompt placement in the Markdown output (synthesis Decision 2)."""
    position: str        # top | before_results_table | before_per_observable | appendix | inline
    content: str
    kind: str            # analytic | proxy_run | halt_notice | signoff_prompt | hard_halt_prompt
    exception_id: Optional[str] = None


@dataclass
class RoutingReport:
    """Final output of stage_p5_render — both JSON and Markdown."""
    model_id: str
    observables: List[str]
    json_report: Dict[str, Any]     # source of truth for content
    markdown_report: str            # source of truth for layout
    placements: List[Placement]
    exit_code: int = 0
    schema_version: int = 1


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class ModelNotInRegistry(Exception):
    """model_id not found in constraints.yaml models block."""


class ModelSpecMissing(Exception):
    """spec_path in registry does not point to an existing file."""


class RegistryCorrupt(Exception):
    """constraints.yaml / blocker_catalog.yaml fails schema validation."""


class SpecValidationError(Exception):
    """ModelSpec YAML fails structural validation."""


class SpecArchivedError(Exception):
    """Model's A8 axis == 'archived'; routing halted early."""


class DetectorInternalError(Exception):
    """WS4 detect() raised an unexpected exception (not an ImportError)."""


class MatrixLoaderError(Exception):
    """matrix_lookup.load_capability_matrix() raised an unexpected exception."""


class BlockerCatalogIntegrityError(Exception):
    """blocker_catalog.yaml has an entry with an unknown blocker_class."""


class MatrixAcknowledgementMissing(Exception):
    """chain_override removes a matrix-blocked prereq without acknowledgement (--strict)."""


class DisclosureBannerMissing(Exception):
    """ROUTE_TO_ANALYTIC verdict with disclosure_required=True but no analytic placement."""


class SchemaValidationError(Exception):
    """Emitted JSON report fails routing_report.schema.json validation."""


class WS1NotMerged(Exception):
    """taxonomy.read_axes not available; WS1-S12 must merge first. Exit code 1."""

    exit_code = 1


class WS2NotMerged(Exception):
    """ConstraintRow.capability_blockers missing; WS2-S10 must merge first. Exit code 3."""

    exit_code = 3


class WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO(Exception):
    """matrix_lookup.py not importable from hep-ph-demo plugin. Exit code 3."""

    exit_code = 3
