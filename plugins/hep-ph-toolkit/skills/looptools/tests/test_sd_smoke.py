"""
test_sd_smoke.py — Tier-3 real-tool GATED smoke for the singlet-doublet eval
(STEP3-DESIGN.md build-order item 3/4).  DOUBLE-GATED, committed-but-skipped:
  - @pytest.mark.smoke
  - skipif HEPPH_RUN_WOLFRAM_TESTS != "1"

Runs the REAL run_eval_sd.wls on the STEP2 chi1-pinned amplitude
(reduce_chi1/amp_reduced.m) at the canonical SD benchmark point, and asserts the
build-order item-3 acceptance: the eval EITHER

  (A) produces finite per-operator Wilson coefficients (SUCCESS, provisional), OR
  (B) fails LOUDLY at a NAMED guard (also acceptable).

Both are green here — what is NOT acceptable is a silent/empty/crash outcome.

The STEP2 artifact lives outside the repo; the test skips cleanly if it or the
SD SLHA is absent, so it never fails for environmental reasons.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"

_WOLFRAM_GATE = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS") != "1"

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        _WOLFRAM_GATE,
        reason="Set HEPPH_RUN_WOLFRAM_TESTS=1 (and have Wolfram + LoopTools "
               "MathLink) to run the real SD loop-DD smoke.",
    ),
]

# STEP2 artifact (outside the repo) + canonical SD SLHA.
STEP2_AMP = Path(
    "/Users/yianni/.claude/jobs/c703354a/tmp/loopset-step2/reduce_chi1/amp_reduced.m")
SD_SLHA = Path(
    "/Users/yianni/.local/share/hephaestus/models/singlet_doublet/runs/"
    "2026-07-11T1554Z-aee644cc/SPheno.spc")

# The named guards that constitute an ACCEPTABLE loud failure (outcome B).
NAMED_GUARDS = (
    "SD-AMP-ABBREVIATIONS-UNRESOLVED",
    "UNBOUND-MODEL-PARAMETERS",
    "LOOPTOOLS_AMPLITUDE_NONFINITE",
)


def _config():
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) \
        / "hephaestus" / "config.json"
    return json.loads(cfg.read_text()) if cfg.exists() else {}


def test_sd_eval_finite_coeffs_or_named_guard(tmp_path):
    if shutil.which("wolframscript") is None:
        pytest.skip("wolframscript not on PATH")
    if not STEP2_AMP.exists():
        pytest.skip(f"STEP2 amp not present: {STEP2_AMP}")
    if not SD_SLHA.exists():
        pytest.skip(f"SD SLHA not present: {SD_SLHA}")
    cfg = _config()
    lt = cfg.get("looptools_path", "")
    if not lt or not (Path(lt) / "bin" / "LoopTools").exists():
        pytest.skip("LoopTools MathLink binary not available")

    # Prepare the SD point.
    sys.path.insert(0, str(SCRIPTS_DIR))
    import prepare_point
    point = prepare_point.prepare_point(SD_SLHA, dm_pdg=9958431)
    point_path = tmp_path / "point.json"
    point_path.write_text(json.dumps(point, indent=2))
    out_path = tmp_path / "sd_eval_output.json"

    res = subprocess.run(
        [shutil.which("wolframscript"), "-script", str(SCRIPTS_DIR / "run_eval_sd.wls"),
         str(STEP2_AMP), str(point_path), "default_2018", str(out_path), lt],
        capture_output=True, text=True, timeout=1800,
    )
    log = (res.stdout or "") + (res.stderr or "")

    if out_path.exists() and out_path.stat().st_size > 0:
        # Outcome A — finite per-operator coefficients.
        doc = json.loads(out_path.read_text())
        assert doc["schema"] == "looptools_sd_coefficients/v1"
        assert doc["model"] == "singlet_doublet"
        wc = doc["wilson_coefficients"]
        for k in ("C_scalar", "C_twist2_1", "C_twist2_2"):
            v = wc[k]
            assert v == v and v not in (float("inf"), float("-inf")), f"{k} non-finite"
        assert doc["amplitude"]["finite"] is True
        # No sigma_SI at this stage (nucleon matching is item 4).
        assert doc.get("nucleon_matching") == "deferred_item4"
    else:
        # Outcome B — loud failure at a named guard (no silent/empty crash).
        assert res.returncode != 0, "empty output but exit 0 — silent failure"
        assert any(g in log for g in NAMED_GUARDS), (
            f"no named guard in driver log (rc={res.returncode}):\n{log[-2000:]}")
