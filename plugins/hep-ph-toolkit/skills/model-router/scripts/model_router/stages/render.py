"""
model_router/stages/render.py — Stage P5: render RoutingReport from ComposedRouting.

S15a: skeleton + _build_json_report + _compute_exit_code + stage_p5_render dispatch.
S15b: _build_placements + placement vocabulary.
S15c: formatting helpers (_format_status_line, _format_axis_snapshot_table, etc.).

S16–S18 (render verdict functions): stubbed; returns a placeholder string.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any, Dict, List, Optional

from model_router.types import (
    AxisBundle,
    ComposedRouting,
    LoadedContext,
    Placement,
    RouterOptions,
    RoutingReport,
    SchemaValidationError,
)

# ---------------------------------------------------------------------------
# S15a — Schema loader (lazy; no pydantic)
# ---------------------------------------------------------------------------

def _schema_path() -> pathlib.Path:
    """Return absolute path to routing_report.schema.json."""
    return (
        pathlib.Path(__file__).resolve().parents[1]
        / "schemas"
        / "routing_report.schema.json"
    )


def _load_schema() -> dict:
    """Load and return the routing_report.schema.json as a dict."""
    return json.loads(_schema_path().read_text())


# ---------------------------------------------------------------------------
# S15a — JSON report builder
# ---------------------------------------------------------------------------

def _build_axis_snapshot(composed: ComposedRouting) -> Optional[Dict[str, Any]]:
    """Extract A1..A8 dict from composed.axes_snapshot if present.

    Returns None when no AxisBundle is attached so callers can omit the field.
    """
    axes = getattr(composed, "axes_snapshot", None)
    if axes is None:
        return None
    snap: Dict[str, Any] = {}
    for axis_id in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"):
        snap[axis_id] = getattr(axes, axis_id, None)
    return snap


def _build_json_report(
    composed: ComposedRouting,
    ctx: LoadedContext,
    options: Optional[RouterOptions] = None,
) -> Dict[str, Any]:
    """Build the JSON report dict from ComposedRouting + LoadedContext.

    The JSON report is the source of truth for content; Markdown is the
    source of truth for layout (synthesis §4.1).

    `options` is optional for backward compatibility with earlier callers; when
    omitted, exit_code is sourced from `composed.exit_code` (default 0).

    Returns a dict matching routing_report.schema.json.
    """
    verdict = "CLEAR"
    if composed.exception_verdict is not None:
        verdict = getattr(composed.exception_verdict, "verdict", "CLEAR")

    # model_props from context's diagnostics or directly
    model_props: Dict[str, Any] = {}
    if ctx.model_meta:
        model_props["analytic_module_status"] = ctx.model_meta.get(
            "analytic_module_status", "unregistered"
        )
    if not model_props.get("analytic_module_status"):
        model_props["analytic_module_status"] = "unregistered"

    # per_observable — serialize each ObservableRouting
    per_observable: Dict[str, Any] = {}
    for obs, obs_routing in composed.per_observable.items():
        active_chain_dict = None
        if obs_routing.active_chain is not None:
            ac = obs_routing.active_chain
            active_chain_dict = {
                "prereq_id": ac.prereq_id,
                "role": ac.role,
                "status": ac.status,
                "blockers": ac.blockers,
                "blocker_classes": ac.blocker_classes,
                "caveats": ac.caveats,
                "runtime_install_required": ac.runtime_install_required,
                "matrix_acknowledgement_missing": ac.matrix_acknowledgement_missing,
            }

        ranked_alts = []
        for alt in (obs_routing.ranked_alternatives or []):
            ranked_alts.append({
                "prereq_id": alt.prereq_id,
                "role": alt.role,
                "status": alt.status,
                "blockers": alt.blockers,
                "blocker_classes": alt.blocker_classes,
                "caveats": alt.caveats,
                "runtime_install_required": alt.runtime_install_required,
                "matrix_acknowledgement_missing": alt.matrix_acknowledgement_missing,
            })

        per_candidate = []
        for pc in (obs_routing.per_candidate or []):
            pc_ac = None
            if pc.active_chain is not None:
                pca = pc.active_chain
                pc_ac = {
                    "prereq_id": pca.prereq_id,
                    "role": pca.role,
                    "status": pca.status,
                    "blockers": pca.blockers,
                    "blocker_classes": pca.blocker_classes,
                    "caveats": pca.caveats,
                    "runtime_install_required": pca.runtime_install_required,
                    "matrix_acknowledgement_missing": pca.matrix_acknowledgement_missing,
                }
            per_candidate.append({
                "candidate_name": pc.candidate_name,
                "candidate_field_type": pc.candidate_field_type,
                "candidate_mediator_regime": pc.candidate_mediator_regime,
                "candidate_uv_provenance": pc.candidate_uv_provenance,
                "active_chain": pc_ac,
                "expected_observable_label": pc.expected_observable_label,
            })

        per_observable[obs] = {
            "observable": obs,
            "status": obs_routing.status,
            "active_chain": active_chain_dict,
            "ranked_alternatives": ranked_alts,
            "blockers": obs_routing.blockers,
            "blocker_classes": obs_routing.blocker_classes,
            "caveats": obs_routing.caveats,
            "per_candidate": per_candidate,
            "matrix_acknowledgement_warnings": obs_routing.matrix_acknowledgement_warnings,
        }

    placements_list = _build_placements(composed, ctx)

    # Phase B drift fix: emit exit_code (Schema-required-int) and axis_snapshot
    # (optional dict) per SKILL.md `## Report structure` example. These were
    # documented but not previously emitted (iter-3 review §Findings #9).
    if options is not None:
        exit_code_value = _compute_exit_code(composed, options)
    else:
        exit_code_value = getattr(composed, "exit_code", 0)

    report: Dict[str, Any] = {
        "schema_version": 1,
        "model_id": composed.model_id,
        "observables": composed.observables,
        "verdict": verdict,
        "model_props": model_props,
        "per_observable": per_observable,
        "placements": [
            {
                "position": p.position,
                "content": p.content,
                "kind": p.kind,
                "exception_id": p.exception_id,
            }
            for p in placements_list
        ],
        "diagnostics": composed.diagnostics,
        "exit_code": exit_code_value,
    }
    axis_snap = _build_axis_snapshot(composed)
    if axis_snap is not None:
        report["axis_snapshot"] = axis_snap
    return report


# ---------------------------------------------------------------------------
# S15a — Schema validation
# ---------------------------------------------------------------------------

def _validate_json_against_schema(json_report: Dict[str, Any]) -> None:
    """Validate json_report against routing_report.schema.json.

    The schema has a relative $ref to `ranked_chain.schema.json`; we
    construct a Draft7Validator with a base URI pointing at the schemas
    directory so the $ref resolves locally.

    Raises:
        SchemaValidationError if the report fails schema validation.
    """
    try:
        import jsonschema  # type: ignore
    except ImportError:
        # jsonschema not installed — skip validation (fail-open at import time)
        return

    schema = _load_schema()
    base_uri = _schema_path().parent.as_uri() + "/"
    try:
        # Newer jsonschema (>=4.18) prefers a referencing Registry; older
        # versions use RefResolver. Try both for forward/backward compat.
        try:
            from referencing import Registry, Resource  # type: ignore
            from referencing.jsonschema import DRAFT7  # type: ignore
            ranked_path = _schema_path().parent / "ranked_chain.schema.json"
            ranked_schema = json.loads(ranked_path.read_text())
            registry = Registry().with_resource(
                "ranked_chain.schema.json",
                Resource(contents=ranked_schema, specification=DRAFT7),
            )
            validator = jsonschema.Draft7Validator(schema, registry=registry)
            errors = list(validator.iter_errors(json_report))
            if errors:
                raise jsonschema.ValidationError(errors[0].message)
        except ImportError:
            resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema)
            jsonschema.validate(json_report, schema, resolver=resolver)
    except jsonschema.ValidationError as exc:
        raise SchemaValidationError(
            f"RoutingReport JSON failed schema validation: {exc.message}"
        ) from exc


# ---------------------------------------------------------------------------
# S15a — Exit code computation
# ---------------------------------------------------------------------------

def _compute_exit_code(composed: ComposedRouting, options: RouterOptions) -> int:
    """Compute the report exit code per synthesis §10 table.

    Default mode (strict=False):
        0 for all verdicts (CLEAR, ROUTE_TO_ANALYTIC, HALT_FOR_SIGNOFF, HARD_HALT).

    Strict mode (strict=True):
        4 — matrix_acknowledgement_missing contradiction.
        5 — HALT_FOR_SIGNOFF.
        6 — HARD_HALT.
        0 — CLEAR or ROUTE_TO_ANALYTIC without contradictions.

    Error codes (set by upstream stages, not here):
        1 — WS1 absent (WS1NotMerged).
        3 — WS2 absent or hep-ph-demo missing.
    """
    verdict = "CLEAR"
    if composed.exception_verdict is not None:
        verdict = getattr(composed.exception_verdict, "verdict", "CLEAR")

    if not options.strict:
        return 0

    # Strict mode
    if verdict == "HARD_HALT":
        return 6
    if verdict == "HALT_FOR_SIGNOFF":
        return 5
    # Check for matrix_acknowledgement_missing contradiction
    for obs_routing in composed.per_observable.values():
        if obs_routing.active_chain and obs_routing.active_chain.matrix_acknowledgement_missing:
            return 4
    return 0


# ---------------------------------------------------------------------------
# S15b — Placement builder
# ---------------------------------------------------------------------------

def _build_placements(composed: ComposedRouting, ctx: LoadedContext) -> List[Placement]:
    """Build the placements list from ComposedRouting per synthesis Decision 2.

    Placement vocabulary (closed enum from routing_report.schema.json):
    - position: top | before_results_table | before_per_observable | appendix | inline
    - kind: analytic | proxy_run | halt_notice | signoff_prompt | hard_halt_prompt

    Dispatch per verdict:
    - ROUTE_TO_ANALYTIC: one placement {before_per_observable, analytic} with the banner.
    - HALT_FOR_SIGNOFF: two placements — {top, halt_notice} + {appendix, signoff_prompt}.
    - HARD_HALT: one placement {top, hard_halt_prompt}.
    - CLEAR: empty list.
    """
    verdict = "CLEAR"
    exception_id = None
    banner_content = None

    if composed.exception_verdict is not None:
        verdict = getattr(composed.exception_verdict, "verdict", "CLEAR")
        exception_id = getattr(composed.exception_verdict, "exception_id", None)

        # Try to get banner from analytic_exceptions registry (ctx.analytic_exceptions)
        if exception_id and ctx.analytic_exceptions:
            entry = ctx.analytic_exceptions.get("exceptions", {}).get(exception_id, {})
            banner_content = entry.get("banner")

    if verdict == "ROUTE_TO_ANALYTIC":
        content = banner_content or (
            f"**Analytic backend active** (exception: {exception_id or 'unknown'}).\n"
            "This model routes to the analytic computation backend instead of Monte Carlo tools."
        )
        return [
            Placement(
                position="before_per_observable",
                content=content,
                kind="analytic",
                exception_id=exception_id,
            )
        ]

    if verdict == "HALT_FOR_SIGNOFF":
        halt_notice = (
            "> **HALT FOR SIGN-OFF REQUIRED**\n"
            "> An analytic exception has been detected for this model. "
            "Routing cannot proceed without sign-off. See Required Next Steps below."
        )
        signoff_prompt = (
            "## Required next steps (analytic exception sign-off)\n\n"
            "An analytic exception was triggered for this model. To proceed:\n\n"
            "1. Review the analytic exception details above.\n"
            "2. Either author a real analytic module and register it, "
            "or declare this model is not analytic-eligible.\n"
            "3. Re-run `/model-router` after resolving the sign-off.\n"
        )
        return [
            Placement(
                position="top",
                content=halt_notice,
                kind="halt_notice",
                exception_id=exception_id,
            ),
            Placement(
                position="appendix",
                content=signoff_prompt,
                kind="signoff_prompt",
                exception_id=exception_id,
            ),
        ]

    if verdict == "HARD_HALT":
        hard_halt_prompt = (
            "> **HARD HALT — EFT REWRITE REQUIRED**\n"
            "> This model's gauge structure requires an EFT rewrite before routing can proceed. "
            "Monte Carlo and analytic tools cannot handle this model in its current form."
        )
        return [
            Placement(
                position="top",
                content=hard_halt_prompt,
                kind="hard_halt_prompt",
                exception_id=exception_id,
            )
        ]

    # CLEAR or unknown verdict → no placements
    return []


# ---------------------------------------------------------------------------
# S15c — Formatting helpers
# ---------------------------------------------------------------------------

def _format_status_line(composed: ComposedRouting, diagnostics: Dict[str, Any]) -> str:
    """Format the Status: header line with applicable modifiers.

    Modifiers:
    - [matrix_acknowledgement_missing] — one or more active chains has missing ack.
    - [PROVISIONAL] — status_modifier is "provisional".
    - [HALT — see Required next steps] — HALT_FOR_SIGNOFF verdict.
    """
    verdict = "CLEAR"
    if composed.exception_verdict is not None:
        verdict = getattr(composed.exception_verdict, "verdict", "CLEAR")

    modifiers = []

    # Check matrix acknowledgement missing
    for obs_routing in composed.per_observable.values():
        if obs_routing.active_chain and obs_routing.active_chain.matrix_acknowledgement_missing:
            modifiers.append("matrix_acknowledgement_missing")
            break

    if diagnostics.get("provisional"):
        modifiers.append("PROVISIONAL")

    if verdict == "HALT_FOR_SIGNOFF":
        modifiers.append("HALT — see Required next steps")

    mod_str = ""
    if modifiers:
        mod_str = " " + " ".join(f"[{m}]" for m in modifiers)

    return f"**Status:** {verdict}{mod_str}"


def _format_axis_snapshot_table(axes: AxisBundle) -> str:
    """Format a Markdown table of WS1 taxonomy axes A1–A8."""
    rows = [
        ("A1", "Gauge extension class", axes.A1),
        ("A2", "Symmetry-breaking patterns", axes.A2),
        ("A3", "Fermion projections", axes.A3),
        ("A4", "Scalar topology", axes.A4),
        ("A5", "Global symmetries", axes.A5),
        ("A6", "Portal couplings", axes.A6),
        ("A7", "Extra colored matter", axes.A7),
        ("A8", "Authoring status", axes.A8),
    ]
    lines = ["| Axis | Description | Value |", "|------|-------------|-------|"]
    for axis_id, desc, val in rows:
        val_str = str(val) if val is not None else "—"
        lines.append(f"| {axis_id} | {desc} | {val_str} |")
    return "\n".join(lines)


def _format_methodology_footnote(ctx: LoadedContext) -> str:
    """Format the methodology footnote explaining routing decisions."""
    return (
        "\n---\n"
        "*Methodology: WS3 model-router v1. "
        "Routing decisions are derived from WS1 taxonomy axes, WS4 analytic-exception "
        "detection, and the WS2 capability matrix. "
        f"Model: `{ctx.model_id}`. "
        "See `plugins/hep-ph-toolkit/skills/model-router/SKILL.md` for ranking policy.*\n"
    )


def _format_ranked_chain_table(obs_routing: Any, fold: Any) -> str:
    """Format a ranked-chain table for one observable showing alternatives.

    Args:
        obs_routing: ObservableRouting for the observable.
        fold: The selected PrereqFold (may be None for BLOCKED/HALT cases).

    Returns:
        Markdown table string.
    """
    lines = [
        "| Rank | Prereq | Role | Status | Blockers |",
        "|------|--------|------|--------|----------|",
    ]

    # Active chain first
    if obs_routing.active_chain is not None:
        ac = obs_routing.active_chain
        blockers_str = ", ".join(ac.blockers) if ac.blockers else "—"
        lines.append(
            f"| **1** | **{ac.prereq_id}** | {ac.role} | {ac.status} | {blockers_str} |"
        )

    # Ranked alternatives
    for i, alt in enumerate(obs_routing.ranked_alternatives or [], start=2):
        blockers_str = ", ".join(alt.blockers) if alt.blockers else "—"
        lines.append(
            f"| {i} | {alt.prereq_id} | {alt.role} | {alt.status} | {blockers_str} |"
        )

    return "\n".join(lines)


def _format_diagnostics_section(diagnostics: Dict[str, Any]) -> str:
    """Format the diagnostics section as a Markdown code block.

    Returns empty string if diagnostics is empty.
    """
    if not diagnostics:
        return ""
    lines = ["\n## Diagnostics\n", "```json"]
    lines.append(json.dumps(diagnostics, indent=2, default=str))
    lines.append("```\n")
    return "\n".join(lines)


def _inject_placements(
    rendered_md: str,
    placements: List[Placement],
    position: str,
) -> str:
    """Inject placements at the specified position anchor in the rendered Markdown.

    Inserts HTML-comment anchors `<!-- WS3:section=<position> -->` and places
    matching placements after each anchor. If no anchor is present, appends
    matching placements at the end.

    Args:
        rendered_md: The partially-rendered Markdown string.
        placements:  All placements to consider (filters by position internally).
        position:    Which position to inject (e.g. 'top', 'before_per_observable').

    Returns:
        Modified Markdown string with placements injected.
    """
    anchor = f"<!-- WS3:section={position} -->"
    matching = [p.content for p in placements if p.position == position]

    if not matching:
        return rendered_md

    injection = "\n".join(matching) + "\n"

    if anchor in rendered_md:
        return rendered_md.replace(anchor, anchor + "\n" + injection, 1)
    else:
        # Append at end if anchor is missing
        return rendered_md + "\n" + injection


# ---------------------------------------------------------------------------
# S16–S18 — verdict-specific render bodies (real Markdown; consume S15c helpers)
# ---------------------------------------------------------------------------

def _format_per_observable_section(
    obs_routing: Any,
    ctx: LoadedContext,
) -> str:
    """Render one #### Observable: <obs> block per synthesis §7."""
    obs = obs_routing.observable
    lines = [f"#### Observable: `{obs}`", "", f"**Status:** {obs_routing.status}", ""]
    lines.append(_format_ranked_chain_table(obs_routing, fold=None))
    lines.append("")
    if obs_routing.matrix_acknowledgement_warnings:
        lines.append("> **Matrix acknowledgement warnings:**")
        for w in obs_routing.matrix_acknowledgement_warnings:
            lines.append(f"> - {w}")
        lines.append("")
    return "\n".join(lines)


