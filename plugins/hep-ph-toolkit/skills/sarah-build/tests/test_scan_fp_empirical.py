"""
test_scan_fp_empirical.py — False-positive empirical gate (plan §7.4).

Runs scan() against real SARAH output trees under $HEPPH_STATE_ROOT (or the
default state root) when they exist. Skips gracefully when they don't.

These are pre-landing gates — if a known-clean baseline trips the scanner,
the pattern list is over-broad and must be retuned before merge.

History: dark_su3 and 2hdm_a were previously corrupt (missing LesHouches
metadata on BSM parameters / particles); both became clean baselines after
the v3 spec fixes. singlet_doublet was previously corrupt (SAxDynkin
leakage, SA-workarounds §15) but became a clean baseline after the
`l → LL` rename landed.
"""

import os
from pathlib import Path

import pytest

from scan_outputs import scan  # noqa: E402


def _state_root() -> Path:
    env = os.environ.get("HEPPH_STATE_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".local" / "share" / "hephaestus"


@pytest.mark.parametrize("model,sarah_name", [
    ("2hdm_a", "THDMa"),
    ("dark_su3", "DarkSU3"),
    ("singlet_doublet", "SingletDoublet"),
])
def test_known_clean_baselines_do_not_fp(model, sarah_name):
    """If a known-clean tree is on disk, scan() must return clean."""
    base = _state_root() / "models" / model
    if not (base / "sarah_output").is_dir():
        pytest.skip(f"no baseline at {base}")
    result = scan(base, sarah_name)
    assert result["status"] == "clean", (
        f"FP detected on known-clean {model} baseline: "
        f"{result['blocker']['context']['hits'][:3]}"
    )
