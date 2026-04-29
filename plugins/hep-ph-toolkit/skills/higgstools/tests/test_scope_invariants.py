"""
test_scope_invariants.py — grep-based invariant tests for scope gates.

Enforces:
1. no-cpv: no CPViolation/complex_mixing/cpv in scripts/
2. no-native-backend: no --native/native_input in scripts/
3. no-unified-default: --backend=unified is never the argparse default
4. no-ndf-synthesis: ndf is never computed from len(channels) in p_value.py

These are static invariants enforced by grepping the source files.
"""
import subprocess
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"


def _grep(pattern: str, path: str, flags: list[str] | None = None) -> list[str]:
    """Run grep -E and return matching lines. Empty list = no matches."""
    cmd = ["grep", "-rn", "-E"] + (flags or []) + [pattern, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # grep returns 0 if matches found, 1 if no matches, 2 on error
    if result.returncode == 2:
        raise RuntimeError(f"grep error: {result.stderr}")
    return [line for line in result.stdout.splitlines() if line.strip()]


class TestScopeInvariants:
    """Static invariant tests via grep."""

    def test_no_cpv_in_scripts(self):
        """No CPViolation, complex_mixing, or cpv in scripts/ (v1 scope: CP-conserving only)."""
        matches = _grep(r"CPViolation\|complex_mixing\|cpv", str(SCRIPTS_DIR))
        assert len(matches) == 0, (
            "CPV references found in scripts/ (v1 scope: CP-conserving only):\n"
            + "\n".join(matches)
        )

    def test_no_native_backend_in_scripts(self):
        """No --native or native_input in scripts/ (dropped per manager decision)."""
        # Use Python re directly to avoid grep issues with '--native' looking like a flag
        import re
        for script in SCRIPTS_DIR.glob("*"):
            if not script.is_file():
                continue
            content = script.read_text(errors="replace")
            bad_matches = re.findall(r"--native|native_input", content)
            assert len(bad_matches) == 0, (
                f"'--native' or 'native_input' found in {script.name} (dropped in v1): {bad_matches}"
            )

    def test_no_unified_default_in_cli(self):
        """
        --backend=unified is never the argparse default.

        The argparse default for --backend must be None or 'legacy', never 'unified'.
        Unified is opt-in only via HEPPH_HIGGSTOOLS_BACKEND env var + explicit flag.
        """
        run_script = SCRIPTS_DIR / "run_higgstools.py"
        assert run_script.exists(), f"run_higgstools.py not found at {run_script}"
        content = run_script.read_text()

        # Check: default="unified" not present in argument parsing
        import re
        # Look for patterns like default="unified" or default='unified'
        # near --backend argument definition
        bad_patterns = [
            r'default\s*=\s*["\']unified["\']',
            r'default=unified',
        ]
        for pattern in bad_patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, (
                f"Found '{pattern}' in run_higgstools.py — "
                f"unified must never be the default backend: {matches}"
            )

    def test_no_ndf_from_len_channels_in_p_value(self):
        """
        ndf is never computed as len(channels) in p_value.py.

        (chi2, ndf) must come from HS native output, not Python-side channel count.
        """
        p_value_script = SCRIPTS_DIR / "p_value.py"
        assert p_value_script.exists(), f"p_value.py not found at {p_value_script}"

        # Use Python re directly for this check to avoid grep parentheses issues
        import re
        content = p_value_script.read_text()
        bad_matches = re.findall(r"ndf\s*=\s*len\(", content)
        assert len(bad_matches) == 0, (
            "ndf = len(...) found in p_value.py — ndf must come from HS native output:\n"
            + "\n".join(bad_matches)
        )

    def test_no_reference_only_exits(self):
        """No reference_only exit path in scripts/."""
        matches = _grep(r"reference_only", str(SCRIPTS_DIR))
        assert len(matches) == 0, (
            "'reference_only' found in scripts/ (no analytic fallback in v1):\n"
            + "\n".join(matches)
        )

    def test_no_gitlab_archive_tarballs_in_install(self):
        """No GitLab archive tarball URLs in install scripts.

        Post-2026-04-29 refactor: install logic lives at
        plugins/hep-ph-toolkit/_shared/installs/higgstools/, not at
        plugins/hep-ph-toolkit/skills/higgstools-install/scripts/.
        """
        install_scripts_dir = (
            SKILL_DIR.parent.parent / "_shared" / "installs" / "higgstools"
        )
        assert install_scripts_dir.exists(), (
            f"Expected {install_scripts_dir} to exist after install-skill refactor"
        )
        matches = _grep(r"archive/.*\.tar\.gz", str(install_scripts_dir))
        assert len(matches) == 0, (
            "GitLab archive tarball URLs found (use git clone, not tarballs):\n"
            + "\n".join(matches)
        )

    def test_all_error_codes_have_higgstools_prefix(self):
        """All SLHA error codes in scripts start with HIGGSTOOLS_."""
        content_files = list(SCRIPTS_DIR.glob("*.py")) + list(SCRIPTS_DIR.glob("*.sh"))
        for f in content_files:
            text = f.read_text()
            import re
            # Find emit_blocker calls and _emit_blocker calls
            # Pattern: HIGGSTOOLS_ or similar
            codes = re.findall(r'"((?:HIGGSTOOLS|SARAH|SPHENO|MICROMEGAS|DDCALC)_[A-Z_]+)"', text)
            for code in codes:
                if "HIGGSTOOLS" not in code and any(
                    prefix in code for prefix in ("SARAH_", "SPHENO_", "MICROMEGAS_", "DDCALC_")
                ):
                    pytest.fail(
                        f"Non-HIGGSTOOLS_ error code '{code}' found in {f.name}"
                    )

    def test_no_analytic_fallback_in_slha_adapter(self):
        """slha_adapter.py has no Python-synthesized effective couplings."""
        slha_script = SCRIPTS_DIR / "slha_adapter.py"
        assert slha_script.exists()
        # Should not compute effective couplings from mixing angles in Python
        matches = _grep(r"effective_coupling\|sin_alpha\|cos_alpha.*\*.*sin_beta", str(slha_script))
        assert len(matches) == 0, (
            "Analytic coupling synthesis found in slha_adapter.py:\n"
            + "\n".join(matches)
        )
