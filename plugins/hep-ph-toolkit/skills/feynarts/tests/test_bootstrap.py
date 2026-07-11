"""Tests for the --sarah-model bootstrap path in run_feynarts.py.

These are hermetic (no Wolfram): the actual SARAH MakeFeynArts[] call is
monkeypatched.  They cover the two things that were broken:

  1. Ordering — bootstrap (MakeFeynArts[] + register) is attempted *before*
     resolve_model can raise FEYNARTS_SARAH_STATE_MISSING; the blocker only
     fires when bootstrap genuinely cannot proceed, and its message says what
     was attempted.
  2. Name mapping — Start[] / SARAH's Output tree use the SARAH model name
     (SingletDoublet), not the toolkit slug (singlet_doublet), via the shared
     modelspec_name_to_sarah source of truth.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import run_feynarts
from render_driver import render_make_feynarts_driver
from resolve_model import resolve_model


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _fake_sarah_output(sarah_path: Path, sarah_name: str) -> Path:
    """Create a fake SARAH MakeFeynArts[] output tree and return its .mod."""
    fa_out = sarah_path / "Output" / sarah_name / "EWSB" / "FeynArts"
    fa_out.mkdir(parents=True, exist_ok=True)
    mod = fa_out / f"{sarah_name}EWSB.mod"
    mod.write_text("(* fake SARAH FeynArts mod *)\n")
    (fa_out / "ParticleNamesFeynArts.dat").write_text("F[1]: chi\n")
    (fa_out / f"Substitutions-{sarah_name}EWSB.m").write_text("(* subs *)\n")
    return mod


def _capture_blocker(monkeypatch):
    """Capture the JSON payload passed to _blocker instead of exiting."""
    captured = {}

    def fake_blocker(code, message, context=None, exit_code=1):
        captured["code"] = code
        captured["message"] = message
        captured["context"] = context or {}
        raise SystemExit(exit_code)

    monkeypatch.setattr(run_feynarts, "_blocker", fake_blocker)
    return captured


# --------------------------------------------------------------------------
# Name mapping
# --------------------------------------------------------------------------
class TestNameMapping:
    def test_make_feynarts_driver_uses_sarah_name(self):
        """The MakeFeynArts driver must Start[] the SARAH name, not the slug."""
        script = render_make_feynarts_driver(
            feynarts_state_dir="/tmp/state",
            sarah_path="/opt/SARAH",
            model_name="SingletDoublet",
        )
        assert 'Start["SingletDoublet"]' in script
        assert 'Start["singlet_doublet"]' not in script

    def test_bootstrap_calls_make_with_sarah_name(self, tmp_path, monkeypatch):
        """_bootstrap_sarah_state maps slug -> SARAH name for MakeFeynArts[]."""
        state_root = tmp_path / "state"
        sarah_path = tmp_path / "SARAH"
        sarah_path.mkdir()

        seen = {}

        def fake_make(sarah_name, sarah_path, feynarts_state_dir, ws_path, timeout_s):
            seen["sarah_name"] = sarah_name
            _fake_sarah_output(Path(sarah_path), sarah_name)

        monkeypatch.setattr(run_feynarts, "_run_make_feynarts", fake_make)

        run_feynarts._bootstrap_sarah_state(
            slug="singlet_doublet",
            state_root=str(state_root),
            sarah_path=str(sarah_path),
            ws_path="/usr/bin/wolframscript",
            timeout_s=60,
        )
        assert seen["sarah_name"] == "SingletDoublet"


# --------------------------------------------------------------------------
# Ordering: bootstrap attempted before blocker
# --------------------------------------------------------------------------
class TestBootstrapOrdering:
    def test_bootstrap_registers_then_resolves(self, tmp_path, monkeypatch):
        """A first-ever SARAH model self-bootstraps: make -> register -> resolvable.

        This is the core regression: previously resolve_model raised
        FEYNARTS_SARAH_STATE_MISSING before MakeFeynArts[] could create the
        state.  Here MakeFeynArts[] is faked to write SARAH's Output tree; the
        real register step must copy it into feynarts_state/<slug>.mod so a
        subsequent resolve_model succeeds.
        """
        state_root = tmp_path / "state"
        sarah_path = tmp_path / "SARAH"
        sarah_path.mkdir()

        def fake_make(sarah_name, sarah_path, feynarts_state_dir, ws_path, timeout_s):
            _fake_sarah_output(Path(sarah_path), sarah_name)

        monkeypatch.setattr(run_feynarts, "_run_make_feynarts", fake_make)

        run_feynarts._bootstrap_sarah_state(
            slug="singlet_doublet",
            state_root=str(state_root),
            sarah_path=str(sarah_path),
            ws_path="/usr/bin/wolframscript",
            timeout_s=60,
        )

        mod = state_root / "models" / "singlet_doublet" / "feynarts_state" / "singlet_doublet.mod"
        assert mod.exists(), "bootstrap did not register <slug>.mod"

        # resolve_model now succeeds without raising
        info = resolve_model(sarah_model="singlet_doublet", state_root=str(state_root))
        assert info["source"] == "sarah"
        assert info["mod_path"].endswith("singlet_doublet.mod")

        # aux files carried over
        fs = state_root / "models" / "singlet_doublet" / "feynarts_state"
        assert (fs / "ParticleNamesFeynArts.dat").exists()
        assert (fs / "PROVENANCE.txt").exists()

    def test_bootstrap_noop_when_state_exists(self, tmp_path, monkeypatch):
        """Idempotent: existing state means MakeFeynArts[] is NOT re-run.

        Protects the registered production state and the --model-file path.
        """
        state_root = tmp_path / "state"
        fs = state_root / "models" / "singlet_doublet" / "feynarts_state"
        fs.mkdir(parents=True)
        (fs / "singlet_doublet.mod").write_text("(* existing *)\n")

        def boom(*a, **k):
            raise AssertionError("MakeFeynArts[] must not run when state exists")

        monkeypatch.setattr(run_feynarts, "_run_make_feynarts", boom)

        # Must not raise / must not call make
        run_feynarts._bootstrap_sarah_state(
            slug="singlet_doublet",
            state_root=str(state_root),
            sarah_path=str(tmp_path / "SARAH"),
            ws_path="/usr/bin/wolframscript",
            timeout_s=60,
        )


# --------------------------------------------------------------------------
# Blocker: only after bootstrap genuinely cannot proceed
# --------------------------------------------------------------------------
class TestBootstrapBlocker:
    def test_blocker_when_sarah_unconfigured(self, tmp_path, monkeypatch):
        """No state + no sarah_path -> blocker that names the attempt."""
        captured = _capture_blocker(monkeypatch)
        with pytest.raises(SystemExit):
            run_feynarts._bootstrap_sarah_state(
                slug="singlet_doublet",
                state_root=str(tmp_path / "state"),
                sarah_path="",  # SARAH not configured
                ws_path="/usr/bin/wolframscript",
                timeout_s=60,
            )
        assert captured["code"] == "FEYNARTS_SARAH_STATE_MISSING"
        assert "MakeFeynArts" in captured["message"]
        assert captured["context"]["sarah_name"] == "SingletDoublet"

    def test_blocker_when_make_produces_no_mod(self, tmp_path, monkeypatch):
        """MakeFeynArts[] runs but emits no .mod -> blocker saying so."""
        captured = _capture_blocker(monkeypatch)
        sarah_path = tmp_path / "SARAH"
        sarah_path.mkdir()

        def fake_make(sarah_name, sarah_path, feynarts_state_dir, ws_path, timeout_s):
            # runs but writes nothing under Output/
            pass

        monkeypatch.setattr(run_feynarts, "_run_make_feynarts", fake_make)

        with pytest.raises(SystemExit):
            run_feynarts._bootstrap_sarah_state(
                slug="singlet_doublet",
                state_root=str(tmp_path / "state"),
                sarah_path=str(sarah_path),
                ws_path="/usr/bin/wolframscript",
                timeout_s=60,
            )
        assert captured["code"] == "FEYNARTS_SARAH_STATE_MISSING"
        assert "no" in captured["message"].lower() and ".mod" in captured["message"]

    def test_blocker_when_slug_invalid(self, tmp_path, monkeypatch):
        """Invalid slug (not modelspec snake_case) -> blocker, not ValueError."""
        captured = _capture_blocker(monkeypatch)
        with pytest.raises(SystemExit):
            run_feynarts._bootstrap_sarah_state(
                slug="Foo_Bar",  # uppercase — violates MODEL_NAME_REGEX
                state_root=str(tmp_path / "state"),
                sarah_path=str(tmp_path),
                ws_path="/usr/bin/wolframscript",
                timeout_s=60,
            )
        assert captured["code"] == "FEYNARTS_SARAH_STATE_MISSING"
        assert "Foo_Bar" in captured["message"]
        assert captured["context"]["model_name"] == "Foo_Bar"


# --------------------------------------------------------------------------
# CLI contract: invalid slug must emit a blocker JSON, never a traceback
# --------------------------------------------------------------------------
class TestCliInvalidSlug:
    def test_cli_emits_blocker_json_for_invalid_slug(self, tmp_path, fake_feynarts_dir):
        """generate.py --sarah-model <invalid> exits 1 with structured JSON on stderr.

        Pinned regression for the agent-CLI contract: an invalid slug used to
        escape as an uncaught ValueError traceback from modelspec_name_to_sarah.
        Hermetic: FeynArts dir is fake, wolfram path is any existing file —
        the blocker fires before any Wolfram invocation.
        """
        generate_py = Path(__file__).parent.parent / "scripts" / "generate.py"
        proc = subprocess.run(
            [
                sys.executable, str(generate_py), "generate",
                "--process", "e+ e- -> mu+ mu-",
                "--sarah-model", "Foo_Bar",
                "--state-root", str(tmp_path / "scratch_state"),
                "--feynarts-path", str(fake_feynarts_dir),
                "--wolfram-path", sys.executable,  # exists; never invoked
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert proc.returncode == 1
        assert "Traceback" not in proc.stderr, f"traceback leaked:\n{proc.stderr}"
        blocker = json.loads(proc.stderr.strip().splitlines()[-1])
        assert blocker["code"] == "FEYNARTS_SARAH_STATE_MISSING"
        assert blocker["mode"] == "fatal"
        assert "Foo_Bar" in blocker["message"]
        assert blocker["context"]["model_name"] == "Foo_Bar"
