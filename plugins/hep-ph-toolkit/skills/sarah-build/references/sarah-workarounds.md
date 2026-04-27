# SARAH wrapper workarounds

A catalogue of the non-obvious tricks `/sarah-build` has to apply because SARAH
(and, underneath it, Mathematica) does things that do not compose cleanly with
an automated pipeline. Every entry lists: **symptom** (what you see if it's
missing), **cause** (why it has to exist), **mitigation** (what we do), and
**where** (file:line where the workaround lives).

For the separate class of *model-authoring* traps that SARAH silently tolerates
(wrong Weyl decomposition, single-letter BSM names, Majorana in `LagNoHC`, etc.),
see `SKILL.md` → "Gotchas (SARAH-idiom discrepancies)". That section documents
six more items; they're not repeated here.

---

## Infrastructure-level workarounds

### 1. Fresh Mathematica kernel per invocation
- **Symptom:** `::shdw` shadowing messages, followed by later calls returning
  `$Failed` or unevaluated expressions with no further diagnostics.
- **Cause:** SARAH defines hundreds of symbols in `` Global` `` during
  `Start["Name"]`. Any symbol that exists in the kernel *before* SARAH loads
  gets shadowed. Loading two SARAH sessions into one kernel compounds this.
- **Mitigation:** We invoke `wolframscript -code …` as a subprocess per build,
  so every run gets a fresh kernel. Never run `<<SARAH\`` twice in one kernel.
- **Where:** `scripts/run_sarah.py` — the `subprocess.run([wolfram_engine_path,
  "-code", code], …)` call.

### 2. Serialise same-model builds with a file lock
- **Symptom:** Two concurrent `build.py` runs on the same spec either produce
  one corrupted UFO tree or hang; logs are interleaved.
- **Cause:** SARAH reads from `$sarah_path/Private-Models/<Name>/` and writes
  to `$sarah_path/Output/<Name>/`. Both paths are derived from `$sarah_path`
  and the model name — not from cwd — so parallel callers share them and race
  at the filesystem level.
- **Mitigation:** `fcntl.flock` on `$STATE_ROOT/models/<name>/.sarah_build.lock`
  around the full stage → invoke → collect → scan → write-cache sequence.
  Hot-cache callers return before acquiring the lock; cold callers double-check
  the cache after acquisition.
- **Where:** `scripts/run_sarah.py` — `_sarah_build_lock()` contextmanager.

### 3. `rmtree` the staged dir to nuke `.mx` caches
- **Symptom:** Model changes do not take effect — SARAH silently reloads a
  compiled `.mx` cache written by a previous run.
- **Cause:** SARAH auto-writes Mathematica `.mx` files next to model `.m`
  files. They live inside `Private-Models/<Name>/` and are not invalidated
  by overwriting the `.m` source.
- **Mitigation:** `stage()` deletes the entire staged dir before rewriting.
- **Where:** `scripts/stage.py:55-56` — `if staged.exists(): shutil.rmtree(staged)`.

### 4. `$Path` must reference `sarah_path/..`, not `sarah_path`
- **Symptom:** `<<SARAH\`` errors `Context SARAH\` not found`.
- **Cause:** `<<Name\`` resolves by looking for a `Name/` subdirectory on
  `$Path`. SARAH's package directory already *is* that subdirectory, so its
  parent is what `$Path` needs.
- **Mitigation:** `AppendTo[$Path, "<sarah_path>/.."]` before `<<SARAH\``.
- **Where:** `scripts/run_sarah.py` — see the constructed `code` string. Do
  **not** drop the `/..`; this mirrors `install_sarah.sh:probe_version`.

### 5. Scan logs for fatal blockers (SARAH does not exit non-zero)
- **Symptom:** `wolframscript` exits 0 and writes output files, but the files
  are nonsense (`Param.$Failed`, `None` particle names).
