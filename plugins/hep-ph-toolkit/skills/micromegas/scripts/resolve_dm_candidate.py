"""resolve_dm_candidate.py — DM candidate resolution for /micromegas.

Implements the spec.yaml > CLI > auto-detect resolution chain.

Public API:
    resolve(spec_dict, cli_pdg, auto_detect_flag, slha_masses, ufo_particles)
        -> (pdg, name, mass_gev, reason)

    class DMResolutionError(Exception)
        code: str  — blocker code
        mode: str  — "fatal" | "recoverable"

DM candidate resolution rules (manager-imposed):
  1. spec_dict['dm_candidate']['pdg'] wins unconditionally (reproducibility).
  2. cli_pdg honoured only when spec omits dm_candidate.
  3. auto_detect_flag is an explicit opt-in; refuses ambiguous cases with
     recoverable DM_CANDIDATE_AMBIGUOUS.
  4. Charged or colored LSP → DM_CANDIDATE_UNPHYSICAL or DM_CANDIDATE_COLOR_MISMATCH (fatal).
  5. Zero-width DECAY block keeps a candidate; non-zero width disqualifies.
  6. Two stable Z2-odd candidates → MULTICOMPONENT_UNSUPPORTED (fatal, v1).
"""
import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

from dataclasses import dataclass, field


# PDG IDs for charged particles (rough set used for DM_CANDIDATE_UNPHYSICAL check).
_CHARGED_PDGS: frozenset[int] = frozenset({
    # Standard model charged: e, mu, tau, W±, H±, charged sleptons, charginos
    11, 12, 13, 14, 15, 16, 24, 37,
    1000011, 1000013, 1000015,  # selectron, smuon, stau1
    2000011, 2000013, 2000015,  # selectron, smuon, stau2
    1000024, 1000037,           # chargino1, chargino2
})

# PDG IDs for colored particles (rough set for DM_CANDIDATE_COLOR_MISMATCH).
_COLORED_PDGS: frozenset[int] = frozenset({
    1, 2, 3, 4, 5, 6,       # quarks
    21,                      # gluon
    1000001, 1000002, 1000003, 1000004, 1000005, 1000006,  # squarks
    2000001, 2000002, 2000003, 2000004, 2000005, 2000006,
    1000021,                 # gluino
})


class DMResolutionError(Exception):
    """Raised when DM candidate cannot be resolved."""

    def __init__(self, code: str, message: str, mode: str = "fatal"):
        super().__init__(message)
        self.code = code
        self.mode = mode


@dataclass
class DMCandidate:
    pdg: int
    name: str
    mass_gev: float
    reason: str


def resolve(
    spec_dict: dict | None,
    cli_pdg: int | None,
    auto_detect_flag: bool,
    slha_masses: dict[int, float],
    ufo_particles: list[dict] | None = None,
) -> tuple[int, str, float, str]:
    """Resolve the DM candidate from spec, CLI, or auto-detect.

    Args:
        spec_dict:       Loaded spec.yaml dict (may be None).
        cli_pdg:         PDG id from --dm-pdg CLI flag (may be None).
        auto_detect_flag: True if --auto-detect was passed.
        slha_masses:     {pdg: mass_gev} from Block MASS.
        ufo_particles:   List of UFO particle dicts with keys: pdg, name,
                         z2_odd (bool), decay_width (float). May be None.

    Returns:
        Tuple (pdg, name, mass_gev, reason).

    Raises:
        DMResolutionError: with .code and .mode set appropriately.
    """
    # ── Rule 1: spec.yaml wins ────────────────────────────────────────────────
    if spec_dict and "dm_candidate" in spec_dict:
        dm_spec = spec_dict["dm_candidate"]
        if not isinstance(dm_spec, dict):
            raise DMResolutionError(
                "DM_CANDIDATE_UNPHYSICAL",
                "spec_dict['dm_candidate'] must be a dict with keys pdg, name, mass_gev.",
            )
        pdg = int(dm_spec["pdg"])
        name = str(dm_spec.get("name", f"PDG{pdg}"))
        mass_gev = float(dm_spec.get("mass_gev", slha_masses.get(pdg, 0.0)))
        _check_unphysical(pdg)
        return pdg, name, mass_gev, "spec.yaml"

    # ── Rule 2: CLI PDG ───────────────────────────────────────────────────────
    if cli_pdg is not None:
        pdg = int(cli_pdg)
        name = f"PDG{pdg}"
        mass_gev = slha_masses.get(pdg, 0.0)
        _check_unphysical(pdg)
        return pdg, name, mass_gev, "cli_pdg"

    # ── Rule 3: auto-detect ───────────────────────────────────────────────────
    if auto_detect_flag:
        return _auto_detect(slha_masses, ufo_particles)

    raise DMResolutionError(
        "MICROMEGAS_INPUT_MISSING",
        "DM candidate not specified. Add dm_candidate to spec.yaml, use --dm-pdg, or pass --auto-detect.",
    )


