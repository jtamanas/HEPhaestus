"""Render EWSB DEFINITION blocks.

Emits the five SARAH ``DEFINITION[...][...]`` sections derived from
``spec.ewsb``:

  * ``DEFINITION[GaugeES][MatterSector]``  (mixing entries with stage='GaugeES')
  * ``DEFINITION[EWSB][MatterSector]``     (mixing entries with stage='EWSB')
  * ``DEFINITION[GaugeES][DiracSpinors]``  (dirac_spinors_pre_ewsb)
  * ``DEFINITION[EWSB][GaugeSector]``      (gauge_sector)
  * ``DEFINITION[EWSB][VEVs]``             (vevs)
  * ``DEFINITION[EWSB][Phases]``           (phases)
  * ``DEFINITION[EWSB][DiracSpinors]``     (dirac_spinors_post_ewsb)

Empty sections are omitted entirely. Block ordering matches the
``singlet_doublet`` golden:

    EWSB MatterSector
    GaugeES DiracSpinors
    EWSB GaugeSector
    EWSB VEVs
    EWSB Phases
    EWSB DiracSpinors

When a ``GaugeES`` MatterSector exists (e.g. scotogenic-style scalar
mixing without a VEV) it is emitted before any of the EWSB-stage blocks.

Schema field names (from schema.json) used here:
  Vev: component, vev, goldstone, physical
  GaugeMix: rotate, to, matrix
  MixingOutput: name, mixing
  MixingDirac: kind, stage, lh, rh, outputs={lh, rh}
  MixingMajorana / MixingScalar: kind, stage, weyls, output
  Phase: field, phase
  Spinor: name, components (length-2 list)
"""
from typing import Iterable, List


def render_ewsb(spec: dict) -> str:
    """Render all EWSB blocks. Returns concatenated text.

    Sections are separated by a blank line. The result ends with a
    newline if any block is emitted; otherwise an empty string is returned.
    """
    ewsb = spec.get('ewsb', {}) or {}

    mixings = ewsb.get('mixing_sector') or []
    gauge_es_mixings = [m for m in mixings if m.get('stage', 'EWSB') == 'GaugeES']
    ewsb_mixings = [m for m in mixings if m.get('stage', 'EWSB') == 'EWSB']

    parts: List[str] = []

    # 1. GaugeES MatterSector (if any) — emit first.
    if gauge_es_mixings:
        parts.append(_render_matter_sector(gauge_es_mixings, stage='GaugeES'))

    # 2. EWSB MatterSector
    if ewsb_mixings:
        parts.append(_render_matter_sector(ewsb_mixings, stage='EWSB'))

    # 3. GaugeES DiracSpinors (pre-EWSB)
    pre = ewsb.get('dirac_spinors_pre_ewsb') or []
    if pre:
        parts.append(_render_dirac_spinors(pre, stage='GaugeES'))

    # 4. GaugeSector (EWSB)
    gauge = ewsb.get('gauge_sector') or []
    if gauge:
        parts.append(_render_gauge_sector(gauge))

    # 5. VEVs (EWSB)
    vevs = ewsb.get('vevs') or []
    if vevs:
        parts.append(_render_vevs(vevs))

    # 6. Phases (EWSB)
    phases = ewsb.get('phases') or []
    if phases:
        parts.append(_render_phases(phases))

    # 7. EWSB DiracSpinors (post-EWSB)
    post = ewsb.get('dirac_spinors_post_ewsb') or []
    if post:
        parts.append(_render_dirac_spinors(post, stage='EWSB'))

    if not parts:
        return ''
    return '\n\n'.join(parts) + '\n'


# ---------------------------------------------------------------------------
# block renderers
# ---------------------------------------------------------------------------

def _render_matter_sector(mixings: Iterable[dict], stage: str) -> str:
    rows = [_render_mixing_entry(m) for m in mixings]
    body = ',\n  '.join(rows)
    return f'DEFINITION[{stage}][MatterSector] = {{\n  {body}\n}};'


def _render_mixing_entry(m: dict) -> str:
    kind = m.get('kind')
    if kind == 'dirac':
        lh = '{' + ', '.join(_fmt(x) for x in m.get('lh', [])) + '}'
        rh = '{' + ', '.join(_fmt(x) for x in m.get('rh', [])) + '}'
        outs = m.get('outputs') or {}
        out_lh = _render_mixing_output(outs.get('lh', {}))
        out_rh = _render_mixing_output(outs.get('rh', {}))
        return f'{{{{{lh}, {rh}}}, {{{out_lh}, {out_rh}}}}}'
    if kind in ('majorana', 'scalar'):
        weyls = '{' + ', '.join(_fmt(x) for x in m.get('weyls', [])) + '}'
        out = _render_mixing_output(m.get('output', {}))
        return f'{{{weyls}, {out}}}'
    raise ValueError(f'unknown mixing kind: {kind!r}')


def _render_mixing_output(out: dict) -> str:
    return f"{{{out.get('name', '')}, {out.get('mixing', '')}}}"


def _render_dirac_spinors(items: Iterable[dict], stage: str) -> str:
    lines = []
    for d in items:
        comps = ', '.join(_fmt(c) for c in d.get('components', []))
        lines.append(f"  {d['name']} -> {{{comps}}}")
    body = ',\n'.join(lines)
    return f'DEFINITION[{stage}][DiracSpinors] = {{\n{body}\n}};'


def _render_gauge_sector(items: Iterable[dict]) -> str:
    lines = []
    for g in items:
        rotate = '{' + ', '.join(_fmt(x) for x in g.get('rotate', [])) + '}'
        to = '{' + ', '.join(_fmt(x) for x in g.get('to', [])) + '}'
        lines.append(f"  {{{rotate}, {to}, {g.get('matrix', '')}}}")
    body = ',\n'.join(lines)
    return f'DEFINITION[EWSB][GaugeSector] = {{\n{body}\n}};'


def _render_vevs(items: Iterable[dict]) -> str:
    lines = []
    for v in items:
        comp = v['component']
        vev_pair = _pair(v.get('vev', [0, 0]))
        gs_pair = _pair(v.get('goldstone', [0, 0]))
        phys_pair = _pair(v.get('physical', [0, 0]))
        lines.append(f'  {{{comp}, {vev_pair}, {gs_pair}, {phys_pair}}}')
    body = ',\n'.join(lines)
    return f'DEFINITION[EWSB][VEVs] = {{\n{body}\n}};'


def _render_phases(items: Iterable[dict]) -> str:
    lines = [f"  {{{p['field']}, {p['phase']}}}" for p in items]
    body = ',\n'.join(lines)
    return f'DEFINITION[EWSB][Phases] = {{\n{body}\n}};'


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _fmt(x) -> str:
    """Format a scalar for Mathematica output.

    Strings pass through unchanged. Integers (including the ``0`` placeholder
    used in spinor components / Goldstone slots) render as their decimal form.
    """
    return str(x)


def _pair(p) -> str:
    """Render a length-2 pair as ``{a, b}``."""
    a, b = p[0], p[1]
    return f'{{{_fmt(a)}, {_fmt(b)}}}'
