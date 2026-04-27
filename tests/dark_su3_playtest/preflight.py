"""Component C — --spec pre-flight gate for WS-3 Dark SU(3) playtest.

Reads SKILL.md and asserts the --spec flag string is present before any LLM
invocation. If absent, raises SpecFlagMissingError with code WS3_SPEC_FLAG_MISSING.

Usage as CLI::

    python preflight.py --skill-md plugins/hep-ph-toolkit/skills/dark-matter-constraints/SKILL.md

Exit 0 on pass, 1 on missing flag.
"""

from __future__ import annotations

import pathlib
import sys


class SpecFlagMissingError(RuntimeError):
    """Raised when --spec flag is absent from SKILL.md."""

    code: str = "WS3_SPEC_FLAG_MISSING"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.code = "WS3_SPEC_FLAG_MISSING"


def preflight_spec_flag(skill_md_path: pathlib.Path) -> None:
    """Assert --spec flag is present in SKILL.md.

    Parameters
    ----------
    skill_md_path:
        Absolute or relative path to SKILL.md to check.

    Raises
    ------
    SpecFlagMissingError
        If --spec is not found in the file content.
    FileNotFoundError
        If skill_md_path does not exist.
    """
    content = skill_md_path.read_text(encoding="utf-8")
    if "--spec" not in content:
        raise SpecFlagMissingError(
            f"WS3_SPEC_FLAG_MISSING: {skill_md_path} does not contain '--spec'"
        )


def main() -> int:
    """CLI entry point. Returns 0 on pass, 1 on missing flag."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-flight: assert --spec flag present in SKILL.md"
    )
    parser.add_argument(
        "--skill-md",
        required=True,
        type=pathlib.Path,
        help="Path to SKILL.md to check",
    )
    args = parser.parse_args()

    try:
        preflight_spec_flag(args.skill_md)
        return 0
    except SpecFlagMissingError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"WS3_SPEC_FLAG_MISSING: file not found: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
