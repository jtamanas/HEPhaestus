"""render_disclosure.py — Disclosure renderer for the workflow-skill upstream routing report.

This renderer is used by the workflow skill's routing report (the UPSTREAM output,
produced BEFORE the user invokes /dark-matter-constraints). It is NOT the DMC
merged-report renderer — DMC uses its own SKILL.md prose contract to emit disclosures.

Note: The /dark-matter-constraints merged-report renderer is a SKILL.md-driven Claude
Code agent action (no Python-callable entry point in WS4 v1). See the S5 spike note in
test_analytic_exception_disclosure_emission.py for details.

Public API:
    render(verdict: Verdict, registry: RegistryView | None = None) -> str

Returns a Markdown-formatted routing report section with:
  - The verbatim disclosure banner (wrapped in a Markdown blockquote) for the
    registered exception, positioned FIRST in the output.
  - A "### Results" anchor section placeholder (so positional tests can verify
    the banner precedes any results).
  - A structured routing recommendation section.

If verdict.verdict != 'ROUTE_TO_ANALYTIC', returns an empty string (no banner needed).
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent
_DEFAULT_REGISTRY = (
    _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"
)


def _get_registry_loader():
    registry_module_path = _HERE / "exceptions_registry.py"
    if "exceptions_registry_render" in sys.modules:
        return sys.modules["exceptions_registry_render"]
    spec = importlib.util.spec_from_file_location("exceptions_registry_render", registry_module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["exceptions_registry_render"] = mod
    spec.loader.exec_module(mod)
    return mod


def _wrap_blockquote(text: str) -> str:
    """Wrap text as a Markdown blockquote."""
    lines = text.rstrip("\n").splitlines()
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines)


def render(verdict, registry=None) -> str:
    """Render the workflow-skill disclosure routing report for a given Verdict.

    Args:
        verdict:  Verdict dataclass from detect_analytic_exception.detect().
        registry: Optional RegistryView. Loaded from default path if None.

    Returns:
        Markdown string — the upstream routing report section.
        Empty string if verdict is not ROUTE_TO_ANALYTIC.
    """
    if verdict.verdict != "ROUTE_TO_ANALYTIC":
        return ""

    # Load registry if not provided
    if registry is None:
        loader = _get_registry_loader()
        registry = loader.load_exceptions(_DEFAULT_REGISTRY)

    # Look up the exception entry
    exception_id = verdict.exception_id
    entry = None
    if exception_id:
        entry = registry.by_id(exception_id)

    # Build the routing report
    sections = []

    # Section 1: Title
    sections.append("## Analytic-Exception Detector — Routing Report\n")

    # Section 2: Verdict summary
    sections.append(f"**Verdict:** `ROUTE_TO_ANALYTIC`\n")
    if exception_id:
        sections.append(f"**Exception ID:** `{exception_id}`\n")
    if verdict.analytic_module:
        sections.append(f"**Analytic module:** `{verdict.analytic_module}`\n")

    # Section 3: Signals
    if verdict.signals_fired:
        sections.append("\n**Structural signals fired:**\n")
        for sig in verdict.signals_fired:
            ev = verdict.evidence.get(sig, {})
            field_path = ev.get("field_path", "?")
            value = ev.get("value", "?")
            ws1 = ev.get("ws1_axis_consulted")
            ws1_val = ev.get("ws1_axis_value")
            note = f" (WS1: `{ws1}={ws1_val}`)" if ws1 else ""
            sections.append(f"  - `{sig}` — `{field_path}` = `{value}`{note}\n")

    # Section 4: Lint warnings
    if verdict.lint_warnings:
        sections.append("\n**Lint warnings:**\n")
        for w in verdict.lint_warnings:
            sections.append(f"  - `{w}`\n")

    # Section 5: DISCLOSURE BANNER — MUST appear before results
    sections.append("\n---\n")
    if entry is not None:
        banner_blockquote = _wrap_blockquote(entry.banner)
        sections.append(f"{banner_blockquote}\n")
        sections.append("\n---\n")
    else:
        raise RuntimeError(
            "Disclosure registry entry missing required `banner` field — "
            "registry must be edited to add it; no template fallback exists"
        )

    # Section 6: Results anchor (positional marker for tests)
    sections.append("### Results\n")
    sections.append(
        "_Results will appear here after invoking `/dark-matter-constraints` "
        "on the analytic-only branch (Step 2)._\n"
    )

    # Section 7: Routing recommendation
    sections.append("\n### Routing recommendation\n")
    sections.append(
        f"Invoke `/dark-matter-constraints` with `--spec <model_spec>`. "
        f"The analytic-only branch will fire (Step 2) because:\n\n"
        f"  1. `multi_component` is `{verdict.evidence.get('multi_component', '?')}` "
        f"(from `_shared/constraints.yaml`).\n"
        f"  2. `backends.spectrum == 'analytic'` (from ModelSpec YAML).\n\n"
        f"Steps 3–5 (micrOMEGAs cross-check, DRAKE) are skipped on the analytic-only branch.\n"
    )

    return "".join(sections)
