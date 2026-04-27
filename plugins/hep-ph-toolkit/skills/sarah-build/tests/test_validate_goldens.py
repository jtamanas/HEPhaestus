"""
test_validate_goldens.py — Unit + smoke tests for ``validate_goldens.py``.

Unit tests mock :func:`validate_goldens._run_wolframscript` with
captured-fixture-style CompletedProcess objects and assert the
error-pattern detection behaves as designed.

The smoke test is gated by ``@pytest.mark.wolfram`` and actually drives
wolframscript against the T05a majorana spike.  It is skipped when the
env var ``SARAH_PATH`` is unset or wolframscript is not on disk.

Acceptance-test coverage (T19 spec):
  - Forbidden patterns each individually trigger the right code.
  - Clean run returns ok=True.
  - Non-zero exit without forbidden pattern → WOLFRAMSCRIPT_NONZERO.
  - Missing goldens dir / missing main .m → FileNotFoundError.
  - Cleanup: Private-Models/<Name>/ is removed on exit (unless keep_staged).
  - outputs=[ufo] adds the MakeUFO[] dispatch and checks the output tree.
  - End-to-end smoke against majorana_spike (opt-in).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

# conftest.py sets up sys.path
import validate_goldens as vg  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPIKE_DIR = Path(__file__).resolve().parent / "spikes"
SARAH_PATH_DEFAULT = Path("/Users/yianni/SARAH/SARAH-4.15.3")
WOLFRAMSCRIPT_DEFAULT = Path("/usr/local/bin/wolframscript")


# ---------------------------------------------------------------------------
# Fixtures — in-tree "goldens" dirs created in tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_sarah_path(tmp_path):
    """Fake $sarah_path tree: SARAH.m sentinel + empty Private-Models/."""
    sp = tmp_path / "sarah"
    sp.mkdir()
    (sp / "SARAH.m").write_text("(* fake SARAH.m sentinel *)\n")
    (sp / "Private-Models").mkdir()
    (sp / "Output").mkdir()
    return sp


@pytest.fixture
def fake_wolframscript(tmp_path):
    """Path to a dummy wolframscript binary (content irrelevant; we monkeypatch)."""
    path = tmp_path / "wolframscript"
    path.write_text("#!/bin/sh\nexit 0\n")
    path.chmod(0o755)
    return path


@pytest.fixture
def singlet_doublet_goldens(tmp_path):
    """Minimal valid-shaped goldens tree for model 'singlet_doublet'.

    SARAH name is 'SingletDoublet'.  Content is a placeholder — we never
    actually feed this to SARAH because we're mocking _run_wolframscript.
    """
    gd = tmp_path / "goldens" / "singlet_doublet"
    gd.mkdir(parents=True)
    (gd / "SingletDoublet.m").write_text('Model`Name = "SingletDoublet";\n')
    (gd / "parameters.m").write_text("ParameterDefinitions = {};\n")
    (gd / "particles.m").write_text("ParticleDefinitions[GaugeES] = {};\n")
    (gd / "SPheno.m").write_text("(* stub *)\n")
    return gd


def _fake_completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["wolframscript", "-code", "..."],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# Unit tests — error-pattern detection
# ---------------------------------------------------------------------------

class TestForbiddenPatterns:
    """Each forbidden SARAH message → the right code, even if exit = 0."""

    def test_model_file_missing(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        stderr = (
            "Start::load: Loading model SingletDoublet\n"
            "ModelFile::MissingModel: Model SingletDoublet not found\n"
        )
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stderr=stderr, returncode=1))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "MODEL_FILE_MISSING"
        assert "ModelFile::MissingModel" in result.context["matched_line"]

    def test_model_file_aborted(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        stderr = "ModelFile::Aborted: Model loading aborted\n"
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stderr=stderr, returncode=1))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "MODEL_FILE_ABORTED"

    def test_checkmodel_abort(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        stderr = "CheckModel::AbortChecks: CheckModel[] aborted due to missing particle.\n"
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stderr=stderr, returncode=0))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        # IMPORTANT: returncode=0 but pattern still caught.
        assert result.ok is False
        assert result.code == "CHECKMODEL_ABORTED"

    def test_matter_sector_parse_error(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        stderr = "MatterSector::parseError: Unrecognised entry at position 3\n"
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stderr=stderr, returncode=1))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "MATTERSECTOR_PARSE"

    def test_first_match_wins_when_multiple_present(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """If multiple forbidden patterns appear, the first one in the log wins."""
        stderr = (
            "ModelFile::Aborted: Model loading aborted\n"
            "CheckModel::AbortChecks: also failed\n"
        )
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stderr=stderr, returncode=1))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "MODEL_FILE_ABORTED"

    def test_pattern_in_stdout_also_caught(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """Pattern in stdout (not stderr) is still detected."""
        stdout = "ModelFile::MissingModel oops\n"
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stdout=stdout, returncode=0))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "MODEL_FILE_MISSING"


# ---------------------------------------------------------------------------
# Unit tests — clean path
# ---------------------------------------------------------------------------

class TestCleanPath:
    def test_clean_run_no_outputs(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        stdout = "[validate_goldens] OK\n"
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(stdout=stdout, returncode=0))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is True
        assert result.code == "VALID"
        assert result.context["outputs_checked"] == []

    def test_nonzero_exit_without_forbidden_pattern(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """Non-zero exit + no forbidden pattern → WOLFRAMSCRIPT_NONZERO."""
        monkeypatch.setattr(vg, "_run_wolframscript",
                            lambda **kw: _fake_completed(stdout="some mystery\n", returncode=137))

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "WOLFRAMSCRIPT_NONZERO"
        assert result.context["returncode"] == 137

    def test_timeout_reported(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        def _raise_timeout(**kw):
            raise subprocess.TimeoutExpired(cmd=["wolframscript"], timeout=1.0)
        monkeypatch.setattr(vg, "_run_wolframscript", _raise_timeout)

        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
            timeout=1.0,
        )
        assert result.ok is False
        assert result.code == "WOLFRAMSCRIPT_TIMEOUT"


# ---------------------------------------------------------------------------
# Unit tests — outputs + output-tree checks
# ---------------------------------------------------------------------------

class TestOutputs:
    def test_ufo_missing_when_tree_not_produced(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """outputs=['ufo'] but $sarah_path/Output/SingletDoublet/ does not exist → UFO_MISSING."""
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            outputs=["ufo"],
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "UFO_MISSING"

    def test_ufo_present_detected(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """UFO tree present with particles.py → ok=True."""
        output_dir = fake_sarah_path / "Output" / "SingletDoublet" / "EWSB" / "UFO"
        output_dir.mkdir(parents=True)
        (output_dir / "particles.py").write_text("# fake UFO\n")
        (output_dir / "parameters.py").write_text("# fake UFO\n")

        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            outputs=["ufo"],
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is True, f"expected OK, got {result}"
        assert "ufo" in result.context["outputs_checked"]

    def test_spheno_missing_when_tree_not_produced(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            outputs=["spheno"],
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is False
        assert result.code == "SPHENO_MISSING"

    def test_spheno_present_detected(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        spheno_dir = fake_sarah_path / "Output" / "SingletDoublet" / "EWSB" / "SPheno"
        spheno_dir.mkdir(parents=True)
        (spheno_dir / "SPheno.m.f90").write_text("! fake f90\n")

        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            outputs=["spheno"],
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is True

    def test_multiple_outputs_both_checked(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        ufo_dir = fake_sarah_path / "Output" / "SingletDoublet" / "EWSB" / "UFO"
        ufo_dir.mkdir(parents=True)
        (ufo_dir / "particles.py").write_text("# fake\n")
        spheno_dir = fake_sarah_path / "Output" / "SingletDoublet" / "EWSB" / "SPheno"
        spheno_dir.mkdir(parents=True)
        (spheno_dir / "SPheno.m.f90").write_text("! fake\n")

        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            outputs=["ufo", "spheno"],
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is True
        assert set(result.context["outputs_checked"]) == {"ufo", "spheno"}

    def test_unknown_output_target_raises(self, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        with pytest.raises(ValueError, match="unknown output target"):
            vg.validate(
                model="singlet_doublet",
                goldens_dir=singlet_doublet_goldens,
                outputs=["madgraph"],
                sarah_path=fake_sarah_path,
                wolframscript=fake_wolframscript,
            )


# ---------------------------------------------------------------------------
# Unit tests — goldens-dir shape errors
# ---------------------------------------------------------------------------

class TestGoldensDirShape:
    def test_missing_goldens_dir_raises(self, fake_sarah_path, fake_wolframscript, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError):
            vg.validate(
                model="singlet_doublet",
                goldens_dir=missing,
                sarah_path=fake_sarah_path,
                wolframscript=fake_wolframscript,
            )

    def test_missing_main_m_raises(self, fake_sarah_path, fake_wolframscript, tmp_path):
        gd = tmp_path / "goldens"
        gd.mkdir()
        (gd / "parameters.m").write_text("ParameterDefinitions = {};\n")
        # Intentionally no SingletDoublet.m
        with pytest.raises(FileNotFoundError, match="expected main model file"):
            vg.validate(
                model="singlet_doublet",
                goldens_dir=gd,
                sarah_path=fake_sarah_path,
                wolframscript=fake_wolframscript,
            )

    def test_missing_sarah_path_raises(self, fake_wolframscript, tmp_path):
        gd = tmp_path / "goldens"
        gd.mkdir()
        (gd / "SingletDoublet.m").write_text("...\n")
        with pytest.raises(FileNotFoundError, match="sarah_path"):
            vg.validate(
                model="singlet_doublet",
                goldens_dir=gd,
                sarah_path=tmp_path / "no_sarah",
                wolframscript=fake_wolframscript,
            )

    def test_missing_wolframscript_raises(self, fake_sarah_path, tmp_path):
        gd = tmp_path / "goldens"
        gd.mkdir()
        (gd / "SingletDoublet.m").write_text("...\n")
        with pytest.raises(FileNotFoundError, match="wolframscript"):
            vg.validate(
                model="singlet_doublet",
                goldens_dir=gd,
                sarah_path=fake_sarah_path,
                wolframscript=tmp_path / "no_wolframscript",
            )


# ---------------------------------------------------------------------------
# Unit tests — staging + cleanup
# ---------------------------------------------------------------------------

class TestStagingLifecycle:
    def test_staging_populates_private_models(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        """During the run, Private-Models/SingletDoublet/SingletDoublet.m exists."""
        captured = {}

        def _capture_and_check(**kw):
            staged = fake_sarah_path / "Private-Models" / "SingletDoublet"
            captured["staged_exists_mid_run"] = (staged / "SingletDoublet.m").is_file()
            captured["staged_file_count"] = len(list(staged.iterdir()))
            return _fake_completed(returncode=0)

        monkeypatch.setattr(vg, "_run_wolframscript", _capture_and_check)
        result = vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        assert result.ok is True
        assert captured["staged_exists_mid_run"] is True
        # 4 .m files + .sarah_build_key
        assert captured["staged_file_count"] == 5

    def test_cleanup_default_removes_staged(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        staged = fake_sarah_path / "Private-Models" / "SingletDoublet"
        assert not staged.exists(), "staged dir should be cleaned up by default"

    def test_cleanup_runs_even_on_failure(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        monkeypatch.setattr(vg, "_run_wolframscript",
                            lambda **kw: _fake_completed(stderr="ModelFile::Aborted\n", returncode=1))
        vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
        )
        staged = fake_sarah_path / "Private-Models" / "SingletDoublet"
        assert not staged.exists(), "staged dir should be cleaned up even after failure"

    def test_keep_staged_preserves_tree(self, monkeypatch, fake_sarah_path, fake_wolframscript, singlet_doublet_goldens):
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        vg.validate(
            model="singlet_doublet",
            goldens_dir=singlet_doublet_goldens,
            sarah_path=fake_sarah_path,
            wolframscript=fake_wolframscript,
            keep_staged=True,
        )
        staged = fake_sarah_path / "Private-Models" / "SingletDoublet"
        assert staged.is_dir()
        assert (staged / "SingletDoublet.m").is_file()


# ---------------------------------------------------------------------------
# Unit tests — wolframscript -code payload
# ---------------------------------------------------------------------------

class TestWolframscriptPayload:
    def test_code_includes_start_and_check(self, fake_sarah_path):
        code = vg._build_code(fake_sarah_path, "SingletDoublet", [])
        assert 'Start["SingletDoublet"]' in code
        assert "CheckModel[]" in code
        assert "MakeUFO[]" not in code
        assert "MakeSPheno[]" not in code

    def test_code_includes_makeufo(self, fake_sarah_path):
        code = vg._build_code(fake_sarah_path, "SingletDoublet", ["ufo"])
        assert "MakeUFO[]" in code
        assert "MakeSPheno[]" not in code

    def test_code_includes_makespheno(self, fake_sarah_path):
        code = vg._build_code(fake_sarah_path, "SingletDoublet", ["spheno"])
        assert "MakeSPheno[]" in code
        assert "MakeUFO[]" not in code

    def test_code_uses_appendto_path(self, fake_sarah_path):
        code = vg._build_code(fake_sarah_path, "SingletDoublet", [])
        assert f'AppendTo[$Path, "{fake_sarah_path}"]' in code
        assert 'Needs["SARAH`"]' in code


# ---------------------------------------------------------------------------
# Unit tests — CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def test_cli_success_exits_zero(self, monkeypatch, fake_sarah_path, fake_wolframscript,
                                     singlet_doublet_goldens, capsys):
        monkeypatch.setattr(vg, "_run_wolframscript", lambda **kw: _fake_completed(returncode=0))
        rc = vg.main([
            "--model", "singlet_doublet",
            "--goldens-dir", str(singlet_doublet_goldens),
            "--sarah-path", str(fake_sarah_path),
            "--wolframscript", str(fake_wolframscript),
        ])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert rc == 0
        assert payload["status"] == "valid"

    def test_cli_failure_exits_one(self, monkeypatch, fake_sarah_path, fake_wolframscript,
                                    singlet_doublet_goldens, capsys):
        monkeypatch.setattr(vg, "_run_wolframscript",
                            lambda **kw: _fake_completed(stderr="ModelFile::Aborted\n", returncode=1))
        rc = vg.main([
            "--model", "singlet_doublet",
            "--goldens-dir", str(singlet_doublet_goldens),
            "--sarah-path", str(fake_sarah_path),
            "--wolframscript", str(fake_wolframscript),
        ])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert rc == 1
        assert payload["status"] == "invalid"
        assert payload["code"] == "MODEL_FILE_ABORTED"

    def test_cli_env_missing_exits_two(self, tmp_path, capsys):
        gd = tmp_path / "goldens"
        gd.mkdir()
        (gd / "SingletDoublet.m").write_text("x\n")
        rc = vg.main([
            "--model", "singlet_doublet",
            "--goldens-dir", str(gd),
            "--sarah-path", str(tmp_path / "nonexistent_sarah"),
            "--wolframscript", str(tmp_path / "nonexistent_ws"),
        ])
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert rc == 2
        assert payload["code"] == "ENVIRONMENT_MISSING"

    def test_cli_parses_outputs_csv(self, monkeypatch, fake_sarah_path, fake_wolframscript,
                                     singlet_doublet_goldens, capsys):
        """--outputs ufo,spheno gets split and both are checked."""
        # make UFO + SPheno present
        for sub, fname in (("UFO", "particles.py"), ("SPheno", "SPheno.m.f90")):
            d = fake_sarah_path / "Output" / "SingletDoublet" / "EWSB" / sub
            d.mkdir(parents=True)
            (d / fname).write_text("# fake\n")

        captured_outputs = {}

        def _capture(**kw):
            captured_outputs["outputs"] = kw["outputs"]
            return _fake_completed(returncode=0)

        monkeypatch.setattr(vg, "_run_wolframscript", _capture)
        rc = vg.main([
            "--model", "singlet_doublet",
            "--goldens-dir", str(singlet_doublet_goldens),
            "--sarah-path", str(fake_sarah_path),
            "--wolframscript", str(fake_wolframscript),
            "--outputs", "ufo,spheno",
        ])
        assert rc == 0
        assert captured_outputs["outputs"] == ["ufo", "spheno"]


# ---------------------------------------------------------------------------
# End-to-end smoke against real wolframscript + majorana spike
# ---------------------------------------------------------------------------

def _wolfram_env_available() -> bool:
    """True iff both SARAH_PATH exists on disk and wolframscript is on PATH."""
    return SARAH_PATH_DEFAULT.is_dir() and WOLFRAMSCRIPT_DEFAULT.exists()


@pytest.fixture
def majorana_spike_goldens_dir(tmp_path):
    """Copy the T05a majorana spike into a <SarahName>.m-shaped dir.

    The spike stages as 'Spike' (Model`Name = "Spike").  To reuse the
    validate_goldens interface, we create a tmp dir 'goldens/spike/' with:
        Spike.m         (renamed from majorana_spike.m)
        particles.m
        parameters.m
    """
    gd = tmp_path / "goldens" / "spike"
    gd.mkdir(parents=True)
    # modelspec_name_to_sarah("spike") → "Spike" (singleton, len=5 > 2 → "Spike")
    # (actually: prefix "spike" has len=5; _title_part returns "Spike").
    src_spike = SPIKE_DIR / "majorana_spike.m"
    src_particles = SPIKE_DIR / "particles.m"
    src_parameters = SPIKE_DIR / "parameters.m"
    (gd / "Spike.m").write_text(src_spike.read_text(encoding="utf-8"), encoding="utf-8")
    (gd / "particles.m").write_text(src_particles.read_text(encoding="utf-8"), encoding="utf-8")
    (gd / "parameters.m").write_text(src_parameters.read_text(encoding="utf-8"), encoding="utf-8")
    return gd


@pytest.mark.wolfram
@pytest.mark.skipif(not _wolfram_env_available(),
                    reason="SARAH or wolframscript not present on this host")
def test_smoke_majorana_spike_validates(majorana_spike_goldens_dir):
    """End-to-end smoke: run real wolframscript against the T05a spike.

    Sanity: the spike is known to load cleanly per T05a.  If this test
    fails, either T19's plumbing is broken or SARAH has regressed.

    We do NOT request MakeUFO[] here — the smoke is about the load +
    CheckModel oracle.  MakeUFO[] for the spike is T20's concern.
    """
    result = vg.validate(
        model="spike",
        goldens_dir=majorana_spike_goldens_dir,
        outputs=[],
        sarah_path=SARAH_PATH_DEFAULT,
        wolframscript=WOLFRAMSCRIPT_DEFAULT,
        timeout=300,  # 5 min safety net; spike loads in ~30s
    )
    # Print the context on failure to make debugging easier — fixture
    # cleanup will have already removed the staged tree.
    assert result.ok is True, (
        f"majorana spike validation failed: code={result.code} "
        f"message={result.message!r} context={result.context}"
    )
