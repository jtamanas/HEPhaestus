"""
test_specs_pass_validator.py — CI invariant: every canonical ModelSpec v3 YAML
must pass validate_spec.py with exit code 0.

This prevents future unmigrated v3 specs from sneaking in undetected.
"""

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
_VALIDATE = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "sarah-build" / "scripts" / "validate_spec.py"
_V3_SPECS_DIR = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "modelspec_v3" / "specs"

# All canonical v3 specs that must pass the validator.
_SPECS = [
    _V3_SPECS_DIR / "singlet_doublet.yaml",
    _V3_SPECS_DIR / "dark_su3.yaml",
    _V3_SPECS_DIR / "2hdm_a.yaml",
    _V3_SPECS_DIR / "ssm.yaml",
]


@pytest.mark.parametrize("spec_path", _SPECS, ids=[p.name for p in _SPECS])
def test_spec_passes_validator(spec_path: Path) -> None:
    """Each canonical v3 spec must exit 0 from validate_spec.py."""
    assert spec_path.exists(), f"Spec not found: {spec_path}"
    cmd = [sys.executable, str(_VALIDATE), str(spec_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"validate_spec.py exited {result.returncode} for {spec_path.name}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
