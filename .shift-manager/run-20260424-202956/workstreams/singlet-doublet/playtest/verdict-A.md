# Variant A Verdict — Singlet-Doublet Playtest

## VERDICT: PASS

```
VERDICT: PASS
BASELINE_USED: 0.292
HARDCODED_REFERENCE: 0.292
WORKSTREAM: singlet-doublet
VARIANT: A
```

---

## Section 1 — Gates G1–G9

| Gate | Status | Evidence |
|------|--------|----------|
| G1 | pass | relic.json absent pre-playtest; preplaytest dir exists |
| G2 | pass | omega_h2=0.292, hardcoded_reference=0.292, drift_flag=false |
| G3 | pass | XDG configs present; practitioner_script_B.md ZN→N done |
| G4 | pass | 0 broken-backup dirs in MadGraph PLUGIN dir |
| G5 | pass | wolframscript printed 'ok', exit=0 |
| G6 | pass | state_root=/tmp/sd-smoke-42332 |
| G7 | pass | env.json for sd-A and sd-B both valid |
| G8 | pass | git status --porcelain clean |
| G9 | warning (downgraded) | schema sentinel absent; schema_ready=0; G9 downgrades to warning per plan; Phase 1 proceeds |

**Overall gate evaluation: warning → proceed (per plan §Gate evaluator)**

---

## Section 2 — Ωh² Result vs 0.292 ± 0.01

| Metric | Value |
|--------|-------|
| Computed omega_h2 | 0.292 |
| BASELINE_USED (P2) | 0.292 |
| HARDCODED_REFERENCE | 0.292 |
| |Δ| vs baseline | 0.000 |
| Tolerance | 0.010 |
| Determinism check | PASS |
| Hardcoded regression | PASS |

**No drift flag.** The computed value matches the synthesis-locked reference exactly, confirming the MadDM + SLHA pipeline is deterministic at this benchmark point.

---

## Section 3 — Drift Flag

- drift_flag: **false**
- P2 captured value: 0.292 (matches hardcoded_reference 0.292 exactly)
- Phase 1 value: 0.292
- Conclusion: No drift between P2 capture and Phase 1 run. The 0.163→0.292 shift documented in sd_synthesis.md pre-dates the prep phase and was captured in P2 as the current baseline.

---

## Section 4 — Finding Count by Severity

| Severity | Count | Issue IDs |
|----------|-------|-----------|
| blocker | 0 | — |
| major | 2 | sd-A-003 (HEPPH_STATE_ROOT isolation), sd-A-004 (flock unavailable macOS) |
| minor | 3 | sd-A-001 (mg5 --version), sd-A-002 (SARAH Package.m), sd-A-006 (Unicode glyphs) |
| warning | 2 | sd-A-005 (MadDM validation warning), sd-A-007 (SARAH model name unused in cached path) |

**No blockers.** The two major issues (sd-A-003, sd-A-004) are infrastructure/tool-driver issues that did not block the run — workarounds were applied (direct SLHA path usage; flock-less execution). They are actionable for fix-loop.

---

## Section 5 — Six-Criterion Table

| Criterion | Result | Evidence |
|-----------|--------|----------|
| C1: summary.json parseable; ran contains "relic"; relic.json.status=="ok" | **PASS** | summary.json valid per schema; ran=["relic"]; status="ok" |
| C2: omega_h2 finite in [0.10, 0.40] | **PASS** | 0.292 ∈ [0.10, 0.40] |
| C3: omega_h2 within ±0.01 of BASELINE_USED | **PASS** | |0.292 − 0.292| = 0.000 ≤ 0.010; HARDCODED_REGRESSION also PASS |
| C4: summary.{pdf,png} exist, >1KB | **PASS** | PDF=31359 bytes, PNG=28210 bytes |
| C5: singlet_doublet_spec.yaml exists; validate_spec.py exits 0 | **PASS** | validate_spec.py → {"status":"valid"} exit=0 |
| C6: Wallclock ≤ 45 min | **PASS** | 5.4 min wall time |

---

## Proceed/No-Go for Variant B

**Proceed.** Variant A is a clean PASS on all 6 criteria with no blockers. The two major findings (sd-A-003, sd-A-004) are infrastructure issues that require fix-loop attention before cold-start runs, but do not affect Variant B in isolation. Variant B should proceed in parallel with the same SLHA/UFO path workarounds.

**Fix-loop recommendations (Phase 2 triggers):**
- sd-A-003 (`expected_fix_scope: tool_driver`): run_spheno.py should fall back to config.json model paths when HEPPH_STATE_ROOT is set but model is absent from the playtest state root, OR the playtest setup should symlink/copy the model state into the per-variant state root.
- sd-A-004 (`expected_fix_scope: fixture`): Replace flock-based locking with a macOS-compatible alternative (e.g., Python filelock, or detect flock absence and fall back to a cooperative Python lock file).
