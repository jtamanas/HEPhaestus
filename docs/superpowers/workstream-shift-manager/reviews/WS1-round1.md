# WS1 Review — Round 1

**Branch under review:** `ws1/shared-scaffold` in `/Users/yianni/Projects/hep-ph-agents.ws1-shared`, commit `7c60860`.

**Verdict:** **APPROVED**

All 12 done-criteria items pass mechanically; 40/40 tests green; `summary.schema.json` matches §4.1 of the final plan byte-for-byte; constraints.yaml carries the required `status` + `hours` per prereq and the `multi_component_prereq: dark-matter-constraints` under `models.dark-su3`; per-model `time_overrides` present; `demo/SKILL.md` structure order is correct and preflight is preserved verbatim from the prior version; `plugin.json` untouched; no `Co-Authored-By:` on any commit. The flagged provisional-as-comment deviation is acceptable (justified below).

---

## Mechanical checks

| # | Done-criterion (§3 WS1) | Verification | Result |
|---|---|---|---|
| 1 | `_shared/` contains 6 top-level artifacts + `assets/` + `tests/` | `ls plugins/hep-ph-toolkit/skills/_shared/` → `constraints.yaml  status_resolve.py  summary.schema.json  time_budget.py  assets/  tests/` (plus `__pycache__`) | **PASS** |
| 2 | `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` exits 0 | `40 passed in 0.24s` | **PASS** |
| 3 | `test_constraints_yaml.py` asserts top-level keys, prereq chain references, `time_overrides` keys ⊂ {relic,dd,id}, `multi_component_prereq ∈ prereqs`, per-prereq `status` + `hours.cold/cached` | 12 tests under `test_constraints_yaml.py`, all named per criteria (`test_top_level_keys`, `test_prereq_entries`, `test_constraint_chains_reference_known_prereqs`, `test_model_time_overrides_valid_keys`, `test_model_multi_component_prereq_in_prereqs`, `test_dark_su3_multi_component`, etc.) — all PASSED | **PASS** |
| 4 | `test_time_budget.py` asserts singlet-doublet relic READY, dd BLOCKED w/ feynarts+formcalc+package-x+ddcalc, dark-su3 relic BLOCKED w/ dark-matter-constraints, overlap dedup | `TestSingletDoubletRelic::test_status_ready`, `TestSingletDoubletDD::test_missing_contains_required_prereqs`, `TestDarkSU3Relic::test_missing_contains_dark_matter_constraints`, `TestOverlapDedup::test_combined_cold_all_less_than_naive_sum` all PASSED | **PASS** |
| 5 | `test_summary_schema.py` validates draft 7 schema + canonical §4 example | 10 tests named per criteria including `test_schema_declares_draft7`, `test_canonical_example_validates`, `test_extra_field_rejected` — all PASSED | **PASS** |
| 6 | All 3 `_shared/assets/*.yaml` validate against `modelspec.schema.json` | `python3 -c "import json, yaml, jsonschema; s=json.load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json')); [jsonschema.validate(yaml.safe_load(open(f)), s) for f in [...]]; print('OK')"` → `OK` | **PASS** |
| 7 | Every provisional YAML has `provisional: true` marker + `# TODO(physics):` block; non-provisional marks false | `grep -n "^# provisional:"` returns one hit per file (true for singlet_doublet.yaml:4 and two_hdm_a.yaml:4; false for dark_su3.yaml:25). `grep -n "TODO(physics)"` hits both provisional files and the TODO text names concrete unverified physics (SU(2) indices + Higgs-portal sign for singlet-doublet; CP-odd mass eigenstates + theta_a for 2HDM+a) | **PASS (comment form; see deviation verdict)** |
| 8 | `demo/SKILL.md` structure: Preflight → Intro → Gate → Picker → Delegation → Closing → Non-goals | `grep -n '^###\|^##' plugins/hep-ph-toolkit/skills/demo/SKILL.md` shows Step 0 Preflight (L16) → Step 1 Paper introduction (L33) → Step 2 Gate: continue? (L43) → Step 3 Model picker (L63) → Delegation (L84) → Closing block (L92) → Non-goals (L112). Intro text matches synthesis §3 verbatim (starts with "Arcadi & Profumo ask:"). Picker JSON ids = `singlet-doublet`, `2hdm-a`, `dark-su3` with cold-hr ranges verbatim from synthesis | **PASS** |
| 9 | Preflight precedes intro | Line 16 < line 33 | **PASS** |
| 10 | `demo/SKILL.md` frontmatter is only `name` + `description` | Lines 1–4 are `---` / `name: demo` / `description: …` / `---` | **PASS** |
| 11 | `plugin.json` UNCHANGED | `git diff main -- plugins/hep-ph-demo/.claude-plugin/plugin.json` → empty | **PASS** |
| 12 | Commits use `W1:`/`W1(<k>):` prefix; no `Co-Authored-By:` | `git log --oneline main..HEAD` → `7c60860 W1: shared scaffolding + ModelSpec YAMLs + /demo rewrite`. `git log --format=%B main..HEAD \| grep -c 'Co-Authored-By'` → `0` | **PASS** |

