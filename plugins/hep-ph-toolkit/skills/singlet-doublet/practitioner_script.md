# Practitioner script — Singlet-Doublet

Scripted answers for the `/lagrangian-builder` interview, played back by
the `/demo` → `singlet-doublet` flow in place of live user input. Written
in the voice of a physicist riffing at a whiteboard — this is roughly
what a practitioner familiar with Arcadi & Profumo
(arXiv:2506.19062 §II) would say if asked the four interview questions
cold.

Q1 and Q2 are self-contained: the physicist describes the physics and
the field content. Q3 and Q4 are **deltas against Claude's drafts** —
Q3 edits Claude's enumerated Lagrangian, Q4 edits Claude's detected
mixing sectors. Claude reconciles each delta with its own enumeration
to produce the final YAML.

---

## Q1 — What are you studying?

> Singlet-doublet fermion DM from Arcadi & Profumo, arXiv:2506.19062 §II.
> The paper's whole point is the tree-level SI blind spot — the singlet
> and doublet components interfere destructively and the induced
> Higgs–DM coupling goes to zero along a specific mass-eigenstate locus.
> For this run I just want relic density

---

## Q2 — What new fields and gauge groups?

> SM gauge groups, unchanged. Two new fermions:
>
> 1. A gauge-singlet Majorana fermion. Call it the singlet
> 2. A vectorlike SU(2)_L doublet with Y = ±½

---

## Q3 — Confirm the Lagrangian

*(deltas against Claude's enumerated draft)*

> A few edits:
>
> 1. **Keep both Yukawa contractions.** The paper uses them both —
>    name the couplings `yh1` and `yh2`.
> 2. **Delete any Yukawa coupling the BSM fermions to SM fermions.**
>    The DM candidate has to be stable; call whatever symmetry you
>    infer from those deletions `DMParity`.
> 3. **Parameter names:** `MS` for the singlet mass, `MPsi` for the
>    doublet mass.
> 4. **Drop any extra scalar-potential terms you drafted.** We're not
>    touching the SM Higgs sector.

---

## Q4 — Confirm post-EWSB mixings

*(deltas against Claude's detected mixing sectors)*

> Both sectors look right. Renames:
>
> - Neutral Majorana 3×3: matrix `ZN`, eigenstates `Chi1`, `Chi2`,
>   `Chi3` (ascending mass; `Chi1` is the DM).
> - Charged Dirac: left matrix `UM`, right matrix `UP`, eigenstates
>   `ChiM` (Q = −1) and `ChiP` (Q = +1).
>
> No scalar mixing.

---

## Reference

Expected ModelSpec YAML (v3 reference spec):
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`.
The interview should produce something physics-equivalent; field names,
parameter names, and matrix names should match. If they don't, the
diagnostic checkpoints in `/lagrangian-builder` will catch the drift.
