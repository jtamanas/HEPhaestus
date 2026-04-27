"""
conftest.py — shared pytest fixtures for /formcalc tests.
"""
from pathlib import Path
import sys

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent

# Add the skill's scripts dir to sys.path for imports.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

# Clear any stale sys.modules entries for modules that live in THIS skill's
# scripts/ directory.  When the full test suite runs, sibling skills
# (feynarts) each add their own scripts/ to sys.path and import
# identically-named modules (cache_key, etc.).  Once a name is cached in
# sys.modules the wrong version is returned for subsequent imports.  We clear
# the affected names here so that the first import inside this skill's tests
# always loads the formcalc-specific version.
_SCRIPTS_MODULES = [
    "cache_key",
    "prepare_kinematics",
    "parse_summary",
    "write_sidecar",
    "run_formcalc",
]
for _mod in _SCRIPTS_MODULES:
    if _mod in sys.modules:
        _src = getattr(sys.modules[_mod], "__file__", "") or ""
        if str(SCRIPTS_DIR) not in _src:
            del sys.modules[_mod]
