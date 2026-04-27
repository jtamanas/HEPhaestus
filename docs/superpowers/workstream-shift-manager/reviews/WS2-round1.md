# WS2 Review — Round 1

**Subject:** WS2 singlet-doublet per-model skill (template-freezing workstream)
**Branch/commit:** `ws2/singlet-doublet` @ `0255333` on top of WS1 `7c60860`
**Worktree:** `/Users/yianni/Projects/hep-ph-agents.ws2-singlet-doublet`
**Reviewed:** 2026-04-19

---

## Verdict: **APPROVED**

All 14 done-criteria items pass mechanically. Prose-directive count/order is exact. `## Model metadata` agrees with `constraints.yaml.models.singlet-doublet` on all keys. The example `summary.json` in the skill body validates against `summary.schema.json`. Commit style is correct (`W2:`, no `Co-Authored-By`). Parametrized structural test skips 2hdm-a / dark-su3 cleanly (26 skips), not failures. Template is regular enough for WS3/WS4 adaptation; the handful of copy-hazard sites are enumerated below and must be flagged in the WS3/WS4 implementer prompts (they already are, per the plan).

---

## 1. Mechanical done-criteria table

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Full test suite green | `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` | **PASS** — `61 passed, 26 skipped in 0.27s` |
| 2 | Prose-directive total count in `singlet-doublet/SKILL.md` | `grep -cE '^>\s*Invoke\s+/[a-z0-9-]+' …/singlet-doublet/SKILL.md` | **4** (matches plan; all 4 are in the relic branch) |
| 3 | Step 4 relic branch has exactly 4 directives | `awk '/^#### Step 4 — Relic.../,/^##### 4e/' … \| grep -cE '^>\s*Invoke\s+/'` | **4** |
| 4 | Step 4 DD/ID branches have zero prose directives (gated away) | `awk '/^##### 4e/,/^##### 4f/' … \| grep -cE '^>\s*Invoke\s+/'` | **0** |
| 5 | Prose-directive order in relic branch | `grep -nE '^>\s*Invoke\s+/'` on lines 176, 193, 208, 210 | **`/sarah-build, /spheno-build, /madgraph, /maddm`** — correct |
| 6 | `summary.json` literal path present | `grep -c "demo_output/singlet-doublet/summary.json"` | **3** (≥1 required) |
| 7 | `plugin.json` is valid JSON, 5 entries in canonical order | `python3 -c "..."` | **PASS** — `['install','demo','singlet-doublet','2hdm-a','dark-su3']` |
| 8 | Seven sections present in order | `grep -n '^## \|^# Singlet' …/SKILL.md` | **PASS** — `# Singlet-Doublet`, `## When to invoke`, `## Model metadata`, `## Constraints and time estimates`, `## Flow`, `## Error paths`, `## File map` |
| 9 | Step 1 single-candidate variant | `grep -c "single-candidate model" …` | **1** — correct variant (not Dark SU(3) multi) |
| 10 | MadDM words (Majorana, relic_density, launch, Omega) | token counts | **Majorana:7, relic_density:3, launch:6, Omega:9** |
| 11 | Plot words (mplhep, ATLAS, black) | token counts | **mplhep:3, ATLAS:4, black:2** |
| 12 | Model metadata YAML keys match constraints.yaml | python diff on `models.singlet-doublet` vs fenced YAML | **all 5 keys MATCH** (display, dm_candidates, plot_axes, multi_component, time_overrides) — `multi_component_prereq` absent on both as required |
| 13 | `All-constraints cold total: 3.2–8.0 hr` within 0.5 hr of `time_budget.resolve(...).overlap_totals.cold_all` | structural test `test_cold_total_within_tolerance` | **PASS** |
| 14 | `W2:` prefix, no `Co-Authored-By` | `git log main..HEAD --format=%B \| grep -c 'Co-Authored-By'` | **0** |
| 15 | WS2 commit touches exactly 3 files | `git show --stat 0255333` | **3 files** — `plugin.json`, `test_skill_structure.py`, `singlet-doublet/SKILL.md` |
| 16 | Parametrized structure test skips (not fails) for 2hdm-a / dark-su3 | pytest output | **26 SKIPPED** on `Test2HdmA::*` + `TestDarkSU3::*`, zero failures |

---

## 2. Prose-directive regex audit

