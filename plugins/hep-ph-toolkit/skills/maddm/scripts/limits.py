"""Experimental limit comparison utilities.

Load digitized exclusion curves and compare against computed predictions.
Library functions Claude composes per-task — not CLI executables.

Requires numpy.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def load_limit(
    experiment: str,
    observable: str,
    data_dir: str | Path,
) -> np.ndarray:
    """Load a digitized exclusion curve from a CSV file.

    Expects CSV with columns: mass_GeV, limit_value.
    File naming: {experiment}_{observable}.csv
    Lines starting with '#' are treated as comments.

    See assets/limit_data/README.md for data sources.

    Args:
        experiment: Experiment name (e.g. 'LZ', 'XENONnT',
            'FermiLAT', 'MAGIC').
        observable: Observable type (e.g. 'SI', 'SD',
            'sigmav_bb', 'sigmav_WW').
        data_dir: Directory containing CSV limit files.

    Returns:
        Array of shape (N, 2): columns [mass_GeV, limit_value].

    Raises:
        FileNotFoundError: If the limit file doesn't exist.
    """
    data_dir = Path(data_dir)
    filename = f"{experiment}_{observable}.csv"
    filepath = data_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Limit file not found: {filepath}\n"
            f"See assets/limit_data/README.md for data sources."
        )

    data = np.loadtxt(filepath, delimiter=",", comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return data


def is_excluded(
    point: dict,
    limit: np.ndarray,
    mass_key: str = "mass",
    value_key: str = "value",
) -> bool:
    """Check whether a theory point is excluded by an experimental limit.

    Uses log-linear interpolation of the limit curve.

    Args:
        point: Dict with mass and observable value.
        limit: Array from load_limit, shape (N, 2).
        mass_key: Key for mass in point dict.
        value_key: Key for observable value in point dict.

    Returns:
        True if the point's value exceeds (is above) the limit.
        False if the mass is outside the limit curve's range.
    """
    mass = point[mass_key]
    value = point[value_key]

    limit_masses = limit[:, 0]
    limit_values = limit[:, 1]

    if mass < limit_masses.min() or mass > limit_masses.max():
        return False

    log_limit = np.interp(
        np.log10(mass),
        np.log10(limit_masses),
        np.log10(limit_values),
    )
    return float(value) > 10**log_limit


def overlay_on_limit(
    results: list[dict],
    limit: np.ndarray,
    mass_key: str = "mass",
    value_key: str = "value",
) -> dict:
    """Prepare data for an exclusion plot overlay.

    Separates theory points into allowed and excluded, alongside
    the limit curve.

    Args:
        results: List of dicts with mass and observable value.
        limit: Array from load_limit.
        mass_key: Key for mass in result dicts.
        value_key: Key for observable value in result dicts.

    Returns:
        Dict with keys: limit_mass, limit_value,
        allowed_mass, allowed_value, excluded_mass, excluded_value
        (all numpy arrays).
    """
    allowed_m, allowed_v = [], []
    excluded_m, excluded_v = [], []

    for r in results:
        if is_excluded(r, limit, mass_key, value_key):
            excluded_m.append(r[mass_key])
            excluded_v.append(r[value_key])
        else:
            allowed_m.append(r[mass_key])
            allowed_v.append(r[value_key])

    return {
        "limit_mass": limit[:, 0],
        "limit_value": limit[:, 1],
        "allowed_mass": np.array(allowed_m),
        "allowed_value": np.array(allowed_v),
        "excluded_mass": np.array(excluded_m),
        "excluded_value": np.array(excluded_v),
    }
