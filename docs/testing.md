# Testing — pytest collection invariants

How the test suite is collected from the repo root, and the one invariant a
contributor can silently break.

## Running the suite

```
python -m pytest plugins/ eval/            # whole repo, from root
python -m pytest plugins/hep-ph-toolkit/skills/_shared/tests -q   # one dir
```

Per-directory and per-skill invocation both work; the root invocation collects
everything in a single pass.

## The `__init__.py` invariant (read before adding or deleting one)

**Invariant: no two duplicate-basename test modules may collapse to the same
import package name.**

Many skills ship a `tests/` dir with the *same* basenames — `test_smoke.py`,
`test_schema.py`, `test_benchmarks.py`, `test_blocker_shape.py`,
`test_activation_parse.py`, and more. If two such files resolve to the same
importable module name, pytest cannot import both and collection fails (or, worse,
one file's fixtures silently shadow another's — e.g. `micromegas/tests/` and
`higgstools/tests/` both once collapsed to package `tests.test_blocker_shape`,
producing a `fixture 'blocker_schema' not found` error on micromegas).

Each duplicate basename is disambiguated in one of two ways, and **both are
load-bearing**:

- **Package-chain disambiguation** — a skill keeps an empty `__init__.py` in its
  skill dir *and* its `tests/` dir, so its modules get a unique dotted name
  (`micromegas.tests.test_blocker_shape` vs `higgstools.tests.test_blocker_shape`).
  Currently relied on by the `higgstools`, `micromegas`, `ddcalc`, and `class`
  skill dirs, plus the leaf `tests/__init__.py` under `_shared/tests`,
  `_shared/modelspec_v3/tests`, and `dark-matter-constraints/tests` (the last is
  also the sole package that does intra-`tests` imports, `from tests.oracle...`).
  **Do not delete these** — removing one reopens a basename collision.
- **Path-based disambiguation** — a skill has *no* `__init__.py` anywhere in its
  `tests/` path, so its modules get a unique path-derived name instead. A number
  of skills use this route. Adding an empty `tests/__init__.py` to one of them can
  *create* a collision with another skill's identically-named module.

Consequences for contributors:

- **Do NOT re-add** an empty `tests/__init__.py` to a skill that does not already
  have one. Nine such markers were removed precisely because they all collapsed to
  a single top-level `tests` package that cross-contaminated `tests.__path__` and
  `tests.conftest` registration.
- **Do NOT delete** any of the load-bearing `__init__.py` chains listed above.
- If a skill genuinely needs intra-`tests` package imports, use **relative**
  imports (`from .conftest import ...`) and be aware that only
  `dark-matter-constraints` currently owns a bare `tests` package.

The invariant holds regardless of pytest's import mode; it is a property of how
duplicate module basenames map to import names, not of any one `pytest.ini`
setting.
