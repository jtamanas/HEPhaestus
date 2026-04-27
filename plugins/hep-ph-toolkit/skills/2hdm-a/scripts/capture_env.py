#!/usr/bin/env python3
"""
capture_env.py — Snapshot the runtime environment for a 2HDM+a playtest run.

Writes demo_output/2hdm-a/playtest_log/env.json with 8 required keys:
  config            — parsed config.json (sanitized: no secrets)
  git_sha_pre_run   — SHA of main before this run started (a05f274 or from main_sha.txt)
  git_sha_at_capture — current HEAD SHA at time of capture
  sarah_version     — SARAH version string (via wolframscript query)
  mg5_version       — MadGraph5 version string (via mg5_aMC --version)
  maddm_version     — MadDM version string (from MG5 plugin dir)
  python_version    — sys.version
  wolfram_version   — Wolfram Engine version (via wolframscript query)

Usage (from repo root):
  python3 plugins/hep-ph-toolkit/skills/2hdm-a/scripts/capture_env.py

Run from the worktree root where config.json lives.
"""

import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent.parent.parent
OUTPUT_PATH = REPO_ROOT / "demo_output" / "2hdm-a" / "playtest_log" / "env.json"
MAIN_SHA_FILE = REPO_ROOT / ".shift-manager" / "run-20260424-202956" / "scoping" / "main_sha.txt"
PRE_RUN_SHA_FALLBACK = "a05f274"


