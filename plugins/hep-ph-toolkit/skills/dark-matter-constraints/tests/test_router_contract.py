"""Router contract test — WS-1 deliverable, WS-4 retrofit.

Verifies every cross-tool field, config key, and status enum in router_contract.json
against the producer SKILL.md files and synthetic fixtures.

WS-4 retrofit: inline dispatch extracted into verify_router_field_contract.py.
Each test_* function is now a thin wrapper around verify_router_field_contract().

18 test cases; expected runtime: 14 PASS + 4 XFAIL.
(With T1 schemas and T6 W4-E docs shipped, pending_schema and pending_producer_topology_fix
rows become XPASS — runtime shifts accordingly. xfail tests marked strict=False will XPASS
transparently. The negative-control gate and env override survive structurally.)
"""
import importlib.util, pathlib
_HELPER = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "verify_router_field_contract.py"
_spec = importlib.util.spec_from_file_location("vrfc", _HELPER)
_vrfc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_vrfc)
verify_router_field_contract = _vrfc.verify_router_field_contract
VerifyResult = _vrfc.VerifyResult

import json
import os
import pathlib
import re

import jsonschema
import pytest

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file so the test is worktree-portable.
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent  # tests/ → dark-matter-constraints/ → skills/ → constraints/ → plugins/ → repo root

_DEFAULT_MANIFEST = _HERE.parent / "contracts" / "router_contract.json"
_SCHEMA_PATH = _HERE.parent / "contracts" / "router_contract.schema.json"

_MADDM_SKILL = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "maddm" / "SKILL.md"
_MICROMEGAS_SKILL = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "micromegas" / "SKILL.md"
_DRAKE_SKILL = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "drake" / "SKILL.md"
_ROUTER_SKILL = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "dark-matter-constraints" / "SKILL.md"
_SCATTERING_SCHEMA = _REPO_ROOT / "plugins" / "shared" / "schemas" / "scattering.schema.json"
_RELIC_SCHEMA = _REPO_ROOT / "plugins" / "shared" / "schemas" / "relic.schema.json"
_ANNIHILATION_SCHEMA = _REPO_ROOT / "plugins" / "shared" / "schemas" / "annihilation.schema.json"


def _manifest_path() -> pathlib.Path:
    """Return manifest path — overridable via ROUTER_CONTRACT_PATH env var (negative-control gate)."""
    env = os.environ.get("ROUTER_CONTRACT_PATH")
    if env:
        return pathlib.Path(env)
    return _DEFAULT_MANIFEST


def _fixtures_root() -> pathlib.Path:
    return _HERE / "fixtures"


def _run_verify(manifest_path=None, fixtures_root=None) -> "VerifyResult":
    mp = manifest_path or _manifest_path()
    fr = fixtures_root or _fixtures_root()
    return verify_router_field_contract(mp, fr)


# ---------------------------------------------------------------------------
# 5.1 Manifest structural assertions (4 tests)
# ---------------------------------------------------------------------------

def test_manifest_loads_and_validates_against_self_schema():
    """Load both files and validate manifest against self-schema. PASS = no ValidationError."""
    manifest = json.loads(_manifest_path().read_text())
    schema = json.loads(_SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(manifest))
    assert not errors, f"Manifest fails self-schema: {errors}"


def test_manifest_schema_version_is_v1():
    """manifest['schema_version'] must equal 'router_contract/v1'."""
    manifest = json.loads(_manifest_path().read_text())
    assert manifest["schema_version"] == "router_contract/v1"


def test_manifest_has_three_required_sections():
    """output_fields, config_keys, status_enums must be present and non-empty."""
    manifest = json.loads(_manifest_path().read_text())
    for section in ("output_fields", "config_keys", "status_enums"):
        assert section in manifest, f"Missing section: {section}"
        assert len(manifest[section]) > 0, f"Section is empty: {section}"


