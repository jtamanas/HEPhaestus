"""Tests for the LaTeX-availability fallback in ``styles/hep_ph_style.py``.

Covers:

- LaTeX available -> ``text.usetex`` stays ``True``
- LaTeX binary missing -> ``text.usetex`` forced ``False`` with one log message
- LaTeX present but compile fails -> ``text.usetex`` forced ``False``
- ``check_overlaps`` renders without exception under both modes
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, must come before pyplot import

import matplotlib.pyplot as plt
import pytest

# Ensure ``styles/`` is importable when tests are collected from the repo root.
_STYLES_DIR = Path(__file__).resolve().parent.parent
if str(_STYLES_DIR) not in sys.path:
    sys.path.insert(0, str(_STYLES_DIR))

import hep_ph_style as hps  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_latex_cache_and_rc(monkeypatch):
    """Reset the cached probe result and rcParams between tests."""
    monkeypatch.setattr(hps, "_LATEX_AVAILABLE", None, raising=False)
    with matplotlib.rc_context():
        yield


# ---------------------------------------------------------------------------
# LaTeX available
# ---------------------------------------------------------------------------
def test_usetex_preserved_when_latex_available(monkeypatch):
    """If LaTeX is available, ``set_hep_context`` leaves ``usetex`` True."""
    monkeypatch.setattr(hps, "_probe_latex", lambda: True)
    hps.set_hep_context("analytic")
    assert matplotlib.rcParams["text.usetex"] is True


# ---------------------------------------------------------------------------
# LaTeX binary missing
# ---------------------------------------------------------------------------
def test_usetex_forced_false_when_latex_binary_missing(monkeypatch, caplog):
    """If neither ``latex`` nor ``pdflatex`` is on PATH, fall back cleanly."""
    monkeypatch.setattr(hps.shutil, "which", lambda _: None)

    with caplog.at_level(logging.INFO, logger=hps.logger.name):
        hps.set_hep_context("analytic")

    assert matplotlib.rcParams["text.usetex"] is False
    assert matplotlib.rcParams["mathtext.fontset"] == "cm"
    fallback_records = [r for r in caplog.records if "LaTeX unavailable" in r.getMessage()]
    assert len(fallback_records) == 1


# ---------------------------------------------------------------------------
# LaTeX present but compile fails (e.g., missing type1cm.sty)
# ---------------------------------------------------------------------------
def test_usetex_forced_false_when_compile_fails(monkeypatch):
    """A LaTeX binary exists but rendering raises -> fall back."""
    monkeypatch.setattr(hps.shutil, "which", lambda name: f"/usr/bin/{name}")
    # Force the probe to simulate a compile failure (e.g., type1cm missing).
    monkeypatch.setattr(hps, "_probe_latex", lambda: False)

    hps.set_hep_context("slate")

    assert matplotlib.rcParams["text.usetex"] is False
    assert matplotlib.rcParams["mathtext.fontset"] == "cm"


# ---------------------------------------------------------------------------
# check_overlaps smoke test in both modes
# ---------------------------------------------------------------------------
def _render_and_check(fig):
    ax = fig.gca()
    ax.plot([0, 1, 2], [0, 1, 4], label=r"$y = x^2$")
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$y$")
    ax.set_title(r"$\alpha + \beta$")
    ax.legend()
    return hps.check_overlaps(fig)


def test_check_overlaps_runs_in_fallback_mode(monkeypatch):
    """``check_overlaps`` must not raise when LaTeX is unavailable."""
    monkeypatch.setattr(hps, "_probe_latex", lambda: False)
    hps.set_hep_context("analytic")

    fig, _ = plt.subplots()
    try:
        issues = _render_and_check(fig)
    finally:
        plt.close(fig)

    assert isinstance(issues, list)


def test_check_overlaps_runs_with_real_probe():
    """With the real probe (LaTeX may or may not be present), rendering succeeds."""
    hps.set_hep_context("analytic")

    fig, _ = plt.subplots()
    try:
        issues = _render_and_check(fig)
    finally:
        plt.close(fig)

    assert isinstance(issues, list)


# ---------------------------------------------------------------------------
# Probe caches its result
# ---------------------------------------------------------------------------
def test_probe_latex_caches_result(monkeypatch):
    """``_probe_latex`` is cached per-process so it isn't re-run every call."""
    calls = {"which": 0}

    def _counting_which(_):
        calls["which"] += 1
        return None

    monkeypatch.setattr(hps.shutil, "which", _counting_which)
    monkeypatch.setattr(hps, "_LATEX_AVAILABLE", None, raising=False)

    assert hps._probe_latex() is False
    assert hps._probe_latex() is False
    # Second invocation should hit the cached branch without reconsulting ``which``.
    assert calls["which"] <= 2
