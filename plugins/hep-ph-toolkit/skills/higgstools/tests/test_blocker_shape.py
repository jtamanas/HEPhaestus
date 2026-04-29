"""
test_blocker_shape.py — every emitted blocker validates against blocker.schema.json.

Tests that all error codes in the higgstools skill emit valid JSON blockers
conforming to plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json.
"""
import json
from pathlib import Path

import pytest

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

SKILL_DIR = Path(__file__).parent.parent
SHARED_DIR = SKILL_DIR.parent / "_shared"
SCHEMA_PATH = SHARED_DIR / "blocker.schema.json"

# All error codes defined in the plan
ALL_BLOCKER_CODES = [
    ("HIGGSTOOLS_TOOLCHAIN_MISSING", "fatal"),
    ("HIGGSTOOLS_OFFLINE_NO_CACHE", "fatal"),
    ("HIGGSTOOLS_DOWNLOAD_FAILED", "fatal"),
    ("HIGGSTOOLS_BUILD_FAILED", "fatal"),
    ("HIGGSTOOLS_SMOKE_TEST_FAILED", "fatal"),
    ("HIGGSTOOLS_PATH_INVALID", "fatal"),
    ("HIGGSTOOLS_BACKEND_UNAVAILABLE", "recoverable"),
    ("HIGGSTOOLS_SLHA_MISSING_BLOCKS", "fatal"),
    ("HIGGSTOOLS_SM_REF_MISSING", "fatal"),
    ("HIGGSTOOLS_DATASET_MISMATCH", "fatal"),
    ("HIGGSTOOLS_NUMERIC_CRASH", "recoverable"),
]


def _make_blocker(code: str, mode: str, message: str, user_instruction: str = "") -> dict:
    """Create a blocker dict matching the schema."""
    blocker = {"code": code, "mode": mode, "message": message}
    if user_instruction:
        blocker["user_instruction"] = user_instruction
    return blocker


@pytest.fixture
def blocker_schema():
    """Load the shared blocker.schema.json."""
    assert SCHEMA_PATH.exists(), f"blocker.schema.json not found at {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text())


class TestBlockerShape:
    """Test that all blocker codes produce schema-valid JSON."""

    @pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="blocker.schema.json not found")
    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    @pytest.mark.parametrize("code,mode", ALL_BLOCKER_CODES)
    def test_blocker_validates_against_schema(self, code, mode, blocker_schema):
        """Each error code produces a blocker that validates against the schema."""
        blocker = _make_blocker(
            code, mode,
            f"Test message for {code}",
            f"User instruction for {code}",
        )
        # Should not raise
        jsonschema.validate(blocker, blocker_schema)

    @pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="blocker.schema.json not found")
    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_blocker_without_user_instruction_validates(self, blocker_schema):
        """Blocker without user_instruction is still valid."""
        blocker = _make_blocker(
            "HIGGSTOOLS_BUILD_FAILED", "fatal",
            "Build failed due to missing library.",
        )
        jsonschema.validate(blocker, blocker_schema)

    @pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="blocker.schema.json not found")
    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_recoverable_mode_validates(self, blocker_schema):
        """Recoverable mode blockers validate against schema."""
        blocker = _make_blocker(
            "HIGGSTOOLS_NUMERIC_CRASH", "recoverable",
            "Numeric crash on one scan row. Row marked bad; scan continues.",
        )
        jsonschema.validate(blocker, blocker_schema)

    @pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="blocker.schema.json not found")
    @pytest.mark.skipif(not HAS_JSONSCHEMA, reason="jsonschema not installed")
    def test_schema_is_valid_json_schema(self, blocker_schema):
        """The blocker schema itself is a valid JSON Schema."""
        jsonschema.Draft202012Validator.check_schema(blocker_schema)

    def test_blocker_codes_are_strings(self):
        """All blocker codes are non-empty strings."""
        for code, mode in ALL_BLOCKER_CODES:
            assert isinstance(code, str) and code
            assert mode in ("fatal", "recoverable")

    def test_all_fatal_blockers_have_higgstools_prefix(self):
        """All blocker codes start with HIGGSTOOLS_."""
        for code, mode in ALL_BLOCKER_CODES:
            assert code.startswith("HIGGSTOOLS_"), f"Code {code} missing HIGGSTOOLS_ prefix"

    def test_install_script_blocker_emission(self, tmp_path):
        """_blocker.sh emits valid JSON via emit_blocker function.

        Post-2026-04-29 refactor: lives under
        plugins/hep-ph-toolkit/_shared/installs/higgstools/_blocker.sh.
        """
        import subprocess
        script = (
            SKILL_DIR.parent.parent
            / "_shared"
            / "installs"
            / "higgstools"
            / "_blocker.sh"
        )
        assert script.exists(), (
            f"Expected {script} to exist after install-skill refactor"
        )

        result = subprocess.run(
            ["bash", "-c",
             f"source {script} && emit_blocker HIGGSTOOLS_BUILD_FAILED fatal 'Build failed.' 'Check logs.'"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # The blocker is emitted on stderr
        blocker_text = result.stderr.strip()
        assert blocker_text, f"No output from emit_blocker: {result.stderr}"
        blocker = json.loads(blocker_text)
        assert blocker["code"] == "HIGGSTOOLS_BUILD_FAILED"
        assert blocker["mode"] == "fatal"
        assert "message" in blocker

        if HAS_JSONSCHEMA and SCHEMA_PATH.exists():
            schema = json.loads(SCHEMA_PATH.read_text())
            jsonschema.validate(blocker, schema)
