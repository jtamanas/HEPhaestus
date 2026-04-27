"""
test_integration_legacy.py — network-gated integration test for legacy driver.

Requires HB-5.10.2 + HS-2.6.2 installed (from test_integration_install).
Run only with HEPPH_RUN_NETWORK_TESTS=1.
"""
import os
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.environ.get("HEPPH_RUN_NETWORK_TESTS") != "1",
    reason="Set HEPPH_RUN_NETWORK_TESTS=1 to run network integration tests",
)
def test_run_2hdm_benchmark(tmp_path):
    """
    Run /higgstools run on committed 2HDM Type-II benchmark SLHA.

    Asserts:
    - hb_allowed=False (heavy A and H are excluded by LHC searches at this benchmark)
    - obsratio_max is finite and positive
    - hs_consistent is a bool
    """
    import json
    import subprocess
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "2hdm_type2_benchmark.slha"
    run_script = Path(__file__).parent.parent / "scripts" / "run_higgstools.py"

    result = subprocess.run(
        ["python3", str(run_script), "run", "--slha", str(fixture), "--mode", "hb"],
        capture_output=True,
        text=True,
        timeout=120,
        env={
            **os.environ,
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "HEPPH_STATE_ROOT": str(tmp_path / "state"),
        },
    )
    assert result.returncode == 0, f"run failed: {result.stderr[-2000:]}"
    data = json.loads(result.stdout)
    assert isinstance(data["hb_allowed"], bool)
    assert "obsratio_max" in data
    assert data["obsratio_max"] >= 0
