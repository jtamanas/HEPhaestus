"""
test_rank1_dirac_patch.py — Unit tests for ``_patch_rank1_dirac_mass``.

Covers the W4 post-SARAH patch that demotes rank-1 length-1 single-eigenstate
Dirac masses (e.g. singlet-doublet ``MFChiM``) to scalar so they match the
module-level declaration used at callers. See ``sarah-workarounds.md`` §16
for the upstream SARAH inconsistency this papers over.

Asserts:
    - Patch rewrites every rank-1 callee Intent(out), module-private cache,
      OneLoop* output, and InputOutput guard shape for the affected mass.
    - Rewrite is idempotent (second call is a no-op).
    - Mass names that are legitimately rank-1 at module level (e.g. MFChi(3))
      are left untouched.
    - The comment-string label ``"# MFChiM(1) "`` that SARAH emits as a SLHA
      block label is NOT rewritten (only executable ``If (MFChiM(1)...`` guards).
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

_HERE = Path(__file__).parent
_SCRIPTS = _HERE.parent / "scripts"
_FIXTURES = _HERE / "fixtures" / "rank1_dirac"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def compile_mod():
    return _load_module("compile_model", _SCRIPTS / "compile_model.py")


@pytest.fixture
def model_src(tmp_path):
    """Copy the ``before`` fixture tree into a scratch dir, renamed to Rank1Fix."""
    dst = tmp_path / "Rank1Fix"
    shutil.copytree(_FIXTURES / "before", dst)
    return dst


class TestModuleScalarFilter:
    def test_mfchim_detected_as_scalar(self, compile_mod, model_src):
        """``MFChiM`` is in the grouped module decl without ``(…)`` → scalar."""
        names = compile_mod._module_scalar_mass_names(model_src, "Rank1Fix")
        assert "MFChiM" in names
        assert "MFChiM2" in names

    def test_mfchi_with_extent_skipped(self, compile_mod, model_src):
        """``MFChi(3)`` / ``MFChi2(3)`` carry an extent → NOT scalar."""
        names = compile_mod._module_scalar_mass_names(model_src, "Rank1Fix")
        assert "MFChi" not in names
        assert "MFChi2" not in names
        assert "MFd" not in names  # MFd(3)

    def test_missing_file_returns_empty(self, compile_mod, tmp_path):
        """Absent Model_Data file → empty set, no crash."""
        names = compile_mod._module_scalar_mass_names(tmp_path, "NoSuchModel")
        assert names == set()


class TestRank1DiracDemotion:
    def test_patches_all_expected_files(self, compile_mod, model_src):
        patched = compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        assert "TreeLevelMasses_Rank1Fix.f90" in patched
        assert "LoopMasses_Rank1Fix.f90" in patched
        assert "InputOutput_Rank1Fix.f90" in patched
        # Every reported file should name MFChiM as the demoted mass.
        for fname, masses in patched.items():
            assert "MFChiM" in masses, f"{fname}: {masses!r}"

    def test_tree_level_masses_rewrites(self, compile_mod, model_src):
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        text = (model_src / "TreeLevelMasses_Rank1Fix.f90").read_text()
        # Rank-1 Intent(out) is gone.
        assert "Intent(out) :: MFChiM(1)" not in text
        # Scalar Intent(out) is present in both Calculate bodies.
        assert text.count("Real(dp), Intent(out) :: MFChiM\n") == 2
        # Sqrt tail assignments index into rank-1 ``MFChiM2(1)``.
        assert text.count("MFChiM = Sqrt( MFChiM2(1) )") == 2
        # Local rank-1 ``MFChiM2(1)`` is intentionally KEPT (EigenSystem needs
        # a vector; the fixture elides the call but the shape must survive).
        assert "MFChiM2(1)" in text

    def test_loop_masses_rewrites(self, compile_mod, model_src):
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        text = (model_src / "LoopMasses_Rank1Fix.f90").read_text()
        # Module-private cache demoted.
        assert "Real(dp), Private :: MFChiM_1L, MFChiM2_1L" in text
        assert "MFChiM_1L(1)" not in text
        assert "MFChiM2_1L(1)" not in text
        # OneLoopFChiM Intent(out) demoted.
        assert "Intent(out) :: MFChiM_1L,MFChiM2_1L" in text
        # ``(il)`` indexing on the scalar caches stripped.
        assert "MFChiM2_1L(il)" not in text
        assert "MFChiM_1L(il)" not in text
        # But the genuine rank-1 temp ``MFChiM2_t(il)`` is preserved — it
        # feeds EigenSystem in the real file, can't be demoted.
        assert "MFChiM2_t(il)" in text

    def test_input_output_guards_rewritten(self, compile_mod, model_src):
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        text = (model_src / "InputOutput_Rank1Fix.f90").read_text()
        # Guards are demoted.
        assert "If (MFChiM(1).Gt." not in text
        assert text.count("If (MFChiM.Gt.0._dp)") == 2
        # The SLHA-label comment string is untouched — the ``(1)`` here is
        # part of a human-readable label, not executable rank-1 indexing.
        assert '"# MFChiM(1) "' in text


class TestIdempotence:
    def test_second_call_is_noop(self, compile_mod, model_src):
        first = compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        second = compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        assert first, "First pass should report patches"
        assert second == {}, f"Second pass must be a no-op; got {second!r}"

    def test_content_unchanged_after_second_pass(self, compile_mod, model_src):
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        snapshot = {
            p.name: p.read_text()
            for p in model_src.iterdir()
            if p.suffix == ".f90"
        }
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        for p in model_src.iterdir():
            if p.suffix != ".f90":
                continue
            assert p.read_text() == snapshot[p.name], (
                f"{p.name} changed on second patch pass — not idempotent"
            )


class TestSafetyFilter:
    def test_no_rank1_decls_means_no_op(self, compile_mod, tmp_path):
        """If the tree has no rank-1 Intent(out) masses, the patch is a no-op."""
        # Scalar-only fixture: strip the ``(1)`` suffixes from a copy, run the
        # patch, expect no rewrites.
        src = tmp_path / "Clean"
        shutil.copytree(_FIXTURES / "before", src)
        tlm = src / "TreeLevelMasses_Rank1Fix.f90"
        tlm.write_text(
            tlm.read_text()
            .replace("Intent(out) :: MFChiM(1)", "Intent(out) :: MFChiM")
            .replace("MFChiM2(1)", "MFChiM2")
        )
        lm = src / "LoopMasses_Rank1Fix.f90"
        lm.write_text(
            lm.read_text()
            .replace("MFChiM_1L(1), MFChiM2_1L(1)", "MFChiM_1L, MFChiM2_1L")
            .replace("MFChiM_1L(1),MFChiM2_1L(1)", "MFChiM_1L,MFChiM2_1L")
            .replace("MFChiM2_1L(il)", "MFChiM2_1L")
            .replace("MFChiM_1L(il)", "MFChiM_1L")
        )
        io = src / "InputOutput_Rank1Fix.f90"
        io.write_text(io.read_text().replace("MFChiM(1).Gt.", "MFChiM.Gt."))
        patched = compile_mod._patch_rank1_dirac_mass(src, "Rank1Fix")
        assert patched == {}

    def test_unrelated_mass_untouched(self, compile_mod, model_src):
        """``MFChi(3)`` stays as ``MFChi(3)`` — the filter excludes rank-3 masses."""
        compile_mod._patch_rank1_dirac_mass(model_src, "Rank1Fix")
        md = (model_src / "Model_Data_Rank1Fix.f90").read_text()
        assert "MFChi(3)" in md
        assert "MFd(3)" in md
