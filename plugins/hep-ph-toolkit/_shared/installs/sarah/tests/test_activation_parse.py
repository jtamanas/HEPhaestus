"""test_activation_parse.py — unit tests for _activation_parse.py.

Tests:
  - wolfram_ok.txt fixture → {"status":"ok"}
  - wolfram_activation_prompt.txt fixture → activation_required (when real fixture;
    skipped when fixture is only a TODO comment)
  - Synthetic activation strings → activation_required with user_instruction
  - Synthetic happy-path → ok
  - Exit code non-zero + no pattern → error (not activation_required)
"""
import sys
import os
import json
import importlib.util
import pathlib

import pytest

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

# ---------------------------------------------------------------------------
# Import _activation_parse without package structure.
# ---------------------------------------------------------------------------
SCRIPTS_DIR = pathlib.Path(__file__).parent.parent
FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_activation_parse", SCRIPTS_DIR / "_activation_parse.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
classify = _mod.classify
ACTIVATION_USER_INSTRUCTION = _mod.ACTIVATION_USER_INSTRUCTION


# ---------------------------------------------------------------------------
# Happy path: output is "2", exit 0.
# ---------------------------------------------------------------------------
class TestHappyPath:
    def test_classify_ok(self):
        result = classify("2", 0)
        assert result == {"status": "ok"}

    def test_classify_ok_with_whitespace(self):
        result = classify("  2  \n", 0)
        assert result == {"status": "ok"}

    def test_wolfram_ok_fixture(self):
        fixture = (FIXTURES_DIR / "wolfram_ok.txt").read_text()
        result = classify(fixture, 0)
        assert result == {"status": "ok"}, f"Expected ok, got: {result}"


# ---------------------------------------------------------------------------
# Activation-required: synthetic activation strings.
# ---------------------------------------------------------------------------
class TestActivationRequired:
    @pytest.mark.parametrize(
        "text",
        [
            "Please activate your Wolfram Engine",
            "This copy of Wolfram Engine is not activated",
            "Enter your Wolfram ID to activate",
            "activation required",
            "No valid password file found",
            "license not found",
        ],
    )
    def test_activation_patterns(self, text: str):
        result = classify(text, 1)
        assert result["status"] == "activation_required", f"text={text!r} result={result}"
        assert "user_instruction" in result
        assert len(result["user_instruction"]) > 0

    def test_user_instruction_content(self):
        result = classify("Please activate your Wolfram Engine", 1)
        assert "wolframscript" in result["user_instruction"]

    def test_activation_with_exit_zero(self):
        """Activation prompt takes precedence even if exit code happens to be 0."""
        result = classify("Please activate your Wolfram Engine", 0)
        assert result["status"] == "activation_required"


# ---------------------------------------------------------------------------
# Real fixture test — skipped if fixture is only a TODO comment.
# ---------------------------------------------------------------------------
class TestRealFixture:
    @staticmethod
    def _is_real_fixture(path: pathlib.Path) -> bool:
        content = path.read_text()
        # If the fixture starts with a comment block explaining how to capture it,
        # it's a placeholder; skip the test.
        return not content.startswith("#")

    def test_activation_prompt_fixture(self):
        fixture_path = FIXTURES_DIR / "wolfram_activation_prompt.txt"
        if not self._is_real_fixture(fixture_path):
            pytest.skip(
                "wolfram_activation_prompt.txt is a TODO placeholder; "
                "capture the real fixture first (see TODO(W1-Day1) comment in the file)."
            )
        content = fixture_path.read_text()
        result = classify(content, exit_code=1)
        assert result["status"] == "activation_required", (
            f"Expected activation_required from fixture, got: {result}"
        )
        assert "user_instruction" in result


# ---------------------------------------------------------------------------
# Benign strings that must NOT trigger activation_required.
# ---------------------------------------------------------------------------
class TestBenignLicense:
    @pytest.mark.parametrize(
        "text",
        [
            "(c) 2026 Wolfram Research. License: commercial.",
            "Wolfram Engine is released under the MathLLA license agreement.",
            "See LICENSE file for details.",
            "This software is licensed under the BSD 3-Clause license.",
            "license information: see https://wolfram.com/engine/free-license",
        ],
    )
    def test_benign_license_strings_do_not_match(self, text: str):
        """A copyright banner or license-type mention must NOT be classified as
        activation_required — the old bare 'license' regex was over-broad."""
        result = classify(text, 0)
        assert result["status"] != "activation_required", (
            f"False-positive: benign text {text!r} was classified as activation_required"
        )


# ---------------------------------------------------------------------------
# Error fallback: unknown output, non-zero exit.
# ---------------------------------------------------------------------------
class TestErrorFallback:
    def test_unknown_error(self):
        result = classify("Something went completely wrong", 2)
        assert result["status"] == "error"
        assert "detail" in result

    def test_detail_truncated_at_200(self):
        long_text = "X" * 500
        result = classify(long_text, 2)
        assert len(result["detail"]) <= 200

    def test_empty_output_with_zero_exit(self):
        """Empty output with exit 0 is not 'ok' (no '2' found)."""
        result = classify("", 0)
        assert result["status"] in ("error",)


# ---------------------------------------------------------------------------
# CLI smoke (subprocess)
# ---------------------------------------------------------------------------
class TestCLI:
    def test_cli_ok(self, tmp_path):
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "_activation_parse.py"), "0"],
            input=b"2\n",
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "ok"

    def test_cli_activation(self, tmp_path):
        import subprocess

        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "_activation_parse.py"), "1"],
            input=b"Please activate your Wolfram Engine\n",
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "activation_required"
