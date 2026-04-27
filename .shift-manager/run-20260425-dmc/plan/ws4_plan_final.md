# WS-4 Plan Final — Refactor: helpers + SKILL.md rewrite

**Synthesizer:** ws4-plan-synthesizer
**Verdict on critique:** Adopted. All 10 critic items resolved in §9. 8 tasks; T2 `__init__.py` dropped; T5 routed to sonnet (opus fallback); WS-1 BLOCK semantics use `test -f` on 4 merged artifacts; cycle envelope **5 (6 ceiling)**.
**Inputs consumed end-to-end:** `briefs/ROUTING_LENS.md`; `brainstorm/ws4_synthesis.md` (design canon); `plan/ws4_plan_draft.md`; `plan/ws4_plan_critique.md` (ACCEPT-WITH-CHANGES, 10 items); `plan/ws1_plan_final.md` (§3 T1/T3, §5, §7, §8); MERGED WS-1 artifacts on main (`plugins/constraints/skills/dark-matter-constraints/contracts/{router_contract.json,router_contract.schema.json,AUDIT.md}` + `tests/{__init__.py,test_router_contract.py,fixtures/}`); router `dark-matter-constraints/SKILL.md` (356 lines); producer `micromegas/SKILL.md` (lines 91–105, 200–245), `maddm/SKILL.md` (152–181), `drake/SKILL.md` (70–95); `drake-install/scripts/install.sh` (`cmd_detect` body, lines 100–142); `formcalc/scripts/run_formcalc.py` (direct-path invocation precedent).

This plan is canonical. Synthesis §6 (8-item) and critic (10-item) adjudications transcribed here; no re-decisions, no hedges.

---

## 1. Goal

Decompose synthesis §1 (4 helpers), §2.1 (compare_dm prose snippet), §3 (SKILL.md rewrite), §4 (W4-A/C/D/E producer edits + W4-E bash fix + drake/SKILL.md docs), §5 (2 new schemas), §7.1 (WS-1 test retrofit) into 8 ordered tasks with mechanically checkable gates. Ship exactly the helpers, schemas, and SKILL.md edits the routing-lens permits; rewrite the WS-1-merged `tests/test_router_contract.py` so that drift-classification dispatch lives in one place (`verify_router_field_contract.py`).

---

## 2. Inputs

| Doc | Role |
|---|---|
| `briefs/ROUTING_LENS.md` | Hard constraint: helpers MUST be model-agnostic; if not provable, route to LLM. |
| `brainstorm/ws4_synthesis.md` | Design canon. §1 helper inventory, §2.1 compare_dm prose, §3 SKILL.md rewrite, §4 W4-A..W4-E, §5 schema bodies (verbatim JSON), §6 8-item adjudication, §7 cross-WS coordination, §8 explicit out-of-scope. |
| `plan/ws4_plan_critique.md` | 10 unresolved items resolved in §9 of this plan. |
| `plan/ws1_plan_final.md` §3 T1, §5, §8 | Manifest shape, 18 in-pytest gate cases, W4-A..W4-G hand-off. |
| `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json` (MERGED on main) | The manifest the verify-helper consumes. |
| `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json` (MERGED) | Self-schema for the manifest. |
| `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` (MERGED) | Permanent audit narrative; T7 may reference. |
| `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (MERGED with INLINE dispatch) | The file T8 retrofits to import from `verify_router_field_contract`. |
| `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/` (MERGED) | Synthetic fixtures (maddm/drake) + symlinks (micromegas). |
| `plugins/constraints/skills/dark-matter-constraints/SKILL.md` | Source of router prose to rewrite. Preserve-verbatim ranges enumerated in §3.2 of synthesis. |
| `plugins/feynman-diagrams/.../run_formcalc.py` | Direct-path invocation precedent (synthesis §1, §6 row 1). |
| `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` | Lines 128–130 — the 5-line bash insertion site for W4-E. |

**Critical contextual fact:** WS-1 has merged. T5 and T8 do NOT block on a future merge event; they BLOCK only if their four required input files are absent at task-start (per §9 item 6).

---

## 3. Tasks

Eight tasks (T1..T8). Owner classes: `sonnet-implementer` for mechanical authoring, `opus-implementer` for highest-judgment work (T4 + T7 only). All paths absolute; `$REPO=/Users/yianni/Projects/hep-ph-agents`.

---

### T1 — Schemas: `relic.schema.json` + `annihilation.schema.json` + 4 fixtures

- **Owner class:** `sonnet-implementer` (synthesis §5 supplies verbatim JSON bodies).
- **Cycle estimate:** 1
- **Depends-on:** none

**Inputs:**
- `ws4_synthesis.md` §5.1 (relic body), §5.2 (annihilation body, including the LOCKED `sigma_v_zero` description naming v→0 and `sigmav_total`), §5.3 (out-of-scope).
- `plugins/shared/schemas/scattering.schema.json` (style template — Draft 2020-12, `$id` shape, `additionalProperties: false`).

**Outputs:**
- `$REPO/plugins/shared/schemas/relic.schema.json` (NEW)
- `$REPO/plugins/shared/schemas/annihilation.schema.json` (NEW)
- `$REPO/plugins/shared/schemas/tests/fixtures/relic_singletDM_synthetic.json` (NEW — minimal valid)
- `$REPO/plugins/shared/schemas/tests/fixtures/annihilation_singletDM_synthetic.json` (NEW — minimal valid)
- `$REPO/plugins/shared/schemas/tests/fixtures/relic_invalid_extra_field.json` (NEW — fails `additionalProperties:false` via a `_failure_mode` extra key)
- `$REPO/plugins/shared/schemas/tests/fixtures/annihilation_invalid_negative.json` (NEW — fails `minimum:0` on `sigma_v_zero` set to -1.0)
- `$REPO/plugins/shared/schemas/tests/fixtures/README.txt` (NEW — names each fixture's failure mode; critic §2 T1 nit closure)

**Acceptance gates:**

```bash
R=$REPO/plugins/shared/schemas/relic.schema.json
A=$REPO/plugins/shared/schemas/annihilation.schema.json
F=$REPO/plugins/shared/schemas/tests/fixtures
test -f "$R" && test -f "$A" && test -f "$F/README.txt"
python -c "import json; json.load(open('$R')); json.load(open('$A'))"

