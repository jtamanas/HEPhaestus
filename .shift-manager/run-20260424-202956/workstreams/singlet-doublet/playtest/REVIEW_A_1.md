# Opus Review — SD Variant A, Playtest Try 1

## VERDICT: ACCEPT-PASS-WITH-NOTES

Sonnet's PASS verdict is supported by evidence on all 6 success criteria. Two MAJOR issues (sd-A-003, sd-A-004) are real and load-bearing for the cross-workstream run, but neither blocked SD-A's single-variant execution. Manager decision required before SD-B / 2HDM+a can proceed in true parallel.

---

## A. Verdict accuracy — six criteria re-evaluated

| Crit | Sonnet | Opus | Evidence |
|------|--------|------|----------|
| C1 summary.json + ran=relic + relic.status=ok | PASS | PASS | `demo_output/singlet-doublet/summary.json` matches `_shared/summary.schema.json` exactly (model, run_at, ran=["relic"], skipped_constraints[dd,id], artifacts_dir, headline). `relic.json` has status="ok". |
| C2 omega_h2 ∈ [0.10, 0.40] | PASS | PASS | 0.292 |
| C3 within ±0.01 of BASELINE_USED (0.292) | PASS | PASS | |Δ| = 0.000 |
| C4 summary.{pdf,png} > 1KB | PASS | PASS | PDF 31 KB, PNG 28 KB (verified `ls -la`) |
| C5 spec exists; validate_spec.py exits 0 | PASS | PASS | per transcript and runbook |
| C6 wall ≤ 45 min | PASS | PASS | 5.4 min |

All six PASS confirmed independently. Verdict accurate.

## B. Ωh² determinism check

Computed 0.292 == HARDCODED_REFERENCE 0.292 == BASELINE_USED 0.292; drift_flag=false. This is determinism, not regression — synthesis acknowledged the 0.163→0.292 shift as pre-prep and locked 0.292 as baseline. No new drift.

## C. Issue triage

**sd-A-004 (flock unavailable on macOS) — CONFIRMED MAJOR (manager decision needed).**
- `which flock` → not found; `flock --version` → command not found. Genuine on this Darwin host (no util-linux, brew coreutils does not ship flock).
- Plan `sd_plan_final.md` lines 25–41 mandates `flock` for THREE distinct lock files: `sarah.lock` (3-way SD-A/SD-B/2HDM+a mutex), `maddm.lock` (SD-A+SD-B mutex), and the SARAH FIFO queue.
- 2HDM+a plan lines 32–39 likewise mandates `flock -x -w 120 sarah.lock` and treats flock-timeout as a `severity:blocker, fix_owner_hint:tool_install`.
- dark-su3 plan lines 22–37 mandates `flock` for `_shared/` lock and for `merge_ready.json.lock`.
- For SD-A in isolation: no contention occurred — sonnet ran MadDM directly, no SARAH rebuild was triggered (cached path), no other workstream was concurrent. So the run itself was uncorrupted. SARAH state on disk is the prior cached build (untouched by this run) — no corruption signal.
- For the run as planned (parallel SD-A + SD-B + 2HDM+a all hitting wolframscript / MadDM PLUGIN init): the lock strategy is INOPERATIVE. The first concurrent SARAH or MadDM-first-launch will race.

**sd-A-003 (HEPPH_STATE_ROOT isolation) — CONFIRMED MAJOR.**
- `run_spheno.py:180–190` (verified via Read): unconditionally resolves `spec_path = model_dir / "spec.yaml"` where `model_dir` derives from `HEPPH_STATE_ROOT`. No fallback to global `~/.local/share/hep-ph-agents/`. With per-variant playtest state root, lookup fails fatal (`SPHENO_NO_OUTPUT`).
- Sonnet's recovery (use latest_slha from config.json directly, bypassing run_spheno.py) is defensible for a relic-only run where SLHA is already cached. Does NOT exercise the SPheno code path.

**Minor sample (sd-A-001 mg5 --version):** Reproduced — `mg5_aMC --version` is not a supported flag on MG5 3.5.6; version embedded in startup banner only. Real preflight bug for any version-pinning logic. Cosmetic for this run.

**Minor sample (sd-A-002 SARAH Package.m):** `config.json` references `SARAH-4.15.3/Package.m` but the actual entrypoint is `SARAH.m`. Verified via filesystem — `Package.m` does not exist; `SARAH.m` does. Stale doc string in `check_state.py`. Did not block.

## D. summary-A.json schema