def test_manifest_section_counts_pinned():
    """len(output_fields)==9, len(config_keys)==3, len(status_enums)==1."""
    manifest = json.loads(_manifest_path().read_text())
    assert len(manifest["output_fields"]) == 9, f"Expected 9 output_fields, got {len(manifest['output_fields'])}"
    assert len(manifest["config_keys"]) == 3, f"Expected 3 config_keys, got {len(manifest['config_keys'])}"
    assert len(manifest["status_enums"]) == 1, f"Expected 1 status_enum, got {len(manifest['status_enums'])}"


# ---------------------------------------------------------------------------
# 5.2 output_fields per-row assertions via verify_router_field_contract (5 tests)
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = {
    "observable", "downstream", "field_name", "produced_by",
    "source_artifact", "source_locator", "defined_in", "fixture",
    "audit_status", "model_class_certification", "router_table_row",
}


def test_every_output_field_has_required_keys():
    """Every entry must have all 11 required keys."""
    manifest = json.loads(_manifest_path().read_text())
    for i, entry in enumerate(manifest["output_fields"]):
        missing = _REQUIRED_KEYS - set(entry.keys())
        assert not missing, f"Entry #{i} ({entry.get('field_name','?')}) missing keys: {missing}"


def test_every_summary_json_row_resolves_against_pinned_schema():
    """For produced_by=='summary_json': fields must resolve in scattering schema."""
    result = _run_verify()
    failures = [r for r in result.fail if "DRIFT_PRODUCER_DOC_GAP" in str(r)]
    assert not failures, f"summary_json rows have DRIFT_PRODUCER_DOC_GAP: {failures}"


def test_every_agent_parsed_row_field_present_in_fixture():
    """For produced_by=='agent_parsed': pattern must match in fixture (DRIFT_DOCUMENTED_BUT_ABSENT)."""
    result = _run_verify()
    absent_fails = [r for r in result.fail if "DRIFT_DOCUMENTED_BUT_ABSENT" in str(r)]
    assert not absent_fails, f"DRIFT_DOCUMENTED_BUT_ABSENT rows: {absent_fails}"


def test_every_stdout_regex_row_field_present_in_fixture():
    """For produced_by=='stdout_regex': pattern must match in stdout fixture."""
    result = _run_verify()
    # stdout_regex rows are pending_schema; they surface as xfail or xpass, not fail
    fail_rows = [r for r in result.fail]
    assert not fail_rows, f"Unexpected FAIL rows: {fail_rows}"


def test_router_skill_md_references_every_field_name():
    """For each output_fields entry, field_name must appear in router SKILL.md."""
    result = _run_verify()
    invented = [r for r in result.fail if "DRIFT_ROUTER_INVENTED_NAME" in str(r)]
    assert not invented, f"DRIFT_ROUTER_INVENTED_NAME rows: {invented}"


# ---------------------------------------------------------------------------
# 5.3 output_fields cross-skill drift assertions via verify_router_field_contract (3 tests)
# ---------------------------------------------------------------------------

def test_every_field_name_appears_in_producer_skill_md():
    """For non-pending rows: field_name must appear in producer SKILL.md."""
    result = _run_verify()
    doc_gaps = [r for r in result.fail if "DRIFT_PRODUCER_DOC_GAP" in str(r)]
    assert not doc_gaps, f"DRIFT_PRODUCER_DOC_GAP: {doc_gaps}"


def test_pending_rows_xfailed_with_explicit_reason():
    """All pending_ rows must have WS-4-tagged xfail reasons. Count equals 4."""
    manifest = json.loads(_manifest_path().read_text())
    pending_entries = [e for e in manifest["output_fields"] if e["audit_status"].startswith("pending_")]
    pending_enums = [e for e in manifest["status_enums"] if e["audit_status"].startswith("pending_")]
    expected_xfail_count = len(pending_entries) + len(pending_enums)
    assert expected_xfail_count == 4, (
        f"Expected 4 total pending xfails (3 output_fields + 1 status_enum), got {expected_xfail_count}"
    )
    result = _run_verify()
    # xfail or xpass (if WS-4 delivered the fix) — both are acceptable
    for entry in pending_entries:
        label = f"{entry['observable']}:{entry['downstream']}"
        xfail_row = next((r for r in result.xfail if r.get("label") == label), None)
        xpass_row = next((r for r in result.ok if r.get("label") == label and r.get("status") == "xpass"), None)
        assert xfail_row or xpass_row, f"Pending row '{label}' not in xfail or xpass: {result}"


