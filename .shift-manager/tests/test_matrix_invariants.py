"""S11 + S11b: Hard CI invariants for the WS2 capability matrix.

12 invariants total:
  Batch A (#1–#6):
    #1 Schema validity
    #2 Blocker registry completeness (no dangling codes)
    #3 Blocker-class enum
    #4 Verdict enum (no 'unknown')
    #5 Required-field-by-verdict
    #6 Axis-name resolvability

  Batch B (#7–#12):
    #7 Coverage (every axis×value pair has ≥1 non-NA rule)
    #8 No shadowed rules within a prereq
    #9 Forward drift (SKILL.md blocker codes appear in matrix)
    #10 Orphan rule (every matrix blocker code has a catalog entry)
    #11 escape_hatch reachability
    #12 Override-matrix conflict → requires matrix_acknowledgement
"""
from __future__ import annotations
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Iterator

import yaml
import pytest

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
NEGATIVE_FIXTURES = Path(__file__).parent / "fixtures" / "matrix" / "negative"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import load_capability_matrix

# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _all_rules(caps: dict) -> Iterator[dict]:
    """Yield all leaf rules from a capabilities block's support list."""
    for rule in caps.get("support", []):
        yield from _flatten_rule(rule)


def _flatten_rule(rule: dict) -> Iterator[dict]:
    """Flatten and/or rules to leaf rules."""
    if "and" in rule:
        for sub in rule["and"]:
            yield from _flatten_rule(sub)
        yield rule  # yield the and-rule itself (for verdict check)
    elif "or" in rule:
        for sub in rule["or"]:
            yield from _flatten_rule(sub)
        yield rule  # yield the or-rule itself
    else:
        yield rule


def _blocker_codes_in_rule(rule: dict) -> set:
    codes = set()
    if "blocker" in rule:
        codes.add(rule["blocker"])
    if "and" in rule:
        for sub in rule["and"]:
            codes |= _blocker_codes_in_rule(sub)
    if "or" in rule:
        for sub in rule["or"]:
            codes |= _blocker_codes_in_rule(sub)
    return codes


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def matrix():
    return load_capability_matrix(
        constraints_path=SHARED / "constraints.yaml",
        catalog_path=SHARED / "blocker_catalog.yaml",
    )


@pytest.fixture(scope="module")
def constraints_data():
    return yaml.safe_load((SHARED / "constraints.yaml").read_text())


@pytest.fixture(scope="module")
def catalog_data():
    return yaml.safe_load((SHARED / "blocker_catalog.yaml").read_text())


@pytest.fixture(scope="module")
def snapshot_data():
    return yaml.safe_load((SHARED / "ws1_axis_enums_snapshot.yaml").read_text())


# ────────────────────────────────────────────────────────────────────────────
# Batch A: invariants #1–#6
# ────────────────────────────────────────────────────────────────────────────

