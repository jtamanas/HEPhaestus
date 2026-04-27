#!/usr/bin/env python3
"""Run a (model, figure) scan and write demo_output/<model>/<figure>/scan_results.json.

Driven by the /demo orchestrator. Dispatches to one of nine handlers under
_figures/ based on --model and --figure. Every physics number comes from
MadGraph (/madgraph) or MadDM (/maddm) via subprocess; the only Python
physics here is (a) loading the paper's analytical overlay from
eval/2506.19062_wimps_blind_spots/{models,cross_sections}/*.py and
(b) cache-key hashing.

Usage:
  run_scan.py --model A --figure 1 --model-hash <sha256> --param-preset default
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `import _cache`, `import _figures` when the script is executed by path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _cache import output_dir  # noqa: E402
from _figures import get_handler  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run a /demo scan (3 models x 3 figures).",
    )
    p.add_argument("--model", required=True, choices=["A", "B", "C"],
                   help="A=Singlet-Doublet, B=SD+2HDM, C=Dark SU(3)")
    p.add_argument("--figure", required=True, type=int, choices=[1, 2, 3])
    p.add_argument("--model-hash", required=True,
                   help="SHA256 of the Lagrangian .m file; locates SARAH cache.")
    p.add_argument("--param-preset", default="default",
                   help="Parameter-card preset; 'default' reads "
                        "eval/2506.19062_wimps_blind_spots/benchmarks/benchmark_points.py.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.param_preset != "default":
        # Custom presets are a stretch goal; the /demo orchestrator always
        # passes 'default' today.
        raise SystemExit(
            f"--param-preset={args.param_preset!r} not yet supported. "
            "Only 'default' (read from benchmarks/benchmark_points.py) works."
        )

    handler = get_handler(args.model, args.figure)
    result = handler(args)

    out = output_dir(args.model, args.figure) / "scan_results.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
