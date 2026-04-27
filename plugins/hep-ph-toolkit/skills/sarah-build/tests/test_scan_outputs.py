"""
test_scan_outputs.py — Unit + integration tests for scan_outputs.scan().

Covers plan §7.2 and §7.4 empirical-gate smoke (skip-gated where live
baseline trees are unavailable).

Fixture layout: tests/fixtures/scan/<file>. Each test copies the relevant
subset into a synthetic ``tmp_path / "sarah_output" / <Tree> / <Name> / …``
tree, then invokes ``scan()``.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

# sys.path is set up by conftest.py.
from scan_outputs import scan  # noqa: E402

_TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = _TESTS_DIR / "fixtures" / "scan"

SARAH_NAME = "TestModel"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _populate_spheno(model_dir: Path, *fixture_names: str) -> Path:
    """Copy fixtures into sarah_output/SPheno/<Name>/. Returns the tree root."""
    root = model_dir / "sarah_output" / "SPheno" / SARAH_NAME
    root.mkdir(parents=True, exist_ok=True)
    for name in fixture_names:
        shutil.copy2(FIXTURES / name, root / name)
    return root


def _populate_ufo(model_dir: Path, *fixture_names: str) -> Path:
    """Copy fixtures into sarah_output/UFO/<Name>/. Returns the tree root."""
    root = model_dir / "sarah_output" / "UFO" / SARAH_NAME
    root.mkdir(parents=True, exist_ok=True)
    for name in fixture_names:
        shutil.copy2(FIXTURES / name, root / name)
    return root


# ---------------------------------------------------------------------------
# Per-pattern unit tests (plan §7.1)
# ---------------------------------------------------------------------------

def test_scan_clean_small(tmp_path):
    _populate_spheno(tmp_path, "clean_small.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "clean"
    assert result["files_scanned"] == 1


def test_scan_dollar_failed_declaration(tmp_path):
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    patterns = {h["pattern"] for h in result["blocker"]["context"]["hits"]}
    assert "DOLLAR_FAILED" in patterns


def test_scan_dollar_failed_expression(tmp_path):
    _populate_spheno(tmp_path, "dollar_failed_expr.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    hit = result["blocker"]["context"]["hits"][0]
    assert hit["pattern"] == "DOLLAR_FAILED"
    assert hit["line"] == 3


def test_scan_sax_dynl_and_dollar_failed_same_line(tmp_path):
    _populate_spheno(tmp_path, "sax_dynkin.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    patterns = {h["pattern"] for h in result["blocker"]["context"]["hits"]}
    assert {"DOLLAR_FAILED", "SAX_DYNL"} <= patterns


def test_scan_sax_casimir(tmp_path):
    _populate_spheno(tmp_path, "sax_casimir.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "SAX_CASIMIR"
               for h in result["blocker"]["context"]["hits"])


def test_scan_sax_mulfactor(tmp_path):
    _populate_spheno(tmp_path, "sax_mulfactor.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "SAX_MULFACTOR"
               for h in result["blocker"]["context"]["hits"])


def test_scan_sax_dynkin(tmp_path):
    _populate_spheno(tmp_path, "sax_dynkin_only.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "SAX_DYNKIN"
               for h in result["blocker"]["context"]["hits"])


def test_scan_part_list_parens(tmp_path):
    _populate_spheno(tmp_path, "part_list.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "PART_LIST"
               for h in result["blocker"]["context"]["hits"])


def test_scan_part_list_brackets(tmp_path):
    _populate_spheno(tmp_path, "part_list_brackets.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "PART_LIST"
               for h in result["blocker"]["context"]["hits"])


def test_scan_mathematica_concat(tmp_path):
    _populate_spheno(tmp_path, "math_concat.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "MATHEMATICA_CONCAT"
               for h in result["blocker"]["context"]["hits"])


def test_scan_dollar_aborted(tmp_path):
    _populate_spheno(tmp_path, "dollar_aborted.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "DOLLAR_ABORTED"
               for h in result["blocker"]["context"]["hits"])


def test_scan_hold_form(tmp_path):
    _populate_spheno(tmp_path, "hold_form.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "HOLD_FORM"
               for h in result["blocker"]["context"]["hits"])


def test_scan_missing_failure(tmp_path):
    _populate_spheno(tmp_path, "missing_failure.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "MISSING_FAILURE"
               for h in result["blocker"]["context"]["hits"])


def test_scan_none_index(tmp_path):
    _populate_spheno(tmp_path, "none_index.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "NONE_INDEX"
               for h in result["blocker"]["context"]["hits"])


def test_scan_diagnostic_write_no_fp(tmp_path):
    """Plan D3: Write(…) '$Failed = ' diagnostic lines don't trigger DOLLAR_FAILED."""
    _populate_spheno(tmp_path, "diagnostic_write_allowed.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "clean", (
        f"diagnostic Write must not trigger DOLLAR_FAILED; got: {result}"
    )


# ---------------------------------------------------------------------------
# Tree-grouping and cross-cutting tests (plan §7.2)
# ---------------------------------------------------------------------------

def test_scan_no_trees_clean(tmp_path):
    """Neither tree exists → files_scanned=0 and clean."""
    result = scan(tmp_path, SARAH_NAME)
    assert result == {
        "status": "clean",
        "files_scanned": 0,
        "trees": {"spheno": 0, "ufo": 0},
    }


def test_scan_ufo_only_corrupt(tmp_path):
    """C1 coverage: UFO-only corruption still blocks (dark_su3 shape)."""
    _populate_ufo(tmp_path, "particles_dollar_failed.py")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    hits = result["blocker"]["context"]["hits"]
    assert {h["tree"] for h in hits} == {"ufo"}


