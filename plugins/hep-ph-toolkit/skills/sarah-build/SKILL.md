---
name: sarah-build
description: Given a validated ModelSpec YAML, render SARAH .m files from templates and invoke SARAH headlessly to produce UFO and/or SPheno source output.
---

# `/sarah-build`

Transforms a `ModelSpec` YAML into SARAH `.m` files, runs SARAH headlessly via
`wolframscript`, and collects UFO/SPheno output under
`$STATE_ROOT/models/<name>/`.  Caches by input SHA-256 so repeated invocations
on the same spec are no-ops.

---

## When to invoke

- When `/lagrangian-builder` has a validated `ModelSpec` and needs SARAH output.
- Directly by the user: `python3 build.py path/to/spec.yaml [--force]`.

---

## Preflight: SARAH

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/sarah/detect.sh

- **exit 0** → SARAH and Wolfram Engine are both ready (composite check
  covering config, Wolfram reachability, activation status, and SARAH
  on-disk presence); proceed.
- **exit non-zero** → SARAH or Wolfram is missing/misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/sarah/INSTALL.md` into context
  and follow it. When the install completes (or the install script
  returns `activation_required`), re-run `detect.sh` before proceeding.
  If it still fails, halt with the blocker code from the install
  reference.

---

## Supported models

The generator supports spec shapes whose physics falls inside the following
envelopes.  Specs outside these envelopes will be rejected at validation or
will produce render-only (not physics-correct) output.

### Gauge groups

- **U(1)** — hypercharge or extra Abelian factors.
- **SU(2)** — electroweak left factor.
- **SU(3)** — QCD color or an additional strongly-coupled sector (e.g. dark SU(3)).

Multiple copies of the same group are supported (e.g. SM + dark SU(3) as in
`dark_su3`).  Non-Abelian groups beyond SU(3) (SU(5), SO(10), E6, …) are
out of scope for v1.

### Fermion kinds

- **Left Weyl** (`chirality: left`) — chiral left-handed Weyl fermion.
- **Right Weyl** (`chirality: right`) — chiral right-handed Weyl fermion.
- **Majorana** (`chirality: majorana`) — self-conjugate Weyl fermion.
- **Dirac pair** (`chirality: dirac`) — shorthand for a left+right pair with
  a common mass and the same quantum numbers (auto-expands to a Dirac fermion).

### Scalar kinds

- **Additional Higgs doublets** (`reps: {WB: 2}`, `hypercharge: 0.5`) — any
  number of SU(2) doublets beyond the SM Higgs.
- **Singlets** (`reps: {WB: 1, G: 1}`, arbitrary hypercharge or Y=0) — real
  or complex SM-singlet scalars (e.g. a CP-odd mediator `a0`).

### EWSB mixing kinds (via `ewsb.mixings`)

Each entry in `ewsb.mixings` is discriminated by `kind`, which may be
`"fermion"` or `"scalar"`:

- `kind: fermion` — fermionic mixing block; requires `chirality` sub-field:
  - `chirality: majorana` — mixes left-Weyl and conjugate-right-Weyl fields
    into Majorana mass eigenstates.  Requires `weyls` list.
  - `chirality: dirac` — mixes distinct left- and right-handed Weyl fields
    into Dirac mass eigenstates.  Requires `lh_weyls` and `rh_weyls`.
- `kind: scalar` — mixes scalar/pseudoscalar fields after EWSB.  Requires
  `weyls` (fields to mix) and `mixing_matrix`.

---

## Inputs

A `ModelSpec` v3 YAML file conforming to
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`.

Minimal required keys (v3 shape): `model.name`, `gauge_groups`, `fermions`,
`scalars`, `parameters`, `lagrangian`. See the SM template at
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml` and
the four reference specs at
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/{singlet_doublet,dark_su3,2hdm_a,ssm}.yaml`
for worked examples covering DM extensions, confining gauge sectors, and
extended Higgs doublets.

For each new model, start by copying the SM template and inserting BSM
fields, then run `validate_spec.py` and `build.py --out <dir>` to render
the SARAH `.m` files.

---

## Decision flow

