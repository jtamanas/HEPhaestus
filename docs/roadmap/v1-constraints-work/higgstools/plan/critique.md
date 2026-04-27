# /higgstools plan — Skeptical Critique

Reviewer: plan-critic agent. Inputs: `plan/draft.md`, `brainstorm/final.md`,
sibling plan drafts (`micromegas`, `ddcalc`), `plugins/shared/install-helpers/_common.sh`,
`plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` and scripts directory.
Format: quote → counter → synthesizer-action.

---

## 1. W0 exit-code coordination is under-specified

> "leave a TODO in `install_higgstools.sh` referencing `EXIT_GENERIC=1` with a
> code-comment marker `# TODO(W0): replace with EXIT_NO_CMAKE once _common.sh
> patch lands`."

**Counter.** `_common.sh` currently ends at `EXIT_NO_LAPACK=25` and W0 has not
merged codes 26/27 yet. The plan's fallback — "use `EXIT_GENERIC=1`" — collapses
two distinct fatal conditions (cmake missing, pybind11 missing) into a single
exit code 1 that's already overloaded as the catch-all. The install script
emits `HIGGSTOOLS_TOOLCHAIN_MISSING` (blocker JSON) *and* exits with 1 during
the interim, so a downstream consumer grepping only exit codes cannot
distinguish "generic failure" from "toolchain missing". Worse, the unified path
is gated on these codes *and* gated on `HEPPH_HIGGSTOOLS_BACKEND=unified`, so
the interim is effectively dead code until W0 ships — yet the plan wires it
all in step 6, **before** step 12's W-verify gate could possibly detect the
regression. The sibling `/micromegas` plan silently grabbed local codes 26/27/28
for its own use (see `micromegas/plan/draft.md` §2.3 — `26=EXIT_CALCHEP_BAD`,
`27=EXIT_MACOS_SDK`, `28=EXIT_SMOKE`). Two workstreams are now fighting for the
same numeric range.

**Synthesizer-action.** (a) Open the W0 PR *first*, before step 1 begins —
with 26/27 reserved for cmake/pybind11 globally. Reject `/micromegas`'s local
claim on 26/27 at merge time. (b) Interim: exit with `EXIT_NO_GFORTRAN=10`-
style discipline — pick `EXIT_GENERIC=1` only if the blocker JSON already
names the fatal mode. Add a one-line invariant test:
`grep -n '# TODO(W0)' install_higgstools.sh` must return exactly 0 matches at
W-verify time. (c) Add a matrix to `plugins/constraints/SHARED.md`: rows =
skills, columns = local exit-code claims. Reserves 26/27 for shared use,
28-35 for per-skill.

---

## 2. Legacy tarball download — GitLab archive semantics

> "`https://gitlab.com/higgsbounds/higgsbounds/-/archive/5.10.2/higgsbounds-5.10.2.tar.gz`"

**Counter.** GitLab's `-/archive/<ref>/<name>.tar.gz` endpoint regenerates the
tarball server-side from the git tree at each request; the SHA256 is **not
stable across server regenerations** if GitLab changes its tar/gzip flags
(documented behavior: `gitlab.com/gitlab-org/gitlab/-/issues/27820`, still
open). The plan pins `HB_VERSION=5.10.2` with a real SHA256 computed once at
scaffolding time, but that SHA can silently invalidate after a GitLab minor
upgrade, turning every fresh install into `HIGGSTOOLS_DOWNLOAD_FAILED`
(via the checksum arm). The sibling `/ddcalc` plan uses the same archive
endpoint and inherits the same fragility. Public-repo auth is fine — anon
clone-over-https works — but the tarball route is NOT the right stable artefact.

**Synthesizer-action.** Prefer `git clone --depth 1 --branch 5.10.2`
(two repos, ~40 MB each) over tarballs. `verify_checksum` becomes
`git rev-parse HEAD` compared against a pinned commit SHA — which GitLab
*cannot* silently mutate. Keep the tarball URL as a fallback gated on
`HEPPH_HIGGSTOOLS_PREFER_TARBALL=1`. Add the commit-SHA pin to
`skill_env.yaml` as `hb_commit: <sha>` / `hs_commit: <sha>` adjacent to the
version. Fortran build-config: HB-5 CMake auto-detects gfortran; no
user-tunable flags matter for v1.

