"""test_legacy_hb_slha_results.py — pin the HB-5 SLHA result-block parse.

HiggsBounds-5 in SLHA mode writes its verdict into ``Block HiggsBoundsResults``
inside the SLHA file; stdout carries only BR diagnostics. legacy_driver used to
parse stdout, reporting a vacuous ``obsratio_max = 0.0`` /
``most_sensitive_channel = None`` while the allow/exclude flag looked fine.

Fixture: ``fixtures/singlet_doublet_hb_results.slha`` — the VERBATIM block
HiggsBounds-5.10.2 (LandH) appended to the singlet_doublet SPheno.spc at the
canonical benchmark (MS=150, MPsi=500, yh1=1, theta=0). Real run evidence:
HBresult=1 (allowed), global obsratio 0.6063, most sensitive channel 85 =
(pp)->h1->ZZ->4l (CMS 1312.5353). Note HB-5 semantics: the global obsratio is
that of the most statistically SENSITIVE channel, not the numeric max — the
rank-2 WW channel carries a higher raw obsratio (0.956) but lower sensitivity.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
FIXTURE = Path(__file__).parent / "fixtures" / "singlet_doublet_hb_results.slha"


@pytest.fixture(scope="module")
def driver():
    import sys
    spec = importlib.util.spec_from_file_location(
        "legacy_driver", SKILL_DIR / "scripts" / "legacy_driver.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec: the module defines dataclasses under
    # `from __future__ import annotations`, and dataclass processing resolves
    # string annotations via sys.modules[cls.__module__] — without this the
    # test only passes when another test happened to import the module first.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parsed(driver):
    return driver._parse_hb_slha_results(FIXTURE.read_text())


def test_block_parses(parsed):
    assert parsed is not None, "HiggsBoundsResults block not recognised"


def test_global_verdict_allowed(parsed):
    ms = parsed.most_sensitive_channel
    assert ms is not None
    assert ms.hb_result == 1  # HBresult=1: allowed


def test_global_obsratio_is_sensitive_channel_not_max(parsed):
    """obsratio_max must be the rank-0 (global) 0.6063, NOT the raw per-channel
    max 0.956 (WW, less sensitive) and NOT the pre-fix vacuous 0.0."""
    assert abs(parsed.obsratio_max - 0.60629644976076968) < 1e-12, (
        parsed.obsratio_max
    )
    assert parsed.obsratio_max != 0.0


def test_most_sensitive_channel_identity(parsed):
    ms = parsed.most_sensitive_channel
    assert ms.id == 85
    assert "Z Z" in ms.expref and "1312.5353" in ms.expref


def test_ranked_channels_extracted(parsed):
    assert len(parsed.channels) == 3
    assert [ch.id for ch in parsed.channels] == [85, 59, 197]
    assert abs(parsed.channels[1].obsratio - 0.95644486565298792) < 1e-12
    # All allowed at this point.
    assert all(ch.hb_result == 1 for ch in parsed.channels)


def test_compute_hb_allowed_on_parsed_channels(parsed):
    spec = importlib.util.spec_from_file_location(
        "exclusion", SKILL_DIR / "scripts" / "exclusion.py"
    )
    excl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(excl)
    assert excl.compute_hb_allowed(parsed.channels) is True


def test_absent_block_returns_none(driver):
    """SLHA without the block -> None, so run_higgsbounds falls back to the
    legacy stdout parse instead of fabricating an empty result."""
    assert driver._parse_hb_slha_results("Block MASS\n  25  125.0  # hh\n") is None


# ---------------------------------------------------------------------------
# R2-1: HB-5's Fortran buffer truncates the SLHA prefix at ~100 chars, so the
# driver must invoke HB with cwd=<slha dir> and the BASENAME as prefix. With
# an absolute path over the limit HB prints "problem opening the SLHA file",
# exits 0, writes no block -> the vacuous obsratio_max=0.0 silent pass.
# Real state-root run paths (~102 chars) exceed the limit.
# ---------------------------------------------------------------------------
FIXTURE_FULL_SLHA = Path(__file__).parent / "fixtures" / "singlet_doublet_spheno.slha"


def _long_run_dir(tmp_path: Path) -> Path:
    """Build a run dir whose SPheno.spc path exceeds 100 characters."""
    d = tmp_path
    while len(str(d / "SPheno.spc")) <= 110:
        d = d / "a-deeply-nested-model-run-directory"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _fake_hb_build(tmp_path: Path) -> Path:
    """Create a build dir holding a fake executable to satisfy _find_binary
    (subprocess.run is monkeypatched, so it is never actually executed)."""
    build = tmp_path / "hb_build"
    build.mkdir(exist_ok=True)
    binary = build / "HiggsBounds"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    return build


class TestHbInvocationShape:
    """Hermetic: pin the basename+cwd invocation without the real binary."""

    def test_prefix_is_basename_and_cwd_is_dir(self, driver, tmp_path, monkeypatch):
        hb_build = _fake_hb_build(tmp_path)
        run_dir = _long_run_dir(tmp_path)
        slha = run_dir / "SPheno.spc"
        slha.write_text(FIXTURE_FULL_SLHA.read_text())
        assert len(str(slha)) > 100  # the shape that broke production

        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["cwd"] = kwargs.get("cwd")
            # Simulate HB-5: append the results block to the SLHA in cwd.
            target = Path(kwargs["cwd"]) / cmd[-1]
            target.write_text(target.read_text() + "\n" + FIXTURE.read_text())

            class P:
                returncode = 0
                stdout = "beginning output...\n finished\n"
                stderr = ""
            return P()

        monkeypatch.setattr(driver.subprocess, "run", fake_run)
        result = driver.run_higgsbounds(str(hb_build), str(slha), 1, 0)

        # Basename as prefix, dir as cwd — never the >100-char absolute path.
        assert captured["cmd"][-1] == "SPheno.spc", captured["cmd"]
        assert captured["cwd"] == str(run_dir)
        # And the SLHA-block results were read back: real, not vacuous.
        assert abs(result.obsratio_max - 0.60629644976076968) < 1e-12
        assert result.channels

    def test_zero_results_raises_blocker_not_vacuous_allowed(
        self, driver, tmp_path, monkeypatch
    ):
        """HB exiting 0 with no block and no stdout table must raise
        HIGGSTOOLS_HB_NO_RESULT — an empty HBResult would make
        compute_hb_allowed([]) vacuously True (silent false 'allowed')."""
        hb_build = _fake_hb_build(tmp_path)
        run_dir = _long_run_dir(tmp_path)
        slha = run_dir / "SPheno.spc"
        slha.write_text(FIXTURE_FULL_SLHA.read_text())

        def fake_run(cmd, **kwargs):
            class P:
                returncode = 0
                stdout = " problem opening the SLHA file\n"
                stderr = ""
            return P()

        monkeypatch.setattr(driver.subprocess, "run", fake_run)
        with pytest.raises(driver.HiggsBoundsNoResultError) as ei:
            driver.run_higgsbounds(str(hb_build), str(slha), 1, 0)
        assert ei.value.code == "HIGGSTOOLS_HB_NO_RESULT"
        assert ei.value.mode == "recoverable"


# ---------------------------------------------------------------------------
# Gated live-binary test: real HiggsBounds on a >100-char path.
# ---------------------------------------------------------------------------
def _hb_build_dir() -> Path | None:
    import json as _json
    import os as _os
    cfg = (
        Path(_os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "hephaestus" / "config.json"
    )
    if not cfg.exists():
        return None
    try:
        path = _json.loads(cfg.read_text()).get("higgsbounds_path", "")
    except Exception:
        return None
    if not path:
        return None
    build = Path(path)
    for cand in (build / "HiggsBounds", build / "bin" / "HiggsBounds"):
        if cand.is_file():
            return build
    return None


_HB_BUILD = _hb_build_dir()


@pytest.mark.skipif(
    _HB_BUILD is None,
    reason="HiggsBounds legacy binary not registered in "
    "~/.config/hephaestus/config.json (higgsbounds_path)",
)
def test_real_hb_on_long_path_yields_real_results(driver, tmp_path):
    """Live regression for the >100-char truncation: the real HB-5 binary,
    invoked by run_higgsbounds on a deeply nested path, must return the real
    verdict (obsratio 0.6063, channel 85) — not the vacuous 0.0/empty."""
    run_dir = _long_run_dir(tmp_path)
    slha = run_dir / "SPheno.spc"
    slha.write_text(FIXTURE_FULL_SLHA.read_text())
    assert len(str(slha)) > 100

    result = driver.run_higgsbounds(str(_HB_BUILD), str(slha), 1, 0)

    assert result.channels, "vacuous empty channel list on long path"
    assert abs(result.obsratio_max - 0.6063) < 1e-3, result.obsratio_max
    assert result.most_sensitive_channel.id == 85
    assert result.most_sensitive_channel.hb_result == 1
