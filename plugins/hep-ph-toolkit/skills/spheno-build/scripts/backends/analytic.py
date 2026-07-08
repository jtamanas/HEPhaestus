"""Analytic backend: dispatches to a registered analytic_models/<name>.py module.

Handles:
    - Registry lookup (ANALYTIC_MODULE_MISSING on miss).
    - Exception classification (ValueError → ANALYTIC_INVALID_PARAMS,
      numpy.linalg.LinAlgError → ANALYTIC_SPECTRUM_PROBLEM, other → ANALYTIC_INTERNAL_ERROR).
    - SLHA rendering via slha_writer.render().
    - summary.json + LesHouches.in (traceability echo) + SPheno.spc writing.
    - Cache key (sha256(module_bytes) + sha256(params_json)) recorded to
      <model_dir>/.spectrum_key.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util as _ilu
import json
import sys
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent.parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"


def _load(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _compute_key(module_path: Path, params: dict) -> str:
    mod_hash = _sha256(module_path.read_bytes())
    params_json = json.dumps(params, sort_keys=True, separators=(",", ":"))
    p_hash = _sha256(params_json.encode())
    return f"{p_hash}+{mod_hash}"


def _write_spectrum_key(model_dir: Path, key: str) -> None:
    import datetime
    path = model_dir / ".spectrum_key"
    blob: dict = {}
    if path.exists():
        try:
            blob = json.loads(path.read_text())
        except Exception:
            blob = {}
    blob["analytic"] = {
        "key": key,
        "built_at": datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.write_text(json.dumps(blob, indent=2, sort_keys=True))


def _resolve_module(spec: dict, model_name: str):
    backends = spec.get("backends") or {}
    dotted = backends.get("analytic_module")
    if dotted:
        # Import from dotted path (e.g. analytic_models.singlet_doublet).
        am = _load_registry()
        if dotted in {f"analytic_models.{k}" for k in am.REGISTRY}:
            key = dotted.rsplit(".", 1)[1]
            return am.REGISTRY[key]
        # Hard dotted path override (future escape hatch).
        try:
            mod = importlib.import_module(dotted)
            return mod
        except Exception:
            return None
    am = _load_registry()
    return am.REGISTRY.get(model_name)


def _load_registry():
    return _load(
        "analytic_models",
        _SCRIPT_DIR / "analytic_models" / "__init__.py",
    )


def _emit_blocker(code: str, mode: str, message: str, ctx: dict | None = None):
    blocker: dict = {"code": code, "mode": mode, "message": message}
    if ctx:
        blocker["context"] = ctx
    print(json.dumps(blocker), file=sys.stderr)


class AnalyticBackend:
    name = "analytic"

    def compute(self, model_name, spec, params, out_dir: Path, config):
        out_dir.mkdir(parents=True, exist_ok=True)

        mod = _resolve_module(spec, model_name)
        if mod is None:
            msg = (f"No analytic module registered for model {model_name!r}. "
                   f"Register it in analytic_models/__init__.py or set "
                   f"backends.analytic_module in spec.yaml.")
            _emit_blocker("ANALYTIC_MODULE_MISSING", "fatal", msg,
                          {"model": model_name})
            return {"status": "fatal", "blocker_code": "ANALYTIC_MODULE_MISSING",
                    "slha_path": None, "summary": None,
                    "backend": "analytic", "cache_hit": False}

        # Execute the physics.
        try:
            result_dict = mod.compute(spec=spec, params=params)
        except ValueError as exc:
            _emit_blocker("ANALYTIC_INVALID_PARAMS", "recoverable", str(exc),
                          {"params": params})
            return {"status": "recoverable",
                    "blocker_code": "ANALYTIC_INVALID_PARAMS",
                    "slha_path": None, "summary": None,
                    "backend": "analytic", "cache_hit": False}
        except np.linalg.LinAlgError as exc:
            _emit_blocker("ANALYTIC_SPECTRUM_PROBLEM", "recoverable", str(exc),
                          {"params": params})
            return {"status": "recoverable",
                    "blocker_code": "ANALYTIC_SPECTRUM_PROBLEM",
                    "slha_path": None, "summary": None,
                    "backend": "analytic", "cache_hit": False}
        except Exception as exc:
            _emit_blocker("ANALYTIC_INTERNAL_ERROR", "fatal",
                          f"{type(exc).__name__}: {exc}", {"params": params})
            return {"status": "fatal", "blocker_code": "ANALYTIC_INTERNAL_ERROR",
                    "slha_path": None, "summary": None,
                    "backend": "analytic", "cache_hit": False}

        # Render SLHA text.
        sw = _load("slha_writer", _SCRIPT_DIR / "slha_writer.py")
        slha_text = sw.render(result_dict, spec=spec, params=params)

        spc_path = out_dir / "SPheno.spc"
        spc_path.write_text(slha_text)

        # Also emit a traceability LesHouches.in so downstream tools / humans
        # see the params that were used. Harmless duplicate when caller wrote one.
        lht = _load("leshouches_template", _SCRIPT_DIR / "leshouches_template.py")
        (out_dir / "LesHouches.in").write_text(lht.build(spec, overrides=params))

        # Parse back to build summary.json (so downstream reads are uniform).
        ps = _load("parse_slha", _SCRIPT_DIR / "parse_slha.py")
        summary = ps.parse(spc_path)

        # Merge diagnostics + mixing from the analytic module's result_dict
        # into the summary payload so they survive the SLHA round-trip.
        # The SLHA writer does not emit diagnostics-only fields (e.g.
        # Omega_V_h2, blind_spot_*) and only partially emits mixing
        # blocks (MHHMIX may be skipped), so consumers downstream of
        # /spheno-build (e.g. /dark-matter-constraints analytic-only branch)
        # need them merged in directly.
        diagnostics = result_dict.get("diagnostics")
        if diagnostics is not None:
            summary["diagnostics"] = diagnostics
        mixing = result_dict.get("mixing")
        if mixing is not None:
            # Stringify tuple keys so the JSON survives a round-trip.
            mixing_serializable: dict = {}
            for block_name, entries in mixing.items():
                if isinstance(entries, dict):
                    mixing_serializable[block_name] = {
                        (",".join(str(k) for k in key)
                         if isinstance(key, tuple) else str(key)): val
                        for key, val in entries.items()
                    }
                else:
                    mixing_serializable[block_name] = entries
            summary["mixing"] = mixing_serializable

        # Record which backend produced this summary so downstream readers
        # (and humans skimming summary.json) don't have to infer it from
        # SPINFO text or file layout.
        summary.setdefault("backend", "analytic")

        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        # Also emit a separate diagnostics.json next to summary.json so
        # downstream router branches (e.g. analytic-only DM constraints)
        # can consume the full diagnostics dict without parsing summary.
        if diagnostics is not None:
            (out_dir / "diagnostics.json").write_text(
                json.dumps(diagnostics, indent=2)
            )

        # Cache-key bookkeeping.
        try:
            module_path = Path(mod.__file__)
            key = _compute_key(module_path, params)
            model_dir = out_dir.parent.parent  # .../models/<name>/runs/<ts>/
            _write_spectrum_key(model_dir, key)
        except Exception:
            # Non-fatal: cache bookkeeping failure should not fail the run.
            pass

        if result_dict.get("problem"):
            _emit_blocker("ANALYTIC_SPECTRUM_PROBLEM", "recoverable",
                          f"Analytic module flagged problems {result_dict['problem']}",
                          {"problems": result_dict["problem"]})
            return {"status": "recoverable",
                    "blocker_code": "ANALYTIC_SPECTRUM_PROBLEM",
                    "slha_path": str(spc_path), "summary": summary,
                    "backend": "analytic", "cache_hit": False}

        if not summary.get("masses"):
            _emit_blocker("ANALYTIC_INTERNAL_ERROR", "fatal",
                          "Analytic module produced empty MASS block.", None)
            return {"status": "fatal", "blocker_code": "ANALYTIC_INTERNAL_ERROR",
                    "slha_path": str(spc_path), "summary": summary,
                    "backend": "analytic", "cache_hit": False}

        return {"status": "ok", "blocker_code": None,
                "slha_path": str(spc_path), "summary": summary,
                "backend": "analytic", "cache_hit": False}
