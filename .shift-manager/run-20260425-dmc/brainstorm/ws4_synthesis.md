# WS-4 Synthesis — Refactor: helpers + SKILL.md rewrite (final design)

**Synthesizer:** WS-4 brainstorm synthesizer
**Inputs consumed end-to-end (in order):** `briefs/ROUTING_LENS.md`; `brainstorm/ws1_synthesis.md`; `plan/ws1_plan_final.md` (W4-A…W4-G in §7/§8); `brainstorm/ws4_propose.md` (509 lines); `brainstorm/ws4_critique.md` (188 lines); `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (full read at the live hash, 356 lines); `plugins/constraints/skills/micromegas/SKILL.md` (lines 85–245); `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (lines 140–187); `plugins/monte-carlo-tools/skills/drake/SKILL.md` (lines 70–95); `plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh` lines 105–142 (`cmd_detect` body); `plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py` (header + invocation convention).

**Verdict on critique:** ACCEPT. All eight items resolved below. Proposer's 4-helper inventory, schema split, layout choice (option A), `compare_dm`-as-prose verdict, and 180–230-line SKILL.md target survive. Critic's CLI-pattern fix (drop `python -m`, use direct path), null-vs-absent semantics for `extract_field`, manifest-path indirection, preserve-verbatim list expansion, W4-E in-scope (5-line bash fix), and the WS-1 ↔ WS-4 import-boundary pin all land. The synthesis is binding for the WS-4 plan-drafter — no "implementer reconciles" hedges remain.

---

## 1. Final helper inventory

Four helpers. All located at `plugins/constraints/skills/dark-matter-constraints/scripts/`. All invoked as **direct path** (matches formcalc convention: `python plugins/feynman-diagrams/skills/formcalc/scripts/run_formcalc.py …`). All dual-mode (importable function + CLI). Stdlib + `jsonschema` only. Exit-code grid is uniform: `0 = clean`, `1 = recoverable drift / contract failure (LLM emits a router blocker code)`, `2 = internal helper bug (fatal — bug report)`. JSON on stdout for success; JSON on stderr for errors.

**Why direct path, not `python -m`.** Critic verified the proposer's `python -m plugins.constraints.skills.dark_matter_constraints.scripts.<name>` is infeasible: (a) no `__init__.py` chain at `plugins/`, `plugins/constraints/`, `plugins/constraints/skills/`; (b) `dark-matter-constraints` contains a hyphen, which is not a valid Python module identifier. Renaming the skill dir would break the marketplace name; adding all the `__init__.py` files is scope creep. The formcalc convention (`python /abs/path/to/run_formcalc.py …`) is the precedent and works under the existing repo layout. SKILL.md prose uses absolute paths anchored at the documented `$REPO_ROOT` env var (or the literal absolute path when `$REPO_ROOT` is unset).

**Default `--manifest`.** Computed from helper location: `Path(__file__).resolve().parent.parent / "contracts" / "router_contract.json"`. SKILL.md examples DO NOT pass `--manifest` unless overriding for tests. Cuts the doc-vs-CLI drift surface.

### 1.1 `check_prereqs.py`

- **Path:** `plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py`
- **Usage:** `python <path>/scripts/check_prereqs.py --config <path> --model <name> [--manifest <path>]`
- **Inputs.** `--config` (path to the YAML/JSON config the LLM is operating from); `--model` (the BSM model the router was invoked with — interpolates into `models.<model>.ufo_path` etc.); `--manifest` (default per above). On stdin: nothing.
- **Outputs.** stdout: single-line JSON `{"status": "ok"|"blocked", "blockers": [{"code": <see below>, "message": "...", "fixit_skill": "/maddm-install"|"/micromegas-install"|"/drake-install"|null}], "checked": [{"key": "...", "exists": true|false, "path": "..."}]}`. stderr empty on success; on internal failure: `{"error": "...", "code": "PREREQ_HELPER_INTERNAL"}`.
- **Blocker codes emitted.** `MADDM_MISSING`, `MICROMEGAS_MISSING`, `DRAKE_PATH_UNSET`, `UFO_MISSING`, `SLHA_MISSING_HINT` (the last is informational; LLM decides per model class).
- **Exit codes.** `0` if `status == ok`; `1` if `status == blocked` (helper ran fine, contract failed); `2` on internal error (manifest unparseable, config unreadable).
- **Manifest dispatch.** Reads `config_keys` section. For each entry, dispatches on `type: path_or_bool` — checks the value is set AND (if a path) the file/dir exists.
- **Model-agnosticism.** **Yes.** File existence is invariant under model class. The single model-aware nuance (`latest_slha` is fatal for MSSM-class only) is surfaced as a HINT blocker (`SLHA_MISSING_HINT`) — the LLM keeps the judgment call about whether to honor it. The helper never inspects the model.
- **LoC estimate.** ~120 lines (argparse + manifest loader + per-key dispatch + JSON emit).

