"""dispatcher.py — Backend-agnostic spectrum dispatch for /spheno-build.

Chooses the SpectrumBackend based on spec['backends']['spectrum'] (default
'spheno' when outputs contains 'spheno') and forwards (model_name, spec, params,
out_dir, config). Used by run_spheno.py (single-point) and scan.py (parameter
scan). All classification is backend-scoped: SPHENO_* for spheno path,
ANALYTIC_* for analytic path.

If a spec has no 'backends' key at all (and outputs doesn't list 'spheno'),
resolution silently falls back to the analytic backend -- the compiled SPheno
binary is NOT run. That fallback prints a one-line warning to stderr so it
isn't mistaken for a real SPheno run.

Test-injection hook: dispatch() accepts an optional ``backend_factory`` kwarg.
When provided, the caller controls backend instantiation (used by
test_spheno_backend_unchanged.py and any future consumer that needs to inject
a fake backend). Default None preserves the production dynamic-load path.
"""

from __future__ import annotations

import importlib.util as _ilu
import sys
from pathlib import Path
from typing import Callable, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolve_backend_name(spec: dict) -> str:
    backends = spec.get("backends") or {}
    if "spectrum" in backends:
        return backends["spectrum"]
    outputs = spec.get("outputs", [])
    if "spheno" in outputs:
        return "spheno"
    # Falling through to the analytic default. Warn whenever we land here
    # WITHOUT an explicit spectrum selection -- i.e. the author made no
    # spectrum choice, whether the 'backends' key is absent entirely, empty
    # ({}), or present but spectrum-less ({"foo": "x"}). Only backends.spectrum
    # (handled above) or "spheno" in outputs counts as an explicit choice, so
    # if we reach this point the selection was never explicit. This is the
    # silent path that made the compiled SPheno binary look like it ran when
    # it never did (SPINFO said "hephaestus analytic" and output was still
    # named SPheno.spc).
    print(
        "spheno-build: spec makes no explicit spectrum-backend choice; "
        "defaulting to the ANALYTIC backend — compiled SPheno was NOT run",
        file=sys.stderr,
    )
    return "analytic"


def _load_backend(name: str):
    if name == "spheno":
        mod = _load("backends_spheno",
                    _SCRIPT_DIR / "backends" / "spheno.py")
        return mod.SphenoBackend()
    if name == "analytic":
        mod = _load("backends_analytic",
                    _SCRIPT_DIR / "backends" / "analytic.py")
        return mod.AnalyticBackend()
    raise ValueError(f"Unknown backend: {name!r}")


def dispatch(model_name: str, spec: dict, params: dict,
             out_dir: Path, config: dict,
             backend_factory: Optional[Callable[[str], object]] = None) -> dict:
    """Dispatch a single spectrum computation to the selected backend.

    Parameters
    ----------
    model_name, spec, params, out_dir, config :
        Standard dispatch arguments.
    backend_factory :
        Optional callable ``(backend_name: str) -> SpectrumBackend``. When
        provided, it is used to build the backend instance instead of the
        internal ``_load_backend``. Intended for test injection (e.g., to
        pass a fake SPheno backend that avoids touching run_point.py). The
        production path (None) preserves the existing dynamic-load behaviour
        byte-for-byte.
    """
    backend_name = _resolve_backend_name(spec)
    if backend_factory is not None:
        backend = backend_factory(backend_name)
    else:
        backend = _load_backend(backend_name)
    return backend.compute(model_name, spec, params, out_dir, config)
