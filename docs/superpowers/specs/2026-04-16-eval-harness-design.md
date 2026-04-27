# Eval Harness for MadGraph+MadDM Skills

**Date**: 2026-04-16
**Paper**: arXiv:2506.19062 — WIMPs Below the Radar (Arcadi & Profumo)

## Purpose

Test whether MadGraph+MadDM skills produce correct physics results. The harness
defines tasks (prompts + expected outcomes), runs them against a pluggable backend,
and grades the output with deterministic checkers.

Follows Anthropic's eval methodology: grade the outcome not the path, code-based
graders for numeric checks, pass@k for non-determinism, clean environment per trial.

## Architecture

```
Task (YAML) → Loader (computes expected values) → Runner (executes) → Graders (check) → Reporter (aggregate)
```

### Components

**Tasks** (`eval/tasks/*.yaml`): YAML files defining prompts, reference function
pointers, grader configurations, and metadata (tier, model, tags).

**Loader** (`eval/harness/loader.py`): Reads YAML, resolves `reference_fn` to a
Python callable, executes it with `reference_args` to compute expected values at
load time. Returns `Task` objects with populated `expected` dicts.

**Runners** (`eval/harness/runners/`): Swappable backends implementing `RunnerBase`.
- `ReferenceRunner`: Calls the reference function directly. Validates the grading
  pipeline without needing Claude or MadGraph.
- `ClaudeCodeRunner` (future): Spawns `claude --output-format json`, extracts
  structured answers from the response.

**Graders** (`eval/harness/graders.py`): Stateless functions that compare expected
vs actual values. Types:
- `numeric`: Relative tolerance comparison. For cross-sections, couplings, masses.
- `exact_zero`: Absolute tolerance for quantities that should vanish (blind spots).
- `unit`: String match on physical units.
- `file_exists`: Check a file was produced at an expected path.
- `file_contains`: Regex match on file content (proc_card validation).
- `ordering`: Assert σ(A) > σ(B) for physics sanity checks.

**Reporter** (`eval/harness/report.py`): Aggregates results across tasks and trials.
Computes pass@k and pass^k. Outputs JSON report + terminal summary table.

**CLI** (`eval/harness/run.py`): Entrypoint with flags for runner selection, tier
filtering, trial count, and output format.

### Reference functions (`eval/harness/refs.py`)

Thin wrappers around the existing analytical code in `2506.19062_wimps_blind_spots/`.
Each function takes physics parameters and returns a dict of observable quantities:

```python
def sd_sigma_si_tree(m_S, m_D, y, theta) -> dict:
    """Full chain: diag → coupling → σ_SI."""
    masses, U = diagonalize(m_S, m_D, *y1_y2_from_y_theta(y, theta))
    y_h = coupling_h_chi1chi1(m_S, m_D, y, theta)
    sigma = sigma_SI_higgs_portal(masses[0], y_h)
    return {"m_chi1": masses[0], "y_h": y_h, "sigma_SI": sigma, "sigma_SI_unit": "cm^2"}
```

## Task YAML format

```yaml
- id: sd_sigma_si_tree_m200
  tier: 2
  model: singlet-doublet
  prompt: >
    Compute the tree-level spin-independent DM-nucleon cross-section for
    the singlet-doublet model with m_S=150 GeV, m_D=500 GeV, y=1, theta=0.
  reference_fn: sd_sigma_si_tree
  reference_args:
    m_S: 150.0
    m_D: 500.0
    y: 1.0
    theta: 0.0
  graders:
    - type: numeric
      key: sigma_SI
      tolerance: 0.05
    - type: unit
      key: sigma_SI_unit
      expected: "cm^2"
  tags: [tree-level, SI, singlet-doublet, figure-2]
```

## Tiers

### Tier 1 — Setup (~8 tasks)
Can the skill set up and run MadGraph?
- Generate proc_card.dat for each model (3 tasks)
- Generate param_card.dat at a benchmark point (3 tasks)
- Parse MadGraph cross-section output (2 tasks)

### Tier 2 — Accuracy (~18 tasks)
Does it get the physics right at known benchmark points?
- σ_SI tree-level at 4 SD benchmark points
- σ_SD at 2 points
- Mass spectrum validation at 3 points
- 2HDM+a trilinear couplings at 3 points
- Dark SU(3) vector σ_SI at 3 Figure 7 points
- Dark SU(3) scalar blind spot at 3 points

### Tier 3 — Advanced (~9 tasks)
Can it handle derived/composite calculations?
- SD blind spot: find θ_bs and verify coupling vanishes (2 tasks)
- 2HDM+a: verify tree-level SI is zero by CP symmetry (1 task)
- SD+2HDM two-Higgs cancellation condition (2 tasks)
- Coupling cross-check Eq.7 vs Eq.33 with Majorana factor (2 tasks)
- σ_SI quadratic scaling with y_h (1 task)
- Heavy DM limit μ → m_p (1 task)

## CLI usage

```bash
# Run all tiers with reference runner
python -m eval.harness.run --runner reference

# Run specific tier
python -m eval.harness.run --runner reference --tier 2

# Multiple trials for pass@k
python -m eval.harness.run --runner reference --trials 5

# JSON report output
python -m eval.harness.run --runner reference --output results.json
```

## Grading

Each task can have multiple graders. A task passes a trial when ALL its graders
pass. Scoring modes per task:
- `all_pass` (default): Every grader must pass.
- `weighted`: Graders have weights, sum must exceed threshold.

Aggregate metrics:
- `pass@1`: Fraction of tasks that pass on a single trial.
- `pass@k`: Probability of at least one pass in k trials.
- `pass^k`: Probability of all k trials passing (consistency).
- Per-tier breakdown.
- Efficiency: token count, tool calls, wall time (when using ClaudeCodeRunner).

## Directory layout

```
eval/
├── harness/
│   ├── __init__.py
│   ├── types.py
│   ├── graders.py
│   ├── loader.py
│   ├── refs.py
│   ├── report.py
│   ├── run.py
│   └── runners/
│       ├── __init__.py
│       ├── base.py
│       └── reference.py
├── tasks/
│   ├── tier1_setup.yaml
│   ├── tier2_accuracy.yaml
│   └── tier3_advanced.yaml
├── 2506.19062_wimps_blind_spots/   # existing analytical code
└── ...
```

## Not in scope

- `ClaudeCodeRunner` — built when skills are ready to test
- Tier 4 (figure reproduction) — needs separate rubric design
- LLM-based graders — not needed for Tiers 1-3
- MadGraph installation/CI — separate infrastructure concern