def _format_per_candidate_block(obs_routing: Any) -> str:
    """Render `#### Candidate <name>` blocks per synthesis §4.6 + Decision 1."""
    if not obs_routing.per_candidate:
        return ""
    parts: List[str] = ["##### Per-candidate routing", ""]
    for pc in obs_routing.per_candidate:
        parts.append(f"##### Candidate `{pc.candidate_name}`")
        parts.append("")
        parts.append(f"- **Field type:** {pc.candidate_field_type or '—'}")
        parts.append(f"- **Mediator regime:** {pc.candidate_mediator_regime or '—'}")
        parts.append(f"- **UV provenance:** {pc.candidate_uv_provenance or '—'}")
        parts.append(f"- **Expected observable label:** `{pc.expected_observable_label}`")
        if pc.active_chain is not None:
            parts.append(f"- **Active chain:** `{pc.active_chain.prereq_id}` "
                         f"(role: {pc.active_chain.role}, status: {pc.active_chain.status})")
        parts.append("")
    return "\n".join(parts)


def _format_header(composed: ComposedRouting, verdict_label: str) -> str:
    """Compose the Markdown header block (title + status line)."""
    diagnostics = composed.diagnostics or {}
    status_line = _format_status_line(composed, diagnostics)
    return (
        f"# Routing Report: `{composed.model_id}`\n\n"
        f"{status_line}\n\n"
        f"**Verdict:** {verdict_label}\n\n"
        f"**Observables requested:** {', '.join(composed.observables) if composed.observables else '—'}\n"
    )


