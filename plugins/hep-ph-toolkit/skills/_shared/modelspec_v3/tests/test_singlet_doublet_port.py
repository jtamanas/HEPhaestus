"""Round-trip tests for the singlet_doublet v3 spec port."""
import pathlib
from modelspec_v3.loader import load_spec
from modelspec_v3.validate import validate
from modelspec_v3.render import render_all

SPEC_PATH = pathlib.Path(__file__).parent.parent / 'specs' / 'singlet_doublet.yaml'


def test_singlet_doublet_validates_clean():
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    assert result.errors == [], f'errors: {result.errors}'
    # Allow no warnings (DM parity model should be fully closed)
    assert result.warnings == [], f'warnings: {result.warnings}'


def test_singlet_doublet_renders_three_files():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    assert set(files.keys()) == {'SingletDoublet.m', 'parameters.m', 'particles.m'}


def test_singlet_doublet_main_m_contains_required_blocks():
    spec = load_spec(SPEC_PATH)
    files = render_all(spec)
    main = files['SingletDoublet.m']
    for required in [
        'Model`Name = "SingletDoublet";',
        'Global[[1]] = {Z[2], DMParity};',
        'NameOfStates = {GaugeES, EWSB};',
        'DEFINITION[GaugeES][LagrangianInput]',
        'Gauge[[1]] = {B, U[1], hypercharge, g1, False, 1};',
        'FermionFields[[1]] = {q, 3, {uL, dL},',
        'FermionFields[[6]] = {FS, 1, s0, 0, 1, 1, -1};',
        'FermionFields[[7]] = {PsiDd,',
        'FermionFields[[8]] = {PsiDu,',
        'ScalarFields[[1]] = {H, 1, {Hp, H0},',
        'LagNoHC',
        'LagHC',
        # BSM Lagrangian terms appear inside LagHC
        '1/2 MS FS.FS',
        'MPsi PsiDu.PsiDd',
        'yh1 conj[H].FS.PsiDu',
        'yh2 H.FS.PsiDd',
        'DEFINITION[EWSB][MatterSector]',
        '{{s0, PsiDd0, PsiDu0}, {Chi, ZN}}',
        '{{{PsiDdm}, {PsiDup}}, {{ChiM, UM}, {ChiP, UP}}}',
        'DEFINITION[GaugeES][DiracSpinors]',
        'DEFINITION[EWSB][GaugeSector]',
        'DEFINITION[EWSB][VEVs]',
        'DEFINITION[EWSB][Phases]',
        'DEFINITION[EWSB][DiracSpinors]',
    ]:
        assert required in main, f'missing: {required!r}'


def test_singlet_doublet_anomaly_clean():
    """Vectorlike pair (PsiDu / PsiDd) cancels; SM remains clean."""
    spec = load_spec(SPEC_PATH)
    result = validate(spec)
    anomaly_warns = [d for d in result.warnings if d.code.startswith('ANOMALY_')]
    assert anomaly_warns == [], f'anomaly warnings: {anomaly_warns}'
