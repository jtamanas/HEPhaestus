# WS-4 Plan Draft — Refactor: helpers + SKILL.md rewrite

**Drafter:** ws4-plan-drafter
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md` (375 lines, design canon); `plan/ws1_plan_final.md` (W4-A..W4-G hand-off + WS-1 T3 inline-test pin); `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (356 lines); `plugins/constraints/skills/micromegas/SKILL.md` (lines 99, 207, 226 region); `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (line 164); `plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 84–86); `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (lines 110–142, `cmd_detect` body); `plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py` (header — direct-path invocation convention).

This draft is binding for sonnet-implementers. Where synthesis §6 already adjudicated (8-item table), this plan transcribes; it does NOT re-decide. Where synthesis was silent on micro-decisions (test path resolution; W4-E unit-test fixture location; W4-D phrasing of `omega_h2`), this plan picks one and flags the choice in §Pre-flight for the plan-critic to challenge.

---

## 1. Goal

Decompose synthesis §1 (4 helpers), §2.1 (compare_dm prose snippet), §3 (SKILL.md rewrite), §4 (W4-A/C/D/E producer edits + W4-E bash fix), §5 (2 new schemas), §7.1 (WS-1 test retrofit) into ordered tasks with mechanically checkable gates. WS-4 ships exactly the helpers, schemas, and SKILL.md edits the lens permits — and rewrites WS-1's `tests/test_router_contract.py` to import from the new helper module so dispatch logic lives in one place.

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint: helpers MUST be model-agnostic; if not provable, route to LLM. |
| `brainstorm/ws4_synthesis.md` | Design canon. §1 helper inventory, §2 compare_dm boundary, §3 SKILL.md rewrite plan, §4 W4-A..W4-E, §5 schema bodies (verbatim JSON), §6 8-item adjudication, §7 cross-WS coordination, §8 explicit out-of-scope. |
| `plan/ws1_plan_final.md` §8 | W4-A..W4-G enumeration + xfail closure mapping. |
| `plan/ws1_plan_final.md` §3 T3 | WS-1's `test_router_contract.py` ships with INLINE dispatch; T6 of this plan refactors it. |
| `plugins/constraints/skills/dark-matter-constraints/SKILL.md` | Source of router prose to rewrite. Preserve-verbatim line-ranges enumerated in synthesis §3.2. |
| `plugins/feynman-diagrams/.../run_formcalc.py` | Direct-path invocation precedent (synthesis §1, §6 row 1). |
| `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` | Lines 128–130 — the 5-line bash insertion site for W4-E. |

---

## 3. Tasks

Eight tasks (T1..T8). Owner classes: `sonnet-implementer` for mechanical authoring of code + verbatim-from-synthesis content, `opus-implementer` for the SKILL.md rewrite (highest judgment), `opus-reviewer` for the final gate. All paths absolute; `$REPO=/Users/yianni/Projects/hep-ph-agents`.

---

### T1 — Schemas: `relic.schema.json` + `annihilation.schema.json`

- **Owner class:** `sonnet-implementer` (synthesis §5 supplies verbatim JSON bodies).
- **Cycle estimate:** 1
- **Depends-on:** none

**Inputs:**
- `ws4_synthesis.md` §5.1 (relic body, lines 230–253), §5.2 (annihilation body, lines 257–282), §5.3 (out-of-scope).
- `plugins/shared/schemas/scattering.schema.json` (style template — Draft 2020-12, `$id` shape, `additionalProperties: false`).

**Outputs:**
- `$REPO/plugins/shared/schemas/relic.schema.json` (NEW)
- `$REPO/plugins/shared/schemas/annihilation.schema.json` (NEW)
- `$REPO/plugins/shared/schemas/tests/fixtures/relic_singletDM_synthetic.json` (NEW — minimal valid fixture for cross-validation gate)
- `$REPO/plugins/shared/schemas/tests/fixtures/annihilation_singletDM_synthetic.json` (NEW — minimal valid fixture)
- `$REPO/plugins/shared/schemas/tests/fixtures/relic_invalid_extra_field.json` (NEW — should fail validation)
- `$REPO/plugins/shared/schemas/tests/fixtures/annihilation_invalid_negative.json` (NEW — should fail validation)

**Acceptance gates:**

```bash
R=$REPO/plugins/shared/schemas/relic.schema.json
A=$REPO/plugins/shared/schemas/annihilation.schema.json
F=$REPO/plugins/shared/schemas/tests/fixtures

# 1. Files exist + parse + draft 2020-12
test -f "$R" && test -f "$A"
python -c "import json; json.load(open('$R')); json.load(open('$A'))"
jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' "$R"
jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' "$A"

# 2. $id pinned (load-bearing for extract_field's schema-version self-check)
jq -e '."$id" == "https://hep-ph-agents/schemas/relic/v1"'        "$R"
jq -e '."$id" == "https://hep-ph-agents/schemas/annihilation/v1"' "$A"

# 3. additionalProperties:false at top level
jq -e '.additionalProperties == false' "$R"
jq -e '.additionalProperties == false' "$A"

# 4. schema_version is a const, not enum/string
jq -e '.properties.schema_version.const == "relic/v1"'        "$R"
jq -e '.properties.schema_version.const == "annihilation/v1"' "$A"

