"""Stage 1: JSONSchema validation."""
import json
import pathlib
import jsonschema
from typing import List
from .diagnostics import Diagnostic

_SCHEMA_PATH = pathlib.Path(__file__).parent / 'schema.json'
_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text())
    return _SCHEMA


def _path_to_pointer(path) -> str:
    return '/' + '/'.join(str(p) for p in path) if path else '/'


def validate_schema(spec: dict) -> List[Diagnostic]:
    diags = []
    validator = jsonschema.Draft202012Validator(_schema())
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
        diags.append(Diagnostic(
            stage=1,
            severity='error',
            code='SCHEMA_' + err.validator.upper(),
            path=_path_to_pointer(err.path),
            message=err.message,
        ))
    return diags
