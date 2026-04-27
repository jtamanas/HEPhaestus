---
name: feynman-tikz
description: Render Feynman diagrams in TikZ-Feynman for direct LaTeX embedding — standalone or inline
---

# Feynman TikZ

Generate TikZ-Feynman code for Feynman diagrams that can be directly embedded in LaTeX documents. Supports both standalone compilation and inline use within papers.

## Workflow

1. **Parse the diagram request**: Identify the process, topology (s/t/u-channel, loop), and any special features (blobs, effective vertices, cut lines).

2. **Choose the rendering approach**:
   - `\feynmandiagram` — Simple inline diagrams with automatic layout
   - `\begin{feynman}` environment — Full control over vertex placement
   - Use the environment for any diagram with more than 4 external legs or loops

3. **Generate the TikZ-Feynman code**:
   - Define vertices with meaningful names
   - Connect with appropriate edge styles:
     - `fermion` / `anti fermion` — solid arrow
     - `photon` — wavy line
     - `gluon` — coiled line (use `half left`/`half right` for loops)
     - `charged boson` — wavy with arrow
     - `scalar` / `charged scalar` — dashed line
     - `ghost` — dotted line
   - Label external particles and momenta
   - Add momentum arrows where needed

4. **Provide both formats**:
   - **Inline**: Ready to paste into a `\begin{figure}` environment
   - **Standalone**: Complete document that compiles to a PDF/PNG

5. **Compilation note**: TikZ-Feynman requires LuaLaTeX for automatic vertex placement. Include a fallback with manual placement for pdfLaTeX compatibility.

## Example

**Input**: "Draw the one-loop gluon self-energy diagram (gluon bubble)"

**Output**:
```latex
\feynmandiagram [horizontal=a to b] {
  i [particle=$g$] -- [gluon, momentum=$k$] a
    -- [gluon, half left, momentum=$k{-}q$] b
    -- [gluon, half left, momentum=$q$] a,
  b -- [gluon, momentum=$k$] f [particle=$g$],
};
```

## Style

> Reference: `docs/design-system.md` — the canonical source of truth for all visual rules.

**Palette**: Ink-only (Palette C). Include the style package in the preamble:
```latex
\usepackage{hephaestus-tikz}   % from styles/hephaestus-tikz.sty
```

**Key rules**:
- All lines default to `hepInk` (`#1a1a1a`) at 1.0pt. Use the `every accent` style for the boson or propagator being discussed (draws in `hepAccent`).
- Vertex style: `hep vertex` (4pt filled black circle). Apply only at interaction vertices.
- Label styles: `hep label` for external legs (italic, gray, 2pt inner sep), `hep propagator label` for internal lines (italic, accent color, midway).
- Use `\hepsetaccent{steel}` to switch to Slate Precision context if the diagram accompanies an exclusion contour.
- Square aspect ratio. Generous padding — external legs at least 30% of diagram width.
- Use `\begin{feynman}[layered layout, horizontal=a to b]` inside a `tikzpicture` for standard diagrams.

## Validation

- Verify that all vertices connect correctly
- Check that the diagram compiles without errors
- Confirm particle flow arrows are consistent with charge conservation
