"""SPheno backend: thin wrapper around run_point.run preserving legacy behaviour."""

from __future__ import annotations

import importlib.util as _ilu
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SphenoBackend:
    name = "spheno"

    def compute(self, model_name, spec, params, out_dir: Path, config):
        rp = _load("run_point", _SCRIPT_DIR / "run_point.py")
        lh_in = out_dir / "LesHouches.in"
        if not lh_in.exists():
            return {
                "status": "fatal",
                "blocker_code": "SPHENO_NO_OUTPUT",
                "slha_path": None,
                "summary": None,
                "backend": "spheno",
                "cache_hit": False,
            }
        r = rp.run(model_name, lh_in, out_dir)
        r["backend"] = "spheno"
        r.setdefault("cache_hit", False)
        return r