- **Cause:** SARAH prints errors via `Message[…]` and keeps going. Most of
  its "errors" are side-effect prints, not exceptions. `CheckModel::*Abort*`,
  `ModelFile::MissingModel`, `MatterSector::parseError`, etc. all leave a
  zero exit code.
- **Mitigation:** After `wolframscript` writes `sarah.log`, the agent reads
  it directly. Fatal patterns that guarantee a broken build trigger blocker
  emission; hint patterns tag soft signals that correlate with silently-
  degraded output.
- **Where:** `SKILL.md` §"Reading sarah.log":
  - Fatal patterns: `Anomalies are not cancelled`, `Error: field \w+ undefined`.
  - Hint patterns: `Part::partd:.*None[[`, `StringJoin::string:.*W<>None`,
    `ToExpression::notstrbox:.*W<>None`, `Part::partw`.

### 6. Scan output trees for Mathematica-internals leakage
- **Symptom:** `sarah.log` is clean but the emitted UFO/SPheno sources
  contain literals like `Param.$Failed`, `Global\`…`, particles named
  `"None"`, or raw SARAH-internal function calls (`SAxDynL(…)`).
- **Cause:** Some SARAH failure modes never reach the log. Missing entries
  in `parameters.m`, rank-1 Dirac sub-blocks, and braced singleton Weyl
  declarations can all produce syntactically-valid but semantically-broken
  output with only a `CheckModelFiles::MissingParameter` warning. Separately,
  SARAH's Fortran/Python serialiser occasionally fails to reduce symbolic
  expressions — the raw Mathematica form ends up in the emitted file.
- **Mitigation:** After `collect()`, walk `sarah_output/{UFO,SPheno}/…` and
  grep every `.f90`/`.py` file line-by-line for the 12-token forbidden list.
  On hit → `SARAH_OUTPUT_CORRUPT`, fatal, cache key **not** stamped.
- **Forbidden tokens** (`scan_outputs._PATTERNS`):
  - Mathematica error markers: `$Failed`, `$Aborted`, `$Interrupted`.
  - Leaked SARAH internals: `SAxDynkin(`, `SAxDynL(`, `SAxMulFactor(`,
    `SAxCasimir(`.
  - Unevaluated Mathematica forms: `Part[List[…]]` / `Part[{…}]`,
    `Hold[/HoldForm[/HoldComplete[`, `Missing[/Failure[`, `None[[`.
  - Bare Mathematica string-concat: `Name<>Name`.
- **False-positive carve-out:** SPheno legitimately `Write()`s the literal
  string `"$Failed"` in diagnostic messages, so the `DOLLAR_FAILED` pattern
  (and only that one) skips lines matching
  `^\s*Write\(.*\".*\$Failed` (`scan_outputs._DIAG_WRITE_RE`).
- **Where:** `scripts/scan_outputs.py`; invoked from
  `scripts/run_sarah.py` — the `scan_outputs(...)` call.

### 7. Stamp the cache key *after* scan, not inside `collect()`
- **Symptom:** A corrupt build gets cached. Every subsequent `build.py` call
  returns `{"status": "cached"}` pointing at broken output.
- **Cause:** An earlier version of the code stamped `.sarah_build_key` inside
  `collect()`, before scan ran. A corrupt tree therefore stamped its own cache.
- **Mitigation:** `_write_cache_key()` runs only after `scan_outputs()` returns
  `clean`. `collect()` no longer writes the key.
- **Where:** `scripts/run_sarah.py` — `_write_cache_key(...)` call; the old
  write at `collect.py:150` is gone (plan §3.2, D2).

### 8. Stage into `Private-Models/`, never into `Models/`
- **Symptom:** Reinstalling SARAH resets the model because it was committed
  to the vendor tree.
- **Cause:** SARAH's built-in `Models/` directory is part of the distributed
  install. Writing there mingles our models with upstream's and breaks
  reproducibility across SARAH upgrades.
