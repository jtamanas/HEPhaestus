"""Backend protocol + shared types for /spheno-build spectrum dispatch.

Two concrete backends live alongside this module:
    backends.spheno   — wraps run_point.run (legacy SPheno CLI path).
    backends.analytic — dispatches to a Python module in analytic_models/.

Dispatch glue lives in scripts/dispatcher.py.
"""

from __future__ import annotations

from typing import Literal, Protocol, TypedDict


class BackendResult(TypedDict, total=False):
    status: Literal["ok", "recoverable", "fatal"]
    blocker_code: str | None
    slha_path: str | None
    summary: dict | None
    cache_hit: bool
    backend: Literal["spheno", "analytic"]
    timing_s: float


class SpectrumBackend(Protocol):
    name: str

    def compute(
        self,
        model_name: str,
        spec: dict,
        params: dict,
        out_dir,
        config: dict,
    ) -> BackendResult: ...
