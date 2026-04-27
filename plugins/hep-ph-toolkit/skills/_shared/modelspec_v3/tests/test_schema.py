import json
import yaml
import jsonschema
import pathlib
import pytest

SCHEMA_PATH = pathlib.Path(__file__).parent.parent / 'schema.json'
FIX_DIR = pathlib.Path(__file__).parent / 'fixtures'


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_minimal_valid_passes():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'minimal_valid.yaml').read_text())
    jsonschema.validate(spec, schema)  # raises if invalid


def test_missing_required_fails():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'missing_required.yaml').read_text())
    with pytest.raises(jsonschema.ValidationError) as ei:
        jsonschema.validate(spec, schema)
    assert 'model' in str(ei.value)


def test_unknown_top_level_key_fails():
    schema = load_schema()
    spec = yaml.safe_load((FIX_DIR / 'minimal_valid.yaml').read_text())
    spec['frobnicate'] = True   # unknown key
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(spec, schema)
