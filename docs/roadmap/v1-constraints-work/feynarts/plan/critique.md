# `/feynarts` Plan — Skeptical Critique

Source: `docs/roadmap/v1-constraints-work/feynarts/plan/draft.md`. Evidence pulled from the feynman-diagrams plugin tree, `/sarah-install` scripts, and the sibling `/formcalc` + `/formcalc` plan drafts. Structured as: quote → counter → synthesizer action.

---

## 1. Placeholder skills are not placeholders

**Quote (§0, §1.4):** "placeholder `amplitude-calc`, `draw-feynman` skills exist … Retire the placeholder `feynman-diagrams/skills/amplitude-calc/` by turning its `SKILL.md` into a one-paragraph dispatch doc."

**Counter:** `plugins/hep-ph-toolkit/skills/amplitude-calc/SKILL.md` is **48 lines of substantive content** — Dirac/color algebra conventions, Mandelstam notation, example outputs. Same for `draw-feynman/SKILL.md` (65 lines — TikZ-Feynman usage, palette references, `docs/design-system.md` citation, `styles/hep-ph-agents-tikz.sty` usage). These are not stubs; they are the *current* behaviourally-live skills. Furthermore `plugins/feynman-diagrams/.claude-plugin/plugin.json` **explicitly declares both** in its `skills: [...]` array. Rewriting `amplitude-calc/SKILL.md` to a one-paragraph dispatch doc silently deletes the Dirac/color conventions the rest of the repo references; worse, the dispatch doc has no skill to dispatch to for the *reference/pedagogical* case that `amplitude-calc` currently serves (hand-derived `|M|²` on blackboard-style questions). The "augment not replace" memory warns against this.

**Synthesizer action:** (a) drop the "retire" line; instead **leave `amplitude-calc/` and `draw-feynman/` untouched** for v1 and have `/feynarts` live alongside them. (b) Update `plugin.json` to *append* `feynarts-install` and `feynarts`, not replace. (c) If `amplitude-calc` must acquire a dispatch header, do it in a small separate PR with the existing content preserved below a "When to dispatch to `/feynarts`" block.

---

## 2. `/sarah-install` does **not** install FeynArts — confirming the plan is right on install-dir convention, but wrong on `activate_wolfram_if_needed.sh`

**Quote (§2.2):** "wraps with `activate_wolfram_if_needed.sh` so a missing activation surfaces as … reuses `/sarah-install`'s `check_wolfram_activation.sh` and `_activation_parse.py` — shared helper, *no fork*."

**Counter:** Grep confirms `check_wolfram_activation.sh` and `_activation_parse.py` exist under `plugins/hep-ph-toolkit/skills/sarah-install/scripts/`. **But `activate_wolfram_if_needed.sh` does not exist anywhere.** Grep for that name across `plugins/` returns zero hits. The plan invents a helper name. Separately, `check_wolfram_activation.sh` sources `detect_wolfram.sh` via a local `$SCRIPT_DIR/detect_wolfram.sh` path that **assumes it is co-located with `detect_wolfram.sh`** — it is not callable in-place from a sibling skill without also co-locating or shim-sourcing that dependency.

**Synthesizer action:** (a) delete references to `activate_wolfram_if_needed.sh`; replace with the real helper name `check_wolfram_activation.sh`. (b) Add a concrete sub-step: "promote `check_wolfram_activation.sh` + `_activation_parse.py` + `detect_wolfram.sh` into `plugins/shared/install-helpers/wolfram/` with a pointer shim left at the old paths" — this is the only way two installers share the activation probe without cross-plugin script sourcing. If that promotion is out of scope, then `/feynarts-install` must invoke `check_wolfram_activation.sh` via its absolute path inside `plugins/hep-ph-toolkit/skills/sarah-install/scripts/`, and that cross-plugin dependency must be declared in `SHARED.md`.

---

## 3. `MakeFeynArts` wolframscript is hand-waved

**Quote (§2.3):** "`scripts/make_feynarts_driver.m.tpl` — separate wolframscript template for the **post-hoc SARAH** branch: `AppendTo[$Path, "<sarah_path>/.."]; <<SARAH\`; Start["<Name>"]; MakeFeynArts[];` — writes `<Name>.mod`/`<Name>.gen` into `$STATE_ROOT/models/<name>/feynarts_state/`."

