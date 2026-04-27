# WS-4 Proposal — Refactor: helpers + SKILL.md rewrite

**Proposer:** WS-4 brainstorm proposer
**Inputs read end-to-end (in order):** `briefs/ROUTING_LENS.md`; `brainstorm/ws1_synthesis.md`; `plan/ws1_plan_final.md` (esp. §7 W4-A…W4-G and §8 hand-off table); `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (355 lines); `plugins/constraints/skills/micromegas/SKILL.md` (lines 85–245 in detail); `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (lines 140–185 in detail); `plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 70–95 in detail); `plugins/constraints/skills/_shared/` (verified contents: `__init__.py`, `tests/`, symlinked `blocker.schema.json`); existing helper conventions across `plugins/*/skills/*/scripts/` and `plugins/*/skills/_shared/*.py`.

This proposal does NOT implement anything. It is the design that WS-4's plan-drafter mechanically translates to tasks, and that the WS-4 critic adjudicates against.

---

## 1. Helper inventory

WS-1 §7 names exactly four code-side helpers, with `compare_dm` flagged as conditional in the lens. The synthesis lists:

1. `verify_router_field_contract(manifest_path, fixtures_root)` — drives WS-2 test harness (the audit's enforcement helper).
2. `check_prereqs(config, manifest_path)` — Step 1 prereq check.
3. `detect_drake(manifest_path)` — Step 5a four-branch tool-state check.
4. `extract_field(json_path, key, schema_version)` — pinned-schema field extraction.

WS-1 plan §8 row W4-F names all four, plus implies `compare_dm` lives in the LLM (synthesis §7 closing list explicitly: "`compare_dm()` numerical adjudication … stays LLM until multi-component DM is in scope"). So **the four helpers are the four primitives above, and `compare_dm` is NOT a helper — it stays in SKILL.md prose**, calling `extract_field` as its primitive when it needs a value out of a pinned-schema JSON.

This is the lens-aligned read of WS-1, and §2 below defends it head-on.

### 1.1 `check_prereqs`

- **Responsibility.** Pure file-existence + config-key presence. Drives Step 1 of the router's decision tree.
- **Consumes.** CLI args `--config <path>` (default: env `HEPPH_CONFIG_PATH` then a documented absolute fallback), `--manifest <path>` (default: the absolute `router_contract.json`), `--model <name>` (the BSM model the router was invoked with).
- **Produces.** stdout: a single-line JSON object `{"status": "ok"|"blocked", "blockers": [{"code": "MADDM_MISSING"|"UFO_MISSING"|"SLHA_MISSING_HINT"|"DRAKE_PATH_UNSET", "message": "...", "fixit_skill": "/maddm-install"}], "checked": [...]}`. stderr: empty on success; on internal error (manifest unparseable, config unreadable) a single-line JSON `{"error": "...", "code": "PREREQ_HELPER_INTERNAL"}` and exit 2. Exit 0 if `status == ok`; exit 1 if blocked-but-helper-ran-fine; exit 2 on internal error.
- **Manifest dispatch.** Reads `config_keys` section. For each entry, dispatches on `type`: `path_or_bool` ⇒ check the value is set AND (if a path) the file/dir exists.
- **Model-agnosticism.** **Yes, guaranteed.** File existence is invariant under model class. The one model-aware nuance is `latest_slha`: the router's existing prose says it's required only for MSSM-class. We resolve this by emitting a *hint* blocker code (`SLHA_MISSING_HINT`, recoverable) rather than fatal, leaving the LLM to decide whether to honor it based on model class. The LLM keeps the judgment; the helper just surfaces the fact.
- **Edge case.** `config.models[<model>].ufo_path` may not exist as a literal config dot-path in the YAML; the helper accepts a JSONPath-style locator from the manifest's `config_keys[i].path` (e.g. `models.<model>.ufo_path`). The router's `<model>` arg is interpolated into `<model>` placeholders by the helper, not by the LLM — keeps the LLM out of path arithmetic.

### 1.2 `detect_drake`

- **Responsibility.** Step 5a: walks the four-branch availability table (`config.drake_path` absent → `Branch1`; set → invoke `/drake-install detect`, parse status, map to one of `configured|found|missing|activation_required|unparseable`).
- **Consumes.** `--config <path>`, `--manifest <path>` (used to validate the literal-set against `status_enums[0].literals`), env `HEPPH_DRAKE_DETECT_CMD` (test override; default invokes the install skill's detect script).
- **Produces.** stdout: `{"branch": "branch1_unset"|"branch2_detect", "status": "configured"|"found"|"missing"|"activation_required"|"unparseable", "router_action": "proceed"|"emit_DRAKE_MISSING"|"emit_DRAKE_ACTIVATION_REQUIRED"|"emit_DRAKE_UNAVAILABLE", "raw_detect_output": "..."}`. Exit 0 always (this is a state report, not a gate); the router LLM uses `router_action` to pick the blocker code to emit.
- **Manifest dispatch.** Reads `status_enums[0].literals` and asserts the live detect output is in that set. Drift (e.g. detect emits a new literal) ⇒ `status: "unparseable"` + `raw_detect_output` populated; LLM surfaces `DRAKE_UNAVAILABLE`.
- **Model-agnosticism.** **Yes, guaranteed.** DRAKE installation state has zero model-class dependence. This helper is the cleanest of the four.
- **One subtlety.** WS-1 logs the `pending_producer_topology_fix` xfail because `detect` doesn't currently emit `activation_required`. Per W4-E we extend `/drake-install detect` to emit it, so the helper's branch table aligns with reality. The helper itself doesn't change shape — it just stops returning `unparseable` once W4-E lands.

### 1.3 `extract_field`

- **Responsibility.** For pinned-schema artifacts (today: `summary.json` against `scattering/v1`; after WS-4 ships `relic.schema.json`/`annihilation.schema.json`, also `relic.json`/`annihilation.json` against their respective `relic/v1`/`annihilation/v1`): open file, validate against pinned schema, extract a top-level key by name, return value (or `null` if `oneOf null` schema branch matches).
- **Consumes.** `--json <path>`, `--key <name>`, `--schema-version <id>` (e.g. `scattering/v1`). Optionally `--schema-root <dir>` (default: `plugins/shared/schemas/`).
- **Produces.** stdout: `{"value": <number|null>, "key": "<name>", "schema_version": "<id>", "source_file": "<abs-path>"}`. On schema mismatch: stderr `{"error": "...", "code": "SCHEMA_MISMATCH"|"KEY_ABSENT"|"VERSION_DRIFT"}` and exit non-zero. Exit 0 on clean extract; exit 1 on schema/key drift; exit 2 on I/O error.
- **Manifest dispatch.** N/A directly — but the LLM (or `compare_dm` LLM-side prose) calls this helper once per field it needs. The manifest entries with `produced_by: summary_json` carry the `schema_version` and key, so the LLM doesn't invent either name.
- **Model-agnosticism.** **Yes, guaranteed.** Schema is pinned with `additionalProperties: false`; the field either exists with the typed value or `null`, no model-class branch ever appears in code. This is the cleanest "contract between tools" primitive in WS-1's lens table.
- **What it deliberately does NOT do.** Compute differences. Choose canonical names. Compare across producers. All of that is `compare_dm` LLM territory.

### 1.4 `verify_router_field_contract`

- **Responsibility.** WS-2's test entry point. Loads `router_contract.json`, dispatches per-entry on `produced_by`, runs the appropriate check (jsonschema validate, regex match, JSON pointer resolve), aggregates pass/fail/xfail. Per WS-1 plan §5 this is the test harness's main loop.
- **Consumes.** `--manifest <path>` (env-overridable for the negative-control gate, per WS-1 plan T3 acceptance gate #3), `--fixtures-root <path>`.
- **Produces.** Exit 0 on full pass (incl. xfail policy honored); exit non-zero with named drift code (`DRIFT_PRODUCER_DOC_GAP`, …) on contract failure. Stdout: pytest-style line-per-row summary with `OK`/`XFAIL`/`FAIL` and the drift code on failures.
- **Model-agnosticism.** **Yes, guaranteed.** Pure string match + JSON pointer + jsonschema.validate. No physics.
- **Where it lives.** Per §3 below, this is shipped as a Python module that the WS-2 pytest file imports — that file IS `tests/test_router_contract.py` from WS-1 plan T3. So WS-1 ships the test, WS-4 ships the importable helper backing it. WS-2 then wires the test into the harness CI hook.

### 1.5 What deliberately did NOT make the helper list

- `compare_dm` (the relative-difference computation). See §2.
- `read_maddm_output` / `read_drake_output`. WS-1 §6.4 already pinned these to LLM until WS-3 produces real-format evidence. WS-4 honors that decision — no parser helper.
- `read_micromegas_output` (stdout regex extraction for `omega_h2` / `sigma_v_zero`). WS-1 logged these as `pending_schema` xfails because the canonical fix is `relic.json` / `annihilation.json`, NOT a regex helper. Once W4-A/W4-B land, these reads route through `extract_field` against the new schemas, with stdout-regex as a fallback documented in `/micromegas` SKILL.md prose for legacy users. **The router never regex-parses stdout** in the steady state. (See §5 W4-A.)
- `render_merged_output`. SKILL.md "Merged output format" section is a Markdown template the LLM fills in; rendering is judgment, not contract. Stays in SKILL.md prose. (See §4.)

---

## 2. `compare_dm` model-agnosticism deep-dive

**Verdict: keep `compare_dm` out of code. It stays in SKILL.md prose. WS-4 ships `extract_field` as the primitive `compare_dm` calls when it needs a value.**

This is the highest-stakes call in WS-4. Both sides argued below; the lens forces the LLM-side answer.

### 2.1 The case for putting `compare_dm` in code

Surface argument. The arithmetic is trivial:

```
rel_diff(a, b) = abs(a - b) / max(abs(a), abs(b))   # if both non-null
flag = (rel_diff > 0.10)
```

Step 4b is four rows (Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩(v→0)), each is one rel-diff, the threshold is fixed at 10%. A 30-line Python helper could do it. The lens table even says "A contract between tools (field names, schemas, exit codes) → Deterministic helper (code)." Field-name pairs ARE a cross-tool contract — `Omegah2` (MadDM) ↔ `omega_h2` (micrOMEGAs) is exactly the kind of thing the manifest pins. So why not also pin the comparison?

Performance. Helper is ~10× faster than LLM rel-diff arithmetic at scan scale. (Currently irrelevant — no scan path lives in v1 — but a future v1.1 micrOMEGAs scan would benefit.)

Test surface. With `compare_dm` in code, WS-2's test harness can drive it with synthetic dual-tool fixtures and assert `flag` is correct without LLM-in-the-loop. With it in prose, WS-3 is the only check.

### 2.2 The case against (the lens-forced answer)

Multi-component DM. micrOMEGAs has `darkOmega2` for two-component DM; MadDM today only handles single-component. A model with two stable DM particles has TWO Ωh² values (one per component) plus a sum. The single-row "Ωh² MadDM vs Ωh² micrOMEGAs" comparison is *meaningless* — MadDM emits the sum (or the dominant component) and micrOMEGAs emits both. The router would have to know which component to pair, and the answer depends on the model's mass ordering, abundance, and which is "primary." That's a judgment call. micromegas/SKILL.md line 134 confirms multi-component is currently `MULTICOMPONENT_UNSUPPORTED` (fatal recoverable) in v1 — but the user's roadmap presumably reaches v1.1+ with multi-component support, and committing `compare_dm` to code now means a load-bearing rewrite then.

Asymmetric DM. ADM models have suppressed (or zero) ⟨σv⟩(v→0) today because annihilation is depleted by the asymmetry. The "row 4: ⟨σv⟩ disagreement > 10%" check will fire trivially (zero vs near-zero) and pollute the output with a false flag. The LLM should know to skip the row; a helper would have to know what "asymmetric" means at the model layer. It can't, without inspecting the UFO.

Null handling. The current SKILL.md (line 144) says: "If `/maddm` returns `sigma_sd_proton: null` (e.g. direct detection not requested), record `—` rather than zero." A helper could implement this rule *for known fields*, but the boundary between "this field is null because the observable wasn't requested" vs "this field is null because the producer failed" vs "this field is null because the model class doesn't have it" (e.g. a Majorana DM has zero σ_SD by symmetry — `null`? `0.0`? `—`?) is a judgment call. micromegas/SKILL.md line 240 already has the analogous tension: "Use 0.0 for any cross-section that is absent or negative (schema requires non-negative values)" — that's a producer-side rule that loses information. The router can't safely re-decide it in code.

Threshold reasonableness. The 10% threshold is heuristic. The user's `briefs/ROUTING_LENS.md` table explicitly classes "Heuristic with a default but expert-overridable" as **LLM** territory. An expert with a Sommerfeld-enhanced model should be able to say "for this model, 5% is the right disagreement gate" without a code change. Hardcoding 10% in `compare_dm` violates the lens.

Schema-vs-text. The MadDM "schema" today is agent-parsed prose extraction (W4-C is still pending). `extract_field` works on JSON; for MadDM the LLM still has to do `read_maddm_output` (LLM-side per WS-1 §6.4 and §1.5 above). So `compare_dm` would be hybrid — calling `extract_field` for micrOMEGAs and `read_maddm_output` for MadDM. The LLM is already in the loop for one half of every comparison. Adding code for the other half is contortion.

### 2.3 Verdict and minimal helper that survives

**`compare_dm` stays in SKILL.md prose. The minimal helper that survives is `extract_field` — a primitive that pulls one named field from one pinned-schema JSON.** The LLM constructs the comparison row-by-row by:

1. Calling `extract_field --json <maddm_run>/maddm_output.json --key Omegah2 --schema-version maddm/v1` (post-W4-C, after the MadDM JSON gets a schema; until then, the LLM agent-parses `MadDM_results.txt` per existing prose).
2. Calling `extract_field --json <mo_run>/relic.json --key omega_h2 --schema-version relic/v1` (post-W4-A/B).
3. Doing rel-diff arithmetic in prose (LLM is fine at simple arithmetic; SKILL.md gives the formula).
4. Deciding flag/skip per the model-class judgment rules SKILL.md documents.

**This means WS-4 forfeits the test-harness surface for `compare_dm`.** WS-2 cannot pytest-assert that the rel-diff is correct without LLM-in-the-loop. Mitigation: WS-2 can fixture-drive `extract_field` alone (assert it returns the right `value` for the right `key` against the right `schema_version`), AND WS-3's Dark SU(3) playtest exercises the full LLM-driven `compare_dm` end-to-end. Two layers of test, neither in unit-pytest, but coverage is real. **This is the lens-aligned cost.**

### 2.4 Promotion path to v1.1

If WS-3 + ongoing experience prove `compare_dm` IS reliably model-agnostic for single-component thermal-relic DM (the 95% case), v1.1 can promote a *narrow* `compare_dm_single_component` helper that exits with a `MULTICOMPONENT_OUT_OF_SCOPE` code if it detects more than one DM candidate in the spectrum. WS-4 leaves the door open by NOT forbidding the future helper, just by not shipping it now. The decision log in §8 records this explicitly.

---

## 3. Helper layout

**Decision: `plugins/constraints/skills/dark-matter-constraints/scripts/`.**

Three options were on the table:

| Option | For | Against |
|---|---|---|
| A. `dark-matter-constraints/scripts/` | Matches every existing per-skill convention (`maddm/scripts/`, `micromegas/scripts/`, `drake/scripts/`, `formcalc/scripts/`, …). Keeps the router's helpers co-located with the router's SKILL.md. WS-2 imports are `from plugins.constraints.skills.dark_matter_constraints.scripts import …` — a clean module path. |  Reusability across other meta-skills (none planned today). |
| B. `plugins/constraints/skills/_shared/scripts/` | The `_shared/` dir already exists in `constraints/skills/`. Helpers like `extract_field` could in principle be reused by `/ddcalc` (which also reads `scattering.schema.json`). |  `_shared/` today holds a symlinked schema, NOT scripts. Promoting it to a code dir changes its convention. `/ddcalc` doesn't currently use `extract_field` — speculative reuse. |
| C. New `plugins/_helpers/` top-level | Maximally generic. |  No top-level helper dir exists in the repo. Inventing one for four scripts is over-architected. The `model-building/skills/_shared/sarah_name.py` pattern shows per-plugin shared code stays inside the plugin. |

**Choice: A.** Three reasons:

1. **Convention.** The repo's existing `scripts/` convention is per-skill, not per-plugin. `model-building/skills/_shared/sarah_name.py` is the only cross-skill shared Python in the repo, and it lives inside one plugin's `_shared`, not a top-level. Following the dominant pattern minimizes drift surface.
2. **Lens-aligned scoping.** These helpers are *router-internal contracts*. `check_prereqs` reads the router's `config_keys` manifest section. `detect_drake` reads the router's `status_enums`. `verify_router_field_contract` IS the router's manifest test driver. Only `extract_field` is plausibly reusable, and its consumer surface today is exactly one (the router). Co-locating with the router keeps the contract tight.
3. **Test ergonomics.** The existing `formcalc/scripts/` + `formcalc/tests/` convention has the test importing the helper via relative path. WS-2's `test_router_contract.py` (in `dark-matter-constraints/tests/`) needs to import these helpers; co-location makes that import a one-liner.

**Concrete layout WS-4 ships:**

```
plugins/constraints/skills/dark-matter-constraints/
├── SKILL.md                                            (rewritten; see §4)
├── contracts/
│   ├── router_contract.json                            (WS-1)
│   ├── router_contract.schema.json                     (WS-1)
│   └── AUDIT.md                                        (WS-1)
├── scripts/                                            (NEW — WS-4)
│   ├── __init__.py
│   ├── check_prereqs.py                                # CLI + import-able function
│   ├── detect_drake.py                                 # CLI + import-able function
│   ├── extract_field.py                                # CLI + import-able function
│   └── verify_router_field_contract.py                 # CLI + import-able function (backs WS-2's test)
└── tests/                                              (WS-1 / WS-2)
    ├── __init__.py                                     (WS-1)
    ├── test_router_contract.py                         (WS-1; uses verify_router_field_contract)
    ├── test_check_prereqs.py                           (WS-2 — tests the helper unit)
    ├── test_detect_drake.py                            (WS-2)
    ├── test_extract_field.py                           (WS-2)
    └── fixtures/                                       (WS-1 + WS-2 additions)
```

Each helper is dual-mode: importable function (`def check_prereqs(config, manifest) -> Result:`) AND CLI entrypoint (`python -m …scripts.check_prereqs --config … --manifest …`). The LLM invokes via CLI from SKILL.md prose; tests import the function. Convention matches `formcalc/scripts/run_formcalc.py`.

**Dependencies.** Stdlib only (`json`, `pathlib`, `re`, `argparse`, `subprocess`) plus `jsonschema` (already in repo per `test_scattering_schema.py`). No new deps. **No bash, no jq inside helpers** — the WS-1 plan uses `jq` only in *acceptance-gate shell snippets*, not inside code.

---

## 4. SKILL.md rewrite shape

**Length target: 180–230 lines (down from 355).** Structural verdict: **decision-tree-with-primitives** (NOT a full rewrite).

### 4.1 What stays, what shrinks, what moves

| Section | Current lines | New lines | Disposition |
|---|---|---|---|
| YAML frontmatter | 1–4 | 1–4 | Unchanged. |
| Invocation | 20–35 | 20–35 | Unchanged. The CLI args stay; the table stays. |
| Decision tree intro | 37–39 | 37–39 | Unchanged. |
| Step 1 — Prereq check | 41–58 | ~12 lines | **Replace prose with helper invocation.** "Run `python -m plugins.constraints.skills.dark_matter_constraints.scripts.check_prereqs --config $CONFIG --manifest $MANIFEST --model $MODEL`. If `status: blocked`, emit each blocker code per the `blockers[]` array. The `SLHA_MISSING_HINT` blocker is informational only — adjudicate based on model class." |
| Step 2 — MadDM | 60–77 | 14 lines | **Lightly trimmed.** Keeps the MG5/UFO rationale (this is *physics judgment* the LLM owns). Subcommand mapping table unchanged. |
| Step 3 — Spectrum analysis | 79–100 | ~18 lines | **Unchanged in substance, slightly compressed.** Triggers A/B and the 10% rationale stay — they're heuristic with expert override per the lens. |
| Step 4a — micrOMEGAs invocation | 102–132 | ~16 lines | **Unchanged in substance.** Subcommand mapping stays; rationale stays. |
| Step 4b — disagreement comparison | 134–150 | ~18 lines | **Refactored to call `extract_field`** but the prose stays LLM-side. New form: "For each row, call `extract_field` against MadDM JSON and micrOMEGAs JSON, compute rel-diff in prose, flag at >10%. Use `—` for null fields. Skip rows where the model class makes the comparison meaningless (multi-component DM, asymmetric DM). Do NOT silently average or pick a winner." Table preserved. |
| Step 5a — DRAKE availability | 152–211 | ~14 lines | **Replace four-branch prose with `detect_drake` invocation.** "Run `python -m …scripts.detect_drake --config $CONFIG --manifest $MANIFEST`. Emit the blocker code from the helper's `router_action` field. The resonance-warning text below applies whenever `router_action != proceed`." Resonance-warning text block (currently lines 191–211) stays. |
| Step 5b — narrow-resonance trigger | 152–185 (interleaved) | ~10 lines | **Unchanged.** The 5% trigger is heuristic per the lens. |
| Tool failure modes | 219–254 | 219–254 | **Unchanged.** This is documentation of physics gotchas. The lens table doesn't even mention it because it's not routing. Stays. |
| Merged output format | 258–291 | ~30 lines | **Stays in SKILL.md.** Rendering is judgment. The Markdown template is a guide, not a contract. (The lens table classes "How to phrase the user-facing output" as judgment.) |
| Blocker / notice codes | 295–309 | ~16 lines | **Stays.** Documentation; no helper. |
| Config keys read | 313–324 | ~12 lines | **Stays** but adds a one-line note: "Authoritative source: `contracts/router_contract.json` `config_keys` section. This table mirrors it for documentation." |
| Cross-skill dependencies | 328–339 | ~12 lines | **Unchanged.** |
| What this skill does NOT do | 343–356 | ~14 lines | **Unchanged in substance.** Add one bullet: "It does not perform deterministic numerical comparisons in code — `compare_dm` is LLM-driven, calling `extract_field` as a primitive, because schema-pinned numerical comparison cannot be guaranteed model-agnostic for multi-component or asymmetric DM." |

**Total new SKILL.md ≈ 200 lines** (the four refactored steps shed ~140 lines combined; the additions are ~10).

### 4.2 What "decision-tree-with-primitives" looks like in markdown

Concrete example for Step 1 (replaces lines 41–58):

```markdown
### Step 1 — Prerequisite check

Run:

    python -m plugins.constraints.skills.dark_matter_constraints.scripts.check_prereqs \
        --config "$HEPPH_CONFIG_PATH" \
        --manifest "plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json" \
        --model "<model>"

Parse the JSON on stdout. If `status: ok`, proceed. If `status: blocked`,
emit one user-facing message per entry in `blockers[]`, citing
`blocker.code`, `blocker.message`, and `blocker.fixit_skill`.

The `SLHA_MISSING_HINT` blocker is informational only: an absent
`latest_slha` is fatal for MSSM-class models (where `/maddm` reads from
SLHA) but not for simplified-model UFOs that ship a `param_card.dat`.
You (the agent) decide based on the model class. If unsure, proceed and
let `/maddm` adjudicate at runtime.

Do not run any downstream skill until the helper returns `status: ok` or
the only remaining blocker is `SLHA_MISSING_HINT`.
```

**Why this shape works.** The mechanical part (file existence, config-key presence) is in the helper. The judgment (which blockers are fatal for which model classes) stays in the LLM, and the SKILL.md prose tells the LLM how to apply judgment. The helper is dumb and certain; the LLM is smart and contextual. Lens-aligned exactly.

### 4.3 What stays out of the rewrite

- **No router-level Python orchestrator.** Lens §"Non-goals" forbids it. The four helpers are leaf primitives; nothing chains them.
- **No new section.** The skill's existing structure (Invocation → Decision tree → Failure modes → Output format → Codes → Config → Deps → NOT) is good. Don't reshape; refactor in place.
- **No code in the markdown.** Bash invocation strings only. The helpers live in `scripts/`.

---

## 5. Producer SKILL.md edits W4-A through W4-E

Specific patches. WS-4's plan-drafter re-derives line numbers against the live worktree per the WS-1 plan §8 instruction; numbers below are from the live files at synthesis time.

### W4-A — `plugins/constraints/skills/micromegas/SKILL.md`, lines 99 and 226

**Edit 1 (line 99 — per-run output table).** Today:

```
| `summary.json` | Validated against `plugins/shared/schemas/scattering.schema.json` |
```

Replace with:

```
| `summary.json` | Direct-detection σ values (validated against `plugins/shared/schemas/scattering.schema.json`) |
| `relic.json` | Relic density Ωh² + Xf (validated against `plugins/shared/schemas/relic.schema.json`) |
| `annihilation.json` | ⟨σv⟩(v→0) + channel fractions (validated against `plugins/shared/schemas/annihilation.schema.json`) |
```

**Edit 2 (line 226 — `summary.json` schema example block).** Today shows only the `scattering/v1` example. Add two sibling example blocks immediately after, mirroring shape:

```json
// Example: <run_dir>/relic.json
{
  "schema_version": "relic/v1",
  "m_dm_gev": <float>,
  "omega_h2": <float or null>,
  "xf": <float or null>,
  "source": "micromegas",
  "source_run": "<run_identifier>",
  "cosmology": "standard_thermal"
}

// Example: <run_dir>/annihilation.json
{
  "schema_version": "annihilation/v1",
  "m_dm_gev": <float>,
  "sigma_v_zero": <float or null>,
  "channel_fractions": {"bb": 0.62, "ww": 0.18, ...},
  "source": "micromegas",
  "source_run": "<run_identifier>"
}
```

**Edit 3 (lines 207–223, "Reading micrOMEGAs output" prose).** Today says "extract from stdout via regex." Add a paragraph at the top:

> **Steady-state path:** the run writer emits `relic.json` and `annihilation.json` directly (post-W4-A). The router reads these via `extract_field` against the pinned schemas. The stdout-regex extraction below is the *legacy* path, retained for compatibility with hand-driven runs predating these schema files.

Closes WS-1 `pending_schema` xfails 5 and 8 once the new schema files (W4-B) ship and the writer emits the JSONs.

### W4-B — New schema files

See §6 below. Two files; they're scoped here because they unblock W4-A's docs claim.

### W4-C — `plugins/monte-carlo-tools/skills/maddm/SKILL.md`, line 164

Today:

```
- **Total annihilation cross-section**: line matching
  `sigmav_xf = <value>` (cm³/s); or the section header `<sigma v>`
```

Replace with:

```
- **Total annihilation cross-section**: line matching
  `sigmav_total = <value>` (cm³/s); or the section header `<sigma v>`.
  (Earlier MadDM 3.2 builds emitted `sigmav_xf`; if you see that name
  in legacy output, treat it as a synonym and re-emit `sigmav_total`
  in the JSON below.)
```

The JSON example at line 176 already uses `sigmav_total`, so the prose now agrees with the JSON. Closes WS-1 `pending_producer_doc_fix` xfail row 4.

### W4-D — `plugins/constraints/skills/dark-matter-constraints/SKILL.md`, ~line 213

Today (line 213):

```
If DRAKE runs, collect its Ωh² output. Compare to MadDM Ωh²: if the relative
difference exceeds 10%, flag `DRAKE_MADDM_DISAGREEMENT` (recoverable) with
both values.
```

Replace with:

```
If DRAKE runs, collect its Ωh² output (the field is named `omega_h2` in
DRAKE's emitted result dict — see `/drake` SKILL.md "Wolfram stdout"
section). Compare to MadDM `Omegah2` via `extract_field` + prose
arithmetic per Step 4b. If the relative difference exceeds 10%, flag
`DRAKE_MADDM_DISAGREEMENT` (recoverable) with both values.
```

This pins the field name explicitly and routes the comparison through the same `extract_field` primitive that Step 4b uses. (No xfail closed; clarity edit.)

### W4-E — `plugins/monte-carlo-tools/skills/drake/SKILL.md`, lines 84–86

Today:

```
Note: `activation_required` is emitted by the `use-path` subcommand (not `detect`) when
a smoke test fails only because Wolfram Engine needs activation. `detect` returns
`configured`, `found`, or `missing`.
```

Replace with:

```
The `detect` and `use-path` subcommands BOTH emit `activation_required` when
a smoke test fails only because Wolfram Engine needs activation. (Earlier
DRAKE builds emitted `activation_required` only from `use-path`; the router
in `/dark-matter-constraints` Step 5a Branch 2 reads it from `detect`.) The
canonical enum from either subcommand is therefore:
`configured`, `found`, `missing`, `activation_required`.
```

Plus a corresponding edit to `drake-install/scripts/install.sh detect` (out of WS-4 docs scope but in WS-4 implementation scope) so it actually emits the new literal. Closes WS-1 `pending_producer_topology_fix` (status_enums entry).

---

## 6. New schemas W4-B

Two files in `plugins/shared/schemas/`. Both follow `scattering.schema.json` conventions exactly: Draft 2020-12, `additionalProperties: false`, `$id` with `/v1` suffix, top-level `schema_version` is a `const`.

### 6.1 `plugins/shared/schemas/relic.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/relic/v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "m_dm_gev", "omega_h2", "source", "source_run", "cosmology"],
  "properties": {
    "schema_version": {"const": "relic/v1"},
    "m_dm_gev":       {"type": "number", "exclusiveMinimum": 0},
    "omega_h2":       {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}]},
    "xf":             {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}]},
    "source":         {"enum": ["micromegas", "maddm", "drake"]},
    "source_run":     {"type": "string", "minLength": 1},
    "cosmology":      {"const": "standard_thermal"},
    "model_class":    {"type": "string"},
    "model":          {"type": "string"}
  }
}
```

**Field rationale (model-agnostic):**
- `schema_version`, `m_dm_gev`, `omega_h2`, `source`, `source_run`, `cosmology` — required because every relic-density run produces them.
- `xf` — optional because DRAKE doesn't emit a freeze-out parameter (it solves the full Boltzmann eq).
- `omega_h2` `oneOf null` — handles `OMEGA_UNCONVERGED` (micromegas/SKILL.md line 222) and "not requested" cleanly without schema violation.
- `model_class`, `model` — optional, free-form strings. Lets producers self-identify (`"MSSM"`, `"DMsimp_s_spin1"`, `"darkSU3"`) without the schema enumerating known models. **This is the model-agnosticism guarantee** — the schema doesn't whitelist model classes, it just lets the producer record which one it ran.
- No `omega_h2_components` field for multi-component DM. v1 is single-component (matches micromegas/SKILL.md line 134's `MULTICOMPONENT_UNSUPPORTED` v1 stance). v1.1 adds it via a `relic/v2` schema.
- `cosmology` is `const "standard_thermal"` (matches micromegas/SKILL.md line 156). v1.1 with non-standard cosmologies bumps to v2.

### 6.2 `plugins/shared/schemas/annihilation.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/annihilation/v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "m_dm_gev", "sigma_v_zero", "source", "source_run"],
  "properties": {
    "schema_version":    {"const": "annihilation/v1"},
    "m_dm_gev":          {"type": "number", "exclusiveMinimum": 0},
    "sigma_v_zero":      {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}]},
    "channel_fractions": {
      "type": "object",
      "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "source":     {"enum": ["micromegas", "maddm"]},
    "source_run": {"type": "string", "minLength": 1},
    "model_class": {"type": "string"},
    "model":       {"type": "string"}
  }
}
```

**Decision: canonical name is `sigma_v_zero`. NOT `sv_total`.** WS-1 §4 already pinned it; we honor that. The MadDM-side name is `sigmav_total` (post-W4-C); micrOMEGAs emits `sigma_v_zero`. The annihilation.json file always uses `sigma_v_zero`. The producer SKILL.md prose (W4-A edit 3 above) tells producers to map their internal name to this canonical name when emitting `annihilation.json`. **Two names do NOT co-exist in the canonical schema.** They co-exist only as a router_contract.json mapping (manifest entries 7 and 8 in WS-1's table).

**Field rationale:**
- `channel_fractions` — `additionalProperties` with `number 0..1` per entry, NO required keys (channels are model-dependent: `bb`, `ww`, `zh`, …). **Model-agnostic.** Producer emits whatever channels are non-zero.
- No required sum-to-one constraint at schema level — JSON Schema can't easily express it, and in practice channel fractions sum to ≤1 (with "other" implicit).
- `source` enum excludes `drake` (DRAKE doesn't emit ⟨σv⟩(v→0) per its current scope; it returns Ωh² only).

### 6.3 What's NOT in the schemas (explicit out-of-scope)

- Asymmetric DM annihilation suppression. v1 assumes symmetric thermal relic; ADM models that emit `sigma_v_zero: 0.0` are schema-valid (`minimum: 0`) but the *meaning* is different. The schema can't enforce that distinction. SKILL.md prose flags it as a model-class skip rule for `compare_dm`.
- Multi-component component-resolved fields. v1.1.
- Sommerfeld-enhanced ⟨σv⟩ at finite v. v1.1. (DRAKE solves it, but not via this schema.)

---

## 7. Risks + scope

### 7.1 Implementation risks

1. **SKILL.md rewrite is high-judgment.** Cutting 155 lines while preserving every physics caveat AND threading helper invocations correctly is opus-implementer work, not sonnet. The prose around Step 4b (which rows to skip for which model class — multi-component, asymmetric, Majorana null σ_SD) is *physics judgment encoded as instructions*, not transcription. Recommend: opus-implementer for the SKILL.md task; opus-reviewer for the post-rewrite review.

2. **Helper CLI shape drift.** Each helper has a CLI surface that the SKILL.md prose hardcodes (the `python -m …scripts.check_prereqs --config … --manifest …` pattern). If the helper's argparse signature drifts, SKILL.md goes stale silently. Mitigation: WS-2 must include a "doc-vs-CLI" test that greps SKILL.md for each `python -m …scripts.<name>` line and runs the helper with `--help`, asserting every flag named in the prose appears in the help output.

3. **No new dependencies.** Repo today uses `jq` in shell gates and `jsonschema` in Python. WS-4 helpers MUST use only stdlib + `jsonschema`. **Forbidden:** PyYAML (config is loaded by the LLM and passed as JSON via `--config`), Click/Typer (use argparse — same as `formcalc/scripts/run_formcalc.py`), pydantic (jsonschema is the contract layer).

4. **Helper exit-code semantics need to be uniform.** Proposed convention: `0 = clean`, `1 = contract-or-input drift (recoverable; LLM emits a router blocker code)`, `2 = internal helper bug (fatal — bug report)`. SKILL.md prose tells the LLM to distinguish. WS-2 tests assert.

5. **`extract_field` needs the schema files to ship before `relic.json`/`annihilation.json` rows can pass.** Sequencing: W4-B (schema files) MUST land before W4-A (producer doc edits referencing them) before W4-F (helper authoring). If the WS-4 plan reverses any of these, tests xfail-cascade and the WS-1 pending_schema xfails don't clear.

6. **The `sigmav_total` doc fix (W4-C) must propagate to WS-1's MadDM synthetic fixture.** WS-1 plan T2 already pins the synthetic to `sigmav_total` (§9 row 3). After W4-C lands, the fixture and the producer doc both say `sigmav_total`; the WS-1 manifest entry 4's `audit_status` flips from `pending_producer_doc_fix` to `verified_against_synthetic`. WS-4 plan must include a "regenerate manifest audit_status" task for this row.

7. **DRAKE detect script change (W4-E implementation half) is real code, not docs.** `drake-install/scripts/install.sh` (a bash script) needs to start emitting `activation_required` when smoke test fails on activation. That's out of the docs-edit scope of W4-E but in the WS-4 implementation scope per WS-1 plan §8 row W4-E. Risk: the bash script might not have the install detect logic to even know if activation is the failure cause. WS-4 plan-drafter must scope this carefully and may need to defer the bash change to a follow-up if `install.sh detect` doesn't carry enough state to distinguish "activation needed" from "binary missing."

### 7.2 Cross-WS dependencies

- **WS-2 consumes WS-4 helpers.** The WS-2 brainstorm must be designed against the helper CLIs and exit-code conventions. WS-4's CLI surface is therefore load-bearing across WS-2 and WS-3. Recommend: WS-4 plan ships the CLI signatures as an explicit deliverable subsection so WS-2 has a stable contract.
- **WS-3 consumes WS-4's rewritten SKILL.md.** WS-3 will exercise the router on Dark SU(3); the rewritten SKILL.md's "decision-tree-with-primitives" shape must be runnable end-to-end from WS-3's perspective. If WS-3 trips on a helper missing or a CLI flag misnamed, WS-4 has shipped broken output. WS-4 plan should include a self-smoke step: invoke each helper with the WS-1 fixtures and confirm it produces sane output before declaring done.

### 7.3 Out-of-scope for WS-4 (explicit)

- WS-4 does NOT build `compare_dm` as a helper (§2 verdict).
- WS-4 does NOT extend `scattering.schema.json` (per WS-1 §4 — `scattering/v1` stays untouched).
- WS-4 does NOT promote MadDM output parsing to a helper (per WS-1 §6.4 — stays LLM until WS-3 produces evidence).
- WS-4 does NOT promote DRAKE Wolfram-stdout reading to a helper (synthesis §1.5 — stays LLM).
- WS-4 does NOT add neutron rows to the router's user-facing Step 4 cross-check table (W4-G is deferred per WS-1 §8 — low priority unless the playtest surfaces a concrete need).
- WS-4 does NOT wire helpers into a router-level orchestrator (lens "Non-goals" — no `dark-matter-constraints.py`).
- WS-4 does NOT generate a top-level `plugins/_helpers/` directory (§3 decision).

---

## 8. Decisions log

Concise list of every choice made above. WS-4's plan-drafter and critic must adjudicate these, not re-decide.

| # | Decision | Rationale anchor |
|---|---|---|
| D1 | Helper count: **4** (`check_prereqs`, `detect_drake`, `extract_field`, `verify_router_field_contract`). | §1; lens table; WS-1 §7. |
| D2 | `compare_dm` stays in **LLM** (SKILL.md prose). Not a helper. | §2 verdict; lens "cannot guarantee model-agnosticism" rule. |
| D3 | Minimal surviving primitive for `compare_dm` is `extract_field`, called once per field. | §2.3. |
| D4 | Multi-component DM and asymmetric DM are the killers for compare_dm-as-code; null-handling and threshold expert-overridability are secondary killers. | §2.2. |
| D5 | Helper layout: **`plugins/constraints/skills/dark-matter-constraints/scripts/`** (option A). | §3. |
| D6 | Helper interface: dual-mode (importable function + CLI). Exit codes: 0 clean / 1 drift / 2 internal. Stdlib + `jsonschema` only. | §3, §7.1.3, §7.1.4. |
| D7 | SKILL.md target length: **180–230 lines**, decision-tree-with-primitives shape. | §4. |
| D8 | Steps 1, 4b, 5a refactor to call helpers; Steps 2, 3, 4a, 5b stay full LLM prose; Tool failure modes / Merged output format / Blocker codes / Config / Cross-skill / NOT sections stay essentially unchanged. | §4.1. |
| D9 | Three new schema files (W4-B): `relic.schema.json`, `annihilation.schema.json`. NOT a `scattering/v2`. | §6; WS-1 §4. |
| D10 | Canonical annihilation field name is **`sigma_v_zero`** (NOT `sv_total`). MadDM internal `sigmav_total` maps to canonical at JSON-emit time. | §6.2. |
| D11 | Schemas use `oneOf [null, number]` for `omega_h2` and `sigma_v_zero` to handle `OMEGA_UNCONVERGED` and "not-requested" cases. | §6.1, §6.2. |
| D12 | Schemas include optional `model_class` / `model` strings; no enum of known models. Model-agnosticism via under-specification. | §6.1. |
| D13 | `channel_fractions` schema uses `additionalProperties: number 0..1` with NO required keys (channels are model-dependent). | §6.2. |
| D14 | W4-A edit shape: add `relic.json` and `annihilation.json` rows to micromegas line-99 table; add example blocks at line 226; add steady-state-vs-legacy paragraph at line 207. | §5 W4-A. |
| D15 | W4-C: replace `sigmav_xf` with `sigmav_total` in maddm/SKILL.md line 164, with a one-sentence backward-compat note. | §5 W4-C. |
| D16 | W4-D: name DRAKE Ωh² field explicitly as `omega_h2` and route the comparison through `extract_field` per Step 4b. | §5 W4-D. |
| D17 | W4-E: docs change names `activation_required` as a `detect` literal AND `use-path` literal; bash-script change to `drake-install/scripts/install.sh detect` is in WS-4 implementation scope but may be deferred if the script lacks state. | §5 W4-E, §7.1.7. |
| D18 | W4-G (neutron rows in router table) is **deferred**, not actioned in WS-4. | §7.3; WS-1 §8 row W4-G. |
| D19 | Helper owner classes: opus-implementer for the SKILL.md rewrite + the four helpers (judgment-heavy CLI design + null/exit-code semantics); opus-reviewer for post-WS-4 review (catches doc-vs-CLI drift, schema-vs-prose drift). | §7.1.1. |
| D20 | Sequencing within WS-4: W4-B (schemas) → W4-A (micrOMEGAs docs) → W4-C (MadDM doc fix) → W4-D (router DRAKE field name) → W4-E (DRAKE detect docs + bash) → W4-F (four helpers) → SKILL.md rewrite. The SKILL.md rewrite goes last because it cites the helper CLIs. | §7.1.5. |
| D21 | `compare_dm` v1.1 promotion path is left open (a `compare_dm_single_component` helper that exits with `MULTICOMPONENT_OUT_OF_SCOPE` if it detects multi-DM). NOT shipped in WS-4. | §2.4. |
| D22 | No new top-level dependencies. `python -m …scripts.<name>` invocation pattern via stdlib argparse + `jsonschema`. | §7.1.3. |
| D23 | No router-level orchestrator (no `dark-matter-constraints.py`). Lens "Non-goals." | §7.3. |
| D24 | Helpers' import path matches Python module path: `plugins.constraints.skills.dark_matter_constraints.scripts.<name>`. SKILL.md prose uses this exact form. | §3. |

---

## Closing routing-lens conformance check

Every helper proposed above passes the lens table:

| Helper | Lens classification | Justification |
|---|---|---|
| `check_prereqs` | "Truly mechanical AND model-agnostic" | File existence is invariant under model class. The one judgment call (`SLHA_MISSING_HINT` fatal-or-not) is surfaced as a hint code; LLM keeps the call. |
| `detect_drake` | "A contract between tools (status enums)" | DRAKE installation state has no model dependence. Pure tool-state machine. |
| `extract_field` | "A contract between tools (schemas)" | Schema is pinned with `additionalProperties: false`; field either exists with the typed value or is `null` per `oneOf`. No physics. |
| `verify_router_field_contract` | "A contract between tools" | String match + JSON pointer + `jsonschema.validate`. No physics. |

And `compare_dm` correctly does NOT pass the lens, per §2.2. WS-4 ships everything that does pass and stays out of code on everything that doesn't.

The proposal is consistent with WS-1 §7's helper boundary, WS-1 §4's schema-split decision, the WS-1 plan §8 W4-A through W4-G hand-off, and the routing lens's hard constraint on model-agnosticism. WS-4's plan-drafter mechanically translates §1, §3, §4, §5, §6 into tasks; the critic adjudicates §2 and §7 against the lens.
