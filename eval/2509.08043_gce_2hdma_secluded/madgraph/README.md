# MadGraph5 Setup — 2HDM+a VBF (arXiv:2509.08043)

## Bauer UFO Status

**Phase-1 delivery: vendored stub (BL7 route 2).**

The paper (Section 3.2.6) uses the Bauer 2HDM+a UFO from [Bauer:2017ota], but
gives no SHA, FeynRules version tag, or specific identifier (S0 E5=NOT_FOUND).

The vendored stub (`stub_ufo/parameters.py`) contains a frozen parameter-name list
matching the LHC DM WG 2HDM+a public specification. It exists solely to make
`bauer_ufo_check.py` CI-executable without a full MadGraph5 + FeynRules installation.

**PINNED_VERSION:** `Bauer-2HDM+a-stub-v1`
**PINNED_SHA:** computed from `sha256sum stub_ufo/parameters.py` after initial commit.
               Update `expected_ufo_params.py:PINNED_SHA` accordingly.

## Running the UFO Check

```bash
python eval/2509.08043_gce_2hdma_secluded/madgraph/bauer_ufo_check.py
```

This exits 0 without MadGraph5 installed. It:
1. Loads `stub_ufo/parameters.py` via `importlib.util.spec_from_file_location`
2. Asserts `EXPECTED_PARAMS ⊆ {p.name for p in all_parameters}`
3. Prints OK and the found/expected sets

## MG5 VBF Task — Phase-1 Deferral

**The MG5 VBF task is intentionally absent from YAML for Phase-1 delivery.**

The proc/param/run cards are present in `2hdma/` for reference and future use.
Re-add the YAML task in a follow-up PR once:
1. A real Bauer UFO tarball is vendored (replace stub)
2. The cross-section result is cached in `mg_cache.json`
3. A `file_contains` grader checks the cached banner file

## MG5 Version Target

MadGraph5_aMC@NLO >= 3.5.0 (latest stable as of 2025). The UFO should be
compatible with MG5 2.9.x and 3.x for LO generation.

## Running the Full MG5 Cross-Check (optional, when MG5 is installed)

```bash
python eval/2509.08043_gce_2hdma_secluded/madgraph/run_comparison.py
```

If `mg5_aMC` is not in PATH, the script prints a warning and exits 0 cleanly.

## Parameter Names (EXPECTED_PARAMS)

| UFO name | Physics meaning | BP-A value |
|---|---|---|
| MXD | DM Dirac fermion mass | 30 GeV |
| MHA | Heavy pseudoscalar mass m_A | 800 GeV |
| Mha | Light pseudoscalar mass m_a | 50 GeV |
| tanbeta | tan(beta), ratio of Higgs VEVs | 1.0 |
| sinp | sin(theta), pseudoscalar mixing angle | 0.09983 |
| yxd | DM Yukawa coupling g_chi | 0.5 |
| lam3 | Trilinear coupling lambda_3 | 1.0 (placeholder) |
| lamP1 | Portal coupling lambda'_1 | 1.0 (placeholder) |
