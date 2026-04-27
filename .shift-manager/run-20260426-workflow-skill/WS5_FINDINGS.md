# WS5 Findings

**Workstream:** WS5 — model-router integration validation
**Date:** 2026-04-26
**Status:** FINAL (iter-4)
**Run dir:** `.shift-manager/run-20260426-workflow-skill/`

All findings are categorised by severity:
- `load-bearing-failure` — failure HELD WS5; now resolved.
- `diagnostic` — failure ships with finding; does not HOLD.
- `router-followup` — behavior note; follow-up in a future workstream.
- `registry-authoring` — gap in registry authoring that WS5 scope cannot fix.

---

## Findings

### Finding 1: Real `_shared/analytic_exceptions.yaml` uses list shape; fixture uses dict shape

- **Severity:** registry-authoring
- **Model:** dark-su3
- **Observable:** N/A
- **Expected:** `render.py:305` can read exception data from the real `_shared/analytic_exceptions.yaml`. The consumer uses `.get("exceptions", {}).get(exception_id, {})` which requires a dict keyed by exception ID.
- **Actual:** Real `_shared/analytic_exceptions.yaml` uses a list shape: `exceptions: [{id: dsu3-002, ...}, ...]`. The dict lookup silently returns `{}`, meaning no banner would be emitted for `dsu3` if the router were pointed at the real registry.
- **Evidence:** `intel/ws5_spike_findings.md` R-class finding R1; `render.py:305` (consumer); `plugins/hep-ph-demo/skills/_shared/analytic_exceptions.yaml` (real registry shape).
- **Suggested follow-up:** hep-ph-demo plugin workstream — either (a) align real-registry shape to dict-keyed (with WS4 detector loader update), or (b) fix `render.py:305` to use the WS4 `RegistryView.by_id()` API. Both options are OUT-OF-SCOPE for WS5 per OOS guards.
- **Status:** DEFERRED

---

### Finding 2: Fixture banner did not match real banner; fixture missing `dark-su3-confining-synthetic` registration

- **Severity:** registry-authoring
- **Model:** dark-su3, dark-su3-confining-synthetic
- **Observable:** N/A
- **Expected:** Fixture `analytic_exceptions.yaml` dsu3-002 banner contains `"REGRESSION-ANCHOR"`, `"25000"`, `"Planck target"`. Fixture `constraints.yaml` has `dark-su3-confining-synthetic` entry.
- **Actual (pre-S0.5):** Fixture banner was an old short form that lacked the LOAD_BEARING substrings. The synthetic model had no fixture registry entry, causing `ModelNotInRegistry`.
- **Evidence:** `intel/ws5_spike_findings.md` D1, D2; first-run spike JSON outputs (error stubs).
- **Suggested follow-up:** N/A — resolved within WS5.
- **Status:** RESOLVED-IN-WS5 (S0.5). Banner rewritten verbatim from real registry. Synthetic model registered in fixture `constraints.yaml`.

---

### Finding 3: Real `_shared/constraints.yaml` lacks `spec_path` / `analytic_module` fields

- **Severity:** registry-authoring
- **Model:** all
- **Observable:** N/A
- **Expected:** The router's `stage_p0_load` expects `spec_path` and `analytic_module` fields in `constraints.yaml` model entries. These are present in the fixture registry and the canonical assets.
- **Actual:** The real `_shared/constraints.yaml` (as inspected during WS3 backfill spike) uses a different shape that does not include `spec_path` or `analytic_module` at the top-level model entry. The router would fail to load real-registry models without an adapter.
- **Evidence:** WS3 discovery; `intel/ws5_spike_findings.md` context.
- **Suggested follow-up:** hep-ph-demo plugin workstream — align real registry to the shape the router expects, or add an adapter layer in `stage_p0_load`. OUT-OF-SCOPE for WS5.
- **Status:** DEFERRED

---

### Finding 4: dark-su3 strict-mode snapshot slot missing (MatrixAcknowledgementMissing)

