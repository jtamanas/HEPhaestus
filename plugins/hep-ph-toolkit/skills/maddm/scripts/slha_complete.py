"""Complete a SARAH/SPheno SLHA param card for MadGraph/MadDM.

Why this exists
---------------
SARAH-generated UFOs declare the SM quark rotation matrices (``UDLMIX``,
``UDRMIX``, ``UULMIX``, ``UURMIX``) and field-redefinition phases
(``PHASES``/``IMPHASES``) as *external* parameters whose UFO default value
is ``0.``. SPheno's SLHA output for such a model frequently omits these
blocks entirely (a rotation that is the identity, or a phase that is unity,
carries no information for SPheno to print). When MadGraph reads the param
card it then falls back to the UFO default of ``0.`` for every missing
entry.

For a *rotation matrix* that fallback is physically wrong: an absent
mixing block means the identity, not the zero matrix. Zeroing ``UDLMIX``/
``UDRMIX`` collapses the rotated Higgs-quark Yukawa ``ZDL^dagger . Yd . ZDR``
to zero, which silently deletes the entire Higgs t-channel from the
direct-detection matrix element. The observable symptom is a spin-independent
cross-section pinned at the ~1e-58 cm^2 vector (Z-exchange) floor and
completely insensitive to the Higgs-portal coupling — see
``singlet-doublet/SKILL.md`` step 4e and the reliability gate there.

Likewise a *phase* block that is absent means unity (1 + 0i), not 0; a zero
``PhaseFS`` multiplies the h-chi-chi coupling by ``conjg(PhaseFS) = 0``.

This helper reads the UFO's ``parameters.py`` to discover which external
blocks the model expects, then, for any such block that is entirely absent
from the card, inserts the physically-correct default: identity for a
two-index (matrix) block, unity for a one-index real phase block, zero for
its imaginary partner. Blocks already present in the card are never touched,
so a model that genuinely has quark mixing (a populated ``UDLMIX``) is left
exactly as SPheno wrote it.

It does NOT invent BSM input values (e.g. the ``BSMPARAMS`` Yukawas): those
carry real physics and must come from the spectrum generator or be set
explicitly by the caller. See ``singlet-doublet/SKILL.md`` for the
BSMPARAMS overlay step.

Library function Claude composes per-task — not a CLI executable.
"""

from __future__ import annotations

import re
from pathlib import Path

# Blocks whose UFO default of 0 must be reinterpreted when the block is
# absent. Keyed by the semantic class that determines the correct fill:
#   "rotation" -> identity (diagonal 1, off-diagonal 0)
#   "phase_re" -> unity on the diagonal code (1.0)
#   "phase_im" -> zero
# The membership is derived from the UFO at runtime; these name hints only
# classify the blocks we discover. Anything not matching a hint is left to
# the MadGraph/UFO default untouched (we only correct where "absent != 0").
_ROTATION_HINT = re.compile(r"(MIX|MIXING)$", re.IGNORECASE)
_PHASE_RE_HINT = re.compile(r"^PHASES$", re.IGNORECASE)
_PHASE_IM_HINT = re.compile(r"^IM(PHASES)$", re.IGNORECASE)

# SLHA keywords SPheno legitimately emits but MG5's param_card.dat reader
# cannot digest. ``DECAY1L`` is SPheno's 1-loop-corrected partial-width block
# (emitted alongside the tree-level ``DECAY`` when a spectrum is produced with
# loop corrections, e.g. for the top and the Higgs). MG5's reader does not
# recognise ``DECAY1L`` as a block keyword; it tries to parse
# ``DECAY1L         6    1.38499650E+00   # Fu_3`` as ordinary parameter lines
# and crashes with ``InvalidParam : line was ['l', '6', '1.38499650e+00']``.
# CRUCIALLY that crash happens INSIDE ``launch -f`` yet the enclosing
# ``mg5_aMC --mode=maddm`` process still EXITS 0 and prints the Planck relic
# constant (Omega h^2 = 1.2000e-01) it loaded before the crash, writing no
# output/run_01/ — a silent failure that masquerades as a landed-on-the-band
# success. Each keyword is matched as a whole first token (case-insensitive),
# so the ordinary ``DECAY <pdg>`` block is never touched.
_MADDM_INDIGESTIBLE_KEYWORDS = frozenset({"decay1l"})


