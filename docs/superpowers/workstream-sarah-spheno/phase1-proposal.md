# Phase 1 — Proposal (Opus proposer)

**Spec:** `/Users/yianni/Projects/hep-ph-agents/docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
**Target plugin:** `plugins/model-building/` (+ minimal patch to `plugins/hep-ph-toolkit/skills/madgraph/`)
**Integration strategy:** six git worktrees, local merges into `main`.

---

## 1. Workstream decomposition

```
W0 Shared Contracts  ────┬──► W1 /sarah-install    ──┐
                         ├──► W2 /spheno-install   ──┤
                         ├──► W3 /sarah-build      ──┤──► W5 /lagrangian-builder  ──► W6 /madgraph resolver
                         └──► W4 /spheno-build     ──┘
```

### Parallelizable after W0
- **W1** `/sarah-install`, **W2** `/spheno-install` — fully independent after W0.
- **W3** `/sarah-build`, **W4** `/spheno-build` — parallel after W0's ModelSpec + config-extension + sarah-output-layout contracts freeze. W4 uses committed fixture tree `tests/fixtures/sarah_output_darksu3/` until W3 lands.
- **W6** `/madgraph` resolver — parallel with W3/W4 once `config.models[<name>]` schema frozen.

### Sequenced
- **W5** `/lagrangian-builder` orchestrator — last; integrates everything; E2E smoke lives here.
- W3's real Wolfram smoke test depends on W1 landed (or `HEPPH_WOLFRAM_KERNEL` env-var injection during dev).

### Boundaries
| Workstream | Owns exclusive | Reads-only (contracts) |
|---|---|---|
| W0 | `docs/`, `plugins/hep-ph-toolkit/SHARED-model-building.md`, `plugins/model-building/.contracts/` | — |
| W1 | `plugins/hep-ph-toolkit/skills/sarah-install/**` | W0 |
| W2 | `plugins/hep-ph-toolkit/skills/spheno-install/**` | W0 |
| W3 | `plugins/hep-ph-toolkit/skills/sarah-build/**`, `tests/fixtures/modelspec/*` | W0 + W1 key names |
| W4 | `plugins/hep-ph-toolkit/skills/spheno-build/**`, `tests/fixtures/sarah_output_*/` | W0 + W2 + W3 layout |
| W5 | `plugins/hep-ph-toolkit/skills/lagrangian-builder/**`, `tests/integration/lagrangian_builder_e2e.sh` | all sub-skill contracts |
| W6 | `plugins/hep-ph-toolkit/skills/madgraph/SKILL.md` edit + 1 new reference | W0 config.models schema |

Single cross-boundary file: `plugins/model-building/.claude-plugin/plugin.json` — W0-owned.

---

## 2. Implementation strategy per workstream

### W0 — Shared Contracts (~1 session, no business logic)
- `plugins/model-building/.contracts/modelspec.schema.json` — JSON Schema for v1 ModelSpec (§4 of spec).
- `plugins/model-building/.contracts/config-extension.schema.json` — keys: `wolfram_kernel`, `wolfram_kind`, `wolfram_version`, `sarah_path`, `sarah_version`, `sarah_installed_at`, `spheno_base_path`, `spheno_version`, `spheno_installed_at`, `models[<name>].{spec, ufo, spheno_bin, latest_slha, latest_run, sarah_built_at, spheno_built_at}`.
- `plugins/model-building/.contracts/blocker.schema.json` — three-state + proposed fourth `user_action_required`.
- `plugins/model-building/.contracts/sarah-output-layout.md`.
- `plugins/hep-ph-toolkit/SHARED-model-building.md` — conventions: root `~/.local/share/hep-ph-agents/`, naming `^[a-z][a-z0-9_]{1,30}$`, cache key `sha256 + version`, timestamps UTC. Env-var overrides: `HEPPH_SARAH_VERSION`, `HEPPH_WOLFRAM_KERNEL`.
- Stub SKILL.md files (frontmatter-only) under all four new skills.
- `plugins/model-building/.claude-plugin/plugin.json` updated once here.
- `scripts/validate-contracts.py` (~30 lines) + one passing fixture per schema.

**Risk:** Schema over-tightening → include `x-extensions: {}` forward-compat escape.

### W1 — /sarah-install
- `SKILL.md` with decision flow (detect → install → activation-handling).
- `scripts/install_sarah.sh` adapted from `hep-ph-demo/skills/install/scripts/install_sarah.sh`.
- `scripts/_common.sh` **copy** (not symlink).
- `skill_env.yaml` pinning SARAH 4.15.3.
- `scripts/check_wolfram_activation.sh` — probes `wolframscript`, emits `{"status":"activation_required"}`.
- Install root: `~/.local/share/hep-ph-agents/sarah/`.
- Tests: `detect` on clean → `missing`; after `install` → `configured`; SARAH `<<SARAH; Start["SM"]; CheckModel[]` exits 0; forced download failure → `SARAH_DOWNLOAD_FAILED` blocker.
- **Risk:** Wolfram activation cannot be automated → propose fourth blocker mode `user_action_required` (or `recoverable` + mandatory `user_instruction`).
- **Back-compat:** detect existing `sarah_path` from prior `hep-ph-demo/install` to avoid reinstall.

### W2 — /spheno-install
- Same shape as W1.
- **Critical:** retain source tree after `make`; record `spheno_base_path = "<install_dir>/SPheno-4.0.5"` (so W4 can `make Model=<X>`). Distinct from `hep-ph-demo`'s `spheno_path` → binary.
- Tests: `install` leaves `bin/SPheno` + `Makefile`; absent gfortran → `GFORTRAN_ABSENT` with per-OS remediation; `make.log` last-40 lines captured into `SPHENO_BASE_BUILD_FAILED` blocker.
- **Back-compat:** if `hep-ph-demo` install still has source at `<binary>/../..` with Makefile, record `spheno_base_path` pointing there and skip reinstall.

### W3 — /sarah-build (heaviest)
- Templates: `templates/{model.m.j2, parameters.m.j2, particles.m.j2, SPheno.m.j2}`.
- Scripts: `run_sarah.py`, `parse_sarah_log.py`, `render_templates.py`, `validate_spec.py`.
- Tests: `test_render.py` against goldens in `tests/golden/dark_su3/`; `test_parse_log.py` canned logs; integration run (needs W1 or env-var) produces `UFO/DarkSU3/`, `SPheno/DarkSU3/`, `.build_key`; rerun no-op ≤2 s; negative anomaly case emits `ANOMALY_CANCELLATION_FAILED` with `coefficients`.
- **Risks:** templates must be pure string-fill (CI check bans `If[`, `Which[`, `Module[` at top level; Jinja2 limited to whitelisted `{% for %}` only); SARAH log patterns may drift (warn-not-fail on unknown warnings); SARAH Title-cases names (`dark_su3 → DarkSU3`) → canonicalizer committed in W0.
- Acceptance: MG5 `import model /path/to/ufo; display particles` exits 0.

### W4 — /spheno-build
- Scripts: `run_spheno.py` (compile → run → parse), `parse_slha.py` → `summary.json` with `masses/widths/problems/mixing`, `scan.py`, `leshouches_template.py`.
- Fixtures: `tests/fixtures/sarah_output_darksu3/` committed (~1–5 MB, acceptable).
- Tests: SLHA parser on goldens (including `Block PROBLEM 1`, `Block SPINFO 4`); compile `SPhenoDarkSU3` from fixture (needs W2); scan over `MpsiD × gD` → 8 rows in `scan_index.csv`; induce `PROBLEM 1` → `mode=recoverable`, scan continues.
- **Risks:** `make -j$(nproc)` fails on macOS → use `os.cpu_count()`; W3 output must strip timestamps to keep cache key stable; v1 scans sequential (no locks).

### W5 — /lagrangian-builder orchestrator
- Full rewrite of existing stub.
- Files: `SKILL.md`, `references/{interview.md, orchestration.md, anomaly-ledger.md}`, `assets/modelspec-templates/{dark_su3.yaml, singlet_doublet.yaml, 2hdm.yaml}`, `scripts/orchestrate.py`, `tests/integration/dark_su3_e2e.sh`.
- E2E: cold-config scripted interview → built `dark_su3` → MG5-ready UFO + SLHA. First run <15 min, rerun <2 min.
- **No free-form `.m` escape hatch** — emit `MODELSPEC_FEATURE_UNSUPPORTED`.
- **Judgment call:** Python `orchestrate.py` vs pure SKILL.md instructions (hep-ph-demo uses the latter).

### W6 — /madgraph resolver patch
- Edit `plugins/hep-ph-toolkit/skills/madgraph/SKILL.md` — "Named model resolution" subsection at top of Decision Tree.
- New `scripts/resolve_named_model.py` — `resolve(name) -> dict | None`.
- `references/generation.md` 10-line callout.
- Test: resolver correctness + `mg5_aMC -c 'import model $(resolve_named_model.py dark_su3 --key ufo)'` exits 0.

---

## 3. Shared contracts (freeze before parallel work)

1. **ModelSpec v1 schema** — exactly §4; version-gated (`spec_version: 1`).
2. **Config-extension schema** — the keys listed in W0. **Key collision with `hep-ph-demo`:** adopt `sarah_path` co-habitation; redefine `spheno_path` → `spheno_base_path`.
3. **Blocker (three-state + maybe fourth)** — propose `user_action_required`.
4. **SARAH output layout** — `models/<name>/sarah_output/{UFO/<Name>/, SPheno/<Model>/, sarah.log}` + committed `modelspec_name_to_sarah(name)` canonicalizer.
5. **Directory root + cache key** — `~/.local/share/hep-ph-agents/`, `.build_key` at conventional path.
6. **`_common.sh` ownership** — open question: duplicate into each install skill vs. extract to `plugins/shared/install-helpers/`. Recommendation: duplicate for v1 (~150 lines), promote on 3rd installer.
7. **plugin.json** — W0-owned, no other workstream touches.

---

## 4. Cross-cutting

| Concern | Owner | Timing |
|---|---|---|
| plugin.json registration | W0 | W0 merge |
| model-building README rewrite | W5 | W5 merge |
| Top-level README line item | W5 | W5 merge |
| CLAUDE.md augment-not-replace exemplar note | W5 | W5 merge |
| marketplace.json | — | no change |
| tests/integration/dark_su3_e2e.sh | W5 | W5 merge |
| Fixtures under tests/fixtures/ | W3/W4 per subtree | rolling |
| ROADMAP placeholders | W0 adds, each workstream updates | rolling |

Docs rule: no workstream creates `*.md` summary files outside its own `references/` except W0-owned `SHARED.md` and `.contracts/`.

---

## 5. Merge strategy (local-only)

Worktrees: `wt-w0-shared-contracts`, `wt-w1-sarah-install`, ..., `wt-w6-madgraph-resolver`.

Sequence:
1. W0 → `main` first. All other worktrees rebase (only forced rebase).
2. W1, W2 land in any order (fully independent).
3. W3 lands after W1 (integration test needs real Wolfram); rebase + minor SHARED.md merge.
4. W4 lands after W2; pre-W3 uses own fixture, post-W3 re-runs integration against actual W3 output.
5. W6 lands anytime post-W0.
6. W5 lands last with full E2E.

Conflict-minimization: each workstream owns full skill dir; plugin.json W0-only; `_common.sh` duplicated; README/CLAUDE.md touched only in W5; fixtures under each skill.

Integration gate before W5: schema validation, per-skill smoke, full E2E on `dark_su3` from cold state (gated on network).

---

## 6. Open judgment calls for skeptic

1. **`user_action_required` as fourth blocker mode** vs recoverable-with-instruction. Proposer picked fourth mode.
2. **`_common.sh` duplicate vs extract** to `plugins/shared/`. Proposer picked duplicate for v1.
3. **4-way parallelism (W1/W2/W3/W4) vs pairwise** (W1+W2 then W3+W4). Proposer picked aggressive; assumes fixture maintenance cheaper than sequencing.
4. **SPheno source-tree reuse from `hep-ph-demo`** if detectable vs always-fresh install. Proposer picked detect-and-reuse.
5. **Jinja2 vs `str.format` vs custom minimal engine** for templates. Proposer picked Jinja2 + whitelist.
6. **W5 as `orchestrate.py` script vs pure SKILL.md instructions.** Proposer picked script (heavier, testable).
7. **CI: real tools vs mock.** Proposer picked nightly full-tool tier; mocking risks augment-not-replace violation.
8. **SARAH UFO → MG5 3.5.6 compatibility** — included in W3 smoke test; fail-early.

### Residual unknowns
- macOS `wolfram-engine` cask + activation E2E untested.
- SPheno compile time on M-series Macs — 5–15 min budget is a guess.
- Scan parallelism in v2 — hook via `scan_worker(point, workdir)`.

### Had-to-guess
- SARAH Title-casing exact rule (`dark_su3 → DarkSU3`) — W3 day-1 verify.
- Anomaly log patterns in SARAH 4.15.3 — parser conservative, falls back to numeric `CheckAnomalies[]`.
- Config key-space collision w/ hep-ph-demo — co-habitation documented; clean split out of scope.
