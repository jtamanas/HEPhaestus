# /higgstools — Critic pushback

Adversarial pass on `proposal.md`. Format per attack vector: quote → counter → synthesizer action. I am not reconciling; I am surfacing every crack I see.

---

## 1. Backend: "HiggsTools unified" as default is a trap for W-phase v1

> "Recommendation: default to HiggsTools unified... but support a `--backend legacy` escape hatch."

**Counter.** The proposal glosses the single biggest integration risk in the whole skill. HiggsTools is a `cmake` + `Eigen3` + `GSL` + `Boost` + `pybind11` C++17 library. There is **no official wheel on PyPI** as of late 2024 — you get it from GitLab source only. On macOS with Apple Silicon, `pybind11` + system Python + a non-conda Eigen/GSL combination routinely blows up on `std::filesystem` linkage and on Homebrew's ABI-incompatible libstdc++. The proposal's toolchain check ("cmake ≥ 3.16, g++ ≥ 9, python3 with pybind11 headers") is a half-truth — it will pass, then `cmake --build` will fail three minutes in on Eigen template depth or Boost version skew. `/sarah-install` got away with "download a tarball" because SARAH is a pile of `.m` files. HiggsTools is a real C++ build, and the closest comparable precedent in this repo is `/spheno-install`, which *also* has one known-good gfortran flag dance. Defaulting to unified means the first-time user hits a compile wall in what is advertised as a drop-in constraint skill.

By contrast, legacy HB-5.10.2 + HS-2.6.2 are pure Fortran, have been built by every BSM group on the planet since 2020, consume SLHA directly (no adapter), and match the arXiv:2506.19062 reference literature. The roadmap's own "augment not replace" rule argues for the tool that the cited paper actually used.

**Synthesizer action.** Flip the default: `--backend legacy` is default for v1; unified is opt-in behind `HEPPH_HIGGSTOOLS_BACKEND=unified`. Gate the unified path on a CI matrix that actually compiles it on macOS-14 arm64 and ubuntu-22.04 before promoting it. Document the "unified library pypi status" explicitly in `skill_env.yaml` with a link to the GitLab issue tracking pip installability. If upstream ships a wheel before v1 release, revisit.

---

## 2. Dataset pin story is under-specified and probably wrong

> "`hbdataset` commit `HEAD@{2024-09-01}` ... Datasets are pinned independently from the code."

**Counter.** Three problems. First, `HEAD@{2024-09-01}` is not a git pin — it is a reflog expression that resolves on the *cloner's* machine, not a fixed SHA. The proposal says "SHA pin" in the config keys section but specifies a date-based ref in the upstream section. That mismatch is a reproducibility hole you could drive a truck through.

Second, does `hbdataset` and `hsdataset` actually exist as separate public GitLab repos under `higgsbounds/`? The proposer asserts this but does not show evidence. Historically HB-5 shipped its dataset inside the source tree (`data/`), and HS-2 did the same. The "split dataset repo" claim needs a URL check before we commit to it — if it turns out the datasets live inside the HiggsTools monorepo's `data/` subdir, the entire "pin independently" story collapses into "pin the same repo twice."

Third, the incremental-dataset-update story ("paper authors publish a new LZ result — who updates?") is not answered. `update-dataset` pulls a new SHA; fine; but who *generates* the new SHA-pinned release? Upstream HiggsTools releases datasets on no fixed cadence. If ATLAS publishes H→ττ high-mass in June 2026, does the user wait for HiggsTools maintainers, or does the skill support a user-local dataset overlay à la `/ddcalc`'s `HEPPH_DDCALC_EXPT_OVERLAY`?

**Synthesizer action.** (a) Replace `HEAD@{2024-09-01}` with a real SHA or, preferably, a GitLab release tag — verify tags exist on the actual repos before committing. (b) Audit the upstream layout before finalizing the proposal: if the datasets live inside the HiggsTools monorepo, drop the "pinned independently" claim and treat the dataset as part of the source pin. (c) Copy the `/ddcalc` overlay pattern (`HEPPH_HIGGSTOOLS_DATASET_OVERLAY`) so users can drop in a new limit without waiting for an upstream release — the constraints plugins should have a *consistent* dataset-overlay story, not one per skill.

---

## 3. Non-SLHA input path hand-waves the hardest case

> "`--native <path>` — bypass SLHA and consume a HiggsTools-native YAML input (for models whose couplings aren't representable in SLHA `HiggsBoundsInput*` blocks)."

