"""
Unit test: halo.py SHM defaults and halo-override echoing.
Verifies byte-identical field names (v0_km_per_s, vesc_km_per_s, rho0_gev_per_cm3).
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from halo import default_shm, resolve_halo, HaloParams  # noqa: E402


class TestHaloEcho:
    def test_default_shm_values(self):
        h = default_shm()
        assert h.model == "shm"
        assert h.v0_km_per_s == pytest.approx(238.0)
        assert h.vesc_km_per_s == pytest.approx(544.0)
        assert h.rho0_gev_per_cm3 == pytest.approx(0.3)

    def test_default_shm_field_names(self):
        """Field names must use _km_per_s and _gev_per_cm3 (not _kms, _gev_cm3)."""
        h = default_shm()
        d = h.to_dict()
        assert "v0_km_per_s" in d
        assert "vesc_km_per_s" in d
        assert "rho0_gev_per_cm3" in d
        assert "v0_kms" not in d
        assert "vesc_kms" not in d
        assert "rho0_gev_cm3" not in d

    def test_halo_null_returns_default(self):
        """halo: None in sigma doc → SHM defaults."""
        doc = {"halo": None}
        h = resolve_halo(doc)
        assert h.v0_km_per_s == pytest.approx(238.0)
        assert h.vesc_km_per_s == pytest.approx(544.0)

    def test_halo_missing_returns_default(self):
        """halo key absent from sigma doc → SHM defaults."""
        doc = {}
        h = resolve_halo(doc)
        assert h.v0_km_per_s == pytest.approx(238.0)

    def test_custom_halo_round_trips(self):
        """Custom SHM values are echoed byte-identical in to_dict()."""
        doc = {
            "halo": {
                "model": "shm",
                "v0_km_per_s": 220.0,
                "vesc_km_per_s": 533.0,
                "rho0_gev_per_cm3": 0.4,
            }
        }
        h = resolve_halo(doc)
        d = h.to_dict()
        assert d["v0_km_per_s"] == pytest.approx(220.0)
        assert d["vesc_km_per_s"] == pytest.approx(533.0)
        assert d["rho0_gev_per_cm3"] == pytest.approx(0.4)

    def test_non_shm_model_raises(self):
        """Non-SHM halo model raises NotImplementedError (v1.1)."""
        doc = {
            "halo": {
                "model": "shm_pp",
                "v0_km_per_s": 238.0,
                "vesc_km_per_s": 544.0,
                "rho0_gev_per_cm3": 0.3,
            }
        }
        with pytest.raises(NotImplementedError, match="shm_pp"):
            resolve_halo(doc)

    def test_halo_params_from_dict(self):
        """HaloParams.from_dict reconstructs correctly."""
        d = {"model": "shm", "v0_km_per_s": 235.0, "vesc_km_per_s": 550.0, "rho0_gev_per_cm3": 0.3}
        h = HaloParams.from_dict(d)
        assert h.v0_km_per_s == pytest.approx(235.0)
