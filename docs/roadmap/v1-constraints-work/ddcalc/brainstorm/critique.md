# `/ddcalc` — Skeptical critique

Proposer's brief is competent on the installer plumbing and weak on the physics-content decisions and cross-skill contracts. Below: quote → counterargument → synthesizer action.

---

## 1. DDCalc version and experiment tables

> "Pin `HEPPH_DDCALC_VERSION=2.2.0` in `skill_env.yaml` … upstream at GitLab `https://gitlab.com/C0RI0LIS/ddcalc`."

The proposer asserts 2.2.0 as canonical without justifying currency. DDCalc's upstream has historically been Jan Conrad / Chris Savage / Felix Kahlhoefer at the Hepforge Redmine; the GitLab `C0RI0LIS/ddcalc` mirror is a **personal fork**, not the canonical upstream. Pinning the plugin to a fork URL is a supply-chain mistake — one bad-day push by that maintainer and every rebuild breaks. Second, DDCalc 2.2.0 (2021) predates **LZ WS2022**, let alone LZ WS2024. Its bundled experiments are LUX 2016, PandaX-II 2017, XENON1T 2018, PICO-60 2019, DarkSide-50 2018. The proposer's output JSON promises an `LZ_2024` key — DDCalc 2.2.0 does not have that likelihood. This is a correctness blocker, not a UX nit.

The proposer then tries to paper over this with `HEPPH_DDCALC_EXPT_OVERLAY=<dir>` claiming experiment files live at `data/experiments/*.eff/*.dat` and can be rsync-overlaid. The actual DDCalc 2.2.0 layout has experiment definitions **compiled into Fortran modules** under `src/experiments/` (e.g. `LUX_2016.f90`) plus tabulated efficiency data. You cannot add a new experiment by dropping a file into a data dir; the efficiency binning, exposure, background model, and likelihood constructor (Poisson vs maximum-gap vs binned Poisson) are all Fortran code that links into `libDDCalc.a`. An "overlay" that silently rsyncs over efficiency tables for an existing experiment would produce a nonsense likelihood because the exposure constant is hardcoded.

