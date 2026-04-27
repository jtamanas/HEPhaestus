"""
Test cache atomicity: .build_key is written last via the Phase-0 atomic_write.sh helper.
Also tests that deleting amp_reduced.m while .build_key exists forces a miss.

Iteration-2 note: _write_build_key_atomic now shells out to
plugins/shared/install-helpers/atomic_write.sh (atomic_write_stdin) rather
than reimplementing tmp+fsync+rename+dir-fsync in Python.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SHARED_HELPERS = SKILL_DIR.parent.parent.parent.parent / "plugins" / "shared" / "install-helpers"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import importlib.util

def _load_run_formcalc():
    spec = importlib.util.spec_from_file_location(
        "run_formcalc_atomic",
        str(SCRIPTS_DIR / "run_formcalc.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCacheAtomic:
    def test_write_build_key_atomic(self, tmp_path):
        """_write_build_key_atomic writes .build_key atomically."""
        mod = _load_run_formcalc()
        cache_key = "a" * 64
        mod._write_build_key_atomic(tmp_path, cache_key)
        bk = tmp_path / ".build_key"
        assert bk.exists()
        assert bk.read_text().strip() == cache_key

    def test_write_build_key_overwrites(self, tmp_path):
        """Second write overwrites the first."""
        mod = _load_run_formcalc()
        mod._write_build_key_atomic(tmp_path, "a" * 64)
        mod._write_build_key_atomic(tmp_path, "b" * 64)
        assert (tmp_path / ".build_key").read_text().strip() == "b" * 64

    def test_cache_hit_requires_all_three(self, tmp_path):
        """Cache hit requires amp_reduced.m + meta.json + .build_key."""
        mod = _load_run_formcalc()
        key = "c" * 64

        # No files → miss
        assert mod._cache_hit(tmp_path, key) is False

        # Add amp_reduced.m only → still miss
        (tmp_path / "amp_reduced.m").write_text("x")
        assert mod._cache_hit(tmp_path, key) is False

        # Add meta.json → still miss (no .build_key)
        (tmp_path / "amp_reduced.meta.json").write_text("{}")
        assert mod._cache_hit(tmp_path, key) is False

        # Add .build_key with correct key → hit
        mod._write_build_key_atomic(tmp_path, key)
        assert mod._cache_hit(tmp_path, key) is True

        # Delete amp_reduced.m → miss (even though .build_key matches)
        (tmp_path / "amp_reduced.m").unlink()
        assert mod._cache_hit(tmp_path, key) is False

    def test_build_key_written_last_semantics(self, tmp_path):
        """
        Simulate mid-run corruption: .build_key exists but amp_reduced.m absent.
        The cache_hit check guards against this.
        """
        mod = _load_run_formcalc()
        key = "d" * 64
        # Write .build_key but NOT amp_reduced.m
        mod._write_build_key_atomic(tmp_path, key)
        (tmp_path / "amp_reduced.meta.json").write_text("{}")
        # Should be a miss
        assert mod._cache_hit(tmp_path, key) is False

    def test_atomic_write_no_tmp_left_on_success(self, tmp_path):
        """No stale .tmp files remain in the output dir after successful atomic write."""
        mod = _load_run_formcalc()
        mod._write_build_key_atomic(tmp_path, "e" * 64)
        # Neither the old Python naming pattern nor the shell helper's pattern should remain.
        tmps = list(tmp_path.glob(".build_key_tmp_*")) + list(tmp_path.glob(".atomic_write_*"))
        assert len(tmps) == 0, f"Leftover tmp files: {tmps}"

    def test_write_build_key_uses_shell_helper(self, tmp_path):
        """_write_build_key_atomic delegates to atomic_write_via_shell (Phase-0 helper)."""
        mod = _load_run_formcalc()
        calls = []
        orig = mod._atomic_write_via_shell

        def spy(dest, content):
            calls.append((dest, content))
            return orig(dest, content)

        mod._atomic_write_via_shell = spy
        mod._write_build_key_atomic(tmp_path, "f" * 64)
        assert len(calls) == 1, "Expected exactly one call to _atomic_write_via_shell"
        dest, content = calls[0]
        assert dest == tmp_path / ".build_key"
        assert content == "f" * 64 + "\n"
