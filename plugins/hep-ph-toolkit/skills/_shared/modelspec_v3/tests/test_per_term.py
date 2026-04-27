"""Tests for Stage 3: per-term U(1) charge and discrete-symmetry conservation."""
import pathlib
import pytest
from modelspec_v3.per_term import check_per_term_charges, check_discrete_symmetry
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_sm_yukawas_balance():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'] = [
        {'term': 'Yd conj[H].d.q'},
        {'term': '-Yu H.u.q'},
        {'term': 'Ye conj[H].e.LL'},
    ]
    spec['parameters'].extend([
        {'name': 'Yd', 'real': False},
        {'name': 'Yu', 'real': False},
        {'name': 'Ye', 'real': False},
    ])
    diags = check_per_term_charges(spec)
    warns = [d for d in diags if d.severity == 'warning']
    assert warns == [], f'unexpected warns: {warns}'


def test_charge_violating_term_warns():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'].append({'term': 'Yextra H.q.q'})  # charge-violating
    spec['parameters'].append({'name': 'Yextra', 'real': False})
    diags = check_per_term_charges(spec)
    assert any(d.code == 'CHARGE_NONZERO' for d in diags)


def test_no_lagrangian_no_warnings():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    diags = check_per_term_charges(spec)
    assert diags == []


def test_discrete_z2_violating_term_warns():
    # Set up Z2 with a non-conserving Yukawa term
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [{'name': 'DMParity', 'type': 'Z(2)'}]
    # All SM fields get DMParity charge 1 (Z2 even)
    for f in spec['fermions']:
        f['reps'] = dict(f['reps'])
        f['reps']['DMParity'] = 1
    for s in spec['scalars']:
        s['reps'] = dict(s['reps'])
        s['reps']['DMParity'] = 1
    # Add a Z2-odd singlet fermion
    spec['fermions'].append({
        'name': 'FS', 'generations': 1, 'components': 's0',
        'reps': {'B': 0, 'WB': 1, 'G': 1, 'DMParity': -1},
    })
    # A Z2-odd Yukawa connecting FS (odd) with q (even) violates Z2
    spec['lagrangian']['hc'].append({'term': 'Ybad FS conj[H].d.q'})
    spec['parameters'].append({'name': 'Ybad', 'real': False})
    diags = check_discrete_symmetry(spec)
    assert any(d.code == 'DISCRETE_NONZERO' for d in diags)


def test_discrete_z2_conserving_term_silent():
    # Yukawa-like term with two Z2-odd fields cancels (mod 2)
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['global_symmetries'] = [{'name': 'DMParity', 'type': 'Z(2)'}]
    for f in spec['fermions']:
        f['reps'] = dict(f['reps'])
        f['reps']['DMParity'] = 1
    for s in spec['scalars']:
        s['reps'] = dict(s['reps'])
        s['reps']['DMParity'] = 1
    spec['fermions'].append({
        'name': 'FS', 'generations': 1, 'components': 's0',
        'reps': {'B': 0, 'WB': 1, 'G': 1, 'DMParity': -1},
    })
    spec['fermions'].append({
        'name': 'FS2', 'generations': 1, 'components': 's2',
        'reps': {'B': 0, 'WB': 1, 'G': 1, 'DMParity': -1},
    })
    spec['lagrangian']['hc'].append({'term': 'Mfs FS.FS2'})
    spec['parameters'].append({'name': 'Mfs', 'real': True})
    diags = check_discrete_symmetry(spec)
    assert not any(d.code == 'DISCRETE_NONZERO' and 'Mfs' in d.message for d in diags)