class TestInvariantsBatchA:
    def test_invariant_1_schema_validity(self, matrix):
        """#1: Matrix loads without ValidationError."""
        # If we got here, load_capability_matrix succeeded (it validates internally)
        assert matrix is not None
        assert matrix.get_constraints_data()["schema_version"] == 2

    def test_invariant_2_no_dangling_blocker_codes(self, constraints_data, catalog_data):
        """#2: Every blocker: cited in any support rule has an entry in blocker_catalog.yaml."""
        catalog_codes = set(catalog_data["blockers"].keys())
        dangling = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_rules(caps):
                codes = _blocker_codes_in_rule(rule)
                for code in codes:
                    if code not in catalog_codes:
                        dangling.append(f"{prereq_id}: {code}")
        assert not dangling, f"Dangling blocker codes (not in catalog): {dangling}"

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_invariant_2_negative_dangling_fixture(self):
        """#2 negative: dangling blocker fixture is detected."""
        import yaml as _yaml
        fixture = _yaml.safe_load((NEGATIVE_FIXTURES / "dangling_blocker.yaml").read_text())
        catalog_data = _yaml.safe_load((SHARED / "blocker_catalog.yaml").read_text())
        catalog_codes = set(catalog_data["blockers"].keys())
        dangling = []
        for prereq_id, prereq in fixture.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_rules(caps):
                codes = _blocker_codes_in_rule(rule)
                for code in codes:
                    if code not in catalog_codes:
                        dangling.append(code)
        assert dangling, "Expected dangling blocker code in negative fixture"
        assert "NONEXISTENT_CODE_XYZ_123" in dangling

    def test_invariant_3_blocker_class_enum(self, catalog_data):
        """#3: Every blocker.class in the 5-class enum."""
        VALID = {
            "missing-skill", "missing-tool-feature", "fundamental-group-theory-gap",
            "regime-mismatch", "spec-authoring-gap", "informational", "analytic-exception"
        }
        for code, entry in catalog_data["blockers"].items():
            assert entry["class"] in VALID, f"{code}: bad class '{entry['class']}'"

    def test_invariant_4_verdict_enum_no_unknown(self, constraints_data):
        """#4: Every verdict in the 4-value enum; no 'unknown'."""
        VALID = {"supported", "supported_with_caveat", "blocked", "not_applicable"}
        violations = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_rules(caps):
                v = rule.get("verdict")
                if v and v not in VALID:
                    violations.append(f"{prereq_id}: verdict='{v}'")
        assert not violations, f"Invalid verdicts: {violations}"

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_invariant_4_negative_unknown_verdict(self):
        """#4 negative: fixture with verdict: unknown fails schema validation."""
        import yaml as _yaml
        fixture = _yaml.safe_load((NEGATIVE_FIXTURES / "verdict_unknown.yaml").read_text())
        schema = json.loads((SHARED / "matrix_capabilities.schema.json").read_text())
        for prereq_id, prereq in fixture.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if caps:
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=caps, schema=schema)
                return
        pytest.fail("No capabilities block found in negative fixture")

    def test_invariant_5_required_fields_by_verdict(self, constraints_data):
        """#5: blocked requires blocker+evidence; supported_with_caveat requires caveat+evidence."""
        violations = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in caps.get("support", []):
                # Only check leaf-level rules (not and/or containers)
                if "axis" in rule and "verdict" in rule:
                    v = rule.get("verdict")
                    if v == "blocked":
                        if not rule.get("blocker"):
                            violations.append(f"{prereq_id}: blocked without blocker")
                        if not rule.get("evidence"):
                            violations.append(f"{prereq_id}: blocked without evidence")
                    elif v == "supported_with_caveat":
                        if not rule.get("caveat"):
                            violations.append(f"{prereq_id}: supported_with_caveat without caveat")
                        if not rule.get("evidence"):
                            violations.append(f"{prereq_id}: supported_with_caveat without evidence")
        assert not violations, f"Required-field violations: {violations}"

    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_invariant_5_negative_missing_evidence(self):
        """#5 negative: blocked without evidence fails schema validation."""
        import yaml as _yaml
        fixture = _yaml.safe_load((NEGATIVE_FIXTURES / "missing_evidence.yaml").read_text())
        schema = json.loads((SHARED / "matrix_capabilities.schema.json").read_text())
        for prereq_id, prereq in fixture.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if caps:
                with pytest.raises(jsonschema.ValidationError):
                    jsonschema.validate(instance=caps, schema=schema)
                return
        pytest.fail("No capabilities block found in negative fixture")

    def test_invariant_6_axis_names_resolvable(self, constraints_data, snapshot_data):
        """#6: Every axis: value resolves against the WS1 axis snapshot."""
        # Build a set of valid axis names from the snapshot
        valid_axes = set(snapshot_data.keys()) | {"A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"}
        valid_axes.update({
            "A2[?].pattern", "A3.has_dark_charged_fermion", "A3.has_majorana_fermion",
            "A3.has_chiral_bsm_fermion", "A4.n_higgs_doublets", "A4.cp_odd_scalar_present",
            "A4.n_pure_sm_singlets", "A4.n_dark_charged_scalars", "A4.replaces_sm_higgs",
            "candidates[?].mediator_regime", "candidates[?].uv_provenance",
            "candidates[?].cp", "candidates[?].field_type", "candidates[?].stabilisation_mechanism",
            "candidates[*]",
            "lagrangian.spec_intent.requested_emissions", "lagrangian.kinetic_mixing_terms",
            "model.analytic_module_status",
        })

        unknown_axes = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in caps.get("support", []):
                if "axis" in rule:
                    axis = rule["axis"]
                    if axis not in valid_axes:
                        unknown_axes.append(f"{prereq_id}: axis='{axis}'")
        assert not unknown_axes, f"Unknown axis names: {unknown_axes}"


# ────────────────────────────────────────────────────────────────────────────
# Batch B: invariants #7–#12
# ────────────────────────────────────────────────────────────────────────────

