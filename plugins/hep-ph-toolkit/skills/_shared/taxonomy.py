"""
taxonomy.py — WS1 S12: Public taxonomy reader API for ModelSpec v2.

Three public functions consumed by WS2 (capability matrix), WS3 (router),
and WS4 (disclosure machinery):
  - read_axes(spec: dict) -> AxisReport
  - read_dm_phenomenology(spec: dict) -> DMPhenomenology
  - analytic_exception_triggered(spec: dict) -> bool

All functions are pass-through readers: they extract structured data from
a ModelSpec dict (already loaded via yaml.safe_load) without inferring
physics beyond what is declared in the spec. Per synthesis §1: no inference.

Public exception:
  - SchemaVersionError: raised when spec._schema_version != 2.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SchemaVersionError(ValueError):
    """Raised when the spec does not carry _schema_version: 2."""
    pass


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AxisReport:
    """Taxonomy axes A1–A8 extracted from a v2 ModelSpec.

    All fields are verbatim reads from the spec; no physics inference.
    """
    a1: str                     # Gauge extension class (synthesis §3 A1)
    a2: list[dict[str, Any]]    # Symmetry-breaking patterns for non-SM gauge factors
    a3: dict[str, bool]         # Fermion projections
    a4: dict[str, Any]          # Scalar sector topology
    a5: list[dict[str, Any]]    # Global symmetry catalogue
    a6: list[str]               # Portal couplings
    a7: dict[str, Any]          # Extra colored matter
    a8: str                     # Authoring status


@dataclass(frozen=True)
class DMCandidate:
    """A single DM candidate entry from dm_phenomenology.candidates."""
    name: str
    field_type: str
    uv_provenance: str
    mass_parameter: Optional[str]
    cp: Optional[str]
    mediator_field: Optional[str]
    mediator_regime: str
    stabilisation_mechanism: str
    blind_spot_reference: Optional[str]
    multi_component_partner: Optional[str]
    coupled: Optional[bool]
    # Any extra keys are stored in extras for forward-compat.
    extras: dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass(frozen=True)
class DMPhenomenology:
    """Parsed dm_phenomenology block."""
    candidates: list[DMCandidate]


# ---------------------------------------------------------------------------
# Private axis extractors
# ---------------------------------------------------------------------------

_SM_KINDS = {"hypercharge", "left", "color"}

# Map from non-SM gauge kinds to A1 class labels per synthesis §3 A1.
# Note: "dark" is NOT in this table because it requires group-level dispatch
# (dark U(1) → "SM + extra U(1)"; dark SU(N) → "SM + extra SU(N)").
_NON_SM_KIND_LABELS = {
    "mirror": "SM + mirror",
    "B-L": "SM + extra U(1)",
    "X": "SM + extra U(1)",
    "embedding": "Non-SM-embedding",
}


def _a1_label_for_gauge_factor(g: dict) -> str:
    """Return the A1 label for a single non-SM gauge factor.

    Dispatches on (kind, group) — the kind=dark case requires group-level
    disambiguation between abelian (U1 → 'SM + extra U(1)') and non-abelian
    (SU(N) → 'SM + extra SU(N)') extensions.  All other kinds look up
    _NON_SM_KIND_LABELS and fall back to 'SM + extra SU(N)'.
    """
    kind = g.get("kind", "")
    group = g.get("group", "")

    if kind == "dark":
        # Abelian dark gauge group: group starts with "U" (U1, U(1), etc.)
        if group.upper().startswith("U"):
            return "SM + extra U(1)"
        return "SM + extra SU(N)"

    return _NON_SM_KIND_LABELS.get(kind, "SM + extra SU(N)")


def _a1_gauge_extension_class(spec: dict) -> str:
    """A1: gauge extension class.

    Returns one of: 'SM', 'SM + extra U(1)', 'SM + extra SU(N)',
    'SM + extra mixed', 'SM + mirror', 'Non-SM-embedding'.

    ws1-iter3 N1 fix: dispatches on (kind, group) not kind alone, so that
    kind=dark + group=U1 correctly returns 'SM + extra U(1)' rather than
    'SM + extra SU(N)'.
    """
    non_sm = [g for g in spec.get("gauge_groups", []) if g.get("kind") not in _SM_KINDS]
    if not non_sm:
        return "SM"
    if len(non_sm) == 1:
        return _a1_label_for_gauge_factor(non_sm[0])
    # Multiple non-SM factors: all same label → return that label; else mixed.
    labels = {_a1_label_for_gauge_factor(g) for g in non_sm}
    if len(labels) == 1:
        return next(iter(labels))
    return "SM + extra mixed"


def _a2_symmetry_breaking_patterns(spec: dict) -> list[dict[str, Any]]:
    """A2: symmetry-breaking pattern list for non-SM gauge factors."""
    result = []
    for g in spec.get("gauge_groups", []):
        if g.get("kind") in _SM_KINDS:
            continue
        sb = g.get("symmetry_breaking", {})
        entry: dict[str, Any] = {
            "factor": g.get("symbol"),
            "kind": g.get("kind"),
            "pattern": sb.get("pattern") if isinstance(sb, dict) else None,
        }
        # Include optional sub-fields if present.
        if isinstance(sb, dict):
            for k in ("residual_subgroup", "breaking_scalar", "vev_parameter"):
                if k in sb:
                    entry[k] = sb[k]
        result.append(entry)
    return result


def _a3_fermion_projections(spec: dict) -> dict[str, bool]:
    """A3: fermion projections.

    Returns:
        has_dark_charged_fermion: any fermion with non-SM gauge rep
        has_majorana: any fermion with chirality: majorana
        has_chiral_bsm: any BSM fermion with left/right chirality
    """
    has_dark_charged = False
    has_majorana = False
    has_chiral_bsm = False
    sm_group_symbols = {
        g["symbol"] for g in spec.get("gauge_groups", [])
        if g.get("kind") in _SM_KINDS
    }
    for f in spec.get("fermions", []):
        chirality = f.get("chirality", "")
        if chirality == "majorana":
            has_majorana = True
        reps = f.get("reps", {})
        non_sm_reps = {k: v for k, v in reps.items() if k not in sm_group_symbols and v > 1}
        if non_sm_reps:
            has_dark_charged = True
            if chirality in ("left", "right"):
                has_chiral_bsm = True
    return {
        "has_dark_charged_fermion": has_dark_charged,
        "has_majorana": has_majorana,
        "has_chiral_bsm": has_chiral_bsm,
    }


def _a4_scalar_topology(spec: dict) -> dict[str, Any]:
    """A4: scalar sector topology."""
    scalars = spec.get("scalars", [])
    sm_higgs = [s for s in scalars if s.get("reps", {}).get("WB") == 2]
    n_higgs_doublets = len(sm_higgs)
    cp_odd_present = any(s.get("cp") == "odd" for s in scalars)
    return {
        "n_higgs_doublets": n_higgs_doublets,
        "cp_odd_scalar_present": cp_odd_present,
        "replaces_higgs": spec.get("sm_overrides", {}).get("higgs_sector", False),
    }


def _a5_global_symmetries(spec: dict) -> list[dict[str, Any]]:
    """A5: global symmetry catalogue."""
    return [dict(g) for g in spec.get("global_symmetries", [])]


def _a6_portal_couplings(spec: dict) -> list[str]:
    """A6: portal couplings verbatim from lagrangian.portal_couplings."""
    return list(spec.get("lagrangian", {}).get("portal_couplings", []))


def _a7_extra_colored_matter(spec: dict) -> dict[str, Any]:
    """A7: extra colored matter (non-SM SU(3)_c reps).

    A fermion or scalar is 'extra colored' if it has G (color) rep > 1,
    excluding SM color-triplet quarks (which are internal SM content).
    We flag any BSM field (non-SM-singlet under G) as extra colored.
    """
    sm_group_symbols = {
        g["symbol"] for g in spec.get("gauge_groups", [])
        if g.get("kind") == "color"
    }
    extra: list[str] = []
    for f in spec.get("fermions", []):
        reps = f.get("reps", {})
        for sym in sm_group_symbols:
            if reps.get(sym, 1) > 1:
                extra.append(f.get("name", "?"))
                break
    for s in spec.get("scalars", []):
        reps = s.get("reps", {})
        for sym in sm_group_symbols:
            if reps.get(sym, 1) > 1:
                extra.append(s.get("name", "?"))
                break
    return {"extra_colored_matter": bool(extra), "fields": extra}


def _a8_authoring_status(spec: dict) -> str:
    """A8: authoring status verbatim."""
    return spec.get("authoring_status", "unknown")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_axes(spec: dict) -> AxisReport:
    """Extract taxonomy axes A1–A8 from a v2 ModelSpec dict.

    Args:
        spec: YAML-loaded ModelSpec dict.

    Returns:
        AxisReport dataclass.

    Raises:
        SchemaVersionError: if spec._schema_version != 2.
    """
    if spec.get("_schema_version") != 2:
        raise SchemaVersionError(
            f"taxonomy.read_axes requires _schema_version: 2; "
            f"got {spec.get('_schema_version')!r}. Migrate the spec first."
        )
    return AxisReport(
        a1=_a1_gauge_extension_class(spec),
        a2=_a2_symmetry_breaking_patterns(spec),
        a3=_a3_fermion_projections(spec),
        a4=_a4_scalar_topology(spec),
        a5=_a5_global_symmetries(spec),
        a6=_a6_portal_couplings(spec),
        a7=_a7_extra_colored_matter(spec),
        a8=_a8_authoring_status(spec),
    )


def read_dm_phenomenology(spec: dict) -> DMPhenomenology:
    """Extract dm_phenomenology from a v2 ModelSpec dict.

    Args:
        spec: YAML-loaded ModelSpec dict.

    Returns:
        DMPhenomenology dataclass with parsed candidates.

    Raises:
        KeyError: if dm_phenomenology is absent from the spec.
        ValueError: if the block is malformed.
    """
    if "dm_phenomenology" not in spec:
        raise KeyError(
            f"dm_phenomenology block absent from spec {spec.get('name', '?')}. "
            "A _schema_version: 2 spec must declare dm_phenomenology."
        )
    block = spec["dm_phenomenology"]
    raw_candidates = block.get("candidates", [])
    candidates: list[DMCandidate] = []
    for raw in raw_candidates:
        known_keys = {
            "name", "field_type", "uv_provenance", "mass_parameter",
            "cp", "mediator_field", "mediator_regime", "stabilisation_mechanism",
            "blind_spot_reference", "multi_component_partner", "coupled",
        }
        extras = {k: v for k, v in raw.items() if k not in known_keys}
        candidates.append(DMCandidate(
            name=raw["name"],
            field_type=raw["field_type"],
            uv_provenance=raw["uv_provenance"],
            mass_parameter=raw.get("mass_parameter"),
            cp=raw.get("cp"),
            mediator_field=raw.get("mediator_field"),
            mediator_regime=raw["mediator_regime"],
            stabilisation_mechanism=raw["stabilisation_mechanism"],
            blind_spot_reference=raw.get("blind_spot_reference"),
            multi_component_partner=raw.get("multi_component_partner"),
            coupled=raw.get("coupled"),
            extras=extras,
        ))
    return DMPhenomenology(candidates=candidates)


def analytic_exception_triggered(spec: dict) -> bool:
    """Implements synthesis §7 analytic-exception trigger predicate.

    Returns True when the model requires the analytic backend because:
    - A1 contains a non-abelian non-SM gauge factor (dark SU(N)/mirror), AND
    - A2 contains Higgsed-partial or unbroken-confining, OR
    - dm_phenomenology has a candidate with uv_provenance in
      {broken-generator-boson, composite}.

    Returns False for SM-only models or models without the trigger conditions.

    Args:
        spec: YAML-loaded ModelSpec dict (any version; no SchemaVersionError raised).

    Returns:
        bool.
    """
    a1 = _a1_gauge_extension_class(spec)
    if a1 not in {"SM + extra SU(N)", "SM + extra mixed", "SM + mirror"}:
        return False
    a2 = _a2_symmetry_breaking_patterns(spec)
    if any(e.get("pattern") in {"Higgsed-partial", "unbroken-confining"} for e in a2):
        return True
    # Check dm_phenomenology candidates if present.
    dm_block = spec.get("dm_phenomenology", {})
    for c in dm_block.get("candidates", []):
        if c.get("uv_provenance") in {"broken-generator-boson", "composite"}:
            return True
    return False
