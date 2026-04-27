#!/usr/bin/env python3
"""
regenerate_expected.py — one-shot script to refresh tests/fixtures/expected/*.json.

Run this after parser fixes to update the byte-stability snapshots:
    python plugins/hep-ph-toolkit/skills/gamlike/tests/regenerate_expected.py

The script:
1. For each *.txt in tests/fixtures/ (excluding README.md), runs parse_maddm_results.py.
2. Scrubs _meta.parsed_at → "<SCRUBBED>" and _meta.source_file → "<SCRUBBED>".
3. Writes to tests/fixtures/expected/<fixture>.json.

Malformed fixtures (exit 3) are skipped (no JSON output to snapshot).
"""
import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_EXPECTED = _FIXTURES / "expected"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"

_EXPECTED.mkdir(parents=True, exist_ok=True)

SCRUB_FIELDS = {"parsed_at": "<SCRUBBED>", "source_file": "<SCRUBBED>"}

SKIP_FIXTURES = {"malformed_truncated.txt"}  # exits 3; no JSON


def scrub(d: dict) -> dict:
    if "_meta" in d:
        for key, val in SCRUB_FIELDS.items():
            if key in d["_meta"]:
                d["_meta"][key] = val
    return d


def main():
    fixtures = sorted(_FIXTURES.glob("*.txt"))
    ok = 0
    skipped = 0
    failed = 0

    for fixture in fixtures:
        name = fixture.name
        if name in SKIP_FIXTURES:
            print(f"SKIP: {name} (known exit-3 fixture)")
            skipped += 1
            continue

        import tempfile
        tmp_out = Path(tempfile.mktemp(suffix=".json"))
        result = subprocess.run(
            [sys.executable, str(_SCRIPT), str(fixture), "--out", str(tmp_out)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"SKIP: {name} (exit {result.returncode}): {result.stderr.strip()[:80]}")
            skipped += 1
            continue

        try:
            doc = json.loads(tmp_out.read_text())
        except Exception as e:
            print(f"FAIL: {name}: {e}")
            failed += 1
            continue
        finally:
            tmp_out.unlink(missing_ok=True)

        doc = scrub(doc)
        out_path = _EXPECTED / (name + ".json")
        out_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"OK: {name} → {out_path.name}")
        ok += 1

    print(f"\nDone: {ok} generated, {skipped} skipped, {failed} failed.")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
