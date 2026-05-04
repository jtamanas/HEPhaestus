"""
test_time_budget.py — unit tests for time_budget.resolve().

Done-criteria assertions (§WS1, R2 fixer update):
  - resolve("singlet-doublet", ["relic"]).rows[0].status == "READY"
  - resolve("singlet-doublet", ["dd"]).rows[0].status == "BLOCKED"
    with missing containing feynarts, formcalc, ddcalc
  - resolve("dark-su3", ["relic"]).rows[0].status == "READY"
    via the chain_overrides analytic-only branch (sarah-build →
    spheno-build → dark-matter-constraints).
  - resolve("dark-su3", ["dd"]) remains BLOCKED on planned prereqs
    (feynarts/formcalc/ddcalc).
  - resolve("dark-su3", ["id"]) is READY after WS1 shipped gamlike v0
    (gamlike.status flipped to exists; pull-computation v1+ is a prose
    caveat only, not a YAML planned-prereq blocker).
  - overlap totals don't double-count shared prereqs (relic+dd sharing sarah-build)
"""

import pytest
from time_budget import resolve


# ---------------------------------------------------------------------------
# Singlet-Doublet: relic (all-exists chain)
# ---------------------------------------------------------------------------

class TestSingletDoubletRelic:
    def setup_method(self):
        self.report = resolve("singlet-doublet", ["relic"])

    def test_has_one_row(self):
        assert len(self.report.rows) == 1

    def test_status_ready(self):
        assert self.report.rows[0].status == "READY"

    def test_constraint_id(self):
        assert self.report.rows[0].constraint == "relic"

    def test_no_missing_prereqs(self):
        assert self.report.rows[0].missing == []

    def test_chain_annotated_all_exists(self):
        for name, tag in self.report.rows[0].chain_annotated:
            assert tag == "EXISTS", f"Prereq '{name}' should be EXISTS for singlet-doublet relic"

    def test_cold_range_positive(self):
        cold = self.report.rows[0].cold
        assert cold[0] > 0 and cold[1] >= cold[0]


# ---------------------------------------------------------------------------
# Singlet-Doublet: direct detection (tree-DD via MadDM chain_override)
# ---------------------------------------------------------------------------
# constraints.yaml gives singlet-doublet dd a chain_override to the tree-DD
# path [sarah-build, spheno-build, madgraph, maddm, ddcalc] — the canonical
# θ=0 benchmark sits off the blind-spot locus, so tree contributions dominate.
# All five prereqs are status:exists, so dd is now READY for this model.
# The loop-DD chain (FeynArts → FormCalc → /looptools eval → /ddcalc) is the
# natural extension near the blind-spot locus and stays deferred — but it is
# not gating the default singlet-doublet dd run.

class TestSingletDoubletDD:
    def setup_method(self):
        self.report = resolve("singlet-doublet", ["dd"])

    def test_status_ready_via_tree_dd_override(self):
        assert self.report.rows[0].status == "READY", (
            f"Expected READY (tree-DD chain_override), got "
            f"{self.report.rows[0].status}; missing={self.report.rows[0].missing}"
        )

    def test_chain_uses_tree_dd_override(self):
        names = [n for n, _ in self.report.rows[0].chain_annotated]
        assert names == ["sarah-build", "spheno-build", "madgraph", "maddm", "ddcalc"], (
            f"Expected tree-DD chain_override; got {names}"
        )

    def test_chain_all_exists(self):
        tags = {tag for _, tag in self.report.rows[0].chain_annotated}
        assert tags == {"EXISTS"}, f"Expected all EXISTS, got tags={tags}"


# ---------------------------------------------------------------------------
# Dark SU(3): relic (R2 fixer — analytic-only chain_overrides; READY)
# ---------------------------------------------------------------------------

class TestDarkSU3Relic:
    def setup_method(self):
        self.report = resolve("dark-su3", ["relic"])

    def test_status_ready_via_chain_override(self):
        """R2 fix: dark-su3 relic now READY via analytic-only chain_override."""
        assert self.report.rows[0].status == "READY", (
            f"Expected READY (analytic-only chain_override), got "
            f"{self.report.rows[0].status}; missing={self.report.rows[0].missing}"
        )

    def test_chain_uses_analytic_override(self):
        """The override chain must skip madgraph/maddm and go through
        dark-matter-constraints (the analytic-only branch consumer)."""
        names = [n for n, _ in self.report.rows[0].chain_annotated]
        assert "madgraph" not in names, (
            f"R2 chain_override should skip madgraph; got {names}"
        )
        assert "maddm" not in names, (
            f"R2 chain_override should skip maddm; got {names}"
        )
        assert "dark-matter-constraints" in names, (
            f"R2 chain_override must include dark-matter-constraints; got {names}"
        )

    def test_dark_matter_constraints_is_exists(self):
        """R2 Part A flag flip: dark-matter-constraints must be EXISTS."""
        for name, tag in self.report.rows[0].chain_annotated:
            if name == "dark-matter-constraints":
                assert tag == "EXISTS", (
                    f"R2 Part A: dark-matter-constraints must be EXISTS, got {tag}"
                )


# ---------------------------------------------------------------------------
# Dark SU(3): dd remains BLOCKED on planned tools (feynarts/formcalc/ddcalc).
# id is READY after WS1 shipped gamlike v0 (gamlike.status=exists).
# Only relic is unblocked by the R2 chain_override for a different reason.
# ---------------------------------------------------------------------------

