"""
Graders for the eval harness.

Each grader is a pure function: (expected, actual, config) -> GradeResult.
All Tier 1-3 graders are deterministic (no LLM judging).
"""

import re
from .types import GraderConfig, GradeResult, GradeStatus


def grade_numeric(expected: dict, actual: dict, config: GraderConfig) -> GradeResult:
    """
    Compare a numeric value within relative tolerance.

    Used for cross-sections, masses, couplings — any quantity with a
    known reference value and physical units.
    """
    key = config.key
    tol = config.tolerance

    if key not in expected:
        return GradeResult("numeric", key, GradeStatus.ERROR,
                           message=f"Key '{key}' missing from expected")
    if key not in actual:
        return GradeResult("numeric", key, GradeStatus.FAIL,
                           expected=expected[key],
                           message=f"Key '{key}' missing from actual output")

    exp_val = expected[key]
    act_val = actual[key]

    try:
        exp_val = float(exp_val)
        act_val = float(act_val)
    except (TypeError, ValueError) as e:
        return GradeResult("numeric", key, GradeStatus.ERROR,
                           expected=exp_val, actual=act_val,
                           message=f"Non-numeric value: {e}")

    if exp_val == 0.0:
        # For zero expected, fall back to absolute comparison
        if abs(act_val) < tol:
            return GradeResult("numeric", key, GradeStatus.PASS,
                               expected=exp_val, actual=act_val)
        return GradeResult("numeric", key, GradeStatus.FAIL,
                           expected=exp_val, actual=act_val,
                           message=f"|actual| = {abs(act_val):.2e} > tol {tol:.2e}")

    rel_diff = abs(act_val - exp_val) / abs(exp_val)
    if rel_diff <= tol:
        return GradeResult("numeric", key, GradeStatus.PASS,
                           expected=exp_val, actual=act_val,
                           message=f"rel_diff={rel_diff:.2e}")
    return GradeResult("numeric", key, GradeStatus.FAIL,
                       expected=exp_val, actual=act_val,
                       message=f"rel_diff={rel_diff:.2e} > tol {tol:.2e}")


def grade_exact_zero(expected: dict, actual: dict, config: GraderConfig) -> GradeResult:
    """
    Check that a value is zero within absolute tolerance.

    Used for blind spots where an amplitude must vanish exactly.
    """
    key = config.key
    tol = config.tolerance

    if key not in actual:
        return GradeResult("exact_zero", key, GradeStatus.FAIL,
                           expected=0.0,
                           message=f"Key '{key}' missing from actual output")

    act_val = actual[key]
    try:
        act_val = float(act_val)
    except (TypeError, ValueError) as e:
        return GradeResult("exact_zero", key, GradeStatus.ERROR,
                           expected=0.0, actual=act_val,
                           message=f"Non-numeric value: {e}")

    if abs(act_val) <= tol:
        return GradeResult("exact_zero", key, GradeStatus.PASS,
                           expected=0.0, actual=act_val,
                           message=f"|val| = {abs(act_val):.2e} <= {tol:.2e}")
    return GradeResult("exact_zero", key, GradeStatus.FAIL,
                       expected=0.0, actual=act_val,
                       message=f"|val| = {abs(act_val):.2e} > tol {tol:.2e}")


def grade_unit(expected: dict, actual: dict, config: GraderConfig) -> GradeResult:
    """Check that a string value matches exactly (for units)."""
    key = config.key
    exp_val = config.expected

    if key not in actual:
        return GradeResult("unit", key, GradeStatus.FAIL,
                           expected=exp_val,
                           message=f"Key '{key}' missing from actual output")

    act_val = str(actual[key])
    if act_val == str(exp_val):
        return GradeResult("unit", key, GradeStatus.PASS,
                           expected=exp_val, actual=act_val)
    return GradeResult("unit", key, GradeStatus.FAIL,
                       expected=exp_val, actual=act_val,
                       message=f"Expected '{exp_val}', got '{act_val}'")


def grade_file_contains(expected: dict, actual: dict, config: GraderConfig) -> GradeResult:
    """
    Check that a file contains a regex pattern.

    Used for validating proc_card.dat and param_card.dat content.
    The actual dict should have a key matching config.key whose value
    is the file content string.
    """
    key = config.key
    pattern = config.pattern

    if key not in actual:
        return GradeResult("file_contains", key, GradeStatus.FAIL,
                           message=f"Key '{key}' missing from actual output")

    content = str(actual[key])
    if re.search(pattern, content, re.MULTILINE):
        return GradeResult("file_contains", key, GradeStatus.PASS,
                           message=f"Pattern '{pattern}' found")
    return GradeResult("file_contains", key, GradeStatus.FAIL,
                       message=f"Pattern '{pattern}' not found in output")


def grade_ordering(expected: dict, actual: dict, config: GraderConfig) -> GradeResult:
    """
    Assert that actual[key_a] > actual[key_b].

    Used for physics sanity: larger coupling → larger cross-section.
    """
    key_a = config.key_a
    key_b = config.key_b

    for k in (key_a, key_b):
        if k not in actual:
            return GradeResult("ordering", f"{key_a}>{key_b}", GradeStatus.FAIL,
                               message=f"Key '{k}' missing from actual output")

    try:
        val_a = float(actual[key_a])
        val_b = float(actual[key_b])
    except (TypeError, ValueError) as e:
        return GradeResult("ordering", f"{key_a}>{key_b}", GradeStatus.ERROR,
                           message=f"Non-numeric: {e}")

    if val_a > val_b:
        return GradeResult("ordering", f"{key_a}>{key_b}", GradeStatus.PASS,
                           expected=f"{key_a} > {key_b}",
                           actual=f"{val_a:.4e} > {val_b:.4e}")
    return GradeResult("ordering", f"{key_a}>{key_b}", GradeStatus.FAIL,
                       expected=f"{key_a} > {key_b}",
                       actual=f"{val_a:.4e} <= {val_b:.4e}")


GRADER_REGISTRY = {
    "numeric": grade_numeric,
    "exact_zero": grade_exact_zero,
    "unit": grade_unit,
    "file_contains": grade_file_contains,
    "ordering": grade_ordering,
}


def run_graders(expected: dict, actual: dict,
                grader_configs: list[GraderConfig]) -> list[GradeResult]:
    """Run all graders for a task and return results."""
    results = []
    for config in grader_configs:
        grader_fn = GRADER_REGISTRY.get(config.type)
        if grader_fn is None:
            results.append(GradeResult(
                config.type, config.key, GradeStatus.ERROR,
                message=f"Unknown grader type: {config.type}"))
            continue
        results.append(grader_fn(expected, actual, config))
    return results