Regex: `^>\s*Invoke\s+/[a-z0-9-]+\b` (plan §1.2 / §4.4).

Extraction per Step-4 sub-branch:

| Sub-branch | Count | Directives (in file order) |
|---|---|---|
| 4c — Relic (READY) | **4** | L176 `/sarah-build`, L193 `/spheno-build`, L208 `/madgraph`, L210 `/maddm` |
| 4d — Plotting | 0 | plain prose consultation of `/hep-plotting` (not a `>` blockquote + `Invoke` pattern); per §4.4 the plot invocation is outside the prose-directive count — correct |
| 4e — DD/ID (BLOCKED) | **0** | gated away; no prose directives emitted — correct per plan |
| 4f — `summary.json` write | 0 | expected |

**Order:** exactly `sarah-build → spheno-build → madgraph → maddm`. **PASS.**

Note: the `/madgraph` and `/maddm` directives are on consecutive lines (208, 210). That's still two distinct blockquote lines starting with `> Invoke /`, which the regex matches twice — correct behavior confirmed by the structural test `test_step4_prose_directive_count`.

---

## 3. Schema contract audit

### 3.1 `summary.json` conformance

The Step-4f example JSON in the SKILL.md body (the fenced block following "Example for the case where only relic ran:") was extracted and validated against `plugins/hep-ph-toolkit/skills/_shared/summary.schema.json`:

```
$ python3 -c "import json, re, jsonschema; ...validate..."
Match found: True
Schema validation OK
Required fields present: ['artifacts_dir', 'headline', 'model', 'ran', 'run_at', 'skipped_constraints']
```

All six required schema fields are present; `additionalProperties: false` is respected; `model` uses the allowed enum value `"singlet-doublet"`; `ran` is a subset of `["relic","dd","id"]`; `skipped_constraints` items have `{id, reason}`. **PASS.**

The SKILL.md also correctly tells Claude to adapt `ran`, `skipped_constraints`, and `headline` to the actual run, and to NOT write `summary.json` on `Cancel` (per plan §4.1 and R9).

### 3.2 `## Model metadata` vs `constraints.yaml.models.singlet-doublet`

Diff of every key:

```
display:           MATCH
dm_candidates:     MATCH
multi_component:   MATCH
plot_axes:         MATCH
time_overrides:    MATCH
```

`multi_component_prereq` is correctly absent from both (singlet-doublet is single-component). **PASS** (§4.3).

Note — a subtle reviewer-prompt ambiguity: §4.3 pins the `## Model metadata` block to `constraints.yaml.models.<id>`, not to `_shared/assets/singlet_doublet.yaml` (the latter is the SARAH ModelSpec, a different schema: `gauge_groups`, `fermions`, `parameters`). The implementer correctly used `constraints.yaml` as the source of truth. If a future reviewer reads the review prompt as "diff `## Model metadata` against the `assets/*.yaml` ModelSpec," they will be confused — the ModelSpec has no `display` / `plot_axes` keys.

---

## 4. Physics content spot-check

- **Single-candidate:** Step 1 prints `"This is a single-candidate model; relic, DD, and ID rates are computed directly for chi1."` — correct variant (not the Dark SU(3) multi-candidate block).
- **MadDM guidance:** mentions Majorana flag (`self_conj = True` in UFO; L252), `set relic_density ON`, `launch`, and `Omega h^2` parse from `MadDM_output/relic_density.dat`. Section is 88 lines (target 40–60 — slightly over, see §7 below).
- **Plotting:** `mplhep`, `hep.style.use("ATLAS")`, `c='black'` scatter points, axis limits pulled from `plot_axes` (`m_chi [100, 1500] GeV`, `sin_2theta [-1, 1]`). Matches plan R11 and memory `feedback_data_point_color`.
- **Blind-spot physics:** Step 4a correctly notes `MS * MD + (y_h v/√2)² = 0` as the parameter-dependent (tuned) blind-spot condition — contrast with dark-su3 WS4 which is the EXACT parameter-independent cancellation. Correct singlet-doublet physics.

---

## 5. Test wiring audit (WS3/WS4 contract surface)

