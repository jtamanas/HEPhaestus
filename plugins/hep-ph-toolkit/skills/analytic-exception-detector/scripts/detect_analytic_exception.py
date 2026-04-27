"""detect_analytic_exception.py — Analytic-exception detector (WS4).

Detects when a BSM ModelSpec structurally requires the analytic-backend escape
hatch and returns a structured Verdict. Implements synthesis §3 signal logic,
§3.3 tier mapping, and §9 WS1-axis coupling.

Public API:
    detect(spec: dict, *,
           signal_inputs: SignalInputs | None = None,
           registry_path: Path | None = None) -> Verdict

Verdict dataclass fields (synthesis §3.4):
    verdict:              CLEAR | ROUTE_TO_ANALYTIC | HALT_FOR_SIGNOFF | HARD_HALT
    short_circuits_fired: list[str]
    signals_fired:        list[str]
    evidence:             dict
    disclosure_required:  bool
    exception_id:         str | None
    analytic_module:      str | None
    lint_warnings:        list[str]
    reason_human:         str

SignalInputs dataclass fields (synthesis §9.3):
    gauge_extension_class:      str | None   (WS1 axis)
    dm_candidate_uv_provenance: str | None   (WS1 axis)
    stabilizing_symmetry:       str | None   (recorded in evidence only)
    raw_modelspec:              dict          (always present; fallback source)
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
# scripts/ -> analytic-exception-detector/ -> skills/ -> workflow/ -> plugins/ -> repo root
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent
_ANALYTIC_MODELS_DIR = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "spheno-build" / "scripts" / "analytic_models"
)
_CONSTRAINTS_YAML = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "constraints.yaml"
)
_DEFAULT_REGISTRY = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)

# ---------------------------------------------------------------------------
# Lazy-load the registry loader to avoid circular imports
# ---------------------------------------------------------------------------

def _get_registry_loader():
    registry_module_path = _HERE / "exceptions_registry.py"
    spec = importlib.util.spec_from_file_location("exceptions_registry_inner", registry_module_path)
    mod = importlib.util.module_from_spec(spec)
    # Register under a unique key so repeated calls work
    if "exceptions_registry_inner" not in sys.modules:
        sys.modules["exceptions_registry_inner"] = mod
        spec.loader.exec_module(mod)
    return sys.modules["exceptions_registry_inner"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SignalInputs:
    """Optional WS1-axis inputs for the detector (synthesis §9.3)."""
    gauge_extension_class: Optional[str] = None       # e.g. 'dark', 'SM + extra SU(N)'
    dm_candidate_uv_provenance: Optional[str] = None  # e.g. 'fundamental', 'broken_generator'
    stabilizing_symmetry: Optional[str] = None        # recorded in evidence only
    raw_modelspec: dict = field(default_factory=dict)


@dataclass
class Verdict:
    """Detector output (synthesis §3.4)."""
    verdict: Literal["CLEAR", "ROUTE_TO_ANALYTIC", "HALT_FOR_SIGNOFF", "HARD_HALT"]
    short_circuits_fired: list[str] = field(default_factory=list)
    signals_fired: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    disclosure_required: bool = False
    exception_id: Optional[str] = None
    analytic_module: Optional[str] = None
    lint_warnings: list[str] = field(default_factory=list)
    reason_human: str = ""


# ---------------------------------------------------------------------------
# Short-circuit inputs (passive read)
# ---------------------------------------------------------------------------

def _check_sc_analytic_declared(spec: dict) -> bool:
    """SC_ANALYTIC_DECLARED: backends.spectrum == 'analytic'."""
    return spec.get("backends", {}).get("spectrum") == "analytic"


def _resolve_analytic_module_path(analytic_module_str: str) -> Optional[pathlib.Path]:
    """Convert 'analytic_models.dark_su3' → absolute path under analytic_models/ dir.

    Returns None if the file does not exist.
    """
    if not analytic_module_str:
        return None
    # Strip 'analytic_models.' prefix if present
    parts = analytic_module_str.split(".")
    if parts[0] == "analytic_models" and len(parts) >= 2:
        filename = parts[-1] + ".py"
    else:
        filename = analytic_module_str.replace(".", "/") + ".py"
    candidate = _ANALYTIC_MODELS_DIR / filename
    return candidate if candidate.exists() else None


def _check_sc_analytic_module_wired(spec: dict, registry_view) -> tuple[bool, Optional[str], Optional[str]]:
    """SC_ANALYTIC_MODULE_WIRED: analytic_module resolves to a real file AND
    registry has an entry with that analytic_module path AND model == spec['name'].

    Returns: (wired: bool, exception_id: str|None, analytic_module_path: str|None)
    """
    analytic_module_str = spec.get("backends", {}).get("analytic_module", "")
    if not analytic_module_str:
        return False, None, None

    resolved = _resolve_analytic_module_path(analytic_module_str)
    if resolved is None:
        return False, None, None

    # Check registry: entry.model must match spec name AND entry.analytic_module
    # must resolve to the same file (compare by basename or relative path)
    model_name = spec.get("name", "")
    # Try both the model name from spec and common name variants
    for entry in registry_view.all_active():
        if entry.kind != "analytic":
            continue
        # Check model name match (allow hyphens/underscores as equivalent)
        entry_model_norm = entry.model.replace("-", "_")
        spec_model_norm = model_name.replace("-", "_")
        if entry_model_norm != spec_model_norm:
            continue
        # Check analytic_module path match — absolute path equality only.
        # Basename fallback is intentionally removed: two different analytic modules
        # with the same filename (e.g., dark_su3.py in different dirs) must not
        # cross-match. The registry must declare the full repo-relative path.
        if entry.analytic_module:
            entry_mod_resolved = _REPO_ROOT / entry.analytic_module
            if entry_mod_resolved.exists() and entry_mod_resolved == resolved:
                return True, entry.id, str(resolved)

    return False, None, str(resolved)


# ---------------------------------------------------------------------------
# Structural signals (active inference)
# ---------------------------------------------------------------------------

def _has_dark_nonabelian_gauge(spec: dict) -> tuple[bool, dict]:
    """S_GAUGE_DARK_NONABELIAN: dark non-abelian gauge group with non-trivial fermion/scalar reps."""
    evidence = {}
    gauge_groups = spec.get("gauge_groups", [])
    for gg in gauge_groups:
        if gg.get("kind") != "dark":
            continue
        group = gg.get("group", "")
        symbol = gg.get("symbol", "")
        # Check for SU(N) with N >= 2 (matches SU2, SU3, SU4, etc.)
        if not re.match(r"^SU\d+$", group, re.IGNORECASE):
            continue
        n = int(re.findall(r"\d+", group)[0])
        if n < 2:
            continue
        # Check that at least one fermion or scalar has non-trivial rep under this symbol
        for f in spec.get("fermions", []):
            reps = f.get("reps", {})
            rep_val = reps.get(symbol)
            if rep_val is not None and rep_val != 1:
                evidence = {
                    "field_path": f"fermions[name={f.get('name','?')}].reps.{symbol}",
                    "value": rep_val,
                    "gauge_group_symbol": symbol,
                    "gauge_group_group": group,
                }
                return True, evidence
        for s in spec.get("scalars", []):
            reps = s.get("reps", {})
            rep_val = reps.get(symbol)
            if rep_val is not None and rep_val != 1:
                evidence = {
                    "field_path": f"scalars[name={s.get('name','?')}].reps.{symbol}",
                    "value": rep_val,
                    "gauge_group_symbol": symbol,
                    "gauge_group_group": group,
                }
                return True, evidence
    return False, evidence


def _is_confining_dark(spec: dict) -> tuple[bool, dict]:
    """S_CONFINING_DARK: explicit confining: true on a dark gauge group, or
    composite-hadron names in scalar_potential without corresponding UV scalars,
    or outputs excludes both ufo and spheno while a dark gauge group is present.
    """
    evidence = {}
    gauge_groups = spec.get("gauge_groups", [])
    has_dark_gauge = any(gg.get("kind") == "dark" for gg in gauge_groups)

    # Criterion 1: explicit confining: true
    for gg in gauge_groups:
        if gg.get("kind") == "dark" and gg.get("confining", False):
            evidence = {
                "field_path": f"gauge_groups[symbol={gg.get('symbol','?')}].confining",
                "value": True,
            }
            return True, evidence

    # Criterion 2: composite hadron names in scalar_potential without UV scalars
    hadron_names = {"dark_pion", "dark_meson", "dark_diquark"}
    scalar_names = {s.get("name", "") for s in spec.get("scalars", [])}
    sp_terms = spec.get("lagrangian", {}).get("scalar_potential", [])
    for term in sp_terms:
        for f in term.get("fields", []):
            fname = f.replace("conj[", "").replace("]", "").strip()
            if fname in hadron_names and fname not in scalar_names:
                evidence = {
                    "field_path": "lagrangian.scalar_potential",
                    "composite_name": fname,
                    "not_in_scalars": True,
                }
                return True, evidence

    # Criterion 3: outputs excludes both ufo and spheno AND dark gauge group present
    outputs = set(spec.get("outputs", []))
    if has_dark_gauge and "ufo" not in outputs and "spheno" not in outputs:
        evidence = {
            "field_path": "outputs",
            "value": list(outputs),
            "has_dark_gauge_group": True,
            "note": "outputs excludes both ufo and spheno with dark gauge group present",
        }
        return True, evidence

    return False, evidence


def _dm_not_in_uv_fields(spec: dict, registry_view=None) -> tuple[bool, dict]:
    """S_DM_NOT_IN_UV_FIELDS: documented DM candidates include names not in UV fields."""
    evidence = {}
    # Collect UV field names
    fermion_names = {f.get("name", "") for f in spec.get("fermions", [])}
    scalar_names = {s.get("name", "") for s in spec.get("scalars", [])}
    # Gauge boson names from gauge_groups
    gauge_boson_names = {gg.get("gauge_boson", "") for gg in spec.get("gauge_groups", []) if gg.get("gauge_boson")}
    # Also include derived names (e.g., V from gauge_boson VD or VD->V)
    uv_field_names = fermion_names | scalar_names | gauge_boson_names

    # Collect DM candidates: from spec.display.dm_candidates if present,
    # or try constraints.yaml models.<name>.dm_candidates
    dm_candidates = spec.get("display", {}).get("dm_candidates", [])

    if not dm_candidates:
        # Try constraints.yaml
        try:
            with open(_CONSTRAINTS_YAML) as fh:
                constraints = yaml.safe_load(fh)
            spec_name = spec.get("name", "")
            # Try both hyphen and underscore forms
            for key in [spec_name, spec_name.replace("_", "-"), spec_name.replace("-", "_")]:
                cands = constraints.get("models", {}).get(key, {}).get("dm_candidates", [])
                if cands:
                    dm_candidates = cands
                    break
        except (FileNotFoundError, yaml.YAMLError):
            pass

    if not dm_candidates:
        return False, evidence

    # Only fire if there are dark gauge groups present.
    # In SM-only models, DM candidates are typically mass eigenstates (chi1, etc.)
    # derived from UV fermion mixing — they are NOT composite/broken-generator states.
    # Without a dark non-abelian gauge group, absent-from-UV-fields DM names are
    # almost always mass eigenstates and should not trigger this signal.
    #
    # WHY THIS GUARD IS PROVISIONAL: The definitive discriminator is the WS1 axis
    # `dm_candidate_uv_provenance` (values: "uv_field" | "composite" | "mass_eigenstate").
    # When WS1 supplies `signal_inputs.dm_candidate_uv_provenance`, that axis should be
    # preferred over this dark-gauge heuristic. The heuristic is intentionally narrow
    # (requires a dark gauge group) to avoid false positives on SM-extension models with
    # mass-eigenstate DM candidates. A hypothetical SM-extension model with composite
    # DM but no dark gauge group would be incorrectly classified CLEAR by this guard;
    # that case requires the WS1 axis to be correctly routed.
    has_dark_gauge = any(gg.get("kind") == "dark" for gg in spec.get("gauge_groups", []))
    if not has_dark_gauge:
        return False, evidence

    for cand in dm_candidates:
        name = cand.get("name", "") if isinstance(cand, dict) else str(cand)
        if name and name not in uv_field_names:
            evidence = {
                "field_path": "dm_candidates",
                "candidate_name": name,
                "uv_field_names": sorted(uv_field_names),
                "note": f"DM candidate '{name}' not in fermions/scalars/gauge_bosons",
            }
            return True, evidence

    return False, evidence


# ---------------------------------------------------------------------------
# WS1 axis signal computation (with fallback to direct inspection)
# ---------------------------------------------------------------------------

# WS1 axis values that fire S_GAUGE_DARK_NONABELIAN
_WS1_DARK_NONABELIAN_VALUES = {"dark", "SM + extra SU(N)", "SU(N)"}


def _compute_signal_gauge_dark_nonabelian(
    spec: dict, signal_inputs: Optional[SignalInputs]
) -> tuple[bool, dict]:
    """Compute S_GAUGE_DARK_NONABELIAN via WS1 or direct inspection."""
    if signal_inputs is not None and signal_inputs.gauge_extension_class is not None:
        gec = signal_inputs.gauge_extension_class
        fired = gec in _WS1_DARK_NONABELIAN_VALUES
        return fired, {
            "ws1_axis_consulted": "gauge_extension_class",
            "ws1_axis_value": gec,
        }
    # Fallback to direct ModelSpec inspection
    return _has_dark_nonabelian_gauge(spec)


_WS1_NOT_FUNDAMENTAL = {"broken_generator", "composite", "pseudo_goldstone"}


def _compute_signal_dm_not_in_uv(
    spec: dict, signal_inputs: Optional[SignalInputs], registry_view=None
) -> tuple[bool, dict]:
    """Compute S_DM_NOT_IN_UV_FIELDS via WS1 or direct inspection."""
    if signal_inputs is not None and signal_inputs.dm_candidate_uv_provenance is not None:
        prov = signal_inputs.dm_candidate_uv_provenance
        fired = prov in _WS1_NOT_FUNDAMENTAL
        return fired, {
            "ws1_axis_consulted": "dm_candidate_uv_provenance",
            "ws1_axis_value": prov,
        }
    # Fallback to direct ModelSpec inspection
    return _dm_not_in_uv_fields(spec, registry_view)


# ---------------------------------------------------------------------------
# Load multi_component from constraints.yaml (read-only side input)
# ---------------------------------------------------------------------------

def _load_multi_component(spec: dict) -> Optional[bool]:
    """Read models.<name>.multi_component from constraints.yaml."""
    try:
        with open(_CONSTRAINTS_YAML) as fh:
            constraints = yaml.safe_load(fh)
        spec_name = spec.get("name", "")
        for key in [spec_name, spec_name.replace("_", "-"), spec_name.replace("-", "_")]:
            val = constraints.get("models", {}).get(key, {}).get("multi_component")
            if val is not None:
                return val
    except (FileNotFoundError, yaml.YAMLError):
        pass
    return None


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def detect(
    spec: dict,
    *,
    signal_inputs: Optional[SignalInputs] = None,
    registry_path: Optional[pathlib.Path] = None,
) -> Verdict:
    """Run the analytic-exception detector on a ModelSpec dict.

    Args:
        spec:          Parsed ModelSpec YAML dict.
        signal_inputs: Optional WS1-axis values. Falls back to direct ModelSpec
                       inspection when None or when individual axis values are None.
        registry_path: Optional path to analytic_exceptions.yaml. Defaults to
                       _shared/analytic_exceptions.yaml.

    Returns:
        Verdict with the tier (CLEAR/ROUTE_TO_ANALYTIC/HALT_FOR_SIGNOFF/HARD_HALT)
        and supporting evidence.
    """
    loader = _get_registry_loader()
    reg_path = registry_path if registry_path is not None else _DEFAULT_REGISTRY
    registry = loader.load_exceptions(reg_path)

    evidence: dict[str, Any] = {}
    short_circuits_fired: list[str] = []
    signals_fired: list[str] = []
    lint_warnings: list[str] = []

    # Read multi_component side input (recorded in evidence; does NOT alter verdict)
    multi_component = _load_multi_component(spec)
    evidence["multi_component"] = multi_component

    # Record WS1 stabilizing_symmetry in evidence if provided
    if signal_inputs is not None and signal_inputs.stabilizing_symmetry is not None:
        evidence["stabilizing_symmetry"] = signal_inputs.stabilizing_symmetry

    # ------------------------------------------------------------------
    # Short-circuit inputs (resolution order: these go first)
    # ------------------------------------------------------------------

    sc_analytic_declared = _check_sc_analytic_declared(spec)
    sc_module_wired, sc_exception_id, sc_module_path = _check_sc_analytic_module_wired(spec, registry)

    if sc_analytic_declared:
        short_circuits_fired.append("SC_ANALYTIC_DECLARED")
        evidence["SC_ANALYTIC_DECLARED"] = {
            "field_path": "backends.spectrum",
            "value": "analytic",
        }

    if sc_module_wired:
        short_circuits_fired.append("SC_ANALYTIC_MODULE_WIRED")
        evidence["SC_ANALYTIC_MODULE_WIRED"] = {
            "exception_id": sc_exception_id,
            "analytic_module_path": sc_module_path,
        }

    # ------------------------------------------------------------------
    # Short-circuit tier mapping (synthesis §3.3, rows 1 and 2)
    # ------------------------------------------------------------------

    if sc_analytic_declared and sc_module_wired:
        # Row 1: ROUTE_TO_ANALYTIC
        # Lint gate: if wired but no structural signal fires, emit lint_warning
        # (we check structural signals below for the lint gate)
        gauge_dark_fired, gauge_evidence = _compute_signal_gauge_dark_nonabelian(spec, signal_inputs)
        dm_uv_fired, dm_uv_evidence = _compute_signal_dm_not_in_uv(spec, signal_inputs, registry)
        if not gauge_dark_fired and not dm_uv_fired:
            lint_warnings.append("analytic_module_without_structural_justification")

        return Verdict(
            verdict="ROUTE_TO_ANALYTIC",
            short_circuits_fired=short_circuits_fired,
            signals_fired=signals_fired,
            evidence=evidence,
            disclosure_required=True,
            exception_id=sc_exception_id,
            analytic_module=sc_module_path,
            lint_warnings=lint_warnings,
            reason_human=(
                f"Model '{spec.get('name', '?')}' has `backends.spectrum: analytic` "
                f"and a registered analytic module (exception {sc_exception_id!r}). "
                "Route to /dark-matter-constraints analytic-only branch. "
                "The mandatory disclosure banner must be embedded before any results table."
            ),
        )

    if sc_analytic_declared and not sc_module_wired:
        # Row 2: HALT_FOR_SIGNOFF (declared but not wired)
        # Check if stub_unimplemented and emit lint_warning if wired-without-declaration
        # (SC_ANALYTIC_MODULE_WIRED=False but the module file itself exists)
        if sc_module_path is not None:
            # File exists but no registry entry → module_wired_without_declaration
            lint_warnings.append("module_wired_without_declaration")
        return Verdict(
            verdict="HALT_FOR_SIGNOFF",
            short_circuits_fired=short_circuits_fired,
            signals_fired=signals_fired,
            evidence=evidence,
            disclosure_required=False,
            exception_id=None,
            analytic_module=None,
            lint_warnings=lint_warnings,
            reason_human=(
                f"Model '{spec.get('name', '?')}' declares `backends.spectrum: analytic` "
                "but no registered analytic exception entry exists in "
                "analytic_exceptions.yaml. The analytic-backend escape hatch requires "
                "user sign-off (PR adding a registry entry with a verbatim banner). "
                "See SKILL.md §Sign-off contract for the authorization process."
            ),
        )

    # ------------------------------------------------------------------
    # Structural signals (active inference)
    # ------------------------------------------------------------------

    confining_fired, confining_evidence = _is_confining_dark(spec)
    gauge_dark_fired, gauge_evidence = _compute_signal_gauge_dark_nonabelian(spec, signal_inputs)
    dm_uv_fired, dm_uv_evidence = _compute_signal_dm_not_in_uv(spec, signal_inputs, registry)

    if confining_fired:
        signals_fired.append("S_CONFINING_DARK")
        evidence["S_CONFINING_DARK"] = confining_evidence
    if gauge_dark_fired:
        signals_fired.append("S_GAUGE_DARK_NONABELIAN")
        evidence["S_GAUGE_DARK_NONABELIAN"] = gauge_evidence
    if dm_uv_fired:
        signals_fired.append("S_DM_NOT_IN_UV_FIELDS")
        evidence["S_DM_NOT_IN_UV_FIELDS"] = dm_uv_evidence

    # ------------------------------------------------------------------
    # Structural tier mapping (synthesis §3.3, rows 3-5)
    # ------------------------------------------------------------------

    if confining_fired:
        # Row 3: HARD_HALT (overrides all other structural signals)
        return Verdict(
            verdict="HARD_HALT",
            short_circuits_fired=short_circuits_fired,
            signals_fired=signals_fired,
            evidence=evidence,
            disclosure_required=False,
            exception_id=None,
            analytic_module=None,
            lint_warnings=lint_warnings,
            reason_human=(
                f"Model '{spec.get('name', '?')}' has a confining dark sector "
                "(S_CONFINING_DARK fired). No analytic escape hatch is available — "
                "paper-grade modelling is required. Do NOT offer the sign-off path."
            ),
        )

    if gauge_dark_fired or dm_uv_fired:
        # Row 4: HALT_FOR_SIGNOFF (structural signals without short-circuits)
        return Verdict(
            verdict="HALT_FOR_SIGNOFF",
            short_circuits_fired=short_circuits_fired,
            signals_fired=signals_fired,
            evidence=evidence,
            disclosure_required=False,
            exception_id=None,
            analytic_module=None,
            lint_warnings=lint_warnings,
            reason_human=(
                f"Model '{spec.get('name', '?')}' has structural signals that indicate "
                "the tool chain (MadDM/SARAH/MG5) cannot handle this model's gauge/DM "
                "structure. An analytic exception is structurally justified but has not "
                "been authorized. See SKILL.md §Sign-off contract."
            ),
        )

    # Row 5: CLEAR — proceed to WS2/WS3 capability lookup
    return Verdict(
        verdict="CLEAR",
        short_circuits_fired=short_circuits_fired,
        signals_fired=signals_fired,
        evidence=evidence,
        disclosure_required=False,
        exception_id=None,
        analytic_module=None,
        lint_warnings=lint_warnings,
        reason_human=(
            f"Model '{spec.get('name', '?')}' shows no structural signals requiring "
            "the analytic-backend escape hatch. Proceed to WS2/WS3 capability lookup."
        ),
    )
