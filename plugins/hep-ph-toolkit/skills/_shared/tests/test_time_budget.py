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
# Singlet-Doublet: direct detection (planned loop subchain)
# ---------------------------------------------------------------------------

class TestSingletDoubletDD:
    def setup_method(self):
        self.report = resolve("singlet-doublet", ["dd"])

    def test_status_blocked(self):
        assert self.report.rows[0].status == "BLOCKED"

    def test_missing_contains_required_prereqs(self):
        # WS2 S7-mega (commit 67ebdac) flipped ddcalc.status planned→exists per intel
        # digest §constraints.yaml schema "drift" note.  ddcalc is now EXISTS, so it
        # no longer appears in missing.  Only feynarts + formcalc remain planned.
        missing = self.report.rows[0].missing
        for expected in ["feynarts", "formcalc"]:
            assert expected in missing, (
                f"Expected '{expected}' in missing for singlet-doublet dd, got {missing}"
            )
        assert "ddcalc" not in missing, (
            f"ddcalc was flipped to status:exists in S7-mega; should not be in missing, got {missing}"
        )

    def test_chain_contains_both_exists_and_planned(self):
        tags = {tag for _, tag in self.report.rows[0].chain_annotated}
        assert "EXISTS" in tags
        assert "PLANNED" in tags


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
            f"dark-su3 dd must remain BLOCKED on planned tools, got {dd_row.status}"
        )
        # At least one of the planned DD-loop tools must surface
        assert any(t in dd_row.missing for t in ("feynarts", "formcalc", "ddcalc")), (
            f"dark-su3 dd missing list should include planned loop tools, got {dd_row.missing}"
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

    def test_ready_total_only_counts_relic_prereqs(self):
        """Only relic is READY for singlet-doublet; ready total should match relic-only total."""
        ready_lo = self.combined.overlap_totals.cold_ready[0]
        ready_hi = self.combined.overlap_totals.cold_ready[1]
        relic_lo = self.relic_only.overlap_totals.cold_all[0]
        relic_hi = self.relic_only.overlap_totals.cold_all[1]
        # They must be equal since relic is the only ready constraint
        assert abs(ready_lo - relic_lo) < 1e-6, (
            f"ready cold lo {ready_lo} should equal relic-only cold lo {relic_lo}"
        )
        assert abs(ready_hi - relic_hi) < 1e-6, (
            f"ready cold hi {ready_hi} should equal relic-only cold hi {relic_hi}"
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
        report = resolve("singlet-doublet", ["dd"])
        names = [n for n, _ in report.rows[0].chain_annotated]
        assert names[:3] == ["sarah-build", "spheno-build", "madgraph"]
        assert "feynarts" in names
        assert "ddcalc" in names
