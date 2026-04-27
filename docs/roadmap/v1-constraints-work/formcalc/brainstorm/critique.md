# `/formcalc` — Critique (Skeptical Critic)

Format: quote → counter → synthesizer-action. Opens at the end.

---

## 1. "FormCalc's tarball already vendors … FORM … LoopTools … Mathematica app."

**Quote (§1 Bundled vs separate):** "FormCalc's tarball already vendors: `FormCalc/` — the Mathematica app. `LoopTools/` — Fortran + C sources … `FORM/` — a bootstrap that downloads and builds Vermaseren's `form` if not already on `$PATH`."

**Counter.** This is the single largest factual risk in the proposal. The reality is close but not this clean:

- FormCalc's tarball (Hahn's distribution, `FormCalc-10.0`) **does** vendor LoopTools and **does** ship a `tools/` area that can download/build FORM if absent — but FORM (Vermaseren) has its own upstream (github.com/vermaseren/form) with independent releases and license, and recent FormCalc releases have oscillated on whether FORM is auto-bootstrapped or expected as a prerequisite. LoopTools likewise has its own release cadence (2.16 vs 2.17 in open Q3) and is sometimes shipped as a separate tarball from Hahn's site.
- Depending on which version we pin, the "single tarball" claim may be wrong on day one.
- Version pinning one variable (`HEPPH_FORMCALC_VERSION=10.0`) hides drift in two downstream libraries that evolve independently.

**Synthesizer action.**

- Before writing `install_formcalc.sh`, add a *distribution-reality probe step* to the plan: `curl` Hahn's download page, inspect the 10.0 tarball contents, confirm FORM bootstrap script presence. Record in `skill_env.yaml` as `formcalc_bundled_form: yes|no`.
- Split version pins: `formcalc_version`, `looptools_version`, `form_version` — three env-var overrides (`HEPPH_FORMCALC_VERSION`, `HEPPH_LOOPTOOLS_VERSION`, `HEPPH_FORM_VERSION`) even if only the first is usually needed. Store all three in config.
- If FORM is not bundled, the install script must fall back to fetching `github.com/vermaseren/form` at a pinned tag. Add blocker `FORM_UPSTREAM_UNREACHABLE`.

## 2. "symlink the built `form` into `$HOME/.local/bin/form`"

**Quote (§1):** "We install the whole tree under `~/.WolframEngine/Applications/FormCalc-<ver>/` … symlink the built `form` into `$HOME/.local/bin/form`."

**Counter.** `$HOME/.local/bin` is not on PATH for default zsh/bash on macOS (and on Linux only via systemd-user conventions or a distro-specific rc). FormCalc's Mathematica side shells out to `form` by name; if PATH is wrong, `CalcFeynAmp` dies with an opaque error deep inside `form.log`. Worse: if the user already has a system `form` (packaged in some HEP distros, or installed via Homebrew tap), our symlink either collides or gets shadowed, producing silent version skew that is very hard to debug.

**Synthesizer action.**

- Do **not** symlink into `$HOME/.local/bin`. Keep the `form` binary under `${formcalc_path}/bin/form` and register the absolute path as `config.form_binary`. Pass it to Mathematica via `SetEnvironment["FORM" -> <form_binary>]` inside the FormCalc driver `.wls` (FormCalc respects a `$FormCmd` override — confirm the symbol name in smoke test).
- `detect` must `realpath` any pre-existing `form` on PATH and refuse to adopt it without a version match: emit `FORM_VERSION_MISMATCH` recoverable if an existing binary is found but its `--version` does not match our pin.
- Smoke test must exercise FORM, not only `Needs["FormCalc\`"]` (see §5 below). A load-only smoke test misses this entire class of bug.

## 3. "Regularization default: `dimreg` … tt̄, EW loops."

**Quote (§2 Inputs):** `--scheme {dimreg,dimred,cdr}` default `dimreg`.

**Counter.** The paper we are reproducing (arXiv:2506.19062, 2HDM+a) is **not** SUSY, but the pseudoscalar `a` sits in a chiral fermion loop for σ_SI (Eqs. 9, 14, 23). `dimreg` + naive γ₅ is the conventional choice there, so the default is probably right *for this paper* — but the proposal immediately widens scope to "MSSM users will hit it" (open Q1), and the pattern across the rest of the roadmap is model-sensitive defaults (see `/spheno-build` reading SPHENOINPUT from SARAH). A fixed `dimreg` default sets a footgun.

**Synthesizer action.**

