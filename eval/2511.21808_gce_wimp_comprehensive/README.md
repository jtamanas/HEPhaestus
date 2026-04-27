# arXiv:2511.21808 — Comprehensive WIMP Study of the Fermi-LAT GCE

**Title:** A Comprehensive Study of WIMP Models Explaining the Fermi-LAT Galactic Center Excess  
**Authors:** Chuiyang Kong, Mattia Di Mauro  
**arXiv:** https://arxiv.org/abs/2511.21808  
**Date:** 2025-11-26 (revised 2026-04-04)

> **A/B test status (2026-04-18):** UFOs for these portals are not advertised
> public per our research; expect `BLOCKED_CORRECTLY` on most observable
> tier-2s under `--runner claude` until UFO-generation support lands.
> Closed-form tier-2/3 algebra tasks pass on the reference runner.

---

## Premise

This paper performs a comprehensive study of WIMP dark matter models that can explain the Fermi-LAT
Galactic Center Excess (GCE) — an excess of GeV-scale gamma rays from the inner Galaxy consistent
with DM annihilation. The paper studies five portal types:

1. **U(1) Lμ−Le** — Z' mediator coupling to muon and electron lepton numbers
2. **U(1) Le−Lτ** — Z' mediator coupling to electron and tau lepton numbers
3. **U(1) Lμ−Lτ** — Z' mediator coupling to muon and tau lepton numbers
4. **U(1) B−L** — Z' mediator coupling to baryon minus lepton number (quarks + leptons)
5. **Higgs portal (scalar DM)** — scalar DM coupled via the SM Higgs

For each portal, the paper determines best-fit DM mass and annihilation cross-section from a
morphological fit to the GCE spectrum, and checks compatibility with direct detection constraints.

---

## What We Benchmark

### Analytically Evaluable Equations (Python Implementations)

| Equation (v1 numbering) | Description | Module |
|---|---|---|
| Eq. 6–8 | Higgs-portal scalar σv (off-funnel + BW) | `cross_sections/sigma_v_higgs.py` |
| Eq. 9 | Higgs-portal σ_SI | `cross_sections/sigma_si_higgs.py` |
| Eq. 15 ("Eq. 27") | Z' decay width to SM fermions | `cross_sections/z_prime_decays.py` |
| Eq. 16 ("Eq. 28") | Z' decay width to DM pair | `cross_sections/z_prime_decays.py` |
| Eq. 17 ("Eq. 29") | Z' decay width to neutrinos | `cross_sections/z_prime_decays.py` |
| Eq. 25 ("Eq. 38") | σv for DM annihilation via Z' (Taylor + BW) | `cross_sections/sigma_v_zp.py` |
| Eq. 15 ("Eq. 39") | σ_SI via Z' exchange (valence quark counting) | `cross_sections/sigma_si_zp.py` |
| Eq. 17 ("Eq. 44") | σ_SD via Z' exchange (axial couplings) | `cross_sections/sigma_sd_zp.py` |

Note: Plan-final.md uses v1 equation numbers which differ from v2. Physics is identical.
Code docstrings cite v1 numbers to match the plan spec.

### MadGraph Comparison Targets

MadGraph B-L cross-check: **Plan C** — not available in v1 (no UFO vendored).
The MG generator script is present and will emit tasks if a future UFO is vendored.

---

## Benchmark Points — Table 2 (Portal Best Fits)

From paper Table 2 (m_Zp = 120 GeV, g_chi = 1.0, Dirac DM):

| Portal | m_DM [GeV] | ⟨σv⟩ [cm³/s] |
|--------|-----------|--------------|
| Lμ−Le  | 44.1      | 7.58e-26     |
| Le−Lτ  | 19.2      | 3.03e-26     |
| Lμ−Lτ  | 20.5      | 3.76e-26     |
| B−L    | 37.5      | 4.67e-26     |

Table-2 entries appear in **Tier-3 self-consistency tests only** (inversion round-trips).
They are NOT external validation anchors.

---

## Tier-2 vs Tier-3 Policy

| Tier | Tests | What They Validate |
|------|-------|-------------------|
| 1 | 1 | MadGraph proc_card setup (Higgs portal scalar DMScalar UFO) |
| 2 | 9 | First-principles hand-calc pins at our chosen benchmark points |
| 3 | 10 | Table-2 inversion round-trips (self-consistency), charge sum rules, thermal average convention |

**Table-2 entries are Tier-3 self-consistency only.** The Tier-3 round-trip tests verify
that our closed-form σv formula can invert to reproduce the quoted ⟨σv⟩ from Table 2 when
we solve for g_Zp. This does NOT validate that our formula matches the paper's — it only
checks our own inverter is consistent.

---

## Figures-to-Equations Map

| Figure | Content | Key Equation |
|--------|---------|-------------|
| Fig. 2 | GCE morphology fit for Lμ−Le | σv formula (Eq. 25/plan-38) |
| Fig. 7 | Direct detection comparison | σ_SI (Eq. 15/plan-39) |
| Fig. 9 | B-L portal constraints | σ_SI^{B-L} with f_p=f_n=g_Zp (valence) |
| Table 2 | Best-fit (m_DM, ⟨σv⟩) per portal | Eq. 25 at GCE best fit |

---

## Charge Structure (Paper §0.3 / Phase-0.5 Decision D3)

The SI cross section for vector Z' exchange uses **valence quark counting** (Case A):

```
f_p = 2 Q_V[u] g_Zp + Q_V[d] g_Zp   (proton = 2u + 1d valence)
f_n = Q_V[u] g_Zp + 2 Q_V[d] g_Zp   (neutron = 1u + 2d valence)
```

For B-L (Q_V[q] = 1/3 for all quarks): **f_p = f_n = g_Zp** (isoscalar, equal).
For Lμ-Le (Q_V[q] = 0 for all quarks): **f_p = f_n = 0** (exact zero, by arithmetic).
