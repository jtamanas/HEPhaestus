# Paper-to-Benchmark Extraction Methodology

How to take a published hep-ph paper and turn it into a computational benchmark
that can validate our skill suite. Written as a repeatable workflow.

## Two-track distinction

The closed-form Python reference implementations in `eval/<paper>/` (models,
cross-sections, loop functions, benchmark tests) are **oracle-only** code. They
exist to provide ground truth for A/B scoring the agent — not as the agent's
production path. When the agent is driven through the harness on the same
observable, it must drive the established tool (MadGraph, MadDM, micrOMEGAs,
SPheno, ...); it must not fall back to reimplementing the paper's formulas in
numpy/scipy. This is the single exception to the project's "augment, don't
replace" principle: closed-form reference implementations are allowed — indeed required — but they
live under `eval/<paper>/` where they are scrutinized as benchmark oracles, and
they are never load-bearing inside a skill. Treat every reference function the
same way you would treat any other piece of physics code: pin it to a hand
calculation, cross-check it against a second route where possible, and assume
it has bugs until proven otherwise (see `CASE_STUDY.md`).

## Phase 1: Deep Paper Read

**Goal:** Extract every computable equation, every stated number, every benchmark parameter point.

Do two passes. The first pass gets the structure; the second gets the numbers.

### Pass 1: Structure extraction

Read the full paper and extract:

- **Paper metadata** — title, authors, arXiv ID, models studied
- **The Lagrangian** — what theory is being defined? What are the free parameters?
- **Every numbered equation** — classify each as:
  - *Closed-form function*: takes inputs, returns a number (e.g. a cross-section formula). These become Python functions.
  - *Algebraic identity*: something that must hold for all parameter values (e.g. a blind spot cancellation, a sum rule). These become tests.
  - *Definition*: names a quantity but isn't independently evaluable (e.g. a Lagrangian term). These become docstrings.
  - *Requires numerical integration*: involves loop integrals, Boltzmann equations, etc. These need scipy or specialized tools.
- **Figures** — what is plotted on each axis? What parameter point was used? What would you need to reproduce it?
- **Computational tools used** — did they use MadGraph, micrOMEGAs, FeynRules, LoopTools? This tells you what to cross-check against.

### Pass 2: Number extraction

Go back and pull out every specific numerical value:

- **Benchmark parameter points** from figure captions (not just scan ranges — the exact values used for the curves)
- **Physical constants** used (form factors, quark masses, VEVs — which reference did they take them from?)
- **Stated numerical results** — any time a cross-section, mass, or coupling is given as a number
- **Constraints applied** — exact relic density value, experimental limits, tolerance windows
- **Validation statements** — "we reproduced X from Ref. [Y]", "our result agrees with Z"

**Critical lesson learned:** Papers that present results as scatter plots over parameter scans (as opposed to tables of numbers) give you very few hard targets. You have to construct your own by computing the formulas at the stated benchmark points and cross-checking the chain of intermediate quantities.

## Phase 2: Directory Setup

One directory per paper, named `{arxiv_id}_{short_name}/`:

```
eval/{arxiv_id}_{short_name}/
├── README.md              # Paper premise, what we benchmark, figure-to-equation map
├── paper_metadata.json    # Structured metadata for programmatic access
├── constants.py           # Physical constants (EW params, form factors, PDFs)
├── models/                # One file per BSM model
│   ├── model_a.py         # Equations as functions, scan ranges, viability checks
│   └── model_b.py
├── cross_sections/        # Observable quantities
│   ├── si_tree_level.py
│   ├── si_one_loop.py
│   └── sd_tree_level.py
├── loop_functions/         # If needed: PV integrals, box functions
├── madgraph/              # proc/param/run cards per model + comparison runner
│   ├── model_a/
│   └── run_comparison.py
└── benchmarks/
    ├── benchmark_points.py  # Parameter points with expected outputs
    └── test_benchmarks.py   # The actual tests
```

**Rules:**
- Every function gets a docstring that says which equation number it implements
- Every parameter gets units in the docstring
- Constants go in one file, not scattered across modules
- The README maps figures to equations: "Figure 3 requires Eq. 14 evaluated over the scan ranges in Eq. 19"

## Phase 3: Implement Equations

Work model by model. For each model:

1. **Start with the mass matrix / spectrum.** If the model has mixing, implement the mass matrix and diagonalization first. Everything else depends on getting the physical masses right.

2. **Implement couplings.** The effective DM-mediator couplings (Higgs coupling, Z coupling, pseudoscalar coupling) that enter the cross-section formulas. If the paper gives two routes to the same coupling (e.g. an analytical formula AND a mixing-matrix formula), implement both — they become a cross-check.

3. **Implement cross-sections.** Tree-level first, then loop-level if needed. Keep the formula structure visible in the code — don't optimize away intermediate steps that you'll want to test.

4. **Implement scan ranges.** Return the parameter-space boundaries as a dict so the comparison runner can sample them.

## Phase 4: Write Tests That Pin Numbers

This is where the first attempt went wrong. The failure mode:

