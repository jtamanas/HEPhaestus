"""Self-containment of the FormCalc reduce writer (amp_reduced.m).

BUG (diagnosed in the SD eval build, SD-AMP-ABBREVIATIONS-UNRESOLVED): the
writer used to emit ``Put[reduced]`` — the bare CalcFeynAmp ``Amp[...]`` — WITHOUT
persisting FormCalc's abbreviation tables. The reduced amplitude references
``F##`` (Dirac/Weyl chains, from ``Abbr[]``) and ``Sub###`` (coefficient
subexpressions, from ``Subexpr[]``); with the tables omitted, those heads are
undefined the moment any *other* kernel ``Get``s the file. The artifact was not
self-contained. The 2HDM+a golden fixture is a hand-curated wrapped association
and so masked the gap.

These are HERMETIC (no Wolfram): two structure-level pins.

  1. SOURCE pin (red on base): run_calcfeynamp.wls must capture BOTH Abbr[] and
     Subexpr[] and write a wrapped association keyed "amp"/"abbr"/"subexpr".
     The base writer does ``Put[reduced]`` with no Subexpr[] reference → red.

  2. FIXTURE pin: a small new-format fixture is self-contained — every F## / Sub###
     referenced inside "amp" is defined in the "abbr"/"subexpr" tables. This
     documents (and enforces) the exact structural contract a fresh-kernel Get
     relies on, checked purely textually.

The real fresh-kernel Get + numeric round-trip lives in the gated e2e
(test_reduce_e2e_gated.py::test_reduced_amp_is_self_contained_fresh_kernel).
"""
from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
WRITER = SCRIPTS_DIR / "run_calcfeynamp.wls"
MIN_FIXTURE = TESTS_DIR / "fixtures" / "self_contained" / "amp_reduced_min.m"

# A symbol reference like F1, F4, Sub188, Sub7 (with or without an [index,...] tail).
_SYM_REF = re.compile(r"\b(F\d+|Sub\d+)\b")
# A definition LHS:  F1 ->    Sub188 ->    Sub7[i_] ->    (also :> delayed).
_SYM_DEF = re.compile(r"\b(F\d+|Sub\d+)\s*(?:\[[^\]]*\])?\s*(?::>|->)")


def _slice_between(text: str, start_key: str, next_keys) -> str:
    """Return the substring of `text` from `start_key` up to the first of
    `next_keys` that follows it (or end of text). Cheap key-region slicer for the
    flat wrapped-association fixture — good enough for a textual structural pin."""
    i = text.index(start_key)
    j = len(text)
    for k in next_keys:
        p = text.find(k, i + len(start_key))
        if p != -1:
            j = min(j, p)
    return text[i:j]


class TestWriterSourcePersistsAbbreviations:
    """SOURCE pin — red against the base writer (Put[reduced], no Subexpr[])."""

    def test_writer_captures_both_abbr_and_subexpr(self):
        src = WRITER.read_text()
        assert "Abbr[]" in src, (
            "run_calcfeynamp.wls must capture Abbr[] (F## Dirac/Weyl chains) so the "
            "reduced amplitude is self-contained across a Get[] in a fresh kernel."
        )
        assert "Subexpr[]" in src, (
            "run_calcfeynamp.wls must capture Subexpr[] (Sub### coefficient "
            "subexpressions). Omitting it leaves every Sub### in the reduced "
            "amplitude undefined cross-session (SD-AMP-ABBREVIATIONS-UNRESOLVED)."
        )

    def test_writer_emits_wrapped_association_keys(self):
        src = WRITER.read_text()
        for key in ('"amp"', '"abbr"', '"subexpr"'):
            assert key in src, (
                f"run_calcfeynamp.wls must write the {key} key of the wrapped "
                "amp_reduced/v2 association (matches the run_eval.wls consumer "
                "contract and the golden fixture)."
            )

    def test_writer_no_longer_puts_bare_reduced(self):
        """The old bare `Put[reduced, ...]` must be gone — it wrote a non
        self-contained Amp[...] with no abbreviation tables."""
        src = WRITER.read_text()
        assert not re.search(r"Put\[\s*reduced\s*,", src), (
            "Writer still Put[reduced, ...] (bare Amp[], no abbreviations). It must "
            "Put the wrapped association carrying Abbr[]/Subexpr[] instead."
        )


class TestMinFixtureSelfContained:
    """FIXTURE pin — every F##/Sub### used in "amp" is defined in the tables."""

    def test_fixture_amp_symbols_all_defined(self):
        text = MIN_FIXTURE.read_text()

        amp_region = _slice_between(text, '"amp"', ('"abbr"', '"subexpr"'))
        abbr_region = _slice_between(text, '"abbr"', ('"subexpr"',))
        subexpr_region = _slice_between(text, '"subexpr"', ())

        referenced = set(_SYM_REF.findall(amp_region))
        defined = set(_SYM_DEF.findall(abbr_region)) | set(_SYM_DEF.findall(subexpr_region))

        assert referenced, "fixture 'amp' region referenced no F##/Sub### — bad fixture"
        missing = referenced - defined
        assert not missing, (
            f"fixture is NOT self-contained: {sorted(missing)} used in 'amp' but "
            f"not defined in 'abbr'/'subexpr'. Defined: {sorted(defined)}"
        )

    def test_fixture_defines_both_plain_and_indexed_sub(self):
        """Guards the indexed-Sub### case (Sub7[i_]) the real SD amplitude hits —
        FormCalc Subexpr[] carries both plain and pattern-indexed subs."""
        text = MIN_FIXTURE.read_text()
        assert re.search(r"Sub\d+\s*->", text), "fixture lacks a plain Sub### -> def"
        assert re.search(r"Sub\d+\[[^\]]*_\S*\]\s*->", text), (
            "fixture lacks an indexed Sub###[i_,...] -> def"
        )
