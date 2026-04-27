# SARAH silent-failure gotchas

Reference catalog of SARAH's silent-failure modes and the ModelSpec patches
that resolve them. The `/lagrangian-builder` diagnostic-retry loop consults
this doc to map a blocker code (from `check_vertices.py`,
`check_mass_matrix.py`, `check_spectrum.py`) to a concrete spec patch,
applies it, and retries.

"Silent" here has a precise meaning. SARAH parses the Lagrangian, then
runs downstream passes — `PossibleTerms::NonSUSY`,
`CalcMixingsOfMatterFields`, vertex extraction — that can drop terms,
collapse matrices, or emit empty vertices *without raising an error and
often without a warning the pipeline can key off of*. The failure only
surfaces at the UFO / SPheno spectrum stage, by which point the causal
chain back to the offending spec field is non-obvious. That's what this
doc fixes: blocker-code → spec-patch, mechanical.

All blocker codes below are keys the three `check_*.py` scripts emit. A
patch recipe names the exact ModelSpec field to edit and the old → new
value. Cross-references anchor to `SARAH-4.15.3/Models/...` files
(line numbers match SARAH 4.15.3) and to the production-tested
singlet-doublet YAML at
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`.

---

## Naming: single-letter uppercase fields collide with SARAH internals

**Blocker codes:** `VERTICES_MISSING`, `MASS_MATRIX_DEGENERATE`,
`SPECTRUM_ZERO_NONZERO_PARAM`

**Symptom:** A declared Yukawa or mass term produces no UFO vertex, or
its mass-matrix entry comes back `OnlyZero`, or the SLHA spectrum has a
zero where the spec default was nonzero. The user sees a
Higgs-portal coupling go to zero at runtime even though the spec has a
nonzero default.

**Root cause:** SARAH reserves single-letter uppercase identifiers as
internal symbols — notably `S` (scalar generic), `N` (neutralino /
counter), `M` (mass generic). When a user-declared field shadows one of
these, `PossibleTerms::NonSUSY` silently drops any Lagrangian term
involving it during the term-classification pass. The term parses into
the model file but never reaches mass-matrix extraction or vertex
emission. No warning fires.

**Patch recipe:** Rename the field with an `F`-prefix (fermion) or
appropriate multi-letter tag. In `fermions[].name` / `scalars[].name`:

- `S` → `FS` (singlet Majorana fermion)
- `N` → `FN` or `PsiN`
- `M` → `FM` or `Mess` (messenger)

Also rename every reference in `lagrangian.mass_terms[].fields`,
`lagrangian.yukawa_terms[].fields`, and `ewsb.mixings[].weyls` to match.
Keep Weyl component names distinct from the outer field name (e.g.
outer `FS`, component `s0`) so `DEFINITION[EWSB][Phases]` and
`MatterSector` entries resolve unambiguously.

**Cross-reference:** `singlet_doublet.yaml:41-52` (comment block
documents the rename). PortalDM / SplitSUSY-MSSM / SDDM all use the
`F`-prefix convention. SARAH 4.15.3.

---

## Majorana masses must live in `LagHC` with `AddHC->True`

**Blocker codes:** `MASS_MATRIX_DEGENERATE`, `SPECTRUM_UNPHYSICAL`

**Symptom:** The neutralino / singlet Majorana mass matrix collapses to
`MassMatrix::OnlyZero` after `CalcMixingsOfMatterFields`. Downstream,
SPheno returns `NaN` or tachyonic masses for the Majorana sector.

**Root cause:** SARAH splits the Lagrangian into `LagNoHC` (no
hermitian-conjugate auto-addition) and `LagHC` (with `AddHC->True`).
For a Majorana bilinear `-1/2 MS FS.FS`, placing the term in `LagNoHC`
causes the mass-matrix extractor to miss the diagonal entry —
`CalcMixingsOfMatterFields` expects the HC pair for a Majorana self-
coupling and the `LagNoHC` form doesn't supply it. The entry silently
drops to zero.

**Patch recipe:** Set `hermitian_conjugate: true` on every Majorana
mass term:

```yaml
lagrangian:
  mass_terms:
    - {fields: [FS, FS], coefficient: MS, hermitian_conjugate: true}  # correct
    # NOT: - {fields: [FS, FS], coefficient: MS, hermitian_conjugate: false}
