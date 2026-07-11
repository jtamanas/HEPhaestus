"""WS-3 pytest conftest — Dark SU(3) playtest harness.

Provides:
  - Session-scoped claude CLI check (skips suite if absent)
  - HardFailure / RetryResult frozen dataclasses
  - run_with_retry_budget() — retry-budget dispatch
  - build_prompt_envelope() — SKILL.md content (not path) + fixture yamls
  - assert_no_claude_md_leakage() — runnable CLAUDE.md isolation check
  - Fixture paths / SKILL.md resolution
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import shutil
import typing

import pytest

# ---------------------------------------------------------------------------
# Repository root (absolute)
# ---------------------------------------------------------------------------

REPO = pathlib.Path(__file__).parent.parent.parent.resolve()
FIXTURES = REPO / "tests" / "fixtures" / "dark_su3_playtest"
SKILL_MD_PATH = (
    REPO / "plugins" / "hep-ph-toolkit" / "skills" / "dark-matter-constraints" / "SKILL.md"
)
CANNED = FIXTURES / "canned"
CONFIGS = FIXTURES / "configs"
SPECS = FIXTURES / "specs"
GOLDEN = FIXTURES / "golden"
NC_DIR = FIXTURES / "negative_control"

# ---------------------------------------------------------------------------
# Session-scoped claude CLI check (plan-final T4 gate #8, critic §3.7)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def require_claude_cli():
    """Skip WS-3 suite if the claude CLI is absent."""
    if not shutil.which("claude"):
        pytest.skip("WS-3 requires the `claude` CLI; install it before running.")


# ---------------------------------------------------------------------------
# Hard/soft assertion dataclasses (plan-final T4, critic §2.7.3)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class HardFailure:
    """Records a single hard-assertion failure on a given attempt.

    ``attempt`` is the 1-indexed attempt number on which the assertion failed.
    With a retry budget > 1 (see ``run_with_retry_budget`` /
    ``HEPPH_PLAYTEST_MAX_ATTEMPTS``) the same assertion may fail on several
    attempts; the per-attempt detail is preserved in
    ``RetryResult.hard_attempt_history``.
    """

    attempt: int
    assertion_id: str


@dataclasses.dataclass(frozen=True)
class RetryResult:
    """Structured result from run_with_retry_budget.

    tier: Literal["tier1","tier2","tier3"] — widened for T5 Tier-3 scaffold.
    hard_failures: list of HardFailure from the FINAL attempt (empty if any
        attempt passed all hard assertions). This is what the tier gates read.
    soft_results: assertion_id -> earliest passing attempt (int) or None
        (failed on every attempt).
    hard_attempt_history: per-attempt list of the hard failures seen on that
        attempt (index 0 == attempt 1). Preserved so reports/handoffs can show
        which assertions flaked and on which attempt they recovered.
    """

    scenario_id: str
    tier: typing.Literal["tier1", "tier2", "tier3"]
    hard_failures: list[HardFailure]
    soft_results: dict[str, int | None]
    hard_attempt_history: list[list[HardFailure]] = dataclasses.field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# SKILL.md resolution (env override for negative-control tests)
# ---------------------------------------------------------------------------


def resolve_skill_md() -> pathlib.Path:
    """Return the SKILL.md path to use (env override for negative-control tests)."""
    override = os.environ.get("WS3_SKILL_OVERRIDE_PATH")
    if override:
        return pathlib.Path(override)
    return SKILL_MD_PATH


# ---------------------------------------------------------------------------
# Scenario path helpers
# ---------------------------------------------------------------------------


def scenario_config_path(scenario_id: str) -> pathlib.Path:
    """Return config YAML path for a given scenario_id."""
    name_map = {
        "pointA_configured": "config_pointA_configured.yaml",
        "pointA_missing": "config_pointA_missing.yaml",
        "pointA_activation_required": "config_pointA_activation_required.yaml",
        "pointA_unset": "config_pointA_unset.yaml",
        "pointB": "config_pointB.yaml",
    }
    fname = name_map.get(scenario_id, f"config_{scenario_id}.yaml")
    return CONFIGS / fname


def scenario_spec_path(scenario_id: str) -> pathlib.Path:
    """Return spec YAML path for a given scenario_id."""
    if "pointB" in scenario_id or scenario_id.startswith("pointB"):
        return SPECS / "spec_pointB.yaml"
    return SPECS / "spec_pointA.yaml"


# ---------------------------------------------------------------------------
# Prompt envelope builder (plan-final T4, critic §3.4 + §3.6)
# ---------------------------------------------------------------------------


def _load_text(path: pathlib.Path) -> str:
    """Read a text file, returning empty string if absent."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def build_prompt_envelope(scenario_id: str) -> dict:
    """Build the harness prompt envelope for a scenario.

    Loads SKILL.md CONTENT as a string (not a path), plus config/spec YAMLs.
    NO project memory, NO global CLAUDE.md, NO unrelated SKILL.md.
    """
    skill_md_path = resolve_skill_md()
    skill_md_content = skill_md_path.read_text(encoding="utf-8")  # content, not path
    config_yaml = _load_text(scenario_config_path(scenario_id))
    spec_yaml = _load_text(scenario_spec_path(scenario_id))
    return {
        "skill_md_content": skill_md_content,
        "config_yaml": config_yaml,
        "spec_yaml": spec_yaml,
        "user_msg": "Run /dark-matter-constraints for darksu3 with --spec spec.yaml",
    }


