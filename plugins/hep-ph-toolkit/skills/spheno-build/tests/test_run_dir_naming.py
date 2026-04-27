"""
test_run_dir_naming.py — regression tests for the run_dir timestamp-collision fix.

Background
----------
``run_spheno.py`` used to name each single-point run directory with
``datetime.now(...).strftime("%Y-%m-%dT%H%MZ")`` — minute resolution. When
``/demo`` or a scan driver fires multiple SPheno runs inside the same UTC
minute (4-point runs were observed in a recent playtest), the second run
reused the first run's ``run_dir`` and silently overwrote its
``SPheno.spc``. ``register_model`` then pointed ``latest_slha`` at whatever
ran last, invalidating earlier results.

Fix: the dir now has the shape ``YYYY-MM-DDTHHMMZ-<8 hex>``, where the hex
suffix is blake2b(JSON(overrides)) — with a ``secrets.token_hex(2)`` salt
appended iff the exact name would otherwise collide with an existing dir.

Test isolation: HEPPH_STATE_ROOT / XDG_CONFIG_HOME per the project invariant.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"

# ``YYYY-MM-DDTHHMMZ-<8 lowercase hex>``. Anchored.
_RUN_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}Z-[0-9a-f]{8}$")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def run_spheno_mod():
    return _load("run_spheno", _SCRIPTS / "run_spheno.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


class TestOverridesHash:
    def test_stable_for_same_overrides(self, run_spheno_mod):
        assert run_spheno_mod._overrides_hash({"MpsiD": 500.0, "gD": 1.2}) == \
               run_spheno_mod._overrides_hash({"gD": 1.2, "MpsiD": 500.0})

    def test_differs_for_different_overrides(self, run_spheno_mod):
        a = run_spheno_mod._overrides_hash({"MpsiD": 500.0})
        b = run_spheno_mod._overrides_hash({"MpsiD": 501.0})
        assert a != b

    def test_empty_overrides_ok(self, run_spheno_mod):
        h = run_spheno_mod._overrides_hash({})
        assert re.fullmatch(r"[0-9a-f]{8}", h)

    def test_none_overrides_ok(self, run_spheno_mod):
        assert run_spheno_mod._overrides_hash(None) == run_spheno_mod._overrides_hash({})


class TestUniqueRunDir:
    """The heart of the fix: collisions within a single UTC minute."""

    def test_format_matches_regex(self, run_spheno_mod, tmp_path):
        runs = tmp_path / "runs"
        runs.mkdir()
        ts = "2026-04-22T1706Z"
        rd = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        assert _RUN_DIR_RE.fullmatch(rd.name), rd.name
        assert rd.name.startswith(ts + "-")

    def test_identical_overrides_deterministic_before_collision(
        self, run_spheno_mod, tmp_path
    ):
        """First call with given overrides produces a deterministic name."""
        runs = tmp_path / "runs"
        runs.mkdir()
        ts = "2026-04-22T1706Z"
        a = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        b = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        # Same name until one of them is created on disk.
        assert a.name == b.name

    def test_back_to_back_same_minute_same_overrides_no_clobber(
        self, run_spheno_mod, tmp_path
    ):
        """The playtest scenario: same minute + same overrides must not collide
        once the first run_dir exists on disk."""
        runs = tmp_path / "runs"
        runs.mkdir()
        ts = "2026-04-22T1706Z"

        first = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        first.mkdir()
        (first / "SPheno.spc").write_text("# first-run output\n")

        second = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        assert second != first, "second run must not reuse the first run's dir"
        assert not second.exists(), "caller creates the dir after resolving it"
        assert _RUN_DIR_RE.fullmatch(second.name), second.name
        assert second.name.startswith(ts + "-")

        # Create it and confirm first-run output is untouched.
        second.mkdir()
        assert (first / "SPheno.spc").read_text() == "# first-run output\n"

    def test_different_overrides_same_minute_distinct(
        self, run_spheno_mod, tmp_path
    ):
        """Different overrides already differ by hash — no salting needed."""
        runs = tmp_path / "runs"
        runs.mkdir()
        ts = "2026-04-22T1706Z"
        a = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 500.0})
        a.mkdir()
        b = run_spheno_mod._unique_run_dir(runs, ts, {"MpsiD": 600.0})
        assert a != b
        assert b.name.startswith(ts + "-")

    def test_four_back_to_back_runs_all_unique(self, run_spheno_mod, tmp_path):
        """The 4-point playtest scenario — four runs with identical overrides
        inside the same minute must each land in their own dir."""
        runs = tmp_path / "runs"
        runs.mkdir()
        ts = "2026-04-22T1706Z"
        overrides = {"MpsiD": 500.0, "gD": 1.2}

        names = []
        for _ in range(4):
            rd = run_spheno_mod._unique_run_dir(runs, ts, overrides)
            rd.mkdir()
            names.append(rd.name)

        assert len(set(names)) == 4, f"collision across 4 back-to-back runs: {names}"
        for n in names:
            assert _RUN_DIR_RE.fullmatch(n), n
            assert n.startswith(ts + "-")
