# NREFT Convention Sheet — arXiv:2603.23040 (Scotogenic Inverse Seesaw)

This sheet is **binding** for all implementations in `si_nreft.py` and `sd_nreft.py`.
See brainstorm §2 for the full ruling.

## Coefficient Table

| Coefficient | Source eq. | Per-nucleon? | Form-factor source | Units | Notes |
|---|---|---|---|---|---|
| `C_SS_h` | Eq. 26a | per-nucleon (via `f_N^(p,n)` insertion at σ level) | n/a at this layer | dim = `[mass]⁻²` | h-exchange scalar-scalar Wilson coefficient. Computed once per (m_χ, y_hχχ); isospin dependence enters at `σ̄^SI` through `f_N^p ≠ f_N^n`. |
| `C^VA_Z`, `C^AA_Z` | Eqs. 26b-c | per-nucleon | n/a at this layer | `[mass]⁻²` | Z-exchange vector-axial / axial-axial. Same Z propagator: Breit-Wigner (fixed Γ_Z) at ZMT limit reduces to `1/m_Z²`. |
| `c1` | Eq. 29a | **per-nucleon** (p and n separately) | Hoferichter 2015: σ_πN = 59.1(3.5) MeV, σ_s = 41.3(7.7) MeV (proton); f_Tu, f_Td, f_Ts derived via `f_Tq = m_q ⟨N\|q̄q\|N⟩/m_N` | dimensionless × mass-mismatch | **Majorana fermion: no factor of 2 ambiguity if we treat χ as identical-particle at the \|M\|² level and NOT at the Wilson-matching level.** Convention: match `L_eff = c1 χ̄χ N̄N` with `χ̄χ` Dirac-bilinear normalization; factor-of-2 for Majorana is applied once, at the σ̄^SI level via the explicit Majorana prefactor (see `sigma_bar_SI` docstring). |
| `c4` | Eq. 29b | **per-nucleon**; isospin-symmetric for this model because the Z-axial coupling is universal | Nucleon axial: ΔΣ^p_u = 0.842, ΔΣ^p_d = −0.427, ΔΣ^p_s = −0.085 (FLAG 2021 g_A averages) | dimensionless | Drives the dominant SD operator. |
| `c6` | Eq. 29c | per-nucleon | same axial form factors | `[mass]⁻²` | Pion/eta pole corrections to SD (Eq. 33 drops this). |
| `c9` | Eq. 29d | per-nucleon | same | `[mass]⁻¹` | Subleading SD velocity-dependent piece. |
| `c8` | Eq. 29e | per-nucleon | scalar form factors | `[mass]⁻¹` | SI subleading, enters σ̄^SI via the `v²/c²` term in Eq. 30. |

## Per-nucleon vs Per-nucleus Rule (binding)

1. All `c_i` are computed **per nucleon** (proton or neutron) at the coupling layer.
2. Isotope averaging (xenon: 9 isotopes) happens **only at `sigma_bar_SI` and `sigma_SD_*`**, never at the `c_i` layer.
3. The final reported `σ̄^SI` is **per-nucleon after averaging the isotope nuclear response**, consistent with Del Nobile (2022) Eq. 5.49 and the XENONnT/LZ convention.
4. σ^SD is reported **per-nucleus** for ^131Xe specifically (the dominant-odd-neutron isotope), matching the paper's convention and the LZ SD limit convention.

## Velocity Convention (binding)

The scalar `v_rel` in all signatures is `v/c` (dimensionless, not β, not v²). The SI velocity-suppression term in Eq. 30 reads `(v_rel)²` explicitly. Frame is the galactic-rest-frame DM velocity; the canonical "v₀ = 220 km/s" translates to `v_rel ≈ 7.3e-4`, but for the benchmark we fix **`v_rel = 1.0e-3`** at all three BPs to match the paper's quoted figures. Documented once in `inputs.py`.

## Majorana Factor (binding)

Applied **exactly once**, at the σ̄^SI / σ^SD return line, as a single `MAJORANA_FACTOR = 2.0` constant defined in `constants.py` with a comment: "Factor from identical-particle statistics in the outgoing DM line; applied at the cross-section layer, NOT at the |M|² or Wilson-coefficient layer. Cross-checked by convention against Del Nobile 2022 Eq. 5.38."

**grep invariant:** `grep -En 'MAJORANA_FACTOR \*' cross_sections/si_nreft.py cross_sections/sd_nreft.py` must return **exactly 3 hits**: 1 in `si_nreft.py` (return of `sigma_bar_SI`), 2 in `sd_nreft.py` (returns of `sigma_SD_full` and `sigma_SD_simplified`).
