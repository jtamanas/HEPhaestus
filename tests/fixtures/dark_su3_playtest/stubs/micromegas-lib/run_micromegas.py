#!/usr/bin/env python3
"""Stub micrOMEGAs runner for WS-3 bell-ring tests.

Returns canned micrOMEGAs output for darksu3 Point A scenario.
Real micrOMEGAs is not available in the test environment.
"""
import json, sys

result = {
    "status": "ok",
    "relic_density": {"omega_h2": 0.118, "units": "dimensionless"},
    "sigma_v_zero": 1.85e-26,
    "sigma_SI": 1.1e-45,
    "sigma_SD": 3.0e-44,
}
print(json.dumps(result))
sys.exit(0)