# Per-schema invariants (run for both R and A as appropriate)
jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' "$R"
jq -e '."$schema" == "https://json-schema.org/draft/2020-12/schema"' "$A"
jq -e '."$id" == "https://hep-ph-agents/schemas/relic/v1"'        "$R"
jq -e '."$id" == "https://hep-ph-agents/schemas/annihilation/v1"' "$A"
jq -e '.additionalProperties == false' "$R" && jq -e '.additionalProperties == false' "$A"
jq -e '.properties.schema_version.const == "relic/v1"'        "$R"
jq -e '.properties.schema_version.const == "annihilation/v1"' "$A"

# v→0 description (synthesis §5.2 LOCKED) + null-permitting oneOf
jq -e '.properties.sigma_v_zero.description | contains("v→0") and contains("sigmav_total")' "$A"
jq -e '[.properties.omega_h2.oneOf[].type] | contains(["null"])'     "$R"
jq -e '[.properties.sigma_v_zero.oneOf[].type] | contains(["null"])' "$A"

# README.txt names each fixture's failure mode (critic §2 T1 nit)
grep -F "relic_invalid_extra_field"     "$F/README.txt" && grep -F "additionalProperties" "$F/README.txt"
grep -F "annihilation_invalid_negative" "$F/README.txt" && grep -E "minimum.*0|negative"   "$F/README.txt"

# Cross-validation: positives validate, negatives fail
python -c "
import json, jsonschema
for s,f,ok in [('$R','$F/relic_singletDM_synthetic.json',True),
               ('$A','$F/annihilation_singletDM_synthetic.json',True),
               ('$R','$F/relic_invalid_extra_field.json',False),
               ('$A','$F/annihilation_invalid_negative.json',False)]:
    errs=list(jsonschema.Draft202012Validator(json.load(open(s))).iter_errors(json.load(open(f))))
    assert (not errs) if ok else errs, f'{f} validation expectation mismatch: ok={ok}, errs={errs}'
print('OK')
"
```

---

### T2 — Helper: `check_prereqs.py`

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** none (parallel with T1, T3, T5, T6)

**Inputs:**
- `ws4_synthesis.md` §1.1 (full spec: usage, blocker codes, exit grid, manifest dispatch on `config_keys[].type=path_or_bool`, ~120 LoC).
- WS-1's shipped `router_contract.json` `config_keys` section.
- `plugins/feynman-diagrams/.../run_formcalc.py` (style template).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py` (NEW; ~120 LoC)

**(Per §9 item 8: NO `scripts/__init__.py` is created. `spec_from_file_location` does not require it.)**

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py
test -f "$H"
test ! -e "$(dirname "$H")/__init__.py"   # §9 item 8 — must NOT exist
for f in --config --model --manifest; do python "$H" --help | grep -F -- "$f"; done

TMP=$(mktemp -d)
# Manifest stub mirrors WS-1 router_contract.json config_keys section
cat > "$TMP/manifest.json" <<EOF
{"schema_version":"router_contract/v1","output_fields":[],"status_enums":[],
 "config_keys":[{"key":"config.maddm_path","type":"path_or_bool"},
                {"key":"config.micromegas_path","type":"path_or_bool"},
                {"key":"config.drake_path","type":"path_or_bool"}]}
EOF

# Happy path: all three paths set + ufo_path present → status:ok, exit 0
echo '{"maddm_path":"'$TMP'","micromegas_path":"'$TMP'","drake_path":"'$TMP'","models":{"dummy":{"ufo_path":"'$TMP'"}}}' > "$TMP/c.json"
python "$H" --config "$TMP/c.json" --model dummy --manifest "$TMP/manifest.json"; test $? -eq 0
python "$H" --config "$TMP/c.json" --model dummy --manifest "$TMP/manifest.json" \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='ok', d"

# Blocker path: maddm_path bogus → exit 1, status:blocked, MADDM_MISSING in blockers
echo '{"maddm_path":"/nonexistent","micromegas_path":"'$TMP'","drake_path":"'$TMP'","models":{"dummy":{"ufo_path":"'$TMP'"}}}' > "$TMP/c.json"
python "$H" --config "$TMP/c.json" --model dummy --manifest "$TMP/manifest.json"; test $? -eq 1
python "$H" --config "$TMP/c.json" --model dummy --manifest "$TMP/manifest.json" 2>/dev/null \
  | python -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='blocked' and any(b['code']=='MADDM_MISSING' for b in d['blockers']), d"

# SLHA_MISSING_HINT path (critic §2 T2): model without latest_slha → hint surfaces but status remains 'ok'
echo '{"maddm_path":"'$TMP'","micromegas_path":"'$TMP'","drake_path":"'$TMP'","models":{"mssm_like":{"ufo_path":"'$TMP'"}}}' > "$TMP/c.json"
python "$H" --config "$TMP/c.json" --model mssm_like --manifest "$TMP/manifest.json" \
  | python -c "
import json,sys; d=json.load(sys.stdin)
hints=[b for b in d.get('blockers',[]) if b['code']=='SLHA_MISSING_HINT']
if hints: assert d['status']=='ok', d
print('HINT OK')
"

# Internal-error: unparseable manifest → exit 2
echo "{not json" > "$TMP/manifest.json"
python "$H" --config "$TMP/c.json" --model dummy --manifest "$TMP/manifest.json"; test $? -eq 2
rm -rf "$TMP"
```

---

### T3 — Helper: `detect_drake.py`

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** none (parallel)

**Inputs:**
- `ws4_synthesis.md` §1.2 (full spec: 4 status branches + `unparseable`, `HEPPH_DRAKE_DETECT_CMD` env override, exit 0 always, ~90 LoC).

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py` (NEW; ~90 LoC)

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py
test -f "$H"
for f in --config --manifest; do python "$H" --help | grep -F -- "$f"; done

