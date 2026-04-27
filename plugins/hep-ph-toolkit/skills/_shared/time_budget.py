"""
time_budget.py — pure-function time-estimate resolver for hep-ph-demo.

Public API:
    resolve(model: str, selected: list[str]) -> TimeReport

TimeReport is a dataclass with:
    rows:           list[ConstraintRow]  — one per selected constraint
    overlap_totals: OverlapTotals        — cold/cached for ready + all

A ConstraintRow has:
    constraint:   str             — constraint id (relic|dd|id|collider)
    status:       str             — "READY" | "BLOCKED"
    missing:      list[str]       — planned prereqs that block execution
    chain_annotated: list[tuple[str, str]]  — [(prereq, "EXISTS"|"PLANNED"), ...]
    cold:         list[float]     — [lo, hi] hours
    cached:       list[float]     — [lo, hi] hours

Usage (CLI):
    python3 time_budget.py --model singlet-doublet --constraints relic dd id
"""

from __future__ import annotations

import argparse
import pathlib
from dataclasses import dataclass, field
from typing import Optional

import yaml

_YAML_PATH = pathlib.Path(__file__).parent / "constraints.yaml"


def _load() -> dict:
    with open(_YAML_PATH) as fh:
        return yaml.safe_load(fh)


@dataclass
class ConstraintRow:
    constraint: str
    status: str                       # "READY" | "BLOCKED"
    missing: list[str] = field(default_factory=list)
    chain_annotated: list[tuple[str, str]] = field(default_factory=list)
    cold: list[float] = field(default_factory=lambda: [0.0, 0.0])
    cached: list[float] = field(default_factory=lambda: [0.0, 0.0])
    # WS2 extension: capability-matrix blockers injected by inject_capability_blockers().
    # Populated by the WS3 routing layer; not modified by resolve().
    capability_blockers: list = field(default_factory=list)


@dataclass
class OverlapTotals:
    # ready constraints only (what can actually run)
    cold_ready: list[float] = field(default_factory=lambda: [0.0, 0.0])
    cached_ready: list[float] = field(default_factory=lambda: [0.0, 0.0])
    # all selected constraints (hypothetical if all prereqs existed)
    cold_all: list[float] = field(default_factory=lambda: [0.0, 0.0])
    cached_all: list[float] = field(default_factory=lambda: [0.0, 0.0])


@dataclass
class TimeReport:
    model: str
    selected: list[str]
    rows: list[ConstraintRow] = field(default_factory=list)
    overlap_totals: OverlapTotals = field(default_factory=OverlapTotals)


