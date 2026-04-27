"""
regenerate_snapshots.py — WS5 snapshot regenerator for model-router validation.

CLI usage:
    python3 regenerate_snapshots.py [--all] [--model <model_id>]

For each (model, mode) pair, routes, normalizes, and writes:
    tests/integration/snapshots/<model_slug>[.strict].json

Normalization (Option B per WS5 OD1 ratification):
    - Sort only the top-level 'diagnostics' dict by key.
    - Preserve natural ordering of placements[*], per_observable[*], etc.
    - Write with json.dumps(indent=2, sort_keys=False).

SKIP policy (per iter-2 Recommendation #1):
    dark-su3 strict mode raises MatrixAcknowledgementMissing (exit code 4).
    The sentinel dict {"exit_code": 4, "verdict": "_EXCEPTION_", ...} is NOT a
    valid RoutingReport JSON and will not validate against the schema.
    Therefore dark-su3-strict.json is NOT generated; only 7 snapshots are
    produced instead of 8. The missing slot is documented in WS5_FINDINGS.md.

Strict guard: ZERO physics imports (numpy/scipy/mpmath).

Exit 0 always.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Resolve repo root and inject sys.path so model_router is importable.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
_PLUGIN_DIR = _SCRIPTS_DIR.parent
_TESTS_DIR = _PLUGIN_DIR / "tests"
_SNAPSHOTS_DIR = _TESTS_DIR / "integration" / "snapshots"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ---------------------------------------------------------------------------
# Default fixture registry paths
# ---------------------------------------------------------------------------
_DEFAULT_REGISTRY_DIR = _TESTS_DIR / "fixtures" / "registries"
_FIXTURE_CONSTRAINTS_PATH = _DEFAULT_REGISTRY_DIR / "constraints.yaml"
_FIXTURE_BLOCKER_CATALOG_PATH = _DEFAULT_REGISTRY_DIR / "blocker_catalog.yaml"
_FIXTURE_ANALYTIC_EXCEPTIONS_PATH = _DEFAULT_REGISTRY_DIR / "analytic_exceptions.yaml"

_ALL_MODELS = [
    "singlet-doublet",
    "two-hdm-a",
    "dark-su3",
    "dark-su3-confining-synthetic",
]

_OBSERVABLES = ["relic", "dd", "id"]

# dark-su3 strict mode raises MatrixAcknowledgementMissing; skip that slot.
# Documented in WS5_FINDINGS.md Finding 4.
_SKIP_STRICT = {"dark-su3"}


def _model_slug(model_id: str) -> str:
    return model_id.replace("-", "_")


def _normalize(report: dict) -> dict:
    """Apply Option B normalization: sort diagnostics dict only."""
    normalized = dict(report)
    if "diagnostics" in normalized and isinstance(normalized["diagnostics"], dict):
        normalized["diagnostics"] = dict(sorted(normalized["diagnostics"].items()))
    return normalized


def _route_and_write(
    model_id: str,
    *,
    strict: bool,
    constraints_path: pathlib.Path,
    blocker_catalog_path: pathlib.Path,
    analytic_exceptions_path: pathlib.Path,
    snapshots_dir: pathlib.Path,
) -> bool:
    """Route model in the given mode and write snapshot. Returns True on success."""
    from model_router.orchestrator import route, RouterOptions
    from model_router.types import MatrixAcknowledgementMissing

    mode_label = "strict" if strict else "default"
    slug = _model_slug(model_id)
    filename = f"{slug}.strict.json" if strict else f"{slug}.json"
    out_path = snapshots_dir / filename

    # Skip dark-su3 strict (MatrixAcknowledgementMissing; sentinel not schema-valid)
    if strict and model_id in _SKIP_STRICT:
        print(f"  SKIP  {model_id} ({mode_label}) — raises MatrixAcknowledgementMissing; "
              f"slot documented in WS5_FINDINGS.md")
        return False

    try:
        options = RouterOptions(strict=strict)
        result = route(
            model_id,
            _OBSERVABLES,
            options,
            constraints_path=constraints_path,
            blocker_catalog_path=blocker_catalog_path,
            analytic_exceptions_path=analytic_exceptions_path,
        )
        report = _normalize(result.json_report)
        out_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"  WROTE {out_path.name}  ({out_path.stat().st_size} bytes)")
        return True
    except MatrixAcknowledgementMissing:
        print(f"  SKIP  {model_id} ({mode_label}) — MatrixAcknowledgementMissing raised unexpectedly")
        return False
    except Exception as exc:
        print(f"  ERROR {model_id} ({mode_label}): {exc}")
        return False


def regenerate(
    models: list[str],
    *,
    constraints_path: pathlib.Path,
    blocker_catalog_path: pathlib.Path,
    analytic_exceptions_path: pathlib.Path,
    snapshots_dir: pathlib.Path,
) -> int:
    """Regenerate snapshots for the given models. Returns count of files written."""
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for model_id in models:
        print(f"\n[{model_id}]")
        for strict in (False, True):
            ok = _route_and_write(
                model_id,
                strict=strict,
                constraints_path=constraints_path,
                blocker_catalog_path=blocker_catalog_path,
                analytic_exceptions_path=analytic_exceptions_path,
                snapshots_dir=snapshots_dir,
            )
            if ok:
                written += 1
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="WS5 model-router snapshot regenerator."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Regenerate all models (default).",
    )
    group.add_argument(
        "--model",
        type=str,
        metavar="MODEL_ID",
        help="Regenerate a single model only.",
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=None,
        help="Path to fixture registry directory (default: tests/fixtures/registries/).",
    )
    args = parser.parse_args(argv)

    if args.config is not None:
        registry_dir = args.config.resolve()
        constraints_path = registry_dir / "constraints.yaml"
        blocker_catalog_path = registry_dir / "blocker_catalog.yaml"
        analytic_exceptions_path = registry_dir / "analytic_exceptions.yaml"
    else:
        constraints_path = _FIXTURE_CONSTRAINTS_PATH
        blocker_catalog_path = _FIXTURE_BLOCKER_CATALOG_PATH
        analytic_exceptions_path = _FIXTURE_ANALYTIC_EXCEPTIONS_PATH

    models = [args.model] if args.model else _ALL_MODELS

    print(f"Regenerating snapshots for: {models}")
    print(f"Snapshots dir: {_SNAPSHOTS_DIR}")
    print(f"Registry: {constraints_path.parent}")

    written = regenerate(
        models,
        constraints_path=constraints_path,
        blocker_catalog_path=blocker_catalog_path,
        analytic_exceptions_path=analytic_exceptions_path,
        snapshots_dir=_SNAPSHOTS_DIR,
    )
    print(f"\nDone. {written} snapshot(s) written.")
    print("Note: dark-su3-strict is skipped (MatrixAcknowledgementMissing); "
          "7 snapshots total (not 8). See WS5_FINDINGS.md Finding 4.")


if __name__ == "__main__":
    # Strict guard: assert no physics computation imports are present in this file.
    import re
    _src = pathlib.Path(__file__).read_text()
    _physics_pattern = re.compile(r"^(?:import|from)\s+(numpy|scipy|mpmath)\b", re.MULTILINE)
    _matches = _physics_pattern.findall(_src)
    assert not _matches, (
        f"regenerate_snapshots.py MUST NOT import physics backends; found: {_matches}"
    )
    main()