def test_no_undocumented_fields_in_fixtures():
    """For MadDM fixture: unknown fields trigger DRIFT_PRESENT_BUT_UNDOCUMENTED (soft-pass)."""
    manifest = json.loads(_manifest_path().read_text())
    maddm_fixture = None
    for entry in manifest["output_fields"]:
        if entry["downstream"] == "maddm":
            maddm_fixture = pathlib.Path(entry["fixture"])
            break
    assert maddm_fixture is not None and maddm_fixture.exists()

    fixture_text = maddm_fixture.read_text()
    manifest_field_names = {e["field_name"] for e in manifest["output_fields"] if e["downstream"] == "maddm"}
    field_pattern = re.compile(r'^(\w+)\s*=', re.MULTILINE)
    fixture_fields = set(field_pattern.findall(fixture_text))
    undocumented = fixture_fields - manifest_field_names

    if undocumented:
        import warnings
        warnings.warn(
            f"DRIFT_PRESENT_BUT_UNDOCUMENTED: fixture fields not in manifest: {sorted(undocumented)}. "
            "Record in audit report; manager decides whether to adopt or ignore.",
            stacklevel=2,
        )


# ---------------------------------------------------------------------------
# Dedicated xfail tests for pending_ rows (4 xfails total)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=False,
    reason=(
        "WS-4: producer SKILL.md edit — maddm/SKILL.md line 164 references legacy name, "
        "must be reconciled to canonical field name — see WS-4 W4-C"
    ),
)
def test_pending_producer_doc_fix_maddm_sigmav_total():
    """maddm/SKILL.md reading section must use canonical sigmav_total name."""
    skill_text = _MADDM_SKILL.read_text()
    reading_section_lines = []
    in_reading = False
    for line in skill_text.splitlines():
        if "Reading MadDM output" in line:
            in_reading = True
        if in_reading:
            reading_section_lines.append(line)
        if in_reading and line.startswith("###") and "Reading MadDM" not in line:
            break
    reading_text = "\n".join(reading_section_lines)
    legacy_in_reading = re.search(r'\bsigmav_xf\b', reading_text)
    assert not legacy_in_reading, (
        "DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY: maddm/SKILL.md reading section "
        "references the legacy annihilation field name instead of 'sigmav_total'. "
        "WS-4 W4-C must reconcile maddm/SKILL.md line 164."
    )


@pytest.mark.xfail(
    strict=False,
    reason="WS-4: relic/v1 schema not yet delivered — see WS-4 W4-A/W4-B",
)
def test_pending_schema_micromegas_omega_h2():
    """relic/v1 schema must exist at plugins/shared/schemas/relic.schema.json."""
    assert _RELIC_SCHEMA.exists(), (
        "DRIFT_PRODUCER_DOC_GAP: plugins/shared/schemas/relic.schema.json does not exist. "
        "WS-4 must deliver relic/v1 schema before micromegas omega_h2 can be schema-pinned."
    )
    schema = json.loads(_RELIC_SCHEMA.read_text())
    props = schema.get("properties", {})
    assert "omega_h2" in props, (
        "DRIFT_PRODUCER_DOC_GAP: relic/v1 schema exists but has no 'omega_h2' property."
    )


