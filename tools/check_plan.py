#!/usr/bin/env python3
"""
check_plan.py — Plan-template lint for hep-ph-demo plans (T-SF-8).

Lint rules:
  R-1 (path-vs-schema): jq filters referencing summary.json must not use paths
      that the core schema's additionalProperties:false forbids (e.g., .provenance.run_id).
  R-2 (schema purity): _shared/summary.core.schema.json and _shared/provenance.schema.json
      must NOT contain channel/particle tokens or model-name enums.
  R-3 (fixture citation): numeric literals near physics keywords (omega_h2|relic|fraction|threshold)
      must be preceded within 3 lines by a fixture citation comment.
  R-4 (atomic-write coupling): any plan asserting summary.json must also assert provenance.json
      in the same task block.

Under --strict, INFO-level findings are fatal (same as --strict in CI).

Usage:
    python tools/check_plan.py <plan.md>
    python tools/check_plan.py --strict <plan.md>

Exit codes:
  0 = no violations (or INFO-only without --strict)
  1 = one or more violations found
  2 = usage error
"""

import argparse
import json
import pathlib
import re
import sys
from typing import Optional

# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]  # tools/../ = hephaestus/
SHARED_DIR = REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared"
CORE_SUMMARY_SCHEMA_PATH = SHARED_DIR / "summary.core.schema.json"
PROVENANCE_SCHEMA_PATH = SHARED_DIR / "provenance.schema.json"

# ---------------------------------------------------------------------------
# R-1: Known top-level keys from core schema (additionalProperties: false)
# ---------------------------------------------------------------------------
CORE_SUMMARY_TOP_KEYS = {
    "schema_version", "model", "run_at", "ran", "skipped_constraints",
    "artifacts_dir", "headline", "relic_approx", "model_source", "model_fixture",
    "channel_percentages", "channel_fractions", "benchmark_id", "provenance_ref",
}

# ---------------------------------------------------------------------------
# R-2: Channel/particle token deny-list for shared schema purity.
# These tokens must not appear in _shared/ schemas (as property names or values).
# Note: uses lookahead/lookbehind for prefix (quote or start) to catch JSON keys.
# ---------------------------------------------------------------------------
CHANNEL_TOKENS_RE = re.compile(
    r'(?:"|^|\s)(bbx|wpwm|zz_pair|tt_pair|chichibar|singlet-doublet|2hdm-a|dark-su3)(?:"|_|\s|$)',
    re.MULTILINE
)
MODEL_ENUM_RE = re.compile(r'"enum"\s*:\s*\[')

# ---------------------------------------------------------------------------
# R-3: Physics keyword pattern near numeric literals
# ---------------------------------------------------------------------------
PHYSICS_KEYWORD_RE = re.compile(
    r'\b(omega_h2|relic|fraction|threshold)\b', re.IGNORECASE
)
NUMERIC_LITERAL_RE = re.compile(r'\b\d+\.\d+\b')
FIXTURE_CITATION_RE = re.compile(
    r'#\s*fixture:\s*\S+/benchmarks/[^/]+/expectations\.json\b'
)

# ---------------------------------------------------------------------------
# R-1: jq gate pattern — matches jq ... -e '<filter>' ... <file>.json
# Handles flags like --arg, --argjson between jq and the filter.
# Also handles: jq -e '<filter>' <file>.json (simple form)
# ---------------------------------------------------------------------------
GATE_JQ_RE = re.compile(
    r"jq\b[^'\n]*'([^']+)'[^'\n]*?(\w+\.json)"
)

# ---------------------------------------------------------------------------
# R-4: Task block boundary (markdown ## or ###)
# ---------------------------------------------------------------------------
TASK_BLOCK_RE = re.compile(r'^#{1,3}\s+', re.MULTILINE)


class LintResult:
    def __init__(self):
        self.violations = []  # (rule_id, lineno, message)
        self.infos = []       # (lineno, message)

    def fail(self, rule_id: str, lineno: int, msg: str):
        self.violations.append((rule_id, lineno, msg))
        print(f"ERROR [{rule_id}] line {lineno}: {msg}", file=sys.stderr)

    def info(self, lineno: int, msg: str):
        self.infos.append((lineno, msg))
        print(f"INFO line {lineno}: {msg}")


def extract_dot_paths(jq_filter: str) -> list:
    """
    Extract simple dot-path access patterns from a jq filter string.
    Handles patterns like .foo.bar, .foo, has("key").
    Only extracts top-level keys (first component of dot-path).
    """
    paths = []
    # Match .key or .key.subkey patterns
    for m in re.finditer(r'\.([A-Za-z_][A-Za-z0-9_]*)', jq_filter):
        paths.append(m.group(1))
    return paths


def schema_permits_path(top_key: str, schema_top_keys: set) -> bool:
    """Check if a dot-path top-level key is permitted by the schema."""
    return top_key in schema_top_keys


def check_r1(lines: list, result: LintResult):
    """
    R-1: jq filters referencing summary.json must not use paths that
    additionalProperties:false forbids (e.g., .provenance.run_id in summary.json).
    """
    full_text = "\n".join(lines)
    for m in GATE_JQ_RE.finditer(full_text):
        jq_filter = m.group(1)
        target_file = m.group(2)
        lineno = full_text[: m.start()].count("\n") + 1

        if target_file != "summary.json":
            continue

        # Check for absence assertions (has("k") | not) — skip
        if "has(" in jq_filter and "not" in jq_filter:
            continue

        for top_key in extract_dot_paths(jq_filter):
            if not schema_permits_path(top_key, CORE_SUMMARY_TOP_KEYS):
                result.fail(
                    "R-1",
                    lineno,
                    (
                        f"jq filter on summary.json references forbidden path "
                        f"'.{top_key}' (not in core schema additionalProperties). "
                        f"Filter: '{jq_filter}'. "
                        f"Allowed top-level keys: {sorted(CORE_SUMMARY_TOP_KEYS)}"
                    ),
                )