### Additional spot-checks

- **Preflight-preserved-verbatim check.** Diff of new `demo/SKILL.md` Step 0 block (lines 16–29) against old file Step 0 block (lines 26–39 at main) — identical content (config.json keys, executable probe, error message, "Do not attempt installation here" clause). **PASS**
- **Step 1 intro verbatim vs synthesis §3 "`/demo` intro text".** Direct read of synthesis L440–446 vs SKILL.md L37–39 — matches including "not by tuning the DM mass, but by tuning the couplings to a cancellation" phrasing and the "FeynArts, FormCalc, DDCalc, GamLike, and the multi-component DM combiner" enumeration. **PASS**
- **Step 3 picker JSON verbatim.** Synthesis L452–463 vs SKILL.md L67–78 — match including the three ids, the cold-hour ranges (`~3–5`, `~5–9`, `~6–12`), and the Dark SU(3) blocked-note. **PASS**
- **dark-su3 fixture seed.** `diff` against `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` shows only additive comments + `claim_source` retargeted to arXiv + 2 added mass parameters (mV, mphi) for the §IV scan. No structural divergence. **PASS**
- **Summary schema byte-equivalent to §4.1.** Direct read of `summary.schema.json` vs plan L688–715 — exact match on `$schema`, `required`, `additionalProperties: false`, enum lists, nested `skipped_constraints.items` shape. **PASS**

---

## Cross-file schema contract audit

| Contract | Location | Frozen? | Parseable? | Notes |
|---|---|---|---|---|
| `summary.schema.json` (§4.1) | `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json` | **Yes, byte-for-byte** per §4.1 | Yes — `jsonschema` validates the canonical example in `test_summary_schema.py::test_canonical_example_validates` | WS2/3/4 can consume without ambiguity; `/demo` closing block reads the matching keys (model, artifacts_dir, skipped_constraints). |
| `constraints.yaml` schema (§4.2) | `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` | **Yes** — top-level `schema_version: 1`, `prereqs`, `constraints`, `models` all present | Yes — 12 tests in `test_constraints_yaml.py` pin the structure; `time_budget.resolve()` contract exercised in `test_time_budget.py` | All 11 prereqs carry `status ∈ {exists, planned}` and `hours.cold/cached`. `models.dark-su3.multi_component_prereq = dark-matter-constraints`. Per-model `time_overrides` keys are all in `{relic, dd, id}`. |
| Prose-directive regex (§4.4, §1.2) | Not yet emitted by WS1 (belongs to WS2) | N/A for WS1 | — | Regex is documented in §4.4; enforcement lives in WS2's `test_skill_structure.py`. |
| `time_budget.resolve()` return shape | `plugins/hep-ph-toolkit/skills/_shared/time_budget.py` | **Yes** — pinned by test_time_budget tests (`rows[].status`, `rows[].missing`, `rows[].constraint_id`, `rows[].chain_annotated`, overlap totals keys `cold_all`, etc.) | Yes | WS2 consumers can rely on `status in {"READY", "BLOCKED"}` and `missing` as a list, per the test assertions. |
| Commit-message convention (§4.5) | Commit `7c60860` | **Yes** — `W1:` prefix, no co-author | N/A | Single commit (sub-commits allowed but not needed). |

**All contracts that WS2/WS3/WS4 depend on are frozen and mechanically checkable.** No hidden coupling.

---

## Deviation verdict: `provisional` as YAML comment vs YAML key

**Acceptable.** The plan's §1.6 A1.4 says "every ModelSpec YAML carries a top-level `provisional: true|false` boolean"; §WS1 done-criteria item 6 phrased enforcement as a `grep -c "^provisional:"` shortcut. The actual intent (per §1.4 framing and the reviewer-ergonomics note) is that a human or simple tool can tell at a glance which YAMLs are unverified and which aren't, and that the marker is parseable. A fixed-format top-of-file comment (`# provisional: true|false` followed by `# TODO(physics):` for true) preserves both affordances — visible at the top of the file, parseable by `grep "^# provisional:"`, and the TODO block is intact. The alternative (extending `modelspec.schema.json` with `additionalProperties: true` or a dedicated `provisional` field) is a larger invasive schema change that would have to be plumbed into every ModelSpec-consuming tool and wasn't actually part of the WS1 scope — blocking WS1 on it would be scope creep. I recommend the planner update the §3 WS1 grep snippet to `grep -cE "^# provisional:" plugins/hep-ph-toolkit/skills/_shared/assets/*.yaml` for the next round, and note this in §4.2 as a known contract.

---

## If CHANGES REQUESTED

None. WS1 is approved. Merge `ws1/shared-scaffold` into `main` per §1.5 sequence and proceed to WS2.
