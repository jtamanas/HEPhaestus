#!/usr/bin/env python3
"""
cache_sm_reference.py — parse HiggsSignals SM run output and write chi2_SM_ref cache.

Usage:
    cache_sm_reference.py --hs-output <text> --cache-file <path> \
        --hb-version <ver> --hs-version <ver>

The cache file is written atomically (tmp + rename + fsync).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile


assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


def parse_hs_output(text: str) -> tuple[float, int]:
    """
    Parse chi2_total and ndf from HiggsSignals output text.

    Looks for lines like:
      chi2 (total) = 89.357
      ndf (rates) = 80

    Returns (chi2_total, ndf). ndf defaults to 0 if not found.
    Raises ValueError if chi2_total not found.
    """
    chi2_match = re.search(r"chi2\s*\(\s*total\s*\)\s*=\s*([0-9.eE+\-]+)", text)
    if not chi2_match:
        raise ValueError(
            "Could not find 'chi2 (total) = ...' in HiggsSignals output.\n"
            f"Output snippet: {text[:500]!r}"
        )
    chi2_total = float(chi2_match.group(1))

    ndf_match = re.search(r"ndf\s*\(\s*rates\s*\)\s*=\s*([0-9]+)", text)
    ndf = int(ndf_match.group(1)) if ndf_match else 0

    return chi2_total, ndf


def write_cache_atomic(cache_file: str, data: dict) -> None:
    """Write data as JSON to cache_file atomically (tmp + rename + fsync)."""
    dest = os.path.abspath(cache_file)
    parent_dir = os.path.dirname(dest)
    os.makedirs(parent_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=".hs2_chi2_sm_ref.tmp.", dir=parent_dir)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, dest)
        # fsync parent directory to persist directory entry
        dir_fd = os.open(parent_dir, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        # Clean up tmp on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse HiggsSignals SM output and cache chi2_SM_ref."
    )
    parser.add_argument("--hs-output", required=True, help="HiggsSignals output text")
    parser.add_argument("--cache-file", required=True, help="Path to write cache JSON")
    parser.add_argument("--hb-version", required=True, help="HiggsBounds version string")
    parser.add_argument("--hs-version", required=True, help="HiggsSignals version string")
    args = parser.parse_args(argv)

    try:
        chi2_sm_ref, ndf = parse_hs_output(args.hs_output)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    cache_data = {
        "chi2_sm_ref": chi2_sm_ref,
        "ndf": ndf,
        "hb_version": args.hb_version,
        "hs_version": args.hs_version,
    }

    write_cache_atomic(args.cache_file, cache_data)
    print(f"SM reference chi2 cached: chi2={chi2_sm_ref:.3f}, ndf={ndf}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
