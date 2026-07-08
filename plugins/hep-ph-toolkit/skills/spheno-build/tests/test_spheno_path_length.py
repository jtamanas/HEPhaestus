"""
test_spheno_path_length.py — preflight for SPheno's silent argv truncation.

Background
----------
The real SPheno binary reads its two positional args (LesHouches.in path,
SPheno.spc path) into a fixed-length Fortran buffer and silently truncates
anything past ~120 chars. The truncated path doesn't exist, so SPheno just
reports a plain file-not-found — there is no hint that the *original* path
was fine and only the argv got mangled.

``run_point.safe_spheno_arg`` is the pure preflight helper that decides what
string to actually hand SPheno for a given path:

    1. absolute path fits (<= limit)          -> use it unchanged
    2. absolute path too long, but the path is
       under the cwd SPheno will run with     -> use the cwd-relative form
    3. neither fits                           -> raise PathTooLongError

``run_point.run`` invokes SPheno with ``cwd=out_dir`` and both
``LesHouches.in`` / ``SPheno.spc`` are direct children of ``out_dir``, so in
practice branch 2 always succeeds no matter how long ``out_dir`` itself is —
branch 3 is a loud-failure safety net, not a path exercised in normal
operation.

These tests exercise the helper (and run()'s use of it) in isolation, with
no real SPheno binary — a tiny stub script stands in.
"""

from __future__ import annotations

import importlib.util
import os
import stat
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_CLEAN_FIXTURE = _HERE / "fixtures" / "slha" / "clean_spectrum.spc"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def run_point_mod():
    return _load("run_point", _SCRIPTS / "run_point.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


def _install_stub_spheno(state_root: Path, model_name: str, sarah_name: str) -> Path:
    """Stub SPheno binary: fails (missing-file style) unless its two argv
    paths, resolved against its own cwd, actually point at real files.
    This mimics the real binary's behaviour if we ever *did* hand it a
    truncated/garbage path — the run must not silently "succeed"."""
    bin_dir = state_root / "models" / model_name / "spheno_bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub_path = bin_dir / f"SPheno{sarah_name}"
    stub_body = f"""#!/usr/bin/env bash
set -e
if [ ! -f "$1" ]; then
  echo "stub: input card not found at: $1" >&2
  exit 1
fi
cp "{_CLEAN_FIXTURE}" "$2"
exit 0
"""
    stub_path.write_text(stub_body)
    stub_path.chmod(stub_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return stub_path


# --- (a)/(c): pure helper, short path passes through unchanged --------------


def test_short_path_passes_through_unchanged(run_point_mod, tmp_path):
    # pytest's own tmp_path prefix (e.g. under /private/var/folders/.../)
    # can itself be long, so pin an explicit limit here to isolate what
    # we're actually testing: the "already fits" branch is a no-op.
    cwd = tmp_path
    short = cwd / "LesHouches.in"
    short.write_text("x")
    generous_limit = len(str(short.resolve())) + 10

    result = run_point_mod.safe_spheno_arg(short, cwd, limit=generous_limit)

    assert result == str(short.resolve())
    assert len(result) <= generous_limit


# --- (b)/(c): pure helper, long path is shortened via cwd-relative form ----


def test_long_path_under_cwd_is_shortened_to_relative_form(run_point_mod, tmp_path):
    # Build an out_dir path deep enough that the absolute form of a child
    # file blows past the 119-char limit, regardless of tmp_path's own
    # (already fairly long, pytest-managed) prefix.
    deep = tmp_path
    for i in range(12):
        deep = deep / f"a_long_path_segment_number_{i:02d}"
    deep.mkdir(parents=True)
    long_file = deep / "LesHouches.in"
    long_file.write_text("x")

    abs_len = len(str(long_file.resolve()))
    assert abs_len > run_point_mod.SPHENO_ARG_LIMIT, (
        f"test fixture didn't actually build a long-enough path ({abs_len} chars); "
        "widen the loop above"
    )

    result = run_point_mod.safe_spheno_arg(long_file, deep)

    assert result == "LesHouches.in"
    assert len(result) <= run_point_mod.SPHENO_ARG_LIMIT


def test_path_outside_cwd_and_too_long_raises(run_point_mod, tmp_path):
    deep = tmp_path
    for i in range(12):
        deep = deep / f"a_long_path_segment_number_{i:02d}"
    deep.mkdir(parents=True)
    long_file = deep / "LesHouches.in"
    long_file.write_text("x")

    other_cwd = tmp_path / "unrelated"
    other_cwd.mkdir()

    with pytest.raises(run_point_mod.PathTooLongError):
        run_point_mod.safe_spheno_arg(long_file, other_cwd)


# --- end-to-end: run() with a genuinely long out_dir still succeeds -------


def test_run_succeeds_with_long_out_dir_path(run_point_mod, tmp_path, monkeypatch):
    """Full run() through a stub binary, with out_dir nested deep enough
    that the absolute LesHouches.in / SPheno.spc paths exceed the Fortran
    argv limit. Before the preflight, this would invoke SPheno with a
    to-be-truncated absolute path and fail silently; after the preflight,
    run() must pass the cwd-relative form and succeed normally."""
    model_name = "singlet_doublet"
    sarah_name = "SingletDoublet"
    state_root = Path(os.environ["HEPPH_STATE_ROOT"])
    _install_stub_spheno(state_root, model_name, sarah_name)

    deep = tmp_path
    for i in range(12):
        deep = deep / f"a_long_path_segment_number_{i:02d}"
    out_dir = deep / "runs" / "20260101T000000Z"
    out_dir.mkdir(parents=True)

    assert len(str((out_dir / "LesHouches.in").resolve())) > run_point_mod.SPHENO_ARG_LIMIT

    input_card = tmp_path / "staged_lh" / "LesHouches.in"
    input_card.parent.mkdir()
    input_card.write_text("Block MODSEL\n   1   0\n")

    result = run_point_mod.run(
        model_name=model_name,
        input_card=input_card,
        out_dir=out_dir,
    )

    assert result["status"] == "ok", result
    assert (out_dir / "SPheno.spc").exists()


def test_run_emits_blocker_when_path_cannot_be_shortened(run_point_mod, tmp_path, monkeypatch):
    """If safe_spheno_arg can't produce a safe path (e.g. spc_out somehow
    isn't under out_dir), run() must emit a fatal SPHENO_PATH_TOO_LONG
    blocker rather than silently invoking SPheno with a truncated path."""
    model_name = "singlet_doublet"
    sarah_name = "SingletDoublet"
    state_root = Path(os.environ["HEPPH_STATE_ROOT"])
    _install_stub_spheno(state_root, model_name, sarah_name)

    out_dir = tmp_path / "runs" / "20260101T000000Z"
    out_dir.mkdir(parents=True)
    input_card = tmp_path / "LesHouches.in"
    input_card.write_text("Block MODSEL\n   1   0\n")

    # Force the preflight to fail for both args regardless of actual
    # length, to exercise the blocker path deterministically.
    def _always_too_long(path, cwd, limit=None):
        raise run_point_mod.PathTooLongError("forced for test")

    monkeypatch.setattr(run_point_mod, "safe_spheno_arg", _always_too_long)

    result = run_point_mod.run(
        model_name=model_name,
        input_card=input_card,
        out_dir=out_dir,
    )

    assert result["status"] == "fatal"
    assert result["blocker_code"] == "SPHENO_PATH_TOO_LONG"
