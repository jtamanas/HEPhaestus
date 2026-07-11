"""test_decay1l_strip.py — pin the DECAY1L strip and the launch-no-output guard.

Two frictions from the singlet-doublet full-chain blind run, both silent
failures that masquerade as success:

* SPheno legitimately emits a 1-loop ``DECAY1L`` block alongside tree-level
  ``DECAY``. MG5's param_card reader crashes on it INSIDE ``launch -f`` while
  the enclosing ``mg5_aMC`` still exits 0 and echoes the Planck relic constant
  (0.1200). ``slha_complete.strip_maddm_indigestible_blocks`` /
  ``complete_sarah_param_card`` must scrub DECAY1L before overlay.
* Regardless of cause, a launch that wrote no ``output/run_*/MadDM_results.txt``
  must raise ``MADDM_LAUNCH_NO_OUTPUT`` (``maddm_run.assert_launch_produced_output``)
  rather than let the echoed constant be parsed as a result.
"""
from __future__ import annotations

import pytest

import slha_complete
import maddm_run


# A minimal param card: a real tree-level DECAY, two DECAY1L blocks (with the
# leading `#  BR` comment line SPheno writes), and a trailing Block. Mirrors the
# real SPheno.spc structure that broke MadDM's launch.
CARD = """\
Block MASS
        25     1.25090000E+02   # hh
DECAY          6     1.32000000E+00   # Fu_3 tree-level (KEEP)
     1.00000000E+00    2            5         24   # BR(Fu_3 -> Fd_3 VWp )
DECAY1L         6     1.38499650E+00   # Fu_3
#    BR                NDA      ID1      ID2
     1.00000000E+00    2            5         24   # BR(Fu_3 -> Fd_3 VWp )
DECAY1L        25     6.25570880E-03   # hh
#    BR                NDA      ID1      ID2
     8.50596324E-01    2           -5          5   # BR(hh -> Fd_3^* Fd_3 )
     2.92959538E-02    2           21         21   # BR(hh -> VG VG )
Block BSMPARAMS
     1     1.00000000E+00   # yh1
"""


class TestStripFunction:
    def test_decay1l_removed(self):
        out, removed = slha_complete.strip_maddm_indigestible_blocks(CARD)
        assert "DECAY1L" not in out
        assert len(removed) == 2  # two DECAY1L headers stripped

    def test_tree_level_decay_preserved(self):
        out, _ = slha_complete.strip_maddm_indigestible_blocks(CARD)
        assert "DECAY          6" in out
        # The tree-level DECAY's BR sub-line survives too.
        assert "BR(Fu_3 -> Fd_3 VWp )" in out

    def test_surrounding_blocks_preserved(self):
        out, _ = slha_complete.strip_maddm_indigestible_blocks(CARD)
        assert "Block MASS" in out
        assert "Block BSMPARAMS" in out
        assert "yh1" in out

    def test_decay1l_br_sublines_and_comment_removed(self):
        out, _ = slha_complete.strip_maddm_indigestible_blocks(CARD)
        # The DECAY1L hh block's characteristic BR line must be gone; the
        # `#  BR NDA ...` header comment that belongs to it too.
        assert "BR(hh -> VG VG )" not in out
        assert out.count("#    BR                NDA") == 0

    def test_noop_when_absent(self):
        clean = "Block MASS\n  25  125.0  # hh\nBlock BSMPARAMS\n  1  1.0\n"
        out, removed = slha_complete.strip_maddm_indigestible_blocks(clean)
        assert removed == []
        assert out == clean


class TestCompleteSarahParamCardStrips:
    """complete_sarah_param_card is the card-prep step every documented overlay
    recipe routes through — DECAY1L must be gone after it runs."""

    def _fake_ufo(self, tmp_path):
        ufo = tmp_path / "ufo"
        ufo.mkdir()
        # No external MIX/PHASES blocks -> no inserts; isolates the strip.
        (ufo / "parameters.py").write_text("# no external parameters\n")
        return ufo

    def test_card_scrubbed_in_place(self, tmp_path):
        card = tmp_path / "param_card.dat"
        card.write_text(CARD)
        report = slha_complete.complete_sarah_param_card(card, self._fake_ufo(tmp_path))
        text = card.read_text()
        assert "DECAY1L" not in text
        assert "Block BSMPARAMS" in text
        assert "DECAY          6" in text
        assert "decay1l" in report.get("_stripped_indigestible", "").lower()


class TestLaunchNoOutputGuard:
    def test_missing_results_raises(self, tmp_path):
        # out_dir with no output/run_*/MadDM_results.txt — the DECAY1L-crash
        # (or any launch that wrote nothing) shape.
        with pytest.raises(maddm_run.MadDMNoOutputError) as ei:
            maddm_run.assert_launch_produced_output(
                tmp_path,
                returncode=0,  # exit 0 is NOT evidence of success here
                stdout_tail="INFO: Omega h^2 = 1.2000e-01 +- 1.2000e-03\n",
            )
        assert ei.value.code == "MADDM_LAUNCH_NO_OUTPUT"
        assert ei.value.mode == "recoverable"

    def test_present_results_returns_path(self, tmp_path):
        run_dir = tmp_path / "output" / "run_01"
        run_dir.mkdir(parents=True)
        results = run_dir / "MadDM_results.txt"
        results.write_text("Omegah2 = 2.92e-01\n")
        got = maddm_run.assert_launch_produced_output(tmp_path, returncode=0)
        assert got == results

    def test_find_returns_newest_run(self, tmp_path):
        import os
        import time
        for i, val in ((1, 100.0), (2, 200.0)):
            d = tmp_path / "output" / f"run_0{i}"
            d.mkdir(parents=True)
            f = d / "MadDM_results.txt"
            f.write_text(f"run {i}\n")
            os.utime(f, (val, val))
        got = maddm_run.find_maddm_results(tmp_path)
        assert got.parent.name == "run_02"
