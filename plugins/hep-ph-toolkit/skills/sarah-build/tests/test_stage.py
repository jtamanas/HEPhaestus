"""
test_stage.py — Exhaustive unit tests for scripts/stage.py.

Tests per T16a spec (design §6.2, §6.3):
  AT1: Basic happy-path: files written, .sarah_build_key stamped, path returned.
  AT2: Idempotency: second call with same inputs produces byte-identical tree.
  AT3: .mx cache wipe: pre-existing .mx files in staged dir are deleted.
  AT4: Filesystem permission edge case: pre-existing dir with read-only file is
       handled — rmtree removes it (UNIX: owner can rmtree a chmod 444 file).
  AT5: Cache-key corruption: key file re-written on every call (old corrupt key
       is replaced).
  AT6: Private-Models/ mkdir-p: works when neither sarah_path nor Private-Models
       exist yet (parents=True, exist_ok=True).
  AT7: Multiple files: all rendered files appear in staged dir.
  AT8: Returns a Path (not a string).
  AT9: sarah_path may be passed as str (coerced to Path).
  AT10: Old staged dir content is fully replaced (extra stale files removed).
"""

import sys
import stat
from pathlib import Path

import pytest

# sys.path is set up by conftest.py
from stage import stage  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_RENDERED: dict[str, str] = {
    "MyModel.m": "ModelName = \"MyModel\";\n",
    "particles.m": "(* particles *)\n",
    "parameters.m": "(* parameters *)\n",
    "SPheno.m": "(* spheno *)\n",
}

SAMPLE_KEY = "abc123deadbeef=4.15.3"


def _make_staged(tmp_path: Path, sarah_name: str = "MyModel") -> tuple[Path, Path]:
    """Return (sarah_path, staged_dir) with a clean staged tree."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, sarah_name, SAMPLE_KEY)
    return sarah_path, staged


# ---------------------------------------------------------------------------
# AT1: Happy-path basic sanity
# ---------------------------------------------------------------------------

def test_stage_returns_correct_path(tmp_path):
    """AT1a: stage() returns $sarah_path/Private-Models/<sarah_name>."""
    sarah_path = tmp_path / "sarah"
    result = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    expected = sarah_path / "Private-Models" / "MyModel"
    assert result == expected


def test_stage_creates_files(tmp_path):
    """AT1b: All rendered files are written to the staged dir."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    for filename, text in SAMPLE_RENDERED.items():
        fpath = staged / filename
        assert fpath.exists(), f"Expected file {filename!r} not found in staged dir"
        assert fpath.read_text(encoding="utf-8") == text


def test_stage_stamps_cache_key(tmp_path):
    """AT1c: .sarah_build_key is written with the exact cache_key string."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    key_file = staged / ".sarah_build_key"
    assert key_file.exists(), ".sarah_build_key not found in staged dir"
    assert key_file.read_text(encoding="utf-8") == SAMPLE_KEY


def test_stage_private_models_created(tmp_path):
    """AT1d: Private-Models/ directory is created if it doesn't exist."""
    sarah_path = tmp_path / "sarah"
    priv = sarah_path / "Private-Models"
    assert not priv.exists()
    stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    assert priv.is_dir()


# ---------------------------------------------------------------------------
# AT2: Idempotency
# ---------------------------------------------------------------------------

def test_stage_idempotent_same_inputs(tmp_path):
    """AT2a: Calling stage() twice with identical inputs yields byte-identical files."""
    sarah_path = tmp_path / "sarah"
    staged1 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    staged2 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    # Same path returned both times
    assert staged1 == staged2

    # All files have identical content after second run
    for filename, text in SAMPLE_RENDERED.items():
        fpath = staged2 / filename
        assert fpath.read_text(encoding="utf-8") == text

    assert (staged2 / ".sarah_build_key").read_text(encoding="utf-8") == SAMPLE_KEY


def test_stage_idempotent_different_content(tmp_path):
    """AT2b: Second run with different content replaces old files completely."""
    sarah_path = tmp_path / "sarah"
    first_rendered = {"MyModel.m": "old content\n"}
    second_rendered = {"MyModel.m": "new content\n", "extra.m": "extra\n"}

    stage(first_rendered, sarah_path, "MyModel", "key-v1")
    staged = stage(second_rendered, sarah_path, "MyModel", "key-v2")

    assert (staged / "MyModel.m").read_text(encoding="utf-8") == "new content\n"
    assert (staged / "extra.m").read_text(encoding="utf-8") == "extra\n"
    assert (staged / ".sarah_build_key").read_text(encoding="utf-8") == "key-v2"


# ---------------------------------------------------------------------------
# AT3: .mx cache wipe
# ---------------------------------------------------------------------------

def test_stage_wipes_mx_files(tmp_path):
    """AT3: Pre-existing .mx files in the staged dir are removed on re-stage."""
    sarah_path = tmp_path / "sarah"

    # First stage: create the tree
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    # Manually drop a .mx file to simulate SARAH having compiled the model
    mx_file = staged / "MyModel.mx"
    mx_file.write_text("binary cache content\n", encoding="utf-8")
    assert mx_file.exists()

    # Second stage: wipe-and-rewrite should remove the .mx file
    staged2 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    assert staged2 == staged
    assert not mx_file.exists(), ".mx cache file was not wiped on re-stage"


