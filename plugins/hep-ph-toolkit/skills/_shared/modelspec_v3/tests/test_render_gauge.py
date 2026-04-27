"""Tests for render_gauge."""
import pathlib
from modelspec_v3.render.gauge import render_gauge
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_render_gauge_5tuple_no_globals():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_gauge(spec)
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False};' in out
    assert 'Gauge[[2]] = {WB, SU[2], left, g2, True};' in out
    assert 'Gauge[[3]] = {G, SU[3], color, g3, False};' in out


def test_render_gauge_6tuple_one_global():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [{'name': 'DMParity', 'type': 'Z(2)'}]
    out = render_gauge(spec)
    # Gauge bosons are trivial under globals -> trailing column is 1
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False, 1};' in out


def test_render_gauge_two_globals():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [
        {'name': 'DMParity', 'type': 'Z(2)'},
        {'name': 'BminusL', 'type': 'U(1)'},
    ]
    out = render_gauge(spec)
    # Z(2) trivial = 1, U(1) trivial = 0
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False, 1, 0};' in out
