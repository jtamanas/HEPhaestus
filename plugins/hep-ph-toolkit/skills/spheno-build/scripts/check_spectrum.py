"""
check_spectrum.py — Sanity-check an SPheno SLHA spectrum against the ModelSpec.

Catches silent failures where SPheno emits a syntactically valid SLHA file
but the physics is broken: NaN masses, tachyonic (negative) mass-squared
entries, or spec parameters whose declared nonzero defaults got zeroed in
the block readback (usually because the ``SPhenoInput`` / ``MINPAR`` block
wasn't wired to the parameter and SPheno substituted its own zero default).

Usage:
    python3 check_spectrum.py --spec <modelspec.yaml> --slha <SPheno.spc_file>

Input paths:
    --slha points to the SPheno SLHA spectrum file produced by /spheno-build.
    Concrete convention:
        <STATE_ROOT>/models/<model_name>/runs/<TS>/SPheno.spc
    Example:
        ~/.local/share/hephaestus/models/singlet_doublet/runs/2026-04-22T1043Z/SPheno.spc
    SARAH's native output names (``SPheno.spc.<Model>``) also work — the
    script only reads the file, it does not rely on the filename.

Exits:
    0 — spectrum passes every check
    1 — at least one SPECTRUM_NAN blocker emitted
    2 — SPECTRUM_UNPHYSICAL only (no NaN)
    3 — SPECTRUM_ZERO_NONZERO_PARAM only (no NaN / unphysical)

Checks:
    (a) For each ewsb.mixings[] mass_eigenstate, locate the SLHA MASS block
        entry. A spec eigenstate can correspond to multiple PDG codes after
        generation expansion (SARAH writes ``Chi`` → Chi1/Chi2/Chi3 with
        distinct PDGs), so we match by PDG range: we scan every MASS entry
        and check all of them for NaN / unphysical, and require at least
        one PDG match per declared eigenstate by name.
    (b) For each spec parameter whose ``default`` is nonzero, scan all SLHA
        blocks (not just MINPAR) for a line whose trailing comment contains
        the parameter name. If found and the numeric value is exactly 0,
        emit SPECTRUM_ZERO_NONZERO_PARAM. The comment-based lookup is
        pragmatic — SPheno's SARAH-generated input blocks always annotate
        each entry with ``# <paramname>`` in the output SLHA.

Parsing approach:
    - Uses a minimal in-file SLHA parser (duplicated from parse_slha.py but
      trimmed to what we need) so this script stays standalone with only
      stdlib + PyYAML deps.
    - NaN detection covers Python's float('nan'), the literal strings
      ``NaN`` / ``nan`` / ``NAN`` in the SLHA, and any non-finite parse
      result (inf, -inf).

Limitations:
    - A missing MASS block entry (e.g. SPheno never computed the eigenstate)
      is reported as SPECTRUM_UNPHYSICAL with mass=null rather than with a
      distinct code — the retry loop treats all "mass is broken" cases the
      same way.
    - Parameter-name matching uses the trailing ``# <name>`` comment; if a
      downstream version of SPheno omits the comment, a parse-skipped
      warning is emitted for that parameter and it's not flagged.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import math
import re
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Blocker emission helpers
# ---------------------------------------------------------------------------


def _emit(blocker: dict) -> None:
    print(json.dumps(blocker, indent=2), file=sys.stderr)


def _emit_nan(particle: str, pdg: str) -> None:
    _emit({
        "code": "SPECTRUM_NAN",
        "mode": "recoverable",
        "message": (
            f"Mass of particle {particle!r} (PDG {pdg}) is NaN in the SLHA "
            f"spectrum. SPheno's numerical diagonalisation failed — usually "
            f"a sign of zero-eigenvalue protection absent or a boundary "
            f"condition that fed in an uninitialised parameter. See "
            f"sarah-gotchas.md §SPECTRUM_NAN."
        ),
        "context": {"particle": particle, "pdg": pdg},
    })


def _emit_unphysical(particle: str, mass: float | None) -> None:
    _emit({
        "code": "SPECTRUM_UNPHYSICAL",
        "mode": "recoverable",
        "message": (
            f"Mass of particle {particle!r} is {mass!r} — either absent, "
            f"zero, or negative. Usually indicates a tachyonic tree-level "
            f"mass-squared or a missing mass-matrix entry. See "
            f"sarah-gotchas.md §SPECTRUM_UNPHYSICAL."
        ),
        "context": {"particle": particle, "mass": mass},
    })


def _emit_zero_param(parameter: str, spec_default: float, slha_value: float) -> None:
    _emit({
        "code": "SPECTRUM_ZERO_NONZERO_PARAM",
        "mode": "recoverable",
        "message": (
            f"Parameter {parameter!r} has spec default "
            f"{spec_default!r} but reads as {slha_value!r} in the SLHA. "
            f"The SARAH→SPheno input block likely doesn't route this "
            f"parameter from MINPAR/EXTPAR into the boundary condition. "
            f"See sarah-gotchas.md §SPECTRUM_ZERO_NONZERO_PARAM."
        ),
        "context": {
            "parameter": parameter,
            "spec_default": spec_default,
            "slha_value": slha_value,
        },
    })


def _warn_parse_skipped(reason: str, context: dict) -> None:
    print(
        json.dumps({
            "code": "SPECTRUM_PARSE_SKIPPED",
            "mode": "warning",
            "message": reason,
            "context": context,
        }, indent=2),
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# SLHA parsing (stripped-down standalone copy)
# ---------------------------------------------------------------------------


_BLOCK_HDR_RE = re.compile(r"^Block\s+(\S+)", re.IGNORECASE)
_DECAY_HDR_RE = re.compile(r"^DECAY\s+(\S+)\s+(\S+)", re.IGNORECASE)


def _parse_float(token: str) -> float:
    """Parse an SLHA float, treating NaN/inf strings as non-finite."""
    t = token.strip()
    if t.lower() in ("nan", "+nan", "-nan"):
        return float("nan")
    return float(t)


def parse_slha(path: Path) -> dict:
    """Return a dict with per-block entries and MASS comments.

    Structure:
        {
            "MASS":   {pdg_str: {"value": float, "comment": str}},
            "BLOCKS": {block_name: [{"indices": (i,j,...), "value": float,
                                     "comment": str}]},
        }

    Comments are the substring after '#' on each data line (stripped).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    masses: dict[str, dict] = {}
    blocks: dict[str, list[dict]] = {}
    current: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        block_m = _BLOCK_HDR_RE.match(stripped)
        if block_m:
            current = block_m.group(1).upper()
            blocks.setdefault(current, [])
            continue

        decay_m = _DECAY_HDR_RE.match(stripped)
        if decay_m:
            current = None
            continue

        if current is None:
            continue

        if "#" in stripped:
            data_part, _, comment = stripped.partition("#")
            comment = comment.strip()
        else:
            data_part, comment = stripped, ""
        tokens = data_part.split()
        if not tokens:
            continue

        if current == "MASS" and len(tokens) >= 2:
            pdg = tokens[0]
            try:
                masses[pdg] = {"value": _parse_float(tokens[1]), "comment": comment}
            except ValueError:
                continue
        else:
            # Generic block entry: last token is the value, earlier tokens
            # are indices (int).
            if len(tokens) < 2:
                continue
            try:
                val = _parse_float(tokens[-1])
            except ValueError:
                continue
            idx_tokens = tokens[:-1]
            try:
                indices = tuple(int(t) for t in idx_tokens)
            except ValueError:
                # Indices weren't all ints — keep as strings.
                indices = tuple(idx_tokens)
            blocks[current].append({
                "indices": indices,
                "value": val,
                "comment": comment,
            })

    return {"MASS": masses, "BLOCKS": blocks}