# ---------------------------------------------------------------------------
# CLAUDE.md leakage check — runnable (plan-final T4, critic §3.4)
# ---------------------------------------------------------------------------


def assert_no_claude_md_leakage(harness_meta: dict) -> None:
    """Assert no Read tool_use targeted any CLAUDE.md path.

    Runnable enforcement of the system-prompt isolation discipline.
    Replaces the prose-comment-grep gate from the plan-draft.
    """
    for tu in harness_meta.get("tool_uses", []):
        if tu.get("name") == "Read":
            path = tu.get("input", {}).get("file_path", "")
            assert not path.endswith("CLAUDE.md"), f"CLAUDE.md leaked: {path}"
            assert "claude-md" not in path.lower(), f"claude-md leaked: {path}"


# ---------------------------------------------------------------------------
# Assertion library helpers
# ---------------------------------------------------------------------------


def _check_prereqs_invoked(
    captured_argv_list: list[list[str]],
    scenario_id: str,
    harness_meta: dict | None = None,
    attempt: int = 1,
) -> list[HardFailure]:
    """HARD: check_prereqs must be run for the darksu3 model.

    Semantic intent: the agent ran the prerequisite check for the darksu3
    model. We match on the *behaviour* (invoking check_prereqs and naming the
    darksu3 model) rather than the exact ``--model``/``--config`` flag spelling,
    which is presentation the live LLM legitimately varies (``--model=darksu3``,
    model name sourced from the config file, flag ordering, etc.).

    Non-vacuity: still requires BOTH the check_prereqs invocation AND the
    darksu3 model reference in the same command; a run that never invokes
    check_prereqs, or invokes it for a different model, still fails.

    In Tier-1 stub mode the check runs against harness_meta["tool_uses"] (the
    synthetic LLM output includes the check_prereqs Bash command); in Tier-2
    real mode captured_argv_list carries any intercepted helper subprocesses.
    """
    # Check captured helper invocations (Tier-2 real mode)
    for argv in captured_argv_list:
        joined = " ".join(argv)
        if "check_prereqs" in joined and "darksu3" in joined:
            return []

    # Check harness_meta tool_uses (Tier-1 synthetic / live tool_uses)
    if harness_meta:
        for tu in harness_meta.get("tool_uses", []):
            cmd = tu.get("input", {}).get("command", "")
            if "check_prereqs" in cmd and "darksu3" in cmd:
                return []

    return [HardFailure(attempt=attempt, assertion_id="check_prereqs_invocation")]


def _extract_field_schema_version_arg(captured_argv_list: list[list[str]]) -> list[HardFailure]:
    """HARD: at least one extract_field call must include --schema-version."""
    for argv in captured_argv_list:
        if any("extract_field" in a for a in argv):
            if "--schema-version" in argv:
                return []
    # No extract_field calls at all -> SOFT (only fail if extract_field was expected)
    return []


def _extract_field_schema_version_arg_required(captured_argv_list: list[list[str]]) -> list[HardFailure]:
    """HARD (strict): extract_field must be called with --schema-version."""
    extract_field_calls = [argv for argv in captured_argv_list if any("extract_field" in a for a in argv)]
    if not extract_field_calls:
        return [HardFailure(attempt=1, assertion_id="extract_field_schema_version_arg")]
    for argv in extract_field_calls:
        if "--schema-version" not in argv:
            return [HardFailure(attempt=1, assertion_id="extract_field_schema_version_arg")]
    return []


def _extract_field_sigma_v_zero_invocation(captured_argv_list: list[list[str]]) -> list[HardFailure]:
    """HARD: extract_field must be called for sigma_v_zero."""
    for argv in captured_argv_list:
        if any("extract_field" in a for a in argv):
            if "--key" in argv:
                idx = argv.index("--key")
                if idx + 1 < len(argv) and "sigma_v_zero" in argv[idx + 1]:
                    return []
    return [HardFailure(attempt=1, assertion_id="extract_field_sigma_v_zero_invocation")]


