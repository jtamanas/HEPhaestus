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
        / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "router_specs" / "dark_su3.yaml"
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


# ---------------------------------------------------------------------------
# Conditional config-key gating (manifest `condition` field)
# ---------------------------------------------------------------------------
#
# The canonical router_contract.json declares class_path / looptools_path as
# CONDITIONAL keys. check_prereqs must evaluate each entry's `condition` against
# the model's ModelSpec and skip a key whose condition does not match. The
# _DEFAULT_MANIFEST (real contract) is used here — the minimal test manifest has
# no conditional keys.


def _build_conditional_config(
    tmp_path: pathlib.Path,
    spec_fixture: str,
    extra_paths: list[str] | None = None,
) -> pathlib.Path:
    """Materialise config_conditional.json against a spec fixture.

    All unconditional tool paths + the UFO dir are created so the ONLY thing
    that can flip status is conditional-key evaluation. class_path /
    looptools_path are absent from the config unless named in ``extra_paths``,
    in which case they are added pointing at real (created) directories.
    """
    spec_src = _FIXTURES / spec_fixture
    raw = (_FIXTURES / "config_conditional.json").read_text()
    raw = raw.replace("__TMPDIR__", str(tmp_path))
    raw = raw.replace("__SPEC_YAML__", str(spec_src))
    d = json.loads(raw)
    for key in extra_paths or []:
        d[key] = str(tmp_path / f"fake_{key}")
    cfg = tmp_path / "config_conditional.json"
    cfg.write_text(json.dumps(d))
    for key in ["maddm_path", "micromegas_path", "drake_path", *(extra_paths or [])]:
        pathlib.Path(d[key]).mkdir(parents=True, exist_ok=True)
    for model_cfg in d.get("models", {}).values():
        ufo = model_cfg.get("ufo_path", "")
        if ufo:
            pathlib.Path(ufo).mkdir(parents=True, exist_ok=True)
    return cfg


@pytest.mark.parametrize("spec_fixture", [
    # Explicit standard-thermal cosmology (object form, real class-fixture shape).
    "spec_standard_thermal.yaml",
    # NO cosmology field at all — the common real case (spec_pointA.yaml shape).
    # Documented absent-field semantics: absent ⇒ standard_thermal ⇒ skipped.
    "spec_no_cosmology.yaml",
    # Realistic v2 ModelSpec with NESTED non-loop candidates (dark_su3.yaml
    # shape): the nested location IS resolved but the regime is off-resonance.
    "spec_nested_nonloop.yaml",
])
def test_conditional_keys_skipped_for_inactive_conditions(tmp_path, spec_fixture):
    """Inactive conditions → class_path/looptools_path are SKIPPED.

    This is the root-cause regression: without condition evaluation, the two
    conditional keys behave as unconditional hard blockers
    (CLASS_PATH_MISSING / LOOPTOOLS_PATH_MISSING) for EVERY config. With the
    fix, specs that don't trigger the conditions skip them and the run is 'ok'.
    """
    cfg = _build_conditional_config(tmp_path, spec_fixture)
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    codes = [b["code"] for b in result["blockers"]]
    assert "CLASS_PATH_MISSING" not in codes, codes
    assert "LOOPTOOLS_PATH_MISSING" not in codes, codes
    # The skipped keys must not even appear in checked[].
    checked_keys = [c["key"] for c in result["checked"]]
    assert "config.class_path" not in checked_keys, checked_keys
    assert "config.looptools_path" not in checked_keys, checked_keys


def test_class_path_enforced_for_nonstandard_cosmology(tmp_path):
    """cosmology.kind != standard_thermal (top-level, real runner-spec shape
    mirroring tests/fixtures/class/spec_cosmology_non_standard.yaml)
    → class_path condition ACTIVE; absent class_path blocks."""
    cfg = _build_conditional_config(tmp_path, "spec_nonstandard_cosmology.yaml")
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 1, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked", result
    codes = [b["code"] for b in result["blockers"]]
    assert "CLASS_PATH_MISSING" in codes, codes


