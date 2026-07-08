"""test_sigma_si_sign_guard.py — regression guard for the up/down Higgs–Yukawa sign bug.

A relative sign error between up-type (+m_q/v) and down-type (−m_q/v) Higgs–quark
couplings in the SARAH-exported singlet-doublet model suppressed tree σ_SI ~200×
and faked isospin violation (opposite-sign / large p/n). It was root-caused to a
dropped leading minus on the up-Yukawa term ('Yu H.u.q' instead of '-Yu H.u.q')
in the ModelSpec YAMLs and fixed on branch sigma-si-sign-fix. See the σ_SI
adjudication VERDICT §2/§6/§7 and RESULTS from the T2 MadDM verification.

This is a pure-python guard: NO MadDM/micrOMEGAs binary. It asserts the *recorded*
truth in benchmarks/canonical-2026/expectations.json is internally consistent with
the trusted analytic anchor eval/.../cross_sections/si_tree_level.py (paper Eq. 5),
and that the canonical ModelSpec still renders the sign-matched up-Yukawa.

The guard is designed to FAIL if the sign fix is reverted, i.e. if expectations.json
were restored to σ_SI(p)=3.7098e-47 with p/n=8.17:
  * Assertion A rejects p/n=8.17 (outside the isoscalar [0.9,1.1] band).
  * Assertion B rejects σ_SI(p)=3.7098e-47 (it is ~205× below the anchor 7.6e-45,
    far outside the ±50% form-factor tolerance).
Sanity-checked in test_guard_would_fail_on_reverted_sign below.

Run: python -m pytest test_sigma_si_sign_guard.py -v
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SKILL = _HERE.parent
_ROOT = _HERE.parents[4]  # tests → singlet-doublet → skills → hep-ph-toolkit → plugins → ROOT

_EXPECTATIONS = _SKILL / "benchmarks" / "canonical-2026" / "expectations.json"
_ANCHOR = _ROOT / "eval" / "2506.19062_wimps_blind_spots" / "cross_sections" / "si_tree_level.py"

# The up-Yukawa sign fix landed in THREE ModelSpec files; a revert of ANY of them
# reintroduces the σ_SI sign bug, so the guard must cover all three (a
# golden-validation blind spot: the golden test never byte-compares this sign).
_MODELSPEC = _ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "modelspec_v3"
_SIGN_FIXED_SPECS = [
    _MODELSPEC / "specs" / "singlet_doublet.yaml",
    _MODELSPEC / "specs" / "dark_su3.yaml",
    _MODELSPEC / "templates" / "sm.yaml",
]

# Canonical benchmark (MS=150, MPsi=500, yh1=1, yh2=0, θ=0), validated values.
# m_χ = m_χ1 and the effective h-χ1-χ1 coupling are the anchor inputs (VERDICT header).
_M_CHI = 132.692285
_Y_H_CHI_CHI = 0.122229

# Tolerances.
_PN_BAND = (0.9, 1.1)          # isoscalar band for Majorana pure-Higgs SI (Assertion A)
_FF_TOL = 0.50                 # ±50% form-factor/running-mass tolerance (Assertion B)


def _load_expectations() -> dict:
    return json.loads(_EXPECTATIONS.read_text())


def _load_anchor():
    """Load si_tree_level.py by file path (spheno-build test idiom).

    The module inserts its own eval/ root onto sys.path at import so `constants`
    resolves regardless of cwd — no sys.path manipulation needed here.
    """
    spec = importlib.util.spec_from_file_location("si_tree_level_anchor", _ANCHOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _recorded_sigma_si_p(exp: dict) -> float:
    """The toolkit's recorded σ_SI(p): the MadDM-measured value."""
    return float(exp["toolkit_measurements"]["maddm_3_2_sarah_consistent"]["sigma_SI_p_cm2"])


def _recorded_p_over_n(exp: dict) -> float:
    return float(exp["toolkit_measurements"]["maddm_3_2_sarah_consistent"]["p_over_n"])


