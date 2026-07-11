"""
test_leshouches_template.py — Unit tests for leshouches_template.build() and patch_minpar().

Asserts:
    - All required blocks present in build() output (MODSEL, SMINPUTS, GAUGEIN,
      HMIXIN, SMIN, MINPAR, BSMPARAMSIN; SPHENOINPUT appended by callers).
    - MINPAR entries in declaration order (index 1..N).
    - BSMPARAMSIN entries mirror MINPAR so the LOW-scale Boundaries branch in
      Boundaries_<Name>.f90 gets non-zero ``<name>IN`` values.
    - GAUGEIN / HMIXIN / SMIN carry SARAH-consistent numerical seeds so that
      the MatchingOrder == -1 pole-matching branch in SPheno<Name>.f90 has
      non-zero g1/g2/g3/vvSM/Lam/m2SM to start from — without them, the Higgs
      quartic (and therefore m_h, and therefore the full BSM spectrum through
      the v-coupled Chi mass matrix) collapses to zero.
    - patch_minpar replaces by name lookup, leaves others unchanged.

Test isolation: uses HEPPH_STATE_ROOT and XDG_CONFIG_HOME per global invariant §2.3.
"""

import importlib.util
import re
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def lht():
    return _load_module("leshouches_template", _SCRIPTS / "leshouches_template.py")


@pytest.fixture(autouse=True)
def isolate_env(tmp_path, monkeypatch):
    state = tmp_path / "hepph-state"
    cfg = tmp_path / "hepph-cfg"
    state.mkdir()
    cfg.mkdir()
    monkeypatch.setenv("HEPPH_STATE_ROOT", str(state))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))


# ---------------------------------------------------------------------------
# Minimal dark_su3 spec for testing (matches spec §4)
# ---------------------------------------------------------------------------
DARK_SU3_SPEC = {
    "name": "dark_su3",
    "parameters": [
        {"name": "MpsiD", "latex": "M_{\\psi_D}", "real": True, "positive": True,
         "default": 500.0, "les_houches": ["BSMPARAMS", 1]},
        {"name": "gD",    "latex": "g_D",         "real": True, "positive": True,
         "default": 1.0, "les_houches": ["BSMPARAMS", 2]},
    ],
}

TWO_PARAM_SPEC = {
    "name": "test_model",
    "parameters": [
        {"name": "A", "default": 100.0, "les_houches": ["BSMPARAMS", 1]},
        {"name": "B", "default": 200.0, "les_houches": ["BSMPARAMS", 2]},
        {"name": "C", "default": 300.0, "les_houches": ["BSMPARAMS", 3]},
    ],
}

# The real singlet_doublet spec places 4 BSM inputs at BSMPARAMS 1-4 and mixes
# in many SM/matrix params that carry NO scalar les_houches index. Used to pin
# that build() honours the declared index and excludes non-input params.
SINGLET_DOUBLET_LIKE_SPEC = {
    "name": "singlet_doublet",
    "parameters": [
        # SM couplings / Yukawas / matrices: NOT card inputs (no les_houches,
        # string les_houches, or a non-input block). Must never reach MINPAR.
        {"name": "g1", "real": True},
        {"name": "Yu", "real": False},
        {"name": "ZN", "les_houches": "ZNMIX"},        # output mixing matrix
        {"name": "PhaseFS", "les_houches": ["PHASES", 1]},  # non-input block
        # The 4 real BSM scalar inputs, declared out of MINPAR order on purpose.
        {"name": "yh2", "latex": "y_{h2}", "default": 0.0, "les_houches": ["BSMPARAMS", 4]},
        {"name": "MS",  "latex": "M_S",    "default": 150.0, "les_houches": ["BSMPARAMS", 1]},
        {"name": "MPsi", "latex": "M_\\Psi", "default": 500.0, "les_houches": ["BSMPARAMS", 2]},
        {"name": "yh1", "latex": "y_{h1}", "default": 1.0, "les_houches": ["BSMPARAMS", 3]},
    ],
}


