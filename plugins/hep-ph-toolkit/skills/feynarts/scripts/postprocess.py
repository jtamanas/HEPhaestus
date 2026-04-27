"""postprocess.py — post-process FeynArts wolframscript output.

Reads FeynAmpList.m from run_dir; checks size cap; writes:
  - FeynAmpList.meta.json  (sidecar)
  - summary.json
  - topologies.json

Raises PostprocessError on cap violations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


class PostprocessError(Exception):
    """Raised on cap violations or fatal post-processing errors."""

    def __init__(self, code: str, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


def postprocess_output(
    run_dir: str,
    n_diagrams: int,
    feynarts_version: str,
    model_hash: str,
    processspec: dict,
    loop_order: int,
    wall_clock_s: float,
    model_name: str,
    amp_size_cap_mb: int = 200,
    cached: bool = False,
) -> dict:
    """Post-process FeynArts output directory.

    Args:
        run_dir: Directory containing FeynAmpList.m.
        n_diagrams: Number of diagrams (from Mathematica stdout).
        feynarts_version: FeynArts version string.
        model_hash: SHA256 of model .mod file.
        processspec: Process specification dict.
        loop_order: Loop order used.
        wall_clock_s: Wall-clock time in seconds.
        model_name: Model name string.
        amp_size_cap_mb: Cap on FeynAmpList.m file size in MB.
        cached: Whether result was served from cache.

    Returns:
        dict with summary info.

    Raises:
        PostprocessError: On FEYNARTS_AMP_TOO_LARGE.
    """
    run_path = Path(run_dir)
    fa_list = run_path / "FeynAmpList.m"

    # Size cap check (Python layer, after Put[])
    if fa_list.exists():
        size_bytes = os.stat(str(fa_list)).st_size
        size_mb = size_bytes // (1024 * 1024)
        if size_mb > amp_size_cap_mb:
            # FeynAmpList.m stays on disk for inspection; no cache key written
            raise PostprocessError(
                "FEYNARTS_AMP_TOO_LARGE",
                f"FeynAmpList.m is {size_mb} MB, exceeds cap of {amp_size_cap_mb} MB.",
                {"amp_size_mb": size_mb, "cap": amp_size_cap_mb},
            )

    # Build meta.json sidecar — conforms to processspec/v1 schema.
    # The full processspec dict (built by resolve_process.py) is embedded
    # verbatim so downstream consumers (/formcalc, LoopTools) can validate
    # against plugins/shared/schemas/processspec.schema.json without
    # re-deriving the spec from the label-only summary.
    meta = {
        "schema_version": "processspec/v1",
        "feynarts_version": feynarts_version,
        "model_hash": model_hash,
        "n_diagrams": n_diagrams,
        "processspec": processspec,
    }
    _write_json(run_path / "FeynAmpList.meta.json", meta)

    # Build summary.json
    summary = {
        "n_diagrams": n_diagrams,
        "process": {
            "in": [p["label"] for p in processspec.get("particles", {}).get("in", [])],
            "out": [p["label"] for p in processspec.get("particles", {}).get("out", [])],
        },
        "loop_order": loop_order,
        "model": model_name,
        "cached": cached,
        "wall_clock_s": wall_clock_s,
    }
    _write_json(run_path / "summary.json", summary)

    # Build topologies.json (placeholder — actual topology extraction would
    # require a Wolfram round-trip; v1 writes a count-only summary)
    topologies = {
        "n_topologies": _estimate_n_topologies(n_diagrams, loop_order),
        "note": "v1: topology count estimated; full extraction in v1.1",
    }
    _write_json(run_path / "topologies.json", topologies)

    return summary


def _write_json(path: Path, data: dict) -> None:
    """Write JSON file with sorted keys and trailing newline."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def _estimate_n_topologies(n_diagrams: int, loop_order: int) -> int:
    """Heuristic topology count for v1 — NOT derived from Wolfram output.

    FeynArts topology extraction (``TopologyList``) requires a Wolfram
    round-trip that is not performed in v1.  This estimator is a coarse
    lower-bound placeholder:

    - Tree level  (loop_order == 0): floor(n_diagrams / 2), minimum 1.
    - Loop level  (loop_order  > 0): n_diagrams, minimum 1.
      (Loop diagrams often have more topologies than tree, but the ratio
      is highly process-dependent.)

    **Known limitation**: the heuristic will produce wrong values on real
    Wolfram runs — the gated integration test uses a tolerance range rather
    than an exact assertion.  Exact topology extraction via
    ``TopologyList[...]`` is planned for v1.1 once a Wolfram round-trip
    harness is in place.
    """
    if loop_order == 0:
        return max(1, n_diagrams // 2) if n_diagrams > 1 else n_diagrams
    # Loop topologies: typically more topologies than tree
    return max(1, n_diagrams)
