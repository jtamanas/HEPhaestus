"""render_driver.py — pure-Python renderer for FeynArts driver templates.

Uses str.format() only (no Jinja2 or other dependencies).
Token dict is passed directly; no implicit context.
"""
from __future__ import annotations

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent

# Template file names
DRIVER_TPL = _TEMPLATE_DIR / "driver.m.tpl"
MAKE_FEYNARTS_TPL = _TEMPLATE_DIR / "make_feynarts_driver.m.tpl"


def render_driver(
    run_dir: str,
    loop_order: int,
    n_in: int,
    n_out: int,
    excludes_m: str,
    process_tuple: str,
    model_name: str,
    feynarts_version: str,
    model_hash: str,
    diagram_cap: int = 2000,
    template_path: str | None = None,
) -> str:
    """Render the main FeynArts driver script.

    Args:
        run_dir: Working directory for wolframscript (absolute path).
        loop_order: Loop order (0, 1, ...).
        n_in: Number of initial-state particles.
        n_out: Number of final-state particles.
        excludes_m: Mathematica list of excluded topology classes, e.g.
            'Tadpoles, SelfEnergies' (without outer braces; template adds them).
        process_tuple: FeynArts process tuple, e.g.
            '{{F[2,{1}], -F[2,{1}]}, {F[2,{2}], -F[2,{2}]}}'.
        model_name: FeynArts model name string.
        feynarts_version: Version string (e.g. "3.11").
        model_hash: SHA256 of .mod file.
        diagram_cap: Maximum diagram count before aborting.
        template_path: Override template file path.

    Returns:
        Rendered Mathematica script as a string.
    """
    tpl_path = Path(template_path) if template_path else DRIVER_TPL
    template = tpl_path.read_text()

    return template.format(
        run_dir=run_dir,
        loop_order=loop_order,
        n_in=n_in,
        n_out=n_out,
        excludes_m=excludes_m,
        process_tuple=process_tuple,
        model_name=model_name,
        feynarts_version=feynarts_version,
        model_hash=model_hash,
        diagram_cap=diagram_cap,
    )


def render_make_feynarts_driver(
    feynarts_state_dir: str,
    sarah_path: str,
    model_name: str,
    template_path: str | None = None,
) -> str:
    """Render the post-hoc SARAH MakeFeynArts[] driver script.

    Args:
        feynarts_state_dir: Directory where .mod/.gen will be written.
        sarah_path: Path to SARAH package directory.
        model_name: SARAH model name.
        template_path: Override template file path.

    Returns:
        Rendered Mathematica script as a string.
    """
    tpl_path = Path(template_path) if template_path else MAKE_FEYNARTS_TPL
    template = tpl_path.read_text()

    return template.format(
        feynarts_state_dir=feynarts_state_dir,
        sarah_path=sarah_path,
        model_name=model_name,
    )