### 1.2 `detect_drake.py`

- **Path:** `plugins/constraints/skills/dark-matter-constraints/scripts/detect_drake.py`
- **Usage:** `python <path>/scripts/detect_drake.py --config <path> [--manifest <path>]`
- **Inputs.** `--config` (path); `--manifest` (default per above); env `HEPPH_DRAKE_DETECT_CMD` (test override; default invokes the install skill's `install.sh detect` directly via `subprocess.run`).
- **Outputs.** stdout: single-line JSON `{"branch": "branch1_unset"|"branch2_detect", "status": "configured"|"found"|"missing"|"activation_required"|"unparseable", "router_action": "proceed"|"emit_DRAKE_MISSING"|"emit_DRAKE_ACTIVATION_REQUIRED"|"emit_DRAKE_UNAVAILABLE", "raw_detect_output": "..."}`. stderr empty on success.
- **Exit codes.** `0` always (this is a state report, not a gate). The router LLM uses `router_action` to pick the blocker code.
- **Manifest dispatch.** Reads `status_enums[0].literals` and asserts the live `status` is in that set. Drift (e.g. detect emits a new literal) ⇒ `status: "unparseable"` + `raw_detect_output` populated; `router_action: "emit_DRAKE_UNAVAILABLE"`.
- **Model-agnosticism.** **Yes.** DRAKE installation state has zero model-class dependence. Cleanest helper of the four.
- **LoC estimate.** ~90 lines.

### 1.3 `extract_field.py`

- **Path:** `plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py`
- **Usage:** `python <path>/scripts/extract_field.py --json <path> --key <name> --schema-version <id> [--schema-root <dir>]`
- **Inputs.** `--json` (path to a pinned-schema JSON file); `--key` (top-level key name); `--schema-version` (e.g. `relic/v1`, `annihilation/v1`, `scattering/v1`); `--schema-root` (default: `plugins/shared/schemas/` resolved from helper location).
- **Outputs.** On clean extract: stdout `{"value": <number|null>, "key": "<name>", "schema_version": "<id>", "source_file": "<abs-path>"}`. On error: stderr `{"error": "...", "code": "<see grid>"}`.
- **Exit-code grid (LOCKED — critic item 3).**

| Condition | Exit | Code |
|---|---|---|
| `--key` present in JSON, value matches a schema branch (number) | `0` | — |
| `--key` present in JSON, value is `null` AND schema permits `oneOf [null, …]` | `0` | — (stdout `value: null`) |
| `--key` absent from JSON entirely | `1` | `KEY_ABSENT` |
| JSON parses but `schema_version` field doesn't match `--schema-version` | `1` | `VERSION_DRIFT` |
| Schema file's `$id` does not end with `/<schema-version>` (asserted before validation) | `1` | `VERSION_DRIFT` |
| JSON validates but value type doesn't match schema's branch | `1` | `SCHEMA_MISMATCH` |
| File unreadable / unparseable / schema file missing | `2` | `EXTRACT_FIELD_INTERNAL` |

  Critic item 3 explicit pin: present-null and absent are semantically distinct. `oneOf [null, number]` schemas make "present-null" a valid result; the helper MUST distinguish.

- **Schema-version self-check.** Helper loads the schema file and asserts `schema["$id"].endswith("/" + schema_version)` BEFORE running `jsonschema.Draft202012Validator(schema).validate(json_data)`. Prevents shadow-loading of a future v2 schema file.
- **Mode.** Top-level keys only. `channel_fractions.bb`-style nested access is OUT OF SCOPE for v1 — the LLM extracts `channel_fractions` as a dict and parses in prose. A future `--json-pointer` flag can be added without breaking the v1 contract.
- **Model-agnosticism.** **Yes.** Schema is pinned with `additionalProperties: false`; the field either exists with a typed value, exists as null, or is absent. No physics, no model-class branch.
- **LoC estimate.** ~110 lines.

### 1.4 `verify_router_field_contract.py`

- **Path:** `plugins/constraints/skills/dark-matter-constraints/scripts/verify_router_field_contract.py`
- **Usage:** `python <path>/scripts/verify_router_field_contract.py [--manifest <path>] [--fixtures-root <path>]`
- **Inputs.** `--manifest` (env-overridable via `ROUTER_CONTRACT_PATH` per WS-1 plan T3 acceptance gate #3; default per above); `--fixtures-root` (default: helper-location-relative `tests/fixtures`).
- **Outputs.** stdout: pytest-style line-per-row summary, one line per `output_fields` entry: `OK <observable>:<downstream>`, `XFAIL <observable>:<downstream>:<reason>`, or `FAIL <observable>:<downstream>:<DRIFT_CODE>:<detail>`. Final summary line: `SUMMARY <ok>/<xfail>/<fail>`.
- **Exit codes.** `0` if all rows pass-or-xfail. `1` if any row fails with a `DRIFT_*` code. `2` on internal error (manifest unparseable, schema file missing).
- **Drift codes emitted.** `DRIFT_PRODUCER_DOC_GAP`, `DRIFT_PRODUCER_RENAMED`, `DRIFT_ROUTER_INVENTED_NAME`, `DRIFT_DOCUMENTED_BUT_ABSENT`, `DRIFT_PRESENT_BUT_UNDOCUMENTED`, `DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY` (per WS-1 synthesis §3 ladder).
- **Importable surface.** Module exports `def verify_router_field_contract(manifest_path: Path, fixtures_root: Path) -> VerifyResult:` where `VerifyResult` is a dataclass with `.ok`, `.xfail`, `.fail` lists. `tests/test_router_contract.py` (authored by WS-1 inline; rewritten by WS-4 — see §7) imports this function.
- **Model-agnosticism.** **Yes.** Pure string match + JSON pointer + `jsonschema.validate`. No physics.
- **LoC estimate.** ~200 lines (4 dispatch branches × ~40 lines each + aggregation).

### 1.5 What deliberately did NOT make the helper list

- **`compare_dm`** — stays as SKILL.md prose, calls `extract_field` as its only primitive. See §2 (lens forces this; critic accepted; synthesizer pins).
- **`read_maddm_output`**, **`read_drake_output`** — LLM territory per WS-1 §6.4. Promotion path opens if WS-3 produces real-format evidence.
- **`read_micromegas_output`** (stdout regex extraction for `omega_h2`/`sigma_v_zero`) — replaced in steady state by `extract_field` against `relic.json`/`annihilation.json` (post-W4-A/B). Legacy stdout-regex path documented in `/micromegas` SKILL.md prose for hand-driven runs predating these schema files.
- **`render_merged_output`** — Markdown template is a guide, not a contract. Stays in SKILL.md prose.
- **Rel-diff arithmetic helper** — heuristic threshold (10%) is expert-overridable per the lens; LLM does the arithmetic in prose.

---

## 2. `compare_dm` LLM-only contract

`compare_dm` is the highest-stakes call in WS-4. The lens forces LLM-only; the critic accepted; the synthesizer **pins the boundary** so v1.1 doesn't regress.

**Constraint (LOCKED — critic item 8):** `compare_dm` prose calls **ONLY** `extract_field` as a deterministic primitive. NO regex helper. NO rel-diff helper. NO flag-renderer helper. The LLM owns:
- Value acquisition for non-JSON producers (MadDM stdout per WS-1 §6.4 — agent-parsed prose extraction until W4-C lands and a future MadDM JSON+schema appears).
- Rel-diff arithmetic in prose.
- Threshold judgment (10% default, expert-overridable).
- Model-class skip rules (multi-component DM, asymmetric DM, Majorana null σ_SD).

Why so strict: a competent collaborator who explains *why* a row is being skipped for an ADM model is more valuable than a deterministic helper that prints a flag without context. The LLM rendering the rationale prose IS the UX win.

### 2.1 Verbatim prose snippet for SKILL.md (~10 lines)

This goes into the rewritten SKILL.md Step 4b (replacing lines 134–150 of the current file):

```markdown
### Step 4b — Disagreement comparison (LLM-driven, calls `extract_field`)

For each row in the cross-check table below, acquire both values then compute
the relative difference in prose:

1. **MadDM side.** Read `<maddm_run>/MadDM_results.txt` and extract the field
   per `/maddm` SKILL.md "Reading MadDM output." (No helper — agent-parses
   prose until MadDM ships a pinned JSON schema.)
2. **micrOMEGAs side.** Run:
       python "$REPO_ROOT/plugins/constraints/skills/dark-matter-constraints/scripts/extract_field.py" \
           --json "<mo_run>/<file>" --key "<canonical_name>" --schema-version "<id>"
   Use `relic.json` + `relic/v1` for Ωh², `annihilation.json` + `annihilation/v1`
   for ⟨σv⟩(v→0), `summary.json` + `scattering/v1` for σ_SI/σ_SD. If
   `extract_field` exits 1 with `KEY_ABSENT`, treat as null and render `—`.
3. **Compute.** `rel_diff = abs(a - b) / max(abs(a), abs(b))` if both non-null.
   Flag at `> 0.10` by default. Expert may override the threshold.
4. **Skip rules.** Skip the row when the model class makes the comparison
   meaningless: multi-component DM (sum vs per-component pairing is undefined),
   asymmetric DM (⟨σv⟩ ≈ 0 by design — flag would be cosmetic), Majorana DM
   with σ_SD-only schemas (null vs 0 distinction is a producer rule). Render
   `—` and explain the skip in one sentence.
5. **Do NOT** silently average, pick a winner, or paper over a flag. If you
   cannot adjudicate, surface both values and the disagreement to the user.
```

This snippet is the bridge between helper-land and prose-land. It tells the LLM exactly which primitive to call (`extract_field`) and exactly which judgment is the LLM's own (skip rules, threshold, render-vs-flag).

### 2.2 v1.1 promotion path (left open, NOT shipped in WS-4)

A future narrow `compare_dm_single_component` helper that exits with `MULTICOMPONENT_OUT_OF_SCOPE` if it detects more than one DM candidate is acceptable. WS-4 does NOT ship it.

---

## 3. SKILL.md rewrite plan

**Length target: 200 lines** (down from 356). Shape: **decision-tree-with-primitives**, NOT a full rewrite. The four helper invocations replace prose; the physics-tutorial-rich and judgment-heavy sections stay verbatim.

### 3.1 Diff sketch

| Section | Current lines | New lines | Disposition |
|---|---|---|---|
| YAML frontmatter | 1–4 | 1–4 | **Unchanged.** |
| Invocation | 20–35 | 20–35 | **Unchanged.** |
| Decision-tree intro | 37–39 | 37–39 | **Unchanged.** |
| Step 1 — Prereq check | 41–58 (18 lines) | ~12 lines | **REPLACE** with `check_prereqs` invocation + SLHA-hint prose (see proposer §4.2 example, verbatim). |
| Step 2 — MadDM (always) | 60–77 (18 lines) | ~18 lines | **PRESERVE-VERBATIM** lines 60–66 (router justification — critic item 7); subcommand mapping table unchanged. |
| Step 3 — Spectrum analysis | 79–100 (22 lines) | 22 lines | **PRESERVE-VERBATIM** (critic item 7 — physics-tutorial-rich, expert-overridable). |
| Step 4a — micrOMEGAs invocation | 102–132 (31 lines) | ~28 lines | **Lightly trimmed** — subcommand mapping stays; rationale stays. |
| Step 4b — disagreement | 134–150 (17 lines) | ~18 lines | **REFACTOR** to call `extract_field` per the §2.1 snippet. Field-name pair table preserved. |
| Step 5a — DRAKE availability (4-branch) | 186–211 (26 lines) | ~14 lines | **REPLACE** with `detect_drake` invocation. Resonance-warning prose (191–211) preserved. |
| Step 5b — narrow-resonance (5%) | (interleaved 152–185) | ~10 lines | **Unchanged** — heuristic per lens. |
| Tool failure modes | 219–254 (36 lines) | 36 lines | **PRESERVE-VERBATIM.** Largest physics-tutorial section; the entire reason the router exists. |
| Merged output format | 258–291 (34 lines) | 34 lines | **PRESERVE-VERBATIM.** |
| Blocker / notice codes | 295–309 (15 lines) | 15 lines | **PRESERVE-VERBATIM.** |
| Config keys read | 313–324 (12 lines) | ~14 lines | **Keep table** (human readers want it) + add header: `> **MIRROR — see `contracts/router_contract.json` `config_keys` for canonical contract.**` |
| Cross-skill dependencies | 328–339 (12 lines) | 12 lines | **Unchanged.** |
| What this skill does NOT do | 343–356 (14 lines) | ~16 lines | **PRESERVE-VERBATIM** (critic item 7) + add one bullet on `compare_dm`-as-prose rationale. |

**New SKILL.md ≈ 200 lines.** The four refactored steps shed ~50 lines net; the §2.1 snippet adds ~10; preserve-verbatim sections are 0-net.

### 3.2 Preserve-verbatim list (LOCKED — critic item 7, EXPANDED)

Three blocks beyond the proposer's "Tool failure modes / Merged output format / Blocker codes / Cross-skill / NOT" baseline:

1. **Lines 60–66** — Step 2 MG5/UFO vs CalcHEP rationale. The router's justification.
2. **Lines 79–100** — Step 3 spectrum analysis with the 10%/5% rationale. Heuristic-with-default per lens.
3. **Lines 343–356** — What this skill does NOT do. Sets user expectations.

Plus the proposer's baseline: lines 219–254 (Tool failure modes), 258–291 (Merged output format), 295–309 (Blocker codes), 328–339 (Cross-skill), 343–356 (NOT — overlaps with #3 above).

### 3.3 What stays out of the rewrite

- No router-level Python orchestrator (lens "Non-goals" forbids).
- No new section. Existing structure is good; refactor in place.
- No code in the markdown — bash invocation strings only.

---

## 4. Producer SKILL.md edits W4-A..W4-E

All line numbers verified by the critic against the live worktree (§3 of the critique). Plan-drafter re-verifies at WS-4 task start.

### W4-A — `plugins/constraints/skills/micromegas/SKILL.md`

- **Edit 1 (line 99 — per-run output table).** Add `relic.json` and `annihilation.json` rows. (Proposer §5 W4-A Edit 1, verbatim.)
- **Edit 2 (line 226 — schema example block).** Add two sibling `relic.json` and `annihilation.json` example blocks. (Proposer §5 W4-A Edit 2, verbatim.)
- **Edit 3 (line 207 — "Reading micrOMEGAs output" prose).** Add a steady-state-vs-legacy paragraph. (Proposer §5 W4-A Edit 3, verbatim.)

Closes WS-1 `pending_schema` xfails 5 and 8 once W4-B ships and the writer emits the JSONs.

### W4-B — New schema files

See §5 below.

### W4-C — `plugins/monte-carlo-tools/skills/maddm/SKILL.md` line 164

Replace `sigmav_xf = <value>` with `sigmav_total = <value>` plus a one-sentence backward-compat note. (Proposer §5 W4-C, verbatim.) Closes WS-1 `pending_producer_doc_fix` row 4.

### W4-D — `plugins/constraints/skills/dark-matter-constraints/SKILL.md` ~line 213

Name DRAKE Ωh² field explicitly as `omega_h2` and route the comparison through `extract_field` per Step 4b. (Proposer §5 W4-D, verbatim.) Clarity edit, no xfail closed.

### W4-E — IN-SCOPE (LOCKED — critic item 4)

Critic verified: `cmd_detect` in `drake-install/scripts/install.sh` already calls `run_smoke` (line 121) which ALREADY emits `activation_required`. The current code falls through to `found` when smoke status is non-`ok` (lines 128–131). The fix is **5 lines of bash** between lines 128 and 130:

```bash
      # Smoke test did not pass — distinguish activation vs other failure
      if [ "$status" = "activation_required" ]; then
        printf '{"status":"activation_required","path":"%s"}\n' "$path"
        return 0
      fi
      # Other smoke failures fall through to "found".
```

Plus the docs edit at `drake/SKILL.md` lines 84–86 (proposer §5 W4-E, verbatim). Plus a new test fixture / unit test asserting `cmd_detect` emits `activation_required` when the smoke output says so. Closes WS-1 `pending_producer_topology_fix`. **All in WS-4 scope; not deferred.**

---

## 5. New schemas W4-B

Two files in `plugins/shared/schemas/`. Both Draft 2020-12, `additionalProperties: false`, `$id` with `/v1` suffix, top-level `schema_version` is a `const`.

### 5.1 `relic.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/relic/v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "m_dm_gev", "omega_h2", "source", "source_run", "cosmology"],
  "properties": {
    "schema_version": {"const": "relic/v1"},
    "m_dm_gev":       {"type": "number", "exclusiveMinimum": 0,
                       "description": "Dark-matter candidate mass in GeV."},
    "omega_h2":       {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}],
                       "description": "Relic density Ωh². Null when OMEGA_UNCONVERGED or not requested."},
    "xf":             {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}],
                       "description": "Freeze-out parameter (m_DM/T_f). Null for solvers (e.g. DRAKE) that don't use it."},
    "source":         {"enum": ["micromegas", "maddm", "drake"]},
    "source_run":     {"type": "string", "minLength": 1},
    "cosmology":      {"const": "standard_thermal",
                       "description": "v1 assumes standard thermal cosmology. Non-standard cosmologies require relic/v2."},
    "model_class":    {"type": "string", "description": "Producer self-identification (e.g. 'MSSM', 'darkSU3'). Free-form; not validated against a whitelist."},
    "model":          {"type": "string"}
  }
}
```

### 5.2 `annihilation.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/annihilation/v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "m_dm_gev", "sigma_v_zero", "source", "source_run"],
  "properties": {
    "schema_version":    {"const": "annihilation/v1"},
    "m_dm_gev":          {"type": "number", "exclusiveMinimum": 0,
                          "description": "Dark-matter candidate mass in GeV."},
    "sigma_v_zero":      {"oneOf": [{"type": "null"}, {"type": "number", "minimum": 0}],
                          "description": "Annihilation cross-section ⟨σv⟩ at v→0 (cm³/s). The v→0 limit is the indirect-detection observable. Producers emitting at v=v_freezeout (e.g. MadDM's `sigmav_total`) MUST convert to v→0 before writing this field, OR set it to null and document the v in `notes`. micrOMEGAs emits at v→0 natively (see micromegas/SKILL.md line 217). The schema does not enforce v=0; this is producer discipline."},
    "channel_fractions": {
      "type": "object",
      "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
      "description": "Per-channel branching fractions of total ⟨σv⟩(v→0). Channel keys (e.g. 'bb','ww','zh') are model-dependent — no required keys. Sum-to-one is producer discipline (JSON Schema cannot easily enforce)."
    },
    "source":      {"enum": ["micromegas", "maddm"],
                    "description": "DRAKE excluded — DRAKE returns Ωh² only in v1."},
    "source_run":  {"type": "string", "minLength": 1},
    "model_class": {"type": "string"},
    "model":       {"type": "string"}
  }
}
```

The `sigma_v_zero` description (LOCKED — critic item 6) is the load-bearing assertion. micrOMEGAs emits at v→0; MadDM emits at v=v_freezeout. The schema does not enforce v=0 (JSON Schema can't), but the description string makes the convention explicit and tells producers what they MUST do at JSON-emit time.

### 5.3 What's NOT in the schemas (out-of-scope)

- Asymmetric-DM annihilation suppression — v1 assumes symmetric thermal relic.
- Multi-component component-resolved fields — v1.1.
- Sommerfeld-enhanced ⟨σv⟩(v) at finite v — v1.1.
- An enum of known model classes — model-agnosticism by under-specification (lens hard constraint).

---

## 6. 8-item adjudication table

| # | Critic item | Decision | Rationale |
|---|---|---|---|
| 1 | Helper invocation: `python -m` vs direct path | **Direct path** — `python "$REPO_ROOT/plugins/constraints/skills/dark-matter-constraints/scripts/<name>.py" …` | Critic verified `python -m` is infeasible: no `__init__.py` chain, hyphen in skill name. Formcalc convention is the precedent and works under existing repo layout. Renaming the skill dir or adding `__init__.py`s is unjustified scope. |
| 2 | Helper default `--manifest` | **`Path(__file__).resolve().parent.parent / "contracts" / "router_contract.json"`** (relative to helper) | Hardcoded absolute breaks on dir rename. SKILL.md examples DO NOT pass `--manifest` unless overriding for tests. |
| 3 | `extract_field` exit-code grid | **Locked per §1.3 grid:** present-null exit 0; absent exit 1 + `KEY_ABSENT`; schema `$id` mismatch exit 1 + `VERSION_DRIFT`; helper asserts `schema["$id"].endswith("/" + schema_version)` BEFORE validating | Critic identified the present-null vs absent conflation. `oneOf [null, number]` makes both legitimate and they MUST be distinguishable. Schema `$id` self-check prevents shadow-loading a future v2 file. |
| 4 | W4-E in WS-4 scope | **In-scope.** 5-line bash fix in `cmd_detect` between current lines 128 and 130 plus docs edit plus unit test. | Critic verified `run_smoke` already emits `activation_required` (line 121); `cmd_detect` falls through to `found` (line 130 comment). Fix is shallow, not deep. Proposer overstated risk. |
| 5 | `verify_router_field_contract` ownership / WS-1 T3 boundary | **WS-4 owns BOTH (a) authoring the helper AND (b) rewriting `tests/test_router_contract.py` to import it.** WS-1 ships T3 with inline dispatch; WS-4 extracts. Test must keep all 18 cases passing AND negative-control gate green. | Per critic item, WS-1 cannot ship the helper without scope creep; WS-4 cannot leave WS-1's inline test as-is without leaving dispatch logic in two places. Cleanest seam: WS-1 inline → WS-4 refactor-and-import. |
| 6 | `sigma_v_zero` v→0 description | **Confirmed.** Schema property carries the verbatim description string in §5.2 asserting v→0 convention; producers emitting at v=v_freezeout MUST convert or null. | micrOMEGAs and MadDM emit at different v's. Schema can't enforce v=0; description string + producer-side discipline is the right contract. |
| 7 | Preserve-verbatim list expansion | **Locked per §3.2:** lines 60–66, 79–100, 343–356 added to baseline (Tool failure modes / Merged output format / Blocker codes / Cross-skill). | Critic identified these three: 60–66 is the router's justification, 79–100 is the heuristic-rationale section (lens-LLM territory), 343–356 sets user expectations. All would amputate UX if cut. |
| 8 | `compare_dm` prose calls ONLY `extract_field` | **Confirmed and pinned.** No regex helper, no rel-diff helper, no flag-renderer helper. LLM owns value-acquisition for non-JSON producers, rel-diff arithmetic, threshold judgment, model-class skip rules. | Lens-aligned UX boundary. Prevents v1.1 regression where helper sprawl absorbs prose. Locks the §2.1 snippet as the canonical Step 4b prose. |

---

## 7. Coordination with WS-1, WS-2, WS-3

Each downstream WS imports/consumes WS-4 deliverables across exact module/file boundaries.

### 7.1 WS-1 import boundary

WS-1 ships `tests/test_router_contract.py` (T3) with **inline** dispatch logic — all 18 cases enumerated in WS-1 plan §5 are implemented as direct `def test_*` functions, not as imports from a helper. This is what WS-1 actually delivers; the WS-1 plan T3 acceptance gates verify it.

**WS-4 retrofit:** at WS-4 helper-authoring time, WS-4 rewrites `tests/test_router_contract.py` to import from `plugins.constraints.skills.dark_matter_constraints.scripts.verify_router_field_contract` (loaded via `importlib.util.spec_from_file_location` because the package path is hyphen-broken — same shape as the direct-path CLI invocation). Specifically: each `test_*` function becomes a thin wrapper that calls `verify_router_field_contract(manifest_path, fixtures_root)` and asserts on the returned `VerifyResult`'s ok/xfail/fail lists. The 18 case count, the negative-control gate, the `ROUTER_CONTRACT_PATH` env override, and the `pending_*` xfail policy ALL survive — the rewrite is structural, not behavioral.

**This is a coordinated retrofit.** WS-1 cannot avoid it (would require shipping the helper, scope creep). WS-4 cannot skip it (would leave dispatch logic in two places). WS-4's plan-drafter MUST scope the test rewrite as part of the `verify_router_field_contract` task, NOT a separate task.

### 7.2 WS-2 import boundary

WS-2 (router test harness) imports each helper as a Python function from its module file via `importlib.util.spec_from_file_location` (same loader pattern as the test rewrite above). WS-2 authors:

- `tests/test_check_prereqs.py` — fixture-drives the function with synthetic configs + manifests, asserts JSON output, asserts exit codes.
- `tests/test_detect_drake.py` — same shape; mocks `HEPPH_DRAKE_DETECT_CMD` to inject canned `install.sh detect` JSON outputs.
- `tests/test_extract_field.py` — fixture-drives against the symlinked `summary_singletDM.json` plus new synthetic `relic.json` + `annihilation.json` fixtures; asserts the §1.3 exit-code grid row-by-row.
- A **doc-vs-CLI test** that greps SKILL.md for each `python …/scripts/<name>.py` line and runs the helper with `--help`, asserting every flag named in prose appears in `--help` output. This is the lock against the §7.1.2-of-proposer drift surface.

WS-2 does NOT test `compare_dm` (it's prose). WS-2 does NOT test `read_maddm_output` / `read_drake_output` (they're prose). WS-2 covers exactly the four helpers, the doc-vs-CLI invariant, and the WS-1-authored `test_router_contract.py` (which now imports WS-4's helper).

### 7.3 WS-3 import boundary

WS-3 (Dark SU(3) end-to-end playtest) does NOT import WS-4 helpers as Python — WS-3 invokes them via the SKILL.md `python …/scripts/<name>.py` invocation strings exactly as the LLM would in real use. WS-3 is the integration test for the SKILL.md prose itself: if the rewritten SKILL.md is ambiguous, WS-3 surfaces it.

WS-3 also catches what WS-1 deferred: real-format MadDM output drift (per WS-1 §6.4). WS-3's playtest report includes a "MadDM contract verification" subsection asserting fixture-vs-reality parity for the WS-1 manifest entries 1–4. If parity holds, the WS-1 manifest's `audit_status: verified_against_synthetic` rows can be promoted to `verified_against_real` in a follow-up.

### 7.4 What WS-4 cannot do without coordinated WS-1 retrofit

The single load-bearing coordination: **WS-4 owns the rewrite of WS-1's `tests/test_router_contract.py`.** This is in WS-4 scope, not WS-1 scope. WS-1 ships the inline test (already pinned in WS-1 plan T3); WS-4 extracts the dispatch into `verify_router_field_contract.py` and rewrites the test to import it. The two repos-of-truth merge into one.

---

## 8. Out-of-scope for WS-4 (explicit)

Things WS-4 deliberately does NOT do.

- **Does NOT build `compare_dm` as a helper** (§2 verdict; lens-forced).
- **Does NOT extend `scattering.schema.json`** — `scattering/v1` stays untouched per WS-1 §4.
- **Does NOT promote MadDM output parsing to a helper** — stays LLM until WS-3 produces real-format evidence (WS-1 §6.4).
- **Does NOT promote DRAKE Wolfram-stdout reading to a helper** — DRAKE emits unstructured Wolfram stdout; no contract to enforce.
- **Does NOT add neutron rows to the router's user-facing Step 4 cross-check table** (W4-G deferred per WS-1 §8).
- **Does NOT wire helpers into a router-level orchestrator** — lens "Non-goals" forbids `dark-matter-constraints.py`.
- **Does NOT generate a top-level `plugins/_helpers/` directory** — convention is per-skill scripts (§3 of proposer, ratified).
- **Does NOT add `--json-pointer` or `--regex` modes to `extract_field`** — single mode (top-level JSON key) for v1; future flags can be added without breaking the v1 contract.
- **Does NOT ship `compare_dm_single_component` v1.1 helper** — promotion path open, not WS-4 work.
- **Does NOT modify `drake-install`'s overall invocation contract** — only the `cmd_detect` 5-line branch (§W4-E) is in scope; the rest of the install skill is untouched.
- **Does NOT rewrite WS-1's manifest** — WS-4 consumes it via `verify_router_field_contract`. The only WS-1 retrofit is the test file (§7.1).

---

## Closing routing-lens conformance check

Every code-bound decision in this synthesis answers the lens question "can we guarantee model-agnosticism?" with yes:

- **`check_prereqs`** — file existence, invariant under model class. The one model-aware nuance (`SLHA_MISSING_HINT`) is surfaced as a hint code; LLM keeps the call.
- **`detect_drake`** — DRAKE installation state has zero model-class dependence.
- **`extract_field`** — schema is pinned with `additionalProperties: false`; the field exists with a typed value, exists as null, or is absent. No physics.
- **`verify_router_field_contract`** — string match + JSON pointer + jsonschema. No physics.

And `compare_dm` correctly does NOT pass the lens. WS-4 ships every helper that does pass and stays out of code on everything that doesn't. The §2.1 prose snippet is the load-bearing collaborative-LLM bridge between the helpers and the LLM's judgment surface.

The proposal is consistent with WS-1 §7's helper boundary, WS-1 §4's schema-split decision, the WS-1 plan §8 W4-A through W4-G hand-off, the routing lens's hard constraint on model-agnosticism, and the critic's 8 items. WS-4's plan-drafter mechanically translates §1, §3, §4, §5, §6, §7 into tasks; the binding adjudications are §6 row 1 (CLI invocation), §6 row 5 (test-file ownership), and §6 row 8 (`compare_dm` prose-only constraint).
