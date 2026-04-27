"""Tests for render_ewsb (DEFINITION[...][...] blocks).

Schema field names follow schema.json $defs:
  Vev: component, vev, goldstone, physical
  GaugeMix: rotate, to, matrix
  MixingOutput: name, mixing
  MixingDirac: kind, stage, lh, rh, outputs={lh, rh}
  MixingMajorana / MixingScalar: kind, stage, weyls, output
  Phase: field, phase
  Spinor: name, components
"""
import pathlib

from modelspec_v3.loader import load_spec
from modelspec_v3.render.ewsb import render_ewsb

FIX = pathlib.Path(__file__).parent / 'fixtures'


def _sm_with_higgs_vev():
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['ewsb'] = {
        'vevs': [
            {
                'component': 'H0',
                'vev': ['v', '1/Sqrt[2]'],
                'goldstone': ['Ah', '\\[ImaginaryI]/Sqrt[2]'],
                'physical': ['hh', '1/Sqrt[2]'],
            },
        ],
        'gauge_sector': [
            {'rotate': ['VB', 'VWB[3]'], 'to': ['VP', 'VZ'], 'matrix': 'ZZ'},
            {'rotate': ['VWB[1]', 'VWB[2]'], 'to': ['VWp', 'conj[VWp]'], 'matrix': 'ZW'},
        ],
        'mixing_sector': [],
        'phases': [],
        'dirac_spinors_pre_ewsb': [],
        'dirac_spinors_post_ewsb': [],
    }
    return spec


# ---------------------------------------------------------------------------
# VEVs
# ---------------------------------------------------------------------------

