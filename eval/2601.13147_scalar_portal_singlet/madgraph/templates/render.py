"""
Render a jinja2 param_card template for the scalar portal singlet model.

Usage:
    python3 render.py BP1 /path/to/output/param_card_BP1.dat
    python3 render.py BP_mid /path/to/output/param_card_BP_mid.dat
    python3 render.py BP9 /path/to/output/param_card_BP9.dat
"""

import sys
from pathlib import Path

# Add paper directory to path
_paper_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_paper_dir))

from benchmarks.benchmark_points import BP1, BP_mid, BP9
from models.scalar_portal_singlet import lagrangian_params_from_physical

_BP_MAP = {"BP1": BP1, "BP_mid": BP_mid, "BP9": BP9}


def render(bp, template_path: str, out_path: str) -> None:
    """
    Render a jinja2 param_card template for a benchmark point.

    Parameters
    ----------
    bp            : ScalarPortalBP — benchmark point dataclass
    template_path : str — path to .j2 template file
    out_path      : str — output path for rendered card
    """
    try:
        from jinja2 import Template
    except ImportError:
        raise ImportError("jinja2 is required: pip install jinja2")

    # Derive Lagrangian parameters from physical inputs
    p = lagrangian_params_from_physical(
        bp.m_h1, bp.m_h2, bp.sin_theta, bp.lambda_s, bp.mu_3
    )

    context = {
        "m_chi": bp.m_chi,
        "g_chi": bp.g_chi,
        "sin_theta": bp.sin_theta,
        "m_h1": bp.m_h1,
        "m_h2": bp.m_h2,
        "lambda_s": bp.lambda_s,
        "mu_3": bp.mu_3,
        "lambda_h": p["lambda_h"],
        "lambda_hs": p["lambda_hs"],
        "mu_hs": p["mu_hs"],
        "mu_s_sq": p["mu_s_sq"],
    }

    template_text = Path(template_path).read_text()
    rendered = Template(template_text).render(**context)
    Path(out_path).write_text(rendered)
    print(f"Rendered {template_path} -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <BP_name> <output_path>")
        print(f"Available BPs: {list(_BP_MAP.keys())}")
        sys.exit(1)

    bp_name = sys.argv[1]
    out_path = sys.argv[2]

    if bp_name not in _BP_MAP:
        print(f"Unknown BP: {bp_name}. Available: {list(_BP_MAP.keys())}")
        sys.exit(1)

    bp = _BP_MAP[bp_name]
    template_path = Path(__file__).parent / f"param_card_{bp_name}.dat.j2"
    render(bp, str(template_path), out_path)
