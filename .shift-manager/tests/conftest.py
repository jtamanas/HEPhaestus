"""pytest conftest for WS2 matrix tests.

Registers fixture paths and provides shared fixtures.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest

# Repo root
REPO_ROOT = Path(__file__).parent.parent.parent

# Shared lib path
SHARED_LIB = REPO_ROOT / "plugins" / "hep-ph-demo" / "skills" / "_shared"

# Fixture paths
MATRIX_FIXTURES = Path(__file__).parent / "fixtures" / "matrix"

# Add shared lib to path so tests can import matrix_lookup etc.
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def shared_lib():
    return SHARED_LIB


@pytest.fixture
def matrix_fixtures():
    return MATRIX_FIXTURES


@pytest.fixture
def constraints_yaml_path():
    return SHARED_LIB / "constraints.yaml"


@pytest.fixture
def blocker_catalog_path():
    return SHARED_LIB / "blocker_catalog.yaml"


@pytest.fixture
def ws1_snapshot_path():
    return SHARED_LIB / "ws1_axis_enums_snapshot.yaml"


@pytest.fixture
def analytic_exceptions_path():
    return SHARED_LIB / "analytic_exceptions.yaml"


@pytest.fixture
def dark_su3_axes(matrix_fixtures):
    import yaml
    return yaml.safe_load((matrix_fixtures / "dark_su3_axes.yaml").read_text())


@pytest.fixture
def singlet_doublet_axes(matrix_fixtures):
    import yaml
    return yaml.safe_load((matrix_fixtures / "singlet_doublet_axes.yaml").read_text())


@pytest.fixture
def two_hdm_a_axes(matrix_fixtures):
    import yaml
    return yaml.safe_load((matrix_fixtures / "2hdm_a_axes.yaml").read_text())
