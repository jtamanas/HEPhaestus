"""S4a + S4b + S5: TDD tests for the single-axis matcher and and:/or: conjunctions.

Single-axis tests (12 cases from WS2 plan S4a):
  1. A1 match exact string against SM → match
  2. A1 match list against SM → match
  3. A1 match SM+SU(N) against dsu3 → match
  4. candidates[?].mediator_regime narrow-resonance against dsu3 → no match
  5. candidates[?].mediator_regime tree-level-open against dsu3 → match
  6. candidates[*] >= 2 against dsu3 → match
  7. A4.n_higgs_doublets >= 2 against 2hdm_a → match
  8. A1 match * → always match
  9. lagrangian.spec_intent.requested_emissions not_contains[calchep_mdl] vs [ufo] → match
  10. contains[calchep_mdl] against synthetic fixture → match
  11. A2[?].pattern against singlet_doublet (A2=[]) → no match (empty list)
  12. candidates[?].cp odd against empty candidates → no match

Conjunction tests (S5 — 6 cases):
  (a) ANALYTIC_EXCEPTION_TRIGGER conjunction against dsu3 → match
  (b) Same against singlet_doublet → no match
  (c) and: with SM+mirror → no match on dsu3
  (d) and: with empty A2[?].pattern → no match
  (e) or: with all false → false; with one true → true
  (f) and: with single sub-rule → works
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"
FIXTURES = Path(__file__).parent / "fixtures" / "matrix"

if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))

from matrix_lookup import _match_single_axis, _match_and, _match_or, _match_rule


@pytest.fixture
def dsu3(dark_su3_axes):
    return dark_su3_axes


@pytest.fixture
def sd(singlet_doublet_axes):
    return singlet_doublet_axes


@pytest.fixture
def hdm(two_hdm_a_axes):
    return two_hdm_a_axes


@pytest.fixture
def synthetic_calchep():
    """Synthetic fixture with calchep_mdl in requested_emissions."""
    return {
        "axes": {"A1": "SM", "A8": "complete"},
        "candidates": [],
        "lagrangian": {
            "spec_intent": {
                "requested_emissions": ["calchep_mdl", "ufo"]
            },
            "kinetic_mixing_terms": [],
        },
        "model_runtime": {"analytic_module_status": "missing"},
    }


# ─── Single-axis tests ────────────────────────────────────────────────────────

class TestSingleAxisMatcher:
    def test_01_a1_exact_sm_matches(self, sd):
        rule = {"axis": "A1", "match": "SM", "verdict": "supported"}
        assert _match_single_axis(rule, sd) is not None

    def test_02_a1_list_sm_matches(self, sd):
        rule = {"axis": "A1", "match": ["SM", "SM + extra U(1)"], "verdict": "supported"}
        assert _match_single_axis(rule, sd) is not None

    def test_03_a1_sun_matches_dsu3(self, dsu3):
        rule = {"axis": "A1", "match": "SM + extra SU(N)", "verdict": "blocked",
                "blocker": "MG5_DARK_COLOR_TENSOR_WALL", "evidence": "digest.md §52"}
        assert _match_single_axis(rule, dsu3) is not None

    def test_04_candidates_mediator_regime_narrow_no_match_dsu3(self, dsu3):
        rule = {"axis": "candidates[?].mediator_regime", "match": "narrow-resonance",
                "verdict": "specialty"}
        # dsu3 candidates have tree-level-open, not narrow-resonance
        assert _match_single_axis(rule, dsu3) is None

    def test_05_candidates_mediator_regime_tree_matches_dsu3(self, dsu3):
        rule = {"axis": "candidates[?].mediator_regime", "match": "tree-level-open",
                "verdict": "supported"}
        assert _match_single_axis(rule, dsu3) is not None

    def test_06_candidates_star_count_ge2_dsu3(self, dsu3):
        rule = {"axis": "candidates[*]", "match": ">=2", "verdict": "supported"}
        assert _match_single_axis(rule, dsu3) is not None

    def test_07_a4_n_higgs_ge2_2hdm(self, hdm):
        rule = {"axis": "A4.n_higgs_doublets", "match": ">=2", "verdict": "supported"}
        assert _match_single_axis(rule, hdm) is not None

    def test_08_wildcard_matches_any(self, sd):
        rule = {"axis": "A1", "match": "*", "verdict": "supported"}
        assert _match_single_axis(rule, sd) is not None

    def test_09_not_contains_calchep_matches_ufo_only(self, dsu3):
        rule = {"axis": "lagrangian.spec_intent.requested_emissions",
                "match": "not_contains[calchep_mdl]", "verdict": "blocked",
                "blocker": "CALCHEP_MDL_MISSING", "evidence": "digest.md §12"}
        # dsu3 has [ufo], no calchep_mdl → not_contains → True → match
        assert _match_single_axis(rule, dsu3) is not None

    def test_10_contains_calchep_matches_synthetic(self, synthetic_calchep):
        rule = {"axis": "lagrangian.spec_intent.requested_emissions",
                "match": "contains[calchep_mdl]", "verdict": "supported"}
        assert _match_single_axis(rule, synthetic_calchep) is not None

    def test_11_a2_existential_empty_list_no_match(self, sd):
        """A2[?].pattern against singlet_doublet (A2=[]) → no match (empty list existential)."""
        rule = {"axis": "A2[?].pattern", "match": "Higgsed-partial", "verdict": "blocked",
                "blocker": "MG5_DARK_COLOR_TENSOR_WALL", "evidence": "digest.md §52"}
        # sd has A2=[], existential over empty list → false
        assert _match_single_axis(rule, sd) is None

    def test_12_candidates_cp_odd_empty_candidates_no_match(self):
        """candidates[?].cp odd against empty candidates → no match."""
        bundle = {
            "axes": {"A1": "SM", "A8": "complete"},
            "candidates": [],
            "lagrangian": {},
            "model_runtime": {},
        }
        rule = {"axis": "candidates[?].cp", "match": "odd", "verdict": "not_applicable"}
        assert _match_single_axis(rule, bundle) is None


# ─── Conjunction tests (S5) ──────────────────────────────────────────────────

class TestConjunctionMatcher:
    """The ANALYTIC_EXCEPTION_TRIGGER rule from WS2 synthesis §3.3:
    A1 in {SM+extra SU(N), SM+extra mixed}
    AND (A2[?].pattern in {Higgsed-partial, unbroken-confining}
         OR candidates[?].uv_provenance in {broken-generator-boson, composite})
    """

    def _analytic_trigger_rule(self):
        return {
            "and": [
                {"axis": "A1",
                 "match": ["SM + extra SU(N)", "SM + extra mixed"]},
                {"or": [
                    {"axis": "A2[?].pattern",
                     "match": ["Higgsed-partial", "unbroken-confining"]},
                    {"axis": "candidates[?].uv_provenance",
                     "match": ["broken-generator-boson", "composite"]},
                ]},
            ],
            "verdict": "blocked",
            "blocker": "ANALYTIC_EXCEPTION_TRIGGER",
            "evidence": "ws1_taxonomy_synthesis.md:660-686",
        }

    def test_a_trigger_matches_dsu3(self, dsu3):
        """Full trigger rule matches dsu3 (A1=SM+SU(N), A2 has Higgsed-partial)."""
        rule = self._analytic_trigger_rule()
        assert _match_rule(rule, dsu3) is not None

    def test_b_trigger_no_match_singlet_doublet(self, sd):
        """Trigger does NOT match singlet-doublet (A1=SM → first and-sub fails)."""
        rule = self._analytic_trigger_rule()
        assert _match_rule(rule, sd) is None

    def test_c_and_with_mirror_no_match_dsu3(self, dsu3):
        """and: requiring SM+mirror does not match dsu3 (A1=SM+SU(N))."""
        rule = {
            "and": [
                {"axis": "A1", "match": "SM + mirror"},
            ],
            "verdict": "blocked",
            "blocker": "MG5_MIRROR_COLOR_WALL",
            "evidence": "digest.md"
        }
        assert _match_rule(rule, dsu3) is None

    def test_d_and_with_empty_list_propagates_false(self, sd):
        """and: containing A2[?].pattern against singlet_doublet (A2=[]) → no match."""
        rule = {
            "and": [
                {"axis": "A1", "match": ["SM", "SM + extra U(1)"]},
                {"axis": "A2[?].pattern", "match": "Higgsed-partial"},
            ],
            "verdict": "blocked",
            "blocker": "ANALYTIC_EXCEPTION_TRIGGER",
            "evidence": "test"
        }
        # A1=SM matches, but A2[?] on empty list → false → and fails
        assert _match_rule(rule, sd) is None

    def test_e_or_semantics(self, dsu3):
        """or: with all false → no match; with one true → match."""
        rule_false = {
            "or": [
                {"axis": "A1", "match": "SM + mirror"},
                {"axis": "A1", "match": "Non-SM-embedding"},
            ]
        }
        assert _match_rule(rule_false, dsu3) is None

        rule_true = {
            "or": [
                {"axis": "A1", "match": "SM + mirror"},
                {"axis": "A1", "match": "SM + extra SU(N)"},
            ]
        }
        assert _match_rule(rule_true, dsu3) is not None

    def test_f_and_single_sub_rule(self, dsu3):
        """and: with a single sub-rule should work (degenerate case)."""
        rule = {
            "and": [
                {"axis": "A1", "match": "SM + extra SU(N)"},
            ],
            "verdict": "blocked",
            "blocker": "MG5_DARK_COLOR_TENSOR_WALL",
            "evidence": "test"
        }
        assert _match_rule(rule, dsu3) is not None
