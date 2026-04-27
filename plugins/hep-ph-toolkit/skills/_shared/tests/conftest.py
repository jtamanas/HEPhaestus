"""
conftest.py — shared pytest fixtures for model-building/_shared tests.
"""
import sys
from pathlib import Path

# Make config_helpers importable
# parents[4] = plugins/  →  plugins/shared/install-helpers
_SHARED_HELPERS = Path(__file__).parents[4] / "shared" / "install-helpers"
if str(_SHARED_HELPERS) not in sys.path:
    sys.path.insert(0, str(_SHARED_HELPERS))

# Make _shared/ importable
_SHARED = Path(__file__).parent.parent
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
