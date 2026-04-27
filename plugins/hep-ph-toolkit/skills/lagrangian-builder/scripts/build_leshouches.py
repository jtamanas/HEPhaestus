"""
build_leshouches.py — thin wrapper over spheno-build's leshouches_template.py.

Keeps the /lagrangian-builder surface consistent: callers invoke this script
rather than reaching directly into the spheno-build skill directory.

Usage:
    python3 build_leshouches.py <spec.yaml> [--override NAME=VALUE ...]

Prints the LesHouches input string to stdout.
Exits 0 on success; exits 1 on error.

spec.yaml must conform to plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/schema.json.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
# leshouches_template.py lives at:
#   plugins/hep-ph-toolkit/skills/spheno-build/scripts/leshouches_template.py
_TEMPLATE_DIR = (
    _SCRIPT_DIR / ".." / ".." / "spheno-build" / "scripts"
)
sys.path.insert(0, str(_TEMPLATE_DIR.resolve()))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a LesHouches input card from a ModelSpec YAML."
    )
    parser.add_argument("spec", help="Path to ModelSpec YAML.")
    parser.add_argument(
        "--override",
        action="append",
        metavar="NAME=VALUE",
        default=[],
        help="Override a parameter value, e.g. --override MpsiD=300.",
    )
    args = parser.parse_args()

    try:
        import yaml  # type: ignore[import]
    except ModuleNotFoundError:
        print("error: pyyaml is required (pip install pyyaml)", file=sys.stderr)
        sys.exit(1)

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"error: spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    overrides: dict[str, float] = {}
    for item in args.override:
        if "=" not in item:
            print(f"error: invalid override syntax {item!r} (use NAME=VALUE)", file=sys.stderr)
            sys.exit(1)
        k, v = item.split("=", 1)
        try:
            overrides[k.strip()] = float(v.strip())
        except ValueError:
            print(f"error: override value must be numeric: {item!r}", file=sys.stderr)
            sys.exit(1)

    try:
        import leshouches_template  # type: ignore[import]
    except ModuleNotFoundError:
        print(
            "error: leshouches_template.py not found at expected location: "
            f"{_TEMPLATE_DIR.resolve()}",
            file=sys.stderr,
        )
        sys.exit(1)

    result = leshouches_template.build(spec, overrides if overrides else None)
    print(result)


if __name__ == "__main__":
    main()
