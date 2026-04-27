"""Tests for cache_key.py."""
import hashlib
from pathlib import Path

import pytest

from cache_key import compute_cache_key


@pytest.fixture
def base_inputs(tmp_path):
    mod = tmp_path / "SM.mod"
    gen_f = tmp_path / "SM.gen"
    lorentz = tmp_path / "Lorentz.gen"
    mod.write_text("(* mod content v1 *)\n")
    gen_f.write_text("(* gen content v1 *)\n")
    lorentz.write_text("(* Lorentz.gen content *)\n")
    return {
        "mod_path": str(mod),
        "gen_path": str(gen_f),
        "feynarts_version": "3.11",
        "processspec": {
            "schema_version": "processspec/v1",
            "particles": {
                "in": [{"label": "e+", "pdg": -11, "mass_symbol": "ME"}],
                "out": [{"label": "mu+", "pdg": 13, "mass_symbol": "MMU"}],
            },
            "loop_order": 0,
            "kinematic_limit": "general",
            "excludes": [],
        },
        "lorentz_gen_path": str(lorentz),
    }


class TestDeterminism:
    def test_same_inputs_same_key(self, base_inputs):
        k1 = compute_cache_key(**base_inputs)
        k2 = compute_cache_key(**base_inputs)
        assert k1 == k2

    def test_key_is_hex_string(self, base_inputs):
        k = compute_cache_key(**base_inputs)
        assert isinstance(k, str)
        assert len(k) == 64  # SHA256 hex


class TestSensitivity:
    def test_mod_change(self, base_inputs, tmp_path):
        k1 = compute_cache_key(**base_inputs)
        mod2 = tmp_path / "SM_v2.mod"
        mod2.write_text("(* mod content v2 *)\n")
        inputs2 = {**base_inputs, "mod_path": str(mod2)}
        k2 = compute_cache_key(**inputs2)
        assert k1 != k2

    def test_gen_change(self, base_inputs, tmp_path):
        k1 = compute_cache_key(**base_inputs)
        gen2 = tmp_path / "SM_v2.gen"
        gen2.write_text("(* gen content v2 *)\n")
        inputs2 = {**base_inputs, "gen_path": str(gen2)}
        k2 = compute_cache_key(**inputs2)
        assert k1 != k2

    def test_feynarts_version_change(self, base_inputs):
        k1 = compute_cache_key(**base_inputs)
        inputs2 = {**base_inputs, "feynarts_version": "3.10"}
        k2 = compute_cache_key(**inputs2)
        assert k1 != k2

    def test_processspec_change(self, base_inputs):
        k1 = compute_cache_key(**base_inputs)
        spec2 = dict(base_inputs["processspec"])
        spec2 = {**spec2, "loop_order": 1}
        inputs2 = {**base_inputs, "processspec": spec2}
        k2 = compute_cache_key(**inputs2)
        assert k1 != k2

    def test_lorentz_gen_change(self, base_inputs, tmp_path):
        k1 = compute_cache_key(**base_inputs)
        lorentz2 = tmp_path / "Lorentz_v2.gen"
        lorentz2.write_text("(* different Lorentz.gen *)\n")
        inputs2 = {**base_inputs, "lorentz_gen_path": str(lorentz2)}
        k2 = compute_cache_key(**inputs2)
        assert k1 != k2


class TestCanonicalisation:
    def test_excludes_order_invariant(self, base_inputs):
        """sorted(excludes) ensures order doesn't matter for the key."""
        spec_a = {**base_inputs["processspec"], "excludes": ["Tadpoles", "SelfEnergies"]}
        spec_b = {**base_inputs["processspec"], "excludes": ["SelfEnergies", "Tadpoles"]}
        k1 = compute_cache_key(**{**base_inputs, "processspec": spec_a})
        k2 = compute_cache_key(**{**base_inputs, "processspec": spec_b})
        assert k1 == k2
