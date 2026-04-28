#!/usr/bin/env python3
"""Migrate `~/.config/hephaestus/config.json` data-dir paths from the legacy
`hep-ph-agents` slug to `hephaestus` after the project rebrand.

Walks the JSON tree; for any string value containing `/hep-ph-agents/`,
rewrites to `/hephaestus/` *only if* the rewritten path exists on disk.
Otherwise leaves the original alone and warns to stderr (the user may have
the tool installed elsewhere or not at all).

Writes a single backup `<config>.bak.<UTC-timestamp>` before mutating; if no
rewrites are needed, no backup is written and the file is untouched (so the
script is safe to re-run).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

LEGACY_SUBSTR = "/hep-ph-agents/"
NEW_SUBSTR = "/hephaestus/"
DEFAULT_CONFIG = Path.home() / ".config/hephaestus/config.json"


def _rewrite(node, warnings: list):
    if isinstance(node, dict):
        n = 0
        out = {}
        for k, v in node.items():
            new_v, c = _rewrite(v, warnings)
            out[k] = new_v
            n += c
        return out, n
    if isinstance(node, list):
        n = 0
        out = []
        for v in node:
            new_v, c = _rewrite(v, warnings)
            out.append(new_v)
            n += c
        return out, n
    if isinstance(node, str) and LEGACY_SUBSTR in node:
        candidate = node.replace(LEGACY_SUBSTR, NEW_SUBSTR)
        if os.path.exists(candidate):
            return candidate, 1
        warnings.append(f"skipped (target missing): {node} -> {candidate}")
        return node, 0
    return node, 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.config.exists():
        print(f"error: config not found at {args.config}", file=sys.stderr)
        return 2

    raw = args.config.read_text()
    data = json.loads(raw)
    warnings: list = []
    rewritten, n = _rewrite(data, warnings)

    for w in warnings:
        print(f"warn: {w}", file=sys.stderr)

    if n == 0:
        print("no changes needed", file=sys.stderr)
        return 0

    if args.dry_run:
        print(f"dry-run: {n} path(s) would be rewritten", file=sys.stderr)
        return 0

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = args.config.with_suffix(args.config.suffix + f".bak.{ts}")
    backup.write_text(raw)
    args.config.write_text(json.dumps(rewritten, indent=2) + "\n")
    print(f"rewrote {n} path(s); backup at {backup}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
