# Transcript — Dark SU(3) PT1 (Practitioner Cold-Read)

2026-04-24 / branch dsu3/playtest-20260424 / SHA 5595b5b

---

## [00:00] Setup

- Worktree created: /Users/yianni/Projects/hep-ph-agents.worktrees/dsu3-playtest at 5595b5b
- Verified clean (nothing to commit).
- HEPPH_STATE_ROOT=/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260424-202956
- Gate decision: overall=warning, proceed_to_pt1=true.
- Prep artifacts confirmed: smoke_test.json, preflight_hashes.json, stale_strings.json, regression_baseline.json.

---

## [00:01] Step 1 — Read SKILL.md files

Practitioner reads demo/SKILL.md cover-to-cover.

Step 0 (preflight): Checks config.json for madgraph_path, sarah_path, spheno_path, wolfram_engine_path.
Step 1 (paper intro): "Arcadi & Profumo ask: where can dark matter hide from direct detection?..."
Step 2 (gate): AskUserQuestion continue/not_now.
Step 3 (model picker): Three options including dark-su3 at line 73.

**Picker entry #3 (STRING A) verbatim:**
  {"id": "dark-su3", "label": "Dark SU(3)      (~6–12 hr cold, all constraints)", "description": "Confining dark sector, two DM candidates with exact blind spot. Currently fully blocked on /dark-matter-constraints."}

OBSERVATION: "Confining dark sector" is factually incorrect. The paper (§IV) and dark-su3/SKILL.md both describe an SU(3)_D → SU(2)_D Higgsed model. The analytic module docstring flags this as "FACTUALLY WRONG". Filing dsu3-001.

---

## [00:02] Step 2 — Picker: Pick #3

Practitioner selects dark-su3.

Practitioner says (verbatim from plan §"PT1 verbatim strings"):
> "I'll take option 3 — Dark SU(3). The stale 'Confining dark sector' description is wrong per the paper; filing it as a blocker."

Delegation: demo/SKILL.md §Delegation → read and execute dark-su3/SKILL.md.

---

## [00:03] Step 3 — dark-su3 SKILL.md Step 1: DM-Candidate Declaration

dark-su3/SKILL.md prints DM-candidate declaration (V = dark vector, Psi = dark pseudoscalar with exact SI blind spot). Reference Lagrangian from Eqs. 26-29.

Practitioner says (verbatim):
> "Two-component DM confirmed: V (spin-1, tree-level SI via H1+H2 portal) and Psi (spin-0, exact parameter-independent SI blind spot from H1/H2 relative sign). Noted that /dark-matter-constraints is required for combination."

---

## [00:04] Step 4 — dark-su3 SKILL.md Step 2: Constraint Multi-Select

Options: relic, dd, id, collider.

Practitioner says (verbatim):
> "Relic only. All three would show BLOCKED anyway since /dark-matter-constraints is planned."

---

## [00:05] Step 5 — dark-su3 SKILL.md Step 3: Time-Estimate Gate

Ran: python3 plugins/hep-ph-demo/skills/_shared/time_budget.py --model dark-su3 --constraints relic

Output:
  Relic density  BLOCKED [BLOCKED — missing: /dark-matter-constraints]
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS] → /dark-matter-constraints [PLANNED]
    cold: 1.5–3 hr   cached: 0.3–0.7 hr
  selected + ready: (none ready)

**STRING B (constraints.yaml:148) verbatim:** hook: "Confining dark sector, two DM candidates with exact parameter-independent blind spot."

OBSERVATION: hook is stale ("Confining dark sector"). Covered by dsu3-001.

G5 assertion ("Assert stdout is READY") fails — stdout shows BLOCKED. Filing dsu3-003 (minor). Analytic compute IS functional.

Practitioner says (verbatim):
> "BLOCKED as expected on /dark-matter-constraints. The time_budget output shows the full prereq chain correctly but the 'Relic density BLOCKED' message is informative — the analytic path bypasses this gate. G5 READY assertion in plan is a spec/plan mismatch; logging dsu3-003 as minor."

BLOCKED-branch gate fires. Practitioner selects "run_ready" → 0 constraints ready → message "No selected constraints are currently runnable." → Loop back to Step 2.
Re-select: relic. Re-run → same BLOCKED → select analytic override (practitioner drives analytic backend directly per SKILL.md Step 4 analytic path).

---

## [00:06] Step 6 — Analytic Relic Compute

Practitioner says (verbatim):
> "Running analytic backend directly: compute({}, BP1, n_points=200). This is the expected path per SKILL.md Step 4c: 'The analytic backend dispatches directly — no MadDM session is run for this model'."

Results:
  n=200: Omega_V_h2=33.30664, Omega_Psi_h2=2995.557, wall=0.046s — PASS bands [31.6,35.0] and [2846,3146]
  n=400: Omega_V_h2=33.30664, Omega_Psi_h2=2995.557, wall=0.044s — drift 0.00% — PASS
  n=800: Omega_V_h2=33.30664, Omega_Psi_h2=2995.557, wall=0.043s — drift 0.00% — PASS
  relic_approx=False, sigmav_approx=True

Paper-fidelity gap: Omega_naive=3029 vs paper 0.12 (~4 OoM). Filing dsu3-004 (major, physics).

MG5 dark-color wall: not hit (never attempted). Expected per SKILL.md §4 and POST_MORTEM.

---

## [00:07] Step 7 — Banner Check

**STRING C (MANUAL_WALKTHROUGH.md:90) verbatim:**
      Description: Confining dark sector, two DM candidates with exact blind spot.
                   Currently fully blocked on /dark-matter-constraints.

Expected banner (STRING D):
  "NOTE: dark-SU(3) relic uses sigma_v approximations (sigmav_approx=True). Paper fidelity (Ω_tot h² ≈ 0.12) is out of reach this run; values reported are regression-anchors, not physics targets."

grep for "regression-anchors", "sigmav_approx=True", "out of reach this run": 0 matches.

Practitioner says (verbatim):
> "Banner is absent — STRING D not found anywhere. This is a BLOCKER per plan: banner finding => severity=blocker, fix_scope=docs. Filing dsu3-002."

---

## [00:08] Steps 8-9 — Summary, Hash-Diff, Verdict

summary.json schema validation: PASS
Hash-diff: all 5 files unchanged (0 source modifications) — PASS

VERDICT: FAIL — dsu3-001 (stale strings) + dsu3-002 (banner missing)
Phase 2 eligible: YES (both blockers are docs + auto_fixable)
