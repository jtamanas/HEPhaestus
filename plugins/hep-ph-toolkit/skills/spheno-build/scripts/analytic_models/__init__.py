"""Registry of analytic spectrum modules.

Each entry: spec.name → module object with a `compute(spec, params) -> dict` entry.
See backends/analytic.py for the dispatch contract.
"""

from __future__ import annotations

import importlib.util as _ilu
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    p = _HERE / f"{name}.py"
    if not p.exists():
        return None
    s = _ilu.spec_from_file_location(f"analytic_models.{name}", p)
    m = _ilu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


singlet_doublet = _load("singlet_doublet")
stub_unimplemented = _load("stub_unimplemented")
dark_su3 = _load("dark_su3")

REGISTRY = {k: v for k, v in {
    "singlet_doublet": singlet_doublet,
    "stub_unimplemented": stub_unimplemented,
    "dark_su3": dark_su3,
}.items() if v is not None}
