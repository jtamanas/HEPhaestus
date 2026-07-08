---
name: sarah-build
description: Given a validated ModelSpec YAML, render SARAH .m files from templates and invoke SARAH headlessly to produce UFO and/or SPheno source output.
---

# `/sarah-build`

Transforms a `ModelSpec` YAML into SARAH `.m` files, runs SARAH headlessly via
`wolframscript`, and collects UFO/SPheno output under
`$STATE_ROOT/models/<name>/`. Caches by input SHA-256 so repeated invocations
on the same spec are no-ops.

## When to invoke

- When `/lagrangian-builder` has a validated `ModelSpec` and needs SARAH output.
- Directly by the user: `python3 build.py path/to/spec.yaml [--force]`.

## Preflight: SARAH

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/sarah/detect.sh

- **exit 0** → SARAH and Wolfram Engine are both ready (composite check
  covering config, Wolfram reachability, activation status, and SARAH
  on-disk presence); proceed.
- **exit non-zero** → SARAH or Wolfram is missing/misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/sarah/INSTALL.md` into context and
  follow it. When the install completes (or the install script returns
  `activation_required`), re-run `detect.sh` before proceeding. If it still
  fails, halt with the blocker code from the install reference.

## Supported models

The generator supports spec shapes whose physics falls inside the following
envelopes. Specs outside them are rejected at validation or produce
render-only (not physics-correct) output.

**Gauge groups:** U(1) (hypercharge or extra Abelian), SU(2) (electroweak
left), SU(3) (QCD color or an extra strongly-coupled sector, e.g. dark SU(3)).
Multiple copies of the same group are supported (SM + dark SU(3) as in
`dark_su3`). Non-Abelian groups beyond SU(3) (SU(5), SO(10), E6, …) are out of
scope for v1.

**Fermion kinds** (`chirality`): `left` / `right` Weyl; `majorana`
(self-conjugate Weyl); `dirac` (shorthand for a left+right pair with a common
mass and quantum numbers, auto-expands to a Dirac fermion).

**Scalar kinds:** additional Higgs doublets (`reps: {WB: 2}`,
`hypercharge: 0.5`) — any number beyond the SM Higgs; singlets
(`reps: {WB: 1, G: 1}`, arbitrary or zero hypercharge) — real or complex
(e.g. a CP-odd mediator `a0`).

**EWSB mixing kinds** (`ewsb.mixings`), discriminated by `kind`:

- `kind: fermion` — requires `chirality`:
  - `chirality: majorana` — mixes left-Weyl and conjugate-right-Weyl fields into
    Majorana mass eigenstates. Requires `weyls`.
  - `chirality: dirac` — mixes distinct left- and right-handed Weyl fields into
    Dirac mass eigenstates. Requires `lh_weyls` and `rh_weyls`.
- `kind: scalar` — mixes scalar/pseudoscalar fields after EWSB. Requires
  `weyls` and `mixing_matrix`.

## Inputs

A `ModelSpec` v3 YAML conforming to
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json`. Minimal
required keys: `model.name`, `gauge_groups`, `fermions`, `scalars`,
`parameters`, `lagrangian`. See the SM template at
`_shared/modelspec_v3/templates/sm.yaml` and the four reference specs at
`_shared/modelspec_v3/specs/{singlet_doublet,dark_su3,2hdm_a,ssm}.yaml` for
worked examples covering DM extensions, confining gauge sectors, and extended
Higgs doublets. For a new model, copy the SM template, insert BSM fields, then
run `validate_spec.py` and `build.py --out <dir>` to render the `.m` files.

## Decision flow

