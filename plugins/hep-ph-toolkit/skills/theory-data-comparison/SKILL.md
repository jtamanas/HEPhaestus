---
name: theory-data-comparison
description: Compare theoretical predictions to experimental data — uncertainty bands, pull distributions, chi-squared goodness of fit
---

# Theory-Data Comparison

Compare theoretical predictions to published experimental measurements with rigorous uncertainty treatment. Produces overlay plots with uncertainty bands, pull distributions, and goodness-of-fit metrics.

## Workflow

1. **Gather the data**:

   **Experimental data**: Central values, statistical errors, systematic errors (correlated and uncorrelated).
   - Source from HEPData where available
   - Manual input from tables in papers
   - Format: arrays of (bin_center, value, stat_error, syst_error_up, syst_error_down)

   **Theory predictions**: Central values with uncertainty breakdown.
   - Scale uncertainty: from mu_R, mu_F variation (7-point or envelope)
   - PDF uncertainty: from PDF replica or Hessian sets
   - Parametric uncertainty: alpha_s, m_t, m_b variations
   - Format: arrays of (bin_center, value, scale_up, scale_down, pdf_up, pdf_down)

2. **Build the comparison plot**:

   **Main panel**:
   - Data: black points with error bars (stat as inner bar, total as outer bar or cap)
   - Theory: colored band showing the prediction envelope
   - Multiple theory curves: different colors/styles (LO, NLO, NNLO; different PDFs; different models)
   ```python
   ax.errorbar(x_data, y_data, yerr=[err_down, err_up], fmt="ko", label="Data")
   ax.fill_between(x_th, y_th - unc_down, y_th + unc_up, alpha=0.3, label="NLO scale unc.")
   ```

   **Ratio panel**: Theory/Data or Data/Theory
   - Reference line at 1.0
   - Data error bars normalized to 1.0
   - Theory band normalized to the central theory prediction
   - Shows shape differences clearly

   **Pull panel** (optional, below ratio):
   - Pull = (data - theory) / sqrt(sigma_data^2 + sigma_theory^2)
   - Horizontal lines at +/-1 and +/-2
   - Points should scatter around zero if theory is good

3. **Goodness of fit**:
   ```python
   # Chi-squared (uncorrelated errors)
   chi2 = np.sum(((data - theory) / total_error)**2)
   ndof = len(data) - n_params
   p_value = 1 - scipy.stats.chi2.cdf(chi2, ndof)
   ```
   - Report chi^2/ndof and p-value on the plot or in text
   - For correlated systematics, use the full covariance matrix:
     `chi2 = (data - theory).T @ np.linalg.inv(cov) @ (data - theory)`

4. **Multiple theory comparisons**: Overlay several predictions to highlight differences:
   - LO vs. NLO vs. NNLO (show perturbative convergence)
   - Different PDF sets (NNPDF, CT18, MSHT20)
   - SM vs. BSM (show the effect of new physics)
   - Use distinct colors and line styles; keep the plot readable (max 4-5 curves)

5. **Output**:
   - Python script producing the multi-panel figure
   - Numerical chi^2/ndof summary printed to stdout
   - PDF and PNG figure files
   - Data arrays included inline or loaded from CSV/JSON

## Uncertainty Display Conventions

| Uncertainty type | Visual encoding |
|-----------------|-----------------|
| Stat. error (data) | Error bars (thin lines with caps) |
| Total error (data) | Error bars (thicker or outer caps) |
| Scale uncertainty (theory) | Hatched or solid semi-transparent band |
| PDF uncertainty (theory) | Cross-hatched or different-color band |
| Combined theory | Outer envelope band |
| Stat. + syst. (data) | Inner/outer error bar convention |

## Example

**Input**: "Compare NNLO QCD predictions for the top quark pair production differential cross section (d sigma / d p_T^t) to CMS measurements at 13 TeV. Show scale and PDF uncertainties separately. Include a ratio panel and report chi^2/ndof."

**Output**: Three-panel figure (distribution + ratio + pull), with data points, NNLO scale band, PDF band, ratio to data, pull distribution, and chi^2/ndof = X.XX (p = 0.XX) annotation.

## Style

> Reference: `docs/design-system.md` — the canonical source of truth for all visual rules.

**Palette**: Cool Analytic (`styles/hephaestus-analytic.mplstyle`). Load with:
```python
from styles.hep_ph_style import set_hep_context, make_ratio_panel, apply_direct_labels, add_uncertainty_band
palette = set_hep_context("analytic")
fig, (ax_main, ax_ratio) = make_ratio_panel()
```

**Key rules**:
- Theory: `#0284c7` (blue), 1.0pt solid curve. Data: `#1a1a1a` (black), points with 0.7pt error bars. Black data points have maximum contrast against any background.
- Multiple theory curves (LO/NLO/NNLO, different PDFs): use multi-curve escalation. Same model = same hue, vary lightness. Different models = different hue.
- **Ratio panel**: height = 30% of main panel, shared x-axis, separated by 0.5pt line with no gap. Reference line at 1.0 in de-emphasis gray. Y-axis: "Data/Theory" or "Ratio".
- **Uncertainty bands**: use `add_uncertainty_band()`. Scale uncertainty and PDF uncertainty get distinct colors from the escalation ladder. 1-sigma at alpha 0.12-0.15, 2-sigma at alpha 0.06-0.08. Boundary lines 0.5pt dashed.
- **No legend boxes.** Direct labels at curve endpoints. Use `apply_direct_labels()` with collision avoidance.
- **No gridlines, no bounding box.** Only left + bottom axes.
- Chi-squared annotation: subsidiary text (7pt, de-emphasis gray at 60% opacity), inside the plot area.
- Figure size: 85mm single-column default. Build at target, never scale.

## Validation

**Mandatory overlap check — do not skip this step:**
```python
from styles.hep_ph_style import check_overlaps
issues = check_overlaps(fig)
if issues:
    print(f"WARNING: {len(issues)} text overlaps detected:")
    for iss in issues:
        print(f"  '{iss['text_a']}' vs '{iss['text_b']}' — {iss['overlap_pt']}pt")
```
If `check_overlaps` returns any issues, **you must fix them before saving**. Common fixes: reposition labels, reduce font size, abbreviate text, or increase figure size. Re-run the check after fixing until it returns an empty list.

- Check that error bar sizes match the input uncertainties
- Verify the ratio panel reference matches the stated denominator
- Confirm pull values are computed with the correct combined uncertainty
- Ensure the chi^2 uses the right number of degrees of freedom
