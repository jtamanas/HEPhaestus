"""Stage 2: ref integrity + reserved names + canonical Weyl table."""
from typing import List, Set

from .diagnostics import Diagnostic
from .reserved import (
    MATHEMATICA_BUILTINS, RENDERER_ALIASES, SARAH_RESERVED, is_reserved
)
from .cwt import build_cwt
from .tokenizer import extract_identifiers


def validate_refs(spec: dict) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    cwt = build_cwt(spec)
    declared_params: Set[str] = {p['name'] for p in spec.get('parameters', [])}

    diags.extend(_check_reserved_and_collision(spec))
    diags.extend(_check_ewsb_refs(spec, cwt))
    diags.extend(_check_lagrangian_refs(spec, cwt, declared_params))
    return diags


def _is_reserved_field(name: str) -> bool:
    """Reserved check for fermion/scalar names and gauge symbols.

    Single-letter names (q, H, B, G, …) are conventional in HEP and are
    NOT treated as reserved for field/gauge declarations.  Only Mathematica
    builtins and SARAH structural keywords are blocked.
    """
    if name in RENDERER_ALIASES:
        return False
    return name in MATHEMATICA_BUILTINS or name in SARAH_RESERVED


def _check_reserved_and_collision(spec) -> List[Diagnostic]:
    seen: dict = {}   # name -> path where first declared
    diags = []
    # is_reserved_fn: parameters get the full check (including SINGLE_LETTERS);
    # other collections only block Mathematica/SARAH keywords, not bare letters.
    collections = [
        ('parameters',        spec.get('parameters', []),        'name', is_reserved),
        ('fermions',          spec.get('fermions', []),           'name', _is_reserved_field),
        ('scalars',           spec.get('scalars', []),            'name', _is_reserved_field),
        ('gauge_groups',      spec.get('gauge_groups', []),       'symbol', _is_reserved_field),
        ('global_symmetries', spec.get('global_symmetries', []), 'name',   _is_reserved_field),
    ]
    for collection_path, items, key, reserved_fn in collections:
        for i, it in enumerate(items):
            name = it.get(key)
            if name is None:
                continue
            path = f'/{collection_path}/{i}/{key}'
            if reserved_fn(name):
                diags.append(Diagnostic(
                    stage=2, severity='error', code='NAME_RESERVED',
                    path=path,
                    message=f"name {name!r} is reserved",
                ))
            elif name in seen:
                diags.append(Diagnostic(
                    stage=2, severity='error', code='NAME_COLLISION',
                    path=path,
                    message=f"name {name!r} already declared at {seen[name]}",
                ))
            else:
                seen[name] = path
    return diags


def _check_ewsb_refs(spec, cwt) -> List[Diagnostic]:
    diags = []
    ewsb = spec.get('ewsb', {})

    # vevs[].component
    for i, v in enumerate(ewsb.get('vevs', [])):
        sym = v.get('component')
        if sym in (None, 0):
            continue
        if sym not in cwt:
            diags.append(_undeclared_diag(f'/ewsb/vevs/{i}/component', sym, cwt))

    # mixing_sector entries
    for i, m in enumerate(ewsb.get('mixing_sector', [])):
        kind = m.get('kind')
        if kind in ('majorana', 'scalar'):
            for j, w in enumerate(m.get('weyls', []) or []):
                if not _resolves(w, cwt):
                    diags.append(_undeclared_diag(
                        f'/ewsb/mixing_sector/{i}/weyls/{j}', w, cwt))
        elif kind == 'dirac':
            for slot in ('lh', 'rh'):
                for j, w in enumerate(m.get(slot, []) or []):
                    if w == 0:
                        continue
                    if not _resolves(w, cwt):
                        diags.append(_undeclared_diag(
                            f'/ewsb/mixing_sector/{i}/{slot}/{j}', w, cwt))

    # dirac_spinors_pre_ewsb / dirac_spinors_post_ewsb
    for block in ('dirac_spinors_pre_ewsb', 'dirac_spinors_post_ewsb'):
        for i, sp in enumerate(ewsb.get(block, []) or []):
            for j, c in enumerate(sp.get('components', []) or []):
                if c == 0:
                    continue
                if not _resolves(c, cwt):
                    diags.append(_undeclared_diag(
                        f'/ewsb/{block}/{i}/components/{j}', c, cwt))
    return diags


def _resolves(sym, cwt) -> bool:
    """True if ``sym`` is a legal Weyl reference (bare, indexed, or ``conj[X]``)."""
    if sym is None or sym == 0:
        return True
    if not isinstance(sym, str):
        return False
    if sym in cwt:
        return True
    if sym.startswith('conj[') and sym.endswith(']'):
        inner = sym[5:-1]
        return inner in cwt
    return False


def _check_lagrangian_refs(spec, cwt, params) -> List[Diagnostic]:
    diags = []
    for bucket in ('hc', 'no_hc'):
        for i, t in enumerate(spec.get('lagrangian', {}).get(bucket, []) or []):
            term = t.get('term', '') if isinstance(t, dict) else str(t)
            for ident in extract_identifiers(term):
                if ident in cwt or ident in params:
                    continue
                diags.append(Diagnostic(
                    stage=2, severity='error', code='REF_UNDECLARED',
                    path=f'/lagrangian/{bucket}/{i}/term',
                    message=f"undeclared symbol {ident!r} in term",
                    hint=_levenshtein_hint(ident, cwt, params),
                ))
    return diags


def _undeclared_diag(path, sym, cwt) -> Diagnostic:
    return Diagnostic(
        stage=2, severity='error', code='REF_UNDECLARED',
        path=path,
        message=f"undeclared Weyl symbol {sym!r}",
        hint=_levenshtein_hint(sym, cwt, set()),
    )


def _levenshtein_hint(s, cwt, params):
    candidates = [k for k in (set(cwt) | params)
                  if isinstance(k, str) and '[' not in k]
    if not candidates:
        return None
    scored = sorted(candidates, key=lambda c: _lev(s, c))[:3]
    return f"did you mean: {', '.join(scored)}?"


def _lev(a: str, b: str) -> int:
    """Iterative Levenshtein distance."""
    if a == b:
        return 0
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j-1] + 1,
                        prev + (0 if a[i-1] == b[j-1] else 1))
            prev = cur
    return dp[n]