def _render_clear(composed: ComposedRouting, ctx: LoadedContext, options: RouterOptions) -> str:
    """Render CLEAR verdict Markdown.

    Per synthesis §7.1 + plan §S16: standard report with axis snapshot,
    per-observable ranked-chain tables, optional diagnostics section, and
    methodology footnote. Includes WS3 section anchors for placement
    injection (CLEAR has no placements, but anchors are still emitted for
    structural consistency and downstream contract tests).
    """
    parts: List[str] = []
    parts.append("<!-- WS3:section=top -->")
    parts.append(_format_header(composed, "CLEAR"))
    parts.append("")

    if composed.axes_snapshot is not None:
        parts.append("## Axis snapshot (WS1 taxonomy)")
        parts.append("")
        parts.append(_format_axis_snapshot_table(composed.axes_snapshot))
        parts.append("")

    parts.append("<!-- WS3:section=before_results_table -->")
    parts.append("## Routing decisions per observable")
    parts.append("")
    parts.append("<!-- WS3:section=before_per_observable -->")
    parts.append("<!-- WS3:section=per-observable -->")
    parts.append("")
    for obs, obs_routing in composed.per_observable.items():
        parts.append(_format_per_observable_section(obs_routing, ctx))

    diagnostics = composed.diagnostics or {}
    diag_section = _format_diagnostics_section(diagnostics)
    if diag_section:
        parts.append(diag_section)

    parts.append("<!-- WS3:section=appendix -->")
    parts.append(_format_methodology_footnote(ctx))
    parts.append("<!-- WS3:section=inline -->")
    return "\n".join(parts)


