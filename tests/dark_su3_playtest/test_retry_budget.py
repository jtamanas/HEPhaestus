"""Deterministic unit tests for the Tier-2 retry-budget machinery.

These tests drive ``run_with_retry_budget`` and the individual HARD-assertion
matchers against *canned / fake* transcripts by monkeypatching the skill
invocation. They NEVER invoke the real ``claude`` CLI, so they run under a plain
``python -m pytest`` with no live env var and no API spend.

Coverage:
  - retry exhaustion (every attempt fails -> hard gate fails, N attempts spent)
  - retry success on attempt 2 (flake recovers -> hard gate passes)
  - budget honoured / short-circuit (pass on attempt 1 spends exactly 1 call)
  - HEPPH_PLAYTEST_MAX_ATTEMPTS is configurable
  - matcher robustness to live-LLM formatting variance WITHOUT vacuity
  - soft-assertion earliest-pass semantics
"""

from __future__ import annotations

import pytest

from tests.dark_su3_playtest import conftest as C


# ---------------------------------------------------------------------------
# Fake-transcript builders
# ---------------------------------------------------------------------------


def _bash(cmd: str) -> dict:
    return {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}


def _passing_pointA_meta(
    *,
    check_prereqs: bool = True,
    schema_version: bool = True,
    sigma_v_zero: bool = True,
    crosscheck: bool = True,
    prereqs_cmd: str | None = None,
    crosscheck_text: str = "CROSSCHECK_DISAGREEMENT: Ωh² MadDM vs micrOMEGAs",
) -> dict:
    """Build a fake harness_meta for Point A; toggles let us drop each signal."""
    tool_uses: list[dict] = []
    if check_prereqs:
        tool_uses.append(_bash(prereqs_cmd or "python check_prereqs.py --model darksu3 --config /tmp/c.json"))
    if schema_version or sigma_v_zero:
        tool_uses.append(
            _bash(
                "python extract_field.py --json relic.json --key omega_h2 "
                + ("--schema-version relic/v1" if schema_version else "")
            )
        )
    if sigma_v_zero:
        tool_uses.append(
            _bash(
                "python extract_field.py --json annihilation.json --key sigma_v_zero "
                + ("--schema-version annihilation/v1" if schema_version else "")
            )
        )
    result_text = (
        "## Dark matter constraints\nrel-diff: 14.4%\nDRAKE branch: configured\n"
        "Δ/(2m_χ) = 0.005\n" + (crosscheck_text + "\n" if crosscheck else "")
    )
    return {
        "total_cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "num_turns": 1,
        "result_text": result_text,
        "tool_uses": tool_uses,
        "raw_answer": {"status": "tool_verified"},
    }


class _ScriptedInvoke:
    """Callable stand-in for conftest._invoke_skill returning scripted metas.

    Each call consumes the next (meta) in ``metas`` (last one repeats if the
    budget exceeds the script). Records the number of calls made.
    """

    def __init__(self, metas: list[dict]) -> None:
        self._metas = metas
        self.calls = 0

    def __call__(self, envelope, wrapper, scenario_id, tier):  # noqa: ANN001
        idx = min(self.calls, len(self._metas) - 1)
        self.calls += 1
        return self._metas[idx], []  # empty captured (live-like)


def _patch_invoke(monkeypatch, metas: list[dict]) -> _ScriptedInvoke:
    scripted = _ScriptedInvoke(metas)
    monkeypatch.setattr(C, "_invoke_skill", scripted)
    return scripted


# ---------------------------------------------------------------------------
# max_attempts()
# ---------------------------------------------------------------------------


def test_max_attempts_default(monkeypatch):
    monkeypatch.delenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", raising=False)
    assert C.max_attempts() == C.DEFAULT_MAX_ATTEMPTS == 3


@pytest.mark.parametrize("value,expected", [("1", 1), ("5", 5), ("0", 1), ("-3", 1), ("junk", 3)])
def test_max_attempts_env(monkeypatch, value, expected):
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", value)
    assert C.max_attempts() == expected


# ---------------------------------------------------------------------------
# Retry budget behaviour
# ---------------------------------------------------------------------------


def test_pass_on_attempt_1_spends_one_call(monkeypatch):
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "3")
    scripted = _patch_invoke(monkeypatch, [_passing_pointA_meta()])
    result = C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    assert result.hard_failures == []
    assert scripted.calls == 1, "must short-circuit after a passing attempt"
    assert len(result.hard_attempt_history) == 1


