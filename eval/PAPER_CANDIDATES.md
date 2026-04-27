# Paper candidates for the eval suite

Status of every hep-ph paper we've considered for the benchmark suite. Updated as
new candidates are surfaced and verified.

## Selection bar (current)

Per `METHODOLOGY.md`, a paper is accepted only if it satisfies AT LEAST one of:

1. **Stated benchmark parameter points + numerical observables.** Specific
   table/figure-caption values like `BP1: m_DM=200 GeV, λ=0.5, σ_SI=5.1×10⁻⁴⁵ cm²`.
2. **Two independent routes to the same quantity** (analytical formula AND
   mixing-matrix expression, OR EFT and UV matching).
3. **Exact algebraic identities / blind spots / sum rules** holding for ALL
   parameter values.
4. **Validation statement** like "we reproduced X" or "agrees with
   micrOMEGAs/MadDM to 1%".

Plus tool-fit: calculations reproducible with **MadGraph5_aMC@NLO and/or MadDM**;
public UFO model strongly preferred.

Reject papers that present results only as scatter/contour plots with no anchor
points, or that depend on tools outside MadGraph/MadDM with no UFO release.

## Accepted

| arXiv | Short title | Why it passed | Notes |
|-------|-------------|---------------|-------|
| [2506.19062](https://arxiv.org/abs/2506.19062) | WIMPs Below the Radar (Arcadi & Profumo) | Reference paper. ~10 BPs, σ_SI/σ_SD pinned, blind-spot identities. | Already implemented in `2506.19062_wimps_blind_spots/`. |
| [2601.13147](https://arxiv.org/abs/2601.13147) | Singlet fermion DM with scalar portal (Das, Niyogi, Srivastava) | 9 fully-pinned BPs with σ_SI numbers; blind-spot factor (1/m_h₂² − 1/m_h₁²); GW/EWPT extension adds ~12 more pinned equations. | MG used (no MadDM); UFO needs FeynRules build. Relevance 8/10. |
| [2603.23040](https://arxiv.org/abs/2603.23040) | Light fermionic DM in scotogenic inverse seesaw (Liang et al.) | 3 BPs with full ILC cutflow; **MadDM used directly** with explicit "matches MadDM" validation; isospin σ_p^SD ≈ σ_n^SD identity. | UFO not published; per-BP σ_SI/σ_SD live in figures. Relevance 7/10. |
| [2509.08043](https://arxiv.org/abs/2509.08043) | GCE benchmark DM models (Hu, Cesarotti, Slatyer) | **Eq. 50 closed-form σ_SI scaling** with explicit anchor 2.2×10⁻⁴⁹ cm² × 5-parameter scaling; Eq. 27 thermal relic anchor 4.4×10⁻²⁶ cm³/s; secluded hypercharge + 2HDM+a model classes. | Uses **public Bauer 2HDM+a UFO** (Bauer:2017ota). MadGraph 5 v2.9.21. No MadDM (analytic relic). Relevance 8/10. |
| [2511.21808](https://arxiv.org/abs/2511.21808) | Comprehensive WIMP study of Fermi-LAT GCE | ~10 portal classes with FeynRules+UFO+CalcHEP+**MadDM**+micrOMEGAs both used; Table 2 has 4 BPs (mDM, ⟨σv⟩, χ²) for U(1)_Li−Lj + B−L; 14 closed-form equations across portals. | UFOs implemented but not advertised public. No quantitative MadDM↔micrOMEGAs validation statement. Relevance 7/10. Scope eval to 4 Table-2 models. |
| [2509.15121](https://arxiv.org/abs/2509.15121) | Shedding Light on DM at the LHC with ML (NMSSM) | Tables 7-8 with full BPs (σ_DD^SI=1.3×10⁻⁴⁸ cm² for BP1-3, 4.2×10⁻⁴⁸ cm² for BP9-3, Ωh²=0.1 anchored); **Eq. 7 NMSSM bino/higgsino blind-spot identity** confirmed exact: (m_χ + g₁²v²/(M₁−m_χ))/(μ_eff sin 2β) ≃ 1; production σ tabulated (105.1 fb). | MadGraph + NMSSM UFO; micrOMEGAs/NMSSMTools for DM observables (no MadDM). Relevance 7/10. |

## WEAK — promote with caveats / graphical-tier candidates

These passed *some* criteria but failed at least one. They become full ACCEPTs
under loosened criteria (graphical extraction, dropping the "MG/MadDM in the
paper" requirement, or accepting UFO build cost).

| arXiv | Short title | Verdict | Strengths | Caveats / unlock condition |
|-------|-------------|---------|-----------|----------------------------|
| [2510.18564](https://arxiv.org/abs/2510.18564) | Muonic Portal to Vector DM | WEAK 6/10 | **Public UFO on HEPMDB** (1025.0355 UFO; 0322.0335 CalcHEP); 15+ closed-form (g-2)_μ equations (Eqs. 20-45); Table 2 has 3 collider BPs with cross-sections. | σ_SI/Ωh²/⟨σv⟩ NOT tabulated per BP — only contours. No MadDM. (a) graphical OR (c) accept g-2 side as a standalone eval. |
| [2510.23771](https://arxiv.org/abs/2510.23771) | WIMP Shadows: secluded DM in 3 BSM scenarios | WEAK 6/10 | **MadDM 3.2 used directly**; 4 clean closed-form eqs (⟨σv⟩A'A', σ_SI, relic, kinetic ε threshold) across 3 models; WIMP-vs-secluded Boltzmann split is a real two-route check (Fig. 2 ≤1% agreement). | UFO not publicly released. Inline numerics only (no per-BP table); Model III has no benchmark numerics. (a) accept figure digitization. |
| [2512.03133](https://arxiv.org/abs/2512.03133) | Thermal Relic Encyclopedia (Hooper, Krnjaic, Trickle, Wang) | WEAK 5/10 | 20-30+ closed-form equations across 4 systematic spin combinations (S=0/½ DM × S=0/1 mediator); Table 2 fully-numeric nucleon coefficients (f_Tu, f_Td, f_Ts, f_TG, Δu, Δd, Δs); could anchor a distinct algebraic-identity eval class (Ward identities, decoupling limits, cross-class consistency). | No paper-stated numerical anchors per BP — formulas-only. No public UFO. Re-frame as "implement Eq. N + verify symbolic limits + cross-checks across model classes" rather than BP pinning. |
| [2602.18051](https://arxiv.org/abs/2602.18051) | Dark photon mediated inelastic DM | WEAK 5/10 | BP1-BP4 in Appendix A with full collider observables (cτ, σ, FASER counts) — pinnable. Eq. 24 (Γ(χ2→χ1ℓℓ̄)) is clean closed form. MG5 v3.5.10 + FeynRules-2.3 UFO (custom). | DM observables (Ωh²/σ_SI/σ_SD) NOT tabulated per BP, only in scatter plots. UFO not confirmed public. micrOMEGAs not MadDM. Useful as an LLP/FASER mini-eval, not a full DM eval. |

## Rejected — revisit when criteria loosen

These papers were rejected in 2026-04-18 verification rounds under the strict
bar. Unlock conditions: (a) introduce graphical-benchmark extraction (digitizing
exclusion contours), (b) drop the "MG/MadDM in the paper" requirement and accept
UFO build cost ourselves, or (c) include papers with input-only BP tables and
generate observables ourselves with a ported pipeline.

### Round 1 rejects

| arXiv | Short title | Verdict | Why rejected | Unlock condition |
|-------|-------------|---------|--------------|------------------|
| [2603.18158](https://arxiv.org/abs/2603.18158) | 2-component DM in Type-I 2HDM | REJECT 3/10 | Table 1 lists BP inputs but no predicted Ωh², σ_SI, BR_inv at the points. Observables in scatter plots. SARAH/SPheno/micrOMEGAs only. No UFO. | (a) graphical, OR (c) input-only-BPs + we port ourselves. |
| [2602.17764](https://arxiv.org/abs/2602.17764) | Generalized minimal EW DM (Sommerfeld + bound states) | REJECT 3/10 | All numerics in Figs. 7-13. σ_SI imported from another paper (Bottaro et al.). No MG/MadDM. | (a) graphical, AND we accept Sommerfeld outside MadDM scope. |
| [2603.16863](https://arxiv.org/abs/2603.16863) | Vector-portal freeze-in DM | REJECT 3/10 | Three BPs but observables are figure-only. Uses FREEZEIN + micrOMEGAs (MadDM doesn't natively support freeze-in). No UFO. | (a) graphical, AND MadDM 3.2+ freeze-in mode is in scope. |
| [2604.07618](https://arxiv.org/abs/2604.07618) | Multi-component minimal model (Ghorbani) | REJECT 3/10 | No BP tables; scan + plots only. Paper has typos ("EXNON1T") suggesting weak editing. | (a) + we contact author for benchmark numbers. |
| [2604.06929](https://arxiv.org/abs/2604.06929) | Inelastic DM with scalar mediator | REJECT 3/10 | Curves only. Self-validation is explicit O(1), not 1%. No MG mention. | Companion paper [2505.04290](https://arxiv.org/abs/2505.04290) (same authors) may be a better candidate — investigate. |
| [2602.19958](https://arxiv.org/abs/2602.19958) | Leptophilic DM + neutron star heating | REJECT 4/10 | Has Eq. 38 blind-spot identity (criterion 3) and Table 1 NS profiles (criterion 1) but half the paper is NS astro outside MG/MadDM scope. No tool validation. | (b) loosen tool criterion + we accept astro side as out-of-scope. |
| [2601.02503](https://arxiv.org/abs/2601.02503) | 3+1HDM scotogenic two-loop ν mass | REJECT 3/10 | SARAH→SPheno→micrOMEGAs pipeline. No blind-spot algebra. No MG/MadDM. Multi-component DM with three candidates makes Python-pinning brittle. | Probably never — model complexity is too high vs eval value. |
| [2509.14869](https://arxiv.org/abs/2509.14869) | φSMEFT + VLQ monojet/DD | REJECT 4/10 | Good EFT↔UV matching equations (Eqs. 4) and Table 1-2 polynomial coefficients. But no UFO; observables are figure-only; relic and σ_SI not tabulated. | (c) input-only-BPs + we port. The matching equations alone could be a unit-test mini-module. |
| [2508.06040](https://arxiv.org/abs/2508.06040) | Scalar DM co-scattering monophoton | REJECT 3/10 | Two BPs (BP1, BP2) but no pinned observables (no σ, no Γ, no BR, no event yields). No public UFO. No validation statement. | (a) graphical + we accept reproducing Ωh²=0.12 contour as a scan-style test. |

### Round 2 rejects (2026-04-18 second wave)

| arXiv | Short title | Verdict | Why rejected | Unlock condition |
|-------|-------------|---------|--------------|------------------|
| [2604.02604](https://arxiv.org/abs/2604.02604) | Spin-2 portal freeze-in DM at LHC + ML | REJECT 4/10 | No BP tables; observables only in exclusion contours. UFO not public. Validation statement present (10% agreement) but no pinned per-BP numerics. | (a) graphical + UFO rebuild from Lagrangian. |
| [2603.11233](https://arxiv.org/abs/2603.11233) | Vector Higgs-portal DM, EFT vs UV | REJECT 3/10 | Zero numbered tables. Validation statement "few-percent" but qualitative single sentence. All observables in (m_V, λ_HS) contour plots. No UFO. | (a) graphical + UFO build from FeynRules. |
| [2602.06681](https://arxiv.org/abs/2602.06681) | CHAMP clockwork charged DM | REJECT 3/10 | No σ_SI/σ_SD predictions anywhere; Ωh²=0.120 is the Planck target, not model output. MadDM v3.2 cited but no UFO published. Single inline configuration, not BP table. | Probably never — clockwork tower is hard to UFO. |
| [2602.16822](https://arxiv.org/abs/2602.16822) | FOPT rescue overabundant DM | REJECT 4/10 | Table 1 BMA-BMD with σ_SI from 8.3e-48 to 1.1e-53 cm² and ⟨σv⟩today is **excellent pinned BPs**, but no MG/MadDM/micrOMEGAs/CalcHEP — pure custom analytic+numeric pipeline. | (b) drop MG/MadDM tool requirement → instant ACCEPT for analytic-only track. |
| [2602.11085](https://arxiv.org/abs/2602.11085) | Sterile-ν DM in conformal Majoron | REJECT 3/10 | MG used only for Γ(N₁→3ν) auxiliary 3-body width — peripheral, not central. No tabulated BP, no validation statements. Eq. 4.14 cubic scaling is regime-bound, not global identity. | Probably never — peripheral MG use can't be promoted. |
| [2510.08677](https://arxiv.org/abs/2510.08677) | DM simplified models in resonance region (Di Mauro, Xie) | REJECT 5/10 | Table 1 categorical only (no parameter BPs); per-BP numerics only in Figs. 4-14. MadDM↔DRAKE comparison qualitative. Two GCE best-fit points + ~7 closed-forms exist but thin. | (a) reframe as "reproduce closed-form ⟨σv⟩ + GCE best-fit point" — could be MEDIUM-difficulty stretch eval. |
| [2512.18568](https://arxiv.org/abs/2512.18568) | Two-component DM with SU(2) dark sector | REJECT 5/10 | Table 2 BP1/BP2 with σ_SI=1.80e-48, 8.54e-48 cm² and component relics is **clean pinned data**; ~10 closed-form equations. But FeynRules→micrOMEGAs only, no MG/MadDM, no UFO. | (b) drop MG/MadDM requirement → instant ACCEPT. |
| [2509.14340](https://arxiv.org/abs/2509.14340) | Lepton collider window to reheating + DM | REJECT 4/10 | Single (m_φ=5 GeV, Λ=2.5 TeV) BP only. DM observables (Ωh²/σ_SI) in contours not tables. UFO not distributed. micrOMEGAs not MadDM. | Useful only as narrow ILC recast + Eq. 4.2 σ_SI sub-eval. |
| [2508.13583](https://arxiv.org/abs/2508.13583) | Inert DM in 3HDM ("blind spot narrative") | REJECT 5/10 | **Eq. 4.7 blind-spot identity** is real and confirmed: λ₅(v²/2)=m²_χ±−m²_χ₀. ~17 codifiable algebraic relations. But no MG/MadDM, no public UFO, no pinned BPs. | (b) drop MG requirement → harvest Eq. 4.7 as standalone algebraic-identity micro-task. |
| [2507.02048](https://arxiv.org/abs/2507.02048) | Vanilla L_μ-L_τ thermal DM | REJECT 4/10 | No tables anywhere (14 figures, 0 tables). All BPs are inline "∼" approximate values. No pinned Ωh². MG standalone subroutine used as cross-section engine but UFO not released. | Unlikely without author UFO release. |
| [2511.23133](https://arxiv.org/abs/2511.23133) | Constraining IDM at the LHC | REJECT 3/10 | Authors explicitly state they avoid fixing benchmark points. MG5+public UFOs (ulirep, idmrep) is strong tool fit but no pinned numerics — only 2D scans in (m_H, m_A) space. | Structurally incompatible with eval format. |
| [2507.16987](https://arxiv.org/abs/2507.16987) | Beyond the Veil: WIMPs at the ν-floor (Arcadi/Lindner/Profumo) | REJECT 4/10 | Same authors as 2506.19062, ~60-70% equation overlap, no MG/MadDM, no BP tables, only figure contours. The non-standard cosmology (Eqs. 33/34/40) is the only fresh content. | Harvest Eqs. 33/34/40 as supplementary cosmology mini-eval bolted onto 2506.19062. |
| [1804.04930](https://arxiv.org/abs/1804.04930) | 2HDM-portal singlet-doublet DM (Arcadi 2018) | REJECT 3/10 | 2018 vintage, micrOMEGAs only (no MG/MadDM/UFO), no BP tables, scan ranges only. 2506.19062 supersedes. | Probably never — superseded by 2506.19062. |
| [2505.11607](https://arxiv.org/abs/2505.11607) | Singlet-doublet DM revisited (Bhattiprolu, Petrosky, Pierce) | REJECT 4/10 | Direct precursor to 2506.19062 (same model). SARAH/SPheno/micrOMEGAs (no MG/MadDM, no UFO). Dataset DOI exists but contains 50M-point scan dump, not pinned BPs. RG-running content (Sec. IV) is genuinely new but niche. | Harvest Eqs. (18)/(21)/(22) as standalone RG-running mini-eval. Otherwise redundant with 2506.19062. |

## Lead pointers (worth checking later)

- **arXiv:2505.04290** — Voronchikhin & Kirpichnikov, scalar-portal inelastic DM
  with lepton fixed-target experiments. Flagged as the likely better companion
  to 2604.06929; expected to have closed-form thermally-averaged ⟨σv⟩ that the
  later paper deferred to.
- **arXiv:2107.09688** (Bottaro et al.) — pure-Majorana minimal DM σ_SI bands.
  Cited by 2602.17764. May itself be a clean closed-form benchmark, though
  custom Sommerfeld code (no MadGraph).
- **Citation graph of 2506.19062** — papers citing or cited by the reference
  paper are higher-prior candidates than random hep-ph hits. Round 6 search
  agent already enumerated; the four citing papers (2512.04158, 2508.13583,
  2507.16987, 2507.18692) and key cited papers (2505.11607, 1311.5896,
  1912.01758, 1804.04930, 2105.04255, 2404.05704) have all been verified or
  flagged for separate handling.
- **Search slice intelligence (2026-04-18):** Google site-search is dead for
  fresh hep-ph (returns 2013-2020 results); arxiv monthly listings page-by-page
  + body grep for "MadDM"/"MadGraph"/"UFO" is what works. Most 2025-2026 hep-ph
  DM papers use SARAH/SPheno/micrOMEGAs and only invoke MadGraph for collider
  pieces — true MadDM-as-relic-engine papers are rare (~1-3 per quarter).

## Statistics

- **Papers verified:** 32 (1 reference + 11 round 1 + 20 round 2)
- **Accepted:** 6 (including reference)
- **WEAK (graphical-tier candidates):** 4
- **Rejected:** 22
- **Acceptance rate under strict bar:** ~16% post-deep-read
- **Promotion rate from PRE-deep-read HIGH to ACCEPT:** ~25%
