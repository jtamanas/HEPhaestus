"""Stage 3: per-term U(1) charge and discrete-symmetry conservation.

For each Lagrangian term, sums the U(1) hypercharges (or checks the
multiplicative product for discrete Z_n symmetries) of every field identifier
it contains.  Emits CHARGE_NONZERO (or DISCRETE_NONZERO) warnings when the
result is non-trivial.

U(1) algorithm
--------------
1. ``extract_identifiers(term)`` returns the set of declared-symbol references.
2. For each identifier:
   - Parameters: contribute 0 (gauge-invariant scalars).
   - Fields by name (FieldRef): use ``field.reps[sym]`` directly.
   - Field components by Weyl symbol (WeylRef with conjugated=True): the
     component is a conjugated spinor, so its charge is –Y(parent field).
3. A bare occurrence of X contributes +charge; an occurrence inside
   ``conj[X]`` contributes –charge (complex-conjugation of the field).
4. Sum charges as Fraction arithmetic; emit warning if non-zero.

Verification against SM Yukawas (all charges under B / hypercharge):
  q=1/6  LL=-1/2  d=1/3  u=-2/3  e=1  H=1/2

  ``Yd conj[H].d.q``  → -Y(H) + Y(d) + Y(q) = -1/2+1/3+1/6 = 0  ✓
  ``-Yu H.u.q``       → +Y(H) + Y(u) + Y(q) = 1/2-2/3+1/6 = 0  ✓
  ``Ye conj[H].e.LL`` → -Y(H) + Y(e) + Y(LL) = -1/2+1-1/2 = 0  ✓
  ``Yextra H.q.q``    → +Y(H)+Y(q)+Y(q) = 1/2+1/6+1/6 = 5/6 ≠ 0 → warns ✓

Discrete Z(n) algorithm
------------------------
Discrete symmetry charges are stored as group elements (typically integers
like +1/−1 for Z2, or 1/2/.../n for Z_n cyclic charges).  The Lagrangian
term is invariant under Z_n if and only if the **product** of all field
parities equals the identity element (+1 for ±1 convention, or 0 mod n in
additive exponent convention).

For the ±1 (multiplicative) convention used in tests:
  - Multiply the parity values of all fields in the term (each raised to the
    number of times the field appears, respecting conjugation does NOT flip
    parity for discrete symmetries — parity is a Z_n eigenvalue, not a phase).
  - Check product == +1.  If not, emit DISCRETE_NONZERO.

Conjugation note for discrete symmetries: unlike U(1), complex conjugation of
a Z_2-even field still gives a Z_2-even field (parity is real).  So
``conj[H]`` has the same DMParity as ``H``.  We therefore do NOT negate the
discrete charge for conj-wrapped occurrences.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from .diagnostics import Diagnostic
from .tokenizer import extract_identifiers
from .charge_eval import evaluate
from .cwt import build_cwt, FieldRef, WeylRef

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_CONJ_RE = re.compile(r'conj\[([A-Za-z][A-Za-z0-9_]*)\]')

# Cache of per-identifier word-boundary patterns.
_IDENT_PAT_CACHE: Dict[str, re.Pattern] = {}


def _ident_pat(ident: str) -> re.Pattern:
    if ident not in _IDENT_PAT_CACHE:
        _IDENT_PAT_CACHE[ident] = re.compile(
            rf'(?<![A-Za-z0-9_])({re.escape(ident)})(?![A-Za-z0-9_])'
        )
    return _IDENT_PAT_CACHE[ident]


# ---------------------------------------------------------------------------
# Group-discovery helpers
# ---------------------------------------------------------------------------

def _u1_groups(spec: dict) -> List[str]:
    """Return the symbol names of all U(1) gauge groups."""
    return [
        g['symbol'] for g in spec.get('gauge_groups', [])
        if g['type'] == 'U(1)'
    ]


def _discrete_groups(spec: dict) -> List[Tuple[str, int]]:
    """Yield (name, modulus) for each Z(n) global symmetry."""
    result = []
    for g in spec.get('global_symmetries', []):
        t = g.get('type', '')
        m = re.match(r'^Z\((\d+)\)$', t)
        if m:
            result.append((g['name'], int(m.group(1))))
    return result


# ---------------------------------------------------------------------------
# Term-parsing helpers
# ---------------------------------------------------------------------------

def _conj_count_map(term: str) -> Dict[str, int]:
    """Map identifier → number of times it appears inside ``conj[…]``."""
    out: Dict[str, int] = {}
    for m in _CONJ_RE.finditer(term):
        sym = m.group(1)
        out[sym] = out.get(sym, 0) + 1
    return out


def _bare_count(term: str, ident: str) -> int:
    """Count occurrences of *ident* NOT inside ``conj[…]`` in *term*.

    Strategy: total word-boundary occurrences minus those inside conj[…].
    """
    total = len(_ident_pat(ident).findall(term))
    inside = sum(1 for m in _CONJ_RE.finditer(term) if m.group(1) == ident)
    return total - inside


def _total_count(term: str, ident: str) -> int:
    """Count all occurrences of *ident* in *term* (bare + inside conj)."""
    return len(_ident_pat(ident).findall(term))


def _field_for_ident(ident: str, cwt: dict, fields_by_name: dict) -> Optional[dict]:
    """Return the spec field dict for *ident* if it maps to a field, else None."""
    entry = cwt.get(ident)
    if isinstance(entry, FieldRef):
        return fields_by_name.get(entry.field_name)
    if isinstance(entry, WeylRef) and entry.field_name != '__builtin__':
        return fields_by_name.get(entry.field_name)
    return None


# ---------------------------------------------------------------------------
# U(1) charge summation
# ---------------------------------------------------------------------------

def _sum_u1_charges(
    term_str: str,
    idents: set,
    cwt: dict,
    fields_by_name: dict,
    params: set,
    sym: str,
) -> Fraction:
    """Return the net U(1) charge under group *sym* for a single term string.

    Complex conjugation (``conj[X]``) negates the U(1) charge contribution.
    Conjugated Weyl components (declared as ``conj[dR]`` in the spec) also
    carry a sign flip relative to the parent field's rep.
    """
    conj_map = _conj_count_map(term_str)
    total = Fraction(0)

    for ident in idents:
        if ident in params:
            continue  # parameters are gauge-invariant

        field = _field_for_ident(ident, cwt, fields_by_name)
        if field is None:
            continue

        raw = field.get('reps', {}).get(sym)
        if raw is None:
            continue

        val = evaluate(raw, A_name='A', A_value=0)
        if val is None:
            continue  # symbolic; cannot evaluate

        charge = Fraction(val)

        # Weyl component declared as conj[X] carries opposite U(1) charge.
        cwt_entry = cwt.get(ident)
        if isinstance(cwt_entry, WeylRef) and cwt_entry.conjugated:
            base_sign = -1
        else:
            base_sign = 1

        # Each conj-wrapped appearance negates the contribution.
        bare = _bare_count(term_str, ident)
        inside_conj = conj_map.get(ident, 0)
        net = bare - inside_conj

        total += charge * base_sign * net

    return total


# ---------------------------------------------------------------------------
# Discrete Z(n) charge check (multiplicative convention)
# ---------------------------------------------------------------------------

def _check_discrete_product(
    term_str: str,
    idents: set,
    cwt: dict,
    fields_by_name: dict,
    params: set,
    sym: str,
    modulus: int,
) -> bool:
    """Return True if the term conserves the Z(n) symmetry *sym*, False otherwise.

    Uses multiplicative parity semantics: the product of all field parities in
    the term must equal the identity element (+1 for ±1 convention).

    Discrete parities are real (Z_n eigenvalues), so ``conj[X]`` does NOT
    change the parity of X — we count all appearances of each field regardless
    of whether they are inside ``conj[…]``.
    """
    product = Fraction(1)
    any_charge_found = False

    for ident in idents:
        if ident in params:
            continue

        field = _field_for_ident(ident, cwt, fields_by_name)
        if field is None:
            continue

        raw = field.get('reps', {}).get(sym)
        if raw is None:
            continue

        val = evaluate(raw, A_name='A', A_value=0)
        if val is None:
            continue

        parity = Fraction(val)
        any_charge_found = True

        # Total appearances (bare + inside conj) — conjugation doesn't flip parity.
        count = _total_count(term_str, ident)

        # Raise parity to the power of the number of occurrences.
        product *= parity ** count

    if not any_charge_found:
        return True  # no charged fields found — trivially conserved

    # Product must equal +1 (the identity element of the parity group).
    # For Z2 with ±1: (-1)*(-1)=+1 → conserved; (-1)*(+1)=−1 → violated.
    return product == Fraction(1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_per_term_charges(spec: dict) -> List[Diagnostic]:
    """Stage 3a: check U(1) charge conservation per Lagrangian term."""
    return _check(spec, kind='u1')


def check_discrete_symmetry(spec: dict) -> List[Diagnostic]:
    """Stage 3b: check discrete (Z_n) charge conservation per Lagrangian term."""
    return _check(spec, kind='discrete')


def _check(spec: dict, *, kind: str) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    cwt = build_cwt(spec)
    fields_by_name = {
        f['name']: f
        for f in spec.get('fermions', []) + spec.get('scalars', [])
    }
    params = {p['name'] for p in spec.get('parameters', [])}

    if kind == 'u1':
        groups: List[Tuple[str, int]] = [(s, 0) for s in _u1_groups(spec)]
        diag_code = 'CHARGE_NONZERO'
    else:
        groups = _discrete_groups(spec)
        diag_code = 'DISCRETE_NONZERO'

    if not groups:
        return diags

    for bucket in ('hc', 'no_hc'):
        terms = spec.get('lagrangian', {}).get(bucket, []) or []
        for ti, t in enumerate(terms):
            term_str = t.get('term', '') if isinstance(t, dict) else str(t)
            idents = extract_identifiers(term_str)

            for sym, modulus in groups:
                if kind == 'u1':
                    total = _sum_u1_charges(
                        term_str, idents, cwt, fields_by_name, params, sym
                    )
                    if total != 0:
                        diags.append(Diagnostic(
                            stage=3, severity='warning', code=diag_code,
                            path=f'/lagrangian/{bucket}/{ti}/term',
                            message=(
                                f"U(1) {sym!r} charge not conserved: "
                                f"net charge {total} in term {term_str!r}"
                            ),
                        ))
                else:
                    conserved = _check_discrete_product(
                        term_str, idents, cwt, fields_by_name, params, sym, modulus
                    )
                    if not conserved:
                        diags.append(Diagnostic(
                            stage=3, severity='warning', code=diag_code,
                            path=f'/lagrangian/{bucket}/{ti}/term',
                            message=(
                                f"discrete symmetry {sym!r} not conserved "
                                f"in term {term_str!r}"
                            ),
                        ))

    return diags
