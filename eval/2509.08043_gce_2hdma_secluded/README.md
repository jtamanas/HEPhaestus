# arXiv:2509.08043 — GCE 2HDM+a / Secluded Hypercharge

**Paper:** "Testing Viability of Benchmark Dark Matter Models for the Galactic Center Excess"
Hu, Cesarotti, Slatyer (2025). arXiv:2509.08043.

> **A/B test status (2026-04-18):** Public Bauer 2HDM+a UFO is available and
> wired into `madgraph/`. However, MadDM does not natively compute the exact
> Bauer 1-loop σ_SI — expect `BLOCKED_CORRECTLY` on the six
> `t2_thdma_sigma_si_exact_*` tasks under `--runner claude` until a loop-σ_SI
> skill exists. Tree-level and secluded-hypercharge tasks should route to MG.

## Premise

This paper tests two DM models against the Galactic Center Excess (GCE):
1. **Secluded Hypercharge** — Dirac DM + dark photon Z', χχ → Z'Z' annihilation
2. **2HDM+a (Two-Higgs-Doublet Plus Axion)** — Dirac DM + pseudoscalar mediators (a, A)
   with mixing angle θ

The benchmark focuses on the 2HDM+a direct detection formula (Eq. 47/50): the
one-loop spin-independent cross-section mediated by the triangle diagram.

## Models

### 2HDM+a (PRIMARY benchmark)

- DM couplings: g_{χa} = y_χ cos θ, g_{χA} = y_χ sin θ (Eq. 41)
- Triangle amplitude: A = (m_A² − m_a²) sin²(2θ) g_χ² / (64π² m_h² m_a²)
- Loop function G(x, 0) = 2 ∫₀¹ dz z(1−z) / [(1−z) + xz²], where x = m_χ²/m_a²
- Full σ_SI (Eq. 47/50): σ_SI = (μ²/π) × [A_loop × G(x,0) × m_χ/V_H² × σ_mq]²

Anchor benchmark (BP-A): m_A=800, m_a=50, m_χ=30 GeV, θ=0.1, g_χ=0.5, tan β=1
→ σ_SI ≈ 2.37×10⁻⁴⁹ cm² (exact formula; paper's scaling approx gives 2.2×10⁻⁴⁹ cm²)

### Secluded Hypercharge

- χχ → Z'Z' via Eq. 24; g_D determined dynamically from relic density (Eq. 27)
- No explicit (m_χ, m_Z', g_D) anchor triplet in the paper (S0 E1=NOT_FOUND)
- `sigma_v_secluded` function is present but unpinned; no YAML grader for Phase-1

## Equation Numbering Note

The original plan labeled the primary σ_SI formula as "Eq. 44." This is incorrect.
In the paper, Eq. 44 is the **box diagram** (uses loop function F, subleading).
The **triangle diagram** amplitude is Eq. 47; the full σ_SI is Eq. 50.
All code and tests use the paper's numbering (Eq. 47/50). The spirit of the
plan's "Eq. 44 exact route vs Eq. 50 scaling" is preserved, but the labels now match the paper.

## What We Benchmark

| Task category | Equation | Tier |
|---|---|---|
| VBF proc_card setup | Bauer UFO proc | Tier 1 |
| Param card anchor | BP-A literals | Tier 1 |
| σ_SI exact at 6 BPs | Eq. 47/50 | Tier 2 |
| Scaling identities (6 axes) | Eq. 50 power laws | Tier 3 |
| G(x,0) threshold identity | G(0,0)=1 | Tier 3 |

## Figures → Equations

| Paper figure | Equation implemented | Status |
|---|---|---|
| Fig. 9 (σ_SI vs m_A) | Eq. 47/50 σ_SI | Implemented |
| Fig. 12 (γ-ray lines) | Eqs. 54-55 | Stub only, no grader (S0 E4=NOT_FOUND) |
| Figs. 6-8 (exclusion) | Eq. 24 σ_v | Function present, no grader (S0 E1=NOT_FOUND) |

## Scope Caveats (Phase-1)

- **No MadDM:** relic-density solver not implemented
- **No Delphes:** detector simulation not included
- **No exclusion-contour reproduction:** plot digitization not performed
- **MG5 VBF task deferred:** present in `madgraph/` as cards + stub UFO check;
  YAML task absent for Phase-1. Re-add in follow-up PR with cached `mg_cache.json`.
- **Secluded hypercharge tasks absent:** S0 E1=NOT_FOUND — paper has no explicit BP triplet
- **Gamma-ray line task absent:** S0 E4=NOT_FOUND — no numeric anchor in paper text

## Usage

```python
import sys
sys.path.insert(0, 'eval/2509.08043_gce_2hdma_secluded')

from cross_sections.sigma_si_2hdma_exact import sigma_SI_exact
from benchmarks.benchmark_points import thdma_anchor

bp = thdma_anchor()
sigma = sigma_SI_exact(**{k: v for k, v in bp.items() if k in
                          ['m_chi','m_a','m_A','theta','g_chi','tan_beta','sigma_mq']})
print(f"sigma_SI = {sigma:.3e} cm^2")  # expected ~2.37e-49
```

Run tests:
```
pytest eval/2509.08043_gce_2hdma_secluded/benchmarks/test_benchmarks.py -v
```

Run harness (paper-3 tasks):
```
python -m eval.harness.run --runner reference --tag paper-3
```

Verify Bauer UFO stub:
```
python eval/2509.08043_gce_2hdma_secluded/madgraph/bauer_ufo_check.py
```
