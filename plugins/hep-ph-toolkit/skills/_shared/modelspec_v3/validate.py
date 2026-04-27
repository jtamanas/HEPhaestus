"""Validation orchestrator."""
from dataclasses import dataclass, field
from typing import List
from .diagnostics import Diagnostic
from .stage1 import validate_schema
from .stage2 import validate_refs
from .anomaly import check_anomalies
from .per_term import check_per_term_charges, check_discrete_symmetry


@dataclass
class ValidationResult:
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)

    @property
    def all(self) -> List[Diagnostic]:
        return list(self.errors) + list(self.warnings)


def validate(spec: dict) -> ValidationResult:
    """Run all validation stages, halting the pipeline on errors.

    Stage 2 and 3 require Stage 1 to be clean (no errors).
    Stage 3 requires Stage 2 to be clean (no errors).
    Stage 2 warnings (rare) are surfaced even if Stage 3 is not run.
    """
    res = ValidationResult()

    s1 = validate_schema(spec)
    res.errors.extend(s1)
    if s1:
        return res   # Stage 2/3 require valid schema

    s2 = validate_refs(spec)
    s2_errors = [d for d in s2 if d.severity == 'error']
    res.errors.extend(s2_errors)
    # warnings from Stage 2 (rare, but possible) — surface them
    res.warnings.extend(d for d in s2 if d.severity == 'warning')
    if s2_errors:
        return res

    res.warnings.extend(check_anomalies(spec))
    res.warnings.extend(check_per_term_charges(spec))
    res.warnings.extend(check_discrete_symmetry(spec))
    return res
