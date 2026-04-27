"""test_resolve_dm_candidate.py — unit tests for resolve_dm_candidate.py."""
import sys
from pathlib import Path

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from resolve_dm_candidate import DMResolutionError, resolve


_SLHA_MASSES = {
    25: 125.0,       # h
    9000001: 100.0,  # S (singlet scalar DM)
    23: 91.2,        # Z
    1000022: 200.0,  # neutralino (lightest SUSY)
    1000024: 210.0,  # chargino
    1000021: 800.0,  # gluino
}


class TestSpecWinsOverCLI:
    def test_spec_wins_when_cli_also_given(self):
        spec = {"dm_candidate": {"pdg": 9000001, "name": "S", "mass_gev": 100.0}}
        pdg, name, mass, reason = resolve(
            spec_dict=spec,
            cli_pdg=1000022,  # different from spec
            auto_detect_flag=False,
            slha_masses=_SLHA_MASSES,
        )
        assert pdg == 9000001
        assert name == "S"
        assert mass == 100.0
        assert reason == "spec.yaml"

    def test_spec_without_mass_reads_from_slha(self):
        spec = {"dm_candidate": {"pdg": 9000001, "name": "S"}}
        pdg, name, mass, reason = resolve(
            spec_dict=spec,
            cli_pdg=None,
            auto_detect_flag=False,
            slha_masses=_SLHA_MASSES,
        )
        assert pdg == 9000001
        assert mass == 100.0  # from SLHA
        assert reason == "spec.yaml"


class TestAutoDetectAmbiguous:
    def test_auto_detect_ambiguous_raises(self):
        """Multiple Z2-odd zero-width candidates → MULTICOMPONENT_UNSUPPORTED."""
        ufo_particles = [
            {"pdg": 9000001, "name": "S", "z2_odd": True, "decay_width": 0.0, "mass_gev": 100.0},
            {"pdg": 9000002, "name": "S2", "z2_odd": True, "decay_width": 0.0, "mass_gev": 200.0},
        ]
        masses = {9000001: 100.0, 9000002: 200.0}
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(None, None, True, masses, ufo_particles)
        assert exc_info.value.code == "MULTICOMPONENT_UNSUPPORTED"
        assert exc_info.value.mode == "fatal"

    def test_no_candidates_raises_ambiguous(self):
        """No Z2-odd particles → DM_CANDIDATE_AMBIGUOUS (recoverable)."""
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(None, None, True, {}, None)
        assert exc_info.value.code == "DM_CANDIDATE_AMBIGUOUS"
        assert exc_info.value.mode == "recoverable"


class TestChargedLSPFatal:
    def test_chargino_spec_raises_unphysical(self):
        spec = {"dm_candidate": {"pdg": 1000024, "name": "chi+", "mass_gev": 210.0}}
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(spec, None, False, _SLHA_MASSES)
        assert exc_info.value.code == "DM_CANDIDATE_UNPHYSICAL"
        assert exc_info.value.mode == "fatal"

    def test_chargino_cli_raises_unphysical(self):
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(None, 1000024, False, _SLHA_MASSES)
        assert exc_info.value.code == "DM_CANDIDATE_UNPHYSICAL"


class TestColoredLSPFatal:
    def test_gluino_spec_raises_color_mismatch(self):
        spec = {"dm_candidate": {"pdg": 1000021, "name": "gluino", "mass_gev": 800.0}}
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(spec, None, False, _SLHA_MASSES)
        assert exc_info.value.code == "DM_CANDIDATE_COLOR_MISMATCH"
        assert exc_info.value.mode == "fatal"

    def test_squark_cli_raises_color_mismatch(self):
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(None, 1000001, False, _SLHA_MASSES)
        assert exc_info.value.code == "DM_CANDIDATE_COLOR_MISMATCH"


class TestZeroWidthDecayKeepsCandidate:
    def test_zero_width_kept(self):
        """Particle with Z2-odd=True and decay_width=0.0 is kept as candidate."""
        ufo = [{"pdg": 9000001, "name": "S", "z2_odd": True, "decay_width": 0.0, "mass_gev": 100.0}]
        pdg, name, mass, reason = resolve(None, None, True, {9000001: 100.0}, ufo)
        assert pdg == 9000001
        assert reason == "auto_detect_ufo"

    def test_nonzero_width_disqualified(self):
        """Particle with non-zero decay width is disqualified; falls back to SLHA."""
        ufo = [{"pdg": 9000001, "name": "S", "z2_odd": True, "decay_width": 0.01, "mass_gev": 100.0}]
        # No other candidates → DM_CANDIDATE_AMBIGUOUS
        with pytest.raises(DMResolutionError) as exc_info:
            resolve(None, None, True, {9000001: 100.0}, ufo)
        assert exc_info.value.code == "DM_CANDIDATE_AMBIGUOUS"
