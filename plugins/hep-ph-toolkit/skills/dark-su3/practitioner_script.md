# Practitioner script — Dark SU(3)

Scripted answers for the `/lagrangian-builder` interview, played back by
the `/demo` → `dark-su3` flow in place of live user input. Written in
the voice of a physicist riffing at a whiteboard.

Q1 and Q2 are self-contained. Q3 and Q4 are **deltas against Claude's
drafts** — Q3 edits Claude's enumerated Lagrangian, Q4 edits Claude's
detected mixing sectors.

The model is SU(3)_D → SU(2)_D Higgsing (arXiv:2506.19062 §IV,
Eqs. 26-29). A dark Higgs doublet in the SU(3)_D fundamental acquires a
VEV, producing the vector DM candidate `V` (3 massive dark gauge bosons)
and the pseudoscalar DM candidate `Psi` (CP-odd component of the dark
Higgs doublet). The analytic backend `analytic_models.dark_su3` is used
for observables — SARAH/MG5 do not apply to this model.

---

## Q1 — What are you studying?

> Dark SU(3) gauge model from Arcadi & Profumo, arXiv:2506.19062 §IV.
> The dark sector is SU(3)_D broken to SU(2)_D by a dark Higgs doublet
> in the fundamental that gets a VEV v_D. DM candidates are the three
> degenerate massive dark gauge bosons `V` (vector, tree-level SI via
> Higgs portal) and the pseudoscalar `Psi` from the CP-odd component of
> the dark Higgs doublet (exact parameter-independent SI blind spot,
> Eq. 29). Two-component DM; paper uses micrOMEGAs. I want relic density.
> The analytic module handles observables — no UV fermions, no SARAH build.

---

## Q2 — What new fields and gauge groups?

> SM triple stays. Add one gauge group:
>
> - `GD` — SU(3)_D, dark, broken to SU(2)_D at scale v_D.
>
> Scalars — one dark Higgs doublet in the SU(3)_D fundamental:
>
> 1. `PhiD` — complex scalar, `GD = 3`, Y = 0; acquires VEV v_D.
>
> No UV fermions. After breaking:
>   - 5 broken generators → 5 massive dark gauge bosons; 3 degenerate
>     form the vector DM triplet `V` with `m_V = g_tilde * v_D / 2`.
>   - 3 unbroken generators → 3 massless dark gauge bosons (unbroken
>     SU(2)_D sector; confined or massless, not DM).
>   - Scalar mass eigenstates: `H_1` (SM-like, 125 GeV) and `H_2` (dark
>     Higgs), mixed by angle theta.
>   - CP-odd component of `PhiD` → dark pseudoscalar `Psi` with
>     `m_Psi = g_tilde * v_D / (2 sqrt(2))`.

---

## Q3 — Confirm the Lagrangian

*(deltas against Claude's enumerated draft)*

> Minimal dark-Higgs Lagrangian. Edits:
>
> 1. **Dark Higgs kinetic + potential.** Keep `|D_mu PhiD|^2` and the
>    dark Higgs potential `V(PhiD) = -mu_D^2 |PhiD|^2 + lambda_D |PhiD|^4`.
>    The VEV is `v_D = sqrt(mu_D^2 / lambda_D)`.
> 2. **Higgs portal.** Keep `lambda_P |H|^2 |PhiD|^2`. This is the
>    only renormalizable SM-dark coupling and produces the H_1/H_2 mixing.
> 3. **Delete any UV fermion mass terms.** No dark quarks in this model —
>    the DM spectrum comes entirely from the Higgsed gauge sector.
> 4. **Register the five scan parameters:** `g_tilde`, `sin_theta`,
>    `m_H2`, `m_V`, `m_Psi` — these are the inputs consumed by the
>    analytic module (not derived from v_D explicitly at the spec level).

---

## Q4 — Confirm post-EWSB mixings

*(deltas against Claude's detected mixing sectors)*

> One physical mixing sector: H_1 / H_2 (2x2 real rotation by angle
> theta). The mixing matrix is:
>
>   H_1 =  cos(theta) phi_SM - sin(theta) phi_dark
>   H_2 =  sin(theta) phi_SM + cos(theta) phi_dark
>
> The relative minus sign on H_1's dark component is what produces the
> exact Psi SI blind spot (Eq. 29). If Claude detects any other mixing
> sectors (e.g., a vector mixing or a gauge-kinetic mixing), delete them —
> there is no kinetic mixing in this model at the renormalizable level.

---

## Reference

Expected ModelSpec YAML:
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/dark_su3.yaml`. The analytic
module is `analytic_models.dark_su3`; backend flag `analytic_only: true`
signals that SARAH/MG5 emission is blocked (MG5 dark-color wall; see
`demo_output/dark-su3/fix_loop/POST_MORTEM.md` §"MG5 dark-color is a wall").
