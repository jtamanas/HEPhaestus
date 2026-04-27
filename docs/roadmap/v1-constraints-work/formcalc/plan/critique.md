# `/formcalc` Plan — Skeptical Critique

**Critic:** skeptical plan critic
**Date:** 2026-04-19
**Target:** `docs/roadmap/v1-constraints-work/formcalc/plan/draft.md`
**Cross-reads:** `formcalc/brainstorm/final.md`, `feynarts/plan/draft.md`, `formcalc/plan/draft.md`, `plugins/shared/install-helpers/_common.sh`, `plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md`.

Format: **quote** → **counter** → **synthesizer action**.

---

## 1. FORM version pin is not justified by a probe

> "`scripts/build_form.sh` — downloads FORM 4.3.1 tarball from `github.com/vermaseren/form/archive/refs/tags/v4.3.1.tar.gz`"

**Counter.** FORM is Vermaseren's C/C++ source tree and the public release cadence is notoriously lumpy. The plan asserts 4.3.1 via the brainstorm's "default (latest stable as of FormCalc 10.0)" line, but the plan itself never probes the tag list or the FormCalc 10.0 `README` / `configure.ac` to confirm FormCalc 10.0 actually links cleanly against 4.3.1. The brainstorm even flags this as an open question (§7 Q1) — but the plan silently freezes the default instead of resolving it. Worse: the tag URL written in the plan is the **archive** URL (`.../archive/refs/tags/v4.3.1.tar.gz`), which is a Git-generated source snapshot, not an `autoreconf`'d release tarball. The archive form has no `configure` script; the `autoreconf -i` step the plan calls is therefore load-bearing and will fail without `autoconf`, `automake`, `libtool`, `m4`. None of those are preflight-checked.

**Synthesizer action.** (a) Add a pre-step to fetch FormCalc 10.0's upstream changelog/README and record the FORM version it was tested against in the plan itself (single source of truth, not a brainstorm footnote). (b) Either switch the URL to the official release tarball from `vermaseren.github.io` / `nikhef.nl` (which ships a generated `configure`), or add `autoconf`, `automake`, `libtool`, `m4` to the prereq probe in step 5 with a `TOOLCHAIN_MISSING` fatal blocker code. (c) Document in §2 the fallback if `v4.3.1` is EOL at install time — env var override + explicit "last-tested pin" vs. "current default" distinction.

---

## 2. `<install-root>/form/<arch>-<os>/form` — who reads this path?

> "`<install-root>/form/<arch>-<os>/form` (no `$PATH` symlink)."

**Counter.** The plan mandates no `PATH` pollution, which is good, but then never specifies where `<install-root>` actually is. `$UserBaseDirectory/Applications/` (where FormCalc lives) is one option; `$HOME/.local/share/hep-ph-agents/` is another; `$CONFIG_DIR/form/` is a third. Without a canonical rule, `form_binary` in `config.json` becomes the *de facto* contract, and every downstream smoke test, re-install, and uninstall has to round-trip through the config to know what to delete. The brainstorm's §1.2 table also leaves `<install-root>` as a literal placeholder.

**Synthesizer action.** Pin `<install-root>` to `$XDG_DATA_HOME/hep-ph-agents/` (default `$HOME/.local/share/hep-ph-agents/`) in §2 and in the installer SKILL.md. Write `form_binary` as the one absolute path and have the driver `.wls` read **only** `form_binary` from config, never reconstruct it. Add a unit test that `form_binary` resolves to an executable file after `install`.

---

## 3. γ₅ static check — the detection method is unspecified

> "`scripts/gamma5_static_check.wls` — pre-`CalcFeynAmp` symbolic pass over `FeynAmpList.m` counting γ₅-sensitive `DiracTrace`/`FermionChains` occurrences."

