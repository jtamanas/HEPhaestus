"""Wiring tests for run_sarah.py (v3 port).

All wolframscript invocations are mocked — these tests verify:
  - _build_make_commands dispatch
  - _compute_cache_key format
  - Cache-hit fast-path (no SARAH invocation)
  - Fatal blocker when wolfram_engine_path is absent from config
"""

import json
import pathlib
import sys
from unittest.mock import patch, MagicMock
import pytest

REPO = pathlib.Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'plugins' / 'hep-ph-toolkit' / 'skills' / 'sarah-build' / 'scripts'))
sys.path.insert(0, str(REPO / 'plugins' / 'hep-ph-toolkit' / 'skills' / '_shared'))
sys.path.insert(0, str(REPO / 'plugins' / 'shared' / 'install-helpers'))

import run_sarah


def test_make_commands_ufo_only():
    assert run_sarah._build_make_commands(['ufo']) == 'MakeUFO[];'


def test_make_commands_ufo_and_spheno():
    assert run_sarah._build_make_commands(['ufo', 'spheno']) == 'MakeUFO[]; MakeSPheno[];'


def test_make_commands_unknown_raises():
    with pytest.raises(ValueError):
        run_sarah._build_make_commands(['frobnicate'])


def test_cache_key_format():
    bytes_ = b'model:\n  name: Foo'
    key = run_sarah._compute_cache_key(bytes_, '4.15.3')
    assert '=' in key
    sha, ver = key.split('=', 1)
    assert len(sha) == 64
    assert ver == '4.15.3'


def test_run_fatal_when_wolfram_kernel_missing(tmp_path):
    """If config has no wolfram_engine_path, run() exits with WOLFRAM_KERNEL_ABSENT."""
    SM_TEMPLATE = REPO / 'plugins' / 'hep-ph-toolkit' / 'skills' / '_shared' / 'modelspec_v3' / 'templates' / 'sm.yaml'

    with patch('run_sarah.config_helpers') as mock_ch:
        mock_ch.load_config.return_value = {}  # no wolfram_engine_path
        mock_ch._reload_roots = MagicMock()
        with pytest.raises(SystemExit):
            run_sarah.run(SM_TEMPLATE, tmp_path / 'model_dir', force=False, outputs=['ufo'])


def test_cache_hit_returns_cached_status(tmp_path):
    """If cache key matches and ufo_dir exists, run() returns {'status': 'cached'} without invoking SARAH."""
    SM_TEMPLATE = REPO / 'plugins' / 'hep-ph-toolkit' / 'skills' / '_shared' / 'modelspec_v3' / 'templates' / 'sm.yaml'
    model_dir = tmp_path / 'model_dir'
    model_dir.mkdir()

    # Pre-populate cache state
    spec_bytes = SM_TEMPLATE.read_bytes()
    cache_key = run_sarah._compute_cache_key(spec_bytes, '4.15.3')
    (model_dir / '.sarah_build_key').write_text(cache_key)

    # In v3, spec.model.name IS the SARAH name directly.
    sarah_name = 'SM'
    ufo_dir = model_dir / 'sarah_output' / 'UFO' / sarah_name
    ufo_dir.mkdir(parents=True)

    with patch('run_sarah.config_helpers') as mock_ch, \
         patch('run_sarah.repair_symlinks'):  # don't actually touch the symlink
        mock_ch.load_config.return_value = {
            'wolfram_engine_path': '/usr/local/bin/wolframscript',
            'sarah_path': '/tmp/sarah-fake',
            'sarah_version': '4.15.3',
        }
        mock_ch._reload_roots = MagicMock()
        mock_ch.get_model.return_value = None

        result = run_sarah.run(SM_TEMPLATE, model_dir, force=False, outputs=['ufo'])

    assert result == {'status': 'cached'}
