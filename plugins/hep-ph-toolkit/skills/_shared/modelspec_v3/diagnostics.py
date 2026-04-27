"""Validator diagnostics."""
from dataclasses import dataclass
from typing import Literal, Optional

Severity = Literal['error', 'warning']


@dataclass(frozen=True)
class Diagnostic:
    stage: int                      # 1, 2, or 3
    severity: Severity
    code: str                       # e.g. 'SCHEMA_TYPE', 'REF_UNDECLARED'
    path: str                       # JSONPointer
    message: str
    hint: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'stage': self.stage, 'severity': self.severity,
            'code': self.code, 'path': self.path,
            'message': self.message, 'hint': self.hint,
        }
