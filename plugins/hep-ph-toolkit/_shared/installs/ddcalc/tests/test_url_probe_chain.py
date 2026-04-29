"""
Unit test: _probe_url.sh URL chain logic.
Tests: 404+200 sequence → first-200-wins, DDCALC_UPSTREAM_UNREACHABLE on exhaustion.
"""
import os
import subprocess
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR
PROBE_URL_SH = SCRIPTS_DIR / "_probe_url.sh"


def make_skill_env(tmp_dir: Path, urls: list) -> str:
    """Return YAML content for a minimal skill_env.yaml with given mirror URLs."""
    yaml_content = "HEPPH_DDCALC_VERSION: '2.2.0'\n"
    yaml_content += "HEPPH_DDCALC_URL: 'https://primary.example.com/ddcalc.tgz'\n"
    yaml_content += "HEPPH_DDCALC_SHA256: 'abc123'\n"
    yaml_content += "HEPPH_DDCALC_FETCH_DATE: '2026-04-19'\n"
    yaml_content += "HEPPH_DDCALC_UPSTREAM_COMMIT: 'abc'\n"
    yaml_content += "HEPPH_DDCALC_MIRROR_URLS:\n"
    for url in urls:
        yaml_content += f"  - '{url}'\n"
    return yaml_content


def make_mock_curl(tmp_dir: Path, responses: dict) -> Path:
    """
    Create a mock 'curl' that returns specific HTTP codes based on the URL.
    responses: dict mapping URL-fragment → HTTP status code, e.g.
      {'primary': 404, 'mirror': 200}
    Falls back to 404 if no key matches.
    """
    entries = []
    for fragment, code in responses.items():
        entries.append(f"  [[ \"$@\" == *'{fragment}'* ]] && {{ echo 'HTTP/2 {code}'; exit {0 if code == 200 else 22}; }}")

    script = "#!/usr/bin/env bash\n"
    for entry in entries:
        script += entry + "\n"
    script += "echo 'HTTP/2 404'\nexit 22\n"

    mock_curl = tmp_dir / "curl"
    mock_curl.write_text(script)
    mock_curl.chmod(0o755)
    return mock_curl


def run_probe(skill_env_content: str, mock_bin_dir: Path | None = None, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    """Run _probe_url.sh with a custom skill_env.yaml, replacing the real one temporarily."""
    orig_env_path = SKILL_DIR / "skill_env.yaml"
    backup = orig_env_path.read_bytes() if orig_env_path.exists() else None

    env = {
        "HOME": os.environ.get("HOME", "/tmp"),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    }
    if mock_bin_dir:
        env["PATH"] = str(mock_bin_dir) + ":" + env["PATH"]
    if extra_env:
        env.update(extra_env)

    try:
        orig_env_path.write_text(skill_env_content)
        return subprocess.run(
            ["bash", str(PROBE_URL_SH)],
            capture_output=True,
            text=True,
            env=env,
        )
    finally:
        if backup is not None:
            orig_env_path.write_bytes(backup)
        elif orig_env_path.exists():
            orig_env_path.unlink()


class TestUrlProbeChain:
    def test_first_200_wins(self, tmp_path):
        """First URL returns 404, second returns 200 → second URL is printed."""
        urls = [
            "https://primary.example.com/ddcalc.tgz",
            "https://mirror.example.com/ddcalc.tgz",
            "https://fallback.example.com/ddcalc.tgz",
        ]
        skill_env = make_skill_env(tmp_path, urls)
        make_mock_curl(tmp_path, {"primary.example.com": 404, "mirror.example.com": 200})

        result = run_probe(skill_env, mock_bin_dir=tmp_path)
        stdout = result.stdout.strip()
        assert "mirror.example.com" in stdout, (
            f"Expected mirror URL (first 200), got: {stdout!r}\n"
            f"stderr: {result.stderr}"
        )

    def test_all_404_returns_unreachable_blocker(self, tmp_path):
        """All URLs return 404 → DDCALC_UPSTREAM_UNREACHABLE on stderr, non-zero exit."""
        urls = [
            "https://primary.example.com/ddcalc.tgz",
            "https://mirror.example.com/ddcalc.tgz",
        ]
        skill_env = make_skill_env(tmp_path, urls)
        make_mock_curl(tmp_path, {})  # no matches → all 404

        result = run_probe(skill_env, mock_bin_dir=tmp_path)
        assert result.returncode != 0, "Should fail when all URLs are 404"
        assert "DDCALC_UPSTREAM_UNREACHABLE" in result.stderr, (
            f"Expected unreachable blocker in stderr: {result.stderr!r}"
        )

    def test_dry_run_returns_first_url(self, tmp_path):
        """--dry-run mode returns the first URL without probing."""
        urls = ["https://primary.example.com/ddcalc.tgz"]
        skill_env = make_skill_env(tmp_path, urls)

        orig_env_path = SKILL_DIR / "skill_env.yaml"
        backup = orig_env_path.read_bytes() if orig_env_path.exists() else None
        try:
            orig_env_path.write_text(skill_env)
            result = subprocess.run(
                ["bash", str(PROBE_URL_SH), "--dry-run"],
                capture_output=True,
                text=True,
                env={"HOME": os.environ.get("HOME", "/tmp"), "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
            assert result.returncode == 0, f"Dry run should exit 0: {result.stderr}"
            assert "primary.example.com" in result.stdout, (
                f"Expected primary URL in dry-run output: {result.stdout!r}"
            )
        finally:
            if backup is not None:
                orig_env_path.write_bytes(backup)