# ── Assertion A: isoscalar p/n ────────────────────────────────────────────────
def test_recorded_p_over_n_is_isoscalar():
    """Majorana pure-Higgs-portal SI is isoscalar (p/n ≈ 0.97). A large or
    opposite-sign p/n (e.g. the sign-bug 8.17) is a model bug and must FAIL."""
    exp = _load_expectations()
    lo, hi = _PN_BAND

    pn_measured = _recorded_p_over_n(exp)
    assert lo <= pn_measured <= hi, (
        f"recorded MadDM p/n={pn_measured} outside isoscalar band {_PN_BAND} — "
        f"the up/down Higgs–Yukawa relative sign may be broken (see VERDICT §2)."
    )

    pn_expectation = float(exp["expectations"]["p_over_n"]["central"])
    assert lo <= pn_expectation <= hi, (
        f"expectations.p_over_n.central={pn_expectation} outside {_PN_BAND}."
    )


# ── Assertion B: recorded σ_SI(p) agrees with the trusted analytic anchor ──────
def test_recorded_sigma_si_matches_anchor():
    """The recorded σ_SI(p) must agree with si_tree_level.py's formula
    (paper Eq. 5) at the canonical benchmark within ±50% form-factor tolerance.
    The sign-bug value 3.7098e-47 is ~205× low and fails this."""
    exp = _load_expectations()
    anchor = _load_anchor()

    anchor_p = anchor.sigma_SI_higgs_portal(m_chi=_M_CHI, y_h_chi_chi=_Y_H_CHI_CHI)
    recorded_p = _recorded_sigma_si_p(exp)

    rel = abs(recorded_p / anchor_p - 1.0)
    assert rel <= _FF_TOL, (
        f"recorded σ_SI(p)={recorded_p:.4e} cm² disagrees with anchor "
        f"{anchor_p:.4e} cm² by {rel*100:.0f}% (> {_FF_TOL*100:.0f}%). A ~200× "
        f"gap is the up/down Higgs–Yukawa sign bug (VERDICT §2/§6)."
    )

    # The 'central' expectation should track the anchor too.
    central = float(exp["expectations"]["sigma_SI_p_cm2"]["central"])
    rel_c = abs(central / anchor_p - 1.0)
    assert rel_c <= _FF_TOL, (
        f"expectations.sigma_SI_p_cm2.central={central:.4e} disagrees with anchor "
        f"{anchor_p:.4e} by {rel_c*100:.0f}% (> {_FF_TOL*100:.0f}%)."
    )


# ── Assertion C (root-cause guard): every fixed ModelSpec renders the sign-matched up-Yukawa
@pytest.mark.parametrize("spec_path", _SIGN_FIXED_SPECS, ids=lambda p: p.name)
def test_modelspec_up_yukawa_has_leading_minus(spec_path):
    """Each fixed ModelSpec must carry the up-Yukawa as '-Yu H.u.q' (leading
    minus), matching the down-type sign so the exported h-quark couplings are all
    −m_q/v. Dropping the minus is the root cause of the σ_SI sign bug. The fix
    landed in three specs, so all three are guarded here — this is the byte-check
    the golden validation never made (T3 blind spot)."""
    text = spec_path.read_text()
    assert "-Yu H.u.q" in text, (
        f"{spec_path.name} up-Yukawa term is not '-Yu H.u.q' — the leading "
        f"minus that keeps up/down Higgs–quark couplings same-sign is missing. "
        f"This collapses tree σ_SI ~200× and fakes isospin violation."
    )
    # And it must NOT carry the bugged unsigned form as an active term.
    assert "'Yu H.u.q'" not in text and '"Yu H.u.q"' not in text, (
        f"{spec_path.name} still contains an unsigned 'Yu H.u.q' term."
    )


# ── Sanity: the guard genuinely fails on a reverted sign fix ───────────────────
def test_guard_would_fail_on_reverted_sign():
    """Prove the guard has teeth: fed the OLD sign-bug record (σ_SI(p)=3.7098e-47,
    p/n=8.172), both assertions must trip. This is the revert-detection contract."""
    anchor = _load_anchor()
    anchor_p = anchor.sigma_SI_higgs_portal(m_chi=_M_CHI, y_h_chi_chi=_Y_H_CHI_CHI)

    old_sigma_p = 3.7098e-47
    old_pn = 8.172

    lo, hi = _PN_BAND
    assert not (lo <= old_pn <= hi), "guard would MISS the old p/n=8.17"

    rel = abs(old_sigma_p / anchor_p - 1.0)
    assert rel > _FF_TOL, "guard would MISS the old σ_SI=3.7098e-47"
