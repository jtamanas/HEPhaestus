"""conftest.py — shared fixtures/paths for the maddm test suite.

Puts the maddm scripts dir (maddm_run.py, staleness.py) and the shared
install-helpers dir (config_helpers.py) on sys.path so tests can import them
directly, mirroring the _shared/tests and gamlike/tests conventions. No real
MadDM / SPheno is ever invoked — everything is pure-Python or mocked.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()
_MADDM_SCRIPTS = _HERE.parent / "scripts"          # .../maddm/scripts
_SKILLS = _HERE.parents[1]                         # .../hep-ph-toolkit/skills
_PLUGINS = _SKILLS.parent.parent                   # .../plugins
_SHARED_HELPERS = _PLUGINS / "shared" / "install-helpers"
_SHARED = _SKILLS / "_shared"

for _p in (_MADDM_SCRIPTS, _SHARED_HELPERS, _SHARED):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