def test_vevs_block():
    spec = _sm_with_higgs_vev()
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][VEVs] = {' in out
    assert (
        '{H0, {v, 1/Sqrt[2]}, {Ah, \\[ImaginaryI]/Sqrt[2]}, {hh, 1/Sqrt[2]}}'
        in out
    )
    # the VEVs block must be properly closed
    vevs_pos = out.find('DEFINITION[EWSB][VEVs]')
    assert vevs_pos != -1
    assert out.find('};', vevs_pos) > vevs_pos


def test_real_scalar_vev_with_zero_goldstone():
    """SSM-style: real scalar VEV has Goldstone [0, 0]."""
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['ewsb'] = {
        'vevs': [
            {
                'component': 'Sing',
                'vev': ['vS', '1'],
                'goldstone': [0, 0],
                'physical': ['phiS', '1'],
            },
        ],
        'gauge_sector': [],
        'mixing_sector': [],
        'phases': [],
        'dirac_spinors_pre_ewsb': [],
        'dirac_spinors_post_ewsb': [],
    }
    out = render_ewsb(spec)
    assert '{Sing, {vS, 1}, {0, 0}, {phiS, 1}}' in out


# ---------------------------------------------------------------------------
# GaugeSector
# ---------------------------------------------------------------------------

def test_gauge_sector():
    spec = _sm_with_higgs_vev()
    out = render_ewsb(spec)
    assert '{{VB, VWB[3]}, {VP, VZ}, ZZ}' in out
    assert '{{VWB[1], VWB[2]}, {VWp, conj[VWp]}, ZW}' in out


# ---------------------------------------------------------------------------
# MatterSector
# ---------------------------------------------------------------------------

def test_majorana_mixing_at_ewsb():
    spec = _sm_with_higgs_vev()
    spec['ewsb']['mixing_sector'] = [
        {
            'kind': 'majorana',
            'stage': 'EWSB',
            'weyls': ['s0', 'PsiDd0', 'PsiDu0'],
            'output': {'name': 'Chi', 'mixing': 'ZN'},
        },
    ]
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][MatterSector] = {' in out
    assert '{{s0, PsiDd0, PsiDu0}, {Chi, ZN}}' in out


def test_dirac_mixing_at_ewsb():
    spec = _sm_with_higgs_vev()
    spec['ewsb']['mixing_sector'] = [
        {
            'kind': 'dirac',
            'stage': 'EWSB',
            'lh': ['dL'],
            'rh': ['conj[dR]'],
            'outputs': {
                'lh': {'name': 'DL', 'mixing': 'Vd'},
                'rh': {'name': 'DR', 'mixing': 'Ud'},
            },
        },
    ]
    out = render_ewsb(spec)
    assert '{{{dL}, {conj[dR]}}, {{DL, Vd}, {DR, Ud}}}' in out


def test_scalar_mixing_at_gauge_es_stage():
    """Scotogenic-style: scalar mixing emitted at GaugeES (no VEV)."""
    spec = _sm_with_higgs_vev()
    spec['ewsb']['mixing_sector'] = [
        {
            'kind': 'scalar',
            'stage': 'GaugeES',
            'weyls': ['phi1', 'phi2', 'phi3'],
            'output': {'name': 'phiM', 'mixing': 'Zphi'},
        },
    ]
    out = render_ewsb(spec)
    assert 'DEFINITION[GaugeES][MatterSector] = {' in out
    assert '{{phi1, phi2, phi3}, {phiM, Zphi}}' in out


def test_scalar_mixing_at_ewsb_stage():
    """SSM-style: scalar mixing emitted at EWSB."""
    spec = _sm_with_higgs_vev()
    spec['ewsb']['mixing_sector'] = [
        {
            'kind': 'scalar',
            'stage': 'EWSB',
            'weyls': ['phiH', 'phiS'],
            'output': {'name': 'hh', 'mixing': 'ZH'},
        },
    ]
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][MatterSector] = {' in out
    assert '{{phiH, phiS}, {hh, ZH}}' in out


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def test_phases_block():
    spec = _sm_with_higgs_vev()
    spec['ewsb']['phases'] = [{'field': 's0', 'phase': 'PhaseFS'}]
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][Phases] = {' in out
    assert '{s0, PhaseFS}' in out


# ---------------------------------------------------------------------------
# DiracSpinors
# ---------------------------------------------------------------------------

def test_dirac_spinors_pre_ewsb_zero_components():
    spec = _sm_with_higgs_vev()
    spec['ewsb']['dirac_spinors_pre_ewsb'] = [
        {'name': 'Fd1', 'components': ['dL', 0]},
        {'name': 'Fd2', 'components': [0, 'dR']},
        {'name': 'Fv1', 'components': ['vL', 0]},
    ]
    out = render_ewsb(spec)
    assert 'DEFINITION[GaugeES][DiracSpinors] = {' in out
    assert 'Fd1 -> {dL, 0}' in out
    assert 'Fd2 -> {0, dR}' in out
    assert 'Fv1 -> {vL, 0}' in out


def test_dirac_spinors_post_ewsb_with_conj():
    spec = _sm_with_higgs_vev()
    spec['ewsb']['dirac_spinors_post_ewsb'] = [
        {'name': 'Fd', 'components': ['DL', 'conj[DR]']},
        {'name': 'Fv', 'components': ['vL', 0]},
    ]
    out = render_ewsb(spec)
    assert 'DEFINITION[EWSB][DiracSpinors] = {' in out
    assert 'Fd -> {DL, conj[DR]}' in out
    assert 'Fv -> {vL, 0}' in out


# ---------------------------------------------------------------------------
# Empty-block omission and ordering
# ---------------------------------------------------------------------------

def test_omits_empty_blocks():
    """If a section is empty, omit its DEFINITION block entirely."""
    spec = load_spec(FIX / 'sm_minimal.yaml')  # all EWSB arrays empty
    out = render_ewsb(spec)
    assert 'DEFINITION[' not in out


def test_block_ordering():
    """Ordering must match the singlet_doublet golden."""
    spec = _sm_with_higgs_vev()
    spec['ewsb']['mixing_sector'] = [
        {
            'kind': 'majorana',
            'stage': 'EWSB',
            'weyls': ['x'],
            'output': {'name': 'A', 'mixing': 'B'},
        },
    ]
    spec['ewsb']['dirac_spinors_pre_ewsb'] = [
        {'name': 'Fd1', 'components': ['dL', 0]},
    ]
    spec['ewsb']['dirac_spinors_post_ewsb'] = [
        {'name': 'Fd', 'components': ['DL', 'conj[DR]']},
    ]
    spec['ewsb']['phases'] = [{'field': 's0', 'phase': 'PhaseFS'}]

    out = render_ewsb(spec)

    def pos(s):
        return out.find(s)

    assert pos('DEFINITION[EWSB][MatterSector]') < pos('DEFINITION[GaugeES][DiracSpinors]')
    assert pos('DEFINITION[GaugeES][DiracSpinors]') < pos('DEFINITION[EWSB][GaugeSector]')
    assert pos('DEFINITION[EWSB][GaugeSector]') < pos('DEFINITION[EWSB][VEVs]')
    assert pos('DEFINITION[EWSB][VEVs]') < pos('DEFINITION[EWSB][Phases]')
    assert pos('DEFINITION[EWSB][Phases]') < pos('DEFINITION[EWSB][DiracSpinors]')
