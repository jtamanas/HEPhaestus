#!/usr/bin/env python3
"""
Test the hephaestus Slate Precision matplotlib style sheet.

Produces a fake exclusion contour plot and verifies that rcParams
are set correctly by the style sheet.
"""

import sys
import os
import pathlib

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
STYLE_PATH = PROJECT_ROOT / "styles" / "hephaestus-slate.mplstyle"
OUTPUT_PATH = PROJECT_ROOT / "eval" / "test_slate_output.png"

# ---------------------------------------------------------------------------
# Pre-flight: does the style sheet exist?
# ---------------------------------------------------------------------------
if not STYLE_PATH.is_file():
    print(f"FAIL: style sheet not found at {STYLE_PATH}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Load matplotlib and try the style sheet
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")  # headless backend, must come before pyplot import
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# First, try loading the style sheet to catch parse errors early
try:
    plt.style.use(str(STYLE_PATH))
    print(f"OK: style sheet loaded from {STYLE_PATH}")
except Exception as exc:
    print(f"FAIL: could not load style sheet: {exc}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# LaTeX fallback: if usetex is True but LaTeX is not available, disable it
# ---------------------------------------------------------------------------
if matplotlib.rcParams.get("text.usetex"):
    try:
        # Quick probe: render a tiny figure with LaTeX
        fig_probe, ax_probe = plt.subplots(figsize=(1, 1))
        ax_probe.set_title(r"$\mu$")
        from io import BytesIO
        fig_probe.savefig(BytesIO(), format="png")
        plt.close(fig_probe)
        print("OK: LaTeX rendering available")
    except Exception as exc:
        print(f"WARN: LaTeX not available ({exc}); falling back to text.usetex=False")
        matplotlib.rcParams["text.usetex"] = False

# ---------------------------------------------------------------------------
# 1. Verify selected rcParams
# ---------------------------------------------------------------------------
failures = []

def check_param(key, expected, *, approx=False):
    actual = matplotlib.rcParams.get(key)
    if approx:
        if abs(float(actual) - float(expected)) > 0.01:
            failures.append(f"  {key}: expected ~{expected}, got {actual}")
    else:
        if str(actual).lower() != str(expected).lower():
            failures.append(f"  {key}: expected {expected!r}, got {actual!r}")

check_param("axes.spines.top", False)
check_param("axes.spines.right", False)
check_param("axes.spines.left", True)
check_param("axes.spines.bottom", True)

# Slate ink colour #334155
check_param("axes.edgecolor", "#334155")
check_param("axes.labelcolor", "#334155")
check_param("xtick.color", "#334155")
check_param("ytick.color", "#334155")

check_param("figure.dpi", 300, approx=True)
check_param("savefig.dpi", 300, approx=True)
check_param("axes.grid", False)
check_param("legend.frameon", False)
check_param("xtick.direction", "in")
check_param("ytick.direction", "in")
check_param("xtick.minor.visible", True)
check_param("ytick.minor.visible", True)

if failures:
    print("rcParam verification FAILURES:")
    for f in failures:
        print(f)
else:
    print("OK: all rcParam checks passed")

# ---------------------------------------------------------------------------
# 2. Create exclusion contour plot
# ---------------------------------------------------------------------------
# Fake model: excluded region in (m_X, sigma) space
m_x = np.linspace(100, 1000, 200)
sigma = np.logspace(-2, 2, 200)
M, S = np.meshgrid(m_x, sigma)

# Fake "exclusion function": CL_s < 0.05 below some boundary
# Observed limit: a curved boundary (1-D, function of m_x only)
obs_limit_1d = 0.5 * np.exp(-((m_x - 400) ** 2) / (2 * 250 ** 2)) + 0.02
# Expected limit: slightly different (1-D)
exp_limit_1d = 0.6 * np.exp(-((m_x - 420) ** 2) / (2 * 260 ** 2)) + 0.03

# 2-D versions for contourf
obs_limit_2d = 0.5 * np.exp(-((M - 400) ** 2) / (2 * 250 ** 2)) + 0.02

# CL_s values (lower = more excluded)
cl_s = S / (obs_limit_2d * 100)

fig, ax = plt.subplots()

# Excluded region: contourf with muted red at low alpha
excluded_color = mcolors.to_rgba("#dc2626", alpha=0.15)
ax.contourf(
    M, S, cl_s,
    levels=[0, 1.0],
    colors=[excluded_color],
)

# 1-sigma and 2-sigma expected bands (yellow/green convention)
band_1sigma_color = mcolors.to_rgba("#facc15", alpha=0.4)
band_2sigma_color = mcolors.to_rgba("#fde68a", alpha=0.3)

# Expected limit band (approximate +/- 1 sigma)
for band_color, factor, label in [
    (band_2sigma_color, 1.4, r"Expected $\pm 2\sigma$"),
    (band_1sigma_color, 1.2, r"Expected $\pm 1\sigma$"),
]:
    upper = exp_limit_1d * 100 * factor
    lower = exp_limit_1d * 100 / factor
    ax.fill_between(m_x, lower, upper, color=band_color, label=label)

# Expected limit (dashed)
ax.plot(
    m_x,
    exp_limit_1d * 100,
    color="#1a1a1a",
    linestyle="--",
    linewidth=1.0,
    label="Expected limit",
)

# Observed limit (solid black, 1.2pt)
ax.plot(
    m_x,
    obs_limit_1d * 100,
    color="#1a1a1a",
    linestyle="-",
    linewidth=1.2,
    label="Observed limit",
)

ax.set_yscale("log")
ax.set_xlabel(r"$m_X$ [GeV]")
ax.set_ylabel(r"$\sigma \times \mathrm{BR}$ [fb]")
ax.set_title(r"Slate Precision style test — exclusion contour", fontsize=9)
ax.set_xlim(100, 1000)
ax.set_ylim(0.1, 100)

ax.legend(loc="upper right", fontsize=7)

fig.savefig(str(OUTPUT_PATH))
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Verify output
# ---------------------------------------------------------------------------
if OUTPUT_PATH.is_file() and OUTPUT_PATH.stat().st_size > 0:
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"OK: output saved to {OUTPUT_PATH} ({size_kb:.1f} KB)")
else:
    print(f"FAIL: output file not created or empty at {OUTPUT_PATH}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if failures:
    print(f"\nDONE with {len(failures)} rcParam issue(s) — see above.")
    sys.exit(1)
else:
    print("\nDONE: all checks passed, plot saved successfully.")
    sys.exit(0)