**Counter.** "Counting occurrences" is not a detection algorithm. FeynArts emits `FeynAmpList` with `FermionChain[...]` and `DiracTrace[...]` heads that *may* be chiral via an explicit `ChiralityProjector`, `gamma5`, `7`/`6` (FormCalc's shorthand for `PL`/`PR`), or indirectly via a `Coupling` with a `G[-1]` vector–axial split. A naive `Count[expr, _DiracTrace, Infinity]` will flag every fermion loop, chiral or not, and will *miss* amplitudes where the chirality enters through the coupling matrix rather than a `gamma5` symbol. Plan does not say whether this is a regex-on-text pass, a `Cases[]` pattern on the parsed expression, or a full AST walk.

**Synthesizer action.** Specify the exact Mathematica pattern match. Recommendation: load `FeynAmpList.m` with `Get[]`, then `Cases[held, _ChiralityProjector | gamma5 | 6 | 7, Infinity]` on the held expression, **and** inspect coupling symbols for axial-vector components (FormCalc exposes `G[-1]`). Document that regex-on-text is rejected (brittle under Mathematica pretty-printing). Add two fixtures beyond the current plan: a *chiral-via-coupling* amplitude (no explicit `gamma5`) and an *anomaly-cancelling full-multiplet* amplitude.

---

## 4. `.build_key` atomicity — "write last" is not atomic

> "Cache flow: … write `.build_key` last, atomically."

**Counter.** "Write last" ≠ atomic. If `amp_reduced.m` is written, then the driver crashes mid-`Put` of `amp_reduced.meta.json`, then `.build_key` is never written — fine, next run is a miss. But if `.build_key` itself is written via `open().write()` without `fsync` + `rename`, a crash between `write` and the filesystem commit leaves a partial or zero-length `.build_key` and the *next* run computes a different hash and calls it a miss — still safe. The real poisoning mode: driver succeeds, writes outputs, writes `.build_key`, but a later partial failure corrupts `amp_reduced.m` (e.g. disk full during symlink update). Nothing detects the drift. `_common.sh::config_merge` already implements the correct tmp+fsync+rename+dir-fsync dance; the plan reinvents a weaker version.

**Synthesizer action.** (a) Write `.build_key` via the same tmp+fsync+rename+dir-fsync pattern as `config_merge` — lift the helper into a shared `atomic_write_text` utility in `plugins/shared/install-helpers/` or shell it out to a Python one-liner. (b) The build-key *content* should hash the **output** file mtimes + sizes alongside the input hash (or re-hash `amp_reduced.m` on read), so that post-write corruption manifests as a cache miss rather than silent use of a poisoned artefact. (c) Add a unit test: delete `amp_reduced.m` but leave `.build_key`; confirm the next invocation treats it as a miss.

---

## 5. Smoke test — "assert `form.log` contains `Time = `" is underspecified

> "load FormCalc in wolframscript + run trivial CalcFeynAmp. Asserts `form.log` contains `Time = `."

**Counter.** Which `CalcFeynAmp` call? The plan lists "a one-diagram QED amplitude (drawn inline in the `.wls`)" in the brainstorm but never pins the exact topology, regulator flag, or γ₅ scheme used in the smoke. A one-diagram QED amplitude is γ₅-free (pure vector), so the smoke can't exercise the γ₅ code path — that's fine for the smoke specifically, but the plan should call out the asymmetry explicitly so nobody "improves" the smoke test into something that exercises γ₅ and then fails because the driver chose a default scheme. Also: `Time = ` appears in nearly every FORM run; it's not a *correctness* assertion, it's a *FORM was invoked* assertion. If FORM crashes after printing "Time = ", the smoke passes.

**Synthesizer action.** (a) Commit the exact `.wls` body in the plan (or the spec): `CreateTopologies[0, 1 -> 1, ExcludeTopologies -> Internal]` → one-diagram self-energy, `CalcFeynAmp[..., FermionChains -> Weyl]`. (b) In addition to the `Time = ` marker, assert the returned expression from `CalcFeynAmp` is `Head[_] === Amp` and has non-empty `PolynomialForm`. (c) Make the smoke deterministic: fix a seed-irrelevant process (e.g. photon self-energy) so the result is independent of `$RandomSeed`.

---

## 6. Sidecar schema location — contract, not a local file

> "`plugins/hep-ph-toolkit/skills/_shared/amp_reduced.meta.schema.json` (new)"

**Counter.** The `/formcalc` plan (§1 prereq 3) reads this schema from exactly that path and references it through a relative import from the sibling skill directory. `/feynarts` plan (§1.1) has already **relocated** the blocker schema to `plugins/shared/schemas/` and replaced the old `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` with a pointer shim, precisely to avoid this cross-skill relative-path tangle. Keeping `amp_reduced.meta.schema.json` under `skills/_shared/` contradicts the pattern `/feynarts` just established one workstream earlier. If `/formcalc` wants to import it from a plugin that doesn't yet exist at its skill's relative path (or if a future skill outside `feynman-diagrams/` wants it — e.g. `/madgraph`), the contract is locked to a brittle path.

**Synthesizer action.** Move the sidecar schema to `plugins/shared/schemas/amp_reduced.meta.schema.json` in line with `/feynarts`'s §1 relocation. Update `/formcalc` prereq list accordingly (coordinate with that workstream; since it hasn't landed, this is a cheap edit). `processspec.schema.json` should make the same move (it already does, per `/feynarts` plan §1.1). Add a verification-checklist item: "no cross-plugin relative imports of schema files".

