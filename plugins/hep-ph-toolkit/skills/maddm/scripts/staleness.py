"""MadDM direct-detection staleness detection.

Defense-in-depth guard against the frozen-SI hazard: MadDM
``direct_detection``-only reruns can serve a STALE/frozen spin-independent
cross-section -- bit-identical across genuinely different coupling points --
because the DD-assembly path does not always re-read the param card. The
canonical symptom is a sigma_SI frozen at the sentinel

    2.4258097266847696E-31 GeV^-2

independent of the Higgs-portal coupling. See
``maddm/SKILL.md`` (section "Frozen-SI DD-rerun staleness") and
``singlet-doublet/references/maddm-invocation.md``.

The runner (``maddm_run.generate_maddm_script``) emits a run-time cleanup
into the generated script so each run recomputes into a *fresh* output dir by
default, preventing the bug in our own plumbing. This module is
the LOUD GUARD that catches the case where upstream MadDM still serves a stale
value despite a fresh dir: given a parsed sigma_SI (and optionally the previous
run's sigma_SI plus a param-card fingerprint), it flags staleness and emits a
structured ``MADDM_STALE_DD_RESULT`` recoverable blocker.

Pure library -- no side effects beyond ``emit_stale_blocker`` writing to stderr.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

# The exact frozen sentinel observed across genuinely different coupling
# points (bit-identical MD5 of MadDM_results.txt DD section). Value in GeV^-2.
FROZEN_SI_SENTINEL: float = 2.4258097266847696e-31

# Blocker code registered in _shared/blocker_catalog.yaml.
STALE_DD_BLOCKER_CODE = "MADDM_STALE_DD_RESULT"

# Workaround pointer echoed in the blocker's user_instruction.
_FRESH_DIR_INSTRUCTION = (
    "Re-run direct_detection into a FRESH output dir: clear out_dir (e.g. "
    "`shutil.rmtree(out_dir, ignore_errors=True)`) before `output <out_dir>` / "
    "`launch -f`, then confirm the sigma_SI value actually moved relative to "
    "the previous coupling point. The runner "
    "(maddm/scripts/maddm_run.py::generate_maddm_script) does this by default "
    "when fresh=True, by emitting a `!rm -rf <out_dir>` line into the script "
    "that runs right before `output`; if you overrode fresh=False, remove "
    "that override. See maddm/SKILL.md section 'Frozen-SI DD-rerun staleness'."
)


def is_frozen_sentinel(si_value: float, tol: float = 0.0) -> bool:
    """Return True if *si_value* equals the known frozen sigma_SI sentinel.

    ``tol`` is an absolute tolerance in GeV^-2. The default 0.0 requires an
    exact float match, because the observed hazard reproduces the sentinel
    bit-for-bit; pass a small tolerance only if the parser rounds.
    """
    if si_value is None:
        return False
    return abs(float(si_value) - FROZEN_SI_SENTINEL) <= tol


def detect_stale_dd(
    si_value: float,
    *,
    previous_si: Optional[float] = None,
    previous_params_hash: Optional[str] = None,
    current_params_hash: Optional[str] = None,
    sentinel_tol: float = 0.0,
) -> Optional[dict[str, Any]]:
    """Detect a stale MadDM DD sigma_SI result.

    Flags staleness when EITHER:

    (i)  *si_value* equals the frozen sentinel ``FROZEN_SI_SENTINEL`` (within
         ``sentinel_tol``), OR
    (ii) *si_value* is bit-identical to *previous_si* while the two runs'
         param-card fingerprints (*current_params_hash* vs
         *previous_params_hash*) genuinely differ -- i.e. the couplings changed
         but sigma_SI did not respond.

    Returns a structured recoverable blocker dict (validates against
    ``blocker.schema.json``) when stale, else ``None``. Does not print; call
    :func:`emit_stale_blocker` to surface it on stderr.
    """
    reasons: list[str] = []

    if is_frozen_sentinel(si_value, tol=sentinel_tol):
        reasons.append("frozen_sentinel")

    params_differ = (
        previous_params_hash is not None
        and current_params_hash is not None
        and previous_params_hash != current_params_hash
    )
    bit_identical = (
        previous_si is not None and float(si_value) == float(previous_si)
    )
    if params_differ and bit_identical:
        reasons.append("unresponsive_to_param_change")

    if not reasons:
        return None

    context: dict[str, Any] = {
        "si_value": float(si_value),
        "reasons": reasons,
        "responded_to_param_change": False,
    }
    if previous_si is not None:
        context["previous_si"] = float(previous_si)
    if previous_params_hash is not None:
        context["previous_params_hash"] = previous_params_hash
    if current_params_hash is not None:
        context["current_params_hash"] = current_params_hash
    if "frozen_sentinel" in reasons:
        context["frozen_sentinel"] = FROZEN_SI_SENTINEL

    if "frozen_sentinel" in reasons:
        message = (
            f"MadDM sigma_SI = {float(si_value):.6e} GeV^-2 equals the known "
            "frozen sentinel: the DD-assembly path served a stale value that "
            "does not respond to the param card."
        )
    else:
        message = (
            f"MadDM sigma_SI = {float(si_value):.6e} GeV^-2 is bit-identical to "
            "the previous run despite different couplings: sigma_SI did not "
            "respond to the param-card change (stale DD result)."
        )

    return {
        "code": STALE_DD_BLOCKER_CODE,
        "mode": "recoverable",
        "message": message,
        "context": context,
        "user_instruction": _FRESH_DIR_INSTRUCTION,
    }


def emit_stale_blocker(blocker: dict[str, Any]) -> None:
    """Write *blocker* as a single JSON line on stderr (emit_blocker pattern)."""
    print(json.dumps(blocker), file=sys.stderr)


def check_and_emit(
    si_value: float,
    *,
    previous_si: Optional[float] = None,
    previous_params_hash: Optional[str] = None,
    current_params_hash: Optional[str] = None,
    sentinel_tol: float = 0.0,
) -> Optional[dict[str, Any]]:
    """Convenience: :func:`detect_stale_dd` and, if stale, emit on stderr.

    Returns the blocker dict (also emitted) or ``None`` when the sigma_SI looks
    responsive.
    """
    blocker = detect_stale_dd(
        si_value,
        previous_si=previous_si,
        previous_params_hash=previous_params_hash,
        current_params_hash=current_params_hash,
        sentinel_tol=sentinel_tol,
    )
    if blocker is not None:
        emit_stale_blocker(blocker)
    return blocker