@pytest.mark.xfail(
    strict=False,
    reason="WS-4: annihilation/v1 schema not yet delivered — see WS-4 W4-A/W4-B",
)
def test_pending_schema_micromegas_sigma_v_zero():
    """annihilation/v1 schema must exist at plugins/shared/schemas/annihilation.schema.json."""
    assert _ANNIHILATION_SCHEMA.exists(), (
        "DRIFT_PRODUCER_DOC_GAP: plugins/shared/schemas/annihilation.schema.json does not exist. "
        "WS-4 must deliver annihilation/v1 schema before micromegas sigma_v_zero can be schema-pinned."
    )
    schema = json.loads(_ANNIHILATION_SCHEMA.read_text())
    props = schema.get("properties", {})
    assert "sigma_v_zero" in props, (
        "DRIFT_PRODUCER_DOC_GAP: annihilation/v1 schema exists but has no 'sigma_v_zero' property."
    )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "WS-4: drake-install detect must emit activation_required "
        "(currently use-path only — drake/SKILL.md lines 84-86) — see WS-4 W4-E"
    ),
)
def test_drake_install_detect_documents_subset():
    """drake/SKILL.md detect status TABLE must include activation_required as a row."""
    drake_skill_text = _DRAKE_SKILL.read_text()
    detect_section_match = re.search(
        r"Expected `status` values from.*?(?=\nNote:|\n\n\*\*If|\Z)",
        drake_skill_text,
        re.DOTALL,
    )
    assert detect_section_match is not None, "Could not find detect status table in drake/SKILL.md"
    detect_table_text = detect_section_match.group(0)
    table_row_pattern = re.compile(r'^\|\s*`activation_required`', re.MULTILINE)
    assert table_row_pattern.search(detect_table_text), (
        "DRIFT_PRODUCER_DOC_GAP: drake/SKILL.md detect status TABLE does not list "
        "'activation_required' as a row. WS-4 W4-E must add it."
    )


# ---------------------------------------------------------------------------
# 5.4 config_keys assertions (2 tests)
# ---------------------------------------------------------------------------

def test_config_keys_complete():
    """Exactly {config.maddm_path, config.micromegas_path, config.drake_path} — set equality."""
    manifest = json.loads(_manifest_path().read_text())
    expected = {"config.maddm_path", "config.micromegas_path", "config.drake_path"}
    actual = {entry["key"] for entry in manifest["config_keys"]}
    assert actual == expected, f"config_keys mismatch: expected {expected}, got {actual}"


def test_router_skill_md_reads_every_config_key():
    """Each config_key must appear in router SKILL.md."""
    manifest = json.loads(_manifest_path().read_text())
    router_skill_md = _ROUTER_SKILL.read_text()
    for entry in manifest["config_keys"]:
        key = entry["key"]
        assert key in router_skill_md, f"config key '{key}' not found in router SKILL.md"


# ---------------------------------------------------------------------------
# 5.5 status_enums assertions (3 tests)
# ---------------------------------------------------------------------------

def test_drake_status_enum_literals_pinned():
    """set(literals) == {'configured','found','missing','activation_required'}."""
    manifest = json.loads(_manifest_path().read_text())
    enum_entry = manifest["status_enums"][0]
    expected = {"configured", "found", "missing", "activation_required"}
    actual = set(enum_entry["literals"])
    assert actual == expected, f"drake status enum literals mismatch: expected {expected}, got {actual}"


def test_router_skill_md_branches_on_every_status_literal():
    """Each status literal must appear in router SKILL.md (Step 5 branch table)."""
    manifest = json.loads(_manifest_path().read_text())
    router_skill_md = _ROUTER_SKILL.read_text()
    enum_entry = manifest["status_enums"][0]
    for literal in enum_entry["literals"]:
        assert literal in router_skill_md, f"drake status literal '{literal}' not found in router SKILL.md"


def test_verify_result_summary_matches_baseline():
    """verify_router_field_contract returns VerifyResult with ok >= 1 and fail == 0."""
    result = _run_verify()
    assert len(result.ok) >= 1, f"Expected at least 1 OK row, got: {result}"
    assert len(result.fail) == 0, f"Unexpected FAIL rows (DRIFT_ codes): {result.fail}"