- Default must be **model-sensitive**, read from the ModelSpec: if `spec.susy == true` (future field) → `dimred`; else `dimreg`. Store the *resolved* scheme in `summary.json` so downstream `/formcalc` can assert-match.
- Independently, add `formcalc_scheme` to the FormCalc output header comment (consistent with `/formcalc` proposal's `(* formcalc-output v1; pv-form; scheme=dr *)` contract). This makes scheme a first-class contract element.

## 4. "Not a MadGraph replacement … `--output-mode=fortran` … advertised as 'one-loop amplitude evaluator,' not a general generator."

**Quote (§3):** "Do **not** make the Fortran path a replacement for MadGraph at tree level — it's opt-in, named `--output-mode=fortran`, and advertised as 'one-loop amplitude evaluator'"

**Counter.** The line is rhetorical, not mechanical. FormCalc's `WriteSquaredME` + compiled Fortran will happily produce a numeric tree-level 2→2 σ for `e⁺e⁻ → tt̄`. If we expose `--output-mode=fortran`, a user who asks "give me σ(e⁺e⁻ → μ⁺μ⁻) at LEP" will get an answer from `/formcalc` and never reach `/madgraph`. That violates the "augment not replace" directive in memory — `/formcalc` becomes a partial reimplementation of MadGraph's tree-level numeric evaluator. The proposal acknowledges this risk but handles it with documentation ("advertised as"), which is the weakest form of enforcement.

**Synthesizer action.**

- Harden the line in code, not docs: when `--output-mode=fortran` is selected and `--loop-order == 0`, emit blocker `FORMCALC_TREE_FORTRAN_REJECTED` (fatal) with `user_instruction` → "Use `/madgraph` for tree-level numeric cross sections." Loop order ≥ 1 is required for Fortran emission.
- Alternative, cleaner: drop `fortran` from v1 entirely (see §6 below).

## 5. "Residual γ₅ ambiguity (BMHV warning) — **recoverable**"

**Quote (§2 Error modes):** "`FORMCALC_G5_SCHEME_AMBIGUOUS` — **recoverable** (record, continue)."

**Counter.** In chiral theories, a γ₅ scheme ambiguity is not noise — it is a choice with physical consequences (anomalous vertices, finite scheme-dependent shifts, BMHV vs naive vs Larin give different answers for non-anomaly-free traces). Calling it "recoverable" means the skill silently picks one and proceeds, and the number that lands in `sigma.json` at the end of the chain is wrong in a way that the user will not see. This is exactly the "augment not replace" anti-pattern: doing physics implicitly instead of surfacing the choice to the tool and the user.

**Synthesizer action.**

- Promote to **fatal** with `user_instruction` instructing the user to pass `--fermion-chain {chiral,non-chiral,fierz}` explicitly (and document that this implies a γ₅ scheme). Do not proceed with a default when the amplitude contains a γ₅-sensitive trace.
- Only if the amplitude has **no** γ₅-sensitive traces (FormCalc's own `$Dim` / `HelicityME` flag pattern can be inspected), quietly continue. This needs a static check before invoking `CalcFeynAmp`, not a post-hoc log parse.
- Keep `FORMCALC_IR_DIVERGENT` recoverable — that one is genuinely a downstream problem that `/formcalc` can handle via subtraction.

## 6. Fortran-emission scope for v1

**Quote (§3):** "**both**, but default `symbolic`."

**Counter.** v1 roadmap (`docs/roadmap/v1-constraint-skills.md`) says v1 exists to close the paper-Eqs.-9/14/23 loop. That is a **symbolic → `/formcalc` → `sigma.json`** pipeline. `WriteSquaredME` + LoopTools linking + macOS gfortran portability is a known pain surface (the open Q2 already admits "known gfortran/LoopTools pain points"). Shipping it in v1 doubles the install-skill surface area, adds a LoopTools build blocker path, adds `FORMCALC_FORTRAN_BUILD_FAILED`, and none of it is on the critical path to reproducing the paper. Classic scope creep.

**Synthesizer action.**

- **v1 ships symbolic only.** `--output-mode` accepts `symbolic` (default) only; `fortran` and `both` return `FORMCALC_OUTPUT_MODE_NOT_IN_V1` (reference_only-style "not implemented" marker, or fatal).
- LoopTools is still built during install (needed as a PV library that `/formcalc` can consume in its numeric-evaluation branch via MLooptools link — confirm with `/formcalc` proposer). But no `WriteSquaredME`, no model-specific Fortran make.
- Fortran-out lands in v1.1 once we have a user asking for it. This also defers the `--mandel-invariants` / kinematics-input question (open Q9 below).

## 7. Plugin placement — three-way conflict

**Quote (§4):** "**Decision: `plugins/feynman-diagrams/`.**"

**Cross-refs.** `/feynarts` proposal §4 says `plugins/model-building/`. `/formcalc` proposal §4 says new `plugins/loop-computation/`. `/formcalc` proposal says `plugins/feynman-diagrams/`. **Three proposals, three different plugins, one pipeline.**

This is the biggest structural bug in the brainstorm round. The three skills *must* live together — they share Wolfram prereq, a state-root layout, blocker codes, and a tight upstream/downstream contract — yet each proposer picked a different home.

**Counter.** `feynman-diagrams/` per `CLAUDE.md` is user-facing drawing (TikZ-Feynman). `model-building/` is already SARAH+SPheno and will become overloaded if the Mathematica amplitude stack lands there. `feynman-diagrams/` co-locating with TikZ drawing tools crosses the "diagram **drawing**" vs "diagram **computation**" boundary awkwardly — a future user asking `/draw-feynman` for a TikZ export will see three unrelated amplitude-computation skills in the plugin listing.

**Synthesizer action.**

- Convene a three-way decision in the orchestrator brainstorm (`docs/roadmap/v1-constraints-work/orchestrator/`) before any skill lands. The critic's recommendation: **new `plugins/loop-computation/`** (aligns with `/formcalc` proposer). Rationale: clean name, clean scope (Wolfram-driven one-loop amplitude pipeline), leaves `feynman-diagrams/` pure-drawing and `model-building/` pure-Lagrangian/spectrum.
- Reject `plugins/feynman-diagrams/` for the computation stack. Rename existing `amplitude-calc` in `feynman-diagrams/` (if it exists) to a thin orchestrator hook or remove.
- Update all three proposals' §4 to point at `plugins/loop-computation/` before implementation.

## 8. "Single file `amp_reduced.m` with FormCalc-native PV heads."

**Quote (§3 Downstream):** "Single file `amp_reduced.m` with FormCalc-native PV heads. `/formcalc` should consume this as its canonical input; conversion from FormCalc `B0i[bb0,…]` to LoopTools `PVB[0,0,…]` is a trivial rule set owned by `/formcalc`."

**Counter.** `/formcalc`'s proposal §2 explicitly declares its input contract as a file "with amplitudes already in **Passarino–Veltman form** (coefficients of `PVA`, `PVB`, `PVC`, `PVD`)". FormCalc's native output is `A0i`/`B0i`/`C0i`/`D0i` via **`Abbreviate[]` chains** — opaque symbols like `Abb1`, `Pair1` that wrap the PV functions. If we ship `amp_reduced.m` with abbreviations unexpanded, `/formcalc` cannot apply `LoopRefine` without first un-abbreviating, which means either (a) `/formcalc` owns a FormCalc-abbreviation-aware de-abbreviator (messy), or (b) `/formcalc` emits two files: abbreviated + expanded.

**Synthesizer action.**

- `/formcalc` emits **two files**: `amp_reduced.m` (abbreviated, for performance / re-use) and `amp_expanded.m` (abbreviations inlined, PV heads visible). The contract to `/formcalc` is `amp_expanded.m`. Both files carry a header comment `(* formcalc-output v1; pv-form; scheme=<x>; abbreviated=<yes|no> *)`.
- Ownership of `B0i → PVB` name translation: **`/formcalc`**, not `/formcalc`. Do the rename at emission time via an explicit replacement rule. Single source of truth for the mapping, versioned with `formcalc_version`.
- Revise the open-Q about `--abbreviate on|off` default: keep abbreviated as an internal optimisation, but always emit expanded to disk.

## 9. Kinematics input format — unspecified

**Quote (§2):** `--mandel-invariants "s,t,u"` and `prepare_kinematics.py <proc>`.

**Counter.** The proposal hand-waves the kinematics spec. For scattering processes (which is most of the paper — σ_SI is χN → χN at q² ≈ 0), the user must specify: incoming/outgoing PDG IDs, masses, the on-shell relations, *and* the small-q² kinematic limit. This is exactly where `/formcalc`'s `--expansion-limit q2=small` lives. If `/formcalc`'s kinematics spec and `/formcalc`'s expansion spec are not the same JSON shape, the user has to reconcile two formats for a single physical process.

Also: `/feynarts` proposer §2 takes `--process '{F[1],-F[1]} -> {V[1],V[1]}'` — raw FeynArts tuples. `/formcalc`'s `--process <pid>` is a bare PID, pointing at `/feynarts` output. These don't even use compatible identifier schemes.

**Synthesizer action.**

- Define a single shared **ProcessSpec** JSON schema at `plugins/loop-computation/skills/_shared/processspec.schema.json` (parallel to `modelspec.schema.json`). Fields: `process_id` (short canonical alias, e.g. `chi_N_to_chi_N`), `feynarts_tuple` (the raw FeynArts expression), `incoming`, `outgoing`, `kinematic_limit` (e.g. `{q2: 0, v: 0}`), `mandelstam` (derived).
- `/feynarts` writes it, `/formcalc` reads it, `/formcalc` reads it. One file, one schema, hashed into the cache keys of all three.
- Remove `--mandel-invariants` flag from `/formcalc` v1; the spec file is the source of truth.

## 10. Caching — is FormCalc output deterministic?

**Open Q from sibling `/formcalc`:** "Cache on `sha256(formcalc-output)`."

**Counter.** FormCalc's output **is mostly deterministic** in the symbolic result, but the `Abb`/`Pair` abbreviation symbol names can depend on the order of expression traversal, which in turn can depend on kernel pattern-matching internals (Mathematica is not guaranteed stable across patch releases). Two invocations with the same input can produce equivalent `amp_reduced.m` files that differ in abbreviation naming and therefore have different SHA256s — cache misses on identical physics. Worse: if we cache on `sha256(amp_reduced.m)`, a no-op Mathematica patch release will invalidate every cache entry.

**Synthesizer action.**

- Cache key for `/formcalc` must be on **input** (FeynAmpList sha256 + scheme + fermion-chain + formcalc_version), not on **output**. This matches the `/spheno-build` pattern (input-only key). Store at `$STATE_ROOT/models/<name>/formcalc/<proc>/.build_key`.
- Downstream `/formcalc` should cache on *its own input* (the `amp_expanded.m` canonical-normalised form — strip abbreviations, sort sums, canonical index renaming — before hashing). Flag for `/formcalc` proposer: their "sha256(formcalc-output)" key is fragile; they need a canonicalizer.

## Missed opens (not in proposer's §5)

1. **Wolfram activation status propagation.** `/sarah-install` returns `activation_required` as a status, not a blocker. Does `/formcalc-install` inherit this pattern? The proposal doesn't say. It must — otherwise a fresh machine first running `/formcalc-install` hits a fatal blocker instead of a user-actionable prompt. Add explicit precedent reference to §1.

2. **LoopTools on macOS ARM.** LoopTools 2.16 has open issues on Apple Silicon (quad-precision build requires `libquadmath`, which is not in Apple's toolchain). The install plan needs a platform probe: on `macos + arm64`, either disable quad-precision (`libooptools-quad.a` omitted) or fail early with `LOOPTOOLS_QUADMATH_ABSENT` and a `user_instruction` pointing at Homebrew `gcc` (not Apple clang).

3. **Interaction with `/madgraph` NLO.** MadGraph's NLO loop mode also uses FormCalc-like machinery (via GoSam / MadLoop). Are we sure `/formcalc` and `/madgraph --nlo` won't produce divergent numeric answers from the same model? Worth a golden cross-check in `tests/fixtures/` for one tree-level process where both pipelines overlap.

4. **Testing gate.** Proposal open Q7 asks `HEPPH_RUN_WOLFRAM_TESTS` vs `HEPPH_RUN_NETWORK_TESTS`. These are different axes: Wolfram-local-only, download-required, and slow (minutes). Need a three-gate convention: `HEPPH_RUN_WOLFRAM_TESTS` (local Wolfram, no network), `HEPPH_RUN_NETWORK_TESTS` (downloads), `HEPPH_RUN_SLOW_TESTS` (>30 s). Apply uniformly to `/feynarts`, `/formcalc`, `/formcalc`.

5. **`--exclude-particles` symmetry with `/feynarts`.** `/feynarts` proposer exposes `--exclude-particles`; `/formcalc` does not. If a diagram was painted and the user then wants to drop a subset before reduction, where does that flag live? Either forbid post-hoc exclusion (diagrams are committed at `/feynarts` time) or push the flag down to `/formcalc` too. Recommend: commit at `/feynarts`, forbid at `/formcalc`.

6. **Reference_only escape hatch.** The blocker schema has a `reference_only` branch for cases where the real tool can't run. Does `/formcalc` ever fall back? The "augment not replace" memory says never — but the schema allows it. Proposal should state explicitly: **`/formcalc` never emits `reference_only`; missing FormCalc is a fatal blocker, full stop.**

---

**Bottom line.** The proposal is structurally sound but has four must-fix items before plan-mode: (a) plugin placement — resolve the three-way conflict; (b) γ₅ recoverable → fatal; (c) drop Fortran-out from v1; (d) downstream contract to `/formcalc` needs expanded-abbreviation file + canonicalized naming + shared ProcessSpec schema. Four nice-to-fix: FORM PATH strategy, model-sensitive scheme default, input-keyed cache, and distribution-reality probe on install.