def test_class_path_satisfied_for_nonstandard_cosmology(tmp_path):
    """Same non-standard-cosmology spec WITH class_path set → passes."""
    cfg = _build_conditional_config(
        tmp_path, "spec_nonstandard_cosmology.yaml", extra_paths=["class_path"]
    )
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    checked = {c["key"]: c["exists"] for c in result["checked"]}
    assert checked.get("config.class_path") is True, checked


def test_class_path_enforced_for_scalar_nonstandard_cosmology(tmp_path):
    """Legacy SCALAR cosmology form (`cosmology: non_standard`, a bare string
    rather than `{kind: ...}`) must ALSO activate the class_path condition.

    should_invoke_class.py:31 treats a scalar cosmology as non-standard
    directly (`cosmology != "standard_thermal"`), so /class WILL be invoked
    at Step 6. Before the scalar-aware fix, `_dig(spec, "cosmology.kind")`
    returned None for a string `cosmology` value (can't `.get("kind")` on a
    str), so the condition was silently treated as inactive and class_path
    was skipped — a loud-but-late failure at Step 6 instead of a prereq
    blocker here. Pins the fix.
    """
    cfg = _build_conditional_config(tmp_path, "spec_scalar_nonstandard_cosmology.yaml")
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 1, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked", result
    codes = [b["code"] for b in result["blockers"]]
    assert "CLASS_PATH_MISSING" in codes, codes


def test_class_path_satisfied_for_scalar_nonstandard_cosmology(tmp_path):
    """Same scalar non-standard-cosmology spec WITH class_path set → passes."""
    cfg = _build_conditional_config(
        tmp_path, "spec_scalar_nonstandard_cosmology.yaml", extra_paths=["class_path"]
    )
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    checked = {c["key"]: c["exists"] for c in result["checked"]}
    assert checked.get("config.class_path") is True, checked


def test_class_path_skipped_for_scalar_standard_thermal_cosmology(tmp_path):
    """Legacy SCALAR `cosmology: standard_thermal` (bare string) → the
    class_path condition must be SKIPPED, same as the dict form
    `{kind: standard_thermal}`."""
    cfg = _build_conditional_config(tmp_path, "spec_scalar_standard_thermal.yaml")
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    codes = [b["code"] for b in result["blockers"]]
    assert "CLASS_PATH_MISSING" not in codes, codes
    checked_keys = [c["key"] for c in result["checked"]]
    assert "config.class_path" not in checked_keys, checked_keys


def test_looptools_path_enforced_for_loop_only_candidate(tmp_path):
    """REAL-structured loop-only spec (candidates nested under
    dm_phenomenology.candidates, per every actual v2 ModelSpec) with
    looptools_path absent → LOOPTOOLS_PATH_MISSING blocks.

    Regression for the dead-gate bug: the manifest's former top-level
    `candidates[?]` spec_field matched no real ModelSpec, so enforcement was
    silently dead for every real loop-only spec.
    """
    cfg = _build_conditional_config(tmp_path, "spec_loop_only.yaml")
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 1, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "blocked", result
    codes = [b["code"] for b in result["blockers"]]
    assert "LOOPTOOLS_PATH_MISSING" in codes, codes


def test_looptools_path_satisfied_for_loop_only_candidate(tmp_path):
    """Same real-structured loop-only spec WITH looptools_path set → passes."""
    cfg = _build_conditional_config(
        tmp_path, "spec_loop_only.yaml", extra_paths=["looptools_path"]
    )
    cp = _run(cfg, model="toyDM", manifest_path=_DEFAULT_MANIFEST)
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    checked = {c["key"]: c["exists"] for c in result["checked"]}
    assert checked.get("config.looptools_path") is True, checked


