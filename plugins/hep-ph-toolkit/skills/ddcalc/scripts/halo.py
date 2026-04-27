"""
Halo model utilities for /ddcalc.

Provides SHM defaults (per plan §2: v0=238 km/s, vesc=544 km/s, rho_0=0.3 GeV/cm³)
and halo-override echoing.

All field names use the Phase-0 schema convention:
  v0_km_per_s, vesc_km_per_s, rho0_gev_per_cm3

NOT: v0_kms, vesc_kms, rho0_gev_cm3 (these are the old brainstorm §5 names, rejected).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import json

# SHM defaults per plan §2 + 2506.19062 (Arcadi–Profumo) convention
SHM_V0_KM_PER_S: float = 238.0
SHM_VESC_KM_PER_S: float = 544.0
SHM_RHO0_GEV_PER_CM3: float = 0.3


@dataclass
class HaloParams:
    model: str
    v0_km_per_s: float
    vesc_km_per_s: float
    rho0_gev_per_cm3: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HaloParams":
        return cls(
            model=d.get("model", "shm"),
            v0_km_per_s=float(d.get("v0_km_per_s", SHM_V0_KM_PER_S)),
            vesc_km_per_s=float(d.get("vesc_km_per_s", SHM_VESC_KM_PER_S)),
            rho0_gev_per_cm3=float(d.get("rho0_gev_per_cm3", SHM_RHO0_GEV_PER_CM3)),
        )


def default_shm() -> HaloParams:
    """Return SHM defaults."""
    return HaloParams(
        model="shm",
        v0_km_per_s=SHM_V0_KM_PER_S,
        vesc_km_per_s=SHM_VESC_KM_PER_S,
        rho0_gev_per_cm3=SHM_RHO0_GEV_PER_CM3,
    )


def resolve_halo(sigma_doc: dict) -> HaloParams:
    """
    Resolve halo parameters from a scattering document.
    If sigma_doc contains a non-null 'halo' key with SHM fields, use those.
    Otherwise use SHM defaults.
    Non-SHM halo models are deferred to v1.1 (raises NotImplementedError).
    """
    halo_spec = sigma_doc.get("halo")

    if halo_spec is None:
        return default_shm()

    model = halo_spec.get("model", "shm")
    if model != "shm":
        raise NotImplementedError(
            f"Halo model '{model}' is not supported in v1. "
            "Only 'shm' is supported. Non-SHM models are v1.1."
        )

    return HaloParams.from_dict(halo_spec)


def halo_to_ddcalc_args(h: HaloParams) -> tuple[float, float, float, float]:
    """
    Return (rho, vrot, v0, vesc) for DDCalc_SetSHM.
    DDCalc SetSHM signature: (Halo, rho [GeV/cm³], vrot [km/s], v0 [km/s], vesc [km/s])
    For pure SHM, vrot = v0.
    """
    return (h.rho0_gev_per_cm3, h.v0_km_per_s, h.v0_km_per_s, h.vesc_km_per_s)
