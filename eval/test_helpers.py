"""
Tests for hep_ph_style.py helper functions.

Exercises every public function and saves a composite output plot
to eval/test_helpers_output.png.
"""

from __future__ import annotations

import sys
from pathlib import Path

# -- ensure styles/ is importable --
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "styles"))

import matplotlib
matplotlib.use("Agg")  # headless backend, must come before pyplot import

# Disable LaTeX rendering if not available
import shutil
if shutil.which("latex") is None:
    matplotlib.rcParams["text.usetex"] = False

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection

import hep_ph_style as hps

PASS = "PASS"
FAIL = "FAIL"
results: list[tuple[str, str, str]] = []  # (test_name, status, detail)


def record(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))
    tag = f"  [{status}]"
    print(f"{tag} {name}" + (f" -- {detail}" if detail else ""))


# -----------------------------------------------------------------------
# 1. set_hep_context("analytic")
# -----------------------------------------------------------------------
def test_set_hep_context_analytic() -> None:
    name = 'set_hep_context("analytic")'
    try:
        palette = hps.set_hep_context("analytic")
        expected_keys = {"theory", "data", "secondary", "ink", "deemph"}
        if not isinstance(palette, dict):
            record(name, FAIL, f"Expected dict, got {type(palette).__name__}")
            return
        missing = expected_keys - set(palette.keys())
        extra = set(palette.keys()) - expected_keys
        if missing:
            record(name, FAIL, f"Missing keys: {missing}")
        elif extra:
            record(name, FAIL, f"Unexpected keys: {extra}")
        else:
            record(name, PASS)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# 2. set_hep_context("slate")
# -----------------------------------------------------------------------
def test_set_hep_context_slate() -> None:
    name = 'set_hep_context("slate")'
    try:
        palette = hps.set_hep_context("slate")
        expected_keys = {"theory", "observed", "excluded", "ink", "deemph"}
        if not isinstance(palette, dict):
            record(name, FAIL, f"Expected dict, got {type(palette).__name__}")
            return
        missing = expected_keys - set(palette.keys())
        extra = set(palette.keys()) - expected_keys
        if missing:
            record(name, FAIL, f"Missing keys: {missing}")
        elif extra:
            record(name, FAIL, f"Unexpected keys: {extra}")
        else:
            record(name, PASS)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# 3. escalate_colors(2, 3) -- 6 entries, correct linestyles
# -----------------------------------------------------------------------
def test_escalate_colors_2_3() -> None:
    name = "escalate_colors(2, 3)"
    try:
        entries = hps.escalate_colors(2, 3)
        if not isinstance(entries, list):
            record(name, FAIL, f"Expected list, got {type(entries).__name__}")
            return
        if len(entries) != 6:
            record(name, FAIL, f"Expected 6 entries, got {len(entries)}")
            return
        # Check keys
        required_keys = {"color", "linestyle", "hue_family"}
        for i, e in enumerate(entries):
            if required_keys - set(e.keys()):
                record(name, FAIL, f"Entry {i} missing keys: {required_keys - set(e.keys())}")
                return
        # First variant of each model (index 0, 3) should be solid "-"
        # Second variant (index 1, 4) should be dashed "--"
        if entries[0]["linestyle"] != "-":
            record(name, FAIL, f"Entry 0 linestyle should be '-', got '{entries[0]['linestyle']}'")
            return
        if entries[1]["linestyle"] != "--":
            record(name, FAIL, f"Entry 1 linestyle should be '--', got '{entries[1]['linestyle']}'")
            return
        if entries[3]["linestyle"] != "-":
            record(name, FAIL, f"Entry 3 linestyle should be '-', got '{entries[3]['linestyle']}'")
            return
        if entries[4]["linestyle"] != "--":
            record(name, FAIL, f"Entry 4 linestyle should be '--', got '{entries[4]['linestyle']}'")
            return
        record(name, PASS)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# 4. escalate_colors(3, 3) -- should raise ValueError (9 > 7)
# -----------------------------------------------------------------------
def test_escalate_colors_overflow() -> None:
    name = "escalate_colors(3, 3) raises ValueError"
    try:
        hps.escalate_colors(3, 3)
        record(name, FAIL, "No exception raised")
    except ValueError:
        record(name, PASS)
    except Exception as exc:
        record(name, FAIL, f"Wrong exception type: {type(exc).__name__}: {exc}")


# -----------------------------------------------------------------------
# 5. make_ratio_panel()
# -----------------------------------------------------------------------
def test_make_ratio_panel() -> None:
    name = "make_ratio_panel()"
    try:
        fig, (ax_main, ax_ratio) = hps.make_ratio_panel()
        # Both axes must exist
        if ax_main is None or ax_ratio is None:
            record(name, FAIL, "One of the axes is None")
            return
        # Check they are Axes instances
        from matplotlib.axes import Axes
        if not isinstance(ax_main, Axes):
            record(name, FAIL, f"ax_main is {type(ax_main).__name__}, not Axes")
            return
        if not isinstance(ax_ratio, Axes):
            record(name, FAIL, f"ax_ratio is {type(ax_ratio).__name__}, not Axes")
            return
        # Ratio panel should share x-axis with main
        # When sharex=True, get_shared_x_axes() group should contain both
        if not ax_main.get_shared_x_axes().joined(ax_main, ax_ratio):
            record(name, FAIL, "Ratio panel does not share x-axis with main")
            return
        record(name, PASS)
        plt.close(fig)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# 6. apply_direct_labels()
