"""run_feynarts.py — top-level driver for /feynarts generate.

Orchestrates:
  1. Prerequisite checks (FeynArts installed, Wolfram present).
  2. Model resolution (builtin / file / SARAH).
  3. Process resolution (alias / raw tuple).
  4. Optional post-hoc SARAH MakeFeynArts[] (if --sarah-model).
  5. Cache probe.
  6. Template rendering + wolframscript execution (timeout enforced).
  7. Postprocessing (size-cap check, JSON sidecars).
  8. Cache write.

Exit codes:
  0  — success
  1  — fatal blocker (JSON on stderr)
  2  — FEYNARTS_TOO_MANY_DIAGRAMS (emitted from Mathematica, caught here)
  3  — FEYNARTS_TIMEOUT
  4  — FEYNARTS_AMP_TOO_LARGE
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

# Script directory — used to locate templates and sibling modules
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

from cache_key import compute_cache_key
from postprocess import PostprocessError, postprocess_output
from render_driver import render_driver, render_make_feynarts_driver
from resolve_model import ModelResolutionError, resolve_model
from resolve_process import ProcessResolutionError, resolve_process

_DEFAULT_STATE_ROOT = os.path.expanduser(
    os.environ.get("HEPPH_FEYNARTS_STATE_ROOT", "~/.local/share/hephaestus")
)


def _blocker(code: str, message: str, context: Optional[dict] = None, exit_code: int = 1) -> None:
    """Emit a blocker JSON to stderr and exit."""
    b: dict = {"code": code, "mode": "fatal", "message": message}
    if context:
        b["context"] = context
    print(json.dumps(b, separators=(",", ":")), file=sys.stderr)
    sys.exit(exit_code)


def _read_config(key: str) -> str:
    """Read a key from hephaestus config.json."""
    config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hephaestus"
    config_file = config_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f).get(key, "") or ""
        except Exception:
            pass
    return ""


def run(
    process: str,
    model: Optional[str] = None,
    sarah_model: Optional[str] = None,
    model_file: Optional[str] = None,
    loop_order: int = 0,
    excludes: Optional[list[str]] = None,
    output_dir: Optional[str] = None,
    force: bool = False,
    state_root: Optional[str] = None,
    feynarts_path: Optional[str] = None,
    wolfram_path: Optional[str] = None,
    diagram_cap: Optional[int] = None,
    amp_size_cap_mb: Optional[int] = None,
    timeout_s: Optional[int] = None,
) -> dict:
    """Run the full FeynArts generate pipeline.

    Args:
        process: Process specification string.
        model: Built-in model name.
        sarah_model: SARAH model name.
        model_file: Path to model file directory.
        loop_order: Loop order (0=tree).
        excludes: Topology classes to exclude.
        output_dir: Output directory for results.
        force: Force re-run even if cached.
        state_root: Override state root.
        feynarts_path: Override FeynArts path.
        wolfram_path: Override wolframscript path.
        diagram_cap: Override diagram count cap.
        amp_size_cap_mb: Override amp file size cap (MB).
        timeout_s: Override wolframscript timeout (seconds).

    Returns:
        dict with summary info.
    """
    # --- Cap defaults (env vars take precedence over defaults) ---
    _diagram_cap = diagram_cap or int(os.environ.get("FEYNARTS_DIAGRAM_CAP", "2000"))
    _amp_cap = amp_size_cap_mb or int(os.environ.get("FEYNARTS_AMP_SIZE_CAP_MB", "200"))
    _timeout = timeout_s or int(os.environ.get("FEYNARTS_DEFAULT_TIMEOUT_S", "600"))

    # --- 1. Prerequisite checks ---
    fa_path = feynarts_path or _read_config("feynarts_path")
    if not fa_path or not Path(fa_path, "FeynArts.m").exists():
        _blocker(
            "FEYNARTS_ABSENT",
            "FeynArts is not installed. Run _shared/installs/feynarts first.",
        )

    ws_path = wolfram_path or _read_config("wolfram_engine_path")
    if not ws_path or not Path(ws_path).exists():
        _blocker(
            "WOLFRAM_KERNEL_ABSENT",
            "wolframscript not found. Run /install to install Wolfram Engine.",
        )

    fa_version = _read_config("feynarts_version") or "3.11"
    lorentz_gen = str(Path(fa_path) / "Models" / "Lorentz.gen")

    # --- 2. Model resolution ---
    try:
        model_info = resolve_model(
            model=model,
            sarah_model=sarah_model,
            model_file=model_file,
            feynarts_path=fa_path,
            state_root=state_root or _DEFAULT_STATE_ROOT,
        )
    except ModelResolutionError as e:
        _blocker(e.code, str(e), e.context)

    model_name = model_info["model_name"]
    mod_path = model_info["mod_path"]
    gen_path = model_info["gen_path"]

    # --- 3. Process resolution ---
    try:
        proc_info = resolve_process(
            process=process,
            model=model_name,
            loop_order=loop_order,
            excludes=excludes,
        )
    except ProcessResolutionError as e:
        _blocker(e.code, str(e), e.context)

    n_in = proc_info["n_in"]
    n_out = proc_info["n_out"]
    process_tuple = proc_info["feynarts_tuple"]
    processspec = proc_info["processspec"]

    # --- 4. Optional post-hoc SARAH MakeFeynArts[] ---
    if sarah_model is not None:
        _run_make_feynarts(
            model_name=model_name,
            sarah_path=_read_config("sarah_path"),
            feynarts_state_dir=model_info.get("state_dir", ""),
            ws_path=ws_path,
            timeout_s=_timeout,
        )
        # Re-resolve model after MakeFeynArts[] has written .mod/.gen
        try:
            model_info = resolve_model(
                sarah_model=sarah_model,
                state_root=state_root or _DEFAULT_STATE_ROOT,
            )
        except ModelResolutionError as e:
            _blocker(e.code, str(e), e.context)
        mod_path = model_info["mod_path"]
        gen_path = model_info["gen_path"]

    # --- 5. Cache probe ---
    cache_key = compute_cache_key(
        mod_path=mod_path,
        gen_path=gen_path,
        feynarts_version=fa_version,
        processspec=processspec,
        lorentz_gen_path=lorentz_gen,
    )

    _state_root = Path(state_root or _DEFAULT_STATE_ROOT)
    cache_dir = _state_root / "cache" / "feynarts" / cache_key

    out_dir = Path(output_dir) if output_dir else Path.cwd() / "feynarts_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not force and (cache_dir / "summary.json").exists():
        # Serve from cache
        for fname in ["FeynAmpList.m", "FeynAmpList.meta.json", "summary.json",
                      "topologies.json", "diagrams.pdf"]:
            src = cache_dir / fname
            if src.exists():
                shutil.copy2(src, out_dir / fname)
        with open(out_dir / "summary.json") as f:
            summary = json.load(f)
        summary["cached"] = True
        return summary

    # --- 6. Template rendering + wolframscript ---
    excludes_m = ", ".join(excludes or [])
    model_hash = _sha256_file(mod_path) if mod_path and Path(mod_path).exists() else ""

    script_content = render_driver(
        run_dir=str(out_dir),
        loop_order=loop_order,
        n_in=n_in,
        n_out=n_out,
        excludes_m=excludes_m,
        process_tuple=process_tuple,
        model_name=model_name,
        feynarts_version=fa_version,
        model_hash=model_hash,
        diagram_cap=_diagram_cap,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".m", delete=False) as tmp:
        tmp.write(script_content)
        script_path = tmp.name

    try:
        t_start = time.monotonic()
        try:
            proc = subprocess.run(
                [ws_path, "-script", script_path],
                capture_output=True,
                text=True,
                timeout=_timeout,
                cwd=str(out_dir),
            )
            wall_clock_s = time.monotonic() - t_start
        except subprocess.TimeoutExpired as exc:
            wall_clock_s = time.monotonic() - t_start
            # Known limitation (v1): subprocess.run(timeout=) raises TimeoutExpired
            # but on macOS the Wolfram kernel subprocess may not be reliably
            # SIGKILLed — the kernel process can linger as an orphan.
            # Workaround (v1.1): replace with psutil-based process-tree kill.
            # See: iteration-1-review.md §nice-to-haves; SKILL.md §Caps and blockers.
            try:
                exc.process.kill()  # type: ignore[union-attr]
            except Exception:
                pass  # Best-effort; process may already be gone
            _blocker(
                "FEYNARTS_TIMEOUT",
                f"wolframscript exceeded timeout of {_timeout} s.",
                {"timeout_s": _timeout, "wall_clock_s": int(wall_clock_s)},
                exit_code=3,
            )

        stdout = proc.stdout.strip()

        # Parse Mathematica stdout
        if "FEYNARTS_EMPTY_RESULT" in stdout:
            # Recoverable — return with n_diagrams=0
            return {"n_diagrams": 0, "cached": False, "status": "FEYNARTS_EMPTY_RESULT"}

        if "FEYNARTS_TOO_MANY_DIAGRAMS" in stdout:
            parts = stdout.split()
            n_diag = int(parts[-1]) if parts[-1].isdigit() else _diagram_cap + 1
            _blocker(
                "FEYNARTS_TOO_MANY_DIAGRAMS",
                f"FeynArts generated {n_diag} diagrams, exceeding cap of {_diagram_cap}.",
                {"diagram_count": n_diag, "cap": _diagram_cap},
                exit_code=2,
            )

        if proc.returncode != 0 and "FEYNARTS_OK" not in stdout:
            _blocker(
                "FEYNARTS_ABSENT",
                f"wolframscript exited with code {proc.returncode}.\n"
                f"stdout: {stdout[:500]}\nstderr: {proc.stderr[:500]}",
            )

        # Extract n_diagrams from stdout
        n_diagrams = 0
        for line in stdout.splitlines():
            if "FEYNARTS_OK" in line:
                parts = line.split()
                if len(parts) >= 2 and parts[-1].isdigit():
                    n_diagrams = int(parts[-1])

    finally:
        Path(script_path).unlink(missing_ok=True)

    # --- 7. Postprocessing ---
    try:
        summary = postprocess_output(
            run_dir=str(out_dir),
            n_diagrams=n_diagrams,
            feynarts_version=fa_version,
            model_hash=model_hash,
            processspec=processspec,
            loop_order=loop_order,
            wall_clock_s=wall_clock_s,
            model_name=model_name,
            amp_size_cap_mb=_amp_cap,
            cached=False,
        )
    except PostprocessError as e:
        _blocker(e.code, str(e), e.context, exit_code=4)

    # --- 8. Cache write ---
    cache_dir.mkdir(parents=True, exist_ok=True)
    for fname in ["FeynAmpList.m", "FeynAmpList.meta.json", "summary.json",
                  "topologies.json", "diagrams.pdf"]:
        src = out_dir / fname
        if src.exists():
            shutil.copy2(src, cache_dir / fname)

    return summary


def _run_make_feynarts(
    model_name: str,
    sarah_path: str,
    feynarts_state_dir: str,
    ws_path: str,
    timeout_s: int,
) -> None:
    """Run the post-hoc SARAH MakeFeynArts[] in a separate Wolfram session."""
    if not sarah_path:
        _blocker(
            "FEYNARTS_SARAH_STATE_MISSING",
            "sarah_path not configured. Run _shared/installs/sarah first.",
        )

    Path(feynarts_state_dir).mkdir(parents=True, exist_ok=True)

    script_content = render_make_feynarts_driver(
        feynarts_state_dir=feynarts_state_dir,
        sarah_path=sarah_path,
        model_name=model_name,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".m", delete=False) as tmp:
        tmp.write(script_content)
        script_path = tmp.name

    try:
        try:
            proc = subprocess.run(
                [ws_path, "-script", script_path],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as exc:
            # Known limitation (v1): same macOS SIGKILL reliability issue as
            # the main wolframscript call — psutil tree kill deferred to v1.1.
            try:
                exc.process.kill()  # type: ignore[union-attr]
            except Exception:
                pass
            _blocker(
                "FEYNARTS_TIMEOUT",
                f"MakeFeynArts[] exceeded timeout of {timeout_s} s.",
                {"timeout_s": timeout_s},
            )

        if proc.returncode != 0:
            _blocker(
                "FEYNARTS_SARAH_STATE_MISSING",
                f"MakeFeynArts[] failed with exit code {proc.returncode}.\n"
                f"stderr: {proc.stderr[:500]}",
            )
    finally:
        Path(script_path).unlink(missing_ok=True)


def _sha256_file(path: str) -> str:
    import hashlib
    p = Path(path)
    if not p.exists():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