---

## 7. Exit code reuse — `EXIT_SPHENO_MAKE=23` for FORM/LoopTools is misleading

> "we reuse `EXIT_SPHENO_MAKE=23` generically for LoopTools/FORM build failures; no new shared exit codes needed."

**Counter.** `_common.sh` names that code `EXIT_SPHENO_MAKE` explicitly. Reusing it for FORM and LoopTools means the exit-code → tool mapping becomes ambiguous at the parent-process level; a CI log showing "exit 23" now could mean SPheno, LoopTools, or FORM. The numeric space is cheap — `_common.sh` uses 10, 11, 12, 13, 14, 15, 16, 20, 21, 22, 23, 24, 25. Adding `EXIT_FORM_BUILD=26` and `EXIT_LOOPTOOLS_BUILD=27` costs one line in `_common.sh` and eliminates the ambiguity. The plan's self-imposed rule "no edits to `_common.sh`" (§2) is the *cause* of this shoehorn, but `_common.sh` is owned by W0 and exit codes are an additive change — this is exactly the kind of edit W0 exists to rubber-stamp.

**Synthesizer action.** File a W0 (shared-contracts) micro-PR adding `EXIT_FORM_BUILD=26`, `EXIT_LOOPTOOLS_BUILD=27`, `EXIT_TOOLCHAIN_MISSING=28`. Coordinate with `/feynarts` and `/formcalc` to batch any other needed codes. If W0 coordination is impractical in this workstream's window, keep the reuse but add a compensating convention: every `exit 23` call site in `/formcalc-install` must also emit the blocker JSON with the specific code (`FORM_BUILD_FAILED`, `LOOPTOOLS_BUILD_FAILED`), and a CI grep ensures the blocker JSON is emitted **before** the `exit 23`, so the numeric code is a secondary signal.

---

## 8. Apple-Silicon branch — `gfortran --version` won't catch architecture

> "Apple-Silicon branch: probe `libquadmath.dylib` under `brew --prefix gcc`"

**Counter.** The plan does not say *how* the arch is detected before choosing the branch. `gfortran --version` reports the compiler version, not the target architecture; on a Rosetta 2 shell, an `arm64` host can present an `x86_64` gfortran. The correct gate is `uname -m` (or `arch`) **and** `uname -s`, evaluated in the installer's entry script. Also: `brew --prefix gcc` assumes Homebrew GCC is installed under that formula name — Homebrew has shipped both `gcc` and `gcc@<n>` at various times; `gcc` currently aliases to the latest major, but `libquadmath.dylib` may live under a version-suffixed prefix (`gcc@13`). The plan's one-shot `brew --prefix gcc` will miss those users.

**Synthesizer action.** (a) Detect arch via `case "$(uname -s)-$(uname -m)" in Darwin-arm64) ... esac` — explicit, no guessing. (b) Probe `libquadmath.dylib` by searching `brew --prefix gcc` *and* `brew --prefix gcc@13`, `gcc@14`, `gcc@15` (or glob `$(brew --cellar)/gcc*/*/lib/gcc/*/libquadmath.dylib`). (c) Elevate this to a **pre-flight check** emitted by `detect`, not just a mid-install decision, so `detect` on darwin-arm64 surfaces `looptools_quad: false` expected *before* the user runs `install`.