# ---------------------------------------------------------------------------
# Test: build() — block presence
# ---------------------------------------------------------------------------
class TestBuildBlockPresence:
    def test_modsel_present(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+MODSEL", card, re.IGNORECASE | re.MULTILINE)

    def test_sminputs_present(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+SMINPUTS", card, re.IGNORECASE | re.MULTILINE)

    def test_minpar_present(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+MINPAR", card, re.IGNORECASE | re.MULTILINE)

    def test_modsel_value_non_susy(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        # Block MODSEL entry 1 = 0 (non-SUSY)
        assert re.search(r"^\s+1\s+0", card, re.MULTILINE), (
            "Expected MODSEL entry '1  0' for non-SUSY"
        )

    def test_sminputs_mz(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        # MZ is entry 4 = 9.118760000E+01
        assert "9.118760000E+01" in card or "9.11876" in card

    def test_sminputs_mt(self, lht):
        card = lht.build(DARK_SU3_SPEC)
        # m_t entry 6 = 1.734000000E+02
        assert "1.734000000E+02" in card or "173.4" in card

    def test_gaugein_present(self, lht):
        """Block GAUGEIN emitted with g1/g2/g3 entries."""
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+GAUGEIN", card, re.IGNORECASE | re.MULTILINE), (
            "Block GAUGEIN missing — SPheno<Name>.f90 pole-matching branch "
            "needs g1IN/g2IN/g3IN seeds"
        )
        # Entries 1,2,3 = g1,g2,g3 present
        gauge_block = re.search(
            r"^Block\s+GAUGEIN\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE,
        )
        assert gauge_block
        for idx in (1, 2, 3):
            assert re.search(rf"^\s+{idx}\s+", gauge_block.group(1), re.MULTILINE), (
                f"GAUGEIN entry {idx} missing"
            )

    def test_hmixin_present(self, lht):
        """Block HMIXIN emits vvSM entry (index 3)."""
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+HMIXIN", card, re.IGNORECASE | re.MULTILINE), (
            "Block HMIXIN missing — SPheno<Name>.f90 pole-matching branch "
            "needs vvSMIN seed"
        )
        # vvSM = 246.22 GeV, entry index 3
        hmix_block = re.search(
            r"^Block\s+HMIXIN\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE,
        )
        assert hmix_block
        assert re.search(r"^\s+3\s+2\.46", hmix_block.group(1), re.MULTILINE), (
            "HMIXIN entry 3 (vvSM) missing or wrong value"
        )

    def test_smin_present(self, lht):
        """Block SMIN emits m2SM (idx 1) and Lam (idx 2)."""
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(r"^Block\s+SMIN\b", card, re.IGNORECASE | re.MULTILINE), (
            "Block SMIN missing — Boundaries_<Name>.f90 LOW branch sets "
            "Lam = LamIN; omitting this block defaults LamIN = 0, which "
            "zeros the Higgs quartic and the full BSM spectrum"
        )
        smin_block = re.search(
            r"^Block\s+SMIN\b\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE,
        )
        assert smin_block
        body = smin_block.group(1)
        # SMIN index 1 = m2SM (sign-consistent with tree-level tadpole: negative)
        assert re.search(r"^\s+1\s+-", body, re.MULTILINE), (
            "SMIN entry 1 (m2SM) should be negative per tadpole convention"
        )
        # SMIN index 2 = Lam ~ 0.26 (SM tree-level Higgs quartic)
        assert re.search(r"^\s+2\s+2\.5[0-9]*E-01", body, re.MULTILINE), (
            f"SMIN entry 2 (Lam) should match SM tree-level quartic ~0.259, body:\n{body}"
        )


# ---------------------------------------------------------------------------
# Test: build() — BSMPARAMSIN mirrors MINPAR
# ---------------------------------------------------------------------------
class TestBsmParamsIn:
    def test_bsmparamsin_present(self, lht):
        """Block BSMPARAMSIN emitted alongside MINPAR."""
        card = lht.build(DARK_SU3_SPEC)
        assert re.search(
            r"^Block\s+BSMPARAMSIN", card, re.IGNORECASE | re.MULTILINE
        ), (
            "Block BSMPARAMSIN missing — Boundaries_<Name>.f90 LOW branch "
            "reads <name>IN values from this block"
        )

    def test_bsmparamsin_mirrors_minpar(self, lht):
        """BSMPARAMSIN carries the same indexed parameter values as MINPAR."""
        card = lht.build(DARK_SU3_SPEC, overrides={"MpsiD": 300.0})
        # Extract both blocks and compare non-comment data lines
        def extract_data(block_name: str) -> list[tuple[int, str]]:
            m = re.search(
                rf"^Block\s+{block_name}\s*\n((?:.*\n)*?)(?=^Block|\Z)",
                card, re.IGNORECASE | re.MULTILINE,
            )
            assert m, f"Block {block_name} not found"
            rows: list[tuple[int, str]] = []
            for line in m.group(1).splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    tokens = stripped.split()
                    if tokens and tokens[0].isdigit():
                        rows.append((int(tokens[0]), tokens[1]))
            return rows

        minpar_rows = extract_data("MINPAR")
        bsm_rows = extract_data("BSMPARAMSIN")
        assert minpar_rows == bsm_rows, (
            f"BSMPARAMSIN does not mirror MINPAR:\nMINPAR={minpar_rows}\n"
            f"BSMPARAMSIN={bsm_rows}"
        )


# ---------------------------------------------------------------------------
# Test: build() — MINPAR ordering
# ---------------------------------------------------------------------------
class TestMinparOrdering:
    def test_minpar_indices_sequential(self, lht):
        """MINPAR indices must be 1..N in declaration order."""
        card = lht.build(DARK_SU3_SPEC)
        # Extract MINPAR block
        minpar_match = re.search(
            r"^Block\s+MINPAR\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE
        )
        assert minpar_match, "Block MINPAR not found"
        minpar_text = minpar_match.group(1)
        # Extract indices from data lines (non-comment lines with index as first token)
        indices = []
        for line in minpar_text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                tokens = stripped.split()
                if tokens and tokens[0].isdigit():
                    indices.append(int(tokens[0]))
        assert indices == list(range(1, len(DARK_SU3_SPEC["parameters"]) + 1)), (
            f"MINPAR indices out of order: {indices}"
        )

    def test_minpar_first_param_name_in_comment(self, lht):
        """Each MINPAR row must have the parameter name in a comment."""
        card = lht.build(DARK_SU3_SPEC)
        assert "MpsiD" in card
        assert "gD" in card

    def test_minpar_declaration_order(self, lht):
        """Parameters appear in the order they are declared in spec."""
        card = lht.build(TWO_PARAM_SPEC)
        # Find positions of A, B, C in the card
        pos_a = card.find("# A")
        pos_b = card.find("# B")
        pos_c = card.find("# C")
        assert pos_a != -1 and pos_b != -1 and pos_c != -1
        assert pos_a < pos_b < pos_c, (
            f"Parameters not in declaration order: A@{pos_a}, B@{pos_b}, C@{pos_c}"
        )

    def test_minpar_default_values_used(self, lht):
        """Default parameter values appear in MINPAR when no overrides given."""
        card = lht.build(DARK_SU3_SPEC)
        # MpsiD default = 500.0, gD default = 1.0
        # Accept any scientific notation that represents 500 (e.g. 5.000000E+02)
        assert re.search(r"5[.\d]*[Ee][+]?02", card), (
            f"Expected 500 in MINPAR, card:\n{card}"
        )
        assert re.search(r"1[.\d]*[Ee][+]?00", card), (
            f"Expected 1.0 in MINPAR, card:\n{card}"
        )

    def test_minpar_override_applied(self, lht):
        """Override values replace defaults."""
        card = lht.build(DARK_SU3_SPEC, overrides={"MpsiD": 300.0})
        assert re.search(r"3[.\d]*[Ee][+]?02", card), (
            f"Expected 300 in MINPAR, card:\n{card}"
        )


# ---------------------------------------------------------------------------
# Test: patch_minpar()
# ---------------------------------------------------------------------------
class TestPatchMinpar:
    def test_replaces_target_param(self, lht):
        """patch_minpar replaces the named parameter."""
        card = lht.build(DARK_SU3_SPEC)
        patched = lht.patch_minpar(card, {"MpsiD": 300.0})
        # After patch, 300 should appear in MINPAR
        assert re.search(r"3[.\d]*[Ee][+]?02", patched), (
            f"Expected 300 in MINPAR after patch, card:\n{patched}"
        )

    def test_leaves_other_params_unchanged(self, lht):
        """patch_minpar does not affect parameters not in the patch dict."""
        card = lht.build(DARK_SU3_SPEC)
        patched = lht.patch_minpar(card, {"MpsiD": 300.0})
        # gD default = 1.0 should still be in MINPAR
        assert "1.000000000E+00" in patched or "1.0" in patched

    def test_empty_patch_returns_unchanged(self, lht):
        """Empty patch dict returns the original card text."""
        card = lht.build(DARK_SU3_SPEC)
        patched = lht.patch_minpar(card, {})
        assert patched == card

    def test_patch_only_affects_minpar_block(self, lht):
        """Values in other blocks (SMINPUTS etc.) are not modified."""
        card = lht.build(DARK_SU3_SPEC)
        # SMINPUTS entry 4 = MZ ~ 91.18
        original_mz_line = next(
            line for line in card.splitlines()
            if "9.118760000E+01" in line
        )
        patched = lht.patch_minpar(card, {"MpsiD": 300.0})
        assert original_mz_line in patched, "SMINPUTS MZ line was unexpectedly modified"

    def test_patch_multiple_params(self, lht):
        """Patch multiple parameters at once."""
        card = lht.build(DARK_SU3_SPEC)
        patched = lht.patch_minpar(card, {"MpsiD": 300.0, "gD": 2.0})
        assert re.search(r"3[.\d]*[Ee][+]?02", patched), (
            f"Expected 300 in patched MINPAR, card:\n{patched}"
        )
        assert re.search(r"2[.\d]*[Ee][+]?00", patched), (
            f"Expected 2.0 in patched MINPAR, card:\n{patched}"
        )


# ---------------------------------------------------------------------------
# Test: build() honours les_houches indices (the layer-2 fix)
# ---------------------------------------------------------------------------
def _minpar_rows(card: str) -> list[tuple[int, str]]:
    """Return [(index, name)] for the MINPAR block, parsed from comments."""
    m = re.search(
        r"^Block\s+MINPAR\s*\n((?:.*\n)*?)(?=^Block|\Z)",
        card, re.IGNORECASE | re.MULTILINE,
    )
    if not m:
        return []
    rows = []
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            mm = re.match(r"^(\d+)\s+\S+\s+#\s*(\S+)", stripped)
            if mm:
                rows.append((int(mm.group(1)), mm.group(2)))
    return rows


class TestLesHouchesIndexHonoured:
    def test_singlet_doublet_four_params_at_1_to_4(self, lht):
        """The 4-param singlet-doublet card yields MINPAR 1-4 exactly, mapped
        to MS/MPsi/yh1/yh2 regardless of declaration order."""
        card = lht.build(SINGLET_DOUBLET_LIKE_SPEC)
        rows = _minpar_rows(card)
        assert rows == [(1, "MS"), (2, "MPsi"), (3, "yh1"), (4, "yh2")], rows

    def test_bsmparamsin_matches_by_index(self, lht):
        card = lht.build(SINGLET_DOUBLET_LIKE_SPEC)
        m = re.search(
            r"^Block\s+BSMPARAMSIN\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE,
        )
        rows = []
        for line in m.group(1).splitlines():
            s = line.strip()
            mm = re.match(r"^(\d+)\s+\S+\s+#\s*(\S+)", s)
            if mm:
                rows.append((int(mm.group(1)), mm.group(2)))
        assert rows == [(1, "MS"), (2, "MPsi"), (3, "yh1"), (4, "yh2")], rows

    def test_non_input_params_excluded(self, lht):
        """Params with no les_houches (g1, Yu), string les_houches (ZN), or a
        non-input block (PhaseFS) never appear in MINPAR — the documented
        fallback that replaces silent misplacement."""
        card = lht.build(SINGLET_DOUBLET_LIKE_SPEC)
        # Only the 4 BSM inputs appear as MINPAR rows (parsed from the row
        # comments) — g1/Yu/ZN/PhaseFS never become card inputs. (Substring
        # checks on the whole card would false-positive on the fixed GAUGEIN
        # seed comment "# g1(M_Z)", which is an SM seed block, not this param.)
        names = {n for _, n in _minpar_rows(card)}
        assert names == {"MS", "MPsi", "yh1", "yh2"}
        bsm = re.search(
            r"^Block\s+BSMPARAMSIN\s*\n((?:.*\n)*?)(?=^Block|\Z)",
            card, re.IGNORECASE | re.MULTILINE,
        ).group(1)
        for excluded in ("g1", "Yu", "ZN", "PhaseFS"):
            assert excluded not in bsm, f"{excluded} leaked into BSMPARAMSIN"

    def test_input_scalar_params_mapping(self, lht):
        mapping = lht.input_scalar_params(SINGLET_DOUBLET_LIKE_SPEC)
        assert mapping == {"MS": 1, "MPsi": 2, "yh1": 3, "yh2": 4}

    def test_override_applied_at_declared_index(self, lht):
        card = lht.build(SINGLET_DOUBLET_LIKE_SPEC, overrides={"MS": 150.0})
        m = re.search(r"^\s+1\s+(\S+)\s+#\s*MS", card, re.MULTILINE)
        assert m and abs(float(m.group(1)) - 150.0) < 1e-9

    def test_index_collision_raises(self, lht):
        bad = {"name": "x", "parameters": [
            {"name": "P", "les_houches": ["BSMPARAMS", 1]},
            {"name": "Q", "les_houches": ["BSMPARAMS", 1]},
        ]}
        with pytest.raises(ValueError, match="collision"):
            lht.build(bad)


# ---------------------------------------------------------------------------
# Test: build() with empty parameters
# ---------------------------------------------------------------------------
class TestEmptyParameters:
    def test_no_minpar_when_no_params(self, lht):
        spec_no_params = {"name": "trivial", "parameters": []}
        card = lht.build(spec_no_params)
        # Should have MODSEL and SMINPUTS but no MINPAR (or empty MINPAR)
        assert re.search(r"^Block\s+MODSEL", card, re.IGNORECASE | re.MULTILINE)
        assert re.search(r"^Block\s+SMINPUTS", card, re.IGNORECASE | re.MULTILINE)
        # MINPAR block should be absent or empty
        minpar_match = re.search(r"^Block\s+MINPAR", card, re.IGNORECASE | re.MULTILINE)
        assert not minpar_match, "MINPAR should not appear when parameters list is empty"
