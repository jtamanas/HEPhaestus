# Scoping: 3 demo models playtest run

## Models

### Model 1: Singlet-Doublet
- **Location**: `/plugins/hep-ph-demo/skills/singlet-doublet/`; benchmark in `eval/2506.19062_wimps_blind_spots/models/singlet_doublet.py`
- **Paper**: arXiv:2506.19062 §II (Arcadi & Profumo)
- **Status**: Working end-to-end. Single successful run with relic `Ω h² = 0.163` (23 Apr 22:32). Uses analytic-bypass path for SPheno (avoids SARAH-to-Fortran RGE compilation bug).
- **How to run**: Via `/demo` skill → select "Singlet-Doublet" → choose constraints → `/sarah-build` → `/spheno-build [analytic]` → `/madgraph` → `/maddm`
- **Success criteria**: Finite `Ω h²` lands in `demo_output/singlet-doublet/relic.json` and `summary.json`
- **Known issues**:
  - SPheno Fortran compile fails on SARAH-emitted RGEs (undeclared symbols `SAxDynkin`, `SAxCasimir`); workaround: analytic backend ✓
  - MadDM plugin loader chokes on sibling backup dirs in `PLUGIN/`; cleanup needed
  - No direct-detection constraint ready (blocks `/feynarts`, `/formcalc`, `/ddcalc`)
- **Latest artifact**: `demo_output/singlet-doublet/summary.json` (23 Apr 22:33); playtest run in `retry_analytic/drive.py`

### Model 2: 2HDM+a
- **Location**: `/plugins/hep-ph-demo/skills/2hdm-a/`; benchmark in `eval/2506.19062_wimps_blind_spots/models/two_hdm_a.py`
- **Paper**: arXiv:2506.19062 §III (Arcadi & Profumo)
- **Status**: Working end-to-end as of 22 Apr. Single relic result `Ω h² = 10.15` (off-resonance, Mχ=100, Ma=400, tan β=10).
- **How to run**: Via `/demo` → select "2HDM+a" → constraints → `/sarah-build` [uses hand-crafted PortalDM idiom, not auto-rendered] → `/spheno-build` → `/madgraph` → `/maddm` with param-card patcher post-output
- **Success criteria**: Finite `Ω h²` in MadDM output; no `-1.0` sentinel
- **Known issues & gotchas** (all documented in `demo_output/2hdm-a/fix_loop/POST_MORTEM.md`):
  - SARAH renderer NOT fixed: `/sarah-build` cannot yet emit the PortalDM Dirac-idiom correctly. Working `.m` files hand-crafted at `/Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix/`. Renderer needs 7 patch sites.
  - SARAH gotchas: Dirac singlet is TWO separate left-Weyls (not paired-field syntax), one with `conj[]`; `DEFINITION[EWSB][Phases]` required; `\[ImaginaryI]` prefix for CP-odd Yukawa; field-name (not component-name) in Lagrangian; `Mchi → mchi` (SARAH adds M prefix); field `a → a0` (collision with gauge boson A)
  - MG5/MadDM: YUKAWA blocks must split (yu, yd, ye separate blocks, not one); phase fields default to 0+0i → param-card patcher mandatory (sets PHASES[1]=1.0); on-resonance hangs indefinitely
  - Param-card patcher: 60-line script at `demo_output/2hdm-a/fix_loop/iter_8_patch_paramcard.py` mandatory to get finite result
- **Latest artifact**: `demo_output/2hdm-a/fix_loop/POST_MORTEM.md` + iter-8 MadDM run