# 5. v→0 convention assertion present in sigma_v_zero description (synthesis §5.2 LOCKED)
jq -e '.properties.sigma_v_zero.description | contains("v→0")'        "$A"
jq -e '.properties.sigma_v_zero.description | contains("sigmav_total")' "$A"

# 6. omega_h2 and sigma_v_zero permit null (oneOf [null, number])
jq -e '[.properties.omega_h2.oneOf[].type] | contains(["null"])'      "$R"
jq -e '[.properties.sigma_v_zero.oneOf[].type] | contains(["null"])' "$A"

# 7. Cross-validation: positive fixtures validate; negative fixtures DO NOT
python -c "
import json, jsonschema
for sch_path, fix_path, expect_ok in [
    ('$R', '$F/relic_singletDM_synthetic.json',          True),
    ('$A', '$F/annihilation_singletDM_synthetic.json',   True),
    ('$R', '$F/relic_invalid_extra_field.json',          False),
    ('$A', '$F/annihilation_invalid_negative.json',      False),
]:
    sch = json.load(open(sch_path)); fix = json.load(open(fix_path))
    v = jsonschema.Draft202012Validator(sch)
    errs = list(v.iter_errors(fix))
    if expect_ok:
        assert not errs, f'expected {fix_path} to validate against {sch_path}: {errs}'
    else:
        assert errs, f'expected {fix_path} to FAIL validation against {sch_path} but it passed'
print('OK')
"
```

---

### T2 — Helper: `check_prereqs.py`

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** none (parallelizable with T1, T3)

**Inputs:**
- `ws4_synthesis.md` §1.1 (full spec: usage, blocker codes, exit grid, manifest dispatch, ~120 LoC).
- `plan/ws1_plan_final.md` §3 T1 (`router_contract.json` `config_keys` shape — drives manifest dispatch).
- `plugins/feynman-diagrams/.../run_formcalc.py` (argparse + JSON-on-stdout style template).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py` (NEW; ~120 lines)
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/__init__.py` (NEW empty — for `importlib` loading by tests)

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py
test -f "$H"
python "$H" --help | grep -F -- "--config"
python "$H" --help | grep -F -- "--model"
python "$H" --help | grep -F -- "--manifest"

# Happy path — fabricate a config that points at existing dirs; expect status:ok exit 0
TMP=$(mktemp -d)
cat > "$TMP/config.json" <<EOF
{"maddm_path":"$TMP","micromegas_path":"$TMP","drake_path":"$TMP",
 "models":{"dummy":{"ufo_path":"$TMP"}}}
EOF
# Manifest stub mirroring config_keys section of router_contract.json
cat > "$TMP/manifest.json" <<EOF
{"schema_version":"router_contract/v1","config_keys":[
 {"key":"config.maddm_path","type":"path_or_bool"},
 {"key":"config.micromegas_path","type":"path_or_bool"},
 {"key":"config.drake_path","type":"path_or_bool"}],
 "output_fields":[],"status_enums":[]}
EOF
python "$H" --config "$TMP/config.json" --model dummy --manifest "$TMP/manifest.json"
test $? -eq 0
python "$H" --config "$TMP/config.json" --model dummy --manifest "$TMP/manifest.json" \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok', d"

# Blocker path — point maddm_path at a nonexistent dir; expect status:blocked exit 1
sed -i.bak "s|$TMP|/nonexistent/path|" "$TMP/config.json"
python "$H" --config "$TMP/config.json" --model dummy --manifest "$TMP/manifest.json"
test $? -eq 1
python "$H" --config "$TMP/config.json" --model dummy --manifest "$TMP/manifest.json" 2>/dev/null \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='blocked'; assert any(b['code']=='MADDM_MISSING' for b in d['blockers']), d"

# Internal-error path — unparseable manifest; expect exit 2
echo "{not json" > "$TMP/manifest.json"
python "$H" --config "$TMP/config.json" --model dummy --manifest "$TMP/manifest.json"
test $? -eq 2
rm -rf "$TMP"
```

---

### T3 — Helper: `detect_drake.py`

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** none (parallelizable with T1, T2)

**Inputs:**
- `ws4_synthesis.md` §1.2 (full spec: usage, status enum branches, manifest dispatch, ~90 LoC).
- `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (the wrapped `detect` subcommand — but T3 helper does not depend on T4's bash fix; it only consumes the JSON output).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py` (NEW; ~90 lines)

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py
test -f "$H"
python "$H" --help | grep -F -- "--config"
python "$H" --help | grep -F -- "--manifest"

TMP=$(mktemp -d)
cat > "$TMP/config.json" <<EOF
{"drake_path":"$TMP"}
EOF
cat > "$TMP/manifest.json" <<EOF
{"schema_version":"router_contract/v1","config_keys":[],"output_fields":[],
 "status_enums":[{"enum_name":"drake_install_detect_status",
  "literals":["configured","found","missing","activation_required"]}]}
EOF

