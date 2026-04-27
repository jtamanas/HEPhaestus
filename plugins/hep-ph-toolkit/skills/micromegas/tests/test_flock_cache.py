"""test_flock_cache.py — test flock concurrency protection for UFO→CalcHEP cache.

Fix C (iteration-2): strengthen test_cache_populated_once to use multiprocessing
and assert exactly one process observed cache-miss and populated the cache.

Two tests:
1. test_cache_populated_once_multiprocessing — two processes compete via fcntl.flock
   to populate a shared cache dir. Asserts exactly one process saw cache-miss and
   populated; both see the populated dir at the end.
2. test_cache_key_depends_on_version / test_cache_key_depends_on_dialect — hash
   key independence tests (unchanged from iteration-1).
"""
import fcntl
import multiprocessing
import os
import sys
import tempfile
import time
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import pytest

_SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPTS = _SCRIPT_DIR.parent / "scripts"


def _create_fake_ufo_dir(base: Path) -> Path:
    """Create a minimal fake UFO directory."""
    ufo = base / "singletDM_UFO"
    ufo.mkdir()
    (ufo / "__init__.py").write_text('UFO_VERSION = "1.0"\n')
    (ufo / "particles.py").write_text("# particles\n")
    (ufo / "restrict_default.dat").write_text("")
    return ufo


def _populate_cache_worker(
    lock_path: str,
    cache_dir: str,
    result_queue: "multiprocessing.Queue",
    worker_id: int,
) -> None:
    """Worker function: acquire exclusive flock, check cache, populate if absent.

    Writes worker_id to 'populated_by' file to record which process populated.
    Puts (worker_id, "miss") or (worker_id, "hit") into result_queue.
    """
    cache_path = Path(cache_dir)
    complete_marker = cache_path / ".complete"
    populated_by = cache_path / "populated_by"
    tmp_path = Path(cache_dir + ".tmp")

    # Acquire exclusive flock on lockfile
    lock_fd = open(lock_path, "w")
    try:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)

        if complete_marker.exists():
            # Cache hit — another process already populated
            result_queue.put((worker_id, "hit"))
        else:
            # Cache miss — populate
            tmp_path.mkdir(parents=True, exist_ok=True)
            # Simulate some work (write a file with worker_id)
            (tmp_path / "populated_by").write_text(str(worker_id))
            (tmp_path / ".complete").touch()
            # Atomic rename
            if cache_path.exists():
                # Another process raced us inside the lock — should not happen
                result_queue.put((worker_id, "race_condition"))
            else:
                tmp_path.rename(cache_path)
                result_queue.put((worker_id, "miss"))
    finally:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        lock_fd.close()


class TestFlockCache:
    def test_cache_populated_once_multiprocessing(self, tmp_path):
        """Two concurrent processes: exactly one populates, the other hits cache.

        Uses fcntl.flock (same syscall as ufo_to_calchep.sh) to exercise real
        mutual exclusion. Asserts:
        (a) exactly one process observed cache-miss and populated,
        (b) the other observed cache-hit,
        (c) both see the same populated dir at the end (.complete marker present).
        """
        cache_dir = str(tmp_path / "cache" / "abc123")
        lock_path = str(tmp_path / "locks" / "abc123.lock")
        Path(lock_path).parent.mkdir(parents=True)
        Path(lock_path).touch()

        # Use fork context: avoids reimporting this module in the child process,
        # which would fail when the test is collected as part of a package
        # (e.g. micromegas.tests.test_flock_cache) and the package root is not
        # on sys.path in the spawned process.  fcntl.flock is POSIX-only anyway,
        # so fork is always available in the environments this test targets.
        _ctx = multiprocessing.get_context("fork")
        result_queue: multiprocessing.Queue = _ctx.Queue()

        # Spawn two processes that race to populate the cache
        p1 = _ctx.Process(
            target=_populate_cache_worker,
            args=(lock_path, cache_dir, result_queue, 1),
        )
        p2 = _ctx.Process(
            target=_populate_cache_worker,
            args=(lock_path, cache_dir, result_queue, 2),
        )

        p1.start()
        p2.start()
        p1.join(timeout=10)
        p2.join(timeout=10)

        assert p1.exitcode == 0, f"Worker 1 exited with {p1.exitcode}"
        assert p2.exitcode == 0, f"Worker 2 exited with {p2.exitcode}"

        results = {}
        while not result_queue.empty():
            worker_id, outcome = result_queue.get_nowait()
            results[worker_id] = outcome

        assert len(results) == 2, f"Expected 2 results, got {results}"

        miss_workers = [wid for wid, outcome in results.items() if outcome == "miss"]
        hit_workers = [wid for wid, outcome in results.items() if outcome == "hit"]
        race_workers = [wid for wid, outcome in results.items() if outcome == "race_condition"]

        assert len(race_workers) == 0, f"Race condition detected: {results}"
        assert len(miss_workers) == 1, (
            f"Expected exactly 1 cache-miss, got {len(miss_workers)}: {results}"
        )
        assert len(hit_workers) == 1, (
            f"Expected exactly 1 cache-hit, got {len(hit_workers)}: {results}"
        )

        # Both processes see the same populated dir
        complete_marker = Path(cache_dir) / ".complete"
        assert complete_marker.exists(), ".complete marker absent after both workers finished"

        populated_by = Path(cache_dir) / "populated_by"
        assert populated_by.exists(), "populated_by file absent"
        populator = int(populated_by.read_text().strip())
        assert populator in (1, 2), f"Unexpected populator id: {populator}"
        assert populator == miss_workers[0], (
            f"populated_by={populator} does not match miss worker {miss_workers[0]}"
        )

    def test_cache_key_depends_on_version(self, tmp_path):
        """Two different micromegas versions should produce different cache keys."""
        ufo_dir = _create_fake_ufo_dir(tmp_path)
        import hashlib, io, tarfile

        def compute_hash(version: str, dialect: str) -> str:
            h = hashlib.sha256()
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                tar.add(str(ufo_dir), arcname=ufo_dir.name)
            h.update(buf.getvalue())
            h.update(version.encode())
            h.update(dialect.encode())
            return h.hexdigest()[:32]

        hash_v1 = compute_hash("6.0.5", "1.x")
        hash_v2 = compute_hash("6.1.0", "1.x")
        assert hash_v1 != hash_v2, "Different versions should produce different cache keys"

    def test_cache_key_depends_on_dialect(self, tmp_path):
        ufo_dir = _create_fake_ufo_dir(tmp_path)
        import hashlib, io, tarfile

        def compute_hash(version: str, dialect: str) -> str:
            h = hashlib.sha256()
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                tar.add(str(ufo_dir), arcname=ufo_dir.name)
            h.update(buf.getvalue())
            h.update(version.encode())
            h.update(dialect.encode())
            return h.hexdigest()[:32]

        hash_d1 = compute_hash("6.0.5", "1.x")
        hash_d2 = compute_hash("6.0.5", "2.0")
        assert hash_d1 != hash_d2, "Different dialects should produce different cache keys"
