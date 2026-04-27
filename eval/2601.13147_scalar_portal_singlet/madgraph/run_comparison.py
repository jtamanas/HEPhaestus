"""
MadGraph cross-section comparison for arXiv:2601.13147 (Scalar Portal Singlet DM).

This script:
1. Requires the UFO model to be built (has_ufo sentinel in madgraph/__init__.py)
2. Runs MadGraph to compute sigma(pp -> h2) at each benchmark point
3. Compares to the analytical sigma_pp_h2 reference

The script uses pytest.skip if has_ufo is False.

Usage (after UFO build):
    cd eval/2601.13147_scalar_portal_singlet
    python -m pytest madgraph/run_comparison.py -v
"""

import pytest
import sys
from pathlib import Path

# Check UFO availability
sys.path.insert(0, str(Path(__file__).parent.parent))
from madgraph import has_ufo

if not has_ufo:
    pytest.skip("UFO not built — run FeynRules to build scalar_portal_singlet UFO",
                allow_module_level=True)

from benchmarks.benchmark_points import BP1, BP_mid, BP9, PINNED_BPS
from models.scalar_portal_singlet import sigma_pp_h2


def get_mg5_sigma_pp_h2(bp, sigma_SM_at_m_h2: float) -> float:
    """
    Run MadGraph to compute sigma(pp -> h2) at a benchmark point.

    This is a stub that should be implemented when the UFO is available.
    It would call MadGraph5 with the rendered param card and return the
    cross section in pb.

    Parameters
    ----------
    bp                : ScalarPortalBP — benchmark point
    sigma_SM_at_m_h2  : float — SM Higgs production cross section at m_h2 [pb]

    Returns
    -------
    float : sigma(pp -> h2) from MadGraph [pb]
    """
    raise NotImplementedError(
        "UFO-dependent MadGraph run not yet implemented. "
        "Build the UFO from feynrules/scalar_portal_singlet.fr first."
    )


class TestMadGraphComparison:
    """Compare MadGraph sigma(pp->h2) to analytical sigma_pp_h2."""

    @pytest.mark.parametrize("bp", PINNED_BPS)
    def test_sigma_pp_h2(self, bp):
        """Check MadGraph agrees with sigma_pp_h2 to 5%."""
        # Example SM Higgs production cross section at 13 TeV LHC
        # (from LHC Higgs Cross Section Working Group)
        sigma_SM_examples = {200.0: 10.0, 300.0: 3.0, 70.0: 100.0}  # pb (rough)
        sigma_SM = sigma_SM_examples.get(bp.m_h2, 10.0)

        analytical = sigma_pp_h2(sigma_SM, bp.sin_theta)
        mg5_sigma = get_mg5_sigma_pp_h2(bp, sigma_SM)

        relative_diff = abs(analytical - mg5_sigma) / analytical
        assert relative_diff < 0.05, (
            f"MadGraph vs analytical sigma_pp_h2 at {bp.name}: "
            f"{mg5_sigma:.3e} vs {analytical:.3e} ({relative_diff:.1%} off)"
        )
