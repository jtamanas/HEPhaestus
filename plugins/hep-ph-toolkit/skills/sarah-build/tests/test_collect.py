"""
test_collect.py — Unit tests for scripts/collect.py.

Acceptance tests from T03b spec:
  AT1: _find_output_dir returns .../X/EWSB/ when sarah_path/Output/X/EWSB/UFO/ exists.
  AT2: _find_output_dir raises FileNotFoundError on empty glob.
  AT3: With two state dirs (EWSB, GaugeES), _find_output_dir prefers EWSB.
  AT4: collect() creates $state_dir/sarah_output/UFO/<sarah_name>/; leaves source intact.
  AT5: collect() creates $state_dir/<sarah_name> symlink -> sarah_output/UFO/<sarah_name>.
       (Basename matches target — avoids MG5 `import model` symlink-basename bug.)
"""

import sys
from pathlib import Path

import pytest

# sys.path is set up by conftest.py
from collect import collect, _find_output_dir, repair_symlinks  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ufo_tree(base: Path, sarah_name: str, state_suffix: str, *,
                   flat: bool = True) -> Path:
    """Create a minimal fake SARAH Output tree. Returns the UFO source dir.

    Args:
        base: Root of the fake $sarah_path.
        sarah_name: SARAH model name.
        state_suffix: e.g. ``EWSB`` or ``GaugeES``.
        flat: If True (default), use the real SARAH-4.15.3 layout that writes
            ``Output/<name>/<state>/UFO/particles.py`` flat (verified empirically
            in Package/Outputs/madgraph.m:84). If False, use the nested
            ``Output/<name>/<state>/UFO/<name>/particles.py`` layout for
            forward compatibility with other SARAH releases.
    """
    if flat:
        ufo_src = base / "Output" / sarah_name / state_suffix / "UFO"
    else:
        ufo_src = base / "Output" / sarah_name / state_suffix / "UFO" / sarah_name
    ufo_src.mkdir(parents=True)
    (ufo_src / "particles.py").write_text("# fake UFO particles\n")
    return ufo_src


def _make_spheno_tree(base: Path, sarah_name: str, state_suffix: str) -> Path:
    """Create a minimal fake SPheno directory inside the state dir."""
    spheno_dir = base / "Output" / sarah_name / state_suffix / "SPheno"
    spheno_dir.mkdir(parents=True, exist_ok=True)
    (spheno_dir / "dummy.f90").write_text("! fake SPheno\n")
    return spheno_dir


# ---------------------------------------------------------------------------
# AT1: _find_output_dir basic happy path
# ---------------------------------------------------------------------------

def test_find_output_dir_ewsb(tmp_path):
    """AT1: Returns the EWSB state dir when Output/X/EWSB/UFO/ exists."""
    sarah_name = "X"
    _make_ufo_tree(tmp_path, sarah_name, "EWSB")
    result = _find_output_dir(tmp_path, sarah_name)
    expected = tmp_path / "Output" / sarah_name / "EWSB"
    assert result == expected


# ---------------------------------------------------------------------------
# AT2: _find_output_dir raises on empty glob
# ---------------------------------------------------------------------------

def test_find_output_dir_raises_empty(tmp_path):
    """AT2: Raises FileNotFoundError when no UFO output exists."""
    sarah_name = "X"
    (tmp_path / "Output" / sarah_name).mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="No UFO output found"):
        _find_output_dir(tmp_path, sarah_name)


# ---------------------------------------------------------------------------
# AT3: Two state dirs — prefers EWSB
# ---------------------------------------------------------------------------

def test_find_output_dir_prefers_ewsb(tmp_path):
    """AT3: With EWSB and GaugeES both present, prefer EWSB."""
    sarah_name = "X"
    _make_ufo_tree(tmp_path, sarah_name, "GaugeES")
    _make_ufo_tree(tmp_path, sarah_name, "EWSB")
    result = _find_output_dir(tmp_path, sarah_name)
    assert result.name == "EWSB"


# ---------------------------------------------------------------------------
# AT4: collect() creates dest tree; leaves source intact
# ---------------------------------------------------------------------------

