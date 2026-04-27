# Dark SU(3) Playtest Fixtures

WS-3 synthetic fixture set for the `/dark-matter-constraints` router playtest.
All files are **synthetic** — they encode beliefs about producer output formats
and routing behavior, not real physics results.

## Distinct-categories disclaimer

The numeric values in `canned/` are **fixture inputs** driving the router's
rel-diff arithmetic. They are **not** gate thresholds asserting "the answer
must be X." The `golden/` structural specs (`expected_blockers_v1.json`,
`expected_table_structure_v1.json`) define required code presence, column
presence, and row counts — also distinct from numeric thresholds. This
distinction is required by `briefs/ROUTING_LENS.md`.

## Spectrum points

| Point | m_χ | m_med | Partner | Γ/m_med | Role |
|-------|-----|-------|---------|---------|------|
| A | 100 GeV | 199 GeV | 105 GeV | 0.005 | On-resonance; exercises Steps 3+4+5 and all DRAKE branches |
| B | 100 GeV | 230 GeV | none | 0.005 | Off-resonance control; verifies no over-invocation |

Point A: Δ/(2·m_χ) = |199−200|/200 = 0.005 (inside 5% Step-5 window).
Point A: Γ/m_med = 0.005 documents this IS a physically-narrow resonance, not
just inside the heuristic window.
Point B: Δ/(2·m_χ) = |230−200|/200 = 0.15 (well outside 5% and 10% windows).

## Directory structure

```
tests/fixtures/dark_su3_playtest/
  README.md                          # this file
  ufo/darkSU3/                       # empty-dir sentinel (README.md + .gitkeep)
  configs/
    config_pointA_configured.yaml    # Point A, DRAKE configured
    config_pointA_missing.yaml       # Point A, DRAKE missing
    config_pointA_activation_required.yaml
    config_pointA_unset.yaml         # Point A, no drake_path key (Branch 1)
    config_pointB.yaml               # Point B, off-resonance
  specs/
    spec_pointA.yaml                 # dm_candidate for Point A
    spec_pointB.yaml                 # dm_candidate for Point B
  canned/
    pointA/
      maddm_stdout.txt               # Omegah2=0.135 (patched from WS-1 source)
      relic.json                     # micrOMEGAs omega_h2=0.118 (14.4% rel-diff vs MadDM)
      annihilation.json              # micrOMEGAs sigma_v_zero
      summary.json                   # micrOMEGAs sigma_SI/sigma_SD
      check_prereqs_ok.json          # check_prereqs canned OK response
      detect_drake_configured.json   # detect_drake "configured"
      detect_drake_missing.json      # detect_drake "missing"
      detect_drake_activation_required.json
    pointB/
      maddm_stdout.txt               # Omegah2=0.292 (WS-1 source value)
      check_prereqs_ok.json          # check_prereqs canned OK response
  golden/
    expected_step_trace_v1.json      # Expected helper invocation sequences (HARD gate spec)
    expected_blockers_v1.json        # Expected blocker codes per scenario (HARD gate spec)
    expected_table_structure_v1.json # Required table rows/columns (HARD gate spec)
    expected_merged_table_pointA.md  # Human diff reference (NOT verbatim gate)
    expected_merged_table_pointB.md  # Human diff reference (NOT verbatim gate)
  negative_control/
    README.md                        # Documents the 4 sabotages
    SKILL.md.broken_NC-1             # extract_field --schema-version arg removed
    SKILL.md.broken_NC-2             # sigma_v_zero extract invocation removed
    SKILL.md.broken_NC-3             # CROSSCHECK_DISAGREEMENT + "do NOT silently average" removed
    SKILL.md.broken_NC-4             # --spec flag removed from invocation section
```

## WS-1 reuse

Point A's `canned/pointA/maddm_stdout.txt` is a sed-patched copy of
`plugins/hep-ph-toolkit/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt`.
The only change is `Omegah2 = 2.92e-01` → `Omegah2 = 1.35e-01` (to produce
the 14.4% rel-diff with micrOMEGAs 0.118). Field names and all other values
are retained from the WS-1 source. Point B retains the WS-1 value verbatim.
