"""Tests for render_header."""
import pathlib
from modelspec_v3.render.header import render_header
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_render_model_header_basic_sm_minimal():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_header(spec)
    assert 'Model`Name = "SMTest";' in out
    assert "Off[General::spell]" in out
    assert "NameOfStates = {GaugeES, EWSB};" in out
    assert 'DEFINITION[GaugeES][LagrangianInput]' in out
    assert 'AddHC -> True' in out
    assert 'AddHC -> False' in out


def test_render_model_header_no_globals():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_header(spec)
    assert 'Global[[' not in out   # no globals -> no Global lines


def test_render_model_header_with_global():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [{'name': 'DMParity', 'type': 'Z(2)'}]
    out = render_header(spec)
    assert 'Global[[1]] = {Z[2], DMParity};' in out


def test_render_model_header_two_globals():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [
        {'name': 'DMParity', 'type': 'Z(2)'},
        {'name': 'BminusL', 'type': 'U(1)'},
    ]
    out = render_header(spec)
    assert 'Global[[1]] = {Z[2], DMParity};' in out
    assert 'Global[[2]] = {U[1], BminusL};' in out
