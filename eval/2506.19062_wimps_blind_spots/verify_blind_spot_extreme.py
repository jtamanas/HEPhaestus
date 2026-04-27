"""Verify Dark SU(3) scalar blind spot at extreme parameters."""
from models.dark_su3 import sigma_SI_scalar_exact_cancellation

g_tilde = 10.0
m_V = 1.0
sin_theta = 0.707
m_H2 = 999.0

amp = sigma_SI_scalar_exact_cancellation(
    g_tilde=g_tilde, m_V=m_V, sin_theta=sin_theta, m_H2=m_H2
)
print(f"blind_spot_amplitude = {amp!r}")