class TestDarkSU3DDIdStillBlocked:
    def setup_method(self):
        self.report = resolve("dark-su3", ["dd", "id"])

    def test_dd_blocked(self):
        dd_row = next(r for r in self.report.rows if r.constraint == "dd")
        assert dd_row.status == "BLOCKED", (
            f"dark-su3 dd must remain BLOCKED, got {dd_row.status}"
        )
        # The default chain runs through madgraph (MG5_DARK_COLOR_TENSOR_WALL)
        # and the loop-DD integration via /looptools eval has not shipped, so
        # the model carries a spec_authoring_blocker for dd.  Mirrors 2hdm-a.
        assert "spec-authoring-incomplete" in dd_row.missing, (
            f"dark-su3 dd missing list should carry the spec_authoring_blocker, "
            f"got {dd_row.missing}"
        )

    def test_id_ready_after_gamlike_v0(self):
        """WS1 shipped gamlike v0 (status: exists). The YAML chain for dark-su3
        id no longer has any planned prereqs, so resolve() returns READY.
        The pull-computation caveat (v1+) is prose-only, not a YAML blocker."""
        id_row = next(r for r in self.report.rows if r.constraint == "id")
        assert id_row.status == "READY", (
            f"dark-su3 id must be READY after gamlike v0 shipped (gamlike.status=exists), "
            f"got {id_row.status}; missing={id_row.missing}"
        )
        assert id_row.missing == [], (
            f"dark-su3 id missing list must be empty after gamlike v0, got {id_row.missing}"
        )


# ---------------------------------------------------------------------------
# Overlap: shared prereqs are NOT double-counted
# ---------------------------------------------------------------------------

class TestOverlapDedup:
    """
    Fixture case: singlet-doublet relic+dd
    Shared prereqs: sarah-build, spheno-build, madgraph
    Unique to relic: maddm
    Unique to dd: feynarts, formcalc, ddcalc
    Total unique prereqs = 3 shared + 1 relic-only + 3 dd-only = 7

    The overlap-adjusted cold total must be LESS THAN the sum of the
    two per-constraint cold totals (because shared prereqs are counted once).
    """
    def setup_method(self):
        self.relic_only = resolve("singlet-doublet", ["relic"])
        self.dd_only = resolve("singlet-doublet", ["dd"])
        self.combined = resolve("singlet-doublet", ["relic", "dd"])

    def test_combined_cold_all_less_than_naive_sum(self):
        naive_lo = (
            self.relic_only.overlap_totals.cold_all[0]
            + self.dd_only.overlap_totals.cold_all[0]
        )
        naive_hi = (
            self.relic_only.overlap_totals.cold_all[1]
            + self.dd_only.overlap_totals.cold_all[1]
        )
        combined_lo = self.combined.overlap_totals.cold_all[0]
        combined_hi = self.combined.overlap_totals.cold_all[1]
        assert combined_lo < naive_lo, (
            f"Overlap dedup failed: combined cold lo {combined_lo} should be < "
            f"naive sum {naive_lo} because sarah-build, spheno-build, madgraph are shared"
        )
        assert combined_hi < naive_hi, (
            f"Overlap dedup failed: combined cold hi {combined_hi} should be < "
            f"naive sum {naive_hi}"
        )

    def test_ready_total_equals_combined_when_all_ready(self):
        """singlet-doublet relic+dd are both READY (dd via tree-DD chain_override).
        The ready total must therefore equal the all-constraints total."""
        ready_lo = self.combined.overlap_totals.cold_ready[0]
        ready_hi = self.combined.overlap_totals.cold_ready[1]
        all_lo = self.combined.overlap_totals.cold_all[0]
        all_hi = self.combined.overlap_totals.cold_all[1]
        assert abs(ready_lo - all_lo) < 1e-6, (
            f"ready cold lo {ready_lo} should equal all cold lo {all_lo} "
            "since both relic and dd are READY"
        )
        assert abs(ready_hi - all_hi) < 1e-6, (
            f"ready cold hi {ready_hi} should equal all cold hi {all_hi}"
        )


# ---------------------------------------------------------------------------
# Collider: always a no-op with BLOCKED status
# ---------------------------------------------------------------------------

class TestCollider:
    def setup_method(self):
        self.report = resolve("singlet-doublet", ["collider"])

    def test_collider_row_blocked(self):
        assert len(self.report.rows) == 1
        assert self.report.rows[0].status == "BLOCKED"
        assert self.report.rows[0].constraint == "collider"


# ---------------------------------------------------------------------------
# Multi-constraint: singlet-doublet relic has correct chain order
# ---------------------------------------------------------------------------

class TestChainOrder:
    def test_relic_chain_order(self):
        report = resolve("singlet-doublet", ["relic"])
        names = [n for n, _ in report.rows[0].chain_annotated]
        assert names == ["sarah-build", "spheno-build", "madgraph", "maddm"]

    def test_dd_chain_starts_with_shared_prereqs(self):
        # singlet-doublet dd uses the tree-DD chain_override; feynarts/formcalc
        # are not in the chain (the loop-DD subchain is deferred).
        report = resolve("singlet-doublet", ["dd"])
        names = [n for n, _ in report.rows[0].chain_annotated]
        assert names[:3] == ["sarah-build", "spheno-build", "madgraph"]
        assert names[-1] == "ddcalc"
        assert "maddm" in names
