"""
test_validation.py — WS5 parametrized integration tests for the model-router.

Tests validate the router's RoutingReport against per-model expected YAML files
for all four fixture-registry models. Created in S2; extended in S3, S4, S5, S7.

Models under test:
  singlet-doublet, two-hdm-a, dark-su3, dark-su3-confining-synthetic

Marker policy:
  load_bearing  — failure HOLDS WS5 unconditionally
  diagnostic    — failure ships with finding in WS5_FINDINGS.md

NOTE: import of route_for, report_pair, load_expected are module-level via
conftest helpers (not pytest fixtures) so they can be called from parametrize.
"""
from __future__ import annotations

import functools
import json
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Model list (parametrize over 4 canonical fixture models)
# ---------------------------------------------------------------------------
_MODELS = [
    "singlet-doublet",
    "two-hdm-a",
    "dark-su3",
    "dark-su3-confining-synthetic",
]

_OBSERVABLES = ["relic", "dd", "id"]

# Model × observable combos for per-observable tests (12 items)
_MODEL_OBS = [(m, o) for m in _MODELS for o in _OBSERVABLES]


# ---------------------------------------------------------------------------
# Module-level cache: route each model once per session to avoid 8× re-routes.
# We call conftest helpers directly (they are importable as module-level funcs).
# ---------------------------------------------------------------------------
from .conftest import report_pair, load_expected, route_for  # noqa: E402


@functools.lru_cache(maxsize=None)
def _get_reports(model_id: str) -> tuple[dict, dict]:
    """Cached per-model call to report_pair. lru_cache cuts routing from 80→8 invocations."""
    return report_pair(model_id)


# ---------------------------------------------------------------------------
# S2 — verdict: LOAD_BEARING (4 tests)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_id", _MODELS, ids=_MODELS)
@pytest.mark.load_bearing
def test_verdict(model_id: str) -> None:
    """Assert top-level verdict matches expected for each model. LOAD_BEARING."""
    default_report, _ = _get_reports(model_id)
    expected = load_expected(model_id)
    assert default_report["verdict"] == expected["verdict"], (
        f"[{model_id}] verdict mismatch: "
        f"got={default_report['verdict']!r}, expected={expected['verdict']!r}"
    )


# ---------------------------------------------------------------------------
# S2 — per_observable status: LOAD_BEARING (12 tests)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_id,obs", _MODEL_OBS, ids=[f"{m}-{o}" for m, o in _MODEL_OBS])
@pytest.mark.load_bearing
def test_per_observable_status(model_id: str, obs: str) -> None:
    """Assert per_observable[obs].status matches expected. LOAD_BEARING."""
    default_report, _ = _get_reports(model_id)
    expected = load_expected(model_id)
    actual = default_report["per_observable"][obs]["status"]
    exp_status = expected["per_observable"][obs]["status"]
    assert actual == exp_status, (
        f"[{model_id}/{obs}] status mismatch: got={actual!r}, expected={exp_status!r}"
    )


# ---------------------------------------------------------------------------
# S2 — per_observable active_chain prereq_id: LOAD_BEARING (12 tests)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_id,obs", _MODEL_OBS, ids=[f"{m}-{o}" for m, o in _MODEL_OBS])
@pytest.mark.load_bearing
def test_per_observable_active_chain_prereq(model_id: str, obs: str) -> None:
    """Assert active_chain prereq_id (or null) matches expected. LOAD_BEARING."""
    default_report, _ = _get_reports(model_id)
    expected = load_expected(model_id)
    expected_prereq = expected["per_observable"][obs]["active_chain_prereq_id"]
    actual_chain = default_report["per_observable"][obs].get("active_chain")

    if expected_prereq is None:
        assert actual_chain is None, (
            f"[{model_id}/{obs}] expected active_chain=null, got {actual_chain!r}"
        )
    else:
        assert actual_chain is not None, (
            f"[{model_id}/{obs}] expected active_chain.prereq_id={expected_prereq!r}, "
            f"but active_chain is null"
        )
        actual_prereq = actual_chain.get("prereq_id")
        assert actual_prereq == expected_prereq, (
            f"[{model_id}/{obs}] active_chain.prereq_id mismatch: "
            f"got={actual_prereq!r}, expected={expected_prereq!r}"
        )


