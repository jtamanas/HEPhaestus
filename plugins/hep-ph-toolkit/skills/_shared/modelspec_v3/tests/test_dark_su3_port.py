"""Round-trip tests for the dark_su3 v3 spec port."""
import pathlib
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

SPEC_PATH = pathlib.Path(__file__).parent.parent / 'specs' / 'dark_su3.yaml'


def test_dark_su3_validates_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    assert result.errors == [], f'errors: {result.errors}'
    assert result.warnings == [], f'warnings: {result.warnings}'


def test_dark_su3_renders():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    assert 'DarkSU3.m' in files


def test_dark_su3_main_m_blocks():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['DarkSU3.m']
    for required in [
        'Model`Name = "DarkSU3";',
        'Gauge[[4]] = {GD, SU[3], dark, gD, False};',
        'FermionFields[[6]] = {psiDL, 1, psiDL, 0, 1, 1, 3};',
        'FermionFields[[7]] = {psiDR, 1, conj[psiDR], 0, 1, 1, 3};',
        'MpsiD psiDL.psiDR',
        'FpsiDL0 -> {psiDL, 0}',
        'FpsiDR0 -> {0, psiDR}',
        'FpsiD -> {psiDL, conj[psiDR]}',
    ]:
        assert required in main, f'missing: {required!r}'


def test_dark_su3_anomaly_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    anomaly_warns = [d for d in result.warnings if d.code.startswith('ANOMALY_')]
    assert anomaly_warns == [], f'anomaly warnings: {anomaly_warns}'


def test_dark_su3_emits_dark_gauge_boson_in_particles():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    p = files['particles.m']
    assert 'VGD' in p
    assert 'gGD' in p
