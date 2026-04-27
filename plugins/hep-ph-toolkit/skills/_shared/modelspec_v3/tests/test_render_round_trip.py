import pathlib
from modelspec_v3.render import render_all
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def test_round_trip_returns_three_files():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    files = render_all(spec)
    assert set(files.keys()) == {'SMTest.m', 'parameters.m', 'particles.m'}


def test_main_m_contains_required_blocks():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    files = render_all(spec)
    main = files['SMTest.m']
    for required in [
        'Model`Name = "SMTest";',
        'NameOfStates = {GaugeES, EWSB};',
        'DEFINITION[GaugeES][LagrangianInput]',
        'Gauge[[1]] = {B,',
        'FermionFields[[1]] = {q,',
        'ScalarFields[[1]] = {H,',
        'LagNoHC',
        'LagHC',
    ]:
        assert required in main, f'missing block: {required!r}'


def test_main_m_no_ewsb_when_empty():
    """sm_minimal has no EWSB content -> no DEFINITION blocks emitted."""
    spec = load_spec(FIX / 'sm_minimal.yaml')
    files = render_all(spec)
    main = files['SMTest.m']
    assert 'DEFINITION[EWSB]' not in main


def test_parameters_m_has_header():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['parameters'] = [{'name': 'g1', 'description': 'Hypercharge-Coupling'}]
    files = render_all(spec)
    p = files['parameters.m']
    assert 'parameters.m' in p   # header comment
    assert 'ParameterDefinitions = {' in p


def test_particles_m_has_header():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    files = render_all(spec)
    p = files['particles.m']
    assert 'particles.m' in p
    assert 'ParticleDefinitions[GaugeES]' in p


def test_render_all_with_full_ewsb():
    """SM with EWSB content: orchestrator wires everything together."""
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['ewsb']['vevs'] = [
        {'component': 'H0',
         'vev': ['v', '1/Sqrt[2]'],
         'goldstone': ['Ah', '\\[ImaginaryI]/Sqrt[2]'],
         'physical': ['hh', '1/Sqrt[2]']},
    ]
    files = render_all(spec)
    main = files['SMTest.m']
    assert 'DEFINITION[EWSB][VEVs]' in main
    assert '{H0, {v, 1/Sqrt[2]}, {Ah, \\[ImaginaryI]/Sqrt[2]}, {hh, 1/Sqrt[2]}}' in main
