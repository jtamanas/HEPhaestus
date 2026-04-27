"""
test_validate_interview.py — unit tests for scripts/validate_interview.py.

Tests:
- good_interview_dict → valid YAML written to stdout
- bad_interview_dict  → MODELSPEC_INVALID blocker on stderr + exit 1
- missing_required_key → error reported

Tests run with isolated XDG_CONFIG_HOME + HEPPH_STATE_ROOT.
Tests skip if validate_spec.py (W3) is not present on disk.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "validate_interview.py"
)
_VALIDATE_SPEC = (
    Path(__file__).resolve().parents[3] / "sarah-build" / "scripts" / "validate_spec.py"
)


def _run_validate_interview(
    answers: dict,
    tmp_path: Path,
) -> subprocess.CompletedProcess:
    answers_file = tmp_path / "answers.json"
    answers_file.write_text(json.dumps(answers))
    state_root = tmp_path / "state"
    state_root.mkdir(exist_ok=True)
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(cfg_dir)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    return subprocess.run(
        [sys.executable, str(_SCRIPT), str(answers_file)],
        capture_output=True,
        text=True,
        env=env,
    )


_GOOD_DARK_SU3 = {
    "name": "dark_su3",
    "claim_source": "test interview",
    "sarah_version_required": ">=4.15,<4.16",
    "gauge_groups": [
        {"symbol": "B",  "group": "U1",  "kind": "hypercharge", "coupling": "g1", "gauge_boson": "B0",  "gaugino": None},
        {"symbol": "WB", "group": "SU2", "kind": "left",        "coupling": "g2", "gauge_boson": "W",   "gaugino": None},
        {"symbol": "G",  "group": "SU3", "kind": "color",       "coupling": "g3", "gauge_boson": "g",   "gaugino": None},
        {"symbol": "GD", "group": "SU3", "kind": "dark",        "coupling": "gD", "gauge_boson": "gD0", "gaugino": None},
    ],
    "fermions": [
        {"name": "psiDL", "reps": {"WB": 1, "G": 1, "GD": 3}, "hypercharge": 0, "generations": 1, "chirality": "left"},
        {"name": "psiDR", "reps": {"WB": 1, "G": 1, "GD": 3}, "hypercharge": 0, "generations": 1, "chirality": "right"},
    ],
    "scalars": [],
    "mass_terms": [{"fields": ["psiDL", "psiDR"], "coefficient": "MpsiD", "hermitian_conjugate": True}],
    "yukawa_terms": [],
    "scalar_potential": [],
    "parameters": [
        {"name": "MpsiD", "latex": "M_{\\psi_D}", "real": True, "positive": True, "default": 500.0},
        {"name": "gD",    "latex": "g_D",          "real": True, "positive": True, "default": 1.0},
    ],
    "outputs": ["ufo", "spheno"],
}


def test_good_interview_outputs_yaml(tmp_path: Path) -> None:
    """A valid interview dict produces YAML on stdout and exits 0."""
    if not _VALIDATE_SPEC.exists():
        pytest.skip("validate_spec.py (W3) not present; skipping integration check")

    result = _run_validate_interview(_GOOD_DARK_SU3, tmp_path)
    assert result.returncode == 0, (
        f"Expected exit 0, got {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # Output must be parseable YAML
    try:
        import yaml  # type: ignore[import]
    except ModuleNotFoundError:
        pytest.skip("pyyaml not installed")
    spec = yaml.safe_load(result.stdout)
    assert spec["name"] == "dark_su3"
    assert spec["spec_version"] == 1


def test_bad_interview_dict_emits_blocker(tmp_path: Path) -> None:
    """An interview dict with invalid data produces MODELSPEC_INVALID on stderr."""
    if not _VALIDATE_SPEC.exists():
        pytest.skip("validate_spec.py (W3) not present")

    bad = dict(_GOOD_DARK_SU3)
    # Invalid: name starts with a digit
    bad["name"] = "2hdm_bad"
    result = _run_validate_interview(bad, tmp_path)
    assert result.returncode != 0
    # stderr should contain MODELSPEC_INVALID
    assert "MODELSPEC_INVALID" in result.stderr


def test_missing_required_key(tmp_path: Path) -> None:
    """Missing 'name' key causes a clear error."""
    incomplete = {k: v for k, v in _GOOD_DARK_SU3.items() if k != "name"}
    result = _run_validate_interview(incomplete, tmp_path)
    assert result.returncode != 0
    # Should mention the missing key on stderr
    assert result.stderr  # some error message


def test_invalid_json_file(tmp_path: Path) -> None:
    """A non-JSON answers file causes exit 1 with a clear error."""
    answers_file = tmp_path / "answers.json"
    answers_file.write_text("{ invalid json }")
    state_root = tmp_path / "state"
    state_root.mkdir()
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    env = dict(os.environ)
    env["XDG_CONFIG_HOME"] = str(cfg_dir)
    env["HEPPH_STATE_ROOT"] = str(state_root)
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), str(answers_file)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert result.stderr  # error message present
