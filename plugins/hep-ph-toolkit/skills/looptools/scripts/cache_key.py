"""
cache_key.py — pure-function cache key computation for /looptools eval.

Mirrors the formcalc cache-key shape (sha256 over inputs + tool versions).

Cache key = SHA256 of:
  1. SHA256(amp_reduced.m bytes)
  2. Canonical JSON of the numeric model point (sorted keys)
  3. nucleon form-factor preset
  4. looptools_version
  5. wolfram_version_major_minor
  6. canonicalizer_version (bump when this hash function changes)

The key is deterministic and stable across re-runs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def compute(
    amp_reduced_path: Path,
    point: dict,
    form_factor_preset: str,
    looptools_version: str,
    wolfram_version: str,
    canonicalizer_version: int = 1,
) -> str:
    """Return a hex SHA256 cache key for an /looptools eval run."""
    amp_bytes = Path(amp_reduced_path).read_bytes()
    return compute_from_bytes(
        amp_reduced_bytes=amp_bytes,
        point_canonical=json.dumps(point, sort_keys=True, separators=(",", ":")),
        form_factor_preset=form_factor_preset,
        looptools_version=looptools_version,
        wolfram_version=wolfram_version,
        canonicalizer_version=canonicalizer_version,
    )


def compute_from_bytes(
    amp_reduced_bytes: bytes,
    point_canonical: str,
    form_factor_preset: str,
    looptools_version: str,
    wolfram_version: str,
    canonicalizer_version: int = 1,
) -> str:
    """Variant for testing: accepts raw bytes + pre-canonicalised point JSON."""
    h = hashlib.sha256()

    amp_sha = hashlib.sha256(amp_reduced_bytes).hexdigest()
    h.update(amp_sha.encode())
    h.update(b"\x00")

    h.update(point_canonical.encode())
    h.update(b"\x00")

    h.update((form_factor_preset or "default_2018").encode())
    h.update(b"\x00")

    h.update(looptools_version.encode())
    h.update(b"\x00")

    h.update(wolfram_version.encode())
    h.update(b"\x00")

    h.update(str(canonicalizer_version).encode())
    h.update(b"\x00")

    return h.hexdigest()
