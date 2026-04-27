#!/usr/bin/env python3
"""Test the Cool Analytic matplotlib style sheet.

Loads the hephaestus-analytic.mplstyle, creates a fake theory-vs-data plot,
saves it to eval/test_analytic_output.png, and verifies rcParams were applied.
"""

import os
import sys
import numpy as np

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
STYLE_PATH = os.path.join(REPO_ROOT, "styles", "hephaestus-analytic.mplstyle")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "test_analytic_output.png")

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt


def load_style_with_fallback(style_path: str) -> list[str]:
    """Load the style sheet, falling back on text.usetex if LaTeX is missing.

    Returns a list of warnings encountered.
    """
    warnings = []

    # First attempt: load as-is
    try:
        plt.style.use(style_path)
    except Exception as e:
        warnings.append(f"Initial style load failed: {e}")
        raise

    # Check if usetex is True but LaTeX is unavailable
    if matplotlib.rcParams.get("text.usetex", False):
        try:
            # Quick probe: try to render a tiny figure with LaTeX
            fig_probe, ax_probe = plt.subplots(figsize=(1, 1))
            ax_probe.set_title(r"$x$")
            fig_probe.savefig(os.devnull, format="png")
            plt.close(fig_probe)
        except Exception as e:
            warnings.append(
                f"LaTeX not available ({e}); falling back to text.usetex=False"
            )
            matplotlib.rcParams["text.usetex"] = False

    return warnings


def verify_rcparams() -> list[str]:
    """Verify key rcParams were applied. Returns a list of failures."""
    failures = []

    checks = {
        "axes.spines.top": (matplotlib.rcParams["axes.spines.top"], False),
        "axes.spines.right": (matplotlib.rcParams["axes.spines.right"], False),
        "axes.grid": (matplotlib.rcParams["axes.grid"], False),
    }

    for name, (actual, expected) in checks.items():
        if actual != expected:
            failures.append(f"  {name}: expected {expected!r}, got {actual!r}")

    # Figure size: approximately 3.346 x 2.510 (tolerance 0.01)
    figsize = matplotlib.rcParams["figure.figsize"]
    if abs(figsize[0] - 3.346) > 0.01 or abs(figsize[1] - 2.510) > 0.01:
        failures.append(
            f"  figure.figsize: expected ~[3.346, 2.510], got {figsize}"
        )

    return failures


def make_theory_vs_data_plot():
    """Create a fake theory-vs-data plot and save it."""

    # --- Fake data ---
    np.random.seed(42)
    x_theory = np.linspace(0.5, 10.0, 200)
    # Theory curve: some smooth function
    y_theory = 50.0 * x_theory ** (-2.5)
    # Uncertainty band: +/- 15% growing at low x
    y_upper = y_theory * (1 + 0.15 / np.sqrt(x_theory))
    y_lower = y_theory * (1 - 0.15 / np.sqrt(x_theory))

    # Data points: sampled from theory with noise
    x_data = np.array([1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    y_data_true = 50.0 * x_data ** (-2.5)
    y_data = y_data_true * (1 + 0.12 * np.random.randn(len(x_data)))
    y_err = y_data_true * 0.10

    # --- Plot ---
    fig, ax = plt.subplots()

    # Theory uncertainty band (first color in cycle = blue)
    ax.fill_between(x_theory, y_lower, y_upper, alpha=0.25, color="#0284c7",
                    label="Theory uncertainty")

    # Theory curve
    ax.plot(x_theory, y_theory, color="#0284c7", label="NLO prediction")

    # Data points (second color in cycle = orange)
    ax.errorbar(x_data, y_data, yerr=y_err, fmt="o", color="#ea580c",
                markersize=4, label="CMS data")

    # Labels
    usetex = matplotlib.rcParams.get("text.usetex", False)
    if usetex:
        ax.set_xlabel(r"$\sqrt{s}$ [TeV]", style="italic")
        ax.set_ylabel(r"$\sigma$ [pb]", style="italic")
    else:
        ax.set_xlabel("sqrt(s) [TeV]")
        ax.set_ylabel("sigma [pb]")

    ax.set_yscale("log")
    ax.legend(loc="upper right")

    fig.savefig(OUTPUT_PATH)
    plt.close(fig)


def main():
    print(f"Style sheet: {STYLE_PATH}")
    print(f"Output:      {OUTPUT_PATH}")
    print()

    # 1. Load style
    print("[1/4] Loading style sheet...")
    try:
        warnings = load_style_with_fallback(STYLE_PATH)
    except Exception as e:
        print(f"FAIL: could not load style sheet: {e}")
        sys.exit(1)

    for w in warnings:
        print(f"  WARNING: {w}")
    print("  OK")

    # 2. Verify rcParams
    print("[2/4] Verifying rcParams...")
    failures = verify_rcparams()
    if failures:
        print("  FAIL: some rcParams did not match expected values:")
        for f in failures:
            print(f)
    else:
        print("  OK")

    # 3. Generate plot
    print("[3/4] Generating theory-vs-data plot...")
    try:
        make_theory_vs_data_plot()
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")
        sys.exit(1)

    # 4. Check output file
    print("[4/4] Verifying output file...")
    if os.path.isfile(OUTPUT_PATH):
        size_kb = os.path.getsize(OUTPUT_PATH) / 1024
        print(f"  OK: {OUTPUT_PATH} ({size_kb:.1f} KB)")
    else:
        print(f"  FAIL: {OUTPUT_PATH} not found")
        sys.exit(1)

    # Summary
    print()
    if failures:
        print(f"DONE with {len(failures)} rcParam verification failure(s).")
        sys.exit(1)
    else:
        print("DONE: all checks passed.")


if __name__ == "__main__":
    main()
