# Interview flow: eliciting a ModelSpec from the user

This document defines the interview Claude follows when a user wants to build
a new BSM model interactively (SKILL.md path (a)). The shape is **four
open-ended physics questions** — not a checklist. Claude does the group-theory
enumeration and drafts the Lagrangian; the physicist's job is to **edit**, not
to enumerate.

The interview produces a draft ModelSpec YAML for `validate_spec.py`.
Iteration is expected: the pipeline has diagnostic checkpoints at every
downstream stage that feed silent failures back here for revision (see
"Iteration expectations" at the bottom).

---

## 0. Preamble (say this before Q1)

Before asking anything, set expectations out loud:

> I'll author a ModelSpec for your model and run it through SARAH → SPheno →
> (downstream tool). This pipeline has silent failure modes — SARAH can drop
> vertices it thinks are redundant, SPheno can produce a degenerate spectrum,
> observables can come out physically impossible. I have diagnostic checks
> at each stage that catch these, but we may still need 2–3 passes to
> converge on a correct spec. Is that OK?

Only proceed on an affirmative answer.

### Scope tier (announce before Q1)

The ModelSpec DSL is expressive for a narrow band of BSM physics and silently
inadequate outside it. Place the model in one of three tiers and tell the
user which tier you landed on before Q1.

- **Tier 1 — Claude authors end-to-end.** SM gauge group unmodified, SM
  Higgs sector untouched, adds new fermion/scalar multiplets only. No new
  confining dynamics, no SUSY. Examples: singlet-doublet DM,
  scalar-singlet Higgs portal, dark photon with kinetic mixing,
  vector-like quark partners. Calibrate against
  `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`
  — the canonical tier-1 spec; read it end-to-end before drafting a new
  one to internalise what a cheap, complete spec looks like.
- **Tier 2 — physics review needed.** Replaces or extends the SM Higgs
  sector (2HDM, IDM, triplet-Higgs, Georgi-Machacek). Claude drafts but
  the user must confirm mixing structure, VEV parameterisation, and
  Yukawa type against the paper. If the user can't answer these from
  the paper, stop and ask them to bring a reviewer — do not guess.
- **Tier 3 — specialist scope.** New confining gauge group, SUSY-scale
  RGE, multi-scale VEV structure. The DSL can declare fields but can't
  derive the spectrum. Help the user scope the required analytic module
  first; come back to the interview once it exists. An absent analytic
  module surfaces later as `/spheno-build`'s `ANALYTIC_MODULE_MISSING`.

One-line format: `Scope assessment: tier <N> (<short reason>). Expected
effort: <time>. Proceed?`

---

## The four questions

### Q1 — What are you studying?

> Describe the physics. A paper citation is ideal; otherwise a free
> description of the model and what observable or regime you care about.

Claude extracts from the answer:
- `name` (lowercase, underscores only; `^[a-z][a-z0-9_]{1,30}$`)
- `claim_source` (paper citation or user description — provenance only)
- a rough sketch — DM model? new Higgs sector? gauge extension? — that
  informs defaults at Q3–Q4.

### Q2 — What new fields and gauge groups?

> List the new fields (fermions and scalars) and gauge groups. For each
> field, give just the name, representation under each gauge group, and
> hypercharge. Don't worry yet about kinetic terms, discrete symmetries,
> or interactions.

Pure bookkeeping. Populates:
- `gauge_groups[]` — the SM triple is pre-filled unless the user replaces
  or extends it (see `references/sarah-gotchas.md` §Gauge group
  conventions).
- `fermions[]` with `{name, reps, hypercharge, generations, chirality}`.
- `scalars[]` with the same shape; pre-populate the SM Higgs doublet if
  the user plans to keep it.

Claude silently handles implementation-layer naming conventions. If the
user proposes a name that will collide with a SARAH internal symbol
(single-letter uppercase like `S`, `N`, `M`; names that shadow SARAH
functions), Claude picks a safer name with a brief parenthetical note.
Reserved-name rules live in `references/sarah-gotchas.md` §Naming.

### Q3 — Confirm the Lagrangian

Claude now enumerates **every renormalizable invariant allowed by the
declared gauge symmetries** — mass bilinears, Yukawa couplings,
scalar-potential terms up to dim-4 — and presents the result as a YAML
block:

```yaml
lagrangian:
  mass_terms:
    # every fermion bilinear with trivial rep under all gauge groups
    ...
  yukawa_terms:
    # every scalar-fermion-fermion contraction; do not collapse
    # independent SU(N) × U(1) contractions into one
    ...
  scalar_potential:
    # every quadratic + quartic invariant
    ...
```

Then asks:

