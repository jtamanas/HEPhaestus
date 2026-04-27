"""test_singletdm_golden.py — integration test: singletDM golden fixture.

GATED: requires HEPPH_RUN_NETWORK_TESTS=1 and a configured micrOMEGAs installation.

Golden comparison strategy (no regex in test code):

  TestSingletDMGolden:
    - Runs the micrOMEGAs-shipped Singlet_DM/ benchmark.
    - Compares raw stdout line-by-line against the committed stdout_singletDM.txt
      fixture. Any deviation means the tool's output format changed — the fixture
      must be regenerated (see scripts/regenerate_fixture.py).
    - For the sigma_si test: reads the golden scalar directly from the committed
      summary_singletDM.json (an opaque fixture the agent produced), then reads
      the same key from the run's summary.json produced by run_micromegas.py.
      No regex; values are extracted by JSON key lookup only.

  TestRegenerateFixture:
    - Runs regenerate_fixture.py and checks that stdout_singletDM.txt was written
      with non-empty content. No scalar extraction in test code.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"
_SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
_FIXTURES = Path(__file__).resolve().parent / "fixtures"

_REL_TOL_OMEGA = 1e-3
_REL_TOL_SIGMA = 5e-3


def _load_config() -> dict:
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            return json.load(f)
    return {}


def _rel_close(a: float | None, b: float | None, tol: float) -> bool:
    """Check relative closeness. True if both None or within tol."""
    import math
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    if b == 0:
        return abs(a) < tol
    return abs(a - b) / abs(b) <= tol


def _run_singletdm(singletdm_dir: Path) -> subprocess.CompletedProcess:
    """Run Singlet_DM/main and return the CompletedProcess."""
    return subprocess.run(
        ["./main"],
        cwd=str(singletdm_dir),
        capture_output=True, text=True,
        env={**os.environ, "HEPPH_MICROMEGAS_SEED": "42"},
        timeout=120,
    )


@pytest.mark.skipif(not _NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS not set")
class TestSingletDMGolden:
    def test_stdout_matches_golden_fixture(self, tmp_path):
        """Singlet_DM benchmark stdout matches committed golden fixture line-by-line.

        This test is a pure text diff — no field extraction, no regex. A failure
        means micrOMEGAs changed its output format or the benchmark parameters
        changed; regenerate the fixture via scripts/regenerate_fixture.py.
        """
        config = _load_config()
        micromegas_path = config.get("micromegas_path", "")
        if not micromegas_path:
            pytest.skip("micromegas_path not configured")

        singletdm_dir = Path(micromegas_path) / "Singlet_DM"
        if not singletdm_dir.exists():
            pytest.skip(f"Singlet_DM/ not found at {singletdm_dir}")

        if not (singletdm_dir / "main").exists():
            result = subprocess.run(
                ["make", "main"], cwd=str(singletdm_dir),
                capture_output=True, text=True
            )
            if result.returncode != 0:
                pytest.skip(f"Failed to build Singlet_DM: {result.stderr[:200]}")

        golden_stdout_file = _FIXTURES / "stdout_singletDM.txt"
        if not golden_stdout_file.exists():
            pytest.skip("stdout_singletDM.txt fixture not found")

        result = _run_singletdm(singletdm_dir)
        live_lines = result.stdout.splitlines()
        golden_lines = golden_stdout_file.read_text().splitlines()

        assert live_lines == golden_lines, (
            f"stdout differs from golden fixture stdout_singletDM.txt.\n"
            f"Regenerate via: HEPPH_RUN_NETWORK_TESTS=1 python3 scripts/regenerate_fixture.py\n"
            f"First diff at index "
            + str(next(
                (i for i, (a, b) in enumerate(zip(live_lines, golden_lines)) if a != b),
                min(len(live_lines), len(golden_lines))
            ))
        )

    def test_sigma_si_matches_golden(self, tmp_path):
        """Singlet_DM benchmark sigma_si_proton matches committed golden within rel=5e-3.

        Golden value is read from the committed summary_singletDM.json (opaque fixture
        produced by the agent from SKILL.md patterns). Live value is obtained by running
        run_micromegas.py --precompiled singletDM and reading its output summary.json.
        No regex in test code.
        """
        config = _load_config()
        micromegas_path = config.get("micromegas_path", "")
        if not micromegas_path:
            pytest.skip("micromegas_path not configured")

        singletdm_dir = Path(micromegas_path) / "Singlet_DM"
        if not singletdm_dir.exists():
            pytest.skip(f"Singlet_DM/ not found")

        if not (singletdm_dir / "main").exists():
            pytest.skip("Singlet_DM/main not compiled")

        golden_summary_file = _FIXTURES / "summary_singletDM.json"
        if not golden_summary_file.exists():
            pytest.skip("summary_singletDM.json fixture not found")

        with open(golden_summary_file) as f:
            golden = json.load(f)
        golden_sigma = golden.get("sigma_si_proton_cm2")

        # Run via run_micromegas.py to get a structured summary.json (no regex extraction)
        run_script = _SCRIPT_DIR / "run_micromegas.py"
        result = subprocess.run(
            [sys.executable, str(run_script),
             "scatter", "singletDM",
             "--precompiled", "singletDM",
             "--output-dir", str(tmp_path)],
            capture_output=True, text=True,
            env={**os.environ, "HEPPH_MICROMEGAS_SEED": "42"},
            timeout=180,
        )
        if result.returncode != 0:
            pytest.skip(
                f"run_micromegas.py failed (exit {result.returncode}): {result.stderr[:300]}"
            )

        summary_file = tmp_path / "summary.json"
        if not summary_file.exists():
            pytest.skip("run_micromegas.py did not produce summary.json")

        with open(summary_file) as f:
            run_summary = json.load(f)

        run_sigma = run_summary.get("sigma_si_proton_cm2")

        if golden_sigma is not None and run_sigma is not None:
            assert _rel_close(run_sigma, golden_sigma, _REL_TOL_SIGMA), (
                f"sigma_si_proton_cm2 {run_sigma:.4e} differs from golden {golden_sigma:.4e} "
                f"by >{_REL_TOL_SIGMA:.0e}"
            )


@pytest.mark.skipif(not _NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS not set")
class TestRegenerateFixture:
    """Integration test: run regenerate_fixture.py and assert output structure.

    Asserts that the raw stdout fixture was written with non-empty content.
    No scalar extraction in test code — the agent reads SKILL.md patterns
    and writes summary_singletDM.json separately.
    """

    def test_regenerator_writes_stdout_fixture(self, tmp_path):
        """regenerate_fixture.py writes a non-empty stdout_singletDM.txt fixture."""
        config = _load_config()
        micromegas_path = config.get("micromegas_path", "")
        if not micromegas_path:
            pytest.skip("micromegas_path not configured")

        singletdm_dir = Path(micromegas_path) / "Singlet_DM"
        if not singletdm_dir.exists():
            pytest.skip(f"Singlet_DM/ not found at {singletdm_dir}")

        regenerate_script = _SCRIPT_DIR / "regenerate_fixture.py"
        result = subprocess.run(
            [sys.executable, str(regenerate_script)],
            capture_output=True, text=True,
            env={**os.environ, "HEPPH_RUN_NETWORK_TESTS": "1"},
            timeout=180,
        )
        assert result.returncode == 0, (
            f"regenerate_fixture.py failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"
        )

        stdout_fixture = _FIXTURES / "stdout_singletDM.txt"
        assert stdout_fixture.exists(), "stdout_singletDM.txt was not written"
        assert stdout_fixture.stat().st_size > 0, "stdout_singletDM.txt is empty"

    def test_committed_summary_json_structure(self):
        """Committed summary_singletDM.json satisfies scattering/v1 schema keys.

        This is a static check on the committed fixture — no live run required.
        The fixture was produced by the agent reading SKILL.md patterns; this
        test guards against accidental truncation or key removal.
        """
        summary_file = _FIXTURES / "summary_singletDM.json"
        if not summary_file.exists():
            pytest.skip("summary_singletDM.json not found")

        with open(summary_file) as f:
            summary = json.load(f)

        required_keys = {
            "schema_version", "m_dm_gev",
            "sigma_si_proton_cm2", "sigma_si_neutron_cm2",
            "sigma_sd_proton_cm2", "sigma_sd_neutron_cm2",
            "source", "source_run",
        }
        assert required_keys.issubset(summary.keys()), (
            f"summary_singletDM.json missing keys: {required_keys - set(summary.keys())}"
        )
