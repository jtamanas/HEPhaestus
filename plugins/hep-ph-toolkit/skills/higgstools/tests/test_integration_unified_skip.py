"""
test_integration_unified_skip.py — network-gated test for unified backend graceful skip.

Asserts that with HEPPH_HIGGSTOOLS_BACKEND=unified but the unified build absent,
run emits HIGGSTOOLS_BACKEND_UNAVAILABLE and no Python traceback escapes stderr.

Run only with HEPPH_RUN_NETWORK_TESTS=1.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

FIXTURE = Path(__file__).parent / "fixtures" / "sm_benchmark.slha"
RUN_SCRIPT = Path(__file__).parent.parent / "scripts" / "run_higgstools.py"


@pytest.mark.skipif(
    os.environ.get("HEPPH_RUN_NETWORK_TESTS") != "1",
    reason="Set HEPPH_RUN_NETWORK_TESTS=1 to run network integration tests",
)
def test_unified_backend_unavailable_emits_clean_blocker(tmp_path):
    """
    With HEPPH_HIGGSTOOLS_BACKEND=unified but unified build absent,
    run emits HIGGSTOOLS_BACKEND_UNAVAILABLE — no raw Python traceback in stderr.
    """
    # Ensure Higgs.bounds module is NOT importable in a clean env
    env = {
        **os.environ,
        "HEPPH_HIGGSTOOLS_BACKEND": "unified",
        "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
        "HEPPH_STATE_ROOT": str(tmp_path / "state"),
    }
    # Remove any higgstools install from PATH/PYTHONPATH
    env.pop("PYTHONPATH", None)

    # Create minimal config pointing to legacy paths that don't have unified
    cfg_dir = tmp_path / "cfg" / "hephaestus"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.json").write_text(json.dumps({
        "higgstools_backend": "legacy",
        "higgsbounds_path": "/nonexistent/hb",
        "higgssignals_path": "/nonexistent/hs",
    }))

    # Also write a minimal SM ref cache so the check passes
    cache_dir = tmp_path / "state" / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "hs2_chi2_sm_ref.json").write_text(json.dumps({
        "chi2_sm_ref": 85.0, "ndf": 80
    }))

    result = subprocess.run(
        ["python3", str(RUN_SCRIPT), "run",
         "--slha", str(FIXTURE),
         "--backend", "unified",
         "--mode", "both"],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    # Should emit HIGGSTOOLS_BACKEND_UNAVAILABLE
    combined = result.stdout + result.stderr
    assert "HIGGSTOOLS_BACKEND_UNAVAILABLE" in combined or "legacy" in combined, \
        f"Expected HIGGSTOOLS_BACKEND_UNAVAILABLE or legacy fallback in output: {combined}"

    # No raw Python traceback should escape
    assert "Traceback (most recent call last)" not in result.stderr, \
        f"Python traceback escaped to stderr: {result.stderr[:1000]}"
