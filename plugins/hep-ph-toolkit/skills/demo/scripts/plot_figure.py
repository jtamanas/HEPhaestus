#!/usr/bin/env python3
"""Plot a scan_results.json produced by run_scan.py.

Reads the JSON's plot_kind and dispatches to one of:
  - 1d_overlay: scatter + analytical line (e.g. A1 blind-spot dip)
  - 2d_heatmap: sequential colormap over a (x, y) grid with optional
                exclusion contours
  - boltzmann:  Y(x) evolution traced from MadDM output

Style: hephaestus analytic context (theory-only papers have no
experimental affiliation; see /hep-plot §Style), black markers
(HEP convention), 200 dpi, tight bbox.

Prints a machine-readable summary line for the /demo orchestrator.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot a /demo scan result.")
    p.add_argument("--results", required=True,
                   help="Path to scan_results.json.")
    return p.parse_args(argv)


def _plot_1d_overlay(data: dict, ax) -> dict:
    import numpy as np
    xs = np.array([p["x"] for p in data["points"]])
    ys = np.array([p["y"] for p in data["points"]])

    overlay = data.get("analytical_overlay")
    if overlay is not None:
        ox = np.array(overlay["x"])
        oy = np.array(overlay["y"])
        oy_plot = np.where(oy > 0, oy, np.nan)
        ax.plot(ox, oy_plot, color="C0", lw=1.8, zorder=2,
                label=overlay.get("label", "Analytical"))

    ax.scatter(xs, ys, s=36, color="black", zorder=3,
               label="MG5/MadDM scan")

    if data.get("y_scale") == "log":
        ax.set_yscale("log")
    ax.set_xlabel(data.get("x_label", "x"))
    ax.set_ylabel(data.get("y_label", "y"))

    # Annotate the min (near the data, per plotting convention).
    min_idx = int(np.argmin(ys))
    mx, my = float(xs[min_idx]), float(ys[min_idx])
    max_y = float(np.nanmax(ys))
    orders = math.log10(max_y / max(my, 1e-80))

    y_lo, y_hi = ax.get_ylim()
    arrow_y = my * 30 if data.get("y_scale") == "log" else my + 0.2 * (y_hi - y_lo)
    if arrow_y > y_hi:
        arrow_y = 10 ** (0.5 * (math.log10(my) + math.log10(y_hi))) \
            if data.get("y_scale") == "log" else 0.5 * (my + y_hi)
    ax.annotate(
        f"min at x={mx:+.2f}",
        xy=(mx, my), xytext=(mx + 0.15 * (xs.max() - xs.min()), arrow_y),
        arrowprops=dict(arrowstyle="->", color="black", lw=1.1),
        fontsize=11, ha="left",
    )
    ax.legend(loc="lower right", frameon=False)
    return {"min_x": mx, "min_y": my, "orders": orders}


def _plot_2d_heatmap(data: dict, ax) -> dict:
    import numpy as np
    pts = data["points"]
    xs = np.array([p["x"] for p in pts])
    ys = np.array([p["y"] for p in pts])
    zs = np.array([p["z"] for p in pts])

    # Grid-reshape via sorted unique axes.
    ux = np.unique(xs)
    uy = np.unique(ys)
    Z = np.full((len(uy), len(ux)), np.nan)
    for p in pts:
        ix = int(np.where(ux == p["x"])[0][0])
        iy = int(np.where(uy == p["y"])[0][0])
        Z[iy, ix] = p["z"]

    import matplotlib.colors as mcolors
    norm = mcolors.LogNorm(
        vmin=max(np.nanmin(Z[Z > 0]), 1e-60),
        vmax=np.nanmax(Z),
    )
    im = ax.pcolormesh(ux, uy, Z, cmap="viridis", norm=norm, shading="auto")
    import matplotlib.pyplot as plt
    plt.colorbar(im, ax=ax, label=data.get("z_label", "z"))

    for contour in data.get("contours", []):
        ax.contour(ux, uy, Z, levels=[contour["level"]],
                   colors=contour.get("color", "white"), linewidths=1.5)

    ax.set_xlabel(data.get("x_label", "x"))
    ax.set_ylabel(data.get("y_label", "y"))

    min_idx = int(np.nanargmin(zs))
    return {
        "min_x": float(xs[min_idx]),
        "min_y": float(zs[min_idx]),
        "orders": math.log10(np.nanmax(zs) / max(np.nanmin(zs[zs > 0]), 1e-80)),
    }


def _plot_boltzmann(data: dict, ax) -> dict:
    import numpy as np
    # Expect points with x=T/m (or x=log10(T)) and y=Y(x).
    xs = np.array([p["x"] for p in data["points"]])
    ys = np.array([p["y"] for p in data["points"]])
    ax.plot(xs, ys, color="black", lw=1.5, label="Y(x) from MadDM")

    y_eq = data.get("equilibrium_trace")
    if y_eq is not None:
        ax.plot(y_eq["x"], y_eq["y"], color="C0", ls="--", lw=1.2,
                label=r"$Y_{\rm eq}$")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(data.get("x_label", "x = m/T"))
    ax.set_ylabel(data.get("y_label", "Y"))
    ax.legend(loc="lower left", frameon=False)

    return {
        "min_x": float(xs[np.argmin(ys)]),
        "min_y": float(np.min(ys)),
        "orders": math.log10(np.max(ys) / max(np.min(ys), 1e-80)),
    }


PLOT_KIND = {
    "1d_overlay": _plot_1d_overlay,
    "2d_heatmap": _plot_2d_heatmap,
    "boltzmann": _plot_boltzmann,
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    import matplotlib.pyplot as plt
    try:
        from styles.hep_ph_style import set_hep_context
    except ImportError:
        raise SystemExit(
            "styles.hep_ph_style not found. Ensure the hephaestus repo "
            "root is on PYTHONPATH, or run this script from there."
        )
    set_hep_context("analytic")

    results_path = Path(args.results).resolve()
    if not results_path.exists():
        raise SystemExit(f"Results file not found: {results_path}")
    data = json.loads(results_path.read_text())

    kind = data.get("plot_kind", "1d_overlay")
    if kind not in PLOT_KIND:
        raise SystemExit(f"Unknown plot_kind: {kind!r}")

    fig, ax = plt.subplots(figsize=(8, 6))
    summary = PLOT_KIND[kind](data, ax)

    ax.text(
        0.02, 0.97, data.get("description", ""),
        transform=ax.transAxes, va="top", ha="left", fontsize=11,
    )

    out_png = results_path.parent / "figure.png"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_png}")

    headline = data.get("headline", {})
    min_x = summary.get("min_x", headline.get("min_x"))
    min_y = summary.get("min_y", headline.get("min_y"))
    orders = summary.get("orders", headline.get("orders_suppressed"))
    paper = headline.get("paper_comparison", "n/a")

    print(f"MIN_X={min_x} MIN_Y={min_y} ORDERS={orders} PAPER_AGREEMENT={paper}")
    print("SUMMARY_JSON=" + json.dumps({
        "figure_png": str(out_png),
        "model": data.get("model"),
        "figure": data.get("figure"),
        "min_x": min_x, "min_y": min_y, "orders": orders,
        "paper_comparison": paper,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