# Stub the detect command via env var (test override per synthesis §1.2)
# Each variant exercises a status branch
for variant in configured found missing activation_required unparseable; do
  case "$variant" in
    configured)         OUT='{"status":"configured","path":"/x","version":"1.0"}' ;;
    found)              OUT='{"status":"found","path":"/x"}' ;;
    missing)            OUT='{"status":"missing"}' ;;
    activation_required) OUT='{"status":"activation_required","path":"/x"}' ;;
    unparseable)        OUT='not json at all' ;;
  esac
  STUB="$TMP/stub_$variant.sh"
  printf '#!/bin/bash\nprintf %%s %q\n' "$OUT" > "$STUB"
  chmod +x "$STUB"
  HEPPH_DRAKE_DETECT_CMD="$STUB" python "$H" --config "$TMP/config.json" --manifest "$TMP/manifest.json"
  test $? -eq 0  # detect_drake exits 0 always per synthesis §1.2
  HEPPH_DRAKE_DETECT_CMD="$STUB" python "$H" --config "$TMP/config.json" --manifest "$TMP/manifest.json" \
    | python -c "
import json, sys
d = json.load(sys.stdin)
v = '$variant'
if v == 'unparseable':
    assert d['status'] == 'unparseable', d
    assert d['router_action'] == 'emit_DRAKE_UNAVAILABLE', d
else:
    assert d['status'] == v, d
"
done
rm -rf "$TMP"
```

---

### T4 — Helper: `extract_field.py` (LOAD-BEARING PRIMITIVE)

- **Owner class:** `opus-implementer` (synthesis §1.3 calls this the linchpin; exit-code grid has 7 distinct rows; getting null-vs-absent semantics wrong silently breaks every router invocation).
- **Cycle estimate:** 2
- **Depends-on:** T1 (uses the new schemas as test material)

**Inputs:**
- `ws4_synthesis.md` §1.3 (full spec: locked exit-code grid, schema-`$id` self-check, ~110 LoC).
- T1's schemas + fixtures.
- `plugins/shared/schemas/scattering.schema.json` (third schema this helper must work against).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py` (NEW; ~110 lines)

**Acceptance gates (exercise every row of the synthesis §1.3 exit-code grid):**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py
F=$REPO/plugins/shared/schemas/tests/fixtures
test -f "$H"
python "$H" --help | grep -F -- "--json"
python "$H" --help | grep -F -- "--key"
python "$H" --help | grep -F -- "--schema-version"

# Row 1: present + numeric → exit 0, value is the number
python "$H" --json "$F/relic_singletDM_synthetic.json" --key omega_h2 --schema-version relic/v1
test $? -eq 0
python "$H" --json "$F/relic_singletDM_synthetic.json" --key omega_h2 --schema-version relic/v1 \
  | python -c "import json,sys; d=json.load(sys.stdin); assert isinstance(d['value'], (int,float)), d; assert d['key']=='omega_h2'; assert d['schema_version']=='relic/v1'"

# Row 2: present + null (oneOf permits) → exit 0, value is null
TMP=$(mktemp -d)
cat > "$TMP/relic_null.json" <<'EOF'
{"schema_version":"relic/v1","m_dm_gev":100.0,"omega_h2":null,
 "source":"micromegas","source_run":"runX","cosmology":"standard_thermal"}
EOF
python "$H" --json "$TMP/relic_null.json" --key omega_h2 --schema-version relic/v1
test $? -eq 0
python "$H" --json "$TMP/relic_null.json" --key omega_h2 --schema-version relic/v1 \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d['value'] is None, d"

# Row 3: KEY ABSENT → exit 1 with code KEY_ABSENT
cat > "$TMP/relic_no_xf.json" <<'EOF'
{"schema_version":"relic/v1","m_dm_gev":100.0,"omega_h2":0.12,
 "source":"micromegas","source_run":"runX","cosmology":"standard_thermal"}
EOF
python "$H" --json "$TMP/relic_no_xf.json" --key xf --schema-version relic/v1
test $? -eq 1
python "$H" --json "$TMP/relic_no_xf.json" --key xf --schema-version relic/v1 2>&1 1>/dev/null \
  | grep -F "KEY_ABSENT"

# Row 4: VERSION DRIFT — manifest's schema_version field disagrees with --schema-version
cat > "$TMP/relic_drift.json" <<'EOF'
{"schema_version":"relic/v2","m_dm_gev":100.0,"omega_h2":0.12,
 "source":"micromegas","source_run":"runX","cosmology":"standard_thermal"}
EOF
python "$H" --json "$TMP/relic_drift.json" --key omega_h2 --schema-version relic/v1
test $? -eq 1
python "$H" --json "$TMP/relic_drift.json" --key omega_h2 --schema-version relic/v1 2>&1 1>/dev/null \
  | grep -F "VERSION_DRIFT"

# Row 5: schema-$id self-check — feed a hand-rolled schema whose $id ends in /v2 with --schema-version relic/v1
mkdir -p "$TMP/badroot"
jq '."$id" = "https://hep-ph-agents/schemas/relic/v2"' \
  "$REPO/plugins/shared/schemas/relic.schema.json" > "$TMP/badroot/relic.schema.json"
python "$H" --json "$F/relic_singletDM_synthetic.json" --key omega_h2 --schema-version relic/v1 --schema-root "$TMP/badroot"
test $? -eq 1
python "$H" --json "$F/relic_singletDM_synthetic.json" --key omega_h2 --schema-version relic/v1 --schema-root "$TMP/badroot" 2>&1 1>/dev/null \
  | grep -F "VERSION_DRIFT"

