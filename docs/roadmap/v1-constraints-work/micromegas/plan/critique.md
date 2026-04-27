# `/micromegas` implementation plan — SKEPTICAL CRITIQUE

Critic: plan-critic agent
Date: 2026-04-19
Inputs read: `plan/draft.md`, `brainstorm/final.md`, sibling drafts
(`ddcalc/plan/draft.md`, `higgstools/plan/draft.md`),
`plugins/shared/install-helpers/_common.sh`, `plugins/hep-ph-toolkit/skills/{spheno-build,sarah-install}/`,
`git log --oneline -25`.

Verdict: the plan is structurally sound but has five execution-blocking gaps and
a handful of concreteness/consistency issues that will cost a coding agent
real time. Listed below in priority order.

---

## A. Helper-reality mismatches (blocking)

> "`download_with_retry` → `MICROMEGAS_DOWNLOAD_FAILED`" and
> "Download under `HEPPH_NO_NETWORK` trap → `MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY`"
> "run `make -C $path -j$(os.cpu_count)` with network trap
> (`MICROMEGAS_BUILD_NEEDS_NETWORK`)"

**Counter.** `_common.sh` provides `check_disk`, `verify_checksum`,
`download_with_retry`, `config_get`, `config_merge` — and nothing else. There
is no `HEPPH_NO_NETWORK` awareness anywhere in the shared helpers; `download_with_retry`
unconditionally invokes `curl`. There is no `HEPPH_CACHE_DIR` lookup and no
"promote curl-inside-make to a structured blocker" plumbing. The plan assumes
behaviour the agent will have to invent from scratch in *this* workstream —
which (a) makes §3 Step 4 (install) much larger than stated, and (b) risks
putting network-policy logic inside a single skill when the sibling plans
(`/ddcalc` §2, `/higgstools` §2 step 5) also claim `HEPPH_NO_NETWORK` support
and will duplicate it.

`$(os.cpu_count)` in §2.3 is a Python function being invoked from a shell
command line; that is a literal bug inherited from hasty prose. The
equivalent in `/spheno-build/scripts/compile_model.py` is `os.cpu_count()`
*inside Python*; in bash the convention is
`python3 -c 'import os; print(os.cpu_count() or 1)'`.

**Synthesizer action.**
1. Either (a) add `hepph_no_network_guard`, `hepph_download` (cache-aware
   wrapper), and a make-wrapping helper to `_common.sh` *as a W0-style
   prework commit* that all three constraints workstreams depend on — and
   label it explicitly as W0 territory so conflicts are avoided — **or** (b)
   declare network-policy a local-to-skill concern, cross-reference the
   sibling plans so all three agree on the exact env-var semantics, and
   accept duplication.
2. Replace `$(os.cpu_count)` with `$(python3 -c 'import os; print(os.cpu_count() or 1)')`
   in §2.3 Stage 7. Also spell out that `make` is `make -C $path` with
   `HEPPH_NO_NETWORK=1` enforcement coming from a wrapper script that
   LD-preloads or PATH-overrides `curl`/`wget`/`git` — this is non-trivial
   and the agent will waste hours on it if it is not specified.
3. The plan says *"network trap (`MICROMEGAS_BUILD_NEEDS_NETWORK`)"* without a
   mechanism. Name one: stub out `curl`/`wget`/`git` on PATH via a
   tmp-directory prepended to PATH for the duration of `make`, and each stub
   exits 42 with a log line. The installer parses the log and promotes.

---

## B. Cross-workstream file-ownership collisions (blocking)

> §1: "every create step must begin with `test -e <path> && echo "exists — picking up"`"

**Counter.** That is good defensive practice, but the three sibling plans
disagree on the *content* of the shared files:

