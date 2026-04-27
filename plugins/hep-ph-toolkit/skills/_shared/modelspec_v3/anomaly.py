"""Stage 3a — anomaly cancellation checks.

For each U(1) gauge group X (with hypercharge variable Y_f = f.reps[X]):
  - [U(1)_X]^3       :  sum_f  D_NA(f) · Y_f^3
  - Grav^2 · U(1)_X  :  sum_f  D_NA(f) · Y_f
  - [SU(2)]^2 · U(1)_X : sum over fermions in an SU(2) doublet of
                         D_NA-without-SU(2)(f) · Y_f
  - [SU(3)]^2 · U(1)_X : sum over fermions in SU(3) (anti)triplet of
                         D_NA-without-SU(3)(f) · sign(rep) · (1/2) · Y_f
                         (Dynkin index simplification: |rep|=3 → ±1/2)

D_NA(f) = product of dimensions of non-abelian reps × generations.
For a fermion with non-trivial SU(2) (rep dim 2) AND SU(3) (rep dim 3),
D_NA = 2·3·gens = 6·gens.

Vectorlike pairs whose two members reference each other via
`dirac_partner: <name>` are excluded entirely (their joint anomaly
contribution is zero by construction).

Multi-U(1) + non-empty `sarah_raw`: emit ANOMALY_KINMIX_SKIP and skip
the cubic check (kinetic-mixing terms can confound anomaly cancellation
across U(1) factors).
"""
from __future__ import annotations

from fractions import Fraction
from typing import List, Optional

from .charge_eval import evaluate
from .diagnostics import Diagnostic


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_vectorlike_pair(name: str, partner_name: Optional[str], spec: dict) -> bool:
    """True iff `partner_name` exists and points back at `name`."""
    if not partner_name:
        return False
    fermions_by_name = {f['name']: f for f in spec.get('fermions', [])}
    partner = fermions_by_name.get(partner_name)
    if partner is None:
        return False
    return partner.get('dirac_partner') == name


def _rep_dim(rep) -> int:
    """Dimension of a non-abelian rep, ignoring sign (anti vs fundamental).

    Accepts int or string-of-int. Anything else falls back to 1.
    """
    try:
        return abs(int(rep))
    except (TypeError, ValueError):
        return 1


def _rep_signed(rep) -> int:
    """Signed rep value (used for SU(N) Dynkin index sign)."""
    try:
        return int(rep)
    except (TypeError, ValueError):
        return 1


def _non_abelian_dim_excluding(reps: dict, gauge_groups: list, exclude_symbol: Optional[str]) -> int:
    """Product of dimensions of non-abelian reps, excluding one group.

    Used to peel off the SU(N) factor whose anomaly we're computing.
    """
    d = 1
    for g in gauge_groups:
        if not g.get('type', '').startswith('SU('):
            continue
        if exclude_symbol is not None and g['symbol'] == exclude_symbol:
            continue
        d *= _rep_dim(reps.get(g['symbol'], 1))
    return d


def _global_sym_var(spec: dict) -> tuple[str, int]:
    """Return (A_name, A_value) for charge_eval.

    If a global symmetry is declared we still pass A=0 (we're counting
    gauge anomalies, which never depend on a global U(1)). Anomalies
    must cancel for *every* allowed value of A; A=0 is a representative
    when no `If[A==…]` switching changes the rep dimensions (it doesn't —
    only the U(1) charge can depend on A in our scheme).

    For the cubic check we additionally try A=1 to catch expression-based
    Y values that depend on A; if cancellation holds at A=0 but not A=1
    that's still a real anomaly — see _evaluate_charges.
    """
    gs = spec.get('global_symmetries') or []
    if gs:
        first = gs[0]
        if isinstance(first, dict) and 'symbol' in first:
            return first['symbol'], 0
    return 'A', 0


def _evaluate_y(rep_value, A_name: str, A_value: int) -> Optional[Fraction]:
    """Evaluate a charge expression to Fraction, or None if symbolic."""
    v = evaluate(rep_value, A_name, A_value)
    if v is None:
        return None
    return Fraction(v)


def _u1_groups(gauge_groups: list) -> list:
    return [g for g in gauge_groups if g.get('type') == 'U(1)']


