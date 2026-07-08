# Testing — pytest collection invariants

How the test suite is collected from the repo root, and the one invariant a
contributor can silently break by adding or deleting a `tests/__init__.py`.

## Running the suite

```
python -m pytest plugins/ eval/            # whole repo, from root
python -m pytest plugins/hep-ph-toolkit/skills/_shared/tests -q   # one dir
```

Per-directory and per-skill invocation both work; the root invocation collects
everything in a single pass.

## The invariant (stable — true before and after the pytest-collection change)

**No two duplicate-basename test modules may collapse to the same import package
name.**

Many skills ship a `tests/` dir with the *same* basenames — `test_smoke.py`,
`test_schema.py`, `test_benchmarks.py`, `test_blocker_shape.py`,
`test_activation_parse.py`, and more. If two such files resolve to the same
importable module name, pytest cannot import both: collection fails, or — worse —
one file's fixtures silently shadow another's (e.g. `micromegas/tests/` and
`higgstools/tests/` once both collapsed to package `tests.test_blocker_shape`,
producing a `fixture 'blocker_schema' not found` error on micromegas). This
invariant must hold no matter how the suite is collected; only the *mechanism*
that keeps it satisfied differs by pytest import mode (below).

## Two mechanisms — which one is load-bearing depends on the import mode

- **Default `prepend` mode (the state on this branch today).** Uniqueness comes
  from a **package chain**: a skill keeps an empty `__init__.py` in its skill dir
  *and* its `tests/` dir so its modules get a unique dotted name
  (`micromegas.tests.test_blocker_shape` vs `higgstools.tests.test_blocker_shape`).
  In this mode those `__init__.py` markers are **load-bearing** — deleting one can
  reopen a basename collision. There are currently 16 `tests/__init__.py` markers
  under `plugins/` (plus the repo-root `tests/__init__.py`, which sits outside the
  collected `plugins/` + `eval/` paths) — 17 repo-wide
  (`git ls-files '*tests/__init__.py' | wc -l`); all are present on this branch.
- **`--import-mode=importlib` (adopted by the in-flight pytest-collection change,
  PR #4).** That change sets `addopts = --import-mode=importlib` in `pytest.ini`,
  under which module uniqueness is derived from the file **path**; a `tests`
  package chain is then no longer required to disambiguate duplicate basenames.
  Because the markers become redundant *and* an empty top-level `tests` package
  cross-contaminates `tests.__path__` / `tests.conftest` registration, PR #4
  removes 9 of them (`skills/{2hdm-a,gamlike,looptools,model-router,spheno-build}/tests/__init__.py`
  and `_shared/installs/{class,ddcalc,higgstools,micromegas}/tests/__init__.py`)
  and switches `model-router` to relative imports. It deliberately **keeps** the
  package chains that other duplicate basenames still rely on (see below).

The invariant is the same under both modes; the guidance below is what protects it
in whichever mode is active.

## Rules for contributors

- **Do NOT add** an empty `tests/__init__.py` to a skill that does not already have
  one. Under `prepend` mode a new bare marker can collide with another skill's
  identically-named module; under `importlib` mode PR #4 has just removed 9 such
  markers for that reason — do not re-add them.
- **Do NOT delete** a `tests/__init__.py` that is disambiguating a duplicate
  basename via a package chain. On this branch (and after PR #4) these are
  load-bearing: the **skill dirs** `skills/{higgstools,micromegas,ddcalc,class}/`
  (each with its own skill-dir + `tests/` markers), and the leaf `tests` packages
  `_shared/tests`, `_shared/modelspec_v3/tests`, and `dark-matter-constraints/tests`.
  (Note: the four *installs* markers
  `_shared/installs/{class,ddcalc,higgstools,micromegas}/tests/__init__.py` share
  the same four names but live under `installs/`, not `skills/` — those are the
  ones PR #4 removes. Keep the four **skill-dir** ones; do not conflate the two
  locations.)
- `dark-matter-constraints` is the sole bare `tests` package that does intra-`tests`
  imports (`from tests.oracle...`). If a skill genuinely needs intra-`tests`
  package imports, use **relative** imports (`from .conftest import ...`).

## Merge-ordering note

The specifics of the marker removal and the `importlib` switch land with the
pytest-collection change (PR #4), not with this doc. If this doc merges first, its
"before/after" framing stays accurate on `main` in the interim: the invariant and
the `prepend`-mode package-chain guidance describe the current state; the
`importlib`/removal paragraphs describe what PR #4 does when it lands.