def test_scan_spheno_only_corrupt(tmp_path):
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    hits = result["blocker"]["context"]["hits"]
    assert {h["tree"] for h in hits} == {"spheno"}


def test_scan_mixed_trees(tmp_path):
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    _populate_ufo(tmp_path, "particles_dollar_failed.py")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    trees = {h["tree"] for h in result["blocker"]["context"]["hits"]}
    assert trees == {"spheno", "ufo"}


def test_scan_ufo_clean_file(tmp_path):
    _populate_ufo(tmp_path, "particles_ok.py")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "clean"


def test_scan_ufo_parameters_failure(tmp_path):
    _populate_ufo(tmp_path, "parameters_failure.py")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any(h["pattern"] == "MISSING_FAILURE"
               for h in result["blocker"]["context"]["hits"])


def test_scan_truncation(tmp_path):
    """100 synthetic hits → total_hits=100, len(hits)=50, truncated=True."""
    spheno_root = tmp_path / "sarah_output" / "SPheno" / SARAH_NAME
    spheno_root.mkdir(parents=True)
    synthetic = "\n".join([f"x{i} = $Failed" for i in range(100)]) + "\n"
    (spheno_root / "many_hits.f90").write_text(synthetic)

    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    ctx = result["blocker"]["context"]
    assert ctx["total_hits"] == 100
    assert len(ctx["hits"]) == 50
    assert ctx["truncated"] is True


def test_scan_deterministic(tmp_path):
    """Two scans of the same tree → identical JSON (sort_keys=True)."""
    _populate_spheno(
        tmp_path,
        "dollar_failed_decl.f90",
        "sax_dynkin.f90",
        "missing_failure.f90",
    )
    r1 = scan(tmp_path, SARAH_NAME)
    r2 = scan(tmp_path, SARAH_NAME)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_scan_oversize_skip(tmp_path):
    """>8 MiB files land in skipped_oversize and don't gate the status."""
    spheno_root = tmp_path / "sarah_output" / "SPheno" / SARAH_NAME
    spheno_root.mkdir(parents=True)
    big = spheno_root / "big_file.f90"
    # 9 MiB of benign ASCII padding
    big.write_text("! padding\n" * (9 * 1024 * 1024 // 10))
    # and a small clean sibling so files_scanned > 0
    shutil.copy2(FIXTURES / "clean_small.f90", spheno_root / "clean.f90")

    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "clean"
    # The oversize file should NOT appear in files_scanned (it was skipped),
    # and we should have scanned exactly one file (clean.f90).
    assert result["files_scanned"] == 1


def test_scan_oversize_listed_in_blocker(tmp_path):
    """Oversize list surfaces in blocker context when OTHER files hit."""
    spheno_root = tmp_path / "sarah_output" / "SPheno" / SARAH_NAME
    spheno_root.mkdir(parents=True)
    big = spheno_root / "big_file.f90"
    big.write_text("! padding\n" * (9 * 1024 * 1024 // 10))
    # Dirty sibling so we get a blocker
    shutil.copy2(FIXTURES / "dollar_failed_decl.f90",
                 spheno_root / "dollar_failed_decl.f90")

    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"
    assert any("big_file.f90" in s
               for s in result["blocker"]["context"]["skipped_oversize"])


def test_scan_attaches_log_hints(tmp_path):
    """Corrupt tree + log containing Part::partd attaches log_hints."""
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    log = tmp_path / "sarah.log"
    log.write_text(
        "some noise\n"
        "Part::partd: Part specification None[[1]] is longer than depth of object.\n"
        "more noise\n"
    )
    result = scan(tmp_path, SARAH_NAME, log_path=log)
    assert result["status"] == "corrupt"
    ctx = result["blocker"]["context"]
    assert "log_hints" in ctx
    assert ctx["log_hints"][0]["pattern"] == "PART_PARTD_NONE"


def test_scan_missing_log_omits_hints(tmp_path):
    """No log file → log_hints key is omitted entirely."""
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    result = scan(tmp_path, SARAH_NAME, log_path=tmp_path / "no_such.log")
    assert result["status"] == "corrupt"
    assert "log_hints" not in result["blocker"]["context"]


def test_scan_f90_uppercase_extension(tmp_path):
    """.F90 is treated the same as .f90 (normalised)."""
    spheno_root = tmp_path / "sarah_output" / "SPheno" / SARAH_NAME
    spheno_root.mkdir(parents=True)
    (spheno_root / "Foo.F90").write_text("y = $Failed\n")
    result = scan(tmp_path, SARAH_NAME)
    assert result["status"] == "corrupt"


# ---------------------------------------------------------------------------
# Blocker shape conformance
# ---------------------------------------------------------------------------

def test_scan_blocker_shape(tmp_path):
    """Blocker has top-level keys expected by blocker.schema.json fatal branch."""
    _populate_spheno(tmp_path, "dollar_failed_decl.f90")
    result = scan(tmp_path, SARAH_NAME)
    b = result["blocker"]
    assert b["code"] == "SARAH_OUTPUT_CORRUPT"
    assert b["mode"] == "fatal"
    assert isinstance(b["message"], str) and b["message"]
    assert isinstance(b["context"], dict)
    assert isinstance(b["user_instruction"], str) and b["user_instruction"]
    # No disallowed top-level keys
    assert set(b.keys()) <= {"code", "mode", "message", "context",
                              "user_instruction"}
