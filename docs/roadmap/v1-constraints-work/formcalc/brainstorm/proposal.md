# /formcalc — Proposal (Proposer)

**Scope.** Phase-B, stage 2 of the Mathematica symbolic pipeline. Consumes a
FeynAmpList from `/feynarts`, performs Dirac algebra / fermion-chain handling /
tensor reduction to Passarino–Veltman (PV) coefficients, and emits either a
symbolic expression (for `/formcalc`) or a standalone Fortran module linked
against LoopTools for numeric evaluation. Mathematica-driven; FormCalc
internally shells out to FORM (Vermaseren) for the heaviest algebra.

**Upstream context.** Wolfram Engine is already activated (`wolfram_engine_path`
in config). FeynArts will be installed by `/feynarts-install` as a Mathematica
app under `~/.WolframEngine/Applications/`. FormCalc ships a companion FORM
binary builder *and* the LoopTools Fortran library in one source tree, so the
install has three artefacts to land: a Mathematica app, a `form` binary, and a
LoopTools `libooptools.a`.

---

## 1. Install skill — `/formcalc-install`

**Source.** Upstream tarball `http://www.feynarts.de/formcalc/FormCalc-10.0.tar.gz`
(pin `10.0`, override via `HEPPH_FORMCALC_VERSION`). Checksum placeholder
`TODO` honoured by `verify_checksum` per `_common.sh` convention.

**Bundled vs separate.** FormCalc's tarball already vendors:

- `FormCalc/` — the Mathematica app.
- `LoopTools/` — Fortran + C sources; `./configure && make` produces
  `libooptools.a`, `libooptools-quad.a`, and the Mathematica interface
  `LoopTools/bin/MLooptools`.
- `FORM/` — a bootstrap that downloads and builds Vermaseren's `form` if not
  already on `$PATH`.