TMP=$(mktemp -d)
echo '{"drake_path":"'$TMP'"}' > "$TMP/c.json"
cat > "$TMP/m.json" <<EOF
{"schema_version":"router_contract/v1","config_keys":[],"output_fields":[],
 "status_enums":[{"enum_name":"drake_install_detect_status",
  "literals":["configured","found","missing","activation_required"]}]}
EOF

# Stub install.sh detect via env var across 5 status branches.
# Heredoc form is robust (critic §2 T3 nit closure — no %q quoting).
for v in configured found missing activation_required unparseable; do
  case "$v" in
    configured)          OUT='{"status":"configured","path":"/x","version":"1.0"}' ;;
    found)               OUT='{"status":"found","path":"/x"}' ;;
    missing)             OUT='{"status":"missing"}' ;;
    activation_required) OUT='{"status":"activation_required","path":"/x"}' ;;
    unparseable)         OUT='not json at all' ;;
  esac
  STUB="$TMP/s_$v.sh"
  printf '#!/bin/bash\ncat <<"END"\n%s\nEND\n' "$OUT" > "$STUB"; chmod +x "$STUB"
  HEPPH_DRAKE_DETECT_CMD="$STUB" python "$H" --config "$TMP/c.json" --manifest "$TMP/m.json"; test $? -eq 0
  HEPPH_DRAKE_DETECT_CMD="$STUB" python "$H" --config "$TMP/c.json" --manifest "$TMP/m.json" \
    | python -c "
import json,sys; d=json.load(sys.stdin); v='$v'
if v=='unparseable': assert d['status']=='unparseable' and d['router_action']=='emit_DRAKE_UNAVAILABLE', d
else: assert d['status']==v, d
"
done
rm -rf "$TMP"
```

---

### T4 — Helper: `extract_field.py` (LOAD-BEARING PRIMITIVE)

- **Owner class:** `opus-implementer` (linchpin per synthesis §1.3; null-vs-absent and schema-`$id` self-check semantics carry every router invocation).
- **Cycle estimate:** 1 (sonnet-impl + opus-review pair = 1 cycle; budget includes 1 retry slot if needed)
- **Depends-on:** T1 (uses the schemas as test material)

**Inputs:**
- `ws4_synthesis.md` §1.3 (LOCKED 7-row exit grid, schema-`$id` self-check before validation).
- T1's schemas + fixtures.
- `plugins/shared/schemas/scattering.schema.json`.

**Schema dispatch rule (LOCKED — §9 item 2):** helper deterministically loads the schema file via:

```
schema_file = <schema-root> / "<basename>.schema.json"
```

where `<basename> = <schema-version>.split("/")[0]`. So `--schema-version relic/v1` ⇒ `<schema-root>/relic.schema.json`. Default `<schema-root>` resolves from helper location: `Path(__file__).resolve().parent.parent.parent.parent / "shared" / "schemas"` (i.e. `$REPO/plugins/shared/schemas/`). The helper does NOT `os.listdir` the schema root.

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py` (NEW; ~110 LoC)

**Acceptance gates (every row of the §1.3 grid PLUS critic §2 T4 missing-row gate). Each row drives `python "$H" --json <fixture> --key <k> --schema-version <v> [--schema-root <r>]` and asserts (a) exit code, (b) on error, the named code appears in stderr.**

| Row | Fixture content | --key | --schema-version | Expected exit | Expected code |
|-----|-----------------|-------|------------------|---------------|---------------|
| 1 | `relic_singletDM_synthetic.json` (valid, omega_h2 numeric) | `omega_h2` | `relic/v1` | 0 | — (value is number) |
| 2 | hand-rolled relic JSON with `omega_h2:null` | `omega_h2` | `relic/v1` | 0 | — (value is null) |
| 3 | hand-rolled valid relic JSON (no `xf` key) | `xf` | `relic/v1` | 1 | `KEY_ABSENT` |
| 4 | hand-rolled relic JSON with `schema_version:"relic/v2"` | `omega_h2` | `relic/v1` | 1 | `VERSION_DRIFT` |
| 5 | valid fixture + `--schema-root` pointing at a schema file whose `$id` ends `/relic/v2` | `omega_h2` | `relic/v1` | 1 | `VERSION_DRIFT` |
| 6 | hand-rolled relic JSON with `m_dm_gev:"oops"` (type violation) | `omega_h2` | `relic/v1` | 1 | `SCHEMA_MISMATCH` |
| 7 | nonexistent file path | `omega_h2` | `relic/v1` | 2 | `EXTRACT_FIELD_INTERNAL` |
| 8 (critic §2 T4) | hand-rolled `summary.json` with `sigma_si_proton_cm2:null` (scattering/v1 schema disallows null on this key) | `sigma_si_proton_cm2` | `scattering/v1` | 1 | `SCHEMA_MISMATCH` |

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py
test -f "$H"
for f in --json --key --schema-version; do python "$H" --help | grep -F -- "$f"; done

# The 8-row matrix is mechanically driven from the table above. Implementer authors a
# small bash harness writing each fixture into $TMP and asserting (exit, stderr code).
# Rows 1, 5: read from $REPO/plugins/shared/schemas/tests/fixtures/relic_singletDM_synthetic.json
# Row 5 specifically: jq '."$id"="https://hep-ph-agents/schemas/relic/v2"' on the schema, write to $TMP/badroot/relic.schema.json, pass --schema-root $TMP/badroot.
# Cross-schema sanity check (must pass exit 0):
python "$H" --json "$REPO/plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json" \
  --key sigma_si_proton_cm2 --schema-version scattering/v1