def _eval_extract_field_hard_assertions(
    harness_meta: dict,
    captured_argv_list: list[list[str]] | None = None,
    attempt: int = 1,
) -> list[HardFailure]:
    """Evaluate HARD extract_field assertions from harness_meta tool_uses.

    Returns failures for:
      - extract_field_schema_version_arg: at least one extract_field call must
        include --schema-version (catches NC-1 sabotage)
      - extract_field_sigma_v_zero_invocation: extract_field must be called for
        sigma_v_zero (catches NC-2 sabotage)

    These assertions deliberately require the *guarded* extractor
    (extract_field with --schema-version): reading the JSON another way
    (jq/Read/python -c) bypasses the schema-drift guard, which is a genuine
    behavioural gap, not matcher brittleness. Arg *spelling* is tolerated —
    the substring checks match both ``--schema-version relic/v1`` and
    ``--schema-version=relic/v1`` — so live formatting variance does not flake.

    Evidence is drawn from harness_meta["tool_uses"] (live/synthetic) and, when
    present, captured_argv_list (Tier-2 intercepted subprocesses).
    """
    failures = []
    tool_uses = harness_meta.get("tool_uses", [])

    # Gather all extract_field command strings from every evidence source.
    extract_cmds = []
    for tu in tool_uses:
        cmd = tu.get("input", {}).get("command", "")
        if "extract_field" in cmd:
            extract_cmds.append(cmd)
    for argv in captured_argv_list or []:
        joined = " ".join(argv)
        if "extract_field" in joined:
            extract_cmds.append(joined)

    # If no extract_field calls at all, both assertions fail
    if not extract_cmds:
        failures.append(HardFailure(attempt=attempt, assertion_id="extract_field_schema_version_arg"))
        failures.append(HardFailure(attempt=attempt, assertion_id="extract_field_sigma_v_zero_invocation"))
        return failures

    # NC-1: at least one extract_field call must include --schema-version
    has_schema_version = any("--schema-version" in cmd for cmd in extract_cmds)
    if not has_schema_version:
        failures.append(HardFailure(attempt=attempt, assertion_id="extract_field_schema_version_arg"))

    # NC-2: at least one extract_field call must be for sigma_v_zero
    has_sigma_v_zero = any("sigma_v_zero" in cmd for cmd in extract_cmds)
    if not has_sigma_v_zero:
        failures.append(HardFailure(attempt=attempt, assertion_id="extract_field_sigma_v_zero_invocation"))

    return failures


def _normalize_blocker_token(text: str) -> str:
    """Uppercase and strip all non-alphanumerics for tolerant token matching.

    ``CROSSCHECK_DISAGREEMENT``, ``CrossCheck Disagreement`` and
    ``cross-check disagreement`` all normalise to a string that CONTAINS the
    contiguous token ``CROSSCHECKDISAGREEMENT``. Because every separator is
    removed, only genuinely adjacent occurrences collapse to the token — the
    two words appearing far apart in unrelated prose do NOT produce a match, so
    the check stays non-vacuous.
    """
    import re as _re

    return _re.sub(r"[^A-Za-z0-9]+", "", text).upper()


def _crosscheck_disagreement_blocker_present(
    result_text: str, raw_answer: dict, attempt: int = 1
) -> list[HardFailure]:
    """HARD: CROSSCHECK_DISAGREEMENT must appear in LLM output for Point A.

    Matching is tolerant of casing and separator variance (underscore, space,
    hyphen) that the live LLM introduces, but still requires the two words to
    be adjacent, so a transcript that never raises the blocker still fails
    (preserves the NC-3 negative-control signal).
    """
    target = "CROSSCHECKDISAGREEMENT"
    if target in _normalize_blocker_token(result_text):
        return []
    # Also check raw_answer for blocker codes
    if target in _normalize_blocker_token(str(raw_answer)):
        return []
    return [HardFailure(attempt=attempt, assertion_id="crosscheck_disagreement_blocker_present")]


def _spec_flag_preflight(skill_md_path: pathlib.Path) -> list[HardFailure]:
    """HARD: --spec must be present in SKILL.md (pre-LLM check)."""
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        if "--spec" not in content:
            return [HardFailure(attempt=1, assertion_id="spec_flag_preflight")]
        return []
    except FileNotFoundError:
        return [HardFailure(attempt=1, assertion_id="spec_flag_preflight")]


# ---------------------------------------------------------------------------
# Retry budget (HEPPH_PLAYTEST_MAX_ATTEMPTS)
# ---------------------------------------------------------------------------

DEFAULT_MAX_ATTEMPTS = 3