---

## 9. FeynArts version compatibility — sidecar declares it, driver ignores it

> (Plan §1.4 reads FeynArts output; no mention of version gating.)

**Counter.** `/feynarts` plan §2.3 writes `FeynAmpList.meta.json` with a `feynarts_version` field (inherited from the schema). FormCalc 10.x is compatible with FeynArts 3.11 only; FeynArts 3.10 and 3.9 emit subtly different `FeynAmpList` structures (different label conventions, loop-integral shorthands). `/formcalc`'s plan reads `FeynAmpList.m` via `<<` with zero validation of the upstream `feynarts_version`. If a user runs an old `/feynarts` install, `/formcalc` will silently produce garbage or crash inside `CalcFeynAmp` with an opaque Mathematica error.

**Synthesizer action.** Add a step to `run_formcalc.py`: before invoking the driver, read `input/FeynAmpList.meta.json`, assert `feynarts_version` matches a pinned set (`{"3.11"}` for v1), emit fatal `FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` on mismatch with `user_instruction` pointing at `/feynarts-install`. Add the code to §2's blocker enum additions. Pin the compatible FeynArts versions in `SHARED.md` (the plan already mentions the Phase-B matrix exists; use it).

---

## 10. QED golden — coupling normalisation is unpinned

> "result must match the textbook `|M|² = e⁴(1 + cos²θ)`. Tolerance: exact symbolic equality after `Simplify`."

**Counter.** FormCalc's `EL` is the elementary charge in its own internal normalisation; the textbook `e` assumes Gaussian-natural units with `α = e²/(4π)`. FormCalc and FeynArts use `EL^2 = 4π α` as the coupling that appears in vertices, which is consistent with the textbook — but the `e⁴` the plan asserts will literally appear as `EL^4` in the emitted amplitude, and `Simplify` will not rewrite `EL → e` without a substitution rule. A naive `Simplify[|M|² - e^4 (1 + Cos[θ]^2)]` returns non-zero. Additionally, the spin average / sum factor of `1/4` for initial-state-averaging is easy to forget; the plan says "averages initial" but doesn't pin the exact code path.

**Synthesizer action.** (a) Commit the exact assertion code in the integration test, not a prose description: include the substitution `{EL -> e, ME -> 0, MM -> 0}`, the `1/4 * Sum[..., {spins}]` averaging, and the `Simplify[..., Assumptions -> {s > 0, Element[θ, Reals]}]` call. (b) Use `PossibleZeroQ` (or `FullSimplify` with assumptions) rather than literal `Simplify`-then-`===`, since `Simplify` is notoriously unreliable for symbolic zero-detection on trig identities. (c) Add a negative control: an intentionally-wrong reference (`e^4 (1 + cos θ)^2`) must *fail* the assertion — proves the test can fail.

---

## Summary of top synthesizer actions

1. Pin FORM version against FormCalc 10.0's upstream compat matrix; add toolchain preflight (`autoconf`/`automake`/`libtool`/`m4`).
2. Canonicalise `<install-root>` = `$XDG_DATA_HOME/hep-ph-agents/`; make `form_binary` the sole contract.
3. Specify γ₅ detection as a Mathematica `Cases[]` on `ChiralityProjector | gamma5 | 6 | 7` plus coupling inspection; add two fixtures.
4. Use `_common.sh`-style atomic-write for `.build_key`; hash output mtimes alongside inputs.
5. Commit the smoke-test `.wls` body in the plan with explicit content assertions beyond `Time = `.
6. Relocate `amp_reduced.meta.schema.json` to `plugins/shared/schemas/`, matching `/feynarts`'s relocation.
7. File a W0 micro-PR adding `EXIT_FORM_BUILD=26` and `EXIT_LOOPTOOLS_BUILD=27`; stop overloading `EXIT_SPHENO_MAKE`.
8. Detect darwin-arm64 via `uname -m`; glob `gcc@*` prefixes; surface `looptools_quad: false` at `detect` time.
9. Validate `feynarts_version` from the upstream sidecar before `CalcFeynAmp`; add `FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` fatal code.
10. Pin the QED golden's substitution + averaging + assumptions; add a negative-control assertion.

Word count: ~1450.
