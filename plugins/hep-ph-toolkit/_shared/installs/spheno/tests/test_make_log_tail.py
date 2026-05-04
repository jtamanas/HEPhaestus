"""test_make_log_tail.py — Unit tests for _make_log_parse.py.

Tests:
- make_fail_lapack.log → likely_cause == "lapack"
- make_fail_generic.log → likely_cause == "generic"
- make_ok.log → still parses (returns dict with correct structure)
- last-40-lines tail truncation verified
- code and mode always correct
"""
import sys
import os
import pytest

# _make_log_parse.py lives one level up from tests/ — the install layout was
# flattened in commit 0bf22f2 (no more scripts/ subdir under installs/spheno/).
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return f.read()


# Import the module under test.
import importlib.util

spec_path = os.path.join(SCRIPTS_DIR, "_make_log_parse.py")
_spec = importlib.util.spec_from_file_location("_make_log_parse", spec_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
parse = _mod.parse


class TestParseStructure:
    """The parse() function always returns the expected structure."""

    def test_code_is_always_correct(self):
        result = parse(_load_fixture("make_fail_generic.log"))
        assert result["code"] == "SPHENO_BASE_BUILD_FAILED"

    def test_mode_is_always_fatal(self):
        result = parse(_load_fixture("make_fail_lapack.log"))
        assert result["mode"] == "fatal"

    def test_context_has_required_keys(self):
        result = parse(_load_fixture("make_ok.log"))
        assert "make_log_tail" in result["context"]
        assert "likely_cause" in result["context"]

    def test_message_is_nonempty(self):
        result = parse(_load_fixture("make_fail_generic.log"))
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0


class TestLikelyCause:
    """Detect LAPACK vs generic failure."""

    def test_lapack_failure_detected(self):
        result = parse(_load_fixture("make_fail_lapack.log"))
        assert result["context"]["likely_cause"] == "lapack"

    def test_generic_failure_when_no_lapack_mention(self):
        result = parse(_load_fixture("make_fail_generic.log"))
        assert result["context"]["likely_cause"] == "generic"

    def test_ok_log_is_generic(self):
        result = parse(_load_fixture("make_ok.log"))
        assert result["context"]["likely_cause"] == "generic"

    def test_lapack_message_mentions_lapack(self):
        result = parse(_load_fixture("make_fail_lapack.log"))
        assert "lapack" in result["message"].lower() or "LAPACK" in result["message"]


class TestTail:
    """make_log_tail is the last 40 lines of the log."""

    def _last_40_lines(self, text: str) -> str:
        lines = text.splitlines()
        tail = lines[-40:] if len(lines) >= 40 else lines
        return "\n".join(tail)

    def test_tail_matches_last_40_lines_lapack(self):
        log_text = _load_fixture("make_fail_lapack.log")
        result = parse(log_text)
        expected = self._last_40_lines(log_text)
        assert result["context"]["make_log_tail"] == expected

    def test_tail_matches_last_40_lines_generic(self):
        log_text = _load_fixture("make_fail_generic.log")
        result = parse(log_text)
        expected = self._last_40_lines(log_text)
        assert result["context"]["make_log_tail"] == expected

    def test_short_log_tail_equals_whole_log(self):
        """If the log has fewer than 40 lines, tail equals the whole content."""
        log_text = "line 1\nline 2\nline 3\n"
        result = parse(log_text)
        # splitlines() → ['line 1', 'line 2', 'line 3']
        expected = "line 1\nline 2\nline 3"
        assert result["context"]["make_log_tail"] == expected

    def test_exactly_40_lines_is_not_truncated(self):
        log_text = "\n".join(f"line {i}" for i in range(1, 41))
        result = parse(log_text)
        assert result["context"]["make_log_tail"] == log_text

    def test_41_lines_drops_first_line(self):
        log_text = "\n".join(f"line {i}" for i in range(1, 42))
        result = parse(log_text)
        expected = "\n".join(f"line {i}" for i in range(2, 42))
        assert result["context"]["make_log_tail"] == expected