### Model 3: Dark SU(3)
- **Location**: `/plugins/hep-ph-demo/skills/dark-su3/`; benchmark in `eval/2506.19062_wimps_blind_spots/models/dark_su3.py`
- **Paper**: arXiv:2506.19062 §IV (Arcadi & Profumo)
- **Status**: Working via analytic backend (not MG5). Returns `Ω_V h² = 1.30e-9` and `Ω_Psi h² = 1.04e-7` at BP1 (analytic approximation, **not paper's micrOMEGAs values**).
- **How to run**: Via `/demo` → select "Dark SU(3)" → constraints → `analytic_models.dark_su3` (Lee-Weinberg + Breit-Wigner approximation, no SARAH/SPheno/MG5)
- **Success criteria**: Per-candidate `Ω_*_h²` in `diagnostics.json` alongside `summary.json`; diagnostics JSON persisted (not dropped by SLHA round-trip)
- **Known issues** (documented in `demo_output/dark-su3/fix_loop/POST_MORTEM.md`):
  - **Fundamental mismatch**: SKILL.md describes confining dark sector (dark pion, HLS-like); paper's actual model is SU(3)_D → SU(2)_D Higgsing (vector + pseudoscalar DM from Higgsing, not confinement). Iter-4 analytic module implements correct physics; SKILL.md + practitioner_script.md + YAML still describe wrong model. Rewriting pending.
  - **MG5 dark-color wall**: SARAH emits dark color indices `dt1..dt4` that MG5 has no algebra for. No user-extensible registration. Do not chase MG5 path.
  - SARAH renderer fixes (iters 1–3) are standalone wins: `render_ewsb()` now emits EWSB entries for unmixed Dirac + non-SM gauge bosons; ghost stubs get `Mass→0, PDG→{0}`; unmixed Dirac `OutputName` strips F prefix. These benefit future BSM models with non-abelian dark groups.
  - `/demo` gate logic fixed: `analytic_only_constraints: [relic]` + 2-line time_budget.py guard prevents multi_component_prereq auto-appending the dark-matter-constraints combiner for single-candidate observables
- **Latest artifact**: `demo_output/dark-su3/fix_loop/POST_MORTEM.md` + iter-5 analytic run

---

## Practitioner script

- **Definition**: Scripted answers to the `/lagrangian-builder` interview questions (Q1: what's the model? Q2: new fields/gauge groups? Q3: confirm enumerated Lagrangian edits? Q4: confirm post-EWSB mixing detections?). Simulates a physicist cold-reading the paper and riffing at a whiteboard. Q3 and Q4 are **deltas against Claude's drafts**, not full specs.
- **Location**: Three files under `/plugins/hep-ph-demo/skills/<model>/practitioner_script.md` for singlet-doublet, 2hdm-a, dark-su3. Full specifications exist.
- **Format**: Markdown with Q/A pairs. Q1–Q2 self-contained prose; Q3–Q4 bullet-list edits against Claude's enumerated drafts (field names, parameter renames, term deletions, matrix renames).
- **Example invocation**: Via `/demo` → model selection → Step 4a invokes `/lagrangian-builder` with `--practitioner-mode=true` and reads practitioner_script.md to auto-answer all four questions; produces final YAML diff against the reference.
- **Status**: All three practitioner scripts written and in repo. Singlet-doublet is actively used (working playtest); 2hdm-a and dark-su3 scripts exist but dark-su3 is now stale (SKILL.md physics description doesn't match script).

---

## End-to-end run pattern

**Entrypoint**: `/demo` skill (plugins/hep-ph-demo/skills/demo/SKILL.md)

**Phases**:
1. **Preflight** (Step 0): Read config.json, verify SARAH, SPheno, MG5, Wolfram respond. Fail fast if any missing.
2. **Intro** (Step 1): Print Arcadi-Profumo blind-spot hook.
3. **Model picker** (Step 2–3): User selects singlet-doublet / 2hdm-a / dark-su3.
4. **Per-model workflow** (Steps 1–4 in per-model skill):
   - Step 1: DM-candidate declaration + reference Lagrangian
   - Step 2: Constraint multi-select (relic / DD / ID / collider)
   - Step 3: Time estimate + chain visualization + gate confirmation
   - Step 4: Execution — drive `/lagrangian-builder` [via practitioner script] → `/sarah-build` [or skip for analytic] → `/spheno-build` → `/madgraph` [or skip for analytic] → `/maddm` [or skip for analytic]
5. **Closure** (per-model return): Write `demo_output/<model>/summary.json` + any constraint results

**Outputs land in**: `demo_output/<model>/` (gitignored). Per-model:
- `summary.json`: top-level result manifest
- `relic.json` / `dd.json` / `id.json`: per-constraint results (structure varies)
- `singlet_doublet_spec.yaml` (or equivalent): final autored ModelSpec
- `summary.pdf` / `.png`: plots (matplotlib + LaTeX if available)
- `maddm_run/`: MG5/MadDM working directory (if chain ran)
- `diagnostics.json`: physics metadata (e.g., analytic approximation flags for dark-su3)

**Success definition**: User sees a printed line with non-empty artifact path, final summary displays.

---

## Tool availability

| Tool | Required by | Installed? | Verify cmd | Status |
|---|---|---|---|---|
| **Wolfram Engine** | SARAH | ✓ (configured) | `wolfram -version` | Required; blocks SARAH build |
| **SARAH 4.15.3** | `/sarah-build` → UFO emission | ✓ (@ `/Users/yianni/SARAH/SARAH-4.15.3/`) | `math -run "Get[\\\"...m\\\"]; Quit[]"` on test model | Working; renderer needs PortalDM backport (2HDM+a) |
| **SPheno 4.0.5** | `/spheno-build` → spectrum | ✓ (binary via compile) + **✓ (analytic path)** | `spheno --version` | Compile path broken (RGE emit bug); analytic bypass ✓ for singlet-doublet/2hdm-a |
| **MadGraph5_aMC@NLO** | `/madgraph` → UFO import + ME gen | ✓ (@ `${MG5_PATH}`) | `mg5_aMC --help` | Working; plugin loader needs backup cleanup; dark-color wall blocks dark-su3 |
| **MadDM** | `/maddm` → relic density + cross-sections | ✓ (plugin in MG5) | `mg5_aMC` → `import model ... → generate relic_density` | Working for singlet-doublet/2hdm-a with param-card patcher for 2hdm-a |
| **micrOMEGAs** | Dark-su3 paper (for reference) | ✗ (not installed) | N/A | Not needed; analytic backend replaces it |
| **FeynArts** | `/feynarts` → diagrams | ✗ (PLANNED) | N/A | Blocks DD constraint |
| **FormCalc** | `/formcalc` → loop amplitudes | ✗ (PLANNED) | N/A | Blocks DD constraint |
| **DDCalc** | `/ddcalc` → SI/SD rates | ✗ (PLANNED) | N/A | Blocks DD constraint |
| **GamLike** | `/gamlike` → indirect-detection gamma profiles | ✗ (PLANNED) | N/A | Blocks ID constraint |

Key dependency: **Wolfram Engine blocks SARAH**, which blocks all spectrum work. If Wolfram is unavailable, entire demo falls at preflight. SPheno compile is broken; analytic backend is the working path.

---

## Recommended workstream split

### Singlet-Doublet
**Recommendation**: Playtest in parallel with 2HDM+a. No shared state (independent ModelSpec YAML, independent SARAH runs, independent SPheno analytic modules). **Blocker to resolve before playtest**: Ensure `/Users/yianni/SARAH/` mount / installation is stable across overnight runs; confirm MadDM plugin loader cleanup (backup dirs in PLUGIN/) is idempotent. **Playtester task**: Re-run end-to-end, verify relic.json structure, confirm summary.json writes correctly, stress-test analytic SPheno backend under repeated calls.

### 2HDM+a
**Recommendation**: Playtest in parallel with singlet-doublet. Depends on hand-crafted SARAH files (not auto-rendered). **Critical blocker**: The seven renderer sites listed in `iter_6_notes.md` need the PortalDM idiom backport into `/sarah-build` before this model can run from YAML alone. Without the patch, runs will fail at SARAH step trying to emit Dirac idiom. **Immediate unblock**: Either apply the renderer patches (medium effort, ~4 skill-layer sites) or document that playtesters must copy hand-crafted `.m` files from `/Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix/` before `/sarah-build` can run. **Playtester task**: Walk the fixed pipeline end-to-end, verify param-card patcher is invoked post-MG5-output, check that Ωh² stays finite across benchmark points, stress on-resonance behavior (expect hang; off-resonance should complete in 3–5 min).

### Dark SU(3)
**Recommendation**: Playtest independently from singlet-doublet / 2HDM+a. **Critical blocker**: The SKILL.md, practitioner_script.md, and YAML describe the wrong model (confining, dark pion) vs. the paper (SU(3)_D → SU(2)_D Higgsing, vector + pseudoscalar DM). The analytic backend (iter-4) is correctly physics-implemented, but the surrounding skill prose will confuse playtester. **Before playtest**:
1. Rewrite SKILL.md Step 1 to match paper's actual Higgsing picture (cite Eqs. 26–30 explicitly).
2. Rewrite practitioner_script.md Q1/Q2/Q3/Q4 to describe SU(3)_D gauge singlets + dark Higgs doublet (not pions).
3. Update `dark_su3.yaml` field content to match (dark Higgs doublet + gauge bosons, not UV fermions).
4. Confirm iter-5 analytic module still works post-rewrite.

**Playtester task**: Once rewritten, verify end-to-end relic flow, check diagnostics.json is persisted, validate `relic_approx: True` flag is set (signals Lee-Weinberg approximation, not exact), compare per-candidate Ω values to paper's micrOMEGAs results (expect order-of-magnitude agreement, not exact).

---

## Open questions

1. **SARAH installation persistence**: Hand-crafted `TwoHdmAfix/` model files live at `/Users/yianni/SARAH/SARAH-4.15.3/Models/`. Are these committed to the repo under git-lfs, or mounted from a separate SARAH build? If mounted, what's the recovery plan if the mount is unavailable during overnight playtest?

2. **Param-card patcher availability**: The 2HDM+a playtest relies on `demo_output/2hdm-a/fix_loop/iter_8_patch_paramcard.py`. Is this one-off debug artifact, or should it be baked into `/maddm` skill as a generic Dirac-phase-field patcher? How does it get invoked in the automated playtest?

3. **Dark-su3 model mismatch**: Confirmation needed that iter-4 analytic module's Lee-Weinberg formula is the intended fallback, not a placeholder pending micrOMEGAs integration. If micrOMEGAs is future work, should dark-su3 playtest be deferred until SKILL.md is rewritten and model description is correct?

4. **Offline tool availability**: The overnight run has no network access. Confirm `/Users/yianni/SARAH/`, `${MG5_PATH}`, SPheno binary, and Wolfram Engine are all locally installed and paths are baked into config.json. If any tool requires license-server contact (e.g., Mathematica license check), will offline mode fail?

5. **SPheno analytic backend scope**: Singlet-doublet uses it; is the same analytic path ready for 2HDM+a, or does 2HDM+a require full SPheno Fortran compile? If compile is still broken, what's the blocker preventing analytic backport?

6. **Multi-model parallel state**: If playtesting all three models in parallel, do they share config.json, common SARAH/SPheno/MG5 work dirs, or are they fully isolated? Any race conditions on temp file creation (MadDM run dirs are hash-suffixed; SPheno compile dirs?)?

7. **Practitioner script automation**: The practitioner scripts are markdown; how are they parsed and injected into `/lagrangian-builder` Q3/Q4 auto-answer flow? Is there a skill that reads practitioner_script.md line-by-line and drives the interview, or does Claude's context just read the file cold?