# Row 6: SCHEMA_MISMATCH — inject a string where number expected
cat > "$TMP/relic_typeerr.json" <<'EOF'
{"schema_version":"relic/v1","m_dm_gev":"oops","omega_h2":0.12,
 "source":"micromegas","source_run":"runX","cosmology":"standard_thermal"}
EOF
python "$H" --json "$TMP/relic_typeerr.json" --key omega_h2 --schema-version relic/v1
test $? -eq 1
python "$H" --json "$TMP/relic_typeerr.json" --key omega_h2 --schema-version relic/v1 2>&1 1>/dev/null \
  | grep -F "SCHEMA_MISMATCH"

# Row 7: INTERNAL — file unreadable
python "$H" --json /nonexistent/file.json --key omega_h2 --schema-version relic/v1
test $? -eq 2
python "$H" --json /nonexistent/file.json --key omega_h2 --schema-version relic/v1 2>&1 1>/dev/null \
  | grep -F "EXTRACT_FIELD_INTERNAL"

# Cross-schema: scattering/v1 still works with this helper
python "$H" --json "$REPO/plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json" \
  --key sigma_si_proton_cm2 --schema-version scattering/v1
test $? -eq 0

rm -rf "$TMP"
```

---

### T5 — Helper: `verify_router_field_contract.py`

- **Owner class:** `opus-implementer` (4-branch dispatch on `produced_by`; 6 drift codes; importable surface load-bearing for T8).
- **Cycle estimate:** 2
- **Depends-on:** T1 (consumes the schemas indirectly — `summary_json` rows resolve schema refs); WS-1 must be MERGED ON MAIN (manifest at `plugins/.../contracts/router_contract.json` must exist; `tests/fixtures/` must exist).

**Inputs:**
- `ws4_synthesis.md` §1.4 (full spec: usage, drift codes, importable surface dataclass, ~200 LoC).
- `plan/ws1_plan_final.md` §5 (gate enumeration — the 18 cases this helper must support).
- WS-1's shipped `router_contract.json` and `router_contract.schema.json`.
- WS-1's shipped fixtures at `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/`.

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py` (NEW; ~200 lines)

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py
M=$REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
test -f "$H"
test -f "$M"   # WS-1 prerequisite
python "$H" --help | grep -F -- "--manifest"
python "$H" --help | grep -F -- "--fixtures-root"

# Baseline: run against shipped manifest → exit 0 (xfails are reported but not failures)
python "$H"
test $? -eq 0
python "$H" | grep -E '^SUMMARY [0-9]+/[0-9]+/[0-9]+$'

# Importable surface — load module via importlib (hyphen in skill dir name)
python -c "
import importlib.util, pathlib
p = pathlib.Path('$H')
spec = importlib.util.spec_from_file_location('vrfc', p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert callable(m.verify_router_field_contract)
r = m.verify_router_field_contract(pathlib.Path('$M'),
    pathlib.Path('$REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures'))
assert hasattr(r, 'ok') and hasattr(r, 'xfail') and hasattr(r, 'fail'), r
print('IMPORT OK', len(r.ok), len(r.xfail), len(r.fail))
"

# Drift surface: mutate manifest → expect FAIL row + DRIFT_* code + exit 1
TMP=$(mktemp -d)
cp "$M" "$TMP/m.json"
jq '.output_fields[0].field_name = "WRONG_NAME_INTENTIONAL"' "$TMP/m.json" > "$TMP/m2.json"
python "$H" --manifest "$TMP/m2.json"
test $? -eq 1
python "$H" --manifest "$TMP/m2.json" 2>&1 \
  | grep -E 'DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME)'

# Internal-error path: unreadable manifest → exit 2
echo "{not json" > "$TMP/bad.json"
python "$H" --manifest "$TMP/bad.json"
test $? -eq 2
rm -rf "$TMP"
```

---

### T6 — Producer SKILL.md edits W4-A / W4-C / W4-D + drake/SKILL.md docs portion of W4-E

- **Owner class:** `sonnet-implementer` (synthesis §4 supplies verbatim wording from proposer §5; this is mechanical search-and-replace with grep gates).
- **Cycle estimate:** 1
- **Depends-on:** none (parallelizable with T1–T5; flagged separately because it touches different files than helpers)

**Inputs:**
- `ws4_synthesis.md` §4 W4-A (lines 99/207/226 of micromegas/SKILL.md — verbatim per proposer §5 W4-A).
- `ws4_synthesis.md` §4 W4-C (line 164 of maddm/SKILL.md: `sigmav_xf` → `sigmav_total` plus backward-compat note).
- `ws4_synthesis.md` §4 W4-D (~line 213 of dark-matter-constraints/SKILL.md: name DRAKE Ωh² as `omega_h2`). NOTE: W4-D is INSIDE the router SKILL.md being rewritten in T7 — to avoid edit collision, this task DEFERS W4-D to T7. (See §Pre-flight item 3 — flagged for plan-critic.)
- `ws4_synthesis.md` §4 W4-E docs portion (drake/SKILL.md lines 84–86 — proposer §5 W4-E).

**Outputs (modifications, no new files):**
- `$REPO/plugins/constraints/skills/micromegas/SKILL.md` (3 edits)
- `$REPO/plugins/monte-carlo-tools/skills/maddm/SKILL.md` (1 edit at line 164)
- `$REPO/plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 84–86 docs touch)

