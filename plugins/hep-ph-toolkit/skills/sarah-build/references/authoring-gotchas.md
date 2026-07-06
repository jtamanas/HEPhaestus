# Gotchas — SARAH-idiom discrepancies

Model-authoring traps that SARAH silently tolerates: it accepts a
structurally-valid Lagrangian, `CheckModel[]` passes, UFO/SPheno emission
completes — but a vertex drops out or a mass matrix collapses to `OnlyZero`.
These are spec/template-level traps, distinct from the wrapper-level
infrastructure workarounds in [`sarah-workarounds.md`](sarah-workarounds.md).
Cite the reference models when writing new specs.

Six patterns follow. `/sarah-build`'s SKILL.md carries the one-line index; this
file is the full reproduction and fix for each.

## 1. Vectorlike fermion doublet — use two left-Weyl doublets, not a Dirac pair

**Reference:** `SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m` lines
34–35, 54–55, 78–79. SARAH's `CalcMixingsOfMatterFields` extracts mass
matrices and vertex couplings by pattern-matching bilinear and trilinear
coefficients in the Lagrangian. Component-level `conj[...]` wrapping on a
right-handed-style FermionFields declaration breaks the match silently:
the model loads, `CheckModel[]` passes, UFO emission completes — but the
neutralino mass matrix degenerates to `OnlyZero` and Higgs-portal Yukawa
vertices drop out of the UFO. Declare vectorlike doublets as two separate
left-Weyl FermionFields with opposite hypercharge (the "Hu/Hd" pattern):

```yaml
fermions:
  - name: PsiDd              # matches SplitSUSY Hd
    reps: {WB: 2, G: 1}
    hypercharge: -0.5
    chirality: left
    components: [PsiDd0, PsiDdm]
  - name: PsiDu              # matches SplitSUSY Hu
    reps: {WB: 2, G: 1}
    hypercharge: 0.5
    chirality: left
    components: [PsiDup, PsiDu0]
```

