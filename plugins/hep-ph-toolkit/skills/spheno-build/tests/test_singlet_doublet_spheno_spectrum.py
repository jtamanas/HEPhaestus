"""test_singlet_doublet_spheno_spectrum.py — gated live-SPheno regression.

Pins the layer-2 fix (leshouches_template honours les_houches indices) and the
A2 flag split (SPhenoInput 11/16 ON, 13/57 OFF) against the ACTUAL compiled
SPheno binary. The historical bug produced a silent SM-only spectrum with
FChi1 = -0.0; the fix must yield the physical spectrum

    FChi1/2/3 = 132.69 / 523.03 / 540.33 GeV,  FChiM = 500 GeV,  zero NaN

and emit the HiggsCoupling blocks HiggsTools consumes.

GATING (repo convention: skipif on the resource): this test is skipped unless
the compiled SPheno binary + SARAH output for singlet_doublet exist under the
real state root (``~/.local/share/hephaestus`` or ``$HEPPH_STATE_ROOT``). It
NEVER writes to the real state root — it builds a hermetic temp state root that
symlinks the read-only artifacts (binary, sarah_output) and copies spec.yaml,
so all run output lands under tmp_path.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"
_RUN_SPHENO = _SCRIPTS / "run_spheno.py"

_REAL_STATE = Path(
    os.environ.get("HEPPH_STATE_ROOT")
    or (Path.home() / ".local" / "share" / "hephaestus")
)
_MODEL = "singlet_doublet"
_SARAH_NAME = "SingletDoublet"
_SRC_MODEL_DIR = _REAL_STATE / "models" / _MODEL
_BIN = _SRC_MODEL_DIR / "spheno_bin" / f"SPheno{_SARAH_NAME}"

_binary_available = _BIN.exists() and (_SRC_MODEL_DIR / "sarah_output").exists()

pytestmark = pytest.mark.skipif(
    not _binary_available,
    reason=(
        f"compiled SPheno binary not found at {_BIN}; "
        "run /install spheno + /sarah-build singlet_doublet to enable this "
        "live-binary regression"
    ),
)


def _hermetic_state(tmp_path: Path) -> Path:
    """Build a temp state root that reuses the real binary/output read-only."""
    state = tmp_path / "state"
    model_dir = state / "models" / _MODEL
    model_dir.mkdir(parents=True)
    # Symlink read-only artifacts; runs/ is created fresh under tmp_path.
    for name in ("spheno_bin", "sarah_output", "sarah", _SARAH_NAME):
        src = _SRC_MODEL_DIR / name
        if src.exists() or src.is_symlink():
            (model_dir / name).symlink_to(src)
    # Copy the spec so a stale/edited real spec cannot leak in.
    (model_dir / "spec.yaml").write_bytes((_SRC_MODEL_DIR / "spec.yaml").read_bytes())
    return state


def _load_adapter():
    p = (
        _HERE.parent.parent
        / "higgstools" / "scripts" / "slha_adapter.py"
    )
    s = importlib.util.spec_from_file_location("slha_adapter", p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def spheno_run(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("sd_spheno")
    state = _hermetic_state(tmp_path)
    env = dict(os.environ)
    env["HEPPH_STATE_ROOT"] = str(state)
    env["XDG_CONFIG_HOME"] = str(tmp_path / "cfg")
    (tmp_path / "cfg").mkdir(exist_ok=True)

    proc = subprocess.run(
        [
            sys.executable, str(_RUN_SPHENO), _MODEL,
            "--backend", "spheno",
            "--params", "MS=150,MPsi=500,yh1=1",
            "--skip-compile",
        ],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, (
        f"run_spheno failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    # The run-stage JSON is the last stdout line.
    run_json = None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("{") and '"stage": "run"' in line:
            run_json = json.loads(line)
    assert run_json is not None, f"no run-stage JSON in stdout:\n{proc.stdout}"
    return run_json


def test_backend_is_real_spheno(spheno_run):
    assert spheno_run["backend"] == "spheno"
    assert spheno_run["status"] == "ok"
    spinfo = spheno_run["summary"]["spinfo"]
    assert spinfo["1"] == "SPhenoSARAH", spinfo


def test_chi_spectrum_physical_not_zero(spheno_run):
    """FChi1 must be 132.69, NOT -0.0 (the silent-misplacement symptom)."""
    masses = spheno_run["summary"]["masses"]
    # PDG ids emitted by this SARAH build.
    fchi1 = masses["9958431"]
    fchi2 = masses["9956206"]
    fchi3 = masses["9979223"]
    fchim = masses["9984071"]
    assert abs(fchi1 - 132.69) < 0.1, f"FChi1={fchi1} (expected ~132.69)"
    assert abs(fchi2 - 523.03) < 0.1, f"FChi2={fchi2}"
    assert abs(fchi3 - 540.33) < 0.1, f"FChi3={fchi3}"
    assert abs(fchim - 500.0) < 1e-6, f"FChiM={fchim}"


def test_no_nan_problems(spheno_run):
    assert spheno_run["summary"]["problems"] == []


def test_coupling_blocks_parse_for_higgstools(spheno_run):
    """The generated SLHA must feed the HiggsTools adapter (A3 chain)."""
    slha = Path(spheno_run["slha_path"]).read_text()
    assert "HiggsCouplingsBosons" in slha
    assert "HiggsCouplingsFermions" in slha
    adapter = _load_adapter()
    res = adapter.parse_slha(slha)  # must NOT raise SlhaMissingBlocksError
    bc = res["boson_couplings"][25]
    assert abs(bc["ww"] - 1.0) < 1e-6
    assert abs(bc["aa"] - 1.043) < 0.01, bc["aa"]
    assert abs(bc["gg"] - 1.022) < 0.01, bc["gg"]
