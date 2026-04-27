# Running DRAKE

## Invocation pattern

DRAKE is a Wolfram Language package invoked via `wolframscript`. The entry point is
`test/test.wls` in the DRAKE root directory:

```bash
cd "$DRAKE_PATH/test"
wolframscript test.wls <model> <benchmark_file> <settings_file>
```

All three positional arguments are required:

| Argument | Description |
|----------|-------------|
| `<model>` | Model identifier — one of the built-in names listed below |
| `<benchmark_file>` | Benchmark parameter file name, without extension (DRAKE appends `.wl` or `.m`). Defines DM mass, mediator mass, couplings. |
| `<settings_file>` | Solver settings file name, without extension. Selects solver mode and numerical precision options. |

DRAKE resolves benchmark and settings files relative to the current working directory.
**Always `cd` into `$DRAKE_PATH/test/` before calling `wolframscript test.wls`.**

The `scripts/run_drake.py` helper handles this automatically.

---

## Built-in pre-implemented models

All five models ship with DRAKE in the `test/` directory:

| Model key | Physical regime | Benchmark file | Settings file |
|-----------|----------------|----------------|---------------|
| `WIMP` | Standard thermal WIMP (smoke-test baseline) | `bm_WIMP` | `settings_WIMP` |
| `VRES` | Narrow s-channel vector resonance | `bm_VRES` | `settings_VRES` |
| `SE` | Sommerfeld-enhanced annihilation | `bm_SE` | `settings_SE` |
| `TH` | Threshold / forbidden channel | `bm_TH` | `settings_TH` |
| `ScalarSingletDM` | Scalar singlet DM, Higgs portal | `bm_ScalarSingletDM` | `settings_ScalarSingletDM` |

Source: arXiv:2103.01944 and the `drake-install/tests/fixtures/drake_stub/test/test.wls`
comment (lists WIMP, VRES, SE, TH, ScalarSingletDM as the shipped benchmarks).

---

## Running a built-in benchmark

```bash
# Narrow-resonance benchmark (VRES)
cd "$DRAKE_PATH/test"
wolframscript test.wls VRES bm_VRES settings_VRES
```

The `scripts/run_drake.py` wrapper (recommended for agent-driven runs):

```python
from scripts.run_drake import run_drake

result = run_drake(
    model="VRES",
    benchmark="bm_VRES",
    settings="settings_VRES",
)
# result["stdout"] contains the raw DRAKE output for the agent to read
```

---

## Adapting parameters

To run with parameters other than the shipped defaults (different DM mass, mediator
mass, or couplings), edit the numerical values directly in the shipped `bm_*.wl` files
in `$DRAKE_PATH/test/`. Inspect those files to see the variable names and structure used
by the specific model.

Do not fabricate new benchmark file formats or function signatures — the exact API for
user-defined model definitions is not verified from publicly accessible documentation
(hepforge is Anubis-gated). Work from the shipped `bm_*` and `settings_*` files as
templates, editing only numerical parameter values whose names are visible in the files.

---

## Solver modes

DRAKE implements multiple Boltzmann equation solvers. The solver is selected via the
settings file (`settings_<model>.wl`). Inspect the shipped `settings_WIMP.wl` and other
settings files in `$DRAKE_PATH/test/` to see the key names and valid values for solver
selection. Do not guess solver-mode strings from the paper notation — use the values
actually present in the shipped files.

From arXiv:2103.01944, DRAKE implements:
1. **Standard number-density Boltzmann equation** — equivalent to the `<σv>` Taylor
   expansion approach. Use as a baseline comparison.
2. **Fluid Boltzmann equations** — couples number density and velocity dispersion
   evolution. Appropriate for early kinetic decoupling and Sommerfeld enhancement.
3. **Full phase-space Boltzmann equation** — full numerical evolution of the phase-space
   distribution. Maximum precision; use for narrow resonances.

---

## Log files

DRAKE stdout and stderr are captured to `/tmp/drake_run.log` by `scripts/run_drake.py`.
Inspect this file on failure. The WIMP smoke test also writes to `/tmp/drake_smoke.log`.

---

## Runtime notes

- DRAKE is pure Wolfram Language; runtime is dominated by Wolfram Engine startup (~5–30 s)
  plus the numerical integration (seconds to minutes depending on model complexity and
  solver mode).
- For the full phase-space solver on a narrow-resonance model, expect several minutes on
  typical hardware.
- There is no parallelism within a single DRAKE run; parameter scans require serial
  invocations or external parallelism (multiple `wolframscript` processes).
