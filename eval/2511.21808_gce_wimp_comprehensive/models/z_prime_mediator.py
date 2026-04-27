"""
Z' mediator dataclass for U(1) portals.
arXiv:2511.21808, Section II.5

The mediator carries all portal-specific information through the Charges
dataclass. No portal_key string is stored — the portal is identified by
the charges object itself.

Decay widths are imported lazily from cross_sections.z_prime_decays to
avoid circular imports (decays use the mediator).
"""

import sys
import os
from dataclasses import dataclass
from typing import Literal, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.charges import Charges, get_charges


@dataclass
class ZPrimeMediator:
    """
    Z' mediator with explicit portal charges.

    Attributes
    ----------
    charges : Charges
        Per-portal charge assignments (Q_V, Q_A, N_nu_active, N_nu_sterile).
    m_Zp : float
        Z' mass [GeV].
    g_Zp : float
        Z' gauge coupling constant.
    g_chi : float
        DM–Z' coupling constant.
    m_DM : float
        Dark matter mass [GeV].
    dm_type : str
        "Dirac" or "Majorana". Affects Γ(Z'→χχ̄) (Majorana inserts 1/2
        symmetry factor) and thermal averages.
    """
    charges: Charges
    m_Zp: float
    g_Zp: float
    g_chi: float
    m_DM: float
    dm_type: Literal["Dirac", "Majorana"]

    def coupling_to_fermion(self, flavor: str) -> Tuple[float, float]:
        """
        Physical vector and axial couplings of Z' to SM fermion `flavor`.

        Returns
        -------
        (g_V, g_A) : tuple[float, float]
            g_V = g_Zp * Q_V[flavor]
            g_A = g_Zp * Q_A[flavor]

        Raises
        ------
        KeyError if flavor is not in the Charges dict.
        """
        return (
            self.g_Zp * self.charges.Q_V[flavor],
            self.g_Zp * self.charges.Q_A[flavor],
        )

    def coupling_to_DM(self) -> float:
        """DM–Z' coupling g_chi."""
        return self.g_chi

    def propagator_squared(self, s: float) -> float:
        """
        Breit-Wigner Z' propagator squared: 1/((s-m_Zp^2)^2 + m_Zp^2 * Gamma_total^2).

        Parameters
        ----------
        s : float
            Mandelstam s [GeV^2].

        Returns
        -------
        float : |propagator|^2 [GeV^-4]
        """
        # Lazy import to avoid circular dependency
        from cross_sections.z_prime_decays import gamma_zprime_total
        gamma_tot = gamma_zprime_total(self, dm_type=self.dm_type)
        denom = (s - self.m_Zp**2)**2 + (self.m_Zp * gamma_tot)**2
        return 1.0 / denom


def make_mediator(portal: str, m_Zp: float, g_Zp: float,
                  g_chi: float, m_DM: float,
                  dm_type: Literal["Dirac", "Majorana"] = "Dirac") -> ZPrimeMediator:
    """
    Convenience constructor: build a ZPrimeMediator from a portal name string.

    Parameters
    ----------
    portal : str
        One of "Lmu_Le", "Le_Ltau", "Lmu_Ltau", "BminusL".
    m_Zp, g_Zp, g_chi, m_DM : float
        Mediator parameters.
    dm_type : str
        "Dirac" or "Majorana".

    Returns
    -------
    ZPrimeMediator
    """
    charges = get_charges(portal)
    return ZPrimeMediator(
        charges=charges,
        m_Zp=m_Zp,
        g_Zp=g_Zp,
        g_chi=g_chi,
        m_DM=m_DM,
        dm_type=dm_type,
    )
