# arXiv:2603.23040 — Scotogenic Inverse Seesaw Benchmark

**Paper:** "Light fermionic dark matter in a scotogenic inverse seesaw model"  
**arXiv:** https://arxiv.org/abs/2603.23040  

> **⚠ A/B test status (2026-04-18):** this paper is **not a useful pure-MadGraph
> skill test** at present. The authors did not release the
> `ScotoInverseSeesaw_UFO`, and no publicly-available UFO covers this specific
> scotogenic + inverse-seesaw + scalar-triplet combination. A skill-off agent
> and a skill-on agent would both fall back to analytic Python reimplementation
> of the paper's Eqs. 22-30, making the A/B delta artificially small.
>
> **Blocked on:** UFO-generation skill support (FeynRules / SARAH / FeynArts /
> LanHEP driver skills).
>
> **When UFO generation lands, promote this paper to the flagship
> end-to-end test:** Claude reads the paper's Lagrangian → drives the
> symbolic-algebra tool to produce the UFO → runs MadDM against the UFO →
> reproduces the paper's Ωh², σ_SI, σ_SD numbers at BP1/BP2/BP3. That full
> chain is the workflow practitioners actually want automated.

## Premise

This model extends the Standard Model with ℤ₂-odd particles: a vector-like lepton doublet E (mass m_E), a Majorana singlet N (mass m_N), and three real scalar singlets φ_r (r=1,2,3). The dark matter candidate is the lightest Majorana mass eigenstate χ₁ from a 3×3 neutral fermion mass matrix.

Neutrino masses arise at one loop (scotogenic mechanism), with the Casas-Ibarra parameterization (R=I₃) used throughout.

## What We Benchmark

### Tier 1 — Setup (UFO-gated)
- `t1_scoto_proc_card`: DM pair annihilation proc_card with ScotoInverseSeesaw_UFO
- `t1_scoto_param_card_BP{1,2,3}`: Param cards at each benchmark point

**Note:** Tier-1 tasks require the ScotoInverseSeesaw_UFO model. Under Plan-C UFO, entries are relocated to `tier1_scoto_blocked.yaml.disabled`. See `madgraph/README.md`.

### Tier 2 — Accuracy (closed-form)
- `t2_scoto_sigmav_BP2`: ⟨σv⟩ at BP2 (59 GeV, Higgs funnel) via Gondolo-Gelmini
- `t2_scoto_sigma_SI_BP3`: σ̄^SI at BP3 via NREFT chain
- `t2_scoto_BR_mueg_BP1`: B(μ→eγ) at BP1 via Casas-Ibarra Yukawa

### Tier 3 — Advanced identities
- `t3_scoto_Eq32_vs_Eq33_BP3`: Full vs simplified SD cross section ratio
- `t3_scoto_isospin_identity`: c4_p/c4_n ratio consistency
- `t3_scoto_casas_ibarra_round_trip`: CI round-trip at BP2

### MadDM: gated via generator
MadDM tasks (Ωh² and ⟨σv⟩ MadDM cross-check) are gated. Run:
```bash
python eval/2603.23040_scotogenic_inverse_seesaw/madgraph/generate_maddm_tasks.py
```
with `MADDM_PATH` and `MG5_AMC_PATH` set.

**Plan-C MadDM drop:** MadDM sample output could not be obtained during implementation (Step 0.5.3 triggered). MadDM tasks are dropped for this round.

## Running the harness on this paper today

**Tier-1 MG-setup tasks are disabled** (relocated to
`tier1_scoto_blocked.yaml.disabled`). Tier-2 and Tier-3 tasks still load and
run. Under `--runner claude`, tasks involving MG/MadDM observables will
correctly trigger the `BLOCKED_CORRECTLY` outcome because the
`ScotoInverseSeesaw_UFO` is unavailable. Under `--runner reference`, all tasks
pass via the closed-form Python oracle in `cross_sections/` and `models/`. Do
not interpret `BLOCKED_CORRECTLY` outcomes on this paper as a regression — they
are the expected signal until UFO-generation support lands.

## Figures-to-Equations Table

| Figure | Equation | Implementation |
|--------|----------|----------------|
| Figs. 3-5 | Eq. 6 (spectrum) | `models/cubic_spectrum.py` |
| Fig. 1 | Eq. 14 (neutrino mass) | `models/neutrino_mass.py` |
| — | Eq. 15 (Casas-Ibarra) | `models/neutrino_mass.py` |
| Eq. 16-17 | μ→eγ loop | `loop_functions/mueg_loops.py` |
| Fig. 2 | Eqs. 19a-b (invisible decays) | `cross_sections/decays.py` |
| — | Eq. 21 (Gondolo-Gelmini) | `cross_sections/thermal_average.py` |
| — | Eq. 22-24 (annihilation) | `cross_sections/annihilation.py` |
| — | Eqs. 26a-c (Wilson coefficients) | `cross_sections/si_nreft.py`, `sd_nreft.py` |
| — | Eqs. 29a-e (NREFT c_i) | `cross_sections/si_nreft.py`, `sd_nreft.py` |
| Fig. 4 | Eq. 30 (σ̄^SI) | `cross_sections/si_nreft.py` |
| Fig. 5 | Eqs. 32-33 (σ^SD) | `cross_sections/sd_nreft.py` |

## Out of Scope

- **ILC cutflow: dropped** (per brainstorm §0 S5). No ILC cards, no Eq. 36 significance.
- Full Boltzmann relic density solve (MadDM-only).
- Figure digitization tasks.

## Convention Sheet Pointer

See `cross_sections/CONVENTIONS.md` for the binding NREFT convention sheet.

## Benchmark Points

| BP | M_R [GeV] | μ_S [GeV] | M_N [GeV] | m_χ₁ [GeV] |
|----|-----------|-----------|-----------|------------|
| BP1 | 42.0 | 0.05 | 42.0 | 42.00 |
| BP2 | 59.0 | 0.05 | 59.0 | 59.00 |
| BP3 | 61.0 | 0.05 | 61.0 | 61.00 |

Scalar triplet: m_φ = (1000, 1200, 1400) GeV.

## Deviations from Plan

- NuFIT 6.0 (2024) used instead of NuFIT 5.2 (θ₂₃ and δ_CP deviate >1%).
- m₁ = 0.01 eV (paper) vs 1e-3 eV (plan).
- BR(μ→eγ) targets T5-T7 computed from code (~1e-31), not pre-specified (4.8e-14 was wrong).
- MadDM: Plan-C drop (sample output unobtainable).
- UFO: Plan-C (Day 0, no author UFO yet).

## Ship State

- All 20 pytest tests pass.
- Tier 1: UFO-blocked (Plan-C). Entries in `tier1_scoto_blocked.yaml.disabled`.
- Tier 2: 3 tasks pass on reference runner.
- Tier 3: 3 closed-form tasks pass on reference runner.
