"""Evaluate whether a parameter point is in the narrow-resonance regime.

The narrow-resonance trigger condition (from arXiv:2103.01944 and the project
memory `project_dm_tool_roles.md`) is:

    |m_med - 2 * m_dm| / m_med  <  threshold

where the default threshold is 0.1 (10%). This is the condition under which
the standard <sigma v> Taylor expansion used by MadDM and micrOMEGAs is
expected to break down and DRAKE should be used instead.

This module also provides helpers for the early-kinetic-decoupling (EKD) and
forbidden/threshold channel regimes, which are harder to express as a single
inequality and instead rely on physical judgment from the user.
"""

from __future__ import annotations


def is_narrow_resonance(
    m_dm: float,
    m_med: float,
    threshold: float = 0.1,
) -> bool:
    """Return True if the parameter point is in the narrow-resonance regime.

    Parameters
    ----------
    m_dm:
        Dark matter mass in GeV.
    m_med:
        Mediator mass in GeV (the s-channel resonance pole).
    threshold:
        Fractional proximity threshold. Default 0.1 (10%).

    Returns
    -------
    bool: True if |m_med - 2*m_dm| / m_med < threshold.

    Notes
    -----
    This is the trigger condition for invoking /drake instead of relying
    on the MadDM or micrOMEGAs result alone.

    Examples
    --------
    >>> is_narrow_resonance(m_dm=100.0, m_med=195.0)
    True   # |195 - 200| / 195 = 0.026 < 0.10

    >>> is_narrow_resonance(m_dm=100.0, m_med=250.0)
    False  # |250 - 200| / 250 = 0.20 > 0.10
    """
    if m_med <= 0:
        raise ValueError(f"m_med must be positive, got {m_med}")
    if m_dm <= 0:
        raise ValueError(f"m_dm must be positive, got {m_dm}")
    return abs(m_med - 2.0 * m_dm) / m_med < threshold


def resonance_proximity(m_dm: float, m_med: float) -> float:
    """Return the fractional proximity to the resonance pole.

    Returns |m_med - 2*m_dm| / m_med.
    Values below 0.1 trigger the DRAKE regime.
    """
    if m_med <= 0:
        raise ValueError(f"m_med must be positive, got {m_med}")
    return abs(m_med - 2.0 * m_dm) / m_med


def regime_summary(
    m_dm: float,
    m_med: float | None = None,
    *,
    early_kinetic_decoupling: bool = False,
    forbidden_channel: bool = False,
    sommerfeld: bool = False,
    threshold: float = 0.1,
) -> dict[str, object]:
    """Summarise which DRAKE-relevant regimes apply to a parameter point.

    Returns a dict with:
        narrow_resonance (bool): resonance trigger condition
        proximity (float or None): |m_med - 2*m_dm| / m_med if m_med provided
        early_kinetic_decoupling (bool): user-flagged
        forbidden_channel (bool): user-flagged (m_X > m_chi; threshold effect)
        sommerfeld (bool): user-flagged
        use_drake (bool): True if any DRAKE regime applies
        recommended_model (str or None): suggested built-in DRAKE model key

    Notes
    -----
    early_kinetic_decoupling, forbidden_channel, and sommerfeld cannot be
    inferred from masses alone — they require knowledge of the model's
    coupling structure. The caller must pass these flags explicitly.
    """
    narrow = False
    prox: float | None = None
    if m_med is not None:
        narrow = is_narrow_resonance(m_dm, m_med, threshold=threshold)
        prox = resonance_proximity(m_dm, m_med)

    use_drake = narrow or early_kinetic_decoupling or forbidden_channel or sommerfeld

    # Suggest a built-in model — conservative: pick first matching regime.
    recommended: str | None = None
    if narrow:
        recommended = "VRES"
    elif sommerfeld:
        recommended = "SE"
    elif forbidden_channel:
        recommended = "TH"
    # early_kinetic_decoupling does not map cleanly to a single built-in;
    # SE uses the fluid solver which handles EKD.

    return {
        "narrow_resonance": narrow,
        "proximity": prox,
        "early_kinetic_decoupling": early_kinetic_decoupling,
        "forbidden_channel": forbidden_channel,
        "sommerfeld": sommerfeld,
        "use_drake": use_drake,
        "recommended_model": recommended,
    }
