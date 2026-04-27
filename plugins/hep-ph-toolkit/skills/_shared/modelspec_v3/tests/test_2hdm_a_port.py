"""Round-trip tests for the 2hdm_a v3 spec port."""
import pathlib
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

SPEC_PATH = pathlib.Path(__file__).parent.parent / 'specs' / '2hdm_a.yaml'


def test_2hdm_a_validates_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    assert result.errors == [], f'errors: {result.errors}'
    assert result.warnings == [], f'warnings: {result.warnings}'


def test_2hdm_a_renders():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    assert '2hdmA.m' in files


def test_2hdm_a_main_m_blocks():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['2hdmA.m']
    for required in [
        'Model`Name = "2hdmA";',
        'ScalarFields[[1]] = {H1, 1, {H1p, H10}, 1/2, 2, 1};',
        'ScalarFields[[2]] = {H2, 1, {H2p, H20}, 1/2, 2, 1};',
        'ScalarFields[[3]] = {a0, 1, {a0}, 0, 1, 1};',
        'RealScalars = {a0};',
        # CP-odd mixing involving a0
        '{{Ah1, Ah2, a0}, {Ah, ZA}}',
        # Charged Higgs mixing with conj[X]
        '{{conj[H1p], conj[H2p]}, {Hm, ZP}}',
        # Two VEVs
        '{H10, {vd, 1/Sqrt[2]}, {Ah1, \\[ImaginaryI]/Sqrt[2]}, {hh1, 1/Sqrt[2]}}',
        '{H20, {vu, 1/Sqrt[2]}, {Ah2, \\[ImaginaryI]/Sqrt[2]}, {hh2, 1/Sqrt[2]}}',
        # Dark sector lagrangian terms
        'mchi ChiR.ChiL',
        '\\[ImaginaryI] ychi a0.ChiR.ChiL',
        '{chiR, Phasechi}',
        # Pre-EWSB and post-EWSB Dirac spinors for chi
        'Fchi1 -> {chiL, 0}',
        'Fchi2 -> {0, chiR}',
        'Fchi -> {chiL, chiR}',
        # Down-type Yukawa uses conj[H1] (hypercharge-balanced)
        'Yd1 conj[H1].d.q',
    ]:
        assert required in main, f'missing: {required!r}'


def test_2hdm_a_anomaly_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    anomaly_warns = [d for d in result.warnings if d.code.startswith('ANOMALY_')]
    assert anomaly_warns == [], f'anomaly warnings: {anomaly_warns}'


def test_2hdm_a_realscalars_emitted():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    assert 'RealScalars = {a0};' in files['2hdmA.m']
