"""
hephaestus style helpers.

Convenience functions for visual rules that matplotlib style sheets
cannot express declaratively: direct labels, uncertainty bands,
multi-curve color escalation, and context switching.

Reference: docs/design-system.md
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Literal

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import Bbox

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_STYLE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Palettes (hex strings without '#')
# ---------------------------------------------------------------------------
_PALETTES = {
    "analytic": {
        "theory": "#0284c7",
        "data": "#1a1a1a",
        "accent": "#ea580c",
        "secondary": "#7c3aed",
        "ink": "#1a1a1a",
        "deemph": "#9ca3af",
    },
    "slate": {
        "theory": "#0369a1",
        "observed": "#1a1a1a",
        "excluded": "#dc2626",
        "ink": "#334155",
        "deemph": "#94a3b8",
    },
}

_ESCALATION_LADDERS = {
    "blue": ["#0c4a6e", "#0369a1", "#0ea5e9", "#7dd3fc"],
    "violet": ["#4c1d95", "#7c3aed", "#a78bfa", "#c4b5fd"],
    "teal": ["#134e4a", "#0f766e", "#14b8a6", "#5eead4"],
}

_FILL_ALPHA = {
    "exclusion": 0.08,
    "unc_1sigma": 0.14,
    "unc_2sigma": 0.07,
    "brazil_1sigma": 0.25,
    "brazil_2sigma": 0.20,
}


# ---------------------------------------------------------------------------
# LaTeX availability (cached per-process)
# ---------------------------------------------------------------------------
_LATEX_AVAILABLE: bool | None = None


def _probe_latex() -> bool:
    """Return True if a LaTeX installation capable of rendering matplotlib text is available.

    Result is cached per-process. Requires both a ``latex`` binary on ``PATH`` and
    a successful minimal compile (catches missing packages like ``type1cm.sty``).
    """
    global _LATEX_AVAILABLE
    if _LATEX_AVAILABLE is not None:
        return _LATEX_AVAILABLE

    if shutil.which("latex") is None and shutil.which("pdflatex") is None:
        _LATEX_AVAILABLE = False
        return False

    prior_usetex = mpl.rcParams.get("text.usetex", False)
    try:
        mpl.rcParams["text.usetex"] = True
        fig_probe, ax_probe = plt.subplots(figsize=(1, 1))
        try:
            ax_probe.set_title(r"$x$")
            fig_probe.canvas.draw()
        finally:
            plt.close(fig_probe)
        _LATEX_AVAILABLE = True
    except Exception:
        _LATEX_AVAILABLE = False
    finally:
        mpl.rcParams["text.usetex"] = prior_usetex
    return _LATEX_AVAILABLE


# ---------------------------------------------------------------------------
# Context switching
# ---------------------------------------------------------------------------
def set_hep_context(context: Literal["analytic", "slate"] = "analytic") -> dict:
    """Load the matching ``.mplstyle`` and return the palette dict.

    If a working LaTeX installation is not available, ``text.usetex`` is
    forced to ``False`` after the style loads and matplotlib's built-in
    mathtext engine is used as the fallback renderer. Styling intent in
    the ``.mplstyle`` files is preserved — only ``text.usetex`` changes.

    Parameters
    ----------
    context : ``"analytic"`` or ``"slate"``
        Which palette to activate.

    Returns
    -------
    dict
        The palette color mapping for the chosen context.
    """
    style_file = _STYLE_DIR / f"hephaestus-{context}.mplstyle"
    if not style_file.exists():
        raise FileNotFoundError(f"Style sheet not found: {style_file}")
    plt.style.use(str(style_file))

    if mpl.rcParams.get("text.usetex", False) and not _probe_latex():
        mpl.rcParams["text.usetex"] = False
        # Fallback: cm mathtext fontset matches Computer Modern serif styling
        # of the usetex output more closely than dejavusans.
        mpl.rcParams["mathtext.fontset"] = "cm"
        logger.info(
            "LaTeX unavailable; falling back to matplotlib mathtext "
            "(text.usetex=False, mathtext.fontset=cm)."
        )

    return _PALETTES[context]


# ---------------------------------------------------------------------------
# Color escalation
# ---------------------------------------------------------------------------
def escalate_colors(
    n_models: int,
    n_variants: int = 1,
    palette: Literal["analytic", "slate"] = "analytic",
) -> list[dict]:
    """Return colors and line styles per the multi-curve escalation ladder.

    Parameters
    ----------
    n_models : int
        Number of distinct models (each gets a different hue).
        Maximum 3 before the spec mandates small multiples.
    n_variants : int
        Number of parameter variants per model (lightness steps).
        Maximum 4 per hue family.
    palette : str
        Which palette context for the primary hue.

    Returns
    -------
    list[dict]
        Each entry has ``"color"``, ``"linestyle"``, and ``"hue_family"`` keys.
        Primary predictions are solid; subordinate variants are dashed.

    Raises
    ------
    ValueError
        If the total curve count exceeds 7 (spec hard cap).
    """
    total = n_models * n_variants
    if total > 7:
        raise ValueError(
            f"Escalation ladder exhausted ({total} curves). "
            "Use small multiples instead of more colors."
        )

    hue_order = ["blue", "violet", "teal"]
    result: list[dict] = []

    for m in range(min(n_models, 3)):
        family = hue_order[m]
        ladder = _ESCALATION_LADDERS[family]
        for v in range(min(n_variants, 4)):
            result.append(
                {
                    "color": ladder[min(v, len(ladder) - 1)],
                    "linestyle": "-" if v == 0 else "--",
                    "hue_family": family,
                }
            )

    return result


# ---------------------------------------------------------------------------
# Direct labels
# ---------------------------------------------------------------------------
def apply_direct_labels(
    ax: Axes,
    curves: list[Line2D] | None = None,
    labels: list[str] | None = None,
    fontsize: float = 8.0,
    offset_pt: float = 4.0,
    max_stagger_pt: float = 20.0,
) -> None:
    """Place endpoint labels on curves with collision avoidance and halo.

    Labels sit at the right end of each curve, vertically aligned with
    the curve's final value. If curves converge, labels are staggered
    vertically with a minimum spacing of 2pt, clamped to *max_stagger_pt*
    so labels don't drift far from their data.

    Each label gets a white halo (semi-transparent background box) so
    text remains readable when placed over dark lines or filled regions.

    Parameters
    ----------
    ax : matplotlib Axes
    curves : list of Line2D, optional
        Lines to label. If ``None``, uses all lines on *ax*.
    labels : list of str, optional
        Text for each curve. If ``None``, uses each line's existing label.
    fontsize : float
        Font size in points (spec default: 8pt for annotations).
    offset_pt : float
        Horizontal offset in points from the rightmost data point.
    max_stagger_pt : float
        Maximum vertical displacement from a label's true y-position,
        in points.  Prevents labels from drifting far from their curve.
    """
    if curves is None:
        curves = [l for l in ax.get_lines() if l.get_label() and not l.get_label().startswith("_")]
    if labels is None:
        labels = [c.get_label() for c in curves]

    # Collect final y-positions in data coords
    positions: list[tuple[float, float, str, str]] = []  # (x, y, label, color)
    for curve, label in zip(curves, labels):
        xdata, ydata = curve.get_xdata(), curve.get_ydata()
        if len(xdata) == 0:
            continue
        positions.append((xdata[-1], ydata[-1], label, curve.get_color()))

    if not positions:
        return

    # Sort by y-position for collision avoidance
    positions.sort(key=lambda p: p[1])

    fig = ax.get_figure()
    dpi = fig.dpi
    inv = ax.transData.inverted()

    def _pt_to_data_y(pt: float) -> float:
        """Convert a distance in points to data-coordinate y-distance."""
        _, y0 = ax.transData.transform((0, 0))
        _, y1 = ax.transData.transform((0, 0))
        y1 = y0 + pt * dpi / 72.0
        _, dy = inv.transform((0, y1)) - inv.transform((0, y0))
        return abs(dy)

    min_gap = _pt_to_data_y(2.0)
    max_drift = _pt_to_data_y(max_stagger_pt)

    # Stagger overlapping labels, clamped to max_drift from original position
    adjusted_y = []
    for i, (x, y, lbl, col) in enumerate(positions):
        new_y = y
        if adjusted_y and (new_y - adjusted_y[-1]) < min_gap:
            new_y = adjusted_y[-1] + min_gap
        # Clamp: don't let the label drift more than max_stagger_pt from its curve
        new_y = min(new_y, y + max_drift)
        new_y = max(new_y, y - max_drift)
        adjusted_y.append(new_y)

    # White halo box for readability over dark lines/fills
    halo_bbox = dict(
        boxstyle="round,pad=0.15",
        facecolor="white",
        edgecolor="none",
        alpha=0.75,
    )

    # Place labels at adjusted positions
    for (x, y_orig, lbl, col), y_adj in zip(positions, adjusted_y):
        y_offset_pt = (y_adj - y_orig)
        # Convert y offset from data coords back to points
        _, y0_disp = ax.transData.transform((0, y_orig))
        _, y1_disp = ax.transData.transform((0, y_adj))
        y_off_display_pt = (y1_disp - y0_disp) * 72.0 / dpi

        ax.annotate(
            lbl,
            xy=(x, y_orig),
            xytext=(offset_pt, y_off_display_pt),
            textcoords="offset points",
            fontsize=fontsize,
            color=col,
            va="center",
            ha="left",
            annotation_clip=False,
            bbox=halo_bbox,
        )


# ---------------------------------------------------------------------------
# Uncertainty bands
# ---------------------------------------------------------------------------
def add_uncertainty_band(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    yerr_up: np.ndarray,
    yerr_down: np.ndarray | None = None,
    *,
    color: str | None = None,
    sigma: Literal[1, 2] = 1,
    label: str | None = None,
) -> None:
    """Draw an uncertainty band with design-system alpha and boundary styling.

    Parameters
    ----------
    ax : matplotlib Axes
    x, y : array-like
        Central value coordinates.
    yerr_up : array-like
        Upper uncertainty (positive offset from *y*).
    yerr_down : array-like, optional
        Lower uncertainty (positive offset below *y*). If ``None``,
        assumed symmetric with *yerr_up*.
    color : str, optional
        Fill color. Defaults to the current first cycle color.
    sigma : 1 or 2
        Which sigma level — controls opacity per spec.
    label : str, optional
        Band label for direct annotation.
    """
    if yerr_down is None:
        yerr_down = yerr_up

    alpha_key = f"unc_{sigma}sigma"
    alpha = _FILL_ALPHA.get(alpha_key, 0.14)

    if color is None:
        color = ax._get_lines.get_next_color()

    ax.fill_between(
        x,
        y - yerr_down,
        y + yerr_up,
        color=color,
        alpha=alpha,
        linewidth=0,
        label=label,
    )
    # Boundary lines: 0.5pt dashed
    ax.plot(x, y + yerr_up, color=color, linewidth=0.5, linestyle="--", alpha=0.6)
    ax.plot(x, y - yerr_down, color=color, linewidth=0.5, linestyle="--", alpha=0.6)


# ---------------------------------------------------------------------------
# Ratio panel helper
# ---------------------------------------------------------------------------
def make_ratio_panel(
    fig_width: float | None = None,
    height_ratio: float = 0.3,
) -> tuple[mpl.figure.Figure, tuple[Axes, Axes]]:
    """Create a figure with main + ratio panel per the design system spec.

    Parameters
    ----------
    fig_width : float, optional
        Figure width in inches. Defaults to the style-sheet value (3.346in).
    height_ratio : float
        Ratio panel height as a fraction of main panel height (spec: 0.3).

    Returns
    -------
    (fig, (ax_main, ax_ratio))
    """
    if fig_width is None:
        fig_width = mpl.rcParams.get("figure.figsize", [3.346, 2.510])[0]

    main_h = fig_width * 0.75  # 4:3
    ratio_h = main_h * height_ratio
    total_h = main_h + ratio_h

    fig, (ax_main, ax_ratio) = plt.subplots(
        2,
        1,
        figsize=(fig_width, total_h),
        height_ratios=[1, height_ratio],
        sharex=True,
        gridspec_kw={"hspace": 0.0},
    )

    # Separator: thin 0.5pt line between panels
    ax_main.spines["bottom"].set_linewidth(0.5)
    ax_ratio.spines["top"].set_visible(False)

    # Reference line at 1.0 in de-emphasis gray
    deemph = mpl.rcParams.get("legend.labelcolor", "#9ca3af")
    ax_ratio.axhline(1.0, color=deemph, linewidth=0.5, zorder=0)
    ax_ratio.set_ylabel(r"Ratio")

    return fig, (ax_main, ax_ratio)


# ---------------------------------------------------------------------------
# Overlap checker
# ---------------------------------------------------------------------------
def check_overlaps(
    fig: mpl.figure.Figure,
    min_gap_pt: float = 0.0,
) -> list[dict]:
    """Check for overlapping text elements in a matplotlib figure.

    Call this after plotting but before ``savefig()``.  The figure layout
    must be finalised first (this function calls ``fig.canvas.draw()``
    internally).

    Parameters
    ----------
    fig : matplotlib Figure
    min_gap_pt : float
        Minimum required gap between text bounding boxes, in points.
        Default 0 means any pixel overlap is flagged.

    Returns
    -------
    list[dict]
        Each entry has keys:

        - ``"text_a"``, ``"text_b"``: the overlapping label strings
        - ``"overlap_pt"``: overlap amount in points (positive = overlapping)
        - ``"bbox_a"``, ``"bbox_b"``: bounding boxes as (x0, y0, x1, y1) tuples
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    dpi = fig.dpi
    gap_px = min_gap_pt * dpi / 72.0

    # Collect visible, non-empty text objects
    texts: list[tuple[str, Bbox]] = []
    for obj in fig.findobj(Text):
        s = obj.get_text().strip()
        if not s or not obj.get_visible():
            continue
        try:
            bb = obj.get_window_extent(renderer)
        except RuntimeError:
            continue
        if bb.width == 0 or bb.height == 0:
            continue
        texts.append((s, bb))

    issues: list[dict] = []
    n = len(texts)
    for i in range(n):
        label_a, bb_a = texts[i]
        # Expand box by half the gap on each side
        a = Bbox.from_extents(
            bb_a.x0 - gap_px / 2, bb_a.y0 - gap_px / 2,
            bb_a.x1 + gap_px / 2, bb_a.y1 + gap_px / 2,
        )
        for j in range(i + 1, n):
            label_b, bb_b = texts[j]
            if not a.overlaps(bb_b):
                continue

            # Compute overlap amount (min penetration depth) in points
            dx = min(a.x1, bb_b.x1) - max(a.x0, bb_b.x0)
            dy = min(a.y1, bb_b.y1) - max(a.y0, bb_b.y0)
            overlap_px = min(dx, dy)
            overlap_pt = overlap_px * 72.0 / dpi

            issues.append({
                "text_a": label_a,
                "text_b": label_b,
                "overlap_pt": round(overlap_pt, 1),
                "bbox_a": (round(bb_a.x0, 1), round(bb_a.y0, 1),
                           round(bb_a.x1, 1), round(bb_a.y1, 1)),
                "bbox_b": (round(bb_b.x0, 1), round(bb_b.y0, 1),
                           round(bb_b.x1, 1), round(bb_b.y1, 1)),
            })

    return issues
