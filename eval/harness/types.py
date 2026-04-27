"""
Core types for the eval harness.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Tier(Enum):
    SETUP = 1
    ACCURACY = 2
    ADVANCED = 3


class GradeStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class OutcomeMode(Enum):
    """Classifier for how an agent trial concluded.

    - MG_CORRECT:        Used MadGraph/MadDM and produced correct answer.
    - MG_WRONG:          Used MadGraph/MadDM but produced wrong answer
                         (or violated the blocker contract).
    - BLOCKED_CORRECTLY: Task required MG, MG was unavailable, and the agent
                         emitted a well-formed {"status":"blocked", ...} payload
                         rather than fabricating a value.
    - PY_FALLBACK:       Task required MG, agent used pure Python instead.
    - NA:                Task did not require MG (transcription / algebra /
                         unit check) and the outcome is judged by pass/fail alone.
    - RUNNER_ERROR:      Runner crashed, timed out, or otherwise failed before
                         a classifiable output was produced. Behavior is unknown.
    - REFERENCE_ONLY:    Agent returned a labeled closed-form estimate behind
                         the opt-in `reference_only` status — desirable for
                         pedagogical/quick-estimate tasks; NOT counted as
                         PY_FALLBACK.
    """
    MG_CORRECT = "MG_CORRECT"
    MG_WRONG = "MG_WRONG"
    BLOCKED_CORRECTLY = "BLOCKED_CORRECTLY"
    PY_FALLBACK = "PY_FALLBACK"
    NA = "NA"
    RUNNER_ERROR = "RUNNER_ERROR"
    REFERENCE_ONLY = "REFERENCE_ONLY"


@dataclass
class GraderConfig:
    """Configuration for a single grader."""
    type: str
    key: str = ""
    tolerance: float = 0.05
    expected: Any = None
    pattern: str = ""
    path: str = ""
    key_a: str = ""
    key_b: str = ""


@dataclass
class Task:
    """A single eval task."""
    id: str
    tier: int
    model: str
    prompt: str
    reference_fn: str
    reference_args: dict[str, Any]
    graders: list[GraderConfig]
    tags: list[str] = field(default_factory=list)
    expected: dict[str, Any] = field(default_factory=dict)
    # New in PR-A: explicit task metadata (soft-deprecates the prompt regex).
    # task_type in {"mg_required", "algebra", "na"}.
    task_type: str | None = None
    # Optional: for tasks known to be gated on missing tooling
    # (e.g. a BLOCKED_CORRECTLY answer is the canonical correct outcome).
    expected_outcome: str | None = None


@dataclass
class GradeResult:
    """Result from a single grader on a single trial."""
    grader_type: str
    key: str
    status: GradeStatus
    expected: Any = None
    actual: Any = None
    message: str = ""


@dataclass
class TrialResult:
    """Result from one trial of one task."""
    task_id: str
    trial_number: int
    passed: bool
    grades: list[GradeResult]
    actual: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    token_count: int = 0
    tool_calls: int = 0
    wall_time_s: float = 0.0
    # New in PR-A: outcome-mode classification for agent runs.
    outcome_mode: OutcomeMode | None = None
    # Signal flags feeding the classifier — useful for downstream histograms.
    used_madgraph: bool = False
    blocked: bool = False
    blocked_reason: str | None = None
    contract_violated: bool = False
    # New in PR-D follow-up: set when status == "reference_only".
    reference_method: str | None = None


@dataclass
class TaskResult:
    """Aggregated result for one task across all trials."""
    task_id: str
    tier: int
    model: str
    tags: list[str]
    trials: list[TrialResult]

    @property
    def n_pass(self) -> int:
        return sum(1 for t in self.trials if t.passed)

    @property
    def n_trials(self) -> int:
        return len(self.trials)

    @property
    def pass_rate(self) -> float:
        if not self.trials:
            return 0.0
        return self.n_pass / self.n_trials

    @property
    def all_pass(self) -> bool:
        return all(t.passed for t in self.trials)

    @property
    def any_pass(self) -> bool:
        return any(t.passed for t in self.trials)


@dataclass
class EvalReport:
    """Full eval report across all tasks."""
    task_results: list[TaskResult]
    runner: str
    n_trials: int

    @property
    def total_tasks(self) -> int:
        return len(self.task_results)

    @property
    def total_pass(self) -> int:
        return sum(1 for r in self.task_results if r.any_pass)

    def by_tier(self, tier: int) -> list[TaskResult]:
        return [r for r in self.task_results if r.tier == tier]

    def pass_at_k(self, k: int | None = None) -> float:
        """Fraction of tasks with at least one pass in k trials."""
        if k is None:
            k = self.n_trials
        count = 0
        for r in self.task_results:
            trials = r.trials[:k]
            if any(t.passed for t in trials):
                count += 1
        return count / self.total_tasks if self.total_tasks else 0.0

    def pass_power_k(self, k: int | None = None) -> float:
        """Fraction of tasks where ALL k trials pass (consistency)."""
        if k is None:
            k = self.n_trials
        count = 0
        for r in self.task_results:
            trials = r.trials[:k]
            if len(trials) == k and all(t.passed for t in trials):
                count += 1
        return count / self.total_tasks if self.total_tasks else 0.0
