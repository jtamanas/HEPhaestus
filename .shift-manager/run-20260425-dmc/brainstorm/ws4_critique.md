# WS-4 Critique — refactor: helpers + SKILL.md rewrite

**Critic:** WS-4 brainstorm critic
**Inputs verified:** `briefs/ROUTING_LENS.md`; `brainstorm/ws1_synthesis.md`; `plan/ws1_plan_final.md`; `brainstorm/ws4_propose.md` (509 lines); the four producer SKILL.md files at the live hashes (`dark-matter-constraints/SKILL.md` 356 lines, `micromegas/SKILL.md` lines 85–245, `maddm/SKILL.md` lines 140–187, `drake/SKILL.md` lines 70–95); `drake-install/scripts/install.sh` `cmd_detect` body (lines 111–142); `formcalc` script convention at `plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py` (the proposer wrote `qft/skills/formcalc` which does NOT exist; see §3 finding 4).

---

## 1. Verdict

**ACCEPT-WITH-CHANGES.** The proposal is structurally sound and the lens-conformance check at the bottom is honest. But it has four discrete issues the synthesizer must resolve — none fatal, all concrete:

1. The `compare_dm` LLM-only call is correct under the lens but the proposal's case for it is *under-argued* in one specific direction — the proposer never engaged the user's UX goal ("competent collaborator"), where a deterministic comparison helper might actually serve the LLM's collaborator persona better than re-deriving rel-diff in prose every invocation. I do not flip the call, but I add a sharper boundary (§2).
2. `extract_field` is under-specified — nested paths, multiple files, regex/JSON dispatch all unaddressed.
3. The `qft/skills/formcalc/scripts/run_formcalc.py` reference is wrong — the file lives in `feynman-diagrams/skills/formcalc/scripts/`, NOT `qft`. Convention claim survives, citation is wrong.
4. W4-E claims a `detect` change. `cmd_detect` actually CALLS `run_smoke` and can already see `activation_required` in the smoke output — it just falls through to `found`. So the change is SHALLOW (one branch in `cmd_detect`), not "feasibility uncertain." Proposer overstated risk.

The four helpers, the layout choice (option A), the schema split, and the SKILL.md target length all stand.

---

## 2. Per-decision rebuttal

### 2.1 `compare_dm` LLM-only — DO NOT FLIP, but harden the boundary

The proposer's verdict (§2.3) is the lens-aligned answer. The four killer arguments — multi-component DM, asymmetric DM, Majorana null σ_SD, expert-overridable threshold — survive scrutiny:

