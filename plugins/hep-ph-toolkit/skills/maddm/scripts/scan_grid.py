"""Parameter space grid generation and batch orchestration for MadDM.

Generate grids of parameter points and batch MadDM scripts.
Library functions Claude composes per-task — not CLI executables.
"""

from __future__ import annotations

import itertools
import math
import re


def make_grid(
    param_ranges: dict[str, tuple[float, float, int]],
    spacing: str = "linear",
) -> list[dict[str, float]]:
    """Generate a parameter space grid.

    Args:
        param_ranges: Dict mapping 'BLOCK:PID' names to
            (min, max, n_points) tuples.
        spacing: 'linear' or 'log' for all axes.

    Returns:
        List of dicts, each mapping parameter names to values.

    Example:
        grid = make_grid({
            "MASS:9000006": (10.0, 1000.0, 20),
            "DMINPUTS:1": (0.01, 4.0, 10),
        }, spacing="log")
    """
    axes = {}
    for name, (lo, hi, n) in param_ranges.items():
        if n < 1:
            raise ValueError(f"n_points must be >= 1, got {n} for {name}")
        if n == 1:
            axes[name] = [lo]
            continue
        if spacing == "log":
            if lo <= 0 or hi <= 0:
                raise ValueError(
                    f"Log spacing requires positive bounds, "
                    f"got ({lo}, {hi}) for {name}"
                )
            log_lo, log_hi = math.log(lo), math.log(hi)
            axes[name] = [
                math.exp(log_lo + i * (log_hi - log_lo) / (n - 1))
                for i in range(n)
            ]
        else:
            axes[name] = [
                lo + i * (hi - lo) / (n - 1) for i in range(n)
            ]

    names = list(axes.keys())
    points = list(itertools.product(*(axes[n] for n in names)))
    return [dict(zip(names, pt)) for pt in points]


def generate_batch(
    grid: list[dict[str, float]],
    template_script: str,
) -> list[str]:
    """Create a batch of MadDM scripts from a parameter grid.

    Replaces ``set BLOCK PID <value>`` lines in the template with
    each grid point's parameter values.

    Args:
        grid: List of parameter dicts from make_grid.
        template_script: MadDM script string containing
            ``set BLOCK PID <value>`` lines.

    Returns:
        List of script strings, one per grid point.
    """
    scripts = []
    for point in grid:
        script = template_script
        for param_key, value in point.items():
            block, pid = param_key.split(":")
            pattern = (
                rf"(set\s+{re.escape(block)}\s+{re.escape(pid)}\s+)"
                rf"[\d.eE+-]+"
            )
            script = re.sub(
                pattern, rf"\g<1>{value}", script, flags=re.IGNORECASE
            )
        scripts.append(script)

    return scripts
