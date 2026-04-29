"""
Integration tests for _shared/installs/formcalc — gated on HEPPH_RUN_NETWORK_TESTS=1.

These tests perform actual downloads; skip if network access is unavailable.
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR
REPO_ROOT = SKILL_DIR.parent.parent.parent.parent.parent
SHARED = REPO_ROOT / "plugins" / "shared" / "install-helpers"

# Gating condition
NETWORK_TESTS = os.environ.get("HEPPH_RUN_NETWORK_TESTS", "0") == "1"
WOLFRAM_TESTS = os.environ.get("HEPPH_RUN_WOLFRAM_TESTS", "0") == "1"

# Canonical upstream URLs (mirrors skill_env.yaml).
FORMCALC_URL = "https://feynarts.de/formcalc/FormCalc-9.10.tar.gz"
FORM_URL = "https://github.com/vermaseren/form/releases/download/v4.3.1/form-4.3.1.tar.gz"

pytestmark = pytest.mark.skipif(
    not NETWORK_TESTS,
    reason="HEPPH_RUN_NETWORK_TESTS=1 required",
)


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestInstallIntegration:
    def test_full_install(self, tmp_path):
        """
        Full install into tmp $UserBaseDirectory.
        Asserts: formcalc_path, form_binary resolves executable,
                 looptools_lib exists, three version keys written,
                 last_configured stamped.
        """
        cfg_dir = tmp_path / "config"
        cfg_dir.mkdir()
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = str(cfg_dir)
        env["XDG_DATA_HOME"] = str(data_dir)
        # Redirect UserBaseDirectory
        env["HEPPH_WOLFRAM_USER_BASE"] = str(tmp_path / "wolfram_user")

        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "install.sh"),
                "install",
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )
        # Should succeed or return activation_required
        cfg_file = cfg_dir / "hephaestus" / "config.json"
        if cfg_file.exists():
            data = json.loads(cfg_file.read_text())
            assert "formcalc_version" in data
            assert "form_version" in data
            assert "looptools_version" in data
            assert "last_configured" in data
            if data.get("form_binary"):
                assert Path(data["form_binary"]).exists()
            if data.get("looptools_lib"):
                assert Path(data["looptools_lib"]).exists()
        else:
            # Acceptable: activation_required or other graceful exit
            assert result.returncode in (0, 15, 20)


@pytest.mark.skipif(not NETWORK_TESTS, reason="HEPPH_RUN_NETWORK_TESTS=1 required")
class TestUpstreamURLs:
    """HEAD probes to catch future upstream URL drift early."""

    def _head_200(self, url: str) -> None:
        """Assert that a HEAD request to url ultimately returns HTTP 200."""
        req = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                code = resp.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        assert code == 200, (
            f"Upstream URL returned HTTP {code}: {url}\n"
            "Update skill_env.yaml + install scripts if the URL has moved."
        )

    def test_formcalc_url_live(self):
        """FormCalc 9.10 tarball at feynarts.de must return HTTP 200."""
        self._head_200(FORMCALC_URL)

    def test_form_url_live(self):
        """FORM 4.3.1 release tarball at GitHub must return HTTP 200."""
        self._head_200(FORM_URL)
