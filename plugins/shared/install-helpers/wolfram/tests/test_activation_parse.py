"""Tests for _activation_parse.py — activation prompt classification.

The test reads the fixture file at:
  plugins/shared/install-helpers/wolfram/tests/fixtures/wolfram_activation_prompt.txt

If the fixture contains only FIXTURE_PENDING, the test is skipped with an
explanatory message.  Once a real fixture is captured (by running
`wolframscript -code '1+1' 2>&1` on an unactivated machine and appending
`exit_code=$?`), the test will run and assert that the parser returns
{"status": "activation_required"}.

CLI mirrored from check_wolfram_activation.sh:
    printf '%s' "$probe_out" | python3 _activation_parse.py "$probe_rc"
i.e. exit code is passed as argv[1]; wolframscript stdout goes on stdin.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve paths relative to this test file so they work regardless of cwd.
_THIS_DIR = Path(__file__).parent
_FIXTURES_DIR = _THIS_DIR / "fixtures"
_FIXTURE_FILE = _FIXTURES_DIR / "wolfram_activation_prompt.txt"
_ACTIVATION_PARSE = _THIS_DIR.parent / "_activation_parse.py"


def test_activation_parse_from_fixture() -> None:
    """Parse the captured wolframscript activation prompt and assert status."""
    contents = _FIXTURE_FILE.read_text(encoding="utf-8")

    if contents.strip() == "FIXTURE_PENDING":
        pytest.skip("fixture not yet captured; see _activation_parse.py TODO")

    # The last line of the fixture is: exit_code=<N>
    # Everything before it is the raw wolframscript output.
    lines = contents.splitlines()
    last_line = lines[-1].strip()
    assert last_line.startswith("exit_code="), (
        f"Last line of fixture must be 'exit_code=<N>', got: {last_line!r}"
    )
    exit_code_str = last_line.split("=", 1)[1]
    exit_code = int(exit_code_str)

    # stdin_data is everything except the final exit_code= line.
    stdin_data = "\n".join(lines[:-1])

    result = subprocess.run(
        [sys.executable, str(_ACTIVATION_PARSE), str(exit_code)],
        input=stdin_data,
        capture_output=True,
        text=True,
        check=False,
    )

    parsed = json.loads(result.stdout)
    assert parsed["status"] == "activation_required", (
        f"Expected status='activation_required', got {parsed!r}\n"
        f"stderr: {result.stderr!r}"
    )
