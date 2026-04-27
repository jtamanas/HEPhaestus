"""resolve_model.py — three-way model source precedence for /feynarts generate.

Precedence:
  1. --sarah-model <name>: SARAH state in $STATE_ROOT/models/<name>/feynarts_state/
  2. --model-file <path>: user-supplied .mod/.gen pair
  3. --model <builtin>: FeynArts built-in (SM, SMQCD, THDM, MSSM)

Exactly one source must be specified. More than one → FEYNARTS_MODEL_SOURCE_CONFLICT.
None → FEYNARTS_ABSENT.

Returns dict with: source, model_name, mod_path, gen_path, state_dir (optional)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_BUILTIN_MODELS = {"SM", "SMQCD", "THDM", "MSSM"}

_DEFAULT_STATE_ROOT = os.path.expanduser(
    os.environ.get("HEPPH_FEYNARTS_STATE_ROOT", "~/.local/share/hephaestus")
)


class ModelResolutionError(Exception):
    """Raised when model specification cannot be resolved."""

    def __init__(self, code: str, message: str, context: Optional[dict] = None):
        # Prepend code so pytest.raises(match=code) works
        super().__init__(f"{code}: {message}")
        self.code = code
        self.context = context or {}


def resolve_model(
    model: Optional[str] = None,
    sarah_model: Optional[str] = None,
    model_file: Optional[str] = None,
    model_name: Optional[str] = None,
    feynarts_path: Optional[str] = None,
    state_root: Optional[str] = None,
) -> dict:
    """Resolve model source and return paths.

    Args:
        model: Built-in model name (SM/SMQCD/THDM/MSSM).
        sarah_model: SARAH model name (looks up feynarts_state/).
        model_file: Path to directory with .mod/.gen files.
        model_name: Model name for use with model_file.
        feynarts_path: Path to FeynArts installation (for builtin).
        state_root: Override state root directory.

    Returns:
        dict: source, model_name, mod_path, gen_path, [state_dir]
    """
    sources_provided = sum(
        x is not None for x in [model, sarah_model, model_file]
    )

    if sources_provided > 1:
        flags = []
        if model is not None:
            flags.append("--model")
        if sarah_model is not None:
            flags.append("--sarah-model")
        if model_file is not None:
            flags.append("--model-file")
        raise ModelResolutionError(
            "FEYNARTS_MODEL_SOURCE_CONFLICT",
            f"Multiple model sources specified: {', '.join(flags)}. "
            "Provide exactly one of --model, --sarah-model, or --model-file.",
            {"flags_provided": flags},
        )

    if sources_provided == 0:
        raise ModelResolutionError(
            "FEYNARTS_ABSENT",
            "No model source specified. Provide --model, --sarah-model, or --model-file.",
        )

    # --- SARAH model ---
    if sarah_model is not None:
        return _resolve_sarah_model(sarah_model, state_root)

    # --- User model file ---
    if model_file is not None:
        return _resolve_model_file(model_file, model_name)

    # --- Built-in model ---
    return _resolve_builtin(model, feynarts_path)


def _resolve_sarah_model(model_name: str, state_root: Optional[str]) -> dict:
    """Resolve SARAH-generated model from feynarts_state/ directory."""
    root = Path(state_root or _DEFAULT_STATE_ROOT)
    state_dir = root / "models" / model_name / "feynarts_state"

    mod_path = state_dir / f"{model_name}.mod"
    gen_path = state_dir / f"{model_name}.gen"

    if not state_dir.exists() or not mod_path.exists():
        raise ModelResolutionError(
            "FEYNARTS_SARAH_STATE_MISSING",
            f"SARAH FeynArts state not found for model '{model_name}'. "
            "Run /feynarts generate with --sarah-model to trigger MakeFeynArts[] first, "
            "or ensure /sarah-build has completed.",
            {"model_name": model_name, "state_dir": str(state_dir)},
        )

    return {
        "source": "sarah",
        "model_name": model_name,
        "mod_path": str(mod_path),
        "gen_path": str(gen_path) if gen_path.exists() else "",
        "state_dir": str(state_dir),
    }


def _resolve_model_file(file_path: str, model_name: Optional[str]) -> dict:
    """Resolve user-supplied .mod/.gen model file directory."""
    p = Path(file_path)

    # Find .mod file
    if not p.exists():
        raise ModelResolutionError(
            "FEYNARTS_MODEL_FILE_INVALID",
            f"Model file path '{file_path}' does not exist.",
            {"path": file_path},
        )

    if p.is_dir():
        mod_files = list(p.glob("*.mod"))
        if not mod_files:
            raise ModelResolutionError(
                "FEYNARTS_MODEL_FILE_INVALID",
                f"No .mod file found in directory '{file_path}'.",
                {"path": file_path},
            )
        mod_path = mod_files[0]
        # Try to find matching .gen
        gen_path = mod_path.with_suffix(".gen")
        resolved_name = model_name or mod_path.stem
    else:
        if p.suffix != ".mod":
            raise ModelResolutionError(
                "FEYNARTS_MODEL_FILE_INVALID",
                f"Model file '{file_path}' must be a .mod file or directory.",
                {"path": file_path},
            )
        mod_path = p
        gen_path = p.with_suffix(".gen")
        resolved_name = model_name or p.stem

    return {
        "source": "file",
        "model_name": resolved_name,
        "mod_path": str(mod_path),
        "gen_path": str(gen_path) if gen_path.exists() else "",
    }


def _resolve_builtin(model_name: str, feynarts_path: Optional[str]) -> dict:
    """Resolve a FeynArts built-in model."""
    if model_name not in _BUILTIN_MODELS:
        raise ModelResolutionError(
            "FEYNARTS_ABSENT",
            f"Unknown built-in model '{model_name}'. "
            f"Available: {', '.join(sorted(_BUILTIN_MODELS))}.",
            {"model_name": model_name, "available": sorted(_BUILTIN_MODELS)},
        )

    if feynarts_path is None:
        # Try to get from environment / config (runtime will inject this)
        feynarts_path = os.environ.get("FEYNARTS_PATH", "")

    if feynarts_path:
        fa = Path(feynarts_path)
        models_dir = fa / "Models"
        mod_path = models_dir / f"{model_name}.mod"
        gen_path = models_dir / f"{model_name}.gen"

        if not mod_path.exists():
            raise ModelResolutionError(
                "FEYNARTS_ABSENT",
                f"Built-in model '{model_name}' not found at {mod_path}.",
                {"model_name": model_name, "feynarts_path": feynarts_path},
            )

        return {
            "source": "builtin",
            "model_name": model_name,
            "mod_path": str(mod_path),
            "gen_path": str(gen_path) if gen_path.exists() else "",
            "feynarts_path": feynarts_path,
        }

    # No feynarts_path — the model name will be used directly in wolframscript
    # (FeynArts resolves it relative to its package dir at runtime)
    return {
        "source": "builtin",
        "model_name": model_name,
        "mod_path": "",  # resolved at runtime
        "gen_path": "",
    }