```

This is the default in ModelSpec v1 — only explicit `false` overrides
will trip it. Same rule for vectorlike Dirac bilinears paired through
SU(2) epsilon contractions (`PsiDu.PsiDd`).

**Cross-reference:**
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:54` (canonical
idiom: `- MG/2 FG.FG - MW/2 FW.FW` inside `LagHC`).
`singlet_doublet.yaml:76-87` (comment block documents the exact SARAH
behaviour when the term was erroneously placed in `LagNoHC`).

---

## Vectorlike SU(2) doublet + Majorana singlet: use two-left-Weyl (Hu/Hd) topology

**Blocker codes:** `MASS_MATRIX_DEGENERATE`, `VERTICES_MISSING`

**Symptom:** The neutralino mass matrix degenerates to `OnlyZero`, and
the Higgs-portal `Chi-Chi-h` vertex is missing from the UFO. The
charged Dirac sector either doesn't form or carries the wrong mass
eigenvalue.

**Root cause:** There are two ways to write a vectorlike SU(2) doublet
in SARAH:

1. **L + R Dirac topology** — one left-chiral doublet `PsiDL`, one
   right-chiral doublet `PsiDR`, with `conj[]` wrapping at the
   component level to form neutral combinations.
2. **Two-left-Weyl (Hu/Hd) topology** — two left-chiral doublets
   `PsiDu` (Y=+½), `PsiDd` (Y=-½), paired by a Dirac mass
   `MPsi PsiDu.PsiDd` through SU(2) epsilon contraction.

Only topology (2) composes correctly with a Majorana singlet mixing.
Topology (1)'s component-level `conj[]` wrapping causes
`CalcMixingsOfMatterFields` to silently degenerate the 3×3
neutral-Majorana block to `OnlyZero` and to drop the Higgs-portal
Yukawa vertex from UFO emission. SARAH's mixing-extractor treats the
`conj[]`-wrapped component as a distinct field for chirality
bookkeeping and the Majorana self-pairing never closes.

**Patch recipe:** Replace one Dirac doublet declaration with two
left-Weyl doublets:

```yaml
# DROP this:
# - {name: PsiDL, reps: {WB: 2, G: 1}, hypercharge: -0.5, chirality: left,  components: [PsiDL0, PsiDLm]}
# - {name: PsiDR, reps: {WB: 2, G: 1}, hypercharge: -0.5, chirality: right, components: [PsiDR0, PsiDRm]}

# ADD this:
fermions:
  - {name: PsiDd, reps: {WB: 2, G: 1}, hypercharge: -0.5, chirality: left, components: [PsiDd0, PsiDdm]}
  - {name: PsiDu, reps: {WB: 2, G: 1}, hypercharge:  0.5, chirality: left, components: [PsiDup, PsiDu0]}

lagrangian:
  mass_terms:
    - {fields: [PsiDu, PsiDd], coefficient: MPsi, hermitian_conjugate: true}
```

Component ordering matters: `PsiDd: (PsiDd0, PsiDdm)` matches SplitSUSY
`Hd: (FHd0, FHdm)`; `PsiDu: (PsiDup, PsiDu0)` matches
`Hu: (FHup, FHu0)`. Downstream `ewsb.mixings` refers to the bare
component names (no `conj[]`).

**Cross-reference:**
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:34-35` (doublet
declarations), `:54-55` (mass + Yukawa pattern), `:78-79` (neutral +
charged mixing entries). `singlet_doublet.yaml:14-18` (cycle-3
root-cause reference). `deviations.md §T15a` in the hep-ph-demo
archive for the original investigation.

---

## Missing discrete symmetry drops portal Yukawas via `PossibleTerms::NonSUSY`

**Blocker codes:** `VERTICES_MISSING`, `MASS_MATRIX_DEGENERATE`

**Symptom:** Higgs-portal Yukawas (`conj[H].FS.PsiDu`, `H.FS.PsiDd`)
parse into the Lagrangian but never appear in the UFO; the singlet
Majorana mass entry `MS FS.FS` is also silently dropped. The DM
candidate's mass eigenstate doesn't form.

**Root cause:** When a model has no declared `global_symmetries` entry,
`PossibleTerms::NonSUSY` runs an unrestricted classification that
applies SM-like heuristics to decide which terms are "physical". BSM
fields carrying no discrete charge get treated as SM-adjacent matter
and portal-style Yukawas (scalar · BSM-fermion · BSM-fermion) are
classified as redundant and silently dropped. The scanner emits no
warning — it just produces a smaller list of terms.

The presence of a `Z[2]` / `DMParity`-style global symmetry with
explicit `discrete_charges` tells `PossibleTerms::NonSUSY` that the
BSM fields are a distinct sector, and portal terms survive the scan.

**Patch recipe:** Add a `Z2` (or appropriate `Zn`) global symmetry with
per-field `discrete_charges`:

```yaml
global_symmetries:
  - {kind: Z2, name: DMParity}

