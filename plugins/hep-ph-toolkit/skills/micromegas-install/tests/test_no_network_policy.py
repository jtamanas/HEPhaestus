"""test_no_network_policy.py — verify HEPPH_NO_NETWORK=1 triggers MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY.

Runs install_impl.sh (or install_micromegas.sh install) with HEPPH_NO_NETWORK=1
and an empty HEPPH_OFFLINE_CACHE_DIR; asserts exit code EXIT_DOWNLOAD (12) and
blocker code MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY on stderr.
"""
import os
import subprocess
import sys
import tempfile
import json
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent / "scripts"
_INSTALL_MICROMEGAS = _SCRIPTS / "install_micromegas.sh"

EXIT_DOWNLOAD = 12


def _run_install(env_overrides: dict, extra_args: list[str] | None = None) -> tuple[int, str, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    result = subprocess.run(
        ["bash", str(_INSTALL_MICROMEGAS), "install"] + (extra_args or []),
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def _find_blocker(stderr: str) -> dict | None:
    for line in stderr.splitlines():
        line = line.strip()
        if line.startswith("{") and "code" in line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


class TestNoNetworkPolicy:
    def test_no_network_empty_cache_exits_download(self, tmp_path):
        """HEPPH_NO_NETWORK=1 with empty cache → EXIT_DOWNLOAD + MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY."""
        empty_cache = tmp_path / "cache"
        empty_cache.mkdir()
        install_dir = tmp_path / "install"

        rc, stdout, stderr = _run_install(
            {
                "HEPPH_NO_NETWORK": "1",
                "HEPPH_OFFLINE_CACHE_DIR": str(empty_cache),
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "HEPPH_SKIP_DISK_CHECK": "1",
            },
            [str(install_dir)],
        )
        assert rc == EXIT_DOWNLOAD, (
            f"Expected exit {EXIT_DOWNLOAD}, got {rc}. stderr: {stderr[:500]}"
        )
        blocker = _find_blocker(stderr)
        assert blocker is not None, f"No blocker JSON in stderr: {stderr[:500]}"
        assert blocker["code"] == "MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY", (
            f"Expected MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY, got {blocker['code']}"
        )
        assert blocker["mode"] == "fatal"

    def test_no_network_with_cached_tarball_succeeds_past_download(self, tmp_path):
        """HEPPH_NO_NETWORK=1 with cached tarball proceeds past download (may fail at extract).

        This test only asserts the download step passes; the rest of the install
        will fail without a real tarball. We accept any exit code != EXIT_DOWNLOAD.
        """
        cache = tmp_path / "cache"
        cache.mkdir()
        # Create a dummy tarball (not a real micrOMEGAs archive)
        fake_tarball = cache / "micromegas_6.0.5.tgz"
        fake_tarball.write_bytes(b"\x1f\x8b\x00")  # Invalid gzip, will fail at extract

        install_dir = tmp_path / "install"

        rc, stdout, stderr = _run_install(
            {
                "HEPPH_NO_NETWORK": "1",
                "HEPPH_OFFLINE_CACHE_DIR": str(cache),
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "HEPPH_SKIP_DISK_CHECK": "1",
            },
            [str(install_dir)],
        )
        # Should NOT be EXIT_DOWNLOAD since the cache had the file
        assert rc != EXIT_DOWNLOAD, (
            f"Expected exit != {EXIT_DOWNLOAD} (cache hit), got {rc}. stderr: {stderr[:500]}"
        )
        blocker = _find_blocker(stderr)
        if blocker:
            assert blocker["code"] != "MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY", (
                "Should not emit MICROMEGAS_DOWNLOAD_BLOCKED_BY_POLICY when cache has tarball"
            )
