"""
compile_model.py — Stage 1 of /spheno-build: compile a model-specific SPheno binary.

Usage:
    python3 compile_model.py <model_name> [--force]

Steps:
    1. Read config for spheno_src_path, sarah_version, spheno_version.
    2. Compute cache key: sha256(spec.yaml) + "=" + sarah_version + "+" + spheno_version.
    3. If cache key matches and binary exists (and not --force): return cached.
    4. Copy SARAH Fortran sources into <spheno_src_path>/<SarahName>/.
    5. Run make -C <spheno_src_path> Model=<SarahName> -j<cpu_count>.
    6. On failure: emit SPHENO_COMPILE_FAILED fatal blocker.
    7. Move binary to model spheno_bin dir. Write cache key.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — resolve shared helpers relative to this script location.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_CONFIG_HELPERS = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers" / "config_helpers.py"

# Dynamic import of config_helpers (may live in shared or be absent pre-W0 merge).
import importlib.util as _ilu

def _load_config_helpers():
    for candidate in [_CONFIG_HELPERS]:
        if candidate.exists():
            spec = _ilu.spec_from_file_location("config_helpers", candidate)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise ImportError(
        f"config_helpers.py not found; expected at {_CONFIG_HELPERS}. "
        "Ensure W0 is merged."
    )


def _load_sarah_name():
    candidate = _SHARED_DIR / "sarah_name.py"
    if not candidate.exists():
        raise ImportError(f"sarah_name.py not found at {candidate}. Ensure W0 is merged.")
    spec = _ilu.spec_from_file_location("sarah_name", candidate)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _emit_fatal(code: str, message: str, context: dict | None = None) -> None:
    blocker: dict = {"code": code, "mode": "fatal", "message": message}
    if context:
        blocker["context"] = context
    print(json.dumps(blocker), file=sys.stderr)


def _last_n_lines(text: str, n: int = 40) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-n:])


# ---------------------------------------------------------------------------
# Post-SARAH patches applied to the copied model source tree.
# See demo_output/singlet-doublet/report.md (2026-04-21) for the diagnosis
# that motivated both helpers.
# ---------------------------------------------------------------------------

def _patch_darwin_ar(spheno_model_src: Path) -> int:
    """Rewrite ``ar -ruc -U`` → ``ar -ruc`` in the per-model Makefile on Darwin.

    SARAH's per-model Makefile (``<SPheno>/<Model>/Makefile``) hard-codes
    ``ar -ruc -U`` in its ``.f90.a`` / ``.F90.a`` suffix rules and does not
    branch on ``uname -s`` (unlike ``SPheno-4.0.5/src/Makefile``, which does).
    macOS's Xcode ``ar`` does not accept ``-U`` and fails the archive step.
    Idempotent; no-op on non-Darwin.
    """
    if platform.system() != "Darwin":
        return 0
    makefile = spheno_model_src / "Makefile"
    if not makefile.exists():
        return 0
    text = makefile.read_text()
    count = text.count("ar -ruc -U")
    if count == 0:
        return 0
    makefile.write_text(text.replace("ar -ruc -U", "ar -ruc"))
    return count


_NOTPARALLEL_MARKER = "# hephaestus: serialize intra-model compile (Fortran .mod ordering)"


def _patch_notparallel(spheno_model_src: Path) -> bool:
    """Insert ``.NOTPARALLEL:`` at the top of the per-model Makefile.

    SARAH's per-model Makefile lists archive members as prerequisites without
    declaring inter-file Fortran ``.mod`` dependencies, so a parallel ``make
    -jN`` can start compiling e.g. ``RGEs_<Model>.f90`` before
    ``Model_Data_<Model>.mod`` has been written to ``../include``, and the
    dependent compile fails with "Cannot open module file". ``.NOTPARALLEL:``
    serializes the targets in *this* Makefile without affecting the parent
    SPheno ``src/Makefile``, which keeps its parallel speedup. Idempotent:
    detects a sentinel marker line and re-inserts nothing on a second call.
    """
    makefile = spheno_model_src / "Makefile"
    if not makefile.exists():
        return False
    text = makefile.read_text()
    if _NOTPARALLEL_MARKER in text:
        return False
    makefile.write_text(f"{_NOTPARALLEL_MARKER}\n.NOTPARALLEL:\n\n{text}")
    return True


_REAL_DECL_RE = re.compile(r"^\s*Real\(dp\)\s*::\s*(.+?)\s*$", re.IGNORECASE)
_IDENT_RE = re.compile(r"([A-Za-z]\w*)")
_CONTAINS_RE = re.compile(r"^\s*Contains\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Rank-1 Dirac-single-eigenstate normalisation.
#
# SARAH 4.15.3 emits an inconsistent shape for single-eigenstate Dirac
# mass variables (e.g. the singlet-doublet charged fermion ``MFChiM``):
# ``Calculate<Name>`` / ``Calculate<Name>EffPot`` subroutine bodies
# declare ``Real(dp), Intent(out) :: MFChiM(1)`` (rank-1, length-1),
# and ``OneLoop<Name>`` / its module-level ``MFChiM_1L(1)`` cache do the
# same, while every caller — ``TreeMasses``, ``TreeMassesEffPot``,
# ``LoopMasses``, ``Boundaries_*``, ``TreeLevel_Decays_*``, etc. and the
# module-level ``Model_Data_<Name>.f90`` — declares ``MFChiM`` as a
# scalar. gfortran rejects the callsite as ``Rank mismatch in argument
# 'mfchim' at (1) (rank-1 and scalar)``. See docs/devlog.md 2026-04-22
# for the full diagnosis; Option A (ii) in the task brief is implemented
# here.
#
# The patch demotes rank-1 to scalar *only* for mass names whose
# module-level declaration in ``Model_Data_<Name>.f90`` is scalar, which
# restricts the rewrite to genuine single-eigenstate Dirac pairs. For
# those names it rewrites:
#   - ``Real(dp), Intent(out) :: <name>(1)`` → ``Real(dp), Intent(out) :: <name>``
#     (in ``Calculate<name>``, ``Calculate<name>EffPot``, ``OneLoop<name>``).
#   - ``Real(dp), Private :: <name>_1L(1), <name>2_1L(1)`` → scalar
#     (module-level cache in ``LoopMasses_<Model>.f90``).
#   - ``Real(dp), Intent(out) :: <name>_1L(1), <name>2_1L(1)`` → scalar
#     (``OneLoop<name>`` output) and the paired indexed uses
#     ``<name>2_1L(il)`` → ``<name>2_1L``, ``<name>_1L(il)`` → ``<name>_1L``.
#   - ``<name> = Sqrt( <name>2 )`` → ``<name> = Sqrt( <name>2(1) )`` for
#     the scalar-from-rank-1 assignment at the tail of each Calculate
#     body (``<name>2`` stays rank-1 because ``EigenSystem`` needs a
#     vector).
#   - ``If (<name>(1).Gt.`` guards in ``InputOutput_<Model>.f90`` →
#     ``If (<name>.Gt.`` (these reference the module-scalar ``<name>``).
#
# Idempotent: on a second run the regexes find nothing to rewrite because
# the ``(1)`` suffix is gone. Logged: the hook returns a dict naming the
# affected files and which mass variables were demoted; the caller
# writes that into ``make.log`` before invoking ``make``.
# ---------------------------------------------------------------------------

# Module-level scalar decl in ``Model_Data_<Name>.f90`` looks like
# ``Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),…``.
# A name is "scalar-at-module-level" iff it appears in that grouped decl
# without a trailing ``(…)``.
_MASS_TOKEN_RE = re.compile(r"([A-Za-z]\w*)(?!\w)(?!\()")


def _module_scalar_mass_names(spheno_model_src: Path, sarah_name: str) -> set[str]:
    """Return mass names declared as scalar in ``Model_Data_<Name>.f90``.

    Walks the module-spec section (up to the first ``Contains``) of
    ``Model_Data_<Name>.f90`` and returns the set of ``MF*`` identifiers
    that are declared without a trailing ``(…)`` extent — i.e., genuine
    scalars. Used as the safety filter for the rank-1 Dirac normaliser
    so we never demote a legitimate rank-1 mass vector (``MFChi(3)``).
    """
    path = spheno_model_src / f"Model_Data_{sarah_name}.f90"
    if not path.exists():
        return set()
    scalar_masses: set[str] = set()
    for line in path.read_text().splitlines():
        if _CONTAINS_RE.match(line):
            break
        m = _REAL_DECL_RE.match(line.rstrip())
        if not m:
            continue
        payload = m.group(1).rstrip("&").rstrip()
        for tok in payload.split(","):
            tok = tok.strip()
            if "(" in tok:
                continue
            name_match = _IDENT_RE.match(tok)
            if name_match and name_match.group(1).startswith("MF"):
                scalar_masses.add(name_match.group(1))
    return scalar_masses


def _patch_rank1_dirac_mass(
    spheno_model_src: Path, sarah_name: str
) -> dict[str, list[str]]:
    """Demote rank-1 length-1 Intent(out) masses to scalar to match callers.

    Scans the four Fortran files where SARAH emits the mismatched
    declarations (``TreeLevelMasses_<Name>.f90``, ``LoopMasses_<Name>.f90``,
    ``InputOutput_<Name>.f90``) and rewrites the specific shapes listed in
    the module docstring above. Only mass names whose module-level decl
    is scalar (per ``_module_scalar_mass_names``) are touched.

    Returns a dict mapping file base name → list of mass names patched
    there (one entry per file that changed; empty dict on no-op).
    """
    scalar_masses = _module_scalar_mass_names(spheno_model_src, sarah_name)
    if not scalar_masses:
        return {}

    patched: dict[str, list[str]] = {}

    def _apply(path: Path, mass: str, transforms: list[tuple[str, str]]) -> bool:
        if not path.exists():
            return False
        text = path.read_text()
        new_text = text
        for pat, repl in transforms:
            new_text = re.sub(pat, repl, new_text)
        if new_text == text:
            return False
        path.write_text(new_text)
        return True

    tlm = spheno_model_src / f"TreeLevelMasses_{sarah_name}.f90"
    lm = spheno_model_src / f"LoopMasses_{sarah_name}.f90"
    io = spheno_model_src / f"InputOutput_{sarah_name}.f90"

    for mass in sorted(scalar_masses):
        mass_e = re.escape(mass)
        mass2 = f"{mass}2"
        mass2_e = re.escape(mass2)

        # --- TreeLevelMasses: Calculate<Mass> + Calculate<Mass>EffPot ---
        # Only rewrite if the file actually contains the ``MFChiM(1)``
        # Intent(out) shape; otherwise ``MFChi(3)`` etc. would be reached
        # by the name-only filter.
        if tlm.exists() and re.search(
            rf"Real\(dp\),\s*Intent\(out\)\s*::\s*{mass_e}\(1\)", tlm.read_text()
        ):
            changed = _apply(
                tlm,
                mass,
                [
                    (
                        rf"Real\(dp\),\s*Intent\(out\)\s*::\s*{mass_e}\(1\)",
                        f"Real(dp), Intent(out) :: {mass}",
                    ),
                    # ``<name> = Sqrt( <name>2 )`` tail assignment: rewrite the
                    # RHS so scalar LHS matches rank-1 RHS element.
                    (
                        rf"(^|\n)(\s*){mass_e}\s*=\s*Sqrt\(\s*{mass2_e}\s*\)",
                        rf"\1\2{mass} = Sqrt( {mass2}(1) )",
                    ),
                ],
            )
            if changed:
                patched.setdefault(tlm.name, []).append(mass)

        # --- LoopMasses: OneLoop<Mass> Intent(out) + module Private cache ---
        if lm.exists():
            text = lm.read_text()
            touched = False
            new = text

            # Module-level ``Real(dp), Private :: <mass>_1L(1), <mass>2_1L(1)``.
            private_re = re.compile(
                rf"Real\(dp\),\s*Private\s*::\s*{mass_e}_1L\(1\)\s*,\s*{mass2_e}_1L\(1\)"
            )
            if private_re.search(new):
                new = private_re.sub(
                    f"Real(dp), Private :: {mass}_1L, {mass2}_1L", new
                )
                touched = True

            # ``OneLoop<mass>`` Intent(out) decl.
            intent_re = re.compile(
                rf"Real\(dp\),\s*Intent\(out\)\s*::\s*{mass_e}_1L\(1\)\s*,\s*{mass2_e}_1L\(1\)"
            )
            if intent_re.search(new):
                new = intent_re.sub(
                    f"Real(dp), Intent(out) :: {mass}_1L,{mass2}_1L", new
                )
                touched = True

            # Paired indexing on the now-scalar caches: ``<mass>_1L(il)`` and
            # ``<mass>2_1L(il)`` → unsubscripted. We key off the ``_1L`` suffix
            # so ``<mass>_t(il)`` (genuine rank-1 temp that feeds EigenSystem)
            # is left intact.
            if touched:
                new = re.sub(
                    rf"\b{mass_e}_1L\((?:il|i1|1)\)", f"{mass}_1L", new
                )
                new = re.sub(
                    rf"\b{mass2_e}_1L\((?:il|i1|1)\)", f"{mass2}_1L", new
                )

            if new != text:
                lm.write_text(new)
                patched.setdefault(lm.name, []).append(mass)

        # --- InputOutput: ``If (MFChiM(1).Gt.`` → ``If (MFChiM.Gt.`` ---
        if io.exists():
            text = io.read_text()
            # Only rewrite the guard shape, not the comment string
            # ``"# MFChiM(1) "`` which SARAH uses as an output label.
            new = re.sub(
                rf"(If\s*\(\s*){mass_e}\(1\)(\s*\.\w+\.)",
                rf"\1{mass}\2",
                text,
            )
            if new != text:
                io.write_text(new)
                patched.setdefault(io.name, []).append(mass)

    # --- OneLoopDecays_<Model>.f90: rank-3 self-energy arrays + Transpose ---
    # Same SARAH bug class: for a single-eigenstate Dirac mass ``MF<X>`` the
    # emitter writes ``Sigma*F<X>(1,1,1)`` (rank-3) arrays but the block
    # assigning ``Zf<X>`` expects a scalar — so the assignment looks like
    # ``ZfChiM = -SigmaRFChiM + …`` (rank 0 = rank 3). And the downstream
    # ``MatMul(ZfChiM - Conjg(Transpose(ZfChiM)), UM)`` calls ``Transpose``
    # on a scalar. Fix both by (a) subscripting every ``Sigma*F<X>`` token
    # that follows the assignment chain with ``(1,1,1)``, and (b)
    # rewriting the MatMul/Transpose line to pure scalar arithmetic.
    old = spheno_model_src / f"OneLoopDecays_{sarah_name}.f90"
    if old.exists():
        text = old.read_text()
        new = text
        for mass in sorted(scalar_masses):
            # ``MFChiM`` → field name ``FChiM`` (strip leading M). We only
            # scope to masses whose module-level decl is scalar, so
            # ``FChi`` (rank-3) never reaches this branch.
            if not mass.startswith("MF"):
                continue
            field = mass[1:]  # ``FChiM``
            field_e = re.escape(field)
            # ``Zf<stripped>`` where ``<stripped>`` is the field name minus
            # the leading ``F``. The SM charge-plus partner shows up as
            # ``Zf<stripped with M→P>`` (``ZfChiM`` / ``ZfChiP`` for the
            # single-eigenstate Dirac pair).
            zf_lh = "Zf" + field[1:]  # ``ZfChiM``
            zf_rh = zf_lh[:-1] + "P" if zf_lh.endswith("M") else None

            # Sanity-check that the rank-3 shape is actually emitted before
            # touching anything; absent shape → no-op, just like the
            # TreeLevelMasses guard above.
            if not re.search(rf"Sigma(?:L|R|SL|SR)F{field_e[1:]}\(1,1,1\)", new):
                # ``field_e[1:]`` strips the ``F`` from ``FChiM`` because
                # the Sigma* symbols prefix ``F`` themselves.
                pass  # still fall through — the sub calls below are no-ops
                # if the rank-3 decls never made it into the file.

            # (a) Subscript the rank-3 self-energy variants in scalar
            # assignments. Conservative: rewrite every ``Sigma*F<X>`` /
            # ``DerSigma*F<X>`` occurrence that is NOT already subscripted
            # and does NOT start a declaration (we leave the ``(1,1,1)``
            # in the decl intact — only the body uses need indexing).
            # The shape-safe subset: tokens appearing in a body line that
            # assigns ``Zf<LH>`` / ``Zf<RH>`` on the LHS.
            # Pattern: a line (incl. continuations) that starts with
            # ``Zf<LH> = `` or ``& `` (continuation). We only rewrite
            # ``Sigma`` / ``DerSigma`` identifiers ending in ``F<field>``
            # (possibly with ``DR`` / ``OS`` / ``ir`` infix).
            variants = [zf_lh] + ([zf_rh] if zf_rh else [])
            for zf in variants:
                # Match the whole ``Zf<…> = … `` assignment, including any
                # Fortran ``&`` line-continuations that immediately follow.
                # The block ends when a new line starts with something
                # other than whitespace or the ``&`` continuation marker.
                # We patch each assignment independently so a second pass
                # is a no-op — no token gets ``(1,1,1)`` twice.
                block_re = re.compile(
                    rf"(?ms)^({re.escape(zf)}\s*=\s*.+?\n)(?=^(?!\s*&).|\Z)"
                )

                def _subscript_sigmas(match: re.Match) -> str:
                    body = match.group(1)
                    # Replace every ``Sigma*F<field>`` /
                    # ``DerSigma*F<field>`` token (with optional DR/OS/ir
                    # infix) that is NOT already followed by ``(``.
                    body = re.sub(
                        rf"\b((?:Der)?Sigma(?:SL|SR|L|R)(?:ir)?{field_e}(?:DR|OS)?)\b(?!\()",
                        r"\1(1,1,1)",
                        body,
                    )
                    return body

                new2 = block_re.sub(_subscript_sigmas, new)
                if new2 != new:
                    new = new2

            # (b) Rewrite the scalar-``Zf`` Transpose/MatMul lines to
            # pure scalar arithmetic. For a scalar Z and a 1×1 matrix U,
            # ``MatMul(Z - Conjg(Transpose(Z)), U)`` is equivalent to
            # ``(Z - Conjg(Z)) * U``. gfortran rejects ``Transpose(Z)``
            # because ``Transpose`` requires rank ≥ 2.
            for zf in variants:
                pattern = (
                    rf"MatMul\(\s*{re.escape(zf)}\s*-\s*Conjg\(\s*Transpose\(\s*"
                    rf"{re.escape(zf)}\s*\)\s*\)\s*,\s*(\w+)\s*\)"
                )
                new = re.sub(
                    pattern,
                    rf"({zf} - Conjg({zf})) * \1",
                    new,
                )

        if new != text:
            old.write_text(new)
            patched.setdefault(old.name, []).extend(sorted(scalar_masses))

    # --- BranchingRatios_<Model>.f90: gTF<Name>/gPF<Name>/BRF<Name> typo ---
    # SARAH 4.15.3 emits the post-decay branching-ratio normalisation loop
    # with the wrong identifiers for BSM fermion mass eigenstates: it
    # *declares* the decay widths as ``gTChi(3)`` / ``gTChiM`` / ``BRChi`` /
    # ``BRChiM`` (no ``F`` prefix) and *calls* ``ChiTwoBodyDecay`` with
    # those names, then the trailing ``Do i1=…`` block writes
    # ``gTFChi(i1) = Sum(gPFChi(i1,:))`` — with an extra ``F`` that
    # doesn't match any declaration. gfortran rejects the statement as
    # "Unclassifiable" (no ``Implicit None`` in this file, so ``gTFChi``
    # gets implicit-typed and then the function-call shape doesn't
    # match). The BSM fermion name set is derived by scanning the
    # subroutine's ``gT<Name>`` / ``gP<Name>`` / ``BR<Name>`` declarations
    # and looking for a matching ``gTF<Name>`` in the body. Each mismatch
    # gets the extra ``F`` stripped.
    br = spheno_model_src / f"BranchingRatios_{sarah_name}.f90"
    if br.exists():
        text = br.read_text()
        # Extract BSM eigenstate names from the CalculateBR signature.
        # The trailing ``gPChi,gTChi,BRChi,gPChiM,gTChiM,BRChiM)`` group
        # names them in the Intent(inout) grouped decl at ``Real(dp),
        # Intent(inout) :: … gPhh,gThh,BRhh,gPChi,gTChi,BRChi,gPChiM,…``.
        # We scan for every ``gT<Name>`` that is not one of the SM
        # {Fu, Fe, Fd, hh} set — those are already correct.
        declared_gt = set(re.findall(r"\bgT([A-Z]\w*)\b", text))
        bsm_names: list[str] = []
        for name in sorted(declared_gt):
            if name in {"Fu", "Fe", "Fd", "hh", "VWp", "VZ", "Ah"}:
                continue
            # The bug shape: a bare ``gTF<name>`` (with the extra ``F``)
            # appears in the body but no declaration matches.
            if re.search(rf"\bgTF{re.escape(name)}\b", text):
                bsm_names.append(name)
        if bsm_names:
            for name in bsm_names:
                name_e = re.escape(name)
                # Rewrite every ``gTF<name>``, ``gPF<name>``, ``BRF<name>``
                # and their ``1L`` counterparts to the declared spelling.
                for prefix, repl in [
                    (f"gTF{name_e}", f"gT{name}"),
                    (f"gPF{name_e}", f"gP{name}"),
                    (f"BRF{name_e}", f"BR{name}"),
                    (f"gT1LF{name_e}", f"gT1L{name}"),
                    (f"gP1LF{name_e}", f"gP1L{name}"),
                    (f"BR1LF{name_e}", f"BR1L{name}"),
                ]:
                    text = re.sub(rf"\b{prefix}\b", repl, text)
            br.write_text(text)
            patched.setdefault(br.name, []).extend(bsm_names)

    # --- Boundaries_<Model>.f90: ``<Name>Input`` vs ``<Name>IN`` typo ---
    # SARAH 4.15.3 emits a "LOW" high-scale fallback block that assigns
    # ``MS = MSInput`` / ``MPsi = MPsiInput`` / ``yh1 = yh1Input`` /
    # ``yh2 = yh2Input`` — but the declared module-level input symbols in
    # ``Model_Data_<Name>.f90`` are ``MSIN`` / ``MPsiIN`` / ``yh1IN`` /
    # ``yh2IN`` (no ``put``). gfortran reports ``Symbol '<name>input' has
    # no IMPLICIT type``. Canonicalise to the ``*IN`` form in Boundaries
    # only — other files use a disjoint set of ``*Input`` symbols for
    # SLHA block parsing that we must NOT touch. We derive the affected
    # names from the ``Real(dp) :: g1IN,g2IN,g3IN,yh2IN,yh1IN,MSIN,MPsiIN``
    # grouped decl in Model_Data so the fix stays model-agnostic.
    md = spheno_model_src / f"Model_Data_{sarah_name}.f90"
    if md.exists():
        md_text = md.read_text()
        # Grouped decl like ``Real(dp) :: g1IN,g2IN,g3IN,yh2IN,yh1IN,MSIN,MPsiIN``
        # or ``Complex(dp) :: LamIN,YuIN(3,3),…,m2SMIN``. Pull every
        # identifier that ends in ``IN`` from those lines.
        in_names: set[str] = set()
        for line in md_text.splitlines():
            if _CONTAINS_RE.match(line):
                break
            m = re.match(
                r"^\s*(?:Real|Complex)\(dp\)\s*::\s*(.+?)\s*$",
                line,
            )
            if not m:
                continue
            for tok in m.group(1).split(","):
                tok = tok.strip().rstrip("&").strip()
                ident = _IDENT_RE.match(tok)
                if ident and ident.group(1).endswith("IN"):
                    in_names.add(ident.group(1))

        # Apply the rename in every file where SARAH miswrites the assignment.
        # Observed in ``Boundaries_<Name>.f90`` and the top-level driver
        # ``SPheno<Name>.f90``; paint a wider net in case SARAH sprinkles
        # the same shape elsewhere in future versions.
        for cand in [
            spheno_model_src / f"Boundaries_{sarah_name}.f90",
            spheno_model_src / f"SPheno{sarah_name}.f90",
        ]:
            if not cand.exists():
                continue
            cand_text = cand.read_text()
            cand_new = cand_text
            renamed: list[str] = []
            for in_name in sorted(in_names):
                base = in_name[:-2]
                bad = f"{base}Input"
                bad_re = re.compile(rf"\b{re.escape(bad)}\b")
                if bad_re.search(cand_new):
                    cand_new = bad_re.sub(in_name, cand_new)
                    renamed.append(in_name)
            if renamed:
                cand.write_text(cand_new)
                patched.setdefault(cand.name, []).extend(renamed)

    # --- InputOutput_<Model>.f90: F-prefix inconsistency (both directions) ---
    # For BSM-fermion names (``Chi``, ``ChiM`` in singlet-doublet) SARAH
    # 4.15.3 emits a matching pair of inverted typos in ``LesHouches_Out``:
    #   - The decay-width block guards read ``gTF<Name>`` / ``gT1LF<Name>``
    #     (extra ``F``), but those are never declared — the module-level
    #     symbols in ``Model_Data_<Name>.f90`` are ``gT<Name>`` /
    #     ``gT1L<Name>``. Same shape as the BranchingRatios bug above.
    #   - The PDG / particle-name writes read ``PDG<Name>`` /
    #     ``NameParticle<Name>`` (missing ``F``), but the local decls in
    #     ``LesHouches_Out`` are ``PDGF<Name>`` / ``NameParticleF<Name>``.
    # Both bugs are localised to BSM fermion names — the SM-fermion
    # names ``Fu`` / ``Fe`` / ``Fd`` / ``Fv`` are emitted consistently.
    # We reuse the ``bsm_names`` set discovered from BranchingRatios (it
    # is empty unless that file has already been patched in this run).
    # If BranchingRatios didn't produce a list, scan the InputOutput
    # locally.
    ioo = spheno_model_src / f"InputOutput_{sarah_name}.f90"
    if ioo.exists():
        text = ioo.read_text()
        # Local discovery of BSM fermion names from the locally-declared
        # ``PDGF<Name>`` / ``PDGF<Name>(3)`` decls: anything beyond the SM
        # ``Fu``, ``Fe``, ``Fd``, ``Fv`` set is BSM.
        bsm_io = set()
        for m in re.finditer(r"\bPDGF([A-Z]\w*?)(?:\(|\b)", text):
            n = m.group(1)
            if n not in {"u", "e", "d", "v"}:
                bsm_io.add(n)
        renamed: list[str] = []
        for name in sorted(bsm_io):
            name_e = re.escape(name)
            before = text
            # ``gTF<name>`` → ``gT<name>``; same for 1L counterpart.
            text = re.sub(rf"\bgTF{name_e}\b", f"gT{name}", text)
            text = re.sub(rf"\bgT1LF{name_e}\b", f"gT1L{name}", text)
            # ``PDG<name>`` → ``PDGF<name>`` — but only when not already
            # followed by another capital (``PDGChi`` OK, ``PDGChiM``
            # matched via a separate entry in bsm_io). We guard with a
            # negative lookahead to avoid rewriting a shorter name that
            # is a prefix of a longer BSM name we're also patching.
            longer = [n for n in bsm_io if n != name and n.startswith(name)]
            suffix_block = ""
            if longer:
                # Prevent ``PDGChi`` from matching when the identifier is
                # actually ``PDGChiM`` (``PDGChi`` prefix of ``PDGChiM``).
                # We require the character after the match is NOT an
                # uppercase letter or digit (i.e., the identifier ends).
                suffix_block = "(?![A-Za-z0-9])"
            text = re.sub(
                rf"\bPDG{name_e}{suffix_block}", f"PDGF{name}", text
            )
            text = re.sub(
                rf"\bNameParticle{name_e}{suffix_block}",
                f"NameParticleF{name}",
                text,
            )
            if text != before:
                renamed.append(name)
        if renamed:
            ioo.write_text(text)
            patched.setdefault(ioo.name, []).extend(renamed)

    return patched


def _patch_phasefs_init(spheno_model_src: Path, sarah_name: str) -> bool:
    """Initialise SARAH's ``PhaseFS`` Majorana-phase variable to unit.

    SARAH emits ``PhaseFS = 0._dp`` in ``Set_All_Parameters_0`` inside
    ``Model_Data_<Name>.f90`` and never assigns it from any ``*IN`` block
    (``Read_PHASESIN`` parses the block but discards the values). ``PhaseFS``
    then appears as a prefactor on every singlet/doublet entry of the
    neutralino mass matrix (``mat(1,1) = MS*PhaseFS**2``,
    ``mat(1,2) = -PhaseFS*vvSM*yh2/Sqrt(2)``, ``mat(1,3) = PhaseFS*vvSM*yh1/Sqrt(2)``
    in ``TreeLevelMasses_<Name>.f90``). With ``PhaseFS = 0``, the entire
    Majorana sub-block goes to zero except the off-diagonal MPsi entry,
    producing a spurious spectrum ``(0, MPsi, MPsi)`` regardless of MS /
    yh1 / yh2 / vvSM.

    The physically correct default is ``PhaseFS = 1``; SARAH flips it to
    ``-1`` internally if a mass eigenvalue turns negative (standard
    Majorana sign-convention machinery). Seeding to zero skips that
    machinery entirely. Rewriting the single init line in
    ``Set_All_Parameters_0`` is sufficient — every other call site either
    reads from this variable or mutates it only when a negative-mass
    ambiguity needs resolving.

    Idempotent; returns ``True`` iff a change was written.
    """
    path = spheno_model_src / f"Model_Data_{sarah_name}.f90"
    if not path.exists():
        return False
    text = path.read_text()
    # Match only the exact zero-init — do not disturb downstream assignments
    # that legitimately flip PhaseFS to ±1 based on sign-of-mass logic.
    new_text, nsub = re.subn(
        r"^(\s*)PhaseFS\s*=\s*0\._dp\s*$",
        r"\1PhaseFS = 1._dp",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if nsub and new_text != text:
        path.write_text(new_text)
        return True
    return False


def _dedupe_model_data_decls(spheno_model_src: Path, sarah_name: str) -> int:
    """Drop standalone ``Real(dp) :: <name>`` lines that duplicate a grouped decl.

    SARAH sometimes emits a BSM parameter both in the grouped "RGE-running"
    declaration (``Real(dp) :: g1,g2,g3,MS,MPsi``) and as later standalone
    lines (``Real(dp) :: MS``) inside the module specification part of
    ``Model_Data_<Model>.f90``, which gfortran rejects. This helper walks
    the module-spec part (everything before the first ``Contains``), records
    names appearing in any grouped (>=2-name) Real(dp) declaration, then
    strips subsequent single-name Real(dp) lines whose identifier is already
    in that set. Dedupe stops at ``Contains`` so per-subroutine scopes
    (e.g. RGEAlphaS's own ``Real(dp) :: nQuark``) are left untouched.
    Idempotent; only touches ``Model_Data_<sarah_name>.f90``.
    """
    path = spheno_model_src / f"Model_Data_{sarah_name}.f90"
    if not path.exists():
        return 0
    lines = path.read_text().splitlines(keepends=True)
    grouped_names: set[str] = set()
    out: list[str] = []
    removed = 0
    in_spec = True
    for line in lines:
        if in_spec and _CONTAINS_RE.match(line):
            in_spec = False
        if in_spec:
            m = _REAL_DECL_RE.match(line.rstrip("\n"))
            if m:
                payload = m.group(1)
                names: list[str] = []
                for tok in payload.split(","):
                    id_match = _IDENT_RE.match(tok.strip())
                    if id_match:
                        names.append(id_match.group(1))
                if len(names) >= 2:
                    grouped_names.update(names)
                    out.append(line)
                    continue
                if len(names) == 1 and names[0] in grouped_names:
                    removed += 1
                    continue
        out.append(line)
    if removed:
        path.write_text("".join(out))
    return removed


def compute_cache_key(spec_path: Path, sarah_version: str, spheno_version: str) -> str:
    """Compute the W4 cache key from spec bytes + tool versions.

    Format: sha256hex(spec.yaml)=<sarah_version>+<spheno_version>
    """
    spec_bytes = spec_path.read_bytes()
    digest = hashlib.sha256(spec_bytes).hexdigest()
    return f"{digest}={sarah_version}+{spheno_version}"


def compile_model(model_name: str, force: bool = False) -> dict:
    """Compile a model-specific SPheno binary.

    Returns:
        {"status": "cached"} if cache hit and not forced.
        {"status": "compiled", "binary": str} on success.
    Raises SystemExit on fatal error (after emitting blocker JSON to stderr).
    """
    config_helpers = _load_config_helpers()
    sarah_name_mod = _load_sarah_name()

    config = config_helpers.load_config()

    spheno_src = config.get("spheno_src_path")
    if not spheno_src or not Path(spheno_src).exists():
        _emit_fatal(
            "SPHENO_PATH_INVALID",
            "spheno_src_path not set or not found in config. Run /spheno-install first.",
        )
        sys.exit(1)
    spheno_src = Path(spheno_src)

    sarah_version = config.get("sarah_version", "unknown")
    spheno_version = config.get("spheno_version", "unknown")

    state_root = config_helpers.STATE_ROOT
    model_dir = state_root / "models" / model_name
    spec_path = model_dir / "spec.yaml"

    if not spec_path.exists():
        _emit_fatal(
            "SPHENO_COMPILE_FAILED",
            f"spec.yaml not found at {spec_path}. Run /sarah-build first.",
        )
        sys.exit(1)

    try:
        sarah_name = sarah_name_mod.modelspec_name_to_sarah(model_name)
    except ValueError as e:
        _emit_fatal("SPHENO_COMPILE_FAILED", f"Invalid model name: {e}")
        sys.exit(1)

    sarah_output_dir = model_dir / "sarah_output" / "SPheno" / sarah_name
    if not sarah_output_dir.exists():
        _emit_fatal(
            "SPHENO_COMPILE_FAILED",
            f"SARAH output not found at {sarah_output_dir}. Run /sarah-build first.",
            {"expected_path": str(sarah_output_dir)},
        )
        sys.exit(1)

    spheno_bin_dir = model_dir / "spheno_bin"
    spheno_bin_dir.mkdir(parents=True, exist_ok=True)

    binary_dest = spheno_bin_dir / f"SPheno{sarah_name}"
    cache_key_file = spheno_bin_dir / ".build_key"

    # Check cache
    cache_key = compute_cache_key(spec_path, sarah_version, spheno_version)
    if not force and cache_key_file.exists() and binary_dest.exists():
        existing_key = cache_key_file.read_text().strip()
        if existing_key == cache_key:
            return {"status": "cached", "binary": str(binary_dest)}

    # Copy SARAH Fortran sources into SPheno source tree
    spheno_model_src = spheno_src / sarah_name
    if spheno_model_src.exists():
        shutil.rmtree(spheno_model_src)
    shutil.copytree(str(sarah_output_dir), str(spheno_model_src))

    # Post-SARAH patches (see demo_output/singlet-doublet/report.md for context):
    # rewrite ar -U on Darwin, strip duplicate Real(dp) decls in Model_Data,
    # serialize the model subtree to dodge a .mod-ordering race, and
    # normalise rank-1 single-eigenstate Dirac masses to scalar (see
    # ``_patch_rank1_dirac_mass`` module docstring + sarah-workarounds.md §16).
    _patch_darwin_ar(spheno_model_src)
    _dedupe_model_data_decls(spheno_model_src, sarah_name)
    _patch_notparallel(spheno_model_src)
    rank1_patched = _patch_rank1_dirac_mass(spheno_model_src, sarah_name)
    phasefs_patched = _patch_phasefs_init(spheno_model_src, sarah_name)

    # Run make
    make_log_path = spheno_bin_dir / "make.log"
    cpu_count = os.cpu_count() or 1
    # Override SPheno's Makefile ifort default. The sibling installer at
    # plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh treats
    # HEPPH_F90_COMPILER as a first-class override (tested), so we honor
    # the same env var here for compiler consistency between base install
    # and model compile — mismatched compilers produce unreadable .mod
    # files. Default is gfortran, which /spheno-install enforces as a
    # precondition via check_gfortran.sh.
    f90_compiler = os.environ.get("HEPPH_F90_COMPILER", "gfortran")
    cmd = [
        "make",
        "-C", str(spheno_src),
        f"Model={sarah_name}",
        f"F90={f90_compiler}",
        f"-j{cpu_count}",
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3600,
        )
        make_output = proc.stdout or ""
    except subprocess.TimeoutExpired:
        make_output = "make timed out after 3600 seconds"
        proc = type("FakeProc", (), {"returncode": 1})()

    # Prepend a header that logs which post-SARAH patches ran, so make.log
    # makes the provenance explicit. Idempotent: ``rank1_patched`` is empty
    # on a re-run (no rank-1 decls left to rewrite).
    patch_lines = [
        "# hephaestus post-SARAH patches applied before make:",
        "#   - Darwin ar -U stripper, Model_Data dedupe, .NOTPARALLEL",
    ]
    if rank1_patched:
        for fname in sorted(rank1_patched):
            masses = ", ".join(rank1_patched[fname])
            patch_lines.append(
                f"#   - rank-1 Dirac demotion in {fname}: {masses} "
                f"(see sarah-workarounds.md §16)"
            )
    else:
        patch_lines.append(
            "#   - rank-1 Dirac demotion: no rank-1 single-eigenstate masses"
        )
    make_log_path.write_text("\n".join(patch_lines) + "\n\n" + make_output)

    built_binary = spheno_src / "bin" / f"SPheno{sarah_name}"

    if proc.returncode != 0 or not built_binary.exists():
        _emit_fatal(
            "SPHENO_COMPILE_FAILED",
            f"make failed for model {sarah_name} (exit {proc.returncode}).",
            {
                "make_log_tail": _last_n_lines(make_output, 40),
                "model_name": model_name,
                "sarah_name": sarah_name,
            },
        )
        sys.exit(1)

    # Move binary to model spheno_bin dir
    shutil.move(str(built_binary), str(binary_dest))
    binary_dest.chmod(0o755)

    # Write cache key
    cache_key_file.write_text(cache_key + "\n")

    return {"status": "compiled", "binary": str(binary_dest)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Compile a model-specific SPheno binary (Stage 1 of /spheno-build)."
    )
    parser.add_argument("model_name", help="Model name (snake_case, e.g. dark_su3)")
    parser.add_argument(
        "--force", action="store_true",
        help="Force recompile even if cache key matches."
    )
    args = parser.parse_args()

    result = compile_model(args.model_name, force=args.force)
    print(json.dumps(result))