def test_collect_creates_ufo_dest_leaves_source(tmp_path):
    """AT4: collect() copies UFO into state_dir/sarah_output/UFO/<name>/; source stays."""
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    ufo_src = _make_ufo_tree(sarah_path, sarah_name, "EWSB")

    result = collect(sarah_path, sarah_name, state_dir, cache_key="sha256hex=4.15.3")

    # Destination was created
    dest_ufo = state_dir / "sarah_output" / "UFO" / sarah_name
    assert dest_ufo.is_dir(), "UFO destination directory was not created"
    assert (dest_ufo / "particles.py").exists(), "UFO contents were not copied"

    # Source is still intact
    assert ufo_src.is_dir(), "Source UFO directory was deleted (should be a copy, not move)"
    assert (ufo_src / "particles.py").exists(), "Source file was removed"

    # Return value contains expected ufo path
    assert result["ufo"] == str(dest_ufo)


# ---------------------------------------------------------------------------
# AT5: collect() creates ufo symlink
# ---------------------------------------------------------------------------

def test_collect_creates_ufo_symlink(tmp_path):
    """AT5: collect() creates state_dir/<sarah_name> -> sarah_output/UFO/<sarah_name>/.

    The symlink basename matches the target directory basename so MG5's
    `import model <path>` resolves correctly (see collect.py Step 6).
    """
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")

    collect(sarah_path, sarah_name, state_dir, cache_key="sha256hex=4.15.3")

    symlink_path = state_dir / sarah_name
    assert symlink_path.is_symlink(), (
        f"state_dir/{sarah_name} is not a symlink"
    )
    # The resolved symlink should point to the UFO model directory
    resolved = symlink_path.resolve()
    expected_resolved = (state_dir / "sarah_output" / "UFO" / sarah_name).resolve()
    assert resolved == expected_resolved, (
        f"Symlink resolves to {resolved!r}, expected {expected_resolved!r}"
    )


def test_collect_removes_legacy_ufo_symlink(tmp_path):
    """collect() removes any pre-existing `state_dir/ufo` symlink from old builds.

    Prior versions of collect() created a symlink named literally "ufo"; that
    tripped MG5's symlink-basename resolution. New builds create
    state_dir/<sarah_name> and must cleanly remove the legacy pointer.
    """
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Pre-seed a legacy symlink as if a prior build had left one behind.
    (state_dir / "ufo").symlink_to(Path("sarah_output") / "UFO" / sarah_name)

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")
    collect(sarah_path, sarah_name, state_dir, cache_key="k")

    assert not (state_dir / "ufo").exists(), (
        "Legacy state_dir/ufo symlink was not removed"
    )
    assert (state_dir / sarah_name).is_symlink()


# ---------------------------------------------------------------------------
# Extra: SPheno copy and cache-key stamp
# ---------------------------------------------------------------------------

def test_collect_copies_spheno_when_present(tmp_path):
    """collect() copies SPheno/ into state_dir/sarah_output/SPheno/<name>/."""
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")
    _make_spheno_tree(sarah_path, sarah_name, "EWSB")

    result = collect(sarah_path, sarah_name, state_dir, cache_key="k")

    dest_spheno = state_dir / "sarah_output" / "SPheno" / sarah_name
    assert dest_spheno.is_dir()
    assert result["spheno"] == str(dest_spheno)


def test_collect_spheno_none_when_absent(tmp_path):
    """collect() returns spheno=None when SPheno/ is not present."""
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")

    result = collect(sarah_path, sarah_name, state_dir, cache_key="k")
    assert result["spheno"] is None


def test_collect_does_not_stamp_cache_key(tmp_path):
    """collect() MUST NOT stamp .sarah_build_key any more (plan §3.2, D2).

    Responsibility moved to run_sarah._write_cache_key(), gated on the
    scan_outputs() clean result. collect() returns state_output_dir so the
    caller can stamp after the scan passes.
    """
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")

    cache_key = "abc123=4.15.3"
    result = collect(sarah_path, sarah_name, state_dir, cache_key=cache_key)

    key_path = sarah_path / "Output" / sarah_name / "EWSB" / ".sarah_build_key"
    assert not key_path.exists(), (
        "collect() must NOT stamp state_output_dir/.sarah_build_key — "
        "run_sarah._write_cache_key() owns that stamp now."
    )

    # And collect() must now return state_output_dir so the caller can stamp.
    assert "state_output_dir" in result
    assert Path(result["state_output_dir"]) == (
        sarah_path / "Output" / sarah_name / "EWSB"
    )