def _render_hard_halt(composed: ComposedRouting, ctx: LoadedContext, options: RouterOptions) -> str:
    """Render HARD_HALT verdict Markdown.

    Per synthesis §7.4 + plan §S16: top halt notice (injected via placement),
    per-observable rows showing EFT_REWRITE_REQUIRED, no
    `## Required next steps` section. Tools cannot proceed; only the
    halt prompt and per-observable diagnostic rows are useful.
    """
    parts: List[str] = []
    parts.append("<!-- WS3:section=top -->")
    parts.append(_format_header(composed, "HARD_HALT"))
    parts.append("")
    parts.append("> **HARD HALT:** This model's gauge structure (or other "
                 "fundamental property) prevents any registered tool chain from "
                 "producing physically meaningful output. The default and "
                 "alternative chains are listed below for diagnostic purposes "
                 "only.")
    parts.append("")

    if composed.axes_snapshot is not None:
        parts.append("## Axis snapshot (WS1 taxonomy)")
        parts.append("")
        parts.append(_format_axis_snapshot_table(composed.axes_snapshot))
        parts.append("")

    parts.append("<!-- WS3:section=before_results_table -->")
    parts.append("## Per-observable diagnostic rows")
    parts.append("")
    parts.append("<!-- WS3:section=before_per_observable -->")
    parts.append("<!-- WS3:section=per-observable -->")
    parts.append("")
    for obs, obs_routing in composed.per_observable.items():
        parts.append(_format_per_observable_section(obs_routing, ctx))
        parts.append("- **Required action:** `EFT_REWRITE_REQUIRED` — "
                     "model gauge structure incompatible with registered tools.")
        parts.append("")

    diag_section = _format_diagnostics_section(composed.diagnostics or {})
    if diag_section:
        parts.append(diag_section)

    parts.append("<!-- WS3:section=appendix -->")
    parts.append(_format_methodology_footnote(ctx))
    parts.append("<!-- WS3:section=inline -->")
    return "\n".join(parts)


