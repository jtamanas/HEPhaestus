# /micromegas — Iteration 2 Implementation Report

Author: claude-sonnet-4-6 (iteration-2)
Date: 2026-04-19
Branch: workstream-constraints-micromegas
Addressing: iteration-1-review.md (NEEDS_FIXES)

---

## Commits Added This Iteration

```
522b2cf W8-mO: fix A — synthetic fixture + seed-dict parser tests, drop 0.118 literal
7c5ee59 W8-mO: fix B — defer scan to v1.1 with MICROMEGAS_SCAN_NOT_IMPLEMENTED blocker
e56042c W8-mO: fix C — strengthen flock test with multiprocessing mutual exclusion
e8a26ab W8-mO: fix D — document HEPPH_SKIP_DISK_CHECK in micromegas-install SKILL.md
```

4 atomic commits, each green at tree time (verified by `pytest plugins/hep-ph-toolkit/skills/ -q` after each).

---

## Per-Fix Results

### Fix A — Golden fixture "no arithmetic" discipline

**What was done:**

1. Created `tests/fixtures/stdout_synthetic.txt` — a structured fake with seeded constants
   and an explicit header comment identifying it as parser-test-only (not real micrOMEGAs output).
   Seed values are chosen to exercise every parser code path; none match the Planck relic density.

2. Rewrote `tests/test_parse_micromegas_out.py` to:
   - Import `_SEED` dict matching the fixture's embedded constants
   - Assert `parse(fixture) == seed_dict` via `pytest.approx` (round-trip test)
   - Remove all literals `0.118`, `0.05` from assertions
   - Preserve `TestNaNOmega` and `TestMissingOmega` classes (unchanged)
   - Add `test_round_trip_all_keys_present` structural regression guard

3. Added a header note to `scripts/regenerate_fixture.py` documenting that the
   committed `stdout_singletDM.txt` is a legacy placeholder, the parser unit tests
   use `stdout_synthetic.txt`, and real fixture regeneration is a v1.1 follow-up.

4. Added `TestRegenerateFixture` integration test class to `test_singletdm_golden.py`
   (gated on `HEPPH_RUN_NETWORK_TESTS=1`) that runs `regenerate_fixture.py` and
   asserts output structure (keys present, values finite+positive) — not specific
   physics values.

**Evidence:**
```
pytest plugins/hep-ph-toolkit/skills/micromegas/tests/test_parse_micromegas_out.py -v
→ 14 passed in 0.01s

grep -rn '0\.118' plugins/hep-ph-toolkit/skills/micromegas/tests/
→ only in a comment line ("constants (like 0.118) appear here"), no assertions
```

**Note:** `stdout_singletDM.txt` (legacy placeholder) is intentionally preserved
for the gated integration test `test_singletdm_golden.py`; it is NOT used by parser
unit tests. The review said "rename the fixture to stdout_synthetic.txt" — I created
`stdout_synthetic.txt` as the new parser test fixture while keeping `stdout_singletDM.txt`
for the integration tier that compares against it.

---

### Fix B — `scan.py` stub rows

**What was done:**

1. In `scripts/scan.py` `scan()` function: replaced `row["status"] = "queued"` with
   `row["status"] = "MICROMEGAS_SCAN_NOT_IMPLEMENTED"` and
   `row["blocker_code"] = "MICROMEGAS_SCAN_NOT_IMPLEMENTED"`. Added a v1.1 TODO
   comment documenting where `run_point.run()` will be connected.

2. In `scripts/run_micromegas.py` CLI: when `--scan` is provided, emit a recoverable
   `MICROMEGAS_SCAN_NOT_IMPLEMENTED` blocker and return exit code 3 (recoverable),
   before invoking `scan_mod.scan()`. This is the CLI-level deferral the review recommended.

3. Updated `SKILL.md`: renamed "Scan mode" section to "Scan mode (v1.1 backlog)",
   added note that `--scan` emits `MICROMEGAS_SCAN_NOT_IMPLEMENTED`. Added scan to the
   "Out of scope (v1.1)" list.

**Evidence:**
```
pytest plugins/hep-ph-toolkit/skills/micromegas/tests/test_scan_determinism.py -v
→ 9 passed in 0.02s

python3 -c "from scan import scan; ...; rows = csv.DictReader(open(csv_path)); \
  assert all(r['status'] != 'queued' for r in rows)"
→ PASS: all rows have status=MICROMEGAS_SCAN_NOT_IMPLEMENTED
```

---

