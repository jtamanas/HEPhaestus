"""
parse_eval_output.py — parse the Wolfram/LoopTools driver output into Python.

The driver (`run_eval.wls`) writes a JSON document (`eval_output.json`) holding
the numerically-evaluated loop amplitude: the effective DM–nucleon couplings,
UV/IR/gauge bookkeeping, and run metadata.  This module loads it, validates the
required shape, and raises on a non-finite / UV-non-cancelled amplitude.

This is pure transport — no physics.  The frozen fixture
`tests/fixtures/eval_output.json` is a hand-authored stand-in for a real run and
stubs the Wolfram subprocess in Tier-1/Tier-2 tests (build plan §3).
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_TAG = "looptools_eval_output/v1"

# Tolerance for residual UV (1/ε) / gauge-parameter dependence that should cancel.
UV_RESIDUE_TOL = 1.0e-9


class AmplitudeNonFinite(ValueError):
    """Raised when the evaluated amplitude is non-finite or has a residual pole."""


def parse(eval_output: dict | str | Path) -> dict:
    """Validate + normalise a driver output document.

    Accepts a dict, a path, or a JSON string.  Returns the normalised dict.
    Raises ValueError on malformed shape, AmplitudeNonFinite on a bad amplitude.
    """
    if isinstance(eval_output, dict):
        doc = eval_output
    else:
        # A path-like string is read from disk; a JSON document passed as a string
        # is parsed directly.  Path(...).exists() can raise OSError (ENAMETOOLONG)
        # when handed a long JSON string, so guard it and fall through to json.loads.
        try:
            p = Path(eval_output)
            is_file = p.exists()
        except OSError:
            is_file = False
        if is_file:
            doc = json.loads(p.read_text())
        else:
            doc = json.loads(str(eval_output))

    schema = doc.get("schema")
    if schema != SCHEMA_TAG:
        raise ValueError(
            f"eval_output schema mismatch: expected {SCHEMA_TAG!r}, got {schema!r}"
        )

    for key in ("m_dm_gev", "amplitude", "effective_couplings"):
        if key not in doc:
            raise ValueError(f"eval_output missing required key: {key!r}")

    amp = doc["amplitude"]
    couplings = doc["effective_couplings"]

    for fk in ("f_p_si_gev_minus2", "f_n_si_gev_minus2"):
        if fk not in couplings:
            raise ValueError(f"effective_couplings missing required key: {fk!r}")

    # Finiteness / UV-cancellation gate.
    finite = bool(amp.get("finite", False))
    uv = float(amp.get("uv_pole_residue", 0.0))
    gauge = float(amp.get("gauge_parameter_dependence", 0.0))

    def _isfinite(x) -> bool:
        return x is not None and x == x and abs(x) != float("inf")

    if not finite:
        raise AmplitudeNonFinite(
            f"Driver flagged amplitude non-finite (point {doc.get('point_id')!r})"
        )
    for fk in ("f_p_si_gev_minus2", "f_n_si_gev_minus2"):
        if not _isfinite(couplings[fk]):
            raise AmplitudeNonFinite(
                f"Effective coupling {fk} is non-finite (point {doc.get('point_id')!r})"
            )
    if abs(uv) > UV_RESIDUE_TOL:
        raise AmplitudeNonFinite(
            f"Residual UV pole {uv} exceeds tol {UV_RESIDUE_TOL} "
            f"(1/ε not cancelled; point {doc.get('point_id')!r})"
        )
    if abs(gauge) > UV_RESIDUE_TOL:
        raise AmplitudeNonFinite(
            f"Gauge-parameter dependence {gauge} exceeds tol {UV_RESIDUE_TOL} "
            f"(point {doc.get('point_id')!r})"
        )

    return doc
