"""MadDM session scripting and output parsing.

Generate MadDM session scripts and parse computed observables.
Library functions Claude composes per-task — not CLI executables.

For param_card manipulation, use the shared SLHA parser from the
madgraph skill: madgraph/scripts/card_io.py

Invocation: when running a generated script with mg5_aMC, always pass
``--mode=maddm``. Bare ``mg5_aMC <script>`` loads the base interpreter
without the MadDM plugin, and any ``generate relic_density`` / ``generate
direct_detection`` / ``generate indirect_detection`` line then raises
``InvalidCmd: The command "generate" has an error``. See
``_shared/installs/maddm/INSTALL.md`` workarounds §8.

Frozen-SI DD-rerun hazard: MadDM ``direct_detection``-only reruns can serve
a STALE spin-independent cross-section (bit-identical across genuinely
different coupling points) because the DD-assembly path does not always
re-read the param card, and a reused output dir keeps the previously compiled
matrix elements. ``generate_maddm_script`` therefore emits a cleanup line into
the generated script by default (``fresh=True``) so the output dir is removed
right before ``output <out_dir>`` runs -- i.e. at RUN time, not at
script-generation time -- so every run recompiles from the current param
card. Generating a script is a pure, side-effect-free operation on the
filesystem; only *executing* the emitted script (via ``mg5_aMC``) deletes
anything. The loud complement is ``staleness.detect_stale_dd`` /
``staleness.MADDM_STALE_DD_RESULT``, which flags a stale sigma_SI if upstream
still serves one. See ``maddm/SKILL.md`` section 'Frozen-SI DD-rerun staleness'.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import sys
from pathlib import Path
import shutil


_OBSERVABLE_TO_GENERATE = {
    "relic": "relic_density",
    "direct_detection": "direct_detection",
    "indirect_detection": "indirect_detection",
}


def validate_ufo_path(ufo_path: str | Path) -> list[str]:
    """Return (and warn about) reasons *ufo_path* may break MG5 ``import model``.

    MG5's command interpreter tokenizes ``import model <path>`` on whitespace
    *and* mis-parses a hyphen in a path component as the start of a CLI flag, so
    a hyphenated path like ``.../demo_output/singlet-doublet/SingletDoublet``
    fails with ``Path .../demo_output/singlet is not a valid pathname``. A
    relative path is CWD-dependent and silently resolves against whichever
    directory the MG5 session started in — a trap across worktrees/sessions.

    This is a LOUD-but-non-fatal read-time guard: it prints a ``WARNING:`` line
    to stderr for each problem and returns the list of warning strings (empty
    when the path is clean). It never raises — the caller may have a good reason
    (e.g. a path it will normalise itself). Prefer the absolute, hyphen-free
    ``$STATE_ROOT/models/<model>/<SarahName>`` symlink written by /sarah-build.
    """
    p = str(ufo_path)
    warnings: list[str] = []
    if not os.path.isabs(p):
        warnings.append(
            f"UFO path {p!r} is RELATIVE — MG5 resolves it against the session "
            "CWD, which is fragile across sessions/worktrees. Pass an absolute "
            "path (e.g. $STATE_ROOT/models/<model>/<SarahName>)."
        )
    # Check every component from the model dir down for a hyphen. MG5 chokes on
    # any hyphen in the imported path, but the common offender is a hyphenated
    # model directory (``singlet-doublet``) vs. the underscore config slug.
    hyphenated = [part for part in Path(p).parts if "-" in part]
    if hyphenated:
        warnings.append(
            f"UFO path {p!r} contains hyphenated component(s) {hyphenated} — "
            "MG5 `import model` mis-tokenizes a hyphen as a CLI flag and fails "
            "with 'Path ... is not a valid pathname'. Use the hyphen-free "
            "$STATE_ROOT/models/<model>/<SarahName> symlink instead."
        )
    for w in warnings:
        print(f"WARNING: maddm UFO path: {w}", file=sys.stderr)
    return warnings


def prepare_output_dir(out_dir: str | Path, fresh: bool = True) -> None:
    """Clear *out_dir* so the next MadDM run recompiles from scratch.

    When ``fresh`` is True (the default) the directory is removed entirely
    (``shutil.rmtree(..., ignore_errors=True)``). This is the fresh-recompute
    discipline that prevents the frozen-SI DD-rerun staleness: MG5's
    ``output <out_dir>`` refuses to overwrite an existing directory *and* a
    reused dir carries previously compiled DD matrix elements that ignore
    param-card changes, so clearing it first guarantees the new param card
    actually takes effect. When ``fresh`` is False this is a no-op and the
    caller is responsible for any reuse hazards.

    Safe to call whether or not *out_dir* exists.

    NOTE: ``generate_maddm_script`` does NOT call this function. Script
    *generation* must never touch the filesystem -- a preview/dry-run or a
    script that is never executed must not delete a live results directory
    as a side effect. Instead ``generate_maddm_script`` emits the equivalent
    cleanup as a shell-escape line inside the returned MG5 script, so the
    deletion happens only when that script is actually run (via
    ``mg5_aMC``), immediately before ``output <out_dir>``. This function is
    kept as a standalone utility for callers who drive their own MG5
    sessions imperatively (e.g. from Python via the MG5 API) rather than by
    handing a generated script to ``mg5_aMC`` -- such a caller should invoke
    it right before its own ``output`` step, not at script-build time.
    """
    if not fresh:
        return
    shutil.rmtree(str(out_dir), ignore_errors=True)


def generate_maddm_script(
    ufo_path: str | Path,
    dm_candidate: str | int,
    out_dir: str | Path,
    observables: list[str],
    split_for_param_overlay: bool = False,
    fresh: bool = True,
) -> str | tuple[str, str]:
    """Build a MadDM 3.2 session script for MG5.

    Emits the high-level MadDM flow, verified against MadDM 3.2.13:

        import model <ufo_path>
        define darkmatter <dm_candidate>
        generate relic_density        # and/or direct_detection, indirect_detection
        output <out_dir>
        launch -f

    Call sites populate the param_card before `launch -f` by copying the
    SPheno SLHA output over ``<out_dir>/Cards/param_card.dat``. Because
    that overlay has to happen *after* ``output <out_dir>`` creates
    ``Cards/param_card.dat`` and *before* ``launch -f`` reads it, fuse
    these into a single MG5 session and the overlay is a no-op (MG5 never
    relinquishes control between the two commands). Pass
    ``split_for_param_overlay=True`` to get two scripts instead; run the
    first with ``mg5_aMC --mode=maddm``, overlay the SLHA, then run the
    second with ``mg5_aMC --mode=maddm``.

    Fresh recompute (``fresh``, default True): the returned script contains a
    shell-escape line (``!rm -rf <out_dir>``) immediately before
    ``output <out_dir>`` that removes any pre-existing ``out_dir`` when the
    script is *executed* by ``mg5_aMC``. This is emitted into the script text,
    not run by this function -- generating a script never touches the
    filesystem, so a preview, a dry run, or a script that errors out before
    launch can never delete a live results directory as a side effect. Only
    running the emitted script (or the setup half, for
    ``split_for_param_overlay``) deletes anything, and only right before the
    ``output`` step that needs a clean directory. This is the primary defense
    against the frozen-SI DD-rerun hazard (a sigma_SI that stays bit-identical
    across genuinely different couplings); the loud complement is
    ``staleness.detect_stale_dd``. Pass ``fresh=False`` only when you
    intentionally want to reuse an existing output directory and accept the
    staleness risk -- no cleanup line is emitted in that case.

    Args:
        ufo_path: Absolute path to the UFO model directory. Must be the
            realpath or a symlink whose basename matches the target
            directory's basename — MG5 uses the basename to re-resolve the
            model path and fails on e.g. a ``state_dir/ufo`` symlink pointing
            at ``sarah_output/UFO/SingletDoublet/``. Both
            ``$STATE_ROOT/models/singlet_doublet/SingletDoublet`` (the
            fixed-up `/sarah-build` symlink) and the realpath
            ``$STATE_ROOT/models/singlet_doublet/sarah_output/UFO/SingletDoublet``
            work.
        dm_candidate: Particle name or PDG id of the DM candidate. Strings
            are lowercased before emission because MG5 normalises UFO
            particle names on import ("Change particles name to pass to MG5
            convention") — a UFO-declared ``Chi1`` becomes addressable only
            as ``chi1`` post-import. Ints (PDG ids) are passed through.
        out_dir: Directory MG5 will write to (passed verbatim to
            ``output``). Cleared first when ``fresh=True``.
        observables: Any subset of ``["relic", "direct_detection",
            "indirect_detection"]``. ``"relic"`` maps to MadDM's high-level
            ``generate relic_density`` entry, which automatically assembles
            the full coannihilation set — NOT the same as
            ``generate <dm> <dm>~ > all all``, which misses coannihilators
            and biases Omega h^2 upward near thresholds.
        split_for_param_overlay: When ``False`` (default) return a single
            script string with both ``output`` and ``launch -f`` in the
            same session — the legacy behaviour. When ``True`` return a
            tuple ``(setup_script, launch_script)``: the first ends after
            ``output <out_dir>``; the second is just
            ``launch <out_dir> -f``. The caller is expected to overlay
            ``Cards/param_card.dat`` between the two MG5 invocations.
        fresh: When True (default) emit a cleanup line into the script that
            clears ``out_dir`` at RUN time (right before ``output``), so the
            run recompiles from the current param card. See above.

    Returns:
        MG5/MadDM 3.2 session script content as a string, or, when
        ``split_for_param_overlay=True``, a ``(setup, launch)`` tuple of
        strings.
    """
    if not observables:
        raise ValueError("observables must be non-empty")
    unknown = [o for o in observables if o not in _OBSERVABLE_TO_GENERATE]
    if unknown:
        raise ValueError(
            f"unknown observable(s): {unknown}; "
            f"expected any of {sorted(_OBSERVABLE_TO_GENERATE)}"
        )

    # Read-time guard: warn loudly (non-fatal) if the UFO path is relative or
    # hyphenated — both make the emitted `import model <ufo_path>` line fail
    # inside MG5. The script is still generated verbatim so a caller that knows
    # what it is doing is not blocked.
    validate_ufo_path(ufo_path)

    candidate_token = (
        dm_candidate.lower() if isinstance(dm_candidate, str) else dm_candidate
    )

    setup_lines = [
        f"import model {ufo_path}",
        f"define darkmatter {candidate_token}",
    ]
    # Preserve the order the caller passed observables in; MadDM accepts
    # multiple `generate` calls in sequence.
    for obs in observables:
        setup_lines.append(f"generate {_OBSERVABLE_TO_GENERATE[obs]}")

    # Fresh-recompute discipline: emit a shell-escape line that clears any
    # prior output dir when the script is RUN (mg5_aMC's cmd interpreter
    # executes a `!`-prefixed line as a raw shell command), immediately
    # before `output <out_dir>` recreates it. This is deliberately NOT done
    # here at generation time -- building script text must be a pure,
    # side-effect-free operation on the filesystem, since the caller may be
    # previewing, dry-running, or erroring out before ever handing the
    # script to mg5_aMC. Only actually running the script deletes anything,
    # and only right where MG5 is about to need a clean directory. Prevents
    # the frozen-SI DD-rerun staleness. Omitted entirely when fresh=False.
    #
    # The path is shlex-quoted because MG5's `!` escape hands the whole line
    # to `subprocess.call(..., shell=True)`: an unquoted path with a space
    # would word-split (`rm -rf /tmp/my results/out` deletes /tmp/my AND
    # results/out), and `~` / glob chars / `;` would expand or split —
    # catastrophic on an `rm -rf`. Quoting makes the path one literal token,
    # matching the old shutil.rmtree semantics. The `output {out_dir}` line
    # below is deliberately NOT quoted: MG5 parses it with its own
    # whitespace tokenizer, which does not strip shell quotes — quotes there
    # would become literal characters in the directory name, making rm and
    # output target different dirs. For paths without shell metacharacters
    # (every documented $STATE_ROOT layout) shlex.quote is the identity, so
    # both lines name the identical string.
    if fresh:
        setup_lines.append(f"!rm -rf {shlex.quote(str(out_dir))}")
    setup_lines.append(f"output {out_dir}")

    if split_for_param_overlay:
        setup_script = "\n".join(setup_lines) + "\n"
        launch_script = f"launch {out_dir} -f\n"
        return setup_script, launch_script

    setup_lines.append("launch -f")
    return "\n".join(setup_lines) + "\n"


# ---------------------------------------------------------------------------
# SLHA / param-card provenance guard for the direct-detection run path
# ---------------------------------------------------------------------------
#
# The frozen-SI defenses above (fresh recompute + staleness.detect_stale_dd)
# catch a stale *result*. This guard catches the upstream mistake that most
# often produces a misleading DD number: feeding MadDM a param card / SLHA
# spectrum that is NOT the one most recently produced for the model. In our
# plumbing the DD param card is an overlay of the SPheno SLHA that
# spheno-build/register_model recorded via
# ``config_helpers.register_latest_slha`` (path + sha256 + point/params).
# Before a DD run, ``check_slha_provenance`` fingerprints the SLHA about to be
# used and compares it against that registered ``latest_slha`` entry, warning
# loudly (with both paths + hashes and a remediation pointer) on any drift.
#
# Design: LOUD WARNING, non-fatal by default — NOT a recoverable blocker.
# A provenance mismatch is advisory ("you may be feeding the wrong/older
# spectrum"), and is a legitimate state in multi-point workflows and for
# pre-guard configs that never recorded provenance; hard-blocking would break
# backward compatibility. The recoverable blocker MADDM_STALE_DD_RESULT stays
# reserved for a *detected* stale numeric result (staleness.py). Callers who
# want a hard stop pass ``fatal=True``.


class SlhaProvenanceMismatch(RuntimeError):
    """Raised by :func:`check_slha_provenance` only when ``fatal=True``."""


def _sha256_of(path: str | Path) -> str | None:
    """Hex sha256 of *path*, or None if it cannot be read."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def check_slha_provenance(
    model: str,
    slha_path: str | Path,
    *,
    expected_point: str | None = None,
    expected_params: dict | None = None,
    observables: list[str] | None = None,
    fatal: bool = False,
) -> dict:
    """Verify the SLHA/param card about to feed a MadDM DD run is the registered one.

    Fingerprints the SLHA at *slha_path* (the file the caller is about to overlay
    onto ``<out_dir>/Cards/param_card.dat``) and compares it against the
    ``latest_slha`` provenance recorded for *model* in the hephaestus config by
    ``config_helpers.register_latest_slha`` (written by spheno-build /
    lagrangian-builder). On any drift — missing registration, unreadable card,
    pre-guard config without a fingerprint, or a sha256 that differs from the
    registered spectrum — a loud ``WARNING:`` line is printed to stderr naming
    both paths and hashes plus remediation ("re-run SPheno / register the
    spectrum").

    Only meaningful for the direct-detection path. When *observables* is given
    and does not include ``"direct_detection"`` the check is skipped
    (``ok=True, skipped=True``) so relic-only / ID-only runs are unaffected.

    Non-fatal by default: returns a result dict and never raises, so existing
    callers and pre-guard configs keep working. Pass ``fatal=True`` to raise
    :class:`SlhaProvenanceMismatch` instead when the card does not match.

    Returns a dict::

        {"ok": bool, "skipped": bool, "reason": str | None,
         "used_path": str, "used_sha": str | None,
         "registered_path": str | None, "registered_sha": str | None}

    ``ok`` is True when the used card's sha256 matches the registered spectrum's
    recorded sha256 (the confident, verified case). It is also True — with
    ``reason="unverifiable"`` — when provenance cannot be checked (config helper
    or fingerprint unavailable), because absence of evidence is not a mismatch;
    a warning is still emitted. It is False only on a genuine sha256 mismatch or
    a missing/unreadable card.
    """
    used_path = str(Path(slha_path))

    def _warn(msg: str) -> None:
        print(f"WARNING: MadDM DD provenance[{model!r}]: {msg}", file=sys.stderr)

    def _result(ok: bool, reason: str | None, *, skipped: bool = False,
                registered_path=None, registered_sha=None, used_sha=None) -> dict:
        return {
            "ok": ok,
            "skipped": skipped,
            "reason": reason,
            "used_path": used_path,
            "used_sha": used_sha,
            "registered_path": registered_path,
            "registered_sha": registered_sha,
        }

    # Only the DD path is exposed to the frozen-SI / wrong-card hazard.
    if observables is not None and "direct_detection" not in observables:
        return _result(True, "not_direct_detection", skipped=True)

    used_sha = _sha256_of(used_path)
    if used_sha is None:
        _warn(
            f"the param card / SLHA to be used at {used_path} cannot be read "
            "(moved/deleted?); cannot verify it matches the registered "
            "spectrum. Re-run SPheno or point at the correct SLHA file."
        )
        return _mismatch_return(
            _result(False, "used_card_unreadable"), fatal,
            "param card unreadable at " + used_path,
        )

    # Lazy import: keep maddm_run importable without config_helpers on path.
    try:
        import config_helpers  # type: ignore
    except Exception:
        _warn(
            "config_helpers is unavailable, so the registered latest_slha "
            "cannot be read; DD provenance is UNVERIFIED. Run inside the "
            "plugin environment to enable the check."
        )
        return _result(True, "unverifiable", used_sha=used_sha)

    # read_latest_slha emits its own loud warnings for drift / point mismatch.
    registered_path = config_helpers.read_latest_slha(
        model, expected_point=expected_point, expected_params=expected_params,
    )
    if registered_path is None:
        _warn(
            "no latest_slha is registered for this model, so the DD param card "
            f"({used_path}) cannot be checked against the produced spectrum. "
            "Re-run SPheno (spheno-build) or register the spectrum "
            "(lagrangian-builder register_model --latest-slha) first."
        )
        return _mismatch_return(
            _result(False, "no_registration", used_sha=used_sha), fatal,
            f"no latest_slha registered for model {model!r}",
        )

    entry = config_helpers.get_model(model) or {}
    prov = entry.get("latest_slha_provenance") or {}
    registered_sha = prov.get("sha256")
    if registered_sha is None:
        _warn(
            "the registered latest_slha has no recorded fingerprint "
            "(pre-guard config); cannot confirm the DD param card matches the "
            "produced spectrum. Re-run SPheno to record provenance."
        )
        return _result(
            True, "unverifiable", used_sha=used_sha,
            registered_path=registered_path, registered_sha=None,
        )

    if used_sha == registered_sha:
        return _result(
            True, None, used_sha=used_sha,
            registered_path=registered_path, registered_sha=registered_sha,
        )

    _warn(
        "the SLHA / param card about to feed direct_detection does NOT match "
        "the registered latest_slha for this model.\n"
        f"    using:      {used_path}\n"
        f"                 sha256 {used_sha[:12]}...\n"
        f"    registered:  {registered_path}\n"
        f"                 sha256 {registered_sha[:12]}...\n"
        "  The DD result will describe whichever spectrum you overlay, not "
        "necessarily the model's latest point. Re-run SPheno (spheno-build) to "
        "regenerate/register the spectrum, or overlay the registered file "
        "above, before launching direct_detection."
    )
    return _mismatch_return(
        _result(
            False, "sha256_mismatch", used_sha=used_sha,
            registered_path=registered_path, registered_sha=registered_sha,
        ),
        fatal,
        (
            f"DD param card {used_path} (sha256 {used_sha[:12]}...) does not "
            f"match registered latest_slha {registered_path} "
            f"(sha256 {registered_sha[:12]}...) for model {model!r}"
        ),
    )


def _mismatch_return(result: dict, fatal: bool, exc_msg: str) -> dict:
    """Return *result*, or raise :class:`SlhaProvenanceMismatch` when *fatal*."""
    if fatal:
        raise SlhaProvenanceMismatch(exc_msg)
    return result
