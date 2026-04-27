# Dark SU(3) — Brainstorm Synthesis (FINAL)

Role: brainstorm-synthesizer. Reconciles propose vs. critique. No planning.
Workstream: `dark-su3` (model 3 of 3, run-20260424-202956).

Load-bearing posture: trust the critique on every disputed fact. Proposer
inherited stale numbers and the wrong commit. The skeptic re-derived against
HEAD; we adopt those.

---

## Verdicts on the proposer's 10 sections

| § | Topic | Decision | Why |
|---|---|---|---|
| 0 | "Surprise finding" framing | **REVISE** | Right that scope.md is partially stale; wrong about which commit fixed it (`3a2da2c`, not `eb90acd`) and missed that picker stub + `_shared/constraints.yaml:148` + `MANUAL_WALKTHROUGH.md:90` are still stale. Keep the reframing but cite correct commits and list the still-stale sites. |
| 1 | Test design (option b) | **KEEP** | Option (b) — playtest current docs — is correct. There is no realistic earlier-state to check out. |
| 2 | Practitioner persona Q1–Q4 | **REVISE** | Q1–Q4 content survives. Strike the "Lee-Weinberg lives in the analytic backend" sentence — HEAD uses scipy Radau Boltzmann (`b66ab35`), `relic_approx: False`. |
| 3 | Invocation flow | **REVISE** | Drive path is correct; **drop the `dt1` UFO canary** (skeptic right: `fermions: []` ⇒ no UFO emitted, scan_outputs hits FileNotFoundError). Replace with a direct check: `analytic_only: true` in `dark_su3.yaml` AND `analytic_only_constraints: [relic]` honored by `time_budget.py`. Also assert `compute(spec, params, n_points=200)` two-arg signature. |
| 4 | Success criteria | **REJECT** numbers; **KEEP** structure | Replace BP1 targets entirely. New baseline at HEAD: `Ω_V h² ≈ 33.31`, `Ω_Psi h² ≈ 2.996e3` (skeptic-verified). `relic_approx: False`. Paper-fidelity is **not** a regression target and must not be hidden under `severity=info` — promote per skeptic (see "Success criteria" below). |
| 5 | Failure taxonomy | **REVISE** | Items #1, #2, #3, #6 survive. Drop #4 (MG5 wall — analytic_only is the chosen path; wall location is moot). Drop #5 (UV-fermion leftover — covered by Q3 inspection already). **Add HIGH**: stale picker label / hook / walkthrough trio (`demo/SKILL.md:73`, `_shared/constraints.yaml:148`, `_shared/tests/MANUAL_WALKTHROUGH.md:90`). **Add MEDIUM**: stale POST_MORTEM read as ground truth. **Add HIGH**: `compute()` signature regression for any older harness. |
| 6 | Issue-log JSON | **REVISE** | Adopt skeptic's v1.1 schema (adds `id`, `evidence_excerpt`, `expected`, `fix_scope`, `related_commit`). Drop unconditional `related_post_mortem` (POST_MORTEM is iter-5 vintage; cite commits). |
| 7 | Fix-loop authorization | **REVISE** | Proposer's "physics off-limits, text only, hard checkpoint commit" is the right shape but wrong scope. The picker/hook/walkthrough triplet sits in `_shared/`. See "Scope of fix authorization" below for the decisive call. |
| 8 | Parallelism | **REVISE** | Per-model isolation holds. Real shared-state risk is `_shared/constraints.yaml` + `time_budget.py` + `analytic_models/_*` — all three workstreams touch them. File-hash capture is necessary but not sufficient; need the lock decision in §"Scope" below. Run dark-su3 LAST still recommended. |
| 9 | Artifact contract | **REVISE** | Trim from 9 to 5: keep `dark_su3_spec.yaml`, `diagnostics.json`, `summary.json`, `issues.json`, `playtest_findings.md`, `run.log`. **Drop** per-candidate `relic_V_<n>.json` / `relic_Psi_<n>.json` as REQUIRED — duplicative of diagnostics.json. **Add** `regression_baseline.json` (skeptic) capturing `Ω_V h² / Ω_Psi h²` at `n_points ∈ {200, 400, 800}`. |
| 10 | Time budget | **KEEP** | 90-min cap, ~50-min target, ~25-min zero-issue. Realistic. |