`test_skill_structure.py` is parametrized-by-class, not by `pytest.mark.parametrize`, but the plan doesn't require a specific parametrization style — it requires coverage of all 3 model ids with skip-if-missing, which is delivered via three classes each gated on `@pytest.mark.skipif(not _skill_exists(...))`. When WS3 creates `2hdm-a/SKILL.md`, the `Test2HdmA` class auto-unskips with 11 assertions; when WS4 creates `dark-su3/SKILL.md`, `TestDarkSU3` auto-unskips with 13 assertions. Confirmed by running pytest now: all 26 test-IDs for the unfinished models are skipped (not errored).

The `Test2HdmA` class includes the physics-adaptation word assertions (`Dirac`, `CP-odd`, `loop-only`, `a-resonance|a resonance`, `tan β|tan_beta|tan beta`) — so WS3 will fail its own test suite if it copy-pastes WS2's Majorana guidance. Similarly `TestDarkSU3` asserts `scalar dark pion`, `vector dark meson`, `confining`, `multi-component`, `blind spot`, plus the `dark-matter-constraints` ≥ 3 occurrence count and the `"No selected constraints are currently runnable"` message. **This is strong adversarial guardrail wiring for the template adaptation** — the implementer did more than the plan strictly required here, and it's load-bearing for WS3/WS4 quality.

---

## 6. Template-adaptation callouts — WS3/WS4 MUST NOT copy verbatim

These are the specific sites in `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md` that WS3/WS4 implementer prompts must flag. **WS3 prompt already covers #1, #2, #3, #4, #7; WS4 prompt already covers #1, #5, #6, #7.** Nothing missing from the plan's existing prompts, but I'm listing them here so the shift-manager can cross-check the WS3/WS4 reviewer prompts during round-1 review of those workstreams.

| # | File + section | Line range | Hazard if copied verbatim |
|---|---|---|---|
| 1 | `## Model metadata` YAML block | L22–L35 | Entire block must be rewritten per `constraints.yaml.models.<id>`: `display.title`, `display.hook`, `dm_candidates[*].name/notes`, `plot_axes.{x,y}.symbol+range`, `multi_component` (true for dark-su3), `multi_component_prereq: dark-matter-constraints` (dark-su3 only), `time_overrides`. `test_skill_structure.py` catches all five keys per-model — strong guard. |
| 2 | `## Constraints and time estimates` table | L48–L54 | Pre-filled **WITH SINGLET-DOUBLET STATUS** (`READY`, `BLOCKED — missing: /feynarts, /formcalc, /package-x, /ddcalc` for DD; `BLOCKED — missing: /gamlike` for ID). For 2hdm-a: DD chain is still loop-only, but the `All-constraints cold total` numerics differ. For dark-su3: **ALL THREE rows are BLOCKED on `/dark-matter-constraints [PLANNED]`**. A naive copy ships wrong STATUS and wrong chain annotations. No structural test covers the table text; adapter must rewrite by hand. |
| 3 | Step 4 header (`Relic density branch`) | L168 (the subsection title) | For dark-su3 the relic constraint is BLOCKED too, so there is no "Relic density branch" to execute — Step 4 for dark-su3 is the one-paragraph N=2 pointer (per plan §1.3 NO-MATH rule, WS4 done-criteria). WS4 must rewrite L162–L291 entirely, NOT adapt in place. |
| 4 | Step 4c MadDM guidance (`Majorana flag`, Higgs-portal coupling, `self_conj = True`, `chi1 chi1~ > all all`, `MS * MD + (y_h v/√2)²` blind-spot formula) | L206–L289 | Singlet-doublet-specific at every line. For 2hdm-a: Dirac candidate, `a`-mediated `chi chi~ > a > SM`, `tan β`-dependent strength, CP-forbidden tree SI, loop-only DD subchain. For dark-su3: there is no Step 4c at all. Adapter will produce physically wrong guidance if they copy verbatim; WS3/WS4 reviewer regex-list in the plan is the enforcement. |
| 5 | Step 4 plot `axhline(0, ..., label="Blind spot (tree SI vanishes)")` | L322 | This horizontal line at `sin_2theta = 0` is the singlet-doublet tuned blind-spot condition. For 2hdm-a the analogous highlight is the `a`-resonance (`2 m_chi ≈ m_a`); for dark-su3 `phi` the blind-spot is parameter-independent and doesn't need highlighting. Adapter must rewrite. |
| 6 | Step 4e DD/ID blocked paragraphs | L349–L355 | The `sigma_SI_tree vanishes at the blind spot` sentence is specifically about singlet-doublet's cancellation structure. For 2hdm-a the reason is CP symmetry (`sigma_SI_tree ≈ 0` is CP-forbidden, **not** a tuned cancellation); for dark-su3 the whole section is different (all constraints blocked on `/dark-matter-constraints`). |
| 7 | `## Error paths` table | L390–L401 | `ANOMALY_CANCELLATION_FAILED` / `MODELSPEC_INVALID` entries reference `singlet_doublet.yaml`, and some error modes don't apply to 2hdm-a (scalar-extended Higgs sector) or dark-su3 (confining sector needs an HLS-like approach that SARAH handles differently). Adapter should verify each error row still applies to their model, not carry forward irrelevant rows. |
| 8 | `## File map` table | L407–L414 | All `$STATE_ROOT/models/singlet_doublet/` paths must become `…/two_hdm_a/` or `…/dark_su3/`. `./demo_output/singlet-doublet/summary.json` must become `./demo_output/2hdm-a/…` or `./demo_output/dark-su3/…` (the structural test asserts this path literal per-model). |