The singlet-doublet-Higgs Yukawa term `yh H.PsiDL.S` (one contraction)
becomes TWO terms `yh1 conj[H].S.PsiDu + yh2 H.S.PsiDd` (both
SU(2)×U(1)-invariant contractions; SplitSUSY-MSSM.m:55's `g1u/g1d` split).
A single-term Yukawa covers only half of the gauge-invariant couplings and
SARAH's Lagrangian-scanner may refuse to canonicalise the result.

## 2. Majorana mass terms live in LagHC, not LagNoHC

**Reference:** SplitSUSY-MSSM.m:54 — Majorana gaugino masses `- MG/2 FG.FG
- MW/2 FW.FW - MB/2 FB.FB` appear inside `LagHC` (with `AddHC -> True`),
NOT inside `LagNoHC` with a pre-applied `-1/2` coefficient. Physically the
two forms are equivalent (hermitian-conjugate of a Majorana mass is the
same term), but SARAH's mass-matrix extractor only picks up the LagHC
placement. The generator classifies singlet Majorana mass terms
`{fields: [S, S], hermitian_conjugate: true}` into LagHC automatically;
the `1/2` coefficient is prepended by `_format_hc_term` so the rendered
output matches SplitSUSY convention byte-for-byte.

## 3. Dirac charged sectors need distinct LH/RH mass-eigenstate names

**Reference:** SplitSUSY-MSSM.m:79 — the charged-chargino mixing block
`{{{fWm, FHdm}, {fWp, FHup}}, {{Lm,UM}, {Lp,UP}}}` uses TWO distinct mass
eigenstates (`Lm`, Q=-1; `Lp`, Q=+1). Using the same ME name on both
slots (the PortalDM SM-quark-pair convention `{{DL,Vd}, {DR,Ud}}`) causes
SARAH's charge-assignment pass to emit `Vertex::ChargeViolating` warnings
and suppresses charged-sector vertex emission. Declare the RH-side
explicitly via the optional `mass_eigenstate_rh` field in
`ewsb.mixings[].kind: fermion, chirality: dirac` entries:

```yaml
- kind: fermion
  chirality: dirac
  lh_weyls: [PsiDdm]          # Q=-1
  rh_weyls: [PsiDup]          # Q=+1 (bare LH Weyl, NO conj[])
  mass_eigenstate:    ChiM    # LH-slot ME, Q=-1
  mass_eigenstate_rh: ChiP    # RH-slot ME, Q=+1
  left_mixing_matrix:  UM
  right_mixing_matrix: UP
```

The DiracSpinor alias in `DEFINITION[EWSB][DiracSpinors]` becomes
`FChiM -> {ChiM, conj[ChiP]}` (parallels SplitSUSY's
`Cha -> {Lm, conj[Lp]}` at line 96).

## 4. BSM matter fields must use F-prefixed (not single-letter) names

**Reference:** `SARAH-4.15.3/Models/SM+VL/PortalDM/SM+VL-PortalDM.m` lines
33–34 (`PSIL`, `PSIR`), `SARAH-4.15.3/Models/SplitSUSY/MSSM/SplitSUSY-MSSM.m`
lines 30–35 (`FG`, `FW`, `FB`, `Hu`, `Hd`), `SARAH-4.15.3/Models/SplitSUSY/NMSSM/SplitSUSY-NMSSM.m`
line 38 (`Fs` singlet with component `fS`). Do NOT use single-letter names like `S`
for BSM matter fields — they collide with SARAH-internal symbols during
`PossibleTerms::NonSUSY` canonicalization. The failure mode is silent:
Lagrangian terms parse correctly (SARAH's "adding: ..." log line shows
them), discrete-symmetry filtering accepts them, but the canonicalizer
drops them from the vertex/mass-matrix extractor and `PossibleTerms::NonSUSY`
still lists them as "not present in the potential". Use F-prefixed names
(`FS`, `FPsi`, `FChi`, `FN`, etc.) for all BSM fermions.

## 5. `DEFINITION[GaugeES][DiracSpinors]` is often a workaround, not a fix

It's not in the stock SARAH reference models for most physics classes
(SplitSUSY-MSSM/MSSM ships without it; PortalDM.m has it for a different
reason). If you're reaching for it to silence `Part::partw` errors in
superpotential checks, suspect instead that the MatterSector has `conj[]`
embedded mid-expression (symptom of gotcha #1 above). Fix the Weyl
formulation first; only add the GaugeES DiracSpinor block when a reference
model for the same physics class uses it.

## 6. Rank-1 Dirac sub-blocks and silent parameter degradation

**Reference:** `scripts/sections/parameters.py:155-171`,
`scripts/render_templates.py:289-302`. Two already-guarded paths cause
silent degradation when a Dirac-fermion sub-block is rank-1 (one LH Weyl
and one RH Weyl, nominal 1×1 left/right mixing matrices). Either path
emits a UFO and SPheno tree that look syntactically plausible but have
`Param.$Failed` in place of a mass or a `None` placeholder in place of a
particle name.

**Trigger A — missing `LesHouches` metadata on a BSM parameter.** SARAH's
`CheckModelFiles` pass requires every BSM symbol referenced from
`<Name>.m` (mass-squared parameters, couplings, Yukawas, mixing matrices,
phases — anything that isn't a SARAH built-in like `g1/g2/g3/Yu/Yd/Ye`)
to carry a `LesHouches` block in `parameters.m`. In v3 ModelSpec YAML
this means a `les_houches:` field on every BSM parameter entry — either
`[BLOCKNAME, INDEX]` for indexed scalars (`[BSMPARAMS, 1]`, `[PHASES, 1]`)
or a bare block name for matrices (`ZHMIX`, `YUKAWAU`). When it's
missing, the log contains:

```
CheckModelFiles::MissingParameter: {ZChi, ZChiML, ZChiMR, PhaseS, ...}
CheckModelFiles::MissingOutputName: ...
```

and downstream UFO / SPheno emission silently substitutes
`Param.$Failed` for the affected masses and couplings. Examples in v3
specs: `_shared/modelspec_v3/specs/singlet_doublet.yaml` (BSM scalars
under `[BSMPARAMS, N]`, mixings as `ZNMIX`/`UMMIX`/`UPMIX`, phase as
`[PHASES, 1]`); `_shared/modelspec_v3/specs/2hdm_a.yaml` (the full
2HDM scalar potential indexed under `[BSMPARAMS, 1..9]`, Yukawas as
`YUKAWAU`/`YUKAWAD`/`YUKAWAE`). SM-style parameters (`g1`, `g2`, `g3`,
`AlphaS`, `eEM`, `Gf`, `aEWinv`, `ThetaW`, `ZZ`, `ZW`, `Vu/Vd/Uu/Ud/Ve/Ue`,
`Yu/Yd/Ye`) have built-in SARAH defaults and don't need `les_houches:`
in the v3 spec.

The renderer defends against the older mixing/phase failure path via
`_render_mixing_matrix_entry` and `_render_phase_entry` in
`sections/parameters.py`; the broader scalar-parameter path is enforced
by the `les_houches:` field threading through the v3 parameters renderer.
A spec that bypasses either helper re-opens the path.

**Trigger B — braced singleton `{S}` in a LH / Majorana Weyl
declaration.** `render_templates.py` emits a bare symbol (`f.name`) for
`chirality ∈ {left, majorana}` with a single component, because a
braced `{S}` is parsed by SARAH as a rank-1 tensor and raises
`Part::partd: Part specification None[[1]]` at CheckModel time. The
failure is not silent when the guard is live (CheckModel aborts), but
a spec that re-introduces the brace pattern via a new chirality kind
or a template edit will reproduce it.

**Trigger C — BSM particle entry with mismatched `pdg` length or
missing `mass`/`width`.** When a `particles.ewsb[]` entry is the output
of a non-trivial mixing (e.g. ZA mixes Ah1+Ah2+a0 → 3 mass eigenstates),
the entry's `pdg:` list length must equal the number of mass
eigenstates. SARAH indexes into the PDG list during emission; a too-short
list produces `Part::partw: Part 3 of {36, 0} does not exist` and the
particle's mass / width name evaluates to `None`, cascading into
`StringJoin::string: ... M<>None` and `ToExpression::notstrbox: ...
W<>None` errors and finally `Param.$Failed` substitutions in the UFO.
For the same reason, BSM mass-eigenstate particle entries must declare
`mass: LesHouches` and `width: Automatic` (or explicit numeric values
for non-physical states); without them SARAH's mass-name lookup returns
`None`. Reference: the v1 goldens at
`tests/goldens/{2hdm_a,singlet_doublet}/particles.m` show the full
shape, including PDG codes for each mass-eigenstate slot. SM-built-in
particles (`VP`, `VZ`, `VG`, `VWp`, `Fd`, `Fu`, `Fe`, `Fv`, ghosts)
do not need any of this — the renderer auto-supplies their metadata.

**Diagnostic markers.** If any guard is bypassed, the SARAH log will
contain one of:

| Layer | Marker | Trigger |
|---|---|---|
| `sarah_output/sarah.log` | `CheckModelFiles::MissingParameter: {...}` | A |
| `sarah_output/sarah.log` | `CheckModelFiles::MissingOutputName: ...` | A |
| `sarah_output/sarah.log` | `Part::partd: Part specification None[[1]]` | B |
| `sarah_output/sarah.log` | `Part::partw: Part N of {...} does not exist` | C |
| `sarah_output/sarah.log` | `StringJoin::string: ... M<>None` / `W<>None` | C |
| `sarah_output/sarah.log` | `ToExpression::notstrbox: ... W<>None` | C |
| `sarah_output/UFO/<Name>/parameters.py` | `Param.$Failed` literal | A or C |
| `sarah_output/UFO/<Name>/particles.py` | particle `name` = `"None"` or `mass = Param.$Failed` | A or C |

A single marker is sufficient. Grep the log and the emitted UFO tree
before editing the ModelSpec.

**Response.** First re-run `/sarah-build` with `--force` to invalidate
the `.sarah_build_key` cache; without it, a cache hit on a previous
broken emission will repeat the same corrupted tree with no new log.
Then:

1. For `MissingParameter` / `MissingOutputName` (Trigger A): grep
   `parameters.py` (UFO) or `parameters.m` (SARAH input) for `Param.$Failed`.
   For each affected symbol, add `les_houches:` to the matching v3 spec
   parameter entry — `[BSMPARAMS, N]` (or another block) for indexed
   scalars, a bare block name for matrices, `[PHASES, N]` for phase
   parameters. Reference idiom: `_shared/modelspec_v3/specs/singlet_doublet.yaml`,
   `_shared/modelspec_v3/specs/2hdm_a.yaml`. SM-style parameters
   (`g1/g2/g3`, `Yu/Yd/Ye`, etc.) do not need `les_houches:`.
2. For `Part::partd` (Trigger B): confirm `chirality ∈ {left, majorana}`
   with a single component renders as a bare symbol, not `{symbol}`. The
   current `render_templates.py:298-302` branch is the reference.
3. For `Part::partw` / `M<>None` / `W<>None` (Trigger C): inspect the
   `particles.ewsb[]` entries in the v3 spec. (a) The `pdg:` list length
   on a mixed mass-eigenstate must equal the number of mass eigenstates
   produced by the corresponding `ewsb.mixing_sector[]` rotation; (b) BSM
   particle entries need `mass: LesHouches` and `width: Automatic` (or
   explicit `0`/numeric values). Cross-reference v1 goldens at
   `tests/goldens/<model>/particles.m` for the canonical PDG codes and
   shape — they are the source of truth when the v3 port loses metadata.
4. If the physics genuinely requires a standalone rank-1 Dirac pair
   with no partner fields, first apply the Weyl reformulation in
   Gotcha #1 (two LH doublets with opposite hypercharge). Most
   vectorlike-fermion extensions accept that reformulation.
5. If (1)–(4) are not tractable (e.g. the rank-1 structure is intrinsic to
   the physics and cannot be reformulated), switch the model to the analytic
   spectrum backend: set `backends.spectrum: analytic` and author a module
   under `spheno-build/scripts/analytic_models/`. See `## Spectrum backends`
   in `/spheno-build` SKILL.md.

**Do not patch the emitted `.f90` or `UFO/*.py` text directly.**
`Param.$Failed` tokens and `None` particle names in emitted output
indicate that the symbol table was incomplete at emission; mass-matrix
initialisation and Yukawa coupling arrays reference the same names
transitively. Textual substitution silences the surface token without
restoring the table.

**Reproduction coverage.** Trigger B observed on `singlet_doublet` during
renderer development (reason the brace guard exists); not reproduced on
a second model. Trigger A observed on `dark_su3` (`gD` lacking
`les_houches:`) and `2hdm_a` (9 BSM scalar potential parameters +
Yukawas + ZH/ZA/ZP + Phasechi all lacking `les_houches:`) during v3 port
end-to-end testing — both produced `Param.$Failed` cascades. Trigger C
observed on `2hdm_a` during the same end-to-end pass (`Ah` PDG list
length 2 vs. ZA's 3-component mix, `hh` missing `mass`/`width` keys).
The generalisation above to "any rank-1 Dirac sub-block" (Trigger B
extension) is a conjecture motivated by the shape, not a second
reproduction. SARAH-version sensitivity is plausible — the pinned range
is `sarah_version_required: ">=4.15,<4.16"`; behaviour under other
versions has not been characterised.
