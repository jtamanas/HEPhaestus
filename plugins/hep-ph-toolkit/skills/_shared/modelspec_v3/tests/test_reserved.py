from modelspec_v3 import reserved

def test_mathematica_builtins_contains_core():
    for name in ['I', 'E', 'D', 'Pi', 'Sum', 'If', 'Sqrt', 'Mass']:
        assert name in reserved.MATHEMATICA_BUILTINS

def test_sarah_reserved_contains_directives():
    for name in ['Casimir', 'Dynkin', 'LagHC', 'LagNoHC', 'GaugeES', 'EWSB',
                'DEFINITION', 'AddHC', 'conj', 'RealScalars']:
        assert name in reserved.SARAH_RESERVED

def test_single_letters_complete():
    assert len(reserved.SINGLE_LETTERS) == 52  # a-z + A-Z
    assert 'a' in reserved.SINGLE_LETTERS and 'Z' in reserved.SINGLE_LETTERS

def test_renderer_aliases():
    assert reserved.RENDERER_ALIASES == {'eEM': 'e', 'vEW': 'v'}

def test_lambda_with_brackets_not_reserved():
    # \[Lambda] is allowed as a parameter name; bare 'Lambda' is reserved
    assert 'Lambda' in reserved.SARAH_RESERVED
    assert '\\[Lambda]' not in reserved.SARAH_RESERVED

def test_is_reserved_helper():
    assert reserved.is_reserved('Sum')
    assert reserved.is_reserved('a')
    assert not reserved.is_reserved('eEM')   # alias, not reserved itself
    assert not reserved.is_reserved('vEW')   # alias, not reserved itself
    assert not reserved.is_reserved('Yu')
