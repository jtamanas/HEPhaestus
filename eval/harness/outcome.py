"""
Outcome classifier for agent trials.

Fills the 4-mode (plus error) classification described in
`eval/harness/types.py::OutcomeMode`.

Critical design points (PR-A hardening):

1.  Tool-use detection works off the *structured* list of tool_use events
    extracted from Claude's `--output-format json` stream — NOT raw stdout.
    Scanning raw stdout produced false positives because the agent
    frequently echoes SYSTEM_PROMPT fragments verbatim (e.g.
    "mg5_batch.py") in its plain-text reasoning. Those echoes are not
    evidence that MadGraph actually ran.

2.  `task_requires_madgraph` prefers the explicit `task.task_type` field.
    The legacy prompt-regex heuristic is kept only as a fallback (with a
    warning logged on first use) and will be removed in PR-B.

3.  The blocker contract is the canonical
    `{"status": "blocked"|"tool_verified", ...}` schema. Mixing
    `status: "blocked"` with a populated `value` is a contract violation
    and is flagged as such (classifier will label that trial MG_WRONG).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .types import OutcomeMode, Task, TrialResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MadGraph / MadDM tool-use detection (operates on structured tool_use events)
# ---------------------------------------------------------------------------

# Tokens that genuinely indicate MG/MadDM execution in a Bash command or
# embedded heredoc script. Each token is matched as a regex with word
# boundaries so that SYSTEM_PROMPT echoes like "mg5_batch.py" and
# "maddm_run.py" do NOT trigger a positive (those are prompt artifacts,
# not evidence of execution).
_MG_CMD_TOKEN_PATTERNS = (
    r"\bmg5_aMC\b",
    r"\bbin/mg5\b",
    r"\bmaddm\b(?!_)",          # the maddm binary; reject `maddm_run.py`
    r"\bmadevent\b",
    r"\blhe_parser\b(?!\.py)",  # command / module invocation, not the prompt
    r"\bMADDM_results\.txt\b",
)

# Strings that appear in SYSTEM_PROMPT and must NOT count as detection
# — filter them out BEFORE running the patterns above. (Belt-and-braces.)
_SYSTEM_PROMPT_ECHOES = (
    "mg5_batch.py",
    "maddm_run.py",
    "card_io.py",
    "lhe_parser.py",
)

# Heredoc / script-content tokens that indicate MG5 directive lines.
# We require these to appear on a line by themselves (possibly indented) so
# that we don't match prose like "you should import model X via mg5".
_MG_SCRIPT_DIRECTIVES = (
    "import model ",
    "launch",
    "output ",
)


def _iter_bash_inputs(tool_uses: list[dict]) -> list[str]:
    """Return every Bash `command` string from the tool_use event list.

    Handles nested / array cases defensively — a tool_use event may arrive
    with `input` as a dict (normal) or, in malformed/partial streams, as
    something else; skip anything that doesn't look right.
    """
    out: list[str] = []
    for ev in tool_uses or []:
        if not isinstance(ev, dict):
            continue
        if ev.get("name") != "Bash":
            continue
        inp = ev.get("input")
        if not isinstance(inp, dict):
            continue
        cmd = inp.get("command")
        if isinstance(cmd, str):
            out.append(cmd)
        elif isinstance(cmd, list):
            # Defensive: some providers emit command as ["bash", "-c", "..."]
            for c in cmd:
                if isinstance(c, str):
                    out.append(c)
    return out


def detect_madgraph_use(tool_uses: list[dict]) -> bool:
    """Detect whether the agent actually invoked MadGraph/MadDM.

    Scans the structured `tool_use` event list (extracted from Claude's
    `--output-format json` stream) for Bash commands that match MG/MadDM
    invocation tokens or MG5 script directives inside heredoc'd scripts.

    Crucially, this does NOT scan raw stdout — that approach produced
    false positives whenever the agent echoed SYSTEM_PROMPT fragments.
    """
    if not tool_uses:
        return False

    commands = _iter_bash_inputs(tool_uses)
    if not commands:
        return False

    for cmd in commands:
        # Strip SYSTEM_PROMPT echoes before running detection so the
        # bare names of helper scripts listed in the prompt (e.g.
        # mg5_batch.py, maddm_run.py) never match.
        stripped = cmd
        for echo in _SYSTEM_PROMPT_ECHOES:
            stripped = stripped.replace(echo, "")

        for pattern in _MG_CMD_TOKEN_PATTERNS:
            if re.search(pattern, stripped):
                return True
        # Heredoc / script-content: require the directive to appear at
        # the start of a (possibly indented) line. This avoids matching
        # prose references.
        for directive in _MG_SCRIPT_DIRECTIVES:
            pat = r"(?m)^\s*" + re.escape(directive)
            if re.search(pat, stripped):
                return True

    return False


# ---------------------------------------------------------------------------
# task_requires_madgraph: prefer task_type, fall back to prompt regex.
# ---------------------------------------------------------------------------

# Legacy regex — kept only as a fallback when `task_type` is absent.
# Will be removed in PR-B once all YAMLs carry `task_type`.
_LEGACY_MG_PROMPT_RE = re.compile(
    r"\b(MadGraph|MadDM|mg5|maddm|proc_card|param_card|run_card|lhe)\b",
    re.IGNORECASE,
)

_WARNED_LEGACY: set[str] = set()


def task_requires_madgraph(task: Task) -> bool:
    """Whether this task's correct execution path runs MadGraph/MadDM.

    Preference order:
      1. Explicit `task.task_type`:
           - "mg_required" -> True
           - "algebra" | "na" -> False
      2. Fallback: legacy prompt regex (with a one-shot warning per task).
    """
    tt = getattr(task, "task_type", None)
    if tt == "mg_required":
        return True
    if tt in ("algebra", "na"):
        return False
    if tt is not None:
        logger.warning(
            "Task %s has unknown task_type=%r; treating as non-MG.",
            task.id, tt,
        )
        return False

    # Fallback (soft-deprecated): regex on the prompt.
    if task.id not in _WARNED_LEGACY:
        logger.warning(
            "Task %s has no `task_type`; falling back to prompt-regex "
            "heuristic. Set task_type to mg_required/algebra/na in the "
            "YAML — the regex will be removed in PR-B.",
            task.id,
        )
        _WARNED_LEGACY.add(task.id)
    return bool(_LEGACY_MG_PROMPT_RE.search(task.prompt or ""))


# ---------------------------------------------------------------------------
# Blocker contract
# ---------------------------------------------------------------------------

def extract_blocked(answer: dict[str, Any]) -> tuple[bool, str | None, bool]:
    """Parse the canonical blocker contract from the agent's JSON answer.

    Canonical schema (PR-A):
        {"status": "tool_verified", "value": {...}}
        {"status": "blocked", "reason": "...", "missing": [...], "next_steps": [...]}

    Returns (blocked, reason, contract_violated).

    Contract violation cases:
      - `status == "blocked"` but `value` is populated with anything truthy
        (the agent is claiming a blocker AND fabricating numbers).
      - `status` is some unknown string.
    Contract violations are flagged and the caller should treat the trial
    as MG_WRONG.

    PR-D will later add `status == "reference_only"`; we treat unknown
    statuses as contract_violated=True but only for true unknowns — when
    PR-D ships, add the new literal here.
    """
    if not isinstance(answer, dict):
        return (False, None, False)

    status = answer.get("status")
    if status is None:
        # No contract wrapper present — not blocked, not violated.
        return (False, None, False)

    if status == "tool_verified":
        return (False, None, False)

    if status == "reference_only":
        # PR-D: reference_only is a valid opt-in status, distinct from blocked.
        # `_is_reference_only` validates the payload shape; here we simply
        # refuse to treat it as a blocker.
        return (False, None, False)

    if status == "blocked":
        value = answer.get("value")
        # A populated `value` alongside blocked is a contract violation.
        if value not in (None, {}, [], ""):
            reason = answer.get("reason") or "blocked-with-value"
            return (True, reason, True)
        reason = answer.get("reason")
        return (True, reason if isinstance(reason, str) else None, False)

    # Unknown status — flag as violation.
    return (False, None, True)


def _is_reference_only(answer: dict[str, Any]) -> bool:
    """Return True iff `answer` is a well-formed reference_only payload.

    Validates the opt-in contract:
      - status == "reference_only"
      - non-empty `reference_method` string
      - non-empty `caveats` list

    Mirrors the logic previously in `outcome_extensions.classify_reference_only`,
    now folded directly into this module.
    """
    if not isinstance(answer, dict):
        return False
    if answer.get("status") != "reference_only":
        return False

    reference_method = answer.get("reference_method")
    if not isinstance(reference_method, str) or not reference_method.strip():
        return False

    caveats = answer.get("caveats")
    if not isinstance(caveats, list) or not caveats:
        return False

    return True


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify(
    task: Task,
    *,
    passed: bool,
    used_madgraph: bool,
    blocked: bool,
    contract_violated: bool,
    runner_error: bool = False,
    reference_only: bool = False,
) -> OutcomeMode:
    """Assign an OutcomeMode to a single trial.

    Order of precedence:
      1. runner_error -> RUNNER_ERROR
      2. blocked (well-formed) -> BLOCKED_CORRECTLY
         (takes precedence over REFERENCE_ONLY; a `status: blocked` response
         is still BLOCKED_CORRECTLY regardless of other signals.)
      3. reference_only (well-formed) -> REFERENCE_ONLY
         (takes precedence over PY_FALLBACK but NOT over blocked.)
      4. task does NOT require MG -> NA
      5. contract_violated -> MG_WRONG
      6. used MG -> MG_CORRECT / MG_WRONG (by passed)
      7. no MG, no blocker, task needed MG -> PY_FALLBACK
    """
    if runner_error:
        return OutcomeMode.RUNNER_ERROR

    # A contract-violating blocked-with-value payload is MG_WRONG, NOT
    # BLOCKED_CORRECTLY. Handle that before the plain blocked branch.
    if contract_violated and blocked:
        return OutcomeMode.MG_WRONG

    if blocked:
        return OutcomeMode.BLOCKED_CORRECTLY

    if reference_only:
        return OutcomeMode.REFERENCE_ONLY

    if not task_requires_madgraph(task):
        return OutcomeMode.NA

    if contract_violated:
        return OutcomeMode.MG_WRONG

    if used_madgraph:
        return OutcomeMode.MG_CORRECT if passed else OutcomeMode.MG_WRONG

    return OutcomeMode.PY_FALLBACK


def annotate_trial(
    trial: TrialResult,
    task: Task,
    *,
    tool_uses: list[dict] | None,
    answer: dict[str, Any] | None,
    runner_error: bool = False,
) -> TrialResult:
    """Populate outcome-mode fields on a TrialResult.

    Safe to call on non-agent runs (just set `tool_uses=None, answer=None`
    and `runner_error=False`); it will classify as NA for algebra/na tasks
    and PY_FALLBACK for mg_required ones — callers decide whether to skip.
    """
    used_mg = detect_madgraph_use(tool_uses or [])
    blocked, reason, contract_violated = extract_blocked(answer or {})
    ref_only = _is_reference_only(answer or {})

    trial.used_madgraph = used_mg
    trial.blocked = blocked
    trial.blocked_reason = reason
    trial.contract_violated = contract_violated
    if ref_only and isinstance(answer, dict):
        rm = answer.get("reference_method")
        if isinstance(rm, str) and rm.strip():
            trial.reference_method = rm
    trial.outcome_mode = classify(
        task,
        passed=trial.passed,
        used_madgraph=used_mg,
        blocked=blocked,
        contract_violated=contract_violated,
        runner_error=runner_error,
        reference_only=ref_only,
    )
    return trial


# ---------------------------------------------------------------------------
# In-script tests — exercise all classifier branches including REFERENCE_ONLY.
# Run with: `python -m eval.harness.outcome`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from .types import GraderConfig

    def _mg_task() -> Task:
        return Task(
            id="test_mg",
            tier=2,
            model="test",
            prompt="",
            reference_fn="",
            reference_args={},
            graders=[GraderConfig(type="numeric", key="sigma_SI")],
            task_type="mg_required",
        )

    def _algebra_task() -> Task:
        return Task(
            id="test_algebra",
            tier=1,
            model="test",
            prompt="",
            reference_fn="",
            reference_args={},
            graders=[],
            task_type="algebra",
        )

    # 1. runner_error branch
    m = classify(_mg_task(), passed=False, used_madgraph=False,
                 blocked=False, contract_violated=False, runner_error=True)
    assert m == OutcomeMode.RUNNER_ERROR, m

    # 2. blocked branch wins over reference_only
    m = classify(_mg_task(), passed=False, used_madgraph=False,
                 blocked=True, contract_violated=False, reference_only=True)
    assert m == OutcomeMode.BLOCKED_CORRECTLY, m

    # 3. valid reference_only payload -> REFERENCE_ONLY
    valid_ref = {
        "status": "reference_only",
        "value": {"sigma_SI": 7.6e-45},
        "reference_method": "tree-level Higgs-portal, Eq. 5 of arXiv:2506.19062",
        "caveats": ["LO only", "form factors from Hoferichter 2015"],
    }
    assert _is_reference_only(valid_ref) is True
    m = classify(_mg_task(), passed=True, used_madgraph=False,
                 blocked=False, contract_violated=False, reference_only=True)
    assert m == OutcomeMode.REFERENCE_ONLY, m

    # 4. reference_only with empty caveats -> invalid, falls through to PY_FALLBACK
    bad_empty_caveats = dict(valid_ref, caveats=[])
    assert _is_reference_only(bad_empty_caveats) is False
    m = classify(_mg_task(), passed=False, used_madgraph=False,
                 blocked=False, contract_violated=False, reference_only=False)
    assert m == OutcomeMode.PY_FALLBACK, m

    # 5. reference_only missing reference_method -> invalid
    bad_no_method = {k: v for k, v in valid_ref.items() if k != "reference_method"}
    assert _is_reference_only(bad_no_method) is False

    # 6. blocked response via extract_blocked -> BLOCKED_CORRECTLY (not REFERENCE_ONLY)
    blocked_payload = {
        "status": "blocked",
        "reason": "MadDM not installed",
        "missing": ["MadDM"],
    }
    b, r, cv = extract_blocked(blocked_payload)
    assert b is True and cv is False and r == "MadDM not installed"
    assert _is_reference_only(blocked_payload) is False

    # 7. reference_only payload does NOT get flagged as blocked
    b, r, cv = extract_blocked(valid_ref)
    assert b is False and cv is False, (b, r, cv)

    # 8. NA branch (non-MG task)
    m = classify(_algebra_task(), passed=True, used_madgraph=False,
                 blocked=False, contract_violated=False)
    assert m == OutcomeMode.NA, m

    # 9. MG_CORRECT / MG_WRONG branches
    m = classify(_mg_task(), passed=True, used_madgraph=True,
                 blocked=False, contract_violated=False)
    assert m == OutcomeMode.MG_CORRECT, m
    m = classify(_mg_task(), passed=False, used_madgraph=True,
                 blocked=False, contract_violated=False)
    assert m == OutcomeMode.MG_WRONG, m

    # 10. blocked-with-value contract violation -> MG_WRONG
    blocked_with_value = {
        "status": "blocked",
        "reason": "whatever",
        "value": {"sigma_SI": 1e-45},
    }
    b, r, cv = extract_blocked(blocked_with_value)
    assert b is True and cv is True
    m = classify(_mg_task(), passed=False, used_madgraph=False,
                 blocked=b, contract_violated=cv)
    assert m == OutcomeMode.MG_WRONG, m

    print("outcome.py self-tests: all branches OK")
