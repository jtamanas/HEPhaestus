"""runner_spec_loader.py — shared YAML loader for dark-matter-constraints runner specs.

Normalizes the legacy scalar ``cosmology: standard_thermal`` form into the
structured object form ``{"kind": "standard_thermal"}``.  Every consumer
(``/dark-matter-constraints``, ``/micromegas``, future skills) should use this
loader so the normalization happens exactly once.

Usage::

    from plugins.shared.runner_spec_loader import load_runner_spec
    spec = load_runner_spec("path/to/spec.yaml")

Does NOT validate the loaded dict against runner_spec.schema.json; call
``validate_runner_spec.py`` (or the schema directly) for validation.
"""
from __future__ import annotations

import pathlib
from typing import Union

import yaml


def load_runner_spec(path: Union[str, pathlib.Path]) -> dict:
    """Load a runner-spec YAML file and return a normalised dict.

    Normalisation rule (D4):
    - If ``cosmology`` is a bare string (legacy scalar form, e.g.
      ``cosmology: standard_thermal``), replace it with
      ``{"kind": <value>}`` before returning.
    - If ``cosmology`` is already a dict, pass it through unchanged.
    - If ``cosmology`` is absent, leave it absent.

    Parameters
    ----------
    path:
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed and normalised spec dict.
    """
    with open(path) as fh:
        spec = yaml.safe_load(fh)

    if spec is None:
        spec = {}

    cosmology = spec.get("cosmology")
    if isinstance(cosmology, str):
        spec["cosmology"] = {"kind": cosmology}

    return spec
