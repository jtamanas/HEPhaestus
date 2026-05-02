"""ini_render.py — render a CLASS .ini file from preset + BSM extension.

Public API:
    render(subcommand, preset, config_path, bsm_extension, lmax, z_pk,
           k_min, k_max, templates_dir) -> str

The rendered string is a valid CLASS ini-format text file. All Boltzmann
physics lives in the templates; this module only assembles key-value lines.

No NumPy, SciPy, or SymPy — pure string manipulation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

VALID_SUBCOMMANDS = ("background", "cmb", "pk", "transfer")
VALID_PRESETS = ("planck18", "planck18_act", "custom")
BSM_KINDS = (
    "dcdm",
    "idm_baryon",
    "idm_dr",
    "idm_photon",
    "exotic_injection",
    "ncdm_extra",
)


class IniRenderError(Exception):
    """Raised when ini rendering fails."""


# ---------------------------------------------------------------------------
# Preset definitions (Planck 2018 TT,TE,EE+lowE+lensing Table 2)
# ---------------------------------------------------------------------------

_PLANCK18 = {
    "H0": "67.32",
    "omega_b": "0.02238",
    "omega_cdm": "0.1201",
    "A_s": "2.100e-09",
    "n_s": "0.9660",
    "tau_reio": "0.0543",
}

# Planck 2018 + ACT DR4 (Aiola+ 2020; combined Planck+ACT best-fit)
_PLANCK18_ACT = {
    "H0": "67.9",
    "omega_b": "0.02242",
    "omega_cdm": "0.1193",
    "A_s": "2.088e-09",
    "n_s": "0.9721",
    "tau_reio": "0.0619",
}

_PRESETS: dict[str, dict[str, str]] = {
    "planck18": _PLANCK18,
    "planck18_act": _PLANCK18_ACT,
}


# ---------------------------------------------------------------------------
# Output key maps per subcommand
# ---------------------------------------------------------------------------

_OUTPUT_KEYS: dict[str, dict[str, str]] = {
    "background": {
        "output": "mPk",  # background always computed; mPk forces full run
        "background": "yes",
        "thermodynamics": "yes",
    },
    "cmb": {
        "output": "tCl,pCl,lCl",
        "lensing": "yes",
    },
    "pk": {
        "output": "mPk",
    },
    "transfer": {
        "output": "mTk",
    },
}


# ---------------------------------------------------------------------------
# BSM extra ini keys per kind
# ---------------------------------------------------------------------------

def _bsm_ini_keys(bsm_extension: dict[str, Any]) -> dict[str, str]:
    """Return CLASS ini key-value pairs for a BSM extension block."""
    kind = bsm_extension["kind"]
    params = bsm_extension.get("params", {})

    if kind not in BSM_KINDS:
        raise IniRenderError(f"Unknown BSM kind: {kind!r}")

    # Pass params through verbatim; the user is responsible for correctness.
    return {str(k): str(v) for k, v in params.items()}


# ---------------------------------------------------------------------------
# Core render function
# ---------------------------------------------------------------------------

def render(
    *,
    subcommand: str,
    preset: str,
    config_path: Path | None,
    bsm_extension: dict[str, Any] | None,
    lmax: int,
    z_pk: str,
    k_min: float,
    k_max: float,
    templates_dir: Path,
) -> str:
    """Render a CLASS ini-format string.

    Parameters
    ----------
    subcommand:
        One of background|cmb|pk|transfer.
    preset:
        One of planck18|planck18_act|custom.
    config_path:
        Path to a YAML override file. For preset=custom this is required.
        For planck18/planck18_act it patches the preset defaults.
    bsm_extension:
        Dict with keys 'kind' and 'params', or None for pure ΛCDM.
    lmax, z_pk, k_min, k_max:
        Numeric resolution controls forwarded to CLASS.
    templates_dir:
        Directory containing planck18.yaml and planck18_act.yaml templates.

    Returns
    -------
    str
        CLASS ini-format text.
    """
    if subcommand not in VALID_SUBCOMMANDS:
        raise IniRenderError(f"Unknown subcommand: {subcommand!r}")
    if preset not in VALID_PRESETS:
        raise IniRenderError(f"Unknown preset: {preset!r}")

    # ── Start from preset base or empty ──────────────────────────────────────
    if preset == "custom":
        params: dict[str, str] = {}
    else:
        params = dict(_PRESETS[preset])

    # ── Load YAML override / custom config ────────────────────────────────────
    if config_path is not None:
        _merge_yaml_config(params, config_path)

    # ── Apply subcommand output keys ──────────────────────────────────────────
    params.update(_OUTPUT_KEYS[subcommand])

    # ── Apply resolution controls ─────────────────────────────────────────────
    if subcommand == "cmb":
        params["l_max_scalars"] = str(lmax)

    if subcommand in ("pk", "transfer"):
        params["z_pk"] = z_pk
        params["P_k_max_h/Mpc"] = str(k_max)

    # k_min in CLASS ini is set via P_k_min_h/Mpc (CLASS 3.x flag name)
    if subcommand in ("pk", "transfer", "cmb"):
        params["P_k_min_h/Mpc"] = f"{k_min:.6e}"

    # ── Apply BSM extension ────────────────────────────────────────────────────
    if bsm_extension is not None:
        params.update(_bsm_ini_keys(bsm_extension))

    # ── Render ini text ───────────────────────────────────────────────────────
    return _dict_to_ini(params)


def _merge_yaml_config(params: dict[str, str], config_path: Path) -> None:
    """Merge YAML config into params in-place."""
    try:
        import yaml  # type: ignore[import]
    except ImportError as exc:
        raise IniRenderError(
            "PyYAML is required to load config files. "
            "Install it with: pip install pyyaml"
        ) from exc

    try:
        with open(config_path) as f:
            extra = yaml.safe_load(f)
    except Exception as exc:
        raise IniRenderError(f"Failed to load config {config_path}: {exc}") from exc

    if not isinstance(extra, dict):
        raise IniRenderError(
            f"Config file {config_path} must be a YAML mapping, got {type(extra).__name__}"
        )

    for k, v in extra.items():
        params[str(k)] = str(v)


def _dict_to_ini(params: dict[str, str]) -> str:
    """Convert a flat dict to CLASS ini format (key = value lines)."""
    lines = ["# CLASS ini file — generated by hephaestus /class", ""]
    for key, value in params.items():
        lines.append(f"{key} = {value}")
    lines.append("")
    return "\n".join(lines)