**Synthesizer action:** (a) confirm authoritative DDCalc upstream (Savage et al. at `ddcalc.hepforge.org` or the DarkBit fork maintained inside GAMBIT). (b) Drop the `HEPPH_DDCALC_EXPT_OVERLAY` fantasy. Either patch-and-rebuild DDCalc with a new Fortran module per experiment, or wrap a different tool (GAMBIT's DarkBit, or directly the LZ public likelihood from `lz_lib`). (c) If `LZ_2024` is required for the paper, block the whole skill until we pick a realistic path — do not ship promising a key we cannot produce.

---

## 2. Neutrino fog source

> "use the Ruppin/O'Hare 2018 Xenon ν-floor curve tabulated in `plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_xe.csv` rather than DDCalc's built-in … O'Hare+ 2021 'neutrino fog' with the gradient-based definition is what the Arcadi–Profumo blind-spots paper overlays."

Three problems. First, the O'Hare 2021 neutrino-fog gradient definition (`dlog(σ)/dlog(exposure) = -2/n`) is **not interchangeable** with the older Ruppin/Billard neutrino-floor definition (discovery-limit 90 % CL at fixed exposure); they give different curves. The proposer conflates them in one data file named `neutrino_fog_xe.csv`. Second, O'Hare's 2021 curves are published in the paper's Mathematica notebooks under a specific licence — vendoring the CSV into the repo needs a licence check (at minimum attribution; possibly CC-BY). Third, Arcadi–Profumo 2506.19062 does not necessarily use O'Hare 2021 — without citing the paper's specific overlay source, the proposer is guessing and baking that guess into a default. This is exactly the kind of "augment not replace" violation the user memo flagged: we would be shipping our own curve instead of driving the tool's.

**Synthesizer action:** default to **DDCalc's built-in ν-floor**, not a vendored CSV. If the paper-reproduction chain needs O'Hare 2021, drive it as an opt-in overlay with explicit citation and licence note in a `NOTICE` file. Verify against Figure 6/7 of 2506.19062 what curve was actually used before making it the default.

---

## 3. `reference_only` enforcement point

> "`DDCALC_REFERENCE_ONLY` … only used when `HEPPH_ALLOW_REFERENCE=1` is explicitly set. Default: block. This is the 'augment not replace' rule."

This fights the three-state blocker schema. `reference_only` in `_shared/blocker.schema.json` is a **result status**, not a blocker — it has `status`, `reference_method`, `caveats`, no `mode` field. The proposer lists it alongside fatal blockers, which is a category error. More importantly, the enforcement decision ("block on reference_only unless opted in") belongs in the `/lagrangian-builder` orchestrator or in a shared policy module, not baked into every leaf skill with its own env var. Every skill inventing its own `HEPPH_ALLOW_*` knob creates UX chaos for scans and for automated orchestration.

**Synthesizer action:** remove `DDCALC_REFERENCE_ONLY` from the blocker table. Do not emit `reference_only` from `/ddcalc` at all — DDCalc is the tool, there is no analytic fallback that makes sense here (Lewin-Smith 1995 is a σ→R conversion, not an exclusion likelihood). Have the orchestrator enforce "no reference_only in production" as a global policy, reading the schema directly.

---

## 4. Input contract: `scattering.json`

> `sigma_SI_p_cm2`, `sigma_SI_n_cm2`, `sigma_SD_p_cm2`, `sigma_SD_n_cm2`, `m_DM_GeV`, `halo`.

Cross-checking the micromegas and looptools proposals:

- micromegas/brainstorm/proposal.md `summary.json` writes `sigma_si_proton_cm2`, `sigma_si_neutron_cm2`, `sigma_sd_proton_cm2`, `sigma_sd_neutron_cm2` — **lowercase, different key names**. Proposer's `sigma_SI_p_cm2` does not match. Silent schema drift will land on day one.
- formcalc/brainstorm/proposal.md writes `sigma.json` with `{sigma_si_proton_cm2, sigma_si_neutron_cm2, ..., operator_coeffs: {...}}`. Again lowercase, and with `operator_coeffs` that `/ddcalc` ignores but which would be dropped on a schema-strict read.
- None of the three proposals defines a shared **schema file**. Without a committed `_shared/scattering.schema.json` plus a pre-commit validator, the contract is aspirational.

Further: the proposer's schema covers only isospin-split point couplings. It lacks (a) **NREFT operator coefficients** (O1…O15) that DDCalc actually consumes if you want anything beyond standard SI/SD — DDCalc's `SetWIMP_NREFT_CPT` API wants 28 coefficients, not 4 numbers; (b) **momentum-dependent form factors** (e.g. for loop-induced anapole, magnetic-dipole DM); (c) any way to flag **CP-violating scattering** or **velocity-dependent cross sections**, both of which the 2HDM+a blind-spot analysis can produce.

**Synthesizer action:** (a) commit `plugins/hep-ph-toolkit/skills/_shared/scattering.schema.json` as the single source of truth, referenced by all three skills. (b) Pick one convention: lowercase `sigma_si_proton_cm2` matches what upstream `/micromegas` and `/formcalc` already propose — `/ddcalc` must adopt it. (c) Add an optional `nreft_coefficients` block and an optional `form_factor` callable spec; document that v1 supports only the SI/SD contact-operator subset and explicitly blocks NREFT input with `DDCALC_NREFT_NOT_SUPPORTED` (fatal) so users don't silently get wrong answers.

---

## 5. Halo, sub-GeV, Migdal

The proposer lists halo marginalization as "opt-in, default off" in open questions, and scopes out sub-GeV and Migdal entirely. This is defensible for a v1, but the proposer does not acknowledge that the Arcadi–Profumo paper's exclusion boundary shifts materially under halo uncertainty — a factor of ~2 on σ at fixed mass — which is larger than the tree-vs-loop distinction the skill is advertised to resolve. Shipping fixed-SHM defaults without even a warning in the output JSON reports false precision.

The proposer also punts on **velocity distribution** choices (Maxwell-Boltzmann vs N-body SHM++ vs observed Gaia halo) as if they were synonymous. DDCalc 2.2.0 does support non-SHM halos via `SetHalo`; the skill brief never mentions the interface.

**Synthesizer action:** (a) require the output JSON to include a `halo_systematic_band` even in single-point mode (±2σ under SHM → SHM++ → Gaia-sausage substitution). (b) Explicitly emit `DDCALC_MASS_OUT_OF_RANGE` with `context.suggested_tool = "LZ_Migdal_likelihood"` for sub-GeV, not just a silent recoverable. (c) Document Migdal/sub-GeV as a known gap in the skill README, not just an open question.

---

## 6. Plugin placement and marketplace consistency

All three Phase A proposals (micromegas, ddcalc, higgstools) independently claim `plugins/constraints/` is the right home. Good — they agree. But none of them addresses:

- The looptools proposal instead argues for `plugins/loop-computation/` for the Phase B stack. Is `/ddcalc` in `plugins/constraints/` while its upstream data producer `/formcalc` is in `plugins/loop-computation/` really what we want? The data contract crosses a plugin boundary; `_shared/scattering.schema.json` must live in `plugins/shared/schemas/` (currently non-existent), not under either plugin.
- The CLAUDE.md category table in the project root does not yet have a "Constraints" row — all three proposals claim they'll add it, which will produce a merge conflict unless coordinated.
- `.claude-plugin/marketplace.json` needs three new plugin entries; sequencing matters.

**Synthesizer action:** land `plugins/constraints/` + `plugins/shared/schemas/scattering.schema.json` in a dedicated prep PR **before** any of the three skills merge. Update `CLAUDE.md` + `marketplace.json` in that same prep PR to eliminate the three-way conflict.

---

## 7. Scan parallelism and state-file races

> "`/ddcalc --from-looptools <path> --scan-index <scan_index.csv>` runs per-point, writes `ddcalc_scan.csv`."

Two issues. First, `/spheno-build`'s `scan_index.csv` is **write-once** per scan and the runs dir is read-only after the scan completes. `/ddcalc --scan-index` is conceptually a **second pass** over that dir — fine — but the proposer does not say where `ddcalc_scan.csv` is written. If it goes in the same `runs/scan_<TS>/` dir, two concurrent `/ddcalc` invocations race on the filename. Second, the `config.models[<name>].latest_*` keys written by `/spheno-build` are single-valued — a downstream scan invocation that updates those mid-scan will desync. Third, the proposer says "serial in v1" for parallelism, which is fine, but does not address what happens when a user runs `/ddcalc --from-looptools A.json` and `/ddcalc --from-looptools B.json` concurrently — they share `$HEPPH_DDCALC_EXPT_OVERLAY` rsync state.

**Synthesizer action:** scan output must go to a timestamped sibling directory (e.g. `$STATE_ROOT/models/<name>/ddcalc_runs/<TS>/ddcalc_scan.csv`), never overwrite `/spheno-build` artefacts. Lock file under `$STATE_ROOT/.locks/ddcalc_overlay` around any overlay-rsync operation. Document the state-file ownership matrix in `plugins/constraints/SHARED.md` before the first merge.

---

## Open questions the proposer missed

1. **DDCalc licence.** Is DDCalc MIT / GPL / custom academic? Can we redistribute experiment-overlay CSVs alongside it?
2. **SHA256 pin authoring.** Proposer insists "no TODO placeholder" but does not supply the actual value. Where does it come from and who is on the hook for re-computing it on upstream refresh?
3. **macOS `-std=legacy` gfortran.** Proposer waves at this as "force via FFLAGS." On Homebrew gfortran 14, the DDCalc 2.2.0 build also hits a `-fallow-invalid-boz` requirement. Has anyone actually built it recently on Apple Silicon?
4. **Relationship to `/higgstools` p-value reporting.** `/higgstools` proposal (open Q 6) also asks about p-values from chi² — three constraint skills, three ad-hoc p-value conventions. Need a shared `_shared/pvalue.py`.
5. **Reproducibility of overlay datasets.** If an overlay is a separate git repo (à la `hbdataset`), how is its commit SHA recorded in `ddcalc` output? Proposer records `experiment_overlay` path + sha256 but not a git commit.
6. **What exactly is `DDCalc_exampleC` printing?** Proposer parses `DDCalc ([0-9.]+)` from its output, but the stock `DDCalc_exampleC` in 2.2.0 prints a header that does *not* include a bare version number — it prints a copyright banner. The probe regex as written will fail. This should be verified with an actual build, not inferred.
7. **`/micromegas`-vs-`/formcalc` precedence.** If a user has both tree-level σ from `/micromegas` and loop-level σ from `/formcalc` for the same point, does `/ddcalc` pick one, combine, or refuse? Proposer never says.

---

**Bottom line.** The installer-plumbing story is coherent and reuses `_common.sh` cleanly. The physics-content and cross-skill-contract story is weak: the DDCalc version/LZ-2024 promise is under-evidenced, the overlay mechanism may not work at all, the `scattering.json` schema silently disagrees with its two upstream producers, and `reference_only` is mis-modelled against the blocker schema. Ship nothing until the DDCalc version + experiment-set question is settled with an actual build test, and land the shared schema + plugin skeleton as a prep PR before any of the three Phase A skills merge.
