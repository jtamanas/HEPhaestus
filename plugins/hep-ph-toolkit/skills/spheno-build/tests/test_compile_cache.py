"""
test_compile_cache.py — Unit tests for the W4 cache key computation.

Asserts:
    - Same (spec_bytes, sarah_version, spheno_version) → same cache key.
    - One-byte whitespace change in spec → different cache key.
    - Version bump → different cache key.
    - Key format: sha256hex=<sarah_version>+<spheno_version>

Test isolation: uses HEPPH_STATE_ROOT and XDG_CONFIG_HOME per global invariant §2.3.
"""

import hashlib
import importlib.util
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def compile_mod():
    return _load_module("compile_model", _SCRIPTS / "compile_model.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SPEC_CONTENT = b"""\
name: dark_su3
sarah_version_required: ">=4.15,<4.16"
parameters:
  - {name: MpsiD, default: 500.0}
  - {name: gD, default: 1.0}
"""

SPEC_CONTENT_WHITESPACE = SPEC_CONTENT + b" "  # One trailing space added

SARAH_VERSION = "4.15.3"
SPHENO_VERSION = "4.0.5"


def _compute_key(spec_bytes: bytes, sv: str, spv: str) -> str:
    """Compute key using the same formula as compile_model.compute_cache_key."""
    digest = hashlib.sha256(spec_bytes).hexdigest()
    return f"{digest}={sv}+{spv}"


# ---------------------------------------------------------------------------
# Tests using compile_mod.compute_cache_key directly
# ---------------------------------------------------------------------------
class TestCacheKeyStability:
    def test_same_inputs_same_key(self, compile_mod, tmp_path):
        """Same spec + same versions → same cache key (called twice)."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_bytes(SPEC_CONTENT)

        key1 = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, SPHENO_VERSION)
        key2 = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, SPHENO_VERSION)
        assert key1 == key2, f"Cache key not stable: {key1!r} vs {key2!r}"

    def test_different_spec_different_key(self, compile_mod, tmp_path):
        """Different spec content → different cache key."""
        spec_a = tmp_path / "spec_a.yaml"
        spec_a.write_bytes(SPEC_CONTENT)

        spec_b = tmp_path / "spec_b.yaml"
        spec_b.write_bytes(SPEC_CONTENT_WHITESPACE)

        key_a = compile_mod.compute_cache_key(spec_a, SARAH_VERSION, SPHENO_VERSION)
        key_b = compile_mod.compute_cache_key(spec_b, SARAH_VERSION, SPHENO_VERSION)
        assert key_a != key_b, "Expected different keys for different spec content"

    def test_sarah_version_bump_different_key(self, compile_mod, tmp_path):
        """SARAH version bump → different cache key (even with same spec)."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_bytes(SPEC_CONTENT)

        key_old = compile_mod.compute_cache_key(spec_file, "4.15.3", SPHENO_VERSION)
        key_new = compile_mod.compute_cache_key(spec_file, "4.15.4", SPHENO_VERSION)
        assert key_old != key_new, "Expected different keys for different SARAH version"

    def test_spheno_version_bump_different_key(self, compile_mod, tmp_path):
        """SPheno version bump → different cache key (even with same spec)."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_bytes(SPEC_CONTENT)

        key_old = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, "4.0.5")
        key_new = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, "4.0.6")
        assert key_old != key_new, "Expected different keys for different SPheno version"

    def test_key_format(self, compile_mod, tmp_path):
        """Cache key must be sha256hex=sarah_version+spheno_version format."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_bytes(SPEC_CONTENT)

        key = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, SPHENO_VERSION)
        assert "=" in key, f"Cache key missing '=': {key!r}"
        assert "+" in key, f"Cache key missing '+': {key!r}"

        digest_part, version_part = key.split("=", 1)
        # SHA-256 hex digest is 64 chars
        assert len(digest_part) == 64, (
            f"Expected 64-char sha256 digest, got {len(digest_part)}: {digest_part!r}"
        )
        # Version part: sarah_version+spheno_version
        assert version_part == f"{SARAH_VERSION}+{SPHENO_VERSION}", (
            f"Version part mismatch: {version_part!r}"
        )

    def test_key_matches_manual_computation(self, compile_mod, tmp_path):
        """Key matches manual sha256 computation."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_bytes(SPEC_CONTENT)

        expected_digest = hashlib.sha256(SPEC_CONTENT).hexdigest()
        expected_key = f"{expected_digest}={SARAH_VERSION}+{SPHENO_VERSION}"
        actual_key = compile_mod.compute_cache_key(spec_file, SARAH_VERSION, SPHENO_VERSION)

        assert actual_key == expected_key, (
            f"Cache key mismatch:\n  expected: {expected_key}\n  actual:   {actual_key}"
        )

    def test_whitespace_change_invalidates_cache(self, compile_mod, tmp_path):
        """Even a single whitespace byte change invalidates the cache."""
        spec_v1 = tmp_path / "spec_v1.yaml"
        spec_v1.write_bytes(SPEC_CONTENT)

        spec_v2 = tmp_path / "spec_v2.yaml"
        spec_v2.write_bytes(SPEC_CONTENT_WHITESPACE)

        key_v1 = compile_mod.compute_cache_key(spec_v1, SARAH_VERSION, SPHENO_VERSION)
        key_v2 = compile_mod.compute_cache_key(spec_v2, SARAH_VERSION, SPHENO_VERSION)
        assert key_v1 != key_v2, (
            "One-byte whitespace addition should change the cache key"
        )
