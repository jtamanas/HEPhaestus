"""
exclude.py — thin wrapper for verdict-only output.

Called by /ddcalc exclude. Loads a scattering JSON, runs the driver,
and emits only the exclusion verdict in a compact JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_scattering import validate_sigma_json  # noqa: E402


def get_verdict(result_json: dict) -> dict:
    """
    Extract exclusion verdict from a full ddcalc_result/v1 dict.
    Returns {verdict, m_dm_gev, experiments_excluded: {name: bool}, ...}.
    """
    experiments = result_json.get("experiments", {})
    excluded_flags = {
        name: exp_data.get("excluded_90cl", False)
        for name, exp_data in experiments.items()
    }
    any_excluded = any(excluded_flags.values())
    return {
        "verdict": result_json.get("verdict", "unknown"),
        "m_dm_gev": result_json.get("m_dm_gev"),
        "experiments_excluded": excluded_flags,
        "excluded_90cl_any": any_excluded,
    }