def _external_blocks(ufo_path: str | Path) -> dict[str, list]:
    """Map lhablock -> sorted list of lhacodes for external UFO parameters.

    Parses ``parameters.py`` textually (no import side effects). Each entry
    is the ``lhacode`` list, e.g. ``[1, 1]`` or ``[3]``.
    """
    text = (Path(ufo_path) / "parameters.py").read_text()
    blocks: dict[str, list] = {}
    # Each external Parameter(...) has a lhablock and lhacode; capture pairs
    # that appear within a single Parameter(...) call.
    for m in re.finditer(
        r"lhablock\s*=\s*'([^']+)'\s*,\s*lhacode\s*=\s*\[([^\]]*)\]",
        text,
    ):
        block = m.group(1).lower()
        code = tuple(int(x) for x in re.findall(r"-?\d+", m.group(2)))
        blocks.setdefault(block, [])
        if code not in blocks[block]:
            blocks[block].append(code)
    for b in blocks:
        blocks[b].sort()
    return blocks


def strip_maddm_indigestible_blocks(text: str) -> tuple[str, list[str]]:
    """Remove SLHA blocks MG5's param_card reader cannot parse (e.g. DECAY1L).

    SPheno legitimately emits a 1-loop ``DECAY1L`` block alongside the
    tree-level ``DECAY``; MG5 chokes on it and — worst of all — the resulting
    crash inside ``launch -f`` still exits 0 while echoing the Planck relic
    constant, a silent failure (see ``_MADDM_INDIGESTIBLE_KEYWORDS``). This
    strips each such block: its header line plus every following BR/parameter
    sub-line, up to (but not including) the next top-level keyword line (one
    whose first non-space character is a letter, i.e. a new ``Block``/``DECAY``/
    ``DECAY1L`` header). Comment and indented/numeric lines belong to the block.

    Pure function: returns ``(new_text, removed)`` where ``removed`` is the list
    of stripped header lines (empty when nothing matched). Matching is on the
    first whitespace token, uppercased/lowercased, so the ordinary
    ``DECAY <pdg>`` block is never removed.
    """
    out_lines: list[str] = []
    removed: list[str] = []
    skipping = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        first_token = stripped.split()[0].lower() if stripped else ""
        is_top_level = bool(line[:1].isalpha())
        if is_top_level:
            # A new top-level keyword line always ends any prior skip and
            # decides whether we start a new one.
            if first_token in _MADDM_INDIGESTIBLE_KEYWORDS:
                skipping = True
                removed.append(stripped)
                continue
            skipping = False
        if skipping:
            # Indented/comment/numeric continuation of an indigestible block.
            continue
        out_lines.append(line)
    return "".join(out_lines), removed