def _render_halt_for_signoff(composed: ComposedRouting, ctx: LoadedContext, options: RouterOptions) -> str:
    """Render HALT_FOR_SIGNOFF verdict Markdown.

    Per synthesis §7.3 + Decision 7 + plan §S17: top halt notice (injected
    via placement); per-observable section renders normally with
    `status: HALT` per row; appendix `## Required next steps (analytic
    exception sign-off)` section sourced from placements.
    """
    parts: List[str] = []
    parts.append("<!-- WS3:section=top -->")
    parts.append(_format_header(composed, "HALT_FOR_SIGNOFF"))
    parts.append("")
    parts.append("> **HALT FOR SIGN-OFF:** an analytic exception requires "
                 "human authorization before routing can proceed. The "
                 "diagnostic per-observable rows below are pinned to "
                 "`status: HALT`; see *Required next steps* in the appendix.")
    parts.append("")

    if composed.axes_snapshot is not None:
        parts.append("## Axis snapshot (WS1 taxonomy)")
        parts.append("")
        parts.append(_format_axis_snapshot_table(composed.axes_snapshot))
        parts.append("")

    parts.append("<!-- WS3:section=before_results_table -->")
    parts.append("## Per-observable rows (status: HALT)")
    parts.append("")
    parts.append("<!-- WS3:section=before_per_observable -->")
    parts.append("<!-- WS3:section=per-observable -->")
    parts.append("")
    for obs, obs_routing in composed.per_observable.items():
        parts.append(_format_per_observable_section(obs_routing, ctx))

    diag_section = _format_diagnostics_section(composed.diagnostics or {})
    if diag_section:
        parts.append(diag_section)

    parts.append("<!-- WS3:section=appendix -->")
    # The signoff prompt itself is injected as a placement at appendix.
    parts.append(_format_methodology_footnote(ctx))
    parts.append("<!-- WS3:section=inline -->")
    return "\n".join(parts)


