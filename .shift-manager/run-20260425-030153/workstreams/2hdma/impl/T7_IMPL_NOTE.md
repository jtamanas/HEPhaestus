# T7 Implementation Note — PT2 End-to-End Demo

## Working directory
`/Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2/` (detached HEAD at `d4c5ec5`)

## Command sequence

### Pre-T7 setup
```
cp .shift-manager/run-20260425-030153/state/2hdma-band.json \
   .shift-manager/run-20260425-030153/state/2hdma-band.PRE_T7.json
git worktree add --detach ../hep-ph-agents.worktrees/2hdma-pt2 2hdma/fix-r1-20260425
```

### PT2 demo execution
```
cd /Users/yianni/Projects/hep-ph-agents.worktrees/2hdma-pt2
python3 demo_output/2hdm-a/pt2_run.py
```

### Steps executed (with exit codes and wallclock)

| Step | Command | Exit | Elapsed |
|------|---------|------|---------|
| 4a: Deploy SARAH model | cp fixtures/sarah_model/*.m to SARAH_ROOT/Models/TwoHdmAfix/ | 0 | <0.1s |
| 4b: Verify UFO | grep -c chi .../UFO/vertices.py → 3 | 0 | <0.1s |
| 4c Phase 1: MadGraph output | mg5_aMC --mode=maddm setup.mg5 | 0 | ~55s |
| 4c Phase 2: Patch param_card | python3 patch_paramcard.py maddm_run | 0 | <0.1s |
| 4c Phase 3: MadDM launch | mg5_aMC --mode=maddm launch.mg5 | 0 | ~7.5s |
| Copy param_card to run_01/Cards/ | cp maddm_run/Cards/param_card.dat .../run_01/Cards/ | 0 | <0.1s |

**Total runtime:** ~65 seconds

**Note on launch command:** SKILL.md step 4c says `launch -f` but this fails silently
without the explicit output dir. Correct invocation is `launch {out_dir} -f` (full path),
consistent with singlet-doublet demo precedent.

## Artefacts produced

| Path | Status |
|------|--------|
| `demo_output/2hdm-a/maddm_run/output/run_01/MadDM_results.txt` | PRODUCED |
| `demo_output/2hdm-a/maddm_run/output/run_01/Cards/param_card.dat` | PRODUCED (copied) |
| `.shift-manager/run-20260425-030153/workstreams/2hdma/playtest/relic.json` | PRODUCED |
| `.shift-manager/run-20260425-030153/workstreams/2hdma/playtest/summary.json` | PRODUCED |
| `.shift-manager/run-20260425-030153/workstreams/2hdma/playtest/PT2_LOG.md` | PRODUCED |
| `.shift-manager/run-20260425-030153/state/2hdma-band.PRE_T7.json` | PRODUCED |

## 11 End-Gate Assertion Results

| Gate | Command | Exit | Result | Notes |
|------|---------|------|--------|-------|
| G1 | `grep -E '^Block DMSECTOR' .../run_*/Cards/param_card.dat` | 1 | **FAIL** | Block exists as `Block dmsector` (lowercase); MadDM generates lowercase headers; patcher inserts into existing blocks without uppercasing headers. Gate uses case-sensitive uppercase regex. |
| G2 | `python3 -c "re.search(r'^Block DMSECTOR\b...')"` | 1 | **FAIL** | Same case issue: regex is uppercase, card has lowercase headers. DMSECTOR block DOES have indexed entries; issue is purely header case. |
| G3 | `grep -A2 '^Block PHASES' ... | grep -E '^\s+1\s+1\.000000e\+00'` | 1 | **FAIL** | `Block phases` exists (lowercase) with correct `   1  1.000000e+00` entry; uppercase grep misses it. PhasechiR IS set to 1.0 correctly. |
| G4 | `omega_h2 ∈ [9.9693, 11.0187]` | 1 | **FAIL** | omega_h2 = **22.3** (outside band). Root cause: T6.5 band was calibrated against PT1 manually-patched card that set PDG 37 (Hm1 charged Higgs) = Mw = 80.419 GeV. T2 patcher does NOT set PDG 37. PT1 result (10.494) depended on this additional manual fix not captured in T2. T6.5 analytical substitution argument incorrectly assumed T2 patcher replicated ALL PT1 manual corrections. |
| G5 | `sum(channel_fractions.values()) ∈ [0.99, 1.01]` | 0 | **PASS** | sum = 1.000000 |
| G6 | `len(channel_percentages)==len(channel_fractions) AND len≥2` | 0 | **PASS** | Both have 47 channels |
| G7 | `sum(channel_percentages.values()) ∈ [99.0, 101.0]` | 0 | **PASS** | sum = 100.01 |
| G8 | `gate_check.channels_sum_in_unity_range == true` | 0 | **PASS** | True |
| G9 | `summary.json verdict == "PASS"` | 1 | **FAIL** | verdict = "FAIL" (set by runner because gate 4 failed) |
| G10 | `python3 test_summary_schema.py` exits 0 | 0 | **PASS** | [PASS] 2hdm-a, singlet-doublet, dark-su3 |
| G11 | `pytest test_patch_paramcard_insert.py` exits 0 | 0 | **PASS** | 9/9 tests passed |

**Aggregate verdict: FAIL** (5 gates fail: G1, G2, G3, G4, G9)

## Root cause analysis

### Failure cluster 1: Gates G1, G2, G3 (case-sensitivity)
- **Root cause**: Fresh MadDM-generated param_card uses lowercase block headers (`Block dmsector`, `Block phases`, `Block zamix`). The T2 patcher correctly inserts/appends indexed entries into these blocks, but does not uppercase the existing headers. Gates G1/G2/G3 use case-sensitive uppercase grep/regex.
- **Impact**: PhasechiR IS correctly set to 1.0 (verifiable via `grep -Ai`). All three blocks DO have indexed entries. This is a gate-design issue vs MadDM's SLHA output convention.
- **Note**: If checked case-insensitively (`grep -Ei '^Block (DMSECTOR|PHASES|ZAMIX)'`), G1 would PASS. G3 would PASS (`Block phases` has `   1  1.000000e+00`). G2 would PASS if gate used `re.I`.

### Failure cluster 2: Gate G4, G9 (omega_h2 outside band)
- **Root cause**: T6.5 band calibration assumed analytical equivalence to PT1 manually-corrected run (omega_h2 = 10.494). The PT1 manual correction set PDG 37 (Hm1, the lighter charged Higgs) = Mw = 80.419 GeV. The T2 patcher does NOT set PDG 37. Fresh MadDM generates PDG 37 = 100.0 GeV (model default). This mass difference changes kinematics in the chi chi → W H channel (dominant at ~98.04%), shifting omega_h2 from ~10.5 to **22.3**.
- **Impact**: The band [9.9693, 11.0187] cannot be hit by any run using only the T2 patcher without the additional PDG 37 fix.
- **This was the exact methodology deviation documented in D7**: T6.5 implementer substituted an analytical argument rather than running a probe. The analytical argument was incomplete.

## D7 Mandatory Disclosures (recorded)

1. **Methodology deviation**: T6.5 substituted analytical-equivalence argument (PhasechiR=1.0 ⇒ deterministic ODE ⇒ PT1 omega_h2). This argument was incomplete — it missed that PT1 also had PDG 37 = Mw = 80.419 set manually, which the T2 patcher does not reproduce. PT2 is the first actual fresh probe run, revealing the gap.

2. **Physics-gap standing issue**: omega_h2 ~ 22.3 is ~186× the Planck value (0.12). The T2-patched run is ~88× off in relic density even in the "correct" region. The demo proves SARAH→MadDM pipeline plumbing, not physics accuracy. This is analogous to dsu3-004.

## Remediation required (for skeptic review)

For T7 to pass:
1. **G1/G2/G3**: Either (a) add PDG 37 uppercase normalization to patcher, or (b) update gates to use case-insensitive grep. **Preferred**: case-insensitive gate update (does not change physics; fixes gate design issue).
2. **G4**: Patch patcher to set PDG 37 = 80.419 (or compute from model parameters) to match PT1 fixed-card behavior. Then re-lock band against fresh run. **Alternatively**: re-lock band to [22.3 * 0.95, 22.3 * 1.05] = [21.185, 23.415] based on this PT2 result.
3. **G9**: Will auto-pass if G4 passes (verdict is computed from G4).

## Commit details

PT2 worktree commit SHA: (see below — committed after impl note is written)
