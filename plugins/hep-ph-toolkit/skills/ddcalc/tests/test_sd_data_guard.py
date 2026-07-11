"""
Tests for the dead-SD-channel runtime guard (ddcalc-sd-channel follow-up).

DDCalc loads its spin-dependent form factors from DATA_DIR/SDFF/<Z>_<A>.dat,
where DATA_DIR is baked at compile time; when the open fails DDCalc silently
zeroes the SD form factor (DDNuclear.f90:542-544), producing a *finite* lnL
equal to background — invisible to the driver's non-finite guards. These
tests pin the loud guard: _verify_sd_data_dirs must report the failure, heal
must repair broken symlinks, and cmd_run must exit 1 with a
DDCALC_DRIVER_FAILED blocker instead of emitting silently SD-blind verdicts.

All tests here are hermetic (fake install tree + fake libDDCalc.a with a
baked path string); no real DDCalc install, compiler, or gating required.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_ddcalc import (  # noqa: E402
    _ensure_ddcalc_data_symlinks,
    _find_compile_data_dir,
    _verify_sd_data_dirs,
)


@pytest.fixture()
def fake_install(tmp_path):
    """
    A minimal fake DDCalc install:
      <install>/lib/libDDCalc.a   — contains the baked DATA_DIR string
      <install>/SDFF/9_19.dat     — fake SD form-factor table
      <install>/Wbar/9_19.dat     — fake Wbar table
      <install>/FAKE_EXP/energies.dat — one fake experiment dir
    plus the (initially nonexistent) baked DATA_DIR at <tmp>/bake/src/data.
    """
    install = tmp_path / "ddcalc"
    baked = tmp_path / "bake" / "src" / "data"
    (install / "lib").mkdir(parents=True)
    # strings(1) finds printable runs; surround with NULs like a real archive.
    (install / "lib" / "libDDCalc.a").write_bytes(
        b"\x00garbage\x00" + str(baked).encode() + b"/\x00more\x00"
    )
    for sub in ("SDFF", "Wbar"):
        (install / sub).mkdir()
        (install / sub / "9_19.dat").write_text("0 0 0 0 0\n")
    (install / "FAKE_EXP").mkdir()
    (install / "FAKE_EXP" / "energies.dat").write_text("1.0\n")
    return install, baked


def test_find_compile_data_dir(fake_install):
    install, baked = fake_install
    assert _find_compile_data_dir(str(install)) == baked


def test_heal_creates_sd_links_and_verify_passes(fake_install):
    install, baked = fake_install
    _ensure_ddcalc_data_symlinks(str(install))
    for name in ("SDFF", "Wbar", "FAKE_EXP"):
        link = baked / name
        assert link.is_symlink() and link.exists(), f"{name} not healed"
    assert _verify_sd_data_dirs(str(install)) is None


def test_verify_fails_loudly_when_sdff_unresolvable(fake_install):
    """Broken SDFF symlink (no heal) => verify returns an error naming SDFF."""
    install, baked = fake_install
    baked.mkdir(parents=True)
    (baked / "SDFF").symlink_to(install / "nonexistent")
    err = _verify_sd_data_dirs(str(install))
    assert err is not None and "SDFF" in err
    assert "zero" in err.lower()  # names the silent-zero failure mode


def test_verify_fails_when_install_lacks_sdff(fake_install):
    """Install tree without SDFF/ => heal cannot create it => loud error."""
    install, baked = fake_install
    import shutil
    shutil.rmtree(install / "SDFF")
    _ensure_ddcalc_data_symlinks(str(install))
    err = _verify_sd_data_dirs(str(install))
    assert err is not None and "SDFF" in err


def test_heal_replaces_broken_symlink(fake_install):
    """A stale/broken symlink (install moved) must be re-pointed, not skipped."""
    install, baked = fake_install
    baked.mkdir(parents=True)
    (baked / "SDFF").symlink_to(install / "gone-away")
    assert not (baked / "SDFF").exists()  # broken
    _ensure_ddcalc_data_symlinks(str(install))
    assert (baked / "SDFF").exists(), "broken SDFF symlink was not repaired"
    assert _verify_sd_data_dirs(str(install)) is None


def test_cmd_run_errors_loudly_not_silent_verdicts(fake_install, tmp_path):
    """
    End-to-end guard: with an install whose SDFF/ is missing, run_ddcalc.py
    must exit 1 with a DDCALC_DRIVER_FAILED blocker — never proceed to emit
    verdicts that would be silently SD-blind.
    """
    install, baked = fake_install
    import shutil
    shutil.rmtree(install / "SDFF")

    # Fake config so _config_get finds our fake install.
    config_dir = tmp_path / "xdg" / "hephaestus"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(
        json.dumps({"ddcalc_path": str(install)})
    )

    sigma = {
        "schema_version": "scattering/v1",
        "m_dm_gev": 100.0,
        "sigma_si_proton_cm2": 0.0,
        "sigma_si_neutron_cm2": 0.0,
        "sigma_sd_proton_cm2": 1e-40,
        "sigma_sd_neutron_cm2": 0.0,
        "source": "micromegas",
        "source_run": "guard-test",
        "halo": None,
        "nucleon_form_factors": {"preset": "default_2018"},
    }
    sigma_path = tmp_path / "sigma.json"
    sigma_path.write_text(json.dumps(sigma))

    env = dict(**__import__("os").environ)
    env["XDG_CONFIG_HOME"] = str(tmp_path / "xdg")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "run_ddcalc.py"), "run",
         "--sigma-json", str(sigma_path)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert result.returncode == 1, (
        f"expected loud failure, got rc={result.returncode}\n"
        f"stdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"
    )
    blocker = json.loads(result.stderr.strip().splitlines()[-1])
    assert blocker["code"] == "DDCALC_DRIVER_FAILED"
    assert "SDFF" in blocker["message"]
    # And crucially: no verdict was emitted.
    assert "verdict" not in result.stdout
