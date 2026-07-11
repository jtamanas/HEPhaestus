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

## Live playtests (opt-in, not run by default)

`tests/dark_su3_playtest/test_playtest_tier2.py` (Tier-2 scenarios, marked
`pytest.mark.integration`) shells out to the real `claude -p --model sonnet`
CLI once per scenario. These are **live LLM calls**: non-deterministic, ~20
minutes and real API spend per scenario (5 scenarios in the matrix). A bare
`python -m pytest` from the repo root must never trigger this spend, so the
module is gated behind an env var and skips by default — regardless of
whether the `claude` CLI is on `PATH` — with a skip reason that states the
opt-in:

```
HEPPH_RUN_LIVE_PLAYTESTS=1 pytest tests/dark_su3_playtest/test_playtest_tier2.py
```

Tier-1 (`test_playtest_tier1.py`, stubbed LLM output) and Tier-3 smoke
(`test_playtest_tier3_smoke.py`, gated separately on a real `maddm-launcher`
binary being on `PATH`) are unaffected by this gate.

### Retry budget for hard assertions

The Tier-2 hard assertions can flake on live tool-invocation checks even when
the underlying behavior is correct (non-deterministic tool selection, arg
spelling, blocker-token casing). To absorb that variance without weakening the
gate, `run_with_retry_budget` (in `tests/dark_su3_playtest/conftest.py`) gives
each scenario a **shared retry budget** across its hard *and* soft assertions:

- Each attempt is exactly one skill invocation (one live LLM call in Tier-2/3).
- The scenario re-invokes only while a hard assertion is still failing and
  budget remains; a scenario that passes its hard gate on attempt 1 spends
  **exactly one** invocation (it does not burn further live calls chasing the
  informational soft retries the older single-shot-hard design did).
- The hard gate is evaluated on the **final** attempt; a soft assertion is
  credited to the earliest attempt on which it passed, else `None`.
- Per-attempt failure detail is preserved in `RetryResult.hard_attempt_history`
  (index 0 == attempt 1) so a report can show which assertion flaked and when
  it recovered.

The budget is the total number of live LLM calls a single scenario may consume
before its hard gate fails. It defaults to **3** and is configurable:

```
HEPPH_PLAYTEST_MAX_ATTEMPTS=1 HEPPH_RUN_LIVE_PLAYTESTS=1 \
  pytest tests/dark_su3_playtest/test_playtest_tier2.py -k pointA_configured
```

`HEPPH_PLAYTEST_MAX_ATTEMPTS=1` reproduces the old single-shot behavior (useful
for a cheap one-call live sanity check). Values below 1 or non-integers fall
back to the default. Worst-case live spend per scenario is
`HEPPH_PLAYTEST_MAX_ATTEMPTS` × (~20 min + one call); across the full 5-scenario
matrix at the default budget of 3 that is **up to 15 live LLM calls** (~5 hours
+ 15 × per-call API spend) in the everything-flakes worst case.

Some matchers were also made robust to live formatting variance while staying
non-vacuous (they still fail when the behavior is genuinely absent): the
`check_prereqs` check matches on running the check for the `darksu3` model
rather than exact `--model`/`--config` flag spelling; the
`CROSSCHECK_DISAGREEMENT` blocker check matches the structured token with
tolerance only for casing and a single space/`_`/`-` internal separator —
prose narration ("cross-check disagreement"), punctuation-separated, or negated
mentions never match, and the check_prereqs matcher requires execution shape
(flags after the script token in the same shell segment), not a mere mention
of the script. The `extract_field` schema-version and
`sigma_v_zero` checks deliberately still require the *guarded* extractor —
reading the JSON via `jq`/`Read` bypasses the schema-drift guard and is treated
as a genuine gap, not a flake. Deterministic coverage of all of this lives in
`tests/dark_su3_playtest/test_retry_budget.py` and runs under a plain
`python -m pytest` with no live calls.

Every attempt that fails a hard assertion also dumps its transcript evidence
(`harness_meta`, captured argv, failure list) as JSON to
`HEPPH_PLAYTEST_DEBUG_DIR` (default: system temp dir), printing the path
(visible under `pytest -s`). Live attempts cost ~20 min + real API spend, so a
failed run must leave something to diagnose.

## Merge-ordering note

The specifics of the marker removal and the `importlib` switch land with the
pytest-collection change (PR #4), not with this doc. If this doc merges first, its
"before/after" framing stays accurate on `main` in the interim: the invariant and
the `prepend`-mode package-chain guidance describe the current state; the
`importlib`/removal paragraphs describe what PR #4 does when it lands.
