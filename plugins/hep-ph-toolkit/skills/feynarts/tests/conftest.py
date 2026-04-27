"""Shared pytest fixtures for feynarts tests.

Sets up sys.path so scripts can be imported without installation.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Root of feynarts skill
SKILL_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = SKILL_ROOT / "scripts"

# Add scripts to path so test imports work
for _p in [str(_SCRIPTS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Clear any stale sys.modules entries for modules that live in THIS skill's
# scripts/ directory.  When the full test suite runs, sibling skills
# (formcalc) each add their own scripts/ to sys.path and import
# identically-named modules (cache_key, etc.).  We clear stale entries so
# feynarts tests always load from feynarts/scripts/.
_FEYNARTS_SCRIPTS_MODULES = [
    "cache_key",
    "resolve_model",
    "resolve_process",
    "generate",
    "postprocess",
    "render_driver",
    "run_feynarts",
]
for _mod in _FEYNARTS_SCRIPTS_MODULES:
    if _mod in sys.modules:
        _src = getattr(sys.modules[_mod], "__file__", "") or ""
        if str(_SCRIPTS_DIR) not in _src:
            del sys.modules[_mod]


@pytest.fixture
def skill_root():
    return SKILL_ROOT


@pytest.fixture
def tables_dir():
    return SKILL_ROOT / "tables"


@pytest.fixture
def sm_table(tables_dir):
    with open(tables_dir / "SM.json") as f:
        return json.load(f)


@pytest.fixture
def tmp_model_dir(tmp_path):
    """Create a fake model directory with .mod and .gen files."""
    mod = tmp_path / "TestModel.mod"
    gen = tmp_path / "TestModel.gen"
    mod.write_text("(* fake mod file *)\n")
    gen.write_text("(* fake gen file *)\n")
    return tmp_path


@pytest.fixture
def tmp_state_root(tmp_path):
    """Create a minimal state root with a SARAH model."""
    state_root = tmp_path / "state"
    state_root.mkdir()
    model_dir = state_root / "models" / "DarkSU3"
    (model_dir / "feynarts_state").mkdir(parents=True)
    (model_dir / "sarah").mkdir(parents=True)
    return state_root


@pytest.fixture
def fake_feynarts_dir(tmp_path):
    """Create a fake FeynArts install with Models/Lorentz.gen."""
    fa_dir = tmp_path / "FeynArts-3.11"
    fa_dir.mkdir()
    (fa_dir / "FeynArts.m").write_text("(* fake FeynArts.m *)\n")
    models = fa_dir / "Models"
    models.mkdir()
    (models / "Lorentz.gen").write_text("(* fake Lorentz.gen *)\n")
    (models / "SM.mod").write_text("(* fake SM.mod *)\n")
    (models / "SM.gen").write_text("(* fake SM.gen *)\n")
    return fa_dir