---

## 3. 2HDM Type-II golden fixture — can the implementer actually write it?

> "`tests/fixtures/2HDM-II-benchmark.slha` — 2HDM Type-II benchmark at
> `(m_A=400, tanβ=10, cos(β-α)=0.1)`. Adapted from HB-5.10.2 `example_data/`."

**Counter.** The plan names three parameters but an SLHA2 Higgs-sector file
needs **five** independent inputs for a CP-conserving 2HDM: {mH, mA, mH+, tanβ,
sin(β-α)} plus m²₁₂. The plan specifies mA, tanβ, cos(β-α) — it does not pin
mH (presumably 125 GeV h-like?), mH+ (bounded by EWPT: ~mA for Z2-symmetric),
or the soft-Z2-breaking parameter. Worse, the SLHA must contain
`HiggsBoundsInputHiggsCouplingsFermions` and
`HiggsBoundsInputHiggsCouplingsBosons` blocks — these are **not hand-authorable
numbers**; they are ratios of BSM to SM effective couplings that depend on
α. "Adapted from HB-5.10.2 `example_data/`" is hopeful, but HB ships SLHA1
benchmark files; the SLHA2-with-HB-blocks variant requires running SPheno
or doing the αeff algebra by hand. The fixture cannot be written from
first principles by the step-7 implementer.

**Synthesizer-action.** Move the fixture authorship to step 7.0
(pre-implementation): either (i) run SPheno on a committed 2HDM spec.yaml
via the existing `/spheno-build` skill and commit the `.spc` as the fixture,
or (ii) write `scripts/make_benchmark_slha.py` that computes HB coupling
blocks from (mh, mH, mA, mH+, tanβ, sin(β-α), m²₁₂) using the well-known
2HDM tree-level formulas (Branco et al. 2011 §2, eqs. 32-44). Commit the
script, its fixture output, and pin **all seven** parameters in SKILL.md.
The current "±5% of HB manual Fig. 7" assertion is also suspect — the manual's
Fig. 7 axes are (mA, tanβ) at fixed cos(β-α), but "quoted value" is not a
single number, it's a contour. The integration test should assert
`obsratio_max ∈ [1.2, 1.8]` for a concrete grid point that the manual
explicitly tabulates, not a vague "±5% of Fig. 7".

---

## 4. p-value degrees-of-freedom source

> "`p_value_rates = 1 - scipy.stats.chi2.cdf(chi2_rates, ndf_rates)`"

**Counter.** Where does `ndf_rates` come from? Two possibilities: (a) HS's
`HiggsSignals_neutral_input_SMXS_mu.F90` output — HS *does* report
`nobs_peak`, `nobs_STXS`, etc. separately, which is the right source; (b)
the input-channel count the plan passes in — this is *wrong* because HS
marginalizes over nuisance parameters, reducing effective df. The plan
conflates these. `scipy.stats.chi2.sf(χ², k)` with the wrong `k` is a silent
numerical bug — values look plausible but are ~10× off.

**Synthesizer-action.** Explicitly require that `ndf_rates` and `ndf_masses`
come from HS's `get_Rvalues` / `HiggsSignals_get_Peak_Chisq` output fields
(HS API §4). Forbid any Python-side computation of `ndf` from input sizes.
Add a unit test: synthesize a fake HS output with `ndf=17`, assert the
emitted `p_value_rates` equals `scipy.stats.chi2.sf(χ², 17)` to 1e-12 —
and that no other `ndf` value appears in the code path (grep assertion:
`grep -rn 'len(channels)' scripts/pvalue.py` returns zero).

---

## 5. `aggregate` subcommand — what does it aggregate?

> "`scripts/aggregate.py` — walks a `scan_<TS>/` directory, joins per-point
> `result.json` into `higgstools_index.csv` sorted by SPheno `index` column."

