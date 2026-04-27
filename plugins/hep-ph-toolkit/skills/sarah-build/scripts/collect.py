"""
collect.py — Post-SARAH output collection: glob state-dir detection + copy.

Public API:
    collect(sarah_path, sarah_name, state_dir, cache_key) -> dict
        Copies UFO (and optionally SPheno) output from SARAH's Output/ tree
        into ``state_dir/sarah_output/``. Creates a
        ``state_dir/<sarah_name>`` symlink whose basename matches the target
        directory name so MG5's ``import model <path>`` resolves correctly.
        Returns {"ufo": str, "spheno": str | None}.

    _find_output_dir(sarah_path, sarah_name) -> Path
        Globs for the state directory (e.g. EWSB/) that contains UFO/.
        Raises FileNotFoundError if no UFO output exists.

Design reference: §6.4 – §6.5 of design-final.md.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def repair_symlinks(state_dir: Path, sarah_name: str) -> list[str]:
    """Heal legacy/mis-named UFO symlinks in *state_dir*.

    MG5's ``import model <path>`` uses the symlink *basename* to re-resolve
    the model directory against the symlink's parent instead of following
    the symlink to its target. A symlink named ``ufo`` pointing at
    ``sarah_output/UFO/SingletDoubletLN`` therefore makes MG5 look for
    ``sarah_output/UFO/ufo`` and fail with ``path ... not valid anymore``.
    This helper removes any symlink in *state_dir* whose basename does not
    match its UFO target directory's basename and recreates it with the
    correct name. It is idempotent and safe to call on every run.

    Args:
        state_dir: Per-model state directory
            (e.g. ``$STATE_ROOT/models/singlet_doublet_ln/``).
        sarah_name: The SARAH model name — used to compute the canonical
            relative target ``sarah_output/UFO/<sarah_name>``.

    Returns:
        A list of human-readable strings describing each repair action
        that was performed (empty if nothing needed healing).
    """
    state_dir = Path(state_dir)
    if not state_dir.is_dir():
        return []

    actions: list[str] = []
    canonical_target = Path("sarah_output") / "UFO" / sarah_name
    canonical_link = state_dir / sarah_name

    # First pass: remove any symlink whose basename disagrees with its UFO
    # target's basename (catches the legacy ``ufo`` name and any other drift).
    for entry in state_dir.iterdir():
        if not entry.is_symlink():
            continue
        try:
            raw_target = Path(entry.readlink())
        except OSError:
            continue
        # Only touch symlinks that clearly point into sarah_output/UFO/.
        parts = raw_target.parts
        if "UFO" not in parts:
            continue
        target_basename = raw_target.name
        if entry.name == target_basename:
            continue  # already healthy
        actions.append(
            f"removed mis-named symlink {entry.name} -> {raw_target} "
            f"(expected basename {target_basename!r})"
        )
        entry.unlink()

    # Second pass: ensure the canonical symlink exists with the right target.
    # We only (re)create it when the UFO tree is actually present — otherwise
    # we would leave a dangling link behind on a fresh state dir.
    ufo_tree = state_dir / canonical_target
    if ufo_tree.is_dir():
        needs_create = True
        if canonical_link.is_symlink():
            try:
                if Path(canonical_link.readlink()) == canonical_target:
                    needs_create = False
            except OSError:
                needs_create = True
        if needs_create:
            if canonical_link.is_symlink() or canonical_link.exists():
                canonical_link.unlink()
            canonical_link.symlink_to(canonical_target)
            actions.append(
                f"created canonical symlink {sarah_name} -> {canonical_target}"
            )

    return actions


def _find_output_dir(sarah_path: Path, sarah_name: str) -> Path:
    """Return the state directory (e.g. …/Output/<sarah_name>/EWSB/) that
    contains a UFO/ sub-directory.

    SARAH writes to ``$sarah_path/Output/<sarah_name>/<StateSuffix>/UFO/``
    where ``StateSuffix`` is determined by ``NameOfStates``.  We do **not**
    hard-code ``EWSB`` — we glob and prefer it when multiple hits exist.

    Args:
        sarah_path: Path to the SARAH installation (contains ``Output/``).
        sarah_name: The SARAH model name (matches ``<sarah_name>.m``).

    Returns:
        The *state directory* ``Path`` object (the parent of ``UFO/``).

    Raises:
        FileNotFoundError: If no ``*/UFO`` directory is found under
            ``$sarah_path/Output/<sarah_name>/``.
    """
    output_base = sarah_path / "Output" / sarah_name
    candidates = list(output_base.glob("*/UFO"))
    if not candidates:
        raise FileNotFoundError(
            f"No UFO output found under {sarah_path}/Output/{sarah_name}/*/UFO"
        )
    if len(candidates) > 1:
        # Prefer EWSB if present (most common NameOfStates final state).
        ewsb = [c for c in candidates if c.parent.name == "EWSB"]
        if ewsb:
            return ewsb[0].parent  # the state dir, which contains UFO/ and SPheno/
        # Fall back to most-recently modified.
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0].parent


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def collect(
    sarah_path: Path,
    sarah_name: str,
    state_dir: Path,
    cache_key: str,
) -> dict:
    """Copy SARAH output into the plugin's state directory.

    Steps (§6.5):
    1. Locate the state output directory via :func:`_find_output_dir`.
    2. Assert ``state_output_dir/UFO/<sarah_name>/`` exists.
    3. Copy ``UFO/<sarah_name>/`` → ``state_dir/sarah_output/UFO/<sarah_name>/``
       (rmtree destination first if it already exists).
    4. If ``SPheno/`` sibling exists, copy it to
       ``state_dir/sarah_output/SPheno/<sarah_name>/``.
    5. Stamp ``state_output_dir/.sarah_build_key`` with *cache_key*.
    6. Create ``state_dir/<sarah_name>`` symlink →
       ``sarah_output/UFO/<sarah_name>/``. The symlink basename matches the
       target directory basename so MG5's ``import model`` resolves the
       symlink correctly. Any legacy ``state_dir/ufo`` symlink from prior
       builds is removed.

    Leaves ``$sarah_path/Output/`` intact (copies, not moves).

    Args:
        sarah_path: Path to the SARAH installation.
        sarah_name: The SARAH model name.
        state_dir: Per-model state directory
            (e.g. ``$STATE_ROOT/models/singlet_doublet/``).
        cache_key: Cache key string to stamp onto the output directory.

    Returns:
        ``{"ufo": str, "spheno": str | None}`` — absolute paths of the
        collected UFO directory and (if present) SPheno directory.

    Raises:
        FileNotFoundError: If the UFO output directory does not exist after
            SARAH ran.
    """
    sarah_path = Path(sarah_path)
    state_dir = Path(state_dir)

    # Step 1 — locate the state output directory (e.g. .../Output/X/EWSB/)
    state_output_dir = _find_output_dir(sarah_path, sarah_name)

    # Step 2 — locate UFO source directory.
    #
    # SARAH-4.15.3 (Package/Outputs/madgraph.m:84) sets
    # ``$sarahCurrentUfoDir = ToFileName[{$sarahCurrentOutputDir, "UFO"}]``
    # and writes ``particles.py`` directly into that flat directory with no
    # per-model subdirectory (verified empirically against dark_su3 run).
    # Older SARAH builds / older versions of this codebase assumed a nested
    # ``UFO/<sarah_name>/`` layout — we support both shapes to stay forward-
    # compatible: prefer the nested layout when present, fall back to the
    # flat layout otherwise.
    nested_ufo = state_output_dir / "UFO" / sarah_name
    flat_ufo = state_output_dir / "UFO"
    if nested_ufo.is_dir() and (nested_ufo / "particles.py").is_file():
        src_ufo = nested_ufo
    elif flat_ufo.is_dir() and (flat_ufo / "particles.py").is_file():
        src_ufo = flat_ufo
    else:
        raise FileNotFoundError(
            f"UFO model directory not found: tried {nested_ufo} and {flat_ufo}"
        )

    # Step 3 — copy UFO source into state_dir/sarah_output/UFO/<sarah_name>/
    # (Regardless of the source shape, the destination is always nested under
    # <sarah_name>/ — this is the stable public contract.)
    dest_ufo = state_dir / "sarah_output" / "UFO" / sarah_name
    if dest_ufo.exists():
        shutil.rmtree(dest_ufo)
    dest_ufo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_ufo, dest_ufo)

    # Step 4 — copy SPheno/ if it exists
    src_spheno = state_output_dir / "SPheno"
    dest_spheno: Path | None = None
    if src_spheno.is_dir():
        dest_spheno = state_dir / "sarah_output" / "SPheno" / sarah_name
        if dest_spheno.exists():
            shutil.rmtree(dest_spheno)
        dest_spheno.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_spheno, dest_spheno)

    # Step 5 — (removed) cache-key stamp moved to run_sarah._write_cache_key()
    #  so it only runs after scan_outputs() clears the collected trees
    #  (plan §3.2, D2).

    # Step 6 — ensure state_dir/<sarah_name> → sarah_output/UFO/<sarah_name>/.
    # The basename of the symlink must match its UFO target's basename so
    # MG5's ``import model <path>`` resolves correctly (MG5 uses the symlink
    # basename to re-resolve the model path against its parent rather than
    # following the symlink to its target). repair_symlinks() sweeps any
    # legacy `ufo` symlink or other basename drift from prior builds and
    # creates the canonical link with a relative target (so state_dir is
    # portable).
    repair_symlinks(state_dir, sarah_name)

    return {
        "ufo": str(dest_ufo),
        "spheno": str(dest_spheno) if dest_spheno is not None else None,
        "state_output_dir": str(state_output_dir),
    }
