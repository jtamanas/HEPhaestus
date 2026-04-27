"""Tests for the sandboxed charge evaluator."""
from fractions import Fraction

import pytest

from modelspec_v3.charge_eval import evaluate


def test_int():
    assert evaluate(5, 'A', 1) == 5


def test_str_int():
    assert evaluate('5', 'A', 1) == 5


def test_neg_int():
    assert evaluate('-5', 'A', 1) == -5


def test_frac():
    assert evaluate('1/6', 'A', 1) == Fraction(1, 6)


def test_neg_frac():
    assert evaluate('-1/2', 'A', 1) == Fraction(-1, 2)


def test_if_eq_then():
    assert evaluate('If[A==1, 5, 7]', 'A', 1) == 5


def test_if_eq_else():
    assert evaluate('If[A==1, 5, 7]', 'A', 2) == 7


def test_if_neq():
    assert evaluate('If[A!=1, 5, 7]', 'A', 1) == 7


def test_if_gt():
    assert evaluate('If[A>0, 1, -1]', 'A', 5) == 1
    assert evaluate('If[A>0, 1, -1]', 'A', -3) == -1


def test_if_le():
    assert evaluate('If[A<=2, 1, 0]', 'A', 2) == 1
    assert evaluate('If[A<=2, 1, 0]', 'A', 3) == 0


def test_nested_if_unknown_branches_are_symbolic():
    e = 'If[A==1, X, If[A==2, Y, Z]]'
    # Branches reference unknown symbols -> entire result is symbolic.
    assert evaluate(e, 'A', 1) is None


def test_nested_if_resolves_numeric():
    e = 'If[A==1, 1, If[A==2, 2, 3]]'
    assert evaluate(e, 'A', 2) == 2
    assert evaluate(e, 'A', 5) == 3


def test_arithmetic():
    assert evaluate('1+2', 'A', 0) == 3
    assert evaluate('1/3 + 1/6', 'A', 0) == Fraction(1, 2)


def test_arithmetic_parens():
    assert evaluate('(1+2)*3', 'A', 0) == 9
    assert evaluate('-(1+2)', 'A', 0) == -3


def test_unknown_symbol_returns_none():
    assert evaluate('qChi', 'A', 1) is None


def test_unknown_in_arithmetic_returns_none():
    assert evaluate('qChi + 1', 'A', 1) is None


def test_a_used_in_arithmetic():
    assert evaluate('A + 1', 'A', 4) == 5
    assert evaluate('A/2', 'A', 6) == 3
    assert evaluate('A/2', 'A', 5) == Fraction(5, 2)


def test_negative_rhs_in_cond():
    assert evaluate('If[A==-1, 5, 7]', 'A', -1) == 5
    assert evaluate('If[A==-1, 5, 7]', 'A', 1) == 7


def test_fraction_input():
    assert evaluate(Fraction(1, 3), 'A', 0) == Fraction(1, 3)


def test_bool_rejected():
    with pytest.raises(TypeError):
        evaluate(True, 'A', 0)


def test_empty_string_errors():
    with pytest.raises(ValueError):
        evaluate('', 'A', 0)


def test_bad_token_errors():
    with pytest.raises(ValueError):
        evaluate('1 @ 2', 'A', 0)