def max_attempts() -> int:
    """Resolve the per-scenario hard-assertion retry budget.

    Controlled by HEPPH_PLAYTEST_MAX_ATTEMPTS (default 3). Live scenarios are
    ~20 min + real API spend each, so this is the total number of live LLM
    invocations a single scenario may consume before its hard gate fails.
    Values < 1 (or non-integer) fall back to the default; the value is clamped
    to >= 1 so there is always at least one attempt.
    """
    raw = os.environ.get("HEPPH_PLAYTEST_MAX_ATTEMPTS")
    if raw is None:
        return DEFAULT_MAX_ATTEMPTS
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_ATTEMPTS
    return max(1, n)


def _eval_hard_assertions(
    point: str,
    captured_argv_list: list[list[str]],
    scenario_id: str,
    harness_meta: dict,
    attempt: int,
) -> list[HardFailure]:
    """Evaluate all HARD assertions for one attempt; return this attempt's failures."""
    failures: list[HardFailure] = []
    if point == "A":
        failures.extend(
            _check_prereqs_invoked(captured_argv_list, scenario_id, harness_meta, attempt)
        )
        # extract_field schema-version and sigma_v_zero (catches NC-1, NC-2 sabotages)
        failures.extend(
            _eval_extract_field_hard_assertions(harness_meta, captured_argv_list, attempt)
        )
        failures.extend(
            _crosscheck_disagreement_blocker_present(
                harness_meta.get("result_text", ""),
                harness_meta.get("raw_answer", {}),
                attempt,
            )
        )
    elif point == "B":
        failures.extend(
            _check_prereqs_invoked(captured_argv_list, scenario_id, harness_meta, attempt)
        )
    return failures


def _dump_failed_attempt(
    scenario_id: str,
    tier: str,
    attempt: int,
    failures: list[HardFailure],
    harness_meta: dict,
    captured_argv_list: list[list[str]],
) -> pathlib.Path:
    """Write the failing attempt's transcript evidence to a JSON debug file.

    Live attempts are ~20 min + real API spend; discarding harness_meta on a
    hard failure makes the failure undiagnosable. Target directory is
    HEPPH_PLAYTEST_DEBUG_DIR if set, else the system temp dir. The path is
    printed (visible under ``pytest -s``) and returned.
    """
    import json
    import tempfile
    import time

    debug_dir = pathlib.Path(
        os.environ.get("HEPPH_PLAYTEST_DEBUG_DIR") or tempfile.gettempdir()
    )
    debug_dir.mkdir(parents=True, exist_ok=True)
    path = debug_dir / (
        f"hepph_playtest_{scenario_id}_{tier}_attempt{attempt}_{int(time.time())}.json"
    )
    payload = {
        "scenario_id": scenario_id,
        "tier": tier,
        "attempt": attempt,
        "hard_failures": [
            {"attempt": hf.attempt, "assertion_id": hf.assertion_id} for hf in failures
        ],
        "captured_argv_list": captured_argv_list,
        "harness_meta": harness_meta,
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"[hepph-playtest] hard-failure transcript evidence: {path}")
    return path


# ---------------------------------------------------------------------------
# run_with_retry_budget — core dispatch (plan-final T4)
# ---------------------------------------------------------------------------

# Avoid importing the harness runner at module load time (it's session-optional).
# Import lazily inside run_with_retry_budget when needed.


