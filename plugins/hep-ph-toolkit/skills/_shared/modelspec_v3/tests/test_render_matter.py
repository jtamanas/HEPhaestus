"""Tests for render_fermions and render_scalars."""
import pathlib
from modelspec_v3.render.matter import render_fermions, render_scalars
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_sm_fermions_match_golden_lines():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_fermions(spec)
    expected_lines = [
        'FermionFields[[1]] = {q, 3, {uL, dL}, 1/6, 2, 3};',
        'FermionFields[[2]] = {LL, 3, {vL, eL}, -1/2, 2, 1};',
        'FermionFields[[3]] = {d, 3, conj[dR], 1/3, 1, -3};',
        'FermionFields[[4]] = {u, 3, conj[uR], -2/3, 1, -3};',
        'FermionFields[[5]] = {e, 3, conj[eR], 1, 1, 1};',
    ]
    for line in expected_lines:
        assert line in out, f'missing line: {line!r}\n--- output ---\n{out}'


def test_sm_higgs_scalar_line():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_scalars(spec)
    assert 'ScalarFields[[1]] = {H, 1, {Hp, H0}, 1/2, 2, 1};' in out


def test_with_global_appends_charge_column():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [{'name': 'DMParity', 'type': 'Z(2)'}]
    # Add DMParity charge to all fermions/scalars (1 = trivial)
    for f in spec['fermions']:
        f['reps'] = dict(f['reps'])
        f['reps']['DMParity'] = 1
    for s in spec['scalars']:
        s['reps'] = dict(s['reps'])
        s['reps']['DMParity'] = 1
    out_f = render_fermions(spec)
    assert 'FermionFields[[1]] = {q, 3, {uL, dL}, 1/6, 2, 3, 1};' in out_f
    assert 'FermionFields[[3]] = {d, 3, conj[dR], 1/3, 1, -3, 1};' in out_f


def test_singleton_components_str_form_emits_bare():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'].append({
        'name': 'FS', 'generations': 1, 'components': 's0',
        'reps': {'B': 0, 'WB': 1, 'G': 1},
    })
    out = render_fermions(spec)
    assert 'FermionFields[[6]] = {FS, 1, s0, 0, 1, 1};' in out


def test_singleton_components_list_form_emits_braces():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['scalars'].append({
        'name': 'a0', 'generations': 1, 'components': ['a0'], 'real': True,
        'reps': {'B': 0, 'WB': 1, 'G': 1},
    })
    out = render_scalars(spec)
    assert 'ScalarFields[[2]] = {a0, 1, {a0}, 0, 1, 1};' in out


def test_realscalars_block_emitted_when_present():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['scalars'].append({
        'name': 'a0', 'generations': 1, 'components': ['a0'], 'real': True,
        'reps': {'B': 0, 'WB': 1, 'G': 1},
    })
    out = render_scalars(spec)
    assert 'RealScalars = {a0};' in out


def test_realscalars_block_omitted_when_none():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_scalars(spec)
    assert 'RealScalars' not in out
