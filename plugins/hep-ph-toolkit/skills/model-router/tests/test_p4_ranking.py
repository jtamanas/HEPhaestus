"""
test_p4_ranking.py — S12 TDD scaffold: ranking.py + user_memory.py pure-function tests.

These tests are WS2-independent: ranking is a pure function over PrereqFold lists
with no dependency on ConstraintRow.capability_blockers.
"""
import pytest

ranking_mod = pytest.importorskip(
    "model_router.ranking",
    reason="ranking module not yet implemented (awaiting S12)",
)
rank_by_role = ranking_mod.rank_by_role
_apply_user_memory_tiebreak = ranking_mod._apply_user_memory_tiebreak

user_memory_mod = pytest.importorskip(
    "model_router.user_memory",
    reason="user_memory module not yet implemented (awaiting S12)",
)
load_user_memory = user_memory_mod.load_user_memory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fold(prereq_id, role, priority_tiebreak, overall_verdict="supported"):
    """Build a minimal PrereqFold for ranking tests."""
    from model_router.types import PrereqFold
    return PrereqFold(
        prereq_id=prereq_id,
        overall_verdict=overall_verdict,
        role_for_observable=role,
        priority_tiebreak=priority_tiebreak,
    )


# ---------------------------------------------------------------------------
# rank_by_role tests
# ---------------------------------------------------------------------------

class TestRankByRole:
    """rank_by_role: three-layer sort (role > priority_tiebreak > prereq_id)."""

    def test_rank_primary_before_validator(self):
        """primary role sorts before validator regardless of priority_tiebreak."""
        folds = [
            _make_fold("micromegas", "validator", 1),
            _make_fold("maddm", "primary", 10),
        ]
        ranked = rank_by_role(folds, "relic")
        assert ranked[0].prereq_id == "maddm"
        assert ranked[1].prereq_id == "micromegas"

    def test_rank_validator_before_specialty(self):
        """validator sorts before specialty."""
        folds = [
            _make_fold("drake", "specialty", 1),
            _make_fold("micromegas", "validator", 5),
        ]
        ranked = rank_by_role(folds, "relic")
        assert ranked[0].prereq_id == "micromegas"
        assert ranked[1].prereq_id == "drake"

    def test_rank_tiebreak_within_same_role(self):
        """Within same role, lower priority_tiebreak wins."""
        folds = [
            _make_fold("micromegas", "validator", 2),
            _make_fold("maddm", "validator", 1),
        ]
        ranked = rank_by_role(folds, "relic")
        assert ranked[0].prereq_id == "maddm"
        assert ranked[1].prereq_id == "micromegas"

    def test_rank_prereq_id_tiebreak_alphabetical(self):
        """When role + priority_tiebreak are equal, sort by prereq_id alphabetically."""
        folds = [
            _make_fold("zz-tool", "primary", 1),
            _make_fold("aa-tool", "primary", 1),
        ]
        ranked = rank_by_role(folds, "relic")
        assert ranked[0].prereq_id == "aa-tool"
        assert ranked[1].prereq_id == "zz-tool"

    def test_rank_empty_list_returns_empty(self):
        """Empty input returns empty list."""
        assert rank_by_role([], "relic") == []

    def test_rank_escape_hatch_after_specialty(self):
        """escape_hatch sorts after specialty."""
        folds = [
            _make_fold("fallback", "escape_hatch", 1),
            _make_fold("specialist", "specialty", 100),
        ]
        ranked = rank_by_role(folds, "relic")
        assert ranked[0].prereq_id == "specialist"
        assert ranked[1].prereq_id == "fallback"


# ---------------------------------------------------------------------------
# _apply_user_memory_tiebreak tests
# ---------------------------------------------------------------------------

class TestApplyUserMemoryTiebreak:
    """_apply_user_memory_tiebreak: tertiary sort by user preference after role+priority."""

    def test_user_memory_reorders_same_role(self):
        """User preference reorders items with equal role + priority_tiebreak."""
        from model_router.types import PrereqFold
        folds = [
            _make_fold("micromegas", "validator", 1),
            _make_fold("maddm", "validator", 1),
        ]
        # User prefers maddm (lower number = higher preference)
        user_memory = {"maddm": 1, "micromegas": 2}
        ranked = _apply_user_memory_tiebreak(folds, user_memory)
        assert ranked[0].prereq_id == "maddm"

    def test_user_memory_none_returns_unchanged(self):
        """None user_memory returns the list unchanged (no reorder)."""
        folds = [
            _make_fold("maddm", "primary", 1),
            _make_fold("micromegas", "validator", 1),
        ]
        ranked = _apply_user_memory_tiebreak(folds, None)
        # Order should remain unchanged since user_memory is None
        assert ranked[0].prereq_id == "maddm"

    def test_user_memory_missing_key_uses_default(self):
        """A prereq absent from user_memory gets default priority 999."""
        folds = [
            _make_fold("unknown-tool", "primary", 1),
            _make_fold("maddm", "primary", 1),
        ]
        user_memory = {"maddm": 1}  # unknown-tool gets 999 → goes last
        ranked = _apply_user_memory_tiebreak(folds, user_memory)
        assert ranked[0].prereq_id == "maddm"
        assert ranked[1].prereq_id == "unknown-tool"


# ---------------------------------------------------------------------------
# load_user_memory tests
# ---------------------------------------------------------------------------

class TestLoadUserMemory:
    """load_user_memory: stub returning options.user_preferences."""

    def test_load_user_memory_returns_user_preferences(self):
        """Stub returns RouterOptions.user_preferences directly."""
        from model_router.types import RouterOptions
        prefs = {"maddm": 1, "micromegas": 2}
        opts = RouterOptions(user_preferences=prefs)
        result = load_user_memory(opts)
        assert result == prefs

    def test_load_user_memory_none_when_no_prefs(self):
        """Returns None when user_preferences is not set."""
        from model_router.types import RouterOptions
        opts = RouterOptions()
        result = load_user_memory(opts)
        assert result is None
