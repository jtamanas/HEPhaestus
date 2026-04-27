# Intel Digest — Model-to-Tool Compatibility Router workstream

**Source:** mined by `ws0-intel` (sonnet, Explore) on 2026-04-26. Returned inline to manager because Explore has no Write tool; manager persisted verbatim.

---

## Tool capability snapshot

| Tool | Input format required | Gauge/scalar/fermion limits | Sharp edges | Blocker codes emitted |
|---|---|---|---|---|
| **MadDM 3.2.13** | MG5-importable UFO (`import model <path>`); UFO basename must match target dir basename; DM candidate has `DMParticle` flag | Standard SM × QCD × QED color algebras only; rejects any BSM non-abelian color tensor (dt1 etc); UFO for dark SU(N) is a hard wall | `bin/maddm` symlink absent (non-critical; use `mg5_aMC --mode=maddm`); `output <dir>` refuses to overwrite existing dir; `generate chi chi~ > all all` misses coannihilation — always use `generate relic_density`; MG5 lowercases all particle names post-import | `MADDM_MISSING` (fatal, from `/dark-matter-constraints`); MadDM itself emits Ωh²=−1 sentinel on failure |
| **micrOMEGAs 6.0.5** | CalcHEP `.mdl` files (`prtcls1.mdl`, `lgrng1.mdl`, `vars1.mdl`, `func1.mdl`); SARAH `WriteCalcHEP[]` required — `WriteUFO[]`/`WriteSPheno[]` alone do not produce them | Non-standard Lorentz/color structures silently mishandled; multi-component DM unsupported in v1 (`MULTICOMPONENT_UNSUPPORTED`); vertex evaluator fails on non-SM gauge structure without error | `Mcdm` is a C macro — do not shadow in driver code; `vSigmaA(0.0)` returns NaN in 6.0.5 — use `calcSpectrum()` instead; smoke regex: 5.x format `Omega h^2 =` vs 6.x format `Omega=`; MSSM binary requires SLHA argument | `MICROMEGAS_MISSING` (recoverable, from DMC router); `OMEGA_UNCONVERGED` (from driver); `proxy_run: true` flag in output JSON when proxy model used |
| **DRAKE 1.0** | User-supplied Wolfram `sv[s_]` and `gam[x_]` closures; does NOT import from MadDM/micrOMEGAs output; benchmark/settings `.wl` files in `$DRAKE_PATH/test/` | Narrow-resonance only (`|m_med − 2m_χ|/m_med < 0.10`); also handles Sommerfeld, forbidden channels, early kinetic decoupling; does NOT do generic freeze-out | `test.wls` `$Path` bug: `AppendTo[$Path,".."]` patch required before first use (vendor: `upstream-patches/test_wls_path.patch`); preset bleed-through: if DRAKE fails to load, MatrixForm shows preset reference values — detect by `runtime0 = 0.`; output regex is `Oh2_(nBE|cBE|fBE)\s*=\s*([0-9eE.+\-]+)` — string `Omega h^2` never appears in DRAKE stdout; Anubis gate on hepforge blocks automated download | `DRAKE_NOT_INSTALLED` (fatal); `DRAKE_WOLFRAM_ABSENT` (fatal); `DRAKE_RUN_FAILED` (fatal); `DRAKE_OUTPUT_INVALID` (fatal); `DRAKE_MODEL_FILE_MISSING` (fatal); `DRAKE_MISSING` (recoverable from DMC); `DRAKE_UNAVAILABLE` (recoverable); `DRAKE_ACTIVATION_REQUIRED` (recoverable); `DRAKE_SKIPPED` (recoverable); `DRAKE_MADDM_DISAGREEMENT` (recoverable) |
| **DDCalc 2.2.0** | `scattering/v1` JSON with σ_SI(p/n) + σ_SD(p/n) in cm²; NREFT not supported; non-SHM halos not supported (v1) | Pure leaf consumer; does not compute cross-sections — requires upstream micrOMEGAs or FormCalc+LoopTools; m_DM < 0.1 GeV out of range | `DATA_DIR` baked into `libDDCalc.a` at build time — symlink fix in `_ensure_ddcalc_data_symlinks()`; Apple Silicon `-L/opt/homebrew/lib/gcc/current` required for `-lgfortran`; DARWIN still unregistered in `ddcalc_driver.c` (tier-2 FU); LZ_2022 was unregistered pre-T1.4 (now fixed) | `DDCALC_INPUT_INVALID` (fatal); `DDCALC_MASS_OUT_OF_RANGE` (recoverable → DarkELF); `DDCALC_DRIVER_FAILED` (fatal); `DDCALC_NREFT_NOT_SUPPORTED` (fatal); `DDCALC_OVERLAY_MISSING` (fatal) |
| **HiggsTools (HB-5.10.2 + HS-2.6.2)** | SLHA2 from `/spheno-build` with `WriteHiggsBoundsBlocks=True`; required blocks: `MASS`, `HMIX`, decay tables, `HiggsBoundsInputHiggsCouplingsFermions`, `HiggsBoundsInputHiggsCouplingsX`; CP-conserving sectors only (v1) | No analytic fallback; no Python-side coupling synthesis; CPV / complex mixing matrices deferred to v1.1 | cmake 4.x incompatibility: pass `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`; `smoke_test.sh` broken (1-arg vs 6-arg) — use `HS_SM_LHCRun1` surrogate; SLHA coupling-block dual-format (SPheno row-index vs FeynHiggs PDG-triplet) — auto-detection by probing col-0 type; `HiggsBounds <whichinput>` arg was missing in legacy driver pre-T1.3; HB-5 SLHA mode requires full path with `.slha` extension, not stem; backend default is `legacy` (unified C++ unverified on macOS arm64) | `HIGGSTOOLS_SLHA_MISSING_BLOCKS` (fatal); `HIGGSTOOLS_SM_REF_MISSING` (fatal); `HIGGSTOOLS_DATASET_MISMATCH` (fatal); `HIGGSTOOLS_BACKEND_UNAVAILABLE` (recoverable); `HIGGSTOOLS_NUMERIC_CRASH` (recoverable) |
| **Analytic backend (dark_su3.py)** | ModelSpec YAML with `backends.spectrum: analytic`, `multi_component: true`; 5 parameters: `g_tilde, sin_theta, m_H2, m_V, m_Psi`; no UFO/CalcHEP required | Dark SU(3)_D only (current); Higgsed (SU(3)→SU(2)) model only; confining variant archived | `dsu3-002` regression-anchor disclosure mandatory — Ωh² is 25000× Planck; `sigmav_approx: true` in all outputs; scipy patch version affects 8th significant digit of Boltzmann result; `REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET` banner must appear verbatim before results table | `ANALYTIC_BACKEND_PATH` (recoverable/informational — fires when `multi_component=true && backends.spectrum=='analytic'`) |