fermions:
  - name: FS
    # ...
    discrete_charges: {DMParity: -1}
  - name: PsiDd
    # ...
    discrete_charges: {DMParity: -1}
  - name: PsiDu
    # ...
    discrete_charges: {DMParity: -1}
```

SM fields default to `DMParity: +1` — don't bother declaring them
explicitly unless you have a non-parity Z_n charge. The symmetry name
is free-form; `DMParity` / `RParity` / `DarkParity` are conventional.

**Cross-reference:**
`SARAH-4.15.3/Models/SM+VL/PortalDM/SM+VL-PortalDM.m:15`
(`Global[[1]] = {Z[2], DMParity}`),
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:14`
(`Global[[1]] = {Z[2], RParity}`). `singlet_doublet.yaml:25-33` for the
comment block tying this to observed behaviour.

---

## Two independent SU(2)×U(1) contractions for singlet-doublet Higgs portal

**Blocker codes:** `VERTICES_MISSING`, `SPECTRUM_ZERO_NONZERO_PARAM`

**Symptom:** The UFO has only one Higgs-portal Yukawa vertex where the
paper has two couplings (`y1`, `y2` or `y cosθ`, `y sinθ`). A
parameter scan over the mixing angle θ shows no dependence at all — one
of the two couplings is effectively zero everywhere.

**Root cause:** SU(2)×U(1) admits *two* independent gauge-invariant
contractions of (scalar doublet) · (Majorana singlet) ·
(vectorlike SU(2) doublet): one using `conj[H]` contracted with the
Y=+½ doublet slot, one using `H` contracted with the Y=-½ doublet
slot. These are not related by hermitian conjugation — each has its
own HC partner. The interview or paper may present a single "Yukawa
`y`" for pedagogical brevity, but the Lagrangian has two independent
coefficients.

Collapsing the two into one term in the ModelSpec — e.g. emitting only
`conj[H].FS.PsiDu` and relying on HC to generate the other — produces
a UFO with one vertex instead of two, and the "second" coupling
doesn't exist in parameter space.

**Patch recipe:** Enumerate both contractions explicitly in
`lagrangian.yukawa_terms`, with distinct coefficient names:

```yaml
lagrangian:
  yukawa_terms:
    - {fields: ["conj[H]", FS, PsiDu], coefficient: yh1, hermitian_conjugate: true}
    - {fields: [H,         FS, PsiDd], coefficient: yh2, hermitian_conjugate: true}
```

If the paper uses a single `y` with a mixing angle `θ`, map at the
demo/parameter-card layer: `(yh1, yh2) = (y cosθ, y sinθ)`. Don't
collapse at the spec layer — SARAH needs both coefficients present in
the Lagrangian to emit both vertices.

