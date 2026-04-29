"""
Unit test: apply_overlay.sh behaviour.
- stub overlay (deferred: v1.1) emits DDCALC_OVERLAY_APPLY_FAILED with
  DDCALC_OVERLAY_NOT_SUPPORTED_V1 tag.
- missing overlay directory emits DDCALC_OVERLAY_MISSING.
"""
import os
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR
APPLY_OVERLAY_SH = SCRIPTS_DIR / "apply_overlay.sh"
OVERLAYS_DIR = SKILL_DIR / "overlays"


def run_overlay(src_dir: str, overlay_name: str, env: dict | None = None):
    full_env = {"HOME": os.environ.get("HOME", "/tmp"), "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    if env:
        full_env.update(env)
    return subprocess.run(
        ["bash", str(APPLY_OVERLAY_SH), src_dir, overlay_name],
        capture_output=True,
        text=True,
        env=full_env,
    )


class TestOverlayApply:
    def test_deferred_overlay_emits_not_supported_v1(self, tmp_path):
        """The stub lz_xenonnt_pandax4t_2024 overlay has deferred: v1.1 → DDCALC_OVERLAY_NOT_SUPPORTED_V1."""
        result = run_overlay(str(tmp_path), "lz_xenonnt_pandax4t_2024")
        assert result.returncode != 0, "Deferred overlay should fail"
        assert "DDCALC_OVERLAY_NOT_SUPPORTED_V1" in result.stderr, (
            f"Expected NOT_SUPPORTED_V1 in stderr: {result.stderr!r}"
        )
        assert "DDCALC_OVERLAY_APPLY_FAILED" in result.stderr, (
            f"Expected APPLY_FAILED code in stderr: {result.stderr!r}"
        )

    def test_missing_overlay_emits_missing_blocker(self, tmp_path):
        """Non-existent overlay → DDCALC_OVERLAY_MISSING blocker."""
        result = run_overlay(str(tmp_path), "nonexistent_overlay_xyz")
        assert result.returncode != 0, "Missing overlay should fail"
        assert "DDCALC_OVERLAY_MISSING" in result.stderr, (
            f"Expected OVERLAY_MISSING in stderr: {result.stderr!r}"
        )

    def test_non_deferred_overlay_proceeds(self, tmp_path):
        """A manifest without deferred flag proceeds to patch application."""
        # Create a minimal non-deferred overlay
        overlay_dir = tmp_path / "overlays" / "test_overlay"
        overlay_dir.mkdir(parents=True)
        (overlay_dir / "patches").mkdir()
        (overlay_dir / "data").mkdir()

        manifest = overlay_dir / "manifest.yaml"
        manifest.write_text(
            "upstream_ddcalc_commit: abc123\n"
            "experiments: []\n"
        )

        # Patch OVERLAYS_DIR and SHARED_COMMON in apply_overlay.sh by creating a modified version
        # SKILL_DIR is plugins/hep-ph-toolkit/_shared/installs/ddcalc.
        # Go up 4 (ddcalc → installs → _shared → hep-ph-toolkit → plugins),
        # then shared/install-helpers/_common.sh.
        common_sh_path = (SKILL_DIR.parent.parent.parent.parent / "shared" / "install-helpers" / "_common.sh").resolve()
        apply_content = APPLY_OVERLAY_SH.read_text()
        patched_apply = tmp_path / "apply_overlay_test.sh"
        # Replace OVERLAYS_DIR and SHARED_COMMON references
        patched_content = apply_content.replace(
            'OVERLAYS_DIR="$SCRIPT_DIR/../overlays"',
            f'OVERLAYS_DIR="{tmp_path}/overlays"',
        ).replace(
            'SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"',
            f'SHARED_COMMON="{common_sh_path}"',
        )
        patched_apply.write_text(patched_content)
        patched_apply.chmod(0o755)

        src_dir = tmp_path / "src"
        src_dir.mkdir()

        env = {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        }
        result = subprocess.run(
            ["bash", str(patched_apply), str(src_dir), "test_overlay"],
            capture_output=True,
            text=True,
            env=env,
        )
        # Should NOT emit DDCALC_OVERLAY_NOT_SUPPORTED_V1
        assert "DDCALC_OVERLAY_NOT_SUPPORTED_V1" not in result.stderr, (
            f"Non-deferred overlay should NOT emit v1 gate: {result.stderr!r}"
        )
        # Should succeed (no patches to apply, no rejects)
        assert result.returncode == 0, (
            f"Non-deferred overlay with empty experiment list should exit 0: "
            f"{result.stderr!r}"
        )