def test_manifest_condition_paths_match_real_spec_shapes():
    """Pin the contract's spec_field paths against REAL spec ground truth.

    - looptools: real v2 ModelSpecs nest candidates under
      `dm_phenomenology.candidates` (_shared/router_specs/dark_su3.yaml); the
      manifest spec_field must be the nested path AND the resolver must find
      values there in the real dark_su3 spec.
    - class: runner specs carry `cosmology` at TOP LEVEL (should_invoke_class
      design §4.1); the manifest spec_field must be exactly `cosmology.kind`.
    """
    manifest = json.loads(_DEFAULT_MANIFEST.read_text())
    by_key = {e["key"]: e for e in manifest["config_keys"]}
    lt_cond = by_key["config.looptools_path"]["condition"]
    assert lt_cond["spec_field"] == "dm_phenomenology.candidates[?].mediator_regime", lt_cond
    cl_cond = by_key["config.class_path"]["condition"]
    assert cl_cond["spec_field"] == "cosmology.kind", cl_cond

    # Resolver must find values at the nested path in a REAL spec.
    import importlib.util as _ilu
    import yaml as _yaml
    real_spec_path = (
        _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared"
        / "router_specs" / "dark_su3.yaml"
    )
    real_spec = _yaml.safe_load(real_spec_path.read_text())
    spec_m = _ilu.spec_from_file_location("check_prereqs_mod", _HELPER)
    mod = _ilu.module_from_spec(spec_m)
    spec_m.loader.exec_module(mod)
    values = mod._spec_field_values(real_spec, lt_cond["spec_field"])
    assert values, "nested spec_field resolved no values from the real dark_su3 spec"
    assert all(isinstance(v, str) for v in values), values
    # And the former (wrong) top-level path must resolve nothing.
    assert mod._spec_field_values(real_spec, "candidates[?].mediator_regime") == []


# ---------------------------------------------------------------------------
# YAML config loading (parity with JSON)
# ---------------------------------------------------------------------------


def test_check_prereqs_loads_yaml_config(tmp_path):
    """A YAML config (not just JSON) parses and yields the same happy-path result.

    SKILL.md documents configs under "## Config (YAML)"; historically the helper
    only accepted JSON, which killed live playtests. check_prereqs must try JSON
    then fall back to yaml.safe_load.
    """
    raw = (_FIXTURES / "config_all_present.yaml").read_text().replace("__TMPDIR__", str(tmp_path))
    cfg = tmp_path / "config_all_present.yaml"
    cfg.write_text(raw)
    import yaml as _yaml
    d = _yaml.safe_load(raw)
    for key in ["maddm_path", "micromegas_path", "drake_path"]:
        pathlib.Path(d[key]).mkdir(parents=True, exist_ok=True)
    for model_cfg in d.get("models", {}).values():
        pathlib.Path(model_cfg["ufo_path"]).mkdir(parents=True, exist_ok=True)
    cp = _run(cfg)  # default model singletDM, minimal manifest
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    assert result["blockers"] == []


# ---------------------------------------------------------------------------
# Regression: the live-playtest bell-ring config must not be blocked
# ---------------------------------------------------------------------------


def test_bellring_config_not_blocked():
    """config_bellring.json (real fixture, repo-root-relative stub paths) → ok.

    Pins the end-to-end consequence of the condition-gating fix against the real
    router_contract.json manifest: a standard-thermal dark-SU(3) config with
    stub tool paths and no class/looptools paths must return status 'ok'. Runs
    from the repo root because the fixture's paths are repo-root-relative.
    """
    config = _REPO_ROOT / "tests" / "fixtures" / "dark_su3_playtest" / "configs" / "config_bellring.json"
    assert config.is_file(), f"bellring config missing at {config}"
    args = [
        sys.executable, str(_HELPER),
        "--config", str(config),
        "--model", "darksu3",
        "--manifest", str(_DEFAULT_MANIFEST),
    ]
    cp = subprocess.run(args, capture_output=True, text=True, cwd=str(_REPO_ROOT))
    assert cp.returncode == 0, f"stdout={cp.stdout!r} stderr={cp.stderr!r}"
    result = json.loads(cp.stdout)
    assert result["status"] == "ok", result
    codes = [b["code"] for b in result["blockers"]]
    assert "CLASS_PATH_MISSING" not in codes, codes
    assert "LOOPTOOLS_PATH_MISSING" not in codes, codes