```
build.py <spec.yaml> [--force]
    │
    ├─ 1. Validate spec
    │       validate_spec.py → MODELSPEC_INVALID (fatal) on failure
    │
    ├─ 2. Check cache
    │       key = sha256(spec.yaml bytes hex) + "=" + sarah_version
    │       stored at $STATE_ROOT/models/<name>/.sarah_build_key
    │       If key matches AND sarah_output/UFO/<Name>/ exists AND not --force
    │           → exit 0  {"status": "cached"}
    │
    ├─ 3. Render .m templates
    │       render_templates.py → <Name>.m, parameters.m, particles.m, SPheno.m
    │       written to $STATE_ROOT/models/<name>/sarah/
    │
    ├─ 4. Stage into Private-Models/
    │       stage.py:stage()
    │       Wipes $sarah_path/Private-Models/<Name>/ (stale .m + .mx caches)
    │       Writes rendered files + .sarah_build_key stamp
    │
    ├─ 5. Invoke SARAH via wolframscript (cwd = sarah_path)
    │       run_sarah.py
    │       AppendTo[$Path, "<sarah_path>/.."];   ← the /.. is required; see below
    │       <<SARAH`;
    │       Start["<Name>"];
    │       CheckModel[];
    │       MakeUFO[];        (if "ufo" in spec.outputs)
    │       MakeSPheno[];     (if "spheno" in spec.outputs)
    │       stdout+stderr → $STATE_ROOT/models/<name>/sarah_output/sarah.log
    │
    ├─ 6. Read sarah.log
    │       Agent checks for fatal / hint patterns (see §"Reading sarah.log")
    │
    ├─ 7. Collect outputs
    │       collect.py:collect()
    │       Globs $sarah_path/Output/<Name>/*/UFO/ (prefers EWSB/)
    │       Copies UFO/<Name>/ → sarah_output/UFO/<Name>/
    │       Copies SPheno/    → sarah_output/SPheno/<Name>/
    │       Creates ufo symlink → sarah_output/UFO/<Name>/
    │       SARAH_OUTPUT_MISSING (fatal) if UFO dir absent
    │
    ├─ 8. Write cache key   (.sarah_build_key = sha256hex=sarah_version)
    │
    └─ 9. Update config     (config.models[<name>].spec, .ufo, .sarah_built_at)
```

**The `/..` in `$Path` is required.** `sarah_path` points to the package
directory containing `SARAH.m` (e.g. `$HOME/SARAH`); the `<<SARAH\`` loader
resolves the `SARAH\`` context from a sibling directory, so the **parent** of
`sarah_path` must be on `$Path`. Do NOT drop the `/..`. Full symptom/cause in
[`references/sarah-workarounds.md`](references/sarah-workarounds.md) §4.

## Cache semantics

Cache key (§2.9 of `phase2-plan-final.md`):
`sha256(<spec.yaml bytes>, hex) + "=" + <sarah_version from config>`, stored at
`$STATE_ROOT/models/<name>/.sarah_build_key` (single line, no newline).

- **Hit:** key matches AND `sarah_output/UFO/<Name>/` exists → skip template
  rendering and `wolframscript`; return `{"status": "cached"}`.
- **Miss:** any mismatch, missing key file, or missing output directory → full
  rebuild.
- **`--force`:** always rebuilds.

The cache is input-only: the output tree is never hashed (output-tree hashing
is explicitly rejected per §2.9). The key is stamped **after** the output scan
passes, not inside `collect()` — a corrupt tree must never stamp its own cache
([`sarah-workarounds.md`](references/sarah-workarounds.md) §7).

## Private-Models staging (RC1 fix)

SARAH loads models from its built-in `Models/` directory and a user-writable
`Private-Models/` directory. This skill always uses `Private-Models/` so the
SARAH installation is never modified. Before each `wolframscript` run,
`stage.py:stage()`:

1. `mkdir -p $sarah_path/Private-Models/` — SARAH does not create it on first use.
2. If `$sarah_path/Private-Models/<Name>/` exists, `shutil.rmtree` it — wiping
   both stale `.m` source and any Mathematica `.mx` compiled cache SARAH left
   from a previous run.
3. Write fresh rendered files from the in-memory `{filename: text}` dict.
4. Stamp `.sarah_build_key` so a later `stage()` can detect a current tree.

Cleanup of `Private-Models/<Name>/` on exit belongs to `validate_goldens.py`;
`run_sarah.py` leaves the staged tree in place for post-mortems. Concurrent
same-model builds are serialised by an `fcntl.flock`
([`sarah-workarounds.md`](references/sarah-workarounds.md) §2).

## Golden-file validation

`scripts/validate_goldens.py` is the golden-file oracle for physics
correctness. Invoked manually (not by CI) because it needs a live
`wolframscript` kernel.

```bash
python3 scripts/validate_goldens.py \
    --model singlet_doublet \
    --goldens-dir tests/goldens/singlet_doublet/ \
    --outputs ufo,spheno \
    [--sarah-path <path>] \
    [--wolframscript <path>]
```

It reads golden `.m` files from `tests/goldens/<model>/`, stages them via
`stage.stage()`, runs `wolframscript` with `Start["<Name>"]` + `CheckModel[]` +
the requested make commands, scans stdout+stderr for forbidden SARAH error
patterns (`ModelFile::MissingModel`, `ModelFile::Aborted`, `CheckModel::*Abort*`,
`MatterSector::parseError`), checks the UFO/SPheno trees were produced on disk,
and cleans up `Private-Models/<Name>/` on exit (unless `--keep-staged`).

Exit 0 = PASS (`{"status": "valid"}`); 1 = FAIL
(`{"status": "invalid", "code": ..., "context": {...}}`); 2 = environment /
usage error.

## Failure modes → blockers

All blockers are emitted as single-line JSON on **stderr**, conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. This table is the
single source for blocker codes; the log-reading step below points here.

| Code | Mode | Trigger | Action |
|------|------|---------|--------|
| `MODELSPEC_INVALID` | fatal | Schema validation fails or semantic check fails (duplicate names, bad reps, bad hypercharge, empty outputs) | Fix the spec; re-run |
| `MODELSPEC_INVALID` | fatal | SARAH log contains `Error: field <X> undefined` | Field `<X>` was referenced but not declared; fix the field name |
| `WOLFRAM_KERNEL_ABSENT` | fatal | `wolfram_engine_path` not set in config | See `_shared/installs/sarah/INSTALL.md` |
| `SARAH_ABSENT` | fatal | `sarah_path` not set in config | See `_shared/installs/sarah/INSTALL.md` |
| `ANOMALY_CANCELLATION_FAILED` | fatal | SARAH log contains `Anomalies are not cancelled` | Inspect coefficients in `context`; modify the model |
| `SARAH_OUTPUT_MISSING` | fatal | `sarah_output/UFO/<Name>/` absent after successful SARAH exit | Check `sarah.log`; may indicate SARAH version mismatch |

### `ANOMALY_CANCELLATION_FAILED` context shape

```json
{
  "code": "ANOMALY_CANCELLATION_FAILED",
  "mode": "fatal",
  "message": "SARAH anomaly check failed for model DarkSU3",
  "context": {
    "coefficients": [
      "SU(3)^3 coefficient = 3",
      "U(1) mixed coefficient = 1/6"
    ]
  }
}
```

The `coefficients` list is extracted from the 10 lines following `Anomalies are
not cancelled` in `sarah.log` — the lines matching `coefficient.*=`
(case-insensitive).

## Reading sarah.log (agent-driven)

SARAH prints most errors via `Message[…]` and keeps going, so `wolframscript`
can exit 0 while writing nonsense output (`Param.$Failed`, `None` particle
names). After the run, `run_sarah.py` writes the full stdout+stderr to
`$STATE_ROOT/models/<name>/sarah_output/sarah.log`; open it and check:

- **Fatal patterns** → abort with the matching blocker above:
  `Anomalies are not cancelled` (→ `ANOMALY_CANCELLATION_FAILED`),
  `Error:\s+field\s+(\w+)\s+undefined` (→ `MODELSPEC_INVALID`).
- **Non-fatal:** collect every `Warning:` line and surface it in the run
  summary; do not abort.
- **Hint patterns** — soft signals of silently-degraded output (see
  authoring-gotchas §6):

  | Pattern name | Pattern |
  |---|---|
  | `PART_PARTD_NONE` | `Part::partd:.*None\[\[` |
  | `STRINGJOIN_W_NONE` | `StringJoin::string:.*W<>None` |
  | `TOEXPRESSION_NOTSTRBOX` | `ToExpression::notstrbox:.*W<>None` |
  | `PART_PARTW` | `Part::partw` |

If any hint pattern matches, the mass matrix or parameter rendering degraded
silently: check `sarah_output/UFO/<Name>/parameters.py` for `Param.$Failed`
and `.../particles.py` for particle `name = "None"`. Both indicate a broken
emission — follow the response procedure in
[`references/authoring-gotchas.md`](references/authoring-gotchas.md) §6.

A separate, non-deterministic leakage of SARAH group-theory internals
(`SAxDynkin`, `SAxDynL`, `$Failed`) into emitted Fortran is scanned for by
`scripts/scan_outputs.py` (→ `SARAH_OUTPUT_CORRUPT`, fatal, cache not stamped);
open investigation notes and the recommended `--force` remedy are in
[`references/saxdynkin-investigation.md`](references/saxdynkin-investigation.md).

## Post-build artifacts

After a successful build the state directory contains (`singlet_doublet`, UFO +
SPheno):

```
$STATE_ROOT/models/singlet_doublet/
├── spec.yaml                                   # copy of the input spec
├── .sarah_build_key                            # cache key (sha256hex=version)
├── sarah/                                      # local reference copy of rendered .m files
│   ├── SingletDoublet.m
│   ├── parameters.m
│   ├── particles.m
│   └── SPheno.m
├── sarah_output/
│   ├── sarah.log                               # wolframscript stdout+stderr
│   ├── UFO/SingletDoublet/                     # UFO model directory (Python files)
│   └── SPheno/SingletDoublet/                  # SPheno Fortran source tree
└── SingletDoublet -> sarah_output/UFO/SingletDoublet/   # relative symlink
```

A UFO-only model (`dark_su3`) has the same shape without `sarah_output/SPheno/`;
its `sarah/SPheno.m` is a render-only stub (no live EWSB content).

The `sarah/` subtree is a **local reference copy** written by `run_sarah.py`;
the authoritative copy SARAH reads is at `$sarah_path/Private-Models/<Name>/`.

**The symlink basename must match the target directory basename.** MG5's
`import model <path>` re-resolves the model path against the symlink's parent
using the symlink basename rather than following the link — a mismatched
basename (prior versions used `ufo`) produces a non-existent path and fails the
import. `collect.py` also removes any legacy `state_dir/ufo` symlink on each
invocation.

Config is updated: `config.models["<name>"].spec` (abs path to `spec.yaml`),
`.ufo` (abs path to the `state_dir/<sarah_name>` symlink — pass this directly to
MG5's `import model`), `.sarah_built_at` (UTC ISO 8601). The SPheno Fortran
sources at `sarah_output/SPheno/<Name>/` are consumed by `/spheno-build` (W4).

## Per-model status

| Model | Test bar | Notes |
|-------|----------|-------|
| `singlet_doublet` | **End-to-end** (physics-correct) | Majorana + Dirac fermion mixing; UFO + SPheno. `validate_goldens.py --outputs ufo,spheno` required before goldens commit. |
| `dark_su3` | **Render-only** | SU(3)_D confinement is outside SARAH's EWSB grammar. `spec.outputs: [ufo]`; no `MakeSPheno[]`. Acceptance bar: `Start["DarkSU3"] + CheckModel[]` pass without abort. |
| `2hdm_a` | **Render-only** | Two Higgs doublets + CP-odd singlet; `sm_overrides.higgs_sector: true`. Acceptance bar: render without fatal error. Full E2E (physics-correct EWSB) is a post-v1 goal. |

"Physics-correct" means the generated files pass `Start[] + CheckModel[] +
MakeUFO[] + MakeSPheno[]` with no forbidden error patterns. "Render-only" means
the files render and `Start[] + CheckModel[]` pass, but the make commands are
out of scope for the current test bar.

## Non-goals (v1)

- **SUSY / superpotential** — no `superpotential:` block; no SUSY mass terms,
  soft-breaking sector, or gaugino content.
- **CP-violating phases beyond auto-derived Majorana phases** — arbitrary
  complex phases in mixing matrices are not supported. `ewsb.phases` pre-wires
  the escape hatch but the generator does not yet act on it.
- **Non-SM gauge groups beyond the 3 target patterns** — SU(5), SO(10), E6, or
  any single simple factor of rank > 3.
- **`MakeCalcHEP[]`, `MakeWHIZARD[]`, `MakeFeynArts[]`** — `spec.outputs`
  accepts only `"ufo"` and `"spheno"`; other targets are rejected at schema
  validation.

## Escape hatches

Spec-level knobs that unlock non-default behaviour when the default generator
logic does not match the model's physics.

**`sm_overrides.higgs_sector: true`** — set when the BSM sector completely
redefines the Higgs sector (2HDM, Georgi-Machacek triplets). Then the generator
does not auto-inject SM Higgs Yukawa terms, `lagrangian.yukawa_terms` is treated
as the complete Yukawa sector, and EWSB is driven solely by `ewsb.vevs`.
`singlet_doublet` leaves it `false`; `2hdm_a` sets it `true`.

**`spec.outputs` without `"spheno"` (UFO-only)** — omit `"spheno"` when the
model's vacuum structure is outside SARAH's EWSB grammar (a confining dark
sector with no EWSB mass spectrum). `run_sarah.py` will not dispatch
`MakeSPheno[]`; the generated `SPheno.m` is a minimal stub so the file exists
for the render bar. `dark_su3` uses this.

**Free-form `ewsb.mixings`** — the list accepts any combination of
`kind: fermion` (`chirality: majorana` or `dirac`) and `kind: scalar` entries in
one spec. Fields in `weyls` / `lh_weyls` / `rh_weyls` may use `conj[<field>]`
notation for conjugate Weyl components. `singlet_doublet` uses a
`majorana` entry (3-component neutral sector) plus a `dirac` entry (charged
fermion); `2hdm_a` uses three `scalar` entries (CP-even, CP-odd, charged Higgs).

## Gotchas (SARAH-idiom discrepancies)

Six spec/template-level patterns that make SARAH silently drop vertices or
collapse mass matrices to `OnlyZero` even though `CheckModel[]` passes. Full
reproduction, reference-model citations, and fixes are in
[`references/authoring-gotchas.md`](references/authoring-gotchas.md). Index:

1. Vectorlike fermion doublet → declare as two left-Weyl doublets, not one Dirac pair.
2. Majorana mass terms → `LagHC` with `AddHC -> True`, not `LagNoHC`.
3. Dirac charged sectors → distinct LH/RH mass-eigenstate names.
4. BSM matter fields → F-prefixed names (`FS`, `FPsi`), never `S` or single letters.
5. `DEFINITION[GaugeES][DiracSpinors]` → usually a symptom of #1, not a fix.
6. Rank-1 Dirac sub-blocks → `Param.$Failed` / `None`-name leaks; spec-side `les_houches:` and PDG-length guards required.

Two further renderer/IR traps, easy to reintroduce while editing `sections/`,
are catalogued in [`references/sarah-workarounds.md`](references/sarah-workarounds.md)
§"Model-authoring traps" (#7 phase targets use inner Weyl components; #8
PDG-code list size must equal mixing cardinality).

## Reference files

- [`references/sarah-workarounds.md`](references/sarah-workarounds.md) — 17
  infrastructure-level workarounds this wrapper applies (fresh kernel per run,
  flock serialisation, `.mx` cache wiping, model-name canonicalisation, the
  rank-1 Dirac compile-time patch, LOW-scale `*IN` block seeding, …), each with
  symptom / cause / mitigation / file:line.
- [`references/authoring-gotchas.md`](references/authoring-gotchas.md) — the six
  model-authoring gotchas above, in full.
- [`references/saxdynkin-investigation.md`](references/saxdynkin-investigation.md)
  — open-bug notes on non-deterministic `SAxDynkin`/`$Failed` leakage into
  emitted Fortran.
- [`references/MIGRATION-sigma-si-sign-fix.md`](references/MIGRATION-sigma-si-sign-fix.md)
  — up-Yukawa sign fix: users with a pre-fix `singlet_doublet`/`dark_su3` export
  must rebuild with `--force` (fixed a ~200× σ_SI suppression / fake isospin
  violation).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_spec.py` | CLI: validate a ModelSpec YAML; exit 0 / 1 |
| `scripts/render_templates.py` | Pure Python: spec dict → `{filename: text}` |
| `scripts/stage.py` | Stage rendered files into `$sarah_path/Private-Models/<Name>/` |
| `scripts/collect.py` | Copy SARAH Output tree into state dir; create `ufo` symlink |
| `scripts/run_sarah.py` | Render + stage + invoke wolframscript + collect + cache write |
| `scripts/validate_goldens.py` | Golden-file oracle: stage + wolframscript + error grep |
| `scripts/build.py` | Top-level CLI driver |

Templates live in `templates/` as plain text with `{placeholder}` tokens
(§2.10: `str.format` only, no Jinja2).