---

## Structural blockers catalog

| Code | Class | One-line explanation | Emitted by |
|---|---|---|---|
| `MADDM_MISSING` | Fatal prereq | MadDM not found / not installed | `/dark-matter-constraints` Step 2 (default pipeline only; suppressed on analytic-only branch) |
| `UFO_MISSING` | Fatal prereq (demotable) | `config.models[<m>].ufo_path` absent; demoted to `ANALYTIC_BACKEND_PATH` notice when `multi_component=true && backends.spectrum=='analytic'` | `/dark-matter-constraints` `check_prereqs.py` Step 1 |
| `SLHA_MISSING` | Fatal prereq | `/maddm` runtime fails with missing spectrum | `/dark-matter-constraints` Step 2 |
| `MICROMEGAS_MISSING` | Recoverable | micrOMEGAs not installed; cross-check triggered but skipped | `/dark-matter-constraints` Step 4 |
| `CROSSCHECK_SKIPPED` | Recoverable | `--skip-crosscheck` passed; Step 4 bypassed | `/dark-matter-constraints` Step 4 |
| `CROSSCHECK_DISAGREEMENT` | Recoverable | MadDM vs micrOMEGAs > 10% on any observable | `/dark-matter-constraints` Step 4b |
| `DRAKE_MISSING` | Recoverable | `config.drake_path` absent or detect returns `missing`/`found` | `/dark-matter-constraints` Step 5, `/drake` |
| `DRAKE_UNAVAILABLE` | Recoverable | `drake_path` set but detect invocation failed/unparseable | `/dark-matter-constraints` Step 5 |
| `DRAKE_ACTIVATION_REQUIRED` | Recoverable | Wolfram Engine not activated | `/dark-matter-constraints` Step 5, `/drake-install detect` |
| `DRAKE_SKIPPED` | Recoverable | `--skip-drake` passed; narrow-resonance detected but bypassed | `/dark-matter-constraints` Step 5 |
| `DRAKE_MADDM_DISAGREEMENT` | Recoverable | DRAKE vs MadDM Ωh² > 10% | `/dark-matter-constraints` Step 5 |
| `DRAKE_NOT_INSTALLED` | Fatal | `install.sh detect` returns `missing`/`found` | `/drake` |
| `DRAKE_WOLFRAM_ABSENT` | Fatal | `wolfram_engine_path` not set or binary not executable | `/drake` |
| `DRAKE_RUN_FAILED` | Fatal | `wolframscript test.wls` exited non-zero | `/drake` |
| `DRAKE_OUTPUT_INVALID` | Fatal | Ωh² absent, NaN, or negative in stdout | `/drake` |
| `DRAKE_MODEL_FILE_MISSING` | Fatal | Benchmark or settings file not found in `$DRAKE_PATH/test/` | `/drake` |
| `ANALYTIC_BACKEND_PATH` | Recoverable/Informational | Analytic-only branch fired: MadDM skipped; analytic backend is authoritative source. Steps 3-5 also skipped. | `/dark-matter-constraints` Step 2 |
| `DDCALC_INPUT_INVALID` | Fatal | Schema validation failed or NREFT/non-SHM present | `/ddcalc` |
| `DDCALC_MASS_OUT_OF_RANGE` | Recoverable | m_DM < 0.1 GeV; `context.suggested_tool = "DarkELF"` | `/ddcalc` |
| `DDCALC_DRIVER_FAILED` | Fatal | Driver compile or runtime error | `/ddcalc` |
| `DDCALC_NREFT_NOT_SUPPORTED` | Fatal | `nreft_coefficients` key present | `/ddcalc` |
| `DDCALC_OVERLAY_MISSING` | Fatal | Overlay requested but files gone | `/ddcalc` |
| `HIGGSTOOLS_SLHA_MISSING_BLOCKS` | Fatal | Required HB input blocks absent | `/higgstools` |
| `HIGGSTOOLS_SM_REF_MISSING` | Fatal | chi2_SM_ref cache absent | `/higgstools` |
| `HIGGSTOOLS_DATASET_MISMATCH` | Fatal | Unified dataset SHA ≠ config pin | `/higgstools` |
| `HIGGSTOOLS_BACKEND_UNAVAILABLE` | Recoverable | Unified Python import failed; falls back to legacy | `/higgstools` |
| `HIGGSTOOLS_NUMERIC_CRASH` | Recoverable | Backend segfault on one scan row; row marked bad | `/higgstools` |
| `SCHEMA_MISMATCH` | Fatal (pre-T1.1) | `extract_field.py` rejected JSON with extra top-level keys — FIXED by relaxing `additionalProperties` to `true` | `extract_field.py` (now fixed) |
| MG5 `dt1` NameError | Fundamental group-theory gap | MG5 color algebra has no SU(N)_D tensor indices; any dark-color UFO import fails at `models/import_ufo.py:1604` | MadGraph5 at UFO import |