**Cross-reference:**
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:55`
(`- g1u/Sqrt[2] conj[H].FB.Hu - g1d/Sqrt[2] H.FB.Hd`).
`singlet_doublet.yaml:88-96` (yukawa_terms block with comment tying
`yh1`/`yh2` to Arcadi-Profumo Eq. 6).
`eval/2506.19062_wimps_blind_spots/models/singlet_doublet.py` —
`y1_y2_from_y_theta` for the demo-layer mapping.

---

## Charged Dirac sector: distinct names on LH and RH slots

**Blocker codes:** `VERTICES_MISSING`, `MASS_MATRIX_RANK_DEFICIENT`

**Symptom:** SARAH emits `Vertex::ChargeViolating` warnings (which the
pipeline doesn't treat as fatal). The Higgs-portal Yukawa vertex for
the charged Dirac fermion is suppressed or missing. The charged Dirac
mass matrix comes out rank-deficient — the physical charged fermion
mass is zero or much smaller than `MPsi`.

**Root cause:** For a vectorlike SU(2) doublet, the charged components
`PsiDdm` (from `PsiDd`, Q=-1, LH-slot) and `PsiDup` (from `PsiDu`,
Q=+1, LH-slot) pair to form a single physical charged Dirac fermion
with `FChiM -> {ChiM, conj[ChiP]}`. SARAH's mixing block expects the
LH-slot Weyl to map to one mass eigenstate (conventionally `ChiM`,
Q=-1) and the RH-slot Weyl to map to a *distinct* mass eigenstate
(`ChiP`, Q=+1) — they combine under conjugation.

The PortalDM quark convention uses the *same* mass eigenstate name on
both slots (treating them as one Dirac field directly). This triggers
SARAH's charge-assignment check: SARAH sees the LH slot with Q=-1 and
the RH slot with Q=+1 collapsed into a single label and fires
`Vertex::ChargeViolating`. The downstream vertex-emission pass drops
the Higgs-portal Yukawa for the charged fermion.

**Patch recipe:** In `ewsb.mixings`, give the LH and RH slots *distinct*
`mass_eigenstate` names:

```yaml
ewsb:
  mixings:
    - kind: fermion
      chirality: dirac
      lh_weyls: [PsiDdm]
      rh_weyls: [PsiDup]
      mass_eigenstate:     ChiM   # Q=-1, LH slot
      mass_eigenstate_rh:  ChiP   # Q=+1, RH slot (distinct name)
      left_mixing_matrix:  UM
      right_mixing_matrix: UP
```

Not `mass_eigenstate: ChiPM` on both, not `mass_eigenstate: Chi` with
charge inferred from context. The two names must be distinct even
though they describe one physical Dirac fermion — the conjugation
relation is applied at the UFO emission stage, not the mixing stage.

**Cross-reference:**
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:79`
(`{{{fWm, FHdm}, {fWp, FHup}}, {{Lm, UM}, {Lp, UP}}}` — note distinct
`Lm` / `Lp` eigenstate names). `singlet_doublet.yaml:117-137` for the
exact patched mixing block, and `:121-127` for the comment block
documenting what `Vertex::ChargeViolating` looks like in practice.

---

## Neutral Majorana mixing: bare component names, no `conj[]`

**Blocker codes:** `MASS_MATRIX_DEGENERATE`

**Symptom:** The 3×3 neutral Majorana mass matrix (singlet + two
doublet neutrals) has a zero row/column or collapses to `OnlyZero` in
`CalcMixingsOfMatterFields`, even after fixing the doublet topology
and the `LagHC` placement.

**Root cause:** When the `ewsb.mixings` block lists Weyl components
with `conj[]` wrapping (e.g. `weyls: [s0, PsiDd0, "conj[PsiDu0]"]`),
SARAH's mixing extractor treats the `conj[]`-wrapped component as
carrying opposite chirality from the mass-term entry, and the Majorana
self-pairing condition fails silently. The mass-matrix entry goes to
zero.

**Patch recipe:** List the bare component names only in
`ewsb.mixings[].weyls`. The Hu/Hd topology already places both
doublets in the left-Weyl basis; no conjugation wrapping is needed at
the mixing stage.

```yaml
ewsb:
  mixings:
    - kind: fermion
      chirality: majorana
      weyls: [s0, PsiDd0, PsiDu0]   # correct — bare names
      # NOT: [s0, PsiDd0, "conj[PsiDu0]"]
      mass_eigenstate: Chi
      mixing_matrix: ZN
```

**Cross-reference:**
`SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m:78`
(`{fB, FB0, FHd0, FHu0}` — all bare names).
`singlet_doublet.yaml:108-116` for the patched mixing block.

---

## Parameter defaults: zero defaults on dimensionful mass parameters

**Blocker codes:** `SPECTRUM_ZERO_NONZERO_PARAM`, `SPECTRUM_NAN`

**Symptom:** SPheno returns `NaN` or a rank-deficient spectrum. The
SLHA output has a zero entry in a block where the spec set a nonzero
default.