def _check_unphysical(pdg: int) -> None:
    """Raise DMResolutionError for charged or colored candidates."""
    abs_pdg = abs(pdg)
    if abs_pdg in _COLORED_PDGS:
        raise DMResolutionError(
            "DM_CANDIDATE_COLOR_MISMATCH",
            f"PDG {pdg} is a colored particle and cannot be the DM candidate.",
        )
    if abs_pdg in _CHARGED_PDGS:
        raise DMResolutionError(
            "DM_CANDIDATE_UNPHYSICAL",
            f"PDG {pdg} is a charged particle and cannot be the DM candidate.",
        )


def _auto_detect(
    slha_masses: dict[int, float],
    ufo_particles: list[dict] | None,
) -> tuple[int, str, float, str]:
    """Auto-detect the DM candidate from SLHA masses + UFO particle attributes.

    A candidate must be:
    - Z2-odd (from UFO attributes) or have zero decay width in SLHA.
    - Not charged or colored.

    Raises:
        DMResolutionError with MULTICOMPONENT_UNSUPPORTED for two stable candidates.
        DMResolutionError with DM_CANDIDATE_AMBIGUOUS for ambiguous cases.
    """
    if not slha_masses:
        raise DMResolutionError(
            "DM_CANDIDATE_AMBIGUOUS",
            "Auto-detect failed: SLHA Block MASS is empty.",
            mode="recoverable",
        )

    candidates: list[DMCandidate] = []

    if ufo_particles:
        # Use UFO particle Z2-odd attribute + decay width check
        for p in ufo_particles:
            pdg = int(p.get("pdg", 0))
            if pdg == 0:
                continue
            z2_odd = bool(p.get("z2_odd", False))
            if not z2_odd:
                continue
            decay_width = float(p.get("decay_width", 0.0))
            if decay_width != 0.0:
                continue  # non-zero width disqualifies
            mass_gev = slha_masses.get(pdg, float(p.get("mass_gev", 0.0)))
            name = str(p.get("name", f"PDG{pdg}"))
            try:
                _check_unphysical(pdg)
            except DMResolutionError:
                continue
            candidates.append(DMCandidate(pdg=pdg, name=name, mass_gev=mass_gev, reason="auto_detect_ufo"))
    else:
        # Fallback: use SLHA LSP (lightest non-SM particle with |mass| > 0)
        # Only attempt if no UFO particles provided
        # We pick the lightest candidate not in SM particle set
        _SM_PDGS = frozenset({1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25})
        bsm = {
            pdg: m for pdg, m in slha_masses.items()
            if abs(pdg) not in _SM_PDGS and m > 0
        }
        if not bsm:
            raise DMResolutionError(
                "DM_CANDIDATE_AMBIGUOUS",
                "Auto-detect failed: no BSM particles in Block MASS.",
                mode="recoverable",
            )
        # Sort by mass, pick lightest that is not charged/colored
        for pdg in sorted(bsm, key=lambda p: bsm[p]):
            try:
                _check_unphysical(pdg)
                candidates.append(DMCandidate(
                    pdg=pdg,
                    name=f"PDG{pdg}",
                    mass_gev=bsm[pdg],
                    reason="auto_detect_slha",
                ))
                break
            except DMResolutionError:
                continue

    if len(candidates) == 0:
        raise DMResolutionError(
            "DM_CANDIDATE_AMBIGUOUS",
            "Auto-detect failed: no neutral, stable, non-SM candidates found.",
            mode="recoverable",
        )

    if len(candidates) >= 2:
        pdgs = [c.pdg for c in candidates]
        raise DMResolutionError(
            "MULTICOMPONENT_UNSUPPORTED",
            f"Two or more stable DM candidates detected (PDGs: {pdgs}). "
            "Multi-component DM is not supported in v1. Specify dm_candidate in spec.yaml.",
        )

    c = candidates[0]
    return c.pdg, c.name, c.mass_gev, c.reason


if __name__ == "__main__":
    import json
    print(json.dumps({
        "module": "resolve_dm_candidate",
        "status": "importable",
    }))
