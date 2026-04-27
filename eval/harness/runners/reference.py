"""
Reference runner — calls analytical Python functions directly.

This runner validates the grading pipeline without needing Claude or MadGraph.
It calls the same reference function used to compute expected values, so it
should always pass (100% pass rate = graders and refs are self-consistent).
"""

from typing import Any

from ..types import Task
from ..loader import _resolve_reference_fn
from .base import RunnerBase


class ReferenceRunner(RunnerBase):
    """Executes tasks by calling the reference function directly."""

    def run(self, task: Task) -> dict[str, Any]:
        ref_fn = _resolve_reference_fn(task.reference_fn)
        return ref_fn(**task.reference_args)

    @property
    def name(self) -> str:
        return "reference"
