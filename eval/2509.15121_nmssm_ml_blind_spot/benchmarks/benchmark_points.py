"""
Benchmark parameter points for arXiv:2509.15121 (NMSSM bino/higgsino blind spot).

Parameter definitions:
  M1        : bino soft mass [GeV]          (fixed: 500 GeV, per Table 2)
  M2        : wino soft mass [GeV]          (large; 5000 GeV, wino decoupled)
  mu_eff    : effective higgsino mass [GeV] (positive convention; paper quotes -mu_eff)
  tan_beta  : tan β = vu/vd                 (fixed: 6.2, per Table 2)
  lambda_   : NMSSM λ coupling              (fixed: 0.027, per Table 2)
  kappa     : NMSSM κ coupling              (varies per group; range 0.010-0.0133)
  vS        : singlet VEV [GeV]             (derived: vS = mu_eff / lambda_)
  A_lambda  : trilinear soft A_λ [GeV]      (not needed for tree-level EWino spectrum)
  A_kappa   : trilinear soft A_κ [GeV]      (100 GeV per Table 2; not needed for tree-level)

Notes on parameter reconstruction:
  - The paper's Table 7-8 output masses are from NMSSMTools (includes radiative corrections).
  - Our tree-level 5×5 diagonalization (Eq. 3) reproduces the masses approximately.
  - vS = mu_eff / lambda_ is the tree-level relation from mu_eff = lambda * vS.
  - kappa is tuned so that 2*kappa*vS matches the singlino-LSP mass to within ~1 GeV.
  - mu_eff is estimated from the chargino mass m_chi1+ ~ |mu_eff| per benchmark group.
  - Paper convention: -mu_eff ranges 130-320 GeV (paper uses negative mu_eff in SLHA).
    Our convention: mu_eff > 0 throughout (positive convention in mass matrix).

Source labels:
  - "paper_table_7": masses from arXiv:2509.15121, Table 7
  - "paper_table_8": masses from arXiv:2509.15121, Table 8 (via Table 6 for BP9-3)
  - "fabricated_negative_control": off-blind-spot cousin (mu_eff sign flip)
"""

import json
import os
from pathlib import Path

# ======================================================================
# NMSSM Benchmark Points
# ======================================================================