def _render_route_to_analytic(composed: ComposedRouting, ctx: LoadedContext, options: RouterOptions) -> str:
    """Render ROUTE_TO_ANALYTIC verdict Markdown.

    Per synthesis §7.2 + §4.6 + Decision 1 + plan §S18: standard report
    with disclosure banner (placement at before_per_observable), per-
    observable ranked-chain tables, per_candidate sub-blocks for each
    DM observable, and a "Blockers on alternative chains" table.

    DisclosureBannerMissing is raised when the WS4 verdict requires a
    disclosure banner but no analytic placement is present (fail-closed
    per plan §S18).
    """
    # Fail-closed: ROUTE_TO_ANALYTIC + disclosure_required must produce a
    # placement; otherwise raise DisclosureBannerMissing.
    ev = composed.exception_verdict
    disclosure_required = bool(getattr(ev, "disclosure_required", False)) if ev else False
    if disclosure_required:
        # Re-build placements to verify presence (cheap, deterministic).
        placements = _build_placements(composed, ctx)
        has_analytic = any(p.kind == "analytic" for p in placements)
        if not has_analytic:
            from model_router.types import DisclosureBannerMissing
            raise DisclosureBannerMissing(
                f"ROUTE_TO_ANALYTIC verdict for model '{composed.model_id}' "
                "requires a disclosure banner (disclosure_required=True), but "
                "no placement with kind='analytic' was produced."
            )

    parts: List[str] = []
    parts.append("<!-- WS3:section=top -->")
    parts.append(_format_header(composed, "ROUTE_TO_ANALYTIC"))
    parts.append("")
    parts.append("> **Routing to the analytic backend.** "
                 "Default Monte Carlo chains cannot represent this model. "
                 "The disclosure banner below is mandatory and verbatim from "
                 "the analytic_exceptions registry.")
    parts.append("")

    if composed.axes_snapshot is not None:
        parts.append("## Axis snapshot (WS1 taxonomy)")
        parts.append("")
        parts.append(_format_axis_snapshot_table(composed.axes_snapshot))
        parts.append("")

    parts.append("<!-- WS3:section=before_results_table -->")
    parts.append("## Routing decisions per observable")
    parts.append("")
    parts.append("<!-- WS3:section=before_per_observable -->")
    parts.append("<!-- WS3:section=per-observable -->")
    parts.append("")
    for obs, obs_routing in composed.per_observable.items():
        parts.append(_format_per_observable_section(obs_routing, ctx))
        per_cand = _format_per_candidate_block(obs_routing)
        if per_cand:
            parts.append(per_cand)

    parts.append("## Blockers on alternative chains (model-level)")
    parts.append("")
    parts.append("The following matrix prereqs were ranked but bypassed by "
                 "the analytic backend selection:")
    parts.append("")
    seen_alts: List[str] = []
    for obs_routing in composed.per_observable.values():
        for alt in (obs_routing.ranked_alternatives or []):
            tag = f"{obs_routing.observable}::{alt.prereq_id}"
            if tag in seen_alts:
                continue
            seen_alts.append(tag)
            blockers_str = ", ".join(alt.blockers) if alt.blockers else "—"
            parts.append(f"- `{obs_routing.observable}` / `{alt.prereq_id}` "
                         f"(role: {alt.role}, status: {alt.status}) — blockers: {blockers_str}")
    parts.append("")

    diag_section = _format_diagnostics_section(composed.diagnostics or {})
    if diag_section:
        parts.append(diag_section)

    parts.append("<!-- WS3:section=appendix -->")
    parts.append(_format_methodology_footnote(ctx))
    parts.append("<!-- WS3:section=inline -->")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# S15a — Top-level dispatch
