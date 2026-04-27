"""Sandboxed evaluator for charge expressions in ModelSpec v3.

Recognises:
  - integer literals (positive / negative)
  - fraction literals like 1/6, -1/2
  - If[cond, then, else] with cond = `<sym> <op> <int>`,
    op ∈ {==, !=, >, <, >=, <=}; nested If allowed
  - bare symbol matching A_name -> A_value
  - bare unknown symbols -> evaluation result is None (symbolic)
  - arithmetic: + - * / and parentheses

Returns int | Fraction on success, or None when an unknown symbol prevented
full numeric evaluation.

Implementation is a small recursive-descent parser. The grammar is:

  expr     := add
  add      := mul (('+' | '-') mul)*
  mul      := unary (('*' | '/') unary)*
  unary    := ('+' | '-') unary | atom
  atom     := number | ifexpr | symbol | '(' expr ')'
  ifexpr   := 'If' '[' cond ',' expr ',' expr ']'
  cond     := symbol op number
  number   := INT
  symbol   := IDENT
"""
from __future__ import annotations

from fractions import Fraction
from typing import Optional, Union

ChargeValue = Union[int, Fraction]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKENS = (
    ('NUM', r'\d+'),
    ('IDENT', r'[A-Za-z_][A-Za-z_0-9]*'),
    ('OP', r'==|!=|>=|<=|[+\-*/(),\[\]<>]'),
    ('SKIP', r'\s+'),
)

import re
_MASTER_RE = re.compile('|'.join(f'(?P<{n}>{p})' for n, p in _TOKENS))


def _tokenize(src: str):
    pos = 0
    out = []
    while pos < len(src):
        m = _MASTER_RE.match(src, pos)
        if not m:
            raise ValueError(f"charge_eval: unexpected character at {pos!r} in {src!r}")
        kind = m.lastgroup
        text = m.group()
        pos = m.end()
        if kind == 'SKIP':
            continue
        out.append((kind, text))
    out.append(('EOF', ''))
    return out


# ---------------------------------------------------------------------------
# Parser / evaluator
# ---------------------------------------------------------------------------

# Sentinel for "expression was symbolic — partial result has no meaning".
class _Symbolic:
    _inst = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst
    def __repr__(self): return '<symbolic>'

_SYMBOLIC = _Symbolic()


def _is_num(v) -> bool:
    return isinstance(v, (int, Fraction)) and not isinstance(v, bool)


class _Parser:
    def __init__(self, tokens, A_name: str, A_value: int):
        self.tokens = tokens
        self.i = 0
        self.A_name = A_name
        self.A_value = A_value

    def peek(self):
        return self.tokens[self.i]

    def eat(self, kind=None, text=None):
        tok = self.tokens[self.i]
        if kind and tok[0] != kind:
            raise ValueError(f"charge_eval: expected {kind}, got {tok}")
        if text and tok[1] != text:
            raise ValueError(f"charge_eval: expected {text!r}, got {tok}")
        self.i += 1
        return tok

    def parse(self):
        v = self.expr()
        if self.peek()[0] != 'EOF':
            raise ValueError(f"charge_eval: trailing tokens at {self.peek()!r}")
        return v

    def expr(self):
        return self.add()

    def add(self):
        left = self.mul()
        while self.peek() == ('OP', '+') or self.peek() == ('OP', '-'):
            op = self.eat()[1]
            right = self.mul()
            left = self._binop(op, left, right)
        return left

    def mul(self):
        left = self.unary()
        while self.peek() == ('OP', '*') or self.peek() == ('OP', '/'):
            op = self.eat()[1]
            right = self.unary()
            left = self._binop(op, left, right)
        return left

    def unary(self):
        tok = self.peek()
        if tok == ('OP', '+'):
            self.eat()
            return self.unary()
        if tok == ('OP', '-'):
            self.eat()
            v = self.unary()
            if v is _SYMBOLIC:
                return _SYMBOLIC
            return -v
        return self.atom()

    def atom(self):
        tok = self.peek()
        if tok[0] == 'NUM':
            self.eat()
            return int(tok[1])
        if tok == ('OP', '('):
            self.eat()
            v = self.expr()
            self.eat('OP', ')')
            return v
        if tok[0] == 'IDENT':
            name = tok[1]
            if name == 'If':
                return self.ifexpr()
            self.eat()
            if name == self.A_name:
                return int(self.A_value)
            return _SYMBOLIC
        raise ValueError(f"charge_eval: unexpected token {tok!r}")

    def ifexpr(self):
        self.eat('IDENT', 'If')
        self.eat('OP', '[')
        cond = self.cond()
        self.eat('OP', ',')
        then_branch_start = self.i
        # Parse both branches regardless; we choose based on cond. If cond is
        # symbolic we still evaluate both, then return _SYMBOLIC.
        then_v = self.expr()
        self.eat('OP', ',')
        else_v = self.expr()
        self.eat('OP', ']')
        if cond is _SYMBOLIC:
            return _SYMBOLIC
        return then_v if cond else else_v

    def cond(self):
        # symbol op number
        tok = self.eat('IDENT')
        sym_name = tok[1]
        if sym_name == self.A_name:
            sym_val = int(self.A_value)
        else:
            sym_val = _SYMBOLIC
        op_tok = self.eat('OP')
        op = op_tok[1]
        if op not in ('==', '!=', '>', '<', '>=', '<='):
            raise ValueError(f"charge_eval: bad cond op {op!r}")
        # rhs may be -INT or INT
        sign = 1
        if self.peek() == ('OP', '-'):
            self.eat()
            sign = -1
        elif self.peek() == ('OP', '+'):
            self.eat()
        rhs_tok = self.eat('NUM')
        rhs = sign * int(rhs_tok[1])
        if sym_val is _SYMBOLIC:
            return _SYMBOLIC
        if op == '==': return sym_val == rhs
        if op == '!=': return sym_val != rhs
        if op == '>':  return sym_val > rhs
        if op == '<':  return sym_val < rhs
        if op == '>=': return sym_val >= rhs
        if op == '<=': return sym_val <= rhs
        raise AssertionError("unreachable")

    def _binop(self, op, a, b):
        if a is _SYMBOLIC or b is _SYMBOLIC:
            return _SYMBOLIC
        if op == '+': return a + b
        if op == '-': return a - b
        if op == '*': return a * b
        if op == '/':
            # Integer-division would lose 1/6; promote to Fraction.
            if not _is_num(a) or not _is_num(b):
                raise ValueError("charge_eval: non-numeric div")
            return Fraction(a) / Fraction(b)
        raise AssertionError(f"unknown op {op}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(expr, A_name: str, A_value: int) -> Optional[ChargeValue]:
    """Evaluate `expr`. Returns int|Fraction on success, None if symbolic.

    `expr` may be int, or str (numeric, fraction, or `If[]`-form expression).
    `A_name` is the global-symmetry variable substituted with `A_value`.
    """
    if isinstance(expr, bool):
        # Don't accept booleans even though they're a subclass of int.
        raise TypeError("charge_eval.evaluate: bool not a valid charge")
    if isinstance(expr, int):
        return expr
    if isinstance(expr, Fraction):
        return expr
    if not isinstance(expr, str):
        raise TypeError(f"charge_eval.evaluate: unsupported type {type(expr).__name__}")

    s = expr.strip()
    if not s:
        raise ValueError("charge_eval: empty expression")

    tokens = _tokenize(s)
    parser = _Parser(tokens, A_name, A_value)
    val = parser.parse()
    if val is _SYMBOLIC:
        return None
    if isinstance(val, Fraction) and val.denominator == 1:
        return int(val)
    return val