**Counter:** The three-line template shown is a fragment, not a driver. Real `MakeFeynArts[]` emits into a SARAH-controlled output directory (SARAH's `$Path` and internal `$MODELDIR` govern file placement) — not wherever our Python wrapper wants them. There is no `WorkingDirectory` kwarg; the plan must either (a) `SetDirectory[...]` before `MakeFeynArts[]`, (b) chase the emitted files in SARAH's `FeynArts/` subdir under `sarah_output/` and copy them, or (c) post-hoc `CopyFile` inside the wolframscript. The plan does none; it asserts files land at `feynarts_state/` without a mechanism.

**Synthesizer action:** Spell out the full driver: `SetDirectory[$STATE_ROOT/models/<name>/feynarts_state]; AppendTo[$Path, "<sarah_path>/.."]; <<SARAH\`; Start[...]; MakeFeynArts[]; AbortOnMessage[];` — and verify against a real SARAH state where the output actually lands. Add a unit probe that runs `MakeFeynArts[]` once against `dark_su3` in a scratch dir and records the exact emitted filenames, so the fixture asserts behaviour rather than documentation.

---

## 4. Blocker-schema relocation: breaks 10+ consumer refs

**Quote (§1.1, §2.4):** "relocation is filesystem-only … `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — shrinks to a one-line pointer (`{"$ref":"../../../shared/schemas/blocker.schema.json"}`)."

**Counter:** Grep shows **11 consumers** of the old path (`sarah-install`, `sarah-build`, `spheno-install`, `spheno-build`, `lagrangian-builder`, orchestration references, `README.md`, `SHARED.md`, `test_blocker_schema.py`). The plan's "shim" is `{"$ref":"../../..."}` — but the existing test at `plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema.py` does `json.load(SCHEMA_PATH)` then `jsonschema.validate(instance, schema)`. With a `$ref`-only document and no `$id` resolution, `jsonschema.validate` will try to resolve the relative `$ref` against `file://` of the loaded path — which works locally but breaks the `$id` identity (the new file has `$id=https://hep-ph-agents/schemas/blocker/v1` but the shim does not). Worse, the sibling `/formcalc` and `/formcalc` plans *extend the enum* of the same schema (adding `FORMCALC_*` codes) — but they reference `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`, not the new shared path. A relocation that happens in `/feynarts` and simultaneously an enum extension that lands in `/formcalc` at the old path is guaranteed to merge-conflict.

**Synthesizer action:** (a) either defer the relocation to a W0-style prep PR that lands *alone* and fixes every consumer ref in-place, or drop the relocation from `/feynarts` entirely and keep `blocker.schema.json` at `model-building/skills/_shared/`. (b) If relocation is retained, expand §1 to enumerate *every* consumer path touched (11 files) with a grep-guarded verification step, not a vague "test-plan coverage." (c) Coordinate with `/formcalc` and `/formcalc` plans *before* they land — both sibling drafts currently point at the old path.

---

## 5. `processspec.schema.json` location **disagrees** with `/formcalc` and `/formcalc`

**Quote (§1.1, §2.4):** `/feynarts` creates `plugins/shared/schemas/processspec.schema.json`.

**Counter:** Both sibling plans insist the file lives at `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json` (formcalc `draft.md:43, 324`; looptools `draft.md:25`, and formcalc `brainstorm/final.md:213, 406` — explicit path). The `/feynarts` plan writes to `plugins/shared/schemas/` without acknowledging either sibling will break on that path. Field-name alignment is also ambiguous: `/feynarts` lists `{model_source, model_ref, initial:[str], final:[str], loop_order, exclude_topologies}`; `/formcalc`'s final specifies `{process_id, feynarts_tuple, incoming[], outgoing[], kinematic_limit, mandelstam, loop_order}` with **richer per-particle structs** (`{label, pdg, mass_symbol}`), none of which the `/feynarts` schema captures. If `/feynarts` lands first with the bare schema, `/formcalc` must either rewrite the schema (widening the field set — which breaks `/feynarts`'s cache-key determinism) or store its extra fields outside the shared contract.

**Synthesizer action:** (a) Pin location to **one** path. Recommend `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json` because both downstreams already expect it there. (b) Define the **union** schema now — `{process_id, feynarts_tuple, incoming:[{label, pdg, mass_symbol}], outgoing:[...], loop_order, kinematic_limit, mandelstam, exclude_topologies}` — so `/feynarts` writes a superset the downstreams can consume without migration. (c) Add a cross-plan note to the sibling drafts acknowledging this pin.

---

## 6. Goldens: SARAH-path integration is too heavy; tree + Z-self-energy are fine

**Quote (§2.3, §3.10):** "Tree-level `e+e- → μ+μ-` (exactly 1 diagram; byte-compare `summary.json` + sidecar) … 1-loop `Z → Z` self-energy … SARAH-path integration against the existing W3 `dark_su3` state directory."

**Counter:** The two builtin-model goldens (`--builtin SM`, tree + Z self-energy) are fine — they only need FeynArts + wolframscript. But the SARAH-path integration requires a **fully-built** SARAH state for `dark_su3` — i.e., `/sarah-build` has already run and produced `$STATE_ROOT/models/dark_su3/sarah/particles.m` + the cached SARAH session. Looking at W3 commit `081b908`, the repo has `dark_su3` templates and fixtures but the SARAH state dir is **not committed** (it would be ~tens of MB of SARAH output). The plan waves at "the existing W3 `dark_su3` state directory" as though it ships — it does not. Test will silent-skip or hard-fail on any fresh clone.