- `scattering.schema.json` — this plan (§2.2) says `required = ["m_dm_gev",
  "sigma_si_proton_cm2", "source", "source_run", "dm_candidate"]` with
  `additionalProperties: true`. `/ddcalc/plan/draft.md` §5 requires
  `nreft_coefficients?` be an optional key and rejects runtime. No
  `/ddcalc` plan item pins `sigma_si_proton_cm2` as required — their tests
  check schema validation on samples from `/micromegas` and `/looptools`,
  implying it must be *permissive* enough to accept both. `/higgstools` does
  not use this schema at all and won't constrain it, but will not resolve the
  micromegas ↔ ddcalc disagreement either.

  The first-to-land workstream will cement a schema the second workstream
  silently redefines on merge. Field-name collisions are very likely
  (`sigma_si_proton_cm2` vs `sigma_SI_p` vs `sigma_si_p`).

- `plugins/constraints/.claude-plugin/plugin.json` — this plan says "create
  with both install + usage skills listed"; `/higgstools` says "listing all
  six skills (micromegas, micromegas-install, ddcalc, ddcalc-install,
  higgstools, higgstools-install)"; `/ddcalc` says "both skills listed".
  Whichever lands first writes a partial list; the second will either (a)
  merge-conflict or (b) silently drop sibling skills by overwriting an
  additive commit.

- `plugins/constraints/README.md` / `SHARED.md` — `/higgstools` creates
  `SHARED.md`, this plan creates only `README.md`. If `/higgstools` lands
  first, the micromegas implementer will skip `SHARED.md` (and miss the
  cross-plugin contract doc). If this plan lands first, `/higgstools`
  duplicates `README.md` content into `SHARED.md`.

- `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` — all three plans
  use a relative symlink to `plugins/hep-ph-toolkit/skills/_shared/`. Good,
  but relative-symlink depth (`../../../model-building/...`) is computed
  differently in the three plans. This one says `../../../model-building/…`
  (three levels). From
  `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`, the target is at
  `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`, and the
  correct relative link is `../../../model-building/skills/_shared/blocker.schema.json`
  (three `..`: `_shared` → `skills` → `constraints` → `plugins`). Verify — the
  plan's string is correct — but this is worth explicitly showing in the
  plan alongside a `readlink` assertion in §5.

**Synthesizer action.** Pick *one* of these:
1. Hard-block one workstream as the designated "shared-skeleton owner" (the
   `/micromegas` plan is the natural choice since it lands first by the
   schedule in Step 1). Sibling plans receive a one-sentence note: "do not
   touch shared files; rebase onto main once micromegas-skeleton PR lands."
2. Land a separate `W-constraints-skeleton` PR authored by the manager (or
   by this workstream as a PR-0) that creates only the shared files with
   zero skill content. Then all three workstreams rebase.
3. At a minimum, the plan MUST name the exact field-by-field schema — the
   sibling plan already refers to it as "byte-for-byte matching final §3",
   so freeze that list in a single commit under `plugins/shared/schemas/`
   before any skill code is written.

---

## C. Golden-fixture reachability (physics reality)

> §4: "`Ωh² = 0.118 ± 0.002` (benchmark from micrOMEGAs manual §5,
> reproducible on `singletDM/main.c`)"
> §4: "`σ_SI(p) ≈ 1.1e-46 cm²` within ±10%"

**Counter.** The `singletDM` project in micrOMEGAs 6.0.5 ships a fixed benchmark
at `m_S=100 GeV, λ_hS=0.1` (not 0.05; check `micromegas_6.0.5/singletDM/main.c`
before committing the fixture). At `λ_hS=0.05` the point is Higgs-funnel-adjacent
and the relic density is closer to 0.4 (thermal underabundance), not 0.118 —
this is a classic singlet-scalar phenomenology result (see Cline et al. 2013,
Fig. 5). Ωh² ≈ 0.118 at `m_S=100 GeV` requires `λ_hS ≈ 0.23` or so.

This makes the golden integration test's numerical assertion suspect. Even
more critically, **the σ_SI(p) value** scales as λ_hS², so an incorrect λ_hS
breaks both assertions.

Secondly, this test requires a SARAH-emitted singletDM UFO → CalcHEP
conversion working end-to-end. SARAH 4.15 emits UFO 1.x (as noted in
brainstorm §1); CalcHEP's UFO importer is notorious for dialect fussiness.
The plan's `CALCHEP_CONVERTER_VERSION_SKEW` blocker acknowledges this, but
the golden test presumes the skew doesn't happen.

