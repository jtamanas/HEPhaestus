"""
Reporting and aggregation for eval results.
"""

import json
from datetime import datetime, timezone
from typing import Any

from collections import Counter

from .types import EvalReport, TaskResult, GradeStatus, OutcomeMode


def terminal_summary(report: EvalReport) -> str:
    """Format a terminal-friendly summary table."""
    lines = []
    lines.append("")
    lines.append(f"{'='*70}")
    lines.append(f"  Eval Report — runner: {report.runner}, "
                 f"trials: {report.n_trials}")
    lines.append(f"{'='*70}")

    for tier in (1, 2, 3):
        tier_results = report.by_tier(tier)
        if not tier_results:
            continue
        tier_names = {1: "Setup", 2: "Accuracy", 3: "Advanced"}
        n_pass = sum(1 for r in tier_results if r.any_pass)
        lines.append(f"\n  Tier {tier} — {tier_names.get(tier, '?')} "
                     f"({n_pass}/{len(tier_results)} pass)")
        lines.append(f"  {'-'*66}")

        for r in tier_results:
            status = "PASS" if r.any_pass else "FAIL"
            marker = " ✓" if r.any_pass else " ✗"
            rate = f"{r.pass_rate:.0%}" if report.n_trials > 1 else ""
            # Mode label from the first trial (trials are i.i.d. in practice)
            mode_label = _mode_label(r.trials[0] if r.trials else None)
            lines.append(
                f"  {marker} {r.task_id:<40s} {status:>4s}  {rate:<4s}  {mode_label}"
            )

            # Show failure details
            if not r.any_pass and r.trials:
                for grade in r.trials[0].grades:
                    if grade.status != GradeStatus.PASS:
                        lines.append(
                            f"      └─ {grade.grader_type}({grade.key}): "
                            f"{grade.message}")
                # Show blocker reason if present — this is a signal, not a bug
                if r.trials[0].blocked and r.trials[0].blocked_reason:
                    lines.append(
                        f"      └─ blocked: {r.trials[0].blocked_reason[:80]}")

    lines.append(f"\n{'='*70}")
    lines.append(f"  Total: {report.total_pass}/{report.total_tasks} tasks pass")
    if report.n_trials > 1:
        lines.append(f"  pass@1:  {report.pass_at_k(1):.1%}")
        lines.append(f"  pass@{report.n_trials}:  "
                     f"{report.pass_at_k():.1%}")
        lines.append(f"  pass^{report.n_trials}:  "
                     f"{report.pass_power_k():.1%}")

    # Outcome-mode breakdown — orthogonal to numeric pass/fail.
    # Counts first-trial mode for each task.
    mode_counts = _count_modes(report)
    if any(v > 0 for v in mode_counts.values()):
        lines.append(f"")
        lines.append(f"  Outcome modes (first-trial classification):")
        total_classifiable = sum(
            v for k, v in mode_counts.items() if k != OutcomeMode.NA
        )
        for mode in (
            OutcomeMode.MG_CORRECT,
            OutcomeMode.MG_WRONG,
            OutcomeMode.BLOCKED_CORRECTLY,
            OutcomeMode.REFERENCE_ONLY,
            OutcomeMode.PY_FALLBACK,
            OutcomeMode.NA,
        ):
            count = mode_counts.get(mode, 0)
            if count == 0:
                continue
            label = _mode_name(mode)
            if mode == OutcomeMode.NA:
                lines.append(f"    {label:<22s}  {count:>3d}")
            else:
                pct = (count / total_classifiable * 100.0
                       if total_classifiable else 0.0)
                lines.append(f"    {label:<22s}  {count:>3d}  ({pct:.0f}%)")
    lines.append(f"{'='*70}")
    lines.append("")
    return "\n".join(lines)


def _count_modes(report: EvalReport) -> Counter:
    counts: Counter = Counter()
    for r in report.task_results:
        if not r.trials:
            continue
        mode = r.trials[0].outcome_mode
        if mode is None:
            continue
        counts[mode] += 1
    return counts


def _mode_label(trial) -> str:
    """Short inline label for per-task display."""
    if trial is None or trial.outcome_mode is None:
        return ""
    return {
        OutcomeMode.MG_CORRECT: "[MG✓]",
        OutcomeMode.MG_WRONG: "[MG✗]",
        OutcomeMode.BLOCKED_CORRECTLY: "[blocked-ok]",
        OutcomeMode.REFERENCE_ONLY: "[ref-only]",
        OutcomeMode.PY_FALLBACK: "[py-fallback]",
        OutcomeMode.NA: "[algebra]",
    }.get(trial.outcome_mode, "")


def _mode_name(mode: OutcomeMode) -> str:
    return {
        OutcomeMode.MG_CORRECT: "MG used, correct",
        OutcomeMode.MG_WRONG: "MG used, wrong",
        OutcomeMode.BLOCKED_CORRECTLY: "Blocked (correctly)",
        OutcomeMode.REFERENCE_ONLY: "Reference-only estimate",
        OutcomeMode.PY_FALLBACK: "Python fallback",
        OutcomeMode.NA: "Algebra (N/A)",
    }.get(mode, mode.value)


def to_json(report: EvalReport) -> dict[str, Any]:
    """Serialize an EvalReport to a JSON-compatible dict."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runner": report.runner,
        "n_trials": report.n_trials,
        "total_tasks": report.total_tasks,
        "total_pass": report.total_pass,
        "pass_at_1": report.pass_at_k(1),
        "pass_at_k": report.pass_at_k(),
        "pass_power_k": report.pass_power_k(),
        "by_tier": {
            tier: {
                "total": len(report.by_tier(tier)),
                "pass": sum(1 for r in report.by_tier(tier) if r.any_pass),
            }
            for tier in (1, 2, 3)
            if report.by_tier(tier)
        },
        "outcome_modes": {
            mode.value: count
            for mode, count in _count_modes(report).items()
        },
        "tasks": [
            {
                "id": r.task_id,
                "tier": r.tier,
                "model": r.model,
                "tags": r.tags,
                "pass_rate": r.pass_rate,
                "any_pass": r.any_pass,
                "all_pass": r.all_pass,
                "trials": [
                    {
                        "trial": t.trial_number,
                        "passed": t.passed,
                        "error": t.error,
                        "outcome_mode": (
                            t.outcome_mode.value if t.outcome_mode else None
                        ),
                        "used_madgraph": t.used_madgraph,
                        "blocked": t.blocked,
                        "blocked_reason": t.blocked_reason,
                        **(
                            {"reference_method": t.reference_method}
                            if t.reference_method
                            else {}
                        ),
                        "grades": [
                            {
                                "grader": g.grader_type,
                                "key": g.key,
                                "status": g.status.value,
                                "expected": _safe_serialize(g.expected),
                                "actual": _safe_serialize(g.actual),
                                "message": g.message,
                            }
                            for g in t.grades
                        ],
                    }
                    for t in r.trials
                ],
            }
            for r in report.task_results
        ],
    }


def write_json(report: EvalReport, path: str) -> None:
    """Write the report as JSON to a file."""
    with open(path, "w") as f:
        json.dump(to_json(report), f, indent=2)


def _safe_serialize(val: Any) -> Any:
    """Make a value JSON-serializable."""
    if val is None:
        return None
    if isinstance(val, float):
        if val != val:  # NaN
            return "NaN"
        if abs(val) == float("inf"):
            return "Inf" if val > 0 else "-Inf"
        return val
    return str(val) if not isinstance(val, (int, bool, list, dict)) else val
