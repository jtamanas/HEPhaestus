---
name: drake
description: Drive DRAKE for relic-density calculations in regimes where the ⟨σv⟩ Taylor expansion fails — narrow s-channel resonances, early kinetic decoupling, forbidden channels, Sommerfeld enhancement.
---

# DRAKE

Drive the DRAKE Wolfram Language package for dark matter relic density in regimes where
the standard `<σv>` Taylor expansion is inaccurate: narrow s-channel resonances within
~10% of 2·m_χ, early kinetic decoupling, forbidden/threshold freeze-out, and
Sommerfeld-enhanced annihilation.

DRAKE does **not** replace `/maddm` or `/micromegas`. It complements them. The intended
workflow is to run the standard tools first, identify a breakdown regime, then invoke
`/drake` to get a reliable result and compare.

---

## When to invoke `/drake` vs other tools

| Regime | Use |
|--------|-----|
| Generic freeze-out, co-annihilation, large parameter scan | `/maddm` (primary) |
| Co-annihilation with large coannihilator library, validation | `/micromegas` |
| Narrow s-channel resonance ( \|m_med − 2 m_χ\| / m_med < 0.1 ) | **`/drake`** |
| Early kinetic decoupling (DM decouples from heat bath before freeze-out) | **`/drake`** |
| Forbidden / threshold channel (m_X > m_χ but T_f correction matters) | **`/drake`** |
| Sommerfeld enhancement | **`/drake`** |
| MadDM Ω h² disagrees with micrOMEGAs near a resonance (cross-tool discrepancy ≥ 20%) | **`/drake`** |

If DRAKE is not installed, this skill blocks with a clear message — it does **not** fall
back to an analytic approximation. Install DRAKE first with `/drake-install`.

---

## Decision tree

**What do you need?**

### Detect DRAKE install or troubleshoot a failed run?

Read: `references/setup.md`

Covers: install detection via `install.sh detect`, re-running the WIMP smoke test,
Wolfram Engine prerequisites, the hepforge Anubis download gate, pointing DRAKE at a
user-provided install path.

### Configure and run DRAKE for a specific model and regime?

Read: `references/running.md`

Covers: built-in pre-implemented models (`WIMP`, `VRES`, `SE`, `TH`, `ScalarSingletDM`),
the wolframscript invocation pattern, benchmark file structure (`bm_*`), settings file
structure (`settings_*`), and how to work from the shipped benchmark files.

### Interpret results and compare against MadDM / micrOMEGAs?

Read: `references/comparison.md`

### Diagnose a run that exits 0 but produces no Ωh² value, or a runtime of 0?

Read: `references/sharp-edges.md`

Covers: stock `test.wls` `$Path` bug (SE-D-1), preset bleed-through false-positive
(SE-D-2), and the correct output regex for DRAKE stdout (SE-D-3).

Covers: reading DRAKE's Ω h² from stdout, diagnosing the departure from the `<σv>`
expansion (ratio of full DRAKE result to the approximation), when disagreement > 20%
is expected and physically meaningful, and how to surface the comparison as a signal
(not a warning).

---

## Install detection (REQUIRED before any run)

Before invoking DRAKE, confirm the install is configured. `scripts/run_drake.py`
delegates detection entirely to `drake-install/scripts/install.sh detect`. Do not
duplicate the detection logic here.

The `detect` subcommand emits status JSON on stdout (exit 0) for all non-fatal outcomes.
Fatal blockers go to stderr as single-line JSON (exit non-zero).

Expected `status` values from `install.sh detect`:

| Value | Meaning | Action |
|-------|---------|--------|
| `configured` | `drake_path` set, `test/test.wls` present, WIMP smoke test passed | Proceed |
| `found` | DRAKE tree on disk but not registered in config (or wolframscript absent) | Run `/drake-install use-path <dir>` |
| `missing` | No DRAKE install found | **BLOCK — run `/drake-install` first** |
| `activation_required` | DRAKE found and path set, but Wolfram Engine needs activation before smoke test can pass | Run `wolframscript --activate`, then re-run `/drake-install detect` |

Note: prior to W4-E, `activation_required` was emitted by the `use-path` subcommand only.
Post-W4-E, `detect` also emits `activation_required` when the smoke test reveals an
unactivated Wolfram Engine, so callers should handle it from `detect` output.

**If status is `missing` or `found`, stop and direct the user to `/drake-install`.
Do not attempt a fallback calculation.**