def test_retry_exhaustion(monkeypatch):
    """Every attempt fails -> hard gate fails and the whole budget is spent."""
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "3")
    failing = _passing_pointA_meta(crosscheck=False)  # drop the crosscheck signal
    scripted = _patch_invoke(monkeypatch, [failing])
    result = C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    ids = [hf.assertion_id for hf in result.hard_failures]
    assert "crosscheck_disagreement_blocker_present" in ids
    assert scripted.calls == 3, "must spend the full budget when never passing"
    assert len(result.hard_attempt_history) == 3
    # final-attempt failures are numbered with the final attempt
    assert all(hf.attempt == 3 for hf in result.hard_failures)
    # per-attempt history preserves the attempt number
    assert result.hard_attempt_history[0][0].attempt == 1


def test_retry_success_on_attempt_2(monkeypatch):
    """Attempt 1 flakes, attempt 2 passes -> hard gate passes, budget not exhausted."""
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "3")
    fail = _passing_pointA_meta(sigma_v_zero=False)
    ok = _passing_pointA_meta()
    scripted = _patch_invoke(monkeypatch, [fail, ok])
    result = C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    assert result.hard_failures == []
    assert scripted.calls == 2, "should stop as soon as an attempt passes"
    assert len(result.hard_attempt_history) == 2
    # attempt 1 recorded the sigma_v_zero flake; attempt 2 is clean
    assert any(
        hf.assertion_id == "extract_field_sigma_v_zero_invocation"
        for hf in result.hard_attempt_history[0]
    )
    assert result.hard_attempt_history[1] == []


def test_budget_of_one_is_single_shot(monkeypatch):
    """Budget=1 reproduces the old single-shot behaviour (one attempt, no retry)."""
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "1")
    fail = _passing_pointA_meta(crosscheck=False)
    ok = _passing_pointA_meta()
    scripted = _patch_invoke(monkeypatch, [fail, ok])
    result = C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    assert scripted.calls == 1
    assert result.hard_failures  # failed, no retry granted


def test_soft_earliest_pass_semantics(monkeypatch):
    """A soft assertion is credited to the earliest attempt on which it passed."""
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "3")
    # Attempt 1: hard fails (no crosscheck) AND soft caveats_rel_diff missing.
    a1 = _passing_pointA_meta(crosscheck=False)
    a1["result_text"] = "DRAKE branch: configured\nΔ = 0.005\n"  # no 14.4 / 0.1x
    # Attempt 2: hard still fails, but rel-diff prose now present.
    a2 = _passing_pointA_meta(crosscheck=False)
    # Attempt 3: everything passes.
    a3 = _passing_pointA_meta()
    _patch_invoke(monkeypatch, [a1, a2, a3])
    result = C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    assert result.hard_failures == []
    assert result.soft_results["caveats_rel_diff_numeric"] == 2


# ---------------------------------------------------------------------------
# Matcher robustness (non-vacuous)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,should_match",
    [
        ("CROSSCHECK_DISAGREEMENT here", True),
        ("CrossCheck Disagreement detected", True),
        ("cross-check disagreement on Ωh²", True),
        ("blocker: CROSSCHECK-DISAGREEMENT", True),
        # non-vacuous: the two words far apart in unrelated prose must NOT match
        ("the cross-check found no material disagreement anywhere", False),
        ("everything agreed; no blocker raised", False),
    ],
)
def test_crosscheck_matcher_robust_but_not_vacuous(text, should_match):
    fails = C._crosscheck_disagreement_blocker_present(text, {}, attempt=1)
    assert (fails == []) == should_match


@pytest.mark.parametrize(
    "cmd,should_pass",
    [
        ("python check_prereqs.py --model darksu3 --config /tmp/c.json", True),
        ("python check_prereqs.py --model=darksu3 --config=/tmp/c.json", True),  # equals form
        ("check_prereqs.py --config /tmp/c.json --model darksu3", True),  # reordered
        # non-vacuous: wrong model must still fail
        ("python check_prereqs.py --model othermodel --config /tmp/c.json", False),
        # non-vacuous: never invoked must fail
        ("python extract_field.py --key omega_h2", False),
    ],
)
def test_check_prereqs_matcher_robust_but_not_vacuous(cmd, should_pass):
    meta = {"tool_uses": [_bash(cmd)], "result_text": "", "raw_answer": {}}
    fails = C._check_prereqs_invoked([], "pointA_configured", meta, attempt=1)
    assert (fails == []) == should_pass


