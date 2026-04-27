"""Render LagHC and LagNoHC."""
from typing import List


def _term_strs(items) -> List[str]:
    """Extract the term string from each entry (dict with 'term' or bare str)."""
    out = []
    for t in items or []:
        if isinstance(t, dict):
            out.append(t.get('term', ''))
        else:
            out.append(str(t))
    return [s for s in out if s.strip()]


def render_lagrangian(spec: dict) -> str:
    lag = spec.get('lagrangian', {}) or {}
    hc_terms = _term_strs(lag.get('hc'))
    no_hc_terms = _term_strs(lag.get('no_hc'))

    if no_hc_terms:
        no_hc_line = f'LagNoHC = {" ".join(no_hc_terms)};'
    else:
        no_hc_line = 'LagNoHC = 0;'

    if hc_terms:
        hc_line = f'LagHC = -({" + ".join(hc_terms)});'
    else:
        hc_line = 'LagHC = 0;'

    return no_hc_line + '\n\n' + hc_line + '\n'
