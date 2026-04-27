# Paper 1 Numerics — arXiv:2601.13147

Extracted from HTML version at https://arxiv.org/html/2601.13147v3

## Benchmark Point Table (from Table 1)

| BP | m_h2 (GeV) | sin_theta | lambda_hs | lambda_s | mu_3 (GeV) | m_chi (GeV) | g_chi |
|----|------------|-----------|-----------|----------|------------|-------------|-------|
| BP1 | 200.0 | 0.001 | 2.2 | 3.38 | -20.0 | 222.0 | 0.57 |
| BP2 | 200.0 | 0.001 | 2.4 | 3.1 | 100.0 | 242.0 | 0.56 |
| BP3 | 200.0 | 0.001 | 1.9 | 2.95 | -100.0 | 180.0 | 0.76 |
| BP4 | 200.0 | 0.001 | 4.3 | 4.5 | 20.0 | 310.0 | 0.87 |
| BP5 | 350.0 | 0.001 | 4.45 | 4.0 | 100.0 | 380.0 | 0.73 |
| BP6 | 350.0 | 0.001 | 4.0 | 4.1 | -100.0 | 300.0 | 0.87 |
| BP7 | 350.0 | 0.07 | 3.8 | 4.8 | 20.0 | 167.4 | 0.03 |
| BP8 | 200.0 | 0.13 | 2.02 | 3.0 | 20.0 | 94.75 | 0.02 |
| BP9 | 70.0 | 0.002 | 0.8 | 0.73 | 20.0 | 78.0 | 0.34 |

## BP9 Parameters (required by plan S-01)

| Parameter | Value |
|-----------|-------|
| m_chi | 78.0 |
| g_chi | 0.34 |
| sin_theta | 0.002 |
| lambda_s | 0.73 |
| mu_3 | 20.0 |

## VEV

Paper states v ≈ 246 GeV. We use V_H = 246.22 GeV (PDG, same as 2506.19062 constants).

## Equations

### Equation 15 — Vacuum Stability (LHS >= 0 for all three conditions)

Three conditions:
1. lambda_h >= 0  (LHS: lambda_h)
2. lambda_s >= 0  (LHS: lambda_s)
3. lambda_hs + 2*sqrt(lambda_h * lambda_s) >= 0  (LHS: lambda_hs + 2*sqrt(lambda_h * lambda_s))

For the benchmark pin tests, we use the binding constraint (condition 3):
  vacuum_stability_lhs(lambda_h, lambda_s, lambda_hs) = lambda_hs + 2*sqrt(lambda_h * lambda_s)

### Equation 16 — Perturbative Unitarity

Binding condition (most restrictive eigenvalue):
  perturbative_unitarity_lhs(lambda_h, lambda_s, lambda_hs) =
    8*pi - |3*lambda_h + 2*lambda_s + sqrt((3*lambda_h - 2*lambda_s)**2 + 2*lambda_hs**2)|

(Positive means the constraint is satisfied.)

### Equation 18 — h2 production cross section

  sigma(pp -> h2) = sin^2(theta) * sigma_SM(m_h2)

Uses sin^2(theta) (confirmed from paper text).

### f_TG Treatment

Standard (2/9) * f_TG form:
  f_N = f_u + f_d + f_s + (2/9)*(1 - f_u - f_d - f_s)

where the (2/9) factor comes from the gluon loop contribution to heavy quark form factors.
