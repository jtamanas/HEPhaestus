"""
test_real_fixture_round_trip.py — T18 byte-stable round-trip tests.

For each fixture, parse, scrub _meta.*, assert byte-for-byte match
against tests/fixtures/expected/<fixture>.json.
"""
import importlib.util
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_FIXTURES = _HERE / "fixtures"
_EXPECTED = _FIXTURES / "expected"
_SCRIPT = _HERE.parent / "scripts" / "parse_maddm_results.py"

_spec = importlib.util.spec_from_file_location("parse_maddm_results", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

SCRUB_FIELDS = {"parsed_at": "<SCRUBBED>", "source_file": "<SCRUBBED>"}
SKIP_FIXTURES = {"malformed_truncated.txt"}  # exits 3

_FIXTURE_NAMES = [
    f.name for f in sorted(_FIXTURES.glob("*.txt"))
    if f.name not in SKIP_FIXTURES
]


def _scrub(d: dict) -> dict:
    if "_meta" in d:
        for key, val in SCRUB_FIELDS.items():
            if key in d["_meta"]:
                d["_meta"][key] = val
    return d


@pytest.mark.parametrize("fixture_name", _FIXTURE_NAMES)
def test_round_trip(fixture_name):
    """Parse fixture, scrub meta, compare byte-for-byte with expected snapshot."""
    expected_path = _EXPECTED / (fixture_name + ".json")
    if not expected_path.exists():
        pytest.skip(f"No expected snapshot for {fixture_name}; run regenerate_expected.py")

    doc = _mod.parse_file(_FIXTURES / fixture_name)
    doc = _scrub(doc)
    actual = json.dumps(doc, indent=2)

    expected = json.loads(expected_path.read_text())
    expected_str = json.dumps(expected, indent=2)

    assert actual == expected_str, (
        f"Round-trip mismatch for {fixture_name}. "
        "If the parser changed intentionally, re-run regenerate_expected.py."
    )