> Here's my best guess at the renormalizable Lagrangian given those
> fields. Please edit — delete terms the paper forbids, confirm the ones
> it keeps, fix parameter names. If the paper forbids some terms because
> of a discrete symmetry, just delete them and tell me the symmetry name;
> I'll add the bookkeeping.

**Group-theory notes for Claude:**
- Enumerate only dim ≤ 4 operators. Dim-5+ is outside ModelSpec v1 scope
  — emit `MODELSPEC_FEATURE_UNSUPPORTED` if the user requests one.
- For each scalar-fermion-fermion Yukawa, enumerate **all** independent
  SU(N) × U(1) contractions. Do not collapse contractions the paper may
  keep separate (e.g. `conj[H]·FS·PsiDu` and `H·FS·PsiDd` are two
  independent contractions, not one; enumerate both).
- Default `hermitian_conjugate: true` on mass terms and Yukawas. Majorana
  mass terms go in `LagHC` with `AddHC->True`; `LagNoHC` causes SARAH to
  silently drop the mass matrix entry (see `references/sarah-gotchas.md`
  §Majorana masses).
- If the user deletes a pattern of terms consistent with a discrete
  symmetry acting on the BSM fields, **infer** the symmetry and propose
  adding `global_symmetries: [{kind: Z2, name: <name>}]` plus
  `discrete_charges` on the affected fields. Confirm with the user
  before writing.

### Q4 — Confirm post-EWSB mixings

> [!WARNING]
> **Reserved mixing-matrix names** — Before renaming any proposed matrix,
> check that the name is not a single-capital-letter Mathematica built-in
> (`N`, `I`, `E`, `D`, `C`, `O`). Using `N` as a matrix name triggers
> cascading `N::precbd` errors in SARAH that silently drop vertices and
> break SPheno compilation — with exit code 0, so no fatal signal fires.
> Prefer the `Z`-prefix convention (e.g. `ZN`, `ZC`) which matches SLHA
> block conventions and avoids all known collisions. See
> `singlet-doublet/SKILL.md` § Known limitations for a worked example.

Claude scans field content for any group of fields whose quantum numbers
add to the trivial rep of the unbroken gauge group after every declared
VEV is taken. For each such group, Claude proposes an `ewsb.mixings[]`
entry with a sensible matrix name, Weyl/component list, and
mass-eigenstate name. Then asks:

> Here are the mass eigenstates I detected post-EWSB. Confirm the
> rotations — fix matrix names and eigenstate names to match the paper.
> If I missed a mixing, add it.

**Notes for Claude:**
- A mixable field group can be **neutral or charged** — enumerate both.
  A Majorana singlet + vectorlike SU(2) doublet gives one neutral
  Majorana mixing *and* one charged Dirac mixing; propose both entries.
- For vectorlike/Dirac SU(2) doublets whose neutral components will mix
  with a Majorana singlet, use the two-left-Weyl (Hu/Hd) topology — see
  `references/sarah-gotchas.md` §Doublet topology. This is an
  implementation-layer choice; don't surface it as a user question.
- If `sm_overrides.higgs_sector: true`, every sector of the scalar
  mixing (CP-even, CP-odd, charged) needs an explicit entry — don't
  skip.

---

## Drafting the YAML

After Q4, present the full ModelSpec YAML and ask:

> Does this look right? I'll validate and start the pipeline on your go.

Run:

```bash
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/validate_spec.py \
    /tmp/<name>_spec.yaml
```

On failure, surface the error, fix in place, re-validate. Common fixes:
- Duplicate field name → rename
- Unknown gauge group symbol in `reps` → cross-check Q2 answers
- Non-rational hypercharge → use `"1/3"` not `0.33333`
- Empty `outputs` → add `ufo` and/or `spheno`

---

## Iteration expectations (post-validation)

Validation passing ≠ physics correct. The pipeline has diagnostic
checkpoints downstream; if any fires, come back here with a specific
patch:

| Checkpoint | Triggers a revision of |
|---|---|
| `check_vertices.py` (post SARAH) | Q3 — missing term, wrong contraction, or an incorrect discrete-symmetry inference |
| `check_mass_matrix.py` (post SARAH) | Q4 — missing or misnamed mixing |
| `check_spectrum.py` (post SPheno) | Q3, or parameter defaults set at Q2 |
| Observable-range check (post downstream tool) | Any of the above |

When a checkpoint fires, consult `references/sarah-gotchas.md` for
known failure-mode → patch mappings and attempt the patch automatically.
Surface to the user only if the patch doesn't resolve the issue or the
failure mode is novel (add it to the gotchas doc in that case).

---

## Schema references

- ModelSpec v3 schema: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`
- ModelSpec v3 SM template: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml`
- ModelSpec v3 reference specs: `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Implementation-layer failure modes: `references/sarah-gotchas.md`
- Per-model v3 reference specs (read for calibration, don't copy blindly):
  `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/`
