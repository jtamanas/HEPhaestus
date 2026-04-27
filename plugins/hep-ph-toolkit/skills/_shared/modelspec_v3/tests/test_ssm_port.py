"""Acceptance tests for the SSM v3 spec (real-scalar VEV stress test)."""
import pathlib
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

SPEC_PATH = pathlib.Path(__file__).parent.parent / 'specs' / 'ssm.yaml'


def test_ssm_validates_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    assert result.errors == [], f'errors: {result.errors}'
    assert result.warnings == [], f'warnings: {result.warnings}'


def test_ssm_renders():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    assert 'SSM.m' in files


def test_ssm_real_scalar_vev_with_zero_goldstone():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['SSM.m']
    assert '{Sing, {vS, 1}, {0, 0}, {phiS, 1}}' in main


def test_ssm_scalar_mixing_at_ewsb():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['SSM.m']
    assert '{{phiH, phiS}, {hh, ZH}}' in main


def test_ssm_singleton_str_components_bare_form():
    """`s` field has components 'Sing' (string), should emit `Sing` not `{Sing}`."""
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['SSM.m']
    assert 'ScalarFields[[2]] = {s, 1, Sing,' in main
    assert '{s, 1, {Sing},' not in main


def test_ssm_realscalars_includes_s():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['SSM.m']
    assert 'RealScalars = {s};' in main


def test_ssm_anomaly_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    anomaly_warns = [d for d in result.warnings if d.code.startswith('ANOMALY_')]
    assert anomaly_warns == [], f'anomaly warnings: {anomaly_warns}'