# ---------------------------------------------------------------------------
# Mass-eigenstate ↔ PDG helpers
# ---------------------------------------------------------------------------


def _bsm_eigenstate_names(spec: dict) -> list[str]:
    """Spec-declared BSM mass-eigenstate names that should appear in the SLHA MASS block.

    Only ``mass_eigenstate`` is included — for Dirac mixings SARAH emits a
    single MASS-block row keyed to ``mass_eigenstate`` (the LH-slot name),
    and ``mass_eigenstate_rh`` shares that row (they are the same physical
    Dirac fermion). Requiring both to appear independently yields false
    positives on Dirac sectors.
    """
    out: list[str] = []
    for m in spec.get("ewsb", {}).get("mixings", []) or []:
        v = m.get("mass_eigenstate")
        if v:
            out.append(str(v))
    return out


def _comment_matches_eigenstate(comment: str, eigenstate: str) -> bool:
    """Match an SLHA MASS-line comment to an eigenstate name.

    SARAH writes comments like ``# Chi_1``, ``# ChiM``, ``# Chi``, and for
    fermion mass eigenstates it prepends ``F`` in the Fortran / SLHA emission
    (``# FChi_1``, ``# FChiM``). Scalars carry no prefix. We match on
    word-boundary of the eigenstate name with an optional leading ``F`` and
    optional trailing ``_<n>`` generation index.
    """
    if not comment:
        return False
    pattern = rf"\bF?{re.escape(eigenstate)}(?:_?\d+)?\b"
    return re.search(pattern, comment) is not None


# ---------------------------------------------------------------------------
# Parameter ↔ SLHA block helpers
# ---------------------------------------------------------------------------


def _find_param_in_blocks(
    param_name: str, parsed: dict
) -> list[tuple[str, dict]]:
    """Return [(block_name, entry)] where the comment references the parameter."""
    out: list[tuple[str, dict]] = []
    pattern = re.compile(rf"\b{re.escape(param_name)}\b")
    for block_name, entries in parsed["BLOCKS"].items():
        for e in entries:
            if e["comment"] and pattern.search(e["comment"]):
                out.append((block_name, e))
    return out


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def _is_nan(x: float) -> bool:
    return isinstance(x, float) and math.isnan(x)


