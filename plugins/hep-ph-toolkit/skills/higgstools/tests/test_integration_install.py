"""
test_integration_install.py — network-gated integration test for full install.

Run only with HEPPH_RUN_NETWORK_TESTS=1.
"""
import os
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.environ.get("HEPPH_RUN_NETWORK_TESTS") != "1",
    reason="Set HEPPH_RUN_NETWORK_TESTS=1 to run network integration tests",
)
def test_full_legacy_install_and_smoke_test(tmp_path):
    """
    Full legacy install: clone HB-5.10.2 + HS-2.6.2, build, run smoke test,
    verify SM chi2 reference cache is populated.
    """
    import subprocess
    from pathlib import Path

    install_script = (
        Path(__file__).parent.parent / "scripts" / "install_higgstools.sh"
    )
    result = subprocess.run(
        ["bash", str(install_script), "install", "--backend=legacy"],
        capture_output=True,
        text=True,
        timeout=600,
        env={
            **os.environ,
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
            "HEPPH_INSTALL_ROOT": str(tmp_path / "install"),
        },
    )
    assert result.returncode == 0, f"Install failed: {result.stderr[-2000:]}"

    # Verify SM ref cache was written
    cache_file = tmp_path / "state" / "cache" / "hs2_chi2_sm_ref.json"
    assert cache_file.exists(), "SM reference chi2 cache not written"

    import json
    cache = json.loads(cache_file.read_text())
    assert "chi2_sm_ref" in cache
    assert 0 < cache["chi2_sm_ref"] < 200, f"SM chi2 out of range: {cache['chi2_sm_ref']}"
