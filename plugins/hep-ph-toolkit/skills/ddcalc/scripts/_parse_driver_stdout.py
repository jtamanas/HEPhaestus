"""
Parse the structured stdout emitted by ddcalc_driver.

Output format from driver:
    EXPERIMENT: <name>
    LOGL: <value>
    PVALUE: <value>
    EXCLUDED90: <0|1>
    ---
    (repeated per experiment)
    STATUS: ok
    VERSION: 2.2.0

Returns a dict:
    {
        "status": "ok",
        "ddcalc_version": "2.2.0",
        "experiments": {
            "XENON1T_2018": {"logL": ..., "p_value": ..., "excluded_90cl": True/False},
            ...
        }
    }
Raises ValueError on malformed input.
"""
from __future__ import annotations


def parse_driver_stdout(text: str) -> dict:
    """Parse ddcalc_driver stdout text into a structured dict."""
    lines = text.strip().splitlines()
    result: dict = {
        "status": "unknown",
        "ddcalc_version": "unknown",
        "experiments": {},
    }

    current_exp: dict | None = None
    current_name: str | None = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("EXPERIMENT:"):
            # Save previous experiment if any
            if current_name and current_exp:
                result["experiments"][current_name] = current_exp
            current_name = line.split(":", 1)[1].strip()
            current_exp = {}

        elif line.startswith("LOGL:"):
            if current_exp is not None:
                current_exp["logL"] = float(line.split(":", 1)[1].strip())

        elif line.startswith("PVALUE:"):
            if current_exp is not None:
                current_exp["p_value"] = float(line.split(":", 1)[1].strip())

        elif line.startswith("EXCLUDED90:"):
            if current_exp is not None:
                current_exp["excluded_90cl"] = bool(int(line.split(":", 1)[1].strip()))

        elif line == "---":
            # End of experiment block — save and reset
            if current_name and current_exp:
                result["experiments"][current_name] = current_exp
            current_name = None
            current_exp = None

        elif line.startswith("STATUS:"):
            result["status"] = line.split(":", 1)[1].strip()

        elif line.startswith("VERSION:"):
            result["ddcalc_version"] = line.split(":", 1)[1].strip()

    # Handle final experiment block without trailing ---
    if current_name and current_exp:
        result["experiments"][current_name] = current_exp

    if result["status"] == "unknown":
        raise ValueError(
            f"Driver stdout missing STATUS line. Got: {text[:200]!r}"
        )

    return result
