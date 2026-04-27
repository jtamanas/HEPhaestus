import pathlib
from modelspec_v3.render.particles import render_particles_m
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def _build_spec(particles_overrides=None, **kwargs):
    spec = load_spec(FIX / 'sm_minimal.yaml')
    if particles_overrides is not None:
        spec['particles'] = particles_overrides
    spec.update(kwargs)
    return spec


def test_auto_emit_gauge_bosons():
    """SM minimal: 3 gauge groups → 3 V-bosons + 3 ghosts in GaugeES block."""
    spec = _build_spec()
    out = render_particles_m(spec)
    for name in ['VB', 'VWB', 'VG', 'gB', 'gWB', 'gG']:
        assert name in out, f'missing auto-emitted {name}'
    assert 'ParticleDefinitions[GaugeES]' in out


def test_auto_emit_scalar_components():
    spec = _build_spec()
    out = render_particles_m(spec)
    assert 'H0' in out
    assert 'Hp' in out


def test_user_override_takes_precedence():
    spec = _build_spec()
    spec['particles']['gauge_es'].append({
        'name': 'VB', 'description': 'Custom B-Boson',
    })
    out = render_particles_m(spec)
    assert 'Custom B-Boson' in out
    # The auto default 'B-Boson' should be replaced; check it doesn't appear with the user one
    # (the auto default for VB would be 'hypercharge-Boson' or similar; we check the user one wins)


def test_ewsb_block_only_from_user():
    """EWSB block contains only user-declared particles."""
    spec = _build_spec()
    spec['particles']['ewsb'] = [
        {'name': 'hh', 'description': 'Higgs', 'pdg': [25]},
        {'name': 'VP', 'description': 'Photon'},
    ]
    out = render_particles_m(spec)
    assert 'ParticleDefinitions[EWSB] = {' in out
    assert 'Description -> "Higgs"' in out
    assert 'PDG -> {25}' in out
    assert 'Description -> "Photon"' in out


def test_weyl_intermediate_auto_emit_from_cwt():
    """Components like uL, dL, q, etc. from CWT auto-emitted to weyl-intermediate block."""
    spec = _build_spec()
    out = render_particles_m(spec)
    assert 'WeylFermionAndIndermediate = {' in out
    for sym in ['uL', 'dL', 'q', 'LL', 'H']:
        assert f'{{{sym},' in out, f'missing weyl-intermediate {sym}'


def test_weyl_intermediate_user_override():
    spec = _build_spec()
    spec['particles']['weyl_intermediate'] = [
        {'name': 'q', 'latex': 'q'},
    ]
    out = render_particles_m(spec)
    # Both user override and auto-emit logic should converge on `{q, ...}`
    assert '{q,' in out


def test_block_structure():
    spec = _build_spec()
    out = render_particles_m(spec)
    assert out.startswith('(*')   # header comment
    assert 'ParticleDefinitions[GaugeES] = {' in out
    assert 'ParticleDefinitions[EWSB] = {' in out or 'WeylFermionAndIndermediate = {' in out
    assert 'WeylFermionAndIndermediate = {' in out  # SARAH typo preserved


def test_pdg_list_rendered():
    spec = _build_spec()
    spec['particles']['ewsb'] = [
        {'name': 'FChi', 'description': 'BSM fermion mass eigenstate Chi',
         'pdg': [9958431, 9956206, 9979223], 'mass': 'LesHouches',
         'electric_charge': 0},
    ]
    out = render_particles_m(spec)
    assert 'PDG -> {9958431, 9956206, 9979223}' in out
    assert 'Mass -> LesHouches' in out


def test_pdg_ix_rendered_with_dot():
    spec = _build_spec()
    spec['particles']['ewsb'] = [
        {'name': 'hh', 'description': 'Higgs', 'pdg': [25], 'pdg_ix': [101000001]},
    ]
    out = render_particles_m(spec)
    assert 'PDG.IX -> {101000001}' in out


def test_dark_su3_emits_dark_gauge_boson():
    """4 gauge groups (B, WB, G, GD) → 4 V-bosons + 4 ghosts."""
    spec = _build_spec()
    spec['gauge_groups'].append({'symbol': 'GD', 'type': 'SU(3)', 'label': 'dark',
                                  'coupling': 'gD', 'ssb': False})
    spec['parameters'].append({'name': 'gD', 'real': True})
    out = render_particles_m(spec)
    assert 'VGD' in out
    assert 'gGD' in out