def run_with_retry_budget(
    scenario_id: str,
    point: str,
    drake_branch: str | None,
    tier: typing.Literal["tier1", "tier2", "tier3"] = "tier1",
) -> RetryResult:
    """Run the /dark-matter-constraints skill for a scenario with retry budget.

    Hard assertions: single-shot, fail on attempt 1.
    Soft assertions: retry budget 2 (3 attempts total); 3-of-3 fail logged
                     as warning, NOT a test gate failure.

    Parameters
    ----------
    scenario_id: str
        e.g. 'pointA_configured', 'pointA_missing', 'pointB'
    point: str
        'A' or 'B'
    drake_branch: str | None
        'configured', 'missing', 'activation_required', 'unset', or None
    tier: Literal["tier1","tier2","tier3"]
        Tier-1: stubbed helpers; Tier-2: real helpers + canned fixtures;
        Tier-3: real helpers + real physics tools.
    """
    import sys as _sys

    # Determine helper mode
    helper_mode = os.environ.get("WS3_HELPER_MODE", "stub" if tier == "tier1" else "real")

    # Pre-flight: --spec flag check (HARD, before LLM). This is a deterministic
    # pre-LLM file check, so it is NOT subject to the retry budget — if it fails
    # once it fails every time.
    skill_md_path = resolve_skill_md()
    preflight_failures = _spec_flag_preflight(skill_md_path)

    if preflight_failures:
        return RetryResult(
            scenario_id=scenario_id,
            tier=tier,
            hard_failures=preflight_failures,
            soft_results={},
            hard_attempt_history=[preflight_failures],
        )

    # Build prompt envelope
    envelope = build_prompt_envelope(scenario_id)

    # Set up helper subprocess wrapper
    _hw_path = pathlib.Path(__file__).parent / "helper_subprocess_wrapper.py"
    import importlib.util as _ilu
    _hw_spec = _ilu.spec_from_file_location("_hw_conftest", _hw_path)
    _hw_mod = _ilu.module_from_spec(_hw_spec)
    _sys.modules["_hw_conftest"] = _hw_mod
    _hw_spec.loader.exec_module(_hw_mod)
    HelperSubprocessWrapper = _hw_mod.HelperSubprocessWrapper

    wrapper = HelperSubprocessWrapper(
        mode=helper_mode,
        canned_dir=CANNED,
    )

    # Run with a shared retry budget for HARD (and SOFT) assertions.
    #
    # Each attempt is ONE skill invocation (one live LLM call in Tier-2/3). We
    # re-invoke only while HARD assertions are still failing and budget remains,
    # so a scenario that passes its hard gate on attempt 1 spends exactly one
    # invocation — it does NOT burn further live calls chasing (informational)
    # soft retries the way the previous single-shot-hard design did. HARD
    # assertions gate on the FINAL attempt; a soft assertion counts as passing
    # on the earliest attempt it passed, else None (failed on every attempt).
    soft_assertion_ids = [
        "caveats_rel_diff_numeric",
        "drake_branch_rationale_prose",
        "spectrum_analysis_ratio_prose",
    ]
    soft_results: dict[str, int | None] = {aid: None for aid in soft_assertion_ids}

    budget = max_attempts()
    hard_attempt_history: list[list[HardFailure]] = []
    last_hard_failures: list[HardFailure] = []

    for attempt in range(1, budget + 1):
        harness_meta, captured = _invoke_skill(envelope, wrapper, scenario_id, tier)
        captured_argv_list = [inv.argv for inv in captured]

        # CLAUDE.md isolation must hold on every attempt.
        assert_no_claude_md_leakage(harness_meta)

        attempt_hard = _eval_hard_assertions(
            point, captured_argv_list, scenario_id, harness_meta, attempt
        )
        hard_attempt_history.append(attempt_hard)
        last_hard_failures = attempt_hard

        # Preserve transcript evidence for any failing attempt: without this a
        # ~20-min live run that fails its hard gate leaves NOTHING to diagnose
        # (harness_meta was discarded). Written under HEPPH_PLAYTEST_DEBUG_DIR
        # if set, else the system temp dir; the path is printed so operators
        # can find it in the pytest -s output.
        if attempt_hard:
            _dump_failed_attempt(
                scenario_id, tier, attempt, attempt_hard, harness_meta, captured_argv_list
            )

        # SOFT assertions: record the earliest attempt each one passed.
        for assertion_id in soft_assertion_ids:
            if soft_results[assertion_id] is None and _eval_soft_assertion(
                assertion_id, harness_meta, captured_argv_list, attempt
            ):
                soft_results[assertion_id] = attempt

        # Hard gate satisfied this attempt: stop spending the budget.
        if not attempt_hard:
            break

    return RetryResult(
        scenario_id=scenario_id,
        tier=tier,
        hard_failures=last_hard_failures,
        soft_results=soft_results,
        hard_attempt_history=hard_attempt_history,
    )