def check_r2(schema_path: pathlib.Path, result: LintResult):
    """
    R-2: Shared schemas must not contain channel/particle tokens or model-name enums.
    This check runs against the actual schema files (not the plan).
    """
    if not schema_path.exists():
        result.info(0, f"R-2: schema file not found, skipping: {schema_path}")
        return

    text = schema_path.read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if CHANNEL_TOKENS_RE.search(line):
            result.fail(
                "R-2",
                i,
                f"Schema purity violation in {schema_path.name}: "
                f"model/channel token found: '{line.strip()}'",
            )
        if MODEL_ENUM_RE.search(line) and '"model"' in text:
            # Only flag if this looks like a model enum (heuristic)
            context = text[max(0, text.index(line) - 50): text.index(line) + 100]
            if '"singlet-doublet"' in context or '"2hdm-a"' in context or '"dark-su3"' in context:
                result.fail(
                    "R-2",
                    i,
                    f"Schema purity violation in {schema_path.name}: "
                    f"model enum list found (bakes model names into universal schema): '{line.strip()}'",
                )


def check_r3(lines: list, result: LintResult):
    """
    R-3: Any plan gate with a numeric literal near physics keywords must be
    preceded within 3 lines by a fixture citation comment.
    """
    for i, line in enumerate(lines):
        lineno = i + 1
        if not PHYSICS_KEYWORD_RE.search(line):
            continue
        if not NUMERIC_LITERAL_RE.search(line):
            continue

        # Check the preceding 3 lines for a fixture citation
        preceding = lines[max(0, i - 3): i]
        has_citation = any(FIXTURE_CITATION_RE.search(pl) for pl in preceding)

        if not has_citation:
            result.fail(
                "R-3",
                lineno,
                (
                    f"Numeric literal near physics keyword without fixture citation. "
                    f"Line: '{line.strip()}'. "
                    f"Add '# fixture: <skill>/benchmarks/<name>/expectations.json' "
                    f"within 3 lines above this gate."
                ),
            )


def check_r4(text: str, lines: list, result: LintResult):
    """
    R-4: Any task block asserting summary.json must also assert provenance.json.
    """
    # Split into task blocks at ## headings
    blocks = TASK_BLOCK_RE.split(text)
    offset = 0
    for block in blocks:
        if not block.strip():
            offset += len(block) + text.count("##", offset, offset + len(block))
            continue

        has_summary = "summary.json" in block
        has_provenance = "provenance.json" in block

        if has_summary and not has_provenance:
            # Find the line number of the start of this block
            block_start = text.find(block)
            lineno = text[:block_start].count("\n") + 1
            result.fail(
                "R-4",
                lineno,
                (
                    f"Task block asserts 'summary.json' without a corresponding "
                    f"'provenance.json' assertion. Add an assertion that "
                    f"provenance.json exists in the same task block."
                ),
            )
        offset += len(block)


def lint_plan(plan_path: pathlib.Path, strict: bool) -> int:
    """
    Run all lint rules against a plan markdown file.
    Returns 0 for pass, 1 for violations.
    """
    if not plan_path.exists():
        print(f"[FAIL] plan file not found: {plan_path}", file=sys.stderr)
        return 1

    text = plan_path.read_text()
    lines = text.splitlines()
    result = LintResult()

    # R-1: jq filter path check
    check_r1(lines, result)

    # R-2: Schema purity (check actual shared schema files)
    check_r2(CORE_SUMMARY_SCHEMA_PATH, result)
    check_r2(PROVENANCE_SCHEMA_PATH, result)

    # R-3: Fixture citation for numeric thresholds
    check_r3(lines, result)

    # R-4: Atomic-write coupling
    check_r4(text, lines, result)

    n_violations = len(result.violations)
    n_infos = len(result.infos)

    if n_violations == 0 and (not strict or n_infos == 0):
        print(f"[PASS] {plan_path}: {n_violations} violations, {n_infos} infos")
        return 0
    elif n_violations == 0 and strict and n_infos > 0:
        print(
            f"[FAIL] {plan_path}: 0 violations, {n_infos} INFO-level findings (--strict mode)",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            f"[FAIL] {plan_path}: {n_violations} violation(s), {n_infos} INFO finding(s)",
            file=sys.stderr,
        )
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Lint a hep-ph-demo plan markdown file for schema/fixture compliance."
    )
    parser.add_argument("plan", help="Path to plan markdown file or schema file to check.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Make INFO-level findings fatal (CI mode).",
    )
    args = parser.parse_args()

    plan_path = pathlib.Path(args.plan)

    # Special case: if linting a schema file directly (R-2 check only)
    if plan_path.suffix == ".json":
        result = LintResult()
        check_r2(plan_path, result)
        if not result.violations:
            print(f"[PASS] R-2 schema purity: {plan_path}")
            return 0
        else:
            print(f"[FAIL] R-2 schema purity: {plan_path}", file=sys.stderr)
            return 1

    exit_code = lint_plan(plan_path, args.strict)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
