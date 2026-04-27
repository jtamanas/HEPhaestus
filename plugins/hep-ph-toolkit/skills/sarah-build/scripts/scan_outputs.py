"""
scan_outputs.py — Post-collect scanner for SARAH output corruption.

Scans the collected ``sarah_output/{SPheno,UFO}/<sarah_name>/`` trees for
Mathematica-internals leakage (``$Failed``, ``SAxDynL(…)``, ``Part[List[…]]``,
etc.). Emits a ``SARAH_OUTPUT_CORRUPT`` fatal blocker when any hit is found.

Design reference: /tmp/shift-manager/ws-b/02-plan.md §§2, 4, 5, 6.

Public API:
    scan(model_dir, sarah_name, log_path=None) -> dict
        Clean:   {"status": "clean",   "files_scanned": int, "trees": {...}}
        Corrupt: {"status": "corrupt", "blocker": {...}, "files_scanned": int,
                  "trees": {...}}

CLI:
    python3 scan_outputs.py <model_dir> <sarah_name> [--log <path>]
    Exit codes: 0 clean, 1 corrupt, 2 usage error.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern table (plan §4)
# ---------------------------------------------------------------------------
#
# Each entry: (name, compiled_regex, allowed_exts_tuple).
# ``allowed_exts`` is matched against Path.suffix in lower-case EXCEPT that
# we normalise ``.F90`` → ``.f90`` in the scanner loop so a single ".f90"
# entry covers both Fortran casings.
#
# Case-sensitive regex; applied line-by-line on raw text.
_PATTERNS: list[tuple[str, "re.Pattern[str]", tuple[str, ...]]] = [
    ("DOLLAR_FAILED",
     re.compile(r"(?<![A-Za-z0-9_])\$Failed(?![A-Za-z0-9_])"),
     (".f90", ".py")),
    ("DOLLAR_ABORTED",
     re.compile(r"(?<![A-Za-z0-9_])\$Aborted(?![A-Za-z0-9_])"),
     (".f90", ".py")),
    ("DOLLAR_INTERRUPTED",
     re.compile(r"(?<![A-Za-z0-9_])\$Interrupted(?![A-Za-z0-9_])"),
     (".f90", ".py")),
    ("SAX_DYNKIN",
     re.compile(r"\bSAxDynkin\s*\("),
     (".f90",)),
    ("SAX_DYNL",
     re.compile(r"\bSAxDynL\s*\("),
     (".f90",)),
    ("SAX_MULFACTOR",
     re.compile(r"\bSAxMulFactor\s*\("),
     (".f90",)),
    ("SAX_CASIMIR",
     re.compile(r"\bSAxCasimir\s*\("),
     (".f90",)),
    ("PART_LIST",
     re.compile(r"\bPart\s*[\(\[]\s*(?:List\s*[\(\[]|\{)"),
     (".f90", ".py")),
    ("MATHEMATICA_CONCAT",
     re.compile(r"[A-Za-z_]\w*\s*<>\s*[A-Za-z_]\w*"),
     (".f90", ".py")),
    ("HOLD_FORM",
     re.compile(r"\b(?:Hold|HoldForm|HoldComplete)\s*\["),
     (".f90", ".py")),
    ("MISSING_FAILURE",
     re.compile(r"\b(?:Missing|Failure)\s*\["),
     (".f90", ".py")),
    ("NONE_INDEX",
     re.compile(r"\bNone\s*\[\s*\["),
     (".f90",)),
]

# DOLLAR_FAILED-only skip: Fortran diagnostic-write lines.
_DIAG_WRITE_RE = re.compile(r"^\s*Write\s*\(.*\).*\".*\$Failed")

# Per-file byte ceiling (plan §2).
_OVERSIZE_BYTES = 8 * 1024 * 1024

# Hit cap in blocker JSON (plan §5).
_HIT_CAP = 50

# Log-hint pattern table — applied line-by-line to sarah.log when the runner
# passes a log_path. These are the upstream Mathematica errors that cascade
# into the file-level corruption markers above.
_LOG_HINT_PATTERNS: list[tuple[str, "re.Pattern[str]"]] = [
    ("PART_PARTD_NONE",
     re.compile(r"Part::partd:.*None\[\[")),
    ("STRINGJOIN_W_NONE",
     re.compile(r"StringJoin::string:.*W<>None")),
    ("TOEXPRESSION_NOTSTRBOX",
     re.compile(r"ToExpression::notstrbox:.*W<>None")),
    ("PART_PARTW",
     re.compile(r"Part::partw")),
]

# Log-hint cap — sarah.log can be megabytes; we only need a handful for
# diagnosis.
_LOG_HINT_CAP = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm_ext(path: Path) -> str:
    """Normalise .F90 → .f90; lower-cases other suffixes."""
    s = path.suffix
    return ".f90" if s in (".f90", ".F90") else s.lower()


def _excerpt(line: str, cap: int = 240) -> str:
    stripped = line.strip()
    if len(stripped) > cap:
        return stripped[:cap]
    return stripped


def _iter_tree(root: Path, patterns: str) -> list[Path]:
    """Recursive glob relative to *root* matching *patterns* (single glob)."""
    if not root.is_dir():
        return []
    return sorted(root.rglob(patterns))


def _scan_file(
    path: Path,
    tree: str,
    tree_root: Path,
) -> tuple[list[dict], bool]:
    """Scan one file. Returns (hits, oversize_flag)."""
    try:
        size = path.stat().st_size
    except OSError:
        return [], False
    if size > _OVERSIZE_BYTES:
        return [], True
    ext = _norm_ext(path)
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return [], False
    rel = str(path.relative_to(tree_root))
    hits: list[dict] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        for name, regex, allowed in _PATTERNS:
            if ext not in allowed:
                continue
            if not regex.search(raw):
                continue
            if name == "DOLLAR_FAILED" and _DIAG_WRITE_RE.search(raw):
                # Defensive: the only FP shape observed is diagnostic
                # ``Write(unit,*) "...$Failed..."`` inside already-corrupt
                # trees. Skip ONLY for DOLLAR_FAILED to avoid over-broadening.
                continue
            hits.append({
                "tree": tree,
                "file": rel,
                "pattern": name,
                "line": lineno,
                "excerpt": _excerpt(raw),
            })
    return hits, False


def _collect_log_hints(log_path: Path) -> list[dict]:
    """Scan sarah.log for upstream Mathematica-error hint patterns.

    Patterns (one per pattern-table entry):
      - Part::partd:.*None[[       → PART_PARTD_NONE
      - StringJoin::string:.*W<>None → STRINGJOIN_W_NONE
      - ToExpression::notstrbox:.*W<>None → TOEXPRESSION_NOTSTRBOX
      - Part::partw                → PART_PARTW

    Returns a list of dicts ``{"pattern", "line", "excerpt"}``, capped at
    ``_LOG_HINT_CAP``. Returns ``[]`` on read errors or oversize logs.
    """
    try:
        size = log_path.stat().st_size
    except OSError:
        return []
    if size > _OVERSIZE_BYTES:
        return []
    try:
        text = log_path.read_text(errors="replace")
    except OSError:
        return []
    hints: list[dict] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        for name, regex in _LOG_HINT_PATTERNS:
            if regex.search(raw):
                hints.append({
                    "pattern": name,
                    "line": lineno,
                    "excerpt": _excerpt(raw),
                })
                if len(hints) >= _LOG_HINT_CAP:
                    return hints
                break  # one pattern per line
    return hints


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan(
    model_dir: Path,
    sarah_name: str,
    log_path: Path | None = None,
) -> dict:
    """Scan collected SARAH output trees for Mathematica-internals leakage.

    Args:
        model_dir: Per-model state directory (contains ``sarah_output/``).
        sarah_name: SARAH model name (subdirectory under ``SPheno/`` and ``UFO/``).
        log_path: Optional path to ``sarah.log`` for log-hint enrichment.

    Returns:
        Clean:   ``{"status": "clean",   "files_scanned": N, "trees": {...}}``
        Corrupt: ``{"status": "corrupt", "blocker": {...},
                    "files_scanned": N, "trees": {...}}``
    """
    model_dir = Path(model_dir)

    spheno_root = model_dir / "sarah_output" / "SPheno" / sarah_name
    ufo_root    = model_dir / "sarah_output" / "UFO"    / sarah_name

    # Discover files.
    spheno_files: list[Path] = []
    if spheno_root.is_dir():
        spheno_files = sorted(set(spheno_root.rglob("*.f90")) |
                              set(spheno_root.rglob("*.F90")))
    ufo_files: list[Path] = []
    if ufo_root.is_dir():
        ufo_files = sorted(ufo_root.glob("*.py"))

    hits: list[dict] = []
    skipped_oversize: list[str] = []
    files_scanned = 0

    for f in spheno_files:
        h, over = _scan_file(f, "spheno", spheno_root)
        if over:
            skipped_oversize.append(f"spheno:{f.relative_to(spheno_root)}")
            continue
        files_scanned += 1
        hits.extend(h)

    for f in ufo_files:
        h, over = _scan_file(f, "ufo", ufo_root)
        if over:
            skipped_oversize.append(f"ufo:{f.relative_to(ufo_root)}")
            continue
        files_scanned += 1
        hits.extend(h)

    trees = {
        "spheno": len(spheno_files),
        "ufo":    len(ufo_files),
    }

    if not hits:
        return {
            "status": "clean",
            "files_scanned": files_scanned,
            "trees": trees,
        }

    # Deterministic ordering: (tree, file, line, pattern).
    hits.sort(key=lambda h: (h["tree"], h["file"], h["line"], h["pattern"]))
    total_hits = len(hits)
    truncated = total_hits > _HIT_CAP
    shown_hits = hits[:_HIT_CAP]
    files_with_hits = len({(h["tree"], h["file"]) for h in hits})

    scanned_roots = {
        "spheno": str(spheno_root) if spheno_root.is_dir() else None,
        "ufo":    str(ufo_root)    if ufo_root.is_dir()    else None,
    }

    context = {
        "sarah_name": sarah_name,
        "scanned_roots": scanned_roots,
        "files_scanned": files_scanned,
        "files_with_hits": files_with_hits,
        "total_hits": total_hits,
        "truncated": truncated,
        "skipped_oversize": skipped_oversize,
        "hits": shown_hits,
    }

    if log_path and Path(log_path).exists():
        context["log_path"] = str(log_path)
        log_hints = _collect_log_hints(Path(log_path))
        if log_hints:
            context["log_hints"] = log_hints

    blocker = {
        "code": "SARAH_OUTPUT_CORRUPT",
        "mode": "fatal",
        "message": (
            f"SARAH emitted {total_hits} corruption marker(s) across "
            f"{files_with_hits} file(s); Mathematica internals leaked into "
            "generated output."
        ),
        "context": context,
        "user_instruction": (
            "SARAH failed to evaluate group-theory / representation "
            "quantities upstream; Mathematica sentinels leaked into the "
            "generated files. See context.hits[] for file:line evidence. "
            "Read context.log_path (sarah.log) for the upstream stderr "
            "cascade — look for: Part::partd:.*None[[, "
            "StringJoin::string:.*W<>None, ToExpression::notstrbox:.*W<>None, "
            "Part::partw. "
            "Common causes: a matter_sector entry with an ambiguous "
            "representation, or a gauge group whose Dynkin/Casimir wasn't "
            "pre-computed. Inspect the excerpts, fix the ModelSpec, then "
            "re-run /sarah-build."
        ),
    }

    return {
        "status": "corrupt",
        "blocker": blocker,
        "files_scanned": files_scanned,
        "trees": trees,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    args = argv[1:]
    log_path: Path | None = None
    positional: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--log":
            if i + 1 >= len(args):
                print("error: --log requires a path", file=sys.stderr)
                return 2
            log_path = Path(args[i + 1])
            i += 2
            continue
        positional.append(args[i])
        i += 1

    if len(positional) != 2:
        print(
            f"Usage: python3 {argv[0]} <model_dir> <sarah_name> [--log <path>]",
            file=sys.stderr,
        )
        return 2

    model_dir = Path(positional[0])
    sarah_name = positional[1]

    result = scan(model_dir, sarah_name, log_path=log_path)
    if result["status"] == "clean":
        print(json.dumps(result, indent=2))
        return 0
    print(json.dumps(result["blocker"]), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
