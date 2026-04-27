"""Render orchestrator. Combines section renderers into the three .m files."""
from typing import Dict
from .header import render_header
from .gauge import render_gauge
from .matter import render_fermions, render_scalars
from .lagrangian import render_lagrangian
from .ewsb import render_ewsb
from .parameters import render_parameters_m
from .particles import render_particles_m


def render_all(spec: dict) -> Dict[str, str]:
    """Produce the three SARAH .m files. Returns dict mapping filename → contents."""
    name = spec['model']['name']

    # Main .m file: header + gauge + matter + lagrangian + EWSB
    main_parts = [
        render_header(spec).rstrip(),
        '',
        render_gauge(spec).rstrip(),
        '',
        render_fermions(spec).rstrip(),
        '',
        render_scalars(spec).rstrip(),
        '',
        render_lagrangian(spec).rstrip(),
    ]
    ewsb_text = render_ewsb(spec).rstrip()
    if ewsb_text:
        main_parts.append('')
        main_parts.append(ewsb_text)
    main = '\n'.join(p for p in main_parts if p is not None) + '\n'

    return {
        f'{name}.m': main,
        'parameters.m': render_parameters_m(spec),
        'particles.m': render_particles_m(spec),
    }
