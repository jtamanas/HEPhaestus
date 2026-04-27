"""
stage.py — Stage rendered model files into SARAH's Private-Models/ search path.

Implements design §6.2: wipes stale .m AND .mx cache files before writing,
creates Private-Models/ if it doesn't exist (mkdir -p), and stamps a
.sarah_build_key so subsequent runs can detect cache freshness.

Public API:
    stage(rendered, sarah_path, sarah_name, cache_key) -> Path
        Stages rendered files into $sarah_path/Private-Models/<sarah_name>/.
        Returns the staged directory Path.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import shutil
from pathlib import Path


def stage(
    rendered: dict[str, str],
    sarah_path: Path | str,
    sarah_name: str,
    cache_key: str,
) -> Path:
    """Stage rendered model files into SARAH's Private-Models search path.

    Per design §6.2:
    1. mkdir -p $sarah_path/Private-Models/  (SARAH does not create it).
    2. If $sarah_path/Private-Models/<sarah_name>/ exists, rmtree it — this
       wipes BOTH stale .m source files AND any .mx compiled cache files.
    3. mkdir staged dir; write each (filename, text) from rendered.
    4. Stamp .sarah_build_key with cache_key.
    5. Return staged Path.

    Args:
        rendered:    Mapping of filename → file text to write (e.g.
                     {"X.m": "...", "particles.m": "...", ...}).
        sarah_path:  Root of the SARAH installation (contains SARAH.m).
        sarah_name:  Model name as SARAH expects it (e.g. "SingletDoublet").
        cache_key:   Opaque string stamped into .sarah_build_key.

    Returns:
        Path to $sarah_path/Private-Models/<sarah_name>/ (the staged dir).
    """
    sarah_path = Path(sarah_path)

    # Step 1: mkdir -p Private-Models/
    priv = sarah_path / "Private-Models"
    priv.mkdir(parents=True, exist_ok=True)

    # Step 2: wipe stale staged dir (including any .mx compiled caches)
    staged = priv / sarah_name
    if staged.exists():
        shutil.rmtree(staged)

    # Step 3: create fresh staged dir and write rendered files
    staged.mkdir()
    for filename, text in rendered.items():
        (staged / filename).write_text(text, encoding="utf-8")

    # Step 4: stamp cache key
    (staged / ".sarah_build_key").write_text(cache_key, encoding="utf-8")

    # Step 5: return staged path
    return staged
