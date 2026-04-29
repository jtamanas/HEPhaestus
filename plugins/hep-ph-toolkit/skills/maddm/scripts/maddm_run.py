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
"""

from __future__ import annotations

from pathlib import Path


_OBSERVABLE_TO_GENERATE = {
    "relic": "relic_density",
    "direct_detection": "direct_detection",
    "indirect_detection": "indirect_detection",
}


def generate_maddm_script(
    ufo_path: str | Path,
    dm_candidate: str | int,
    out_dir: str | Path,
    observables: list[str],
    split_for_param_overlay: bool = False,
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
            ``output``).
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
    setup_lines.append(f"output {out_dir}")

    if split_for_param_overlay:
        setup_script = "\n".join(setup_lines) + "\n"
        launch_script = f"launch {out_dir} -f\n"
        return setup_script, launch_script

    setup_lines.append("launch -f")
    return "\n".join(setup_lines) + "\n"