NMSSM_BENCHMARKS = {

    # ------------------------------------------------------------------
    # BP1-3: Group 1 on-blind-spot benchmark (Table 7)
    # m_chi1=147.5, m_chi2=158.5, m_chi3=164.8, m_chi1+=161.8 GeV
    # sigma_DD^SI = 1.3e-48 cm^2, Omega_h2 = 0.10, epsilon = 0.075
    # Z_BL = 6.29 sigma, Z_MLL = 6.67 sigma  (discovery significance)
    # Tree-level approximation: our 5x5 diag gives slightly different m_chi2.
    # ------------------------------------------------------------------
    "BP1_3": {
        "params": {
            "M1": 500.0,         # bino soft mass [GeV], fixed per Table 2
            "M2": 5000.0,        # wino soft mass [GeV], decoupled
            "mu_eff": 161.8,     # |mu_eff| = m_chi1+ (group 1 chargino mass) [GeV]
            "tan_beta": 6.2,     # fixed per Table 2
            "lambda_": 0.027,    # fixed per Table 2
            "kappa": 0.01243,    # tuned: 2*kappa*vS ~ m_chi1 (singlino LSP)
            "vS": 5992.59,       # = mu_eff / lambda_ [GeV]
            "A_lambda": -900.0,  # typical; range -800 to -1100 GeV per Table 2
            "A_kappa": 100.0,    # fixed per Table 2 [GeV]
        },
        "expected": {
            # Paper Table 7 values (tree-level formula gives slight variations)
            "m_chi1_paper": 147.5,        # [GeV] paper Table 7
            "m_chi2_paper": 158.5,        # [GeV] paper Table 7
            "m_chi3_paper": 164.8,        # [GeV] paper Table 7
            "sigma_DD_SI": 1.3e-48,       # [cm^2] paper Table 7 (transcription)
            "omega_h2": 0.10,             # Omega_chi h^2, paper Table 7 (transcription)
            "epsilon_paper": 0.075,       # compression param, paper Table 7
        },
        "source": "paper_table_7",
        "sigma_prod_mg5_cached": None,    # populated when cached_sigma_prod.json exists
    },

    # ------------------------------------------------------------------
    # BP9-3: Group 9 sub-relic benchmark (Table 8 / Table 6)
    # m_chi1=235.1, m_chi2=245.0, m_chi3=251.7 GeV
    # sigma_DD^SI = 4.2e-48 cm^2, Omega_h2 = 0.07, Z_BL = 2.84, Z_MLL = 3.80
    # sigma(pp->chi1+chi20 j) ~ 28.4 fb at sqrt(s)=14 TeV
    # ------------------------------------------------------------------
    "BP9_3": {
        "params": {
            "M1": 500.0,         # bino soft mass [GeV], fixed per Table 2
            "M2": 5000.0,        # wino soft mass [GeV], decoupled
            "mu_eff": 250.306,   # |mu_eff| estimated from higgsino mass scale [GeV]
            "tan_beta": 6.2,     # fixed per Table 2
            "lambda_": 0.027,    # fixed per Table 2
            "kappa": 0.01277,    # tuned: 2*kappa*vS ~ m_chi1 (singlino LSP)
            "vS": 9270.59,       # = mu_eff / lambda_ [GeV]
            "A_lambda": -1000.0, # typical; range -800 to -1100 GeV per Table 2
            "A_kappa": 100.0,    # fixed per Table 2 [GeV]
        },
        "expected": {
            # Paper values from Table 8 / Table 6
            "m_chi1_paper": 235.1,        # [GeV] paper Table 8 / Table 6
            "m_chi2_paper": 245.0,        # [GeV] paper Table 8 / Table 6
            "m_chi3_paper": 251.7,        # [GeV] paper Table 8 / Table 6
            "sigma_DD_SI": 4.2e-48,       # [cm^2] paper Table 6 (transcription)
            "omega_h2": 0.07,             # Omega_chi h^2, paper Table 6 (transcription)
            "epsilon_paper": 0.0421,      # = 245.0/235.1 - 1, from paper masses
        },
        "source": "paper_table_8",
        "sigma_prod_mg5_cached": None,    # populated when cached_sigma_prod.json exists
    },

    # ------------------------------------------------------------------
    # BP5-2: Group 5 intermediate benchmark (Table 7)
    # m_chi1=179.8, m_chi2=204.4, m_chi3=210.8 GeV
    # sigma(pp->chi1+chi20 j) = 49.93 fb
    # ------------------------------------------------------------------
    "BP5_2": {
        "params": {
            "M1": 500.0,         # bino soft mass [GeV], fixed per Table 2
            "M2": 5000.0,        # wino soft mass [GeV], decoupled
            "mu_eff": 209.051,   # |mu_eff| estimated from higgsino mass scale [GeV]
            "tan_beta": 6.2,     # fixed per Table 2
            "lambda_": 0.027,    # fixed per Table 2
            "kappa": 0.01165,    # tuned: 2*kappa*vS ~ m_chi1 (singlino LSP)
            "vS": 7742.63,       # = mu_eff / lambda_ [GeV]
            "A_lambda": -1000.0, # typical
            "A_kappa": 100.0,    # fixed per Table 2 [GeV]
        },
        "expected": {
            # Paper Table 7 values
            "m_chi1_paper": 179.8,        # [GeV] paper Table 7
            "m_chi2_paper": 204.4,        # [GeV] paper Table 7
            "m_chi3_paper": 210.8,        # [GeV] paper Table 7
            "sigma_DD_SI": 9.7e-49,       # [cm^2] paper Table 7 (BP5-2)
            "omega_h2": 2.7,              # Omega_chi h^2, paper Table 7
            "epsilon_paper": 0.137,       # = 204.4/179.8 - 1
        },
        "source": "paper_table_7",
        "sigma_prod_mg5_cached": None,
    },

    # ------------------------------------------------------------------
    # BP1_3_off: Fabricated negative control (off blind spot)
    # Same as BP1_3 but with mu_eff sign flipped: mu_eff -> -mu_eff.
    # This takes the point away from the blind-spot condition by inverting
    # the sign of the higgsino mass, breaking the blind-spot cancellation.
    # The Eq. 7 LHS at this point is clearly different from the on-BP value.
    # Source: FABRICATED — NOT from the paper.
    # ------------------------------------------------------------------
    "BP1_3_off": {
        "params": {
            "M1": 500.0,
            "M2": 5000.0,
            "mu_eff": -161.8,    # SIGN FLIPPED relative to BP1_3
            "tan_beta": 6.2,
            "lambda_": 0.027,
            "kappa": 0.01243,    # same kappa as BP1_3
            "vS": -5992.59,      # = mu_eff / lambda_ (negative because mu_eff < 0)
            "A_lambda": -900.0,
            "A_kappa": 100.0,
        },
        "expected": {
            # Not from paper — fabricated for negative control test
        },
        "source": "fabricated_negative_control",
        "sigma_prod_mg5_cached": None,
    },
}


def _spectrum_inputs(params: dict) -> dict:
    """
    Extract kwargs for diagonalize_neutralino from a BP params dict.

    Returns the subset of params needed for the 5×5 neutralino diagonalization.
    A_lambda and A_kappa are soft-breaking parameters not needed at tree level.
    """
    return {
        "M1": params["M1"],
        "M2": params["M2"],
        "mu_eff": params["mu_eff"],
        "tan_beta": params["tan_beta"],
        "lambda_": params["lambda_"],
        "kappa": params["kappa"],
        "vS": params["vS"],
    }


def _load_sigma_prod_cache() -> dict:
    """
    Load the MadGraph5 cached production cross sections if available.

    Returns empty dict if the cache file does not exist. Never raises
    an exception on a missing file (returns {} instead).

    The cache file (if present) is at:
        eval/2509.15121_nmssm_ml_blind_spot/madgraph/cached_sigma_prod.json
    """
    cache_path = Path(__file__).parent.parent / "madgraph" / "cached_sigma_prod.json"
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _populate_sigma_prod_cache():
    """Populate sigma_prod_mg5_cached in NMSSM_BENCHMARKS from cache file (if present)."""
    cache = _load_sigma_prod_cache()
    for bp_name, cache_entry in cache.items():
        if bp_name in NMSSM_BENCHMARKS and "sigma_fb" in cache_entry:
            NMSSM_BENCHMARKS[bp_name]["sigma_prod_mg5_cached"] = cache_entry["sigma_fb"]


# Populate at import time (reads cache file at call time; no side effects if absent)
_populate_sigma_prod_cache()
