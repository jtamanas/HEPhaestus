"""
test_validation_report_smoke.py — S6 smoke test for validation_report.py.

Verifies that validation_report.py runs without error and emits one
markdown section (## <model_id>) per fixture-registry model.

Plan §S6.Do.6; no marker (utility/smoke per plan §Test inventory).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


_VALIDATION_REPORT = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "scripts"
    / "validation_report.py"
)

_EXPECTED_MODELS = [
    "singlet-doublet",
    "two-hdm-a",
    "dark-su3",
    "dark-su3-confining-synthetic",
]


def test_validation_report_emits_section_per_model() -> None:
    """Assert validation_report.py exits 0 and prints one ## <model_id> section per model.

    Per plan §S6.Do.6. Smoke test: utility marker (no load_bearing/diagnostic).
    """
    result = subprocess.run(
        [sys.executable, str(_VALIDATION_REPORT), "--no-color"],
        capture_output=True,
        text=True,
        check=True,
    )
    out = result.stdout
    for mid in _EXPECTED_MODELS:
        assert f"## {mid}" in out, (
            f"validation_report.py output missing section '## {mid}'. "
            f"Full output:\n{out[:500]}"
        )