**Blocker classifier taxonomy** (from `workflow_work.md`):
1. **Missing skill** — skill not yet written (`/feynarts`, `/formcalc`, `/gamlike`, `/nulike`, `/darkelf`)
2. **Missing tool feature** — DARWIN unregistered in DDCalc; upstream `cmake_minimum_required < 3.5`; Package-X upstream dead
3. **Fundamental group-theory gap** — SU(3)_D in SARAH/MG5; dark-color algebra wall; any confining or Higgsed BSM non-abelian gauge group
4. **Approximation regime mismatch** — DRAKE required near resonances; MadDM velocity expansion fails at `|m_med − 2m_χ|/m_med < 0.1`; micrOMEGAs loop-level silent failure for exotic mediators

---

## ModelSpec schema today

**Vocabulary** (verbatim from template files in `/plugins/model-building/skills/lagrangian-builder/assets/modelspec-templates/`):

```yaml
spec_version: 1
name: <string>
claim_source: "<string>"
sarah_version_required: ">=4.15,<4.16"

gauge_groups:
  - {symbol: B,  group: U1,  kind: hypercharge, coupling: g1, gauge_boson: B0, gaugino: null}
  - {symbol: WB, group: SU2, kind: left,        coupling: g2, gauge_boson: W,  gaugino: null}
  - {symbol: G,  group: SU3, kind: color,       coupling: g3, gauge_boson: g,  gaugino: null}
  # BSM extension example (dark SU(3)):
  - {symbol: GD, group: SU3, kind: dark,        coupling: g_tilde, gauge_boson: VD, gaugino: null}

fermions:
  - name: N
    reps: {WB: 1, G: 1}          # singlet under SU(2) and SU(3)
    hypercharge: 0
    generations: 1
    chirality: majorana           # or: left, right
  - name: psiDL
    reps: {WB: 2, G: 1}
    hypercharge: "-1/2"
    generations: 1
    chirality: left
  - name: psiDR
    reps: {WB: 2, G: 1, GD: 3}   # GD: -3 for anti-fundamental
    hypercharge: 0
    generations: 1
    chirality: right

scalars:
  - name: H
    reps: {WB: 2, G: 1}
    hypercharge: "1/2"
  - name: PhiD
    reps:  {WB: 1, G: 1, GD: 3}  # BSM dark Higgs in GD fundamental
    hypercharge: 0

lagrangian:
  mass_terms:
    - {fields: [N, N], coefficient: MN, hermitian_conjugate: false}
    - {fields: [psiDL, psiDR], coefficient: MPsi, hermitian_conjugate: true}
  yukawa_terms:
    - {fields: [H, psiDL, N], coefficient: yN, hermitian_conjugate: true}
  scalar_potential:
    - {fields: [PhiD, PhiD], coefficient: "-mu_D_sq", hermitian_conjugate: false}
    - {fields: ["conj[H]", H, "conj[PhiD]", PhiD], coefficient: lambda_P, hermitian_conjugate: false}

parameters:
  - {name: MN,   latex: "M_N",    real: true, positive: true,  default: 300.0}
  - {name: MPsi, latex: "M_{\\Psi}", real: true, positive: true, default: 500.0}

outputs: [ufo]          # vocab: ufo, spheno, analytic_only

backends:
  spectrum: analytic    # or: spheno (default)
  analytic_module: analytic_models.dark_su3
```