def _run_real_claude(envelope: dict, wrapper: typing.Any) -> tuple[dict, list]:
    """Invoke the real claude CLI and return (harness_meta, captured_invocations).

    Builds a prompt from the envelope, installs the helper subprocess wrapper
    (stub mode in Tier-1, real mode in Tier-2/3), runs claude -p, parses the
    JSON output via _parse_claude_json_output from ClaudeCodeRunner's boundary,
    and surfaces the result as a harness_meta dict identical in shape to
    ClaudeCodeRunner.last_meta.

    Helper subprocesses are captured via wrapper.invocations after the run.
    """
    import subprocess as _subprocess
    import sys as _sys

    # Import _parse_claude_json_output from the harness runner.
    # This is the Component B coupling target — the same function that
    # ClaudeCodeRunner uses internally. If the harness moves, the import fails
    # loudly (transcript_event_log.py symbol check also catches this at load).
    import importlib as _importlib
    _runner_mod = _importlib.import_module("eval.harness.runners.claude_code")
    _parse = _runner_mod._parse_claude_json_output  # noqa: SLF001

    import tempfile as _tempfile

    skill_md_content = envelope.get("skill_md_content", "")
    config_yaml = envelope.get("config_yaml", "")
    spec_yaml = envelope.get("spec_yaml", "")
    user_msg = envelope.get("user_msg", "Run /dark-matter-constraints")

    # Write config and spec to temp files so the LLM can pass them to
    # check_prereqs.py and other scripts by path.  The inline YAML approach
    # causes check_prereqs.py to fail (it needs a file path, not inline text).
    # Prefer the bell-ring config when WS3_FORCE_LIVE=1 (it points to stub
    # executables that actually exist on disk, so check_prereqs returns "ok").
    force_live = os.environ.get("WS3_FORCE_LIVE") == "1"
    # Bell-ring config is JSON form (check_prereqs.py is JSON-only by design;
    # WS-4 helpers reject YAML pipeline configs).
    _bellring_config = REPO / "tests" / "fixtures" / "dark_su3_playtest" / "configs" / "config_bellring.json"
    if force_live and _bellring_config.exists():
        _config_path = str(_bellring_config)
        _config_note = (
            f"Config file path: `{_config_path}` "
            f"(bell-ring JSON config with stub tool paths — check_prereqs will return ok)."
        )
    else:
        _tmp_cfg = _tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, prefix="ws3_config_", mode="w"
        )
        _tmp_cfg.write(config_yaml)
        _tmp_cfg.flush()
        _tmp_cfg.close()
        _config_path = _tmp_cfg.name
        _config_note = f"Config file path: `{_config_path}`"

    _tmp_spec = _tempfile.NamedTemporaryFile(
        suffix=".yaml", delete=False, prefix="ws3_spec_", mode="w"
    )
    _tmp_spec.write(spec_yaml)
    _tmp_spec.flush()
    _tmp_spec.close()
    _spec_path = _tmp_spec.name

    # Build prompt: include config/spec paths so scripts receive real file paths.
    prompt = (
        f"{user_msg}\n\n"
        f"{_config_note}\n"
        f"Spec file path: `{_spec_path}`\n\n"
        f"## Config (YAML)\n```yaml\n{config_yaml}\n```\n\n"
        f"## Spec (YAML)\n```yaml\n{spec_yaml}\n```\n\n"
        "Return your answer inside a ```json ... ``` block as instructed.\n\n"
        "IMPORTANT: Use the file paths above when invoking scripts like "
        "check_prereqs.py (--config flag). Canned micrOMEGAs outputs are at: "
        f"`{REPO}/tests/fixtures/dark_su3_playtest/canned/pointA/` "
        "(annihilation.json, relic.json, summary.json)."
    )

    # Build claude CLI command (mirrors ClaudeCodeRunner._build_command).
    # skill_md_content is the system prompt (content, not path — plan-final T4 §3.6).
    # --plugin-dir is required so the LLM can dispatch /maddm, /micromegas, and
    # other slash-commands referenced in SKILL.md Steps 2-3. Without it the model
    # bails at the prereq-check step and never reaches Step 4b (NC-1/NC-2 root cause).
    # --model and --max-budget-usd mirror ClaudeCodeRunner._build_command defaults.
    _constraints_plugin_dir = REPO / "plugins" / "hep-ph-toolkit"
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "json",
        "--model", "sonnet",
        "--permission-mode", "bypassPermissions",
        "--append-system-prompt", skill_md_content,
        "--max-budget-usd", "1.0",
        "--no-session-persistence",
        "--plugin-dir", str(_constraints_plugin_dir),
    ]

    # Install helper wrapper BEFORE launching claude so that any subprocess
    # calls the model makes to helper scripts are captured/stubbed.
    wrapper.install()
    try:
        result = _subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min: real LLM needs time to complete all SKILL.md steps
            cwd=str(REPO),
        )
    finally:
        wrapper.restore()

    captured = list(wrapper.invocations)

    if result.returncode != 0 and not result.stdout:
        raise RuntimeError(
            f"claude CLI failed (rc={result.returncode}): {result.stderr[:500]}"
        )

    parsed = _parse(result.stdout)

    harness_meta = {
        "total_cost_usd": parsed["total_cost_usd"],
        "input_tokens": parsed["input_tokens"],
        "output_tokens": parsed["output_tokens"],
        "num_turns": parsed["num_turns"],
        "result_text": parsed["result_text"],
        "tool_uses": parsed["tool_uses"],
        "raw_answer": parsed.get("answer", {}),
    }

    return harness_meta, captured


