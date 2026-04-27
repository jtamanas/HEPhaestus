"""
sarah_name.py — SARAH-name canonicalizer.

# PROVISIONAL — verified by W3 Day-1 probe
# If the real SARAH loader uses a different convention, W3 amends this file
# and fills in the §X section of plugins/hep-ph-toolkit/SHARED-model-building.md.

Provisional rule: split on '_', apply _title_part() to each segment, join.
    dark_su3         → DarkSU3
    singlet_doublet  → SingletDoublet

The _title_part rule: uppercase the leading alpha run if it is ≤2 chars
(physics group abbreviations: su, u, su, sp, …); otherwise capitalize only
the first character and leave the rest lower-case.  Digits are preserved
as-is in all cases.

Examples:
    "dark"    → "Dark"      (len=4 > 2 → capitalize)
    "su3"     → "SU3"       (alpha prefix "su" has len=2 → uppercase)
    "u1"      → "U1"        (alpha prefix "u" has len=1 → uppercase)
    "singlet" → "Singlet"   (len=7 > 2 → capitalize)
    "2hdm_a"  → "2hdmA"     (leading-digit segment kept as-is by _title_part)

This rule is PROVISIONAL.  W3 Day-1 probe confirms or overrides it.

CLI:
    python3 sarah_name.py <name>   → prints SARAH name, exit 0
                                   → exit 2 on regex failure
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import re

MODEL_NAME_REGEX = re.compile(r"^[a-z0-9][a-z0-9_]{1,30}$")

# Match a leading alpha run followed by optional trailing digits/chars
_ALPHA_PREFIX_RE = re.compile(r"^([a-z]+)([0-9].*)?$")


def _title_part(part: str) -> str:
    """Apply SARAH-style title casing to one underscore-segment.

    - If the leading alpha prefix is 1–2 chars (group abbreviation like
      'su', 'u', 'sp'), uppercase the entire alpha prefix; preserve trailing
      digits/chars as-is.
    - Otherwise: capitalize the first character, lowercase the rest.
    """
    m = _ALPHA_PREFIX_RE.match(part)
    if m is None:
        # Part starts with a digit — this should be blocked by the regex but
        # handle defensively.
        return part
    alpha, rest = m.group(1), m.group(2) or ""
    if len(alpha) <= 2:
        return alpha.upper() + rest
    return alpha.capitalize() + rest


def modelspec_name_to_sarah(name: str) -> str:
    """Convert a modelspec name (snake_case) to the SARAH model name.

    Provisional rule (to be confirmed by W3 Day-1 probe):
        Split on '_', apply _title_part to each segment, concatenate.

    Args:
        name: A valid modelspec name matching MODEL_NAME_REGEX.

    Returns:
        The SARAH-style name.

    Raises:
        ValueError: if *name* does not match MODEL_NAME_REGEX.

    Examples:
        >>> modelspec_name_to_sarah("dark_su3")
        'DarkSU3'
        >>> modelspec_name_to_sarah("singlet_doublet")
        'SingletDoublet'
    """
    if not MODEL_NAME_REGEX.match(name):
        raise ValueError(
            f"invalid model name {name!r}: must match {MODEL_NAME_REGEX.pattern}"
        )
    return "".join(_title_part(w) for w in name.split("_"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <model_name>", file=sys.stderr)
        sys.exit(2)
    name = sys.argv[1]
    try:
        print(modelspec_name_to_sarah(name))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
