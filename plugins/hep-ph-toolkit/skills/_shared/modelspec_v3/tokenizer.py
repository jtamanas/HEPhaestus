"""Mathematica tokenizer for Lagrangian terms.

Produces a stream of typed tokens:
  NAMED_SYM  - Mathematica named-symbol form, e.g. \\[Lambda], \\[ImaginaryI]
  IDENT      - alphanumeric identifier starting with a letter, e.g. Yd, phi1, a0
  INT        - integer literal, e.g. 3, 12
  OP         - arithmetic operator: + - * /
  BRACKET    - square bracket: [ ]
  BRACE      - curly brace: { }
  COMMA      - comma: ,
  DOT        - non-commutative product dot: .
"""
import re
from dataclasses import dataclass
from typing import List, Set

from .reserved import MATHEMATICA_BUILTINS, SARAH_RESERVED


@dataclass(frozen=True)
class Token:
    kind: str   # NAMED_SYM, IDENT, INT, OP, BRACKET, BRACE, COMMA, DOT
    value: str
    pos: int


# Order matters: NAMED_SYM must be tried before IDENT so that the leading
# backslash is consumed before the regex falls through to plain letter matching.
_NAMED_SYM_RE = re.compile(r'\\\[([A-Za-z]+)\]')
_IDENT_RE     = re.compile(r'[A-Za-z][A-Za-z0-9_]*')
_INT_RE       = re.compile(r'\d+')
_WS           = re.compile(r'\s+')

# Brace-iterator pattern: {varName, <optional sign><digit>...}
# Captures the iteration variable (first element before the comma).
_BRACE_ITER_RE = re.compile(r'\{\s*([A-Za-z][A-Za-z0-9]*)\s*,\s*[-+]?\d')

# Skip-set for extract_identifiers: identifiers that are NOT field/param refs.
# Includes:
#   - Mathematica builtins (Sum, If, Sqrt, I, Pi, …)
#   - SARAH structural reserved words (conj, Delta, Casimir, …)
#   - Named-symbol form of imaginary unit
#
# NOTE: SINGLE_LETTERS is intentionally NOT included here.  Single-letter
# names like H, u, q, d are valid SARAH field references in Lagrangian terms
# (SM Higgs doublet, quark singlets, etc.).  SINGLE_LETTERS is only used by
# the declaration validator (is_reserved) to prevent *naming* a field with a
# bare letter; it must not block *referencing* such a field.
_EXTRACTION_SKIP: frozenset = (
    MATHEMATICA_BUILTINS
    | SARAH_RESERVED
    | frozenset({'\\[ImaginaryI]'})   # named-symbol builtin, not in reserved.py
)


def tokenize(s: str) -> List[Token]:
    """Tokenize a Mathematica Lagrangian term string into a list of Tokens."""
    out: List[Token] = []
    i = 0
    while i < len(s):
        # Skip whitespace
        if (m := _WS.match(s, i)):
            i = m.end()
            continue
        # Named symbol: \[LetterRun]  — must precede IDENT
        if (m := _NAMED_SYM_RE.match(s, i)):
            out.append(Token('NAMED_SYM', m.group(0), i))
            i = m.end()
            continue
        # Plain identifier
        if (m := _IDENT_RE.match(s, i)):
            out.append(Token('IDENT', m.group(0), i))
            i = m.end()
            continue
        # Integer literal
        if (m := _INT_RE.match(s, i)):
            out.append(Token('INT', m.group(0), i))
            i = m.end()
            continue
        # Single-character tokens
        c = s[i]
        if c in '+-*/':
            out.append(Token('OP', c, i))
            i += 1
            continue
        if c in '[]':
            out.append(Token('BRACKET', c, i))
            i += 1
            continue
        if c in '{}':
            out.append(Token('BRACE', c, i))
            i += 1
            continue
        if c == ',':
            out.append(Token('COMMA', c, i))
            i += 1
            continue
        if c == '.':
            out.append(Token('DOT', c, i))
            i += 1
            continue
        raise SyntaxError(f'unexpected char {c!r} at pos {i} in {s!r}')
    return out


def extract_identifiers(s: str) -> Set[str]:
    """Return field/parameter identifiers in *s*, filtering reserved names and
    Sum[]/If[] iteration variables.

    The returned set contains only identifiers that are plausible refs to
    declared model symbols (fields or parameters).
    """
    out: Set[str] = set()
    toks = tokenize(s)
    for t in toks:
        if t.kind == 'NAMED_SYM':
            if t.value not in _EXTRACTION_SKIP:
                out.add(t.value)
        elif t.kind == 'IDENT':
            if t.value not in _EXTRACTION_SKIP:
                out.add(t.value)
    # Remove Sum/If iteration variables detected in brace-range syntax {var, lo, hi}
    out -= _detect_brace_iterators(s)
    return out


def _detect_brace_iterators(s: str) -> Set[str]:
    """Identify Mathematica iteration variables appearing in ``{var, lo, hi}`` form.

    Matches constructs like ``{i, 1, 3}`` or ``{mu, 0, 3}`` and returns the
    set of variable names so they can be excluded from identifier results.
    The ``[-+]?\\d`` suffix ensures we only match numeric bounds (not, e.g.,
    field-list braces ``{H, phi}``).
    """
    return {m.group(1) for m in _BRACE_ITER_RE.finditer(s)}
