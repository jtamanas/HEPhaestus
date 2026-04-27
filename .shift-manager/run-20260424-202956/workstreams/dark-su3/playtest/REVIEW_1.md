# Opus Review 1 — Dark SU(3) PT1

**VERDICT: ACCEPT (sonnet FAIL is correct + well-evidenced; Phase 2 docs-only fix-loop is GO).**

Reviewer: opus | Reviewed at: 2026-04-24 | Worktree tip: a46f796 | Sonnet verdict: FAIL

---

## Per-letter findings

### A. 5 Primary Success Criteria

| # | Criterion | Sonnet | Opus check | Verdict |
|---|---|---|---|---|
| P1 | Pipeline connectivity (Ω>0, relic_approx=False, sigmav_approx=True) | PASS | summary shows Ω_V=33.307, Ω_Psi=2995.557, both >0; flags consistent | PASS |
| P2 | summary.json schema-valid | PASS | `demo_output/dark-su3/playtest/summary.json` validates clean against `_shared/summary.schema.json` (Draft7Validator: 0 errors) | PASS |
| P3 | BP1 bands at n=200 | PASS | 33.307 ∈ [31.6,35.0]; 2995.557 ∈ [2846,3146] | PASS |
| P4 | Convergence baseline locked | PASS | 0.00% drift @ n=400/800; pre-acknowledged grid-independent per `dsu3-fix-scope.json::weak_drift_gate_note` | PASS |
| P5 | iter-5 guard | PARTIAL | time_budget.py emits BLOCKED (correct because /dark-matter-constraints PLANNED); plan G5 spec mismatch logged as dsu3-003 minor | PARTIAL — accepted |

P5 partial is correctly attributed to a plan/contract mismatch (dsu3-003 minor docs), not an implementation defect. Plan §G5 was deferred to PT1 and the time_budget contract under current iteration cannot satisfy "READY without /dark-matter-constraints" — sonnet's diagnosis is right.

### B. Numerical results & drift

- 33.307 / 2995.557 — both inside locked bands. Confirmed.
- n=400/800 drift = 0.00% (float64-identical) — synthesis pre-acknowledged via `weak_drift_gate_note`. Treat as smoke pass, not regression. Confirmed.

### C. Banner check (G6)

Banner expected status = **WARNING** in prep gate (G6 banner_template_line non-null was downgraded to warning per plan line 153). Preflight `stale_strings.json` recorded `banner_template_line: null`, `banner_status: "missing"` — confirmed. PT1 banner_check therefore correctly fails and emits dsu3-002 as **blocker / docs / auto_fixable=true** per plan line 187 ("Banner finding (absent/paraphrased) ⇒ severity=blocker, fix_scope=docs"). Sonnet's classification is correct.

### D. dsu3-001 — stale "Confining dark sector" hits

Independent grep:
```
plugins/hep-ph-demo/skills/demo/SKILL.md:73
plugins/hep-ph-demo/skills/_shared/constraints.yaml:148
plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md:90
```
Exactly 3 hits at exactly the lines plan §P0.3 demanded. Confirmed.

### E. dsu3-002 — banner absence

`grep -rnI "regression-anchors|sigmav_approx=True|out of reach this run" plugins/hep-ph-demo/skills/` → 0 matches. Confirmed.

### F. dsu3-004 — paper-fidelity gap

Sonnet reports ~4 OoM (Ω_naive=3029 vs paper 0.12). Prompt asked about ~10 OoM — that was a prompt approximation; the actual gap is 4 OoM (log10(3029/0.12) ≈ 4.4). Either way, classification is correct: **major / physics / auto_fixable=false / NOT in Phase 2 docs scope** (plan line 188, 311). Sonnet correctly did NOT conflate this with the banner blocker.

### G. issues.jsonl schema compliance

All 4 records carry `schema_version:"1.1"` and the 13 required fields (id, severity, phase, symptom, evidence_path, evidence_excerpt, expected, hypothesis, blocking, auto_fixable, fix_scope, fix_owner_hint, related_commit) per plan line 219. Severity/fix_scope enum values valid. Phase-2 eligibility correctly tagged: dsu3-001/002 = blocker+docs+auto_fixable; dsu3-003 = minor (non-blocking, not gate-relevant); dsu3-004 = major+physics+NOT auto_fixable. Confirmed.

### H. summary.json against `_shared/summary.schema.json` (2hdma/prep tip 2c9dd31)

