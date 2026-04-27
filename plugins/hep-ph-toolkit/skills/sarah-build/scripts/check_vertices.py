"""
check_vertices.py — Cross-check ModelSpec Lagrangian terms vs. UFO vertex list.

Catches SARAH silent failures where a yukawa_term or mass_term parses into the
Lagrangian but never reaches UFO vertex emission (PossibleTerms::NonSUSY scan
drops, ChargeViolating suppression, DMParity mismatch). Two directions:

    1. Each spec mass_term / yukawa_term must have a matching UFO vertex whose
       particle list contains the mass-eigenstate counterparts of the declared
       Weyl components (modulo conj[] wrapping). Missing => VERTICES_MISSING.

    2. Each UFO vertex touching a BSM mass eigenstate must have at least one
       declared spec term that could produce it. Orphan UFO vertices =>
       VERTICES_UNEXPECTED (weaker — may indicate a forgotten discrete
       symmetry rather than a real bug).

Usage:
    python3 check_vertices.py --spec <modelspec.yaml> --output-dir <UFO_dir>

Input paths:
    --output-dir points at the UFO model directory (containing vertices.py,
    couplings.py). /sarah-build writes this under:
        <STATE_ROOT>/models/<model_name>/sarah_output/UFO/<SarahName>/
    (where <SarahName> is the CamelCased form of <model_name>, e.g.
    singlet_doublet → SingletDoublet). A convenience symlink also exists at
        <STATE_ROOT>/models/<model_name>/<SarahName>/
    pointing at the same directory — either path works.
    Example:
        ~/.local/share/hephaestus/models/singlet_doublet/sarah_output/UFO/SingletDoublet/
    SARAH's native output tree (``~/SARAH/SARAH-4.15.3/Output/<SarahName>/
    EWSB/UFO/<SarahName>/``) is also accepted — the script only reads the
    directory contents.

Exits:
    0 — all declared terms accounted for, no unexpected BSM vertices
    1 — at least one VERTICES_MISSING blocker emitted
    2 — VERTICES_UNEXPECTED only (no MISSING)

Parsing approach (pragmatic, regex-based):
    - UFO vertices.py: each ``V_<n> = Vertex(...)`` block is split; the
      ``particles = [P.X, P.Y, ...]`` line is captured with a regex and the
      ``P.`` prefixes stripped to yield the particle symbol list.
    - UFO couplings.py: each ``GC_<n> = Coupling(...)`` block is captured
      and its ``value = '<expr>'`` string scanned for spec parameter names
      (word-boundary match) to mark couplings as ``nonzero`` iff the
      declared coefficient appears in the value string.
    - A spec term is matched to a UFO vertex when (a) the vertex particle
      list, mapped through the spec-declared Weyl-to-mass-eigenstate
      mapping, is a superset of the term's fields, AND (b) at least one
      of the vertex's couplings has a value string referencing the term's
      coefficient symbol. The superset rule handles generation expansion
      (SARAH writes one ``Chi1/Chi2/Chi3`` vertex per mass eigenstate).

Limitations:
    - conj[...] wrappers in spec fields are stripped before the
      Weyl-to-eigenstate lookup; direction of mass-eigenstate creation is
      not distinguished. UFO never exposes particle/antiparticle in the
      vertex list symbol either.
    - SM-sector vertices (e.g. SM Yukawas with Yu/Yd/Ye) are filtered out
      of the "unexpected" scan to avoid noise. Only vertices touching a
      BSM mass eigenstate (from the spec's ewsb.mixings) are flagged.
    - If couplings.py can't be opened, coefficient matching falls back
      to "any coupling satisfies" and a ``parse_skipped`` warning is
      emitted on stderr.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import argparse
import json
import re
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Blocker emission helpers
# ---------------------------------------------------------------------------


def _emit(blocker: dict) -> None:
    """Pretty-print a blocker JSON object to stderr."""
    print(json.dumps(blocker, indent=2), file=sys.stderr)


def _emit_missing(term: dict, expected_fields: list[str]) -> None:
    _emit({
        "code": "VERTICES_MISSING",
        "mode": "recoverable",
        "message": (
            f"Declared Lagrangian term with coefficient "
            f"{term.get('coefficient', '<no coeff>')!r} has no matching UFO "
            f"vertex. Fields {expected_fields!r} should appear (after Weyl→"
            f"mass-eigenstate mapping) in some V_<n>.particles entry with a "
            f"nonzero coupling referencing {term.get('coefficient')!r}. "
            f"SARAH likely dropped this term at the vertex-engine stage — "
            f"see sarah-gotchas.md §VERTICES_MISSING."
        ),
        "context": {
            "term": dict(term),
            "expected_fields": expected_fields,
            "coefficient": term.get("coefficient"),
        },
    })


def _emit_unexpected(ufo_vertex_name: str, ufo_fields: list[str]) -> None:
    _emit({
        "code": "VERTICES_UNEXPECTED",
        "mode": "recoverable",
        "message": (
            f"UFO vertex {ufo_vertex_name!r} touches BSM mass eigenstate(s) "
            f"{ufo_fields!r} but has no declared spec counterpart. May indicate "
            f"a forgotten discrete symmetry (DMParity/Z2) or an accidental "
            f"term in the renderer. See sarah-gotchas.md §VERTICES_UNEXPECTED."
        ),
        "context": {
            "ufo_vertex_name": ufo_vertex_name,
            "ufo_fields": ufo_fields,
        },
    })


def _warn_parse_skipped(reason: str, context: dict) -> None:
    """Diagnostic (not a blocker) when a file/construct can't be parsed."""
    print(
        json.dumps({
            "code": "VERTICES_PARSE_SKIPPED",
            "mode": "warning",
            "message": reason,
            "context": context,
        }, indent=2),
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# UFO parsing (regex-based)
# ---------------------------------------------------------------------------

_VERTEX_HEADER_RE = re.compile(r"^(V_\S+)\s*=\s*Vertex\(", re.MULTILINE)
_PARTICLES_RE = re.compile(r"particles\s*=\s*\[([^\]]+)\]", re.DOTALL)
_COUPLINGS_RE = re.compile(r"couplings\s*=\s*\{([^}]+)\}", re.DOTALL)
_P_PREFIX_RE = re.compile(r"\bP\.(\w+)")
_C_PREFIX_RE = re.compile(r"\bC\.(\w+)")

_COUPLING_HEADER_RE = re.compile(r"^(GC_\S+)\s*=\s*Coupling\(", re.MULTILINE)
_COUPLING_VALUE_RE = re.compile(r"value\s*=\s*['\"](.+?)['\"]\s*,", re.DOTALL)


def _iter_blocks(text: str, header_re: re.Pattern) -> list[tuple[str, str]]:
    """Yield (name, body) for each top-level Vertex(...) / Coupling(...) block.

    Splits the file on header matches. Each block's body runs from after the
    opening paren to the matching closing paren, found by a simple paren depth
    counter (UFO never nests brackets inside these constructs beyond the
    couplings / value literals the regexes already handle).
    """
    blocks: list[tuple[str, str]] = []
    for match in header_re.finditer(text):
        name = match.group(1)
        start = match.end()  # position right after the '('
        depth = 1
        i = start
        in_str: str | None = None
        while i < len(text):
            c = text[i]
            if in_str:
                if c == "\\":
                    i += 2
                    continue
                if c == in_str:
                    in_str = None
            else:
                if c in ("'", '"'):
                    in_str = c
                elif c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        blocks.append((name, text[start:i]))
                        break
            i += 1
    return blocks


def parse_ufo_couplings(path: Path) -> dict[str, str]:
    """Return {coupling_name: value_expr} from a UFO couplings.py.

    Returns an empty dict and emits a parse_skipped warning if the file is
    missing or unreadable.
    """
    if not path.exists():
        _warn_parse_skipped(
            f"UFO couplings.py not found at {path} — coefficient matching will "
            f"fall back to permissive mode.",
            {"path": str(path)},
        )
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _warn_parse_skipped(
            f"Failed to read {path}: {exc}",
            {"path": str(path)},
        )
        return {}
    out: dict[str, str] = {}
    for name, body in _iter_blocks(text, _COUPLING_HEADER_RE):
        m = _COUPLING_VALUE_RE.search(body)
        if m is None:
            continue
        out[name] = m.group(1)
    return out


def parse_ufo_vertices(path: Path) -> list[dict]:
    """Return [{name, particles: [...], couplings: [GC_...]}] from vertices.py.

    Exits 1 if the file is missing — a UFO dir without vertices.py is a fatal
    input error (upstream should have validated the UFO directory).
    """
    if not path.exists():
        _emit({
            "code": "VERTICES_PARSE_FAILED",
            "mode": "fatal",
            "message": f"UFO vertices.py not found at {path}",
            "context": {"path": str(path)},
        })
        sys.exit(1)
    text = path.read_text(encoding="utf-8", errors="replace")
    vertices: list[dict] = []
    for name, body in _iter_blocks(text, _VERTEX_HEADER_RE):
        p_match = _PARTICLES_RE.search(body)
        if p_match is None:
            _warn_parse_skipped(
                f"UFO vertex {name!r} has no parseable particles list — skipped.",
                {"vertex": name},
            )
            continue
        particles = _P_PREFIX_RE.findall(p_match.group(1))
        c_match = _COUPLINGS_RE.search(body)
        couplings = _C_PREFIX_RE.findall(c_match.group(1)) if c_match else []
        vertices.append({
            "name": name,
            "particles": particles,
            "couplings": couplings,
        })
    return vertices


# ---------------------------------------------------------------------------
# Spec → Weyl-to-mass-eigenstate map
# ---------------------------------------------------------------------------

# Wrappers in spec field references that we strip before lookup.
_CONJ_WRAPPERS = ("conj[", "Conjugate[")


def _strip_wrapper(ref: str) -> str:
    s = ref.strip()
    for w in _CONJ_WRAPPERS:
        if s.startswith(w) and s.endswith("]"):
            return s[len(w):-1].strip()
    return s


def build_weyl_map(spec: dict) -> dict[str, list[str]]:
    """Return {weyl_or_outer: [mass_eigenstate_prefixes]}.

    Each Weyl component AND each outer field name map to a list of
    mass-eigenstate name prefixes. SARAH expands a single eigenstate
    name into generation-indexed UFO particle symbols (``Chi`` → ``Chi1``,
    ``Chi2``, ``Chi3``), so we match by prefix (startswith) against the UFO
    particle symbols.

    Outer-field mapping rule: the outer symbol inherits the union of its
    components' mass eigenstates. This matters for Lagrangian terms written
    with the outer symbol (e.g. ``conj[H].FS.PsiDu``) rather than the Weyl
    components — SARAH accepts both forms.

    The SM Higgs doublet H maps to {h, Ah, Hp, Hpc} in SARAH's EWSB-phase UFO
    naming; we insert that mapping explicitly here since it's universal.
    """
    mapping: dict[str, list[str]] = {}

    # Universal SM Higgs doublet → EWSB mass eigenstates in UFO.
    mapping["H"] = ["h", "Ah", "Hp", "Hpc", "G0", "Gp", "Gpc"]
    mapping["H0"] = ["h", "Ah", "G0"]
    mapping["Hp"] = ["Hp", "Gp"]
    mapping["Hpc"] = ["Hpc", "Gpc"]

    # Component → mass-eigenstate list, from ewsb.mixings.
    for mixing in spec.get("ewsb", {}).get("mixings", []) or []:
        kind = mixing.get("kind")
        targets: list[str] = []
        me = mixing.get("mass_eigenstate")
        me_rh = mixing.get("mass_eigenstate_rh")
        if me:
            targets.append(me)
        if me_rh:
            targets.append(me_rh)
        if not targets:
            continue
        if kind == "fermion":
            weyls = (
                (mixing.get("weyls") or [])
                + (mixing.get("lh_weyls") or [])
                + (mixing.get("rh_weyls") or [])
            )
        elif kind == "scalar":
            weyls = mixing.get("weyls") or []
        else:
            weyls = []
        for w in weyls:
            mapping.setdefault(str(w), []).extend(targets)

    # Outer-field → union of its components' targets. A fermion / scalar
    # whose components appear in mixings inherits their mass-eigenstate
    # prefixes; one whose components never appear in a mixing either maps
    # back to itself (if the outer symbol is also a mass eigenstate after
    # EWSB) or to an empty list (unbroken gauge eigenstate — caller should
    # fall back to outer symbol literal).
    for f in spec.get("fermions", []) or []:
        outer = f.get("name")
        if not outer:
            continue
        comps = f.get("components") or []
        inherited: list[str] = []
        for c in comps:
            inherited.extend(mapping.get(str(c), []))
        if outer not in mapping:
            mapping[outer] = list(dict.fromkeys(inherited)) if inherited else [outer]
        else:
            # Merge (in case outer was explicitly named as a Weyl).
            for t in inherited:
                if t not in mapping[outer]:
                    mapping[outer].append(t)
    for s in spec.get("scalars", []) or []:
        outer = s.get("name")
        if not outer:
            continue
        comps = s.get("components") or []
        inherited: list[str] = []
        for c in comps:
            inherited.extend(mapping.get(str(c), []))
        if outer not in mapping:
            mapping[outer] = list(dict.fromkeys(inherited)) if inherited else [outer]

    return mapping


def _candidate_particles(ref: str, weyl_map: dict[str, list[str]]) -> list[str]:
    """Mass-eigenstate name prefixes that could represent this spec field."""
    inner = _strip_wrapper(ref)
    return weyl_map.get(inner, [inner])


def _particle_matches(ufo_symbol: str, candidates: list[str]) -> bool:
    """True iff any candidate prefix-matches the UFO particle symbol."""
    for cand in candidates:
        if ufo_symbol == cand or ufo_symbol.startswith(cand):
            return True
    return False


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def _coupling_uses_coefficient(value_expr: str, coeff: str) -> bool:
    """Word-boundary check for coeff symbol inside a UFO coupling value string."""
    return re.search(rf"\b{re.escape(coeff)}\b", value_expr) is not None


def _term_matches_vertex(
    term_fields: list[str],
    coeff: str,
    vertex: dict,
    couplings: dict[str, str],
    weyl_map: dict[str, list[str]],
) -> bool:
    """True if the vertex's particles cover the term's fields AND a coupling uses the coefficient."""
    ufo_particles = list(vertex["particles"])
    # Each term field must find a distinct UFO particle that matches one of
    # its candidate eigenstate names.
    remaining = list(ufo_particles)
    for ref in term_fields:
        cands = _candidate_particles(ref, weyl_map)
        hit_idx = None
        for idx, sym in enumerate(remaining):
            if _particle_matches(sym, cands):
                hit_idx = idx
                break
        if hit_idx is None:
            return False
        remaining.pop(hit_idx)

    # Coefficient check: permissive fallback when couplings.py couldn't be
    # parsed (empty dict).
    if not couplings:
        return True
    for c_name in vertex["couplings"]:
        value = couplings.get(c_name, "")
        if _coupling_uses_coefficient(value, coeff):
            return True
    return False


def _touches_bsm(vertex: dict, bsm_eigenstates: set[str]) -> bool:
    """True iff any vertex particle prefix-matches a BSM mass-eigenstate name."""
    for sym in vertex["particles"]:
        for bsm in bsm_eigenstates:
            if sym == bsm or sym.startswith(bsm):
                return True
    return False


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def _collect_spec_terms(spec: dict) -> list[dict]:
    """Flatten yukawa_terms + scalar_potential into a list with section tags.

    Only sections that produce UFO vertices. Mass_terms contribute to the
    mass matrix (diagonalisation → particle masses) rather than directly to
    vertex couplings, so they're handled by check_mass_matrix.py instead.
    """
    out: list[dict] = []
    lag = spec.get("lagrangian", {}) or {}
    for sec in ("yukawa_terms", "scalar_potential"):
        for t in lag.get(sec, []) or []:
            if isinstance(t, dict) and t.get("fields") and t.get("coefficient"):
                out.append({**t, "_section": sec})
    return out


def _bsm_mass_eigenstates(spec: dict) -> set[str]:
    out: set[str] = set()
    for m in spec.get("ewsb", {}).get("mixings", []) or []:
        for key in ("mass_eigenstate", "mass_eigenstate_rh"):
            v = m.get(key)
            if v:
                out.add(str(v))
    return out


def _all_declared_coefficients(spec: dict) -> set[str]:
    """Every symbol a BSM-touching UFO coupling may legitimately contain.

    Includes yukawa / scalar_potential coefficients AND mass_term coefficients
    (which SARAH threads through the mass-matrix diagonalisation into vertex
    values), plus SM gauge couplings g1/g2/g3 and the SM Higgs VEV vvSM
    (gauge-boson couplings to the BSM sector come entirely from these).
    """
    coeffs: set[str] = {"g1", "g2", "g3", "vvSM", "v", "e", "ThetaW", "TW"}
    lag = spec.get("lagrangian", {}) or {}
    for sec in ("mass_terms", "yukawa_terms", "scalar_potential"):
        for t in lag.get(sec, []) or []:
            if isinstance(t, dict) and t.get("coefficient"):
                coeffs.add(str(t["coefficient"]))
    for p in spec.get("parameters", []) or []:
        if p.get("name"):
            coeffs.add(str(p["name"]))
    return coeffs


def run(spec_path: Path, ufo_dir: Path) -> int:
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    vertices = parse_ufo_vertices(ufo_dir / "vertices.py")
    couplings = parse_ufo_couplings(ufo_dir / "couplings.py")
    weyl_map = build_weyl_map(spec)
    bsm = _bsm_mass_eigenstates(spec)
    declared_coeffs = _all_declared_coefficients(spec)

    missing = 0
    unexpected = 0

    # Direction 1: every declared term → matching UFO vertex.
    for term in _collect_spec_terms(spec):
        term_fields = [str(f) for f in term["fields"]]
        coeff = str(term["coefficient"])
        hit = any(
            _term_matches_vertex(term_fields, coeff, v, couplings, weyl_map)
            for v in vertices
        )
        if not hit:
            _emit_missing(term, term_fields)
            missing += 1

    # Direction 2: every BSM-touching UFO vertex → some declared counterpart.
    for v in vertices:
        if not _touches_bsm(v, bsm):
            continue
        # A vertex is "accounted for" if any of its couplings references any
        # declared BSM coefficient symbol (permissive fallback: any match
        # across the declared coefficient set is sufficient, since the
        # inverse direction was already enforced above).
        accounted = False
        if not couplings:
            accounted = True  # parse-skipped — don't flag unexpected
        else:
            for c_name in v["couplings"]:
                value = couplings.get(c_name, "")
                if any(_coupling_uses_coefficient(value, c) for c in declared_coeffs):
                    accounted = True
                    break
        if not accounted:
            _emit_unexpected(v["name"], list(v["particles"]))
            unexpected += 1

    if missing > 0:
        return 1
    if unexpected > 0:
        return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check ModelSpec Lagrangian terms against UFO vertex list.",
    )
    parser.add_argument("--spec", required=True, type=Path,
                        help="ModelSpec YAML file.")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="UFO directory (containing vertices.py, couplings.py).")
    args = parser.parse_args()
    sys.exit(run(args.spec, args.output_dir))


if __name__ == "__main__":
    main()