**Counter.** This is finally specified — good. But the plan is silent on the
**input** semantics: does `aggregate` *re-run* HB/HS on each SLHA in the scan
directory (which is what an implementer would naively assume from the word
"walks"), or does it only *collect* already-computed `result.json` files? The
brainstorm §2 says "per-point `run` evaluations are independent and run under
`multiprocessing.Pool`", suggesting aggregate both runs and collects. But the
plan's step 10 says "parallelises per-point runs", while §4 integration test
#8 `aggregate over a 5-point mini-scan; assert CSV determinism across
workers` suggests a pure join of pre-existing files. Ambiguity: if aggregate
re-runs, it needs write-locking on the state root; if it only collects, it
doesn't.

**Synthesizer-action.** Split the semantics explicitly: `aggregate` is
**collect-only** (reads N `result.json` files, emits one CSV). Running HB/HS
on N SLHA files is `run --scan-dir <dir>` (the same existing `run`
subcommand with a new flag). This matches `/spheno-build` precedent where
`scan.py` runs points and a separate pass produces `scan_index.csv`. Fix
SKILL.md to say: "`aggregate` does NOT invoke HB or HS; it only joins
result.jsons produced by prior `run` invocations." Update test 8 to
pre-populate the 5 result files, not compute them.

---

## 6. `hb_allowed` vs `hs_consistent` — native output mapping

> "`hb_allowed = (obsratio_max < 1.0)` … `hs_consistent = (chi2_total -
> chi2_SM_ref < 6.18)`"

**Counter.** For HB-5: the manual defines "allowed" via `HBresult=1` *per
channel*, not via `obsratio<1`. The plan collapses all channels to their max
obsratio, which is almost the right thing — but HB-5 applies channel-specific
theoretical uncertainties *before* the ratio comparison, and a channel with
`HBresult=0` (excluded) can coexist with max(obsratio) < 1 if the uncertainty
band straddles 1. The correct v1 formula is `hb_allowed = all(HBresult == 1
for each channel)`, not `max(obsratio) < 1`. For HS-2: `chi2_SM_ref` is NOT
a field HS outputs; HS reports `chi2_total`, and the SM reference must come
from a **separate** HS run on a SM-like point or the cached `chi²_SM`
from HS's examples. The plan assumes it's "bundled" — it isn't automatically.

**Synthesizer-action.** (a) Change `hb_allowed` semantics to the AND of
per-channel `HBresult`. Keep `obsratio_max` as a reported field, not the
decision basis. Update `compute_hb_allowed(channels_list)` signature. (b) Add
a step to the install script: after HS build, run HS's bundled SM example
and cache `chi2_SM_ref` to `$STATE_ROOT/cache/hs2_chi2_sm_ref.json`. On
first `run` invocation, read the cache or recompute. Emit
`HIGGSTOOLS_SM_REF_MISSING` fatal if absent. Add this to the §1.2 blocker
table.

---

## 7. Sibling coordination — plugin.json ownership

> "Sibling constraint workstreams (`/micromegas`, `/ddcalc`) run on their
> own branches and merge independently; conflicts in
> `plugins/constraints/.claude-plugin/plugin.json` are resolved at merge
> time, not during development."

**Counter.** All three plans claim "create if absent" for `plugin.json`.
The `/micromegas` plan (step 1) creates it, commits it with two skill
entries. The `/ddcalc` plan (step 3) does the same. The `/higgstools`
plan says "first constraint ws to land". This is a **last-writer-wins
merge race**: whichever plan lands second will overwrite the first's
skills list unless the merge is hand-resolved. "Resolved at merge time"
is hand-waving.

**Synthesizer-action.** Either (a) pre-land a minimal `plugin.json` with
**all six skills** listed in a single prep PR owned by the manager before
any of the three workstreams open — this is a 20-line commit; or (b) use
an explicit merge strategy: each workstream adds *only its own skills
entry* to the array and uses `git merge -X union` at merge time. Pick (a).
Also pre-land `plugins/constraints/README.md`, `SHARED.md`, and the
`_shared/blocker.schema.json` symlink in the same prep PR. This moves the
race out of critical path.

---

## 8. Blocker codes and actionable `user_instruction`

> "`HIGGSTOOLS_SLHA_MISSING_BLOCKS` … with `user_instruction` to rerun
> `/sarah-build` with `SPheno.m` directive `WriteHiggsBoundsBlocks=True`."

**Counter.** `WriteHiggsBoundsBlocks` is a SARAH `SPheno.m` flag, not a
user-facing CLI argument in `/sarah-build`. The suggested user instruction
asks the user to modify SARAH source — the skill provides no such
surface. The `/sarah-build` SKILL.md does not document a way to toggle
this flag from the outside.

**Synthesizer-action.** Fix the `user_instruction` to one of: (i) "edit
`spec.yaml` to set `sarah_options.write_hb_blocks: true`, then rerun
`/sarah-build <model> --force`" (requires adding that spec key to
`/sarah-build`) — do this as a coordinated patch; or (ii) "the
SARAH-generated `SPheno.m` in `$STATE_ROOT/models/<name>/sarah_output/`
needs `WriteHiggsBoundsBlocks=True`; patch it then rerun `/spheno-build
<name> --force`". Pick (i); open a companion patch to `/sarah-build`.

---

## 9. Test coverage gap — charged Higgs dispatch

> "5 unit + 3 integration tests"

**Counter.** The 2HDM+a paper 2506.19062 is explicitly about a model with
a light pseudoscalar *plus* a charged Higgs, and HB's charged-Higgs search
channels (ATLAS/CMS H±→τν, H±→tb, H±→cs) have different code paths from
the neutral ones in HB-5. Nothing in the test matrix exercises
`--channels=charged` or verifies that a charged-Higgs-dominated exclusion
flows through correctly. `test_cli_args.py` covers the argparse surface
but not the dispatch.

**Synthesizer-action.** Add `test_channels_dispatch.py` unit test: mock
the Fortran binary, verify `--channels=charged` passes the right flag to
the HB binary (or the right channel-ID filter to the unified backend) and
excludes neutral-channel IDs from `per_channel.csv`. Plus one integration
case: a 2HDM point with m_H+ = 150 GeV, tanβ = 1 (excluded by H±→τν),
assert the dominant obsratio channel is a charged-Higgs channel ID.

---

## 10. v1 scope gates — are exclusions code-enforced?

> "No CPV, no `--native`, no unified-default."

**Counter.** These are documented in SKILL.md prose but not enforced in
code. A future contributor adding a `--native` branch won't hit any
grep-level guard. The sibling `/ddcalc` plan does explicitly ban
`HEPPH_ALLOW_REFERENCE` in a verification checkbox (grep for zero refs).
The `/higgstools` plan's checklist says "No call-site performs an
analytic fallback" — but that's a manual review item, not a test.

**Synthesizer-action.** Add three assertion tests to the unit tier:
(a) `grep -rn 'native\|--native' plugins/hep-ph-toolkit/skills/higgstools/`
returns zero; (b) `grep -rn 'cpv\|CPViolation\|complex_mixing'` in scripts
returns zero; (c) the `--backend=unified` default in argparse is tested
to raise unless `HEPPH_HIGGSTOOLS_BACKEND=unified` is also set. Bake
these into `test_scope_invariants.py`. They take 30 lines and catch scope
creep at CI time.

---

**Summary of blocking items (must resolve before step-1 commit):**

1. Pre-land W0 exit-code patch (26/27 for cmake/pybind11) with cross-plugin
   matrix in `SHARED.md`.
2. Pre-land `plugins/constraints/` scaffold in a manager-owned prep PR.
3. Replace tarball download with git-clone-by-commit-SHA for HB/HS.
4. Commit a `make_benchmark_slha.py` script (or pre-run SPheno) to produce
   the 2HDM fixture; pin all seven parameters; replace "Fig. 7 ±5%" with a
   concrete obsratio interval at a tabulated grid point.
5. Specify `ndf` source as HS native output; add grep guard.
6. Clarify `aggregate` as collect-only; move scan-running to `run
   --scan-dir`.
7. Fix `hb_allowed` to AND-of-HBresult; wire SM-ref cache for `hs_consistent`.
8. Fix `user_instruction` for `HIGGSTOOLS_SLHA_MISSING_BLOCKS` with a real
   CLI surface patch on `/sarah-build`.
9. Add charged-Higgs channel dispatch test.
10. Add three scope-invariant grep assertions in a dedicated test file.

Word count: ~1,430.