**`outputs` vocab:**
- `ufo` — SARAH `WriteUFO[]` → MadGraph5 import
- `spheno` — SARAH `WriteSPheno[]` → spectrum file
- `analytic_only` — no SARAH/MG5 emission; all observables from `analytic_module`

**Key discriminants for routing:**
- `gauge_groups[*].kind` — `hypercharge | left | color | dark` (anything `dark` triggers MG5 wall)
- `fermions[*].chirality` — `majorana | left | right` (Majorana → null σ_SD)
- `backends.spectrum` — `analytic | spheno` (controls analytic-only branch gate)
- `multi_component` in `constraints.yaml` — true triggers multi-component combiner prereq
- `outputs` — if `ufo` absent: MadDM blocked; if `spheno` absent: HiggsTools blocked

**Active canonical specs (in `_shared/assets/`):**

| Spec | `gauge_groups` beyond SM | `fermions` | DM candidates | `backends.spectrum` | `outputs` |
|---|---|---|---|---|---|
| `singlet_doublet.yaml` | none (SM only) | N (Majorana singlet), psiDL/psiDR (Weyl doublet) | chi1 (Majorana) | spheno (implicit) | `[ufo, spheno]` |
| `two_hdm_a.yaml` | none (SM only) | chiL, chiR (Dirac singlet) | chi (Dirac) | analytic (stub: `analytic_models.stub_unimplemented`) | `[ufo]` |
| `dark_su3.yaml` | SU3 kind: dark (GD) | none | V (vector spin-1), Psi (pseudo-scalar spin-0) | analytic (`analytic_models.dark_su3`) | `[ufo]` |

**Archived:** `lagrangian-builder/assets/modelspec-templates/archived/dark_su3_confining.yaml` — confining dark QCD with vector-like dark quark + `outputs: [ufo, spheno]`. Archived because it describes a different model than the canonical analytic module. Exemplar of "what failure looks like in the registry."

---

## constraints.yaml schema

```yaml
schema_version: 1                    # integer; must be 1

prereqs:                             # canonical list of every skill referenced by any chain
  <skill-id>:
    status: exists | planned         # exists = skill committed; planned = not yet written
    hours:
      cold:   [<lo float>, <hi float>]   # hours, amortized contribution
      cached: [<lo float>, <hi float>]

constraints:                         # per-observable default chains
  relic | dd | id | collider:
    chain: [<prereq-id>, ...]        # ordered list of prereq skills
    default_time:
      cold:   [lo, hi]
      cached: [lo, hi]
    placeholder: true                # optional; emits message instead of chain
    message: "<string>"              # required if placeholder: true

models:
  <model-id>:
    display:
      title: "<string>"
      hook:  "<string>"              # one-sentence model description
    dm_candidates:
      - {name: <str>, spin: "<str>", notes: "<str>"}
    plot_axes:
      x: {symbol: "<str>", range: [lo, hi], units: "<str>", scale: linear | log}
      y: {symbol: "<str>", range: [lo, hi], units: "<str>", scale: linear | log}
    multi_component: true | false
    multi_component_prereq: <skill-id>    # appended to every chain if multi_component=true
    time_overrides:                       # per-constraint override of default_time
      <relic|dd|id>: {cold: [lo, hi]}    # cached optional
    spec_authoring_blockers:             # pseudo-tokens that force BLOCKED regardless of skill status
      <relic|dd|id>:
        - "<token-string>"
    spec_authoring_reason: >-            # human explanation
      <string>
    chain_overrides:                     # full replacement of default chain per constraint
      <relic|dd|id>:
        chain: [<prereq-id>, ...]        # replaces constraints.<c>.chain entirely
        reason: "<one-line>"             # required; surfaces in router caveats
        backend_hint: <str>              # optional; e.g. 'analytic'
```

