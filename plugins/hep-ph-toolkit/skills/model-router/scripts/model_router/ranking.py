"""
model_router/ranking.py — Stage P4 ranking helpers (S12).

Three-layer sort per synthesis §6:
  1. Role index (primary=0 < validator=1 < specialty=2 < escape_hatch=3 < none=4)
  2. priority_tiebreak (lower wins)
  3. user_memory rank (lower wins; missing prereq → 999)
  4. prereq_id alphabetical (deterministic final tiebreak)

This module is WS2-independent: operates purely on PrereqFold lists with no
dependency on ConstraintRow.capability_blockers.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from model_router.types import PrereqFold

# ---------------------------------------------------------------------------
# Role ordering
# ---------------------------------------------------------------------------

_ROLE_ORDER: Dict[str, int] = {
    "primary":      0,
    "validator":    1,
    "specialty":    2,
    "escape_hatch": 3,
    "none":         4,
    "BLOCKED":      5,
}


def _role_index(role: str) -> int:
    """Return sort key for role string; unknown roles sort last."""
    return _ROLE_ORDER.get(role, 99)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rank_by_role(
    folds: List[PrereqFold],
    observable: str,  # noqa: ARG001 — reserved for future per-observable tuning
) -> List[PrereqFold]:
    """Sort a list of PrereqFold by (role, priority_tiebreak, prereq_id).

    Returns a new sorted list. Does not mutate the input.

    Args:
        folds:      List of PrereqFold objects for one observable.
        observable: The observable being ranked (reserved for future use).

    Returns:
        List[PrereqFold] sorted ascending by (role_index, priority_tiebreak, prereq_id).
    """
    return sorted(
        folds,
        key=lambda r: (_role_index(r.role_for_observable), r.priority_tiebreak, r.prereq_id),
    )


def _apply_user_memory_tiebreak(
    ranked: List[PrereqFold],
    user_memory: Optional[Dict[str, int]],
) -> List[PrereqFold]:
    """Re-sort ranked PrereqFold list applying user-memory tertiary tiebreak.

    The user_memory dict maps prereq_id → priority integer (lower = higher preference).
    Prerequisites absent from user_memory get default priority 999.

    When user_memory is None, returns the list unchanged (no reorder applied).

    Args:
        ranked:      Pre-sorted PrereqFold list (output of rank_by_role).
        user_memory: dict[prereq_id, int] | None from load_user_memory().

    Returns:
        Re-sorted list incorporating user preference as a tertiary sort key.
    """
    if user_memory is None:
        return ranked

    return sorted(
        ranked,
        key=lambda r: (
            _role_index(r.role_for_observable),
            r.priority_tiebreak,
            user_memory.get(r.prereq_id, 999),
            r.prereq_id,
        ),
    )
