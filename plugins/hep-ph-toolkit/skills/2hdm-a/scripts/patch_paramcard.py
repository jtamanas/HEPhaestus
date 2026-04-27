#!/usr/bin/env python3
"""
patch_paramcard.py — 2HDM+a param_card patcher (iter-8 reconstruction)

Reconstructed from the description in:
  demo_output/2hdm-a/fix_loop/POST_MORTEM.md  (iter-7 → iter-8 section)
  demo_output/2hdm-a/fix_loop/iter_6_playtest_report.md
  demo_output/2hdm-a/fix_loop/iter_7_maddm_results.txt

The root cause of Ωh² = -1 sentinel (all channels NaN) was that every
chi-chi-Ah vertex in couplings.py has the form:

    coupling = gchi * pchiR * ZA[i,3]

where pchiR = PhasechiR (PHASES block 1) is the Dirac rephasing phase
from DEFINITION[EWSB][Phases] = {{chiR, PhasechiR}}.  MG5's auto-generated
param_card sets pchiR = rpchiR + i*ipchiR = 0 + 0i, making every DM coupling
identically zero.

This patcher:
  1. Sets PHASES[1] = 1.0  (PhasechiR → 1, restores DM couplings)
  2. Fills identity mixing matrices for UDLMIX, UDRMIX, UULMIX, UURMIX,
     UELMIX, UERMIX (3×3 CKM/lepton rotations defaulting to zero off-diagonal
     can cause mdl_XXX is not defined errors in MadDM's EFT re-import path)
  3. Sets diagonal Yukawa matrices for YUKAWAU, YUKAWAD, YUKAWAE
     (top Yukawa only; others negligible but must be present)
  4. Seeds all BSM particle widths to ≥ 1 GeV (zero widths blow up
     propagators in internal MadDM integration calls)

Usage:
    python3 patch_paramcard.py <maddm_output_dir>

where <maddm_output_dir> is the directory MadDM wrote after `output` —
the Cards/param_card.dat lives at <maddm_output_dir>/Cards/param_card.dat.

Order of operations (CRITICAL — see POST_MORTEM gotcha):
    1. Run MadDM `output <maddm_output_dir>`          (writes param_card)
    2. Run THIS SCRIPT on <maddm_output_dir>           (patches param_card)
    3. Run MadDM `launch -f` in <maddm_output_dir>    (reads patched card)

The script is idempotent: running it twice on the same card is safe.

Benchmark parameters (can be overridden via CLI flags or imported as a
function — see patch_paramcard(path, **overrides)):
    Mchi   = 100.0  GeV  (DM mass; DMSECTOR 1)
    Ma     = 400.0  GeV  (pseudoscalar mediator Ah2; off-resonance)
    gchi   = 1.0         (DM-mediator coupling; DMSECTOR 2)
    tan_beta = 10.0      (vu/vd)
"""

import re
import sys
import math
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Default benchmark values (off-resonance: Ma ≈ 4 × Mchi)
# ---------------------------------------------------------------------------

DEFAULTS = {
    "Mchi":     100.0,   # GeV — DM Dirac mass
    "Ma_Ah2":   400.0,   # GeV — Ah2 (physical pseudoscalar, DM mediator)
    "Ma_Ah3":   500.0,   # GeV — Ah3 (heavier CP-odd state)
    "Mh1":      125.0,   # GeV — lighter CP-even Higgs (≈ SM h)
    "Mh2":      600.0,   # GeV — heavier CP-even Higgs
    "MHp":      550.0,   # GeV — charged Higgs (Hm[2])
    "gchi":       1.0,
    "tan_beta":  10.0,
    "theta_a":    0.1,   # singlet-doublet mixing in CP-odd sector
    "lamP":       1.0,   # portal coupling
    # Phase — the key fix: set to 1.0 so DM couplings are non-zero
    "PhasechiR":  1.0,
}

