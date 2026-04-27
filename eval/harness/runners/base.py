"""
Abstract base class for eval runners.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..types import Task


class RunnerBase(ABC):
    """A runner executes a task and returns the actual output dict."""

    @abstractmethod
    def run(self, task: Task) -> dict[str, Any]:
        """Execute a task and return the output as a dict.

        The dict keys should match the keys used in the task's graders.
        For example, a task grading 'sigma_SI' expects the returned dict
        to contain a 'sigma_SI' key.

        Raises RuntimeError if execution fails.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this runner."""
        ...