def _is_unphysical(x: float) -> bool:
    return not math.isfinite(x) or x <= 0.0


def run(spec_path: Path, slha_path: Path) -> int:
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    parsed = parse_slha(slha_path)

    nan_hits = 0
    unphysical_hits = 0
    zero_param_hits = 0

    # --- Pass 1: every MASS entry, regardless of comment ---
    # Covers SM particles that would otherwise be skipped; NaN/unphysical
    # anywhere in the spectrum indicates SPheno numerical failure.
    for pdg, entry in parsed["MASS"].items():
        v = entry["value"]
        particle_label = entry["comment"] or f"PDG_{pdg}"
        if _is_nan(v):
            _emit_nan(particle_label, pdg)
            nan_hits += 1
        elif _is_unphysical(v):
            _emit_unphysical(particle_label, v)
            unphysical_hits += 1

    # --- Pass 2: each declared BSM eigenstate must have at least one MASS row ---
    # Pass 2 relies on particle-name comments (``# FChi_1``, ``# ChiM``). Some
    # backends — notably the hephaestus analytic SLHA writer — emit only
    # numeric comments of the form ``# pdg=<N>``. When every MASS comment is
    # empty or numeric-only, name-based matching is impossible; skip pass 2
    # with a diagnostic rather than firing false positives.
    bsm_names = _bsm_eigenstate_names(spec)
    has_name_comments = any(
        entry["comment"] and re.search(r"[A-Za-z]", entry["comment"])
        and not entry["comment"].startswith("pdg=")
        for entry in parsed["MASS"].values()
    )
    if bsm_names and not has_name_comments:
        _warn_parse_skipped(
            "MASS block carries no particle-name comments (only 'pdg=<N>' "
            "or empty) — cannot verify BSM eigenstate presence by name. "
            "Pass 2 skipped. Likely the analytic spectrum backend; run with "
            "the SPheno backend to enable name-based checks.",
            {"mass_pdgs": list(parsed["MASS"].keys())},
        )
    else:
        for name in bsm_names:
            hit = False
            for pdg, entry in parsed["MASS"].items():
                if _comment_matches_eigenstate(entry["comment"], name):
                    hit = True
                    break
            if not hit:
                _emit_unphysical(name, None)
                unphysical_hits += 1

    # --- Pass 3: spec parameters with nonzero default must be nonzero in SLHA ---
    # Purpose: catch SARAH-side wiring drops where a parameter declared in
    # the spec never reaches the SPheno INPUT blocks. A scan driver is free
    # to *override* a nonzero default to 0 for a specific point — that is
    # not a blocker. Discriminator: if the parameter appears in any INPUT
    # block (MINPAR / EXTPAR / any ``*IN`` block), the wiring is intact and
    # the 0.0 is user-supplied; do not fire.
    _INPUT_BLOCK_NAMES = {"MINPAR", "EXTPAR"}

    def _is_input_block(block_name: str) -> bool:
        bn = block_name.upper()
        return bn in _INPUT_BLOCK_NAMES or bn.endswith("IN")

    for p in spec.get("parameters", []) or []:
        default = p.get("default", 0)
        if not isinstance(default, (int, float)):
            continue
        if default == 0:
            continue
        name = p.get("name")
        if not name:
            continue
        hits = _find_param_in_blocks(name, parsed)
        if not hits:
            _warn_parse_skipped(
                f"Parameter {name!r} has nonzero default {default!r} but no "
                f"SLHA block entry comments reference it — cannot verify.",
                {"parameter": name, "spec_default": default},
            )
            continue
        # Wiring-intact short-circuit: appearance in any INPUT block means
        # SPheno accepted the parameter from user input, so a 0.0 read is a
        # deliberate scan choice, not a wiring drop.
        wired_via_input = any(_is_input_block(bname) for bname, _ in hits)
        if wired_via_input:
            continue
        # Only the read-back path shows the parameter, and every occurrence
        # is zero — strong signal that SARAH's SPheno template never wired
        # the parameter into MINPAR/EXTPAR/*IN.
        all_zero = all(e["value"] == 0.0 for _, e in hits)
        if all_zero:
            _emit_zero_param(name, float(default), 0.0)
            zero_param_hits += 1

    if nan_hits > 0:
        return 1
    if unphysical_hits > 0:
        return 2
    if zero_param_hits > 0:
        return 3
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanity-check an SPheno SLHA spectrum against the ModelSpec.",
    )
    parser.add_argument("--spec", required=True, type=Path,
                        help="ModelSpec YAML file.")
    parser.add_argument("--slha", required=True, type=Path,
                        help="SPheno SLHA spectrum file (e.g. SPheno.spc.<Model>).")
    args = parser.parse_args()
    sys.exit(run(args.spec, args.slha))


if __name__ == "__main__":
    main()
