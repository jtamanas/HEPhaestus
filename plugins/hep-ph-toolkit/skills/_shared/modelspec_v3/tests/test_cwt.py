import pathlib
from modelspec_v3.cwt import build_cwt, WeylRef, FieldRef
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_sm_cwt_has_quark_components():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    # bare and indexed forms
    for sym in ['uL', 'dL', 'eL', 'vL', 'dR', 'uR', 'eR']:
        assert sym in cwt, f'{sym} missing from CWT'
        for g in [1, 2, 3]:
            assert f'{sym}[{g}]' in cwt, f'{sym}[{g}] missing from CWT'


def test_sm_cwt_marks_conjugates():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    # 'd' is declared with components 'conj[dR]' — CWT entry for dR is conjugated
    assert cwt['dR'].conjugated is True
    assert cwt['uL'].conjugated is False


def test_cwt_has_field_aliases():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    assert isinstance(cwt['q'], FieldRef)
    assert isinstance(cwt['LL'], FieldRef)
    assert cwt['q'].field_name == 'q'


def test_cwt_seeds_gauge_bosons():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    for tok in ['VB', 'VWB[1]', 'VWB[2]', 'VWB[3]', 'VWp', 'VG', 'VP', 'VZ']:
        assert tok in cwt, f'{tok} missing from CWT'


def test_cwt_includes_higgs_components():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    cwt = build_cwt(spec)
    assert 'Hp' in cwt and 'H0' in cwt
    assert 'H' in cwt and isinstance(cwt['H'], FieldRef)