# ---------------------------------------------------------------------------
# S2 — per_observable blockers set: DIAGNOSTIC (12 tests)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_id,obs", _MODEL_OBS, ids=[f"{m}-{o}" for m, o in _MODEL_OBS])
@pytest.mark.diagnostic
def test_per_observable_blockers_set(model_id: str, obs: str) -> None:
    """Assert per_observable[obs].blockers set matches expected. DIAGNOSTIC.

    blockers is List[str] per critic §M.1; assert as set() for order-independence.
    """
    default_report, _ = _get_reports(model_id)
    expected = load_expected(model_id)
    expected_blockers = set(expected["per_observable"][obs].get("blockers_set", []))
    actual_blockers = set(default_report["per_observable"][obs].get("blockers", []))
    assert actual_blockers == expected_blockers, (
        f"[{model_id}/{obs}] blockers set mismatch: "
        f"got={actual_blockers!r}, expected={expected_blockers!r}"
    )


# ===========================================================================
# S3 — dsu3 LOAD-BEARING assertions (4 tests: 3 LOAD_BEARING + 1 DIAGNOSTIC)
# ===========================================================================

@pytest.mark.load_bearing
def test_dsu3_per_candidate_pair_emitted() -> None:
    """Assert dark-su3 emits exactly 2 per_candidates per observable with correct names/labels.

    LOAD_BEARING: per plan §S3.Do.1.
    Iterates all three observables; expected labels are per-observable (iter-1 review O2):
      relic  → {Omega_V_h2, Omega_Psi_h2}
      dd     → {sigma_SI_V, sigma_SI_Psi}
      id     → {Phi_id_V, Phi_id_Psi}
    """
    default_report, _ = _get_reports("dark-su3")
    expected = load_expected("dark-su3")

    for obs in _OBSERVABLES:
        pcs = default_report["per_observable"][obs].get("per_candidate", [])
        exp_pc = expected.get("per_candidate", {}).get(obs, {})
        exp_length = exp_pc.get("length", 0)
        exp_names = set(exp_pc.get("names_set", []))
        exp_labels = set(exp_pc.get("labels_set", []))

        assert len(pcs) == exp_length, (
            f"[dark-su3/{obs}] per_candidate length mismatch: got={len(pcs)}, expected={exp_length}"
        )
        names = {pc["candidate_name"] for pc in pcs}
        assert names == exp_names, (
            f"[dark-su3/{obs}] per_candidate names mismatch: got={names!r}, expected={exp_names!r}"
        )
        labels = {pc["expected_observable_label"] for pc in pcs}
        assert labels == exp_labels, (
            f"[dark-su3/{obs}] per_candidate labels mismatch: got={labels!r}, expected={exp_labels!r}"
        )


@pytest.mark.load_bearing
def test_dsu3_dark_color_wall_surfaces_in_disclosure_banner() -> None:
    """Assert dark-su3 placements[0] contains the REGRESSION-ANCHOR triple-substring.

    LOAD_BEARING: per plan §S3.Do.2 + synthesis §1.2.
    Asserts kind, exception_id, position, and all three content substrings.
    GREEN against post-S0.5 fixture banner (iter-2 confirmed).
    Uses recompute_assertion_categories for DRY consistency (plan R7).
    """
    from .conftest import recompute_assertion_categories  # noqa: local import
    default_report, _ = _get_reports("dark-su3")

    placements = default_report.get("placements", [])
    assert len(placements) >= 1, "dark-su3 must have at least 1 placement"

    p0 = placements[0]
    assert p0["kind"] == "analytic", (
        f"placements[0].kind mismatch: got={p0['kind']!r}, expected='analytic'"
    )
    assert p0["exception_id"] == "dsu3-002", (
        f"placements[0].exception_id mismatch: got={p0['exception_id']!r}, expected='dsu3-002'"
    )
    assert p0["position"] == "before_per_observable", (
        f"placements[0].position mismatch: got={p0['position']!r}, expected='before_per_observable'"
    )

    content = p0["content"]
    for substring in ["REGRESSION-ANCHOR", "25000", "Planck target"]:
        assert substring in content, (
            f"placements[0].content missing required substring: {substring!r}"
        )

    # DRY cross-check: recompute_assertion_categories must also report True for this
    cats = recompute_assertion_categories("dark-su3", default_report)
    assert cats.get("dsu3_banner_triple_substring") is True, (
        "recompute_assertion_categories dsu3_banner_triple_substring returned False"
    )


