# MadGraph5 Setup — arXiv:2509.15121

## Process

```
pp > chi1+ chi20 j   (associated production: lightest chargino + second neutralino + jet)
```

## Pinned Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| UFO model | `nmssm` (MG5 built-in, no external download) | Plan A only |
| sqrt(s) | 14 TeV | paper context + HL-LHC standard |
| ebeam1 = ebeam2 | 7000 GeV | from sqrt(s) |
| PDF | NNPDF30_lo_as_0130 (LHAPDF ID 262000) | MG5 LO default |
| mu_R = mu_F | H_T / 2 (dynamical_scale_choice=3) | MG5 default for this class |
| Order | LO (tree-level only, no merging) | paper focus |
| nevents | 50000 | ~1% MC statistical uncertainty |
| Merging | None | inclusive matrix element |

## Benchmark Point

**BP1-3** is the primary MadGraph benchmark:
- Paper quoted: sigma(pp > chi1+ chi20 j) = 105.1 fb
- Parameters: M1=500, M2=5000, mu_eff=161.8, tan_beta=6.2, lambda=0.027, kappa=0.01243, vS=5992.59 GeV
- Param card: `param_card_BP1_3.dat` (hand-authored SLHA-1 from paper parameters)

## Offline Generation Procedure

1. Install MadGraph5 (pinned: latest stable release with built-in `nmssm` model)
2. Verify `nmssm` model availability: `mg5> import model nmssm`
3. Run: `python madgraph/run_mg5_production.py`
4. Output: `madgraph/cached_sigma_prod.json` (committed if within 5% of 105.1 fb)

## Plan A Only

No Plan B/C is documented. If MadGraph5 is unavailable or the built-in `nmssm`
model cannot be loaded, escalate to the project maintainer.

## Harness Integration

Per plan §18 (S18 precondition):
- The `t2_nmssm_sigma_prod_bp1_3` YAML task row is authored **only if**:
  1. `cached_sigma_prod.json` exists with key `BP1_3`
  2. `abs(sigma_cached - 105.1) / 105.1 < 0.05` (within 5% of paper)
- If the cache is absent: the YAML row does NOT exist. No `skipif` or `requires_tool`.
- The `nmssm_sigma_production` ref_fn reads the cache at call time; raises
  `FileNotFoundError` cleanly if cache is missing.

## Current Status

`cached_sigma_prod.json` is **absent** (MG5 not run during Phase-1).
The `t2_nmssm_sigma_prod_bp1_3` YAML row has NOT been authored.
