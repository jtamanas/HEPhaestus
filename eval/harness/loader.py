"""
Load task definitions from YAML and compute expected values from reference functions.
"""

import importlib
from pathlib import Path
from typing import Any

import yaml

from .types import Task, GraderConfig


TASKS_DIR = Path(__file__).parent.parent / "tasks"


def _parse_grader(raw: dict) -> GraderConfig:
    """Parse a grader config dict from YAML into a GraderConfig."""
    return GraderConfig(
        type=raw["type"],
        key=raw.get("key", ""),
        tolerance=raw.get("tolerance", 0.05),
        expected=raw.get("expected"),
        pattern=raw.get("pattern", ""),
        path=raw.get("path", ""),
        key_a=raw.get("key_a", ""),
        key_b=raw.get("key_b", ""),
    )


def _resolve_reference_fn(fn_name: str) -> callable:
    """Resolve a reference function name to a callable.

    Names are relative to eval.harness.refs, e.g. 'sd_sigma_si_tree'.
    """
    module = importlib.import_module("eval.harness.refs")
    fn = getattr(module, fn_name, None)
    if fn is None:
        raise ValueError(f"Reference function '{fn_name}' not found in eval.harness.refs")
    return fn


def load_tasks(tier: int | None = None) -> list[Task]:
    """Load all tasks, optionally filtered by tier.

    Computes expected values by calling each task's reference function.
    """
    tasks = []
    for yaml_path in sorted(TASKS_DIR.glob("*.yaml")):
        with open(yaml_path) as f:
            raw_tasks = yaml.safe_load(f)
        if raw_tasks is None:
            continue
        for raw in raw_tasks:
            task_tier = raw["tier"]
            if tier is not None and task_tier != tier:
                continue

            graders = [_parse_grader(g) for g in raw.get("graders", [])]

            # Coerce reference_args values — PyYAML parses '1.0e6' as str
            ref_args = {}
            for k, v in raw.get("reference_args", {}).items():
                if isinstance(v, str):
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                ref_args[k] = v

            task = Task(
                id=raw["id"],
                tier=task_tier,
                model=raw["model"],
                prompt=raw["prompt"],
                reference_fn=raw["reference_fn"],
                reference_args=ref_args,
                graders=graders,
                tags=raw.get("tags", []),
                task_type=raw.get("task_type"),
                expected_outcome=raw.get("expected_outcome"),
            )

            # Compute expected values from the reference function
            ref_fn = _resolve_reference_fn(task.reference_fn)
            task.expected = ref_fn(**task.reference_args)

            tasks.append(task)

    return tasks
