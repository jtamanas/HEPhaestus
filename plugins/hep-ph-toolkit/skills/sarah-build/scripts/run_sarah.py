"""
run_sarah.py — Core SARAH invocation: cache check, render, wolframscript, log parse.

This module is the inner engine called by build.py.  It does NOT read argv directly.

Public API:
    run(spec_path, model_dir, force=False, outputs=['ufo']) -> dict
        Returns {"status": "cached"} on cache hit.
        Returns {"status": "built", "sarah_name": ..., "ufo": ..., "log": ...} on success.
        Raises SystemExit(1) on fatal blocker.
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import datetime
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared imports
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_SHARED_HELPERS_DIR = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers"

# Add shared paths
for _p in [str(_SHARED_DIR), str(_SHARED_HELPERS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config_helpers  # noqa: E402

from modelspec_v3.loader import load_spec, SpecLoadError  # noqa: E402
from modelspec_v3.validate import validate  # noqa: E402
from modelspec_v3.render import render_all  # noqa: E402

from stage import stage  # noqa: E402
from collect import collect, repair_symlinks  # noqa: E402
from scan_outputs import scan as scan_outputs  # noqa: E402


# ---------------------------------------------------------------------------
# Make-dispatch map (RC2 fix — §7 of design-final)
# ---------------------------------------------------------------------------

#: Maps output target keys to their Mathematica invocations.
#: Only ``ufo`` and ``spheno`` are supported; all others raise ValueError.
_MAKE_DISPATCH: dict[str, str] = {
    "ufo":    "MakeUFO[]",
    "spheno": "MakeSPheno[]",
}


def _build_make_commands(outputs: list[str]) -> str:
    """Return a semicolon-separated Mathematica command string for *outputs*.

    Args:
        outputs: List of output target keys, each must be a key in
            :data:`_MAKE_DISPATCH`.

    Returns:
        A string like ``"MakeUFO[]; MakeSPheno[];"`` — one entry per output,
        joined by ``"; "`` with a trailing ``";"``.

    Raises:
        ValueError: If any entry in *outputs* is not a known dispatch key.
    """
    try:
        cmds = [_MAKE_DISPATCH[o] for o in outputs]
    except KeyError as exc:
        raise ValueError(
            f"Unknown output target: {exc.args[0]!r}. "
            f"Must be one of {sorted(_MAKE_DISPATCH)}"
        ) from exc
    return "; ".join(cmds) + ";"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit_fatal(blocker: dict) -> None:
    """Print a fatal blocker JSON to stderr."""
    print(json.dumps(blocker), file=sys.stderr)


def _fatal(code: str, message: str, context: dict | None = None) -> None:
    """Emit fatal blocker and exit 1."""
    blocker = {
        "code": code,
        "mode": "fatal",
        "message": message,
    }
    if context:
        blocker["context"] = context
    _emit_fatal(blocker)
    sys.exit(1)


def _compute_cache_key(spec_bytes: bytes, sarah_version: str) -> str:
    """Compute the W3 cache key: sha256hex=sarah_version (§2.9)."""
    sha = hashlib.sha256(spec_bytes).hexdigest()
    return f"{sha}={sarah_version}"


def _read_cache_key(model_dir: Path) -> str | None:
    key_path = model_dir / ".sarah_build_key"
    if key_path.exists():
        return key_path.read_text().strip()
    return None


def _write_cache_key(
    model_dir: Path,
    key: str,
    state_output_dir: Path | str | None = None,
) -> None:
    """Stamp ``.sarah_build_key`` onto *model_dir* and, if provided, *state_output_dir*.

    Called only after ``scan_outputs.scan()`` returns ``status=clean``, so a
    corrupt SARAH tree can never leave a cache stamp anywhere (plan §3.2, D2).
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / ".sarah_build_key").write_text(key)
    if state_output_dir:
        sod = Path(state_output_dir)
        sod.mkdir(parents=True, exist_ok=True)
        (sod / ".sarah_build_key").write_text(key)


def _register_model_safe(spec: dict, model_dir: Path, sarah_name: str) -> Path:
    """Register *spec* in config with the correctly-named UFO symlink.

    Hardens ``config.models.<name>.ufo`` against the legacy ``state_dir/ufo``
    shape. Calls :func:`collect.repair_symlinks` first so the canonical link
    exists, then refuses to register if its basename still mismatches the
    UFO target — this would only happen if the UFO tree is absent, in which
    case we raise rather than persist a broken pointer.

    Returns the canonical symlink path that was written to config.
    """
    repair_symlinks(model_dir, sarah_name)
    ufo_link = model_dir / sarah_name
    if ufo_link.is_symlink():
        target_basename = Path(os.readlink(ufo_link)).name
        if target_basename != sarah_name:
            raise RuntimeError(
                f"refusing to register {spec['model']['name']}: symlink "
                f"{ufo_link} -> basename {target_basename!r} does not "
                f"match sarah_name {sarah_name!r}; heal state dir first"
            )
    spec_dest = model_dir / "spec.yaml"
    config_helpers.register_model(
        _config_slug(spec),
        spec=str(spec_dest),
        ufo=str(ufo_link),
        sarah_built_at=_utc_now(),
    )
    return ufo_link


