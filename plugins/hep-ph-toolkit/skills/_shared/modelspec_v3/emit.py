"""Diagnostic emitters."""
import json
from typing import List
from .diagnostics import Diagnostic


def emit_json(diags: List[Diagnostic]) -> str:
    """One JSON object per line."""
    return '\n'.join(json.dumps(d.to_dict()) for d in diags)


def emit_pretty(diags: List[Diagnostic]) -> str:
    """Human-readable. One line per diagnostic plus a trailing summary."""
    lines = []
    n_err = sum(1 for d in diags if d.severity == 'error')
    n_warn = sum(1 for d in diags if d.severity == 'warning')

    for d in diags:
        marker = 'ERROR  ' if d.severity == 'error' else 'warning'
        line = f'[stage {d.stage}] {marker} {d.code} {d.path}: {d.message}'
        lines.append(line)
        if d.hint:
            lines.append(f'    hint: {d.hint}')

    if not diags:
        lines.append('0 errors, 0 warnings')
    else:
        lines.append(f'\n{n_err} error{"s" if n_err != 1 else ""}, {n_warn} warning{"s" if n_warn != 1 else ""}')

    return '\n'.join(lines)