```
build.py <spec.yaml> [--force]
    │
    ├─ 1. Validate spec
    │       validate_spec.py → MODELSPEC_INVALID (fatal) on failure
    │
    ├─ 2. Check cache
    │       key = sha256(spec.yaml bytes hex) + "=" + sarah_version
    │       stored at $STATE_ROOT/models/<name>/.sarah_build_key
    │       If key matches AND sarah_output/UFO/<Name>/ exists AND not --force
    │           → exit 0  {"status": "cached"}
    │
    ├─ 3. Render .m templates
    │       render_templates.py → <Name>.m, parameters.m, particles.m, SPheno.m
    │       written to $STATE_ROOT/models/<name>/sarah/
    │
    ├─ 4. Stage into Private-Models/
    │       stage.py:stage()
    │       Wipes $sarah_path/Private-Models/<Name>/ (stale .m + .mx caches)
    │       Writes rendered files + .sarah_build_key stamp
    │
    ├─ 5. Invoke SARAH via wolframscript (cwd = sarah_path)
    │       run_sarah.py
    │       AppendTo[$Path, "<sarah_path>/.."];
    │       <<SARAH`;
    │       Start["<Name>"];
    │       CheckModel[];
    │       MakeUFO[];        (if "ufo" in spec.outputs)
    │       MakeSPheno[];     (if "spheno" in spec.outputs)
    │       stdout+stderr → $STATE_ROOT/models/<name>/sarah_output/sarah.log
    │
    ├─ 6. Read sarah.log
    │       $STATE_ROOT/models/<name>/sarah_output/sarah.log
    │       Agent checks for fatal patterns (see §"Reading sarah.log" below)
    │       ANOMALY_CANCELLATION_FAILED (fatal) on anomaly
    │       MODELSPEC_INVALID (fatal) on undefined field
    │       Warnings collected, non-fatal
    │
    ├─ 7. Collect outputs
    │       collect.py:collect()
    │       Globs $sarah_path/Output/<Name>/*/UFO/ (prefers EWSB/)
    │       Copies UFO/<Name>/ → $STATE_ROOT/models/<name>/sarah_output/UFO/<Name>/
    │       Copies SPheno/    → $STATE_ROOT/models/<name>/sarah_output/SPheno/<Name>/
    │       Creates ufo symlink → sarah_output/UFO/<Name>/
    │       SARAH_OUTPUT_MISSING (fatal) if UFO dir absent
    │
    ├─ 8. Write cache key
    │       .sarah_build_key = sha256hex=sarah_version
    │
    └─ 9. Update config
            config.models[<name>].spec, .ufo, .sarah_built_at
```

---

## Cache semantics

Cache key (§2.9 of `phase2-plan-final.md`):
```
sha256(<spec.yaml bytes>, hex) + "=" + <sarah_version from config>
```

Stored at `$STATE_ROOT/models/<name>/.sarah_build_key` (single line, no newline).

- **Cache hit:** key matches AND `sarah_output/UFO/<Name>/` directory exists → skip
  template rendering and `wolframscript` entirely; return `{"status": "cached"}`.
- **Cache miss:** any mismatch, missing key file, or missing output directory → full rebuild.
- **`--force`:** always rebuilds regardless of cache.

The cache is input-only: no hashing of the output tree (output-tree hashing is
explicitly rejected per §2.9).

---

## Private-Models staging (RC1 fix)

SARAH loads models from two locations: its built-in `Models/` directory and a
user-writable `Private-Models/` directory.  This skill always uses
`Private-Models/` so the SARAH installation is never modified.

`stage.py:stage()` performs the following steps before each wolframscript run:

1. `mkdir -p $sarah_path/Private-Models/` — SARAH does not create it on first use.
2. If `$sarah_path/Private-Models/<Name>/` already exists, `shutil.rmtree` it.
   This wipes **both** stale `.m` source files and any Mathematica `.mx` compiled
   cache files that SARAH may have left from a previous run.
3. Write fresh rendered files from the in-memory `{filename: text}` dict.
4. Stamp `.sarah_build_key` so a subsequent `stage()` call can detect whether the
   staged tree is already current.

Cleanup of `Private-Models/<Name>/` on exit is the responsibility of
`validate_goldens.py` (see below).  `run_sarah.py` leaves the staged tree in
place for post-mortems.

---

## Golden-file validation

`scripts/validate_goldens.py` is the golden-file oracle for physics correctness.
It is invoked manually (not by CI) because it requires a live `wolframscript`
kernel.

```bash
python3 scripts/validate_goldens.py \
    --model singlet_doublet \
    --goldens-dir tests/goldens/singlet_doublet/ \
    --outputs ufo,spheno \
    [--sarah-path <path>] \
    [--wolframscript <path>]
```

The script:
1. Reads golden `.m` files from `tests/goldens/<model>/`.
2. Stages them into `$sarah_path/Private-Models/<Name>/` via `stage.stage()`.
3. Runs `wolframscript` with `Start["<Name>"]` + `CheckModel[]` + the
   requested make commands.
4. Scans stdout+stderr for forbidden SARAH error patterns
   (`ModelFile::MissingModel`, `ModelFile::Aborted`, `CheckModel::*Abort*`,
   `MatterSector::parseError`).
5. Checks that UFO/SPheno output trees were produced on disk.
6. Cleans up `Private-Models/<Name>/` on exit (unless `--keep-staged`).

Exit 0 = PASS (`{"status": "valid"}`).
Exit 1 = FAIL (`{"status": "invalid", "code": ..., "context": {...}}`).
Exit 2 = environment / usage error.

---

## Failure modes → blockers

All blockers are emitted as single-line JSON on **stderr**, conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | Action |
|------|------|---------|--------|
| `MODELSPEC_INVALID` | fatal | Schema validation fails or semantic check fails (duplicate names, bad reps, bad hypercharge, empty outputs) | Fix the spec; re-run |
| `WOLFRAM_KERNEL_ABSENT` | fatal | `wolfram_engine_path` not set in config | See `_shared/installs/sarah/INSTALL.md` |
| `SARAH_ABSENT` | fatal | `sarah_path` not set in config | See `_shared/installs/sarah/INSTALL.md` |
| `ANOMALY_CANCELLATION_FAILED` | fatal | SARAH log contains `Anomalies are not cancelled` | Inspect coefficients in `context`; modify the model |
| `MODELSPEC_INVALID` | fatal | SARAH log contains `Error: field <X> undefined` | Fix field name in spec |
| `SARAH_OUTPUT_MISSING` | fatal | `sarah_output/UFO/<Name>/` absent after successful SARAH exit | Check `sarah.log`; may indicate SARAH version mismatch |

### `ANOMALY_CANCELLATION_FAILED` context shape

```json
{
  "code": "ANOMALY_CANCELLATION_FAILED",
  "mode": "fatal",
  "message": "SARAH anomaly check failed for model DarkSU3",
  "context": {
    "coefficients": [
      "SU(3)^3 coefficient = 3",
      "U(1) mixed coefficient = 1/6"
    ]
  }
}
```

The `coefficients` list is extracted by the agent from the 10 lines following
`Anomalies are not cancelled` in `sarah.log` — look for lines matching
`coefficient.*=` (case-insensitive).

---

## Post-build artifacts

After a successful build the state directory contains:

```
$STATE_ROOT/models/singlet_doublet/
├── spec.yaml                                   # copy of the input spec
├── .sarah_build_key                            # cache key (sha256hex=version)
├── sarah/                                      # local copy of rendered .m files
│   ├── SingletDoublet.m
│   ├── parameters.m
│   ├── particles.m
│   └── SPheno.m
├── sarah_output/
│   ├── sarah.log                               # wolframscript stdout+stderr
│   ├── UFO/
│   │   └── SingletDoublet/                    # UFO model directory (Python files)
│   └── SPheno/
│       └── SingletDoublet/                    # SPheno Fortran source tree
└── SingletDoublet -> sarah_output/UFO/SingletDoublet/   # relative symlink
```

The symlink's basename matches the target directory's basename. MG5's
`import model <path>` appears to use the symlink basename to re-resolve the
model path against the symlink's parent rather than following the symlink to
its target — a mismatched basename (prior versions used `ufo` as the
symlink name) produces a non-existent path and fails the import. `collect.py`
also removes any legacy `state_dir/ufo` symlink from prior builds on each
invocation.

For `dark_su3` (UFO-only, no SPheno):
```
$STATE_ROOT/models/dark_su3/
├── spec.yaml
├── .sarah_build_key
├── sarah/
│   ├── DarkSU3.m
│   ├── parameters.m
│   ├── particles.m
│   └── SPheno.m                               # stub (render-only; no live EWSB content)
├── sarah_output/
│   ├── sarah.log
│   └── UFO/
│       └── DarkSU3/
└── DarkSU3 -> sarah_output/UFO/DarkSU3/
```

Note: the `sarah/` subtree is a **local reference copy** written by `run_sarah.py`
alongside the `Private-Models/` staging.  The authoritative copy that SARAH reads
is at `$sarah_path/Private-Models/<Name>/`.

Config is updated:
- `config.models["<name>"].spec` — absolute path to `spec.yaml`
- `config.models["<name>"].ufo` — absolute path to `state_dir/<sarah_name>` symlink (pass this directly to MG5's `import model`)
- `config.models["<name>"].sarah_built_at` — UTC ISO 8601 timestamp

The SPheno Fortran sources at `sarah_output/SPheno/<Name>/` are consumed by
`/spheno-build` (W4).

---

## The `/..` in `$Path`

`AppendTo[$Path, "<sarah_path>/.."]` is correct.  `sarah_path` points to the
package directory containing `SARAH.m` (e.g. `$HOME/SARAH`).  The `<<SARAH\``
loader resolves the `SARAH\`` context from a sibling directory, so the **parent**
of `sarah_path` must be in `$Path`.  This matches the existing
`install_sarah.sh:probe_version` convention in `hep-ph-demo`.  Do NOT drop the `/..`.

---

## Per-model status

| Model | Test bar | Notes |
|-------|----------|-------|
| `singlet_doublet` | **End-to-end** (physics-correct) | Majorana + Dirac fermion mixing; UFO + SPheno. `validate_goldens.py --outputs ufo,spheno` required before goldens commit. |
| `dark_su3` | **Render-only** | SU(3)_D confinement is outside SARAH's EWSB grammar. `spec.outputs: [ufo]`; no `MakeSPheno[]` dispatched. Acceptance bar: `Start["DarkSU3"] + CheckModel[]` pass without abort. |
| `2hdm_a` | **Render-only** | Two Higgs doublets + CP-odd singlet; `sm_overrides.higgs_sector: true`. Acceptance bar: render without fatal error. Full E2E (physics-correct EWSB) is a post-v1 goal. |

"Physics-correct" means the generated SARAH files pass `Start[] + CheckModel[] +
MakeUFO[] + MakeSPheno[]` with no forbidden error patterns.  "Render-only" means
the files render (template substitution succeeds) and `Start[] + CheckModel[]`
pass, but the make commands are not in scope for the current test bar.

---

## Non-goals (v1)

The following are explicitly out of scope for this release:

- **SUSY / superpotential** — no `superpotential:` block in the spec schema;
  no SUSY mass terms, soft-breaking sector, or gaugino content.
- **CP-violating phases beyond auto-derived Majorana phases** — arbitrary
  complex phases in mixing matrices are not supported.  The `ewsb.phases`
  list pre-wires the escape hatch but the generator does not yet act on it.
- **Non-SM gauge groups beyond the 3 target patterns** — SU(5), SO(10), E6,
  or any gauge group with rank > 3 in a single simple factor.
- **`MakeCalcHEP[]`, `MakeWHIZARD[]`, `MakeFeynArts[]`** — `spec.outputs`
  accepts only `"ufo"` and `"spheno"`; other targets are rejected at
  JSON-schema validation.

---

## Escape hatches

These spec-level knobs unlock non-default behaviour when the default generator
logic does not match the model's physics.

### `sm_overrides.higgs_sector: true`

Set when the BSM sector completely redefines the Higgs sector (e.g.
two-Higgs-doublet models, Georgi-Machacek-style triplet models).  When `true`:

- The generator does **not** auto-inject the SM Higgs Yukawa terms.
- The spec's `lagrangian.yukawa_terms` is treated as the complete Yukawa sector.
- EWSB is driven solely by the `ewsb.vevs` entries in the spec.

`singlet_doublet` leaves this `false` (SM Higgs sector unchanged).
`2hdm_a` sets this `true`.

### `spec.outputs` without `"spheno"` (UFO-only)

Omit `"spheno"` from `spec.outputs` when the model's vacuum structure is
outside SARAH's EWSB grammar (e.g. a confining dark sector with no EWSB
mass spectrum).  `run_sarah.py` will not dispatch `MakeSPheno[]`; the
generated `SPheno.m` is a minimal stub so the file exists for the render bar.

`dark_su3` uses this pattern.

### Free-form `ewsb.mixings` for non-default mixings

The `ewsb.mixings` list accepts any combination of `kind: fermion`
(with `chirality: majorana` or `chirality: dirac`) and `kind: scalar`
entries in a single spec.  Fields listed in `weyls` / `lh_weyls` /
`rh_weyls` may include `conj[<field>]` notation for conjugate Weyl
components.  This covers mixing topologies that do not match the standard
SM or simple-extension patterns.

`singlet_doublet` uses a `kind: fermion, chirality: majorana` entry
(3-component neutral sector) plus a `kind: fermion, chirality: dirac`
entry (charged fermion).  `2hdm_a` uses three `kind: scalar` mixing
entries (CP-even Higgs, CP-odd/pseudoscalar, charged Higgs).

---

## Gotchas (SARAH-idiom discrepancies)

Six patterns that cause SARAH to silently drop vertices or collapse mass
matrices to `OnlyZero`. Cite the reference models when writing new specs.

### 1. Vectorlike fermion doublet — use two left-Weyl doublets, not a Dirac pair

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

### 2. Majorana mass terms live in LagHC, not LagNoHC

**Reference:** SplitSUSY-MSSM.m:54 — Majorana gaugino masses `- MG/2 FG.FG
- MW/2 FW.FW - MB/2 FB.FB` appear inside `LagHC` (with `AddHC -> True`),
NOT inside `LagNoHC` with a pre-applied `-1/2` coefficient. Physically the
two forms are equivalent (hermitian-conjugate of a Majorana mass is the
same term), but SARAH's mass-matrix extractor only picks up the LagHC
placement. The generator classifies singlet Majorana mass terms
`{fields: [S, S], hermitian_conjugate: true}` into LagHC automatically;
the `1/2` coefficient is prepended by `_format_hc_term` so the rendered
output matches SplitSUSY convention byte-for-byte.

### 3. Dirac charged sectors need distinct LH/RH mass-eigenstate names

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

### 4. BSM matter fields must use F-prefixed (not single-letter) names

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

### 5. `DEFINITION[GaugeES][DiracSpinors]` is often a workaround, not a fix

It's not in the stock SARAH reference models for most physics classes
(SplitSUSY-MSSM/MSSM ships without it; PortalDM.m has it for a different
reason). If you're reaching for it to silence `Part::partw` errors in
superpotential checks, suspect instead that the MatterSector has `conj[]`
embedded mid-expression (symptom of gotcha #1 above). Fix the Weyl
formulation first; only add the GaugeES DiracSpinor block when a reference
model for the same physics class uses it.

### 6. Rank-1 Dirac sub-blocks and silent parameter degradation

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

---

## Reading sarah.log (agent-driven)

After `wolframscript` completes, `run_sarah.py` writes the full
stdout+stderr to `$STATE_ROOT/models/<name>/sarah_output/sarah.log`.
Open that file and check for the following patterns:

**Fatal blockers — abort the build:**

| Pattern | Blocker code | Action |
|---|---|---|
| `Anomalies are not cancelled` | `ANOMALY_CANCELLATION_FAILED` | Inspect the 10 lines following the match for `coefficient.*=` lines; include them in `context.coefficients`. Fix the model spec. |
| `Error:\s+field\s+(\w+)\s+undefined` | `MODELSPEC_INVALID` | The captured field name `\1` was referenced in the spec but not declared. Fix the field name. |

**Non-fatal — collect and surface:**

| Pattern | Notes |
|---|---|
| `Warning:` | Collect all matching lines; surface in the run summary but do not abort. |

**Hint patterns — indicate silently-degraded output (see Gotcha #6):**

| Pattern name | Pattern |
|---|---|
| `PART_PARTD_NONE` | `Part::partd:.*None\[\[` |
| `STRINGJOIN_W_NONE` | `StringJoin::string:.*W<>None` |
| `TOEXPRESSION_NOTSTRBOX` | `ToExpression::notstrbox:.*W<>None` |
| `PART_PARTW` | `Part::partw` |

If any hint pattern matches, it indicates the mass matrix or parameter
rendering degraded silently. Check `sarah_output/UFO/<Name>/parameters.py`
for `Param.$Failed` literals and `sarah_output/UFO/<Name>/particles.py` for
particle `name = "None"` — both indicate a broken emission. See Gotcha #6
for the response procedure.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_spec.py` | CLI: validate a ModelSpec YAML; exit 0 / 1 |
| `scripts/render_templates.py` | Pure Python: spec dict → `{filename: text}` |
| `scripts/stage.py` | Stage rendered files into `$sarah_path/Private-Models/<Name>/` |
| `scripts/collect.py` | Copy SARAH Output tree into state dir; create `ufo` symlink |
| `scripts/run_sarah.py` | Render + stage + invoke wolframscript + collect + cache write |
| `scripts/validate_goldens.py` | Golden-file oracle: stage + wolframscript + error grep |
| `scripts/build.py` | Top-level CLI driver |

Templates live in `templates/` as plain text with `{placeholder}` tokens
(§2.10: `str.format` only, no Jinja2).