def _config_slug(spec: dict) -> str:
    """Return the lowercase config-registry key for *spec*.

    Uses spec.model.slug if declared; otherwise falls back to
    spec.model.name.lower(). Required because config_helpers.register_model
    enforces ``^[a-z][a-z0-9_]{1,30}$`` while spec.model.name is the SARAH
    (CamelCase) name.
    """
    m = spec["model"]
    return m.get("slug") or m["name"].lower()


@contextmanager
def _sarah_build_lock(lock_path: Path):
    """Advisory exclusive lock serialising same-model SARAH builds.

    SARAH reads from ``$sarah_path/Private-Models/<Name>/`` and writes to
    ``$sarah_path/Output/<Name>/`` — both shared across runs. Parallel builds
    of the same model race at the filesystem level (stage() wipes and
    rewrites Private-Models/<Name>/ while another wolframscript is mid-read;
    Output/<Name>/ is written by both kernels). This lock forces same-model
    callers to serialise; different models remain fully parallel.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


# ---------------------------------------------------------------------------
# Core run function
# ---------------------------------------------------------------------------

def run(
    spec_path: Path,
    model_dir: Path,
    force: bool = False,
    outputs: list[str] | None = None,
) -> dict:
    """Render templates, invoke SARAH via wolframscript, update cache.

    Args:
        spec_path: Path to the ModelSpec v3 YAML.
        model_dir: Per-model state directory (e.g. $STATE_ROOT/models/dark_su3/).
        force: If True, bypass the cache and always rebuild.
        outputs: List of SARAH targets to build (default: ['ufo']).
                 Supported values: 'ufo', 'spheno'.

    Returns:
        {"status": "cached"} on cache hit.
        {"status": "built", "sarah_name": str, "ufo": str, "log": str} on success.
        Exits 1 on fatal blocker.
    """
    if outputs is None:
        outputs = ["ufo"]

    # Reload config roots in case env was set after module import
    config_helpers._reload_roots()
    config = config_helpers.load_config()

    # Check prerequisites
    wolfram_engine_path = config.get("wolfram_engine_path") or config.get("wolfram_kernel")
    if not wolfram_engine_path:
        _fatal(
            "WOLFRAM_KERNEL_ABSENT",
            "wolfram_engine_path not set in config; see _shared/installs/sarah/INSTALL.md",
        )
    sarah_path = config.get("sarah_path")
    if not sarah_path:
        _fatal(
            "SARAH_ABSENT",
            "sarah_path not set in config; see _shared/installs/sarah/INSTALL.md",
        )
    sarah_version = config.get("sarah_version", "unknown")

    # Load spec (v3 loader — raises SpecLoadError on parse failure)
    spec_path = Path(spec_path)
    try:
        spec = load_spec(spec_path)
    except SpecLoadError as exc:
        _fatal("MODELSPEC_INVALID", str(exc))

    # Validate spec before rendering
    val_result = validate(spec)
    if val_result.errors:
        error_msgs = "; ".join(str(e) for e in val_result.errors)
        _fatal(
            "MODELSPEC_INVALID",
            f"ModelSpec validation failed: {error_msgs}",
            {"errors": [str(e) for e in val_result.errors]},
        )
    # Warnings are non-fatal — surface them to stderr but continue
    for w in val_result.warnings:
        print(json.dumps({"level": "warning", "message": str(w)}), file=sys.stderr)

    # Read raw bytes for cache key (re-open after load_spec to get raw bytes)
    with open(spec_path, "rb") as f:
        spec_bytes = f.read()

    # In v3, model.name is the SARAH name directly (no v1-style transform).
    sarah_name = spec["model"]["name"]
    cache_key = _compute_cache_key(spec_bytes, sarah_version)

    # Heal any legacy / mis-named UFO symlink in the state dir BEFORE the
    # cache-hit fast-path returns. State dirs built by older versions of
    # this skill contain a symlink literally named ``ufo`` — MG5's
    # ``import model`` resolves against the symlink basename, so such a
    # link breaks downstream consumers even on a cache hit. See
    # collect.repair_symlinks() for the invariant.
    if model_dir.is_dir():
        repair_symlinks(model_dir, sarah_name)

    # Fast-path cache check (no lock — hot callers return immediately).
    ufo_dir = model_dir / "sarah_output" / "UFO" / sarah_name
    if not force:
        existing_key = _read_cache_key(model_dir)
        if existing_key == cache_key and ufo_dir.is_dir():
            # If a prior build persisted the legacy ``.../ufo`` basename in
            # config, heal it by re-registering with the canonical link.
            # Otherwise leave config untouched (hot callers must not pay
            # for a config rewrite on every invocation).
            existing = config_helpers.get_model(_config_slug(spec)) or {}
            existing_ufo = existing.get("ufo", "")
            if existing_ufo and Path(existing_ufo).name != sarah_name:
                _register_model_safe(spec, model_dir, sarah_name)
            return {"status": "cached"}

    # Serialise same-model builds: SARAH's Private-Models/<Name>/ and
    # Output/<Name>/ are shared across runs, so parallel builds race on the
    # filesystem. Different models remain fully parallel.
    model_dir.mkdir(parents=True, exist_ok=True)
    with _sarah_build_lock(model_dir / ".sarah_build.lock"):
        # Double-check cache under the lock — another caller may have just
        # finished building while we were waiting.
        if not force:
            existing_key = _read_cache_key(model_dir)
            if existing_key == cache_key and ufo_dir.is_dir():
                return {"status": "cached"}

        # Step 1 — Render templates → {filename: text}
        rendered = render_all(spec)

        # Step 2 — Stage rendered files into $sarah_path/Private-Models/<Name>/
        sarah_path_obj = Path(sarah_path)
        stage(rendered, sarah_path_obj, sarah_name, cache_key)

        # Step 3 — Also write rendered files to model_dir/sarah/ (local copy for reference)
        sarah_render_dir = model_dir / "sarah"
        sarah_render_dir.mkdir(parents=True, exist_ok=True)
        for filename, text in rendered.items():
            (sarah_render_dir / filename).write_text(text, encoding="utf-8")

        # Copy spec into model dir
        spec_dest = model_dir / "spec.yaml"
        shutil.copy2(spec_path, spec_dest)

        # Step 4 — Build wolframscript command
        # AppendTo[$Path, "<sarah_path>/.."] so <<SARAH` context loader finds SARAH.
        # Start["<Name>"] loads from Private-Models/<Name>/. CheckModel[] validates.
        # _build_make_commands() maps outputs → correct Mathematica calls.
        sarah_output_dir = model_dir / "sarah_output"
        sarah_output_dir.mkdir(parents=True, exist_ok=True)

        make_cmds = _build_make_commands(outputs)
        code = (
            f'AppendTo[$Path, "{sarah_path}/.."];'
            f' <<SARAH`;'
            f' Start["{sarah_name}"];'
            f' CheckModel[];'
            f' {make_cmds}'
        )
        cmd = [wolfram_engine_path, "-code", code]

        # Step 5 — Run SARAH via wolframscript (cwd = sarah_path per §6.3)
        log_path = sarah_output_dir / "sarah.log"
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(sarah_path_obj),
            )
            log_text = result.stdout + ("\n" if result.stdout else "") + result.stderr
        except FileNotFoundError:
            _fatal(
                "WOLFRAM_KERNEL_ABSENT",
                f"wolframscript not found at {wolfram_engine_path!r}",
            )

        # Write log
        log_path.write_text(log_text)

        # Step 6 — Surface log path for agent inspection.
        # The agent reads sarah.log per the patterns in SKILL.md §"Failure modes → blockers":
        #   - "Anomalies are not cancelled" → ANOMALY_CANCELLATION_FAILED (fatal)
        #   - "Error: field <X> undefined"  → MODELSPEC_INVALID (fatal)
        #   - "Warning:"                     → non-fatal, collect and surface

        # Check return code (SARAH may exit non-zero on compile errors)
        if result.returncode != 0:
            _fatal(
                "SARAH_OUTPUT_MISSING",
                f"wolframscript exited {result.returncode}; check {log_path}",
                {"returncode": result.returncode, "log": str(log_path)},
            )

        # Step 7 — Collect: copy Output tree, create ufo symlink, write cache key
        try:
            collected = collect(sarah_path_obj, sarah_name, model_dir, cache_key)
        except FileNotFoundError as exc:
            _fatal(
                "SARAH_OUTPUT_MISSING",
                f"Expected UFO directory not found after SARAH run: {exc}",
                {"log": str(log_path)},
            )

        # Step 7.5 — Scan collected output trees for Mathematica-internals leakage.
        # Runs AFTER collect() (so we scan the stable copy, not the live
        # Output/ tree) and BEFORE _write_cache_key() (so a corrupt tree is
        # never cached). Plan §3.1, D2.
        scan_result = scan_outputs(
            model_dir=model_dir,
            sarah_name=sarah_name,
            log_path=log_path,
        )
        if scan_result["status"] == "corrupt":
            _emit_fatal(scan_result["blocker"])
            sys.exit(1)

        # Step 8 — Write cache key to model_dir (for run() cache checks).
        # Also stamps the SARAH state_output_dir/.sarah_build_key (moved here
        # from collect.py:150 per plan §3.2, D2).
        _write_cache_key(
            model_dir,
            cache_key,
            state_output_dir=collected.get("state_output_dir"),
        )

        # Step 9 — Register model in config via the hardened helper, which
        # re-runs repair_symlinks() before writing so the persisted
        # ``models.<name>.ufo`` is always the canonical <sarah_name> link
        # (never the legacy ``ufo`` basename).
        ufo_link = _register_model_safe(spec, model_dir, sarah_name)

        return {
            "status": "built",
            "sarah_name": sarah_name,
            "ufo": str(ufo_link),
            "log": str(log_path),
        }