**Counter.** The proposal confuses two issues. Issue A: SARAH-generated SPheno does write `HiggsBoundsInputHiggsCouplingsFermions/Bosons` blocks *when the model is configured for it* (it is not automatic — you need the right `SPheno.m` directives in SARAH and sometimes manual patches). Issue B: 2HDM+a is claimed in §4 to be "CP-conserving at tree level" but the open question #2 in §6 then says "2HDM+a has CP-violating mixing that sometimes breaks the `HiggsBoundsInput*` block ordering." Which is it? The proposer contradicts himself within one document.

If 2HDM+a mixing is CP-conserving at tree level (correct), the SLHA `HiggsBoundsInput*` path works. If there is CPV from one-loop or from the a-h0 mixing matrix being complex, then the SLHA effective-coupling convention cannot represent it and the `--native` YAML is mandatory. The proposer's "fallback: compute effective couplings from `Block MASS` + decay tables — emit caveats" is a euphemism for reimplementing part of HiggsBounds' input layer in Python, which is exactly what the augment-not-replace rule forbids.

**Synthesizer action.** (a) Pick a lane. For v1 with arXiv:2506.19062 (CP-conserving tree), the SLHA path is sufficient; drop the `--native` subcommand from v1 scope and the analytic effective-coupling fallback entirely. Raise a fatal blocker if SLHA blocks are missing instead of trying to synthesize them. (b) File a follow-up ticket for `--native` + CPV support tied to whichever paper first needs it. (c) Resolve the CP-structure claim: 2HDM+a with complex a-mixing *can* be CPV — state the v1 assumption explicitly in SKILL.md.

---

## 4. Output semantics don't match the paper's exclusion convention

> "`result.json` | `{allowed: bool, obsratio: float, most_sensitive: {...}, chi2_total, chi2_rates, chi2_masses, ndof, pvalue}`"

**Counter.** The proposal does not cite which exclusion convention arXiv:2506.19062 uses. HB's default is `obsratio < 1` at 95% CL from the most sensitive single channel (Bechtle et al. procedure). HS chi² is a *separate* test, typically cited as Δχ² < 6.18 for 2D 95% CL contours or Δχ²_min for best-fit. The proposer's `allowed: bool` smashes both into one boolean — but HB-allowed + HS-excluded is the common case (no HB channel hits, but 125 GeV Higgs rate mismatches ATLAS/CMS combined). The boolean loses that signal.

Further: the paper almost certainly uses HB-5's `--usepdg` effective-coupling input mode with the specific channel set for heavy neutral + charged Higgs. Without a concrete paper-Table reference in the proposal, we cannot verify the output schema matches what a user needs to reproduce fig. 8.

**Synthesizer action.** (a) Split `allowed` into `hb_allowed: bool` and `hs_consistent: bool` (the latter at user-chosen Δχ² threshold, default 6.18). (b) Before implementation, read arXiv:2506.19062 §4 (or wherever HB/HS enters) and *quote the exact exclusion convention* in the SKILL.md — if they cite Δχ² < 5.99 for 2D or a p-value cut, the schema must express it. (c) Add `hb_channel_list` to the output as an array of all channels *tried*, not just the most sensitive — users doing chi² marginalization need the full set.

---

## 5. Plugin placement — the "new plugin" claim needs a stronger test

> "Proposal: new `plugins/constraints/` plugin housing `/higgstools`, `/micromegas`, `/ddcalc`."

**Counter.** All three sibling proposals (ddcalc, micromegas, higgstools) independently arrive at the same "new `plugins/constraints/`" conclusion. That consensus is actually a warning sign, not a confirmation: three proposers each wanted to declare their own turf. The real question is whether `plugins/constraints/` shares enough *implementation* to justify being one plugin vs. three loosely-related plugins under a shared marketplace category.

Shared code the proposals hint at: `_shared/expt_overlays/`, `_shared/scattering.schema.json`, `_shared/blocker.schema.json` reference. That is thin. The bigger question the proposer dodges: `/higgstools` consumes SLHA straight from `/spheno-build`'s `latest_slha` config key. Its natural home — by data flow — is adjacent to `/spheno-build`, not adjacent to `/ddcalc` (which consumes a `scattering.json` from `/micromegas`). The semantic-grouping argument ("constraints") wins over the data-flow argument ("SLHA consumer"), but only by a narrow margin, and the proposer never weighs the two.

**Synthesizer action.** Accept `plugins/constraints/` as the v1 placement (consistency with ddcalc/micromegas proposals, and the marketplace category table in CLAUDE.md has an obvious "Constraints" slot). But: require the synthesizer to document in `plugins/constraints/SHARED.md` the cross-plugin contract — specifically that `/higgstools` reads `config.models[<name>].latest_slha` written by `/spheno-build` in a *different* plugin, and that this cross-plugin dependency is intentional. Do not let it slide unremarked.

