---
name: draw-feynman
description: Generate publication-quality Feynman diagrams in TikZ-Feynman, FeynMF, or ASCII
---

# Draw Feynman Diagrams

Generate Feynman diagrams for particle physics processes. Supports tree-level and loop diagrams across QED, QCD, electroweak, and BSM theories.

## Output Formats

- **TikZ-Feynman** (default) — Modern LaTeX package, best for publications
- **FeynMF** — Traditional MetaFont-based diagrams
- **ASCII** — Quick text-based sketches for discussion

## Workflow

1. **Parse the process**: Identify initial and final state particles, the relevant theory (QED/QCD/EW/BSM), and the perturbative order.

2. **Enumerate topologies**: List all contributing Feynman diagrams at the requested order. For tree-level, enumerate all valid s-channel, t-channel, u-channel, and contact diagrams. For loops, enumerate all one-particle-irreducible topologies.

3. **Draw each diagram**: Generate the diagram code in the requested format.

4. **Wrap in compilable LaTeX**: Provide a complete `.tex` file that compiles standalone.

## TikZ-Feynman Conventions

- Use `\feynmandiagram` for simple diagrams, `\begin{feynman}` environment for complex layouts
- Fermion lines: `fermion`, `anti fermion`
- Gauge bosons: `photon` (wavy), `gluon` (coiled), `boson` (dashed for scalars)
- Label all external legs with particle names
- Label internal propagators with momentum when computing amplitudes
- Use `[blob]` for effective vertices and form factors
- For Majorana particles, draw both initial-state arrows pointing into the vertex (arrows-in convention).

## Example

**Input**: "Draw the leading-order Feynman diagrams for e+e- -> mu+mu-"

**Output**: Two diagrams (s-channel gamma and Z), each as compilable TikZ-Feynman code with proper labels.

## Style

> Reference: `docs/design-system.md` — the canonical source of truth for all visual rules.

**Palette**: Ink-only (Palette C). The repo ships `styles/hephaestus-tikz.sty`, but it is repo-local — pdflatex won't find it from a user's working directory unless `TEXINPUTS` is set. **Emit a self-contained preamble inline so the output compiles anywhere.** Use this exact block at the top of every generated `.tex`:

```latex
\documentclass[border=2pt]{standalone}
\usepackage{tikz-feynman}
\usepackage{xcolor}

% Inlined from styles/hephaestus-tikz.sty — keep in sync.
\definecolor{hepInk}{HTML}{1a1a1a}
\definecolor{hepAccent}{HTML}{0284c7}      % use {0369a1} for slate context
\definecolor{hepLabelGray}{HTML}{555555}
\tikzfeynmanset{
  every fermion/.style={line width=1.0pt, draw=hepInk},
  every anti fermion/.style={line width=1.0pt, draw=hepInk},
  every photon/.style={line width=1.0pt, draw=hepInk},
  every gluon/.style={line width=1.0pt, draw=hepInk},
  every boson/.style={line width=1.0pt, draw=hepInk},
  every scalar/.style={line width=1.0pt, draw=hepInk},
  every ghost/.style={line width=0.7pt, draw=hepInk},
  every dot/.style={fill=hepInk, inner sep=0pt, minimum size=4pt},
}
\tikzset{
  hep label/.style={font=\itshape\small, text=hepLabelGray, inner sep=2pt},
  hep propagator label/.style={font=\itshape\small, text=hepAccent, inner sep=2pt, midway},
}
```

**Key rules**:
- All propagator lines: `#1a1a1a` (near-black), 1.0pt. Ghost lines: 0.7pt dotted.
- Boson of interest (the propagator being discussed): accent color `#0284c7` or `#0369a1`, same weight.
- Vertex dots: 2pt radius, filled black. Only at interaction vertices, never at line endpoints.
- Particle labels: italic Computer Modern Serif in `#555555`, 2pt offset from the line, placed at the midpoint of external legs.
- Propagator labels: centered above/below the propagator, in accent color.
- Square aspect ratio. External legs extend to at least 30% of diagram width before the vertex.
- No bounding box, no background fill.

## Validation

- Verify charge conservation at every vertex
- Verify fermion number conservation (or violation if BSM)
- Confirm color flow is consistent for QCD diagrams
- Check that the number of diagrams matches the expected count for the process and order — see Gotchas for the Majorana t/u undercount trap

## Gotchas

These are silent failure modes — the LaTeX compiles, the diagrams *look* right, but the output is wrong. Check each before emitting.

### Propagator label syntax — `[hep propagator label]` rendered as literal text

`edge label=<x>` expands to `node[auto]{<x>}`, so `<x>` is the text content of the node, *not* its options. Putting a tikzset key in the braces typesets it literally:

```latex
% WRONG — [hep propagator label] lands inside text braces, prints literally:
(a) -- [photon, edge label={[hep propagator label]\(Z\)}] (b)

% CORRECT (plain) — accepts default styling:
(a) -- [photon, edge label=\(Z\)] (b)

% CORRECT (with accent-color styling) — use edge node= so the brackets are parsed as node options:
(a) -- [photon, edge node={node[hep propagator label]{\(Z\)}}] (b)
```

Use the plain form by default. Use the accent-color form only when the propagator is the "boson of interest" being discussed.

### LuaTeX-only layout keys silently ignored under pdflatex

`layered layout`, `horizontal=a to b`, and `spring layout` are PGF graph-drawing algorithms that require LuaTeX. Under pdflatex they're silently dropped — the diagram still compiles, but vertices land wherever you put them (or collapse to the origin). Compile with `pdflatex` using **explicit vertex coordinates** (`at (x,y)` or `right=of a`). Only emit the layout keys if the caller's pipeline runs `lualatex`.

### Majorana t/u-channel undercount

For a Majorana initial state, every t-channel topology has a required u-channel partner (with relative Fermi sign −1) obtained by swapping the two identical incoming legs. If you emit only one, you've undercounted. Example: `chi1 chi1 -> W+ W-` with chargino exchange gives **both** a t-channel and a u-channel diagram, not one.
