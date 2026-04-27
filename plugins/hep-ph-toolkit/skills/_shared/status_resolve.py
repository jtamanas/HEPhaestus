"""
status_resolve.py — static prereq status annotation for hep-ph-demo.

Public API:
    annotate(chain: list[str]) -> list[tuple[str, str]]
        Returns [(prereq_name, "EXISTS" | "PLANNED"), ...] for the given chain.

    missing(chain: list[str]) -> list[str]
        Returns the subset of chain entries whose status is "planned".

Both functions read `constraints.yaml` in the same directory as this module.
Status is STATIC (not probed at runtime) — flip `status:` in constraints.yaml
when a prereq ships.
"""

from __future__ import annotations

import pathlib
import yaml

_YAML_PATH = pathlib.Path(__file__).parent / "constraints.yaml"


def _load_prereqs() -> dict[str, dict]:
    with open(_YAML_PATH) as fh:
        data = yaml.safe_load(fh)
    return data["prereqs"]


def annotate(chain: list[str]) -> list[tuple[str, str]]:
    """Return [(prereq, 'EXISTS'|'PLANNED'), ...] for each name in chain.

    Parameters
    ----------
    chain:
        List of prereq skill names, e.g. ['sarah-build', 'spheno-build', 'maddm'].

    Returns
    -------
    list of (name, status_tag) tuples in the same order as chain.

    Raises
    ------
    KeyError if a prereq name is not registered in constraints.yaml.
    """
    prereqs = _load_prereqs()
    result = []
    for name in chain:
        if name not in prereqs:
            raise KeyError(f"Prereq '{name}' not found in constraints.yaml prereqs section.")
        status = prereqs[name]["status"]
        tag = "EXISTS" if status == "exists" else "PLANNED"
        result.append((name, tag))
    return result


def missing(chain: list[str]) -> list[str]:
    """Return the subset of chain entries whose status is 'planned'.

    Parameters
    ----------
    chain:
        List of prereq skill names.

    Returns
    -------
    List of names in chain that are not yet implemented.
    """
    annotated = annotate(chain)
    return [name for name, tag in annotated if tag == "PLANNED"]
