"""
validation_report.py — WS5 pretty-printer for model-router validation results.

CLI usage:
    python3 validation_report.py [--config <fixture-registry-dir>] [--no-color]

Outputs one markdown section per fixture-registry model showing verdict,
per-observable status, and placement summary. Imports assertion logic from
tests/integration/conftest.py (the recompute_assertion_categories helper) for
DRY consistency per plan R7.

Exit 0 always — this is a formatter, not a regression gate.

Strict guard: ZERO physics imports (numpy/scipy/mpmath).
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# ---------------------------------------------------------------------------
# Resolve repo root and inject sys.path so model_router + tests packages
# are importable without installation.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
_PLUGIN_DIR = _SCRIPTS_DIR.parent
_TESTS_DIR = _PLUGIN_DIR / "tests"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

# ---------------------------------------------------------------------------
# Default fixture registry paths
# ---------------------------------------------------------------------------
_DEFAULT_REGISTRY_DIR = _TESTS_DIR / "fixtures" / "registries"
_FIXTURE_CONSTRAINTS_PATH = _DEFAULT_REGISTRY_DIR / "constraints.yaml"
_FIXTURE_BLOCKER_CATALOG_PATH = _DEFAULT_REGISTRY_DIR / "blocker_catalog.yaml"
_FIXTURE_ANALYTIC_EXCEPTIONS_PATH = _DEFAULT_REGISTRY_DIR / "analytic_exceptions.yaml"

_MODELS = [
    "singlet-doublet",
    "two-hdm-a",
    "dark-su3",
    "dark-su3-confining-synthetic",
]

_OBSERVABLES = ["relic", "dd", "id"]


# ---------------------------------------------------------------------------
# Routing helper — calls production route() with fixture registry overrides
# ---------------------------------------------------------------------------
def _route_for(
    model_id: str,
    observables: list[str],
    *,
    strict: bool = False,
    constraints_path: pathlib.Path,
    blocker_catalog_path: pathlib.Path,
    analytic_exceptions_path: pathlib.Path,
) -> dict:
    """Route model and return json_report dict.

    Catches MatrixAcknowledgementMissing in strict mode (dark-su3 fixture contract)
    and returns a sentinel dict so the formatter can still display exit_code=4.
    """
    from model_router.orchestrator import route, RouterOptions
    from model_router.types import MatrixAcknowledgementMissing

    options = RouterOptions(strict=strict)
    try:
        result = route(
            model_id,
            observables,
            options,
            constraints_path=constraints_path,
            blocker_catalog_path=blocker_catalog_path,
            analytic_exceptions_path=analytic_exceptions_path,
        )
        return result.json_report
    except MatrixAcknowledgementMissing:
        return {
            "exit_code": 4,
            "verdict": "_EXCEPTION_",
            "_exception_type": "MatrixAcknowledgementMissing",
        }


# ---------------------------------------------------------------------------
# Assertion category evaluation via DRY helper from tests/integration/conftest
# ---------------------------------------------------------------------------
def _compute_assertion_categories(model_id: str, report: dict) -> dict[str, bool]:
    """Delegate to the shared recompute_assertion_categories helper (plan R7)."""
    from integration.conftest import recompute_assertion_categories  # noqa: late import
    return recompute_assertion_categories(model_id, report)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
_PASS = "OK"
_FAIL = "FAIL"


def _tick(passed: bool, use_color: bool) -> str:
    if passed:
        return "\033[32m[OK]\033[0m" if use_color else "[OK]"
    return "\033[31m[FAIL]\033[0m" if use_color else "[FAIL]"


def _format_model_section(
    model_id: str,
    default_report: dict,
    strict_report: dict,
    *,
    use_color: bool,
) -> str:
    lines: list[str] = []
    lines.append(f"## {model_id}")
    lines.append("")

    # Top-level verdict and exit codes
    verdict = default_report.get("verdict", "N/A")
    ec_default = default_report.get("exit_code", "?")
    ec_strict = strict_report.get("exit_code", "?")
    lines.append(f"**Verdict (default):** {verdict}")
    lines.append(f"**Exit code:** default={ec_default}, strict={ec_strict}")
    lines.append("")

    # Per-observable summary
    lines.append("| Observable | Status | Active Chain | Blockers |")
    lines.append("|---|---|---|---|")
    for obs in _OBSERVABLES:
        po = default_report.get("per_observable", {}).get(obs, {})
        status = po.get("status", "N/A")
        ac = po.get("active_chain")
        chain_str = ac.get("prereq_id") if ac else "null"
        blockers = po.get("blockers", [])
        blocker_str = ", ".join(blockers) if blockers else "(none)"
        lines.append(f"| {obs} | {status} | {chain_str} | {blocker_str} |")
    lines.append("")

    # Placements summary
    placements = default_report.get("placements", [])
    if placements:
        lines.append(f"**Placements ({len(placements)}):**")
        for i, p in enumerate(placements):
            kind = p.get("kind", "?")
            pos = p.get("position", "?")
            exc_id = p.get("exception_id", "null")
            lines.append(f"  [{i}] kind={kind} position={pos} exception_id={exc_id}")
        lines.append("")

    # Assertion categories (via DRY helper)
    try:
        cats = _compute_assertion_categories(model_id, default_report)
        lines.append("**Assertion categories:**")
        for name, passed in sorted(cats.items()):
            lines.append(f"  {_tick(passed, use_color)} {name}")
        lines.append("")
    except Exception as exc:
        lines.append(f"**Assertion categories:** ERROR computing categories: {exc}")
        lines.append("")

    return "\n".join(lines)


def _build_report(
    *,
    constraints_path: pathlib.Path,
    blocker_catalog_path: pathlib.Path,
    analytic_exceptions_path: pathlib.Path,
    use_color: bool,
) -> str:
    """Route all four models and return the full formatted report string."""
    sections: list[str] = []
    sections.append("# Model-Router Validation Report (WS5)")
    sections.append("")
    sections.append(
        f"Fixture registry: {constraints_path.parent}"
    )
    sections.append("")

    for model_id in _MODELS:
        default_report = _route_for(
            model_id,
            _OBSERVABLES,
            strict=False,
            constraints_path=constraints_path,
            blocker_catalog_path=blocker_catalog_path,
            analytic_exceptions_path=analytic_exceptions_path,
        )
        strict_report = _route_for(
            model_id,
            _OBSERVABLES,
            strict=True,
            constraints_path=constraints_path,
            blocker_catalog_path=blocker_catalog_path,
            analytic_exceptions_path=analytic_exceptions_path,
        )
        section = _format_model_section(
            model_id,
            default_report,
            strict_report,
            use_color=use_color,
        )
        sections.append(section)
        sections.append("---")
        sections.append("")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="WS5 model-router validation report formatter."
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=None,
        help=(
            "Path to the fixture registry directory "
            "(default: tests/fixtures/registries/)."
        ),
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color codes in output.",
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

    use_color = not args.no_color and sys.stdout.isatty()

    report = _build_report(
        constraints_path=constraints_path,
        blocker_catalog_path=blocker_catalog_path,
        analytic_exceptions_path=analytic_exceptions_path,
        use_color=use_color,
    )
    print(report)
    # Exit 0 always — this is a formatter, not a regression gate.


if __name__ == "__main__":
    # Strict guard: assert no physics computation imports are present in this file.
    import re
    _src = pathlib.Path(__file__).read_text()
    _physics_pattern = re.compile(r"^(?:import|from)\s+(numpy|scipy|mpmath)\b", re.MULTILINE)
    _matches = _physics_pattern.findall(_src)
    assert not _matches, (
        f"validation_report.py MUST NOT import physics backends; found: {_matches}"
    )
    main()
