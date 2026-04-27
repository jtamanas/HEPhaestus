"""Render Gauge[[i]] tuples."""
from ._idioms import gauge_type_to_sarah, fmt_bool, trivial_global_charge


def render_gauge(spec: dict) -> str:
    globals_ = spec.get('global_symmetries', [])
    trailing = [trivial_global_charge(g['type']) for g in globals_]
    lines = []
    for i, g in enumerate(spec.get('gauge_groups', []), 1):
        cols = [
            g['symbol'],
            gauge_type_to_sarah(g['type']),
            g['label'],
            g['coupling'],
            fmt_bool(g.get('ssb', False)),
        ] + [str(c) for c in trailing]
        lines.append(f'Gauge[[{i}]] = {{{", ".join(cols)}}};')
    return '\n'.join(lines) + '\n'
