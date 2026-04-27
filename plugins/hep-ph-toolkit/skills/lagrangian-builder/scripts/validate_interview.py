"""
validate_interview.py — turn interview answers into a ModelSpec YAML and validate it.

Usage:
    python3 validate_interview.py <answers.json>

    answers.json must be a JSON object with keys matching the interview
    questions in references/interview.md. See _build_spec() for required fields.

Outputs:
    On success: prints the generated YAML to stdout, exits 0.
    On failure: emits a MODELSPEC_INVALID blocker JSON to stderr, exits 1.

The generated spec is also validated by calling validate_spec.py from the
sarah-build skill (W3) via subprocess, so the same schema and semantic rules
apply here as in the full pipeline.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_VALIDATE_SPEC = (
    _SCRIPT_DIR / ".." / ".." / "sarah-build" / "scripts" / "validate_spec.py"
)


def _build_spec(answers: dict) -> dict:
    """
    Convert an interview answer dict into a ModelSpec dict.

    Required keys in answers:
        name            : str
        claim_source    : str
        sarah_version_required : str   (default ">=4.15,<4.16")
        gauge_groups    : list[dict]   — each: symbol, group, kind, coupling,
                                         gauge_boson, gaugino
        fermions        : list[dict]   — each: name, reps, hypercharge,
                                         generations, chirality
        scalars         : list[dict]   — may be []
        mass_terms      : list[dict]   — each: fields, coefficient, [hermitian_conjugate]
        yukawa_terms    : list[dict]   — may be []
        scalar_potential: list[dict]   — may be []
        parameters      : list[dict]   — each: name, latex, real, positive, default
        outputs         : list[str]    — e.g. ["ufo", "spheno"]
    """
    return {
        "spec_version": 1,
        "name": answers["name"],
        "claim_source": answers.get("claim_source", "interview"),
        "sarah_version_required": answers.get("sarah_version_required", ">=4.15,<4.16"),
        "gauge_groups": answers.get("gauge_groups", []),
        "fermions": answers.get("fermions", []),
        "scalars": answers.get("scalars", []),
        "lagrangian": {
            "mass_terms": answers.get("mass_terms", []),
            "yukawa_terms": answers.get("yukawa_terms", []),
            "scalar_potential": answers.get("scalar_potential", []),
        },
        "parameters": answers.get("parameters", []),
        "outputs": answers.get("outputs", ["ufo", "spheno"]),
    }


def _emit_blocker(message: str, context: dict | None = None) -> None:
    blocker: dict = {
        "code": "MODELSPEC_INVALID",
        "mode": "fatal",
        "message": message,
    }
    if context:
        blocker["context"] = context
    print(json.dumps(blocker), file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a ModelSpec from interview answers and validate it."
    )
    parser.add_argument("answers", help="Path to interview answers JSON file.")
    args = parser.parse_args()

    answers_path = Path(args.answers)
    if not answers_path.exists():
        _emit_blocker(f"answers file not found: {answers_path}")
        sys.exit(1)

    try:
        with open(answers_path) as f:
            answers = json.load(f)
    except json.JSONDecodeError as e:
        _emit_blocker(f"answers file is not valid JSON: {e}")
        sys.exit(1)

    # Build the spec dict
    try:
        spec = _build_spec(answers)
    except KeyError as e:
        _emit_blocker(f"missing required interview answer: {e}")
        sys.exit(1)

    # Serialise to YAML
    try:
        import yaml  # type: ignore[import]
    except ModuleNotFoundError:
        _emit_blocker("pyyaml is required (pip install pyyaml)")
        sys.exit(1)

    spec_yaml = yaml.dump(spec, default_flow_style=False, sort_keys=False)

    # Delegate validation to validate_spec.py (W3)
    if not _VALIDATE_SPEC.exists():
        # validate_spec.py not present; do basic schema-only check
        _emit_blocker(
            "validate_spec.py not found — cannot run full validation. "
            f"Expected at: {_VALIDATE_SPEC.resolve()}"
        )
        sys.exit(1)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix="_interview_spec.yaml", delete=False
    ) as tmp:
        tmp.write(spec_yaml)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, str(_VALIDATE_SPEC), tmp_path],
            capture_output=True,
            text=True,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        # Forward the blocker from validate_spec.py
        print(result.stderr, file=sys.stderr, end="")
        sys.exit(1)

    # Success: print the YAML
    print(spec_yaml)


if __name__ == "__main__":
    main()