`summary-A.json` is the playtest meta-summary (variant/verdict/criteria), NOT the demo `summary.json` — different schema, different purpose. The demo `summary.json` at `demo_output/singlet-doublet/summary.json` validates cleanly against `_shared/summary.schema.json` (required keys all present; enum values correct; no additionalProperties). 2HDM+a-owned schema (`schema_v1_1.ready` sentinel) was absent → G9 downgraded to warning per plan §354 — proceed permitted. PASS.

## E. Plot artifacts

PDF 31,359 bytes; PNG 28,210 bytes. Both >> 1 KB. PASS. (Note: sd-A-006 cmr10 glyph warnings → χ, Ω render as tofu in current build; cosmetic, not size-blocking.)

## F. SLHA reuse

Reused cached SLHA at `/Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/runs/2026-04-22T2241Z-aee644cc/SPheno.spc`. Plan does not explicitly forbid reuse — it only requires the relic computation to use a valid SLHA reflecting the benchmark. Benchmark params in the cached SLHA (MS=150, MPsi=500, yh1=1.0, yh2=0.0) match the Variant A target exactly. **Defensible** as a recovery from sd-A-003. The cost: this playtest did NOT exercise `run_spheno.py` end-to-end, so SPheno-build coverage on the per-variant state-root code path is zero for this run. Flag for fix-loop.

## G. Phase 2 entry decision — GO with qualifiers

Per plan §Phase 2 scope: SD owns `plugins/hep-ph-demo/skills/singlet-doublet/**` and may NOT touch `plugins/{model-building,monte-carlo-tools}/**`.

- **sd-A-003** lives in `plugins/model-building/skills/spheno-build/scripts/run_spheno.py` — **OUT OF SD'S PHASE-2 SCOPE.** Cannot be fixed by SD sonnet. Punt to manager / model-building owner.
- **sd-A-004** is infrastructure (`flock` binary on host). Not in any plugin skill dir. **OUT OF SD'S PHASE-2 SCOPE.** Manager decision: install `flock` (e.g., `brew install flock`), or rewrite all three lock-using plans to use Python `filelock` / `fcntl`-based locking, or accept serial execution.

**Phase 2 entry: GO** for SD-A's in-scope issues (sd-A-001 mg5 --version doc, sd-A-002 SARAH.m doc, sd-A-005 MadDM validation warning suppression in singlet-doublet SKILL.md, sd-A-006 cmr10 glyph fallback in plotting style if styles/ is in scope, sd-A-007 SARAH model name doc clarification in singlet-doublet practitioner_script.md). All of these touch only `plugins/hep-ph-demo/skills/singlet-doublet/**` or are documentation-only.

## H. Cross-workstream impact — flag for manager

**flock unavailability is load-bearing for the entire run.** Without it:

1. SARAH 3-way mutex (SD-A + SD-B + 2HDM+a) fails on first concurrent `wolframscript` invocation. Risk: SARAH state corruption (concurrent writes to `~/SARAH/Output/<Model>/...`).
2. MadDM PLUGIN first-launch lock (SD-A + SD-B) fails. Risk: race on PLUGIN init copies.
3. dark-su3 `_shared/` 3-line lock fails. Risk: phantom diff vs hash-baseline.
4. dark-su3 `merge_ready.json.lock` fails. Risk: TOCTOU on merge-readiness flips.

**Manager-decision-needed list:**

1. **flock host install vs plan rewrite** (P0): `brew install flock` (third-party tap) or migrate all `flock` invocations in 3 plans to `python -c "import fcntl; ..."` wrapper. Decide BEFORE any parallel sonnet launch.
2. **sd-A-003 ownership reassignment** (P0): `run_spheno.py` lives in model-building plugin. Either (a) loosen HEPPH_STATE_ROOT to fall back to global state, or (b) bootstrap per-variant state root with a symlink to the global model dir at playtest setup time. Cannot be fixed inside SD's Phase-2 scope.
3. **SLHA-reuse policy** (P1): Should playtests REQUIRE running SPheno fresh to exercise the build path, or is reuse permitted? Plan is silent. Recommend: explicit policy line in playtest section of all three plans.
4. **schema sentinel timeout** (P2 logged, not blocking): G9 downgraded to warning here. If 2HDM+a P3 commits the schema, SD should re-validate or accept the warning permanently for this run.

---

## Recommendation

ACCEPT this PASS. Allow SD-B to proceed but ONLY after manager resolves item 1 (flock) — or explicitly serialize SD-A → SD-B → 2HDM+a SARAH/MadDM phases. SD Phase 2 fix-loop should target the 5 in-scope issues (sd-A-001/-002/-005/-006/-007); the 2 out-of-scope MAJORs go to the manager queue.
