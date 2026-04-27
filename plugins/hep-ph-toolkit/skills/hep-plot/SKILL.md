---
name: hep-plot
description: Publication-quality HEP plots with matplotlib and mplhep — distributions, stacked histograms, ratio panels, multi-panel figures
---

# HEP Plot

Generate publication-quality plots for HEP phenomenology papers using matplotlib with the `mplhep` style library. Covers the most common plot types in phenomenology publications.

## Workflow

1. **Determine the plot type**:
   - **1D distribution**: Differential cross sections, branching ratios, kinematic spectra
   - **Stacked histogram**: Signal over backgrounds with data overlay
   - **2D histogram / heatmap**: Correlation plots, parameter scans
   - **Line plot**: Running couplings, scale dependence, form factors
   - **Multi-panel**: Side-by-side comparisons, grid of parameter points

2. **Set the experiment style**:
   ```python
   import mplhep as hep
   hep.style.use("ATLAS")   # or "CMS", "LHCb", "ALICE", "ATLAS"
   ```
   If no experiment context, use `"CMS"` as the default (clean and widely recognized). For theory-only papers with no experimental affiliation, use a clean custom style.

3. **Build the figure**:

   **Axis labels**: Always include units. Use LaTeX rendering.
   ```python
   ax.set_xlabel(r"$m_{t\bar{t}}$ [GeV]")
   ax.set_ylabel(r"$d\sigma/dm_{t\bar{t}}$ [pb/GeV]")
   ```

   **Legends**: Place inside the plot area where there is empty space. Use short, descriptive labels. Order: data first, then signal, then backgrounds largest-to-smallest.

   **Colors**: Use a colorblind-friendly palette. Default ordering:
   - Signal: red or dark blue (solid line, thicker)
   - Major backgrounds: blue, green, orange (filled histograms)
   - Data: black points with error bars

   **Log scale**: Use log y-axis when the distribution spans more than 2 orders of magnitude. Always use linear x-axis unless the variable is intrinsically logarithmic (e.g., Q^2).

4. **Ratio panel** (include whenever data and theory/MC are both present):
   ```python
   from styles.hep_ph_style import make_ratio_panel
   fig, (ax, rax) = make_ratio_panel()
   ```
   - **Always include a ratio panel when the plot shows data overlaid with theory or MC.** This is the standard in HEP papers and readers expect it.
   - Ratio = data/prediction or NLO/LO
   - Draw a horizontal reference line at 1.0
   - Shade the uncertainty band around the reference
   - Use the same x-axis range and binning as the main panel
   - y-axis label: "Ratio" or "Data/MC" or "NLO/LO"

5. **Uncertainty bands**:
   - Theory scale uncertainty: hatched or semi-transparent fill
   - PDF uncertainty: separate color or cross-hatched
   - Statistical errors: error bars on points
   - Use `ax.fill_between()` for continuous bands

6. **Output**:
   - Python script that produces the plot
   - Save as both PDF (for paper) and PNG (for slides): `fig.savefig("plot.pdf", bbox_inches="tight")`
   - Figure size: 8x6 inches for single column, 16x6 for double column

## Style Rules

- Font size: axis labels 16pt, tick labels 14pt, legend 13pt
- Line widths: 2pt for theory curves, 1.5pt for MC, markers size 6 for data
- No title on the plot (use caption in the paper instead)
- Grid: off by default (enable only if it aids readability)
- Tick marks: inside, on both axes, minor ticks enabled
- No unnecessary chart junk — every ink mark should encode data

## Example

**Input**: "Plot the transverse momentum distribution of the leading jet for signal (Z' -> tt, m_Z' = 3 TeV) and backgrounds (ttbar, W+jets) as a stacked histogram with a data/MC ratio panel, CMS style, sqrt(s) = 13 TeV, 139 fb^-1"

**Output**: Complete Python script producing a two-panel figure with stacked backgrounds, signal overlay, mock data points with error bars, CMS preliminary label, luminosity text, and a ratio panel with uncertainty band.

## Style

> Reference: `docs/design-system.md` — the canonical source of truth for all visual rules.

**Palette**: Cool Analytic (`styles/hephaestus-analytic.mplstyle`). Load with:
```python
from styles.hep_ph_style import set_hep_context
palette = set_hep_context("analytic")
```

**Key rules**:
- Theory curves: `#0284c7` (blue), 1.0pt solid. Data: `#1a1a1a` (black), points + 0.7pt error bars. Black data points have maximum contrast against any background.
- **No legend boxes.** Use `apply_direct_labels()` — endpoint labels on each curve, right-aligned.
- **No gridlines, no bounding box.** Only left + bottom axes, ticks inward.
- Multi-curve escalation: same model/different parameters = same hue, vary lightness (4-step ladder). Different models = different hue. Subordinate variants = dashed. Hard cap at 7 curves — beyond that, use small multiples.
- Uncertainty bands: 1-sigma at alpha 0.12-0.15, 2-sigma at alpha 0.06-0.08, boundary lines 0.5pt dashed.
- Figure size: 85mm x 63.75mm (single-column 4:3). Build at target size, never scale in LaTeX.
- Typography: Computer Modern Serif via `text.usetex: True`. Axis labels 9pt italic, tick labels 8pt roman, annotations 8pt, subsidiary text 7pt gray.

**Helper functions** (`styles/hep_ph_style.py`):
- `escalate_colors(n_models, n_variants)` — returns colors + line styles per escalation ladder
- `apply_direct_labels(ax)` — endpoint labels with collision avoidance
- `add_uncertainty_band(ax, x, y, yerr_up)` — correct alpha + boundary styling
- `make_ratio_panel()` — main + ratio panel with 0.3 height ratio, shared x-axis
- `check_overlaps(fig)` — detect overlapping text; run before `savefig()` and fix any issues it reports

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
If `check_overlaps` returns any issues, **you must fix them before saving**. Common fixes: reposition labels, reduce font size, abbreviate text, increase figure size, or switch from direct labels to a legend. Re-run the check after fixing until it returns an empty list.

- Verify all axis labels have units
- Check that the legend doesn't obscure data
- Confirm the ratio panel shares the x-axis exactly
- Ensure the script runs standalone with only numpy, matplotlib, and mplhep
