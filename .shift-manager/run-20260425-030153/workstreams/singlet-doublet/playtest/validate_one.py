#!/usr/bin/env python3
"""validate_one.py — wrapper: validate a summary.json against schema v1.1.

Usage:
    python3 validate_one.py <summary.json>

Exits 0 on PASS, non-zero on parse error or schema violation.

Decision: WRAPPER under run-dir (not an upstream extension of _shared/).
See PLAN_FINAL §Validator-wrapper vs upstream-extension decision.
"""
import json
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[5] / \
    "plugins" / "hep-ph-demo" / "skills" / "_shared" / "summary.schema.json"

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} <summary.json>", file=sys.stderr)
    sys.exit(2)

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed; run: pip install jsonschema", file=sys.stderr)
    sys.exit(3)

try:
    instance = json.load(open(sys.argv[1]))
except (json.JSONDecodeError, OSError) as exc:
    print(f"PARSE ERROR: {exc}", file=sys.stderr)
    sys.exit(1)

try:
    schema = json.load(open(SCHEMA))
except (json.JSONDecodeError, OSError) as exc:
    print(f"SCHEMA LOAD ERROR: {exc}", file=sys.stderr)
    sys.exit(4)

try:
    jsonschema.validate(instance, schema)
except jsonschema.ValidationError as exc:
    print(f"SCHEMA VIOLATION: {exc.message}", file=sys.stderr)
    sys.exit(1)

print(f"[PASS] {sys.argv[1]}")
sys.exit(0)