def complete_sarah_param_card(
    card_path: str | Path,
    ufo_path: str | Path,
    *,
    in_place: bool = True,
) -> dict[str, str]:
    """Insert identity/unity defaults for absent SARAH rotation/phase blocks.

    Args:
        card_path: Path to the MadGraph param_card.dat (already overlaid with
            the SPheno SLHA spectrum). Modified in place unless
            ``in_place=False``.
        ufo_path: Path to the UFO model directory (needs ``parameters.py``).
        in_place: When True, rewrite ``card_path``. When False, leave the
            file untouched and only return the report.

    Returns:
        Report dict mapping each block that was inserted to a short reason,
        e.g. ``{"udlmix": "identity 3x3", "phases": "unit phase"}``. Empty
        dict means the card already had every rotation/phase block SPheno
        could have written — nothing was changed.
    """
    card_path = Path(card_path)
    expected = _external_blocks(ufo_path)

    text = card_path.read_text()

    # Strip MG5-indigestible blocks (e.g. SPheno's 1-loop DECAY1L) FIRST. Left
    # in place they crash `launch -f` while it exits 0 and echoes the Planck
    # relic constant — a silent failure. SPheno legitimately emits DECAY1L, so
    # this must be scrubbed in the card-prep step every documented overlay
    # recipe already routes through, not left for each caller to rediscover.
    report: dict[str, str] = {}
    text, stripped_blocks = strip_maddm_indigestible_blocks(text)
    if stripped_blocks:
        report["_stripped_indigestible"] = ", ".join(sorted(set(
            b.split()[0] for b in stripped_blocks
        )))

    present = {
        m.group(1).lower()
        for m in re.finditer(r"(?im)^\s*block\s+(\w+)", text)
    }

    inserts: list[str] = []

    # Repair a PRESENT real phase block whose entry is exactly 0. That value
    # is SARAH's Set_All_Parameters_0 sentinel, not physics: a phase has unit
    # modulus, so 0 silently deletes every conjg(Phase*)-carrying coupling
    # (relic 0.166-instead-of-0.2916 symptom). Present blocks are otherwise
    # trusted verbatim; this is the one exception, justified because no
    # legitimate spectrum can put a zero here.
    repaired = False
    if "phases" in present:
        out_lines = []
        in_phases = False
        for line in text.splitlines(keepends=True):
            stripped = line.strip().lower()
            if stripped.startswith("block "):
                in_phases = stripped.split()[1] == "phases"
            elif in_phases:
                m = re.match(r"^(\s*\d+\s+)([0-9.eE+\-]+)(.*)$", line.rstrip("\n"))
                if m:
                    try:
                        is_zero = float(m.group(2)) == 0.0
                    except ValueError:
                        is_zero = False
                    if is_zero:
                        line = (f"{m.group(1)}1.00000000E+00"
                                f"   # coerced 0->1: zero phase unphysical\n")
                        repaired = True
            out_lines.append(line)
        if repaired:
            text = "".join(out_lines)
            report["phases"] = "coerced present zero phase -> 1"

    for block, codes in expected.items():
        if block in present:
            continue  # SPheno wrote it — trust it verbatim.

        max_len = max(len(c) for c in codes)
        is_imag = block.startswith("im")
        if max_len == 2 and _ROTATION_HINT.search(block):
            # Rotation matrix. The REAL part of an absent rotation is the
            # identity; the IMAGINARY part (IM*MIX) is the zero matrix.
            dim = max(max(c) for c in codes)
            diag = "0.00000000E+00" if is_imag else "1.00000000E+00"
            lines = [f"Block {block.upper()}"]
            for i in range(1, dim + 1):
                lines.append(f"  {i:>3d} {i:>3d}   {diag}   # {'zero' if is_imag else 'identity'} fill")
            inserts.append("\n".join(lines))
            report[block] = f"{'zero' if is_imag else 'identity'} {dim}x{dim}"
        elif max_len == 1 and _PHASE_RE_HINT.search(block):
            # Real part of a field-redefinition phase: absent => unity.
            code = codes[0][0]
            inserts.append(
                f"Block {block.upper()}\n"
                f"  {code:>3d}   1.00000000E+00   # unit phase fill"
            )
            report[block] = "unit phase"
        elif max_len == 1 and _PHASE_IM_HINT.search(block):
            code = codes[0][0]
            inserts.append(
                f"Block {block.upper()}\n"
                f"  {code:>3d}   0.00000000E+00   # zero phase fill"
            )
            report[block] = "zero imaginary phase"
        # else: an ordinary external block (e.g. BSMPARAMS) whose absence
        # genuinely means "use the UFO default". We do not fabricate physics.

    if inserts:
        # Insert before the first DECAY block if present, else append.
        decay = re.search(r"(?im)^\s*decay\b", text)
        block_text = "\n" + "\n".join(inserts) + "\n"
        if decay:
            pos = decay.start()
            text = text[:pos] + block_text.lstrip("\n") + "\n" + text[pos:]
        else:
            text = text.rstrip("\n") + "\n" + block_text
    if (inserts or repaired or stripped_blocks) and in_place:
        card_path.write_text(text)

    return report
