import pathlib
import pytest
from modelspec_v3.stage2 import validate_refs
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'

def test_sm_minimal_clean():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    diags = validate_refs(spec)
    errors = [d for d in diags if d.severity == 'error']
    assert errors == [], f'unexpected errors: {errors}'

def test_undeclared_weyl_in_mixing_blocks():
    spec = load_spec(FIX / 'typo_in_mixing.yaml')
    diags = validate_refs(spec)
    errs = [d for d in diags if d.severity == 'error']
    assert any(d.code == 'REF_UNDECLARED' for d in errs)
    assert any('dr' in d.message for d in errs)
    # Levenshtein hint should mention dL
    hint_diags = [d for d in errs if d.code == 'REF_UNDECLARED' and 'dr' in d.message]
    assert any(d.hint and 'dL' in d.hint for d in hint_diags)

def test_reserved_parameter_name():
    spec = load_spec(FIX / 'reserved_param.yaml')
    diags = validate_refs(spec)
    errs = [d for d in diags if d.code == 'NAME_RESERVED']
    assert len(errs) >= 1
    assert any("'e'" in d.message for d in errs)

def test_collision_two_fermions_same_name():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'].append(dict(spec['fermions'][0]))  # duplicate first entry
    diags = validate_refs(spec)
    errs = [d for d in diags if d.code == 'NAME_COLLISION']
    assert len(errs) >= 1
