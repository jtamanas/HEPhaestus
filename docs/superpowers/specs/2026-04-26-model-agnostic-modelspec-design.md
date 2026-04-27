# Model-Agnostic ModelSpec — Design

**Status:** Locked design, ready for implementation.

**Supersedes:** the earlier draft at this path that targeted v1 byte-equivalence. That draft is abandoned. We are doing a ground-zero rewrite.

## Goal

Provide a YAML format for authoring BSM and EFT models that:
1. Is a **thin structural mirror of SARAH**, faithful to what SARAH actually consumes.
2. Catches physics and structural errors **fast, in pure Python**, before the SARAH/Mathematica handoff.
3. Stays out of the renderer's way: no opinions about prefactors, signs, or "what physics this term means."

The validator's reason to exist is the things SARAH skips: anomaly cancellation, U(1) charge conservation per term, discrete-symmetry conservation per term, reserved-name collisions, dangling references. SARAH catches Mathematica syntax errors when it runs — that is not the validator's job.

## Architecture decisions (locked)

These are the foundational choices. Each was selected against alternatives during brainstorming; revisiting them is a rewrite.

1. **Thin SARAH mirror.** Field names mirror SARAH's. The schema does not introduce abstractions ("Higgs portal coupling", "DM stabilization") that the renderer must translate.
2. **Strings for Lagrangian terms.** Each term in `lagrangian.hc` / `lagrangian.no_hc` is a Mathematica string. The renderer concatenates; it does not understand operator structure. This avoids v1's prefactor/coefficient/sign opinions that produced silent physics bugs.
3. **Closed schema.** Unknown keys are blocking errors. Every field is enumerated; anything not in the schema goes through the escape hatch.
4. **One escape hatch.** Top-level `sarah_raw:` field whose contents are appended verbatim to the rendered `.m`. No per-section escapes. When `sarah_raw:` patterns recur across 2–3 specs, promote them to first-class schema fields.
5. **No runtime include / fragment mechanism.** The Standard Model ships as a verified copy-paste template. Authors fork it and edit. No merge engine, no fragment-validates-standalone rules, no override semantics.
6. **Pure Python validator.** No Mathematica subprocess. SARAH runtime errors are SARAH's problem. The validator runs in milliseconds, no external dependencies beyond `pyyaml` and `jsonschema`.
7. **Three-stage validation.** Stage 1 (schema) and Stage 2 (refs / reserved-name collisions / canonical Weyl table) emit blocking errors. Stage 3 (physics: anomalies, per-term U(1) charge conservation, per-term discrete symmetry conservation) emits **warnings**. Symmetry violations and anomalies are sometimes intentional (anomaly inflow in EFTs, explicit symmetry-breaking operators); the validator shouts but does not block.

## Schema

The schema is closed (`additionalProperties: false`) at every level. Top-level structure:

| Field | Type | Required | Notes |
|---|---|---|---|
| `model` | object | yes | metadata |
| `gauge_groups` | list | yes (≥1) | one per gauge factor |
| `global_symmetries` | list | yes (may be `[]`) | discrete & global U(1)s |
| `fermions` | list | yes (may be `[]`) | LH-Weyl entries |
| `scalars` | list | yes (may be `[]`) | |
| `parameters` | list | yes (may be `[]`) | |
| `lagrangian` | `{hc, no_hc}` | yes | each may be `[]` |
| `ewsb` | object | yes | required even if minimal |
| `particles` | object | yes | particles.m metadata |
| `sarah_raw` | string | optional, default `""` | escape hatch |

### `model`

| Field | Type | Required |
|---|---|---|
| `name` | string (CamelCase, ≥2 chars) | yes |
| `latex` | string | yes |
| `authors` | string | yes |
| `date` | string (ISO `YYYY-MM-DD`) | yes |

### `gauge_groups[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `symbol` | string (identifier, not reserved) | yes | e.g. `B`, `WB`, `G`, `BL` |
| `type` | enum `U(1) \| SU(2) \| SU(3) \| SU(N)` | yes | `SU(N)` accepts arbitrary integer N |
| `label` | string | yes | SARAH "description" |
| `coupling` | string (param name) | yes | must appear in `parameters[]` |
| `ssb` | bool | yes | explicit (no inference) |
| `discrete_charges` | dict[name→int] | optional | charges under each `global_symmetries[]` |
| `boson_name` | string | optional | default `V<symbol>` |
| `ghost_name` | string | optional | default `g<symbol>` |