**`chain_overrides` semantics:**
- `override.chain` replaces `constraints.<cid>.chain` entirely for that model + constraint
- `multi_component_prereq` is still appended after the override chain if not already present
- Used by dark-su3 relic: `[sarah-build, spheno-build, dark-matter-constraints]` — skips madgraph/maddm because of dark-color wall

**Current prereq status table** (verbatim from file):

| Prereq | status | cold hr range |
|---|---|---|
| sarah-build | exists | [0.33, 1.0] |
| spheno-build | exists | [0.17, 0.5] |
| madgraph | exists | [0.25, 0.5] |
| maddm | exists | [0.25, 0.5] |
| hep-plotting | exists | [0.05, 0.1] |
| feynarts | planned | [0.5, 1.0] |
| formcalc | planned | [0.5, 1.0] |
| ddcalc | planned | [0.5, 1.5] |
| gamlike | planned | [0.5, 1.5] |
| nulike | planned | [0.5, 1.5] |
| dark-matter-constraints | exists | [0.5, 1.5] |

**Note (drift):** `ddcalc.status: planned` in constraints.yaml but `plugins/constraints/skills/ddcalc/SKILL.md` exists on disk. `/dark-su3/SKILL.md:287` says `[EXISTS]`. One-line follow-up: flip constraints.yaml to `exists`.

**`time_budget.py` "render chain" logic summary:**
- `resolve(model, selected)` → `TimeReport` with per-constraint `ConstraintRow`
- Status is `READY` iff `missing == []` (no planned prereqs and no spec-authoring blockers)
- `chain_overrides` fully replaces the default chain; `multi_component_prereq` appended if not present
- Prereq hours are accumulated with overlap dedup (each unique prereq counted once across all selected constraints)
- CLI: `python3 time_budget.py --model dark-su3 --constraints relic dd id` → relic READY; DD BLOCKED on feynarts/formcalc/ddcalc; ID BLOCKED on gamlike

---

## The dsu3 analytic-exception precedent

### Why it exists

MG5 color algebra registers only SM QCD tensors (`T`, `f`, `d` on `colour_1..3`). SARAH emits `dt1..dt4` indices for BSM non-abelian gauge group structure constants. MG5 fails at `models/import_ufo.py:1604` with `NameError: name 'dt1' is not defined`. This was live-reproduced in the dsu3-round run-20260425 with a captured stack trace (`results/mg5_attempt/MG5_debug.captured`). It is an MG5 architecture limitation, not a SARAH bug.

Additionally, the dark-SU(3) paper's DM candidates (V, Psi) are composite/broken-gauge states — they are not present in any UV UFO that SARAH would emit. Even if the color algebra were resolved, MadDM could not generate the coannihilation set for these candidates.

The analytic backend (`analytic_models.dark_su3`) was authorized as a documented exception via the `dsu3-002` disclosure. The decision was made during fix_loop/dark-su3-iter-3 via "ornery opus counsel" and formalized through four iterative rounds.

### What disclosure machinery is mandatory

From `/dark-matter-constraints/SKILL.md:72-83` (verbatim):

> **Mandatory regression-anchor disclosure (analytic-only branch).** When the analytic-only branch fires, the merged report MUST embed a verbatim `REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET` callout for any backend whose `_meta.backend == "analytic"` in `summary.json` (or whose diagnostics carry `sigmav_approx: true`). The callout text is the per-model banner — for dark-su3, this is the `dsu3-002` disclosure mirrored verbatim from `plugins/hep-ph-demo/skills/dark-su3/SKILL.md` top-of-file banner. Render the callout **before** the results table, not buried in a caveats footnote. Downstream readers must see, at a glance, that the analytic Ωh² values are regression-anchors for the analytic pipeline — **not** a physics prediction or a paper-fidelity result. Quoting the analytic numbers without the disclosure is a contract violation.

From `dark-su3/SKILL.md:8-17` (the banner itself):

> REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET. The relic density values produced by this skill (`Omega_V_h2`, `Omega_Psi_h2`) are regression anchors for the analytic pipeline. They are roughly 25000× the Planck target (`Ωh² ≈ 0.120`). Any downstream report that quotes these numbers MUST embed this banner verbatim — do not silently strip it.

