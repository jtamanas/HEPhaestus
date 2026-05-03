"""parse_outputs.py — parse classy result dict and write TSV .dat files.

Writes one TSV file per subcommand with a `# col_a col_b ...` header line
and deterministic `f"{x:.10e}"` float formatting throughout.

No NumPy, SciPy, or SymPy — pure Python string/dict manipulation.
"""
from __future__ import annotations

from pathlib import Path


class ParseOutputError(Exception):
    """Raised when output parsing fails."""


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def compute_summary(classy_result: object, input_config: dict, subcommand: str) -> dict:
    # tested against classy 3.3.4
    """Compute a scalar summary dict from a classy result object.

    Always returns exactly 8 keys:
      H0, omega_b, omega_cdm, Omega_m_h2, N_eff, tau_reio, sigma_8, z_eq

    Values are null when not computable for the given subcommand:
      - background: H0, omega_b, omega_cdm, Omega_m_h2, N_eff, z_eq populated;
                    tau_reio and sigma_8 are null.
      - cmb:        + tau_reio populated (sigma_8 still null).
      - pk:         + sigma_8 populated (tau_reio still null unless also cmb).
      - transfer:   same as background.

    Parameters
    ----------
    classy_result:
        The classy Cosmology object returned by the driver (must support
        .Hubble(0), .h(), .omega_b(), .Omega0_cdm(), .Neff(), .z_eq(),
        .tau_reio(), .sigma8()).
    input_config:
        The rendered CLASS ini parameter dict (used for omega_b / omega_cdm
        fallback when the classy object lacks methods).
    subcommand:
        One of background|cmb|pk|transfer.
    """
    # Helper: safely call a method on the result object; return None on failure.
    def _safe(method_name: str, *args):
        try:
            method = getattr(classy_result, method_name)
            return method(*args)
        except Exception:
            return None

    # ── Background parameters (available for all subcommands) ────────────────
    # classy .Hubble(0) returns H0 in km/s/Mpc
    H0_val = _safe("Hubble", 0)

    # Prefer classy methods; fall back to input_config for ω_b / ω_cdm
    h = _safe("h")
    omega_b_val = _safe("omega_b")
    if omega_b_val is None:
        raw = input_config.get("omega_b")
        omega_b_val = float(raw) if raw is not None else None

    omega_cdm_val = _safe("Omega0_cdm")
    if omega_cdm_val is not None and h is not None:
        # classy returns Ω_cdm (dimensionless); convert to ω_cdm = Ω_cdm * h²
        omega_cdm_val = omega_cdm_val * h * h
    else:
        raw = input_config.get("omega_cdm")
        omega_cdm_val = float(raw) if raw is not None else None

    # Ω_m h² = (ω_b + ω_cdm)
    if omega_b_val is not None and omega_cdm_val is not None:
        Omega_m_h2_val: float | None = omega_b_val + omega_cdm_val
    else:
        Omega_m_h2_val = None

    N_eff_val = _safe("Neff")
    z_eq_val = _safe("z_eq")

    # ── Subcommand-conditional parameters ────────────────────────────────────
    tau_reio_val: float | None = None
    sigma_8_val: float | None = None

    if subcommand == "cmb":
        tau_reio_val = _safe("tau_reio")

    if subcommand == "pk":
        sigma_8_val = _safe("sigma8")

    return {
        "H0":         H0_val,
        "omega_b":    omega_b_val,
        "omega_cdm":  omega_cdm_val,
        "Omega_m_h2": Omega_m_h2_val,
        "N_eff":      N_eff_val,
        "tau_reio":   tau_reio_val,
        "sigma_8":    sigma_8_val,
        "z_eq":       z_eq_val,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def write_outputs(
    *,
    classy_result: dict,
    run_dir: Path,
    subcommand: str,
) -> dict[str, Path]:
    """Write TSV output file(s) for the given subcommand.

    Parameters
    ----------
    classy_result:
        The dict returned by classy_driver.run().
    run_dir:
        Directory where output files are written.
    subcommand:
        One of background|cmb|pk|transfer.

    Returns
    -------
    dict[str, Path]
        Mapping of subcommand → output file path.
    """
    dispatch = {
        "background": _write_background,
        "cmb": _write_cmb,
        "pk": _write_pk,
        "transfer": _write_transfer,
    }
    if subcommand not in dispatch:
        raise ParseOutputError(f"Unknown subcommand: {subcommand!r}")

    return dispatch[subcommand](classy_result, run_dir)


# ---------------------------------------------------------------------------
# Subcommand writers
# ---------------------------------------------------------------------------

def _write_background(result: dict, run_dir: Path) -> dict[str, Path]:
    """Write background.dat with background evolution quantities."""
    bg = result.get("background")
    if not bg:
        raise ParseOutputError("classy result missing 'background' key")

    # Determine row count from first array
    columns = list(bg.keys())
    if not columns:
        raise ParseOutputError("background dict is empty")

    n_rows = len(bg[columns[0]])

    # Verify all columns have the same length
    for col in columns:
        if len(bg[col]) != n_rows:
            raise ParseOutputError(
                f"Column {col!r} has {len(bg[col])} rows, expected {n_rows}"
            )

    # Sanitise column names for TSV header (replace spaces with underscores)
    safe_cols = [c.replace(" ", "_").replace("[", "").replace("]", "") for c in columns]

    out_path = run_dir / "background.dat"
    lines = [f"# {' '.join(safe_cols)}"]
    for i in range(n_rows):
        row = " ".join(bg[col][i] for col in columns)
        lines.append(row)

    out_path.write_text("\n".join(lines) + "\n")
    return {"background": out_path}


def _write_cmb(result: dict, run_dir: Path) -> dict[str, Path]:
    """Write cls.dat with lensed CMB power spectra."""
    cls = result.get("cls")
    if not cls:
        raise ParseOutputError("classy result missing 'cls' key")

    # ell is always present; remaining keys are spectra
    ell = cls.get("ell")
    if ell is None:
        raise ParseOutputError("cls dict missing 'ell' key")

    # Standard spectra order (skip ell itself)
    spectra_keys = [k for k in cls if k != "ell"]
    header_cols = ["ell"] + spectra_keys

    out_path = run_dir / "cls.dat"
    lines = [f"# {' '.join(header_cols)}"]
    for i, ell_val in enumerate(ell):
        # ell values come as floats from classy; format as integer-like
        row_parts = [f"{float(ell_val):.0f}"]
        for k in spectra_keys:
            row_parts.append(cls[k][i])
        lines.append(" ".join(row_parts))

    out_path.write_text("\n".join(lines) + "\n")
    return {"cmb": out_path}


def _write_pk(result: dict, run_dir: Path) -> dict[str, Path]:
    """Write pk.dat with matter power spectrum P(k, z)."""
    k_h = result.get("k_h")
    pk_by_z = result.get("pk_by_z")
    z_list = result.get("z_list", ["0"])

    if not k_h or not pk_by_z:
        raise ParseOutputError("classy result missing 'k_h' or 'pk_by_z' keys")

    # Header: k_h/Mpc Pk_z0.0 Pk_z1.0 ...
    pk_cols = [f"Pk_z{z}" for z in z_list]
    header_cols = ["k_h/Mpc"] + pk_cols

    out_path = run_dir / "pk.dat"
    lines = [f"# {' '.join(header_cols)}"]
    for i, k in enumerate(k_h):
        row_parts = [k]
        for z in z_list:
            row_parts.append(pk_by_z[z][i])
        lines.append(" ".join(row_parts))

    out_path.write_text("\n".join(lines) + "\n")
    return {"pk": out_path}


def _write_transfer(result: dict, run_dir: Path) -> dict[str, Path]:
    """Write tk.dat with transfer functions T(k, z) from classy get_transfer().

    B1-fix: the result now contains per-species arrays from c.get_transfer(z).
    tk_by_z shape: {z_str: {component: [str_values, ...]}}
    Emitted components: d_cdm, d_b, d_tot (δ_cdm, δ_b, δ_tot from CLASS).
    One file per z-slice: tk_z{z}.dat; tk.dat is the z=0 slice (or first z).
    The primary output path key "transfer" points at tk.dat.
    """
    k_h = result.get("k_h")
    tk_by_z = result.get("tk_by_z")
    z_list = result.get("z_list", ["0"])
    tk_components = result.get("tk_components", ("d_cdm", "d_b", "d_tot"))

    if not k_h or not tk_by_z:
        raise ParseOutputError("classy result missing 'k_h' or 'tk_by_z' keys")

    output_paths: dict[str, Path] = {}
    primary_path: Path | None = None

    for z in z_list:
        z_data = tk_by_z.get(str(z), {})
        # Determine which components are actually present for this z
        present_comps = [c for c in tk_components if c in z_data]
        if not present_comps:
            raise ParseOutputError(
                f"tk_by_z[{z!r}] missing all expected components {tk_components!r}"
            )

        # Header: k_h/Mpc d_cdm d_b d_tot (or subset of present components)
        header_cols = ["k_h/Mpc"] + list(present_comps)
        fname = f"tk_z{z}.dat"
        out_path = run_dir / fname

        lines = [f"# {' '.join(header_cols)}"]
        for i, k in enumerate(k_h):
            row_parts = [k] + [z_data[c][i] for c in present_comps]
            lines.append(" ".join(row_parts))

        out_path.write_text("\n".join(lines) + "\n")
        output_paths[f"transfer_z{z}"] = out_path
        if primary_path is None:
            primary_path = out_path

    # Symlink / copy first-z file to tk.dat for backward compat
    tk_dat = run_dir / "tk.dat"
    if primary_path is not None:
        tk_dat.write_text(primary_path.read_text())

    output_paths["transfer"] = tk_dat
    return output_paths
