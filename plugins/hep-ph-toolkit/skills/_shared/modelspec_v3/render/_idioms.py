"""Shared rendering helpers (small)."""
import re


def gauge_type_to_sarah(g_type: str) -> str:
    """Convert gauge type string to SARAH notation.

    U(1) -> U[1], SU(2) -> SU[2], etc.
    """
    m = re.match(r'^(SU|U)\((\d+)\)$', g_type)
    if not m:
        raise ValueError(f'unknown gauge type {g_type!r}')
    base, n = m.group(1), m.group(2)
    return f'{base}[{n}]'


def model_name(spec: dict) -> str:
    return spec['model']['name']


def fmt_bool(b: bool) -> str:
    return 'True' if b else 'False'


def trivial_global_charge(global_type: str) -> int:
    """Return the trivial charge for a gauge-boson-like row under a global symmetry.

    Discrete Z(n) -> 1; U(1) -> 0.
    """
    if global_type.startswith('Z('):
        return 1
    if global_type == 'U(1)':
        return 0
    return 0