**Acceptance gates (each new wording present AND old wording absent — both directions):**

```bash
MM=$REPO/plugins/constraints/skills/micromegas/SKILL.md
MD=$REPO/plugins/monte-carlo-tools/skills/maddm/SKILL.md
DR=$REPO/plugins/monte-carlo-tools/skills/drake/SKILL.md

# W4-A Edit 1 (line 99 region — per-run output table now lists relic.json + annihilation.json)
grep -F "relic.json"        "$MM"
grep -F "annihilation.json" "$MM"

# W4-A Edit 2 (line 226 region — schema example blocks for both files)
grep -F '"schema_version": "relic/v1"'        "$MM"
grep -F '"schema_version": "annihilation/v1"' "$MM"

# W4-A Edit 3 (line 207 region — steady-state-vs-legacy paragraph)
grep -E "steady.state|legacy"  -i "$MM"

# W4-C: maddm/SKILL.md line 164 reads sigmav_total, NOT sigmav_xf
grep -nF "sigmav_total" "$MD" | head -1
# Old wording removed at line 164 — assert no `sigmav_xf` remains as the canonical name (a back-compat note may mention it once)
COUNT_XF=$(grep -c "sigmav_xf" "$MD")
test "$COUNT_XF" -le 1   # at most one mention (the back-compat note)

# W4-E docs (drake/SKILL.md lines 84–86 — detect now documents activation_required)
grep -F "activation_required" "$DR"
sed -n '80,95p' "$DR" | grep -F "activation_required"
```

---

### T7 — Router `dark-matter-constraints/SKILL.md` rewrite (HIGHEST JUDGMENT)

- **Owner class:** `opus-implementer` (synthesis §3 calls 200-line target; preserve-verbatim list is precise; §2.1 prose snippet must land exactly; W4-D `omega_h2` clarification embeds here).
- **Cycle estimate:** 2
- **Depends-on:** T2, T3, T4, T5 (helper paths must exist before SKILL.md references them); T6 not strictly required but co-merging is cleaner.

**Inputs:**
- Current `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (356 lines).
- `ws4_synthesis.md` §2.1 (verbatim Step 4b prose snippet, ~25 lines).
- `ws4_synthesis.md` §3.1 (diff sketch table — which sections shrink, preserve, expand).
- `ws4_synthesis.md` §3.2 (preserve-verbatim ranges: lines 60–66, 79–100, 219–254, 258–291, 295–309, 328–339, 343–356).
- `ws4_synthesis.md` §3.3 (out-of-rewrite list).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md` (REWRITTEN; target 180–230 lines, design point 200)

**Authoring discipline:**
1. Capture the live file at task start: `cp SKILL.md /tmp/skill_before.md`.
2. Extract preserve-verbatim ranges using `sed -n` with the ranges in §3.2; concatenate into the new file with the rewritten sections in between.
3. Step 4b becomes the §2.1 prose snippet **verbatim, byte-for-byte** (no paraphrase).
4. W4-D embeds at the rewritten Step 5 Branch 2: name DRAKE's Ωh² field as `omega_h2` and route comparison through `extract_field` with `--schema-version relic/v1`.
5. Steps 1, 4a, 5a use direct-path helper invocations: `python "$REPO_ROOT/plugins/constraints/skills/dark-matter-constraints/scripts/<name>.py" …` exactly as synthesis §1 prescribes. NO `python -m`.
6. The `Config keys read` table gets the mirror header from synthesis §3.1: `> **MIRROR — see `contracts/router_contract.json` `config_keys` for canonical contract.**`

**Acceptance gates:**

```bash
S=$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md
test -f "$S"

# 1. Line-count band (180–230, design point 200)
LINES=$(wc -l < "$S")
test "$LINES" -ge 180 && test "$LINES" -le 230

# 2. Preserve-verbatim sections still present byte-for-byte
# (use git to extract pre-edit content; this gate runs after the edit, in a clean worktree)
git show HEAD:plugins/constraints/skills/dark-matter-constraints/SKILL.md > /tmp/skill_pre.md
for range in "60,66" "79,100" "219,254" "258,291" "295,309" "328,339" "343,356"; do
  PRE=$(sed -n "${range}p" /tmp/skill_pre.md)
  # The exact textual block from PRE must appear contiguously somewhere in the new file
  python -c "
pre = open('/tmp/skill_pre.md').read().splitlines()
new = open('$S').read()
a, b = (int(x) for x in '$range'.split(','))
block = '\n'.join(pre[a-1:b])
assert block in new, 'preserve-verbatim block lines ${range} missing or altered'
print('PRESERVE OK ${range}')
"
done

# 3. Step 4b prose snippet present verbatim (synthesis §2.1)
# Extract synthesis §2.1 fenced block, assert substring presence in the rewritten SKILL.md
python -c "
synth = open('$REPO/.shift-manager/run-20260425-dmc/brainstorm/ws4_synthesis.md').read()
# Find the '### Step 4b — Disagreement comparison' heading and copy the next ~25 lines from synthesis
import re
m = re.search(r'### Step 4b — Disagreement comparison.*?(?=\n### |\n## |\n---)', synth, re.DOTALL)
assert m, 'synthesis §2.1 block not found'
block = m.group(0).strip()
new = open('$S').read()
# Snippet must appear character-identical (synthesis §2.1 declares it 'verbatim')
assert block in new, 'Step 4b prose snippet not embedded verbatim'
print('STEP4B OK')
"

# 4. Direct-path helper references (NOT python -m)
grep -F "scripts/check_prereqs.py"        "$S"
grep -F "scripts/detect_drake.py"         "$S"
grep -F "scripts/extract_field.py"        "$S"
! grep -F "python -m plugins" "$S"   # forbidden invocation form (synthesis §6 row 1)

# 5. W4-D: omega_h2 named in DRAKE branch
grep -F "omega_h2" "$S"

# 6. Mirror header for config_keys
grep -F "MIRROR" "$S"
grep -F "router_contract.json" "$S"

# 7. Schema-version literals appear at extract_field call sites
grep -F "relic/v1"        "$S"
grep -F "annihilation/v1" "$S"
grep -F "scattering/v1"   "$S"
```

