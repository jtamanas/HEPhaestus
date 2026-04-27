"""
conftest.py — WS3 model-router test fixtures.

Path-shim: inserts the scripts/ directory into sys.path so tests can
    from model_router import ...
without a package install.

Manager D3: sys.path.insert(0, str(SCRIPTS_DIR))
Manager D6: monkeypatch time_budget._YAML_PATH + time_budget._load (NOT _DATA).
"""
import sys
import pathlib
import pytest
import yaml

# ---------------------------------------------------------------------------
# Path shim — executed at collection time so all test files can import model_router
# ---------------------------------------------------------------------------
_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_SKILL_DIR = _TESTS_DIR.parent
SCRIPTS_DIR = _SKILL_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Add the toolkit's _shared/ to sys.path so time_budget is importable
# (needed for mock_constraints_yaml fixture patching).
# _SKILL_DIR.parents[2] resolves to plugins/hep-ph-toolkit/skills/
_TOOLKIT_SKILLS = _SKILL_DIR.parents[2]
_SHARED = _TOOLKIT_SKILLS / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))

FIXTURES_DIR = _TESTS_DIR / "fixtures"
REGISTRY_DIR = FIXTURES_DIR / "registries"
SPECS_DIR = FIXTURES_DIR / "specs"


# ---------------------------------------------------------------------------
# Registry file helpers
# ---------------------------------------------------------------------------

def _load_registry(name: str) -> dict:
    path = REGISTRY_DIR / name
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Fixtures: mock constraint registry (manager D6)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_constraints_yaml(tmp_path, monkeypatch):
    """
    Write the fixture constraints.yaml to tmp_path and monkeypatch time_budget
    to load from there.  Does NOT touch _DATA (doesn't exist — manager D6).
    """
    import time_budget  # noqa: imported inside fixture after sys.path shim

    src = REGISTRY_DIR / "constraints.yaml"
    dst = tmp_path / "constraints.yaml"
    dst.write_bytes(src.read_bytes())

    monkeypatch.setattr(time_budget, "_YAML_PATH", dst)
    monkeypatch.setattr(time_budget, "_load", lambda: yaml.safe_load(dst.open()))
    return dst


@pytest.fixture
def mock_blocker_catalog():
    return _load_registry("blocker_catalog.yaml")


@pytest.fixture
def mock_analytic_exceptions():
    return _load_registry("analytic_exceptions.yaml")


# ---------------------------------------------------------------------------
# Fixtures: model spec YAMLs
# ---------------------------------------------------------------------------

@pytest.fixture
def spec_singlet_doublet() -> dict:
    with open(SPECS_DIR / "singlet_doublet.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def spec_dark_su3() -> dict:
    with open(SPECS_DIR / "dark_su3.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def spec_two_hdm_a() -> dict:
    with open(SPECS_DIR / "two_hdm_a.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def spec_leptoquark_synthetic() -> dict:
    with open(SPECS_DIR / "leptoquark_synthetic.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def spec_dark_su3_confining_synthetic() -> dict:
    with open(SPECS_DIR / "dark_su3_confining_synthetic.yaml") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Fixtures: user memory mock (D11/OQ-2 — real parser is stub)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user_memory(monkeypatch):
    """Returns a mock user_preferences dict matching project_dm_tool_roles."""
    return {"maddm": 1, "micromegas": 2, "drake": 3}


# ---------------------------------------------------------------------------
# Fixtures: absent WS4 detector (for fallback path tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def absent_ws4_registry(monkeypatch):
    """Simulate WS4 analytic_exceptions.yaml absent by returning empty registry."""
    return {"schema_version": 1, "exceptions": {}}


# ---------------------------------------------------------------------------
# Fixtures: absent hep-ph-demo (for D2 cross-plugin dep test)
# ---------------------------------------------------------------------------

@pytest.fixture
def absent_hep_ph_demo(monkeypatch):
    """
    Simulate missing hep-ph-demo._shared.matrix_lookup by patching sys.modules
    so that importing matrix_lookup raises ImportError.
    """
    import builtins
    original_import = builtins.__import__

    def _failing_import(name, *args, **kwargs):
        if "matrix_lookup" in name:
            raise ImportError(f"Simulated absent hep-ph-demo: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _failing_import)
    return None