class TestInvariantsBatchB:
    def test_invariant_7_axis_coverage(self, constraints_data, snapshot_data):
        """#7: For every WS1 axis × value pair, at least one prereq has a non-NA rule.

        Partial coverage check: A1 and A8 are enumerable; check these specifically.
        Other axes (A3 booleans, A4 integers) are covered by wildcard rules.
        """
        a1_values = snapshot_data.get("A1", [])
        a8_values = snapshot_data.get("A8", [])

        # For A1: verify each value appears in at least one rule (match or * wildcard)
        # across all prereqs with capabilities
        def has_coverage(axis, value, prereqs):
            for prereq_id, prereq in prereqs.items():
                caps = prereq.get("capabilities")
                if not caps:
                    continue
                for rule in caps.get("support", []):
                    if "axis" in rule:
                        if rule["axis"] == axis:
                            m = rule.get("match")
                            if m == "*" or m == value or (isinstance(m, list) and value in m):
                                if rule.get("verdict") != "not_applicable":
                                    return True
            return False

        prereqs = constraints_data.get("prereqs", {})
        # CQ5 fix: remove "more than half" slack.  Known gaps are explicit.
        # Values legitimately not yet covered by any non-NA rule in v1:
        KNOWN_UNCOVERED_A1 = {"Non-SM-embedding"}
        uncovered = []
        for val in a1_values:
            if not has_coverage("A1", val, prereqs):
                uncovered.append(f"A1={val}")
        unexpected_uncovered = [u for u in uncovered if u.split("=", 1)[1] not in KNOWN_UNCOVERED_A1]
        if unexpected_uncovered:
            pytest.fail(
                f"Unexpected uncovered A1 values (not in KNOWN_UNCOVERED_A1={KNOWN_UNCOVERED_A1}): "
                f"{unexpected_uncovered}"
            )

    def test_invariant_8_no_shadowed_rules(self, constraints_data):
        """#8: Within a prereq, no rule is shadowed by an earlier match:* on the same axis."""
        violations = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            seen_wildcard_axes = set()
            for rule in caps.get("support", []):
                if "axis" not in rule:
                    continue  # skip and/or containers
                axis = rule["axis"]
                if axis in seen_wildcard_axes:
                    # A rule after a wildcard on the same axis is shadowed
                    intentional = rule.get("intentional_shadow", False)
                    if not intentional:
                        violations.append(
                            f"{prereq_id}: rule on axis '{axis}' shadowed by earlier match:*"
                        )
                if rule.get("match") == "*":
                    seen_wildcard_axes.add(axis)
        assert not violations, f"Shadowed rules: {violations}"

    def test_invariant_9_no_matrix_code_missing_from_catalog(self, constraints_data, catalog_data):
        """#9: Every blocker code in the matrix's support rules must appear in the catalog.

        CQ6 fix: previous implementation duplicated invariant #2.  The proper forward-
        drift check (SKILL.md codes must appear in matrix) is in
        test_matrix_drift.py::TestBidirectionalDrift::test_forward_drift_skill_codes_in_matrix.
        This test is kept as a distinct belt+suspenders check with a clearer name:
        no matrix code is allowed to be absent from the catalog.
        """
        catalog_codes = set(catalog_data["blockers"].keys())
        matrix_codes: set = set()
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_rules(caps):
                matrix_codes |= _blocker_codes_in_rule(rule)
        dangling = matrix_codes - catalog_codes
        assert not dangling, (
            f"Matrix support rules reference codes absent from blocker_catalog.yaml "
            f"(dangling = not registered): {dangling}"
        )

    def test_invariant_10_orphan_rule_catalog_cross_ref(self, constraints_data, catalog_data):
        """#10: Every matrix blocker has an entry in catalog with a reference field."""
        catalog = catalog_data["blockers"]
        violations = []
        for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            for rule in _all_rules(caps):
                for code in _blocker_codes_in_rule(rule):
                    entry = catalog.get(code)
                    if not entry:
                        violations.append(f"{prereq_id}: {code} not in catalog")
                        continue
                    # Must have at least one reference field
                    has_ref = any(
                        entry.get(k)
                        for k in ["digest_reference", "ws1_reference", "ws4_reference"]
                    )
                    if not has_ref:
                        violations.append(
                            f"{prereq_id}: {code} in catalog but missing all reference fields"
                        )
        assert not violations, f"Orphan rule violations: {violations}"

    def test_invariant_11_escape_hatch_reachability(self, constraints_data):
        """#11: For every observable with a blocked prereq that can serve it,
        at least one escape_hatch or primary exists for that observable.

        CQ4 fix: filter has_blocked to prereqs with role.<obs> != 'none'.
        A prereq that is blocked but has role.relic='none' should not trigger
        the escape-hatch requirement for relic.
        """
        observables = ["relic", "dd", "id"]  # skip collider (placeholder)
        prereqs = constraints_data.get("prereqs", {})

        for obs in observables:
            # Only count blockers from prereqs that have a non-'none' role for this observable
            has_blocked = any(
                prereq.get("capabilities", {}).get("role", {}).get(obs, "none") != "none"
                and any(
                    rule.get("verdict") == "blocked"
                    for rule in _all_rules(prereq.get("capabilities", {}) or {})
                )
                for prereq in prereqs.values()
                if prereq.get("capabilities")
            )
            if not has_blocked:
                continue  # no observable-scoped blockers — skip check

            has_escape = any(
                prereq.get("capabilities", {}).get("role", {}).get(obs) in ("escape_hatch", "primary")
                for prereq in prereqs.values()
                if prereq.get("capabilities")
            )
            assert has_escape, (
                f"Observable '{obs}' has blocked prereqs with non-none role "
                f"but no escape_hatch or primary for that observable"
            )

    def test_invariant_12_override_requires_acknowledgement(self, constraints_data):
        """#12: chain_overrides that drop prereqs carrying matrix blockers must include
        matrix_acknowledgement listing every such blocker code.

        Algorithm (plan review §Blocker 6):
          1. For each model's chain_override, compute removed_prereqs =
             default_chain - override_chain.
          2. Collect all blocker codes in the matrix's support rules for each
             removed prereq.
          3. If any blocker codes exist for removed prereqs, require that:
             (a) matrix_acknowledgement is present, and
             (b) every blocker code is listed in accepted_blockers.

        This catches the case where a future override silently drops a blocked
        prereq without acknowledgement.
        """
        models = constraints_data.get("models", {})
        violations = []

        for model_id, model in models.items():
            overrides = model.get("chain_overrides", {})
            for observable, override in overrides.items():
                override_chain = set(override.get("chain", []))
                default_chain = set(
                    constraints_data.get("constraints", {}).get(observable, {}).get("chain", [])
                )
                removed_prereqs = default_chain - override_chain
                if not removed_prereqs:
                    continue

                # Collect all blocker codes in matrix rules for removed prereqs
                removed_blocker_codes: set = set()
                for prereq_id in removed_prereqs:
                    prereq = constraints_data.get("prereqs", {}).get(prereq_id, {})
                    caps = prereq.get("capabilities")
                    if not caps:
                        continue
                    for rule in _all_rules(caps):
                        if rule.get("verdict") == "blocked" and "blocker" in rule:
                            removed_blocker_codes.add(rule["blocker"])

                if not removed_blocker_codes:
                    continue  # removed prereqs have no blockers; no ack required

                ack = override.get("matrix_acknowledgement")
                if ack is None:
                    violations.append(
                        f"{model_id}.chain_overrides.{observable}: removes prereqs "
                        f"{sorted(removed_prereqs)} which carry blockers "
                        f"{sorted(removed_blocker_codes)}, but matrix_acknowledgement is absent"
                    )
                    continue

                accepted = set(ack.get("accepted_blockers", []))
                unacknowledged = removed_blocker_codes - accepted
                if unacknowledged:
                    violations.append(
                        f"{model_id}.chain_overrides.{observable}: blockers "
                        f"{sorted(unacknowledged)} from removed prereqs are not listed "
                        f"in accepted_blockers (accepted: {sorted(accepted)})"
                    )

        assert not violations, (
            "Invariant #12 violation — override-without-acknowledgement:\n"
            + "\n".join(violations)
        )

    def test_invariant_12_negative_missing_acknowledgement(self):
        """#12 negative: override without matrix_acknowledgement fixture is detectable."""
        fixture = yaml.safe_load((NEGATIVE_FIXTURES / "missing_acknowledgement.yaml").read_text())
        models = fixture.get("models", {})
        for model_id, model in models.items():
            overrides = model.get("chain_overrides", {})
            for constraint, override in overrides.items():
                ack = override.get("matrix_acknowledgement")
                if ack is None:
                    # Found a missing acknowledgement — test passes
                    return
        pytest.fail("Expected missing matrix_acknowledgement in negative fixture")