@pytest.mark.diagnostic
def test_dsu3_matrix_acknowledgement_intact() -> None:
    """Assert no observable's active chain has matrix_acknowledgement_missing==True (default mode).

    DIAGNOSTIC: plan §S3.Do.3.
    In default mode, matrix_acknowledgement_missing is True only for relic (chain_override
    deliberately omits MATRIX_COVERAGE_GAP for the WS3 contract). This is an informational
    field — the router does NOT halt in default mode. Failure → WS5_FINDINGS.md.
    """
    default_report, _ = _get_reports("dark-su3")
    missing_obs = [
        obs
        for obs in _OBSERVABLES
        if default_report["per_observable"][obs]
        .get("active_chain", {})
        .get("matrix_acknowledgement_missing", False)
    ]
    # In default mode, relic's chain_override lacks MATRIX_COVERAGE_GAP acknowledgement.
    # This is a known finding (WS3 contract); document rather than assert as zero.
    # Failure DIAGNOSTIC only — file in WS5_FINDINGS.md if unexpected observables appear.
    unexpected = [o for o in missing_obs if o != "relic"]
    assert not unexpected, (
        f"Unexpected matrix_acknowledgement_missing=True for observables: {unexpected} "
        f"(relic is expected to be missing per WS3 fixture contract)"
    )


@pytest.mark.load_bearing
def test_dsu3_active_chain_is_analytic_backend() -> None:
    """Assert all three dark-su3 observables have active_chain with prereq_id=analytic_backend, role=escape_hatch.

    LOAD_BEARING: plan §S3.Do.4.
    """
    default_report, _ = _get_reports("dark-su3")
    for obs in _OBSERVABLES:
        ac = default_report["per_observable"][obs].get("active_chain")
        assert ac is not None, f"[dark-su3/{obs}] active_chain is null"
        assert ac.get("prereq_id") == "analytic_backend", (
            f"[dark-su3/{obs}] active_chain.prereq_id={ac.get('prereq_id')!r}, expected='analytic_backend'"
        )
        assert ac.get("role") == "escape_hatch", (
            f"[dark-su3/{obs}] active_chain.role={ac.get('role')!r}, expected='escape_hatch'"
        )


# ===========================================================================
# S4 — Strict-mode + exit-code assertions (8 LOAD_BEARING tests)
# ===========================================================================

@pytest.mark.parametrize("model_id", _MODELS, ids=_MODELS)
@pytest.mark.load_bearing
def test_exit_code_default(model_id: str) -> None:
    """Assert default-mode exit_code == 0 for all models. LOAD_BEARING.

    Per spike: all four models exit 0 in default mode (HARD_HALT does not
    set a non-zero exit code in default mode — strict mode only).
    """
    default_report, _ = _get_reports(model_id)
    assert default_report["exit_code"] == 0, (
        f"[{model_id}] default exit_code={default_report['exit_code']!r}, expected=0"
    )


@pytest.mark.parametrize("model_id", _MODELS, ids=_MODELS)
@pytest.mark.load_bearing
def test_exit_code_strict(model_id: str) -> None:
    """Assert strict-mode exit_code matches expected per spike output. LOAD_BEARING.

    Expected (per post-S0.5 spike + iter-2 D5):
      singlet-doublet               → 0
      two-hdm-a                     → 5  (HALT_FOR_SIGNOFF)
      dark-su3                      → 4  (MatrixAcknowledgementMissing; sentinel dict)
      dark-su3-confining-synthetic  → 6  (HARD_HALT)

    Uses dict-access (Recommendation #2): report_pair returns json_report dicts,
    including the sentinel dict for dark-su3 strict mode.
    """
    expected = load_expected(model_id)
    _, strict_report = _get_reports(model_id)
    expected_exit = expected["exit_code"]["strict"]
    actual_exit = strict_report["exit_code"]
    assert actual_exit == expected_exit, (
        f"[{model_id}] strict exit_code={actual_exit!r}, expected={expected_exit!r}"
    )


# ===========================================================================
# S5 — Markdown 3-substring + HARD_HALT no-signoff negative (5 LOAD_BEARING tests)
# ===========================================================================