The renderer emits `Gauge[[i]] = {symbol, group, label, coupling, ssb, dc1, dc2, ...};` where the trailing columns are this group's charge under each declared global symmetry. **Verified against SARAH goldens**: 2hdm_a/dark_su3 (no globals → 5-tuple); singlet_doublet (one global → 6-tuple). Width is `5 + len(global_symmetries)`.

### `global_symmetries[]`

| Field | Type | Required |
|---|---|---|
| `kind` | enum `Z2 \| Z3 \| Z4 \| Zn \| U1` | yes |
| `name` | string (identifier) | yes |

Renders as `Global[[i]] = {Z[n], name};` or `Global[[i]] = {U[1], name};`.

### `fermions[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string (identifier, not reserved) | yes | SARAH FermionField name |
| `generations` | int ≥1 | yes | |
| `components` | string OR list[string] | yes | bare for singletons (`s0`, `'conj[dR]'`) or list for multiplets (`[uL, dL]`) |
| `reps` | dict[gauge_symbol → Charge] | yes | see Charge type below |
| `discrete_charges` | dict[name→int] | optional | defaults all-trivial |
| `dirac_partner` | string | optional | name of the LH-Weyl this pairs with for vectorlike Dirac mass |

**`Charge` type union:** `int | Rational(string 'a/b') | param_symbol(string) | expression_string('If[A==1, ...]')`. Numeric is the common case; expression-valued is for per-generation differentiation under U(1) factors (e.g. `L_μ - L_e`); param-symbol is for parametric charges (e.g. DM charge `qChi`).

All entries are LH-Weyl by SARAH convention. RH SM fields appear as LH-Weyl conjugates with `components: 'conj[dR]'` and conjugate-flipped charges (e.g. `B: 1/3` for the d-quark singlet). This is faithful to SARAH's actual encoding.

