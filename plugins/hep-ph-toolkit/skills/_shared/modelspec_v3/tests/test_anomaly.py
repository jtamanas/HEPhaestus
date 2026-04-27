"""Tests for Stage 3a anomaly cancellation."""
import pathlib

import pytest

from modelspec_v3.anomaly import check_anomalies
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_sm_cubic_y_anomaly_cancels():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    diags = check_anomalies(spec)
    errs_or_warns = [d for d in diags if d.code.startswith('ANOMALY_')]
    assert errs_or_warns == [], f'unexpected anomaly diags: {errs_or_warns}'


def test_artificial_anomaly_warns():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'][0]['reps']['B'] = '1/7'  # break Y(q)
    diags = check_anomalies(spec)
    warns = [d for d in diags if d.severity == 'warning']
    assert any('ANOMALY' in d.code for d in warns)


def test_dirac_partner_excluded_from_anomaly():
    # Add two vectorlike fermions to sm_minimal that ALONE would unbalance
    # anomalies but cancel when paired by dirac_partner.
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['fermions'].extend([
        {'name': 'PsiDd', 'generations': 1, 'components': ['PsiDd0', 'PsiDdm'],
         'reps': {'B': '-1/2', 'WB': 2, 'G': 1}, 'dirac_partner': 'PsiDu'},
        {'name': 'PsiDu', 'generations': 1, 'components': ['PsiDup', 'PsiDu0'],
         'reps': {'B':  '1/2', 'WB': 2, 'G': 1}, 'dirac_partner': 'PsiDd'},
    ])
    diags = check_anomalies(spec)
    # Net contribution of vectorlike pair is zero; SM still cancels;
    # no warnings expected.
    assert [d for d in diags if d.severity == 'warning'] == []


def test_sarah_raw_with_two_u1s_emits_kinmix_warning():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['gauge_groups'].append({
        'symbol': 'BL', 'type': 'U(1)', 'label': 'BminusL',
        'coupling': 'gBL', 'ssb': False,
    })
    spec['parameters'].append({'name': 'gBL', 'real': True})
    spec['sarah_raw'] = '(* arbitrary SARAH directive *)\n'
    diags = check_anomalies(spec)
    assert any(d.code == 'ANOMALY_KINMIX_SKIP' for d in diags)
