"""Component B — Structured harness-meta consumer for WS-3 Dark SU(3) playtest.

Consumes the runner's ``last_meta`` dict (from ClaudeCodeRunner.last_meta /
_parse_claude_json_output) and Component A's captured HelperInvocations.
Pure function — no I/O, no regex parsing of stdout, no subprocess calls.

Format-bearing region pin:
  File: eval/harness/runners/claude_code.py, lines 254–345
  SHA256: see HARNESS_FORMAT_SHA256 below.
  An edit to _collect_tool_uses or _parse_claude_json_output WILL invalidate
  the pin (desired). An edit to the `name` property (line 442) or unrelated
  methods will NOT invalidate it.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import re
import sys
import typing

# Python 3.10 importlib compatibility fix (frozen dataclass + sys.modules lookup).
if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get(__name__, type(sys)(__name__))

# ---------------------------------------------------------------------------
# Format-region pin (binding — plan-final T3 §3.1)
# ---------------------------------------------------------------------------

HARNESS_FORMAT_REGION: tuple[str, int, int] = (
    "eval/harness/runners/claude_code.py",
    254,
    345,
)

HARNESS_FORMAT_SHA256: str = (
    "2673250afafc4591dd6a08257ddb25d9f09554be65715de978a2a8035bf817f8"
)
# Computed via:
#   python -c "
#   import hashlib, pathlib
#   p = pathlib.Path('eval/harness/runners/claude_code.py')
#   region = b''.join(p.read_bytes().splitlines(keepends=True)[253:345])
#   print(hashlib.sha256(region).hexdigest())
#   "

# ---------------------------------------------------------------------------
# Import-time symbol check (plan-final T3 §3.1 binding — critic §2.3)
# A refactor that renames last_meta or removes _parse_claude_json_output
# MUST fail here at module load, not silently at parse time.
# ---------------------------------------------------------------------------

def _check_at_repo_root() -> bool:
    """Return True if cwd looks like the repository root (has eval/harness/)."""
    return (pathlib.Path.cwd() / "eval" / "harness").is_dir()


try:
    # Lazy import to avoid making eval.harness a hard runtime dep for tests
    # that don't exercise Component B's full path. The assert is the gate.
    import importlib
    _runner_mod = importlib.import_module("eval.harness.runners.claude_code")
    _parse_claude_json_output = _runner_mod._parse_claude_json_output  # noqa: SLF001
    _ClaudeCodeRunner = _runner_mod.ClaudeCodeRunner
    assert hasattr(_ClaudeCodeRunner, "last_meta"), (
        "ClaudeCodeRunner.last_meta missing — harness API changed; "
        "update HARNESS_FORMAT_SHA256 and Component B."
    )
    del _runner_mod, _ClaudeCodeRunner  # keep namespace clean
except ModuleNotFoundError:
    if _check_at_repo_root():
        # Running from repo root means eval.harness SHOULD be importable.
        # A ModuleNotFoundError here means the harness was renamed/moved.
        # Raise loudly so CI catches the drift — do NOT silently set None.
        raise ImportError(
            "eval.harness.runners.claude_code not importable from repo root. "
            "The harness may have been renamed or moved. "
            "Update HARNESS_FORMAT_SHA256 and Component B imports. "
            "If intentionally relocating the harness, update transcript_event_log.py."
        )
    # Not at repo root (e.g. isolated test run). Symbol check is best-effort;
    # gate T3 #2 (content-SHA) is the hard enforcement.
    _parse_claude_json_output = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------

# HelperInvocation imported from Component A.
# Support both package-style and spec_from_file_location loading.
try:
    from tests.dark_su3_playtest.helper_subprocess_wrapper import HelperInvocation
except ModuleNotFoundError:
    import importlib.util as _ilu
    _hw_path = pathlib.Path(__file__).parent / "helper_subprocess_wrapper.py"
    _hw_spec = _ilu.spec_from_file_location("_hw_local", _hw_path)
    _hw_mod = _ilu.module_from_spec(_hw_spec)
    sys.modules["_hw_local"] = _hw_mod
    _hw_spec.loader.exec_module(_hw_mod)
    HelperInvocation = _hw_mod.HelperInvocation


@dataclasses.dataclass(frozen=True)
class TranscriptEventLog:
    """Parsed structured record of a single harness run.

    Built from the runner's last_meta dict (Component B's coupling target)
    plus Component A's captured helper invocations. All fields are read-only.
    """

    helper_invocations: list[HelperInvocation]   # ordered; from Component A
    tool_uses: list[dict]                         # raw harness_meta["tool_uses"]
    file_reads: list[pathlib.Path]                # tool_uses where name == "Read"
    decision_branches: list[str]                  # routing branches in result_text
    merged_table: str                             # Markdown table block from result_text
    raw_answer: dict                              # harness_meta["raw_answer"]
    result_text: str                              # full LLM final-text response


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_TABLE_PATTERN = re.compile(
    r"((?:\|[^\n]+\|\n)+)",  # one or more pipe-delimited rows
    re.MULTILINE,
)

_BRANCH_KEYWORDS = [
    "configured",
    "missing",
    "activation_required",
    "DRAKE_MISSING",
    "DRAKE_ACTIVATION_REQUIRED",
    "DRAKE_SKIPPED",
    "DRAKE_MADDM_DISAGREEMENT",
    "CROSSCHECK_DISAGREEMENT",
    "ADJUDICATION REQUIRED",
    "Step 3",
    "Step 4",
    "Step 5",
]


def _extract_merged_table(result_text: str) -> str:
    """Return the first Markdown table block found in result_text, or ''."""
    match = _TABLE_PATTERN.search(result_text)
    return match.group(1).strip() if match else ""


def _extract_decision_branches(result_text: str) -> list[str]:
    """Return routing-relevant keywords found in result_text prose."""
    found = []
    for kw in _BRANCH_KEYWORDS:
        if kw in result_text:
            found.append(kw)
    return found


def _extract_file_reads(tool_uses: list[dict]) -> list[pathlib.Path]:
    """Return file paths from tool_use entries where name == 'Read'."""
    paths = []
    for tu in tool_uses:
        if isinstance(tu, dict) and tu.get("name") == "Read":
            raw_path = tu.get("input", {}).get("file_path", "")
            if raw_path:
                paths.append(pathlib.Path(raw_path))
    return paths


def parse_transcript(
    harness_meta: dict,
    captured_invocations: list[HelperInvocation],
) -> TranscriptEventLog:
    """Build a TranscriptEventLog from the runner's structured last_meta dict.

    Parameters
    ----------
    harness_meta:
        The dict returned by ``ClaudeCodeRunner.last_meta``. Expected keys:
          - ``tool_uses``: list[dict] of tool_use events
          - ``result_text``: str — LLM's final text response
          - ``raw_answer``: dict — structured JSON block (for blocker codes)
    captured_invocations:
        Component A's ordered list of helper subprocess invocations.

    Returns
    -------
    TranscriptEventLog
        Pure structured data; no I/O performed.
    """
    tool_uses: list[dict] = harness_meta.get("tool_uses", []) or []
    result_text: str = harness_meta.get("result_text", "") or ""
    raw_answer: dict = harness_meta.get("raw_answer", {}) or {}

    return TranscriptEventLog(
        helper_invocations=list(captured_invocations),
        tool_uses=tool_uses,
        file_reads=_extract_file_reads(tool_uses),
        decision_branches=_extract_decision_branches(result_text),
        merged_table=_extract_merged_table(result_text),
        raw_answer=raw_answer,
        result_text=result_text,
    )
