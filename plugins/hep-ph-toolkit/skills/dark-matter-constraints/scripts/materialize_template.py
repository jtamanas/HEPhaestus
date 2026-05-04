"""materialize_template.py — CLASS template materialiser (D8 / §4.4).

Reads a YAML template as raw text, substitutes ``{{key}}`` placeholders
with values from a JSON overrides dict, and writes the result to an output
file.

Rules:
- Any ``{{key}}`` in the template that has no matching overrides entry → SystemExit(2).
- Any overrides key that does not appear in the template → SystemExit(2).

Usage::

    python materialize_template.py --template path/to/template.yaml \\
                                   --overrides '{"Gamma_dcdm": 1.0e-29}' \\
                                   --out path/to/output.yaml
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


# Pattern that matches {{ key }} with optional surrounding whitespace
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def materialize_template(template_text: str, overrides: dict) -> str:
    """Substitute ``{{key}}`` placeholders in *template_text* with *overrides* values.

    Parameters
    ----------
    template_text:
        Raw template string (not parsed as YAML).
    overrides:
        Dict mapping placeholder key → replacement value.

    Returns
    -------
    str
        Template text with all placeholders substituted.

    Raises
    ------
    SystemExit(2)
        If a placeholder in the template is absent from overrides, or if an
        overrides key is never used in the template.
    """
    # Collect all placeholder keys used in the template
    used_keys = set(_PLACEHOLDER_RE.findall(template_text))
    override_keys = set(overrides.keys())

    missing_overrides = used_keys - override_keys
    if missing_overrides:
        print(
            f"materialize_template: template uses {{{{key}}}} placeholders with no "
            f"matching overrides: {sorted(missing_overrides)}",
            file=sys.stderr,
        )
        sys.exit(2)

    unused_overrides = override_keys - used_keys
    if unused_overrides:
        print(
            f"materialize_template: overrides keys not used in template: "
            f"{sorted(unused_overrides)}",
            file=sys.stderr,
        )
        sys.exit(2)

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        return str(overrides[key])

    return _PLACEHOLDER_RE.sub(_replace, template_text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialise a {{key}} template file with JSON overrides.",
    )
    parser.add_argument("--template", required=True, help="Path to template file.")
    parser.add_argument(
        "--overrides",
        required=True,
        help="JSON object string mapping placeholder keys to values.",
    )
    parser.add_argument("--out", required=True, help="Output file path.")
    args = parser.parse_args()

    template_path = pathlib.Path(args.template)
    if not template_path.exists():
        print(f"materialize_template: template file not found: {template_path}", file=sys.stderr)
        sys.exit(2)

    try:
        overrides = json.loads(args.overrides)
    except json.JSONDecodeError as exc:
        print(f"materialize_template: invalid --overrides JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    template_text = template_path.read_text()
    result = materialize_template(template_text, overrides)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result)


if __name__ == "__main__":
    main()
