"""Canonical Weyl Table — the symbol resolution source of truth."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WeylRef:
    field_name: str
    gen: Optional[int]
    component: str
    conjugated: bool


@dataclass(frozen=True)
class FieldRef:
    field_name: str


@dataclass(frozen=True)
class MixingOutputRef:
    """Represents a mass-eigenstate name produced by a mixing_sector rotation.

    These appear as component references in ``dirac_spinors_post_ewsb`` and
    are not Weyl fields themselves.  They carry no gauge charges for the purpose
    of per-term U(1) checks (charge conservation is verified on the gauge-ES
    side; the mass-eigenstate basis is unitary and trivially charge-neutral).
    """
    output_name: str


_CONJ_RE = re.compile(r'^conj\[([A-Za-z][A-Za-z0-9_]*)\]$')

# SARAH-conventional gauge boson symbols. Seeded into every CWT.
_GAUGE_BUILTIN = ('VB', 'VWB[1]', 'VWB[2]', 'VWB[3]', 'VWp', 'VG', 'VP', 'VZ')


def build_cwt(spec: dict) -> dict:
    """Build the Canonical Weyl Table from a parsed ModelSpec dict.

    Returns a dict mapping every legal symbol reference to a WeylRef or
    FieldRef.  Keys include:
      - bare component names  (e.g. 'uL', 'dR')
      - indexed component names  (e.g. 'uL[1]', 'dR[2]')
      - field names as FieldRef aliases  (e.g. 'q', 'LL')
      - builtin gauge boson tokens (seeded unconditionally)
    """
    cwt: dict = {}
    for f in spec.get('fermions', []):
        _add_field(cwt, f)
    for s in spec.get('scalars', []):
        _add_field(cwt, s)
    for tok in _GAUGE_BUILTIN:
        cwt[tok] = WeylRef(field_name='__builtin__', gen=None,
                           component=tok, conjugated=False)

    # Seed mixing-sector output names so that dirac_spinors_post_ewsb can
    # reference them (e.g. DL, DR, UL, UR from quark mixing).
    for m in (spec.get('ewsb', {}) or {}).get('mixing_sector', []) or []:
        kind = m.get('kind')
        if kind == 'dirac':
            outs = m.get('outputs') or {}
            for side in ('lh', 'rh'):
                out = outs.get(side) or {}
                oname = out.get('name')
                if oname and oname not in cwt:
                    cwt[oname] = MixingOutputRef(oname)
        elif kind in ('majorana', 'scalar'):
            out = m.get('output') or {}
            oname = out.get('name')
            if oname and oname not in cwt:
                cwt[oname] = MixingOutputRef(oname)

    # Seed VEV-produced symbols (physical eigenstates and Goldstone bosons)
    # so that scalar mixing_sector weyls[] can reference them.
    # e.g. H10 → {vd, 1/Sqrt[2]}, goldstone: [Ah1, ...], physical: [hh1, ...]
    for v in (spec.get('ewsb', {}) or {}).get('vevs', []) or []:
        for slot in ('goldstone', 'physical'):
            pair = v.get(slot) or []
            if pair:
                sym = pair[0]
                if isinstance(sym, str) and sym and sym not in cwt:
                    cwt[sym] = MixingOutputRef(sym)

    return cwt


def _add_field(cwt: dict, f: dict) -> None:
    """Populate CWT entries for a single fermion or scalar field dict."""
    name = f['name']
    gens = f['generations']
    raw = f['components']

    # `conj[X]` form — the field is the conjugate of component X
    m = _CONJ_RE.match(raw) if isinstance(raw, str) else None
    if m:
        components = [m.group(1)]   # the inner symbol
        conjugated = True
    elif isinstance(raw, str):
        components = [raw]
        conjugated = False
    else:
        components = list(raw)
        conjugated = False

    for comp in components:
        # Indexed forms: comp[1], comp[2], ..., comp[gens]
        for g in range(1, gens + 1):
            cwt[f'{comp}[{g}]'] = WeylRef(name, g, comp, conjugated)
        # Bare (generation-unspecified) form
        cwt[comp] = WeylRef(name, None, comp, conjugated)

    # Field-name alias
    cwt[name] = FieldRef(name)
