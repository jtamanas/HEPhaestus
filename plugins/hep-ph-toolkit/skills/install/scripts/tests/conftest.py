"""Top-level conftest for install/scripts/tests.

Registers pytest options used by test_check_config_golden.py.
"""
from __future__ import annotations


def pytest_addoption(parser):
    """Register the --regen flag for golden-file regeneration."""
    try:
        parser.addoption(
            "--regen",
            action="store_true",
            default=False,
            help="Regenerate golden files from current check_config.py output.",
        )
    except ValueError:
        # Option already registered (e.g., by a parent conftest).
        pass
