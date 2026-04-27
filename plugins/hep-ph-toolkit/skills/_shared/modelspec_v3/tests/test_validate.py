"""Tests for the validate() orchestrator."""
import pathlib
import pytest
from modelspec_v3.validate import validate, ValidationResult
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_minimal_valid_clean():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    result = validate(spec)
    assert result.errors == []
    assert isinstance(result.warnings, list)
    assert isinstance(result.all, list)


def test_sm_minimal_clean():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    result = validate(spec)
    assert result.errors == []


def test_stage1_errors_halt_pipeline():
    # Missing required keys: only Stage 1 errors should appear; Stage 2/3 must NOT run
    spec = load_spec(FIX / 'missing_required.yaml')
    result = validate(spec)
    assert result.errors  # at least one
    assert all(d.stage == 1 for d in result.errors)
    assert result.warnings == []   # Stage 3 didn't run


def test_stage2_errors_halt_stage3():
    spec = load_spec(FIX / 'reserved_param.yaml')
    result = validate(spec)
    # Stage 2 should produce NAME_RESERVED error; Stage 3 should not run
    assert any(d.stage == 2 for d in result.errors)
    assert result.warnings == []


def test_warnings_appear_when_stages_clean():
    # Inject an artificial anomaly to confirm Stage 3 runs and emits warnings
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'][0]['reps']['B'] = '1/7'   # break Y(q)
    result = validate(spec)
    assert result.errors == []   # all stages structurally OK
    assert any(d.severity == 'warning' for d in result.warnings)