Where they disagreed and we sided with the skeptic: every numerical claim
(BP1 values, `relic_approx` flag, Lee-Weinberg framing, `compute()` signature),
the canary mechanic, the artifact list, the severity treatment of paper-fidelity
miss, and the scope of fix authorization.

Where they disagreed and we sided with the proposer: option (b) for test
design, run-LAST scheduling, ~90-min cap, in-stream fix sub-phase (with
refined scope below).

---

## Scope of fix authorization (the big decision)

**Decision: option (a) — include shared-file text fixes in the Dark-SU(3)
workstream, with a hard scope guard.** Reasoning:

- The user said "make sure they all work" and "spin up agents to resolve any
  issues". A 4th serialized "shared" workstream (option b) adds a full agent
  hop for three one-line text edits and breaks the "keep grinding" directive.
- Option (c) (freeze + punt) leaves the most-likely user-visible confusion
  (picker still says "Confining dark sector") in front of the next
  practitioner. Unacceptable.
- The picker / hook / walkthrough strings refer specifically to the dark-SU(3)
  model. SD and 2HDM+a workstreams have **no semantic reason** to touch those
  three lines. Contention is theoretical, not real, if we name the lines.

**Scope guard (enforced — escalate on violation):**

- **Allowed write paths for dark-su3 fix sub-phase** (exact, no globs broader):
  - `plugins/hep-ph-demo/skills/dark-su3/**` (any file)
  - `plugins/hep-ph-demo/skills/demo/SKILL.md` — **lines 70–80 only** (picker entry #3)
  - `plugins/hep-ph-demo/skills/_shared/constraints.yaml` — **line 148 only** (the dark-su3 hook entry)
  - `plugins/hep-ph-demo/skills/_shared/tests/MANUAL_WALKTHROUGH.md` — **line 90 only** (the dark-su3 walkthrough sentence)
  - `demo_output/dark-su3/fix_loop/POST_MORTEM.md` (refresh or supersede; not load-bearing for other workstreams)
  - `.shift-manager/run-20260424-202956/workstreams/dark-su3/**`

- **Off-limits** — escalate, do not edit:
  - `plugins/hep-ph-demo/skills/_shared/time_budget.py`
  - `plugins/hep-ph-demo/skills/_shared/analytic_models/**` (including `dark_su3.py`)
  - `plugins/hep-ph-demo/skills/_shared/backends/**`
  - `_shared/constraints.yaml` lines other than 148
  - Any file under `plugins/hep-ph-demo/skills/{singlet-doublet,2hdm-a}/**`
  - SD or 2HDM+a workstream issue logs

- **Escalation triggers** (write `escalation.md` and stop fix sub-phase):
  - Picker entry has moved off lines 70–80 (then SD or 2HDM+a touched it).
  - `_shared/constraints.yaml:148` no longer says the stale string.
  - Any failing assertion implicates `analytic_models/dark_su3.py`,
    `time_budget.py`, or `backends/analytic.py`.
  - `compute()` signature drift from `(spec, params, n_points=200)`.
  - File-hash diff at end-of-run shows a `_shared/` file changed without
    being on the allow-list.

This sidesteps option (b)'s coordination cost without the contention risk of
naive option (a).

---

## Success criteria (quantitative, HEAD-anchored)

**Pipeline-connectivity (primary, must-pass):**

1. `demo_output/dark-su3/diagnostics.json` exists, finite positive
   `Omega_V_h2` and `Omega_Psi_h2`, and `relic_approx: False`,
   `sigmav_approx: True`.
2. `demo_output/dark-su3/summary.json` schema-valid against
   `plugins/hep-ph-demo/skills/_shared/summary.schema.json`.
3. BP1 (`g_tilde=2.0, sin_theta=0.10, m_H2=500, m_V=150, m_Psi=70`) at
   `n_points=200` returns:
   - `Omega_V_h2  ∈ [31.6, 35.0]`  (33.31 ± 5%)
   - `Omega_Psi_h2 ∈ [2846, 3146]` (2996 ± 5%)
4. Convergence check: re-run BP1 at `n_points ∈ {400, 800}`. Relative drift
   on each Ω vs. n=200 must be `< 5%`. (Drift > 5% ⇒ Boltzmann integrator
   not converged at default; log as `severity=major`, `fix_scope=physics`.)
5. `time_budget.py --model dark-su3 --constraints relic` emits READY without
   appending `/dark-matter-constraints`. (Iter-5 guard regression detector.)

**Tolerance justification:** 5% is wide enough to absorb floating-point
nondeterminism and minor scipy version drift, narrow enough that a
propagator/coupling sign flip (the kind of bug `b66ab35` just fixed) shows
up as a 10× explosion. We are NOT comparing to the paper here — paper
fidelity is unreachable with the current `sigmav_approx: True` cross-section
estimator.

**Paper-fidelity (secondary, expected MAJOR miss — banner-printed):**

- §IV Fig. 7 has `Ω_tot h² ≈ 0.12`. HEAD gives `Ω_V + Ω_Psi ≈ 3.0e3`.
  Four-orders-off. **Severity = major** (per skeptic), **not info**.
- Mitigation: `/demo` summary must print a banner:
  `"NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True).
  Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported
  are regression-anchors, not physics targets."` If the banner is missing or
  the user-visible summary claims success without it, that is itself a
  blocker-severity finding.

---

## Pre-playtest preparation steps

Run sequentially before the playtester fires:

1. **Rotate stale demo_output**: `mv demo_output/dark-su3
   demo_output/dark-su3.preplaytest-$(date +%Y%m%d%H%M%S)` (do not delete —
   POST_MORTEM and iter_*.md may inform forensics). Then `mkdir -p
   demo_output/dark-su3`. Also note any `demo_output/dark_su3/` (underscore
   variant) and rotate it the same way; flag mixed-naming as an issue if
   both exist.
2. **POST_MORTEM disposition**: do **not** trust
   `demo_output/dark-su3/fix_loop/POST_MORTEM.md` as ground truth. Two options
   — pick one in the planner: (i) refresh the POST_MORTEM in the fix
   sub-phase to reflect `3a2da2c` + `b66ab35`; (ii) prepend a one-line
   "STALE — superseded by commits 3a2da2c, b66ab35; see synthesis.md" header
   and treat as archive. **Synthesizer recommendation: (ii)** — cheaper, less
   surface area, no re-derivation risk.
3. **Confirm picker slot #3 → dark-su3** at `plugins/hep-ph-demo/skills/demo/SKILL.md:73`.
   String search "Confining dark sector" should return three hits
   (SKILL.md:73, constraints.yaml:148, MANUAL_WALKTHROUGH.md:90); if more or
   fewer, escalate before playtest.
4. **Capture pre-run hashes**: `sha256sum` of `_shared/constraints.yaml`,
   `_shared/time_budget.py`, `_shared/analytic_models/dark_su3.py`,
   `_shared/backends/analytic.py`, `demo/SKILL.md`. Write to
   `.shift-manager/run-20260424-202956/workstreams/dark-su3/preflight_hashes.json`.
5. **Smoke-test `compute()`**: call `compute({}, {g_tilde:2.0, sin_theta:0.10,
   m_H2:500, m_V:150, m_Psi:70})` directly, confirm two-arg signature,
   confirm Ω_V ≈ 33.3. If smoke fails, escalate before playtest fires —
   pipeline regressed since synthesis time.
6. **Lock baseline**: write `regression_baseline.json` to the workstream
   dir with the `n_points ∈ {200, 400, 800}` triple. This becomes the v1
   regression target; any future run comparing-itself-to-itself uses this.

---

## Issue-log JSON schema (final, shared across all 3 workstreams)

```json
{
  "schema_version": "1.1",
  "workstream": "dark-su3 | singlet-doublet | 2hdm-a",
  "iter": "playtest-1",
  "id": "dsu3-001",
  "severity": "blocker | major | minor | info",
  "phase": "preflight | picker | interview | sarah | spheno | madgraph | maddm | summary | plot | docs",
  "symptom": "<one-line user-visible failure>",
  "evidence_path": "<abs path or repo-relative path:line>",
  "evidence_excerpt": "<verbatim quote, ≤200 chars>",
  "expected": "<what should have happened>",
  "hypothesis": "<one-sentence root-cause guess>",
  "blocking": true,
  "auto_fixable": true,
  "fix_scope": "docs | physics | build | test",
  "related_commit": "<sha or empty>"
}
```

Aggregate at
`.shift-manager/run-20260424-202956/workstreams/<model>/issues.json` as a
JSON array. `id` prefix is `dsu3-`, `sd-`, `2hdma-` per workstream.
**Drop** `related_post_mortem` (POST_MORTEM is stale; cite commits).
`auto_fixable: true` ∧ `fix_scope: docs` are the only items the in-stream
fix sub-phase touches; everything else escalates.

---

## Go / no-go gate

**Playtest GO conditions** (all must hold; any failure blocks playtest start):

- Steps 1–6 of pre-playtest preparation completed; smoke-test passes.
- Three "Confining dark sector" hits found at the expected file:line
  triplet — confirms picker still maps slot #3 to dark-su3 in the way the
  fix-loop expects. (Zero hits ⇒ another workstream already moved; reassess.
  More than three hits ⇒ unknown drift, escalate.)
- `preflight_hashes.json` written.
- Workstream output dir `.shift-manager/run-.../workstreams/dark-su3/` exists
  and is writable.

**Playtest PASS conditions** (success criteria above, restated):

- Primary criteria 1–5 all green.
- Paper-fidelity banner present in `/demo` summary output.
- `issues.json` written (may be empty array — not all-green requires zero
  issues, but every captured issue has `auto_fixable` decided).
- `playtest_findings.md` written.
- End-of-run hash diff against `preflight_hashes.json`: only allow-list
  files changed.

**Playtest FAIL ⇒ fix-loop**: enter fix sub-phase only if every blocking
issue has `fix_scope: docs` and `auto_fixable: true`. Any `fix_scope:
physics | build | test` blocker ⇒ escalate to user, do not attempt fix.

**Hard cap**: 90 min wall-clock. At cap, write `escalation.md` with current
state and stop.

---

## Planner-to-resolve ambiguity (flagged, not decided here)

1. **POST_MORTEM disposition** — option (i) refresh vs. (ii) prepend-stale-header.
   Synthesizer recommends (ii); planner should confirm.
2. **`relic_V_<n>.json` / `relic_Psi_<n>.json` per-candidate JSONs** — dropped
   from REQUIRED list, but if the analytic module *currently writes them
   anyway*, do we delete them post-run for cleanliness or accept as
   informational artifacts? Planner decides.
3. **Banner text exact wording** — synthesizer drafted above; planner may
   prefer a shorter form. Non-load-bearing.
4. **Concurrent-run scheduling** — synthesizer says "run dark-su3 LAST" but
   the run-`_shared/`-lock strategy is the planner's call (lock files vs.
   serialized landing vs. branched workstreams). All three workstreams
   share this question; resolve uniformly.
5. **Singlet-doublet / 2HDM+a synthesis docs** — they may make different
   calls on the `_shared/` lock question. If so, the planner reconciles;
   this doc commits dark-su3 to "edit only the three named lines, hash-diff
   end-of-run, escalate on any other `_shared/` mutation".
