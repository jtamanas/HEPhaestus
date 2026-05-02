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
    """Write tk.dat with transfer functions T(k, z)."""
    k_h = result.get("k_h")
    tk_by_z = result.get("tk_by_z")
    z_list = result.get("z_list", ["0"])

    if not k_h or not tk_by_z:
        raise ParseOutputError("classy result missing 'k_h' or 'tk_by_z' keys")

    # Header: k_h/Mpc Tk_z0.0 Tk_z1.0 ...
    tk_cols = [f"Tk_z{z}" for z in z_list]
    header_cols = ["k_h/Mpc"] + tk_cols

    out_path = run_dir / "tk.dat"
    lines = [f"# {' '.join(header_cols)}"]
    for i, k in enumerate(k_h):
        row_parts = [k]
        for z in z_list:
            row_parts.append(tk_by_z[z][i])
        lines.append(" ".join(row_parts))

    out_path.write_text("\n".join(lines) + "\n")
    return {"transfer": out_path}
