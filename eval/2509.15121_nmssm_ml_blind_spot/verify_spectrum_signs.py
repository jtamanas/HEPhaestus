"""
Standalone sign/convention sanity check for neutralino spectrum.
arXiv:2509.15121, NMSSM bino/higgsino benchmark.

USAGE (debug only, not in verification gate):
    python verify_spectrum_signs.py

This script prints the mass matrix, eigenvalues, signs, mixing matrix,
orthogonality check, and trace/det checks at BP1-3. Use it to diagnose
sign convention issues or mass ordering bugs.

NOT invoked by pytest or the harness (per plan N4).
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from constants import V_H, G1_SM
from models.neutralino_spectrum import (
    neutralino_mass_matrix, diagonalize_neutralino, bino_higgsino_fractions
)
from models.blind_spot_identity import blind_spot_identity_lhs
from benchmarks.benchmark_points import NMSSM_BENCHMARKS, _spectrum_inputs


def main():
    print("=" * 70)
    print("NMSSM Neutralino Spectrum Sign/Convention Sanity Check")
    print("arXiv:2509.15121, BP1-3")
    print("=" * 70)

    params = NMSSM_BENCHMARKS["BP1_3"]["params"]
    inp = _spectrum_inputs(params)

    M = neutralino_mass_matrix(**inp)
    print("\nMass matrix M (GeV) — (B~, W~3, Hd0, Hu0, S~) basis:")
    for i, row in enumerate(M):
        labels = ["B~", "W~3", "Hd", "Hu", "S~"]
        print(f"  {labels[i]:3s}: {[f'{x:8.3f}' for x in row]}")

    masses_abs, signs, N = diagonalize_neutralino(**inp)
    signed = masses_abs * signs

    print(f"\nEigenvalues (signed):    {signed[:4]}")
    print(f"Physical masses |m|:      {masses_abs[:4]}")
    print(f"Signs:                    {signs[:4]}")

    print("\nOrthogonality check: ||N N^T - I||_F")
    ortho_err = np.linalg.norm(N @ N.T - np.eye(5), 'fro')
    print(f"  ||N N^T - I||_F = {ortho_err:.2e}  (should be < 1e-12)")

    print("\nTrace/det checks:")
    trace_diff = np.sum(signed) - np.trace(M)
    print(f"  sum(signed evals) - tr(M) = {trace_diff:.2e}  (should be < 1e-9)")
    det_diff_rel = abs(np.prod(signed) - np.linalg.det(M)) / abs(np.linalg.det(M))
    print(f"  |prod(evals) - det(M)| / |det(M)| = {det_diff_rel:.2e}  (< 1e-8)")

    fracs = bino_higgsino_fractions(N, 0)
    print(f"\nLSP (chi1) composition:")
    print(f"  Z_B = {fracs['Z_B']:.4f}  (bino fraction)")
    print(f"  Z_W = {fracs['Z_W']:.4f}  (wino fraction)")
    print(f"  Z_H = {fracs['Z_H']:.4f}  (higgsino fraction)")
    print(f"  Z_S = {fracs['Z_S']:.4f}  (singlino fraction)")
    print(f"  Sum = {sum(fracs.values()):.12f}  (should be 1.0 exactly)")

    m_signed = masses_abs[0] * signs[0]
    denom_margin = abs(params["M1"] - m_signed)
    lhs = blind_spot_identity_lhs(m_signed, params["M1"], params["mu_eff"], params["tan_beta"])
    print(f"\nBlind-spot identity (Eq. 7) at BP1-3:")
    print(f"  m_chi1_signed = {m_signed:.4f} GeV")
    print(f"  |M1 - m_chi1| = {denom_margin:.2f} GeV (conditioning margin; want > 5 GeV)")
    print(f"  LHS = {lhs:.6f}  (Phase-1 expected: ~3.33; NOT ~1.0 due to M1=500)")
    print()
    print("NOTE: LHS != 1 because M1=500 (bino decoupled). True blind-spot test")
    print("uses the synthetic 4x4 limit test in test_benchmarks.py.")


if __name__ == "__main__":
    main()
