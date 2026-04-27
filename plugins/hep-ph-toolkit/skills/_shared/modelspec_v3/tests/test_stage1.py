import pathlib
from modelspec_v3.stage1 import validate_schema
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_minimal_valid_clean():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    diags = validate_schema(spec)
    assert diags == []

def test_missing_model_blocks():
    spec = load_spec(FIX / 'missing_required.yaml')
    diags = validate_schema(spec)
    assert len(diags) >= 1
    assert all(d.severity == 'error' for d in diags)
    assert all(d.stage == 1 for d in diags)
    assert any('model' in d.path or 'model' in d.message for d in diags)

def test_unknown_key_blocks():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    spec['extra'] = 'oops'
    diags = validate_schema(spec)
    assert any('extra' in d.message for d in diags)