# -----------------------------------------------------------------------
def test_apply_direct_labels() -> None:
    name = "apply_direct_labels(ax, ...)"
    try:
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 50)
        (line1,) = ax.plot(x, np.sin(x), label="Model A")
        (line2,) = ax.plot(x, np.cos(x), label="Model B")
        hps.apply_direct_labels(ax, curves=[line1, line2], labels=["Model A", "Model B"])
        # If we get here without error, PASS
        record(name, PASS)
        plt.close(fig)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# 7. add_uncertainty_band()
# -----------------------------------------------------------------------
def test_add_uncertainty_band() -> None:
    name = "add_uncertainty_band(ax, x, y, yerr_up)"
    try:
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 50)
        y = np.sin(x)
        yerr = 0.2 * np.ones_like(x)
        hps.add_uncertainty_band(ax, x, y, yerr)
        # Check that fill_between created a PolyCollection
        polys = [c for c in ax.collections if isinstance(c, PolyCollection)]
        if len(polys) == 0:
            record(name, FAIL, "No PolyCollection found (fill_between not drawn)")
            return
        record(name, PASS)
        plt.close(fig)
    except Exception as exc:
        record(name, FAIL, str(exc))


# -----------------------------------------------------------------------
# Composite output plot
# -----------------------------------------------------------------------
def make_output_plot() -> None:
    """Generate a composite figure exercising multiple helpers."""
    # Disable usetex for output plot safety
    matplotlib.rcParams["text.usetex"] = False

    fig = plt.figure(figsize=(10, 8))
    fig.suptitle("hep_ph_style.py -- test output", fontsize=12)

    # Panel 1: escalation colors demo
    ax1 = fig.add_subplot(2, 2, 1)
    entries = hps.escalate_colors(2, 3)
    x = np.linspace(0, 5, 100)
    for i, e in enumerate(entries):
        ax1.plot(x, np.sin(x + i * 0.5), color=e["color"],
                 linestyle=e["linestyle"], label=f'{e["hue_family"]}_{i}')
    ax1.set_title("escalate_colors(2,3)", fontsize=9)
    ax1.legend(fontsize=6)

    # Panel 2: uncertainty band
    ax2 = fig.add_subplot(2, 2, 2)
    x = np.linspace(0, 10, 80)
    y = np.sin(x)
    yerr = 0.15 + 0.1 * np.abs(np.cos(x))
    ax2.plot(x, y, color="#0284c7", linewidth=1)
    hps.add_uncertainty_band(ax2, x, y, yerr, color="#0284c7")
    ax2.set_title("add_uncertainty_band", fontsize=9)

    # Panel 3: direct labels
    ax3 = fig.add_subplot(2, 2, 3)
    x = np.linspace(0, 8, 60)
    lines = []
    for i, lbl in enumerate(["NLO", "NNLO", "N3LO"]):
        (ln,) = ax3.plot(x, np.sin(x + i * 0.3) + i * 0.2, label=lbl)
        lines.append(ln)
    hps.apply_direct_labels(ax3, curves=lines)
    ax3.set_title("apply_direct_labels", fontsize=9)

    # Panel 4: ratio panel
    fig_ratio, (ax_m, ax_r) = hps.make_ratio_panel()
    x = np.linspace(1, 100, 80)
    ax_m.plot(x, x**2, label="data")
    ax_m.plot(x, 1.05 * x**2, label="theory")
    ax_r.plot(x, 1.05 * np.ones_like(x))
    ax_r.set_xlabel("x")
    ax_m.set_ylabel("counts")
    output_ratio = ROOT / "eval" / "test_helpers_ratio_panel.png"
    fig_ratio.savefig(str(output_ratio), dpi=150)
    plt.close(fig_ratio)

    # Draw a note in panel 4 of the composite
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.text(0.5, 0.5, "Ratio panel saved\nseparately\n(see ratio_panel.png)",
             ha="center", va="center", fontsize=10, transform=ax4.transAxes)
    ax4.set_title("make_ratio_panel", fontsize=9)
    ax4.axis("off")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    output = ROOT / "eval" / "test_helpers_output.png"
    fig.savefig(str(output), dpi=150)
    plt.close(fig)
    print(f"\nOutput plot saved to: {output}")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("hep_ph_style.py -- test suite")
    print("=" * 60)

    test_set_hep_context_analytic()
    test_set_hep_context_slate()
    test_escalate_colors_2_3()
    test_escalate_colors_overflow()
    test_make_ratio_panel()
    test_apply_direct_labels()
    test_add_uncertainty_band()

    print("\n" + "=" * 60)
    n_pass = sum(1 for _, s, _ in results if s == PASS)
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    print(f"Results: {n_pass} passed, {n_fail} failed out of {len(results)} tests")
    print("=" * 60)

    # Generate composite output plot regardless of test results
    try:
        make_output_plot()
    except Exception as exc:
        print(f"\nFailed to generate output plot: {exc}")

    sys.exit(1 if n_fail > 0 else 0)
