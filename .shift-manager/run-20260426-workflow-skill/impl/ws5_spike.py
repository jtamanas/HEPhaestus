"""
ws5_spike.py — S0 router-output spike for WS5.

Calls route() for all 4 models × 2 modes (default + strict),
using the fixture registries (NOT the real _shared/ registries).

Outputs: intel/ws5_spike_<model>_<mode>.{json,md}

Usage:
    python3 .shift-manager/run-20260426-workflow-skill/impl/ws5_spike.py

Run from repo root.
"""
from __future__ import annotations

import json
import pathlib
import sys
import traceback

# ---------------------------------------------------------------------------
# Path setup — mirrors tests/conftest.py shim
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]  # hep-ph-agents/
SCRIPTS_DIR = REPO_ROOT / "plugins" / "workflow" / "skills" / "model-router" / "scripts"
HEP_PH_DEMO_SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

for _p in (str(SCRIPTS_DIR), str(HEP_PH_DEMO_SHARED)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from model_router.orchestrator import route  # noqa: E402
from model_router.types import RouterOptions  # noqa: E402

# ---------------------------------------------------------------------------
# Fixture registry paths
# ---------------------------------------------------------------------------
FIXTURES_DIR = (
    REPO_ROOT / "plugins" / "workflow" / "skills" / "model-router"
    / "tests" / "fixtures"
)
REGISTRY_DIR = FIXTURES_DIR / "registries"
CONSTRAINTS_PATH = REGISTRY_DIR / "constraints.yaml"
BLOCKER_CATALOG_PATH = REGISTRY_DIR / "blocker_catalog.yaml"
ANALYTIC_EXCEPTIONS_PATH = REGISTRY_DIR / "analytic_exceptions.yaml"

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
RUN_DIR = REPO_ROOT / ".shift-manager" / "run-20260426-workflow-skill"
INTEL_DIR = RUN_DIR / "intel"
INTEL_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Models and observables to spike
# ---------------------------------------------------------------------------
MODELS = [
    "singlet-doublet",
    "two-hdm-a",
    "dark-su3",
    "dark-su3-confining-synthetic",
]
OBSERVABLES = ["relic", "dd", "id"]
MODES = [
    ("default", False),
    ("strict", True),
]

# ---------------------------------------------------------------------------
# Spike loop
# ---------------------------------------------------------------------------
results_summary = []

for model_id in MODELS:
    for mode_name, strict in MODES:
        tag = f"{model_id.replace('-', '_')}_{mode_name}"
        json_path = INTEL_DIR / f"ws5_spike_{tag}.json"
        md_path = INTEL_DIR / f"ws5_spike_{tag}.md"

        print(f"\n{'='*60}")
        print(f"  SPIKE: model={model_id!r}  mode={mode_name}")
        print(f"{'='*60}")

        try:
            report = route(
                model_id=model_id,
                observables=OBSERVABLES,
                options=RouterOptions(strict=strict),
                constraints_path=CONSTRAINTS_PATH,
                blocker_catalog_path=BLOCKER_CATALOG_PATH,
                analytic_exceptions_path=ANALYTIC_EXCEPTIONS_PATH,
            )

            # Write JSON output
            json_data = {
                "model_id": model_id,
                "mode": mode_name,
                "exit_code": report.exit_code,
                "json_report": report.json_report,
            }
            json_path.write_text(json.dumps(json_data, indent=2))
            print(f"  -> JSON: {json_path}")

            # Write markdown output
            md_path.write_text(report.markdown_report or "")
            print(f"  -> MD:   {md_path}")

            # Quick summary
            jreport = report.json_report
            verdict = jreport.get("verdict", "?")
            exit_code = report.exit_code
            print(f"  verdict={verdict}  exit_code={exit_code}")

            # Print placements summary
            placements = jreport.get("placements", [])
            print(f"  placements ({len(placements)}):")
            for i, p in enumerate(placements):
                kind = p.get("kind", "?")
                exception_id = p.get("exception_id", None)
                position = p.get("position", "?")
                content_snippet = (p.get("content", "") or "")[:80].replace("\n", " ")
                print(f"    [{i}] kind={kind!r} exception_id={exception_id!r} position={position!r}")
                print(f"        content[0:80]={content_snippet!r}")

            # Per-observable summary
            per_obs = jreport.get("per_observable", {})
            for obs, obs_data in per_obs.items():
                status = obs_data.get("status", "?")
                active_chain = obs_data.get("active_chain")
                prereq_id = (active_chain or {}).get("prereq_id", None) if active_chain else None
                blockers = obs_data.get("blockers", [])
                per_cand = obs_data.get("per_candidate", [])
                print(f"  {obs}: status={status!r}  active_chain.prereq_id={prereq_id!r}  blockers={blockers!r}  per_candidate_len={len(per_cand)}")

            results_summary.append({
                "model_id": model_id,
                "mode": mode_name,
                "verdict": verdict,
                "exit_code": exit_code,
                "ok": True,
            })

        except Exception as exc:
            err_msg = f"EXCEPTION: {type(exc).__name__}: {exc}"
            print(f"  {err_msg}")
            traceback.print_exc()

            # Write error JSON
            error_data = {
                "model_id": model_id,
                "mode": mode_name,
                "error": type(exc).__name__,
                "error_msg": str(exc),
            }
            json_path.write_text(json.dumps(error_data, indent=2))
            md_path.write_text(f"# SPIKE ERROR\n\n{err_msg}\n\n```\n{traceback.format_exc()}\n```\n")

            results_summary.append({
                "model_id": model_id,
                "mode": mode_name,
                "error": type(exc).__name__,
                "error_msg": str(exc),
                "ok": False,
            })

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
print(f"\n\n{'='*60}")
print("SPIKE SUMMARY")
print(f"{'='*60}")
print(f"{'Model':<35} {'Mode':<10} {'Verdict/Error':<30} {'Exit'}")
print("-" * 85)
for r in results_summary:
    if r["ok"]:
        print(f"{r['model_id']:<35} {r['mode']:<10} {r['verdict']:<30} {r['exit_code']}")
    else:
        print(f"{r['model_id']:<35} {r['mode']:<10} ERROR:{r['error']:<24} n/a")

json_count = len(list(INTEL_DIR.glob("ws5_spike_*.json")))
print(f"\nJSON files in intel/: {json_count}")