**Synthesizer action.**
1. Re-derive the `(m_S, λ_hS)` benchmark from a verified source before
   freezing the fixture. Either grab the exact pair from the micrOMEGAs
   manual §5 table, or from a known paper (Cline+Scott+Kainulainen+Weniger
   Appendix, Arcadi+ review Table 3). Commit the citation inline.
2. Add an explicit plan step between §3 Step 11 and §3 Step 12: "derive
   golden values by running micrOMEGAs by hand on a known-good SLHA; record
   actual Ωh² and σ_SI(p) with quoted uncertainties." Don't take the spec's
   ±2% / ±10% tolerances at face value.
3. Gate the UFO→CalcHEP path behind `HEPPH_RUN_NETWORK_TESTS=1` AND presence
   of the `--precompiled singletDM` project. Phrased differently: v1's
   golden test should use `--precompiled singletDM` (avoiding SARAH/UFO
   entirely), and a separate gated test exercises the UFO path against a
   stubbed fixture. Otherwise the v1 golden is pinned to SARAH's UFO-1 output
   quality, which is W3-owned and not yet validated.

---

## D. Step-atomicity failures

> §3: "Each step is a commit candidate. Run test suite green before committing."

**Counter.** Several steps cannot be green independently:

- **Step 6 (DM candidate resolver + SLHA parser)** pretends to be standalone
  Python. But `resolve_dm_candidate.py` in §2.4 is called by `run_micromegas.py`,
  which isn't written until Step 10. The resolver tests will pass, fine —
  but the tree is *functionally broken* (no `/micromegas` entry point) until
  Step 10. The plan claims independent reviewability but the SKILL.md
  documents a CLI that does not exist yet in Step 5.
- **Step 5 (SKILL.md for `/micromegas-install`)** lands before Step 7–11
  implement the `/micromegas` usage skill, meaning the docs refer to cross-skill
  state keys (e.g. `config.micromegas_path`) that are validated by nothing
  runnable yet. This is a minor cosmetic issue for the install skill; it's
  more acute for §3 Step 12 (usage SKILL.md), which documents the scan
  contract before any integration test exists for it.
- **Step 9 (UFO→CalcHEP + project build)** depends on `main_c_template.py`
  (Step 7) and `parse_micromegas_out.py` (Step 8) being stable. Good. But it
  depends on SARAH-emitted UFO fixtures existing — those are created only in
  Step 12's fixture commit. The `test_ufo_conversion.py` integration test
  cited in §4 has no fixture to consume at Step 9's commit boundary.
- **Step 3 (`/micromegas-install` detect + use-path)** requires
  `_blocker.sh`, which the plan says is "a copy of `sarah-install/_blocker.sh`".
  That file is 4 levels deep, the sourcing pattern is longer; just say so
  explicitly and also warn the agent NOT to symlink (the `cp` is intentional
  because `_blocker.sh` will diverge for mO-specific fields like
  `attempted_url`).

**Synthesizer action.** Either:
1. Rewrite §3 so each step's test suite is a subset that actually passes at
   that commit (the current ordering is roughly correct; the plan just
   needs to say explicitly which tests are added *in* the step vs. which
   are authored-but-skipped-until-later).