We install the whole tree under `~/.WolframEngine/Applications/FormCalc-<ver>/`
(so `<<FormCalc`` works from any notebook) and symlink the built `form` into
`$HOME/.local/bin/form`. LoopTools gets its own config key
(`looptools_path`) because `/formcalc` can link against it independently.

**Subcommands** (mirrors `/sarah-install`):

| Subcommand | Purpose | Exits |
|---|---|---|
| `detect` | Scan candidates, read config; emit `{"status":"configured\|found\|missing",…}` on stdout | 0 |
| `use-path <dir>` | Register existing FormCalc tree; run smoke test (`<<FormCalc`; `CalcFeynAmp` symbol resolved) | 0/15/16/20 |
| `install [dir]` | Full install: Wolfram probe → disk → download → checksum → extract → LoopTools `make` → FORM bootstrap → register `$Path` via `init.m` → smoke test | 0/11/12/13/14/15/20/23 |

**Prerequisites** checked before work (fatal blockers via
`_shared/blocker.schema.json`):

- `wolfram_engine_path` set → else `WOLFRAM_KERNEL_ABSENT` (exit 20).
- `gfortran` on PATH → else `GFORTRAN_ABSENT` (exit 10) — LoopTools build requires it.
- ≥ 2 GB free in `$HOME` via `check_disk 2 4`.
- Network reachable → `FORMCALC_DOWNLOAD_FAILED` (exit 12).

**New blocker codes.** `FORMCALC_DOWNLOAD_FAILED`, `FORMCALC_SMOKE_TEST_FAILED`,
`FORMCALC_PATH_INVALID`, `FORM_BUILD_FAILED`, `LOOPTOOLS_BUILD_FAILED`. All
fatal. Add to the known-codes enum in `blocker.schema.json`.

**Config keys written.**

| Key | Value |
|---|---|
| `formcalc_path` | `~/.WolframEngine/Applications/FormCalc-10.0` |
| `formcalc_version` | `10.0` |
| `formcalc_installed_at` | UTC ISO-8601 |
| `form_binary` | `~/.local/bin/form` |
| `form_version` | `form --version` first line |
| `looptools_path` | `${formcalc_path}/LoopTools` |
| `looptools_lib` | `${looptools_path}/lib64/libooptools.a` (or `lib/` on macOS) |

**Smoke test.** `WolframScript` one-liner:
`Needs["FormCalc\`"]; Print[CalcFeynAmp[] // Head];` — expects `CalcFeynAmp`
symbol to resolve (argument-empty call is fine; just checks load). Exit code
15 on empty stdout. Stores `formcalc_version` from `$FormCalcVersion`.

**Paclet vs legacy archive.** FormCalc is **not** on the Wolfram paclet server
as of 10.0; we ship only the tarball path. Leave room for a `install-paclet`
subcommand later if upstream publishes one — gate behind `--method=paclet`
flag, not a new subcommand.

---

## 2. Usage skill — `/formcalc`

**Inputs** (positional model-name + flags, scan-friendly like `/spheno-build`):

```
/formcalc <model_name> \
  --process <pid>                          # references FeynArts output dir
  --scheme {dimreg,dimred,cdr}             # default: dimreg (tt̄, EW loops)
  --fermion-chain {chiral,non-chiral,fierz} # default: chiral
  --output-mode {symbolic,fortran,both}    # default: symbolic
  --abbreviate {on,off}                    # default: on (FormCalc `Abbreviate`)
  --reduce {pv,loopnum,off}                # default: pv (Passarino–Veltman)
  --mandel-invariants "s,t,u"              # auxiliary kinematic spec
```

State layout under `$STATE_ROOT/models/<name>/formcalc/<process_id>/`:

- `input/` — symlinked `FeynAmpList.m` from `/feynarts` output.
- `kinematics.m` — Mathematica expressions for `Process`, `OnShell`, `Neglect`.
- `amp_raw.m` — `CreateFeynAmp` imported.
- `amp_reduced.m` — after `CalcFeynAmp` + `Abbreviate` (**canonical symbolic output**).
- `squaredME/` — `WriteSquaredME` Fortran tree (only when `--output-mode` ≠ `symbolic`).
- `run/<ts>/summary.json` — parsed abbreviations, number of PV funcs, timing.
- `make.log`, `form.log` — raw tool output.

**Operations pipeline** (implemented as `scripts/run_formcalc.py`):

1. `prepare_kinematics.py <proc>` — emits `kinematics.m` from a minimal JSON
   spec (incoming/outgoing PDG IDs, masses from `/spheno-build` summary.json).
2. `run_calcfeynamp.wls` — headless `wolframscript` that `Needs["FormCalc\`"]`,
   loads `FeynAmpList.m`, applies regularization scheme, calls `CalcFeynAmp`
   with chosen fermion-chain option, `Abbreviate`s, serialises
   `amp_reduced.m`.
3. `emit_fortran.wls` (optional) — `SetupCodeDir[…]`, `WriteSquaredME[…]`,
   `WriteRenConst[…]`, runs `make -C squaredME` linking against
   `$looptools_lib`.
4. `parse_summary.py` — counts `A0/B0/B1/C0/D0` appearances, writes
   `summary.json`.

**Error modes → blockers.**

| Condition | Code | Mode |
|---|---|---|
| `wolframscript` exit ≠ 0 | `FORMCALC_KERNEL_ERROR` | fatal |
| FORM subprocess exit ≠ 0 (parse `form.log`) | `FORM_EXECUTION_FAILED` | fatal |
| `amp_reduced.m` not produced | `FORMCALC_NO_OUTPUT` | fatal |
| Residual γ₅ ambiguity (BMHV warning) | `FORMCALC_G5_SCHEME_AMBIGUOUS` | **recoverable** (record, continue) |
| PV reduction produced IR-divergent `B0[0,0,0]` flagged | `FORMCALC_IR_DIVERGENT` | **recoverable** |
| Fortran `make` failure when `--output-mode=fortran` | `FORMCALC_FORTRAN_BUILD_FAILED` | fatal |
| FeynAmpList missing | `FORMCALC_INPUT_MISSING` | fatal |

Recoverable cases write a row to `run/<ts>/blockers.jsonl` and let the
orchestrator show a warning; fatal cases exit 15/23 and stop.

**Outputs downstream.**

- `amp_reduced.m` — the contract to `/formcalc`. Mathematica-friendly,
  contains PV function heads (`A0i`, `B0i`, `C0i`, `D0i`) FormCalc-style.
- Optional `squaredME/*.F` + compiled binary — can be called directly for
  numeric σ, ⟨|M|²⟩, differential distributions.

---

## 3. Integration

**Upstream contract (from `/feynarts`).** FeynAmpList object serialised to
`$STATE_ROOT/models/<name>/feynarts/<proc>/FeynAmpList.m` plus a
`process.json` metadata file (PDG IDs, loop order, topology count). `/formcalc`
only reads these two files; it never re-runs FeynArts.

**Downstream contract (to `/formcalc`).** Single file `amp_reduced.m` with
FormCalc-native PV heads. `/formcalc` should consume this as its canonical
input; conversion from FormCalc `B0i[bb0,…]` to LoopTools `PVB[0,0,…]` is a
trivial rule set owned by `/formcalc`.

**Parallel question — Fortran emission vs always route through /looptools.**
Recommendation: **both**, but default `symbolic`. Rationale: for analytic
limits (Arcadi–Profumo Eqs. 9/14/23 reproduce cleanly in LoopTools),
Mathematica-only is faster to iterate. For σ_SI scans where the user wants
numeric evaluation outside Mathematica (Python pipelines, MadGraph-alternative
at one loop), emit Fortran linked to LoopTools. Do **not** make the Fortran
path a replacement for MadGraph at tree level — it's opt-in, named
`--output-mode=fortran`, and advertised as "one-loop amplitude evaluator," not
a general generator.

**Orchestrator hook** (`/lagrangian-builder` Phase C): if user asks for
"one-loop σ_SI" or "loop-level amplitude," dispatch
`/feynarts` → `/formcalc --output-mode=symbolic` → `/formcalc`. If user asks
for "numeric one-loop cross section as a function of m_χ," switch to
`--output-mode=both`.

---

## 4. Plugin placement

**Decision: `plugins/feynman-diagrams/`.**

- `/feynarts`, `/formcalc`, `/formcalc` form one tight toolchain, all
  Mathematica-driven, all operate on diagram/amplitude objects. They belong
  together.
- `plugins/model-building/` already houses SARAH/SPheno (Lagrangian → spectrum);
  adding FormCalc there would blur the boundary.
- A new `plugins/constraints/` is premature — relic/DD/Higgs limits in v1 are
  the *constraint* skills (µmegas, DDCalc, HiggsTools). FormCalc/LoopTools
  *produce* the quantities those constraints bind against; they are upstream.
- Rename existing `amplitude-calc` in `feynman-diagrams/` to be a thin wrapper
  that dispatches to `/feynarts` + `/formcalc`, or deprecate it — open
  question for the critic.

Resulting `plugins/feynman-diagrams/.claude-plugin/plugin.json` skills list:
`draw-feynman`, `feynarts-install`, `feynarts`, `formcalc-install`, `formcalc`,
`looptools-install`, `looptools`.

---

## 5. Open questions for the critic

1. **Regularization default.** `dimreg` (conventional) vs `dimred` (SUSY-safe,
   needed for MSSM benchmarks) vs `cdr`. Paper 2506.19062 is 2HDM+a, not
   SUSY → `dimreg` default seems right, but MSSM users will hit it
   immediately. Should the default be model-sensitive (read from
   `spec.yaml` SUSY flag)?
2. **Fortran build vs Mathematica-only.** Is `--output-mode=fortran` worth
   supporting in v1, given the LoopTools build risk on macOS (known
   gfortran/LoopTools pain points)? Ship symbolic-only in v1 and defer
   Fortran to v1.1?
3. **LoopTools version pinning.** LoopTools ships inside FormCalc but has
   independent releases. Pin to whatever is bundled with FormCalc 10.0 (2.16),
   or fetch latest (2.17)? Bundled avoids drift; latest gets bug fixes.
4. **γ₅ scheme for chiral fermions.** Naive vs BMHV vs Larin. FormCalc
   supports all three; default to naive (fast, correct for anomaly-free
   chains) or BMHV (pedantically correct, slow)?
5. **Caching.** FormCalc runs can take minutes. Reuse the SPheno-style build
   key (sha256 of input `.m` + FormCalc version + scheme flags)? Cache
   `amp_reduced.m` or regenerate every invocation?
6. **Process-ID naming.** FeynArts processes are tuples like
   `{F[3,{3}], -F[3,{3}]} -> {V[1], V[1]}`. Do we expose that raw, or assign
   short IDs (`ttbar_to_gammagamma`) and store a lookup?
7. **Testing strategy.** FormCalc smoke test needs a real Wolfram kernel;
   network tests gate on `HEPPH_RUN_NETWORK_TESTS=1` per convention, but
   FormCalc is local — use a separate `HEPPH_RUN_WOLFRAM_TESTS=1` gate, or
   reuse?

---

## Summary artefact list (concrete)

- `plugins/hep-ph-toolkit/skills/formcalc-install/SKILL.md` + `scripts/install_formcalc.sh`, `probe_formcalc.wls`, `skill_env.yaml`.
- `plugins/hep-ph-toolkit/skills/formcalc/SKILL.md` + `scripts/run_formcalc.py`, `prepare_kinematics.py`, `run_calcfeynamp.wls`, `emit_fortran.wls`, `parse_summary.py`.
- Update `plugins/feynman-diagrams/.claude-plugin/plugin.json` skills list.
- Extend `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` known-codes enum with new FORMCALC/FORM/LOOPTOOLS codes (or move enum into a shared location since it's no longer model-building-only).
- Bump `.claude-plugin/marketplace.json` version entry.
