import json
from modelspec_v3.diagnostics import Diagnostic
from modelspec_v3.emit import emit_json, emit_pretty


def test_emit_json_round_trip():
    diag = Diagnostic(stage=1, severity='error', code='X', path='/y',
                      message='m', hint='h')
    line = emit_json([diag])
    parsed = [json.loads(l) for l in line.splitlines() if l.strip()]
    assert parsed[0] == diag.to_dict()


def test_emit_pretty_includes_severity_marker():
    diag = Diagnostic(stage=2, severity='warning', code='C', path='/p', message='m')
    text = emit_pretty([diag])
    assert 'warning' in text and 'C' in text and '/p' in text


def test_emit_pretty_summary_count():
    diags = [
        Diagnostic(stage=1, severity='error', code='A', path='/x', message='m1'),
        Diagnostic(stage=3, severity='warning', code='B', path='/y', message='m2'),
    ]
    text = emit_pretty(diags)
    assert '1 error' in text or '1 errors' in text  # Either form acceptable
    assert '1 warning' in text or '1 warnings' in text


def test_emit_json_empty():
    assert emit_json([]).strip() == ''


def test_emit_pretty_empty():
    text = emit_pretty([])
    # Could say "no issues" or just be empty / contain "0 errors"
    assert 'error' in text or text.strip() == '' or '0 ' in text
