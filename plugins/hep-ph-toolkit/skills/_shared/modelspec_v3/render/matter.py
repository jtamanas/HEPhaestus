"""Render FermionFields, ScalarFields, RealScalars."""


def _format_components(raw):
    """Return the component cell content for a Fermion/Scalar entry.

    raw can be: str (bare or 'conj[X]') OR list of strings.
    Output: 'X' for str, '{a}' for list of 1, '{a, b}' for list of >=2.
    """
    if isinstance(raw, str):
        return raw
    return '{' + ', '.join(raw) + '}'


def _format_charge(c):
    """Format a charge value for the .m output. Accepts int, float, or str."""
    return str(c)


def _row_columns(field, gauge_groups, globals_):
    """Build the column list for one Fermion/Scalar entry."""
    cols = [
        field['name'],
        str(field['generations']),
        _format_components(field['components']),
    ]
    reps = field.get('reps', {})
    for g in gauge_groups:
        cols.append(_format_charge(reps.get(g['symbol'], 1)))
    for gs in globals_:
        cols.append(_format_charge(reps.get(gs['name'], 1)))
    return cols


def _render(field_kind: str, fields, gauge_groups, globals_):
    """Common formatter for FermionFields[[i]] / ScalarFields[[i]] lines."""
    lines = []
    for i, f in enumerate(fields, 1):
        cols = _row_columns(f, gauge_groups, globals_)
        lines.append(f'{field_kind}[[{i}]] = {{{", ".join(cols)}}};')
    return '\n'.join(lines)


def render_fermions(spec: dict) -> str:
    """Return the FermionFields block as a string (newline-terminated)."""
    body = _render(
        'FermionFields',
        spec.get('fermions', []),
        spec.get('gauge_groups', []),
        spec.get('global_symmetries', []),
    )
    return body + '\n'


def render_scalars(spec: dict) -> str:
    """Return the ScalarFields block, plus RealScalars if any, newline-terminated."""
    body = _render(
        'ScalarFields',
        spec.get('scalars', []),
        spec.get('gauge_groups', []),
        spec.get('global_symmetries', []),
    )
    parts = [body]
    real_names = [s['name'] for s in spec.get('scalars', []) if s.get('real')]
    if real_names:
        parts.append('')
        parts.append(f'RealScalars = {{{", ".join(real_names)}}};')
    return '\n'.join(parts) + '\n'
