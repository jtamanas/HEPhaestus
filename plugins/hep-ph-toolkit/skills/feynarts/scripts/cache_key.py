"""cache_key.py — compute deterministic cache key for /feynarts generate results.

Cache key is sha256 of the concatenation of:
  1. sha256(mod_path)        — .mod file content
  2. sha256(gen_path)        — .gen file content
  3. feynarts_version        — version string
  4. sha256(canonical processspec JSON)  — sorted keys, sorted excludes
  5. sha256(lorentz_gen_path) — Lorentz.gen content (generic model hash)

Each component is represented as its sha256 hex string, joined by '|'.
The overall key is sha256 of that joined string.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional


def _sha256_file(path: str) -> str:
    """Compute sha256 of a file, or sha256 of empty string if file not found."""
    p = Path(path)
    h = hashlib.sha256()
    if p.exists():
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    return h.hexdigest()


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _canonical_processspec(processspec: dict) -> str:
    """Canonical JSON representation of a processspec for hashing.

    Ensures:
      - keys are sorted
      - excludes list is sorted
    """
    spec = dict(processspec)
    if "excludes" in spec:
        spec = {**spec, "excludes": sorted(spec["excludes"])}
    return json.dumps(spec, sort_keys=True, separators=(",", ":"))


def compute_cache_key(
    mod_path: str,
    gen_path: str,
    feynarts_version: str,
    processspec: dict,
    lorentz_gen_path: str,
) -> str:
    """Compute a deterministic cache key for a FeynArts run.

    Args:
        mod_path: Path to .mod file.
        gen_path: Path to .gen file.
        feynarts_version: FeynArts version string (e.g. "3.11").
        processspec: Process specification dict (processspec/v1).
        lorentz_gen_path: Path to Models/Lorentz.gen in FeynArts install.

    Returns:
        64-character hex string (sha256).
    """
    component_1 = _sha256_file(mod_path)
    component_2 = _sha256_file(gen_path)
    component_3 = _sha256_str(feynarts_version)
    component_4 = _sha256_str(_canonical_processspec(processspec))
    component_5 = _sha256_file(lorentz_gen_path)

    combined = "|".join([
        component_1,
        component_2,
        component_3,
        component_4,
        component_5,
    ])
    return hashlib.sha256(combined.encode()).hexdigest()