test $? -eq 0
```

The schema-dispatch rule (§9 item 2) means row 5 must use `<schema-root>/relic.schema.json` — the `<basename>` extraction logic is what gate row 5 exercises. The implementer ships an inline 8-row bash matrix; reviewer re-runs it.

---

### T5 — Helper: `verify_router_field_contract.py`

- **Owner class:** `sonnet-implementer` (per §9 item 1; opus fallback if cycle-1 acceptance gates fail). Synthesis §1.4 spec is precise enough for sonnet — 4-branch dispatch on `produced_by`, 6 enumerated drift codes, mechanical aggregation.
- **Cycle estimate:** 1
- **Depends-on:** WS-1 artifacts present on main (§9 item 6 `test -f` pre-flight).

**Inputs:**
- `ws4_synthesis.md` §1.4 (full spec: usage, drift codes, importable surface dataclass `VerifyResult`).
- `plan/ws1_plan_final.md` §5 (the 18 cases the helper must support).
- The MERGED `router_contract.json`, `router_contract.schema.json`, `tests/fixtures/`.

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py` (NEW; ~200 LoC)

**Acceptance gates:**

```bash
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py
M=$REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
FIX=$REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures
test -f "$H" && test -f "$M" && test -d "$FIX"   # WS-1 prereqs (§9 item 6)
for f in --manifest --fixtures-root; do python "$H" --help | grep -F -- "$f"; done

# Baseline: shipped manifest passes (xfails reported)
python "$H"; test $? -eq 0
python "$H" | grep -E '^SUMMARY [0-9]+/[0-9]+/[0-9]+$'

# Importable surface — dataclass shape (critic §2 T5 defect closure)
python -c "
import importlib.util, pathlib, dataclasses
spec = importlib.util.spec_from_file_location('vrfc', pathlib.Path('$H'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r = m.verify_router_field_contract(pathlib.Path('$M'), pathlib.Path('$FIX'))
assert dataclasses.is_dataclass(r), 'VerifyResult must be a dataclass'
assert all(isinstance(getattr(r,a), list) for a in ('ok','xfail','fail')), r
print('IMPORT OK', len(r.ok), len(r.xfail), len(r.fail))
"

# Drift surface: mutate manifest → exit 1 + DRIFT_*
TMP=$(mktemp -d); cp "$M" "$TMP/m.json"
jq '.output_fields[0].field_name = "WRONG_NAME_INTENTIONAL"' "$TMP/m.json" > "$TMP/m2.json"
python "$H" --manifest "$TMP/m2.json"; test $? -eq 1
python "$H" --manifest "$TMP/m2.json" 2>&1 | grep -E 'DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME)'

# Internal-error: unparseable manifest → exit 2
echo "{not json" > "$TMP/bad.json"; python "$H" --manifest "$TMP/bad.json"; test $? -eq 2
rm -rf "$TMP"
```

---

### T6 — Producer SKILL.md edits W4-A / W4-C + drake/SKILL.md docs portion of W4-E

- **Owner class:** `sonnet-implementer` (mechanical search-and-replace; verbatim wording specified below).
- **Cycle estimate:** 1
- **Depends-on:** none (parallel with T1–T5)

**W4-D placement:** DEFERRED to T7 (per critic §4.1; the file being edited is the same file T7 rewrites). T6 does NOT touch `plugins/constraints/skills/dark-matter-constraints/SKILL.md`. T7 acceptance gate #5 grep-asserts `omega_h2` lands in the rewritten Step 5 Branch 2.

**Inputs:**
- `ws4_synthesis.md` §4 W4-A / W4-C / W4-E (verbatim wording from proposer §5).

**W4-A Edit 3 canonical phrase (LOCKED — §9 item 3):** the new paragraph at micromegas/SKILL.md just after line 207 (inside "Reading micrOMEGAs output") MUST contain the verbatim sentence:

> **Steady-state path (post-W4-B):** when `relic.json` and `annihilation.json` exist alongside `summary.json`, downstream skills MUST prefer the schema-pinned JSONs and treat the stdout regex extraction as a legacy fallback for hand-driven runs predating those schema files.

The implementer wraps this sentence in a paragraph with whatever transitional prose is natural; the gate asserts the bolded prefix and the words `legacy fallback` survive verbatim.

**Outputs (modifications, no new files):**
- `$REPO/plugins/constraints/skills/micromegas/SKILL.md` (3 edits at line 99 / 207 / 226 regions)
- `$REPO/plugins/monte-carlo-tools/skills/maddm/SKILL.md` (1 edit at line 164 — `sigmav_xf` → `sigmav_total` PLUS one-sentence back-compat note that mentions `sigmav_xf` exactly once)
- `$REPO/plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 84–86 docs touch — document `activation_required` as a possible `detect` output post-W4-E)

**Acceptance gates:**

```bash
MM=$REPO/plugins/constraints/skills/micromegas/SKILL.md
MD=$REPO/plugins/monte-carlo-tools/skills/maddm/SKILL.md
DR=$REPO/plugins/monte-carlo-tools/skills/drake/SKILL.md

# W4-A Edit 1 (line 99 region — per-run output table)
grep -F "relic.json"        "$MM"
grep -F "annihilation.json" "$MM"

# W4-A Edit 2 (line 226 region — schema example blocks)
grep -F '"schema_version": "relic/v1"'        "$MM"
grep -F '"schema_version": "annihilation/v1"' "$MM"

# W4-A Edit 3 (§9 item 3 LOCKED phrase)
grep -F "Steady-state path (post-W4-B)" "$MM"
grep -F "legacy fallback"               "$MM"

# W4-C: maddm/SKILL.md replaces the canonical name; back-compat note retains exactly one mention
grep -nF "sigmav_total" "$MD" | head -1
COUNT_XF=$(grep -c "sigmav_xf" "$MD")
test "$COUNT_XF" -eq 1   # §9 item 10: tightened from <=1 to ==1

