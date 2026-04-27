# Dark SU(3) — Skeptic Critique

Role: brainstorm-skeptic. Adjudicates proposer claims against HEAD + git evidence.

---

## Verdict (load-bearing): scope.md is partially stale; proposer is partially wrong

The proposer correctly flags that scope.md's "wrong physics in SKILL.md /
practitioner_script.md / yaml" line is stale — but cites the **wrong commit**
and **wrong fix-loop iteration** as the reason. The actual physics rewrite
landed in `3a2da2c` ("dark-su3 skill: rewrite prose + YAML to match paper
physics", Fri Apr 24 06:44), NOT in iter-5's `eb90acd` (Thu Apr 23 00:01).
`eb90acd`'s own commit message states explicitly: *"Does NOT rewrite the Step
1 DM-candidate prose ... That's iter-6+."* Proposer cites `eb90acd` as the
fix; that's a misread of the git log.

The fix that did land (`3a2da2c`) is downstream of `eb90acd` AND downstream
of `b66ab35` ("analytic_models/dark_su3: Boltzmann integrator for relic
density", same day). This second commit is more dangerous to the proposal
than the proposer realizes — see §"Quantitative challenges" below.

Net: scope.md was true at the time of writing but had been overtaken by two
commits on Apr 24 06:44. Proposer attributes the freshness to the wrong
commit and inherits stale numbers from the pre-rewrite era.

---

## Verified facts (file:line)

- **SKILL.md DOES describe Higgsing correctly** at HEAD:
  - `plugins/hep-ph-demo/skills/dark-su3/SKILL.md:8` — "SU(3)_D → SU(2)_D Higgsing: a dark Higgs doublet ..."
  - SKILL.md:78–94 — Eqs. 26–29 referenced; reference Lagrangian quoted; m_V = g̃ v_D / 2; m_Psi = g̃ v_D / (2√2); blind-spot Eq. 29 cited.
- **practitioner_script.md DOES match** (file:11–87) — Higgsing, PhiD, V triplet, Psi CP-odd.
- **dark_su3.yaml DOES match** (file:1–60) — `gauge_groups` has `GD: SU3 kind:dark`; `fermions: []`; PhiD scalar in `{GD:3}`; dark Higgs potential.
- **eb90acd touched** `_shared/constraints.yaml`, `time_budget.py`, `backends/analytic.py`, SKILL.md (Step 3+4 only). It did NOT touch Step 1 prose, practitioner_script.md, or dark_su3.yaml.
- **3a2da2c is the actual physics rewrite** — touched SKILL.md Step 1, practitioner_script.md, dark_su3.yaml.
- **b66ab35** replaced Lee-Weinberg with a scipy Radau Boltzmann integrator and **fixed an H1-channel propagator bug** ("missing /m_H1^4, was making Omega values ~10 orders of magnitude too small").

---

## Factual errors in the proposal

1. **`relic_approx: True` is wrong.** The current analytic module sets `relic_approx: False` (Boltzmann integrator) — see `analytic_models/dark_su3.py:458`. Proposer cites `relic_approx: True` four times as a success-criterion. Any test that asserts `True` will FAIL on HEAD. The honesty flag at HEAD is `sigmav_approx: True` (cross-section approximations), not `relic_approx`.
2. **BP1 numbers are stale by ~10 orders of magnitude.** Proposer's `Ω_V h² ≈ 1.30e-9`, `Ω_Psi h² ≈ 1.04e-7` came from the buggy Lee-Weinberg in `bf70ae1`. Re-running `compute({}, {g_tilde:2.0, sin_theta:0.10, m_H2:500, m_V:150, m_Psi:70})` at HEAD gives **`Ω_V h² ≈ 33.3`**, **`Ω_Psi h² ≈ 2996`** (verified by direct invocation). Proposer's "5% drift threshold" would explode on the very first run.
3. **Lee-Weinberg description in §2 ("Lee-Weinberg approximation lives in the analytic backend")** is no longer true. b66ab35's commit message: "Replace Lee-Weinberg approximation with scipy solve_ivp Radau on the standard Boltzmann equation." Proposer's practitioner Q1 already says "paper uses micrOMEGAs", which is fine, but the §2 framing of the BACKEND as Lee-Weinberg is wrong.
4. **Cited POST_MORTEM is itself stale.** The POST_MORTEM at `demo_output/dark-su3/fix_loop/POST_MORTEM.md` was written at iter-5 (Apr 23) and explicitly defers the prose rewrite + Boltzmann upgrade to iter-6+ and iter-7+. Both have since happened (`3a2da2c`, `b66ab35`). The POST_MORTEM has not been refreshed. Proposer cited it without noting this — anyone reading it will get an iter-5 picture of HEAD.
5. **scope.md is no longer 0% stale on dark-su3.** It's stale on **physics description** (rewrite landed) and on **implementation method** (Boltzmann not Lee-Weinberg). It is STILL CORRECT on the picker stub (`demo/SKILL.md:73` still says *"Confining dark sector"*) and the constraints.yaml hook (`_shared/constraints.yaml:148`). Proposer missed both.
6. **`compute()` signature.** Proposer's invocation flow assumes a single dict argument; HEAD's `compute(spec, params, n_points=200)` takes two positional dicts. Any harness that calls it the old way crashes with `TypeError: compute() missing 1 required positional argument: 'params'` (verified).

---

## Scope / design challenges

- **"Text-only docs, hard checkpoint commit, physics off-limits"** is too narrow. The most-likely real issue (picker label still says "Confining dark sector" at `demo/SKILL.md:73`, hook still says it at `_shared/constraints.yaml:148`, `MANUAL_WALKTHROUGH.md:90` ditto) is text-only and trivially fixable, but it sits in shared files that the singlet-doublet and 2hdm-a workstreams will also touch. A hard-checkpoint-commit strategy in main with three workstreams editing shared `_shared/` files is a merge-conflict generator. **Better isolation**: each workstream branches from a known SHA, fix-PRs land sequentially, fix sub-phase rebases. Or, narrowly: dark-su3's fix-pass touches ONLY files under `plugins/hep-ph-demo/skills/dark-su3/` plus the picker entry; SD/2hdm-a explicitly do not.
- **Authorization scope.** "Physics-code off-limits" sounds safe but b66ab35 + 3a2da2c shipped together yesterday — the analytic-module / SKILL.md / yaml / picker form a single semantic unit. If the playtester finds the picker description out of sync with the analytic backend's relic_approx flag, refusing to touch picker text or analytic header docstrings just kicks the problem to a third agent. The user said *"resolve any issues"*; "text-only docs in dark-su3/" is narrower than that. Recommend escalation triggers explicitly enumerated.
- **Artifact contract is gratuitous.** 9 required files vs. SD's 4–5. Concretely, `relic_V_<n>.json` and `relic_Psi_<n>.json` are duplicative of `diagnostics.json` (which already carries `Omega_V_h2` and `Omega_Psi_h2`). Drop the per-candidate JSONs unless the playtester chooses to write them; do not list them as REQUIRED.
- **`diagnostics.json` as iter-5 sentinel.** Proposer flags they couldn't find it on disk. That's not a sentinel failure — `demo_output/dark-su3/` is gitignored and `diagnostics.json` is generated only when the analytic backend runs. Citing absence as a regression marker is wrong; citing absence after a successful run as a regression marker is correct. State the difference.

---

## Quantitative challenges

- **5% drift on BP1 is impossible to use as a regression target until a new baseline is captured.** The pre-b66ab35 numbers in proposer's spec are off by ~10 orders of magnitude from current. New baseline (verified at HEAD): `Ω_V h² ≈ 33.3`, `Ω_Psi h² ≈ 2996`. These are themselves *unphysical* (paper target ~0.12 for total Ωh²; current sigma_v approximations are O(1) wrong per the module's own `sigmav_approx: True` flag), so even the new baseline is not a paper-fidelity target — only a regression-anchor.
- **Logging the paper-fidelity miss as `severity=info` is success-theater.** Proposer phrases it as "expected to fail (info severity)" but a 4–5 order-of-magnitude miss against the paper's `Ω_tot h² ≈ 0.12` is the headline finding of the demo, not background noise. Either:
  - log it as `severity=major` and route to `/dark-matter-constraints` / proper micrOMEGAs (when shipped), OR
  - print a banner *in the user-visible /demo summary* explicitly stating "paper-fidelity gap; sigma_v approximations dominate; not a regression target."
  Hiding it under `info` will let an unattended overnight run claim success while delivering a 10⁴-off relic.
- **Breit-Wigner near threshold.** The current Boltzmann integrator evaluates s = 4m²(1 + 3/(2x)), which sits very close to threshold; near `m_H2 ≈ 2 m_V` the BW propagator spikes. The proposer's BP1 (`m_H2=500, m_V=150`) is OFF resonance, so this won't surface in BP1 — but their proposed "fourth point near `m_H2 ~ 2 m_V`" will hit it. Add a convergence sweep on `n_points` (default 200; rerun at 400, 800) for that BP and assert relative drift < 5% before trusting the value.

---

## Invocation challenges

- **`dt1` UFO canary.** `dt1` is a real artifact (`UFOError: NameError: name 'dt1' is not defined`, documented `POST_MORTEM.md:56`). But running `scan_outputs.py` against `$STATE_ROOT/models/dark_su3/sarah_output/UFO/dark_su3/` requires that SARAH actually emitted that UFO — and the new yaml has `fermions: []`, so SARAH has nothing to render the dark-quark portion of the model. The UFO directory may not exist at all. The canary as proposed will fail with `FileNotFoundError`, not "MG5 wall is gone". Either: (a) drop the canary (analytic_only is the chosen path, MG5 is dead-letter regardless of where the wall is); (b) reframe as "verify the analytic-only flag is still wired in `dark_su3.yaml`" — direct evidence, not proxy.
- **Model picker #3 maps to `dark-su3`** — confirmed (`demo/SKILL.md:73`). HOWEVER the picker's `label` and `description` still say *"Confining dark sector"* and *"fully blocked on /dark-matter-constraints"*. Both are wrong post `eb90acd` + `3a2da2c`. The same stale string appears in `_shared/constraints.yaml:148` and `_shared/tests/MANUAL_WALKTHROUGH.md:90`. **This is the most likely user-visible confusion source for the playtest** and the proposer missed it entirely.

---

## Missed failure modes

1. **Stale picker / hook labels** (HIGH). Three files still call the model "confining". These are user-facing and override the corrected per-model SKILL.md prose. Fix-loop authorization MUST include `demo/SKILL.md:73` and `_shared/constraints.yaml:148`.
2. **Stale POST_MORTEM** (MEDIUM). Cited as ground truth for the playtest; describes iter-5 reality (Lee-Weinberg, `relic_approx:True`, prose stale). The synthesis agent and downstream fix agent must NOT trust it without re-reading at HEAD.
3. **`compute()` signature change** (HIGH). Any older harness calling `compute(params)` (single arg) breaks. Tests at `test_dark_su3_analytic.py` may have already been migrated; verify before fix-loop authorization.
4. **Stale `demo_output/dark-su3/` from prior runs** (MEDIUM). `iter_*` markdown files dated Apr 22–23 sit beside `fix_loop/`. A naive playtest will see them and reason from iter-5 reality. `mkdir -p` does not clean. Recommend: rotate or move iter-5 artifacts to `fix_loop/iter5_archive/` before the playtest fires.
5. **Concurrent mutation of `_shared/`** (HIGH). `constraints.yaml`, `time_budget.py`, `analytic_models/_*` constants are touched by all three workstreams. Proposer flagged but proposed only "capture file hashes start/end". Real mitigation: lock `_shared/` to read-only for two of three workstreams; whichever lands its fix-pass first releases the lock. Or: branch each workstream and serialize landing.
6. **Picker description "~6–12 hr cold"** is wrong post-eb90acd (analytic relic now READY ⇒ minutes not hours). Inconsistent with per-model SKILL.md. Adds confusion.
7. **No baseline lock-in.** The proposer's BP1 numbers are stale; without a checked-in golden the first re-run is also the first baseline. Pin `Ω_V h² = 33.31 ± 5%`, `Ω_Psi h² = 2.996e3 ± 5%` at `n_points=200` as the regression target NOW (commit a `regression_baseline.json` under the workstream dir).

---

## Concrete issue-log JSON schema

Proposer's schema is fine in shape but lacks two required fields and lacks examples. Replace with:

```json
{
  "schema_version": "1.1",
  "workstream": "dark-su3",
  "iter": "playtest-1",
  "id": "dsu3-001",
  "severity": "blocker|major|minor|info",
  "phase": "preflight|picker|interview|sarah|spheno|maddm|summary|plot|docs",
  "symptom": "/demo picker label says 'Confining dark sector'",
  "evidence_path": "plugins/hep-ph-demo/skills/demo/SKILL.md:73",
  "evidence_excerpt": "\"description\": \"Confining dark sector, two DM candidates...\"",
  "expected": "Picker label matches per-model SKILL.md (Higgsed SU(3)_D → SU(2)_D)",
  "hypothesis": "demo/SKILL.md picker stub was not updated when 3a2da2c rewrote per-model prose",
  "blocking": false,
  "auto_fixable": true,
  "fix_scope": "docs|physics|build|test",
  "related_commit": "3a2da2c",
  "related_post_mortem": "demo_output/dark-su3/fix_loop/POST_MORTEM.md#picking-up-iter-6"
}
```

Second concrete example (physics, NOT auto-fixable):

```json
{
  "schema_version": "1.1",
  "workstream": "dark-su3",
  "id": "dsu3-002",
  "severity": "major",
  "phase": "spheno",
  "symptom": "BP1 returns Omega_V_h2 = 33.3 (paper target ~0.12 for sum)",
  "evidence_path": ".shift-manager/run-20260424-202956/workstreams/dark-su3/run.log",
  "expected": "Order-of-magnitude agreement with arXiv:2506.19062 Fig. 7",
  "hypothesis": "sigmav_approx=True; crude H_2 width and missing SM-decay sum dominate",
  "blocking": false,
  "auto_fixable": false,
  "fix_scope": "physics",
  "related_commit": "b66ab35"
}
```

Required additions over proposer's schema: `id`, `evidence_excerpt`, `expected`, `fix_scope`, `related_commit`. Drop the unconditional `related_post_mortem` (POST_MORTEM is stale; cite commits instead).

---

## Summary — what survives from the proposal

**Survives**:
- Option (b) — playtest the current docs, not a checked-out earlier state.
- Independence from SD / 2hdm-a workstreams at the per-model file level.
- Stress on `time_budget.py` `analytic_only_constraints` guard regression detection.
- Failure-taxonomy items #1 (stale internal references — but the worst case is the picker/hook stubs, not SARAH anomaly mention) and #6 (diagnostics SLHA strip).

**Discarded**:
- BP1 = `1.30e-9 / 1.04e-7` numbers (replace with `33.3 / 2996` baseline).
- `relic_approx: True` as a success criterion (HEAD: `False`).
- "Lee-Weinberg in the backend" framing.
- "5% drift target" (no checked-in baseline yet; capture one first).
- "info severity" for the paper-fidelity miss (promote to major OR banner-print).
- 9-file artifact contract (trim to 5; per-candidate relic_*.json are duplicative).
- `dt1` canary on a UFO that won't be emitted.
- "Hard checkpoint commit" as the isolation strategy (use branch + serialize-land).

**Added required scope for the playtester / fix sub-phase**:
- Update `demo/SKILL.md:73` picker label + description.
- Update `_shared/constraints.yaml:148` hook.
- Update `_shared/tests/MANUAL_WALKTHROUGH.md:90` walkthrough text.
- Refresh or supersede `demo_output/dark-su3/fix_loop/POST_MORTEM.md` to reflect 3a2da2c + b66ab35 (otherwise next session repeats this confusion).
- Capture `regression_baseline.json` at `n_points = {200, 400, 800}` to lock convergence.
