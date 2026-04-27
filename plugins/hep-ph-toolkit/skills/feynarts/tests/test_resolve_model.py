"""Tests for resolve_model.py."""
from pathlib import Path

import pytest

from resolve_model import (
    ModelResolutionError,
    resolve_model,
)


class TestBuiltinModel:
    """--model <builtin> path."""

    def test_sm_builtin(self, fake_feynarts_dir):
        result = resolve_model(model="SM", feynarts_path=str(fake_feynarts_dir))
        assert result["source"] == "builtin"
        assert result["model_name"] == "SM"
        assert "SM.mod" in result["mod_path"] or result["mod_path"].endswith("SM.mod")

    def test_unknown_builtin_raises(self, fake_feynarts_dir):
        with pytest.raises(ModelResolutionError, match="FEYNARTS_ABSENT"):
            resolve_model(model="UnknownModel99", feynarts_path=str(fake_feynarts_dir))


class TestModelFile:
    """--model-file <path> path."""

    def test_model_file_valid(self, tmp_model_dir):
        result = resolve_model(model_file=str(tmp_model_dir), model_name="TestModel")
        assert result["source"] == "file"
        assert result["mod_path"].endswith("TestModel.mod")

    def test_model_file_invalid_raises(self, tmp_path):
        with pytest.raises(ModelResolutionError, match="FEYNARTS_MODEL_FILE_INVALID"):
            resolve_model(model_file=str(tmp_path / "nonexistent"), model_name="Bad")


class TestSarahModel:
    """--sarah-model <name> path."""

    def test_sarah_state_missing_raises(self, tmp_state_root):
        # DarkSU3 exists but has no .mod file yet
        with pytest.raises(ModelResolutionError, match="FEYNARTS_SARAH_STATE_MISSING"):
            resolve_model(
                sarah_model="NonExistentModel",
                state_root=str(tmp_state_root),
            )

    def test_sarah_state_with_mod(self, tmp_state_root):
        # Seed a .mod/.gen pair
        state_dir = tmp_state_root / "models" / "DarkSU3" / "feynarts_state"
        (state_dir / "DarkSU3.mod").write_text("(* mod *)\n")
        (state_dir / "DarkSU3.gen").write_text("(* gen *)\n")
        result = resolve_model(
            sarah_model="DarkSU3",
            state_root=str(tmp_state_root),
        )
        assert result["source"] == "sarah"
        assert result["model_name"] == "DarkSU3"


class TestConflict:
    """Model source conflict detection."""

    def test_two_sources_conflict(self, fake_feynarts_dir, tmp_model_dir):
        with pytest.raises(ModelResolutionError, match="FEYNARTS_MODEL_SOURCE_CONFLICT"):
            resolve_model(
                model="SM",
                model_file=str(tmp_model_dir),
                feynarts_path=str(fake_feynarts_dir),
            )

    def test_no_source_raises(self):
        with pytest.raises(ModelResolutionError, match="FEYNARTS_ABSENT"):
            resolve_model()