- The PT1 per-model `demo_output/dark-su3/playtest/summary.json` validates clean (Draft7Validator → 0 errors). Optional v1.1 fields (relic_approx, model_source, model_fixture) absent but optional per `state/schema_v1_1.ready`.
- The `.shift-manager/.../summary.json` is a separate run-summary metadata artifact (PT1 process state), NOT subject to the per-model schema; treating it as such would be a category error.
- PRIMARY-2 PASS confirmed.

### I. Plan deviations

None material. Sonnet:
- Honored fix-scope guard (zero source modifications; hash-diff PASS for all 5 files).
- Followed F3-fixed approach (no slash-command invocation; SKILL.md walk authoritative).
- Wrote all required artifacts (banner_check.json, diagnostics.json, summary.json, issues.json/jsonl, findings.md, run.log, timing.json, verdict.md, runbook.md, transcript.md).
- Filed banner finding correctly as blocker/docs (not conflated with paper-fidelity).
- Filed paper-fidelity correctly as major/physics (not blocker).

Minor: PT1 emitted `issues.jsonl` (newline-delimited) in addition to `issues.json` — consistent with plan §219 which references `issues.json` but mentions schema_version 1.1 lineage; both formats present, no harm.

### J. Phase 2 entry GO/NO-GO

**GO.**

Plan §"Phase 2 Entry" (lines 249-250): "Phase 1 produces ≥1 issue with `severity:blocker` AND `fix_scope:docs` AND `auto_fixable:true` ONLY. Any blocker with `fix_scope ∈ {physics, build, test, schema, cross_workstream}` → halt."

Blocker inventory:
- dsu3-001: blocker / docs / auto_fixable ✓
- dsu3-002: blocker / docs / auto_fixable ✓
- (dsu3-004 is major, NOT blocker — does not gate Phase 2)
- (dsu3-003 is minor — does not gate Phase 2)

No blockers in {physics, build, test, schema, cross_workstream}. Phase 2 docs-only fix-loop ELIGIBLE.

---

## Phase 2 issue manifest (for the Phase 2 sonnet)

Scope-guard authorization: `dsu3-fix-scope.json` allows edits to `plugins/hep-ph-demo/skills/dark-su3/**`, `demo_output/dark-su3/**`, plus the three named lines below, plus `banner_widening.active=true` authorizes a single banner-template insertion in `plugins/hep-ph-demo/skills/demo/SKILL.md` within the dark-su3 model section (record exact line at edit time).

| Issue | File | Target line | Fix description |
|---|---|---|---|
| dsu3-001a | `plugins/hep-ph-demo/skills/demo/SKILL.md` | 73 | Replace picker entry #3 `description` field. Drop "Confining dark sector"; replace with accurate SU(3)_D → SU(2)_D Higgsed phrasing (e.g., "Higgsed SU(3)_D dark sector with two DM candidates and exact parameter-independent SI blind spot. Currently fully blocked on /dark-matter-constraints."). Preserve JSON shape. |
| dsu3-001b | `plugins/hep-ph-demo/skills/_shared/constraints.yaml` | 148 | Replace `hook:` value. Drop "Confining dark sector"; rephrase to match Higgsed SU(3)_D model with exact parameter-independent blind spot. |
| dsu3-001c | `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md` | 90 | Replace `Description:` text in walkthrough. Drop "Confining dark sector"; mirror the picker description from dsu3-001a (single source of truth). |
| dsu3-002 | `plugins/hep-ph-demo/skills/demo/SKILL.md` | (insert within dark-su3 model section; record exact line in fix_loop iter log) | Insert verbatim banner template (synthesis-locked wording): `NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets.` Must match VERBATIM — no shortened form. After insert, rerun banner_check.json verification. |

dsu3-003 (minor, plan §G5 contract) is OUT OF SCOPE for Phase 2 docs-fix-loop; queue for next plan revision.
dsu3-004 (major, physics, micrOMEGAs integration) is OUT OF SCOPE for Phase 2; remains as the standing paper-fidelity gap with banner (dsu3-002) as the documented UX mitigation.

Phase 2 sonnet should:
1. Apply all 4 edits, atomic-commit `[dsu3-fix-docs-1] dsu3-001,dsu3-002: refresh picker/hook/walkthrough + insert banner`.
2. Re-run banner_check.json + grep verification (regression-anchors should now match exactly once).
3. Append to `workstreams/dark-su3/fix_loop/iter_1_attempts.json`.
4. Re-playtest gate.
