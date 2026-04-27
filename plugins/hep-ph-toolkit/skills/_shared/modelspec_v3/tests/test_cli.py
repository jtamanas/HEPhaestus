import json
import pathlib
import subprocess
import os
import pytest

REPO = pathlib.Path(__file__).resolve().parents[6]   # repo root
SHARED = REPO / 'plugins' / 'hep-ph-toolkit' / 'skills' / '_shared'
FIX = pathlib.Path(__file__).parent / 'fixtures'


def _run_cli(*args):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SHARED) + os.pathsep + env.get('PYTHONPATH', '')
    return subprocess.run(
        ['python', '-m', 'modelspec_v3.cli', *args],
        capture_output=True, text=True, env=env, cwd=str(REPO))


def test_cli_validates_clean():
    proc = _run_cli('validate', str(FIX / 'sm_minimal.yaml'))
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_cli_reports_errors_with_exit_2():
    proc = _run_cli('validate', str(FIX / 'missing_required.yaml'))
    assert proc.returncode == 2
    assert 'error' in proc.stdout.lower() or 'error' in proc.stderr.lower()


def test_cli_warnings_exit_0_by_default(tmp_path):
    # Make a fixture with only warnings: load sm_minimal, perturb anomaly, write to tmp
    import yaml
    spec = yaml.safe_load((FIX / 'sm_minimal.yaml').read_text())
    spec['fermions'][0]['reps']['B'] = '1/7'
    p = tmp_path / 'anomaly.yaml'
    p.write_text(yaml.dump(spec))
    proc = _run_cli('validate', str(p))
    assert proc.returncode == 0   # warnings don't fail by default


def test_cli_strict_warns_become_errors(tmp_path):
    import yaml
    spec = yaml.safe_load((FIX / 'sm_minimal.yaml').read_text())
    spec['fermions'][0]['reps']['B'] = '1/7'
    p = tmp_path / 'anomaly.yaml'
    p.write_text(yaml.dump(spec))
    proc = _run_cli('validate', '--strict', str(p))
    assert proc.returncode == 1   # warnings become errors with --strict


def test_cli_json_format():
    proc = _run_cli('validate', '--format=json', str(FIX / 'missing_required.yaml'))
    assert proc.returncode == 2
    for line in proc.stdout.strip().splitlines():
        if line.strip():
            json.loads(line)   # each line must be valid JSON


def test_cli_render_writes_files(tmp_path):
    proc = _run_cli('render', str(FIX / 'sm_minimal.yaml'), '--out', str(tmp_path))
    assert proc.returncode == 0, proc.stderr + proc.stdout
    expected = {'SMTest.m', 'parameters.m', 'particles.m'}
    actual = {p.name for p in tmp_path.iterdir()}
    assert expected.issubset(actual)


def test_cli_render_refuses_invalid_spec(tmp_path):
    proc = _run_cli('render', str(FIX / 'missing_required.yaml'), '--out', str(tmp_path))
    assert proc.returncode == 2
    assert 'refusing to render' in proc.stderr or 'error' in proc.stderr.lower()
