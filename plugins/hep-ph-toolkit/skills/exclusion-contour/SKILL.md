---
name: exclusion-contour
description: Generate BSM exclusion and discovery contour plots in 2D parameter planes — observed, expected, Brazil bands
---

# Exclusion Contour

Generate exclusion and discovery reach contour plots in two-dimensional BSM parameter planes. The bread and butter of phenomenology papers.

## Workflow

1. **Define the parameter plane**:
   - Axes: mass parameters (m_stop vs. m_neutralino), couplings (tan(beta) vs. m_A), or any two BSM parameters
   - Axis ranges and scaling (linear or log)
   - Physical boundaries (e.g., m_neutralino < m_stop for the decay to be kinematic)

2. **Prepare the exclusion data**:

   **From a parameter scan**: Grid of (x, y) points with a test statistic or signal strength mu at each point.
   ```python
   # Interpolate the grid to find the contour where mu = 1 (exclusion boundary)
   from scipy.interpolate import griddata
   from matplotlib.contour import QuadContourSet
   ```

   **From published limits**: Digitized contour coordinates from HEPData or manual extraction.

3. **Draw the contours**:

   **Observed limit** (solid line):
   ```python
   ax.contour(X, Y, Z, levels=[1.0], colors="black", linewidths=2)
   ax.contourf(X, Y, Z, levels=[1.0, Z.max()], colors=["gray"], alpha=0.3)
   ```

   **Expected limit** (dashed line):
   ```python
   ax.contour(X, Y, Z_exp, levels=[1.0], colors="black",
              linewidths=2, linestyles="dashed")
   ```

   **Brazil bands** (expected +/-1sigma, +/-2sigma):
   ```python
   ax.contourf(X, Y, Z_p2s, levels=[1.0, Z.max()], colors=["#FFF200"], alpha=0.5)  # yellow: 2sigma
   ax.contourf(X, Y, Z_p1s, levels=[1.0, Z.max()], colors=["#00CC00"], alpha=0.5)  # green: 1sigma
   ```

   **Kinematic boundary**: Diagonal line where decay is forbidden.
   ```python
   ax.plot([x_min, x_max], [x_min, x_max], "k--", alpha=0.5, label="Kinematic boundary")
   ```

4. **Overlay multiple experiments/analyses**:
   - Different colors for ATLAS, CMS, LEP, Tevatron
   - Solid fill with transparency for excluded regions
   - Use `ax.contourf()` with distinct colors per experiment
   - Legend with experiment names and luminosities

5. **Annotations**:
   - Process label (e.g., "$\\tilde{t}_1 \\to t \\tilde{\\chi}^0_1$")
   - sqrt(s) and luminosity
   - Assumption text (e.g., "BR = 100%", "m_gluino >> m_stop")
   - Experiment/preliminary label
   - Theory reference line (e.g., "NLO+NLL cross section")

6. **Output**:
   - Python script producing the contour plot
   - PDF and PNG outputs
   - If scan data is provided, include the interpolation pipeline
   - If digitized, include the coordinate arrays

## Color Conventions

Standard color scheme for multi-experiment overlays:
- ATLAS: blue
- CMS: red
- LEP: green
- Tevatron: orange/purple
- Theory (natural, fine-tuning): gray dashed contours

For single-experiment plots:
- Observed excluded: solid gray fill
- Expected: dashed black line
- 1-sigma band: green
- 2-sigma band: yellow

## Example

**Input**: "Plot the exclusion contour in the (m_stop, m_neutralino) plane for direct stop pair production at the 13 TeV LHC with 139 fb^-1. Show observed, expected, and +/-1,2 sigma bands. Add the kinematic boundary line where m_stop = m_top + m_neutralino."

**Output**: Complete Python script generating a ATLAS/CMS-style exclusion plot with Brazil bands, kinematic boundary, and proper annotations.

## Style

> Reference: `docs/design-system.md` — the canonical source of truth for all visual rules.

**Palette**: Slate Precision (`styles/hephaestus-slate.mplstyle`). Load with:
```python
from styles.hep_ph_style import set_hep_context
palette = set_hep_context("slate")
```

**Key rules**:
- Observed limit: `#1a1a1a` (black), 1.2pt solid — highest-contrast element on the plot.
- Theory prediction: `#0369a1` (steel blue), 1.0pt solid.
- Excluded region fill: `#dc2626` (muted red) at alpha 0.06-0.10. The boundary line does the work, not the fill.
- Expected limit: thin dashed black.
- **Brazil bands**: Green (+/-1-sigma) at alpha 0.25 desaturated, yellow (+/-2-sigma) at alpha 0.20 desaturated. Direct labels ("expected", "+/-1 sigma") instead of legend entries.
- **No legend boxes.** Use direct labels inside the plot area. Region labels ("excluded", "95% CL") sit inside the region, lower-right, in de-emphasis gray at 60% opacity.
- **No gridlines, no bounding box.** Only left + bottom axes, ticks inward.
- Figure size: 85mm x 63.75mm (single-column) or 170mm x 95.6mm (double-column for wide scans).
- Typography: Computer Modern Serif. Axis labels 9pt, tick labels 8pt.

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

- Check that excluded region is on the correct side of the contour
- Verify kinematic boundaries are in the right place
- Confirm Brazil band ordering (2-sigma outside 1-sigma)
- Ensure axis labels include units
