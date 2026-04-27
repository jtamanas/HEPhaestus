"""
model_router/user_memory.py — User memory / preferences stub (S12, D11/OQ-2).

Per manager Decision 11 / OQ-2: the actual MEMORY.md parser is deferred to a future
harness workstream. This stub returns options.user_preferences directly so that
callers (ranking.py, compose_rank.py) can inject test preferences via RouterOptions
without any filesystem coupling.
"""
from __future__ import annotations

from typing import Dict, Optional

from model_router.types import RouterOptions


def load_user_memory(options: RouterOptions) -> Optional[Dict[str, int]]:
    """Return user preferences for tool-chain ranking.

    Stub implementation (D11/OQ-2): returns options.user_preferences as-is.
    The actual MEMORY.md parser (reading ~/.claude/projects/…/memory/MEMORY.md)
    is deferred to a future harness workstream.

    Args:
        options: RouterOptions from the caller; carries user_preferences dict.

    Returns:
        dict[prereq_id, int] | None. Lower integer = higher preference rank.
        None means no user preferences are available (use default ordering).
    """
    return options.user_preferences  # parser deferred to harness workstream