Config keys read (written by `/drake-install use-path`):
- `drake_path` — absolute path to DRAKE root (contains `test/test.wls`)
- `wolfram_engine_path` — path to `wolframscript` binary
- `drake_version` — version string written by `drake-install` (required; absence blocks)

---

## Quick reference: invoking DRAKE

DRAKE is invoked via `wolframscript` from the DRAKE `test/` directory. The canonical
pattern (from `drake-install/scripts/probe_drake.sh` and the WIMP smoke test in
arXiv:2103.01944):

```bash
cd "$DRAKE_PATH/test"
wolframscript test.wls <model> <benchmark_file> <settings_file>
```

Where:
- `<model>` — model identifier (see Built-in models below)
- `<benchmark_file>` — name of the benchmark file (e.g. `bm_WIMP`, without extension)
- `<settings_file>` — name of the settings file (e.g. `settings_WIMP`, without extension)

Example — WIMP benchmark (canonical smoke test):
```bash
cd "$DRAKE_PATH/test"
wolframscript test.wls WIMP bm_WIMP settings_WIMP
```

Example — narrow-resonance VRES model:
```bash
cd "$DRAKE_PATH/test"
wolframscript test.wls VRES bm_VRES settings_VRES
```

**Note**: DRAKE resolves benchmark and settings files relative to the working directory.
Always `cd` into `$DRAKE_PATH/test/` before invoking `wolframscript test.wls`.

The `scripts/run_drake.py` helper handles `cd` and path resolution automatically.

---

## Built-in pre-implemented models

These ship with DRAKE and correspond directly to the benchmarks in arXiv:2103.01944:

| Model key | Regime | Benchmark file | Settings file |
|-----------|--------|----------------|---------------|
| `WIMP` | Standard thermal WIMP (smoke-test baseline) | `bm_WIMP` | `settings_WIMP` |
| `VRES` | Narrow s-channel vector resonance | `bm_VRES` | `settings_VRES` |
| `SE` | Sommerfeld-enhanced annihilation | `bm_SE` | `settings_SE` |
| `TH` | Threshold / forbidden channel freeze-out | `bm_TH` | `settings_TH` |
| `ScalarSingletDM` | Scalar singlet DM (Higgs portal, near resonance) | `bm_ScalarSingletDM` | `settings_ScalarSingletDM` |

For the `VRES` model: the correct regime trigger is `|m_res − 2 m_χ| / m_res < 0.1`.
This is the primary use case for `/drake` in the hephaestus marketplace.

**User-defined models**: To use parameters other than the shipped defaults, edit the
numerical values directly in the shipped `bm_*.wl` benchmark files. Do not fabricate
new Wolfram function signatures — the exact API for custom model definitions is not
verified from publicly accessible documentation (hepforge is Anubis-gated). Work only
from the shipped benchmark files and settings files present in `$DRAKE_PATH/test/`.

---

## Running DRAKE via `scripts/run_drake.py`

The `scripts/run_drake.py` script handles:
- Detecting DRAKE by shelling out to `drake-install/scripts/install.sh detect`
- Blocking with a clear error if DRAKE is not installed or `drake_version` is absent
- Building the `wolframscript` invocation
- `cd`-ing to `$DRAKE_PATH/test/` automatically
- Capturing stdout+stderr to a log file
- Returning raw stdout for the calling agent to read

Basic usage (agent-driven — Claude composes this, not the user):

```python
from scripts.run_drake import run_drake

result = run_drake(
    model="VRES",
    benchmark="bm_VRES",
    settings="settings_VRES",
)
# result keys: stdout, model, benchmark, settings, log_path, drake_path, drake_version
# Read result["stdout"] directly to extract Omega h^2 and other quantities.
```

Import note: when running from outside the skill directory, add the skill root to
`sys.path` before importing:
```python
import sys
sys.path.insert(0, "/path/to/plugins/hep-ph-toolkit/skills/drake")
from scripts.run_drake import run_drake
```

---

## Reading DRAKE output (agent-driven)

After a successful `wolframscript test.wls ...` run, DRAKE writes results to stdout.
The calling agent reads `result["stdout"]` directly — no regex parser is interposed.

Known output structure from the WIMP smoke test (arXiv:2103.01944):
- The output is Wolfram Language print output, typically a few lines.
- DRAKE prints relic density as `Oh2_nBE = <value>`, `Oh2_cBE = <value>`, and
  `Oh2_fBE = <value>` (not `Omega h^2`). Use the acceptance regex:
  `Oh2_(nBE|cBE|fBE)\s*=\s*([0-9eE.+\-]+)` to extract these values.
