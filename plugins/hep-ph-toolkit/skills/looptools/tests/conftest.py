"""
conftest.py — shared pytest setup for /looptools tests.

Mirrors the formcalc conftest sys.path/sys.modules hygiene: sibling skills
(formcalc, feynarts) each add their own scripts/ to sys.path and import
identically-named modules (cache_key, prepare_point, ...).  Once a name is
cached in sys.modules the wrong version is returned for subsequent imports.  We
clear the affected names so this skill's tests always load the looptools copy.
"""
from pathlib import Path
import sys

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES_DIR = TESTS_DIR / "fixtures"
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

_SCRIPTS_MODULES = [
    "cache_key",
    "prepare_point",
    "match_nucleon",
    "parse_eval_output",
    "emit_scattering",
    "run_looptools",
]
for _mod in _SCRIPTS_MODULES:
    if _mod in sys.modules:
        _src = getattr(sys.modules[_mod], "__file__", "") or ""
        if str(SCRIPTS_DIR) not in _src:
            del sys.modules[_mod]
