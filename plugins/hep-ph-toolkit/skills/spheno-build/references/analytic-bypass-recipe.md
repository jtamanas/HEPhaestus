# Analytic-backend bypass recipe

When `/spheno-build`'s SPheno backend fails (e.g. SARAH-emitted Fortran
has unresolved symbols like `SAxDynkin(2,color)` that gfortran can't
compile — see `sarah-build/references/sarah-workarounds.md` §
"SAxDynkin/$Failed emission"), the same skill ships an analytic
backend that can stand in for small closed-form models. This doc is
the recipe for routing around SPheno without abandoning the skill.

## When this applies

- You have a model whose mass matrix is small (3×3 or smaller) and
  closed-form diagonalisable (Majorana eigenvalue problem, or
  symmetric real matrix).
- An analytic module exists under
  `plugins/hep-ph-toolkit/skills/spheno-build/scripts/analytic_models/<model>.py`
  and is registered in the sibling `__init__.py`'s `REGISTRY` dict.
- The downstream consumer (e.g. MadDM) can read an SLHA with
  `SPINFO 2 = WS-A` and use the `MASS` + mixing blocks without
  round-tripping through SPheno's RGE runner.
- No observable that depends on SPheno-specific loop-level output is
  required (no loop-corrected Higgs mass, no radiatively-computed
  decay widths from SPheno). Relic density via MadDM is fine because
  MadDM recomputes the annihilation cross-section from the UFO — the
  SLHA is parameter input, not an observable.

## Two ways to invoke the analytic backend

### A. Via `/spheno-build`'s dispatcher (preferred when you own the spec)

Edit the ModelSpec YAML to add a `backends` block:

```yaml
backends:
  spectrum: analytic       # override the default (which is `spheno`
                           # whenever `outputs` contains "spheno")
  analytic_module: singlet_doublet   # optional; defaults to spec.name
```

Then run `/spheno-build` as usual. The dispatcher resolution order is
documented in `spheno-build/SKILL.md` § "Spectrum backends" (Selection rule):

1. `spec['backends']['spectrum']` wins if set.
2. Else `outputs` contains `spheno` → `spheno`.
3. Else → `analytic`.

### B. Call the backend directly (playtest / out-of-tree driver)

When you don't want to modify the spec (e.g. during a playtest that
only wants one success), call the module directly. Minimal skeleton:

```python
import importlib.util as ilu
from pathlib import Path

SCRIPT_DIR = Path("plugins/hep-ph-toolkit/skills/spheno-build/scripts")

def _load(name, path):
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

sd = _load("sd", SCRIPT_DIR / "analytic_models/singlet_doublet.py")
sw = _load("sw", SCRIPT_DIR / "slha_writer.py")

result = sd.compute({"name": "singlet_doublet"},
                    {"MS": 150.0, "MPsi": 500.0, "yh1": 1.0, "yh2": 0.0})
slha_text = sw.render(result, spec={"name": "singlet_doublet"},
                      params={"MS": 150.0, "MPsi": 500.0,
                              "yh1": 1.0, "yh2": 0.0})
Path("spectrum.slha").write_text(slha_text)
```

The emitted SLHA conforms to `parse_slha.parse`'s grammar and can be
fed to MadDM either as `param_card.dat` (after copying MASS / mixing
blocks over MG5's UFO-default template) or placed in `Cards/` directly.

A full working driver (analytic spectrum → patch `param_card.dat` →
MG5+MadDM launch) lives at
`demo_output/singlet-doublet/retry_analytic/drive.py`.

## What's missing compared to a real SPheno run

| Thing | Real SPheno | Analytic module |
|---|---|---|
| Tree-level masses | ✓ | ✓ |
| Mixing matrices | ✓ | ✓ (per module — all currently emit ZNMIX, UMMIX, UPMIX) |
| Decay widths | ✓ (computed from model) | ✗ (left at UFO default) |
| Running couplings (RGE) | ✓ | ✗ (tree-level inputs only) |
| Loop-corrected Higgs mass | ✓ | ✗ |
| 2-loop contributions | ✓ (Higgs sector) | ✗ |
| FlavorKit observables | ✓ (if model has them) | ✗ |

For WIMP relic density via MadDM at tree level, nothing in the missing
column is load-bearing: MadDM reads `MASS` + mixing from the SLHA and
recomputes annihilation cross-sections from the UFO vertices. The
paper benchmark (`arXiv:2506.19062` §II) also works at tree level, so
the analytic path reproduces it.

For direct detection with loop-induced box diagrams (when
`/feynarts`, `/formcalc`, `/ddcalc` ship), the
analytic SLHA is still sufficient as the tree-level input; the loop
machinery doesn't consume SPheno-specific output.

## Registering a new analytic module

Two lines in `scripts/analytic_models/__init__.py`:

```python
new_name = _load("new_name")
# ... and in the dict literal below:
REGISTRY = {..., "new_name": new_name}
```

Then `scripts/analytic_models/new_name.py` defines
`compute(spec, params) -> dict` returning `masses`, `mixing`,
`problem`, etc. See `singlet_doublet.py` for the canonical pattern.

Common sharp edges are covered in
[`analytic-backend.md`](analytic-backend.md) § "Interface contract" and
"Location and discovery".