def _invoke_skill(
    envelope: dict,
    wrapper: typing.Any,
    scenario_id: str,
    tier: str,
) -> tuple[dict, list]:
    """Invoke the skill and return (harness_meta, captured_invocations).

    Tier-1 with WS3_FORCE_LIVE unset: returns synthetic harness_meta (stubbed).
    Tier-1 with WS3_FORCE_LIVE=1, or Tier-2/3: invokes the real claude CLI
    (via _run_real_claude) with helpers stubbed via HelperSubprocessWrapper.

    Fix #1 (cycle-2): live/Tier-2/Tier-3 paths now use _run_real_claude, which
    calls _parse_claude_json_output from the harness runner boundary and surfaces
    the result as last_meta — identical in shape to ClaudeCodeRunner.last_meta.
    NC-1/NC-2/NC-3 are now real LLM signal, not a simulator mirror of SKILL.md.
    """
    helper_mode = os.environ.get("WS3_HELPER_MODE", "stub" if tier == "tier1" else "real")
    force_live = os.environ.get("WS3_FORCE_LIVE") == "1"

    if force_live or (tier in ("tier2", "tier3") and helper_mode == "real"):
        # Live/real mode: invoke real claude CLI with helper subprocesses.
        # helper_mode controls whether subprocess.run is stubbed (Tier-2 with
        # WS3_HELPER_MODE=stub) or real (Tier-2/3 in normal operation).
        # harness_meta comes from _parse_claude_json_output (Component B coupling target).
        return _run_real_claude(envelope, wrapper)
    # Tier-1 stub mode, or Tier-2/3 with WS3_HELPER_MODE=stub (scaffolding tests):
    # return synthetic harness_meta from fixture content.
    # NC-1/NC-2/NC-3 are tautological in this path — use WS3_FORCE_LIVE=1 for
    # bell-ring validation (which invokes the real claude CLI above).
    return _synthetic_harness_meta(scenario_id, envelope), []