---

### T8 — `drake-install/install.sh` 5-line bash patch + WS-1 test retrofit

- **Owner class:** `sonnet-implementer` (bash patch is 5 lines verbatim from synthesis §4; test retrofit is mechanical refactor of WS-1's inline test to import T5's helper).
- **Cycle estimate:** 1
- **Depends-on:** T5 (`verify_router_field_contract.py` must exist for the test to import it); WS-1 ON MAIN (the file `tests/test_router_contract.py` must exist with inline dispatch).

**Inputs:**
- `ws4_synthesis.md` §4 W4-E (5-line bash insertion between current lines 128 and 130 of `cmd_detect`).
- `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (live).
- `plan/ws1_plan_final.md` §3 T3 (the inline test file ships with all 18 cases).
- `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (live, post-WS-1 merge).

**Outputs:**
- `$REPO/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (MODIFIED, 5-line insert in `cmd_detect`)
- `$REPO/plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh` (NEW — unit test asserting `cmd_detect` emits `activation_required` when smoke says so)
- `$REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (REWRITTEN — thin wrappers around `verify_router_field_contract`)

**Bash patch (verbatim, between lines 128 and 130 of `install.sh`):**

```bash
      # Smoke test did not pass — distinguish activation vs other failure
      if [ "$status" = "activation_required" ]; then
        printf '{"status":"activation_required","path":"%s"}\n' "$path"
        return 0
      fi
      # Other smoke failures fall through to "found".
```

**Test retrofit shape (synthesis §7.1):** each existing `test_*` function becomes a thin wrapper. The body uses `importlib.util.spec_from_file_location` to load `verify_router_field_contract.py` (hyphen in skill dir name forbids `import`), calls `verify_router_field_contract(manifest_path, fixtures_root)`, and asserts on the returned `VerifyResult.ok / .xfail / .fail` lists. The 18 case count, negative-control gate, `ROUTER_CONTRACT_PATH` env override, and `pending_*` xfail policy all survive structurally — what changes is the location of the dispatch logic.

**Acceptance gates:**

