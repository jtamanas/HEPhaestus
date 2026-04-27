# hep-ph-agents Design System

> *Every visual difference encodes a physics difference. Subtract everything else.*

This document is the source of truth for all visual output produced by hep-ph-agents skills. Any skill that generates a plot, diagram, or figure references this document for judgment calls.

---

## 1. Principles

In priority order:

1. **Visual dimensions = model-space dimensions.** Hue maps to model identity. Lightness maps to parameter variation. Line style maps to approximation level. If two things look different on the plot, they mean something different in the physics.
2. **Direct over indirect.** Labels live on the data. No legend boxes. A reader understands a curve without moving their eyes.
3. **Subtract, don't add.** No gridlines. No bounding boxes. No background fills. Default is invisible; justify every piece of emphasis.
4. **Build for print reality.** Figures are built at exact target column width. Never scale in LaTeX. What you export is what the reader sees.
5. **Semantic color only.** Color is never decorative. Each hue has a fixed role. Grays are warm-tinted, never pure neutral.

---

## 2. Color Palettes

### 2.1 Palette A — Cool Analytic (theory-vs-data)

| Role | Color | Hex | When |
|------|-------|-----|------|
| Theory prediction | Blue | `#0284c7` | Calculated curves, NLO/NNLO predictions |
| Experimental data | Black | `#1a1a1a` | Measured points, error bars — maximum contrast on any background |
| Secondary data / accent | Burnt orange | `#ea580c` | Second data set, highlight, or accent |
| Exclusion/secondary | Violet | `#7c3aed` | Uncertainty bands, secondary exclusion |
| Ink | Near-black | `#1a1a1a` | Axes, ticks, primary text |
| De-emphasis gray | Warm gray | `#9ca3af` | Subsidiary labels, annotations |

### 2.2 Palette B — Slate Precision (exclusion contours)

| Role | Color | Hex | When |
|------|-------|-----|------|
| Theory prediction | Steel blue | `#0369a1` | Predicted limits, theory curves |
| Observed data | Black | `#1a1a1a` | Observed limit (highest-contrast element) |
| Excluded region | Muted red | `#dc2626` | Ruled-out parameter space (low-opacity fill) |
| Ink | Slate | `#334155` | Axes, ticks, labels |
| De-emphasis gray | Slate gray | `#94a3b8` | Subsidiary structure |

### 2.3 Palette C — Ink-only (Feynman diagrams)

| Role | Color | Hex | When |
|------|-------|-----|------|
| Fermion/scalar lines | Near-black | `#1a1a1a` | External legs, propagators |
| Boson of interest | Context accent | `#0284c7` or `#0369a1` | The propagator or vertex being discussed |
| Labels | Dark gray | `#555555` | Particle labels in italic CM Serif |

### 2.4 Multi-curve escalation

When multiple theory curves share a plot:

1. **Same model, different parameters** — same hue, vary lightness. 4-step ladders:
   - Blue: `#0c4a6e` / `#0369a1` / `#0ea5e9` / `#7dd3fc`
   - Violet: `#4c1d95` / `#7c3aed` / `#a78bfa` / `#c4b5fd`
   - Teal: `#134e4a` / `#0f766e` / `#14b8a6` / `#5eead4`

2. **Same model, subordinate variant** — same hue + lightness, dashed. Solid = primary prediction, dashed = limiting case or different approximation order.

3. **Different models** — different hue. Second model: violet (`#7c3aed`), third: teal (`#0f766e`). Each gets its own solid/dashed pair.

4. **Hard cap: 7+ curves** — switch to small multiples with a shared axis. Never add more colors.

### 2.5 Brazil bands

The green/yellow convention is established but we mute it: desaturated fills at alpha 0.20-0.25 (green) and 0.20 (yellow), observed limit as solid black, expected limit as thin dashed, direct labels instead of legend entries.

### 2.6 Fill opacity rules

| Fill type | Alpha |
|-----------|-------|
| Exclusion region fills | 0.06-0.10 |
| Uncertainty bands (1 sigma) | 0.12-0.15 |
| Uncertainty bands (2 sigma) | 0.06-0.08 |
| Brazil bands (+/-1 sigma green) | 0.25, desaturated |
| Brazil bands (+/-2 sigma yellow) | 0.20, desaturated |

