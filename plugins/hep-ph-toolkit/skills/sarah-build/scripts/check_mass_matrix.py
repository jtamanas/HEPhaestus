"""
check_mass_matrix.py — Verify SARAH mass-matrix extraction for each ewsb.mixing.

Catches SARAH silent failures where CalcMixingsOfMatterFields degenerates a
mass matrix to ``MassMatrix::OnlyZero`` (usually because of a bad-Lagrangian
section pattern — e.g. a Majorana mass in LagNoHC instead of LagHC, or a
component-level conj[] wrapper that confuses CalcMixingsOfMatterFields) or
emits a rank-deficient matrix (a Weyl that never couples back to the rest
of the block).

For each ewsb.mixings[] entry we locate the corresponding
``CalculateM<eigenstate>`` subroutine in SPheno Fortran source (SARAH's
primary mass-matrix emission path) and read the ``mat(i,j) = ...`` lines.

Usage:
    python3 check_mass_matrix.py --spec <modelspec.yaml> --output-dir <SARAH_output_dir>

    <SARAH_output_dir> should be the top-level SARAH model output dir
    (contains ``EWSB/SPheno/``) or the SPheno source dir directly (contains
    ``TreeLevelMasses_<model>.f90``). Both layouts are searched.

Input paths:
    --output-dir accepts any directory under which ``TreeLevelMasses_*.f90``
    can be found by recursive glob. /sarah-build writes the SPheno Fortran
    tree under:
        <STATE_ROOT>/models/<model_name>/sarah_output/SPheno/<SarahName>/
    so --output-dir may be:
        <STATE_ROOT>/models/<model_name>/sarah_output/     (SARAH tree)
        <STATE_ROOT>/models/<model_name>/sarah_output/SPheno/<SarahName>/
    Example:
        ~/.local/share/hephaestus/models/singlet_doublet/sarah_output/
    SARAH's native output tree (``~/SARAH/SARAH-4.15.3/Output/<SarahName>/
    EWSB/``) is also accepted — the recursive glob picks up either layout.

Exits:
    0 — every declared mixing has a populated, full-rank mass matrix
    1 — at least one MASS_MATRIX_DEGENERATE blocker emitted
    2 — MASS_MATRIX_RANK_DEFICIENT only (no DEGENERATE)

Parsing approach (pragmatic, regex-based):
    - Find ``TreeLevelMasses_*.f90`` (SPheno's tree-level mass extraction
      source, written by SARAH). Fall back to ``MassMatrices.m`` in
      ``EWSB/`` if present (older SARAH layouts).
    - Locate ``Subroutine CalculateM<eigenstate>(...)`` header and read
      until the matching ``End Subroutine``.
    - Scan for ``mat(<i>,<j>) = ...`` assignments and also
      ``mat(<i>,<j>) = mat(<i>,<j>) + <expr>`` accumulators. A matrix
      entry counts as "populated" iff at least one such line assigns
      a non-literal-zero expression.
    - Rank heuristic: build the symmetric matrix (upper entries mirrored
      to lower), treat each populated (i,j) slot as a unit, and compute
      the connected-component count of the graph where nodes are Weyl
      indices and edges are populated off-diagonal entries. A fully
      populated block has 1 component; isolated unused rows show as
      extra components and are reported as rank-deficient.

Limitations:
    - A populated entry is not the same as a nonzero entry at runtime;
      we can't evaluate Fortran expressions here. But ``OnlyZero`` shows
      up in the Fortran source as an entirely empty matrix block (or
      one with only ``mat(i,i) = 0._dp`` initialisations), which this
      script catches correctly.
    - If neither TreeLevelMasses_*.f90 nor MassMatrices.m is found, a
      parse-skipped warning is emitted and we exit 0 (nothing to check).
    - We rely on SARAH's convention that the subroutine name is
      ``CalculateM<mass_eigenstate>`` (e.g. ``CalculateMFChi``). Dirac
      mixings with ``mass_eigenstate: ChiM`` are looked up as
      ``CalculateMFChiM`` — we try both with and without the ``F``
      prefix that SARAH prepends to Dirac / Majorana fermion eigenstates.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import re
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Blocker emission helpers
# ---------------------------------------------------------------------------


def _emit(blocker: dict) -> None:
    print(json.dumps(blocker, indent=2), file=sys.stderr)


def _emit_degenerate(mixing_name: str, expected_fields: list[str]) -> None:
    _emit({
        "code": "MASS_MATRIX_DEGENERATE",
        "mode": "recoverable",
        "message": (
            f"Mass matrix for mixing {mixing_name!r} is OnlyZero — every "
            f"(i,j) entry is either absent or a literal 0 in the "
            f"SARAH/SPheno emission. SARAH's CalcMixingsOfMatterFields "
            f"silently dropped every element. Common root causes: "
            f"(a) Majorana mass term placed in LagNoHC instead of LagHC "
            f"with AddHC->True; (b) mixing block spelled over conj[]-"
            f"wrapped Weyl components; (c) missing discrete symmetry "
            f"tag on constituent Weyls. See sarah-gotchas.md "
            f"§MASS_MATRIX_DEGENERATE."
        ),
        "context": {
            "mixing_name": mixing_name,
            "expected_fields": expected_fields,
        },
    })


def _emit_rank_deficient(
    mixing_name: str, expected_rank: int, actual_rank: int
) -> None:
    _emit({
        "code": "MASS_MATRIX_RANK_DEFICIENT",
        "mode": "recoverable",
        "message": (
            f"Mass matrix for mixing {mixing_name!r} has structural rank "
            f"{actual_rank} < expected {expected_rank}. At least one "
            f"declared Weyl does not couple to the rest of the block at "
            f"the populated-entry level. Likely a missing Yukawa or "
            f"mass term; if intentional (e.g. one decoupled generation), "
            f"split the mixing entry. See sarah-gotchas.md "
            f"§MASS_MATRIX_RANK_DEFICIENT."
        ),
        "context": {
            "mixing_name": mixing_name,
            "expected_rank": expected_rank,
            "actual_rank": actual_rank,
        },
    })


def _warn_parse_skipped(reason: str, context: dict) -> None:
    print(
        json.dumps({
            "code": "MASS_MATRIX_PARSE_SKIPPED",
            "mode": "warning",
            "message": reason,
            "context": context,
        }, indent=2),
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Locate SARAH / SPheno sources
# ---------------------------------------------------------------------------


def _find_fortran_sources(output_dir: Path) -> list[Path]:
    """Return TreeLevelMasses_*.f90 files under *output_dir* (recursive)."""
    return sorted(output_dir.rglob("TreeLevelMasses_*.f90"))


def _find_mass_matrices_m(output_dir: Path) -> list[Path]:
    """Return MassMatrices.m files under *output_dir* (if any)."""
    return sorted(output_dir.rglob("MassMatrices.m"))


# ---------------------------------------------------------------------------
# Fortran parsing
# ---------------------------------------------------------------------------

_SUBROUTINE_RE = re.compile(
    r"^\s*Subroutine\s+(\w+)\s*\(", re.IGNORECASE | re.MULTILINE,
)
_END_SUBROUTINE_RE = re.compile(
    r"^\s*End\s+Subroutine", re.IGNORECASE | re.MULTILINE,
)
_MAT_ASSIGN_RE = re.compile(
    r"\bmat\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*(.+?)\s*$",
    re.MULTILINE,
)


def _subroutine_body(text: str, name: str) -> str | None:
    """Return the body of ``Subroutine <name>(...) ... End Subroutine``.

    Case-insensitive on the ``Subroutine`` / ``End Subroutine`` keywords.
    """
    hdr_re = re.compile(
        rf"^\s*Subroutine\s+{re.escape(name)}\s*\(",
        re.IGNORECASE | re.MULTILINE,
    )
    m = hdr_re.search(text)
    if m is None:
        return None
    body_start = m.end()
    end_m = _END_SUBROUTINE_RE.search(text, body_start)
    if end_m is None:
        return text[body_start:]
    return text[body_start:end_m.start()]


def _candidate_subroutine_names(mass_eigenstate: str) -> list[str]:
    """SARAH prepends 'F' to fermion mass eigenstates and 'M' to the Calculate*."""
    candidates = [
        f"CalculateM{mass_eigenstate}",
        f"CalculateMF{mass_eigenstate}",
    ]
    # Also the "EffPot" variants live in the same file — we prefer the plain
    # one but accept either (the matrix structure is identical).
    candidates += [c + "EffPot" for c in candidates]
    return candidates


def _populated_entries(body: str) -> dict[tuple[int, int], bool]:
    """Scan a subroutine body for mat(i,j) assignments.

    Returns a dict {(i,j): is_populated}. An entry is ``populated`` iff it
    appears at least once with a right-hand side that isn't exactly
    ``0._dp`` / ``0._dp;`` / ``(0._dp,0._dp)`` and isn't a pure re-copy of
    its own zero initialiser.
    """
    populated: dict[tuple[int, int], bool] = {}
    for m in _MAT_ASSIGN_RE.finditer(body):
        i, j = int(m.group(1)), int(m.group(2))
        rhs = m.group(3).strip().rstrip(";").strip()
        # Strip trailing Fortran continuation markers / comments.
        rhs = rhs.split("!")[0].strip()
        is_zero = rhs in (
            "0._dp", "0.0_dp", "0.d0", "0.0d0", "(0._dp,0._dp)", "0",
        )
        # Accumulator form ``mat(i,j) = mat(i,j)`` by itself is also
        # effectively zero until another assignment adds a term.
        is_self_copy = re.fullmatch(
            rf"mat\(\s*{i}\s*,\s*{j}\s*\)\s*",
            rhs,
            re.IGNORECASE,
        ) is not None
        if not (is_zero or is_self_copy):
            populated[(i, j)] = True
        else:
            populated.setdefault((i, j), False)
    return populated


def _connected_components(n: int, edges: set[tuple[int, int]]) -> int:
    """Count connected components of an undirected graph on nodes 1..n.

    Each node is its own component unless an off-diagonal edge links it
    to another.
    """
    parent = {i: i for i in range(1, n + 1)}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in edges:
        if a != b and 1 <= a <= n and 1 <= b <= n:
            union(a, b)
    roots = {find(i) for i in range(1, n + 1)}
    return len(roots)


def _analyse_matrix(body: str, dim: int) -> tuple[bool, int]:
    """Return (is_degenerate, structural_rank_proxy) for a subroutine body.

    ``is_degenerate`` iff no (i,j) entry has a nonzero-looking RHS.
    ``structural_rank_proxy`` = dim - (connected_components - 1), clipped
    to [0, dim]. A fully-coupled n×n block gives dim. A block split into
    two disconnected sub-blocks drops by 1.
    """
    populated = _populated_entries(body)
    any_populated = any(populated.values())
    if not any_populated:
        return (True, 0)

    # Every populated off-diagonal entry counts as an edge (symmetrise).
    edges: set[tuple[int, int]] = set()
    diag_populated = 0
    for (i, j), ok in populated.items():
        if not ok:
            continue
        if i == j:
            diag_populated += 1
        else:
            edges.add((min(i, j), max(i, j)))
    components = _connected_components(dim, edges)
    # A Weyl with no populated entry in its row/col at all is a rank drop.
    touched: set[int] = {i for (i, j), ok in populated.items() if ok for i in (i, j)}
    untouched = dim - len(touched & set(range(1, dim + 1)))
    rank_proxy = dim - (components - 1) - untouched
    rank_proxy = max(0, min(dim, rank_proxy))
    return (False, rank_proxy)


# ---------------------------------------------------------------------------
# MassMatrices.m fallback parser
# ---------------------------------------------------------------------------

_MM_BLOCK_RE = re.compile(
    r"MassMatrix\s*\[\s*(\w+)\s*\]\s*:?=\s*(\{.*?\})\s*;",
    re.DOTALL,
)


def _analyse_mm_block(block: str, dim: int) -> tuple[bool, int]:
    """Analyse a Mathematica matrix literal: OnlyZero or symbolic."""
    s = block.strip()
    if "OnlyZero" in s or re.fullmatch(r"\{\s*(\{\s*0\s*,?\s*\}?,?\s*)+\s*\}", s):
        return (True, 0)
    # Coarse rank proxy: count non-zero symbolic slots. Mathematica literals
    # are too varied for a proper parse — just count commas.
    populated_slots = len(re.findall(r"[A-Za-z]\w*", s))
    return (False, min(dim, max(1, populated_slots)))


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def _mixing_dim(mixing: dict) -> int:
    """Dimension of the SARAH mass-matrix block.

    Majorana / scalar: n = number of weyls (they all mix among themselves).
    Dirac: n = max(|lh_weyls|, |rh_weyls|) — SARAH emits a rectangular
    lh×rh matrix but SPheno diagonalises the square M M^dag / M^dag M
    blocks; when both sides have length 1 the matrix is 1×1.
    """
    if mixing.get("chirality") == "dirac":
        lh = len(mixing.get("lh_weyls") or [])
        rh = len(mixing.get("rh_weyls") or [])
        return max(1, max(lh, rh))
    weyls = mixing.get("weyls") or []
    return max(1, len(weyls))


def _mixing_expected_fields(mixing: dict) -> list[str]:
    weyls = (
        (mixing.get("weyls") or [])
        + (mixing.get("lh_weyls") or [])
        + (mixing.get("rh_weyls") or [])
    )
    return [str(w) for w in weyls]


def _mixing_name(mixing: dict) -> str:
    return str(
        mixing.get("mass_eigenstate")
        or mixing.get("mixing_matrix")
        or "<unnamed>"
    )


def _analyse_mixing(
    mixing: dict,
    fortran_texts: list[str],
    mm_text: str | None,
) -> tuple[bool, int] | None:
    """Return (is_degenerate, rank_proxy) or None if no matrix source found."""
    eigenstate = mixing.get("mass_eigenstate")
    if not eigenstate:
        return None
    dim = _mixing_dim(mixing)

    for text in fortran_texts:
        for name in _candidate_subroutine_names(eigenstate):
            body = _subroutine_body(text, name)
            if body is not None:
                return _analyse_matrix(body, dim)

    if mm_text is not None:
        for m in _MM_BLOCK_RE.finditer(mm_text):
            if m.group(1) == eigenstate or m.group(1) == f"F{eigenstate}":
                return _analyse_mm_block(m.group(2), dim)
    return None


def run(spec_path: Path, output_dir: Path) -> int:
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    fortran_files = _find_fortran_sources(output_dir)
    mm_files = _find_mass_matrices_m(output_dir)

    if not fortran_files and not mm_files:
        _warn_parse_skipped(
            f"No TreeLevelMasses_*.f90 or MassMatrices.m found under {output_dir}. "
            f"Nothing to check.",
            {"output_dir": str(output_dir)},
        )
        return 0

    fortran_texts = [p.read_text(encoding="utf-8", errors="replace") for p in fortran_files]
    mm_text = (
        "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in mm_files)
        if mm_files else None
    )

    degenerate_hits = 0
    rank_hits = 0

    for mixing in spec.get("ewsb", {}).get("mixings", []) or []:
        # Only fermion mixings currently have a SARAH CalculateM* subroutine
        # that follows the mat(i,j) convention; scalar mixings emit a
        # different structure we skip for now.
        if mixing.get("kind") != "fermion":
            continue
        result = _analyse_mixing(mixing, fortran_texts, mm_text)
        if result is None:
            _warn_parse_skipped(
                f"No matrix block found for mixing "
                f"{_mixing_name(mixing)!r} (tried Fortran CalculateM* and "
                f"MassMatrices.m). Skipping.",
                {"mixing_name": _mixing_name(mixing)},
            )
            continue
        is_degenerate, rank_proxy = result
        dim = _mixing_dim(mixing)
        if is_degenerate:
            _emit_degenerate(_mixing_name(mixing), _mixing_expected_fields(mixing))
            degenerate_hits += 1
            continue
        if rank_proxy < dim:
            _emit_rank_deficient(_mixing_name(mixing), dim, rank_proxy)
            rank_hits += 1

    if degenerate_hits > 0:
        return 1
    if rank_hits > 0:
        return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify SARAH mass-matrix extraction against spec ewsb.mixings.",
    )
    parser.add_argument("--spec", required=True, type=Path,
                        help="ModelSpec YAML file.")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="SARAH output dir or SPheno model source dir.")
    args = parser.parse_args()
    sys.exit(run(args.spec, args.output_dir))


if __name__ == "__main__":
    main()
