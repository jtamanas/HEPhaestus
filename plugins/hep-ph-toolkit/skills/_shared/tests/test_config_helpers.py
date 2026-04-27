"""
test_config_helpers.py — unit tests for config_helpers.py.

Tests per plan W0 item 17:
    - merge into empty config
    - preserve unrelated keys
    - register_model regex enforcement
    - round-trip (write then read back)
    - fsync discipline: no orphaned .tmp file after simulated crash
"""
import json
import os
import sys
from pathlib import Path

import pytest

# config_helpers is on sys.path via conftest.py
import config_helpers


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory and reload roots."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(tmp_path / "state"))
    config_helpers._reload_roots()
    yield
    config_helpers._reload_roots()  # clean up after test


# ---------------------------------------------------------------------------
# Basic merge tests
# ---------------------------------------------------------------------------

def test_merge_into_empty(tmp_path):
    """Merging into an absent config creates a valid JSON file."""
    config_helpers.merge_config(sarah_path="/fake/sarah")
    data = config_helpers.load_config()
    assert data["sarah_path"] == "/fake/sarah"
    assert "last_configured" in data


def test_preserve_unrelated_keys(tmp_path):
    """Merging new keys does not clobber existing keys."""
    config_helpers.merge_config(wolfram_engine_path="/fake/wolfram")
    config_helpers.merge_config(sarah_path="/fake/sarah")
    data = config_helpers.load_config()
    assert data["wolfram_engine_path"] == "/fake/wolfram"
    assert data["sarah_path"] == "/fake/sarah"


def test_overwrite_existing_key(tmp_path):
    """Merging an existing key updates it."""
    config_helpers.merge_config(sarah_path="/old/path")
    config_helpers.merge_config(sarah_path="/new/path")
    data = config_helpers.load_config()
    assert data["sarah_path"] == "/new/path"


def test_round_trip(tmp_path):
    """Write and read back produce identical data."""
    config_helpers.merge_config(spheno_path="/fake/spheno", mg5_path="/fake/mg5")
    data = config_helpers.load_config()
    assert data["spheno_path"] == "/fake/spheno"
    assert data["mg5_path"] == "/fake/mg5"


def test_load_config_absent_returns_empty(tmp_path):
    """load_config returns {} when the config file does not exist."""
    assert config_helpers.load_config() == {}


def test_last_configured_utc_format(tmp_path):
    """last_configured must be UTC ISO 8601 with Z suffix."""
    import re
    config_helpers.merge_config(test_key="test_val")
    data = config_helpers.load_config()
    ts = data["last_configured"]
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts), ts


# ---------------------------------------------------------------------------
# register_model tests
# ---------------------------------------------------------------------------

def test_register_model_valid(tmp_path):
    """register_model creates models[name] sub-dict."""
    config_helpers.register_model("dark_su3", ufo_path="/fake/ufo")
    data = config_helpers.load_config()
    assert "models" in data
    assert "dark_su3" in data["models"]
    assert data["models"]["dark_su3"]["ufo_path"] == "/fake/ufo"


def test_register_model_upsert(tmp_path):
    """register_model upserts — does not clobber existing model fields."""
    config_helpers.register_model("dark_su3", ufo_path="/fake/ufo")
    config_helpers.register_model("dark_su3", slha_path="/fake/slha")
    data = config_helpers.load_config()
    model = data["models"]["dark_su3"]
    assert model["ufo_path"] == "/fake/ufo"
    assert model["slha_path"] == "/fake/slha"


def test_register_model_regex_leading_digit():
    """register_model raises ValueError for names starting with a digit."""
    with pytest.raises(ValueError, match="invalid model name"):
        config_helpers.register_model("2hdm")


def test_register_model_regex_uppercase():
    """register_model raises ValueError for uppercase names."""
    with pytest.raises(ValueError, match="invalid model name"):
        config_helpers.register_model("DarkSU3")


def test_register_model_regex_too_short():
    """register_model raises ValueError for single-char name."""
    with pytest.raises(ValueError, match="invalid model name"):
        config_helpers.register_model("a")


def test_register_model_regex_valid_short():
    """A 2-char name is the minimum valid."""
    config_helpers.register_model("ab")
    data = config_helpers.load_config()
    assert "ab" in data["models"]


def test_get_model_present(tmp_path):
    """get_model returns the model sub-dict when present."""
    config_helpers.register_model("dark_su3", ufo_path="/fake/ufo")
    model = config_helpers.get_model("dark_su3")
    assert model is not None
    assert model["ufo_path"] == "/fake/ufo"


def test_get_model_absent(tmp_path):
    """get_model returns None for an unknown model."""
    assert config_helpers.get_model("no_such_model") is None


# ---------------------------------------------------------------------------
# Atomic write / fsync discipline
# ---------------------------------------------------------------------------

def test_no_orphaned_tmp_after_normal_write(tmp_path):
    """After a normal merge_config, no .tmp file should remain."""
    config_helpers.merge_config(test_key="value")
    cfg_dir = config_helpers.CONFIG_DIR
    tmp_files = list(cfg_dir.glob("*.tmp"))
    assert tmp_files == [], f"Orphaned tmp files: {tmp_files}"


def test_config_unchanged_on_simulated_write_crash(tmp_path, monkeypatch):
    """If the write crashes mid-way (exception in fsync), config.json stays unchanged."""
    # Write a known good config first
    config_helpers.merge_config(sarah_path="/known/path")
    config_before = config_helpers.load_config()

    # Simulate a crash by making os.rename raise after the tmp is written
    original_rename = os.rename

    def boom(src, dst):
        # Remove tmp ourselves to simulate a crash that left no tmp
        try:
            os.unlink(src)
        except OSError:
            pass
        raise OSError("simulated crash")

    monkeypatch.setattr(os, "rename", boom)
    with pytest.raises(OSError, match="simulated crash"):
        config_helpers.merge_config(sarah_path="/new/path")

    # Restore rename
    monkeypatch.setattr(os, "rename", original_rename)

    # Config file must still have the ORIGINAL content
    config_after = config_helpers.load_config()
    assert config_after["sarah_path"] == "/known/path"

    # No .tmp files left
    cfg_dir = config_helpers.CONFIG_DIR
    tmp_files = list(cfg_dir.glob("*.tmp"))
    assert tmp_files == [], f"Orphaned tmp files: {tmp_files}"


def test_config_json_is_valid_json(tmp_path):
    """The written config.json must be parseable as JSON."""
    config_helpers.merge_config(key1="val1", key2="val2")
    cfg = config_helpers.CONFIG_PATH
    with open(cfg) as f:
        data = json.load(f)
    assert data["key1"] == "val1"
    assert data["key2"] == "val2"
