"""
cache_key.py — pure-function cache key computation for /formcalc.

Cache key = SHA256 of:
  1. SHA256(FeynAmpList.m bytes)
  2. Canonical JSON of ProcessSpec.json (sorted keys)
  3. --reg flag
  4. --gamma5 flag (or "none" if absent)
  5. formcalc_version
  6. form_version
  7. looptools_version

The key is deterministic and stable across re-runs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional


def compute(
    feynamp_path: Path,
    processspec_path: Path,
    reg: str,
    gamma5: str,          # pass "none" when absent
    formcalc_version: str,
    form_version: str,
    looptools_version: str,
) -> str:
    """Return a hex SHA256 cache key."""
    h = hashlib.sha256()

    # 1. SHA256(FeynAmpList.m bytes)
    fa_bytes = Path(feynamp_path).read_bytes()
    fa_sha = hashlib.sha256(fa_bytes).hexdigest()
    h.update(fa_sha.encode())
    h.update(b"\x00")

    # 2. Canonical JSON of ProcessSpec.json
    with open(processspec_path) as f:
        spec = json.load(f)
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    h.update(canonical.encode())
    h.update(b"\x00")

    # 3. --reg flag
    h.update(reg.encode())
    h.update(b"\x00")

    # 4. --gamma5 flag
    h.update((gamma5 or "none").encode())
    h.update(b"\x00")

    # 5. formcalc_version
    h.update(formcalc_version.encode())
    h.update(b"\x00")

    # 6. form_version
    h.update(form_version.encode())
    h.update(b"\x00")

    # 7. looptools_version
    h.update(looptools_version.encode())
    h.update(b"\x00")

    return h.hexdigest()


def compute_from_bytes(
    feynamp_bytes: bytes,
    processspec_canonical: str,
    reg: str,
    gamma5: str,
    formcalc_version: str,
    form_version: str,
    looptools_version: str,
) -> str:
    """Variant for testing: accepts raw bytes + pre-canonicalised processspec."""
    h = hashlib.sha256()
    fa_sha = hashlib.sha256(feynamp_bytes).hexdigest()
    h.update(fa_sha.encode())
    h.update(b"\x00")
    h.update(processspec_canonical.encode())
    h.update(b"\x00")
    h.update(reg.encode())
    h.update(b"\x00")
    h.update((gamma5 or "none").encode())
    h.update(b"\x00")
    h.update(formcalc_version.encode())
    h.update(b"\x00")
    h.update(form_version.encode())
    h.update(b"\x00")
    h.update(looptools_version.encode())
    h.update(b"\x00")
    return h.hexdigest()
