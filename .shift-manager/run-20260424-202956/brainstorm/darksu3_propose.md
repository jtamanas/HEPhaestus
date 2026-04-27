# Dark SU(3) — Playtest Proposal (PROPOSER)

Role: brainstorm-propose. Skeptic critique and synthesis follow.
Workstream: `dark-su3` (model 3 of 3, run-20260424-202956).

---

## 0. Surprise finding (read first)

The scope doc claims SKILL.md and practitioner_script.md describe the WRONG
physics (confining/HLS instead of Higgsing). **No longer accurate as of
commit `eb90acd` (iter-5 of prior fix loop).** Inspection of:

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/dark-su3/SKILL.md` (lines 8, 78-94)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/dark-su3/practitioner_script.md` (lines 11-87)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/_shared/assets/dark_su3.yaml` (lines 1-60)

…shows the Higgsing model (SU(3)_D → SU(2)_D, dark Higgs doublet PhiD, V + Psi
DM, Eqs. 26-29) is already authored throughout. The POST_MORTEM
"Deferred (iter-6+)" landed before run-20260424.

Remaining gap (per POST_MORTEM): **physics is Lee-Weinberg + Breit-Wigner
approximation, not paper's micrOMEGAs values** (`relic_approx: True` flag).
`Ω_V h² = 1.30e-9` / `Ω_Psi h² = 1.04e-7` are structurally finite,
order-of-magnitude only.

This reframes the playtest goal.

---

## 1. Test design

**Recommendation: option (b) — run against current (already-corrected) docs.**

There is no "wrong-docs" version to playtest in the current repo (the wrong
text exists only in the scope memo). Running (a) would require checking out
an earlier commit — out-of-scope.

Faithful interpretation of "make sure they all work": verify iter-5
end-to-end pipeline still completes, returns non-sentinel `Ω_*_h²` for both
candidates, persists `diagnostics.json`, SKILL.md prose matches what
`analytic_models.dark_su3` computes. **Confusion budget**: log spots where
SKILL.md / practitioner_script.md / yaml / analytic module disagree
internally — those are the real freshness bugs.

---

## 2. Practitioner persona

Practitioner script is already correct (verbatim from `practitioner_script.md`):

- **Q1**: Dark SU(3) gauge model, Arcadi & Profumo §IV. SU(3)_D Higgsed to
  SU(2)_D by PhiD with VEV v_D. DM = vector triplet `V` (Higgs-portal SI) +
  pseudoscalar `Psi` (parameter-independent SI blind spot, Eq. 29).
  Two-component, paper uses micrOMEGAs, analytic module handles observables.
- **Q2**: SM stays. New gauge group `GD = SU(3)_D` broken to SU(2)_D at v_D.
  One scalar `PhiD` (GD = 3, Y = 0). Post-breaking: 5 → massive dark gauge
  bosons (3 form `V`, m_V = g̃ v_D / 2); 3 unbroken; H_1/H_2 mixed by θ;
  CP-odd → `Psi` (m_Psi = g̃ v_D / (2√2)).
- **Q3** (deltas): keep `|D_μ PhiD|²`, dark Higgs potential, Higgs portal
  `λ_P |H|² |PhiD|²`. Delete UV fermion mass terms. Register five scan
  parameters: `g_tilde, sin_theta, m_H2, m_V, m_Psi`.
- **Q4** (deltas): one mixing sector (H_1/H_2, 2×2 by θ); sign on H_1's dark
  component drives Psi blind-spot. Delete spurious vector / kinetic-mixing.

Lee-Weinberg approximation lives in the analytic backend, not the script;
script correctly says "paper uses micrOMEGAs".

---

## 3. Invocation

`cd /Users/yianni/Projects/hep-ph-agents` → `/demo` → model 3 "Dark SU(3)"
→ constraints = relic only. Backend: analytic-only
(`analytic_only: true` in `dark_su3.yaml`).

Drive path (auto-selected by `time_budget.py` post iter-5):
`/lagrangian-builder --practitioner-mode` → `validate_spec.py` →
`demo_output/dark-su3/dark_su3_spec.yaml` → `/sarah-build` **bypassed** →
`/spheno-build [analytic]` → `analytic_models.dark_su3.compute()` →
`backends/analytic.py` writes `diagnostics.json` → `/maddm` **bypassed**
→ `summary.json`.

**MG5 dark-color wall canary**: `python3
plugins/model-building/skills/sarah-build/scripts/scan_outputs.py
$STATE_ROOT/models/dark_su3/sarah_output/UFO/dark_su3/`. Expect no UFO or
MG5 import failure (`NameError: name 'dt1' is not defined`). If MG5 silently
accepts, analytic-only justification needs review.

---

## 4. Success criteria

**Pipeline-connectivity (primary, per iter-5)**:
- `demo_output/dark-su3/diagnostics.json` exists, finite positive
  `Omega_V_h2` / `Omega_Psi_h2`, `relic_approx: True`.
- `demo_output/dark-su3/summary.json` schema-valid against
  `plugins/hep-ph-demo/skills/_shared/summary.schema.json`.
- BP1 reproduces iter-5 within 5% drift: `Ω_V h² ≈ 1.30e-9`,
  `Ω_Psi h² ≈ 1.04e-7`. Drift > 5% is itself a finding (Lee-Weinberg is
  deterministic).

**Paper-fidelity (secondary, expected to FAIL — severity=info)**:
- §IV Fig. 7: `Ω_tot h² ≈ 0.12`. Lee-Weinberg gives ~9-orders-underabundance
  at BP1. Known approximation gap; not a regression target.

**Files under `demo_output/dark-su3/`**: `dark_su3_spec.yaml`,
`diagnostics.json`, `relic_V_<n>.json`, `relic_Psi_<n>.json`, `summary.json`.

---

## 5. Failure taxonomy (ranked)

1. **Stale-internal-reference confusion** (HIGH). SKILL.md line 376 mentions
   `ANOMALY_CANCELLATION_FAILED` for SARAH — but SARAH is bypassed.
   Playtester may follow dead branch. Evidence: any `/sarah-build`
   invocation in agent steps.
2. **Analytic-backend numerical drift** (MEDIUM). Lee-Weinberg depends on
   `_shared` constants. Unrelated edits shift BP1 > 5%. Evidence: full
   `diagnostics.json` + commit hashes for `analytic_models/`.
3. **`time_budget.py` regression** (MEDIUM). Iter-5 added 2-line guard for
   `analytic_only_constraints: [relic]`. Sibling workstreams could revert.
   Evidence: `time_budget.py --model dark-su3 --constraints relic` should
   show READY, no `/dark-matter-constraints`.
4. **MG5 dark-color wall has moved** (LOW). If MG5 imports the UFO,
   analytic-only justification weakens. Evidence: `mg5_aMC` log + UFO scan.
5. **Missing field definitions** (LOW). Iter-4 dropped UV fermions; any
   leftover `psiDL`/`psiDR` reference confuses interview. Evidence: grep yaml.
6. **`diagnostics.json` SLHA round-trip strip** (LOW, regressed-fix). If
   `backends/analytic.py` was refactored, keys could be dropped, sentinel
   `-1.0` returns. Evidence: full summary.json + diagnostics.json.

---

## 6. Issue-logging format

Per-issue JSON (aggregate to `.shift-manager/run-20260424-202956/workstreams/dark-su3/issues.json`):

```json
{
  "schema_version": "1.0",
  "workstream": "dark-su3",
  "iter": "playtest-1",
  "severity": "blocker|major|minor|info",
  "phase": "preflight|interview|sarah|spheno|madgraph|maddm|summary|plot",
  "symptom": "<one-line user-visible failure>",
  "evidence_path": "/abs/path/to/log_or_artifact",
  "hypothesis": "<one-sentence root-cause guess>",
  "blocking": true,
  "related_post_mortem": "demo_output/dark-su3/fix_loop/POST_MORTEM.md#section",
  "auto_fixable": true
}
```

`auto_fixable: true` flags items the docs-fix sub-phase (§7) handles without
re-running physics. Severity ladder mirrors 2hdm-a iter-8.

---

## 7. Fix-loop authorization

**Recommendation: same workstream rewrites docs, in strictly-sequenced
sub-phase, after playtest issues captured.**

Sequence:
1. Playtester runs end-to-end. Captures confusion in `issues.json`.
2. Playtester writes `playtest_findings.md`.
3. **Hard checkpoint**: findings committed before any docs touch.
4. Same workstream's fix sub-phase reads `issues.json`, fixes only
   `auto_fixable: true` ∧ `phase ∈ {summary, interview, plot}` (no physics
   code).
5. Playtester re-runs to confirm; logs delta.

Spinning up a separate fix agent for ≤ a few text edits adds coordination
cost. Physics-code line (anything under `analytic_models/`, `backends/`,
`time_budget.py`, `constraints.yaml`) stays **off-limits** — those need a
playtester-fixer split. Escalate, do not fix in-stream.

---

## 8. Parallelism

- **Independent of singlet-doublet and 2hdm-a**. Distinct YAML, distinct
  analytic module, distinct subdirectory.
- **Subdirectory**: `demo_output/dark-su3/` (hyphen — iter-5 convention;
  legacy `demo_output/dark_su3/` underscore exists; capture if mixed).
- **Shared state risks**: `plugins/hep-ph-demo/skills/_shared/constraints.yaml`,
  `_shared/time_budget.py`, `analytic_models/_*` constants. Capture file
  hashes at start and end of run.
- **Race conditions**: none expected; analytic dispatch is in-process Python.

Recommended: run dark-su3 LAST (after singlet-doublet and 2hdm-a) to absorb
any shared-state damage. Alternative: parallel + accept risk, cheaper but
contaminates diagnosis.

---

## 9. Artifact contract

Outputs under `/Users/yianni/Projects/hep-ph-agents/`:

| Path | Producer | Required? |
|---|---|---|
| `demo_output/dark-su3/dark_su3_spec.yaml` | `/lagrangian-builder` | Yes |
| `demo_output/dark-su3/diagnostics.json` | `backends/analytic.py` | **Yes (iter-5 fix sentinel)** |
| `demo_output/dark-su3/relic_V_<n>.json` | analytic module | Yes |
| `demo_output/dark-su3/relic_Psi_<n>.json` | analytic module | Yes |
| `demo_output/dark-su3/summary.json` | `/demo` closing | Yes |
| `demo_output/dark-su3/summary.{pdf,png}` | `/hep-plotting` | Optional |
| `.shift-manager/run-20260424-202956/workstreams/dark-su3/issues.json` | playtester | Yes |
| `.shift-manager/run-20260424-202956/workstreams/dark-su3/playtest_findings.md` | playtester | Yes |
| `.shift-manager/run-20260424-202956/workstreams/dark-su3/run.log` | shell capture | Yes |

---

## 10. Time budget

Cold (full /demo, analytic-only, BP1): preflight+picker 2m,
practitioner replay 3m, validate+write 1m, analytic dispatch 1m, summary 1m,
issue triage 15m, fix sub-phase 20m, re-run 8m.
**Total: ~50 min; ~25 min zero-issue.** Cap at **90 min** before escalating.

---

## Confidence and unknowns

**Confidence**: HIGH that pipeline still works (iter-5 was clean, 128/128
tests green, no intervening commits to `analytic_models/dark_su3.py` or
`backends/analytic.py` per recent git log). HIGH that scope.md framing of
docs as "wrong" is itself stale — docs describe Higgsing correctly as of
`eb90acd`.

**Unknowns**:
1. Whether `demo_output/dark-su3/diagnostics.json` survives across runs or
   gets wiped — was missing on filesystem read; may be gitignored and only
   generated on demand. If first run can't produce it, that's the iter-5
   regression to chase first.
2. Whether practitioner-mode interview handles "no UV fermions" correctly
   in `/lagrangian-builder`'s Q3 reconciliation (no playtest evidence post
   iter-5).
3. Whether `time_budget.py`'s `analytic_only_constraints` guard is touched
   by sibling workstreams (interaction risk).
4. Whether SKILL.md error-paths table still references SARAH anomaly
   despite SARAH being bypassed — sanity-check during playtest.
5. 5% drift tolerance is a guess; Lee-Weinberg should be bit-reproducible.
   If not, evidence of nondeterministic input (RNG seed? float summation
   order?).
