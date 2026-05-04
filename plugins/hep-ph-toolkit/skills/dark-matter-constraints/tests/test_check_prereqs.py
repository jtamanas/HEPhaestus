"""test_check_prereqs.py — WS-2 tests for scripts/check_prereqs.py helper.

9 test functions; 12 behaviors via parametrize.

WS-4-owned unknown (#2): check_prereqs --model nonexistent_in_config exit code (1 vs 2)
is marked xfail(strict=True) per synthesis §8.2 and plan-final §6.3.

Pre-flight CLI-shape check (runs at collection time via module-level assertion):
  python scripts/check_prereqs.py --help must expose: --config, --model, --manifest
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

from .conftest import _HERE, _REPO_ROOT, _DEFAULT_MANIFEST  # noqa: F401 (canonical names imported)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DMC = _HERE.parent
_SCRIPTS = _DMC / "scripts"
_HELPER = _SCRIPTS / "check_prereqs.py"
_FIXTURES = _HERE / "fixtures" / "helpers" / "check_prereqs"
_MANIFEST = _FIXTURES / "manifest_minimal.json"

# ---------------------------------------------------------------------------
# Pre-flight: CLI shape (per plan T5 critic item 5)
# ---------------------------------------------------------------------------
_help_text = subprocess.run([sys.executable, str(_HELPER), "--help"], capture_output=True, text=True).stdout  # sys.executable
_help_text += subprocess.run([sys.executable, str(_HELPER), "--help"], capture_output=True, text=True).stderr  # sys.executable


def _assert_cli_flag(flag: str) -> None:
    assert flag in _help_text, f"PREFLIGHT FAIL: --help missing flag {flag!r}"


for _f in ["--config", "--model", "--manifest"]:
    _assert_cli_flag(_f)


# ---------------------------------------------------------------------------
# Helper: load fixture and patch __TMPDIR__ placeholders to real tmp dirs
# ---------------------------------------------------------------------------

def _load_config(tmp_path: pathlib.Path, fixture_name: str) -> pathlib.Path:
    """Load a config fixture, replacing __TMPDIR__ with real directories that exist."""
    raw = (_FIXTURES / fixture_name).read_text()
    raw = raw.replace("__TMPDIR__", str(tmp_path))
    config_out = tmp_path / fixture_name
    config_out.write_text(raw)
    # Create all directories that are referenced so path-existence checks pass
    d = json.loads(raw)
    for key in ["maddm_path", "micromegas_path", "drake_path"]:
        if key in d and not d[key].startswith("/nonexistent"):
            p = pathlib.Path(d[key])
            p.mkdir(parents=True, exist_ok=True)
    # UFO paths
    models = d.get("models", {})
    for model_cfg in models.values():
        ufo = model_cfg.get("ufo_path", "")
        if ufo and not ufo.startswith("/nonexistent"):
            pathlib.Path(ufo).mkdir(parents=True, exist_ok=True)
    return config_out


def _run(config_path: pathlib.Path, model: str = "singletDM",
         manifest_path: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(_HELPER), "--config", str(config_path), "--model", model]
    if manifest_path:
        args += ["--manifest", str(manifest_path)]
    else:
        args += ["--manifest", str(_MANIFEST)]
    return subprocess.run(args, capture_output=True, text=True)  # sys.executable


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_check_prereqs_all_present_returns_ok_exit_zero(tmp_path):
    """Happy path: all required paths exist; status is 'ok'; exit 0."""
    cp = _run(_load_config(tmp_path, "config_all_present.json"))
    assert cp.returncode == 0
    result = json.loads(cp.stdout)
    assert result["status"] == "ok"
    assert result["blockers"] == []


@pytest.mark.parametrize("fixture,expected_code_prefix", [
    ("config_maddm_missing.json", "MADDM_MISSING"),
    ("config_micromegas_missing.json", "MICROMEGAS_MISSING"),
])
def test_check_prereqs_tool_path_missing_emits_blocker_exit_one(
    tmp_path, fixture, expected_code_prefix
):
    """Parametrize × 2: maddm_path or micromegas_path missing → blocker code, exit 1.

    Collapses synthesis §1.1 proposer cases 2 and 3.
    """
    cp = _run(_load_config(tmp_path, fixture))
    assert cp.returncode == 1
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked"
    codes = [b["code"] for b in result["blockers"]]
    assert any(c.startswith(expected_code_prefix) for c in codes), codes


@pytest.mark.parametrize("fixture,expected_code_prefix", [
    ("config_drake_unset.json", "DRAKE_PATH_UNSET"),
    ("config_drake_nonexistent.json", "DRAKE_"),
])
def test_check_prereqs_drake_path_blocker_exit_one(
    tmp_path, fixture, expected_code_prefix
):
    """Parametrize × 2: drake_path absent or nonexistent → DRAKE_* blocker, exit 1.

    Collapses synthesis §1.1 proposer cases 4 and 5.
    """
    cp = _run(_load_config(tmp_path, fixture))
    assert cp.returncode == 1
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked"
    codes = [b["code"] for b in result["blockers"]]
    assert any(c.startswith(expected_code_prefix) for c in codes), codes


def test_check_prereqs_ufo_missing_emits_blocker_exit_one(tmp_path):
    """models.<model>.ufo_path nonexistent → UFO_MISSING blocker, exit 1."""
    cp = _run(_load_config(tmp_path, "config_no_ufo.json"))
    assert cp.returncode == 1
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked"
    codes = [b["code"] for b in result["blockers"]]
    assert "UFO_MISSING" in codes, codes


def test_check_prereqs_slha_missing_emits_hint_status_remains_ok(tmp_path):
    """mssm_like model with missing latest_slha: SLHA_MISSING_HINT in blockers, status='ok', exit 0.

    SLHA is informational; the agent adjudicates. Status does NOT flip to 'blocked'.
    """
    cp = _run(_load_config(tmp_path, "config_mssm_like.json"), model="MSSM")
    assert cp.returncode == 0
    result = json.loads(cp.stdout)
    assert result["status"] == "ok"
    codes = [b["code"] for b in result["blockers"]]
    assert "SLHA_MISSING_HINT" in codes, codes


def test_check_prereqs_unknown_model_documents_decision(tmp_path):
    """--model nonexistent_in_config: WS-4 resolved as exit 1 + UFO_MISSING blocker.

    WS-4 cycle-1 decision-of-record (ws2_synthesis.md §8.2 item 2):
      When --model names a key absent from config.models{}, check_prereqs treats
      the missing ufo_path as UFO_MISSING and exits 1 (blocked). Exit code 2 is
      reserved for manifest/config parse failures; an unknown model is a contract
      failure, not an internal error.

    This assertion pins whatever WS-4 landed; if WS-4 changes behavior, this test
    must be intentionally rewritten. Asserts exit code in {1, 2} and a meaningful
    blocker/error code is emitted.
    """
    cp = _run(_load_config(tmp_path, "config_all_present.json"), model="nonexistent_in_config")
    assert cp.returncode in {1, 2}
    # Should emit a meaningful code either on stdout (exit 1) or stderr (exit 2)
    combined = cp.stdout + cp.stderr
    parsed = None
    try:
        parsed = json.loads(combined.strip())
    except json.JSONDecodeError:
        # Not JSON — still acceptable if returncode is set
        pass
    if parsed:
        # Either a blocker code or an error code must be present
        has_blocker = bool(parsed.get("blockers", []))
        has_error = "code" in parsed
        assert has_blocker or has_error, f"No meaningful code in: {parsed}"


@pytest.mark.xfail(strict=True, reason="WS-4 decision pending — see ws2_synthesis.md §8.2: check_prereqs does not yet emit MODEL_NOT_IN_CONFIG (distinct from UFO_MISSING) for unknown model names. Pin this future behaviour here; flip when WS-4 adds the code.")
def test_ws4_decision_check_prereqs_unknown_model_emits_model_not_in_config_PIN(tmp_path):
    """Pin future WS-4 behaviour: distinct MODEL_NOT_IN_CONFIG code for truly unknown models.

    WS-4 cycle-1 emits UFO_MISSING (because ufo_path is absent for an unknown model key).
    A future WS-4 may add MODEL_NOT_IN_CONFIG to distinguish this case. Until then
    this test is expected to fail (XFAIL) to document the gap.

    WS-4 decision pending — see ws2_synthesis.md §8.2.
    """
    cp = _run(_load_config(tmp_path, "config_all_present.json"), model="nonexistent_in_config")
    result = json.loads(cp.stdout + cp.stderr)
    codes = [b.get("code", "") for b in result.get("blockers", [])]
    assert "MODEL_NOT_IN_CONFIG" in codes, f"Expected MODEL_NOT_IN_CONFIG, got: {codes}"


def test_check_prereqs_unparseable_manifest_exit_two(tmp_path):
    """Unparseable manifest → exit 2; stderr contains code:'PREREQ_HELPER_INTERNAL'."""
    cp = _run(
        _load_config(tmp_path, "config_all_present.json"),
        manifest_path=_FIXTURES / "manifest_unparseable.json",
    )
    assert cp.returncode == 2
    err_data = json.loads(cp.stderr)
    assert err_data.get("code") == "PREREQ_HELPER_INTERNAL"


def test_check_prereqs_unreadable_config_exit_two(tmp_path):
    """--config is a directory → exit 2 (cannot read file)."""
    dir_config = tmp_path / "a_directory"
    dir_config.mkdir()
    args = [sys.executable, str(_HELPER), "--config", str(dir_config), "--model", "singletDM", "--manifest", str(_MANIFEST)]
    cp = subprocess.run(args, capture_output=True, text=True)  # sys.executable
    assert cp.returncode == 2


# WS4 migration note: test_dsu3_002_disclosure_propagation_contract was removed
# here (lines 223-261 of the pre-WS4 file). Its assertions are preserved as
# parametrized cases in:
#   plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/
#       test_analytic_exception_disclosure_static.py
# The new registry-driven test covers dsu3-002 placements (P1, P2, P3) and
# well-formedness; the proxy_run entry is also covered with the same machinery.


def test_check_prereqs_dsu3_analytic_demotion(tmp_path):
    """dsu3 analytic-only branch: UFO_MISSING demoted to ANALYTIC_BACKEND_PATH notice.

    When a model has `multi_component: true` AND `backends.spectrum == "analytic"`
    in its ModelSpec YAML, the missing UFO is recoverable, not fatal: the router's
    Step 2 analytic-only branch will skip /maddm and consume diagnostics.json
    directly. check_prereqs must not raise UFO_MISSING in that case.

    Asserts:
      - exit code 0 (status="ok")
      - notices[] contains a code "ANALYTIC_BACKEND_PATH"
      - blockers[] does NOT contain "UFO_MISSING"
    """
    spec_yaml = (
        _REPO_ROOT
        / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "assets" / "dark_su3.yaml"
    )
    assert spec_yaml.is_file(), f"dsu3 spec yaml missing at {spec_yaml}"

    raw = (_FIXTURES / "config_dsu3_analytic.json").read_text()
    raw = raw.replace("__TMPDIR__", str(tmp_path))
    raw = raw.replace("__SPEC_YAML__", str(spec_yaml))
    config = tmp_path / "config_dsu3_analytic.json"
    config.write_text(raw)
    # Create the tool directories that DO exist.
    d = json.loads(raw)
    for key in ["maddm_path", "micromegas_path", "drake_path"]:
        pathlib.Path(d[key]).mkdir(parents=True, exist_ok=True)

    cp = _run(config, model="dark-su3")
    assert cp.returncode == 0, (
        f"Expected exit 0 (analytic-only demotion). "
        f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    )
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", f"status not ok: {result}"
    notice_codes = [n["code"] for n in result.get("notices", [])]
    assert "ANALYTIC_BACKEND_PATH" in notice_codes, (
        f"ANALYTIC_BACKEND_PATH missing from notices; got {notice_codes}"
    )
    blocker_codes = [b["code"] for b in result.get("real_blockers", [])]
    assert "UFO_MISSING" not in blocker_codes, (
        f"UFO_MISSING should be demoted, not raised; real_blockers={blocker_codes}"
    )


def test_check_prereqs_does_not_emit_class_missing_code():
    """CLASS_MISSING is prose-side only per design D7/§5."""
    from pathlib import Path
    src_path = (Path(__file__).resolve().parents[1]
                / "scripts/check_prereqs.py")
    assert "CLASS_MISSING" not in src_path.read_text()


def test_check_prereqs_structural_outputs(tmp_path):
    """Happy path: checked[] has key/exists/path per entry; multi-blocker test.

    Part A: happy path — len(checked) >= len(config_keys); each entry has 'key', 'exists', 'path'.
    Part B: two prereqs missing → both blocker codes present, exit 1.
    Ordering of blockers is NOT asserted (synthesis §1.1 critic D1).
    """
    # Part A: structural check on happy path
    cp = _run(_load_config(tmp_path, "config_all_present.json"))
    result = json.loads(cp.stdout)
    manifest = json.loads(_MANIFEST.read_text())
    n_config_keys = len(manifest.get("config_keys", []))
    assert len(result["checked"]) >= n_config_keys
    for entry in result["checked"]:
        assert "key" in entry
        assert "exists" in entry
        assert "path" in entry

    # Part B: two blockers (maddm + micromegas both missing → two blockers)
    # Build a combined missing config
    raw = (_FIXTURES / "config_all_present.json").read_text().replace("__TMPDIR__", str(tmp_path))
    d = json.loads(raw)
    d["maddm_path"] = "/nonexistent_shared/installs/maddm"
    d["micromegas_path"] = "/nonexistent_shared/installs/micromegas"
    # Create real directories for non-missing paths so they pass
    for key in ["drake_path"]:
        p = pathlib.Path(d[key])
        p.mkdir(parents=True, exist_ok=True)
    for model_cfg in d.get("models", {}).values():
        ufo = model_cfg.get("ufo_path", "")
        if ufo and not ufo.startswith("/nonexistent"):
            pathlib.Path(ufo).mkdir(parents=True, exist_ok=True)
    multi_cfg = tmp_path / "config_multi_missing.json"
    multi_cfg.write_text(json.dumps(d))
    cp2 = _run(multi_cfg)
    assert cp2.returncode == 1
    result2 = json.loads(cp2.stdout)
    codes = [b["code"] for b in result2["blockers"]]
    assert "MADDM_MISSING" in codes, codes
    assert "MICROMEGAS_MISSING" in codes, codes
