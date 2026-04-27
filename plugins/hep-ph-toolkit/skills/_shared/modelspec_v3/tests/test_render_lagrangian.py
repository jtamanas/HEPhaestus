import pathlib
from modelspec_v3.render.lagrangian import render_lagrangian
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_laghc_wraps_in_minus_parens():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'] = [
        {'term': 'Yd conj[H].d.q'},
        {'term': 'Ye conj[H].e.LL'},
        {'term': '-Yu H.u.q'},
    ]
    out = render_lagrangian(spec)
    assert 'LagHC = -(Yd conj[H].d.q + Ye conj[H].e.LL + -Yu H.u.q);' in out


def test_lagnohc_no_wrap():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['no_hc'] = [
        {'term': '-mu2 conj[H].H'},
        {'term': '-1/2 \\[Lambda] conj[H].H.conj[H].H'},
    ]
    out = render_lagrangian(spec)
    assert 'LagNoHC = -mu2 conj[H].H -1/2 \\[Lambda] conj[H].H.conj[H].H;' in out


def test_empty_hc_bucket():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian'] = {'hc': [], 'no_hc': [{'term': '-mu2 conj[H].H'}]}
    out = render_lagrangian(spec)
    assert 'LagHC = 0;' in out


def test_empty_no_hc_bucket():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian'] = {'hc': [{'term': 'Yd conj[H].d.q'}], 'no_hc': []}
    out = render_lagrangian(spec)
    assert 'LagNoHC = 0;' in out


def test_both_buckets_empty():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    out = render_lagrangian(spec)
    assert 'LagHC = 0;' in out
    assert 'LagNoHC = 0;' in out


def test_single_hc_term():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'] = [{'term': 'Yd conj[H].d.q'}]
    out = render_lagrangian(spec)
    assert 'LagHC = -(Yd conj[H].d.q);' in out


def test_term_string_directly():
    """Robustness: if a term is a bare string, not a {term: ...} dict, accept it."""
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['lagrangian']['hc'] = [{'term': 'A.B'}]
    out = render_lagrangian(spec)
    assert 'LagHC = -(A.B);' in out
