# Phase 1 — Final Implementation Strategy (Synthesizer)

**Inputs:** spec (`docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`), proposer (`phase1-proposal.md`), skeptic (`phase1-skeptic.md`), verified precedent `plugins/hep-ph-toolkit/skills/install/`.

**Role of this doc:** decided, actionable plan for Phase 2 planners. Not a compromise. Each disagreement is resolved in §8.

---

## 1. Workstream decomposition

Final graph — **pairwise parallelism**, not 4-way. W0 lands first (synchronously on `main`) before any downstream worktree is spawned.

```
W0 Shared Contracts + Config Migration  (synchronous, blocking)
      │
      ├── wave A  ──► W1 /sarah-install     ─┐
      │              W2 /spheno-install     ─┤
      │                                      │
      └── wave B  ──► W3 /sarah-build  (after W1)  ─┐
                     W4 /spheno-build (after W2)  ─┤
                     W6 /madgraph resolver (after W0)
                                                    │
                     wave C ─► W5 /lagrangian-builder (after W1–W4, W6)
```

Rationale (resolving proposer vs skeptic Issue 5):
- W1 and W2 are genuinely independent — run in parallel.
- W3 needs a real Wolfram kernel for any non-trivial smoke; W4 needs a real `gfortran` + SPheno base for any compile. Running W3 before W1, or W4 before W2, forces heavy fixture-mocking that violates augment-not-replace (memory rule). Fixtures are fine for unit tests *inside* W3/W4 but not as a substitute for the install.
- W3 emits SPheno Fortran source consumed by W4. Parallel W3/W4 forces one of them to run against a committed fixture tree that silently drifts when SARAH or SPheno versions bump. Skeptic is right. Serialize W3→W4 within wave B; W3 and W4 start in the same wave only because W4 has a preceding compile step (stage 1 of its driver) it can develop against fixtures while W3 finishes.
- W6 (MG5 resolver) depends only on W0 config schema; can run anytime in wave B.
- W5 is the orchestrator — runs last, no parallelism.

**Spawn discipline:** manager lands W0 on `main` first. Only then spawns wave-A worktrees from the fresh `main`. Wave B worktrees spawn after wave A merges. No forced rebase across workstreams (resolves Issue 6).

---

## 2. Per-workstream scope

File paths are absolute-from-repo-root.

### W0 — Shared contracts + config migration

