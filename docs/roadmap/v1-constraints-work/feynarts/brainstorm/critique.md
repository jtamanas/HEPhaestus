# `/feynarts` — Critique (Skeptical Critic)

Format: quote → counter → synthesizer-action.

---

## 1. Scope creep into `/sarah-build`

**Quote (§0, §3):**
> "the natural home is a small extension to `/sarah-build` (add `feynarts` to `outputs:`) rather than a separate converter … Add `feynarts` to the permitted `outputs:` list in `modelspec.schema.json`. In `run_sarah.py`, when `feynarts` is requested, append `MakeFeynArts[];` to the wolframscript program."

**Counter.** This is not "small." `/sarah-build` shipped W3 with a committed
"Non-goal (v1)" list explicitly naming `MakeFeynArts[]` (SKILL.md:252). The
matching non-goal is echoed at `lagrangian-builder/SKILL.md:277` and in the
spec at `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md:282`.
Reopening that non-goal requires:

- touching `modelspec.schema.json` (the W0 shared contract);
- touching `run_sarah.py` and `render_templates.py` and the cache-key composer
  (§2.9 of phase2-plan-final explicitly fixes the key to `sha256(spec) + "=" +
  sarah_version` — flipping `outputs` must invalidate, meaning the key shape
  itself has to change);
- re-running every W2/W3 golden (the cached-build test fixtures are byte-stable
  on the current key, and the committed `make.log` fixtures noted in commit
  `41f8b5d` are keyed to the current cache-key string);
- assert-outputs step 6 in `sarah-build/SKILL.md` currently only checks
  `UFO/<Name>/` — needs a parallel check for `FeynArts/<Name>.mod` plus
  `<Name>.gen`, and a new `SARAH_OUTPUT_MISSING` context variant.

That's not a "small extension"; it's a cross-cutting refactor the proposal
hides in one sentence. The W2/W3 authors (different workstream per the git
log: `cd45c2d`, `081b908`) should co-sign. No evidence in the proposal that
this has been coordinated.

**Synthesizer action.** Either (a) ship `/feynarts` with its own tiny emitter
skill — a thin wolframscript driver that `<<SARAH\`; Start[...]; MakeFeynArts[]`
runs against an already-built model and writes into
`$STATE_ROOT/models/<name>/feynarts/` without touching `/sarah-build`'s cache
or schema; or (b) promote the `/sarah-build` extension to a named subtask with
its own plan doc, explicitly list the golden-test regeneration, and put it on
the W2/W3 reviewer's queue before `/feynarts` starts. Option (a) keeps W3's
contracts frozen and is faster to land.

---

## 2. Install-location conflict with `/sarah-install`

**Quote (§1):**
> "mirror `/sarah-install` exactly — default install to `~/FeynArts/FeynArts-3.11/`"

**Counter.** `/sarah-install` installs to `~/SARAH/SARAH-<ver>/` and registers
`AppendTo[$Path, "<sarah_path>/.."]` so `<<SARAH\`` resolves from the parent.
The proposal copies this shape, which is fine in isolation, but:

- the FormCalc proposal installs FormCalc under
  `~/.WolframEngine/Applications/FormCalc-<ver>/` (the real Mathematica app
  dir, auto-discovered). So within the same Phase-B chain the proposer picks
  one convention, the FormCalc proposer picks the other, and a user who installs
  both will have half their Mathematica stack in `$HOME/FeynArts/` (not on the
  app path) and half in `$UserBaseDirectory/Applications/` (on the app path).
  That is genuinely confusing and will break `Needs["FeynArts\`"]` from any
  notebook the user opens by hand.
- The proposal's table Candidate 1 (`$UserBaseDirectory/Applications/FeynArts`)
  is rejected for "cross-project contamination," but that is *exactly* how
  FormCalc is being installed next door. Inconsistent.
- SARAH's own `MakeFeynArts[]` writes `<Name>.mod`/`<Name>.gen` into its own
  output dir and expects FeynArts's `Lorentz.gen` GenericModel to be reachable
  via `$Path`. Double-install risk is real if the user has a pre-existing
  Mathematica install of FeynArts in `Applications/` and we add a second one
  in `~/FeynArts/`: `Needs["FeynArts\`"]` will non-deterministically pick
  whichever is earlier on `$Path`, and model/generic versions can mismatch
  silently (Open Question 1 of the proposal gestures at this but does not
  resolve it).