- **Mitigation:** Render into `$sarah_path/Private-Models/<Name>/` (which
  SARAH also scans). `stage()` `mkdir -p`s it because SARAH does not create
  it on first use.
- **Where:** `scripts/stage.py:50-51`.

### 9. Wolfram Engine activation cannot be scripted
- **Symptom:** Fresh install → first `wolframscript` call hangs forever on
  "Enter your Wolfram ID".
- **Cause:** Activation binds the Engine to a free Wolfram ID and requires a
  browser round-trip. There is no headless activation API.
- **Mitigation:** `/sarah-install` emits an explicit manual-step banner
  ("Not possible to automate — activation requires a browser and a free
  Wolfram ID") and blocks the rest of the install until `wolframscript -code
  "1+1"` returns `2`.
- **Where:** `plugins/hep-ph-toolkit/skills/install/SKILL.md` → "Wolfram wall";
  gate enforced by `check_wolfram_activation.sh`.

### 10. Pin SARAH to 4.15.x
- **Symptom:** Build succeeds on 4.15 but the same spec emits subtly different
  output (or different failure mode) on 4.14 or 4.16.
- **Cause:** SARAH has no API-stability guarantee across minor versions.
  Internal rewrites of the Lagrangian scanner, mass-matrix extractor, and
  parameter resolver have landed in minor releases.
- **Mitigation:** Every `ModelSpec` must declare
  `sarah_version_required: ">=4.15,<4.16"`, and the cache key includes the
  installed SARAH version so upgrading invalidates prior builds automatically.
- **Where:** spec schema at `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`;
  the v3 backend (deletion of v1 sub-rendering) is at
  `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/`.

### 11. Output tree discovered by glob, preferring `EWSB/`
- **Symptom:** `FileNotFoundError: UFO model directory not found` after a
  successful SARAH run, even though `Output/<Name>/` exists.
- **Cause:** SARAH writes to `Output/<Name>/<NameOfStates>/UFO/` where
  `<NameOfStates>` varies by model (usually `EWSB`, but not universal —
  some models produce multiple intermediate stages). The actual directory
  name is not exposed as a config option.
- **Mitigation:** Glob `Output/<Name>/*/UFO`. If multiple matches, prefer
  the `EWSB/` parent; otherwise fall back to most-recently-modified.
- **Where:** `scripts/collect.py` — `_find_output_dir()`.

### 12. Flat-vs-nested UFO layout probed at collect time
- **Symptom:** `particles.py` not found where we expect.
- **Cause:** SARAH 4.15.3 writes `UFO/particles.py` directly into the flat
  UFO directory. Older SARAH versions (and earlier revisions of our own
  codebase) expected a nested `UFO/<Name>/particles.py` layout.
- **Mitigation:** `collect()` probes `UFO/<Name>/particles.py` first, then
  the flat `UFO/particles.py`; copies from whichever is present. Destination
  is always the nested shape — that's the stable public contract downstream
  consumers rely on.
- **Where:** `scripts/collect.py:119-129`.

### 13. Model-name canonicalisation (snake_case → SARAH's CamelCase)
- **Symptom:** `Start["dark_su3"]` fails with `ModelFile::MissingModel`
  because SARAH looks up `Private-Models/DarkSU3/`.
- **Cause:** Our specs use lower snake_case for filesystem friendliness;
  SARAH expects PascalCase-with-preserved-physics-abbreviations. Plain
  `.title()` produces wrong output (`dark_su3` → `Dark_Su3`, not `DarkSU3`).
- **Mitigation:** Custom title-casing rule: split on `_`; for each segment,
  uppercase the leading alpha run if its length is ≤2 chars (group
  abbreviations like `su`, `u`, `sp`), otherwise `.capitalize()`. Digits
  pass through. Examples: `dark` → `Dark`; `su3` → `SU3`; `u1` → `U1`;
  `2hdm_a` → `2hdmA`. The module docstring still flags this `PROVISIONAL` —
  not every abbreviation SARAH expects has been reproduced.
- **Where:** `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` —
  `_title_part()`.

### 14. No-op knobs that look like they should work
- **Symptom:** You reach for `SetOptions[MakeAll, IncludeSPheno->False]` to
  disable SPheno emission for a confining dark sector. Nothing happens.
- **Cause:** `SetOptions[MakeAll, ...]` affects `MakeAll[]`. Our dispatch
  calls `MakeSPheno[]` and `MakeUFO[]` directly — `MakeAll` is never
  invoked. The option is applied to a function that never runs.
- **Mitigation:** The real switch is spec-level: omit `"spheno"` from
  `spec.outputs`. `_build_make_commands()` maps `spec.outputs` to the
  concrete `Make…[]` calls, so `MakeSPheno[]` is simply not dispatched.
- **Where:** `scripts/model_ir.py:213-216` (docstring warning);
  `scripts/run_sarah.py` — `_MAKE_DISPATCH` + `_build_make_commands()`.

### 15. Emit SM lepton doublet as `LL`, not `l`, to dodge a SARAH symbol collision
- **Symptom:** Scanner (§6) fires `SARAH_OUTPUT_CORRUPT` with ~22 markers
  all in `RGEs_<Name>.f90`: `SAxDynkin(2,left)`, `SAxDynkin(2,color)`,
  `SAxCasimir(2,{color,left})`, `SAxDynL(2,hypercharge)`, plus `$Failed`
  inside gauge-coupling β expressions. In `Output/<Name>/RGEs/GijF.m` the
  SM lepton-doublet γ_ij entry renders as `{{2[{1}][{i1}], 2[{lef2}][{i2}]}, …}`
  while every other fermion (`d`, `e`, `u`, `q`, BSM fields) keeps its
  head symbol. Coefficients in the lepton entry retain unevaluated
  `SA\`Casimir[2, left]` / `SA\`DynL[2, hypercharge]^2`; other fields'
  coefficients reduce to rationals. Reproduces deterministically across
  cold rebuilds (shared `Output/<Name>/` and `.local/share/.../` wipes);
  not a concurrency race.
- **Cause:** SARAH 4.15.3 has a latent symbol-level pattern-match
  collision on the bare atom `l`. `l` is SARAH's own canonical SM
  lepton doublet symbol and works in the shipped `Models/SM` and
  `Models/SM+VL/PortalDM`; against specific BSM content (our singlet-doublet
  combines `DMParity` + Majorana singlet + a vectorlike SU(2)-doublet
  pair as two left-Weyls with explicit MatterSector mixings — the exact
  trigger is not isolated) `l` gets rewritten to the integer `2` — its
  SU(2) rep dim — during γ_ij assembly. The guard at SARAH's
  `mathRGEs.m:300` refuses to canonicalise integer-headed args of
  `SA\`Dynkin[_Integer, _]`, so the Dynkin/Casimir lookups stay
  symbolic and leak through the Fortran serialiser. Isolated by
  subagent bisection (A–C): `l → LL` rename clears it, `yh2` removal
  does not, renaming `q` (also SU(2)-doublet) unnecessary because `q`
  never corrupts. The collision is specific to the atom `l`.
- **Mitigation:** Emit `FermionFields[[2]] = {LL, 3, {vL, eL}, -1/2, 2, 1, …}`
  instead of `{l, …}`. Propagate the rename into `_SM_YUKAWA_EXPR`
  (`Ye conj[H].e.LL`) and the `WeylFermionAndIndermediate` entry
  (`{LL, {LaTeX -> "l"}}`). The LaTeX output stays `"l"` so user-visible
  physics presentation is unchanged; only SARAH's internal atom is
  renamed. Verified against a cold singlet-doublet build: 1002-line
  `RGEs_SingletDoublet.f90`, 0 scanner hits, γ_ij entry now reads
  `LL[{1}][{i1}], LL[{lef2}][{i2}]` with the canonical
  `(3*(g1^2 + 5*g2^2)*Xi*…)/20` form. (A downstream rank-1 Dirac
  sub-block compile error in `TreeLevelMasses` is a separate known
  class — see SKILL.md Gotcha #6 in the pointer below — and is
  unrelated to this workaround.)
- **Where:** the v3 renderer at
  `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/`.

### 16. Normalise rank-1 single-eigenstate Dirac masses at compile time
- **Symptom:** A clean `/sarah-build` (1002-line `RGEs_<Name>.f90`, 0
  scanner hits) is followed by a gfortran cascade in `/spheno-build`:
  ```
  TreeLevelMasses_<Name>.f90:148:32:
    Call CalculateMFChiM(MPsi,UM,UP,MFChiM,kont)
    Error: Rank mismatch in argument 'mfchim' at (1) (rank-1 and scalar)
  ```
  plus, once that's patched, further rank-0-vs-rank-3 assignment errors
  in `OneLoopDecays_<Name>.f90` (`ZfChiM = -SigmaRFChiM + …`), `Transpose`-
  rank errors (`MatMul(ZfChiM - Conjg(Transpose(ZfChiM)), UM)`),
  "`Unclassifiable statement`" errors in `BranchingRatios_<Name>.f90`
  (`gTFChi(i1) = Sum(gPFChi(i1,:))` where the declaration is `gTChi(3)`
  / `gPChi(3,0)` / `BRChi(3,0)` — no `F` prefix), "`Symbol … has no
  IMPLICIT type`" for `MSInput` / `MPsiInput` / `yh1Input` / `yh2Input`
  in `Boundaries_<Name>.f90` and `SPheno<Name>.f90` (declarations are
  `MSIN` / `MPsiIN` / `yh1IN` / `yh2IN`), and the mirror-inverted typo
  in `InputOutput_<Name>.f90` where decay-width guards use the wrong
  prefix in both directions (`gT1LFChi`, `gTFChiM` add ``F``; `PDGChiM`,
  `NameParticleChiM` drop ``F`` relative to `PDGFChiM`, `NameParticleFChiM`
  which are the locally-declared names). All symptoms share a root
  cause and all occur together; fixing just one leaves the others.
- **Cause:** SARAH 4.15.3's emitter is inconsistent about the Fortran
  rank of the mass-eigenstate variable for an EWSB mixing with
  **exactly one** Dirac mass eigenstate (nominal 1×1 left/right
  mixing). Some subroutine bodies treat the mass as a length-1 array
  (`MFChiM(1)`, `MFChiM2(1)`, `MFChiM_1L(1)`, and the self-energy
  arrays `SigmaRFChiM(1,1,1)` for the ChiM sector specifically),
  others treat it as a pure scalar (the module-level `Model_Data_<Name>.f90`
  declaration, every caller in `TreeMasses` / `LoopMasses` / `Boundaries`
  / `TreeLevel_Decays` / `CouplingsForDecays`). The caller-vs-callee
  mismatch is guaranteed to trip gfortran. The BranchingRatios, Boundaries,
  SPheno-driver, and InputOutput renderers layer on additional
  independently-broken name-prefix emissions for the same sector — the
  SARAH symbol table that tracks BSM fermion names appears to be
  fragile when the Dirac mixing dimension is 1. Touching the spec side
  (e.g. adding a second generation to fatten the sub-block to 2) dodges
  the class of bugs, but costs phenomenology; text-patching the emitted
  Fortran at compile time does not. Reproduces deterministically on
  cold rebuilds of `singlet_doublet` (charged eigenstate ChiM);
  conjectured to trigger for any model with a 1×1 Dirac sub-block, but
  not reproduced on a second spec. Related but distinct failure shape
  from Gotcha #6 in `SKILL.md`, which covers `Param.$Failed` leakage
  that escapes the scanner; the rank-mismatch here is caught by
  gfortran and never reaches the scanner. Cross-reference: §15 above
  is the *upstream* blocker (SM lepton doublet atom `l`) whose fix
  lets the build progress far enough to surface this one.
- **Mitigation:** `compile_model.py:_patch_rank1_dirac_mass` applies a
  scoped text patch post-SARAH, before the model tree is copied into
  the SPheno source. The patch (i) demotes every rank-1 length-1
  `Intent(out) :: <mass>(1)` declaration to scalar (in `TreeLevelMasses`
  `CalculateMF*` subroutines + `LoopMasses` `OneLoop*` subroutine
  Intent(out) and the module-private `*_1L(1)` cache), adjusting the
  ` = Sqrt( <mass2> )` tails to index into rank-1 `<mass2>(1)` locally
  (the local `<mass2>(1)` stays rank-1 because `EigenSystem` needs a
  vector); (ii) subscripts rank-3 self-energy arrays like `SigmaRFChiM`
  at `(1,1,1)` inside every `ZfChiM = …` / `ZfChiP = …` assignment
  block (including `&`-continuations) in `OneLoopDecays`; (iii)
  rewrites the two `MatMul(ZfChiM - Conjg(Transpose(ZfChiM)), UM)`
  lines to `(ZfChiM - Conjg(ZfChiM)) * UM` (scalar-safe); (iv) renames
  the extra-F typos `gTF<Name>` → `gT<Name>`, `gPF<Name>` → `gP<Name>`,
  `BRF<Name>` → `BR<Name>` and their `1L` counterparts in
  `BranchingRatios_<Name>.f90` for every BSM fermion name emitted
  there; (v) mirrors that rename into `InputOutput_<Name>.f90` and
  also applies the inverse `PDG<Name>` → `PDGF<Name>` /
  `NameParticle<Name>` → `NameParticleF<Name>` rename because SARAH
  gets the F prefix inverted there; (vi) rewrites `<param>Input` →
  `<param>IN` in `Boundaries_<Name>.f90` and `SPheno<Name>.f90` for
  every `*IN` symbol declared at module level in `Model_Data_<Name>.f90`.
  Safety filter: the Intent(out) demotion only fires for mass names
  declared scalar at module level (so `MFChi(3)` is not touched); the
  `Zf<…>` rewrite only runs when the rank-3 `(1,1,1)` shape is
  actually present. Idempotent: the regexes target the broken shape,
  not the fixed shape, so a second call is a no-op. The run-time
  `/spheno-build` wrapper also flips SPhenoInput flags ``16`` /
  ``13`` / ``57`` to 0 in the staged `LesHouches.in` — the one-loop
  decay counterterm path, 3-body decays, and low-energy constraints
  all evaluate NaN or hang inside `CalculateBR` for this Dirac shape;
  the tree-level + 2-body-BR spectrum is enough for the Profumo
  benchmark.
- **Where:** `plugins/hep-ph-toolkit/skills/spheno-build/scripts/compile_model.py`
  — `_patch_rank1_dirac_mass` (the main hook) and `_module_scalar_mass_names`
  (safety filter); wired into `compile_model.compile_model` after the
  Darwin `ar -U` strip and `Model_Data` dedupe. Runtime LesHouches flag
  flipping lives at `plugins/hep-ph-toolkit/skills/spheno-build/scripts/run_spheno.py`
  inside the SPhenoInput block append. Unit tests: `tests/test_rank1_dirac_patch.py`.

### 17. Full SARAH `*IN` input blocks + `PhaseFS` init for LOW-scale spectra
- **Symptom:** After §15 + §16 land, a `singlet_doublet` build compiles
  and SPheno runs to completion (no PROBLEM block), but the emitted
  `Block MASS` is numerically degenerate:
  ```
  25   0.00E+00  # hh          (should be ~125 GeV)
  9958431  0.0  # FChi_1       (should be ~275 GeV at MS=300, MPsi=500, y=0.3)
  9956206  500  # FChi_2       (correct only by coincidence)
  9979223  500  # FChi_3       (should be ~524 GeV)
  9984071  500  # FChiM        (the one that survives)
  ```
  `Block SM` shows `Lam = 0`, `m2SM = 0`. The ZN mixing matrix is purely
  imaginary-diagonal with `Aimag(ZN(1,1)) = 1`. Every singlet/doublet
  entry of the 3×3 Majorana neutralino mass matrix vanishes.
- **Cause:** Two orthogonal SARAH emission gaps surfaced by the same
  `HighScaleModel = "LOW"` + `CalculateOneLoopMasses = False` combination
  that the Profumo benchmark runs under:
  1. `SPheno<Name>.f90` selects `MatchingOrder = -1` (pole matching) in
     this configuration and pulls its initial ``g1``, ``g2``, ``g3``,
     ``vvSM``, ``Lam``, ``m2SM`` values from the module-level `*IN`
     variables. `Read_GAUGEIN`, `Read_SMIN`, `Read_HMIXIN` populate
     those variables from the corresponding `Block GAUGEIN`,
     `Block SMIN`, `Block HMIXIN` entries in the LesHouches input.
     `Read_BSMPARAMSIN` does the same for per-parameter `<name>IN`
     variables — we already emitted that block, but every other `*IN`
     block defaulted to zero in the module init, so the Higgs quartic
     stayed zero through ``Boundaries`` → ``SolveTadpoleEquations`` →
     ``TreeMasses`` and the Higgs mass dropped to zero (Higgs VEV still
     fills via ``SetMatchingConditions`` — that's why `Block HMIX` looks
     fine — but the Higgs quartic Lam was never seeded).
  2. `Model_Data_<Name>.f90` ships `PhaseFS = 0._dp` in
     `Set_All_Parameters_0`, and nothing ever assigns the variable
     elsewhere — `Read_PHASESIN` parses `Block PHASESIN` entries but
     discards the values, and the downstream sign-flip reassignments
     only fire when a mass eigenvalue turns negative. SARAH includes
     `PhaseFS` as a prefactor on every singlet/doublet entry of the
     neutralino mass matrix:
     ``mat(1,1) = MS*PhaseFS**2``,
     ``mat(1,2) = -PhaseFS*vvSM*yh2/Sqrt(2)``,
     ``mat(1,3) =  PhaseFS*vvSM*yh1/Sqrt(2)``,
     so with `PhaseFS = 0` the whole sub-block collapses and the
     spectrum degenerates to ``(0, MPsi, MPsi)`` regardless of MS / y /
     vvSM. This is a SARAH 4.15.3 emission bug for models where the
     Majorana sign-convention machinery is never exercised; the physical
     default is `PhaseFS = 1`. Both bugs reproduce deterministically on
     `singlet_doublet` cold builds.
- **Mitigation:** Two-part fix.
  (a) `leshouches_template.build()` now emits `Block GAUGEIN`,
      `Block HMIXIN`, `Block SMIN` alongside the existing
      `Block MODSEL` / `Block SMINPUTS` / `Block MINPAR` /
      `Block BSMPARAMSIN`. Numerical seeds:
      ``g1 = 0.4626``, ``g2 = 0.6488``, ``g3 = 1.2198`` (SM couplings at
      M_Z); ``vvSM = 246.22`` GeV; ``Lam = 0.25875 = m_h^2/v^2`` (tree-
      level SM Higgs quartic in SARAH's convention
      ``Mhh^2 = m2SM + 3 v^2 Lam / 2`` with tadpole
      ``m2SM = -v^2 Lam / 2`` → ``Mhh^2 = Lam v^2``); ``m2SM = -v^2 Lam/2``
      as a consistent seed that ``SolveTadpoleEquations`` overwrites.
      Most of these are redundant for paths other than
      `MatchingOrder = -1` (``SetMatchingConditions`` rederives
      ``g1``/``g2``/``g3``/``vvSM`` from `SMINPUTS` on every call), but
      ``Lam`` is the one value that uniquely lives in the `*IN` block
      and genuinely propagates through `Boundaries` → `OneLoopMasses`.
      Emitting all four blocks keeps the input complete regardless of
      which `MatchingOrder` path the downstream SPheno driver resolves
      to. Unit tests: `tests/test_leshouches_template.py`
      (`TestBuildBlockPresence::test_gaugein_present` / `_hmixin_present`
      / `_smin_present`, plus `TestBsmParamsIn`).
  (b) `compile_model._patch_phasefs_init` rewrites the single
      `PhaseFS = 0._dp` init line in `Set_All_Parameters_0` to
      `PhaseFS = 1._dp` (Fortran auto-promotes the real literal to the
      complex declaration). Applied post-SARAH, before the model tree
      is copied into the SPheno build root. Idempotent; does not touch
      legitimate downstream sign-flip reassignments (those have a
      different RHS, e.g. `PhaseFS = -1._dp`). Unit tests:
      `tests/test_phasefs_init_patch.py`.
- **Verification:** On `singlet_doublet` at MS=300, MPsi=500, yh1=yh2=0.3
  SPheno now reports the analytic spectrum within numerical tolerance:
  hh = 125.25, FChi_1 = 275.68, FChi_2 = 500.0, FChi_3 = 524.32,
  FChiM = 500.0 (all GeV). `Block SM` shows `Lam = 0.259`,
  `m2SM = -7843`. ZN mixing is no longer diagonal. No PROBLEM block.
- **Where:**
  - LesHouches template blocks:
    `plugins/hep-ph-toolkit/skills/spheno-build/scripts/leshouches_template.py`
    — module-level `_GAUGEIN_LINES`, `_HMIXIN_LINES`, `_SMIN_LINES`
    plus the `sections` list in `build()`.
  - PhaseFS init patch:
    `plugins/hep-ph-toolkit/skills/spheno-build/scripts/compile_model.py`
    — `_patch_phasefs_init`, wired into `compile_model` after
    `_patch_rank1_dirac_mass`.

---

## Model-authoring traps (pointer)

`SKILL.md` → "Gotchas (SARAH-idiom discrepancies)" catalogues six
workarounds that exist at the *spec*/*template* level, not at the wrapper
level. They are there because SARAH accepts structurally-valid Lagrangians
that it silently refuses to canonicalise. Summary index — follow the
SKILL.md section for the full reproduction and fix:

1. Vectorlike fermion doublets → declare as two left-Weyl, not one Dirac pair.
2. Majorana mass terms → `LagHC` with `AddHC -> True`, not `LagNoHC`.
3. Dirac charged sectors → distinct LH/RH mass-eigenstate names.
4. BSM matter fields → F-prefixed names (`FS`, `FPsi`), never `S` or `X`.
5. `DEFINITION[GaugeES][DiracSpinors]` → usually a symptom, not a fix.
6. Rank-1 Dirac sub-blocks → `Param.$Failed` leaks; spec-side guard required.

Two more traps live in the renderer/IR rather than SKILL.md. They're here
because they're easy to reintroduce while editing `sections/`:

7. **Phase targets use inner Weyl components, not outer field names.** A
   `Phases` block referencing the outer field `S` when the Weyl component
   is `s0` silently fails to bind — SARAH looks up phases by the Weyl
   spinor context. `build_phases` prefers the first explicit component
   over the outer name. **Where:** `scripts/model_ir.py:303-308`.
8. **PDG-code list size must equal mixing cardinality.** The `{pdg1, pdg2,
   …}` tuple attached to a mixed particle must contain exactly N entries,
   where N is the number of mass eigenstates the mixing produces. Off-by-one
   → `CheckModelFiles::MissingParticle` → UFO degrades to `name='None'`.
   **Where:** `scripts/sections/particles.py:224-229`.
