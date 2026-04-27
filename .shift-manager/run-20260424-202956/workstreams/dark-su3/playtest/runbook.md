# Runbook — Dark SU(3) PT1

JIT distillation of demo/SKILL.md walk into dark-su3/SKILL.md execution path.
Approach: F3-fixed (no slash-command invocation; SKILL.md walk is authoritative).

## Step 0 — Preflight
- Read preflight_hashes.json from prep worktree (path: five_hashes).
- Verify dsu3-prep-tip.txt SHA matches git rev-parse HEAD (5595b5b).
- Confirmed gate_decision.json overall=warning, proceed_to_pt1=true.

## Step 1 — SKILL.md Read
- demo/SKILL.md: Step 3 model picker at lines 65-80. Picker entry #3 is dark-su3.
- dark-su3/SKILL.md: Full constraint workflow. Step 1 = DM-candidate declaration (V + Psi). Step 2 = constraint multi-select. Step 3 = time-estimate gate. Step 4 = execute (all BLOCKED for dark-su3 in this iteration).
- Verbatim strings A,B,C,D quoted in findings.md.

## Step 2 — Picker
- Pick #3: dark-su3. Label stale ("Confining dark sector"). Issue dsu3-001.

## Step 3 — Interview
- Practitioner Q1: "Dark SU(3) gauge model from Arcadi & Profumo..."
- Practitioner Q2: SM gauge group + SU(3)_D (dark), PhiD scalar (dark Higgs fundamental), no UV fermions.
- Practitioner Q3: dark Higgs kinetic + Higgs portal + 5 scan parameters (g_tilde, sin_theta, m_H2, m_V, m_Psi).
- Practitioner Q4: H_1/H_2 mixing sector with relative minus sign producing Psi SI blind spot.
- Selection: relic only + analytic backend.

## Step 4 — Time-Budget Probe
- Command: python3 time_budget.py --model dark-su3 --constraints relic
- Output: BLOCKED (dark-matter-constraints [PLANNED]). G5 READY assertion fails — see dsu3-003.
- Analytic compute is functional regardless.

## Step 5 — Analytic Relic (FRESH)
- compute({}, BP1, n_points=200/400/800) — never reusing baseline values.
- BP1: g_tilde=2.0, sin_theta=0.10, m_H2=500, m_V=150, m_Psi=70.
- Results: Omega_V=33.307, Omega_Psi=2995.557 (float64-identical across all n).
- Drift vs baseline: 0.00% (expected — solver ignores t_eval grid for Y_final).
- Band check: PASS.

## Step 6 — Banner
- Search: 0 matches for banner template text anywhere in plugins/hep-ph-demo/skills/.
- banner_check.json: present=False, verbatim_match=False, template_line=None.
- Issue dsu3-002 (blocker, docs).

## Step 7 — summary.json
- Written per schema. Schema validation: PASS.

## Step 8 — Hash-Diff
- All 5 files from five_hashes unchanged: PASS.

## Step 9 — Verdict
- VERDICT: FAIL (dsu3-001 + dsu3-002 blockers, both docs, both auto_fixable).
- Phase 2 eligible.