@pytest.mark.load_bearing
def test_dsu3_markdown_contains_regression_anchor_phrase() -> None:
    """Assert dark-su3 markdown_report contains the full REGRESSION-ANCHOR phrase.

    LOAD_BEARING: plan §S5.Do.1.
    The post-S0.5 fixture banner repair makes this GREEN.
    """
    r = route_for("dark-su3", ["relic", "dd", "id"], strict=False)
    md = r.markdown_report
    assert "REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (dsu3-002)" in md, (
        "dark-su3 markdown missing REGRESSION-ANCHOR phrase"
    )


@pytest.mark.load_bearing
def test_two_hdm_a_markdown_contains_signoff_section_header() -> None:
    """Assert two-hdm-a markdown_report contains the signoff section header.

    LOAD_BEARING: plan §S5.Do.2.
    The section header is inlined in render.py:328-335 as a hardcoded template
    (per critic R11); GREEN regardless of WS4 prompt-callable concern.
    """
    r = route_for("two-hdm-a", ["relic", "dd", "id"], strict=False)
    md = r.markdown_report
    assert "## Required next steps (analytic exception sign-off)" in md, (
        "two-hdm-a markdown missing '## Required next steps (analytic exception sign-off)'"
    )


@pytest.mark.load_bearing
def test_dark_su3_confining_markdown_contains_eft_rewrite_phrase() -> None:
    """Assert dark-su3-confining-synthetic markdown_report contains EFT REWRITE REQUIRED.

    LOAD_BEARING: plan §S5.Do.3.
    """
    r = route_for("dark-su3-confining-synthetic", ["relic", "dd", "id"], strict=False)
    md = r.markdown_report
    assert "EFT REWRITE REQUIRED" in md, (
        "dark-su3-confining-synthetic markdown missing 'EFT REWRITE REQUIRED'"
    )


@pytest.mark.load_bearing
def test_dark_su3_confining_markdown_no_signoff_section() -> None:
    """Assert dark-su3-confining-synthetic markdown does NOT contain the signoff section header.

    LOAD_BEARING: plan §S5.Do.4.
    HARD_HALT vs HALT_FOR_SIGNOFF distinguisher — the EFT rewrite halt does not
    include a signoff prompt section (placements contain hard_halt_prompt, not signoff_prompt).
    """
    r = route_for("dark-su3-confining-synthetic", ["relic", "dd", "id"], strict=False)
    md = r.markdown_report
    assert "## Required next steps" not in md, (
        "dark-su3-confining-synthetic markdown should NOT contain '## Required next steps' "
        "(HARD_HALT must not produce a signoff section)"
    )


@pytest.mark.load_bearing
def test_hard_halt_no_signoff_placement() -> None:
    """Assert dark-su3-confining-synthetic placements contain no signoff_prompt entry.

    LOAD_BEARING: plan §S5.Do.5.
    Verifies the JSON placement list (not markdown) for the signoff_prompt kind.
    """
    default_report, _ = _get_reports("dark-su3-confining-synthetic")
    placements = default_report.get("placements", [])
    signoff_placements = [p for p in placements if p.get("kind") == "signoff_prompt"]
    assert not signoff_placements, (
        f"dark-su3-confining-synthetic has unexpected signoff_prompt placements: {signoff_placements}"
    )


# ===========================================================================
# S7 — Snapshot tripwire tests
#
# Snapshot files live in tests/integration/snapshots/.
# dark-su3-strict is MISSING (MatrixAcknowledgementMissing; sentinel dict is
# not schema-valid). This is documented in WS5_FINDINGS.md Finding 4.
# Actual snapshot parametrize list is 7 items (3 models × 2 modes - 1 skip).
# ===========================================================================

_SNAPSHOTS_DIR = pathlib.Path(__file__).resolve().parent / "snapshots"

# All (model_id, mode) pairs that have actual snapshot files.
# dark-su3-strict is excluded — MatrixAcknowledgementMissing; see WS5_FINDINGS.md.
_SNAPSHOT_PAIRS = [
    ("singlet-doublet", "default"),
    ("singlet-doublet", "strict"),
    ("two-hdm-a", "default"),
    ("two-hdm-a", "strict"),
    ("dark-su3", "default"),
    # ("dark-su3", "strict"),  # SKIP: MatrixAcknowledgementMissing — WS5_FINDINGS.md Finding 4
    ("dark-su3-confining-synthetic", "default"),
    ("dark-su3-confining-synthetic", "strict"),
]
_SNAPSHOT_IDS = [f"{m}-{mode}" for m, mode in _SNAPSHOT_PAIRS]