**Root cause:** SARAH's SPheno template initialises parameters from
the LesHouches input block. If a parameter's `default` in the ModelSpec
is zero (or missing, which maps to zero) *and* the generated input
card doesn't override it, the SPheno run starts with a zero mass in
the relevant mass matrix. Diagonalisation either returns zero
eigenvalues (and the spectrum blocks report zero where the spec
"intended" nonzero) or fails numerically with `NaN`.

**Patch recipe:** Set physically sensible nonzero `default` values on
every dimensionful parameter in `parameters[]`. For Majorana and Dirac
mass parameters, a few hundred GeV is a safe default. For
dimensionless Yukawa couplings, `0.1`–`0.3` typically.

```yaml
parameters:
  - {name: MS,   real: true, positive: false, default: 300.0}   # not 0.0
  - {name: MPsi, real: true, positive: true,  default: 500.0}
  - {name: yh1,  real: true, positive: false, default: 0.3}
  - {name: yh2,  real: true, positive: false, default: 0.3}
```

Also ensure the parameter is wired into the generated LesHouches input
block — validate with `validate_spec.py` before the SPheno run. If
the `SPECTRUM_ZERO_NONZERO_PARAM` blocker fires with a parameter that
has a nonzero default, the template wiring is the problem, not the
default.

**Cross-reference:** `singlet_doublet.yaml:99-103` (parameter defaults
block). `/spheno-build` §"PhaseFS LOW-boundary initialisation" for
cases where a nonzero default still produces a zero SLHA entry.

---

## Gauge group conventions: SM triple comes pre-filled

**Blocker codes:** `VERTICES_MISSING` (wrong hypercharge normalisation),
`SPECTRUM_NAN`

**Symptom:** Hypercharge-dependent vertices emit with the wrong
numerical coefficient, or the `g1` running produces `NaN` in SPheno.

**Root cause:** The ModelSpec SM triple uses the SARAH-idiomatic
GUT normalisation (`g1 = sqrt(5/3) g_Y`) and hypercharge in units of
`Y = Q - T_3`. Users coming from a physics paper that uses the
non-GUT normalisation will sometimes override `g1` or the hypercharges
and produce off-by-`sqrt(5/3)` vertex coefficients. SARAH doesn't
catch the mismatch — it just computes vertices with whatever
normalisation the spec declared.

**Patch recipe:** Keep the pre-filled SM triple:

```yaml
gauge_groups:
  - {symbol: B,  group: U1,  kind: hypercharge, coupling: g1, gauge_boson: B0, gaugino: null}
  - {symbol: WB, group: SU2, kind: left,        coupling: g2, gauge_boson: W,  gaugino: null}
  - {symbol: G,  group: SU3, kind: color,       coupling: g3, gauge_boson: g,  gaugino: null}
```

Declare hypercharges in the GUT-normalised `Y = Q - T_3` convention —
the doublet `PsiDd` has `hypercharge: -0.5`, not `-1` (SU(5)-style)
or `-sqrt(3/5) * 0.5`. If the paper uses a different normalisation,
convert at spec-writing time, not at SARAH-runtime.

**Cross-reference:** `singlet_doublet.yaml:35-38`.

---

## Summary: blocker code → gotcha map

| Blocker code                    | Relevant gotchas |
|---------------------------------|------------------|
| `VERTICES_MISSING`              | Naming, Doublet topology, Missing discrete symmetry, Two contractions, Charged Dirac names, Gauge conventions |
| `VERTICES_UNEXPECTED`           | (Usually indicates an over-permissive discrete symmetry — check `discrete_charges` on BSM fields; a symmetry meant to forbid a term may not be assigned to every BSM field it should cover.) |
| `MASS_MATRIX_DEGENERATE`        | Majorana `LagHC`, Doublet topology, Missing discrete symmetry, Neutral Majorana mixing |
| `MASS_MATRIX_RANK_DEFICIENT`    | Charged Dirac names |
| `SPECTRUM_NAN`                  | Parameter defaults, Gauge conventions, Majorana `LagHC` |
| `SPECTRUM_UNPHYSICAL`           | Majorana `LagHC` |
| `SPECTRUM_ZERO_NONZERO_PARAM`   | Naming, Two contractions, Parameter defaults |

When a blocker fires and none of the patches above resolves it, the
failure mode is novel — surface to the user and add an entry here
(include the blocker `context` payload, the minimal repro spec diff,
and a SARAH file:line anchor where possible).
