"""
Explicit U(1) charge assignments per portal for arXiv:2511.21808.

Each Charges dataclass stores VECTOR couplings Q_V[flavor] and AXIAL
couplings Q_A[flavor] for every SM fermion flavor. No defaults, no
inheritance. A missing flavor raises KeyError — guarantees that any
silent zero assignment fails loudly.

Physical conventions:
  - Q_V[f] = right-chiral charge = left-chiral charge for vector U(1)
  - Q_A[f] = 0 for all portals in this paper (pure vector couplings)
  - N_nu_active: number of active neutrino species that couple to this Z'
  - N_nu_sterile: number of sterile (RH) neutrinos (relevant for B-L anomaly)

Anomaly cancellation checks:
  - Lᵢ-Lⱼ portals: sum over charged leptons = 0, sum over neutrinos = 0
  - B-L: requires 3 RH sterile neutrinos; mixed/gravitational anomaly = 0

References:
  arXiv:2511.21808, Section II.5 (U(1)_{Li-Lj} and U(1)_{B-L} models)
"""

from dataclasses import dataclass

# All SM fermion flavor labels used in this benchmark
SM_FLAVORS = ("u", "d", "c", "s", "t", "b",
              "e", "mu", "tau",
              "nu_e", "nu_mu", "nu_tau")

# Quark flavors subset
QUARK_FLAVORS = ("u", "d", "c", "s", "t", "b")

# Charged lepton flavors subset
LEPTON_FLAVORS = ("e", "mu", "tau")

# Active neutrino flavors subset
NEUTRINO_FLAVORS = ("nu_e", "nu_mu", "nu_tau")


@dataclass(frozen=True)
class Charges:
    """
    U(1) charge assignments for one portal.

    Attributes
    ----------
    Q_V : dict[str, float]
        Vector coupling charge for each SM flavor.
        Physical coupling = g_Zp * Q_V[f].
    Q_A : dict[str, float]
        Axial coupling charge for each SM flavor.
        Physical axial coupling = g_Zp * Q_A[f].
        Zero for all portals in this paper.
    N_nu_active : int
        Number of active (SM) neutrino species coupling to this Z'.
    N_nu_sterile : int
        Number of right-handed (sterile) neutrinos (needed for B-L anomaly).
    name : str
        Human-readable portal name.
    """
    Q_V: dict
    Q_A: dict
    N_nu_active: int
    N_nu_sterile: int
    name: str

    def __post_init__(self):
        for f in SM_FLAVORS:
            if f not in self.Q_V:
                raise KeyError(f"{self.name}: missing Q_V[{f}]")
            if f not in self.Q_A:
                raise KeyError(f"{self.name}: missing Q_A[{f}]")


# ---------------------------------------------------------------------------
# U(1) Lμ − Le
# Charges: +1 for μ, ν_μ; −1 for e, ν_e; 0 for τ, ν_τ; 0 for quarks
# arXiv:2511.21808, Section II.5
# ---------------------------------------------------------------------------
LMU_MINUS_LE = Charges(
    name="Lmu_minus_Le",
    Q_V={
        "u": 0.0, "d": 0.0, "c": 0.0, "s": 0.0, "t": 0.0, "b": 0.0,
        "e": -1.0, "mu": +1.0, "tau": 0.0,
        "nu_e": -1.0, "nu_mu": +1.0, "nu_tau": 0.0,
    },
    Q_A={f: 0.0 for f in SM_FLAVORS},
    N_nu_active=2,    # ν_μ and ν_e
    N_nu_sterile=0,
)

# ---------------------------------------------------------------------------
# U(1) Le − Lτ
# Charges: +1 for e, ν_e; −1 for τ, ν_τ; 0 for μ, ν_μ; 0 for quarks
# arXiv:2511.21808, Section II.5
# ---------------------------------------------------------------------------
LE_MINUS_LTAU = Charges(
    name="Le_minus_Ltau",
    Q_V={
        "u": 0.0, "d": 0.0, "c": 0.0, "s": 0.0, "t": 0.0, "b": 0.0,
        "e": +1.0, "mu": 0.0, "tau": -1.0,
        "nu_e": +1.0, "nu_mu": 0.0, "nu_tau": -1.0,
    },
    Q_A={f: 0.0 for f in SM_FLAVORS},
    N_nu_active=2,    # ν_e and ν_τ
    N_nu_sterile=0,
)

# ---------------------------------------------------------------------------
# U(1) Lμ − Lτ
# Charges: +1 for μ, ν_μ; −1 for τ, ν_τ; 0 for e, ν_e; 0 for quarks
# arXiv:2511.21808, Section II.5
# ---------------------------------------------------------------------------
LMU_MINUS_LTAU = Charges(
    name="Lmu_minus_Ltau",
    Q_V={
        "u": 0.0, "d": 0.0, "c": 0.0, "s": 0.0, "t": 0.0, "b": 0.0,
        "e": 0.0, "mu": +1.0, "tau": -1.0,
        "nu_e": 0.0, "nu_mu": +1.0, "nu_tau": -1.0,
    },
    Q_A={f: 0.0 for f in SM_FLAVORS},
    N_nu_active=2,    # ν_μ and ν_τ
    N_nu_sterile=0,
)

# ---------------------------------------------------------------------------
# U(1) B − L
# Charges: +1/3 for all quarks; −1 for all leptons including 3 RH sterile ν
# arXiv:2511.21808, Section II.5
# Anomaly cancellation: requires 3 RH (sterile) neutrinos
# Sum rule: 3*(6 quarks * 1/3) + (3 charged leptons + 3 active ν) * (-1)
#           + 3 RH sterile ν * (-1) = 0
#           = 3*(2) + 6*(-1) + 3*(-1) = 6 - 6 - 3 ≠ 0 without RH ν
# With RH sterile: 6 - 6 - 3 + 3*(-1+1) ... see test_anomaly_free_BminusL
# Note: Q_V dict covers active-ν only; sterile counted via N_nu_sterile
# ---------------------------------------------------------------------------
B_MINUS_L = Charges(
    name="B_minus_L",
    Q_V={
        "u": +1.0/3, "d": +1.0/3, "c": +1.0/3, "s": +1.0/3,
        "t": +1.0/3, "b": +1.0/3,
        "e": -1.0, "mu": -1.0, "tau": -1.0,
        "nu_e": -1.0, "nu_mu": -1.0, "nu_tau": -1.0,
    },
    Q_A={f: 0.0 for f in SM_FLAVORS},
    N_nu_active=3,    # all 3 active neutrinos
    N_nu_sterile=3,   # 3 RH sterile neutrinos (each Q_B-L = -1)
)


# ---------------------------------------------------------------------------
# Portal name → Charges lookup
# ---------------------------------------------------------------------------
PORTAL_CHARGES = {
    "Lmu_Le":   LMU_MINUS_LE,
    "Le_Ltau":  LE_MINUS_LTAU,
    "Lmu_Ltau": LMU_MINUS_LTAU,
    "BminusL":  B_MINUS_L,
}


def get_charges(portal: str) -> Charges:
    """
    Return the Charges dataclass for a named portal.

    Parameters
    ----------
    portal : str
        One of "Lmu_Le", "Le_Ltau", "Lmu_Ltau", "BminusL".

    Returns
    -------
    Charges

    Raises
    ------
    KeyError if portal name is unknown.
    """
    if portal not in PORTAL_CHARGES:
        raise KeyError(
            f"Unknown portal '{portal}'. "
            f"Valid options: {list(PORTAL_CHARGES.keys())}"
        )
    return PORTAL_CHARGES[portal]