**Synthesizer action.** Standardize Phase B on
`$UserBaseDirectory/Applications/` for *all* Mathematica packages (FeynArts,
FormCalc, LoopTools). Use the Mathematica convention, not the SARAH
convention, because FeynArts/FormCalc/LoopTools are Mathematica apps — SARAH
is idiosyncratic. `/feynarts-install detect` must refuse to register a second
path if FeynArts is already resolvable from `$UserBaseDirectory/Applications/`
and emit a new `FEYNARTS_AMBIGUOUS_INSTALL` fatal blocker listing both paths.

---

## 3. Plugin placement — three-way conflict, flag it

**Quote (§4):**
> "Recommendation: `plugins/model-building/`. … `plugins/feynman-diagrams/`
> is tempting but that plugin is positioned for user-facing diagram drawing
> (TikZ-Feynman per `CLAUDE.md`), not for the FeynArts/FormCalc/LoopTools
> amplitude pipeline."

**Counter.** This is a straight misread of `CLAUDE.md`:

> "QFT | `feynman-diagrams` | Diagram drawing & amplitude calculation"

"Amplitude calculation" is literally the category label. That is the table
row that owns FeynArts/FormCalc/LoopTools. The TikZ-Feynman preference is a
*rendering* convention ("When generating Feynman diagrams, prefer
TikZ-Feynman unless the user specifies otherwise"), not a scope fence.

More damning: **the three Phase-B proposals conflict with each other.**

| Skill | Proposed plugin |
|---|---|
| `/feynarts` | `plugins/model-building/` |
| `/formcalc` | `plugins/feynman-diagrams/` |
| `/formcalc` | new `plugins/loop-computation/` |

Shipping all three as proposed splits one pipeline across three plugins. A
user who runs Phase B end-to-end must install three plugins; the orchestrator
in `/lagrangian-builder` has to cross three manifests; the blocker-schema
enum (currently at `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`)
is referenced by all three and will need to move to a truly shared location
(FormCalc proposal already notes this in §Summary, but doesn't commit to it).

`/feynarts`'s rationale "data-locality with `/sarah-build`" is weak: the
`$STATE_ROOT/models/<name>/feynarts/` path is already a cross-plugin contract
via state root, identical to how `/spheno-build` consumes
`$STATE_ROOT/models/<name>/sarah_output/SPheno/`. State-root paths are the
data-locality mechanism; they do *not* force co-location of plugin source.

**Synthesizer action.** Require a single placement decision for all three
Phase-B skills before any of them ships. Options:

1. **`plugins/feynman-diagrams/`** for all three — matches `CLAUDE.md` row,
   FormCalc proposer already agrees, only the `/feynarts` and `/formcalc`
   proposers need to bend. Also rename or retire the placeholder
   `amplitude-calc` skill that FormCalc mentions.
2. **`plugins/loop-computation/`** new plugin for all three — LoopTools
   proposer's choice. Costs: a new plugin entry in `marketplace.json`, new
   README, new `.claude-plugin/plugin.json`. Benefit: clean category.

Option 1 is lower cost and respects the existing marketplace table. Take
option 1. The critic recommends this become a gate on Phase-B kickoff.

---

## 4. Ownership seam — no SARAH-less path

**Quote (§3):**
> "FeynArts model **generation** (`.mod`/`.gen`) is owned by `/sarah-build`
> (SARAH is the model authority). FeynArts model **consumption** … is owned by
> `/feynarts`. Clean seam."

**Counter.** Clean only if every user needs SARAH. Counterexamples:

- FeynArts ships **built-in models** (`SMQCD.mod`, `SM.mod`, `MSSM.mod`,
  `THDM.mod`). A user reproducing a textbook SM calculation does not want or
  need SARAH in the loop. The decision flow in §2 step 1 hard-fails with
  `FEYNARTS_MODEL_MISSING` unless `$STATE_ROOT/models/<name>/feynarts/<Name>.mod`
  exists — shipped FeynArts models are invisible to this skill.
- Research workflows frequently modify a `.mod` by hand (dropping a diagram
  class, adding a counterterm). Round-tripping through `/sarah-build` is wrong.
- The paper benchmark (2506.19062, 2HDM+a) has a `.mod` in the FeynArts THDM
  examples already; recomputing it through SARAH just to feed FeynArts is
  wasted work.

**Synthesizer action.** `/feynarts` must accept `--model-file <path>` as an
alternative to `--model <name>`. When given, skip the SARAH-output lookup,
copy the file into the run dir, and proceed. Add `FEYNARTS_MODEL_FILE_INVALID`
fatal blocker for the bad-path case. Update the decision flow in §2 step 1
to treat SARAH-provenance as one of two sources, not the only one.

---

## 5. Process-spec ergonomics — opaque

**Quote (§2 Inputs):**
> "`--process '{F[1],-F[1]} -> {V[1],V[1]}'` … `--process` — FeynArts process
> spec string, passed through verbatim."

**Counter.** Verbatim FeynArts notation is hostile. `F[1]` is "lepton, first
generation" only in FeynArts's *SM* model; in a SARAH-emitted `.mod` the
indexing is *model-specific*. A user reading `{F[1], -F[1]} -> {V[1], V[1]}`
from memory will write the wrong process for any BSM model.

SARAH already writes a `particles.m` that lists `{pdg_code, FeynArts_index,
latex_name}` per state; `/sarah-build` emits it into
`$STATE_ROOT/models/<name>/sarah/particles.m`. We can translate
`e+ e- -> Z Z` via PDG codes in one pass, with a clean fallback: accept
FeynArts notation verbatim *or* a PDG/name string, auto-detect by checking
for `[` and `]`.

Open Question 2 of the proposal flags this and leans vague. This is the
"augment not replace" principle in action — we're not reimplementing physics,
we're shimming an ergonomic layer on top of FeynArts. Low risk, high UX win.

**Synthesizer action.** v1 must accept both:
`--process 'e+ e- -> Z Z'` (resolved via `particles.m` lookup) and
`--process '{F[1],-F[1]} -> {V[1],V[1]}'` (passed verbatim). Emit the resolved
form into `driver.m` as a comment so users learn the FeynArts indexing.
Reject names absent from `particles.m` with `FEYNARTS_PROCESS_UNKNOWN_PARTICLE`.

---

## 6. Amplitude-size caps — unhandled failure mode

**Quote (Open Q 3):**
> "One-loop amplitude generation for a moderately large BSM model (e.g.
> 2HDM+a with 40 states) can produce thousands of diagrams and amplitude `.m`
> files of 50–500 MB."

**Counter.** The proposal acknowledges this then punts. The real failure modes
are (a) wolframscript OOM on `CreateFeynAmp[ins]` (silent `$Aborted`,
hard to parse), (b) `Put` writing a multi-hundred-MB `.m` file that FormCalc
will then try to `Get[]` and itself OOM, and (c) `Paint[]` producing a PDF
where `ColumnsXRows -> {4,4}` crams 1000 diagrams into a grid that is visually
useless.

**Synthesizer action.** Add hard caps with blockers:

- Count `Length[ins]` *before* `CreateFeynAmp`. If `> N_MAX_DIAGRAMS` (default
  500, override via `HEPPH_FEYNARTS_DIAGRAM_CAP`), emit
  `FEYNARTS_TOO_MANY_DIAGRAMS` fatal with the count and a suggested
  `--exclude-topologies` or loop-order reduction. Check the cap *before* the
  expensive step.
- After `Put`, stat `amplitude.m`. If `> 200 MB` (override
  `HEPPH_FEYNARTS_AMP_SIZE_CAP_MB`), emit `FEYNARTS_AMP_TOO_LARGE` fatal and
  refuse to write the cache key. FormCalc proposer should mirror the cap on
  ingest.
- `Paint[]` layout should be computed: `ColumnsXRows -> {Ceiling[Sqrt[n]],
  Ceiling[n/Ceiling[Sqrt[n]]]}` and split into pages of ≤ 16 per page. One
  PDF per topology class is overkill for v1.

---

## 7. Downstream contract stability

**Quote (§3):**
> "`amplitude.m = Put[amp, ...]` … So our emitted artifact is exactly what
> FormCalc expects — no format conversion."

**Counter.** This conflates two things. `Put` serializes arbitrary Mathematica
expressions via `InputForm`. The head after `CreateFeynAmp[ins]` is
`FeynAmpList[...]`. FormCalc's `CalcFeynAmp` consumes `FeynAmpList`, yes —
but the *internal layout* of `FeynAmpList` (order of rules in options, how
propagator factors are grouped) is not a FormCalc public API and has shifted
between FeynArts 3.10 → 3.11. If we pin FeynArts 3.11 and FormCalc 10.0 the
current shape matches, but any `HEPPH_FEYNARTS_VERSION` override opens a
compatibility gap.

Second: the FormCalc proposer writes amplitude output as
`<proc>/FeynAmpList.m`, the FeynArts proposer writes `amplitude.m`. The
filenames differ. One of the two must change before Phase-B integration.

**Synthesizer action.**

- Emit both a version stamp and the expression:
  `Put[{"feynarts_version" -> "3.11", "amp" -> amp}, "amplitude.m"]` and have
  FormCalc's `Get` check the version tag and refuse on mismatch
  (`FORMCALC_FEYNARTS_VERSION_SKEW` fatal). Record the pinned pair in
  `SHARED.md` as a compatibility matrix.
- Align the filename: `FeynAmpList.m` is more descriptive; rename
  `/feynarts` output to match `/formcalc` proposal's expectation.

---

## 8. Paint output format vs TikZ-Feynman handoff

**Quote (§2 step 4):**
> "`Paint[ins, ColumnsXRows -> {4,4}, DisplayFunction -> (Export["diagrams.pdf", #]&)];`"

**Counter.** `CLAUDE.md` line 20: "When generating Feynman diagrams, prefer
TikZ-Feynman unless the user specifies otherwise." `Paint[]`'s PDF output is
not TikZ-Feynman; it's PostScript rendered through Mathematica's graphics
engine, publication-ugly by modern HEP-paper standards. A user who wants a
paper figure will regenerate by hand in TikZ — the skill's PDF is throwaway.

FeynArts has an undocumented but stable `FeynArts\`Graphics\`TopologyToTeX`
helper (community-known) that emits `feynmp` (not TikZ-Feynman but closer);
there is also `FeynArtsTeX` contrib. Neither is a FeynArts public API. The
pragmatic answer is a two-track output: cheap PDF for in-skill preview,
structured JSON listing per-topology edge/node data so a separate
`/draw-feynman` TikZ-Feynman skill (already hinted at in `feynman-diagrams/`)
can render publication-grade.

**Synthesizer action.** Emit three files:
`diagrams.pdf` (Paint preview, auto-layout per §6),
`topologies.json` (structured topology list suitable for TikZ-Feynman
hand-off), and `amplitude.m` (the FormCalc handoff). Topology-JSON schema
stays informal in v1 (`{n_external, edges: [{from,to,kind,particle}], ...}`)
but gets a schema in v1.1 when `/draw-feynman` lands.

---

## Missed opens (critic-added)

9. **Cache key does not include FeynArts version.** §2 step 2 proposes
   `sha256(.mod) + "=" + feynarts_version + "|" + sha256(process + loop)`.
   But SARAH version is not in the key — if `/sarah-build` re-emits a
   different `.mod` (same model, new SARAH patch), the `.mod` bytes change so
   the key changes. OK. But the *generic* model (`Lorentz.gen`) lives inside
   FeynArts itself and is not in the key. Upgrading FeynArts silently
   invalidates every cache without any key change. Fix: include
   `sha256(<feynarts_path>/Models/Lorentz.gen)` in the key composition.

10. **No CPU/time budget.** `/spheno-build` uses `-j<cpu_count>`; wolframscript
    runs single-threaded. One-loop `CreateFeynAmp` for a 500-diagram process
    can run 10–30 minutes. No wall-clock cap is specified; CI will time out.
    Require `--timeout <seconds>` flag (default 900s) and emit
    `FEYNARTS_TIMEOUT` fatal on expiry.

11. **Reference-only branch.** Open Q 4 leans "hard-block." Agreed per
    `MEMORY.md#augment_not_replace` — FeynArts is the whole point; a sympy
    fallback here defeats the skill. Close the open question: no
    `reference_only` fallback. Document explicitly in SKILL.md.

12. **`/lagrangian-builder` dispatch trigger.** §3 "Phase-B orchestration"
    says dispatch on "one-loop amplitude or similar." The current
    `/lagrangian-builder` (commit `cd45c2d`) uses a keyword-match dispatcher
    per W5. Add the explicit keyword list to the proposal before
    implementation; "or similar" will silently fail to route.

13. **macOS wolframscript activation edge case.** `/sarah-install` surfaces
    `activation_required` as a status, not a blocker (SKILL.md §Activation
    handling). `/feynarts-install` proposal does not mention this path. A
    user who installs FeynArts on a fresh machine with an unactivated Wolfram
    Engine will hit `FEYNARTS_SMOKE_TEST_FAILED` (fatal) instead of
    `activation_required` (benign). Must surface activation status identically
    to `/sarah-install`.

---

## Summary of blocking issues

1. Plugin placement three-way conflict — **gate** before any Phase-B code.
2. `/sarah-build` output-list extension — either drop it (own emitter in
   `/feynarts`) or formalize as cross-workstream refactor with W2/W3 sign-off.
3. No SARAH-less entry path — add `--model-file`.
4. Missing diagram/amplitude caps — add hard caps and dedicated blockers.
5. Version stamp on `amplitude.m` handoff to `/formcalc` — aligned filename +
   version-skew blocker.

Non-blocking but recommended: friendlier process spec, cache-key includes
`Lorentz.gen` hash, explicit timeout, activation-status parity, reject
`reference_only` explicitly.
