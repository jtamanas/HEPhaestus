"""
test_relic_json_byte_stability.py — T18b byte-stability check vs pre-migration baselines.

Per-model: parse the real MadDM fixture, apply consumer-side migration code,
compare to manager-pre-staged relic_<model>_pre_migration.json baseline.
Per O1 (folds in T30). Per U3: numeric tolerance 1e-12 relative.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"

# Manager-pre-staged baselines
_BASELINES_DIR = Path(
    "/Users/yianni/Projects/hep-ph-agents/"
    ".shift-manager/run-20260426-punchlist-tier2/fixtures"
)

_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def _apply_consumer_migration(gamlike: dict) -> dict:
    """
    Apply consumer-side post-processing (per plan §7.1).
    Mirrors the 2hdm-a migration block: flatten channels, compute fractions.
    Returns a relic.json-equivalent dict.
    """
    relic = gamlike["relic"]
    flat_channels = {}
    for finals in relic["channels"].values():
        for k, v in finals.items():
            if v is not None:
                flat_channels[k] = v

    total = sum(flat_channels.values()) or 1.0
    fractions = {k: v / total for k, v in flat_channels.items()}
    gate_check = {
        "channels_sum_in_unity_range": 0.99 <= sum(fractions.values()) <= 1.01
        if fractions else True,
    }

    return {
        "Omegah2": relic["Omegah2"],
        "xsi": relic["xsi"],
        "x_f": relic["x_f"],
        "sigmav_xf": relic["sigmav_xf"],
        "channel_percentages": flat_channels,
        "channel_fractions": fractions,
        "gate_check": gate_check,
        "sigmav_channels": flat_channels,
    }


def _numeric_close(a, b, rel=1e-12) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if abs(b) < 1e-300:
        return abs(a - b) < 1e-300
    return abs(a - b) <= rel * abs(b)


@pytest.mark.parametrize("model", ["2hdma", "sd"])
def test_relic_json_byte_stability(model):
    """Parse real fixture, apply consumer migration, compare to pre-migration baseline."""
    fixture_map = {
        "2hdma": "relic_only_xsi_eq_1_2hdma.txt",
        "sd": "relic_only_xsi_eq_1_sd.txt",
    }
    baseline_path = _BASELINES_DIR / f"relic_{model}_pre_migration.json"
    fixture_path = _FIXTURES / fixture_map[model]

    if not baseline_path.exists():
        pytest.skip(f"No pre-migration baseline for {model}; manager did not stage it.")

    baseline = json.loads(baseline_path.read_text())

    gamlike = _mod.parse_file(fixture_path)
    migrated = _apply_consumer_migration(gamlike)

    # Check numeric fields
    for key in ["Omegah2", "xsi", "x_f", "sigmav_xf"]:
        if key in baseline:
            b_val = baseline[key]
            m_val = migrated.get(key)
            assert _numeric_close(m_val, b_val), (
                f"Field {key} mismatch: migrated={m_val}, baseline={b_val}"
            )

    # Channel percentages: each channel value within 1e-12
    if "channel_percentages" in baseline and isinstance(baseline["channel_percentages"], dict):
        for chan, b_val in baseline["channel_percentages"].items():
            m_val = migrated["channel_percentages"].get(chan)
            if b_val is None:
                continue
            assert _numeric_close(m_val, b_val), (
                f"Channel {chan} pct mismatch: migrated={m_val}, baseline={b_val}"
            )
