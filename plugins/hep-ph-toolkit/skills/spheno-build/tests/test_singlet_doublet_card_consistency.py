"""test_singlet_doublet_card_consistency.py — Majorana card self-consistency gate.

The core invariant is the Takagi-style relation for a symmetric Majorana mass
matrix: for every emitted card, the complex mixing matrix ZN = ZNMIX + i*IMZNMIX
must satisfy

    ZN . M . ZN^T == diag(+|m_i|)                      (transpose, NOT dagger)

where M is the module's OWN _mass_matrix and |m_i| are the physical (positive)
Block-MASS values. The Majorana phases live in ZN precisely so the diagonal
comes out real and POSITIVE. Additionally ZN must be unitary (ZN . ZN^dagger = I).

This is an INTERNAL-consistency gate: it checks the emitted card against the
module's own _mass_matrix. What that scope does and does not buy us w.r.t. the
two historical singlet-doublet bugs (both invisible to Block-MASS and sigma_SI):

  1. Missing Majorana phase (relic 0.0717 vs 0.2916; "Majorana phase contract"
     in analytic-backend.md) IS robustly caught by the main grid invariant on
     its own: reverting the phase leaves _mass_matrix untouched, so card<->matrix
     consistency genuinely breaks — the negative-eigenvalue row's diagonal comes
     out zero/negative and positivity fails. Guard (a) below is just an explicit
     demonstration of that.

  2. Wrong mass-matrix sign convention (spurious sigma_SI blind spot at
     theta = +/- pi/4 vs the true theta = -0.152; "Mass-matrix sign contract")
     is only PARTIALLY in scope. Because the paper's all-plus matrix is
     M_paper = D.M_sarah.D with D = diag(1,-1,1) (same spectrum), an internal
     gate cannot catch a COHERENT revert of BOTH _mass_matrix and the card back
     to paper-all-plus — that stays self-consistent and would pass. Guard (b)
     only detects an INCOHERENT card/matrix sign mismatch (right card vs wrong
     M). The coherent-revert case is out of scope for an internal-consistency
     gate; it is guarded by the Fortran-transcription contract in
     analytic-backend.md and by test_singlet_doublet_blind_spot. To add teeth
     against a coherent revert, test_mass_matrix_sarah_sign_convention below
     PINS the SARAH sign convention on _mass_matrix directly.

Pure numpy — no SPheno binary, no external data.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent / "scripts"

_TOL = 1e-8  # relative to max(|masses|)

# Parameter grid. Every point here has exactly one negative signed eigenvalue,
# so the Majorana IMZNMIX branch is exercised at every point; the yh2 != 0 rows
# also exercise the SARAH sign convention on the (1,2)/(2,3) off-diagonals.
_MS_GRID = [100.0, 150.0, 433.0, 600.0]
_MPSI_GRID = [300.0, 500.0]
_Y_GRID = [(1.0, 0.0), (0.6, 0.8), (1.0, -0.5), (0.3, 1.2)]

# A reference point with a negative eigenvalue AND yh2 != 0, used by the two
# deliberate-corruption regression guards.
_REG_POINT = {"MS": 100.0, "MPsi": 300.0, "yh1": 0.6, "yh2": 0.8}


def _load(name: str, p: Path):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def _sd():
    return _load("sd", _SCRIPTS / "analytic_models" / "singlet_doublet.py")


def _assemble_zn(znmix: dict, imznmix: dict, n: int = 3) -> np.ndarray:
    """Reconstruct complex ZN (n x n) from the (row,col)-keyed real dicts.

    Keys are 1-indexed (row, col) tuples as emitted by the analytic module;
    missing entries default to 0.
    """
    ZN = np.zeros((n, n), dtype=complex)
    for (i, j), val in znmix.items():
        ZN[i - 1, j - 1] += float(val)
    for (i, j), val in imznmix.items():
        ZN[i - 1, j - 1] += 1j * float(val)
    return ZN


def check_card_consistency(M, masses, znmix, imznmix, tol: float = _TOL):
    """Assert a Majorana mixing card is self-consistent with its mass matrix.

    Reusable core check. `M` is the (real, symmetric) mass matrix the module
    diagonalised; `masses` is the sequence of physical POSITIVE masses (Block
    MASS values) in mass-eigenstate order; `znmix`/`imznmix` are the raw
    (row,col)-keyed real dicts from result["mixing"]["ZNMIX"]/["IMZNMIX"] (or,
    equivalently, already-assembled real arrays are also accepted). `tol` is
    relative to max(|masses|).

    Verifies three things and raises AssertionError on any failure:
      * ZN . M . ZN^T == diag(masses)         (Takagi-style Majorana relation)
      * the reconstructed diagonal entries are real and POSITIVE (+|m|)
      * ZN is unitary: ZN . ZN^dagger == I

    A future second analytic module that emits SARAH-style complex mixing
    blocks (ZN = real + i*imag with |m| in Block MASS) can reuse this helper
    verbatim by passing its own _mass_matrix, Block-MASS values, and mixing
    dicts.
    """
    M = np.asarray(M, dtype=complex)
    masses = np.asarray(masses, dtype=float)
    n = M.shape[0]

    if isinstance(znmix, dict):
        ZN = _assemble_zn(znmix, imznmix, n)
    else:
        ZN = np.asarray(znmix, dtype=float) + 1j * np.asarray(imznmix, dtype=float)

    scale = float(np.max(np.abs(masses)))
    D = ZN @ M @ ZN.T
    target = np.diag(masses.astype(complex))

    dev = float(np.max(np.abs(D - target)))
    assert dev < tol * scale, (
        f"ZN.M.ZN^T != diag(masses): max|dev|={dev:.3e} "
        f"> tol*scale={tol * scale:.3e}"
    )

    diag = np.diag(D)
    assert np.max(np.abs(diag.imag)) < tol * scale, (
        f"reconstructed diagonal not real: max|Im|={np.max(np.abs(diag.imag)):.3e}"
    )
    assert np.all(diag.real > 0.0), (
        f"reconstructed diagonal not all positive: {diag.real}"
    )

    uni = float(np.max(np.abs(ZN @ ZN.conj().T - np.eye(n))))
    assert uni < tol, f"ZN not unitary: max|ZN ZN^dagger - I|={uni:.3e} > tol={tol:.3e}"

    return ZN


def _masses_vec(result, sd) -> np.ndarray:
    """Extract the three physical neutralino masses (Block MASS) in order."""
    pdg = sd.SINGLET_DOUBLET_PDG_IDS
    return np.array([
        result["masses"][pdg["Chi1"]],
        result["masses"][pdg["Chi2"]],
        result["masses"][pdg["Chi3"]],
    ], dtype=float)


@pytest.mark.parametrize("MS", _MS_GRID)
@pytest.mark.parametrize("MPsi", _MPSI_GRID)
@pytest.mark.parametrize("yh1,yh2", _Y_GRID)
def test_card_consistency_over_grid(MS, MPsi, yh1, yh2):
    """Main invariant: ZN.M.ZN^T = diag(+|m|) and ZN unitary at every point."""
    sd = _sd()
    r = sd.compute(spec={}, params={"MS": MS, "MPsi": MPsi, "yh1": yh1, "yh2": yh2})
    M = sd._mass_matrix(MS, MPsi, yh1, yh2)
    masses = _masses_vec(r, sd)
    check_card_consistency(
        M, masses, r["mixing"]["ZNMIX"], r["mixing"]["IMZNMIX"], tol=_TOL
    )


def test_regression_guard_missing_majorana_phase():
    """Dropping IMZNMIX (real-only ZN) must VIOLATE the invariant.

    Explicit demonstration of the missing-Majorana-phase failure mode (relic
    0.0717 vs 0.2916). The main grid invariant already catches this bug on its
    own — reverting the phase leaves _mass_matrix untouched, so card<->matrix
    consistency breaks — but here we make it concrete: the negative-eigenvalue
    row lives entirely in IMZNMIX, so a real-only card has a zero row -> zero
    (hence non-positive) diagonal entry and broken unitarity.
    """
    sd = _sd()
    r = sd.compute(spec={}, params=_REG_POINT)
    M = sd._mass_matrix(**_REG_POINT)
    masses = _masses_vec(r, sd)

    zero_im = {k: 0.0 for k in r["mixing"]["IMZNMIX"]}
    with pytest.raises(AssertionError):
        check_card_consistency(M, masses, r["mixing"]["ZNMIX"], zero_im, tol=_TOL)


def test_regression_guard_paper_sign_matrix():
    """The module's card must NOT diagonalise the paper's all-plus matrix.

    Detects an INCOHERENT card/mass-matrix sign mismatch (right card vs wrong M).
    The paper matrix flips the signs of the (1,2) and (2,3) off-diagonals
    relative to SARAH's _mass_matrix (see the "Mass-matrix sign contract"). It
    is related to SARAH's by conjugation with diag(1,-1,1), so it has the SAME
    spectrum (Block MASS is unchanged) yet the module's emitted ZN does not
    diagonalise it -> invariant violated.

    NOTE: this does NOT prove the historical wrong-sign bug would be caught in
    full. A COHERENT revert of BOTH _mass_matrix and the card back to
    paper-all-plus stays self-consistent (M_paper = D.M_sarah.D) and would pass
    this internal gate. That coherent case is out of scope for an
    internal-consistency gate — it is guarded by the Fortran-transcription
    contract in analytic-backend.md, by test_singlet_doublet_blind_spot, and by
    the direct sign pin in test_mass_matrix_sarah_sign_convention below.
    """
    sd = _sd()
    p = _REG_POINT
    r = sd.compute(spec={}, params=p)
    masses = _masses_vec(r, sd)

    # Paper-sign, all-plus off-diagonals (opposite convention to _mass_matrix).
    v = sd.V_H
    a = p["yh1"] * v / np.sqrt(2.0)
    b = p["yh2"] * v / np.sqrt(2.0)
    M_paper = np.array([
        [p["MS"],  b,        a       ],
        [b,        0.0,      p["MPsi"]],
        [a,        p["MPsi"], 0.0     ],
    ], dtype=float)

    # Sanity: same spectrum as the module's matrix (the bug is invisible to MASS).
    M_sarah = sd._mass_matrix(**p)
    assert np.allclose(
        np.sort(np.abs(np.linalg.eigvalsh(M_paper))),
        np.sort(np.abs(np.linalg.eigvalsh(M_sarah))),
    ), "paper/SARAH matrices should share a spectrum"

    # Checking the module's emitted card against the paper matrix must fail.
    with pytest.raises(AssertionError):
        check_card_consistency(
            M_paper, masses, r["mixing"]["ZNMIX"], r["mixing"]["IMZNMIX"], tol=_TOL
        )


def test_mass_matrix_sarah_sign_convention():
    """Pin the SARAH sign convention on _mass_matrix directly.

    The internal-consistency invariant cannot see a COHERENT revert of both
    _mass_matrix and the card back to the paper's all-plus form (M_paper =
    D.M_sarah.D shares the spectrum and stays self-consistent). This assertion
    adds teeth against exactly that: it fixes the module's matrix to SARAH's
    convention, where the (1,2) and (2,3) off-diagonals are NEGATIVE
    (-yh2*v/sqrt(2) and -MPsi per CalculateMFChi). A revert to all-plus flips
    both signs and trips this test even though the invariant would still pass.
    """
    sd = _sd()
    # Representative point with yh2 != 0 so both off-diagonals are non-zero.
    M = sd._mass_matrix(MS=200.0, MPsi=400.0, yh1=0.7, yh2=0.9)
    assert M[0, 1] < 0.0, (
        f"expected SARAH sign M[0,1] = -yh2*v/sqrt(2) < 0, got {M[0, 1]}"
    )
    assert M[1, 2] < 0.0, (
        f"expected SARAH sign M[1,2] = -MPsi < 0, got {M[1, 2]}"
    )
    # Symmetry sanity (Majorana mass matrix is symmetric).
    assert M[1, 0] == M[0, 1] and M[2, 1] == M[1, 2]