def resolve(model: str, selected: list[str]) -> TimeReport:
    """Compute per-constraint status and overlap-adjusted time totals.

    Parameters
    ----------
    model:
        One of 'singlet-doublet', '2hdm-a', 'dark-su3'.
    selected:
        Subset of constraint ids: ['relic'], ['relic','dd'], etc.
        'collider' is accepted (placeholder — always skipped with a note).

    Returns
    -------
    TimeReport
    """
    data = _load()
    prereqs_meta = data["prereqs"]
    constraints_meta = data["constraints"]
    model_meta = data["models"][model]
    time_overrides = model_meta.get("time_overrides", {})
    multi_prereq: Optional[str] = model_meta.get("multi_component_prereq")
    # Per-constraint spec-authoring blockers: pseudo-prereq tokens that force
    # BLOCKED status regardless of prereq skill availability. See
    # constraints.yaml models.*.spec_authoring_blockers for usage.
    spec_blockers: dict = model_meta.get("spec_authoring_blockers", {}) or {}
    # Per-constraint chain overrides: full replacement for the default chain.
    # See constraints.yaml header for schema. Used by models whose default
    # chain doesn't apply (e.g. dark SU(3)_D non-SM color forces relic to
    # skip MadGraph/MadDM and run via the analytic backend).
    chain_overrides: dict = model_meta.get("chain_overrides", {}) or {}

    report = TimeReport(model=model, selected=list(selected))

    # Prereqs seen across ALL selected constraints (for overlap dedup)
    seen_prereqs_all: dict[str, bool] = {}
    # Prereqs seen across READY selected constraints only
    seen_prereqs_ready: dict[str, bool] = {}

    cold_all_lo, cold_all_hi = 0.0, 0.0
    cached_all_lo, cached_all_hi = 0.0, 0.0
    cold_ready_lo, cold_ready_hi = 0.0, 0.0
    cached_ready_lo, cached_ready_hi = 0.0, 0.0

    for cid in selected:
        if cid == "collider":
            row = ConstraintRow(
                constraint="collider",
                status="BLOCKED",
                missing=["collider-not-implemented"],
                chain_annotated=[],
                cold=[0.0, 0.0],
                cached=[0.0, 0.0],
            )
            report.rows.append(row)
            continue

        if cid not in constraints_meta:
            raise ValueError(f"Unknown constraint: {cid!r}")

        c = constraints_meta[cid]
        # Per-model chain_overrides take precedence over the default chain.
        # When present, the override.chain replaces constraints.<cid>.chain
        # entirely (the multi_component_prereq is still appended below if
        # not already present, so models can rely on a single source of
        # truth for the multi-component combiner skill).
        override_entry = chain_overrides.get(cid) or {}
        if override_entry.get("chain"):
            chain = list(override_entry["chain"])
        else:
            chain = list(c["chain"])

        # Inject multi-component prereq at end if applicable
        if multi_prereq and multi_prereq not in chain:
            chain.append(multi_prereq)

        # Annotate each prereq
        annotated = []
        missing = []
        for prereq in chain:
            pmeta = prereqs_meta[prereq]
            tag = "EXISTS" if pmeta["status"] == "exists" else "PLANNED"
            annotated.append((prereq, tag))
            if pmeta["status"] == "planned":
                missing.append(prereq)

        # Spec-authoring blockers: force BLOCKED and prepend the pseudo-token(s)
        # to `missing` so the user sees them first in the chain table. These
        # are not real skills — they represent ModelSpec YAML / analytic module
        # gaps the caller must fix before the prereq chain can run.
        for token in spec_blockers.get(cid, []) or []:
            if token not in missing:
                missing.insert(0, token)

        status = "READY" if not missing else "BLOCKED"

        # Determine time for this constraint
        override = time_overrides.get(cid, {})
        default_cold = c["default_time"]["cold"]
        default_cached = c["default_time"]["cached"]
        cold_range = override.get("cold", default_cold)
        cached_range = override.get("cached", default_cached)

        row = ConstraintRow(
            constraint=cid,
            status=status,
            missing=missing,
            chain_annotated=annotated,
            cold=list(cold_range),
            cached=list(cached_range),
        )
        report.rows.append(row)

        # Overlap accumulation: count each unique prereq once.
        # We accumulate per-prereq hours (not the constraint-level total) to
        # avoid double-counting shared prereqs (sarah-build, spheno-build, etc.)
        for prereq, _ in annotated:
            pmeta = prereqs_meta[prereq]
            ph_cold = pmeta["hours"]["cold"]
            ph_cached = pmeta["hours"]["cached"]

            if prereq not in seen_prereqs_all:
                seen_prereqs_all[prereq] = True
                cold_all_lo += ph_cold[0]
                cold_all_hi += ph_cold[1]
                cached_all_lo += ph_cached[0]
                cached_all_hi += ph_cached[1]

            if status == "READY" and prereq not in seen_prereqs_ready:
                seen_prereqs_ready[prereq] = True
                cold_ready_lo += ph_cold[0]
                cold_ready_hi += ph_cold[1]
                cached_ready_lo += ph_cached[0]
                cached_ready_hi += ph_cached[1]

    report.overlap_totals = OverlapTotals(
        cold_ready=[cold_ready_lo, cold_ready_hi],
        cached_ready=[cached_ready_lo, cached_ready_hi],
        cold_all=[cold_all_lo, cold_all_hi],
        cached_all=[cached_all_lo, cached_all_hi],
    )
    return report