- **Multi-component:** real. micrOMEGAs `darkOmega2` is a documented v1.1 escape hatch (`micromegas/SKILL.md` line 134 confirms `MULTICOMPONENT_UNSUPPORTED` in v1, but the user's roadmap reaches multi-component). A helper baked today against the single-component shape locks the router into a v1.1 rewrite.
- **Asymmetric:** real. ADM models legitimately produce ⟨σv⟩ ≈ 0; a "row 4 disagreement > 10%" alarm fires on the wrong side of zero and pollutes the merged output with a cosmetic flag. The LLM can read a `model_class: "ADM"` tag and skip. A helper cannot, without inspecting the UFO — and inspecting the UFO is exactly the model-aware logic the lens forbids.
- **Majorana σ_SD:** real but milder. The "null vs 0.0 vs `—`" tension already exists in the existing SKILL.md (line 144) and is NOT a fresh risk. But the comparison rule ("skip the row when the model class makes σ_SD trivially zero") IS a model-class judgment.
- **10% threshold:** the lens table puts this in LLM territory by name ("Heuristic with a default but expert-overridable").

**Counter-counter I considered and reject.** The proposer-flagged counterargument ("most users run single-component thermal-relic WIMPs; optimize for the common case via a `model_class: single_wimp` parameter") is plausible but loses on two grounds: (a) the lens explicitly forbids putting a model-aware switch in code even when the switch is named — once the helper *takes* `model_class`, the helper IS model-aware; this is the exact tradeoff the lens kills; (b) the user's UX is "competent collaborator," and a competent collaborator who takes the time to explain *why* row 4 is being skipped for an ADM model is more valuable than a deterministic helper that prints a flag without context. The LLM rendering the rationale prose IS the UX win.

**What I add to the proposer's call.** A sharper minimal-helper boundary: `extract_field` is the ONLY primitive `compare_dm`-prose calls. The LLM does NOT regex-extract from MadDM stdout via a helper (per WS-1 §6.4) and does NOT compute rel-diff via a helper. Prose owns *both* the value-acquisition (for non-JSON producers) and the arithmetic. This forces the LLM to render the explanation alongside the comparison, which is the UX point. The proposer implies this but does not state it as a constraint; the synthesizer should pin it.

**v1.1 promotion path (§2.4) accepted.** A future `compare_dm_single_component` that exits `MULTICOMPONENT_OUT_OF_SCOPE` on detected multi-DM is fine; not WS-4 work.

### 2.2 `extract_field` design — under-specified

The proposer's §1.3 says `extract_field` takes `--json <path> --key <name> --schema-version <id>` and returns `{"value": <number|null>, …}`. Issues:

1. **Missing-field semantics.** Proposer says "exit non-zero with `KEY_ABSENT`." But `relic.schema.json` and `annihilation.schema.json` allow `omega_h2`/`sigma_v_zero` to be `oneOf [null, number]`. So "absent" and "present-as-null" are semantically distinct and the helper must distinguish them: present-as-null → exit 0, value=null; truly absent → exit 1, code=`KEY_ABSENT`. Proposer's text conflates them. **Synthesizer must pin.**

2. **Nested paths.** Proposer assumes top-level keys only ("extract a top-level key by name"). The schemas as written (proposer §6) ARE flat top-level — so the assumption holds for v1. But `annihilation.schema.json` has `channel_fractions` as a nested object. If the LLM ever needs `channel_fractions.bb`, the helper has no path to give it. **Decision needed:** flat-only and add a `--json-pointer` mode later (cleaner; matches `scattering.schema.json`-style flat keys), or accept dotted paths now (more expressive, larger surface). I lean flat-only — the LLM can `extract_field --key channel_fractions` and parse the dict in prose.

3. **Regex/stdout mode does NOT belong here.** Proposer §1.5 explicitly says "the router never regex-parses stdout in steady state" because W4-A makes micrOMEGAs emit JSON. Good. But until W4-A ships and tooling catches up, the WS-1 manifest entries 5 and 8 are `pending_schema` xfails reading from stdout. The helper does not handle that path. The LLM does. **This is correct under the lens** (regex on stdout is fragile and producer-private); flagging here so the synthesizer doesn't backslide.

4. **Schema-root indirection.** Proposer takes `--schema-root <dir>` defaulting to `plugins/shared/schemas/`. Fine, but the helper must verify the schema's `$id` matches `--schema-version`, NOT just load the file by filename. Otherwise a future `relic.schema.json` v2 file shadows the v1 path silently. **Synthesizer must add: helper asserts `schema["$id"].endswith("/" + schema_version)`.**

5. **Is it really one helper?** The proposer's three counterarguments to a 3-helper split are correct: stdout-regex is LLM territory, CSV-column extraction is v1.1 scan-only and out of scope, JSON-pointer can be added as a flag later if needed. **One helper, one mode (top-level JSON key from a pinned-schema file). Synthesizer endorses.**

### 2.3 Helper layout — A is right but `_shared/` deserves a one-line note

The proposer chose option A (`dark-matter-constraints/scripts/`) and the convention citation is correct in spirit (every existing skill puts its helpers in its own `scripts/` dir). The argument against `_shared/scripts/` (it currently holds only a symlinked schema, not code) is sound.

**One concern.** `extract_field` is the *one* helper that's plausibly reusable. `/ddcalc` reads `scattering.schema.json` today and could in principle use the same primitive. The proposer dismisses this as "speculative reuse." That's fine for v1. **Synthesizer should record:** if a second consumer surfaces (`/ddcalc`, or a future `/relic-only` micro-router), `extract_field` is the candidate to relocate; the others are router-specific. This is a 2-line note in AUDIT.md, not a WS-4 deliverable.

**`detect_drake` placement.** Proposer kept it in `dark-matter-constraints/scripts/`. The reviewer's natural counterargument — "DRAKE-specific, should live with `drake-install`" — is wrong because the helper is *a router-side state-reader*, not a producer-side detector. It WRAPS `/drake-install detect` with manifest-driven enum validation; the wrapping logic is router-specific. Co-location with the router is correct.

### 2.4 SKILL.md rewrite shape — 180–230 lines is right; cut list needs concretizing

The proposer's table (§4.1) is the right shape, but the "what stays vs cuts" decisions need concrete lines. Reading the live SKILL.md (356 lines):

**Cut these (proposer's call ratified):**
- Lines 41–58 (Step 1 prose) → 12 lines invoking `check_prereqs`. The bullet expansion of `MADDM_MISSING`, `UFO_MISSING`, `SLHA_MISSING` is duplicative with the Blocker / notice codes table at lines 295–309.
- Lines 186–211 (Step 5 four-branch availability prose) → 14 lines invoking `detect_drake`. The four branches collapse into "emit the helper's `router_action`."
- Lines 134–150 (Step 4 disagreement table) → ~18 lines that ROUTE through `extract_field` for each row but keep the field-name pair table and the model-class skip rules (the physics judgment).

**Keep these (under attack and surviving):**
- Lines 79–100 (Step 3 spectrum analysis, the 10% / 5% rationale). This IS physics-tutorial-rich prose, and it's exactly what makes the router a "competent collaborator" rather than a button. Cut would amputate the user-facing explanation. **Keep verbatim.**
- Lines 219–254 (Tool failure modes). This is the largest physics-tutorial section. The proposer keeps it; correct call. The MadDM "uses velocity expansion, fails near narrow resonances" paragraph is the entire reason the router exists. Helpers cannot replace this prose without losing the UX goal.
- Lines 258–291 (Merged output format). Templates are guides, not contracts.
- Lines 343–356 (What this skill does NOT do). Sets user expectations; cannot be moved into helper output.

**Relocate these (proposer didn't address):**
- Lines 313–324 (Config keys read). Today this is a flat table. After WS-1's `router_contract.json` ships, this table is *redundant* with `config_keys` section of the manifest. Proposer's added one-line note ("Authoritative source: `contracts/router_contract.json`") is right but doesn't go far enough. **Either remove the table entirely (point to the manifest) OR keep it with a "MIRROR — see manifest for canonical" header.** I lean: keep the table for human readers, add the header. Synthesizer decides.

**One paragraph the proposer cut that I'd preserve.** Step 2 prose at lines 60–66 ("MadDM's MG5/UFO path handles exotic Lorentz and color structures … micrOMEGAs' CalcHEP path can silently mishandle non-standard Lorentz/color structures"). Proposer says "Lightly trimmed" — but this paragraph is the *justification for the entire router*. If the user asks "why are we running both?" this is the answer. **Mark as preserve-verbatim.**

### 2.5 Producer SKILL.md edits W4-A..W4-E — line-number verification

See §3 below for verification table. Three of five are correct, one is hedged but feasible, one is mis-cited.

### 2.6 Schema files (W4-B) — `sigma_v_zero` name and other niggles

**Name `sigma_v_zero` correctness.** This is a real concern. The schema documents the field as the "v→0 limit" of ⟨σv⟩. Reading the existing `micromegas/SKILL.md` line 217: `sigma_v(v=0) = <value> cm^3/s`. The micrOMEGAs source emits ⟨σv⟩ at v→0 (what's used for indirect detection), NOT thermally averaged ⟨σv⟩(T_freezeout). The name is **accurate**, not misleading. MadDM's `sigmav_total` (the legacy `sigmav_xf`) is the same quantity at freezeout — and the W4-C edit reconciles the producer side. The two names refer to physically *similar* quantities (both are ⟨σv⟩ at low velocity, the v→0 limit being the relevant indirect-detection observable), but they're not identical: `sigmav_xf` is at freeze-out v, `sigma_v(v=0)` is at v→0. **Synthesizer must record this:** the canonical schema name `sigma_v_zero` is correct as a v→0 quantity; producers that emit it from a different v must convert OR document the discrepancy in the JSON. The schema does not enforce v=0 (no way to enforce that via JSON Schema). This is a producer-side discipline issue. **Add a description string to the schema: `"sigma_v_zero": {"description": "Annihilation cross-section at v→0 (cm³/s). Producers emitting at v=v_freezeout MUST convert to v→0 before writing this field, OR set to null."}`.**

**`model_class` field.** Proposer §6.1 makes it free-form `string`. I agree against an enum: the lens forbids whitelisting model classes (model-agnosticism by under-specification). Free-form string + producers self-identify is correct.

**No `version` field beyond `$id`?** The proposer's schemas use `schema_version: const "relic/v1"` AND `$id: ".../relic/v1"`. Two pins, both required. The `const` is what JSON Schema validators check; the `$id` is the URI. Fine, matches `scattering.schema.json` exactly.

**Missing required vs `oneOf null`.** The proposer makes `omega_h2` required-but-nullable (`oneOf [null, number]`) and `xf` optional-and-nullable. Why the asymmetry? Because every relic-density run produces an Ωh² result-or-null (at minimum, `OMEGA_UNCONVERGED` records null), but `xf` is producer-specific (DRAKE doesn't emit it). Correct call.

### 2.7 CLI invocation pattern — `python -m` is right

The proposer chose `python -m …scripts.<name>` + argparse + JSON stdout. Alternatives:

- **Bash for `detect_drake`?** Tempting because `cmd_detect` is bash. But the helper's job includes (a) loading and validating against `router_contract.schema.json`, (b) asserting the live status is in the manifest's enum literals. (a) requires `jsonschema`, which is Python. Bash + jq could do (b) alone, but not (a). **Python wins.** Bash-shaping the helper would force a Python sub-call anyway.
- **Pure jq for `extract_field`?** Genuinely tempting. `jq -e ".$key" file.json` IS one line. But `jsonschema.validate` against `relic/v1` is the load-bearing safety check (otherwise the helper will happily extract a key from a schema-mismatched JSON). jq cannot do that. Python wins.
- **Single multi-subcommand entry point** (`dmc-helpers prereq`/`detect-drake`/`extract-field`)? Reduces the four `python -m …` invocations to one. Argument against: each helper has a different LLM-side prose narrative, and `python -m …scripts.<name>` makes the boundary visible in SKILL.md. A single entry point obscures which primitive is being called. **Reject.** Four separate `python -m` invocations is the right shape.

**Synthesizer endorses proposer's choice.**

### 2.8 Risks the proposer missed

The proposer's §7 is solid. Three additional risks:

1. **`router_contract.json` path indirection in helpers.** Proposer hardcodes `--manifest <path>` as a CLI flag, defaulting to "the absolute `router_contract.json`." But the SKILL.md prose example (§4.2) literally writes the absolute path string. If the manifest moves (W4-A renames `contracts/` to `contract/`, say), every helper invocation breaks AND every SKILL.md example breaks. **Synthesizer must add:** helpers default to `Path(__file__).parent.parent / "contracts" / "router_contract.json"` (relative to the helper's own location, NOT a hardcoded absolute path); SKILL.md examples USE the default and don't pass `--manifest` unless overriding for tests. Cuts the doc-vs-CLI drift surface from §7.1.2.

2. **`__init__.py` Python package shape.** Proposer's layout has `dark-matter-constraints/scripts/__init__.py` and a Python module path of `plugins.constraints.skills.dark_matter_constraints.scripts.<name>`. But `dark-matter-constraints` has a HYPHEN — an invalid Python identifier. The module path can't be `dark_matter_constraints` UNLESS there's a top-level `plugins/__init__.py`, `plugins/constraints/__init__.py`, etc., with explicit name remapping. **None of those `__init__.py` files exist today** (verified via `ls /Users/yianni/Projects/hep-ph-agents/plugins/`). The `formcalc` skill solves this differently — its `run_formcalc.py` is invoked as `python /path/to/run_formcalc.py …`, NOT `python -m`. **Synthesizer must resolve:** either (a) require a `python /absolute/path/to/scripts/<name>.py …` invocation (matches existing repo convention; SKILL.md must use absolute paths or a `$REPO_ROOT`-relative path), OR (b) ship the missing `__init__.py` files in `plugins/`, `plugins/constraints/`, `plugins/constraints/skills/`, and rename `dark-matter-constraints` to `dark_matter_constraints` (massive scope creep, breaks the marketplace name). I strongly favor (a). Proposer's §3 closing note "Convention matches `formcalc/scripts/run_formcalc.py`" is right that formcalc is the template, but formcalc does NOT use `python -m` — proposer hallucinated the invocation pattern.

3. **`verify_router_field_contract` overlap with WS-1 T3.** The proposer §1.4 says this helper "backs WS-2's test." But WS-1 plan T3 already ships `test_router_contract.py` as an executable contract test (acceptance gate #1: "pytest exits 0"). T3 is currently expected to inline its dispatch logic (per WS-1 plan §5's 18 cases). If WS-4 later EXTRACTS that logic into a helper, the WS-1 test must be retroactively rewritten to import the helper. **Either WS-1 ships T3 with the dispatch inline AND WS-4 is responsible for the refactor (extra work), OR WS-1 ships the helper alongside T3 (scope creep into WS-1)**. Proposer asserts the former without flagging the cost. **Synthesizer must pin: WS-4 owns both (a) authoring `verify_router_field_contract.py` and (b) rewriting `test_router_contract.py` to import it; the test must continue to pass after the rewrite.** WS-1 ships an inline test; WS-4 extracts.

---

## 3. Source-file verification (W4-A..W4-E)

Verified against the live worktree. Pass = proposer's claim holds; FAIL = needs adjustment.

| ID | Claim | Verification | Status |
|---|---|---|---|
| W4-A line 99 | Per-run output table row for `summary.json` | Confirmed at `micromegas/SKILL.md` line 99: `\| `summary.json` \| Validated against `plugins/shared/schemas/scattering.schema.json` \|` | **PASS** |
| W4-A line 226 | `summary.json` schema example block | Confirmed at lines 225–239 (the JSON example block is at 226 onward; the heading "Reading micrOMEGAs output" precedes at 205). Proposer's "Edit 2 (line 226)" lands correctly. | **PASS** |
| W4-A line 207 | "Reading micrOMEGAs output" prose for steady-state vs legacy paragraph | Confirmed at lines 205–223. Proposer's paragraph insertion is well-targeted. | **PASS** |
| W4-C line 164 | `sigmav_xf` line in MadDM SKILL.md | Confirmed at `maddm/SKILL.md` line 164: `  \`sigmav_xf = <value>\` (cm³/s); or the section header \`<sigma v>\``. JSON example at line 176 already says `sigmav_total`. Proposer's edit shape is correct. | **PASS** |
| W4-D ~line 213 | DRAKE Ωh² comparison in `dark-matter-constraints/SKILL.md` | Confirmed at line 213: `If DRAKE runs, collect its Ωh² output. Compare to MadDM Ωh²: if the relative …`. Proposer's line number is exact. | **PASS** |
| W4-E lines 84–86 | `drake/SKILL.md` `activation_required` topology note | Confirmed at lines 84–86: `Note: \`activation_required\` is emitted by the \`use-path\` subcommand (not \`detect\`) when a smoke test fails only because Wolfram Engine needs activation. \`detect\` returns \`configured\`, \`found\`, or \`missing\`.` Proposer's edit shape is correct. | **PASS** |
| W4-E feasibility (`detect` extension) | Proposer flagged uncertainty about whether `install.sh detect` "carries enough state to distinguish 'activation needed' from 'binary missing.'" | **WRONG — proposer overstated risk.** Read `drake-install/scripts/install.sh` lines 113–142 (`cmd_detect` body). The function calls `run_smoke "$path" "$ws"` (line 121) and parses a JSON `status` field (line 122). The smoke output already DOES emit `activation_required` (confirmed by line 188's `cmd_use_path` case statement using the same `run_smoke` and matching `activation_required`). `cmd_detect` currently FALLS THROUGH to `found` when the smoke status is non-`ok` (line 129 comment: "Smoke test did not pass — fall through to 'found' to avoid claiming configured"). The fix is one branch: between lines 128 and 130, add `if status=activation_required → emit activation_required JSON`. **Trivial, ~5 lines of bash. NOT a feasibility risk.** Proposer should have read the script. | **CORRECT-WITH-CORRECTION** (the doc edit lands; the bash change is shallow, NOT deep) |

**Convention citation finding.** Proposer §3 says "`formcalc/scripts/run_formcalc.py`" but the file lives at `plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py`, not `plugins/qft/skills/formcalc/scripts/`. The proposer's closing note in §3 ("Convention matches `formcalc/scripts/run_formcalc.py`") elides the plugin parent and so doesn't directly assert a wrong path, but a careless reader could plausibly look in the wrong plugin. Two corrections needed: (a) cite the full path `plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py`; (b) re-check the convention claim: this script is invoked as a direct path, NOT as `python -m`. Proposer's §3 closing line ("Convention matches…") is half-right (file shape matches) and half-wrong (invocation pattern does NOT match — see §2.8 risk 2 above).

---

## 4. New issues discovered (not in proposer's risk list)

1. **Python module-path infeasibility.** §2.8 risk 2 above. Proposer's `python -m plugins.constraints.skills.dark_matter_constraints.scripts.<name>` will not resolve without `__init__.py` files at every level AND a name change from `dark-matter-constraints` to `dark_matter_constraints`. The fix (use `python /path/to/scripts/<name>.py`) IS the formcalc convention; proposer cited the right reference and then violated it.

2. **Manifest path indirection.** §2.8 risk 1. Hardcoded `--manifest` defaults break on dir rename. Helpers should default to a path computed from `__file__`.

3. **`extract_field` null-vs-absent semantics.** §2.2 issue 1. `oneOf [null, number]` makes "field present, value null" a valid result (exit 0). "Field absent" must be a different result (exit 1, `KEY_ABSENT`). Proposer conflated.

4. **`schema_version` self-check.** §2.2 issue 4. Helper must verify `schema["$id"]` matches `--schema-version`. Otherwise the schema-root indirection allows silent shadow loading.

5. **WS-1 T3 vs WS-4 helper extraction.** §2.8 risk 3. WS-4 must own the rewrite of `test_router_contract.py` to import `verify_router_field_contract`, not just author the helper. Otherwise WS-1's T3 sits as inline-dispatch code that nobody updates.

6. **`sigma_v_zero` is an ambiguous name across producers.** §2.6. micrOMEGAs emits at v→0; MadDM emits at v=v_freezeout. Same field name, slightly different physical quantities. Schema should carry a `description` string asserting the v→0 convention; producers that emit from another v MUST convert. This is producer discipline, not enforceable in JSON Schema, but documenting it in the schema is the right place.

7. **`bash` change in W4-E is trivial, not deep.** §3 finding. Proposer's "may need to defer the bash change to a follow-up if `install.sh detect` doesn't carry enough state" is wrong. The state already exists (smoke result already encodes `activation_required`); the change is one bash branch in `cmd_detect`. WS-4 ships it inline with W4-E, not deferred.

8. **Step 2 paragraph (lines 60–66) is the entire router's justification.** §2.4 closing. Proposer says "lightly trimmed" without specifying. Synthesizer must mark this paragraph as preserve-verbatim — it's the user-facing answer to "why are we running both MadDM and micrOMEGAs?"

---

## 5. Synthesizer must resolve

Numbered, binding for the WS-4 plan-drafter:

1. **CLI invocation pattern.** Replace `python -m plugins.constraints.skills.dark_matter_constraints.scripts.<name>` with `python "$REPO_ROOT/plugins/constraints/skills/dark-matter-constraints/scripts/<name>.py"` (matches the formcalc convention; avoids the module-path infeasibility from `__init__.py` absence and the `dark-matter-constraints` hyphen). All SKILL.md prose examples must use this form. Helpers stay dual-mode (importable + CLI), but tests `import` via `importlib.util.spec_from_file_location`, NOT via `python -m`.

2. **Manifest path default.** Helpers default `--manifest` to a path computed from `Path(__file__).parent.parent / "contracts" / "router_contract.json"` (relative to the helper's location). SKILL.md examples DO NOT pass `--manifest` unless overriding for tests.

3. **`extract_field` null-vs-absent semantics.** Helper distinguishes:
   - `--key` present in JSON, value matches a schema branch (number or null per `oneOf`): exit 0, stdout `{"value": <number|null>, …}`.
   - `--key` absent from JSON entirely: exit 1, stderr `{"error": "key absent", "code": "KEY_ABSENT"}`.
   - Schema mismatch (e.g. `schema_version` field doesn't match `--schema-version`): exit 1, code `SCHEMA_MISMATCH` or `VERSION_DRIFT`.
   - Schema's `$id` does not end with `--schema-version`: exit 1, code `VERSION_DRIFT`.
   - I/O error: exit 2, code `EXTRACT_FIELD_INTERNAL`.

4. **W4-E scope.** Bash edit to `drake-install/scripts/install.sh cmd_detect` is in WS-4 implementation scope, NOT deferred. The existing `run_smoke` already returns `activation_required`; `cmd_detect` adds one branch (~5 lines) between lines 128 and 130 to surface it. Includes producer-side test update (or new test) verifying `cmd_detect` emits `activation_required` when smoke does.

5. **WS-1 T3 ↔ WS-4 helper extraction.** WS-4 owns BOTH (a) authoring `verify_router_field_contract.py` and (b) rewriting `test_router_contract.py` to import it. The rewritten test must keep all 18 cases from WS-1 plan §5 passing AND the negative-control gate green. Plan-drafter scopes this as part of the helper task, NOT a separate task.

6. **Schema `description` for `sigma_v_zero`.** `annihilation.schema.json` includes a `description` string on `sigma_v_zero` asserting the v→0 convention: `"Annihilation cross-section at v→0 (cm³/s). Producers emitting at v=v_freezeout MUST convert to v→0 before writing this field, OR set to null."` Same treatment optional for `omega_h2` (less ambiguous; one-line description fine).

7. **SKILL.md preserve-verbatim list.** In addition to the proposer's "Tool failure modes / Merged output format / Blocker codes / Cross-skill / NOT" preservation, mark these explicitly preserve-verbatim:
   - Step 2 paragraph at lines 60–66 (MG5/UFO vs CalcHEP rationale — the router's justification).
   - Step 3 prose at lines 79–100 (10% / 5% rationale — physics-tutorial-rich, expert-overridable per lens).
   - Lines 343–356 (What this skill does NOT do — sets user expectations).

8. **`compare_dm` LLM-only constraint sharpening.** Synthesis must explicitly state: `compare_dm` prose calls ONLY `extract_field` as a primitive. No regex helper, no rel-diff helper, no flag-renderer helper. The LLM owns value-acquisition for non-JSON producers (MadDM stdout per WS-1 §6.4) AND the rel-diff arithmetic AND the model-class skip rules. This is the lens-aligned UX boundary; pin it so v1.1 doesn't regress.

---

## Closing

The proposal is a strong WS-4 starting point. The four helpers are right, the schema split is right, the SKILL.md target shape is right, and the lens-conformance check is honest. The eight items in §5 are the gaps the synthesizer must resolve before WS-4's plan-drafter can mechanically translate to tasks. None are fatal; all are concrete and bounded.

The single highest-stakes item is #1 (CLI invocation pattern) — proposer's `python -m` will silently fail to resolve when an LLM reads SKILL.md and tries the literal command. Fixing it to match the existing formcalc convention is a one-line change with downstream prose updates, and it's load-bearing for WS-2 (test imports) and WS-3 (live router invocation).