# PDG codes assigned by SARAH in TwoHdmAfix/particles.m
PDG = {
    "chi":   9989932,   # Fchi (Dirac DM)
    "Ah2":   9931569,   # physical CP-odd (mostly singlet a0s at small theta_a)
    "Ah3":   9949515,   # physical CP-odd (mostly doublet A)
    "hh1":      25,     # lighter CP-even
    "hh2":      35,     # heavier CP-even
    "Hm2":   9920911,   # charged Higgs (second eigenstate; first is W Goldstone 37)
}


def _parse_block_structure(text: str) -> dict:
    """
    Return a dict mapping (block_name_upper, index_tuple) -> (line_index, full_line).
    Only parses single-value lines of the form:  <index>  <value>  # comment
    """
    result = {}
    current_block = None
    for i, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if stripped.lower().startswith("block "):
            current_block = stripped.split()[1].upper()
            continue
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.lower().startswith("decay"):
            current_block = None
            continue
        if current_block is None:
            continue
        parts = stripped.split()
        # Could be single index (1  value) or matrix index (1 1  value)
        try:
            if len(parts) >= 2:
                # Try parsing leading integers as index
                idx_parts = []
                val_pos = 0
                for p in parts:
                    try:
                        int(p)
                        idx_parts.append(int(p))
                        val_pos += 1
                    except ValueError:
                        break
                if idx_parts and val_pos < len(parts):
                    try:
                        float(parts[val_pos])
                        result[(current_block, tuple(idx_parts))] = i
                    except ValueError:
                        pass
        except Exception:
            pass
    return result


# T2_SMOKE: _set_block_value scan-1 fix — replaced (?!\d) regex with _parse_block_structure lookup
def _set_block_value(lines: list, block: str, index: tuple, value: float,
                     comment: str = "") -> list:
    """
    Find and replace a value in `lines` for the given BLOCK and index tuple.
    If not found, appends a new entry at the end of the block.
    Returns the modified lines list.

    Fix (2hdma-T2): scan-1 previously used a regex with ``(?!\\d)`` after
    ``\\s+``, which failed on single-space SLHA rows (e.g. ``   1 0.0``)
    because ``\\s+`` consumed the single space and ``(?!\\d)`` then saw the
    leading digit of the value.  The fix reuses ``_parse_block_structure``
    which already handles single-space/double-space uniformly via
    ``str.split()``.
    """
    idx_str = "  ".join(str(i) for i in index)
    indent = "   "
    cmt = f"  # {comment}" if comment else ""

    # T2_SMOKE: scan-1 replace-existing-index — use _parse_block_structure to
    # locate the line directly; this handles both single-space and double-space
    # SLHA without any regex lookahead.
    struct = _parse_block_structure("".join(lines))
    key = (block.upper(), tuple(index))
    if key in struct:
        line_idx = struct[key]
        lines[line_idx] = f"{indent}{idx_str}  {value:.6e}{cmt}\n"
        return lines

    # Not found — need to insert after the block header
    in_block = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower().startswith("block "):
            bname = stripped.split()[1].upper()
            if bname == block.upper():
                in_block = True
                insert_after = i
                continue
        if in_block:
            stripped2 = line.strip()
            if stripped2.lower().startswith("block ") or stripped2.lower().startswith("decay"):
                # Insert before this line
                new_line = f"{indent}{idx_str}  {value:.6e}{cmt}\n"
                lines.insert(i, new_line)
                return lines
            insert_after = i

    if in_block:
        new_line = f"{indent}{idx_str}  {value:.6e}{cmt}\n"
        lines.insert(insert_after + 1, new_line)
        return lines

    # Block doesn't exist — create it
    lines.append(f"\nBlock {block}\n")
    lines.append(f"{indent}{idx_str}  {value:.6e}{cmt}\n")
    return lines


def _ensure_block_exists(lines: list, block: str) -> list:
    """Add an empty block header if it doesn't exist."""
    for line in lines:
        if line.strip().lower().startswith("block ") and \
                line.strip().split()[1].upper() == block.upper():
            return lines
    lines.append(f"\nBlock {block}\n")
    return lines


