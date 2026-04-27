import pathlib
import pytest
from modelspec_v3.loader import load_spec, SpecLoadError

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_load_minimal():
    spec = load_spec(FIX / 'minimal_valid.yaml')
    assert spec['model']['name'] == 'TestModel'


def test_load_nonexistent_raises():
    with pytest.raises(SpecLoadError):
        load_spec(FIX / 'nope.yaml')


def test_load_malformed_yaml_raises(tmp_path):
    bad = tmp_path / 'malformed.yaml'
    bad.write_text('model: {name: foo')
    with pytest.raises(SpecLoadError):
        load_spec(bad)
