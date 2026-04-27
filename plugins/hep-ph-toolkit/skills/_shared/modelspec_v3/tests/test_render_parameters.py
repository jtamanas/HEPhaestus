import pathlib
from modelspec_v3.render.parameters import render_parameters_m
from modelspec_v3.loader import load_spec

FIX = pathlib.Path(__file__).parent / 'fixtures'


def _build_spec_with_params(params):
    spec = load_spec(FIX / 'sm_minimal.yaml')
    spec['parameters'] = params
    return spec


def test_simple_description_only_param():
    spec = _build_spec_with_params([
        {'name': 'g1', 'description': 'Hypercharge-Coupling'},
    ])
    out = render_parameters_m(spec)
    assert '{g1,' in out
    assert 'Description -> "Hypercharge-Coupling"' in out
    assert out.startswith('(*')   # has header comment
    assert 'ParameterDefinitions = {' in out
    assert '};' in out             # closing


def test_eEM_renders_as_e():
    spec = _build_spec_with_params([
        {'name': 'eEM', 'description': 'electric charge'},
    ])
    out = render_parameters_m(spec)
    assert '{e,' in out  # alias applied
    assert 'eEM' not in out


def test_les_houches_indexed():
    spec = _build_spec_with_params([
        {'name': 'MS', 'latex': 'M_S', 'output_name': 'MS', 'real': True,
         'les_houches': ['BSMPARAMS', 1]},
    ])
    out = render_parameters_m(spec)
    assert 'LesHouches -> {BSMPARAMS, 1}' in out


def test_les_houches_bare():
    spec = _build_spec_with_params([
        {'name': 'ZN', 'description': 'Majorana-Mixing-Matrix-Chi',
         'output_name': 'ZN', 'real': False, 'les_houches': 'ZNMIX'},
    ])
    out = render_parameters_m(spec)
    assert 'LesHouches -> ZNMIX' in out
    assert 'LesHouches -> "ZNMIX"' not in out  # not quoted


def test_dependence_num_emitted_verbatim():
    spec = _build_spec_with_params([
        {'name': 'Yu', 'description': 'Up-Yukawa-Coupling',
         'dependence_num': 'Sqrt[2]/v* {{Mass[Fu,1],0,0}, {0, Mass[Fu,2],0}, {0, 0, Mass[Fu,3]}}'},
    ])
    out = render_parameters_m(spec)
    assert 'DependenceNum ->  Sqrt[2]/v* {{Mass[Fu,1],0,0}, {0, Mass[Fu,2],0}, {0, 0, Mass[Fu,3]}}' in out or \
           'DependenceNum -> Sqrt[2]/v* {{Mass[Fu,1],0,0}, {0, Mass[Fu,2],0}, {0, 0, Mass[Fu,3]}}' in out
    # Either single or double space after `->` is acceptable


def test_real_true_and_false():
    spec = _build_spec_with_params([
        {'name': 'A', 'real': True},
        {'name': 'B', 'real': False},
    ])
    out = render_parameters_m(spec)
    assert 'Real -> True' in out
    assert 'Real -> False' in out


def test_output_name_no_quotes():
    spec = _build_spec_with_params([
        {'name': 'MS', 'real': True, 'output_name': 'MS'},
    ])
    out = render_parameters_m(spec)
    assert 'OutputName -> MS' in out
    assert 'OutputName -> "MS"' not in out


def test_block_well_formed():
    """Emitted block is wellformed: starts with header, has ParameterDefinitions, has closing."""
    spec = _build_spec_with_params([{'name': 'g1', 'description': 'foo'}])
    out = render_parameters_m(spec)
    assert out.count('ParameterDefinitions = {') == 1
    # ends with `};` followed by optional newline
    assert out.rstrip().endswith('};')


def test_no_trailing_comma_on_last_entry():
    spec = _build_spec_with_params([
        {'name': 'A', 'description': 'a'},
        {'name': 'B', 'description': 'b'},
    ])
    out = render_parameters_m(spec)
    # The last `}}` before the closing `};` should NOT have a comma after it
    # Find `}}` followed (possibly by whitespace) by `};` directly
    import re
    m = re.search(r'\}\}\s*\};', out)
    assert m, f'malformed end of block: {out[-200:]!r}'
