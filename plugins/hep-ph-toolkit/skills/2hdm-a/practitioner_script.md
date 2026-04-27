# Practitioner script — 2HDM+a

Scripted answers for the `/lagrangian-builder` interview, played back by
the `/demo` → `2hdm-a` flow in place of live user input. Written in the
voice of a physicist riffing at a whiteboard.

Q1 and Q2 are self-contained. Q3 and Q4 are **deltas against Claude's
drafts** — Q3 edits Claude's enumerated Lagrangian, Q4 edits Claude's
detected mixing sectors.

Tier 2: the SM Higgs sector is replaced, so Q4 needs every scalar
rotation explicitly.

---

## Q1 — What are you studying?

> 2HDM + pseudoscalar mediator from Arcadi & Profumo,
> arXiv:2506.19062 §III. Two Higgs doublets plus a CP-odd
> gauge-singlet `a` mediating to a Dirac DM fermion. Tree-level SI is
> CP-forbidden (pseudoscalar mediator), so DD is loop-dominated;
> relic comes from the s-channel `a`-resonance. For this run I want
> relic density.

---

## Q2 — What new fields and gauge groups?

> SM gauge groups, unchanged. SM Higgs sector replaced — flag that.
>
> Scalars:
>
> 1. `H1` — SU(2)_L doublet, Y = +½
> 2. `H2` — SU(2)_L doublet, Y = +½
> 3. `a` — real gauge singlet, CP-odd
>
> Fermions (Dirac DM):
>
> 1. `chiL` — SM-singlet left Weyl, Y = 0
> 2. `chiR` — SM-singlet right Weyl, Y = 0

---

## Q3 — Confirm the Lagrangian

*(deltas against Claude's enumerated draft)*

> Edits:
>
> 1. **Yukawa structure is Type-II.** Up-type quarks couple to `H2`;
>    down-types and charged leptons to `H1`. Delete the wrong-doublet
>    halves of any Type-I / Type-III Yukawas you drafted.
> 2. **The only `chi` coupling is `a · chibar·chi`.** Delete any
>    `H1·chi·chi` / `H2·chi·chi` — `chi` is a total SM singlet, those
>    break hypercharge.
> 3. **Softly-broken Z2.** Call whatever symmetry you infer from the
>    Type-II Yukawa structure `Z2soft`. The `m12²` term
>    (`H1†·H2 + h.c.`) softly breaks it — keep that term; drop any
>    dim-4 Z2-odd quartics.
> 4. **Parameter names:** `Mchi` for the DM Dirac mass, `gchi` for
>    `a·chibar·chi`, `lamP` for the `H1·H2·a` portal.

---

## Q4 — Confirm post-EWSB mixings

*(deltas against Claude's detected mixing sectors)*

> Higgs sector fully replaced, so every rotation needs an entry.
> Three mixings:
>
> - CP-even neutral 2×2: matrix `ZH`, eigenstates `h` (SM-like) and
>   `H` (heavy).
> - CP-odd neutral 3×3: matrix `ZA`, eigenstates `G0`, `A`, `aphys`
>   (the DM mediator). Two angles — `β` separates the Goldstone,
>   `θ_a` mixes `A` with the singlet.
> - Charged 2×2: matrix `ZP`, eigenstates `Gp` and `Hp`.
>
> VEVs: `v1 = v cos β`, `v2 = v sin β`, `v = 246 GeV`; `a` stays at
> zero. No fermion mixing — `chi` is a Dirac singlet.

---

## Reference

Expected ModelSpec YAML:
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/2hdm_a.yaml`.
The interview should produce a result consistent with Type-II Yukawas,
softly-broken Z2, corrected `conj[H1]·H2·a` portal contraction, and
three rotation matrices.
