"""
CLI entrypoint for the eval harness.

Usage:
    python -m eval.harness.run --runner reference
    python -m eval.harness.run --runner reference --tier 2
    python -m eval.harness.run --runner reference --trials 5
    python -m eval.harness.run --runner reference --output results.json
    python -m eval.harness.run --runner claude --model sonnet --tier 2
"""

import argparse
import time
import sys

from .types import EvalReport, TaskResult, TrialResult, GradeStatus, OutcomeMode
from .graders import run_graders
from .loader import load_tasks
from .outcome import annotate_trial
from .runners.reference import ReferenceRunner
from .runners.claude_code import ClaudeCodeRunner
from .report import terminal_summary, write_json


RUNNERS = {
    "reference": ReferenceRunner,
    "claude": ClaudeCodeRunner,
}


def _is_agent_run(runner) -> bool:
    """True when the runner produces outputs that need outcome classification.

    The reference runner calls Python directly; outcome modes are not
    meaningful for it (everything would be NA or MG_CORRECT by definition).
    """
    return isinstance(runner, ClaudeCodeRunner)


def run_trial(runner, task, trial_number: int) -> TrialResult:
    """Execute one trial of one task."""
    t0 = time.time()
    is_agent = _is_agent_run(runner)

    try:
        actual = runner.run(task)
    except Exception as e:
        trial = TrialResult(
            task_id=task.id,
            trial_number=trial_number,
            passed=False,
            grades=[],
            error=str(e),
            wall_time_s=time.time() - t0,
        )
        if is_agent:
            # PR-A: timeouts/crashes get RUNNER_ERROR instead of silently
            # collapsing into outcome_mode=None.
            meta = getattr(runner, "last_meta", {}) or {}
            annotate_trial(
                trial, task,
                tool_uses=meta.get("tool_uses"),
                answer=meta.get("raw_answer"),
                runner_error=True,
            )
            # Force RUNNER_ERROR even if annotate_trial chose otherwise.
            trial.outcome_mode = OutcomeMode.RUNNER_ERROR
        return trial

    grades = run_graders(task.expected, actual, task.graders)
    passed = all(g.status == GradeStatus.PASS for g in grades)

    # Capture token/cost metadata from Claude runner.
    token_count = 0
    tool_calls = 0
    if hasattr(runner, "last_meta"):
        meta = runner.last_meta
        token_count = meta.get("input_tokens", 0) + meta.get("output_tokens", 0)
        tool_calls = meta.get("num_turns", 0)

    trial = TrialResult(
        task_id=task.id,
        trial_number=trial_number,
        passed=passed,
        grades=grades,
        actual=actual,
        wall_time_s=time.time() - t0,
        token_count=token_count,
        tool_calls=tool_calls,
    )

    if is_agent:
        meta = getattr(runner, "last_meta", {}) or {}
        annotate_trial(
            trial, task,
            tool_uses=meta.get("tool_uses"),
            answer=meta.get("raw_answer"),
            runner_error=False,
        )

    return trial


def main():
    parser = argparse.ArgumentParser(description="Run the eval harness")
    parser.add_argument("--runner", choices=list(RUNNERS.keys()),
                        default="reference",
                        help="Which runner backend to use (default: reference)")
    parser.add_argument("--tier", type=int, default=None,
                        help="Run only tasks from this tier (1, 2, or 3)")
    parser.add_argument("--trials", type=int, default=1,
                        help="Number of trials per task (default: 1)")
    parser.add_argument("--output", type=str, default=None,
                        help="Write JSON report to this path")
    parser.add_argument("--task", type=str, default=None,
                        help="Run only this task ID")
    parser.add_argument("--tag", type=str, default=None,
                        help="Run only tasks with this tag")
    # Claude runner options
    parser.add_argument("--model", type=str, default="sonnet",
                        help="Claude model to use (default: sonnet)")
    parser.add_argument("--max-budget", type=float, default=1.0,
                        help="Max USD per task for Claude runner (default: 1.0)")
    parser.add_argument("--timeout", type=int, default=300,
                        help="Timeout in seconds per task (default: 300)")
    parser.add_argument("--no-skills", action="store_true",
                        help="Run without MadGraph/MadDM skills (baseline)")
    args = parser.parse_args()

    # Load tasks
    tasks = load_tasks(tier=args.tier)
    if args.task:
        tasks = [t for t in tasks if t.id == args.task]
    if args.tag:
        tasks = [t for t in tasks if args.tag in t.tags]

    if not tasks:
        print("No tasks matched the filters.")
        sys.exit(1)

    print(f"Loaded {len(tasks)} tasks"
          f"{f' (tier {args.tier})' if args.tier else ''}")

    # Create runner
    if args.runner == "claude":
        runner = ClaudeCodeRunner(
            model=args.model,
            max_budget_usd=args.max_budget,
            timeout_s=args.timeout,
            skills=not args.no_skills,
        )
    else:
        runner = RUNNERS[args.runner]()
    print(f"Runner: {runner.name}")
    print(f"Trials: {args.trials}")
    print()

    # Execute
    task_results = []
    for task in tasks:
        trials = []
        for trial_num in range(1, args.trials + 1):
            result = run_trial(runner, task, trial_num)
            trials.append(result)

        task_result = TaskResult(
            task_id=task.id,
            tier=task.tier,
            model=task.model,
            tags=task.tags,
            trials=trials,
        )
        task_results.append(task_result)

        # Progress indicator
        status = "PASS" if task_result.any_pass else "FAIL"
        last_trial = task_result.trials[-1]
        cost_str = ""
        if last_trial.token_count > 0:
            cost_str = f"  ({last_trial.token_count} tok, {last_trial.wall_time_s:.1f}s)"
        err_str = f"  [{last_trial.error[:60]}]" if last_trial.error else ""
        mode_str = ""
        if last_trial.outcome_mode is not None:
            mode_str = f"  <{last_trial.outcome_mode.value}>"
        print(f"  {status}  {task.id}{cost_str}{mode_str}{err_str}")

    # Report
    report = EvalReport(
        task_results=task_results,
        runner=runner.name,
        n_trials=args.trials,
    )

    print(terminal_summary(report))

    if args.output:
        write_json(report, args.output)
        print(f"JSON report written to {args.output}")


if __name__ == "__main__":
    main()