- Additional quantities (x_f, solver diagnostics) may appear on separate lines.
- The exact line format depends on the DRAKE version and model; read the actual stdout
  and extract quantities by scanning for the relevant label on each line.

> **Note on stock DRAKE_v1.0 test.wls:** The upstream file has `$Path` issues
> that prevent `<<DRAKE\`` from resolving. Apply
> `upstream-patches/test_wls_path.patch` before first use.

The complete raw stdout is also written to `log_path` (default `/tmp/drake_run.log`).

After reading stdout, emit a result dict:
```json
{
  "omega_h2": <float or null>,
  "xf": <float or null>,
  "model": "<string>",
  "log_path": "<absolute path>",
  "drake_path": "<absolute path>",
  "drake_version": "<string from config>"
}
```

If `omega_h2` is absent, NaN, or negative: record `null` and raise
`DRAKE_OUTPUT_INVALID` — do not return empty values or fall back to MadDM.

---

## Comparison workflow (the intended use case)

The primary signal from `/drake` is **disagreement** with `/maddm` or `/micromegas`.
A large departure (> 20%) is physically expected in the narrow-resonance regime and
should be surfaced as a result, not suppressed as a warning.

Recommended comparison sequence:

1. Run `/maddm` (or `/micromegas`) for the same model point → record Ω h²_standard
2. Check whether the resonance trigger condition fires:
   `|m_med − 2 m_χ| / m_med < 0.1`
3. If yes, run `/drake` with the appropriate model → record Ω h²_DRAKE
4. Report:
   - Ω h²_standard vs. Ω h²_DRAKE
   - Fractional departure: `(Ω h²_DRAKE − Ω h²_standard) / Ω h²_standard`
   - Whether the standard result over- or under-estimates the relic density

A departure > 50% in the narrow-resonance regime is consistent with the benchmarks in
arXiv:2103.01944 and validates the use of DRAKE over the standard approach.

---

## Failure modes → blockers

| Code | Mode | Trigger | Action |
|------|------|---------|--------|
| `DRAKE_NOT_INSTALLED` | fatal | `install.sh detect` returns `missing` or `found` | Run `/drake-install` |
| `DRAKE_WOLFRAM_ABSENT` | fatal | `wolfram_engine_path` not set or binary not executable | Run `/install` for Wolfram Engine |
| `DRAKE_RUN_FAILED` | fatal | `wolframscript test.wls` exited non-zero | Inspect log at `/tmp/drake_run.log`; check model file paths |
| `DRAKE_OUTPUT_INVALID` | fatal | Ω h² absent, NaN, or negative in stdout | Inspect log; DRAKE may need a valid model benchmark |
| `DRAKE_MODEL_FILE_MISSING` | fatal | Benchmark or settings file not found in `$DRAKE_PATH/test/` | Provide correct file names; use shipped `bm_*` files |

No analytic fallback is provided when DRAKE is unavailable. Block and direct the user
to `/drake-install`.

---

## File map

| Path | Description |
|------|-------------|
| `references/setup.md` | Install detection, Wolfram prerequisites, Anubis gate handling |
| `references/running.md` | Invocation, built-in models, benchmark/settings file structure |
| `references/comparison.md` | Interpreting DRAKE results, MadDM/micrOMEGAs comparison |
| `references/sharp-edges.md` | Playtest-surfaced gotchas: `$Path` bug, preset bleed-through, output regex |
| `scripts/run_drake.py` | DRAKE runner: delegates detection to install.sh, invokes wolframscript, returns raw stdout |
| `scripts/resonance_check.py` | Helper: evaluate whether a parameter point is in the narrow-resonance regime |

---

## Cross-skill dependencies

- **Install prerequisite**: `/drake-install` — must run first; configures `drake_path`.
- **Wolfram prerequisite**: `/install` — installs Wolfram Engine / `wolframscript`.
- **Standard relic density**: `/maddm` — run first; DRAKE validates in resonance regimes.
- **Coannihilation validator**: `/micromegas` — complementary; does not need DRAKE.
- **Orchestrator**: `/dark-matter-constraints` — meta-skill that routes to DRAKE when
  the resonance trigger fires.
- **Upstream spectrum**: `/spheno-build` — SLHA spectrum provides m_χ and m_med for
  the resonance check; values are passed to DRAKE's benchmark file manually (DRAKE does
  not read SLHA directly).
