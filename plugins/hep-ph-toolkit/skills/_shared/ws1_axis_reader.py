"""ws1_axis_reader.py — Forward-compat alias from live ModelSpec to WS1 axis vocabulary.

DEPRECATION WARNING: This module is a *shim* that will be replaced by a call to
plugins/hep-ph-toolkit/skills/_shared/taxonomy.py when WS1 implementation lands.
See WS2 plan S23. Do not add new logic here; fix WS1's taxonomy.py instead.

Alias semantics (per WS2 plan D2):
  - Read order: (i) if spec has spec_intent.requested_emissions → use directly.
                (ii) else if spec has outputs → translate outputs[*] into
                     spec_intent.requested_emissions.
                (iii) else: empty list.
  - Vocabulary mapping (legacy → WS1): ufo→ufo, spheno→spheno,
    analytic_only→analytic_only. No calchep_mdl in legacy vocabulary.
  - Predicates over absent calchep_mdl evaluate as the negative case
    (i.e., not_contains[calchep_mdl] → true universally on legacy specs).

Public API:
    read_axes(model_spec_path: Path | str) -> dict

Return shape:
    {
      "axes": {
        "A1": str,
        "A2": list[{factor, pattern}],
        "A3": {has_dark_charged_fermion, has_majorana_fermion, has_chiral_bsm_fermion},
        "A4": {n_higgs_doublets, n_pure_sm_singlets, n_dark_charged_scalars,
               cp_odd_scalar_present, replaces_sm_higgs, pseudo_goldstone_higgs},
        "A5": list[{kind, name, stabilises}],
        "A6": list[str],       # portal couplings
        "A7": bool,            # extra colored matter
        "A8": str,             # complete | provisional | archived
      },
      "candidates": list[{name, field_type, mediator_regime, uv_provenance,
                           stabilisation_mechanism, cp}],
      "lagrangian": {
        "spec_intent": {"requested_emissions": list[str]},
        "kinetic_mixing_terms": list,
      },
      "model_runtime": {
        "analytic_module_status": str,   # set externally by matrix loader
      },
    }
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional

import yaml

# ────────────────────────────────────────────────────────────────────────────
# Branch A: full alias logic (WS1 not yet implemented)
# Branch B would be:
#   from plugins.model_building.skills._shared.taxonomy import read_axes as _ws1_read_axes
#   def read_axes(spec_path): return _ws1_read_axes(spec_path)
# S23 replaces this file with Branch B when WS1 ships.
# ────────────────────────────────────────────────────────────────────────────

# SM gauge groups (by kind) — not BSM
_SM_KINDS = {"hypercharge", "left", "color"}

# WS1 A1 enum values
_A1_SM = "SM"
_A1_EXTRA_U1 = "SM + extra U(1)"
_A1_EXTRA_SUN = "SM + extra SU(N)"
_A1_EXTRA_MIXED = "SM + extra mixed"
_A1_MIRROR = "SM + mirror"
_A1_NON_SM = "Non-SM-embedding"


def read_axes(model_spec_path) -> dict:
    """Read a ModelSpec YAML and return a WS1-vocabulary axis-bundle dict.

    This is a forward-compat shim (WS2 plan D2). Replace with taxonomy.read_axes()
    when WS1 ships.
    """
    spec_path = pathlib.Path(model_spec_path)
    spec = yaml.safe_load(spec_path.read_text())

    gauge_groups = spec.get("gauge_groups", [])
    fermions = spec.get("fermions", [])
    scalars = spec.get("scalars", [])
    lagrangian = spec.get("lagrangian", {})
    parameters = spec.get("parameters", [])
    global_syms = spec.get("global_symmetries", [])

    # ── A1: Gauge extension class ────────────────────────────────────────────
    bsm_groups = [g for g in gauge_groups if g.get("kind") not in _SM_KINDS]
    bsm_u1 = [g for g in bsm_groups if g.get("group", "").startswith("U1")]
    bsm_sun = [g for g in bsm_groups if g.get("group", "").startswith("SU") and not g.get("group", "").startswith("SU1")]
    bsm_mirror = [g for g in bsm_groups if g.get("kind") == "mirror"]

    if not bsm_groups:
        a1 = _A1_SM
    elif bsm_mirror:
        a1 = _A1_MIRROR
    elif bsm_sun and bsm_u1:
        a1 = _A1_EXTRA_MIXED
    elif bsm_sun:
        a1 = _A1_EXTRA_SUN
    elif bsm_u1:
        a1 = _A1_EXTRA_U1
    else:
        a1 = _A1_EXTRA_MIXED

    # ── A2: Symmetry-breaking pattern ────────────────────────────────────────
    a2 = []
    for g in bsm_groups:
        sym = g.get("symmetry_breaking", {})
        if isinstance(sym, dict):
            pattern = sym.get("pattern", "unknown")
        else:
            pattern = "unknown"
        # Infer Higgsed-partial if dark Higgs scalar exists for this gauge factor
        factor_symbol = g.get("symbol", "")
        if pattern == "unknown":
            # Check if any scalar is charged under this factor
            for s in scalars:
                reps = s.get("reps", {})
                if factor_symbol in reps and reps[factor_symbol] != 1:
                    pattern = "Higgsed-partial"
                    break
        a2.append({"factor": factor_symbol, "pattern": pattern})

    # ── A3: Fermion projections ───────────────────────────────────────────────
    bsm_group_symbols = {g.get("symbol") for g in bsm_groups}
    has_dark_charged = any(
        bool(set(f.get("reps", {}).keys()) & bsm_group_symbols)
        for f in fermions
    )
    has_majorana = any(f.get("chirality") == "majorana" for f in fermions)
    # BSM chiral: left/right fermion that has reps under at least one BSM group
    # OR is not present in the SM field content
    sm_field_names = {"Q", "L", "U", "D", "E", "Hd", "Hu", "H", "u_L", "d_L", "e_L", "N_L"}
    has_chiral_bsm = any(
        f.get("chirality") in ("left", "right")
        and f.get("name") not in sm_field_names
        for f in fermions
    )
    a3 = {
        "has_dark_charged_fermion": has_dark_charged,
        "has_majorana_fermion": has_majorana,
        "has_chiral_bsm_fermion": has_chiral_bsm,
    }

    # ── A4: Scalar sector topology ────────────────────────────────────────────
    n_higgs_doublets = 0
    n_pure_sm_singlets = 0
    n_dark_charged_scalars = 0
    cp_odd_scalar_present = False
    replaces_sm_higgs = False

    for s in scalars:
        reps = s.get("reps", {})
        hc = str(s.get("hypercharge", "0"))
        wb = reps.get("WB", 1)
        name = s.get("name", "")
        cp = s.get("cp", "")

        # Higgs doublet: WB=2, hypercharge=1/2
        if wb == 2 and hc in ("1/2", "0.5"):
            n_higgs_doublets += 1
        # Dark-charged scalar: charged under BSM gauge group
        elif any(sym in reps and reps[sym] != 1 for sym in bsm_group_symbols):
            n_dark_charged_scalars += 1
        # Pure SM singlet (WB=1, not dark-charged)
        elif wb == 1 and not any(sym in reps for sym in bsm_group_symbols):
            n_pure_sm_singlets += 1

        # CP-odd scalar: read from spec's cp field (WS1 v2 schema)
        if cp == "odd" or name in ("a", "A0", "phi_odd"):
            cp_odd_scalar_present = True

    # Check for explicit spec flags
    sm_overrides = spec.get("sm_overrides", {})
    if sm_overrides.get("higgs_sector") is True:
        replaces_sm_higgs = True
    if n_higgs_doublets >= 2:
        replaces_sm_higgs = True

    # Also check dm_phenomenology.candidates[].cp for CP-odd DM candidates.
    # This is the authoritative source for composite/broken-generator candidates
    # (e.g. Psi in dark SU(3)) whose CP character is defined at the DM-phenomenology
    # level, not the scalar-sector level.  Derived from spec content, not model name.
    dm_pheno_candidates = spec.get("dm_phenomenology", {}).get("candidates", [])
    if any(c.get("cp") == "odd" for c in dm_pheno_candidates):
        cp_odd_scalar_present = True
    elif dm_pheno_candidates:
        pass  # candidates present but none cp:odd — keep current value
    else:
        # dm_phenomenology not present (WS1 not yet merged to this spec):
        # fall back to outputs: shim; emit WS1_NOT_MERGED diagnostic.
        if not cp_odd_scalar_present:
            outputs = spec.get("outputs", [])
            if outputs:
                import warnings as _warnings
                _warnings.warn(
                    "[WS1_NOT_MERGED] cp_odd_scalar_present derived from outputs: shim "
                    f"for spec {spec.get('name', '?')} — install WS1 taxonomy.py for "
                    "authoritative A4.cp_odd_scalar_present",
                    stacklevel=3,
                )

    a4 = {
        "n_higgs_doublets": n_higgs_doublets,
        "n_pure_sm_singlets": n_pure_sm_singlets,
        "n_dark_charged_scalars": n_dark_charged_scalars,
        "cp_odd_scalar_present": cp_odd_scalar_present,
        "replaces_sm_higgs": replaces_sm_higgs,
        "pseudo_goldstone_higgs": False,  # not derivable from v1 spec vocabulary
    }

    # ── A5: Discrete symmetries catalogue ────────────────────────────────────
    a5 = []
    for sym in global_syms:
        a5.append({
            "kind": sym.get("kind", "discrete"),
            "name": sym.get("name", ""),
            "stabilises": sym.get("stabilises", ""),
        })
    # Check spec.discrete_symmetries if present (older format)
    for sym in spec.get("discrete_symmetries", []):
        a5.append({
            "kind": "discrete",
            "name": sym.get("name", ""),
            "stabilises": sym.get("stabilises", ""),
        })

    # ── A6: Portal-coupling presence ─────────────────────────────────────────
    a6 = set()
    scalar_potential = lagrangian.get("scalar_potential", [])
    yukawa = lagrangian.get("yukawa_terms", [])

    for term in scalar_potential:
        fields = [f.lower() for f in term.get("fields", [])]
        fields_str = " ".join(str(f) for f in term.get("fields", []))
        # Higgs portal: H + dark scalar
        if any("h" in f.lower() and "conj" not in f.lower() for f in fields) and \
           any(sym.lower() in fields_str.lower() for sym in [g.get("symbol", "") for g in bsm_groups]):
            a6.add("higgs-portal")
        # Pseudoscalar portal: a or A0 in term
        if any(f in ("a", "A0", fields_str) for f in ("a", "A0")):
            a6.add("pseudoscalar-portal")

    for term in yukawa:
        fields = [str(f) for f in term.get("fields", [])]
        fields_str = " ".join(fields)
        # Pseudoscalar portal: a mediator coupling
        if "a" in [f.lower() for f in fields]:
            a6.add("pseudoscalar-portal")

    # kinetic mixing: check lagrangian for explicit kinetic_mixing_terms
    if lagrangian.get("kinetic_mixing_terms"):
        a6.add("vector-portal-darkphoton-kinmix")

    # If no portal found but there are SM+BSM scalars, assume higgs-portal
    if not a6 and bsm_groups and scalars:
        a6.add("higgs-portal")

    # ── A7: Extra colored matter ──────────────────────────────────────────────
    color_symbol = next(
        (g.get("symbol") for g in gauge_groups if g.get("kind") == "color"), "G"
    )
    # SM quarks have color charge; BSM particles with G-charge that aren't SM
    sm_colored_names = {"Q", "U", "D", "u", "d", "g", "G"}
    a7 = any(
        f.get("name") not in sm_colored_names
        and f.get("reps", {}).get(color_symbol, 1) != 1
        for f in fermions + scalars
    )

    # ── A8: Spec authoring status ─────────────────────────────────────────────
    explicit_status = spec.get("authoring_status", None)
    if explicit_status:
        a8 = explicit_status
    elif str(spec_path).find("/archived/") >= 0 or str(spec_path).find("/_archive/") >= 0:
        a8 = "archived"
    elif "stub_unimplemented" in backends.get("analytic_module", ""):
        a8 = "provisional"
    else:
        a8 = "complete"

    # ── requested_emissions alias ─────────────────────────────────────────────
    spec_intent = spec.get("spec_intent", {})
    if spec_intent and spec_intent.get("requested_emissions"):
        requested_emissions = list(spec_intent["requested_emissions"])
    elif spec.get("outputs"):
        # Legacy vocabulary → WS1 vocabulary (same names; no calchep_mdl)
        requested_emissions = list(spec["outputs"])
    else:
        requested_emissions = []

    kinetic_mixing_terms = lagrangian.get("kinetic_mixing_terms", [])

    # ── candidates: read dm_phenomenology if present, else empty ─────────────
    candidates = []
    dm_pheno = spec.get("dm_phenomenology", {})
    if dm_pheno and dm_pheno.get("candidates"):
        candidates = dm_pheno["candidates"]
    # Else: empty — caller should inject from constraints.yaml dm_candidates
    # with best-effort defaults (per WS2 plan D2).

    # ── model_runtime: placeholder (filled externally by matrix loader) ───────
    model_runtime = {
        "analytic_module_status": "missing",  # overridden by matrix loader
    }

    return {
        "axes": {
            "A1": a1,
            "A2": a2,
            "A3": a3,
            "A4": a4,
            "A5": a5,
            "A6": sorted(a6),
            "A7": a7,
            "A8": a8,
        },
        "candidates": candidates,
        "lagrangian": {
            "spec_intent": {
                "requested_emissions": requested_emissions,
            },
            "kinetic_mixing_terms": kinetic_mixing_terms,
        },
        "model_runtime": model_runtime,
    }