### Fix C — `test_flock_cache.py` trivially-passable test

**What was done:**

Rewrote `test_cache_populated_once` as `test_cache_populated_once_multiprocessing`:
- Uses `multiprocessing.Process` to spawn two workers competing to populate a shared cache dir
- Each worker uses `fcntl.flock(LOCK_EX)` (the same syscall as `ufo_to_calchep.sh`)
- Atomically renames a `.tmp` dir to the cache dir after population
- Puts `(worker_id, "miss" | "hit")` into a `multiprocessing.Queue`
- Asserts: exactly 1 cache-miss, exactly 1 cache-hit, 0 race conditions
- Asserts `.complete` marker and `populated_by` file are present at end
- Asserts populator ID matches the miss worker

The assertion `len(miss_workers) == 1` FAILS if nothing populates (verified by simulation
showing two "hit" workers cause `AssertionError: Expected exactly 1 cache-miss, got 0`).

**Evidence:**
```
pytest plugins/hep-ph-toolkit/skills/micromegas/tests/test_flock_cache.py -v
→ 3 passed in 0.11s

python3 -c "# simulate no-population case: AssertionError raised as expected"
→ TEST WOULD FAIL AS EXPECTED
```

---

### Fix D — Disk-check ordering / HEPPH_SKIP_DISK_CHECK documentation

**What was done:**

Added explicit documentation block to `micromegas-install/SKILL.md` under the `install`
subcommand section. Documents:
- What `check_disk 3 5` does (3 GB required, 5 GB warn threshold)
- The `HEPPH_SKIP_DISK_CHECK=1` env var and when to use it
- The disk-check/network-check ordering (disk check fires first)
- Example command combining both `HEPPH_SKIP_DISK_CHECK=1` and `HEPPH_NO_NETWORK=1`

The `HEPPH_SKIP_DISK_CHECK` env-var branch already existed in `install_impl.sh` (line 49);
this fix is documentation-only per the review's "Pick the simpler" guidance.

**Evidence:**
```
HEPPH_SKIP_DISK_CHECK=1 HEPPH_NO_NETWORK=1 HEPPH_OFFLINE_CACHE_DIR=/tmp/empty \
  bash install_micromegas.sh install 2>&1 | grep -q MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY
→ PASS
```

---

## Nice-to-haves (Skipped)

The following nice-to-haves from the review were skipped as scope-creep:

- `command -v flock` check in `ufo_to_calchep.sh`: macOS flock availability is a runtime
  concern noted in Deviation #4 of iteration-1; a `command -v flock` guard is a small
  improvement but not blocking.
- `plugin.json` lexical sort: sibling workstreams have not landed; will resolve at merge.
- PPPC table path verification: needs a real micrOMEGAs 6.0.5 tarball; v1.1 install smoke.

---

## Re-Verification Results

### pytest (full suite)
```
pytest plugins/hep-ph-toolkit/skills/ -q
→ 100 passed, 5 skipped in 1.05s
```
(Up from 95 passed, 4 skipped in iteration-1.)

### Plan §4 checklist
```
python -m json.tool .claude-plugin/marketplace.json >/dev/null         → PASS
python -m json.tool plugins/constraints/.claude-plugin/plugin.json     → PASS
python -m json.tool plugins/shared/schemas/scattering.schema.json      → PASS
Draft 2020-12 schema validation                                         → PASS
symlink resolves to ../../../model-building/skills/_shared/...          → PASS
grep "constraints" marketplace.json = 1                                 → PASS
grep "micromegas" plugin.json = 3                                       → PASS
bash test_detect_states.sh                                              → PASS (4/4)
install_micromegas.sh detect → {"status":"missing"}                    → PASS
HEPPH_SKIP_DISK_CHECK=1 HEPPH_NO_NETWORK=1 ... | grep BLOCKED_BY_POLICY → PASS
git log -1 | grep W8-mO                                                → PASS
```

### Review re-verification items
```
grep -n '0\.118\|0\.05' tests/ → only in comment, no test assertions   → PASS
scan.py rows status != queued                                           → PASS (MICROMEGAS_SCAN_NOT_IMPLEMENTED)
test_flock_cache.py: test fails if mock fails to populate               → PASS (verified by simulation)
```

---

## Summary

All 4 required fixes from the opus-4-7 review are addressed. The full suite went from
95 passed → 100 passed. No physics literals in test assertions. Scan mode explicitly
deferred with proper blocker codes. Flock test now has a meaningful assertion that
distinguishes zero-population from mutual exclusion.
