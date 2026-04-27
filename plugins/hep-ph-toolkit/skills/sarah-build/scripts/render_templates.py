"""sarah-build render_templates: thin wrapper around modelspec_v3.render.

Public API:
    render(spec)            -> dict[str, str]   (filename → SARAH source)
    render_all(spec)        -> dict[str, str]   (alias of render; v3 native name)
    render_to_dir(spec, d)  -> None             (writes files under d)

This module is a compatibility shim. The actual rendering logic lives in
``plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/``.
"""
from __future__ import annotations

import pathlib
import sys

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_SHARED_DIR = _SCRIPT_DIR.parent.parent / "_shared"

if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from modelspec_v3.render import render_all  # noqa: E402


def render(spec: dict) -> dict[str, str]:
    """Render a v3 ModelSpec dict to SARAH .m files.

    Returns a dict mapping filename → file contents. Filenames are
    ``<Name>.m``, ``parameters.m``, and ``particles.m`` (no SPheno.m
    in v3 — SPheno emission is handled separately when requested).
    """
    return render_all(spec)


def render_to_dir(spec: dict, out_dir: pathlib.Path) -> None:
    """Render *spec* and write the .m files under *out_dir*."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in render(spec).items():
        (out_dir / name).write_text(content)


__all__ = ["render", "render_all", "render_to_dir"]


def main() -> None:
    """CLI: python3 render_templates.py <spec.yaml> <out_dir>."""
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <spec.yaml> <out_dir>", file=sys.stderr)
        sys.exit(2)
    from modelspec_v3.loader import load_spec  # noqa: PLC0415
    spec = load_spec(sys.argv[1])
    render_to_dir(spec, pathlib.Path(sys.argv[2]))
    print(f"Rendered to {sys.argv[2]}")


if __name__ == "__main__":
    main()
