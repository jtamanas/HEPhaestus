#!/usr/bin/env python3
"""
Plot A/B Test Eval Orchestrator.

Generates synthetic data, spawns parallel Claude CLI agents (one with design
skills, one without), collects output PNGs, and builds an HTML voting page.

Usage:
    python run_eval.py              # Full run
    python run_eval.py --data-only  # Only generate data
    python run_eval.py --view-only  # Only build viewer from existing outputs
    python run_eval.py --max-parallel 2  # Limit concurrent agent pairs
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ensure imports work regardless of cwd
_EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_EVAL_DIR))

from test_cases import ALL_CASES
from prompts import build_with_skills_prompt, build_without_skills_prompt

DATA_DIR = _EVAL_DIR / "data"
OUTPUT_DIR = _EVAL_DIR / "outputs"
RESULTS_DIR = _EVAL_DIR / "results"
VIEWER_TEMPLATE = _EVAL_DIR / "viewer_template.html"
VIEWER_OUTPUT = _EVAL_DIR / "viewer.html"


def generate_data() -> dict[str, Path]:
    """Generate synthetic data for all test cases. Returns {case_id: npz_path}."""
    DATA_DIR.mkdir(exist_ok=True)
    paths = {}
    for case in ALL_CASES:
        path = case["generate"](DATA_DIR)
        paths[case["id"]] = path
        print(f"  ✓ {case['id']}: {path.name}")
    return paths


def run_agent(
    case_id: str,
    variant: str,  # "with_skills" or "without_skills"
    prompt: str,
    data_src: Path,
    output_dir: Path,
) -> dict:
    """Run a single Claude CLI agent and return result metadata."""
    start = time.time()
    result = {"case_id": case_id, "variant": variant, "success": False, "error": None}

    # Create isolated temp directory outside the repo tree
    with tempfile.TemporaryDirectory(prefix=f"hep_ab_{case_id}_{variant}_") as tmpdir:
        # Copy data file into temp dir for proper isolation
        local_data = Path(tmpdir) / data_src.name
        shutil.copy2(data_src, local_data)

        # Replace the absolute data path in the prompt with the local copy
        prompt = prompt.replace(str(data_src), str(local_data))

        plot_output = output_dir / "plot.png"

        cmd = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            "--allowedTools", "Edit,Write,Bash,Read",
            "--max-budget-usd", "1.00",
            "--disable-slash-commands",
            "-p", prompt,
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=300,  # 5-minute hard timeout per agent
            )

            if plot_output.exists():
                result["success"] = True
            else:
                result["error"] = "plot.png not found in output directory"
                # Check if agent wrote plot.png in temp dir instead
                tmp_plot = Path(tmpdir) / "plot.png"
                if tmp_plot.exists():
                    plot_output.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(tmp_plot, plot_output)
                    result["success"] = True
                    result["error"] = None

            if proc.returncode != 0 and not result["success"]:
                result["error"] = f"Exit code {proc.returncode}: {proc.stderr[:500]}"

        except subprocess.TimeoutExpired:
            result["error"] = "Timed out after 300s"
        except FileNotFoundError:
            result["error"] = "claude CLI not found. Is it installed and on PATH?"

    result["duration_s"] = round(time.time() - start, 1)
    return result


def run_all_agents(data_paths: dict[str, Path], max_parallel: int = 4) -> list[dict]:
    """Run all test cases with bounded parallelism.

    Uses a flat pool of individual agent runs (not nested case pools) to avoid
    the claude CLI bootstrap race condition that occurs when too many processes
    start at the exact same instant. A small stagger between submissions
    gives each process time to acquire its temp file lock.
    """
    all_results = []
    jobs = []

    for case in ALL_CASES:
        case_id = case["id"]
        data_path = data_paths[case_id]
        skill_cat = case["skill_category"]
        desc = case["description"]

        out_with = OUTPUT_DIR / case_id / "with_skills"
        out_without = OUTPUT_DIR / case_id / "without_skills"
        out_with.mkdir(parents=True, exist_ok=True)
        out_without.mkdir(parents=True, exist_ok=True)

        prompt_with = build_with_skills_prompt(desc, skill_cat, str(data_path), str(out_with))
        prompt_without = build_without_skills_prompt(desc, str(data_path), str(out_without))

        jobs.append((case_id, "with_skills", prompt_with, data_path, out_with))
        jobs.append((case_id, "without_skills", prompt_without, data_path, out_without))

    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        futures = {}
        for i, (cid, variant, prompt, dsrc, odir) in enumerate(jobs):
            # Stagger submissions by 2s to avoid claude CLI bootstrap race
            if i > 0:
                time.sleep(2)
            f = pool.submit(run_agent, cid, variant, prompt, dsrc, odir)
            futures[f] = (cid, variant)

        for future in as_completed(futures):
            cid, variant = futures[future]
            try:
                r = future.result()
                status = "✓" if r["success"] else "✗"
                print(f"  {status} {cid}/{r['variant']} ({r['duration_s']}s)")
                if r["error"]:
                    print(f"    Error: {r['error']}")
                all_results.append(r)
            except Exception as e:
                print(f"  ✗ {cid}/{variant}: exception: {e}")
                all_results.append({"case_id": cid, "variant": variant, "success": False, "error": str(e)})

    return all_results


def _img_to_base64(path: Path) -> str:
    """Convert an image file to a base64 data URI."""
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_viewer() -> Path:
    """Build the HTML voting viewer from the template and output images."""
    cases_data = []

    for case in ALL_CASES:
        case_id = case["id"]
        with_path = OUTPUT_DIR / case_id / "with_skills" / "plot.png"
        without_path = OUTPUT_DIR / case_id / "without_skills" / "plot.png"

        entry = {
            "id": case_id,
            "description": case["description"].split("\n")[0],  # First line only
            "with_skills_img": _img_to_base64(with_path) if with_path.exists() else "",
            "without_skills_img": _img_to_base64(without_path) if without_path.exists() else "",
            "with_skills_ok": with_path.exists(),
            "without_skills_ok": without_path.exists(),
        }
        cases_data.append(entry)

    template = VIEWER_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("/*__CASES_DATA__*/[]", json.dumps(cases_data, indent=2))
    VIEWER_OUTPUT.write_text(html, encoding="utf-8")
    return VIEWER_OUTPUT


def main():
    parser = argparse.ArgumentParser(description="Plot A/B Test Eval Suite")
    parser.add_argument("--data-only", action="store_true", help="Only generate synthetic data")
    parser.add_argument("--view-only", action="store_true", help="Only build/open the viewer")
    parser.add_argument("--max-parallel", type=int, default=4, help="Max concurrent agent pairs (default: 4)")
    args = parser.parse_args()

    if args.view_only:
        print("Building viewer from existing outputs...")
        viewer = build_viewer()
        print(f"Viewer: {viewer}")
        webbrowser.open(f"file://{viewer}")
        return

    print(f"Generating synthetic data for {len(ALL_CASES)} test cases...")
    data_paths = generate_data()
    print()

    if args.data_only:
        print("Data generation complete. Use --view-only after running agents manually.")
        return

    print(f"Spawning agents ({args.max_parallel} pairs in parallel)...")
    print(f"Budget ceiling: ${len(ALL_CASES) * 2 * 1.0:.0f} (${1.0}/agent × {len(ALL_CASES) * 2} agents)")
    print()

    results = run_all_agents(data_paths, max_parallel=args.max_parallel)

    # Save run metadata
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
    run_meta = RESULTS_DIR / f"run_{timestamp}.json"
    with open(run_meta, "w") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)
    print(f"\nRun metadata: {run_meta}")

    # Tally
    successes = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"Completed: {successes}/{total} agents produced plots")

    if successes > 0:
        print("\nBuilding voter...")
        viewer = build_viewer()
        print(f"Viewer: {viewer}")
        webbrowser.open(f"file://{viewer}")


if __name__ == "__main__":
    main()
