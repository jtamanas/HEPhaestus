"""
test_phasefs_init_patch.py — Unit tests for ``_patch_phasefs_init``.

Covers the post-SARAH patch that initialises ``PhaseFS`` to unit inside
``Set_All_Parameters_0`` in ``Model_Data_<Name>.f90``. Without this patch
SARAH ships ``PhaseFS = 0._dp`` and never assigns the variable anywhere
else (``Read_PHASESIN`` discards the value, and the only other writes are
sign-flips gated on a negative mass eigenvalue). The zero prefactor
collapses every singlet/doublet entry of the neutralino mass matrix to
zero, producing a spurious ``(0, MPsi, MPsi)`` spectrum for the Singlet-
Doublet benchmark.

Asserts:
    - Init line ``PhaseFS = 0._dp`` is rewritten to ``PhaseFS = 1._dp``.
    - Rewrite is idempotent (second call is a no-op, returns False).
    - Absence of any ``PhaseFS = 0._dp`` line is a no-op.
    - Only the exact zero-init matches — any sign-flip assignments
      (``PhaseFS = -1._dp``) or iteration-guarded updates are left alone.
    - Files that don't exist (no ``Model_Data_<Name>.f90``) return False.
"""

import importlib.util
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
def compile_mod():
    return _load_module("compile_model", _SCRIPTS / "compile_model.py")


# Shape of SARAH's ``Set_All_Parameters_0`` that we need to patch.
_BROKEN_MODULE_DATA = """\
Module Model_Data_Sample
Implicit None
Complex(dp) :: PhaseFS,ZN(3,3)
Real(dp) :: MS,MPsi,yh1,yh2,vvSM

Contains

Subroutine Set_All_Parameters_0()
Implicit None
MS = 0._dp
MPsi = 0._dp
yh1 = 0._dp
yh2 = 0._dp
vvSM = 0._dp
PhaseFS = 0._dp
ZN = 0._dp
End Subroutine Set_All_Parameters_0

End Module Model_Data_Sample
"""

_ALREADY_FIXED = _BROKEN_MODULE_DATA.replace(
    "PhaseFS = 0._dp", "PhaseFS = 1._dp"
)


class TestPhaseFsPatch:
    def test_patches_zero_init_to_one(self, compile_mod, tmp_path):
        """Matches the exact init line and rewrites to 1._dp."""
        (tmp_path / "Model_Data_Sample.f90").write_text(_BROKEN_MODULE_DATA)
        changed = compile_mod._patch_phasefs_init(tmp_path, "Sample")
        assert changed is True
        text = (tmp_path / "Model_Data_Sample.f90").read_text()
        assert "PhaseFS = 1._dp" in text
        assert "PhaseFS = 0._dp" not in text

    def test_idempotent(self, compile_mod, tmp_path):
        """Second call is a no-op."""
        (tmp_path / "Model_Data_Sample.f90").write_text(_ALREADY_FIXED)
        changed = compile_mod._patch_phasefs_init(tmp_path, "Sample")
        assert changed is False
        # Value unchanged
        text = (tmp_path / "Model_Data_Sample.f90").read_text()
        assert "PhaseFS = 1._dp" in text

    def test_missing_file_is_noop(self, compile_mod, tmp_path):
        """No Model_Data_<Name>.f90 → returns False without raising."""
        # tmp_path has no Model_Data_Missing.f90 file
        changed = compile_mod._patch_phasefs_init(tmp_path, "Missing")
        assert changed is False

    def test_leaves_sign_flip_assignments_alone(self, compile_mod, tmp_path):
        """Only the exact ``= 0._dp`` init is rewritten; ``-1._dp`` is kept.

        SARAH emits sign-flip reassignments like ``PhaseFS = -1._dp`` and
        ``PhaseFS = -PhaseFS`` downstream for negative-mass ambiguity
        resolution. Those must stay intact.
        """
        source = _BROKEN_MODULE_DATA + """
Subroutine FlipSign()
PhaseFS = -1._dp
End Subroutine FlipSign
"""
        (tmp_path / "Model_Data_Sample.f90").write_text(source)
        compile_mod._patch_phasefs_init(tmp_path, "Sample")
        text = (tmp_path / "Model_Data_Sample.f90").read_text()
        # Init rewritten, sign-flip preserved.
        assert "PhaseFS = 1._dp" in text
        assert "PhaseFS = -1._dp" in text

    def test_absent_init_line_is_noop(self, compile_mod, tmp_path):
        """Model_Data with no PhaseFS init line → returns False."""
        src = _BROKEN_MODULE_DATA.replace("PhaseFS = 0._dp\n", "")
        (tmp_path / "Model_Data_Sample.f90").write_text(src)
        changed = compile_mod._patch_phasefs_init(tmp_path, "Sample")
        assert changed is False
