#!/usr/bin/env python3
"""router.py — CLI entrypoint for the WS3 model-router skill.

Per WS3 plan §S24 + manager Decision 3 (path-shim).

The first three lines insert this script's parent directory (``scripts/``)
into ``sys.path`` so ``import model_router`` resolves without an editable
install. The CLI is a thin wrapper around ``model_router.orchestrator.route``.

Usage:
    python3 router.py <model-id> [--observables ...] [--strict]
                      [--output md|json|both] [--output-dir DIR]
                      [--config PATH] [--explain PREREQ_ID]
                      [--constraints PATH] [--blocker-catalog PATH]
                      [--analytic-exceptions PATH]

Exit codes (per SKILL.md `## Strict mode + exit codes`):
    0 — success (CLEAR, ROUTE_TO_ANALYTIC; HALT/HARD in default mode).
    1 — WS1NotMerged (taxonomy.read_axes not importable).
    2 — generic CLI / argparse error (also used for unknown model in strict).
    3 — WS2NotMerged or WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO.
    4 — --strict + matrix acknowledgement contradiction.
    5 — --strict + HALT_FOR_SIGNOFF.
    6 — --strict + HARD_HALT.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import argparse
import json
from typing import List, Optional


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="router",
        description="WS3 model-to-tool routing — emit JSON+Markdown report for a registered model.",
    )
    p.add_argument(
        "model_id",
        help="Registered model identifier (must be in constraints.yaml `models`).",
    )
    p.add_argument(
        "--observables",
        nargs="+",
        default=None,
        help="Subset of observables to route (e.g. relic dd id). Defaults to all model defaults.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: raise on matrix-acknowledgement contradictions; "
             "HALT verdicts get non-zero exit codes.",
    )
    p.add_argument(
        "--output",
        choices=["md", "json", "both"],
        default="md",
        help="Output format: md (markdown), json (sidecar), or both. Default: md.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Write reports to files in this directory instead of stdout.",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Path to a config.json overriding ~/.config/hephaestus/config.json.",
    )
    p.add_argument(
        "--explain",
        default=None,
        metavar="PREREQ_ID",
        help="Append a `## Verdict trace for <prereq-id>` section to the Markdown report.",
    )
    # Registry-path overrides — useful for tests / non-default registries.
    p.add_argument(
        "--constraints",
        default=None,
        help="Override path to constraints.yaml (default: hep-ph-demo _shared).",
    )
    p.add_argument(
        "--blocker-catalog",
        default=None,
        help="Override path to blocker_catalog.yaml.",
    )
    p.add_argument(
        "--analytic-exceptions",
        default=None,
        help="Override path to analytic_exceptions.yaml.",
    )
    return p


def _format_explain(report, prereq_id: str) -> str:
    """Append a Markdown trace section for the requested prereq.

    The trace shows, per observable, the per-prereq fold breakdown
    (matrix verdict, blockers, role, status) — useful for `--explain`.
    """
    lines = ["", "## Verdict trace for `" + prereq_id + "`", ""]
    json_report = report.json_report
    found_any = False
    for obs, obs_routing in json_report.get("per_observable", {}).items():
        # Active chain
        ac = obs_routing.get("active_chain") or {}
        if ac.get("prereq_id") == prereq_id:
            found_any = True
            lines.append(f"### `{obs}` (active chain)")
            lines.append(f"- role: `{ac.get('role')}`")
            lines.append(f"- status: `{ac.get('status')}`")
            blockers = ac.get("blockers") or []
            lines.append(f"- blockers: {', '.join(f'`{b}`' for b in blockers) if blockers else '—'}")
            lines.append("")
        # Alternatives
        for alt in obs_routing.get("ranked_alternatives") or []:
            if alt.get("prereq_id") == prereq_id:
                found_any = True
                lines.append(f"### `{obs}` (alternative)")
                lines.append(f"- role: `{alt.get('role')}`")
                lines.append(f"- status: `{alt.get('status')}`")
                blockers = alt.get("blockers") or []
                lines.append(
                    f"- blockers: {', '.join(f'`{b}`' for b in blockers) if blockers else '—'}"
                )
                lines.append("")
    if not found_any:
        lines.append(f"_No fold for prereq `{prereq_id}` in any routed observable._\n")
    return "\n".join(lines)


def _emit(report, args) -> None:
    """Write report content per --output / --output-dir flags."""
    md = report.markdown_report
    if args.explain:
        md = md + _format_explain(report, args.explain)

    json_str = json.dumps(report.json_report, indent=2, default=str)

    if args.output_dir:
        out = pathlib.Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        if args.output in ("md", "both"):
            (out / f"{args.model_id}.md").write_text(md)
        if args.output in ("json", "both"):
            (out / f"{args.model_id}.json").write_text(json_str)
    else:
        if args.output == "json":
            print(json_str)
        elif args.output == "both":
            print(json_str)
            print()
            print(md)
        else:
            print(md)


def _exit_for_exception(exc: Exception) -> int:
    """Map known router exceptions to documented exit codes."""
    # Late import so test monkeypatches resolve correctly.
    from model_router.types import (
        DisclosureBannerMissing,
        MatrixAcknowledgementMissing,
        ModelNotInRegistry,
        ModelSpecMissing,
        RegistryCorrupt,
        SchemaValidationError,
        SpecArchivedError,
        SpecValidationError,
        WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO,
        WS1NotMerged,
        WS2NotMerged,
    )

    if isinstance(exc, WS1NotMerged):
        return 1
    if isinstance(exc, (WS2NotMerged, WORKFLOW_PLUGIN_MISSING_DEP_HEP_PH_DEMO)):
        return 3
    if isinstance(exc, MatrixAcknowledgementMissing):
        return 4
    if isinstance(exc, (ModelNotInRegistry, ModelSpecMissing, RegistryCorrupt,
                        SpecValidationError, SpecArchivedError,
                        SchemaValidationError, DisclosureBannerMissing)):
        return 2
    return 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Late import so the path-shim is in effect.
    from model_router import RouterOptions, route

    options = RouterOptions(
        strict=args.strict,
        output=args.output,
        output_dir=args.output_dir,
        config_path=args.config,
        explain=args.explain,
    )

    constraints_path = pathlib.Path(args.constraints) if args.constraints else None
    blocker_catalog_path = pathlib.Path(args.blocker_catalog) if args.blocker_catalog else None
    analytic_exceptions_path = pathlib.Path(args.analytic_exceptions) if args.analytic_exceptions else None

    try:
        report = route(
            model_id=args.model_id,
            observables=args.observables,
            options=options,
            constraints_path=constraints_path,
            blocker_catalog_path=blocker_catalog_path,
            analytic_exceptions_path=analytic_exceptions_path,
        )
    except Exception as exc:
        sys.stderr.write(f"router error: {type(exc).__name__}: {exc}\n")
        return _exit_for_exception(exc)

    _emit(report, args)
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
