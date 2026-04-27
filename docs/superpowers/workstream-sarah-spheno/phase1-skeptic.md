# Phase 1 — Skeptical Review (Opus skeptic)

## Blocker
**Issue 1 — Config-key collision with `hep-ph-demo`.** Proposer misread existing config schema.
- `hep-ph-demo/install_wolfram.sh:80` writes `wolfram_engine_path` + `wolfram_engine_version`; proposer invented `wolfram_kernel`/`wolfram_kind`/`wolfram_version`.
- `hep-ph-demo/install_sarah.sh:152` defaults to `$HOME/SARAH`; proposer changed root to `~/.local/share/hep-ph-agents/sarah/` under same key `sarah_path`.
- `hep-ph-demo/install_spheno.sh:158` writes `spheno_path` → binary; proposer renames to `spheno_base_path` → source dir.
- No migration story for "hep-ph-demo first, then model-building" or vice versa.
- **Fix:** align with existing `wolfram_engine_path`/`sarah_path`/`spheno_path`, OR make W0's first deliverable an explicit config migration. Not co-habitation hand-wave.

## Major

**Issue 2 — Orchestrator-as-script violates augment-not-replace.** User memory: skills drive tools; not Python state machines. `hep-ph-demo/skills/install/SKILL.md` is the proven precedent. Orchestration tests require mocking → lie-world. **Fix:** W5 = SKILL.md + small helper scripts per atomic action. Match hep-ph-demo precedent.

**Issue 4 — Fourth blocker mode wrong layer.** Spec already defines `activation_required` as a status code from `/sarah-install`, not as a blocker mode. Expanding PR-D three-state contract (fatal/recoverable/reference-only) on speculative need is wrong. **Fix:** keep activation_required at the install-skill-status level; if orchestrator needs a pause-and-ask mechanism at blocker level, use `fatal` with mandatory `user_instruction` field.

**Issue 5 — Hidden dependencies + parallelism is wasteful.**
- W3→W2 edge: W3's SPheno Fortran output must compile against W2's pinned SPheno version; fixtures silently drift if W2 bumps.
- W6 depends on W4's semantics of `latest_slha` (scan vs single run), not just config schema.
- W3/W4 both edit SHARED.md/ModelSpec schema during dev → serialize conflicts.
- **Fix:** pairwise parallelism: W0 → [W1,W2] → [W3,W4] → [W5,W6].

**Issue 6 — Merge strategy glosses worktree rebase pain.** If W1–W6 worktrees exist before W0 lands, each author must rebase onto W0. For isolated-worktree agents, manager must update each worktree manually. **Fix:** land W0 synchronously on main before spawning downstream worktrees. No forced rebase.

**Issue 9 — Scope slippage vs. spec.**
- Omitted: `/sarah-install use-path <path>` and `/spheno-install use-path <path>` subcommands (spec §2).
- Omitted: spec §5 Stage-2 exact SPheno signature `SPheno$MODEL <LesHouches.in> <SPheno.spc>`.
- Omitted: spec §5 explicit SLHA blocks enumeration (MODSEL/SMINPUTS/MINPAR/SPHENOINPUT).
- Added: `.contracts/` subdir (spec puts schema in SKILL.md or refs).
- Added: `scripts/validate-contracts.py` (no spec requirement).
- Added: `x-extensions: {}` forward-compat escape.
- Added: `HEPPH_WOLFRAM_KERNEL` env override (spec only mentions `HEPPH_SARAH_VERSION`).
- **Fix:** drop additions; add the omissions.

## Minor → Major

**Issue 3 — Jinja2 over-engineered.** Spec says "pure string-fill." Jinja+MarkupSafe adds runtime dep; `str.format` or a tiny in-file template engine is purer. CI-whitelist detects a smell rather than preventing it. Also **SARAH Title-casing (`dark_su3 → DarkSU3`) is unverified** — commit a canonicalizer function in W0 and make the filesystem layer use *our* canonical form, or flag as day-1 W3 probe. **Fix:** use `str.format` + pre-joined lists; verify-or-canonicalize SARAH name handling.

**Issue 11 — Worktree isolation semantics.** Agents with `isolation: "worktree"` get temp worktrees isolated from each other; only manager synchronizes. W4's "post-W3 re-run" requires explicit re-dispatch after merge — not mentioned in §5. **Fix:** explicit handoff steps in plan: W3 merge → manager re-spawns W4 from fresh worktree.

## Minor

**Issue 7 — Timestamp-stripping in W3 speculative.** SARAH embeds `DateString[]` in generated headers we can't fully control. Spec §4 keys cache on `sha256(spec.yaml) + sarah_version` (inputs only). Proposer introduced a second W4 cache key `sha256(sarah_output/...) + spheno_version` vulnerable to timestamps. **Fix:** W4 cache key = `sha256(spec.yaml) + sarah_version + spheno_version`, input-based only.

**Issue 8 — `_common.sh` duplication drift trap.** Actual file is 142 lines, has atomic-write issues (`_common.sh:113-142` no fsync). Third installer is hep-ph-demo/install which already exists. N=3 today, not N=2. **Fix:** promote to `plugins/shared/install-helpers/_common.sh` in W0.

**Issue 10 — SPheno reuse needs version-pin check.** "Detect and reuse" works only if versions match. Detect must include version check before adopting. **Fix:** detect-and-reuse **only if version matches pin**, else fresh install alongside.

**Issue 12 — Ergonomic.**
- "Rerun no-op ≤2s" → ≤5s (Python startup + sha256).
- "8 rows in scan_index.csv" → toy test; spec example is 190-point scan.
- `mg5_aMC -c 'import model ...'` — `mg5_aMC` doesn't accept `-c`; takes a script file.
- SHARED.md justification thin — could live in plugin README.

## Synthesizer priorities (ranked)
1. Fix config schema to align with existing `wolfram_engine_path`/`sarah_path`/`spheno_path` OR write explicit migration.
2. Make W5 SKILL.md-driven, not `orchestrate.py`.
3. Reject fourth blocker mode; use status-level `activation_required`.
4. Pairwise parallelism, not 4-way.
5. Promote `_common.sh` to shared helpers in W0.
6. Add `use-path` subcommands to W1/W2.
7. Land W0 synchronously before spawning downstream worktrees.