**Deliverables:**
- `plugins/hep-ph-toolkit/SHARED-model-building.md` — conventions: state root `~/.local/share/hep-ph-agents/models/` (the models-registry root only; base tool installs stay where `hep-ph-demo/install` already put them — see §3), model-name regex `^[a-z][a-z0-9_]{1,30}$`, UTC timestamps, cache-key recipe, env-var overrides (`HEPPH_SARAH_VERSION` only; drop `HEPPH_WOLFRAM_KERNEL`, not in spec).
- `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` — JSON Schema for ModelSpec v1 exactly as spec §4. `spec_version: 1` required. No `x-extensions` escape hatch (reject forward-compat speculation per skeptic Issue 9).
- `plugins/hep-ph-toolkit/skills/_shared/sarah-name.py` — `modelspec_name_to_sarah(name)` canonicalizer stub returning `"".join(w.capitalize() for w in name.split("_"))`. **Day-1 W3 probe verifies** against a real SARAH run; W0 commits it as provisional with a test that can be flipped once W3 reports. (Resolves Issue 3's unverified-casing concern.)
- `plugins/shared/install-helpers/_common.sh` — **promoted** from `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` (verbatim copy at first; refactor hep-ph-demo to source this version in a dedicated commit within W0). Skeptic Issue 8 is correct: three installers today (wolfram/sarah/spheno/mg5 + two new) is past the rule of three. Promoting avoids drift in the busiest part of the codebase. (Resolves Issue 8.)
- `plugins/hep-ph-toolkit/skills/_shared/config-migration.py` — reads existing `~/.config/hep-ph-agents/config.json`, performs no-op migration for v1 (confirms existing keys `wolfram_engine_path`, `sarah_path`, `spheno_path` are accepted as-is by the new skills), writes `models: {}` if absent. Exists to document that there is no rename, not to rewrite anything.
- Stub `SKILL.md` (frontmatter + one-line description) for `/sarah-install`, `/sarah-build`, `/spheno-install`, `/spheno-build` so each downstream worktree touches only its own dir.
- `plugins/model-building/.claude-plugin/plugin.json` — register four new skill names. **W0-owned; no other workstream edits this file.**

**NOT in W0:**
- No `.contracts/` subdirectory (skeptic Issue 9 — spec does not mandate one). Schema lives at `skills/_shared/modelspec.schema.json`.
- No `scripts/validate-contracts.py` (spec doesn't require it; trust peer review).
- No fourth blocker mode (see §4).

**Acceptance:**
- `jsonschema` validates the §4 ModelSpec example without error.
- Bash dispatch of `install.sh detect-all` from hep-ph-demo still works after _common.sh promotion (regression gate).
- `plugins/model-building/.claude-plugin/plugin.json` parses and lists all four stubs.

### W1 — `/sarah-install`

**Deliverables at `plugins/hep-ph-toolkit/skills/sarah-install/`:**
- `SKILL.md` — describes decision flow (detect → install → activation handling), mirroring `hep-ph-demo/skills/install/SKILL.md` §2.
- `scripts/install_sarah.sh` — subcommands `detect | use-path <dir> | install [dir]`. Adapted from `hep-ph-demo/skills/install/scripts/install_sarah.sh`. **Sources `plugins/shared/install-helpers/_common.sh`.**
- `scripts/check_wolfram_activation.sh` — probes with `wolframscript -code '1+1'`; if output contains the activation prompt string, emits `{"status":"activation_required","message":"..."}` with the exact remediation from spec §3.
- `skill_env.yaml` — pin `sarah_version: 4.15.3`.

**Config keys it writes (aligned with existing hep-ph-demo — resolves Issue 1):**
- `wolfram_engine_path` (not `wolfram_kernel`)
- `wolfram_engine_version` (not `wolfram_kind`/`wolfram_version`)
- `sarah_path` — SARAH package directory (contains `SARAH.m`), e.g. `$HOME/SARAH/SARAH-4.15.3`. **Do NOT relocate to `~/.local/share/hep-ph-agents/sarah/`.** (Resolves Issue 1.)
- `sarah_version`
- `sarah_installed_at`

**Detect-and-reuse:** if `hep-ph-demo/install` already configured `sarah_path` and `wolfram_engine_path`, and the smoke test passes, skill reports `status: configured` and exits clean — no reinstall.

**Acceptance:**
- `install_sarah.sh detect` on a clean machine → `{"status":"missing"}`.
- After `install`, `wolframscript -code '<<SARAH\`; Start["SM"]; CheckModel[]'` exits 0.
- Forced network failure → `SARAH_DOWNLOAD_FAILED` blocker (fatal).
- Unactivated Wolfram → surfaces `activation_required` **as an install-skill status** (not a blocker), per §4.

### W2 — `/spheno-install`

**Deliverables at `plugins/hep-ph-toolkit/skills/spheno-install/`:**
- `SKILL.md`.
- `scripts/install_spheno.sh` — `detect | use-path <path-to-source-tree> | install [dir]`. Sources shared `_common.sh`.
- `skill_env.yaml` — pin `spheno_version: 4.0.5`.

**Config-key conflict resolved (resolves Issue 1):** hep-ph-demo writes `spheno_path` = *binary at `bin/SPheno`*. `/spheno-build` in W4 needs the *source tree with `Makefile`* to run `make Model=<X>`. The sibling dir of the binary (`$spheno_path/../..`) is the source tree in the hep-ph-demo install layout.

Decision: **do not rename.** W2 writes a second key alongside:
- `spheno_path` — binary path, preserved for hep-ph-demo compatibility. W2 populates it from its own install too.
- `spheno_src_path` — directory containing `Makefile` (source tree root). New. Both keys point into the same install. Detection of an existing hep-ph-demo install: if `spheno_path` exists, derive `spheno_src_path = dirname(dirname(spheno_path))`, verify `Makefile` present, and record.
- `spheno_version`, `spheno_installed_at`.

**Acceptance:**
- After `install`, `$spheno_src_path/Makefile` exists and `make -C $spheno_src_path` (no target) succeeds.
- `gfortran` absent → `GFORTRAN_ABSENT` with per-OS remediation.
- `make.log` tail (last 40 lines) embedded in `SPHENO_BASE_BUILD_FAILED` blocker.
- Detect existing hep-ph-demo install → `status: configured`, derives `spheno_src_path` without reinstall.

### W3 — `/sarah-build`

**Deliverables at `plugins/hep-ph-toolkit/skills/sarah-build/`:**
- `SKILL.md` — describes ModelSpec-YAML → SARAH `.m` → UFO+SPheno-source flow.
- `templates/{model.m, parameters.m, particles.m, SPheno.m}` — **`str.format` templates**, not Jinja2 (resolves Issue 3). Placeholders use `{name}` / `{gauge_group_block}` with lists pre-joined in `render_templates.py`. No conditional logic in templates; any `{% if %}`-shaped need is a schema expansion or belongs in SARAH.
- `scripts/render_templates.py` — validates ModelSpec against `_shared/modelspec.schema.json`, uses `sarah-name.py` canonicalizer, writes `.m` files.
- `scripts/run_sarah.py` — invokes `wolframscript` with the exact code-string from spec §4 ("Headless SARAH invocation"). Stdout → `models/<name>/sarah_output/sarah.log`.
- `scripts/parse_sarah_log.py` — pattern table from spec §4.
- `scripts/validate_spec.py` — standalone schema + semantic check (name uniqueness, rep well-formedness).

**State root:** `~/.local/share/hep-ph-agents/models/<name>/` per spec §1. Tool installs stay where hep-ph-demo placed them.

**Cache key (resolves Issue 7):** `sha256(spec.yaml contents) + sarah_version` — **inputs only**, no output-tree hashing. Stored at `models/<name>/.sarah_build_key`. `--force` overrides. Rerun with same key → no-op in ≤5 s (not ≤2 s; Python startup + sha256 realistic).

**Day-1 probe:** before any template work, W3's first task is to run `wolframscript -code '<<SARAH\`; Start["SM"]'` on a known-good SM and confirm SARAH's name-canonicalization rule against `sarah-name.py`. If it diverges, fix the canonicalizer in `_shared/` (single commit back through W0 territory; touch nothing else).

**Acceptance:**
- `dark_su3` golden ModelSpec renders deterministic `.m` files (byte-for-byte).
- Full integration run (needs W1) produces `sarah_output/UFO/DarkSU3/`, `sarah_output/SPheno/DarkSU3/`.
- `mg5_aMC` reading a script file `import model <path-to-UFO>; display particles; exit` (not `-c`, per Issue 12) exits 0.
- Negative case: non-anomaly-free model → `ANOMALY_CANCELLATION_FAILED` with coefficients.

### W4 — `/spheno-build`

**Deliverables at `plugins/hep-ph-toolkit/skills/spheno-build/`:**
- `SKILL.md`.
- `scripts/run_spheno.py` — compile stage (idempotent, cached) + run stage + summary.
- `scripts/parse_slha.py` — extracts `masses`, `widths`, `problems`, `mixing` into `summary.json`. Raw `SPheno.spc` is source of truth.
- `scripts/leshouches_template.py` — templates LesHouches `MODSEL` / `SMINPUTS` / `MINPAR` / `SPHENOINPUT` blocks (**explicit enumeration per spec §5** — addresses Issue 9).
- `scripts/scan.py` — sequential scan driver.
- `tests/fixtures/sarah_output_darksu3/` — **minimal committed fixture**, gate: <2 MB, regenerated by W3 integration test and re-committed after wave B merges. Used for W4 unit tests that don't have SARAH available.

**Exact binary invocation (resolves Issue 9, spec §5):**
```
$MODEL_DIR/spheno_bin/SPheno$MODEL  $RUN/LesHouches.in  $RUN/SPheno.spc
```
Two positional arguments, not redirection.

**Cache key (resolves Issue 7):** `sha256(spec.yaml) + sarah_version + spheno_version`. **Input-based only.** Stored at `models/<name>/spheno_bin/.build_key`. No hashing of SARAH output tree — SARAH embeds `DateString[]` in generated headers that we cannot control.

**Compile:** `os.cpu_count()` not `nproc` (mac compat, per proposer §W4 risk — correct, keep).

**Recoverable-failure contract:** three-state per PR-D, as spec §5 table:
| Condition | Blocker | Mode |
|---|---|---|
| Exit ≠ 0 or no `SPheno.spc` | `SPHENO_NO_OUTPUT` | fatal |
| `Block PROBLEM` code 1/2/3 | `SPHENO_SPECTRUM_PROBLEM` | recoverable |
| `Block SPINFO 4` | `SPHENO_RGE_NONCONVERGENT` | recoverable |
| Clean `Block MASS` | success | — |

**Acceptance:**
- SLHA parser produces correct `summary.json` on committed goldens (including `Block PROBLEM 1` and `Block SPINFO 4` rows).
- `dark_su3` scan `MpsiD=200:1000:step=100` × `gD=0.5:2.5:step=0.5` produces `scan_index.csv` with all 45 rows, at least one marked `status=recoverable`. (Not 8 rows — too toy; not 190 — too slow for CI. 45 is spec-plausible.)
- `--params MpsiD=300` patches `Block MINPAR` before run.
- `--input-card path` used verbatim.

### W5 — `/lagrangian-builder`

**Deliverables at `plugins/hep-ph-toolkit/skills/lagrangian-builder/`:**
- `SKILL.md` — **this is the orchestrator**. SKILL.md-driven, not a Python state machine (resolves Issue 2 — skeptic is correct; hep-ph-demo precedent is SKILL.md + per-action scripts; orchestrator-as-script would force mock tests that violate augment-not-replace).
- `references/{interview.md, orchestration.md, anomaly-ledger.md}` — loaded on-demand by SKILL.md.
- `assets/modelspec-templates/{dark_su3.yaml, singlet_doublet.yaml, 2hdm.yaml}` — reference ModelSpecs.
- `scripts/check_state.py` — *small helper*, single purpose: reads config, returns JSON `{"sarah_install":"configured|missing", "spheno_install":"configured|missing", "model":"present|missing"}`. Not an orchestrator — a status probe the SKILL.md instructs Claude to call.
- `scripts/register_model.py` — *small helper*, writes `config.models[<name>]` atomically via the shared `config_merge` helper. Single side-effect call.
- `tests/integration/dark_su3_e2e.sh` — cold-config → built `dark_su3` → MG5-ready UFO + SLHA. Network-gated.

**Orchestration flow (SKILL.md-driven):** the skill instructs Claude to: run `check_state.py` → conduct interview → validate ModelSpec → invoke `/sarah-install` if missing → invoke `/sarah-build` → invoke `/spheno-install` if missing → invoke `/spheno-build` → call `register_model.py` → report paths. No script owns the state machine.

**Acceptance:**
- E2E on `dark_su3` from cold cache: first run <15 min, rerun with cache <3 min (Issue 12 — 2 min too tight with real SARAH).
- `activation_required` from `/sarah-install` triggers a clean pause with the exact instruction string; user reruns and flow resumes.

### W6 — `/madgraph` named-model resolver patch

**Deliverables:**
- `plugins/hep-ph-toolkit/skills/madgraph/SKILL.md` — single-subsection edit at top of decision tree: "Named model resolution" (per spec §6).
- `plugins/hep-ph-toolkit/skills/madgraph/scripts/resolve_named_model.py` — CLI `resolve_named_model.py <name> --key {ufo,latest_slha}` → prints path, exits 1 if missing. ~30 lines.
- `plugins/hep-ph-toolkit/skills/madgraph/references/generation.md` — 10-line callout.

**Acceptance:**
- `resolve_named_model.py dark_su3 --key ufo` prints the UFO dir.
- MG5 script-file invocation `echo "import model $(resolve ... --key ufo); generate p p > psiD psiD~; output test_out; exit" | mg5_aMC -` (or `mg5_aMC script.mg5`) exits 0. (Not `mg5_aMC -c` — Issue 12 is right; `mg5_aMC` takes a script file.)

---

## 3. Shared contracts (W0) — exact resolution

### 3.1 Config schema — alignment with existing hep-ph-demo

Verified against `install_wolfram.sh:80`, `install_sarah.sh`, `install_spheno.sh` (see §8 Issue 1). **Spec §1's invented keys are replaced by the existing ones.** No migration required; just adoption.

Final schema after both skills run:
```json
{
  "wolfram_engine_path":    "/Applications/Wolfram.app/.../wolframscript",
  "wolfram_engine_version": "14.1",

  "sarah_path":             "/Users/you/SARAH/SARAH-4.15.3",
  "sarah_version":          "4.15.3",
  "sarah_installed_at":     "2026-04-18T12:00:00Z",

  "spheno_path":            "/Users/you/SPheno/SPheno-4.0.5/bin/SPheno",
  "spheno_src_path":        "/Users/you/SPheno/SPheno-4.0.5",
  "spheno_version":         "4.0.5",
  "spheno_installed_at":    "2026-04-18T12:05:00Z",

  "madgraph_path":          "/Users/you/MG5_aMC/bin/mg5_aMC",
  "madgraph_version":       "3.5.6",
  "python":                 "/usr/bin/python3",
  "last_configured":        "2026-04-18T12:05:00Z",

  "models": {
    "dark_su3": {
      "spec":            "~/.local/share/hep-ph-agents/models/dark_su3/spec.yaml",
      "ufo":             "~/.local/share/hep-ph-agents/models/dark_su3/ufo",
      "spheno_bin":      "~/.local/share/hep-ph-agents/models/dark_su3/spheno_bin/SPhenoDarkSU3",
      "latest_slha":     "~/.local/share/hep-ph-agents/models/dark_su3/runs/2026-04-18T1230Z/SPheno.spc",
      "latest_run":      "2026-04-18T1230Z",
      "sarah_built_at":  "2026-04-18T12:20:00Z",
      "spheno_built_at": "2026-04-18T12:30:00Z"
    }
  }
}
```

Changes from the spec's draft schema:
- `wolfram_kernel` → `wolfram_engine_path` (existing).
- Drop `wolfram_kind` (existing schema has no analogue; `wolframscript` auto-detects Engine vs Mathematica, no need to record).
- `wolfram_version` → `wolfram_engine_version` (existing).
- `spheno_base_path` → `spheno_src_path` (new key, doesn't collide).
- Preserve existing `spheno_path` (binary).

**Spec needs a fix-up commit** (part of W0) noting the alignment — not a rewrite.

### 3.2 ModelSpec schema

Exactly spec §4. JSON Schema in `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`. `spec_version: 1` required. No `x-extensions` escape (skeptic Issue 9, correct).

### 3.3 Blocker contract

**Three states, not four.** See §4.

### 3.4 State root

`~/.local/share/hep-ph-agents/models/<name>/` — for **per-model state** only. Base tool installs (`sarah_path`, `spheno_src_path`) stay where `/install` put them (`$HOME/SARAH`, `$HOME/SPheno`). Resolves Issue 1's relocation conflict.

### 3.5 Cache-key recipe

All build caches keyed on **inputs only**:
- W3: `sha256(spec.yaml) + sarah_version`.
- W4: `sha256(spec.yaml) + sarah_version + spheno_version`.

Stored at `models/<name>/.sarah_build_key` and `models/<name>/spheno_bin/.build_key`. Single format: hex sha256 on one line.

---

## 4. Blocker contract — three-state, not four

**Decision:** **three-state** (fatal / recoverable / reference-only) per PR-D. Reject proposer's `user_action_required` fourth mode.

**Justification:**
- Spec §3 already defines `activation_required` as a **status code returned by `/sarah-install`**, not as a blocker mode. It's install-skill status, not a cross-cutting blocker class.
- PR-D landed a specific three-state contract. Expanding it on speculative need violates the skeptic's correct principle: don't widen proven contracts for one edge case.
- The orchestrator (W5) treats `activation_required` by parsing the JSON status output of `/sarah-install` and pausing with the exact instruction — no blocker-layer plumbing needed.
- For any *other* install skill that needs to pause for a user action, use `fatal` blocker with a mandatory `user_instruction` field populated. Single special field, not a new mode.

Resolves Issue 4.

---

## 5. `_common.sh` strategy — promote to shared

**Decision:** **promote to `plugins/shared/install-helpers/_common.sh` in W0.** Refactor hep-ph-demo to source the shared copy in the same W0 commit.

**Justification:**
- Verified: `_common.sh` is 142 lines (matches skeptic). Contains `config_get`, `config_merge`, `download_with_retry`, `verify_checksum`, `check_disk`, `log`/`warn`/`err`. All used identically by W1 and W2.
- Skeptic Issue 8 is correct that we already have 4 installers today (mg5/wolfram/sarah/spheno in hep-ph-demo), not 2 — rule-of-three threshold is passed. Adding W1+W2 makes it six installers all duplicating the same atomic-write + download machinery.
- Proposer's "duplicate for v1, promote on 3rd installer" rule already expired before v1 started.
- Risk of regression from the refactor is bounded: single-commit cherry-pick of an identical file, sourced by `scripts/install_*.sh` from a repo-relative path. W0 acceptance gate includes running `hep-ph-demo`'s `install.sh detect-all` as a regression check.

The atomic-write concern (no fsync) is a pre-existing issue orthogonal to this decision; file as a follow-up, not a blocker.

Resolves Issue 8.

---

## 6. Merge / worktree strategy

**Principle:** land W0 synchronously on `main` before spawning any downstream worktree. No forced rebases across agents.

1. **W0 on main.** Manager creates worktree `wt-w0-shared-contracts`, lands PR to `main`.
2. **Wave A parallel spawn:** manager creates fresh worktrees `wt-w1-sarah-install` and `wt-w2-spheno-install` from merged `main`. Agents work fully isolated. Merge order independent; either can land first.
3. **Wave B sequencing:**
   - `wt-w3-sarah-build` spawns from post-wave-A `main` (depends on W1 for real Wolfram smoke).
   - `wt-w4-spheno-build` spawns from post-wave-A `main` (depends on W2 for real SPheno base). Its committed SARAH-output fixture lives under `skills/spheno-build/tests/fixtures/` — agent owns it in its own worktree.
   - `wt-w6-madgraph-resolver` spawns from post-wave-A `main` (depends only on W0 schema).
   - W3 and W4 in the same wave: if merge conflicts appear in `plugins/hep-ph-toolkit/SHARED-model-building.md` or shared schema, W3 lands first (schema owner edge-case) and W4 rebases. Proposer's SHARED.md conflict risk is real but rare — any rebase is short because each skill owns its subdir.
4. **Explicit re-dispatch after W3:** manager re-spawns `wt-w4-spheno-build-integration` (or reuses the same worktree with fresh rebase) to re-run integration tests against actual W3 output rather than committed fixture. Skeptic Issue 11: this step is explicit in the plan, not glossed.
5. **Wave C (W5):** spawned only after W1–W4, W6 are on `main`. E2E test is gated on all upstream being green.

**Conflict minimization invariants:**
- `plugins/model-building/.claude-plugin/plugin.json` touched only in W0.
- `plugins/shared/install-helpers/_common.sh` touched only in W0.
- Each skill owns its full `plugins/hep-ph-toolkit/skills/<name>/` dir.
- Top-level README / CLAUDE.md updates only in W5.
- Fixtures nested per-skill, not top-level.

---

## 7. Open risks and explicit unknowns

To be resolved in Phase 2 planning or deferred to live implementation:

1. **SARAH name canonicalization.** Our guess is Title-case (`dark_su3 → DarkSU3`). **Unverifiable without running SARAH.** Day-1 W3 probe before any template work. Defer final decision; W0 commits a provisional `sarah-name.py` with a test marked `@skip_if_no_sarah`.

2. **Wolfram Engine activation UX on macOS.** Skeptic and proposer both flag this is untested by either of them. Planning phase should require wave-A agent to run through activation on a clean macOS before declaring W1 acceptance-tested.

3. **SPheno compile time budget.** Proposer guessed 5-15 min on M-series. Keep as a budget, not a contract; if actual exceeds, we accept it — nothing we can do.

4. **SARAH UFO → MG5 3.5.6 compatibility.** Not actually verified; proposer promises a smoke test. If the UFO format emitted by SARAH 4.15.3 is incompatible with MG5 3.5.6's UFO loader, we block on SARAH upstream, not on this workstream. Flag for wave B day-1.

5. **Fixture tree size.** Proposer said 1-5 MB for `tests/fixtures/sarah_output_darksu3/`. **Hard cap 2 MB** — if SARAH emits larger, gzip the fixture and decompress in setup. Don't bloat the repo.

6. **Scan concurrency in v2.** Out of scope, but W4's `scan.py` should factor `scan_worker(point, workdir)` so v2 parallelism is a wrapper, not a rewrite.

7. **How MG5 reads a model-import script.** The `mg5_aMC -c` invocation in the proposer is wrong (Issue 12). Correct form is `mg5_aMC <script_file>` where the script contains `import model ...; generate ...; output ...`. W6 smoke test must use this form. Planning phase must double-check by reading MG5 docs or existing eval/ examples.

8. **`hep-ph-demo` regression gate in W0.** The shared-`_common.sh` refactor needs a regression test. Planning phase must decide: add to CI, or manual-verify once and assert. Recommend CI addition with a `--no-network` probe of `detect-all`.

---

## 8. Resolution log — every skeptic issue

| # | Issue | Decision | Justification |
|---|---|---|---|
| 1 | Config-key collision with hep-ph-demo | **Adopt skeptic.** Use existing `wolfram_engine_path`, `sarah_path` (pointing to existing `$HOME/SARAH/...`), `spheno_path` (binary). Add only `spheno_src_path` as new. State root for per-model data is `~/.local/share/hep-ph-agents/models/`. | Verified lines 75-80 of `install_wolfram.sh`, 147-152 of `install_sarah.sh`, 155-160 of `install_spheno.sh`. Proposer invented keys that don't match reality; no migration story would be kind to users. |
| 2 | Orchestrator-as-script violates augment-not-replace | **Adopt skeptic.** W5 is SKILL.md-driven with two small helpers (`check_state.py`, `register_model.py`). No `orchestrate.py` state machine. | User memory is explicit; hep-ph-demo precedent is SKILL.md-driven; mock tests on orchestrator would lie about integration. |
| 3 | Jinja2 over-engineered | **Adopt skeptic.** Use `str.format` with pre-joined lists. Day-1 SARAH-name probe in W3. | Spec says "pure string-fill"; `str.format` is stdlib, zero deps, no CI whitelist gymnastics needed. |
| 4 | Fourth blocker mode wrong layer | **Adopt skeptic.** Three states, keep `activation_required` as install-skill status. | Spec §3 defines `activation_required` at status level; PR-D is a proven contract; no cross-cutting need demonstrated. |
| 5 | Hidden dependencies + wasteful 4-way parallelism | **Adopt skeptic.** Pairwise waves: W0 → [W1,W2] → [W3,W4,W6] → [W5]. | W3→W2 version-drift is real; W3/W4 SHARED.md conflicts predictable; planning-phase humility beats developer ego here. |
| 6 | Worktree rebase pain | **Adopt skeptic.** W0 lands on `main` synchronously before spawning downstreams. | Saves manager-level rebase coordination; each downstream spawns from a stable base. |
| 7 | Cache-key timestamp-stripping speculative | **Adopt skeptic.** All cache keys are input-only: W3 = `sha256(spec) + sarah_version`; W4 = `sha256(spec) + sarah_version + spheno_version`. | SARAH emits headers we can't control; output-based keys would churn forever. |
| 8 | `_common.sh` duplication drift | **Adopt skeptic.** Promote to `plugins/shared/install-helpers/_common.sh` in W0; refactor hep-ph-demo in same PR. | Already 4 installers, adding 2 more; rule-of-three long past. |
| 9 | Scope slippage vs spec | **Adopt skeptic.** Drop `.contracts/`, `validate-contracts.py`, `x-extensions`, `HEPPH_WOLFRAM_KERNEL`. Add spec §2 `use-path` subcommands, spec §5 exact SPheno signature, spec §5 SLHA-block enumeration. | Spec is the contract; both additions and omissions tracked to spec. |
| 10 | SPheno reuse needs version-pin check | **Adopt skeptic.** W2's detect-and-reuse runs `probe_version` against pin; on mismatch, install fresh alongside rather than adopt. | Silent version mismatch would break W4 compile against drifting headers. |
| 11 | Worktree isolation semantics | **Adopt skeptic.** Plan names explicit "re-dispatch W4 integration post-W3-merge" step. | Agents don't auto-sync; manager-orchestrated re-spawn is required. |
| 12 | Ergonomic nits | **Adopt skeptic.** Rerun no-op ≤5s (not ≤2s). Scan test uses 45-row `dark_su3` 2D scan (not 8-row toy, not 190-row tedium). MG5 invocation uses script file, not `-c`. SHARED.md retained at least for conventions + cross-skill env vars (not demoted to README). | Each item verifiable; worth fixing. |

---

## 9. Summary for Phase 2 planners

- Six workstreams total: W0 (shared), W1 (sarah-install), W2 (spheno-install), W3 (sarah-build), W4 (spheno-build), W5 (lagrangian-builder), W6 (madgraph resolver).
- Wave structure: W0 synchronous; wave A = [W1, W2]; wave B = [W3, W4, W6] with W3→W4 re-integration step; wave C = [W5].
- Config schema aligns with existing hep-ph-demo keys. Only net-new key is `spheno_src_path`.
- Three-state blocker contract unchanged. `activation_required` stays at install-skill status level.
- `_common.sh` promoted to `plugins/shared/install-helpers/` in W0.
- Templates use `str.format`, not Jinja2.
- Orchestrator W5 is SKILL.md + two small helpers, not a Python state machine.
- Cache keys are input-only.
- No `.contracts/` subdirectory; schemas live at `skills/_shared/`.
- Day-1 W3 probe verifies SARAH name canonicalization against a real SARAH run.
