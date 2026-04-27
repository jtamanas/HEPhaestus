"""
regenerate_fixture.py — Rebuild tests/fixtures/sarah_output_darksu3.tar.gz
from a real W3 SARAH output tree.

Usage:
    python3 regenerate_fixture.py [--model dark_su3] [--force]

Requires W3 to have produced SARAH output at:
    $STATE_ROOT/models/<model>/sarah_output/SPheno/<SarahName>/

Hard cap: 10 MB gzipped (policy from §2.11).
On success, overwrites tests/fixtures/sarah_output_darksu3.tar.gz and logs a checksum.

Run this script after W3 merges and the real SARAH output is available.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import hashlib
import importlib.util as _ilu
import os
import tarfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_CONFIG_HELPERS = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers" / "config_helpers.py"
_FIXTURE_PATH = _SKILL_DIR / "tests" / "fixtures" / "sarah_output_darksu3.tar.gz"

MAX_FIXTURE_BYTES = 10 * 1024 * 1024  # 10 MB


def _load_module(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def regenerate(model_name: str = "dark_su3", force: bool = False) -> None:
    config_helpers = _load_module("config_helpers", _CONFIG_HELPERS)
    sarah_name_mod = _load_module("sarah_name", _SHARED_DIR / "sarah_name.py")

    config = config_helpers.load_config()
    state_root = config_helpers.STATE_ROOT

    try:
        sarah_name = sarah_name_mod.modelspec_name_to_sarah(model_name)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    source_dir = (
        state_root / "models" / model_name /
        "sarah_output" / "SPheno" / sarah_name
    )

    if not source_dir.exists():
        print(
            f"error: SARAH SPheno output not found at {source_dir}.\n"
            "Run W3 /sarah-build first:\n"
            "  python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py "
            "<spec.yaml>",
            file=sys.stderr,
        )
        sys.exit(1)

    if _FIXTURE_PATH.exists() and not force:
        print(
            f"Fixture already exists at {_FIXTURE_PATH}.\n"
            "Use --force to regenerate.",
            file=sys.stderr,
        )
        sys.exit(0)

    print(f"Generating fixture from {source_dir} ...")
    _FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = _FIXTURE_PATH.with_suffix(".tar.gz.tmp")
    with tarfile.open(tmp_path, "w:gz", compresslevel=9) as tf:
        tf.add(
            str(source_dir),
            arcname=f"sarah_output/SPheno/{sarah_name}",
            recursive=True,
        )

    size_bytes = tmp_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"Compressed size: {size_mb:.2f} MB")

    if size_bytes > MAX_FIXTURE_BYTES:
        tmp_path.unlink(missing_ok=True)
        print(
            f"error: fixture size {size_mb:.2f} MB exceeds hard cap of "
            f"{MAX_FIXTURE_BYTES // (1024*1024)} MB (§2.11).\n"
            "Consider splitting into sub-fixtures or stripping unnecessary files.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Compute SHA-256
    digest = hashlib.sha256(tmp_path.read_bytes()).hexdigest()

    # Atomic rename
    tmp_path.rename(_FIXTURE_PATH)
    print(f"Fixture written to {_FIXTURE_PATH}")
    print(f"SHA-256: {digest}")
    print(f"Size: {size_mb:.2f} MB")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Rebuild sarah_output_darksu3.tar.gz from real W3 SARAH output."
    )
    parser.add_argument(
        "--model", default="dark_su3",
        help="Model name (default: dark_su3)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing fixture."
    )
    args = parser.parse_args()
    regenerate(args.model, force=args.force)