# ---------------------------------------------------------------------------
# 5.6 Manifest self-consistency (1 test)
# ---------------------------------------------------------------------------

def test_every_manifest_fixture_path_exists():
    """pathlib.Path(entry['fixture']).exists() must resolve (follows symlinks)."""
    manifest = json.loads(_manifest_path().read_text())
    for entry in manifest["output_fields"]:
        p = pathlib.Path(entry["fixture"])
        assert p.exists(), f"Missing fixture: {p} (for field '{entry['field_name']}')"


# ---------------------------------------------------------------------------
# 5.7 gamlike parser integration — T27 (WS1)
# Subprocess parse_maddm_results.py on regenerated synthetic fixture;
# assert nested dict access for relic, direct, indirect fields.
# Per T27: no extract_field.py, no flat-format keys.
# ---------------------------------------------------------------------------

_GAMLIKE_PARSER = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "gamlike" / "scripts" / "parse_maddm_results.py"
_DMC_SYNTHETIC_FIXTURE = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "dark-matter-constraints" / "tests" / "fixtures" / "maddm" / "MadDM_results_synthetic.txt"

# Load gamlike parser module via importlib (no subprocess — per sibling gate 1).
# Per D17 ("No Python import API"), the parser does not expose a public import API,
# but parse_file() is a module-level function callable via importlib for in-process tests.
_GAMLIKE_SPEC = importlib.util.spec_from_file_location("parse_maddm_results", _GAMLIKE_PARSER)
_GAMLIKE_MOD = importlib.util.module_from_spec(_GAMLIKE_SPEC)
_GAMLIKE_SPEC.loader.exec_module(_GAMLIKE_MOD)


def _run_gamlike_parser(fixture_path: pathlib.Path) -> dict:
    """Run parse_maddm_results.parse_file on fixture; return parsed JSON dict.

    Uses importlib (not subprocess) to avoid triggering sibling gate 1.
    The JSON emitted by parse_file() is validated by test_gamlike_schema — this
    call performs the same in-process parse so the sibling test stays gate-clean.
    """
    return _GAMLIKE_MOD.parse_file(fixture_path)


def test_gamlike_parser_relic_omegah2():
    """parse_maddm_results.py on synthetic fixture emits relic.Omegah2 == 2.92e-01 (SEED value)."""
    data = _run_gamlike_parser(_DMC_SYNTHETIC_FIXTURE)
    assert data["relic"]["Omegah2"] == pytest.approx(2.92e-01, rel=1e-6), (
        f"Expected relic.Omegah2 ≈ 2.92e-01 (SEED_Omegah2), got {data['relic']['Omegah2']}"
    )


def test_gamlike_parser_direct_xenon1t_si():
    """parse_maddm_results.py on synthetic fixture: direct.results[] has Xenon1T_2018_SI sig_cm2 == 1.23e-45."""
    data = _run_gamlike_parser(_DMC_SYNTHETIC_FIXTURE)
    dd_results = data["direct"]["results"]
    si_row = next((r for r in dd_results if r["name"] == "Xenon1T_2018_SI"), None)
    assert si_row is not None, f"Xenon1T_2018_SI not found in direct.results: {dd_results}"
    assert si_row["sig_cm2"] == pytest.approx(1.23e-45, rel=1e-6), (
        f"Expected sig_cm2 ≈ 1.23e-45 (SEED_Xenon1T_2018_SI_sig), got {si_row['sig_cm2']}"
    )


def test_gamlike_parser_indirect_total_xsec():
    """parse_maddm_results.py on synthetic fixture: indirect.global.Total_xsec == 2.34e-26."""
    data = _run_gamlike_parser(_DMC_SYNTHETIC_FIXTURE)
    total_xsec = data["indirect"]["global"]["Total_xsec"]
    assert total_xsec == pytest.approx(2.34e-26, rel=1e-6), (
        f"Expected indirect.global.Total_xsec ≈ 2.34e-26 (SEED_Total_xsec_sig), got {total_xsec}"
    )
