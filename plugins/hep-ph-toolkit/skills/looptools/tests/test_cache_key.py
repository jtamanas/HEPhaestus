"""Tier-1 — cache_key stability + sensitivity for /looptools eval."""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import cache_key as ck


def _key(**over):
    kw = dict(
        amp_reduced_bytes=b"amp content",
        point_canonical='{"m_dm_gev":100.0}',
        form_factor_preset="default_2018",
        looptools_version="2.16",
        wolfram_version="14.3",
        canonicalizer_version=1,
    )
    kw.update(over)
    return ck.compute_from_bytes(**kw)


def test_stable_across_recomputes():
    assert len({_key() for _ in range(10)}) == 1


def test_valid_sha256_hex():
    k = _key()
    assert len(k) == 64 and all(c in "0123456789abcdef" for c in k)


def test_changes_on_amp_bytes():
    assert _key(amp_reduced_bytes=b"v1") != _key(amp_reduced_bytes=b"v2")


def test_changes_on_point():
    assert _key(point_canonical='{"m_dm_gev":100.0}') != _key(point_canonical='{"m_dm_gev":200.0}')


def test_changes_on_form_factor_preset():
    assert _key(form_factor_preset="default_2018") != _key(form_factor_preset="A1")


def test_changes_on_looptools_version():
    assert _key(looptools_version="2.16") != _key(looptools_version="2.15")


def test_changes_on_wolfram_version():
    assert _key(wolfram_version="14.3") != _key(wolfram_version="14.2")


def test_changes_on_canonicalizer_version():
    assert _key(canonicalizer_version=1) != _key(canonicalizer_version=2)


def test_compute_from_files_matches(tmp_path):
    amp = tmp_path / "amp_reduced.m"
    amp.write_bytes(b"amp content")
    point = {"m_dm_gev": 100.0}
    import json
    k_file = ck.compute(
        amp_reduced_path=amp,
        point=point,
        form_factor_preset="default_2018",
        looptools_version="2.16",
        wolfram_version="14.3",
    )
    k_bytes = _key(point_canonical=json.dumps(point, sort_keys=True, separators=(",", ":")))
    assert k_file == k_bytes
