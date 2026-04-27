"""matrix_lookup.py — WS2 Tool-Capability Matrix loader, matcher, fold, and CLI.

Public API:
    load_capability_matrix(
        constraints_path, catalog_path, registry_path=None
    ) -> CapabilityMatrix

    matrix.lookup_blockers(axes_bundle: dict) -> dict[str, list[BlockerVerdict]]
    matrix.fold(verdicts) -> dict[str, ToolLevelVerdict]
    matrix.rank_by_role(fold, observable) -> list[ToolLevelVerdict]
    matrix.viable_chain_for(observable, fold) -> list[str]
    matrix.compute_analytic_module_status(model_id) -> str

CLI:
    python3 matrix_lookup.py --model dark-su3 --observables relic dd id --output json

WS2 synthesis ref: brainstorm/ws2_matrix_synthesis.md §8.1, §8.2
WS2 plan: plan/ws2_plan_final.md S3, S4b, S5, S6, S16
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal

import yaml

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

_SHARED = pathlib.Path(__file__).parent
_CONSTRAINTS_PATH = _SHARED / "constraints.yaml"
_CATALOG_PATH = _SHARED / "blocker_catalog.yaml"
_SCHEMA_PATH = _SHARED / "matrix_capabilities.schema.json"
_CATALOG_SCHEMA_PATH = _SHARED / "blocker_catalog.schema.json"

ROLE_ORDER = ["primary", "validator", "specialty", "escape_hatch", "none"]


# ────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ────────────────────────────────────────────────────────────────────────────

class MultipleSamePriorityRolesError(ValueError):
    """Raised by rank_by_role when two prereqs share the same role tier and
    priority_tiebreak, making ranking nondeterministic.

    Per WS2 plan D10: 'S6 fold logic raises an explicit error when ties occur
    and priority_tiebreak is not set on at least one of the tied prereqs.'
    Fix: set a distinct priority_tiebreak on one of the colliding prereqs.
    """


# ────────────────────────────────────────────────────────────────────────────
# Dataclasses (frozen per WS2 plan D4)
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BlockerVerdict:
    """Per-(prereq, rule) verdict returned by lookup_blockers."""
    prereq_id: str
    axis: str                  # e.g. "A1" or "candidates[?].uv_provenance"
    matched_value: Any         # the value that triggered this rule
    verdict: str               # supported | supported_with_caveat | blocked | not_applicable
    blocker: Optional[str] = None    # blocker_catalog key (when verdict==blocked)
    blocker_class: Optional[str] = None
    caveat: Optional[str] = None
    workaround: Optional[str] = None
    escape_hatch_target: Optional[str] = None
    evidence: Optional[str] = None
    acknowledged: bool = False        # set by apply_acknowledgements


@dataclass(frozen=True)
class ToolLevelVerdict:
    """Folded (per-prereq) verdict across all axes."""
    prereq_id: str
    overall_verdict: str       # worst non-NA verdict; or "no_coverage"
    first_blocker: Optional[str] = None
    first_blocker_class: Optional[str] = None
    viable_for_observables: tuple = field(default_factory=tuple)
    role: dict = field(default_factory=dict)   # {observable: role_tier}
    gating_for: tuple = field(default_factory=tuple)
    priority_tiebreak: int = 100
    depends_on_prereqs: tuple = field(default_factory=tuple)


# ────────────────────────────────────────────────────────────────────────────
# Path helper
# ────────────────────────────────────────────────────────────────────────────

def _dotted_get(obj: dict, path: str) -> Any:
    """Resolve a dotted path like 'axes.A1' or 'lagrangian.spec_intent.requested_emissions'."""
    parts = path.split(".")
    cur = obj
    for part in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


# ────────────────────────────────────────────────────────────────────────────
# Single-axis matcher (S4b)
# ────────────────────────────────────────────────────────────────────────────

def _eval_comparator(value: Any, match: Any) -> bool:
    """Evaluate match spec against a resolved value.

    Match forms:
      - "*"                        → always True
      - str or list                → equality or membership check
      - ">=N"                      → value >= N (numeric)
      - "<N"                       → value < N (numeric)
      - "contains[x]"              → x in value (list/set)
      - "not_contains[x]"          → x not in value (list/set)
    """
    if match == "*":
        return True

    m = match
    if isinstance(m, str):
        if m.startswith(">="):
            try:
                threshold = float(m[2:])
                return float(value) >= threshold
            except (TypeError, ValueError):
                return False
        if m.startswith("<"):
            try:
                threshold = float(m[1:])
                return float(value) < threshold
            except (TypeError, ValueError):
                return False
        if m.startswith("contains[") and m.endswith("]"):
            target = m[9:-1]
            if isinstance(value, (list, tuple, set)):
                return target in value
            return False
        if m.startswith("not_contains[") and m.endswith("]"):
            target = m[13:-1]
            if isinstance(value, (list, tuple, set)):
                return target not in value
            return True   # if value is not a list, not_contains is trivially true
        # Simple equality
        return value == m
    elif isinstance(m, list):
        return value in m
    else:
        return value == m


def _resolve_axis_value(axis: str, axes_bundle: dict) -> Any:
    """Resolve an axis key to a value from the axes_bundle.

    Axis forms:
      Ax                       → axes_bundle["axes"][Ax]
      Ax.subfield              → axes_bundle["axes"][Ax][subfield]
      Ax[?].subfield           → existential over list-axis (returns sentinel)
      candidates[?].field      → existential over candidates list
      candidates[*]            → len(candidates) (for count comparators)
      lagrangian.<field>       → axes_bundle["lagrangian"][field]
      model.<field>            → axes_bundle["model_runtime"][field]
    """
    # model.* → model_runtime
    if axis.startswith("model."):
        subkey = axis[6:]
        return _dotted_get(axes_bundle.get("model_runtime", {}), subkey)

    # lagrangian.* → lagrangian block
    if axis.startswith("lagrangian."):
        subkey = axis[11:]
        return _dotted_get(axes_bundle.get("lagrangian", {}), subkey)

    # candidates[*] → count
    if axis == "candidates[*]":
        return len(axes_bundle.get("candidates", []))

    # candidates[?].field → existential sentinel (handled separately)
    if axis.startswith("candidates[?]."):
        return None  # signal to caller to use existential logic

    # A<N>[?].subfield → existential sentinel
    if "[?]." in axis:
        return None  # signal to caller to use existential logic

    # Pure axis like A1, A2, A3 etc.
    axes = axes_bundle.get("axes", {})
    if axis in axes:
        return axes[axis]

    # Dotted axis like A4.n_higgs_doublets
    parts = axis.split(".", 1)
    if len(parts) == 2:
        top, sub = parts
        val = axes.get(top)
        if val is None:
            return None
        if isinstance(val, dict):
            return val.get(sub)
    return None


def _match_single_axis(rule: dict, axes_bundle: dict) -> Optional[dict]:
    """Evaluate a single-axis rule against the axes_bundle.

    Returns the rule dict if matched (with resolved match value), else None.
    Empty-list existential → False (no match).
    """
    axis = rule["axis"]
    match = rule["match"]

    # Existential over candidates[?].field
    if axis.startswith("candidates[?]."):
        subfield = axis[len("candidates[?]."):]
        candidates = axes_bundle.get("candidates", [])
        if not candidates:  # empty list → existential is false
            return None
        for cand in candidates:
            val = cand.get(subfield)
            if _eval_comparator(val, match):
                return rule
        return None

    # Existential over A<N>[?].subfield (list axis like A2[?].pattern)
    if "[?]." in axis:
        top, sub = axis.split("[?].", 1)
        axes = axes_bundle.get("axes", {})
        lst = axes.get(top, [])
        if not isinstance(lst, list) or not lst:
            return None
        for item in lst:
            val = item.get(sub) if isinstance(item, dict) else item
            if _eval_comparator(val, match):
                return rule
        return None

    # candidates[*] count
    if axis == "candidates[*]":
        val = len(axes_bundle.get("candidates", []))
        if _eval_comparator(val, match):
            return rule
        return None

    # Normal axis resolution
    val = _resolve_axis_value(axis, axes_bundle)
    if _eval_comparator(val, match):
        return rule
    return None


# ────────────────────────────────────────────────────────────────────────────
# And/Or conjunction matcher (S5)
# ────────────────────────────────────────────────────────────────────────────

def _match_rule(rule: dict, axes_bundle: dict) -> Optional[dict]:
    """Match any rule shape: single-axis, and:, or:."""
    if "and" in rule:
        return _match_and(rule, axes_bundle)
    if "or" in rule:
        return _match_or(rule, axes_bundle)
    return _match_single_axis(rule, axes_bundle)


def _match_and(rule: dict, axes_bundle: dict) -> Optional[dict]:
    """All sub-rules in rule["and"] must match."""
    for sub in rule["and"]:
        if _match_rule(sub, axes_bundle) is None:
            return None
    return rule


def _match_or(rule: dict, axes_bundle: dict) -> Optional[dict]:
    """At least one sub-rule in rule["or"] must match."""
    for sub in rule["or"]:
        if _match_rule(sub, axes_bundle) is not None:
            return rule
    return None


# ────────────────────────────────────────────────────────────────────────────
# Capability matrix
# ────────────────────────────────────────────────────────────────────────────

class CapabilityMatrix:
    """Parsed and validated capability matrix.

    Loaded via load_capability_matrix(). Do not instantiate directly.
    """

    def __init__(
        self,
        constraints_data: dict,
        catalog_data: dict,
        registry_data: Optional[dict],
        registry_present: bool,
    ):
        self._data = constraints_data
        self._catalog = catalog_data
        self._registry = registry_data
        self.registry_present = registry_present

        # Build reverse index: blocker_code → catalog entry
        self._blocker_index: dict[str, dict] = {}
        if catalog_data and "blockers" in catalog_data:
            self._blocker_index = catalog_data["blockers"]

        # Build prereq capability map
        self._prereqs: dict[str, dict] = constraints_data.get("prereqs", {})

    # ── Public API ──────────────────────────────────────────────────────────

    def compute_analytic_module_status(self, model_id: str) -> str:
        """Return the analytic module status for model_id.

        When registry_present=False: always "missing".
        When registry_present=True: check analytic_exceptions.yaml entries.

        Return values: registered_active | deprecated | retired | missing | stub
        """
        if not self.registry_present or not self._registry:
            return "missing"
        # Look for a matching entry in the registry
        entries = self._registry.get("exceptions", self._registry.get("entries", []))
        if isinstance(entries, dict):
            entries = list(entries.values())
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("model") == model_id:
                status = entry.get("status", "missing")
                if status == "active":
                    # Verify the analytic_module path exists
                    module = entry.get("analytic_module", "")
                    if module and "stub_unimplemented" in module:
                        return "stub"
                    return "registered_active"
                return status  # deprecated, retired, etc.
        # Entry present but no matching model
        return "missing"

    def lookup_blockers(
        self, axes_bundle: dict
    ) -> Dict[str, List[BlockerVerdict]]:
        """Evaluate all prereq capability blocks against axes_bundle.

        Returns: {prereq_id: [BlockerVerdict, ...]}
        First-match-wins within each prereq's support list.
        """
        result: Dict[str, List[BlockerVerdict]] = {}
        for prereq_id, prereq in self._prereqs.items():
            caps = prereq.get("capabilities")
            if not caps:
                continue
            support = caps.get("support", [])
            verdicts: List[BlockerVerdict] = []
            # First-match-wins: find the first matching rule
            for rule in support:
                matched = _match_rule(rule, axes_bundle)
                if matched is not None:
                    verdict = rule.get("verdict", "not_applicable")
                    blocker_code = rule.get("blocker")
                    # Resolve blocker_class from catalog or rule
                    blocker_class = rule.get("blocker_class")
                    if blocker_code and not blocker_class:
                        cat_entry = self._blocker_index.get(blocker_code, {})
                        blocker_class = cat_entry.get("class")
                    axis_label = self._rule_axis_label(rule)
                    bv = BlockerVerdict(
                        prereq_id=prereq_id,
                        axis=axis_label,
                        matched_value=rule.get("match"),
                        verdict=verdict,
                        blocker=blocker_code,
                        blocker_class=blocker_class,
                        caveat=rule.get("caveat"),
                        workaround=rule.get("workaround"),
                        escape_hatch_target=rule.get("escape_hatch_target"),
                        evidence=rule.get("evidence"),
                    )
                    verdicts.append(bv)
                    break  # first-match-wins
            result[prereq_id] = verdicts
        return result

    def fold(
        self, verdicts: Dict[str, List[BlockerVerdict]]
    ) -> Dict[str, ToolLevelVerdict]:
        """Fold per-rule verdicts into per-prereq tool-level verdicts.

        Severity order: blocked > supported_with_caveat > supported
        not_applicable is skipped.
        If every verdict is not_applicable → overall_verdict = "no_coverage"
        """
        SEVERITY = {
            "blocked": 3,
            "supported_with_caveat": 2,
            "supported": 1,
            "not_applicable": 0,
        }
        result: Dict[str, ToolLevelVerdict] = {}
        for prereq_id, bvlist in verdicts.items():
            prereq = self._prereqs.get(prereq_id, {})
            caps = prereq.get("capabilities", {})
            role = caps.get("role", {})
            gating_for = tuple(caps.get("gating_for", []))
            priority_tiebreak = caps.get("priority_tiebreak", 100)
            depends_on = tuple(caps.get("depends_on_prereqs", []))

            # Filter out not_applicable
            active = [bv for bv in bvlist if bv.verdict != "not_applicable"]
            if not active:
                # Either no rules matched or all were not_applicable
                overall = "no_coverage"
                first_blocker = None
                first_blocker_class = None
            else:
                worst = max(active, key=lambda bv: SEVERITY.get(bv.verdict, 0))
                overall = worst.verdict
                first_blocker = worst.blocker
                first_blocker_class = worst.blocker_class

            # Determine which observables this prereq is viable for
            # (role is not "none" and overall verdict is not "blocked")
            viable = tuple(
                obs for obs, tier in role.items()
                if tier != "none" and overall != "blocked"
            )

            result[prereq_id] = ToolLevelVerdict(
                prereq_id=prereq_id,
                overall_verdict=overall,
                first_blocker=first_blocker,
                first_blocker_class=first_blocker_class,
                viable_for_observables=viable,
                role=role,
                gating_for=gating_for,
                priority_tiebreak=priority_tiebreak,
                depends_on_prereqs=depends_on,
            )
        return result

    def rank_by_role(
        self, fold: Dict[str, ToolLevelVerdict], observable: str
    ) -> List[ToolLevelVerdict]:
        """Return prereqs ranked by role tier for an observable.

        Excludes role="none" and "blocked" verdicts.
        Tie-breaks by priority_tiebreak (lower wins).
        Raises ValueError on unresolvable ties (both tied prereqs lack priority_tiebreak).
        """
        ranked = [
            tlv for tlv in fold.values()
            if tlv.role.get(observable, "none") not in ("none",)
            and tlv.overall_verdict != "blocked"
        ]

        def sort_key(tlv):
            role = tlv.role.get(observable, "none")
            try:
                tier_rank = ROLE_ORDER.index(role)
            except ValueError:
                tier_rank = 99
            return (tier_rank, tlv.priority_tiebreak)

        ranked.sort(key=sort_key)

        # Check for ties that cannot be resolved (plan D10)
        for i in range(len(ranked) - 1):
            a, b = ranked[i], ranked[i + 1]
            role_a = a.role.get(observable, "none")
            role_b = b.role.get(observable, "none")
            if role_a == role_b and a.priority_tiebreak == b.priority_tiebreak == 100:
                # Both are at the default priority_tiebreak with the same role tier —
                # this is an unresolvable tie; raise so the author fixes the catalog.
                raise MultipleSamePriorityRolesError(
                    f"unresolvable tie at observable={observable!r}, role={role_a!r}: "
                    f"{a.prereq_id!r} vs {b.prereq_id!r}; "
                    f"set a distinct priority_tiebreak on at least one of these prereqs"
                )

        return ranked

    def viable_chain_for(
        self, observable: str, fold: Dict[str, ToolLevelVerdict]
    ) -> List[str]:
        """Return an ordered chain of prereqs for an observable.

        Ordering: gating_for prereqs (deduped, topo-ordered by depends_on_prereqs)
        followed by the producing prereq.
        """
        ranked = self.rank_by_role(fold, observable)
        if not ranked:
            return []

        # Use the top-ranked (non-blocked, lowest tier-rank) producer
        producer = ranked[0]

        # Gather gatings: prereqs that declare gating_for this observable
        gating_ids = []
        for prereq_id, tlv in fold.items():
            if observable in tlv.gating_for:
                gating_ids.append(prereq_id)

        # Topo-sort the gating prereqs by depends_on_prereqs (simple linear)
        ordered_gating = self._topo_sort(gating_ids, fold)

        chain = [pid for pid in ordered_gating if pid != producer.prereq_id]
        if producer.prereq_id not in chain:
            chain.append(producer.prereq_id)

        return chain

    # ── Acknowledgement suppression (S12) ───────────────────────────────────

    def apply_acknowledgements(
        self,
        verdicts: Dict[str, List[BlockerVerdict]],
        override_block: dict,
    ) -> Dict[str, List[BlockerVerdict]]:
        """Mark blockers as acknowledged when listed in override_block.matrix_acknowledgement.

        Returns a new verdicts dict with acknowledged=True on matching BlockerVerdicts.
        """
        ack = override_block.get("matrix_acknowledgement", {})
        accepted = set(ack.get("accepted_blockers", []))
        if not accepted:
            return verdicts

        result: Dict[str, List[BlockerVerdict]] = {}
        for prereq_id, bvlist in verdicts.items():
            new_list = []
            for bv in bvlist:
                if bv.blocker in accepted:
                    # Replace with acknowledged=True (frozen dataclass → rebuild)
                    import dataclasses
                    bv = dataclasses.replace(bv, acknowledged=True)
                new_list.append(bv)
            result[prereq_id] = new_list
        return result

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _rule_axis_label(self, rule: dict) -> str:
        """Extract a human-readable axis label from a rule (handles and/or)."""
        if "axis" in rule:
            return rule["axis"]
        if "and" in rule:
            return "and:" + "+".join(
                self._rule_axis_label(s) for s in rule["and"]
            )
        if "or" in rule:
            return "or:(" + "|".join(
                self._rule_axis_label(s) for s in rule["or"]
            ) + ")"
        return "unknown"

    def _topo_sort(self, ids: List[str], fold: Dict[str, ToolLevelVerdict]) -> List[str]:
        """Simple topological sort of prereq ids by depends_on_prereqs."""
        result = []
        seen = set()

        def visit(pid: str):
            if pid in seen:
                return
            seen.add(pid)
            tlv = fold.get(pid)
            if tlv:
                for dep in tlv.depends_on_prereqs:
                    if dep in ids:
                        visit(dep)
            result.append(pid)

        for pid in ids:
            visit(pid)
        return result

    def get_constraints_data(self) -> dict:
        return self._data

    def get_prereqs(self) -> dict:
        return self._prereqs


# ────────────────────────────────────────────────────────────────────────────
# Loader
# ────────────────────────────────────────────────────────────────────────────

def load_capability_matrix(
    constraints_path: Optional[pathlib.Path] = None,
    catalog_path: Optional[pathlib.Path] = None,
    registry_path: Optional[pathlib.Path] = None,
) -> CapabilityMatrix:
    """Load and validate constraints.yaml + blocker_catalog.yaml.

    registry_path: path to analytic_exceptions.yaml (WS4 registry).
                   Optional; when absent, analytic_module_status returns 'missing'.
    """
    if constraints_path is None:
        constraints_path = _CONSTRAINTS_PATH
    if catalog_path is None:
        catalog_path = _CATALOG_PATH

    # Load YAML files
    constraints_data = yaml.safe_load(constraints_path.read_text())
    catalog_data = yaml.safe_load(catalog_path.read_text())

    # Validate schema if jsonschema available
    if HAS_JSONSCHEMA:
        import json as _json
        # Validate catalog
        if _CATALOG_SCHEMA_PATH.exists():
            cat_schema = _json.loads(_CATALOG_SCHEMA_PATH.read_text())
            jsonschema.validate(instance=catalog_data, schema=cat_schema)

        # Validate each capabilities block in constraints.yaml
        if _SCHEMA_PATH.exists():
            cap_schema = _json.loads(_SCHEMA_PATH.read_text())
            for prereq_id, prereq in constraints_data.get("prereqs", {}).items():
                caps = prereq.get("capabilities")
                if caps:
                    try:
                        jsonschema.validate(instance=caps, schema=cap_schema)
                    except jsonschema.ValidationError as e:
                        raise ValueError(
                            f"capabilities block for prereq '{prereq_id}' "
                            f"failed schema validation: {e.message}"
                        ) from e

            # Validate each chain_overrides entry against the ChainOverride schema.
            # Use full schema so $ref to MatrixAcknowledgement resolves correctly.
            chain_override_schema = {
                "$ref": "#/$defs/ChainOverride",
                "$defs": cap_schema["$defs"],
            }
            for model_id, model in constraints_data.get("models", {}).items():
                for obs, override in model.get("chain_overrides", {}).items():
                    try:
                        jsonschema.validate(
                            instance=override,
                            schema=chain_override_schema,
                        )
                    except jsonschema.ValidationError as e:
                        raise ValueError(
                            f"chain_overrides[{model_id!r}][{obs!r}] failed schema "
                            f"validation: {e.message}"
                        ) from e

    # Load registry if present
    registry_data = None
    registry_present = False
    if registry_path is None:
        # Check default location
        default_registry = _SHARED / "analytic_exceptions.yaml"
        if default_registry.exists():
            registry_path = default_registry
    if registry_path is not None and pathlib.Path(registry_path).exists():
        registry_data = yaml.safe_load(pathlib.Path(registry_path).read_text())
        registry_present = True

    return CapabilityMatrix(
        constraints_data=constraints_data,
        catalog_data=catalog_data,
        registry_data=registry_data,
        registry_present=registry_present,
    )


# ────────────────────────────────────────────────────────────────────────────
# CLI (S16) — __main__
# ────────────────────────────────────────────────────────────────────────────

def _cli_main():
    parser = argparse.ArgumentParser(
        description="WS2 Tool-Capability Matrix bulk lookup CLI"
    )
    parser.add_argument("--model", required=True, help="Model id (e.g. dark-su3)")
    parser.add_argument(
        "--observables", nargs="+", default=["relic", "dd", "id"],
        help="Observables to route"
    )
    parser.add_argument(
        "--output", choices=["json", "md"], default="json",
        help="Output format"
    )
    parser.add_argument("--constraints-path", default=None)
    parser.add_argument("--catalog-path", default=None)
    parser.add_argument("--registry-path", default=None)
    parser.add_argument("--axes-path", default=None,
                        help="Path to axes-bundle YAML; if not given, uses ws1_axis_reader")

    args = parser.parse_args()

    # Load the matrix
    matrix = load_capability_matrix(
        constraints_path=pathlib.Path(args.constraints_path) if args.constraints_path else None,
        catalog_path=pathlib.Path(args.catalog_path) if args.catalog_path else None,
        registry_path=pathlib.Path(args.registry_path) if args.registry_path else None,
    )

    # Load axes bundle
    if args.axes_path:
        axes_bundle = yaml.safe_load(pathlib.Path(args.axes_path).read_text())
    else:
        # Try ws1_axis_reader
        try:
            sys.path.insert(0, str(_SHARED))
            from ws1_axis_reader import read_axes
            # Find model spec path in modelspec_v3/specs/
            specs_dir = _SHARED / "modelspec_v3" / "specs"
            model_yaml = args.model.replace("-", "_")
            spec_candidates = list(specs_dir.glob(f"{model_yaml}.yaml"))
            if spec_candidates:
                axes_bundle = read_axes(spec_candidates[0])
            else:
                print(f"Warning: no spec found for model '{args.model}'; using empty axes", file=sys.stderr)
                axes_bundle = {"axes": {"A1": "SM", "A8": "complete"}, "candidates": [], "lagrangian": {}, "model_runtime": {}}
                axes_bundle["model_runtime"]["analytic_module_status"] = matrix.compute_analytic_module_status(args.model)
        except Exception as e:
            print(f"Warning: ws1_axis_reader error ({e}); using empty axes", file=sys.stderr)
            axes_bundle = {"axes": {"A1": "SM", "A8": "complete"}, "candidates": [], "lagrangian": {}, "model_runtime": {}}

    # Always set analytic_module_status from the registry
    if "model_runtime" not in axes_bundle:
        axes_bundle["model_runtime"] = {}
    axes_bundle["model_runtime"]["analytic_module_status"] = matrix.compute_analytic_module_status(args.model)

    # Run lookup
    verdicts = matrix.lookup_blockers(axes_bundle)
    fold = matrix.fold(verdicts)

    # Build ranked chains per observable
    ranked_chains = {}
    for obs in args.observables:
        chain = matrix.viable_chain_for(obs, fold)
        ranked_chains[obs] = chain

    if args.output == "json":
        # Convert to JSON-serializable form
        def bv_to_dict(bv: BlockerVerdict) -> dict:
            return {
                "prereq_id": bv.prereq_id,
                "axis": bv.axis,
                "matched_value": str(bv.matched_value) if bv.matched_value is not None else None,
                "verdict": bv.verdict,
                "blocker": bv.blocker,
                "blocker_class": bv.blocker_class,
                "caveat": bv.caveat,
                "evidence": bv.evidence,
                "acknowledged": bv.acknowledged,
            }

        def tlv_to_dict(tlv: ToolLevelVerdict) -> dict:
            return {
                "prereq_id": tlv.prereq_id,
                "overall_verdict": tlv.overall_verdict,
                "first_blocker": tlv.first_blocker,
                "first_blocker_class": tlv.first_blocker_class,
                "viable_for_observables": list(tlv.viable_for_observables),
                "role": tlv.role,
            }

        output = {
            "model": args.model,
            "observables": args.observables,
            "verdicts_by_prereq": {
                pid: [bv_to_dict(bv) for bv in bvlist]
                for pid, bvlist in verdicts.items()
            },
            "fold_by_prereq": {
                pid: tlv_to_dict(tlv) for pid, tlv in fold.items()
            },
            "ranked_chains": ranked_chains,
        }
        print(json.dumps(output, indent=2))
    else:
        # Markdown output
        print(f"# Capability Matrix Report: {args.model}\n")
        print(f"Observables: {', '.join(args.observables)}\n")
        print("## Ranked Chains\n")
        for obs, chain in ranked_chains.items():
            status = "READY" if chain else "BLOCKED"
            print(f"- **{obs}**: {status} → {chain}")
        print("\n## Blocker Summary\n")
        for pid, bvlist in verdicts.items():
            blocked = [bv for bv in bvlist if bv.verdict == "blocked"]
            if blocked:
                for bv in blocked:
                    print(f"- `{pid}`: {bv.blocker} ({bv.blocker_class})")


if __name__ == "__main__":
    _cli_main()
