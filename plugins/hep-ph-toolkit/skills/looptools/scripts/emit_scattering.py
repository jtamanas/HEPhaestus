"""
emit_scattering.py — assemble + validate a scattering/v1 JSON document.

The physics result of /looptools eval is the shared `scattering/v1` contract
(plugins/shared/schemas/scattering.schema.json), whose `source` enum already
lists `"looptools"`.  No schema change is required.  This is exactly what
`/ddcalc run --sigma-json` consumes.

`source` is stamped `"looptools"`; the document also carries the fixture/model
provenance stamps required by the fixture-bypass decision (build plan §8 dec. #1):
`model_source`, `model_fixture`.  These are allowed because the schema sets
`additionalProperties: true` (do NOT re-tighten — FU-wsk-01).
"""
from __future__ import annotations

import json
from pathlib import Path

_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "shared"
    / "schemas"
    / "scattering.schema.json"
)


def build(
    m_dm_gev: float,
    sigmas: dict,
    source_run: str,
    form_factor_preset: str = "default_2018",
    extra: dict | None = None,
) -> dict:
    """Assemble a scattering/v1 document.

    Parameters
    ----------
    m_dm_gev:           DM mass [GeV].
    sigmas:             dict with the four sigma_* keys (from match_nucleon.match).
    source_run:         non-empty run identifier (e.g. the run/<ts> dir).
    form_factor_preset: nucleon form-factor preset ("default_2018"|"A1").
    extra:              optional extra top-level keys (provenance stamps etc.).
    """
    doc = {
        "schema_version": "scattering/v1",
        "m_dm_gev": m_dm_gev,
        "sigma_si_proton_cm2": sigmas["sigma_si_proton_cm2"],
        "sigma_si_neutron_cm2": sigmas["sigma_si_neutron_cm2"],
        "sigma_sd_proton_cm2": sigmas.get("sigma_sd_proton_cm2"),
        "sigma_sd_neutron_cm2": sigmas.get("sigma_sd_neutron_cm2"),
        "source": "looptools",
        "source_run": source_run,
        "nucleon_form_factors": {"preset": form_factor_preset},
    }
    if extra:
        doc.update(extra)
    return doc


def validate(doc: dict) -> list:
    """Validate ``doc`` against scattering.schema.json.

    Returns a list of human-readable error strings (empty == valid).  If
    jsonschema is unavailable, returns [] (validation is best-effort, matching
    the sibling skills' optional-dependency posture).
    """
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
    except ImportError:
        return []
    if not _SCHEMA_PATH.exists():
        return [f"schema not found: {_SCHEMA_PATH}"]
    with open(_SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: str(e.path))
    return [
        f"{'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors
    ]


def write(dest: Path, doc: dict) -> None:
    """Write ``doc`` as pretty JSON to ``dest``."""
    Path(dest).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
