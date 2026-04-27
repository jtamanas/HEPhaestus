"""conftest.py — shared fixtures for analytic-exception-detector tests."""
from __future__ import annotations

import pathlib

import pytest

# ---------------------------------------------------------------------------
# Module-level path constants
# ---------------------------------------------------------------------------

_HERE: pathlib.Path = pathlib.Path(__file__).parent
# tests/ -> analytic-exception-detector/ -> skills/ -> workflow/ -> plugins/ -> repo root
_REPO_ROOT: pathlib.Path = _HERE.parent.parent.parent.parent.parent
_REGISTRY_PATH: pathlib.Path = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)
_SHARED_ASSETS: pathlib.Path = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "assets"
)
_DARK_SU3_SPEC: pathlib.Path = _SHARED_ASSETS / "dark_su3.yaml"
_TWO_HDMA_SPEC: pathlib.Path = _SHARED_ASSETS / "two_hdm_a.yaml"
_SINGLET_DOUBLET_SPEC: pathlib.Path = _SHARED_ASSETS / "_archive" / "singlet_doublet.yaml"
_CONFINING_SPEC: pathlib.Path = _HERE / "fixtures" / "confining_synthetic.yaml"


@pytest.fixture
def repo_root() -> pathlib.Path:
    return _REPO_ROOT


@pytest.fixture
def registry_path() -> pathlib.Path:
    return _REGISTRY_PATH


@pytest.fixture
def dark_su3_spec_path() -> pathlib.Path:
    return _DARK_SU3_SPEC


@pytest.fixture
def two_hdma_spec_path() -> pathlib.Path:
    return _TWO_HDMA_SPEC


@pytest.fixture
def singlet_doublet_spec_path() -> pathlib.Path:
    return _SINGLET_DOUBLET_SPEC


@pytest.fixture
def confining_spec_path() -> pathlib.Path:
    return _CONFINING_SPEC
