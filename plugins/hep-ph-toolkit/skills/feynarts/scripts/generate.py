#!/usr/bin/env python3
"""generate.py — thin argparse CLI wrapper for /feynarts generate.

Usage:
  python3 generate.py generate \
    --process "e+ e- -> mu+ mu-" \
    --model SM \
    [--loop-order 0] \
    [--excludes "Tadpoles,SelfEnergies"] \
    [--output-dir /path/to/output] \
    [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_feynarts


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="feynarts",
        description="FeynArts diagram and amplitude generator.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    gen = sub.add_parser("generate", help="Generate Feynman diagrams and amplitudes.")
    gen.add_argument(
        "--process",
        required=True,
        help='Process specification, e.g. "e+ e- -> mu+ mu-" or raw tuple.',
    )

    # Model source — mutually exclusive group
    model_grp = gen.add_mutually_exclusive_group(required=True)
    model_grp.add_argument(
        "--model",
        help="Built-in FeynArts model (SM, SMQCD, THDM, MSSM).",
    )
    model_grp.add_argument(
        "--sarah-model",
        dest="sarah_model",
        help="SARAH model name (triggers post-hoc MakeFeynArts[]).",
    )
    model_grp.add_argument(
        "--model-file",
        dest="model_file",
        help="Path to directory containing .mod/.gen files.",
    )

    gen.add_argument(
        "--loop-order",
        dest="loop_order",
        type=int,
        default=0,
        help="Loop order (0=tree, 1=one-loop, ...). Default: 0.",
    )
    gen.add_argument(
        "--excludes",
        default="",
        help='Comma-separated topology classes to exclude, e.g. "Tadpoles,SelfEnergies".',
    )
    gen.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Output directory (default: ./feynarts_output/).",
    )
    gen.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force re-run even if cached.",
    )
    gen.add_argument(
        "--state-root",
        dest="state_root",
        default=None,
        help="Override HEPPH_FEYNARTS_STATE_ROOT.",
    )
    gen.add_argument(
        "--feynarts-path",
        dest="feynarts_path",
        default=None,
        help="Override FeynArts installation path.",
    )
    gen.add_argument(
        "--wolfram-path",
        dest="wolfram_path",
        default=None,
        help="Override wolframscript path.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    excludes = [e.strip() for e in args.excludes.split(",") if e.strip()] if args.excludes else []

    if args.subcommand == "generate":
        summary = run_feynarts.run(
            process=args.process,
            model=args.model,
            sarah_model=args.sarah_model,
            model_file=args.model_file,
            loop_order=args.loop_order,
            excludes=excludes,
            output_dir=args.output_dir,
            force=args.force,
            state_root=args.state_root,
            feynarts_path=args.feynarts_path,
            wolfram_path=args.wolfram_path,
        )
        print(json.dumps(summary, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