def _slug(model_id: str) -> str:
    return model_id.replace("-", "_")


def _snapshot_path(model_id: str, mode: str) -> pathlib.Path:
    suffix = ".strict.json" if mode == "strict" else ".json"
    return _SNAPSHOTS_DIR / f"{_slug(model_id)}{suffix}"


def _recompute_snapshot(model_id: str, mode: str) -> dict:
    """Re-route model in given mode and apply Option B normalization."""
    from .conftest import route_for  # noqa: late import
    from model_router.types import MatrixAcknowledgementMissing

    strict = mode == "strict"
    try:
        result = route_for(model_id, ["relic", "dd", "id"], strict=strict)
        report = dict(result.json_report)
    except MatrixAcknowledgementMissing:
        # Should not be reachable for the pairs in _SNAPSHOT_PAIRS.
        raise

    # Option B normalization: sort diagnostics dict only.
    if "diagnostics" in report and isinstance(report["diagnostics"], dict):
        report["diagnostics"] = dict(sorted(report["diagnostics"].items()))
    return report


@pytest.mark.parametrize("model_id,mode", _SNAPSHOT_PAIRS, ids=_SNAPSHOT_IDS)
@pytest.mark.diagnostic
def test_snapshot_matches(model_id: str, mode: str) -> None:
    """Assert re-routed report byte-for-byte matches checked-in snapshot. DIAGNOSTIC.

    Compares re-routed + Option-B-normalized report to the checked-in snapshot.
    DIAGNOSTIC: snapshot drift is expected after legitimate router changes;
    run regenerate_snapshots.py to update after intentional router changes.
    Failure → WS5_FINDINGS.md (ships with finding, does not HOLD WS5).
    """
    snap_path = _snapshot_path(model_id, mode)
    assert snap_path.exists(), (
        f"Snapshot file missing: {snap_path}. Run regenerate_snapshots.py --all."
    )

    expected_json = json.loads(snap_path.read_text())
    actual_json = _recompute_snapshot(model_id, mode)

    assert actual_json == expected_json, (
        f"[{model_id}-{mode}] snapshot mismatch. "
        f"Run regenerate_snapshots.py --model {model_id} to update."
    )


@pytest.mark.parametrize("model_id,mode", _SNAPSHOT_PAIRS, ids=_SNAPSHOT_IDS)
@pytest.mark.load_bearing
def test_snapshot_validates_against_schema(model_id: str, mode: str) -> None:
    """Assert checked-in snapshot validates against routing_report.schema.json. LOAD_BEARING.

    Loads schema via model_router.stages.render._schema_path (per OD3 ratification).
    Validates using jsonschema. Failure HOLDS WS5.
    """
    snap_path = _snapshot_path(model_id, mode)
    assert snap_path.exists(), (
        f"Snapshot file missing: {snap_path}. Run regenerate_snapshots.py --all."
    )

    snapshot_dict = json.loads(snap_path.read_text())

    # Load schema via the public helper from render.py (OD3: re-import, not hardcode)
    from model_router.stages.render import _schema_path as get_schema_path

    schema_path = get_schema_path()
    schema = json.loads(schema_path.read_text())

    try:
        import jsonschema  # type: ignore
    except ImportError:
        pytest.skip("jsonschema not installed — schema validation skipped")

    # Validate using the same logic as render._validate_json_against_schema.
    # Mirror render.py verbatim to avoid divergence.
    base_uri = schema_path.parent.as_uri() + "/"
    try:
        from referencing import Registry, Resource  # type: ignore
        from referencing.jsonschema import DRAFT7  # type: ignore

        ranked_path = schema_path.parent / "ranked_chain.schema.json"
        ranked_schema = json.loads(ranked_path.read_text())
        registry = Registry().with_resource(
            "ranked_chain.schema.json",
            Resource(contents=ranked_schema, specification=DRAFT7),
        )
        validator = jsonschema.Draft7Validator(schema, registry=registry)
        errors = list(validator.iter_errors(snapshot_dict))
        if errors:
            raise jsonschema.ValidationError(errors[0].message)
    except ImportError:
        # Older jsonschema without referencing library
        resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema)
        jsonschema.validate(snapshot_dict, schema, resolver=resolver)
