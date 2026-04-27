"""YAML loader for ModelSpec v3."""
import pathlib
import yaml


class SpecLoadError(Exception):
    """Failed to load a spec file."""


def load_spec(path: "pathlib.Path | str") -> dict:
    p = pathlib.Path(path)
    if not p.is_file():
        raise SpecLoadError(f"spec file not found: {p}")
    try:
        with p.open() as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise SpecLoadError(f"YAML parse error in {p}: {e}") from e
