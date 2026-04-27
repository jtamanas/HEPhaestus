# WS5 Spike Findings

**Date:** 2026-04-26
**Step:** S0 (spike) + S0.5 (fixture repair)
**Spike script:** `impl/ws5_spike.py`
**Spike outputs:** `intel/ws5_spike_*.json` (10 files; 8 current 4×2, 2 old error stubs)

---

## Summary

All 8 spike outputs (4 models × 2 modes) are now valid after S0.5 fixes.
Initial spike (pre-S0.5) revealed 5 findings; 4 are D-class (plan table errors)
and 1 is R-class (router behavior note).

---

## Pre-S0.5 Findings

### D1 — Fixture banner missing "25000" + "Planck target" (RESOLVED by S0.5)

- **Class:** D-class (plan table/fixture wrong, not router wrong)
- **Model:** dark-su3
- **Expected (plan §1.1.3):** `placements[0].content` contains "25000" and "Planck target"
- **Actual (pre-S0.5):** fixture `analytic_exceptions.yaml` dsu3-002 banner was the old short form; did NOT contain "25000" or "Planck target"
- **Evidence:** `ws5_spike_dark_su3_default.json` (first run); fixture file mismatch against real `_shared/analytic_exceptions.yaml`
- **Status:** RESOLVED-IN-WS5 (S0.5). Fixture banner rewritten verbatim from real registry.

### D2 — Synthetic model "dark-su3-confining-synthetic" not in fixture registry (RESOLVED by S0.5)

- **Class:** D-class (fixture authoring gap)
- **Model:** dark-su3-confining-synthetic
- **Expected (plan §1.1.4):** routable via fixture `constraints.yaml`
- **Actual (pre-S0.5):** `ModelNotInRegistry` for all spike calls; fixture had no entry for this model
- **Evidence:** first spike run error outputs `ws5_spike_dark_su3_confining_synthetic_*.json`
- **Status:** RESOLVED-IN-WS5 (S0.5). Model registered in fixture `constraints.yaml`.

### D3 — Model ID "2hdm-a" is "two-hdm-a" in fixture registry (RESOLVED by S0.5)

- **Class:** D-class (plan uses wrong model ID)
- **Model:** two-hdm-a
- **Expected (plan §1.1.2):** plan calls the model `2hdm-a`
- **Actual:** fixture registry key is `two-hdm-a` (with "two" not "2"); `ModelNotInRegistry` on `2hdm-a`
- **Evidence:** first spike run error outputs `ws5_spike_2hdm_a_*.json`; fixture `constraints.yaml` shows `two-hdm-a` key
- **Impact:** All WS5 S1+ files must use `two-hdm-a` as the model_id (not `2hdm-a`). Spike script updated accordingly.
- **Status:** RESOLVED-IN-WS5 (S0.5 spike re-run). No fixture change needed; spike script and test files must use `two-hdm-a`.

### D4 — dark-su3 strict mode raised MatrixAcknowledgementMissing (RESOLVED by S0.5)

- **Class:** D-class (fixture authoring gap; chain_overrides lacked matrix_acknowledgement)
- **Model:** dark-su3
- **Expected (plan §1.1.3):** exit_code strict = 0 (acknowledgement intact per fixture chain_overrides)
- **Actual (pre-S0.5):** `MatrixAcknowledgementMissing` exception raised; exit code 4; strict spike failed
- **Evidence:** first spike run dark-su3 strict exception traceback
- **Missing blockers:** `SPHENO_NOT_REQUESTED`, `MG5_DARK_COLOR_TENSOR_WALL`, `CALCHEP_MDL_MISSING`, `DRAKE_SINGLE_SPECIES_ONLY`, `HIGGSTOOLS_SLHA_MISSING_BLOCKS`, `ANALYTIC_MODULE_MISSING`, `MATRIX_COVERAGE_GAP`
- **Fix:** Added `matrix_acknowledgement.accepted_blockers` to both `relic` and `dd` chain_overrides in fixture `constraints.yaml`
- **Status:** RESOLVED-IN-WS5 (S0.5). Post-S0.5 spike: dark-su3 strict exits 0.

---

## Additional Observations (for S1 expected YAML authoring)

### O1 — singlet-doublet dd active_chain.prereq_id is "ddcalc" not "maddm"

- **Class:** D-class (plan synthesis table §1.1.1 wrong)
- **Observable:** dd only
- **Actual:** `per_observable.dd.active_chain.prereq_id = "ddcalc"` (role: primary), with `maddm` in `ranked_alternatives`
- **Relic and id:** `maddm` (primary) as expected
- **Impact:** S1 expected YAML for singlet-doublet must set `dd.active_chain_prereq_id: ddcalc` (not `maddm`)
- **Status:** DOCUMENTED — S1 expected YAML must reflect actual spike output.

### O2 — dark-su3 per_candidate labels differ by observable