---

## 6. Scan parallelism vs W4 determinism — non-problem dressed as a problem

> "Do we parallelize over scan points here, or stay sequential to match the W4 determinism contract?"

**Counter.** W4's determinism contract is about *SPheno output being byte-identical for a given input*, not about scan parallelism. Each HiggsTools evaluation reads one SLHA file and writes one `result.json`. There is no shared mutable state. Parallelize at will; sort the output CSV at the end. The only risk is nondeterministic *ordering* of log lines, which is cosmetic.

**Synthesizer action.** Kill this as an open question. State in SKILL.md: "scan mode is parallel across points with `multiprocessing.Pool(os.cpu_count())` by default; `--serial` flag for debugging. Output `higgstools_index.csv` is sorted by `index` column so it is byte-identical across runs regardless of worker count." Done.

---

## 7. Subcommand surface area is bloated

> "`/higgstools run | exclude | signals | scan-summary <run_dir>`"

**Counter.** Four subcommands for what is fundamentally "run HiggsTools on one SLHA and emit a JSON" is overkill for v1. The `/sarah-install` and `/spheno-install` precedent is `detect | use-path | install` — three subcommands that are genuinely different actions. Here, `exclude` and `signals` are just `run` with a flag. `scan-summary` is an aggregation on a different noun.

**Synthesizer action.** Collapse to two subcommands: `/higgstools run <model> [--mode=both|hb|hs]` and `/higgstools scan-summary <run_dir>`. Default mode is `both`. Rename `scan-summary` → `aggregate` if we want to be consistent with future scan-aggregation verbs. Net: four → two.

---

## 8. p-value computation — punt, don't absorb

> "HS returns raw chi². Users will want a p-value against N_obs degrees of freedom; do we compute it inline (scipy) or leave it to downstream plotting?"

**Counter.** Compute it inline, but be honest about what the p-value means. `scipy.stats.chi2.sf(chi2, ndof)` is three lines and adding scipy to skill deps is trivial. The real hazard is the *interpretation*: a chi² p-value from HS assumes a specific null (SM + best-fit nuisance) that users will misread. If `/hep-plotting` downstream also computes p-values, we end up with two slightly different numbers.

**Synthesizer action.** Compute inline with a fixed, documented formula: `pvalue_hs = 1 - scipy.stats.chi2.cdf(chi2_total, ndof)`. Emit it in `result.json` with an explicit comment in the schema doc pointing to the null-hypothesis assumption. Instruct `/hep-plotting` to *read* this field rather than recompute, establishing one source of truth.

---

## Missed open questions the proposer didn't raise

9. **Mass-uncertainty input.** HS chi² depends on a mass uncertainty (`dMh`) passed per scalar. SPheno SLHA doesn't write this; HiggsBounds/HS have historically used a hardcoded 3 GeV default, which is wrong for heavy scalars. Who sets it in our schema? Proposal is silent.

10. **Python version compatibility.** pybind11 bindings are version-sensitive; HiggsTools v1.2 probably requires Python 3.10+. Our `_common.sh` asserts `sys.version_info >= (3, 10)`. Verify the specific floor.

11. **What if SPheno writes *multiple* higgs-bounds input formats?** SARAH can emit both `HiggsBounds` (legacy) and `HiggsCouplingsBosons/Fermions` (newer) blocks. Which does the adapter consume? Precedence rule needs to be stated.

12. **`update-dataset` interaction with cached results.** Proposal open question #3 raises it but does not resolve. Concrete answer needed: snapshot dataset SHA into each run dir (I recommend this) OR refuse update when runs exist.

13. **HB-5 vs HS-2 coupling — are they one install or two?** The "legacy fallback" line breezes past this. Historically they are *two separate Fortran builds* with their own config steps and linked together via `configure-with-chiSq` hacks. If we commit to supporting legacy as a real fallback, the installer has to do two builds, not one.

14. **Smoke-test physics correctness.** The proposal's smoke test is "SM-like point → expect `allowed=True`, finite chi²." That is a liveness check, not a correctness check. A regression in the adapter that zeroed all couplings would also pass this test. Recommend: ship a second smoke-test SLHA (2HDM benchmark at a published exclusion boundary) and assert the obsratio is within ±5% of a canned expected value.

15. **Charged-Higgs PDG introspection (proposal q4).** Accept the coupling to SARAH's PDG conventions — SARAH uses PDG 37 for H± universally, and `/sarah-build` already commits us to SARAH's scheme. This is not the risk the proposer fears.

---

Word count ≈ 1,480.