2. Or compress Step 6–10 into three larger commits: (6') resolver +
   parsers + templates (pure Python, no driver), (7') full `run_point` +
   subcommand dispatcher (tests become green as one), (8') scan +
   integration test fixture. Three commits instead of five; each one is
   actually green.

Call this out in the plan: "atomic = tests that existed *before* the
commit continue to pass, and any tests added by the commit pass; tests
authored for later steps are skipped via `pytest.mark.skipif(not ..., ...)`."

---

## E. Concreteness gaps

> §2.1: "(plus placeholders commented out for ddcalc/higgstools to aid
> sibling picks-up — if policy forbids, document in PR body instead)"

**Counter.** JSON does not have comments; JSONC does. `plugin.json` must be
strict JSON (per the marketplace schema). The parenthetical hedge leaves the
implementer to discover this. Just say: "list only `micromegas-install` and
`micromegas` in the initial `skills[]` array. Sibling workstreams append
entries in their own commits. Merge conflict resolution strategy: lexical
sort of the `skills[]` array on merge."

> §2.4: `main_c_template.py` — "jinja-free string builder → `report.md`"

Which is it — jinja-free or a string builder? (These are the same thing; say
"no template engine — plain f-strings with a `dedent` helper".) The plan conflates
`main_c_template.py` (code generator for C) and `render_report.py` (Markdown
generator) in two places. Pull these apart in the per-file plan.

> §2.4: `spectra.h5` — hinted at in inputs/outputs

Who writes it? Neither `run_point.py` nor `parse_micromegas_out.py` is
documented as doing so. micrOMEGAs' `calcSpectrum` writes ASCII; converting
to HDF5 requires `h5py` or `pytables`. The plan doesn't specify the
dependency. Add: "requires `h5py >= 3.0` as a runtime dep; declare in
`plugins/hep-ph-toolkit/skills/micromegas/requirements.txt` (create this file
in Step 8) and document in SKILL.md's 'Prerequisites' section."

> §2.4: `scan.py` — "identical semantics to `/spheno-build/scan.py`"

Reference the exact functions expected to be reused. Looking at
`plugins/hep-ph-toolkit/skills/spheno-build/scripts/scan.py`, the shape of
grid parsing is specific; a handwave invites re-implementation.

> §2.3: `install_impl.sh` stage 9 — "Check PPPC tables exist
> (`Data/pppc4dmid/*`) → `PPPC_TABLES_MISSING`"

Wrong directory name. In micrOMEGAs 6.0.5 the PPPC4DMID tables live under
`Data/` at the top level (e.g. `Data/AtProduction_gammas.dat`), not
`Data/pppc4dmid/`. Verify against a real 6.0.5 tarball before pinning the
glob.

> §2.3: `skill_env.yaml` has `micromegas_sha256: TODO`

Per the project convention `verify_checksum` WARN-not-aborts on `TODO`, so
this is fine for v1 scaffolding — but the verification checklist in §5
should explicitly allow or ban TODO. The `/ddcalc` plan bans it (§5 "no
`TODO`"); consistency is a good thing.

---

## F. Style/voice drift from `/spheno-build`

> §7: "Commit messages — follow `W<n>: <verb> <subject>` convention observed
> in `git log`. Prefix used here: `W-constraints-mO: ...`"

**Counter.** `git log --oneline -20` shows `W0`, `W1`, `W2`, …, `W6`, and
sub-commits like `W1(1)`, `W1 r2` — all *numeric* prefixes. `W-constraints-mO`
is a divergence. If the intent is to keep the three constraints workstreams
distinguishable, a better convention is `W7-mO:`, `W7-dd:`, `W7-ht:` (where
W7 is the next numeric slot after W6), or to reuse a W-slot per workstream
and tag. Using the ad-hoc `W-constraints-*` prefix will make
`git log --grep=^W7` or similar tooling break silently.

Also, the SKILL.md voice is described as "matches `/spheno-build/SKILL.md`".
Good call. One concrete miss: `/spheno-build/SKILL.md` has no "Decision flow"
ASCII diagram, but `/sarah-install/SKILL.md` does. The plan says
"Decision flow (ASCII diagram, mirrors sarah-install)" for `/micromegas-install`,
which is correct. For `/micromegas` usage skill, the plan lists
"Recoverable vs fatal contract (table from final.md §2)" — matching
spheno-build — good.

**Synthesizer action.** Switch to numeric-prefixed commits
(`W7-mO: …` or similar), and explicitly reference `git log --oneline` as the
authority. Add to §7: "every commit body ends with a blank line — no
`Co-Authored-By: Claude` line unless the user explicitly requests it."

---

## G. Missed-risk bullets

1. **Apple Silicon CalcHEP.** Brainstorm §1 notes `FFLAGS=-ff2c` and
   `LDFLAGS=-Wl,-ld_classic`. The plan embeds these in `_macos_env.sh` —
   good. But CalcHEP's `getFlags` script on arm64 macOS is known to probe
   `uname -m`, find `arm64`, and fall back to x86_64 compiler flags that
   fail with clang 15+. The plan does not mention patching `getFlags`.
   Expect `MICROMEGAS_BUILD_FAILED` on M1/M2/M3 hardware with no clear
   remediation path. Add a pre-make patch or document an env-var override.

2. **`darkOmega` signature.** The plan uses `darkOmega(&Xf, fast=1, Beps=1e-6)`.
   In 6.0.5, the actual C signature is `darkOmega(&Xf, 1, 1e-6, &err)` (or
   similar — check `sources/ms_constructor.c`). The plan's `main_c_template`
   golden fixtures will bit-rot the moment the generator is wrong; a
   compile-failure is visible but a wrong-arg is not. Specify: "before
   committing golden `main.c` fixtures, compile each one against the
   installed micrOMEGAs 6.0.5 tree and assert `make main` exits 0."

3. **UFO dialect versioning.** Cache key is
   `sha256(ufo_dir_tar) || micromegas_version || ufo_dialect`. `ufo_dialect`
   is never defined. Is it UFO version (1.x vs 2.0), or is it a SARAH-specific
   dialect string? Specify the source of truth (most likely
   `$ufo_dir/restrict_default.dat` or `$ufo_dir/__init__.py`'s
   `UFO_VERSION` attribute) or the rule will be implemented inconsistently.

4. **No concurrency lock for `micromegas_project/cache/<hash>/`.** The plan
   (§7) says "top-level cache read-only across runs". True only if
   `ufo_to_calchep.sh` is atomic. It isn't — `newProject` writes files
   in-place. The plan needs either a `flock` around cache population or a
   write-to-tmp-then-rename pattern. `/ddcalc` plan mentions `flock` on
   `$STATE_ROOT/.locks/ddcalc`; mirror that discipline here.

5. **`spec.yaml` schema.** §2.4 gives an annotated template but no formal
   schema. `/sarah-build`'s spec.yaml had `modelspec.schema.json` (per
   `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`). Is the
   micromegas spec an extension of that schema? If so, say which fields
   extend it; if not, say why the new skill gets its own YAML shape
   without schema validation.

6. **`regenerate_fixture.py` mentioned but under-specified.** Plan says it
   "runs only when `HEPPH_RUN_NETWORK_TESTS=1`; rebuilds the golden
   singletDM outputs." What does it do vs. `/spheno-build`'s
   `regenerate_fixture.py`? Specify inputs and outputs, and whether it
   depends on SARAH/SPheno state being present.

7. **`DDCALC` coordination gate.** The sibling `/ddcalc` plan's Step 1
   ("planning-phase verifications") must run before `/ddcalc`'s Step 3
   (scaffold). If `/micromegas` lands its scaffold first, the sibling
   workstream is *forced* to run its verification after the scaffold is
   committed. This is probably fine, but the micromegas plan should
   acknowledge the scheduling dependency in §1.

---

## Bottom-line recommendation

The plan is 85% ready. Blocking fixes needed before handoff:
- Land a W0-style skeleton commit (shared schema + plugin.json + marketplace
  + CLAUDE.md) as a separate PR-0 owned by the manager, *not* by this
  workstream, so all three constraints plans rebase onto it cleanly.
- Derive the singletDM golden numerically by hand; stop assuming `λ_hS=0.05`
  gives Ωh²=0.118.
- Move `HEPPH_NO_NETWORK` plumbing into `_common.sh` via W0, or explicitly
  scope it to this skill.
- Fix `$(os.cpu_count)`, `Data/pppc4dmid/*`, and `darkOmega` signature
  claims against the real 6.0.5 tarball before freezing templates.
- Rename commit prefix to a numeric slot (`W7-mO:` or equivalent).

Everything else is polish: atomicity can be made honest by annotating which
tests land per step, and the coordination gate with ddcalc/higgstools can be
spelled out in §1 explicitly rather than left to "pick up if exists".