When more than 2 bands overlap: switch to small multiples.

---

## 3. Typography

**One font family: Computer Modern Serif.** Every label looks like it was typeset in the same system as the paper's equations.

| Element | Size (at print) | Weight | Style | Color |
|---------|-----------------|--------|-------|-------|
| Axis labels | 9pt | Regular | Italic | Ink |
| Tick labels | 8pt | Regular | Roman | Ink |
| Direct annotations | 8pt | Regular | Italic (theory), Roman (data) | Matches curve |
| Subsidiary text | 7pt | Regular | Roman | De-emphasis gray, 60% opacity |
| Units in brackets | 8pt | Regular | Roman | Ink |

### Rules

- Exactly two text hierarchy levels: primary (9pt ink) and secondary (7-8pt gray). Never a third.
- Left-align all annotations. Never center.
- LaTeX rendering for all math.
- Particle symbols always italic. Units always roman.

---

## 4. Line Weight Hierarchy

All values at final print size:

| Element | Weight | Notes |
|---------|--------|-------|
| Primary data/theory curves | 1.0-1.2pt | What the reader is here to see |
| Uncertainty band boundaries | 0.5pt, dashed | Subordinate to the central value |
| Axis lines | 0.5pt | Structural, not informational |
| Tick marks | 0.5pt wide, 3pt long (major), 1.5pt long (minor) | Orientation only |
| Error bars | 0.7pt | Visible but thinner than the curve |
| Exclusion region boundary | 1.2pt | As prominent as data |

**No gridlines.** If a reader needs to trace a value to an axis, the tick marks are sufficient.

---

## 5. Layout & Composition

### 5.1 Figure dimensions

Build at exact target. Never scale in LaTeX.

| Context | Width | Aspect | Use |
|---------|-------|--------|-----|
| Single-column | 85mm (3.346in) | 4:3 | Default for most plots |
| Double-column / slides | 170mm (6.693in) | 16:9 | Small multiples, wide exclusion scans |

### 5.2 Axis treatment

- No bounding box. Only left and bottom axes.
- Ticks face inward.
- Axis lines meet at origin corner but don't extend beyond data range.
- Log scale: major ticks at each power of 10, minor at 2-9. No labels on minor ticks.

### 5.3 Whitespace

- Margin between axis labels and tick labels: 4pt minimum.
- Margin between plot area and annotations: 2pt minimum from any curve.
- Padding: `bbox_inches='tight'`, `pad_inches=0.02`.
- Between small-multiple panels: 8mm horizontal, 6mm vertical.

### 5.4 Annotation placement

- Direct labels at curve endpoints, right side, vertically aligned with the curve's final value. Stagger with 2pt minimum spacing if curves converge.
- Region labels ("excluded", "95% CL") inside the region, lower-right, de-emphasis gray at 60% opacity.
- All annotations inside the plot area.

### 5.5 Ratio panels

Height = 30% of main panel. Separated by a thin 0.5pt line, no gap. Y-axis: "Data/Theory" or "Ratio". Horizontal reference line at 1.0 in de-emphasis gray.

### 5.6 Feynman diagrams

- Square aspect ratio.
- External legs extend to at least 30% of diagram width.
- Particle labels: 2pt offset from line, italic CM Serif, at midpoint of external legs.
- Propagator labels: centered above/below, in accent color.
- Vertex dots: 2pt radius, filled black. Only at interaction vertices.

---

## 6. Implementation

### Style sheets

- `styles/hep-ph-agents-analytic.mplstyle` — Palette A (theory-vs-data)
- `styles/hep-ph-agents-slate.mplstyle` — Palette B (exclusion contours)

### TikZ package

- `styles/hep-ph-agents-tikz.sty` — Feynman diagram styling (Palette C)

### Python helpers

- `styles/hep_ph_style.py` — Convenience functions for direct labels, uncertainty bands, color escalation, and context switching.

### Skill mapping

| Skill | Palette | Special rules |
|-------|---------|---------------|
| `hep-plot` | Cool Analytic | Multi-curve escalation |
| `exclusion-contour` | Slate Precision | Brazil band handling |
| `draw-feynman` | Ink-only | TikZ style package |
| `feynman-tikz` | Ink-only | TikZ style package |
| `theory-data-comparison` | Cool Analytic | Ratio panel layout |
