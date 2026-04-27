"""Acceptance tests for the canonical SM template (templates/sm.yaml)."""
import pathlib
import pytest
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

SM_PATH = pathlib.Path(__file__).parent.parent / 'templates' / 'sm.yaml'


def test_sm_template_loads():
    spec = load_spec(SM_PATH)
    assert spec['model']['name'] == 'SM'


def test_sm_template_validates_clean():
    spec = load_spec(SM_PATH)
    result = validate(spec)
    assert result.errors == [], f'errors: {result.errors}'
    # Aim for zero warnings, but tolerate ANOMALY_KINMIX_SKIP if it ever fires
    # (it shouldn't for the SM which has a single U(1))
    non_kinmix = [w for w in result.warnings if w.code != 'ANOMALY_KINMIX_SKIP']
    assert non_kinmix == [], f'unexpected warnings: {non_kinmix}'


def test_sm_template_renders():
    spec = load_spec(SM_PATH)
    files = render_all(spec)
    assert 'SM.m' in files
    main = files['SM.m']
    assert 'Model`Name = "SM"' in main
    assert 'NameOfStates = {GaugeES, EWSB};' in main
    assert 'Gauge[[1]] = {B, U[1], hypercharge, g1, False};' in main
    assert 'FermionFields[[1]] = {q, 3, {uL, dL},' in main
    assert 'ScalarFields[[1]] = {H, 1, {Hp, H0},' in main
    assert 'LagHC' in main and 'LagNoHC' in main
    assert 'DEFINITION[EWSB][VEVs]' in main


def test_sm_template_yukawas_balance():
    """SM Yukawas charge-conservation: no warnings about hypercharge balance."""
    spec = load_spec(SM_PATH)
    result = validate(spec)
    assert not any(d.code == 'CHARGE_NONZERO' for d in result.warnings)


def test_sm_template_anomaly_clean():
    """SM cancels all four anomaly types."""
    spec = load_spec(SM_PATH)
    result = validate(spec)
    assert not any(d.code.startswith('ANOMALY_U1') for d in result.warnings)
    assert not any(d.code.startswith('ANOMALY_GRAV') for d in result.warnings)
    assert not any(d.code.startswith('ANOMALY_SU') for d in result.warnings)
