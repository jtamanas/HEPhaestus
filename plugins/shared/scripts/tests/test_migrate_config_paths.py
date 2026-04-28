"""Unit tests for migrate_config_paths.py."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "migrate_config_paths.py"


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data, indent=2))
    return p


def _run(config_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(config_path)],
        capture_output=True, text=True, check=False,
    )


def test_rewrites_existing_path(tmp_path):
    real = tmp_path / ".local/share/hephaestus/tools/DDCalc"
    real.mkdir(parents=True)
    cfg = _write_config(tmp_path, {
        "ddcalc_path": str(tmp_path / ".local/share/hep-ph-agents/tools/DDCalc"),
    })
    proc = _run(cfg)
    assert proc.returncode == 0, proc.stderr
    after = json.loads(cfg.read_text())
    assert after["ddcalc_path"] == str(real)


def test_leaves_dead_path_alone(tmp_path):
    cfg = _write_config(tmp_path, {
        "ddcalc_path": str(tmp_path / ".local/share/hep-ph-agents/tools/DDCalc"),
    })
    proc = _run(cfg)
    assert proc.returncode == 0, proc.stderr
    after = json.loads(cfg.read_text())
    # Unchanged because the rewritten path doesn't exist either.
    assert "hep-ph-agents" in after["ddcalc_path"]
    assert "skipped" in proc.stderr.lower() or "missing" in proc.stderr.lower()


def test_recurses_into_nested_dicts(tmp_path):
    real = tmp_path / ".local/share/hephaestus/models/sd/SPheno.spc"
    real.parent.mkdir(parents=True)
    real.write_text("dummy")
    cfg = _write_config(tmp_path, {
        "models": {
            "singlet_doublet": {
                "latest_slha": str(tmp_path / ".local/share/hep-ph-agents/models/sd/SPheno.spc"),
                "spheno_built_at": "2026-04-22T22:41:16Z",  # untouched
            }
        }
    })
    proc = _run(cfg)
    assert proc.returncode == 0, proc.stderr
    after = json.loads(cfg.read_text())
    assert after["models"]["singlet_doublet"]["latest_slha"] == str(real)
    assert after["models"]["singlet_doublet"]["spheno_built_at"] == "2026-04-22T22:41:16Z"


def test_backup_written_once(tmp_path):
    real = tmp_path / ".local/share/hephaestus/x"
    real.mkdir(parents=True)
    cfg = _write_config(tmp_path, {
        "x": str(tmp_path / ".local/share/hep-ph-agents/x"),
    })
    _run(cfg)
    backups = list(tmp_path.glob("config.json.bak.*"))
    assert len(backups) == 1


def test_idempotent(tmp_path):
    real = tmp_path / ".local/share/hephaestus/x"
    real.mkdir(parents=True)
    cfg = _write_config(tmp_path, {
        "x": str(tmp_path / ".local/share/hep-ph-agents/x"),
    })
    _run(cfg)
    first = cfg.read_text()
    proc2 = _run(cfg)
    assert proc2.returncode == 0
    second = cfg.read_text()
    assert first == second
    backups = list(tmp_path.glob("config.json.bak.*"))
    assert len(backups) == 1


def test_no_tmp_file_left_behind(tmp_path):
    """Atomic write uses a .tmp staging file; it must not leak past success."""
    real = tmp_path / ".local/share/hephaestus/x"
    real.mkdir(parents=True)
    cfg = _write_config(tmp_path, {
        "x": str(tmp_path / ".local/share/hep-ph-agents/x"),
    })
    proc = _run(cfg)
    assert proc.returncode == 0
    leftover = list(tmp_path.glob("config.json.tmp"))
    assert leftover == [], f"tmp file leaked: {leftover}"


def test_back_to_back_invocations_get_distinct_backups(tmp_path):
    """Two invocations within the same second must produce distinct backups —
    timestamp resolution is microseconds, not seconds."""
    cfg_data = lambda: {
        "x": str(tmp_path / ".local/share/hep-ph-agents/x"),
    }
    real = tmp_path / ".local/share/hephaestus/x"
    real.mkdir(parents=True)

    # First migration
    cfg = _write_config(tmp_path, cfg_data())
    _run(cfg)
    # Reset config to legacy state and migrate again immediately
    cfg.write_text(json.dumps(cfg_data(), indent=2))
    _run(cfg)

    backups = list(tmp_path.glob("config.json.bak.*"))
    assert len(backups) == 2, f"expected 2 distinct backups, got {len(backups)}: {backups}"


def test_dry_run_does_not_mutate(tmp_path):
    real = tmp_path / ".local/share/hephaestus/x"
    real.mkdir(parents=True)
    cfg = _write_config(tmp_path, {
        "x": str(tmp_path / ".local/share/hep-ph-agents/x"),
    })
    before = cfg.read_text()
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(cfg), "--dry-run"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert cfg.read_text() == before
    assert not list(tmp_path.glob("config.json.bak.*"))
