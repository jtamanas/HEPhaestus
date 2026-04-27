"""Dispatch table for the 3 models x 3 figures matrix."""

from __future__ import annotations

import importlib
from typing import Callable

VALID = {"a1", "a2", "a3", "b1", "b2", "b3", "c1", "c2", "c3"}


def get_handler(model: str, figure: int) -> Callable:
    key = f"{model.lower()}{figure}"
    if key not in VALID:
        raise SystemExit(
            f"Unknown (model, figure) combo: model={model} figure={figure}. "
            "Valid: A|B|C x 1|2|3."
        )
    mod = importlib.import_module(f"_figures.{key}")
    return mod.run