def test_extract_field_requires_guarded_extractor():
    """Reading the field WITHOUT extract_field --schema-version must still fail.

    This keeps the NC-1 schema-drift guard non-vacuous: a jq/Read bypass does
    not satisfy the assertion.
    """
    meta = {
        "tool_uses": [
            _bash("jq '.sigma_v_zero' annihilation.json"),
            _bash("cat relic.json"),
        ],
        "result_text": "",
        "raw_answer": {},
    }
    fails = C._eval_extract_field_hard_assertions(meta, [], attempt=1)
    ids = {hf.assertion_id for hf in fails}
    assert "extract_field_schema_version_arg" in ids
    assert "extract_field_sigma_v_zero_invocation" in ids


def test_extract_field_equals_form_passes():
    meta = {
        "tool_uses": [
            _bash("extract_field.py --json relic.json --key omega_h2 --schema-version=relic/v1"),
            _bash("extract_field.py --json annihilation.json --key sigma_v_zero"),
        ],
        "result_text": "",
        "raw_answer": {},
    }
    fails = C._eval_extract_field_hard_assertions(meta, [], attempt=1)
    assert fails == []


def test_failed_attempt_dumps_transcript_evidence(monkeypatch, tmp_path):
    """Each failing attempt writes a JSON evidence file to HEPPH_PLAYTEST_DEBUG_DIR."""
    import json

    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("HEPPH_PLAYTEST_DEBUG_DIR", str(tmp_path))
    failing = _passing_pointA_meta(crosscheck=False)
    _patch_invoke(monkeypatch, [failing])
    C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")

    dumps = sorted(tmp_path.glob("hepph_playtest_pointA_configured_tier2_attempt*.json"))
    assert len(dumps) == 2, f"expected one dump per failing attempt, got {dumps}"
    payload = json.loads(dumps[0].read_text())
    assert payload["scenario_id"] == "pointA_configured"
    assert payload["attempt"] in (1, 2)
    assert "crosscheck_disagreement_blocker_present" in [
        f["assertion_id"] for f in payload["hard_failures"]
    ]
    assert "result_text" in payload["harness_meta"]


def test_passing_attempt_writes_no_dump(monkeypatch, tmp_path):
    monkeypatch.setenv("HEPPH_PLAYTEST_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("HEPPH_PLAYTEST_DEBUG_DIR", str(tmp_path))
    _patch_invoke(monkeypatch, [_passing_pointA_meta()])
    C.run_with_retry_budget("pointA_configured", "A", "configured", tier="tier2")
    assert list(tmp_path.glob("hepph_playtest_*.json")) == []


def test_config_tempfile_is_json_check_prereqs_can_parse():
    """Tier-2 config temp file must be JSON: check_prereqs.py is JSON-only.

    Root cause of the deterministic live Tier-2 failures: the harness wrote
    the scenario config verbatim as YAML, so check_prereqs returned
    PREREQ_HELPER_INTERNAL on every live run and the agent bailed at step 1.
    """
    import json
    import pathlib

    config_yaml = C.scenario_config_path("pointA_configured").read_text(encoding="utf-8")
    path = pathlib.Path(C._write_config_tempfile(config_yaml))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))  # must be valid JSON
        assert "models" in data and "darksu3" in data["models"]
        assert data.get("maddm_path"), "tool paths must survive the conversion"
    finally:
        path.unlink()


def test_config_tempfile_empty_yaml_yields_empty_object():
    import json
    import pathlib

    path = pathlib.Path(C._write_config_tempfile(""))
    try:
        assert json.loads(path.read_text(encoding="utf-8")) == {}
    finally:
        path.unlink()


def test_extract_field_evidence_from_captured_argv():
    """captured_argv_list is also honoured as an evidence source (Tier-2 real)."""
    meta = {"tool_uses": [], "result_text": "", "raw_answer": {}}
    captured = [
        ["python", "extract_field.py", "--json", "relic.json", "--key", "omega_h2", "--schema-version", "relic/v1"],
        ["python", "extract_field.py", "--json", "annihilation.json", "--key", "sigma_v_zero"],
    ]
    fails = C._eval_extract_field_hard_assertions(meta, captured, attempt=1)
    assert fails == []