- **Severity:** diagnostic
- **Model:** dark-su3
- **Observable:** N/A (strict-mode exit code)
- **Expected (plan OD4):** 8 snapshot files (4 models × 2 modes). `test_snapshot_matches[dark-su3-strict]` and `test_snapshot_validates_against_schema[dark-su3-strict]` should exist.
- **Actual:** `dark-su3` strict mode raises `MatrixAcknowledgementMissing` (exit code 4) per the WS3 contract (`test_dark_su3_strict_with_missing_acknowledgement_exits_4`). The sentinel dict `{"exit_code": 4, "verdict": "_EXCEPTION_", ...}` returned by `report_pair` is not a valid `RoutingReport` JSON and fails schema validation. Therefore only 7 snapshots are generated; the `dark-su3-strict` slot is absent.
- **Evidence:** iter-2 Recommendation #1 (`ws5_iter2_review.md`); `test_strict_mode_exit_codes.py:33-44` (WS3 contract test); `regenerate_snapshots.py` SKIP message; `conftest.py` sentinel dict.
- **Suggested follow-up:** Either (a) add a separate "exception-captured snapshot" schema with a different `$schema` field to enable schema validation of the exception state, or (b) modify the fixture `constraints.yaml` `dark-su3` chain_override to include `MATRIX_COVERAGE_GAP` in `accepted_blockers` (but this would break the WS3 contract test). Preferred: option (a) in a future WS.
- **Status:** OPEN (documented; 14 snapshot tests instead of 16)

---

### Finding 5: `matrix_acknowledgement_missing_observables` schema field not asserted

- **Severity:** diagnostic
- **Model:** dark-su3
- **Observable:** relic
- **Expected:** The `matrix_acknowledgement_missing_observables` field in the expected YAMLs documents which observables have `matrix_acknowledgement_missing=True` in the router output. For `dark-su3`, `relic` has `matrix_acknowledgement_missing=True` because the fixture chain_override lacks `MATRIX_COVERAGE_GAP` (WS3 contract).
- **Actual:** The field is present in the expected YAMLs (`dark_su3.yaml: []`) but is never asserted by any test. Additionally, the value `[]` is arguable — the actual router behavior has `relic` as missing-acknowledgement, so the YAML should arguably be `["relic"]`.
- **Evidence:** iter-2 Recommendation #3; `test_dsu3_matrix_acknowledgement_intact` (DIAGNOSTIC, S3) asserts only `unexpected` (non-relic) observables.
- **Suggested follow-up:** (a) Correct `dark_su3.yaml` `matrix_acknowledgement_missing_observables` to `["relic"]`, or (b) drop the field from the schema as inert data. Low-priority schema cleanup.
- **Status:** OPEN (DIAGNOSTIC — ships with this finding)

---

### Finding 6: `_get_reports` not actually LRU-cached across test parametrize IDs (cosmetic)

- **Severity:** diagnostic
- **Model:** all
- **Observable:** N/A
- **Expected:** `@functools.lru_cache(maxsize=None)` on `_get_reports` should cut routing invocations from 80× to 8× per test session.
- **Actual:** Per iter-2 Recommendation #7, `lru_cache` was applied in iter-3. Test wallclock is ~6s for 73 integration tests, which is acceptable. This finding is retained for transparency.
- **Evidence:** `test_validation.py:47` (`@functools.lru_cache`); 73-test wallclock ≈ 6s.
- **Suggested follow-up:** None — performance is acceptable. Can profile if suite grows beyond 200 tests.
- **Status:** RESOLVED-IN-WS5 (iter-3 applied the cache)

---

## Summary table

| # | Title | Severity | Status |
|---|---|---|---|
| 1 | Real `_shared/analytic_exceptions.yaml` list-vs-dict shape | registry-authoring | DEFERRED |
| 2 | Fixture banner + synthetic model missing pre-S0.5 | registry-authoring | RESOLVED-IN-WS5 |
| 3 | Real `_shared/constraints.yaml` lacks `spec_path`/`analytic_module` | registry-authoring | DEFERRED |
| 4 | dark-su3-strict snapshot slot missing (sentinel-dict / schema) | diagnostic | OPEN |
| 5 | `matrix_acknowledgement_missing_observables` field inert | diagnostic | OPEN |
| 6 | `_get_reports` LRU cache (cosmetic) | diagnostic | RESOLVED-IN-WS5 |