**Synthesizer action:** (a) State explicitly that the SARAH-path integration test is **locally gated** — requires the developer to have run `/sarah-build dark_su3` on their machine first, and is skipped otherwise. (b) Commit a *minimal* fixture: just `particles.m` + the emitted `.mod` + `.gen` files from a prior run, under `tests/fixtures/dark_su3_feynarts_state/`. Pin exact SARAH version in the fixture header so staleness is detectable. (c) Move the full end-to-end SARAH-path test behind `HEPPH_RUN_WOLFRAM_TESTS=1 && HEPPH_HAVE_SARAH_STATE=1`, not just the single Wolfram gate the plan implies.

---

## 7. Amp-size caps are guessed numbers

**Quote (§2.3, §3.9):** "`FEYNARTS_DIAGRAM_CAP=2000`, `FEYNARTS_AMP_SIZE_CAP_MB=200`, `FEYNARTS_DEFAULT_TIMEOUT_S=600`."

**Counter:** Brainstorm `final.md:212` attributes the 2000-diagram cap to "manager-specified" — fine as policy. The 200 MB and 600 s numbers have **no provenance** in either draft or brainstorm. For the Z-self-energy golden (~14 diagrams), `FeynAmpList.m` will be ~KB, not MB; for a 500-diagram 2-loop problem it could plausibly be 50-100 MB. 200 MB is a plausible guess but untested. Blocker UX on hit is also underspecified: plan says emit `FEYNARTS_AMP_TOO_LARGE` fatal and "refuses to write the cache key" — but does it leave `FeynAmpList.m` on disk for the user to inspect, or tear it down? The user needs to know whether the cap was tripped during Mathematica `Length[ins]` (cheap) or after `Put` (expensive).

**Synthesizer action:** (a) Document caps as **policy defaults, not thresholds backed by evidence** — annotate `skill_env.yaml` with `# default chosen pre-benchmark; revisit after first SUSY 2-loop run`. (b) Emit blocker `context` including actual measured value (`{diagram_count: 2347, cap: 2000}` or `{amp_size_mb: 312, cap: 200}`) so the user can decide whether to bump the env-var. (c) On `AMP_TOO_LARGE` — preserve `FeynAmpList.m` on disk but do not write the cache key; document that the partial file exists for diagnostics.

---

## 8. Gating of wolfram tests is over-specified

**Quote (Attack vector #10 echoes §4 of the plan):** integration tier gated by `HEPPH_RUN_WOLFRAM_TESTS=1` only; the install end-to-end test gated by `HEPPH_RUN_NETWORK_TESTS=1` only.

**Counter:** Plan gets this right — goldens (tree + Z self-energy) only need a local Wolfram kernel, no network. The integration tier gating is correct. However the plan conflates the two gates in §4 table row "Network (gated `HEPPH_RUN_NETWORK_TESTS=1`)" — the `test_install_gated.sh` *also* needs a Wolfram kernel for the smoke test (`Needs["FeynArts\`"]; $FeynArtsVersion`), so it should be `WOLFRAM=1 && NETWORK=1`.

**Synthesizer action:** Change the row for `test_install_gated.sh` to require both gates. Mirror the tri-gate pattern `/formcalc` uses (`WOLFRAM + NETWORK + SLOW`).

---

## 9. Minor but important

- §2.3 pins `feynarts_generic_model_hash = sha256(Lorentz.gen)` into the cache key. Good — matches brainstorm §5. But `Lorentz.gen` lives under `<feynarts_path>/Models/` and the plan's install script hashes it at install time and stores it in `config.json`. That key becomes stale if the user hand-edits `Lorentz.gen` (some users do). Add: `/feynarts generate` must re-hash `Lorentz.gen` at run time and emit `FEYNARTS_GENERIC_MODEL_DRIFTED` recoverable if it diverges from config — cheap safety net.
- §2.4 shim approach using a JSON `$ref` needs `jsonschema.RefResolver` wiring in tests; default `jsonschema.validate` does not always follow relative file refs. Verify explicitly.
- §2.3 `tables/SM.json` etc. — the plan commits to manually curating four alias tables cross-referenced from `Models/*.mod` "headers." FeynArts `.mod` files are Mathematica expressions, not headers; the mapping comes from `M$ClassesDescription` entries, not comments. Rephrase.

---

## Overall

The plan is structurally right but leaks abstraction in four high-impact spots: (1) it silently deletes live skills calling them placeholders; (2) it invents a helper name (`activate_wolfram_if_needed.sh`); (3) it relocates a schema without coordinating with the two sibling plans that reference the old path; (4) it pins a different `processspec.schema.json` location than both downstreams. The `MakeFeynArts[]` driver, amp caps, and SARAH-state fixture strategy need concrete artefacts, not prose. Fix those eight items and this is ready for eng-plan-review.