def test_stage_wipes_all_mx_files(tmp_path):
    """AT3b: Multiple .mx files are all removed."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    # Simulate multiple compiled caches
    mx_files = [staged / f"compiled{i}.mx" for i in range(3)]
    for mxf in mx_files:
        mxf.write_text("cache\n")

    stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    for mxf in mx_files:
        assert not mxf.exists(), f"{mxf.name} was not wiped"


# ---------------------------------------------------------------------------
# AT4: Filesystem permission edge case
# ---------------------------------------------------------------------------

def test_stage_removes_readonly_file_in_staged_dir(tmp_path):
    """AT4: rmtree handles a read-only file in the old staged dir (UNIX owner semantics)."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    # Make one file read-only (chmod 444)
    readonly_file = staged / "MyModel.m"
    readonly_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    # Re-staging must succeed — owner can remove files in owned dirs on UNIX
    staged2 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    assert staged2.exists()
    assert (staged2 / "MyModel.m").read_text(encoding="utf-8") == SAMPLE_RENDERED["MyModel.m"]


# ---------------------------------------------------------------------------
# AT5: Cache-key corruption
# ---------------------------------------------------------------------------

def test_stage_overwrites_corrupt_key(tmp_path):
    """AT5: A corrupt/truncated .sarah_build_key is replaced with the correct key."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    # Corrupt the key file
    (staged / ".sarah_build_key").write_text("CORRUPTED\x00\xff\n", encoding="utf-8")

    # Re-staging must replace it
    staged2 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    key_text = (staged2 / ".sarah_build_key").read_text(encoding="utf-8")
    assert key_text == SAMPLE_KEY, f"Key not replaced: got {key_text!r}"


def test_stage_overwrites_empty_key(tmp_path):
    """AT5b: An empty .sarah_build_key is replaced with the correct key."""
    sarah_path = tmp_path / "sarah"
    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    (staged / ".sarah_build_key").write_text("", encoding="utf-8")

    staged2 = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    assert (staged2 / ".sarah_build_key").read_text(encoding="utf-8") == SAMPLE_KEY


# ---------------------------------------------------------------------------
# AT6: Private-Models/ mkdir-p with nested non-existent parents
# ---------------------------------------------------------------------------

def test_stage_mkdir_p_nested(tmp_path):
    """AT6: stage() works even when neither sarah_path nor Private-Models/ exist yet."""
    # Use a deeply nested path that doesn't exist at all
    sarah_path = tmp_path / "deep" / "nested" / "sarah"
    assert not sarah_path.exists()

    staged = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)

    assert staged.is_dir()
    assert (staged / ".sarah_build_key").exists()


# ---------------------------------------------------------------------------
# AT7: Multiple rendered files
# ---------------------------------------------------------------------------

def test_stage_multiple_files(tmp_path):
    """AT7: All files in rendered dict are written correctly."""
    sarah_path = tmp_path / "sarah"
    many_files = {f"file_{i}.m": f"content {i}\n" for i in range(10)}
    staged = stage(many_files, sarah_path, "MyModel", SAMPLE_KEY)

    for filename, text in many_files.items():
        assert (staged / filename).read_text(encoding="utf-8") == text


def test_stage_single_file(tmp_path):
    """AT7b: A single-file rendered dict is handled correctly."""
    sarah_path = tmp_path / "sarah"
    staged = stage({"Only.m": "lone file\n"}, sarah_path, "M", "key1")
    assert (staged / "Only.m").read_text(encoding="utf-8") == "lone file\n"
    assert (staged / ".sarah_build_key").read_text(encoding="utf-8") == "key1"


# ---------------------------------------------------------------------------
# AT8: Returns a Path (not a string)
# ---------------------------------------------------------------------------

def test_stage_returns_path_object(tmp_path):
    """AT8: stage() returns a pathlib.Path, not a str."""
    sarah_path = tmp_path / "sarah"
    result = stage(SAMPLE_RENDERED, sarah_path, "MyModel", SAMPLE_KEY)
    assert isinstance(result, Path), f"Expected Path, got {type(result).__name__}"


# ---------------------------------------------------------------------------
# AT9: sarah_path may be passed as str
# ---------------------------------------------------------------------------

def test_stage_accepts_str_sarah_path(tmp_path):
    """AT9: sarah_path coerced from str to Path correctly."""
    sarah_path_str = str(tmp_path / "sarah")
    result = stage(SAMPLE_RENDERED, sarah_path_str, "MyModel", SAMPLE_KEY)
    expected = Path(sarah_path_str) / "Private-Models" / "MyModel"
    assert result == expected
    assert result.is_dir()


# ---------------------------------------------------------------------------
# AT10: Old staged dir content fully replaced
# ---------------------------------------------------------------------------

def test_stage_removes_stale_files(tmp_path):
    """AT10: Files present in the old staged dir but absent from new rendered are removed."""
    sarah_path = tmp_path / "sarah"

    # First stage: write three files
    first_rendered = {
        "A.m": "content A\n",
        "B.m": "content B\n",
        "stale.m": "this should be gone\n",
    }
    stage(first_rendered, sarah_path, "MyModel", "key-1")

    # Second stage: only two files — stale.m should disappear
    second_rendered = {
        "A.m": "new A\n",
        "B.m": "new B\n",
    }
    staged = stage(second_rendered, sarah_path, "MyModel", "key-2")

    assert not (staged / "stale.m").exists(), "stale.m was not removed on re-stage"
    assert (staged / "A.m").read_text(encoding="utf-8") == "new A\n"
    assert (staged / "B.m").read_text(encoding="utf-8") == "new B\n"


def test_stage_no_extra_files(tmp_path):
    """AT10b: Staged dir contains exactly the rendered files + .sarah_build_key."""
    sarah_path = tmp_path / "sarah"
    rendered = {"X.m": "x\n", "Y.m": "y\n"}
    staged = stage(rendered, sarah_path, "M", "k")

    actual_names = {p.name for p in staged.iterdir()}
    expected_names = set(rendered.keys()) | {".sarah_build_key"}
    assert actual_names == expected_names, (
        f"Unexpected files in staged dir: {actual_names - expected_names}; "
        f"missing: {expected_names - actual_names}"
    )