```bash
SH=$REPO/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh
TS=$REPO/plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh
TR=$REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py

# 1. Bash patch present
grep -F 'distinguish activation vs other failure' "$SH"
grep -F 'status" = "activation_required"' "$SH"
grep -F 'Other smoke failures fall through to "found"' "$SH"

# 2. Bash unit test exists and passes
test -x "$TS" || chmod +x "$TS"
"$TS"
test $? -eq 0

# 3. Test retrofit: imports the helper module, no longer carries inline dispatch
grep -F "verify_router_field_contract" "$TR"
grep -F "spec_from_file_location"      "$TR"
# Inline dispatch removed: heuristic — original WS-1 test had inline regex/jsonschema calls per row.
# The retrofitted test must NOT re-implement the dispatch logic; we assert no `re.search` over fixtures
# and no `jsonschema.Draft202012Validator(...).validate(` are called from this file (those live in the helper now).
! grep -F 'jsonschema.Draft202012Validator' "$TR"
! grep -E 'pattern.*re\.search|re\.search.*pattern' "$TR"

# 4. Retrofitted test still passes against shipped manifest
pytest "$TR" -v
test $? -eq 0

# 5. Negative-control still works through retrofit (proves the helper does the work)
TMP=$(mktemp -d)
M=$REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
cp "$M" "$TMP/m.json"
jq '.output_fields[0].field_name = "WRONG_NAME"' "$TMP/m.json" > "$TMP/m2.json"
ROUTER_CONTRACT_PATH="$TMP/m2.json" pytest "$TR" -v
test $? -ne 0
ROUTER_CONTRACT_PATH="$TMP/m2.json" pytest "$TR" -v 2>&1 | grep -E "DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME)"
pytest "$TR" -v
test $? -eq 0
rm -rf "$TMP"

# 6. Import target exists (proves test retrofit can resolve)
test -f "$H"
```

---

## 4. Sequencing

```
T1 (schemas, sonnet, 1c)  ──┐
T2 (check_prereqs)         ─┼─→ T4 (extract_field, opus, 2c) ─┐
T3 (detect_drake)          ─┘                                  │
                                                                ├─→ T7 (SKILL.md rewrite, opus, 2c)
T6 (producer SKILL.md edits, sonnet, 1c) ──────────────────────┤
                                                                │
T5 (verify_router_field_contract, opus, 2c) ───────────────────┤
[depends on WS-1 merged]                                        │
                                                                ↓
                                                T8 (bash 5-line + WS-1 test retrofit, sonnet, 1c)
                                                                ↓
                                          (handed off to WS-4 reviewer / WS-2 / WS-3)
```

**Parallel cycle 1 (4 sonnet-impl tracks + 1 opus-impl track):** T1, T2, T3, T6 (sonnet) + T4 start (opus). T5 also starts in this cycle since it depends only on WS-1 main, not on T1–T4.

**Cycle 2:** T4 finishes; T5 finishes.

**Cycle 3 (opus-impl):** T7 (SKILL.md rewrite) — needs helper paths to reference. Cannot parallel with T8 because T8 retrofits a test that T5 supplies the import target for, and T7 may collide with W4-D edits if not coordinated.

**Cycle 4 (sonnet-impl):** T8.

**Critical path:** T1 → T4 → T7 → T8 (opus + opus + opus + sonnet). Total cycle envelope: **4 cycles** (1 + 2 + 1 + 1 with parallelism, or 8 cycles strictly sequential — flagged for plan-critic).

**Parallelism explicit:** T1–T3, T6 are independent; T5 is independent of T1–T4 (depends on WS-1 manifest only); T6 is independent except W4-D which is deferred to T7.

---

## 5. Gates summary

Every task has runnable bash/python gates. No `wc -l > 0`, no "file exists" alone. Highlights:

- **Schemas (T1):** jsonschema cross-validation (positive AND negative fixtures), `$id` pin, `additionalProperties:false`, v→0 description string presence.
- **Helpers (T2/T3/T4/T5):** invocation gates exercising happy + error paths; `extract_field`'s 7-row exit grid is gated row-by-row.
- **Producer SKILL.md (T6):** new wording present AND old wording absent (both directions per spec).
- **Router SKILL.md (T7):** line-count band, preserve-verbatim by-substring against pre-edit git blob, Step 4b prose substring-equality with synthesis §2.1, direct-path grep, `python -m` forbidden grep.
- **Test retrofit (T8):** import target exists, helper-module reference present, inline-dispatch markers absent, retrofitted test passes, negative-control still works.

---

## 6. Coordination

### 6.1 With WS-1

WS-1 ships `tests/test_router_contract.py` with INLINE dispatch (WS-1 plan T3 acceptance gate #2 enforces 18 in-pytest cases as direct `def test_*` bodies). T8 of THIS plan refactors that file: each `test_*` becomes a wrapper around `verify_router_field_contract(manifest_path, fixtures_root)` and asserts on the returned `VerifyResult`'s lists. The 18 case count, negative-control, env override, xfail policy all survive structurally.

**Sequencing requirement:** **T8 cannot start until WS-1 is merged onto main.** T5 also depends on WS-1 (manifest must exist). Implementer MUST verify `git log --oneline plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` returns at least one commit before starting T5 or T8. If WS-1 has not landed, T5/T8 BLOCK and surface a manager-visible blocker; they do NOT skip or stub.

**WS-1 test file path (verified):** `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`.

**Exact import statement to add:**

```python
import importlib.util, pathlib
_HELPER = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "verify_router_field_contract.py"
_spec = importlib.util.spec_from_file_location("vrfc", _HELPER)
_vrfc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_vrfc)
verify_router_field_contract = _vrfc.verify_router_field_contract
```

### 6.2 With WS-2

WS-2 (router test harness) imports each helper via the same `importlib.util.spec_from_file_location` pattern. T2/T3/T4/T5 must export importable functions, not only argparse `main`. Synthesis §1 already pins this ("dual-mode: importable function + CLI"); T2..T5 acceptance gates explicitly exercise the importable surface for T5 (the load-bearing one); T2/T3/T4 leave WS-2 to assert importability. WS-2 also writes the doc-vs-CLI test.

### 6.3 With WS-3

WS-3 invokes the helpers via SKILL.md prose (no Python imports). T7's rewritten SKILL.md is the integration surface WS-3 stresses. If WS-3 surfaces ambiguity, the fix is a follow-on SKILL.md edit, not a helper rewrite.

---

## 7. Pre-flight risks

Implementer MUST verify each before opening tasks.

1. **WS-1 not yet merged.** T5 depends on `router_contract.json`; T8 depends on `tests/test_router_contract.py`. Verify with `git log --oneline plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` and `git log --oneline plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`. If absent, BLOCK T5/T8 (do NOT proceed with stubs); T1, T2, T3, T4, T6 can still run.
2. **T7 is the highest-judgment task; sonnet may not get the prose right.** Already routed to opus-implementer. Plan-critic should challenge whether 2 cycles is enough; if T7 fails its acceptance gates twice, escalate to a second opus pass with a different model class.
3. **W4-D placement decision.** Synthesis §4 W4-D names "~line 213 of dark-matter-constraints/SKILL.md" — but that file is being rewritten in T7. To avoid edit collision, this plan defers W4-D content to T7 (Step 5 Branch 2) rather than running a pre-rewrite W4-D edit in T6. **Flagged for plan-critic adjudication.**
4. **`extract_field`'s schema-`$id` self-check requires reading the schema file BEFORE jsonschema validation.** Synthesis §1.3 LOCKS this. Implementer must assert `schema["$id"].endswith("/" + schema_version)` BEFORE constructing the validator; getting the order wrong allows shadow-loading a future v2.
5. **`detect_drake`'s `HEPPH_DRAKE_DETECT_CMD` env override.** Synthesis §1.2 says default invokes the install skill's `install.sh detect` directly; tests override via env. Implementer must NOT reach into `install.sh` internals — the helper consumes the JSON only.
6. **Direct-path invocation precedent.** Synthesis §6 row 1 LOCKS direct path (`python /abs/path/to/script.py …`); `python -m` is forbidden because no `__init__.py` chain and the skill dir has a hyphen. T7 acceptance gate #4 grep-asserts the absence.
7. **Preserve-verbatim ranges in T7.** Synthesis §3.2 expanded the list to include lines 60–66, 79–100, 343–356. Implementer must extract from the PRE-edit git blob (not memory) and assert byte-for-byte substring presence. T7 gate #2 implements this via `git show HEAD:` snapshot.
8. **Step 4b prose verbatim.** Synthesis §2.1 declares the 25-line block "verbatim" and §6 row 8 LOCKS `compare_dm` as prose-only. T7 gate #3 substring-tests the synthesis block character-identical against the rewritten file.
9. **W4-E unit-test fixture location.** Plan picks `plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh` (parallel to existing test conventions). **Flagged for plan-critic adjudication** — synthesis §4 W4-E says "a new test fixture / unit test" but doesn't specify path or shape.
10. **No new Python deps.** All helpers stdlib + `jsonschema`. WS-1 already verified jsonschema available.

---

## 8. Out-of-scope

WS-4 deliberately does NOT (synthesis §8):

- Build `compare_dm` as a helper (lens-forced LLM-only; §6 row 8 LOCKED).
- Modify `scattering.schema.json` (WS-1 territory; v1 stays untouched).
- Add tests beyond the WS-1 retrofit (WS-2 territory).
- Run real MadDM / micrOMEGAs / DRAKE (WS-3 territory).
- Promote MadDM / DRAKE stdout parsing to helpers (LLM until WS-3 evidence).
- Add neutron rows to router cross-check table (W4-G deferred).
- Wire helpers into a router-level orchestrator (lens "Non-goals" forbids `dark-matter-constraints.py`).
- Generate `plugins/_helpers/` (per-skill scripts dir convention).
- Add `--json-pointer` or `--regex` to `extract_field` (single mode for v1).
- Ship `compare_dm_single_component` v1.1 helper.
- Modify `drake-install`'s overall invocation contract (only the 5-line `cmd_detect` branch).
- Rewrite WS-1's manifest (only retrofit the test).
- Touch the marketplace or plugin manifest (no new dependency added).

---

## 9. Ready check

Before T1 starts:

1. `git status` clean for `plugins/shared/schemas/relic.schema.json`, `annihilation.schema.json` — must not exist.
2. `git status` clean for `plugins/constraints/skills/dark-matter-constraints/scripts/` — directory must not exist (T2 is first to create).
3. WS-1 status: check `test -f plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` and `test -f plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`. If absent, T5/T8 are BLOCKED; surface immediately.
4. `python -c 'import jsonschema'` exits 0 in harness env.
5. `which jq` returns a path.
6. The current `plugins/constraints/skills/dark-matter-constraints/SKILL.md` is at the hash referenced by synthesis §3.1 line numbers (60–66, 79–100, etc.). If the hash has shifted, re-read end-to-end and re-derive the preserve-verbatim ranges before opening T7.
7. The four producer-side SKILL.md files referenced by T6 (micromegas line 99/207/226, maddm line 164, drake lines 84–86) are at the hashes referenced by synthesis §4. If shifted, T6 implementer re-greps for the canonical phrases before editing.
8. Implementer has read `briefs/ROUTING_LENS.md`, `ws4_synthesis.md` end-to-end, AND this plan. No partial reads.

---

## Summary

- **8 tasks (T1–T8).** Cycle estimate **4–8** (4 with parallelism, 8 strictly sequential).
- **Critical path:** T1 → T4 → T7 → T8.
- **Highest-judgment tasks:** T4 (`extract_field` exit grid is load-bearing primitive), T5 (`verify_router_field_contract` 4-branch dispatch + 6 drift codes), T7 (router SKILL.md rewrite with verbatim preserve and verbatim Step 4b).
- **Mechanical tasks:** T1 (schemas verbatim from synthesis §5), T2/T3 (small helpers), T6 (search-and-replace edits), T8 (5-line bash + test refactor).
- **WS-1 coordination:** T5 and T8 BLOCK on WS-1 merge to main; do not stub or skip.
- **Adjudications binding** per synthesis §6. Implementer does NOT re-decide.
