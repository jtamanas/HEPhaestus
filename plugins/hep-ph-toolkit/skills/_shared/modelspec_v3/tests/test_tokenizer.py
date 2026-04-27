"""Tests for the Mathematica tokenizer (modelspec_v3.tokenizer)."""
import pytest
from modelspec_v3.tokenizer import tokenize, extract_identifiers, Token


# ---------------------------------------------------------------------------
# tokenize() tests
# ---------------------------------------------------------------------------

def test_simple_identifiers():
    toks = tokenize('Yd conj[H].d.q')
    types = [t.kind for t in toks]
    assert 'IDENT' in types
    idents = [t.value for t in toks if t.kind == 'IDENT']
    assert 'Yd' in idents and 'conj' in idents and 'H' in idents
    assert 'd' in idents and 'q' in idents


def test_named_symbol():
    toks = tokenize('-1/2 \\[Lambda] conj[H].H.conj[H].H')
    named = [t.value for t in toks if t.kind == 'NAMED_SYM']
    assert '\\[Lambda]' in named


def test_sum_brackets():
    toks = tokenize('Sum[yL[i,a] phi[a] LL[i].NL, {i,1,3}, {a,1,3}]')
    idents = [t.value for t in toks if t.kind == 'IDENT']
    assert 'Sum' in idents and 'yL' in idents and 'phi' in idents


def test_dot_produces_dot_token():
    toks = tokenize('H.q.u')
    kinds = [t.kind for t in toks]
    assert kinds.count('DOT') == 2


def test_op_tokens():
    toks = tokenize('-1/2')
    ops = [t.value for t in toks if t.kind == 'OP']
    assert '-' in ops and '/' in ops


def test_bracket_tokens():
    toks = tokenize('f[x]')
    kinds = [t.kind for t in toks]
    assert 'BRACKET' in kinds


def test_brace_tokens():
    toks = tokenize('{i,1,3}')
    kinds = [t.kind for t in toks]
    assert 'BRACE' in kinds


def test_comma_token():
    toks = tokenize('f[i,j]')
    kinds = [t.kind for t in toks]
    assert 'COMMA' in kinds


def test_integer_token():
    toks = tokenize('3')
    assert toks[0].kind == 'INT' and toks[0].value == '3'


def test_alphanumeric_identifier():
    toks = tokenize('phi1 a0 Yu11')
    idents = [t.value for t in toks if t.kind == 'IDENT']
    assert 'phi1' in idents and 'a0' in idents and 'Yu11' in idents


def test_named_sym_before_ident():
    # Ensure \[ImaginaryI] is tokenized as NAMED_SYM, not mangled as IDENT
    toks = tokenize('\\[ImaginaryI] ychi')
    assert toks[0].kind == 'NAMED_SYM'
    assert toks[0].value == '\\[ImaginaryI]'
    assert toks[1].kind == 'IDENT' and toks[1].value == 'ychi'


def test_token_pos():
    toks = tokenize('AB CD')
    assert toks[0].pos == 0
    assert toks[1].pos == 3


def test_unexpected_char_raises():
    with pytest.raises(SyntaxError):
        tokenize('f @ g')


# ---------------------------------------------------------------------------
# extract_identifiers() tests
# ---------------------------------------------------------------------------

def test_extract_identifiers_skips_reserved():
    # Sum, conj should be filtered out; Sum-iterators i,j too
    ids = extract_identifiers('Sum[Yu[i,j] H.u.q, {i,1,3}, {j,1,3}]')
    assert 'Yu' in ids
    assert 'H' in ids and 'u' in ids and 'q' in ids
    assert 'Sum' not in ids and 'i' not in ids and 'j' not in ids


def test_extract_identifies_imaginary_unit():
    ids = extract_identifiers('\\[ImaginaryI] ychi a0.ChiR.ChiL')
    assert '\\[ImaginaryI]' not in ids   # builtin, filtered
    assert 'ychi' in ids and 'a0' in ids
    assert 'ChiR' in ids and 'ChiL' in ids


def test_simple_term_no_brackets():
    ids = extract_identifiers('Yd conj[H].d.q')
    assert ids == {'Yd', 'H', 'd', 'q'}    # 'conj' filtered, no iterators


def test_nested_indices():
    ids = extract_identifiers('Sum[yL[i,a] phi[a] LL[i].NL, {i,1,3}, {a,1,3}]')
    # Even though i,a appear in `phi[a]` and `LL[i]`, they should not be in result
    assert 'i' not in ids and 'a' not in ids
    assert 'NL' in ids and 'phi' in ids and 'LL' in ids and 'yL' in ids


def test_lambda_named_symbol_is_extracted():
    # \[Lambda] is a parameter name, not reserved
    ids = extract_identifiers('-1/2 \\[Lambda] conj[H].H.conj[H].H')
    assert '\\[Lambda]' in ids


def test_double_sum_iterators_both_dropped():
    ids = extract_identifiers('Sum[Sum[Aij[i,j] phi[i].phi[j], {i,1,3}], {j,1,3}]')
    assert 'i' not in ids and 'j' not in ids
    assert 'Aij' in ids and 'phi' in ids


def test_no_sum_iterators_plain_expr():
    # Without Sum braces, single-letter names ARE included — they are valid
    # SARAH field refs (e.g. H = Higgs doublet, q = quark doublet).
    # SINGLE_LETTERS only blocks *declarations* (is_reserved), not references.
    ids = extract_identifiers('Y H.q.u')
    assert 'Y' in ids   # valid single-letter field ref
    assert 'H' in ids   # valid single-letter field ref
    assert 'q' in ids   # valid single-letter field ref


def test_multichar_idents_not_dropped():
    ids = extract_identifiers('Yt Ht Qt')
    assert 'Yt' in ids and 'Ht' in ids and 'Qt' in ids


def test_extract_returns_set():
    ids = extract_identifiers('Yd conj[H].d.q')
    assert isinstance(ids, set)


def test_empty_string():
    ids = extract_identifiers('')
    assert ids == set()