The renderer emits `FermionFields[[i]] = {name, gens, components, q1, q2, ..., dc1, dc2, ...};` — one charge column per declared gauge group, then one discrete-charge column per declared global symmetry. **Singleton normalization**: schema accepts both bare string and single-element list for components; renderer emits bare for singletons (matching SARAH's conventional form, e.g. SSM.m line 35 `{s, 1, Sing, 0, 1, 1}`).

### `scalars[]`

Same shape as `fermions[]` plus:

| Field | Type | Required | Notes |
|---|---|---|---|
| `real` | bool | yes | `true` for real scalar |
| `vev` | string | optional | name of VEV parameter (must appear in `parameters[]`) |

### `parameters[]`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string (identifier or `\[Sym]`) | yes | |
| `description` | string | optional | SARAH `Description -> "..."` |
| `latex` | string | optional | SARAH `LaTeX -> "..."` |
| `real` | bool | optional, default `false` | |
| `shape` | enum `scalar \| matrix:NxM \| vector:N` | optional, default `scalar` | matrix shape required for mixing matrices |
| `dependence_num` | string | optional | raw Mathematica for SARAH `DependenceNum -> ...` |
| `dependence` | string | optional | for fixed-form dependences (e.g. `1/Sqrt[2] {{1,1},{I,-I}}`) |
| `dependence_spheno` | string \| `"None"` | optional | SARAH `DependenceSPheno -> ...` |
| `output_name` | string | optional | SARAH `OutputName -> ...` |
| `les_houches` | string \| `[string, int]` | optional | bare symbol (`Yu`) or `{block, idx}` (`[BSMPARAMS, 1]`) |
| `positive` | bool | optional | |

### `lagrangian`

```yaml
lagrangian:
  hc:    [{ term: <string>, description?: <string> }]
  no_hc: [{ term: <string>, description?: <string> }]
```

The renderer emits:

```mathematica
LagHC = -(t1 + t2 + ... + tN);
LagNoHC = u1 u2 ... uM;
```

Where `t_i` are `hc[].term` strings joined with ` + `, wrapped in `-(...)`. The user signs each term with its physics sign as it would appear *after* the implicit minus (so a Yukawa `Yd conj[H].d.q` writes positively; an up-Yukawa `-Yu H.u.q` retains the conventional minus).

`u_j` are `no_hc[].term` strings space-concatenated (the user includes signs).

**No prefactor or sign opinions in the renderer.** This is the response to v1's silent-physics bugs (`-1/2 \[Lambda]` factor, Majorana auto-half).

Term strings must parse as a single Mathematica expression — balanced brackets, no semicolons. `Sum[...]` is supported (see scotogenic Yukawa pattern); the symbol-extraction tokenizer handles it.

### `ewsb`

| Field | Type | Required | Notes |
|---|---|---|---|
| `vevs` | list[Vev] | yes (may be `[]`) | `DEFINITION[EWSB][VEVs]` |
| `gauge_sector` | list[GaugeMix] | yes (may be `[]`) | `DEFINITION[EWSB][GaugeSector]` |
| `mixing_sector` | list[Mixing] | yes (may be `[]`) | `DEFINITION[<stage>][MatterSector]` |
| `phases` | list[Phase] | yes (may be `[]`) | `DEFINITION[EWSB][Phases]` |
| `dirac_spinors_pre_ewsb` | list[Spinor] | yes (may be `[]`) | `DEFINITION[GaugeES][DiracSpinors]` |
| `dirac_spinors_post_ewsb` | list[Spinor] | yes (may be `[]`) | `DEFINITION[EWSB][DiracSpinors]` |
| `real_scalars` | list[string] | optional | field names appearing in `RealScalars = {...};` |

**`Vev`** = `{component: str, vev: [str, str|number], goldstone: [str|0, str|number|0], physical: [str, str|number]}`. Verified against SARAH's official `SSM.m`: real-scalar VEVs use the literal `[0, 0]` for the Goldstone slot (no Goldstone) and unit factors (no `1/Sqrt[2]` complex split). Example:

```yaml
vevs:
  - { component: H0,   vev: [v,  '1/Sqrt[2]'], goldstone: [Ah, '\[ImaginaryI]/Sqrt[2]'], physical: [hh, '1/Sqrt[2]'] }
  - { component: Sing, vev: [vS, 1],            goldstone: [0, 0],                       physical: [phiS, 1] }
```

**`GaugeMix`** = `{rotate: [str, str], to: [str, str], matrix: str}`.

**`Mixing`** — closed-shape per `kind`:
- `dirac`: `{kind: dirac, stage: GaugeES|EWSB (default EWSB), lh: [str], rh: [str], outputs: {lh: {name: str, mixing: str}, rh: {name: str, mixing: str}}}`
- `majorana`: `{kind: majorana, stage: GaugeES|EWSB, weyls: [str], output: {name: str, mixing: str}}`
- `scalar`: `{kind: scalar, stage: GaugeES|EWSB, weyls: [str], output: {name: str, mixing: str}}`

Note `kind: dirac` has TWO outputs (LH-side and RH-side mass eigenstates), `kind: majorana` and `kind: scalar` have ONE. **Verified against goldens**: SingletDoublet line 47 (Majorana 3-Weyl mixing → one ME `Chi` with one matrix `ZN`), SingletDoublet line 48 (Dirac 1-Weyl pair → two MEs `ChiM`/`ChiP` with two matrices `UM`/`UP`), 2hdmA line 49 (scalar 3-Weyl mixing `{Ah1, Ah2, a0}` → one ME `Ah` with one matrix `ZA`).

Per-entry `stage:` field handles the GaugeES-vs-EWSB question for VEV-less scalar mixings (e.g. scotogenic real-scalar singlets that mix without breaking any U(1) and are mass eigenstates at GaugeES rather than EWSB).

**`Phase`** = `{field: str, phase: str}` — for Majorana phase declarations.

**`Spinor`** = `{name: str, components: [str|0, str|0]}`. Literal `0` is a valid component (no LH or RH partner present). YAML int `0` round-trips correctly.

### `particles`

| Field | Type | Required | Notes |
|---|---|---|---|
| `gauge_es` | list[Particle] | yes (may be `[]`) | `ParticleDefinitions[GaugeES]` |
| `ewsb` | list[Particle] | yes (may be `[]`) | `ParticleDefinitions[EWSB]` |
| `weyl_intermediate` | list[Particle] | yes (may be `[]`) | `WeylFermionAndIndermediate` |

**`Particle`**:

| Field | Type | Required |
|---|---|---|
| `name` | string | yes |
| `description` | string | optional |
| `latex` | string \| list[string] | optional |
| `output_name` | string \| list[string] | optional |
| `pdg` | list[int] | optional |
| `pdg_ix` | list[int] | optional |
| `mass` | `"Automatic"` \| `"LesHouches"` \| int \| list[int] | optional |
| `width` | `"Automatic"` \| int \| list[int] | optional |
| `feynarts_nr` | int | optional |
| `electric_charge` | int \| Rational | optional |
| `goldstone` | string | optional |

`pdg_ix` maps to SARAH's `PDG.IX -> ...` (Mathematica dot-access syntax preserved on emit).

**Auto-emission rules** (renderer fills these without user authoring; user entries override):

- Each `gauge_groups[]` entry produces a default `gauge_es` entry for its boson (`{V<symbol>, {Description -> "<label>-Boson"}}`) and ghost (`{g<symbol>, {Description -> "<label>-Boson Ghost"}}`).
- Each Weyl symbol in the canonical Weyl table (built from `fermions[].components` and `scalars[].components`) produces a default `weyl_intermediate` entry `{<sym>, {LaTeX -> "<sym>"}}`. Users override LaTeX/PDG via explicit entries.
- All other particle metadata (PDG, ElectricCharge, Goldstone, etc.) is user-authored — there is no defaulting beyond `LaTeX -> name` and `Description`-from-label.

Auto-emit is deterministic. Boson/ghost name overrides via `gauge_groups[].boson_name` and `ghost_name`. Auto-emitted names that collide with user-declared names produce a Stage-2 blocking error.

### `sarah_raw`

Top-level string, default `""`. Content is appended verbatim to the rendered `.m` after all schema-driven content. Use for SARAH directives the schema does not model (e.g. U(1)×U(1) kinetic mixing's `DEFINITION[GaugeES][GaugeSector]` block). When `sarah_raw:` patterns recur in 2–3 specs, promote to first-class schema.

## Validator

Three stages. Stage 1/2 emit blocking errors; Stage 3 emits warnings.

### Stage 1 — Schema (blocking)

Validate against the JSONSchema. Failures produce diagnostics with JSONPointer paths. Library: `jsonschema`. No physics knowledge.

### Stage 2 — Refs, reserved names, canonical Weyl table (blocking)

**Build the Canonical Weyl Table (CWT).**

```
CWT = {}
for f in fermions:
    is_conj = isinstance(f.components, str) and f.components.startswith('conj[')
    raw_comp = parse_conj_inner(f.components) if is_conj else f.components
    components = [raw_comp] if isinstance(raw_comp, str) else raw_comp
    for c in components:
        for gen in 1..f.generations:
            CWT[f"{c}[{gen}]"] = WeylRef(field=f, gen=gen, comp=c, conjugated=is_conj)
        CWT[c] = WeylRef(field=f, gen=None, comp=c, conjugated=is_conj)  # implicit-gen alias
    CWT[f.name] = FieldRef(f)
# scalars: same construction, conjugated=False, real-flag from spec
# also seed with SARAH-builtin gauge boson Weyl tokens:
#   VB, VWB[1], VWB[2], VWB[3], VWp, VG, VP, VZ
```

The CWT is the single source of truth for symbol resolution. Stage-2 checks reference it.

**Reference checks.** For every reference in the spec — `mixing_sector.weyls/lh/rh`, `vevs[].component`, `gauge_sector.rotate/to`, `dirac_spinors_*.components`, `phases[].field`, `lagrangian` term symbols (after tokenization), `parameters[].les_houches[0]`, etc. — the referenced symbol must:

- be in CWT, OR
- be a SARAH-builtin gauge boson Weyl token, OR
- be the literal `0`, OR
- be a declared `parameters[].name`, OR
- be a Mathematica builtin (handled by tokenizer, not as a reference)

Otherwise: blocking error with the unrecognized symbol and a hint of nearest 3 candidates by Levenshtein distance.

**Reserved-name collision.** For every declared name (parameters, fermions, scalars, gauge groups, particles, EWSB outputs, mixing matrices), reject if the name is in `RESERVED_NAMES` or collides with another declared name. Auto-emitted boson/ghost names that collide with declared names also produce a blocking error.

**Stage-2 termination.** Collect all violations, emit them all, halt before Stage 3 if any blocking error.

### Stage 3 — Physics (warnings)

#### Anomaly cancellation

For each U(1) gauge group `G` and each anomaly type `T ∈ { [G]³, [G][SU(2)]², [G][SU(3)]², [G][grav] }`:

1. For every fermion `f`, for every generation `g ∈ 1..f.generations`:
   - Resolve `Y = f.reps[G]`:
     - int/Rational → use directly
     - expression in `A` → evaluate with `A = g` using a sandboxed evaluator (knows `If[cond, then, else]`, integer math, `==`, `!=`, `<`, `>`)
     - bare param symbol → record as `symbolic[Y]`; do not contribute to numeric sum
   - SU(2) dim factor: `f.reps[SU(2)]` (default 1)
   - SU(3) dim factor: `|f.reps[SU(3)]|` (negative-int convention encodes conjugate rep; magnitude for dim, sign tracked separately for chirality)
   - Sign: `+1` for left-Weyl (no `conj`), `-1` for right-Weyl (`conj[...]` in components). Read from CWT.

2. Sum `T(f, g)`:
   - `[G]³`: `Σ Y³ × dim_SU2 × dim_SU3 × sign`
   - `[G][SU(2)]²`: `Σ Y × T2(SU2) × dim_SU3 × sign` — only when `dim_SU2 ≥ 2`
   - `[G][SU(3)]²`: `Σ Y × dim_SU2 × T2(SU3) × sign` — only when `dim_SU3 ≥ 2`
   - `[G][grav]`: `Σ Y × dim_SU2 × dim_SU3 × sign`

3. **Vectorlike pair exclusion**: fermions annotated with `dirac_partner: <name>` are excluded entirely from each sum. Their net contribution is zero by construction; emitting the warning is misleading.

4. **Reporting**:
   - sum exactly 0, no symbolic charges → silent
   - sum nonzero, all charges numeric → warning: `[G]³ anomaly: <value> (not zero)`
   - symbolic charges present → warning: `[G]³ anomaly: <numeric_part> + symbolic(qChi, ...) — verify by hand`

5. **Kinetic-mixing skip**: if `sarah_raw:` is non-empty AND the user has declared two or more U(1) factors, the validator emits a one-line warning: `Stage 3 anomaly checks may be incomplete because U(1) kinetic mixing is handled via sarah_raw — verify mixing structure manually`. (Conservative; no attempt to parse `sarah_raw:` content.)

#### U(1) per-term charge conservation

For each term in `lagrangian.hc + lagrangian.no_hc`:

1. Tokenize per the Mathematica grammar (below).
2. Walk AST; for each leaf identifier, look up in CWT or in `parameters[]`.
   - Field-leaf in CWT contributes its `reps[<U1group>]` charge (sign-flipped if leaf is wrapped in `conj[...]`).
   - Parameter-leaf contributes 0 (parameters are gauge-singlets).
   - Mathematica builtin (`Sum`, `If`, `Mass`, `Sqrt`, `I`, `\[ImaginaryI]`, integer literal) contributes 0.
3. For terms in `lagrangian.hc:`, the Hermitian-conjugate piece is automatic; charge conservation only requires the un-conjugated piece be balanced.
4. Sum charges. Exact-zero → silent. Nonzero with all-numeric charges → warning. Symbolic charges → annotated warning.

#### Discrete symmetry conservation

Same as U(1) per-term charge conservation, applied per `global_symmetries[].name`. Z_n group: additive mod n. U(1) global: additive over reals. Same reporting rules.

### Symbol-extraction grammar (used by Stage 2 ref checks and Stage 3)

Term strings are tokenized as Mathematica:

1. `\[Letter+\]` matches as a single named-symbol token (e.g. `\[Lambda]`, `\[ImaginaryI]`).
2. `[A-Za-z][A-Za-z0-9]*` matches as a bare-identifier token.
3. `[` and `]` are grouping tokens. `[` immediately following a bare identifier denotes function call (`conj[X]`, `Mass[Fu, 1]`, `Sum[...]`, indexed `Yu[i, j]`).
4. `.` is the SARAH non-commutative product.
5. `*`, `+`, `-`, `/` are commutative operators.
6. `{` and `}` are list/braces.
7. `,` is argument separator.
8. Integer and Rational (`a/b` where both numeric) literals.

**Reserved tokens** (skipped during field-extraction): `Sum`, `If`, `Conj`, `conj`, `Mass`, `Width`, `Sqrt`, `I`, `True`, `False`, plus all Mathematica builtins from the reserved list.

The field-extraction pass walks the AST and collects bare identifiers that are NOT reserved, NOT integer literals, and that match a name in `(fermions ∪ scalars ∪ their components ∪ parameters)`.

## Renderer

The renderer emits three SARAH files: `<Name>.m`, `parameters.m`, `particles.m`.

### Lagrangian assembly

```mathematica
LagHC = -(t1 + t2 + ... + tN);
LagNoHC = u1 u2 ... uM;
```

`LagHC` wraps in `-(...)`, joins `hc[].term` strings with ` + `. `LagNoHC` space-concatenates `no_hc[].term` strings without wrapping.

### Auto-emission

- One `Gauge[[i]]`-line per gauge group, with width `5 + len(global_symmetries)`.
- One `FermionFields[[i]]`/`ScalarFields[[i]]` line per matter field, with width `3 + len(gauge_groups) + len(global_symmetries)`.
- One `ParameterDefinitions` block per `parameters[]` entry, with all SARAH attributes (`Description`, `LaTeX`, `OutputName`, `LesHouches`, `DependenceNum`, etc.) emitted only when the YAML field is present.
- Default `particles.gauge_es` entries for every gauge group's boson and ghost.
- Default `particles.weyl_intermediate` entries for every Weyl symbol in the CWT, with `LaTeX -> <sym>`.
- User-declared entries override defaults.

### Aliases

| YAML name | SARAH emission |
|---|---|
| `eEM` | `e` |

Single name-aliasing, so the user's electric-charge parameter (`eEM`) emits to SARAH's conventional `e`. Other reserved-name conflicts (parameter named `g`, etc.) produce blocking errors with rename guidance.

### Pre-EWSB Dirac spinors block name

Renderer emits `DEFINITION[GaugeES][DiracSpinors]` (matching singlet_doublet golden). SARAH also accepts `DEFINITION[EWSB][GaugeES]` (used in SSM.m) — both are valid SARAH input; we pick the singlet_doublet form for semantic clarity.

### Singleton component normalization

Schema accepts both bare string and single-element list for fermion/scalar components (`s0` or `[s0]`). Renderer emits bare for singletons (matches SARAH's conventional form, e.g. `SSM.m: ScalarFields[[2]] = {s, 1, Sing, 0, 1, 1};`).

### `RealScalars`

If `ewsb.real_scalars: [<names>]` is non-empty, renderer emits `RealScalars = {n1, n2, ...};` after the `ScalarFields` declarations and before `LagNoHC`.

## Reserved names

Implemented as four sets in `_shared/reserved.py`:

**`MATHEMATICA_BUILTINS`**: `I`, `E`, `D`, `N`, `O`, `K`, `C`, `Pi`, `True`, `False`, `Null`, `Sum`, `If`, `Sin`, `Cos`, `Tan`, `Sqrt`, `Exp`, `Log`, `Abs`, `Sign`, `Re`, `Im`, `List`, `Times`, `Plus`, `Power`, `Module`, `Block`, `Function`, `Rule`, `RuleDelayed`, `Set`, `SetDelayed`, `Equal`, `Unequal`, `Greater`, `Less`, `And`, `Or`, `Not`, `Derivative`, `Integrate`, `Solve`, `Simplify`, `Mass`, `Width`, `Conjugate`.

**`SARAH_RESERVED`**: `Casimir`, `Dynkin`, `Delta`, `Eps`, `epsTensor`, `KroneckerDelta`, `Lam`, `Lambda` (without bracket — `\[Lambda]` is allowed), `f`, `Gauge`, `Global`, `FermionFields`, `ScalarFields`, `RealScalars`, `Model`, `LagHC`, `LagNoHC`, `LagrangianInput`, `MatterSector`, `DiracSpinors`, `GaugeSector`, `VEVs`, `Phases`, `Description`, `LaTeX`, `OutputName`, `PDG`, `LesHouches`, `Automatic`, `FeynArtsNr`, `ElectricCharge`, `Goldstone`, `Real`, `DependenceNum`, `Dependence`, `DependenceSPheno`, `ParameterDefinitions`, `ParticleDefinitions`, `WeylFermionAndIndermediate`, `NameOfStates`, `GaugeES`, `EWSB`, `DEFINITION`, `AddHC`, `conj`.

**`SINGLE_LETTERS`**: all single Latin letters `a`–`z`, `A`–`Z` (refused as declared names; permitted only as Mathematica index symbols inside expression strings, e.g. `A` in `If[A==1, ...]`).

**`RENDERER_ALIASES`**: dict `{ "eEM": "e" }`.

The validator imports these sets and rejects any declared name that appears in the union (modulo aliases).

Diagnostic format on collision: `name '<X>' is reserved`. Verbose alias-aware messages (e.g. "rename to eEM") are not used per design choice — terse is enough for users to look up the rename.

## Diagnostic output

The validator emits diagnostics in two forms:

1. **JSON** (machine consumption): newline-delimited objects of shape
   ```json
   {"stage": 1|2|3, "severity": "error"|"warning", "code": "<code>", "path": "<jsonptr>", "message": "<text>", "hint": "<text-or-null>"}
   ```
2. **Pretty text** (human consumption): rendering of the same data with file:line / path markers, color-coded severity, and trailing summary count.

Same data, two renderers. CLI flag `--format=json|pretty` selects (default `pretty`).

## Scope and known gaps

**In scope for v1:**

- All schema sections enumerated above
- Stages 1–3 of the validator
- Renderer for `<Name>.m`, `parameters.m`, `particles.m`
- SM template (verified, copy-paste)
- BSM ports for: singlet_doublet, dark_su3, 2hdm_a (existing v1 fixtures, ported to v2 schema)
- One additional BSM port to verify schema generality: SSM (real-scalar VEV, validates Q1)
- `sarah_raw:` escape hatch with documented warning about anomaly-check skip when kinetic mixing is in use

**Known gaps (deferred to a future iteration):**

- **U(1) × U(1) kinetic mixing** as a first-class schema feature. Currently handled via `sarah_raw:`. Promote when 2–3 specs need it.
- **Scotogenic loop functions**: SARAH auto-emits these in UFO/SPheno output; the schema does not represent them. Author has nothing to author here.
- **Stage 4 SARAH dry-run subprocess**: not in v1. SARAH catches Mathematica syntax when it runs.
- **DM stabilization graph search**: not in v1. The Z₂/Z_n declaration is the user's responsibility; graph-walking allowed-decay channels can be added later if a specific model exposes the gap.
- **Mathematica AST parsing**: tokenizer is sufficient for symbol extraction; full AST is not built. EFT operators with arbitrary mass dimension are accepted as opaque strings.

**Not in scope, ever:**

- Backward compatibility with v1 schema. v1 is deleted; specs are ported by hand.
- Auto-injection of SM content. Authors copy the SM template and modify.
- Renderer opinions about prefactors, signs, half-factors, or which physics a term represents.

## Verification against goldens

The schema's correctness was verified against four SARAH model files:

- `2hdm_a/2hdmA.m` (5-tuple gauge groups, scalar mixing, RealScalars singleton)
- `dark_su3/DarkSU3.m` (5-tuple gauge groups, four gauge factors, dark sector)
- `singlet_doublet/SingletDoublet.m` (6-tuple gauge groups, Z₂ DMParity, Majorana neutralino mixing, vectorlike Dirac doublet)
- `SARAH-current/Models/SSM/SSM.m` (real-scalar VEV with `[0, 0]` Goldstone slot — the canonical answer to Q1)

All four shapes round-trip through the schema cleanly.

The seven BSM sketches (Higgs-portal real scalar DM, Das/Niyogi singlet fermion + scalar portal, three flavored U(1)' WIMPs, U(1)_{B-L}, scotogenic inverse seesaw) collectively exercise: `Z[2]` global symmetries, real scalars with and without VEVs, scalar mixing (`kind: scalar`), Majorana mixing (`kind: majorana`), Dirac vectorlike pairs with `dirac_partner`, expression-valued reps for per-generation U(1) charges, parameter-symbol reps for parametric DM charges, cross-field Weyl references in mixings, and `Sum[]`-form indexed Lagrangian terms.

## Next steps

Implementation plan: `docs/superpowers/plans/2026-04-26-modelspec-v3-implementation.md`. Single-phase plan (no v1 compatibility means no migration phase). Schema + validator + renderer + SM template + 4 BSM ports, all in one cohesive sequence.