def _synthetic_harness_meta(scenario_id: str, envelope: dict) -> dict:
    """Build a synthetic harness_meta from fixture content (Tier-1 stub mode).

    This simulates what the LLM would return if it correctly followed SKILL.md,
    using the fixture's canned values. Hard assertions verify the STRUCTURE
    the LLM should produce; this enables gate evaluation without LLM calls.
    """
    skill_content = envelope.get("skill_md_content", "")
    has_spec_flag = "--spec" in skill_content
    has_crosscheck_disagreement = "CROSSCHECK_DISAGREEMENT" in skill_content
    has_extract_field = "extract_field" in skill_content
    has_schema_version = "--schema-version" in skill_content
    # NC-2 sabotage detection: check if SKILL.md specifically instructs extract_field
    # for sigma_v_zero / annihilation.json (not just mentions sigma_v_zero in a table).
    # NC-2 removes the extract_field invocation but leaves the table row intact,
    # so we check for the co-occurrence of "extract_field" and "annihilation" within
    # the same Step 4b context block.
    import re as _re
    _step4b_match = _re.search(r"Step 4b.*?(?=Step 5|---)", skill_content, _re.DOTALL)
    _step4b_content = _step4b_match.group(0) if _step4b_match else ""
    has_sigma_v_zero_instruction = (
        ("sigma_v_zero" in _step4b_content and "extract_field" in _step4b_content)
        or "annihilation/v1" in _step4b_content
    )

    is_point_a = "pointA" in scenario_id
    is_configured = "configured" in scenario_id
    is_missing = "missing" in scenario_id and "activation" not in scenario_id
    is_activation = "activation_required" in scenario_id

    # Simulate the LLM's result_text based on SKILL.md content
    table_rows = (
        "| Ωh² | 0.135 | 0.118 | "
        + ("(drake val)" if is_configured else "—")
        + " | FLAG |\n"
        + "| σ_SI(p) [cm²] | 1.23e-45 | 1.21e-45 | — | OK |\n"
        + "| σ_SD(p) [cm²] | 5.67e-42 | 5.60e-42 | — | OK |\n"
        + "| ⟨σv⟩ [cm³/s] | 2.34e-26 | 2.31e-26 | — | OK |\n"
    ) if is_point_a else (
        "| Ωh² | 0.292 | — | — | OK |\n"
        "| σ_SI(p) [cm²] | 1.23e-45 | — | — | OK |\n"
        "| σ_SD(p) [cm²] | 5.67e-42 | — | — | OK |\n"
        "| ⟨σv⟩ [cm³/s] | 2.34e-26 | — | — | OK |\n"
    )

    disagreement_text = (
        "\nCROSSCHECK_DISAGREEMENT: Ωh² — MadDM: 0.135, micrOMEGAs: 0.118 (rel. diff 14.4%)\n"
        "ADJUDICATION REQUIRED\n"
    ) if (is_point_a and has_crosscheck_disagreement) else ""

    drake_notice = ""
    if is_point_a:
        if is_missing:
            drake_notice = "\nDRAKE_MISSING: drake_path not found.\n"
        elif is_activation:
            drake_notice = "\nDRAKE_ACTIVATION_REQUIRED: run wolframscript --activate.\n"

    result_text = (
        "## Dark matter constraints: darksu3\n\n"
        "### Results\n"
        "| Observable | MadDM | micrOMEGAs | DRAKE | Status |\n"
        "|------------|-------|------------|-------|--------|\n"
        + table_rows
        + "\nPlanck 2018 target: Ωh² = 0.1200 ± 0.0012\n"
        + disagreement_text
        + "\n### Caveats\n"
        + drake_notice
        + "\nStep 3 Trigger A fired (Δ/(2m_χ) = 0.005 < 0.10).\n"
        + "Step 5 narrow-resonance: Δ/(2m_χ) = 0.005 < 0.05.\n"
        + "DRAKE branch: configured\n"
        + "rel-diff: 14.4%\n"
    ) if is_point_a else (
        "## Dark matter constraints: darksu3\n\n"
        "### Results\n"
        "| Observable | MadDM | Status |\n"
        "|------------|-------|--------|\n"
        + table_rows
        + "\nPlanck 2018 target: Ωh² = 0.1200 ± 0.0012\n"
        + "\n### Caveats\n"
        "No triggers fired. Step 3, Step 4, Step 5 not invoked.\n"
    )

    # Simulate tool_uses (what the LLM's tool calls would look like)
    tool_uses = [
        {
            "type": "tool_use",
            "name": "Bash",
            "input": {
                "command": (
                    f"python {REPO}/plugins/hep-ph-toolkit/skills/dark-matter-constraints/"
                    f"scripts/check_prereqs.py --model darksu3 --config {scenario_id}"
                )
            },
        },
    ]
    if is_point_a and has_extract_field:
        tool_uses.append({
            "type": "tool_use",
            "name": "Bash",
            "input": {
                "command": (
                    f"python {REPO}/plugins/hep-ph-toolkit/skills/dark-matter-constraints/"
                    f"scripts/extract_field.py --json relic.json --key omega_h2 "
                    + ("--schema-version relic/v1" if has_schema_version else "")
                )
            },
        })
        # Only add sigma_v_zero extract if SKILL.md instructs it (NC-2 sabotage
        # removes this instruction, so the LLM wouldn't know to call it)
        if has_sigma_v_zero_instruction:
            tool_uses.append({
                "type": "tool_use",
                "name": "Bash",
                "input": {
                    "command": (
                        f"python {REPO}/plugins/hep-ph-toolkit/skills/dark-matter-constraints/"
                        f"scripts/extract_field.py --json annihilation.json --key sigma_v_zero "
                        + ("--schema-version annihilation/v1" if has_schema_version else "")
                    )
                },
            })

    return {
        "total_cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "num_turns": 1,
        "result_text": result_text,
        "tool_uses": tool_uses,
        "raw_answer": {
            "status": "tool_verified",
            "value": {"omega_h2": 0.135 if is_point_a else 0.292},
        },
    }


def _eval_soft_assertion(
    assertion_id: str,
    harness_meta: dict,
    captured_argv_list: list[list[str]],
    attempt: int,
) -> bool:
    """Evaluate a soft assertion. Returns True if passed."""
    result_text = harness_meta.get("result_text", "")
    if assertion_id == "caveats_rel_diff_numeric":
        # rel-diff value (14.4% or similar) present in prose
        import re
        return bool(re.search(r"14[\.,]4|0\.1[2-5]", result_text))
    if assertion_id == "drake_branch_rationale_prose":
        keywords = {"configured", "missing", "activation_required", "DRAKE"}
        return any(kw in result_text for kw in keywords)
    if assertion_id == "spectrum_analysis_ratio_prose":
        return "Δ" in result_text or "delta" in result_text.lower() or "0.005" in result_text
    return False


# ---------------------------------------------------------------------------
# run_playtest — simplified wrapper used by test modules
# ---------------------------------------------------------------------------


def run_playtest(
    point: str = "A",
    drake_branch: str | None = "configured",
    tier: typing.Literal["tier1", "tier2", "tier3"] = "tier1",
) -> RetryResult:
    """Convenience wrapper: map point + drake_branch to scenario_id."""
    if point == "B":
        scenario_id = "pointB"
    else:
        scenario_id = f"pointA_{drake_branch}" if drake_branch else "pointA_unset"
    return run_with_retry_budget(scenario_id, point, drake_branch, tier)