# ---------------------------------------------------------------------------

def stage_p5_render(
    composed: ComposedRouting,
    ctx: LoadedContext,
    options: RouterOptions,
) -> RoutingReport:
    """Stage P5: render RoutingReport from ComposedRouting.

    Dispatches on composed.exception_verdict.verdict to one of four render
    functions, builds and validates the JSON report, and assembles the final
    RoutingReport.

    Raises:
        SchemaValidationError: if the JSON report fails schema validation.
    """
    verdict = "CLEAR"
    if composed.exception_verdict is not None:
        verdict = getattr(composed.exception_verdict, "verdict", "CLEAR")

    # Build placements first (used by both JSON and Markdown)
    placements = _build_placements(composed, ctx)

    # Dispatch verdict-specific Markdown render
    if verdict == "HARD_HALT":
        raw_md = _render_hard_halt(composed, ctx, options)
    elif verdict == "HALT_FOR_SIGNOFF":
        raw_md = _render_halt_for_signoff(composed, ctx, options)
    elif verdict == "ROUTE_TO_ANALYTIC":
        raw_md = _render_route_to_analytic(composed, ctx, options)
    else:
        raw_md = _render_clear(composed, ctx, options)

    # Inject placements into Markdown
    md = raw_md
    for position in ["top", "before_results_table", "before_per_observable", "appendix", "inline"]:
        md = _inject_placements(md, placements, position)

    # Build and validate JSON report
    json_report = _build_json_report(composed, ctx, options)
    _validate_json_against_schema(json_report)

    # Compute exit code
    exit_code = _compute_exit_code(composed, options)

    return RoutingReport(
        model_id=composed.model_id,
        observables=composed.observables,
        json_report=json_report,
        markdown_report=md,
        placements=placements,
        exit_code=exit_code,
        schema_version=1,
    )