# W4-E docs (drake/SKILL.md lines 84–86 region documents activation_required as a detect output)
sed -n '76,95p' "$DR" | grep -F "activation_required"
```

---

### T7 — Router `dark-matter-constraints/SKILL.md` rewrite (HIGHEST JUDGMENT)

- **Owner class:** `opus-implementer`
- **Cycle estimate:** 2 (judgment-heavy; the only task that gets 2 cycles)
- **Depends-on:** T2, T3, T4, T5 (helper paths must exist before SKILL.md references them); coordinated with T6 (T6 finishes producer-side wording so T7's Step 4b prose snippet aligns with the producer SKILL.md it cites).

**Inputs:**
- Current `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (356 lines).
- `ws4_synthesis.md` §2.1 (verbatim Step 4b prose snippet, ~25 lines).
- `ws4_synthesis.md` §3.1 (diff sketch table).
- `ws4_synthesis.md` §3.2 (preserve-verbatim ranges).
- `ws4_synthesis.md` §3.3 (out-of-rewrite list).

**Authoring discipline (numbered steps, all binding):**

1. **Pre-edit checkpoint commit.** Before editing, the implementer creates a commit on the WS-4 worktree branch that captures the live SKILL.md state (`git add SKILL.md && git commit -m "checkpoint: pre-T7 SKILL.md baseline"`). This is what gate #2 reads via `git show HEAD~1:` (critic §2 T7 edge-case closure).
2. Extract preserve-verbatim ranges using `sed -n` on the checkpoint blob. Concatenate with rewritten sections in between.
3. Step 4b becomes the synthesis §2.1 prose snippet **verbatim, byte-for-byte** (no paraphrase).
4. **W4-D LANDING (§9 item 9 — promoted to dedicated step):** at the rewritten Step 5 Branch 2, name DRAKE's Ωh² field as `omega_h2` (lowercase) and route the comparison through `extract_field` with `--schema-version relic/v1`. This MUST land in T7; T6 deliberately does not touch this file.
5. Steps 1, 4a, 5a use direct-path helper invocations: `python "$REPO_ROOT/plugins/constraints/skills/dark-matter-constraints/scripts/<name>.py" …`. NO `python -m` (synthesis §6 row 1 LOCKED).
6. The `Config keys read` table gets the mirror header: `> **MIRROR — see contracts/router_contract.json config_keys for canonical contract.**`
7. **Routing-semantics sacrosanct branch labels (§9 item 5 — gate #8 below):** the following decision-tree branch labels MUST survive verbatim across the rewrite (string-identical):
   - `Step 1 — Prerequisite check`
   - `Step 2 — Default pipeline: MadDM (always)`
   - `Step 3 — Spectrum analysis: detect cross-check triggers`
   - `Trigger A — Coannihilation`
   - `Trigger B — Near-threshold resonance (relic)`
   - `Step 4 — Cross-check via micrOMEGAs (conditional)`
   - `Step 5 — DRAKE invocation (narrow-resonance)`
   - `Branch 1 — config.drake_path absent`
   - `Branch 2 — config.drake_path set`

   These labels carry the routing semantics (which step decides what); a paraphrase would change the meaning of the router. The §3.2 preserve-verbatim line ranges already cover the *bodies* of Steps 2 and 3 (60–66 and 79–100); these labels cover the *headings* and the two DRAKE branches, which are interleaved across replaced sections.

**Outputs:**
- `$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md` (REWRITTEN; target 180–230 lines, design point 200)

**Acceptance gates:**

```bash
S=$REPO/plugins/constraints/skills/dark-matter-constraints/SKILL.md
test -f "$S"

# 1. Line-count band [180, 230]
LINES=$(wc -l < "$S"); test "$LINES" -ge 180 && test "$LINES" -le 230

# 2. Preserve-verbatim 7 ranges via HEAD~1 (checkpoint commit, per discipline step 1)
git show HEAD~1:plugins/constraints/skills/dark-matter-constraints/SKILL.md > /tmp/skill_pre.md
for range in "60,66" "79,100" "219,254" "258,291" "295,309" "328,339" "343,356"; do
  python -c "
pre=open('/tmp/skill_pre.md').read().splitlines(); new=open('$S').read()
a,b=(int(x) for x in '$range'.split(','))
block='\n'.join(pre[a-1:b])
assert block in new, 'preserve-verbatim $range missing or altered'
print('PRESERVE OK $range')"
done

# 3. Step 4b prose snippet verbatim (synthesis §2.1)
python -c "
import re
synth=open('$REPO/.shift-manager/run-20260425-dmc/brainstorm/ws4_synthesis.md').read()
m=re.search(r'### Step 4b — Disagreement comparison.*?(?=\n### |\n## |\n---)', synth, re.DOTALL)
assert m and m.group(0).strip() in open('$S').read(), 'Step 4b not verbatim'
print('STEP4B OK')"

# 4. Direct-path helper refs; python -m forbidden
for s in scripts/check_prereqs.py scripts/detect_drake.py scripts/extract_field.py; do grep -F "$s" "$S"; done
! grep -F "python -m plugins" "$S"

# 5. W4-D landed: omega_h2 in DRAKE branch
grep -F "omega_h2" "$S"

# 6. Mirror header + router_contract.json reference
grep -F "MIRROR" "$S" && grep -F "router_contract.json" "$S"

# 7. Schema-version literals at extract_field call sites
for v in "relic/v1" "annihilation/v1" "scattering/v1"; do grep -F "$v" "$S"; done

# 8. Routing-semantics sacrosanct labels (§9 item 5 — 9 labels verbatim)
for L in \
  "Step 1 — Prerequisite check" \
  "Step 2 — Default pipeline: MadDM (always)" \
  "Step 3 — Spectrum analysis: detect cross-check triggers" \
  "Trigger A — Coannihilation" \
  "Trigger B — Near-threshold resonance (relic)" \
  "Step 4 — Cross-check via micrOMEGAs (conditional)" \
  "Step 5 — DRAKE invocation (narrow-resonance)" \
  "Branch 1 — config.drake_path absent" \
  "Branch 2 — config.drake_path set"; do
  grep -F "$L" "$S" || { echo "MISSING SACROSANCT LABEL: $L"; exit 1; }
done
```

---

### T8 — `drake-install/install.sh` 5-line bash patch + WS-1 test retrofit

- **Owner class:** `sonnet-implementer`
- **Cycle estimate:** 1
- **Depends-on:** T5 (`verify_router_field_contract.py` must exist for the test to import it); WS-1 artifacts on main (§9 item 6).

**Inputs:**
- `ws4_synthesis.md` §4 W4-E (5-line bash insertion between current lines 128 and 130 of `cmd_detect`).
- `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (live).
- The MERGED `tests/test_router_contract.py` (WS-1's inline-dispatch shape).

**Outputs:**
- `$REPO/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` (MODIFIED — 5-line insert in `cmd_detect`)
- `$REPO/plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh` (NEW — bash convention matching sibling `test_detect.sh`)
- `$REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (REWRITTEN — thin wrappers around `verify_router_field_contract`)

**Bash patch (verbatim, between current lines 128 and 130 of `install.sh`, replacing the existing comment line):**

```bash
      # Smoke test did not pass — distinguish activation vs other failure
      if [ "$status" = "activation_required" ]; then
        printf '{"status":"activation_required","path":"%s"}\n' "$path"
        return 0
      fi
      # Other smoke failures fall through to "found".
```

**`test_cmd_detect_activation.sh` body — 5-step spec (LOCKED — §9 item 4):**

1. Source `install.sh` in a subshell so `cmd_detect` and its helpers are in scope (or `bash -c "source ...; cmd_detect"`).
2. Stub the four helpers `cmd_detect` calls — `config_get`, `wolfram_path`, `is_drake_dir`, `run_smoke` — by exporting shell functions before/after sourcing. Stubs: `config_get drake_path`→echo tmpdir; `wolfram_path`→echo `/usr/local/bin/wolframscript`; `is_drake_dir`→return 0; `run_smoke`→echo a JSON literal whose `status` varies per case.
3. Drive 3 cases: (a) `status="ok"` → assert `cmd_detect` stdout has `status:"configured"`; (b) `status="activation_required"` → expect `status:"activation_required"`; (c) `status="error"` → expect `status:"found"`.
4. Each case: capture stdout, parse via `python -c "json.load(...)"`, assert `d['status']` equals the expected literal, fail loudly with case name on mismatch.
5. Exit 0 only if all three pass. Print `OK 3/3 cases` on success; on any failure print case name and exit 1.

Binding; implementer does not redesign.

**Test retrofit shape (synthesis §7.1):** each `test_*` becomes a thin wrapper calling `verify_router_field_contract(manifest_path, fixtures_root)` and asserting on `VerifyResult.ok/.xfail/.fail`. 18-case count, negative-control, `ROUTER_CONTRACT_PATH` env override, `pending_*` xfail policy all survive.

**Exact import block at top of retrofitted file:**

```python
import importlib.util, pathlib
_HELPER = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "verify_router_field_contract.py"
_spec = importlib.util.spec_from_file_location("vrfc", _HELPER)
_vrfc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_vrfc)
verify_router_field_contract = _vrfc.verify_router_field_contract
VerifyResult = _vrfc.VerifyResult
```

**Acceptance gates:**

```bash
SH=$REPO/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh
TS=$REPO/plugins/monte-carlo-tools/skills/drake-install/tests/test_cmd_detect_activation.sh
TR=$REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
H=$REPO/plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py
M=$REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json

# 1. Bash patch present (3 phrases)
grep -F 'distinguish activation vs other failure' "$SH"
grep -F 'status" = "activation_required"'         "$SH"
grep -F 'Other smoke failures fall through to "found"' "$SH"

# 2. Bash unit test exists + 3 cases pass
test -x "$TS" || chmod +x "$TS"
"$TS"; test $? -eq 0
"$TS" | grep -E "OK 3/3|3/3 cases"

# 3. Test retrofit: imports helper; inline dispatch removed (call-form check, critic §2 T8)
grep -F "verify_router_field_contract" "$TR" && grep -F "spec_from_file_location" "$TR"
! grep -E 'jsonschema\.Draft202012Validator\(.+\)\.validate' "$TR"

# 4. Retrofitted test passes against shipped manifest
pytest "$TR" -v; test $? -eq 0

# 5. Negative-control through the retrofit
TMP=$(mktemp -d); cp "$M" "$TMP/m.json"
jq '.output_fields[0].field_name = "WRONG_NAME"' "$TMP/m.json" > "$TMP/m2.json"
ROUTER_CONTRACT_PATH="$TMP/m2.json" pytest "$TR" -v; test $? -ne 0
ROUTER_CONTRACT_PATH="$TMP/m2.json" pytest "$TR" -v 2>&1 \
  | grep -E "DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME)"
pytest "$TR" -v; test $? -eq 0
rm -rf "$TMP"

# 6. Import target exists
test -f "$H"
```

---

## 4. Sequencing diagram

```
Cycle 1 (parallel): T1 (sonnet, schemas) ║ T2 (sonnet, check_prereqs) ║ T3 (sonnet, detect_drake)
                    ║ T5 (sonnet, verify_router_field_contract — needs WS-1 files) ║ T6 (sonnet, producer SKILL.md)
                    ║ T4 (opus, extract_field — depends on T1 mid-cycle)
Cycle 2: T7 begins (opus, router SKILL.md rewrite — depends on T2/T3/T4/T5)
Cycle 3: T7 finishes
Cycle 4: T8 (sonnet, bash patch + WS-1 test retrofit — depends on T5)
Cycle 5: Reviewer pass over every gate; hand off to WS-2 / WS-3
```

**Critical path:** T1 → T4 → T7 → T8 (1+1+2+1 = 5 cycles).
**Cycle envelope (BINDING — §9 item 7):** 5 cycles, 6 ceiling (1 retry slot for T7).

---

## 5. Gate enumeration (code-level)

Each task's **Acceptance gates** block above is the canonical, runnable code-level gate spec. Aggregate counts (sub-gate level): T1 ~22, T2 ~8, T3 ~17, T4 ~17 (8 grid rows × 2 + cross-schema sanity), T5 ~9, T6 ~9, T7 ~28 (line-count + 7 preserve ranges + Step 4b + 3 direct-path + python-m forbidden + omega_h2 + 2 mirror + 3 schema versions + 9 sacrosanct labels), T8 ~14. **~124 mechanical sub-gates total.** No `wc -l > 0`, no bare `test -f` claims of done — every gate carries a content assertion.

---

## 6. Coordination with WS-1, WS-2, WS-3

### 6.1 With WS-1 (MERGED on main)

T8 retrofits `tests/test_router_contract.py`: each `test_*` becomes a wrapper around `verify_router_field_contract(manifest_path, fixtures_root)` and asserts on the returned `VerifyResult.ok/.xfail/.fail` lists. The 18 case count, negative-control, env override, xfail policy survive structurally.

**WS-1 BLOCK semantics (REVISED — §9 item 6):** unblocking signal is **file presence**, not branch state. T5/T8 pre-flight:

```bash
test -f $REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
test -f $REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json
test -f $REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
test -d $REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures
```

If any of the four fails, T5/T8 BLOCK and surface a manager blocker. No stubbing.

### 6.2 With WS-2

WS-2 imports each helper as a Python function via `importlib.util.spec_from_file_location` (same loader pattern as T8's retrofit). T2/T3/T4/T5 export importable functions, not only argparse `main`s. WS-2 also writes the doc-vs-CLI test (greps SKILL.md for invocation lines, runs `--help`, asserts flag parity).

**WS-2 must pre-emptively scope around:** the four WS-4-owned helper script paths (`scripts/{check_prereqs,detect_drake,extract_field,verify_router_field_contract}.py`) — WS-2 does NOT modify them. WS-2 also does NOT test `compare_dm` / `read_maddm_output` / `read_drake_output` (all prose).

### 6.3 With WS-3

WS-3 does NOT import WS-4 helpers as Python — invokes them via SKILL.md `python …/scripts/<name>.py …` strings as the LLM would. WS-3 is the integration test for the rewritten SKILL.md prose itself; ambiguity surfaces as a follow-on SKILL.md edit, not a helper rewrite. WS-3 also catches deferred MadDM real-format drift (WS-1 §6.4); a "MadDM contract verification" subsection may promote `verified_against_synthetic` → `verified_against_real`.

### 6.4 Worktree branch

Proposed: **`ws-4-refactor`** (off main; WS-1 already merged). Subagents share this branch; §4 sequencing prevents edit collisions.

---

## 7. Pre-flight risks

Implementer verifies each before opening tasks.

1. **WS-1 file presence** (§9 item 6). Run the four `test -f`/`test -d` from §6.1. If any fail, BLOCK T5/T8.
2. **Worktree branch.** Create `ws-4-refactor` off main. T7 requires a pre-edit checkpoint commit (discipline step 1) so gate #2 reads pre-edit content via `git show HEAD~1:`.
3. **T7 highest-judgment.** Opus. If gates fail twice, 6-cycle ceiling absorbs the retry; beyond that, escalate.
4. **W4-D placement.** DEFERRED to T7. T6 does NOT touch the router SKILL.md. T7 gate #5 grep-asserts `omega_h2` lands.
5. **`extract_field` schema-`$id` self-check ORDER.** Assert `schema["$id"].endswith("/" + schema_version)` BEFORE constructing the validator. Wrong order silently allows shadow-loading future v2.
6. **`detect_drake` env override.** Default invokes `install.sh detect`; tests override via `HEPPH_DRAKE_DETECT_CMD`. Helper consumes JSON only.
7. **Direct-path invocation.** §9 row 1 of synthesis LOCKED. T7 gate #4 grep-asserts `python -m plugins` absent.
8. **Preserve-verbatim ranges in T7.** Read from HEAD~1 checkpoint, not memory. T7 gate #2.
9. **Step 4b prose verbatim.** Synthesis §2.1 25-line block "verbatim, byte-for-byte." T7 gate #3.
10. **Sacrosanct labels.** §9 item 5: 9 labels. T7 gate #8 grep-asserts each.
11. **No new Python deps.** stdlib + `jsonschema` only (WS-1 verified availability).
12. **No `__init__.py` for scripts** (§9 item 8). T2 gate asserts ABSENCE.
13. **`test_cmd_detect_activation.sh` 5-step body** (§9 item 4) is binding.

---

## 8. Out-of-scope and WS-2/WS-3 hand-off

WS-4 deliberately does NOT (synthesis §8): build `compare_dm` as a helper (lens-forced LLM-only); modify `scattering.schema.json`; add net-new helper tests beyond the WS-1 retrofit (WS-2 territory); run real MadDM/micrOMEGAs/DRAKE (WS-3 territory); promote MadDM/DRAKE stdout parsing to helpers; add neutron rows to router table (W4-G deferred); wire helpers into a router-level orchestrator (lens forbids); generate `plugins/_helpers/`; add `--json-pointer`/`--regex` to `extract_field`; ship `compare_dm_single_component` v1.1 helper; modify `drake-install`'s overall invocation contract beyond the 5-line `cmd_detect` branch; rewrite WS-1's manifest (only retrofit the test); touch the marketplace or plugin manifest.

**Hand-off to WS-2:** writes net-new `tests/test_{check_prereqs,detect_drake,extract_field}.py`; writes doc-vs-CLI invariance test (greps SKILL.md for `python …/scripts/<name>.py …` invocations, runs each with `--help`, asserts every flag in prose appears in `--help`); inherits the `importlib.util.spec_from_file_location` loader pattern T8 establishes.

**Hand-off to WS-3:** exercises the rewritten SKILL.md prose end-to-end on Profumo Fig. 8 (arXiv:2506.19062); catches real-format MadDM drift (WS-1 §6.4 deferred); MadDM contract verification subsection may promote `verified_against_synthetic` → `verified_against_real` in a follow-up.

---

## 9. 10-item adjudication table

| # | Critic item | Decision | Rationale |
|---|---|---|---|
| 1 | T5 owner class — sonnet or opus | **sonnet** (with opus fallback if cycle-1 fails) | Synthesis §1.4 spec is precise (4-branch dispatch + 6 enumerated drift codes; mechanical aggregation). Saves opus capacity for T7. The 5-cycle envelope absorbs a sonnet retry if needed. |
| 2 | T4 row-5 schema dispatch rule | **`<schema-root>/<basename>.schema.json` where `<basename> = <schema-version>.split("/")[0]`** | Deterministic, testable, no `os.listdir` ambiguity. Matches the natural one-schema-per-version convention already in `plugins/shared/schemas/`. |
| 3 | T6 W4-A Edit 3 canonical phrase | **VERBATIM:** `**Steady-state path (post-W4-B):** when relic.json and annihilation.json exist alongside summary.json, downstream skills MUST prefer the schema-pinned JSONs and treat the stdout regex extraction as a legacy fallback for hand-driven runs predating those schema files.` | Surfaces proposer's wording. Gate asserts the bolded prefix and `legacy fallback` survive (T6 gate W4-A Edit 3). |
| 4 | T8 bash-test 5-step body spec | **VERBATIM 5 steps in T8 §body** (source install.sh; stub config_get/wolfram_path/is_drake_dir/run_smoke; drive 3 cases — ok→configured, activation_required→activation_required, error→found; assert each via python json.load; print "OK 3/3" + exit 0) | Eliminates implementer ambiguity. Gate asserts `OK 3/3` summary line. |
| 5 | T7 routing-semantics sacrosanct branch labels | **9 labels enumerated** in T7 authoring discipline step 7: Step 1, Step 2, Step 3, Trigger A, Trigger B, Step 4, Step 5, Branch 1, Branch 2 (verbatim full headings, including em-dashes) | Captures the routing semantics that WS-3 will integration-test. Gate #8 grep-asserts each. |
| 6 | WS-1 BLOCK semantics — file-presence not branch | **Replace `git log --oneline` with `test -f` / `test -d` on the four required artifacts** (router_contract.json, router_contract.schema.json, test_router_contract.py, tests/fixtures/) | WS-1 has merged; absolute-path file presence is the right signal. `git log` is fragile across worktrees. Pre-flight risk #1 implements. |
| 7 | Cycle envelope | **BIND TO 5 CYCLES, 6 CEILING** | Cycle 1 parallelizes T1+T2+T3+T5+T6 (sonnet) plus T4 (opus); cycle 2–3 covers T7 (opus, 2c, the only multi-cycle task); cycle 4 covers T8 (sonnet); cycle 5 covers final reviewer pass. The 6th cycle covers a possible T7 retry. |
| 8 | Drop T2 `scripts/__init__.py` | **CONFIRMED** — output dropped | `spec_from_file_location` does not require `__init__.py`. Adding one would imply the directory is a package, but parent dirs lack `__init__.py` and the skill name has a hyphen (synthesis §1 ratified). T2 acceptance gate asserts ABSENCE. |
| 9 | Promote W4-D in T7 | **CONFIRMED** — W4-D elevated to T7 authoring discipline step 4 (dedicated step, not a bullet in a discipline list) | Prevents the implementer from missing it. T7 gate #5 grep-asserts `omega_h2` lands. T6 explicitly does NOT touch the router SKILL.md. |
| 10 | Tighten T6 `sigmav_xf` count from `<=1` to `==1` | **CONFIRMED** — T6 gate uses `test "$COUNT_XF" -eq 1` | Back-compat note must exist (preserves users still using the old name) AND the canonical replacement must land. Both directions enforced. |

---

## 10. Ready check

Predicates that must hold before T1 starts.

1. WS-1 artifacts on main:
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md`
   - `test -f $REPO/plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`
   - `test -d $REPO/plugins/constraints/skills/dark-matter-constraints/tests/fixtures`
2. `git status` clean for `plugins/shared/schemas/relic.schema.json`, `annihilation.schema.json` — must NOT exist.
3. `git status` clean for `plugins/constraints/skills/dark-matter-constraints/scripts/` — directory must NOT exist (T2 first to create).
4. Worktree branch `ws-4-refactor` created from main HEAD; subagents share this branch.
5. `python -c 'import jsonschema, pytest'` exits 0 in harness env.
6. `which jq` returns a path.
7. Current `dark-matter-constraints/SKILL.md` is at the hash referenced by synthesis §3.1 line numbers (60–66, 79–100, etc.). If shifted, T7 implementer re-derives ranges before authoring.
8. Producer SKILL.md hashes (micromegas line 99/207/226, maddm line 164, drake lines 84–86) match synthesis §4 references. If shifted, T6 implementer re-greps for canonical phrases before editing.
9. Implementer has read `briefs/ROUTING_LENS.md`, `ws4_synthesis.md`, `ws4_plan_critique.md`, AND this plan end-to-end. No partial reads.

If any of items 1–8 fails, raise a blocker. Item 9 is verified by the implementer's own discipline.

---

## Summary

8 tasks; cycle envelope **5 binding, 6 ceiling**; critical path T1→T4→T7→T8; opus on T4 (1c) and T7 (2c); sonnet on T1/T2/T3/T5/T6/T8 (1c each, T5 with opus fallback); WS-1 coordination via file-presence; adjudications in §9 binding; worktree branch `ws-4-refactor`.