- **Class:** D-class (plan synthesis table §1.1.3 incomplete)
- **Observable:** all three, but labels differ
- **Actual:**
  - relic: `Omega_V_h2`, `Omega_Psi_h2`
  - dd: `sigma_SI_V`, `sigma_SI_Psi`
  - id: `Phi_id_V`, `Phi_id_Psi`
- **Plan §1.1.3 claimed:** "labels {Omega_V_h2, Omega_Psi_h2}" (only true for relic)
- **Impact:** S3 test `test_dsu3_per_candidate_pair_emitted` should assert names {V, Psi} (correct); label assertion must be per-observable or restricted to relic
- **Status:** DOCUMENTED — S3 test should not assert label set globally across all observables. Or assert only for relic. S1 expected YAML captures per-observable labels.

### O3 — dark-su3 id chain has no chain_override; active_chain is analytic_backend via normal routing

- **Class:** Informational
- **Actual:** dark-su3 `id` observable has `active_chain.matrix_acknowledgement_missing = false` (no `id` chain_override in fixture); analytic_backend is selected normally without override
- **Impact:** None on test plan; just clarifies routing mechanism.

### O4 — dark-su3-confining-synthetic per_observable status is "HARD_HALT" (not BLOCKED or PLACEHOLDER)

- **Class:** D3 resolution (plan said "per spike — BLOCKED, HARD_HALT, or PLACEHOLDER")
- **Actual:** `status = "HARD_HALT"` for all three observables
- **Impact:** S1 expected YAML must set `status: HARD_HALT` for all observables.

### O5 — two-hdm-a placements[0].exception_id is null (not set)

- **Class:** Informational
- **Actual:** Both placements have `exception_id: null` (halt_notice and signoff_prompt; no specific exception id)
- **Signoff prompt text:** `"## Required next steps (analytic exception sign-off)"` present at position `appendix`
- **Impact:** S5 test assertion for 2hdm-a signoff section header is correct.

### O6 — axis_snapshot field present in all 4 model reports

- **Class:** Informational (per critic R10)
- **Actual:** `axis_snapshot` key present in all spike JSON outputs with A1..A8 sub-fields
- **Impact:** S1 schema `axis_snapshot: presence_only` is correct.

---

## Resolved-by-S0.5 Section

The following two D-class items from the plan's pre-identified list are resolved:

1. **D1** — Fixture banner missing "25000"+"Planck target" → RESOLVED: banner rewritten verbatim from real registry.
2. **D2** — Synthetic model unregistered in fixture `constraints.yaml` → RESOLVED: `dark-su3-confining-synthetic` entry added.

Additional D-class items resolved during S0.5:
3. **D3** — Model ID mismatch (`2hdm-a` vs `two-hdm-a`) → RESOLVED: spike script corrected.
4. **D4** — dark-su3 strict mode MatrixAcknowledgementMissing → RESOLVED: matrix_acknowledgement added to fixture chain_overrides.

---

## Post-S0.5 Spike Summary

| Model | Mode | Verdict | Exit Code | OK? |
|---|---|---|---|---|
| singlet-doublet | default | CLEAR | 0 | YES |
| singlet-doublet | strict | CLEAR | 0 | YES |
| two-hdm-a | default | HALT_FOR_SIGNOFF | 0 | YES |
| two-hdm-a | strict | HALT_FOR_SIGNOFF | 5 | YES |
| dark-su3 | default | ROUTE_TO_ANALYTIC | 0 | YES |
| dark-su3 | strict | ROUTE_TO_ANALYTIC | 0 | YES |
| dark-su3-confining-synthetic | default | HARD_HALT | 0 | YES |
| dark-su3-confining-synthetic | strict | HARD_HALT | 6 | YES |

All 8 outputs valid. dsu3 banner contains REGRESSION-ANCHOR, 25000, Planck target.
Synthetic verdict=HARD_HALT, strict exit_code=6. Per plan S0.5 acceptance: PASS.

---

## R-class Findings

### R1 — Real _shared/analytic_exceptions.yaml uses list shape; fixture uses dict shape

- **Class:** R-class (registry-authoring; router consumer cannot read real registry without adapter)
- **Severity:** registry-authoring (per plan R9)
- **Model:** dark-su3
- **Expected:** real `_shared/analytic_exceptions.yaml` has `exceptions: [{id: dsu3-002, ...}]` (list with `id` field)
- **Actual (fixture):** `exceptions: {dsu3-002: {...}}` (dict keyed by id)
- **Router consumer:** `render.py:305` uses `.get("exceptions", {}).get(exception_id, {})` which silently returns `{}` against the real shape
- **Impact:** if router is pointed at real registry (not fixture), no banner would be emitted for dsu3
- **Status:** DEFERRED — out of WS5 scope. Documented in `WS5_FINDINGS.md`.