**Pinned by test:** `test_dsu3_002_disclosure_propagation_contract` in `dark-matter-constraints/tests/` checks that SKILL.md prose contains `MUST`/`Mandatory` near "analytic-only branch" and `REGRESSION-ANCHOR ONLY` in `dark-su3/SKILL.md`. This is a SKILL-prose contract, not a generated-report-shape contract (gap noted by round-3 reviewer — the test does not examine an actual emitted merged report artifact).

**Analytic-only branch gate (dual AND-condition):**
- `multi_component: true` (from `_shared/constraints.yaml models.<m>.multi_component`)
- `backends.spectrum == "analytic"` (from the model's ModelSpec YAML)

Both must be true. A single condition is not sufficient:
- `analytic` spectrum on non-multi-component model → still blocks (UFO_MISSING not demoted)
- `multi_component=true` on spheno backend → still blocks (MadDM required)

### Dual-spec drift cost

The confining variant (`lagrangian-builder/.../dark_su3.yaml`) and the canonical Higgsed variant (`_shared/assets/dark_su3.yaml`) coexisted in the tree through rounds 1-2, causing:
- 5 `test_skill_structure.py` failures (dm_candidates described confining: `phi`/`m_phi`)
- `constraints.yaml` lines 163-168 described the confining model (`phi`/`m_phi`/"Scalar dark pion") even after confining template was archived
- 6 stale `[PLANNED]` references in `dark-su3/SKILL.md` that lied to users

Resolution: commit `2bb56d6` archived confining spec to `archived/dark_su3_confining.yaml` with README. Round 3 fixer reconciled `constraints.yaml` dm_candidates. Round 4 swept stale prose. Cost: 3 of 4 rounds were partially consumed by cleanup that stemmed from the dual-spec ambiguity.

**Lesson for the router skill:** When a new model gets an analytic exception, the rule is: one canonical spec (in `_shared/assets/`), zero templates in `lagrangian-builder/assets/modelspec-templates/` for the same model name, immediate archive of any competing spec.

---

## Open follow-ups bearing on this workstream

### FU codes from dsu3-playtest/decisions/FOLLOWUPS.md

| FU-id | Title | Severity | Routing relevance |
|---|---|---|---|
| FU-wsa-03 | darkSU3 stub UFO files are placeholders — `dt1` NameError on real MG5 import | major | Router must surface this as a fundamental group-theory gap, not a missing-skill gap |
| FU-wsf-01 | Dark SU(3) UFO dt1 color tensor blocker — MadDM/MG5 cannot load dsu3 UFO | (scoped-out) | Primary evidence for the MG5 dark-color wall entry in the capability matrix |
| FU-wsf-06 | Cycle-4 salvaged real /tmp MadDM data (relic+DD in separate runs) | info | MadDM split-file relic+DD output: skill must merge two `MadDM_results.txt` files |
| FU-wsg-01 | singlet_doublet SARAH output missing CalcHEP files — micrOMEGAs requires `.mdl` | major | Router must check `WriteCalcHEP[]` was called before routing to micrOMEGAs |
| FU-wsg-02 | `vSigmaA(T=0)` returns NaN in micrOMEGAs 6.0.5 | minor | Router should not surface NaN σ_v as a physics result; use `calcSpectrum()` path |
| FU-WS-H-1 | DRAKE acceptance regex does not match actual wolframscript stdout | major | FIXED in T1.5: correct regex is `Oh2_(nBE\|cBE\|fBE)\s*=\s*([0-9eE.+\-]+)` |
| FU-wsj-01 | `slha_adapter._parse_coupling_block` PDG-triplet format not supported | major | FIXED in T1.3: auto-detection of row-index vs PDG-triplet format |
| FU-wsj-02 | `legacy_driver.run_higgsbounds` missing `whichinput` arg | major | FIXED in T1.3 |
| FU-wsj-03 | 2HDM+a SPheno binary not built — fallback to FH example SLHA | minor | Router must detect missing `latest_slha` and route to fallback or emit SLHA_MISSING |
| FU-wsi-01 | LZ_2022 not in DDCalc v1 native set; DARWIN still unregistered | major | LZ_2022 FIXED in T1.4; DARWIN still tier-2. Router's "native" vs "overlay" experiment set affects constraint scope |
| FU-wsi-02 | Apple Silicon `-lgfortran` linker flag for DDCalc | minor | FIXED in T1.4; install-detection in router should check DDCalc is fully linked |
| FU-wsk-01 | `extract_field.py` strict schema rejected real producer output | major | FIXED in T1.1: `additionalProperties: false` → `true` on router-contract schemas |
| FU-wsg-01 (DMC) | `proxy_run: true` flag in micrOMEGAs output must be honored | major | Router must detect proxy flag and refuse to report proxy values as native-model predictions |

### Tier-1 fixes touching routing/compatibility (from MERGE_REPORT.md)

| Fix | Branch | Commit | What it fixed |
|---|---|---|---|
| T1.1 | `tier1/t15-drake-path-regex-r1-20260426` | `9724b4e` | DRAKE `test.wls` `$Path` patch + correct `Oh2_(nBE\|cBE\|fBE)` regex |
| T1.2 | `tier1/t11-extract-field-r1-20260426` | `f413a67` | `extract_field.py` `additionalProperties: false` → `true`; added `_resolve_type` for `oneOf`/`anyOf` |
| T1.3 | `tier1/t14-ddcalc-lz2022-r1-20260426` | `e5e424b` | LZ_2022 registration in DDCalc driver; DATA_DIR symlink fix |
| T1.4 | `tier1/t12-config-write-lock-r1-20260426` | `7678b92` | `bin/config_write_locked.sh` wave-mutex config writer |
| T1.5 | `tier1/t13-higgstools-driver-r1-20260426` | `5355461` | HiggsTools SLHA format auto-detect; HB-5 `whichinput` + full-path fix |
| Docs | `tier1/sharp-edges-mo` | `bff6bbc` | micrOMEGAs sharp edges documented (CalcHEP req, Mcdm shadow, vSigmaA NaN, 6.0.5 smoke regex) |
| Docs | `tier1/sharp-edges-drake-dd` | `1beaba9` | DRAKE + DDCalc sharp edges documented |
| Docs | `tier1/sharp-edges-ht-router` | `c22d2a6` | HiggsTools + DMC sharp edges documented (proxy_run, schema relax, NC stream) |

**Remaining open from tier-1 doc merge:**
- `scattering.schema.json` source enum: `"package_x"` vs `"looptools"` — unstaged working tree change; manager must decide direction
- 4 SD/SI fields in fixtures not in router-contract manifest (pre-existing drift)

---

## Cross-cutting observations

### 1. The `check_prereqs.py` AND-gate pattern should become generic

The round-2/3 fix that demoted `UFO_MISSING` for analytic-only models reads both `multi_component` (from `constraints.yaml`) AND `backends.spectrum` (from the model's `spec.yaml`) before deciding whether to block. This dual-source read is exactly the pattern the router skill will need for every branching decision. The current code in `check_prereqs.py:73-112` is the only place this pattern is implemented; it should be promoted to a shared utility (`_resolve_branch_conditions()` or similar) that the new skill can consume.

### 2. `time_budget.py` is the closest existing thing to a routing stub

It already does:
- Per-constraint `READY`/`BLOCKED` classification based on prereq status
- `chain_overrides` dispatch (replaces default chain)
- `spec_authoring_blockers` (pseudo-tokens that force BLOCKED)
- Overlap-dedup time estimation

What it does NOT do:
- Reason about the model's gauge/fermion/scalar content — it operates on declared chains, not model properties
- Probe tool availability at runtime (reads `constraints.yaml` status only, not `config.json`)
- Classify blockers (missing-skill vs fundamental-gap vs regime-mismatch)

The new skill should extend `time_budget.py`'s output (add a `blocker_class` field per blocked prereq) rather than replace it.

### 3. `config.json` is the runtime tool-availability source

The `/dark-matter-constraints` `check_prereqs.py` already probes `config.json` for `ufo_path`, `micromegas_path`, `maddm_path`, `drake_path`. The router skill should use the same pattern (read `config.json`; emit missing-tool blockers before attempting any chain). Current installed tools on this machine: Wolfram 14.3.0, SARAH 4.15.3, SPheno 4.0.5, MG5 3.5.6, MadDM 3.2.13, micrOMEGAs 6.0.5, DRAKE 1.0, DDCalc 2.2.0, HiggsBounds 5.10.2, HiggsSignals 2.6.2, FeynArts 3.11, FormCalc 9.10, LoopTools 2.16. Missing: Package-X (upstream dead), FeynCalc (no install skill), 2HDMC (no install skill), GamLike (no skill at all).

### 4. The MadDM split-file relic+DD output is a known structural issue

FU-wsf-06: relic density and direct detection live in two separate MadDM output files from two separate runs. The router skill (or its downstream consumers) must merge fields from both files. The `/maddm` SKILL.md reading section documents the field names for each; the router's cross-check comparison in Step 4b must handle the possibility that the relic run and DD run are in different directories.

### 5. `proxy_run: true` is a mandatory check before any result is reported

When micrOMEGAs runs on a proxy model (e.g., SingletDM proxy for singlet-doublet because CalcHEP `.mdl` files were not generated), the output JSON carries `proxy_run: true` and `_meta.proxy_model`. The router MUST:
1. Not report proxy values as native predictions
2. Not compute relic pulls against Planck using proxy numbers
3. Not apply LZ-SD or PICO cuts to proxy σ_SD
4. Tag every affected table row with `[proxy]`
5. Emit verbatim: `"micrOMEGAs run on proxy model (<description>); results do not apply to the target model."`

This check is behavioral (not enforced by any test that examines the actual emitted report).

### 6. `dark_su3.yaml:71` says `outputs: [ufo]` but analytic backend means UFO is never generated

The `outputs` field in the canonical dark_su3.yaml spec claims `[ufo]` but the `backends.spectrum: analytic` setting means SARAH/MG5 emission is never attempted. This is a latent spec inconsistency — the outputs field is aspirational/historical, not reflective of current capability. The router skill will need to check `backends.spectrum` independently of `outputs` when determining which tool chains are viable.

### 7. The 2HDM+a analytic module does not exist yet

`two_hdm_a.yaml` has `backends.analytic_module: analytic_models.stub_unimplemented`. The `/spheno-build` skill emits `ANALYTIC_MODULE_MISSING` for this model. DD/ID are blocked on `spec_authoring_blockers`. Relic is also currently blocked via the stub. This model cannot be routed to any constraint chain in its current state — the router skill should surface this as a "missing analytic module" blocker (distinct from "missing tool feature" and "fundamental gap").

### 8. The SARAH renderer has known failure modes for BSM non-abelian gauge groups

From the POST_MORTEM:
- `particles.py::render_ewsb()` only iterates `ewsb_mixings`; unmixed Dirac spinors and non-SM gauge bosons are not covered — triggers `CheckModelFiles::MissingOutputName`
- BSM ghosts need `Mass -> 0, PDG -> {0}, Width -> 0` on GaugeES stubs
- Dirac fermions with non-trivial gauge charges need RH Weyl in the anti-rep
- `Mixing::DifferentQN` can still trip even after rep flip — requires trivial MatterSector rotation

These are SARAH-renderer bugs that affect any BSM model with a non-abelian dark gauge group. The router skill should surface "SARAH renderer limitation" as a sub-category of the structural blocker classification.

### 9. Install surface and install skills

Install skills exist at:
- `/plugins/constraints/skills/ddcalc-install/`
- `/plugins/constraints/skills/higgstools-install/`
- `/plugins/constraints/skills/micromegas-install/`
- `/plugins/feynman-diagrams/skills/feynarts-install/`
- `/plugins/feynman-diagrams/skills/formcalc-install/`
- `/plugins/model-building/skills/feynrules-install/`
- `/plugins/model-building/skills/looptools-install/`
- `/plugins/model-building/skills/sarah-install/`
- `/plugins/model-building/skills/spheno-install/`
- `/plugins/monte-carlo-tools/skills/drake-install/`
- `/plugins/monte-carlo-tools/skills/maddm-install/`

No install skill for: GamLike, NuLike, FeynCalc, 2HDMC, Package-X (upstream dead), DarkELF. The router skill should map these gaps when classifying blockers.

### 10. The `scattering.schema.json` source enum is ambiguous

The router-contract schema for `scattering/v1` has an unstaged working tree change: `"source"` enum is `["micromegas", "package_x"]` in the merged codebase but `["micromegas", "looptools"]` in the working tree. Manager must decide: if LoopTools (standalone FormCalc chain) is now the intended second source of `scattering/v1`, the enum should be updated and committed. This affects what the DDCalc input-validation gate accepts.

---

**Key file paths for downstream use:**

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/_shared/constraints.yaml` — canonical compatibility registry (extend, don't replace)
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/_shared/time_budget.py` — render chain logic (extend)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/SKILL.md` — router contract (read; do not modify)
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py` — AND-gate pattern to reuse
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-demo/skills/_shared/assets/dark_su3.yaml` — canonical dsu3 spec (authoritative)
- `/Users/yianni/Projects/hep-ph-agents/plugins/model-building/skills/spheno-build/scripts/analytic_models/dark_su3.py` — analytic backend reference implementation
- `/Users/yianni/Projects/hep-ph-agents/plugins/model-building/skills/lagrangian-builder/assets/modelspec-templates/archived/README.md` — archive policy
- `/Users/yianni/.config/hep-ph-agents/config.json` — runtime tool-path registry (probe availability same way `/demo` Step 0 does)
- `/Users/yianni/Projects/hep-ph-agents/.shift-manager/run-20260425-dmc/install/MANIFEST.md` — installed versions snapshot