### Multi-candidate extensibility (dark-su3 readiness check)

The `dm_candidates:` YAML list in `## Model metadata` (L28–L29) is a single-element list. Extending to N=2 for dark-su3 is trivial:

```yaml
dm_candidates:
  - {name: phi, spin: "0",   notes: "scalar dark pion, parameter-independent SI blind spot"}
  - {name: V,   spin: "1",   notes: "vector dark meson, resonance region per Fig. 8"}
```

`test_skill_structure.py::TestDarkSU3::test_metadata_dm_candidates` compares `model_meta["dm_candidates"] == constraints_model["dm_candidates"]` — trivially extends to any `N`. **No template refactor needed for dark-su3.**

---

## 7. Minor / advisory (not blocking)

- **Step 4c length:** The plan's implementer prompt says "Target 40–60 lines"; the actual MadDM paragraph (lines 206–293, including code fences for MG5 session and `param_card.dat` blocks) is **88 lines**. This overshoots the target but delivers on the tractability attestation (R8): another Sonnet reading this section alone could drive an MG5 session — session setup, card edits, launch invocation, output parse location, and Planck comparison are all concrete. I am not requesting changes, because the extra length is concrete tractability content, not fluff. Flagging for WS3/WS4 reviewers so they don't use this as the length ceiling and accidentally demand WS3/WS4 also run long.
- **§4.3 reviewer-prompt ambiguity:** The review prompt for me said "Check `## Model metadata` YAML block matches `_shared/assets/singlet_doublet.yaml` on ALL keys. Diff them." This is ambiguous — §4.3 of the plan actually pins it to `constraints.yaml.models.<id>`, not to the ModelSpec asset YAML. The implementer did the correct thing (matched `constraints.yaml`). Flagging so the shift-manager can tighten the WS3/WS4 reviewer prompts if they inherited the same ambiguous wording.
- **Error-paths table is singlet-doublet specific:** Already captured as template callout #7 above. Worth a one-line note in the WS3/WS4 implementer prompts: "Review every row in Error paths; drop rows that don't apply, add rows specific to your model (e.g., 2hdm-a loop-subchain errors, dark-su3 HLS/confining-sector warnings)."

---

## Attestation (tractability, per §1.6 A2.2)

Reading only Step 4c (L206–L289) plus the reference `/madgraph` and `/maddm` skill files, another Sonnet could drive an MG5 session to produce `Omega h²` for `chi1`. The paragraph gives: (a) the MG5 prompt command sequence (`import model`, `generate`, `output`, `launch`), (b) the three `MadDM_card.dat` lines to edit with exact key names, (c) the `param_card.dat` Block MASS / Block SDMIX template, (d) the Majorana-flag check (`self_conj = True` in UFO `particles.py`), (e) the output file location (`run_01/MadDM_output/relic_density.dat`) and exact line prefix to grep (`Omega h^2 =`), (f) the Planck comparison value (`0.120 ± 0.001`). Two gaps a downstream Sonnet would need to ask about: (i) the exact PDG id assigned to `chi1` by SARAH (noted as `<chi1_pdg_id>` placeholder in L243 — resolved by reading the UFO `particles.py` after the `/sarah-build` step, documented upstream), (ii) choice of cosmological parameters for the MadDM thermal calculation (defaulted inside MadDM, non-blocking). Both are acceptable. **Tractable.**
