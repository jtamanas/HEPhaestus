"""
test_sm_ref_cache.py — unit tests for SM reference chi2 cache shape
and downstream absence-check behavior.

No network access required. Uses temp directories and fixture SLHA files.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
CACHE_SCRIPT = SCRIPTS_DIR / "cache_sm_reference.py"

# The usage skill's run_higgstools.py to test SM ref absent check
USAGE_SKILL_DIR = SKILL_DIR.parent / "higgstools"
RUN_SCRIPT = USAGE_SKILL_DIR / "scripts" / "run_higgstools.py"


class TestCacheSmReference:
    """Test cache_sm_reference.py shape and behavior."""

    def test_cache_file_written_with_correct_keys(self, tmp_path):
        """cache_sm_reference.py writes a valid JSON cache file with required keys."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "hs2_chi2_sm_ref.json"

        # Provide mock HS output (what a real HiggsSignals run on SM would produce)
        mock_hs_output = """
 HiggsSignals chi^2 summary
 chi2 (rates) = 85.234
 chi2 (masses) = 4.123
 chi2 (total) = 89.357
 ndf (rates) = 80
 ndf (masses) = 5
 p-value = 0.234
"""
        result = subprocess.run(
            ["python3", str(CACHE_SCRIPT),
             "--hs-output", mock_hs_output,
             "--cache-file", str(cache_file),
             "--hb-version", "5.10.2",
             "--hs-version", "2.6.2"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, f"cache_sm_reference.py failed: {result.stderr}"
        assert cache_file.exists(), "Cache file was not created"

        data = json.loads(cache_file.read_text())
        assert "chi2_sm_ref" in data, "Missing chi2_sm_ref key"
        assert "ndf" in data, "Missing ndf key"
        assert "hb_version" in data, "Missing hb_version key"
        assert "hs_version" in data, "Missing hs_version key"
        assert isinstance(data["chi2_sm_ref"], float), "chi2_sm_ref should be float"
        assert data["chi2_sm_ref"] > 0, "chi2_sm_ref should be positive"

    def test_cache_chi2_value_parsed_correctly(self, tmp_path):
        """cache_sm_reference.py correctly parses chi2_total from HS output."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "hs2_chi2_sm_ref.json"

        mock_hs_output = """
 chi2 (total) = 123.456
 ndf (rates) = 90
"""
        result = subprocess.run(
            ["python3", str(CACHE_SCRIPT),
             "--hs-output", mock_hs_output,
             "--cache-file", str(cache_file),
             "--hb-version", "5.10.2",
             "--hs-version", "2.6.2"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(cache_file.read_text())
        assert abs(data["chi2_sm_ref"] - 123.456) < 1e-9

    def test_cache_written_atomically(self, tmp_path):
        """cache_sm_reference.py uses atomic write (tmp + rename)."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "hs2_chi2_sm_ref.json"

        mock_hs_output = "chi2 (total) = 88.0\nndf (rates) = 80\n"
        result = subprocess.run(
            ["python3", str(CACHE_SCRIPT),
             "--hs-output", mock_hs_output,
             "--cache-file", str(cache_file),
             "--hb-version", "5.10.2",
             "--hs-version", "2.6.2"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        # No tmp files left behind
        tmp_files = list(cache_dir.glob("*.tmp.*"))
        assert len(tmp_files) == 0, f"Temporary files left behind: {tmp_files}"

    def test_cache_version_fields_written(self, tmp_path):
        """Cache file includes hb_version and hs_version for provenance."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "hs2_chi2_sm_ref.json"

        mock_hs_output = "chi2 (total) = 90.0\nndf (rates) = 81\n"
        result = subprocess.run(
            ["python3", str(CACHE_SCRIPT),
             "--hs-output", mock_hs_output,
             "--cache-file", str(cache_file),
             "--hb-version", "5.10.2",
             "--hs-version", "2.6.2"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(cache_file.read_text())
        assert data["hb_version"] == "5.10.2"
        assert data["hs_version"] == "2.6.2"


class TestSmRefCacheAbsence:
    """Test that run refuses to proceed when SM ref cache is absent."""

    def test_run_emits_sm_ref_missing_blocker_when_cache_absent(self, tmp_path):
        """run subcommand emits HIGGSTOOLS_SM_REF_MISSING when cache file is absent."""
        # Create a minimal config with HB/HS paths but no SM ref cache
        cfg_dir = tmp_path / "cfg" / "hephaestus"
        cfg_dir.mkdir(parents=True)
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Fake HB/HS binaries
        hb_bin = tmp_path / "hb" / "build" / "bin"
        hs_bin = tmp_path / "hs" / "build" / "bin"
        hb_bin.mkdir(parents=True)
        hs_bin.mkdir(parents=True)
        (hb_bin / "HiggsBounds").write_text("#!/bin/bash\n")
        (hb_bin / "HiggsBounds").chmod(0o755)
        (hs_bin / "HiggsSignals").write_text("#!/bin/bash\n")
        (hs_bin / "HiggsSignals").chmod(0o755)

        config = {
            "higgstools_backend": "legacy",
            "higgsbounds_path": str(tmp_path / "hb" / "build"),
            "higgssignals_path": str(tmp_path / "hs" / "build"),
        }
        (cfg_dir / "config.json").write_text(json.dumps(config))

        # Use a valid SLHA fixture with HB coupling blocks
        # (SLHA parsing happens before SM ref check, so we need valid blocks)
        sm_fixture = Path(__file__).parent.parent.parent / "higgstools" / "tests" / "fixtures" / "sm_benchmark.slha"
        if sm_fixture.exists():
            import shutil
            slha_file = tmp_path / "test.slha"
            shutil.copy(sm_fixture, slha_file)
        else:
            slha_file = tmp_path / "test.slha"
            slha_file.write_text("Block MASS\n  25  125.0  # Higgs\nBlock HiggsBoundsInputHiggsCouplingsBosons\n   1   1   0   1   1.0   1.0   1.0   1.0   1.0\nBlock HiggsBoundsInputHiggsCouplingsFermions\n   1   1   0   1   1.0   1.0   1.0\n")

        # SM ref cache is NOT present in state_dir
        # cache_file = state_dir / "cache" / "hs2_chi2_sm_ref.json"  # absent

        if not RUN_SCRIPT.exists():
            pytest.skip("run_higgstools.py not yet implemented")

        result = subprocess.run(
            ["python3", str(RUN_SCRIPT),
             "run",
             "--slha", str(slha_file),
             "--mode", "hs"],
            capture_output=True,
            text=True,
            timeout=15,
            env={
                **os.environ,
                "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
                "HEPPH_STATE_ROOT": str(state_dir),
            },
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "HIGGSTOOLS_SM_REF_MISSING" in combined, \
            f"Expected HIGGSTOOLS_SM_REF_MISSING in output, got: {combined}"