> **Bad test:** `assert sigma > 0` / `assert 1e-50 < sigma < 1e-40`
>
> **Why it's bad:** A formula wrong by a factor of 10 passes both checks.

**Every test must compare against a specific number that was computed independently of the code under test.** There are exactly four sources of such numbers:

### Source A: Hand calculation of the formula

Evaluate the formula step by step with a calculator. Write each intermediate value in the test docstring. Compare the code output to the final value.

```python
def test_sigma_SI_m200_yh01(self):
    """
    μ = 200×0.93827/(200+0.93827) = 0.93389 GeV
    μ²/π = 0.27755
    (m_p/v)² = 1.4528e-5
    y_h²/m_h⁴ = 4.063e-11
    f_N² = 0.08053
    σ = 5.137e-45 cm²
    """
    expected = self._sigma_SI_by_hand(200.0, 0.1)
    actual = sigma_SI_higgs_portal(200.0, 0.1)
    assert abs(actual - expected) / expected < 1e-10
```

### Source B: Two independent implementations of the same quantity

If the paper gives two paths to the same number (e.g. an analytical coupling formula AND a mixing-matrix route), implement both and compare. This is how we caught the Majorana factor-of-2 between Eq. 7 and Eq. 33.

```python
def test_coupling_cross_check(self):
    y_eq7 = coupling_from_analytical_formula(...)
    y_eq33 = 2.0 * coupling_from_mixing_matrix(...)  # Majorana factor
    assert abs(y_eq7 - y_eq33) < 1e-4
```

### Source C: Algebraic identities

Properties that must hold for ALL parameter values, not just specific ones:

- **Eigenvalue identities**: sum of eigenvalues = trace, product = determinant
- **Exact cancellations**: a blind spot amplitude that is structurally zero
- **Sum rules**: g_a² + g_A² = y_χ² (from unitarity of a mixing matrix)
- **Limit behavior**: μ → m_p when m_χ → ∞

Test these at multiple random parameter points, not just one. If the identity involves a cancellation, test at edge cases (tiny/huge masses, maximal mixing).

### Source D: Self-consistency under parameter variation

- Solve for the blind-spot θ numerically, then verify the coupling actually vanishes at that θ
- Verify σ_SI(y_H=0) reduces exactly to the single-Higgs formula
- Check that doubling y_h multiplies σ by exactly 4 (not approximately — exactly)

### What NOT to test

- "Is positive" — almost everything is positive, this catches nothing
- "Is in [1e-50, 1e-40]" — a 10-order-of-magnitude window catches nothing
- "Is finite" — only useful for NaN/inf edge cases, not formula correctness
- "Increases with coupling" — true for any monotonic function, doesn't validate the formula

These property checks are acceptable ONLY as supplements to pinned-number tests, never as the sole test for a formula.

## Phase 5: MadGraph Setup

For each model:

1. **Identify the UFO model.** Is it publicly available (like the LHC DM WG 2HDM+a)? Or does it need to be generated from FeynRules?

2. **Write proc_card.dat.** Define the processes that correspond to the paper's calculations:
   - DM-nucleon elastic scattering (for SI/SD cross-section comparison)
   - DM pair annihilation (for relic density comparison)
   - Collider production (for constraint validation)

3. **Write param_card.dat.** Use the paper's benchmark parameter point. Include comments explaining where each value comes from.

4. **Write run_card.dat.** For DM-nucleon scattering: fixed-target, zero-momentum-transfer limit. For annihilation: COM frame near 2×m_DM.

5. **Write run_comparison.py.** A script that:
   - Takes a model name and benchmark point
   - Runs MadGraph at that point
   - Extracts the cross-section from MadGraph output
   - Compares to the analytical Python implementation
   - Reports pass/fail with tolerance

## Phase 6: Iterate on Failures

When a test fails, it's telling you something real. The three most common causes:

1. **Convention mismatch.** Factor-of-2 from Majorana fermions, factor of 4π from coupling definitions, missing 1/2 from identical particles. Fix by tracing the convention from the Lagrangian through to the observable.

2. **Sign error in mixing.** The rotation matrix convention (which entry gets the minus sign) matters for cancellations. If a blind spot test fails, the sign convention is wrong.

3. **Tolerance too tight.** If the diff is 1e-59 on a 1e-43 quantity, that's double-precision noise, not a bug. Use relative tolerances for cross-sections, absolute tolerances for quantities that should be exactly zero.

## Summary Checklist

- [ ] Full paper read: equations classified, figures mapped, numbers extracted
- [ ] Directory created with README, metadata, constants
- [ ] Model equations implemented as functions with equation-number docstrings
- [ ] Cross-section formulas implemented (tree-level and loop-level)
- [ ] Hand calculations done for at least 3 benchmark points
- [ ] Two independent paths cross-checked where available
- [ ] Algebraic identities tested at random parameter points
- [ ] Self-consistent blind spot verified (solve + check)
- [ ] Every test pins a specific number, not a range
- [ ] MadGraph cards written for each model at benchmark points
- [ ] Tests pass (and would FAIL if you introduced a factor-of-2 error)
