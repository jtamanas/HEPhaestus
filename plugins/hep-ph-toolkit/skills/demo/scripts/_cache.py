"""Cache path resolution and config loading for the /demo scripts.

The demo reads (never writes) artifacts produced upstream by /sarah and
/spheno, and calls /madgraph and /maddm at runtime. This module owns every
filesystem path the demo touches.

Layout:
    ~/.cache/hephaestus/
        sarah_cache/<model_hash>/
            ufo/                         # SARAH-produced UFO (read)
            spheno_bin                   # SPheno executable (read, exec)
            lagrangian.m                 # source Lagrangian (read)
        runs/<model_hash>/<param_hash>/
            spectrum.slha                # SPheno output per param point
            param_card.dat               # MG5 param card (write)
            run_card.dat                 # MG5 run card (write)
            mg5_stdout.log               # MG5 log (write)

    ~/.config/hephaestus/config.json  # madgraph_path, maddm_path
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
EVAL_DIR = REPO_ROOT / "eval" / "2506.19062_wimps_blind_spots"


def cache_root() -> Path:
    # XDG_CACHE_HOME is respected so CI can relocate the cache.
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "hephaestus"


def config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "hephaestus" / "config.json"


def load_config() -> dict:
    p = config_path()
    if not p.exists():
        raise SystemExit(
            f"Config not found at {p}. Run /install first to set up "
            "MadGraph and MadDM paths."
        )
    return json.loads(p.read_text())


def sarah_cache_dir(model_hash: str) -> Path:
    return cache_root() / "sarah_cache" / model_hash


def ufo_dir(model_hash: str) -> Path:
    return sarah_cache_dir(model_hash) / "ufo"


def spheno_binary(model_hash: str) -> Path:
    return sarah_cache_dir(model_hash) / "spheno_bin"


def run_dir(model_hash: str, param_hash: str) -> Path:
    return cache_root() / "runs" / model_hash / param_hash


def ensure_sarah_cache(model_hash: str) -> Path:
    """Return the UFO directory or bail with an actionable diagnostic.

    The script NEVER regenerates SARAH output — that's /sarah's job. A cache
    miss means the orchestrator skipped a step.
    """
    ufo = ufo_dir(model_hash)
    if not ufo.is_dir():
        raise SystemExit(
            f"SARAH cache miss for model-hash {model_hash} — "
            "run /demo from the top to regenerate"
        )
    return ufo


def ensure_spheno(model_hash: str) -> Path:
    sp = spheno_binary(model_hash)
    if not sp.exists():
        raise SystemExit(
            f"SPheno binary missing at {sp} — run /demo from the top to "
            "regenerate"
        )
    return sp


def param_hash(params: dict) -> str:
    """Deterministic hash of a parameter point for run-dir caching."""
    canon = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


def output_dir(model: str, figure: int) -> Path:
    """Where run_scan.py writes scan_results.json (CWD-local, not cache)."""
    d = Path.cwd() / "demo_output" / model / str(figure)
    d.mkdir(parents=True, exist_ok=True)
    return d