def test_collect_supports_nested_ufo_layout(tmp_path):
    """Forward-compatibility: if SARAH produces nested UFO/<name>/, collect() handles it.

    Real SARAH-4.15.3 writes flat (see _make_ufo_tree default). Some SARAH builds /
    future releases may nest under <sarah_name>/. collect() must accept both.
    """
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB", flat=False)

    result = collect(sarah_path, sarah_name, state_dir, cache_key="k")

    dest_ufo = state_dir / "sarah_output" / "UFO" / sarah_name
    assert dest_ufo.is_dir()
    assert (dest_ufo / "particles.py").exists()
    assert result["ufo"] == str(dest_ufo)


def test_repair_symlinks_heals_legacy_ufo_basename(tmp_path):
    """repair_symlinks() heals a legacy `state_dir/ufo` symlink in place.

    Reproduces the shape observed in pre-fix state dirs:
        state_dir/ufo -> sarah_output/UFO/Foo
    After repair:
        state_dir/Foo -> sarah_output/UFO/Foo
        state_dir/ufo absent
    The UFO tree on disk is untouched.
    """
    sarah_name = "Foo"
    state_dir = tmp_path / "state"
    ufo_tree = state_dir / "sarah_output" / "UFO" / sarah_name
    ufo_tree.mkdir(parents=True)
    (ufo_tree / "particles.py").write_text("# fake UFO\n")

    # Pre-seed the legacy shape exactly as observed on disk.
    legacy_link = state_dir / "ufo"
    legacy_target = Path("sarah_output") / "UFO" / sarah_name
    legacy_link.symlink_to(legacy_target)

    actions = repair_symlinks(state_dir, sarah_name)

    # Legacy link gone; canonical link present and pointing at the same target.
    assert not legacy_link.exists(), "legacy state_dir/ufo must be removed"
    assert not legacy_link.is_symlink(), "legacy symlink must be unlinked"
    canonical = state_dir / sarah_name
    assert canonical.is_symlink(), (
        f"canonical state_dir/{sarah_name} symlink not created"
    )
    assert Path(canonical.readlink()) == legacy_target, (
        "canonical symlink must point at the same UFO target"
    )
    # UFO tree is untouched.
    assert (ufo_tree / "particles.py").exists()
    # The action log is non-empty (for observability in real runs).
    assert actions, "repair_symlinks should report at least one action"


def test_repair_symlinks_idempotent_on_healthy_state_dir(tmp_path):
    """repair_symlinks() is a no-op when the canonical link already matches."""
    sarah_name = "Foo"
    state_dir = tmp_path / "state"
    ufo_tree = state_dir / "sarah_output" / "UFO" / sarah_name
    ufo_tree.mkdir(parents=True)
    target = Path("sarah_output") / "UFO" / sarah_name
    (state_dir / sarah_name).symlink_to(target)

    actions = repair_symlinks(state_dir, sarah_name)

    assert actions == [], f"expected no repairs, got {actions}"
    assert (state_dir / sarah_name).is_symlink()


def test_collect_idempotent(tmp_path):
    """Calling collect() twice on the same model is safe (rmtrees old dest)."""
    sarah_name = "MyModel"
    sarah_path = tmp_path / "sarah"
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    _make_ufo_tree(sarah_path, sarah_name, "EWSB")

    collect(sarah_path, sarah_name, state_dir, cache_key="k1")
    collect(sarah_path, sarah_name, state_dir, cache_key="k2")

    dest_ufo = state_dir / "sarah_output" / "UFO" / sarah_name
    assert dest_ufo.is_dir()
    # Symlink should still work
    assert (state_dir / sarah_name).is_symlink()