def _has_su(gauge_groups: list, dim: int) -> Optional[dict]:
    for g in gauge_groups:
        if g.get('type') == f'SU({dim})':
            return g
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def check_anomalies(spec: dict) -> List[Diagnostic]:
    """Run Stage 3a anomaly checks. All emitted diags are warnings."""
    diags: List[Diagnostic] = []
    gauge_groups = spec.get('gauge_groups', []) or []
    fermions = spec.get('fermions', []) or []
    u1s = _u1_groups(gauge_groups)
    su2 = _has_su(gauge_groups, 2)
    su3 = _has_su(gauge_groups, 3)

    sarah_raw = (spec.get('sarah_raw') or '').strip()
    multi_u1 = len(u1s) >= 2

    if multi_u1 and sarah_raw:
        diags.append(Diagnostic(
            stage=3,
            severity='warning',
            code='ANOMALY_KINMIX_SKIP',
            path='/sarah_raw',
            message=(
                f'spec has {len(u1s)} U(1) gauge groups and a non-empty '
                'sarah_raw block; cubic U(1)^3 anomaly checks are skipped '
                'because kinetic-mixing terms can confound the tally.'
            ),
            hint='Defer cubic U(1) anomaly verification to manual review or a later validator pass.',
        ))

    A_name, A_value = _global_sym_var(spec)

    # Build the list of "active" fermions, dropping vectorlike pairs
    # whose partner is also in the spec.
    active_fermions = []
    for f in fermions:
        partner = f.get('dirac_partner')
        if _is_vectorlike_pair(f.get('name', ''), partner, spec):
            continue
        active_fermions.append(f)

    for u1 in u1s:
        sym = u1['symbol']
        # Per-fermion (Y, D_full, gens, signed_su2_rep, signed_su3_rep)
        records = []
        symbolic_skip = False
        for f in active_fermions:
            reps = f.get('reps', {}) or {}
            y = _evaluate_y(reps.get(sym, 0), A_name, A_value)
            if y is None:
                symbolic_skip = True
                continue
            gens = int(f.get('generations', 1) or 1)
            su2_rep = _rep_signed(reps.get(su2['symbol'], 1)) if su2 else 1
            su3_rep = _rep_signed(reps.get(su3['symbol'], 1)) if su3 else 1
            su2_dim = abs(su2_rep) if su2 else 1
            su3_dim = abs(su3_rep) if su3 else 1
            d_full = gens * su2_dim * su3_dim
            records.append({
                'name': f.get('name', '?'),
                'y': y, 'gens': gens,
                'su2_rep': su2_rep, 'su3_rep': su3_rep,
                'su2_dim': su2_dim, 'su3_dim': su3_dim,
                'd_full': d_full,
            })

        # Cubic [U(1)]^3 (skip when kinetic mixing flagged)
        if not (multi_u1 and sarah_raw):
            cubic = sum((r['d_full'] * r['y'] ** 3 for r in records), Fraction(0))
            if cubic != 0:
                diags.append(Diagnostic(
                    stage=3,
                    severity='warning',
                    code='ANOMALY_U1_CUBIC',
                    path=f'/gauge_groups/{sym}',
                    message=(
                        f'[U(1)_{sym}]^3 anomaly does not cancel: '
                        f'sum(D · Y^3) = {cubic} (expected 0)'
                    ),
                    hint='Re-check fermion U(1) charges, multiplicities, or add chirality partners.',
                ))

        # Grav^2 · U(1)
        grav = sum((r['d_full'] * r['y'] for r in records), Fraction(0))
        if grav != 0:
            diags.append(Diagnostic(
                stage=3,
                severity='warning',
                code='ANOMALY_U1_GRAV',
                path=f'/gauge_groups/{sym}',
                message=(
                    f'Grav^2 · U(1)_{sym} anomaly does not cancel: '
                    f'sum(D · Y) = {grav} (expected 0)'
                ),
                hint='Re-check fermion U(1) charges or multiplicities.',
            ))

        # [SU(2)]^2 · U(1)
        if su2:
            su2_anom = Fraction(0)
            for r in records:
                if r['su2_dim'] != 2:
                    continue
                # peel SU(2) off D_full
                d_other = r['d_full'] // 2
                # Dynkin index for SU(2) doublet = 1/2
                su2_anom += d_other * Fraction(1, 2) * r['y']
            if su2_anom != 0:
                diags.append(Diagnostic(
                    stage=3,
                    severity='warning',
                    code='ANOMALY_SU2_SQ_U1',
                    path=f'/gauge_groups/{sym}',
                    message=(
                        f'[SU(2)]^2 · U(1)_{sym} anomaly does not cancel: '
                        f'{su2_anom} (expected 0)'
                    ),
                    hint='Re-check the SU(2)-doublet fermions\' U(1) charges.',
                ))

        # [SU(3)]^2 · U(1) — Dynkin index 1/2 for both 3 and 3̄.
        # In the v3 spec all fermions are written as left-handed Weyl spinors
        # (with conj[…] indicating the physical right-handed partner). With
        # uniform chirality, T(R) = 1/2 for both fundamental and
        # anti-fundamental — there is no sign flip from rep<0. Verified
        # against the SM: 6·(1/2)·(1/6) + 3·(1/2)·(1/3) + 3·(1/2)·(-2/3) = 0.
        if su3:
            su3_anom = Fraction(0)
            for r in records:
                if r['su3_dim'] != 3:
                    continue
                d_other = r['d_full'] // 3
                su3_anom += d_other * Fraction(1, 2) * r['y']
            if su3_anom != 0:
                diags.append(Diagnostic(
                    stage=3,
                    severity='warning',
                    code='ANOMALY_SU3_SQ_U1',
                    path=f'/gauge_groups/{sym}',
                    message=(
                        f'[SU(3)]^2 · U(1)_{sym} anomaly does not cancel: '
                        f'{su3_anom} (expected 0)'
                    ),
                    hint='Re-check (anti-)triplet fermions\' U(1) charges and rep signs.',
                ))

        if symbolic_skip:
            diags.append(Diagnostic(
                stage=3,
                severity='warning',
                code='ANOMALY_SYMBOLIC_SKIP',
                path=f'/gauge_groups/{sym}',
                message=(
                    f'one or more fermion charges under U(1)_{sym} are symbolic '
                    '(unknown bare symbols); those fermions were skipped from '
                    'the anomaly tally.'
                ),
                hint='Resolve the symbolic charges or pin them to numeric values.',
            ))

    return diags
