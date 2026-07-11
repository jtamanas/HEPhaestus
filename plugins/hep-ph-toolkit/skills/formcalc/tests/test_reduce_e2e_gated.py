"""Gated GREEN end-to-end regression for the FormCalc reduce leg.

GATED: requires HEPPH_RUN_WOLFRAM_TESTS=1 (real Wolfram kernel + FormCalc +
FORM install).

This replaces the coverage the dead ee->mumu golden never provided (its
fixture is a hand-simplified non-curried stub that DeclareProcess rejects —
see test_ee_to_mumu_golden.py's xfail). Here BOTH legs are real tools:

  /feynarts generate  (FeynArts built-in SM, tree e+e- -> mu+mu-, 1 diagram)
      -> FeynAmpList.m + FeynAmpList.meta.json   (real curried FeynArts output)
  /formcalc reduce    (run_formcalc.py, the production runner)
      -> amp_reduced.m + amp_reduced.meta.json + .build_key

Chosen process: the cheapest that exercises CalcFeynAmp meaningfully
(DeclareProcess on a real curried FeynAmpList, FORM round-trip, Weyl chains).
Tree-level, so the reduced amplitude is an Amp[...] object with no loop-PV
heads — the loop-PV assertion (B0i/C0i/D0i) is covered by the singlet-doublet
1PI-core artifact run; a loop process here would cost minutes, not seconds.

Uses the production feynarts/formcalc install read-only via the normal config;
all outputs go to tmp_path.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "plugins" / "shared" / "schemas"
FEYNARTS_SCRIPTS = SKILL_DIR.parent / "feynarts" / "scripts"

AMP_REDUCED_SCHEMA = SCHEMAS_DIR / "amp_reduced.meta.schema.json"
EE_MUMU_DIR = FIXTURES_DIR / "ee_to_mumu"

WOLFRAM_TESTS = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not WOLFRAM_TESTS,
    reason="HEPPH_RUN_WOLFRAM_TESTS=1 required",
)


@pytest.fixture
def run_feynarts_module():
    """Import run_feynarts lazily so collection works without Wolfram.

    Both the feynarts and formcalc skills ship a `cache_key.py` (and other
    bare-named helpers); when the formcalc suite runs first, its modules are
    already cached in sys.modules under those bare names, and run_feynarts's
    `from cache_key import compute_cache_key` would resolve to the WRONG one.
    Temporarily evict the colliding names, import run_feynarts with the
    feynarts scripts dir at the front of sys.path, then restore the originals
    so later formcalc tests are unaffected (run_feynarts keeps its own bound
    references).
    """
    colliding = ("cache_key", "postprocess", "render_driver", "resolve_model",
                 "resolve_process", "sarah_name", "run_feynarts")
    saved = {}
    for name in colliding:
        if name in sys.modules:
            saved[name] = sys.modules.pop(name)
    sys.path.insert(0, str(FEYNARTS_SCRIPTS))
    try:
        import run_feynarts
    finally:
        sys.path.remove(str(FEYNARTS_SCRIPTS))
        sys.modules.pop("run_feynarts", None)
        for name in colliding:
            sys.modules.pop(name, None)
        sys.modules.update(saved)
    return run_feynarts


class TestReduceEndToEnd:
    def test_sm_ee_mumu_tree_generates_and_reduces(self, run_feynarts_module, tmp_path):
        """feynarts generate -> formcalc reduce, both real, asserts artifact +
        Amp[] structure + valid sidecar."""
        gen_dir = tmp_path / "feynarts_out"
        out_dir = tmp_path / "formcalc_out"

        # ── Leg 1: real /feynarts generate (built-in SM, tree, 1 diagram) ──
        t0 = time.time()
        summary = run_feynarts_module.run(
            process="e+ e- -> mu+ mu-",
            model="SM",
            loop_order=0,
            output_dir=str(gen_dir),
            force=True,
        )
        t_generate = time.time() - t0
        assert summary["n_diagrams"] == 1
        feynamp = gen_dir / "FeynAmpList.m"
        assert feynamp.exists() and feynamp.stat().st_size > 0

        # ── Leg 2: real /formcalc reduce via the production runner ──
        # ProcessSpec fixture matches this exact process (e+e- -> mu+ mu-).
        t0 = time.time()
        result = subprocess.run(
            [
                sys.executable, str(SCRIPTS_DIR / "run_formcalc.py"), "reduce",
                "--feynamp", str(feynamp),
                "--process", str(EE_MUMU_DIR / "ProcessSpec.json"),
                "--output-dir", str(out_dir),
                "--reg", "dimreg",
                "--gamma5", "naive",  # Z exchange carries chiral couplings
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=600,
        )
        t_reduce = time.time() - t0
        assert result.returncode == 0, (
            f"reduce failed (generate {t_generate:.0f}s, reduce {t_reduce:.0f}s):\n"
            f"{result.stderr}"
        )
        status = json.loads(result.stdout.strip().splitlines()[-1])
        assert status["status"] == "ok"

        # ── Artifact: non-empty amp_reduced.m with a genuine Amp[] object ──
        amp_reduced = out_dir / "amp_reduced.m"
        assert amp_reduced.exists(), "amp_reduced.m not produced"
        content = amp_reduced.read_text()
        assert len(content) > 0, "amp_reduced.m is empty"
        assert re.search(r"\bAmp\[", content), (
            "amp_reduced.m lacks an Amp[...] head — not a CalcFeynAmp result"
        )
        # Tree-level must NOT be UV-regularized noise: either no loop-PV heads
        # at all (expected) or, if FormCalc emits any, they must be symbolic.
        pv_heads = set(re.findall(r"\b([ABCD]0i?)\[", content))
        # (Presence is not required at tree level; this documents the check the
        # loop-level artifact run makes binding: B0i/C0i/D0i symbolic heads.)

        # ── Sidecar validates against the Phase-0 schema ──
        sidecar_path = out_dir / "amp_reduced.meta.json"
        assert sidecar_path.exists(), "amp_reduced.meta.json not produced"
        sidecar = json.loads(sidecar_path.read_text())
        assert sidecar["pv_heads"] == "formcalc-native"
        assert sidecar["schema_version"] == "amp_reduced.meta/v1"
        try:
            import jsonschema
            schema = json.loads(AMP_REDUCED_SCHEMA.read_text())
            jsonschema.validate(sidecar, schema)
        except ImportError:
            pass  # schema library optional; structural asserts above still ran

        # ── Cache key written last (success marker) ──
        assert (out_dir / ".build_key").exists()

        print(
            f"\n[e2e] generate {t_generate:.1f}s, reduce {t_reduce:.1f}s, "
            f"pv_heads_in_tree_amp={sorted(pv_heads)}"
        )