def inject_capability_blockers(
    report: "TimeReport",
    matrix: object,  # CapabilityMatrix — imported optionally to avoid circular
    model_axes: dict,
) -> "TimeReport":
    """Inject capability-matrix blocker verdicts into each ConstraintRow.

    This is the WS3 integration point. resolve() remains pure; this helper is
    called after resolve() by the routing layer.

    Parameters
    ----------
    report:
        TimeReport from resolve().
    matrix:
        CapabilityMatrix from load_capability_matrix().
    model_axes:
        Axis-bundle dict from ws1_axis_reader.read_axes().

    Returns
    -------
    TimeReport with each row's capability_blockers field populated.
    """
    # Run lookup once for all prereqs
    verdicts = matrix.lookup_blockers(model_axes)
    fold = matrix.fold(verdicts)

    for row in report.rows:
        blocked_verdicts = []
        # Gather blockers for prereqs in this row's chain
        for prereq, _tag in row.chain_annotated:
            bvlist = verdicts.get(prereq, [])
            for bv in bvlist:
                if bv.verdict == "blocked":
                    blocked_verdicts.append(bv)
        # Also include fold-level blockers not in chain_annotated
        for prereq_id, tlv in fold.items():
            if tlv.overall_verdict == "blocked":
                for bv in verdicts.get(prereq_id, []):
                    if bv.verdict == "blocked" and bv not in blocked_verdicts:
                        blocked_verdicts.append(bv)
                        break  # only first blocker per prereq
        row.capability_blockers = blocked_verdicts

    return report


def _fmt_range(lo: float, hi: float, unit: str = "hr") -> str:
    def _fmt(v: float) -> str:
        if v == int(v):
            return str(int(v))
        return f"{v:.1f}"
    return f"{_fmt(lo)}–{_fmt(hi)} {unit}"


def _print_report(report: TimeReport) -> None:
    data = _load()
    model_meta = data["models"][report.model]
    title = model_meta["display"]["title"]
    print(f"\nPlanned chain for {title}:\n")
    for row in report.rows:
        if row.constraint == "collider":
            print("  Collider (coming soon — skipped)")
            print("    No execution in this iteration.\n")
            continue
        blocked_str = ""
        if row.status == "BLOCKED":
            missing_strs = ", ".join(f"/{p}" for p in row.missing)
            blocked_str = f" [BLOCKED — missing: {missing_strs}]"
        label = row.constraint.capitalize().replace("_", " ")
        if row.constraint == "dd":
            label = "Direct detection"
        elif row.constraint == "id":
            label = "Indirect detection"
        elif row.constraint == "relic":
            label = "Relic density"
        print(f"  {label:<22}{row.status}{blocked_str}")
        chain_str = " → ".join(
            f"/{prereq} [{tag}]" for prereq, tag in row.chain_annotated
        )
        print(f"    {chain_str}")
        print(f"    cold: {_fmt_range(*row.cold)}   cached: {_fmt_range(*row.cached, 'hr')}")
        if row.capability_blockers:
            for bv in row.capability_blockers:
                prereq = getattr(bv, "prereq_id", str(bv))
                verdict = getattr(bv, "verdict", "blocked")
                axis = getattr(bv, "axis", "")
                blocker = getattr(bv, "blocker", None)
                desc = f"{prereq}: {verdict} on {axis}"
                if blocker:
                    desc += f" ({blocker})"
                print(f"    [CAP BLOCK] {desc}")
        print()

    t = report.overlap_totals
    print("Overlap-adjusted totals (shared prereqs counted once):")
    if t.cold_ready[1] > 0:
        print(f"  selected + ready : cold ~{_fmt_range(*t.cold_ready)},  cached ~{_fmt_range(*t.cached_ready)}")
    else:
        print("  selected + ready : (none ready)")
    print(f"  selected total   : cold ~{_fmt_range(*t.cold_all)},  cached ~{_fmt_range(*t.cached_all)}  (if all prereqs existed)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve constraint time estimates.")
    parser.add_argument("--model", required=True, help="Model id (singlet-doublet|2hdm-a|dark-su3)")
    parser.add_argument("--constraints", nargs="+", default=["relic", "dd", "id"], help="Selected constraint ids")
    args = parser.parse_args()
    _print_report(resolve(args.model, args.constraints))