def _run(cmd, cwd=None, timeout=30):
    """Run a command, return stdout stripped or None on error."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def get_git_sha_pre_run() -> str:
    """Return the pre-run SHA from the scoping file, or the fallback."""
    if MAIN_SHA_FILE.exists():
        val = MAIN_SHA_FILE.read_text().strip()
        if val:
            return val
    return PRE_RUN_SHA_FALLBACK


def get_git_sha_at_capture() -> str:
    sha = _run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT))
    return sha or "unknown"


def _find_config_path() -> pathlib.Path | None:
    """Locate config.json using XDG-first read order:
    1. $XDG_CONFIG_HOME/hephaestus/config.json
    2. $HOME/.config/hephaestus/config.json
    3. repo-root config.json (legacy fallback)
    """
    xdg_home = os.environ.get("XDG_CONFIG_HOME", "")
    candidates = []
    if xdg_home:
        candidates.append(pathlib.Path(xdg_home) / "hephaestus" / "config.json")
    candidates.append(pathlib.Path.home() / ".config" / "hephaestus" / "config.json")
    candidates.append(REPO_ROOT / "config.json")
    for p in candidates:
        if p.exists():
            return p
    return None


def get_config() -> dict:
    """Load config.json (XDG-first), sanitize sensitive fields."""
    config_path = _find_config_path()
    if config_path is None:
        return {"error": "config.json not found (checked XDG, ~/.config, repo root)"}
    try:
        cfg = json.loads(config_path.read_text())
        # Sanitize: remove any key that looks like a secret or token
        sanitized = {
            k: v for k, v in cfg.items()
            if not any(s in k.lower() for s in ("token", "secret", "password", "key"))
        }
        sanitized["_config_source"] = str(config_path)
        return sanitized
    except json.JSONDecodeError as e:
        return {"error": f"config.json parse error: {e}"}


def _strip_styleform(s: str) -> str:
    """Strip Mathematica StyleForm[…] wrappers from a string.

    SARAH prints styled headers like:
      StyleForm[SARAH , Section, FontSize -> 14]StyleForm[4.15.3, Section, FontSize -> 14]
    We want just the bare content of the last StyleForm that looks like a version.
    Strategy: extract all StyleForm first-arguments, return the last version-like one,
    or fall back to removing all StyleForm[...] patterns via simple regex.
    """
    import re
    # Try to extract the first argument of every StyleForm[content, ...] occurrence
    # A version token looks like digits.digits.digits
    version_pat = re.compile(r'\d+\.\d+[\.\d]*')
    styleform_content_pat = re.compile(r'StyleForm\[([^,\]]+)')
    contents = styleform_content_pat.findall(s)
    for content in reversed(contents):
        content = content.strip()
        if version_pat.match(content):
            return content
    # Fallback: strip all StyleForm[...] wrappers entirely, keep bare text
    bare = re.sub(r'StyleForm\[[^\]]*\]', '', s).strip()
    if bare:
        return bare
    return s


def get_sarah_version(wolfram_path: str | None = None) -> str:
    """Query SARAH version via wolframscript. Strips StyleForm wrappers."""
    cmd = ["wolframscript", "-code",
           'Needs["SARAH`"]; Print[$SARAHVersion]; Quit[]']
    if wolfram_path:
        cmd[0] = wolfram_path
    result = _run(cmd, timeout=60)
    if result:
        # Extract version line (may have Mathematica banner before it)
        for line in result.splitlines():
            line = line.strip()
            if not line or line.startswith("Mathematica"):
                continue
            # Strip any StyleForm wrappers that SARAH emits
            cleaned = _strip_styleform(line)
            if cleaned:
                return cleaned
    return "unavailable"


def get_wolfram_version(wolfram_path: str | None = None) -> str:
    """Query Wolfram Engine version via wolframscript."""
    cmd = ["wolframscript", "-code",
           'Print[$VersionNumber]; Quit[]']
    if wolfram_path:
        cmd[0] = wolfram_path
    result = _run(cmd, timeout=30)
    return result.splitlines()[0] if result else "unavailable"


def _resolve_mg5_bin(mg5_path: str) -> str | None:
    """Given madgraph_path from config (may be the binary itself or a directory),
    return the path to the mg5_aMC binary if it exists."""
    p = pathlib.Path(mg5_path)
    if p.is_file():
        # madgraph_path points directly to the binary
        return str(p)
    if p.is_dir():
        candidate = p / "bin" / "mg5_aMC"
        if candidate.exists():
            return str(candidate)
    return None


def get_mg5_version(mg5_path: str | None = None, cfg: dict | None = None) -> str:
    """Get MadGraph5 version.

    Probe order:
    1. If config has madgraph_version key, use it directly (avoids slow MG5 startup).
    2. Resolve mg5_aMC binary from madgraph_path (handles both dir and binary paths).
    3. Try system mg5_aMC.
    """
    # Use version recorded in config if available
    if cfg and isinstance(cfg, dict) and cfg.get("madgraph_version"):
        return str(cfg["madgraph_version"])
    if mg5_path:
        bin_path = _resolve_mg5_bin(mg5_path)
        if bin_path:
            result = _run([bin_path, "--version"], timeout=30)
            if result:
                return result.splitlines()[0]
    # Try system mg5_aMC
    result = _run(["mg5_aMC", "--version"], timeout=30)
    if result:
        return result.splitlines()[0]
    return "unavailable"


def get_maddm_version(mg5_path: str | None = None, cfg: dict | None = None) -> str:
    """Detect MadDM version.

    Probe order:
    1. If config has maddm_version key, use it directly.
    2. If config has maddm_path, look for version file there.
    3. Try to find MadDM under the MG5 root (PLUGIN/maddm, models/maddm, MadDM).
    """
    # Use version recorded in config if available
    if cfg and isinstance(cfg, dict) and cfg.get("maddm_version"):
        return str(cfg["maddm_version"])
    # Check maddm_path from config
    maddm_path = cfg.get("maddm_path") if cfg and isinstance(cfg, dict) else None
    candidates_dirs = []
    if maddm_path:
        candidates_dirs.append(pathlib.Path(maddm_path))
    if mg5_path:
        mg5_dir = pathlib.Path(mg5_path)
        if mg5_dir.is_file():
            mg5_dir = mg5_dir.parent.parent  # bin/mg5_aMC -> MG5 root
        for subpath in ("PLUGIN/maddm", "models/maddm", "MadDM"):
            candidates_dirs.append(mg5_dir / subpath)
    for candidate in candidates_dirs:
        if candidate.exists():
            for vfile in ("__version__.py", "version.py", "VERSION"):
                vpath = candidate / vfile
                if vpath.exists():
                    content = vpath.read_text()
                    for line in content.splitlines():
                        if "version" in line.lower() and "=" in line:
                            return line.split("=")[-1].strip().strip('"\'')
            return f"found at {candidate} (version file absent)"
    return "unavailable"


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cfg = get_config()
    wolfram_path = cfg.get("wolfram_engine_path") if isinstance(cfg, dict) else None
    mg5_path = cfg.get("madgraph_path") if isinstance(cfg, dict) else None

    env = {
        "config": cfg,
        "git_sha_pre_run": get_git_sha_pre_run(),
        "git_sha_at_capture": get_git_sha_at_capture(),
        "sarah_version": get_sarah_version(wolfram_path),
        "mg5_version": get_mg5_version(mg5_path, cfg=cfg),
        "maddm_version": get_maddm_version(mg5_path, cfg=cfg),
        "python_version": sys.version,
        "wolfram_version": get_wolfram_version(wolfram_path),
    }

    OUTPUT_PATH.write_text(json.dumps(env, indent=2))
    print(f"[capture_env] Wrote {OUTPUT_PATH}")
    print(f"  git_sha_pre_run:    {env['git_sha_pre_run']}")
    print(f"  git_sha_at_capture: {env['git_sha_at_capture']}")
    print(f"  python_version:     {env['python_version'].splitlines()[0]}")
    print(f"  wolfram_version:    {env['wolfram_version']}")
    print(f"  sarah_version:      {env['sarah_version']}")
    print(f"  mg5_version:        {env['mg5_version']}")
    print(f"  maddm_version:      {env['maddm_version']}")


if __name__ == "__main__":
    main()