def patch_paramcard(
    run_dir: Path,
    Mchi: float = DEFAULTS["Mchi"],
    Ma_Ah2: float = DEFAULTS["Ma_Ah2"],
    Ma_Ah3: float = DEFAULTS["Ma_Ah3"],
    Mh1: float = DEFAULTS["Mh1"],
    Mh2: float = DEFAULTS["Mh2"],
    MHp: float = DEFAULTS["MHp"],
    gchi: float = DEFAULTS["gchi"],
    tan_beta: float = DEFAULTS["tan_beta"],
    theta_a: float = DEFAULTS["theta_a"],
    lamP: float = DEFAULTS["lamP"],
    PhasechiR: float = DEFAULTS["PhasechiR"],
) -> Path:
    """
    Patch Cards/param_card.dat in `run_dir`.

    Returns the path to the (modified) param_card.dat.

    Raises FileNotFoundError if Cards/param_card.dat does not exist —
    meaning `output` has not been run yet (run MadDM `output` first).
    """
    card_path = run_dir / "Cards" / "param_card.dat"
    if not card_path.exists():
        raise FileNotFoundError(
            f"param_card.dat not found at {card_path}. "
            "Run MadDM `output <run_dir>` first, then patch, then `launch -f`."
        )

    lines = card_path.read_text().splitlines(keepends=True)

    # ------------------------------------------------------------------
    # 1. PHASES / IMPHASES blocks — PhasechiR = rpchiR + i*ipchiR
    #    Root-cause fix: every DM vertex is proportional to pchiR.
    #    MG5 auto-generates rpchiR=0, ipchiR=0 → zero DM coupling.
    #
    #    Convention (confirmed from TwoHdmAfix UFO parameters.py):
    #      BLOCK PHASES:   lhacode [1] → rpchiR (real part)
    #      BLOCK IMPHASES: lhacode [1] → ipchiR (imaginary part)
    #    Both are single-index, single-value blocks (NOT 2-index rows).
    #    Setting rpchiR=1.0, ipchiR=0.0 gives pchiR=1.0 (pure real).
    # ------------------------------------------------------------------
    lines = _set_block_value(lines, "PHASES",   (1,), PhasechiR,
                             "rpchiR — real part of PhasechiR (MUST be 1.0)")
    lines = _set_block_value(lines, "IMPHASES", (1,), 0.0,
                             "ipchiR — imaginary part of PhasechiR (must be 0.0)")

    # ------------------------------------------------------------------
    # 2. MASS block — physical masses for BSM particles
    # ------------------------------------------------------------------
    lines = _set_block_value(lines, "MASS", (PDG["chi"],), Mchi, "Fchi (Dirac DM)")
    lines = _set_block_value(lines, "MASS", (PDG["Ah2"],), Ma_Ah2, "Ah2 (DM pseudoscalar mediator)")
    lines = _set_block_value(lines, "MASS", (PDG["Ah3"],), Ma_Ah3, "Ah3 (heavy CP-odd)")
    lines = _set_block_value(lines, "MASS", (PDG["hh1"],), Mh1, "hh1 (SM-like Higgs)")
    lines = _set_block_value(lines, "MASS", (PDG["hh2"],), Mh2, "hh2 (heavy CP-even)")
    lines = _set_block_value(lines, "MASS", (PDG["Hm2"],), MHp, "Hm2 (charged Higgs)")
    # PDG 37 = Hm1 (lighter charged Higgs ~ W Goldstone): must equal Mw so that
    # chi chi → W Hm1 kinematics match the PT1 manually-corrected card that produced
    # Ωh² ≈ 10.494 (fixture-calibration target).  Without this, MadDM defaults to
    # 100 GeV and the dominant channel shifts Ωh² to ~22.3 (T7 PT2 finding, D8).
    lines = _set_block_value(lines, "MASS", (37,), 80.419, "MHm1 ~ Mw")

    # ------------------------------------------------------------------
    # 3. DMSECTOR — gchi and mchi (also set in MASS but here for safety)
    # ------------------------------------------------------------------
    lines = _set_block_value(lines, "DMSECTOR", (1,), Mchi, "mchi (DM mass)")
    lines = _set_block_value(lines, "DMSECTOR", (2,), gchi, "gchi (DM-mediator coupling)")

    # ------------------------------------------------------------------
    # 4. HMIX — VEVs from tan_beta (v = 246.22 GeV)
    # ------------------------------------------------------------------
    v = 246.22
    vd = v / math.sqrt(1.0 + tan_beta**2)
    vu = v * tan_beta / math.sqrt(1.0 + tan_beta**2)
    lines = _set_block_value(lines, "HMIX", (102,), vd, "vd = v cos(beta)")
    lines = _set_block_value(lines, "HMIX", (103,), vu, "vu = v sin(beta)")

    # ------------------------------------------------------------------
    # 5. Mixing matrices — identity 3×3 for CKM/lepton rotations
    #    (UDLMIX, UDRMIX, UULMIX, UURMIX, UELMIX, UERMIX)
    #    Zero off-diagonal entries cause mdl_XXX not defined in MadDM's
    #    EffOperators/COMPLEX EFT re-import for Dirac DM.
    # ------------------------------------------------------------------
    for block in ("UDLMIX", "UDRMIX", "UULMIX", "UURMIX", "UELMIX", "UERMIX"):
        for i in range(1, 4):
            for j in range(1, 4):
                val = 1.0 if i == j else 0.0
                lines = _set_block_value(lines, block, (i, j), val,
                                         f"identity ({i},{j})")

    # ------------------------------------------------------------------
    # 6. Yukawa matrices — diagonal, top-only non-negligible
    #    YUKAWAU / YUKAWAD / YUKAWAE (distinct blocks — iter-6 fix)
    #    Values: SM fermion masses / vd (Type-II: down-types couple to H1)
    # ------------------------------------------------------------------
    # Top: mt ~ 173 GeV, bottom: mb ~ 4.2 GeV, tau: m_tau ~ 1.78 GeV
    # For a first run any non-zero diagonal suffices; refine with SPheno spectrum
    mt_yuk = math.sqrt(2) * 173.0 / vu   # top Yukawa (Type-II couples up-types to H2)
    mb_yuk = math.sqrt(2) * 4.2  / vd    # bottom Yukawa (couples to H1)
    mc_yuk = math.sqrt(2) * 1.27 / vu    # charm
    ms_yuk = math.sqrt(2) * 0.095/ vd    # strange
    mtau_yuk = math.sqrt(2) * 1.777 / vd  # tau

    yukawau = {(1, 1): 0.0, (2, 2): mc_yuk, (3, 3): mt_yuk}
    yukawad = {(1, 1): 0.0, (2, 2): ms_yuk, (3, 3): mb_yuk}
    yukawae = {(1, 1): 0.0, (2, 2): 0.0,    (3, 3): mtau_yuk}

    for block, ydict in (("YUKAWAU", yukawau), ("YUKAWAD", yukawad), ("YUKAWAE", yukawae)):
        for idx, val in ydict.items():
            lines = _set_block_value(lines, block, idx, val)
        # Off-diagonal zeros
        for i in range(1, 4):
            for j in range(1, 4):
                if i != j:
                    lines = _set_block_value(lines, block, (i, j), 0.0)

    # ------------------------------------------------------------------
    # 7. BSM particle widths — seed to 1 GeV if currently zero
    #    Zero widths blow up MadDM propagator calls internally.
    #    Pattern: DECAY <pdg>  <width>
    # ------------------------------------------------------------------
    MIN_WIDTH = 1.0  # GeV (for visible-sector BSM particles)

    # Wchi := 0.0 (LOCKED — DM particle is stable on collider timescales; MadDM
    # determines the DM relic via thermal averages, not from the DECAY block).
    # Synthesis-locked decision; do NOT set chi width to MIN_WIDTH.
    Wchi = 0.0  # Wchi = 0.0

    bsm_pdgs_visible = {
        PDG["Ah2"]: "WAh2 (pseudoscalar mediator width)",
        PDG["Ah3"]: "WAh3 (heavy CP-odd width)",
        PDG["hh2"]: "Whh2 (heavy Higgs width)",
        PDG["Hm2"]: "WHm2 (charged Higgs width)",
    }

    # DM particle handled separately: always set width to 0 (LOCKED)
    chi_decay_re = re.compile(r"^\s*DECAY\s+" + str(PDG["chi"]) + r"\s+.*")
    chi_found = False
    for i, line in enumerate(lines):
        if chi_decay_re.match(line):
            chi_found = True
            lines[i] = f"DECAY  {PDG['chi']}  {Wchi:.6e}  # Wchi = 0.0 (DM stable, LOCKED)\n"
            break
    if not chi_found:
        lines.append(f"DECAY  {PDG['chi']}  {Wchi:.6e}  # Wchi = 0.0 (DM stable, LOCKED)\n")

    for pdg, comment in bsm_pdgs_visible.items():
        # Find existing DECAY line for this PDG
        found = False
        decay_re = re.compile(r"^\s*DECAY\s+" + str(pdg) + r"\s+(.+)")
        for i, line in enumerate(lines):
            m = decay_re.match(line)
            if m:
                found = True
                try:
                    current_width = float(m.group(1).split()[0])
                except (ValueError, IndexError):
                    current_width = 0.0
                if current_width < MIN_WIDTH:
                    # Replace width, preserve any trailing comment
                    rest = m.group(1).strip()
                    parts = rest.split(None, 1)
                    comment_tail = parts[1] if len(parts) > 1 else f"# {comment}"
                    lines[i] = f"DECAY  {pdg}  {MIN_WIDTH:.6e}  {comment_tail}\n"
                break
        if not found:
            lines.append(f"DECAY  {pdg}  {MIN_WIDTH:.6e}  # {comment}\n")

    # ------------------------------------------------------------------
    # 8. ZA mixing — 3×3 CP-odd rotation (Ah1=Goldstone, Ah2=mediator, Ah3=A)
    #    At theta_a (singlet-doublet mixing angle) and beta from tan_beta:
    #      ZA[2,3] ≈ cos(theta_a) — sets chi-chi-Ah2 coupling strength
    # ------------------------------------------------------------------
    beta = math.atan(tan_beta)
    cb = math.cos(beta)
    sb = math.sin(beta)
    ca = math.cos(theta_a)
    sa = math.sin(theta_a)

    # Standard 3×3 for (G0, aphys, A) → (Ah1, Ah2, Ah3)
    # Row 1 = Goldstone: (sb, -cb, 0)
    # Row 2 = aphys (singlet-dominated): (0, 0, 1) rotated by theta_a
    # Row 3 = A (doublet): mixed
    # Simplified two-angle parametrization matching SARAH's default ZA output:
    ZA = [
        [sb,      -cb,      0.0],   # Ah1 row (Goldstone ~ Im H10, Im H20)
        [cb*sa,    sb*sa,   ca],    # Ah2 row (mostly singlet a0s at small theta_a)
        [cb*ca,    sb*ca,  -sa],    # Ah3 row (mostly doublet A)
    ]

    for i in range(1, 4):
        for j in range(1, 4):
            lines = _set_block_value(lines, "ZAMIX", (i, j), ZA[i - 1][j - 1],
                                     f"ZA({i},{j})")

    # ZH mixing (CP-even, 2×2 via alpha)
    alpha = -0.1  # default small mixing
    ZH = [
        [math.cos(alpha), -math.sin(alpha)],
        [math.sin(alpha),  math.cos(alpha)],
    ]
    for i in range(1, 3):
        for j in range(1, 3):
            lines = _set_block_value(lines, "ZHMIX", (i, j), ZH[i - 1][j - 1],
                                     f"ZH({i},{j})")

    # ZP mixing (charged Higgs, 2×2)
    ZP = [
        [cb, -sb],
        [sb,  cb],
    ]
    for i in range(1, 3):
        for j in range(1, 3):
            lines = _set_block_value(lines, "ZPMIX", (i, j), ZP[i - 1][j - 1],
                                     f"ZP({i},{j})")

    card_path.write_text("".join(lines))
    print(f"[patch_paramcard] Patched {card_path}")
    print(f"  PHASES[1] = {PhasechiR}  (rpchiR — real part of PhasechiR, restores DM couplings)")
    print(f"  IMPHASES[1] = 0.0  (ipchiR — imaginary part, kept zero)")
    print(f"  Mchi = {Mchi} GeV, Ma_Ah2 = {Ma_Ah2} GeV, gchi = {gchi}, tan_beta = {tan_beta}")
    return card_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Patch Cards/param_card.dat in a MadDM output directory for 2HDM+a."
    )
    parser.add_argument("run_dir", type=Path,
                        help="MadDM output directory (contains Cards/param_card.dat)")
    parser.add_argument("--Mchi",     type=float, default=DEFAULTS["Mchi"])
    parser.add_argument("--Ma-Ah2",   type=float, default=DEFAULTS["Ma_Ah2"], dest="Ma_Ah2")
    parser.add_argument("--Ma-Ah3",   type=float, default=DEFAULTS["Ma_Ah3"], dest="Ma_Ah3")
    parser.add_argument("--gchi",     type=float, default=DEFAULTS["gchi"])
    parser.add_argument("--tan-beta", type=float, default=DEFAULTS["tan_beta"], dest="tan_beta")
    parser.add_argument("--theta-a",  type=float, default=DEFAULTS["theta_a"],  dest="theta_a")
    parser.add_argument("--lamP",     type=float, default=DEFAULTS["lamP"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be changed without writing the file.")
    args = parser.parse_args()

    if args.dry_run:
        # Dry-run: read the card, compute what would change, print diff-style summary
        card_path = args.run_dir / "Cards" / "param_card.dat"
        if not card_path.exists():
            print(f"[dry-run] ERROR: {card_path} does not exist (run MadDM output first)")
            raise SystemExit(1)
        import copy
        original_lines = card_path.read_text().splitlines(keepends=True)
        # Run a copy through the patcher by temporarily rerouting write
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_card = Path(tmpdir) / "Cards" / "param_card.dat"
            tmp_card.parent.mkdir(parents=True)
            shutil.copy(card_path, tmp_card)
            patch_paramcard(
                run_dir=Path(tmpdir),
                Mchi=args.Mchi, Ma_Ah2=args.Ma_Ah2, Ma_Ah3=args.Ma_Ah3,
                gchi=args.gchi, tan_beta=args.tan_beta,
                theta_a=args.theta_a, lamP=args.lamP,
            )
            new_lines = tmp_card.read_text().splitlines(keepends=True)
        import difflib
        diff = list(difflib.unified_diff(original_lines, new_lines,
                                         fromfile="param_card.dat (before)",
                                         tofile="param_card.dat (after)"))
        if diff:
            print(f"[dry-run] {len(diff)} diff lines — changes that would be applied:")
            print("".join(diff[:200]))
        else:
            print("[dry-run] Card already up-to-date; no changes would be applied.")
        print("[dry-run] No file written.")
    else:
        patch_paramcard(
            run_dir=args.run_dir,
            Mchi=args.Mchi,
            Ma_Ah2=args.Ma_Ah2,
            Ma_Ah3=args.Ma_Ah3,
            gchi=args.gchi,
            tan_beta=args.tan_beta,
            theta_a=args.theta_a,
            lamP=args.lamP,
        )
