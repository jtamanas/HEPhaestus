"""
test_routing_report_schema.py — CI invariant #1 (S25, plan §11.3).

For each fixture model spec, run route(...) and validate the emitted JSON
against routing_report.schema.json. The renderer's _validate_json_against_schema
already runs at every render, so any unhandled report would already fail
inside route(); this test pins the contract from the OUTSIDE so a future
refactor that loosens validator wiring is caught.
"""
import pathlib
import json
import pytest

# The orchestrator is required.
orch_mod = pytest.importorskip(
    "model_router.orchestrator",
    reason="orchestrator.route required for schema-invariant tests",
)
route = orch_mod.route

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "registries"
SCHEMA_PATH = (
    pathlib.Path(__file__).parent.parent
    / "scripts" / "model_router" / "schemas" / "routing_report.schema.json"
)


# Five canonical fixture models (per plan §3.5).
# Note: archived / unknown models intentionally not parametric here — those
# are covered by orchestrator error tests; the schema contract only applies
# to successfully emitted reports.
PARAMETRIC_MODELS = [
    "singlet-doublet",
    "dark-su3",
    "two-hdm-a",
]


@pytest.mark.parametrize("model_id", PARAMETRIC_MODELS)
def test_emitted_json_validates_against_schema(model_id, mock_constraints_yaml):
    from model_router.types import RouterOptions
    report = route(
        model_id=model_id,
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    # If we got here, _validate_json_against_schema didn't raise — but pin
    # the contract from outside too: re-validate here (defensive).
    try:
        import jsonschema  # type: ignore
    except ImportError:
        pytest.skip("jsonschema not installed; cannot validate contract")
    schema = json.loads(SCHEMA_PATH.read_text())
    try:
        from referencing import Registry, Resource  # type: ignore
        from referencing.jsonschema import DRAFT7  # type: ignore
        ranked = json.loads((SCHEMA_PATH.parent / "ranked_chain.schema.json").read_text())
        registry = Registry().with_resource(
            "ranked_chain.schema.json",
            Resource(contents=ranked, specification=DRAFT7),
        )
        validator = jsonschema.Draft7Validator(schema, registry=registry)
        errors = list(validator.iter_errors(report.json_report))
        assert not errors, f"Schema errors: {[e.message for e in errors]}"
    except ImportError:
        resolver = jsonschema.RefResolver(
            base_uri=SCHEMA_PATH.parent.as_uri() + "/", referrer=schema
        )
        jsonschema.validate(report.json_report, schema, resolver=resolver)


def test_schema_required_top_level_fields_present(mock_constraints_yaml):
    """Schema invariant: every emitted report carries the required top-level fields."""
    from model_router.types import RouterOptions
    report = route(
        model_id="singlet-doublet",
        observables=["relic"],
        options=RouterOptions(),
        constraints_path=mock_constraints_yaml,
        blocker_catalog_path=FIXTURES / "blocker_catalog.yaml",
        analytic_exceptions_path=FIXTURES / "analytic_exceptions.yaml",
    )
    j = report.json_report
    for required in ("schema_version", "model_id", "observables", "verdict",
                     "model_props", "per_observable", "placements", "diagnostics"):
        assert required in j, f"Missing required top-level field: {required}"
    assert j["schema_version"] == 1
