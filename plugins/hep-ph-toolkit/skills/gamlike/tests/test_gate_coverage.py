"""
test_gate_coverage.py — gate ↔ fixture coverage check (T18d / O3).

Parses references/conditional_emission_gates.md to extract G1–G21 gate IDs
and the fixture filenames cited under each gate.
Parses tests/fixtures/README.md for fixtures listed.
Asserts: for every G1–G21, at least one fixture is cited in the gates doc.
"""
import re
from pathlib import Path

import pytest

_HERE = Path(__file__).parent.resolve()
_GATES_DOC = _HERE.parent / "references" / "conditional_emission_gates.md"
_README = _HERE / "fixtures" / "README.md"

EXPECTED_GATES = {f"G{i}" for i in range(1, 22)}


def parse_gates_doc(path: Path) -> dict:
    """
    Returns dict: {gate_id: set_of_fixture_names}.
    Gate IDs are like 'G1', 'G2', ...
    """
    content = path.read_text()
    result = {}
    current_gate = None
    fixture_re = re.compile(r'\b([\w_]+\.txt)\b')

    for line in content.splitlines():
        # Detect gate heading: ## G<n> — <name>
        hm = re.match(r'^## (G\d+)', line)
        if hm:
            current_gate = hm.group(1)
            result[current_gate] = set()
        elif current_gate:
            # Look for .txt fixture filenames in this gate's block
            for fname in fixture_re.findall(line):
                result[current_gate].add(fname)

    return result


def test_all_gates_present_in_doc():
    """All G1–G21 gate headings are present in conditional_emission_gates.md."""
    gates = parse_gates_doc(_GATES_DOC)
    found = set(gates.keys())
    missing = EXPECTED_GATES - found
    assert not missing, f"Gates missing from doc: {sorted(missing)}"


def test_all_gates_cite_at_least_one_fixture():
    """Every G1–G21 gate cites at least one fixture filename."""
    gates = parse_gates_doc(_GATES_DOC)
    no_fixtures = []
    for gate_id in sorted(EXPECTED_GATES):
        if not gates.get(gate_id):
            no_fixtures.append(gate_id)
    assert not no_fixtures, (
        f"Gates with no cited fixture: {no_fixtures}. "
        "Add a fixture reference to references/conditional_emission_gates.md."
    )


def test_gate_count():
    """Exactly 21 gates in the document."""
    gates = parse_gates_doc(_GATES_DOC)
    assert len(gates) == 21, f"Expected 21 gates, found {len(gates)}: {sorted(gates.keys())}"
