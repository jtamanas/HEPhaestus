#!/usr/bin/env python3
"""
parse_maddm_results.py — MadDM results.txt → gamlike/v1 JSON parser.

Usage:
    python parse_maddm_results.py <results-path> [--out <json-path>] [--md-summary <md-path>]

Exit codes:
    0 — Parsed successfully; JSON written.
    2 — Input file not found.
    3 — Input file present but malformed (invariant violation).

Stable invocation path (D-DPATH):
    plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py

Consumers call via subprocess.run and read the JSON with json.loads().
No Python import API (D17). No --strict mode (D6).
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

PARSER_VERSION = "0.1.0"

# Section banners — 3-line #-bordered blocks (48 or 49 # chars)
BANNER_HEADER = "MadDM v."  # substring match inside the bordered line
BANNER_RELIC = "# Relic Density"
BANNER_DIRECT = "# Direct Detection [cm^2]"
BANNER_INDIRECT = "# Indirect Detection"
BANNER_FLUXES = "# CR Flux at Earth"  # 49-char border; prefix match

# D11 / O7 — spectral has different banner shape (1-line + 1-line column comment)
SPECTRAL_SECTION_HEADER = "# Gamma-line spectrum and line limits"

# Continuum/line sub-block headers (inside Indirect Detection)
CONTINUUM_HEADER = "# <sigma v>[cm^3 s^-1] of continuum spectrum"
LINE_HEADER = "# <sigma v>[cm^3 s^-1] of line spectrum"
GLOBAL_FERMI_HEADER = "# Global Fermi dSph Limit computed with"
SIGMAV_METHOD_PREFIX = "# Annihilation cross section computed with the method:"

# Spectral experiment header
SPECTRAL_EXP_RE = re.compile(r'^# (.+?) \(ArXiv:(\S+?)\)\s*$')
SPECTRAL_ROI_RE = re.compile(r'^ROI\s+=\s+([\d.]+)')
SPECTRAL_JFACTOR_RE = re.compile(r'^J-factor\s+=\s+(\S+)')
NO_PEAKS_LINE = "# No peaks found: out of detection range."

# Fluxes source method
FLUXES_METHOD_RE = re.compile(r'^# Fluxes calculated using the spectra from (.+)$')

# G13 source reference — literal string; tests assert this exact value
G13_SOURCE_REF = "maddm_run_interface.py:3572-3574"

# Canonical KV line regex (D14 / spec §2.5.2)
# Key: letters, digits, _, parens, %, #, -, *, spaces (for 'Omega h^2' legacy alias)
_KV_RE = re.compile(
    r'^(?P<key>[-A-Za-z_%*][\w()%#\-\*\s\^]*?)'  # key (may contain spaces/^/- for legacy alias; may start with - for -2*log)
    r'\s+=\s+'                                   # padded equals
    r'(?P<value>'
    r'    \[[^\]]+\]'                            # bracketed pair
    r'    |'
    r'    -?\d[\d.eE+\-]*'                       # numeric (incl. negative, scientific)
    r'    |'
    r'    -?(?:nan|inf)\s*%?'                    # NaN / Inf literals (D15), optionally with '%'
    r'    |'
    r'    \w+(?:\([\w\s]+\))?'                   # string label (e.g. peak_0(states))
    r')'
    r'(?:\s*%)?'                                 # optional trailing '%' for channel lines
    r'(?:\s*\#\s*(?P<comment>.*?))?'             # optional inline comment
    r'\s*$',
    re.VERBOSE,
)

# Pattern for bracketed numeric pair [A,B]
_BRACKET_RE = re.compile(r'^\[(-?[\d.eE+\-]+),(-?[\d.eE+\-]+)\]')

# Pattern for percent channel lines: %_<initial>_<final> = 85.00 %  (or nan %)
_CHANNEL_RE = re.compile(r'^%_(?P<initial>[^_]+)_(?P<final>.+?)\s*$')

# Pattern for peak lines: peak_<n>(<states>) = <energy>
_PEAK_KEY_RE = re.compile(r'^peak_(\d+)\((.+)\)$')
_PEAK_NUM_RE = re.compile(r'^(\w+)_(\d+)$')


# ── Warning / Error types ──────────────────────────────────────────────────────

class ParserError(Exception):
    """Fatal parse error — emits to stderr + exit 3."""
    def __init__(self, message: str, section: str = "", line_num: int = 0):
        super().__init__(message)
        self.section = section
        self.line_num = line_num


def _make_warning(code: str, field: str, reason: str, source_ref: str = "") -> dict:
    return {"code": code, "field": field, "reason": reason, "source_ref": source_ref}


# ── Numeric parsing helpers ────────────────────────────────────────────────────

def _parse_num(val_str: str, field: str, warnings: list) -> Optional[float]:
    """
    Parse a numeric string to float. NaN/Inf → null + warning (D15).
    Returns None for null/invalid.
    """
    s = val_str.strip().lower()
    if s in ("nan", "-nan"):
        warnings.append(_make_warning(
            "FIELD_NAN", field,
            f"Producer emitted 'nan' for {field}; converted to null (D15).",
            ""
        ))
        return None
    if s in ("inf", "-inf", "+inf"):
        warnings.append(_make_warning(
            "FIELD_INF", field,
            f"Producer emitted '{val_str}' for {field}; converted to null (D15).",
            ""
        ))
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


def _parse_bracket(val_str: str, field_prefix: str, warnings: list) -> tuple:
    """Parse [A,B] → (A_float_or_none, B_float_or_none)."""
    m = _BRACKET_RE.match(val_str.strip())
    if not m:
        return (None, None)
    a = _parse_num(m.group(1), f"{field_prefix}[0]", warnings)
    b = _parse_num(m.group(2), f"{field_prefix}[1]", warnings)
    return (a, b)


def _parse_kv(line: str) -> Optional[tuple]:
    """Parse a KV line. Returns (key, value_str, comment_str) or None."""
    m = _KV_RE.match(line.rstrip())
    if not m:
        return None
    key = m.group("key").strip()
    value = m.group("value").strip() if m.group("value") else ""
    comment = m.group("comment").strip() if m.group("comment") else ""
    return (key, value, comment)


# ── Section detection ──────────────────────────────────────────────────────────

def detect_sections(lines: list) -> dict:
    """
    Scan lines and identify top-level section ranges.
    Returns dict mapping section name → slice (start, end) line indices.
    3-line bordered banners: the content starts 2 lines after the first `#...#` line.
    Spectral: 1-line + 1-line column-comment banner.
    """
    sections = {}
    n = len(lines)
    unknown_banners = []

    i = 0
    while i < n:
        stripped = lines[i].rstrip()

        # Detect 3-line bordered banners (48 or 49 # chars)
        if re.match(r'^#{48,49}$', stripped):
            # Next line should be the title, then another #-border
            if i + 2 < n:
                title_line = lines[i + 1].rstrip()
                close_line = lines[i + 2].rstrip()
                if re.match(r'^#{48,49}$', close_line):
                    # We have a valid 3-line banner
                    title = title_line.strip().rstrip('#').strip()
                    content_start = i + 3  # first content line after the 3-line banner

                    # Find next banner (the start of the next section)
                    j = content_start
                    while j < n:
                        if re.match(r'^#{48,49}$', lines[j].rstrip()):
                            break
                        if lines[j].rstrip() == SPECTRAL_SECTION_HEADER:
                            break
                        j += 1

                    if BANNER_HEADER in title:
                        sections["header"] = slice(content_start, j)
                    elif "Relic Density" in title:
                        sections["relic"] = slice(content_start, j)
                    elif "Direct Detection" in title:
                        sections["direct"] = slice(content_start, j)
                    elif "Indirect Detection" in title:
                        sections["indirect"] = slice(content_start, j)
                    elif "CR Flux at Earth" in title:
                        sections["fluxes_source"] = slice(content_start, j)
                    else:
                        unknown_banners.append(title)

                    i += 3
                    continue

        # Detect spectral section (1-line banner)
        if stripped == SPECTRAL_SECTION_HEADER:
            content_start = i + 1
            # Skip the column-comment line
            if content_start < n and lines[content_start].rstrip().startswith("# peak"):
                content_start += 1
            # Find next section boundary
            j = content_start
            while j < n:
                if re.match(r'^#{48,49}$', lines[j].rstrip()):
                    break
                j += 1
            sections["spectral"] = slice(content_start, j)
            i = j
            continue

        i += 1

    sections["_unknown_banners"] = unknown_banners
    return sections


# ── Per-section parsers ────────────────────────────────────────────────────────

def _parse_header(lines: list, section_slice: slice) -> Optional[str]:
    """Extract MadDM version from header section lines. Returns version string or None."""
    for line in lines[section_slice]:
        m = re.search(r'MadDM v\.\s*([\d.]+)', line)
        if m:
            return m.group(1).strip()
    return None


def _parse_relic(lines: list, section_slice: slice, warnings: list) -> dict:
    """Parse the Relic Density section."""
    result = {
        "present": True,
        "Omegah2": None,
        "Omegah_Planck": None,
        "xsi": None,
        "x_f": None,
        "sigmav_xf": None,
        "initial_states": [],
        "channels": {},
        "channels_sum_pct": None,
    }

    for line in lines[section_slice]:
        stripped = line.rstrip()
        if not stripped or stripped.startswith('#'):
            continue

        kv = _parse_kv(stripped)
        if not kv:
            continue
        key, val_str, comment = kv

        # D8: legacy MadDM < 3.2 alias
        if key in ("Omegah2", "Omega h^2"):
            result["Omegah2"] = _parse_num(val_str, "relic.Omegah2", warnings)

        elif key == "Omegah_Planck":
            result["Omegah_Planck"] = _parse_num(val_str, "relic.Omegah_Planck", warnings)

        elif key == "xsi":
            result["xsi"] = _parse_num(val_str, "relic.xsi", warnings)

        elif key == "x_f":
            result["x_f"] = _parse_num(val_str, "relic.x_f", warnings)

        elif key == "sigmav_xf":
            result["sigmav_xf"] = _parse_num(val_str, "relic.sigmav_xf", warnings)

        elif key.startswith("%_"):
            # Channel percent line: key is "%_<initial>_<final>"
            chan_m = _CHANNEL_RE.match(key)
            if chan_m:
                initial = chan_m.group("initial")
                final = chan_m.group("final")
                # Value may be: '85.00', 'nan %', 'nan', '85.00 %' etc.
                pct_str = val_str.rstrip().rstrip('%').strip()
                pct = _parse_num(pct_str, f"relic.channels.{initial}.{final}", warnings)
                if initial not in result["channels"]:
                    result["channels"][initial] = {}
                result["channels"][initial][final] = pct

    # Compute derived fields
    result["initial_states"] = sorted(result["channels"].keys())

    all_pcts = []
    for finals in result["channels"].values():
        for pct in finals.values():
            if pct is not None:
                all_pcts.append(pct)
    result["channels_sum_pct"] = sum(all_pcts) if all_pcts else None

    return result


def _parse_direct(lines: list, section_slice: slice, warnings: list) -> dict:
    """Parse the Direct Detection section."""
    results_list = []
    for line in lines[section_slice]:
        stripped = line.rstrip()
        if not stripped or stripped.startswith('#'):
            continue
        kv = _parse_kv(stripped)
        if not kv:
            continue
        key, val_str, comment = kv
        if val_str.startswith('['):
            a, b = _parse_bracket(val_str, f"direct.{key}", warnings)
            results_list.append({
                "name": key,
                "experiment_label": comment.strip() if comment else None,
                "sig_cm2": a,
                "lim_cm2": b,
            })

    return {
        "present": True,
        "results": results_list,
    }


def _parse_indirect(lines: list, section_slice: slice, warnings: list) -> dict:
    """Parse the Indirect Detection section (including sub-blocks)."""
    result = {
        "present": True,
        "sigmav_method": None,
        "continuum": {"present": False, "channels": {}},
        "lines": {"present": False, "channels": {}},
        "global": {
            "flux_method": None,
            "Total_xsec": None,
            "TotalSM_xsec": None,
            "Fermi_Likelihood": None,
            "Fermi_pvalue": None,
            "Fermi_Likelihood_Thermal": None,
            "Fermi_pvalue_Thermal": None,
            "thermal_emitted": False,
        },
    }

    in_continuum = False
    in_lines_block = False

    for line in lines[section_slice]:
        stripped = line.rstrip()

        # Comment lines that carry information
        if stripped.startswith('#'):
            if SIGMAV_METHOD_PREFIX in stripped:
                method = stripped[len(SIGMAV_METHOD_PREFIX):].strip()
                result["sigmav_method"] = method if method else None
            elif CONTINUUM_HEADER in stripped:
                in_continuum = True
                in_lines_block = False
                result["continuum"]["present"] = True
            elif LINE_HEADER in stripped:
                in_lines_block = True
                in_continuum = False
                result["lines"]["present"] = True
            elif GLOBAL_FERMI_HEADER in stripped:
                in_continuum = False
                in_lines_block = False
                # Extract flux method: "# Global Fermi dSph Limit computed with <method> spectra"
                m = re.match(r'^# Global Fermi dSph Limit computed with (.+) spectra', stripped)
                if m:
                    result["global"]["flux_method"] = m.group(1).strip()
            continue

        if not stripped:
            continue

        kv = _parse_kv(stripped)
        if not kv:
            continue
        key, val_str, comment = kv

        if in_continuum:
            if val_str.startswith('['):
                a, b = _parse_bracket(val_str, f"indirect.continuum.{key}", warnings)
                result["continuum"]["channels"][key] = {"sigmav": a, "limit": b}
            elif key in ("Total_xsec", "TotalSM_xsec", "Fermi_Likelihood", "Fermi_pvalue",
                         "Fermi_Likelihood(Thermal)", "Fermi_pvalue(Thermal)"):
                in_continuum = False  # fall through to global
            else:
                continue

        if in_lines_block:
            if val_str.startswith('['):
                a, b = _parse_bracket(val_str, f"indirect.lines.{key}", warnings)
                result["lines"]["channels"][key] = {"sigmav": a, "limit": b}
            elif key in ("Total_xsec", "TotalSM_xsec", "Fermi_Likelihood", "Fermi_pvalue",
                         "Fermi_Likelihood(Thermal)", "Fermi_pvalue(Thermal)"):
                in_lines_block = False  # fall through to global
            else:
                continue

        # Global fields
        if key == "Total_xsec":
            if val_str.startswith('['):
                a, _ = _parse_bracket(val_str, "indirect.global.Total_xsec", warnings)
                result["global"]["Total_xsec"] = a
            else:
                result["global"]["Total_xsec"] = _parse_num(val_str, "indirect.global.Total_xsec", warnings)
        elif key == "TotalSM_xsec":
            if val_str.startswith('['):
                a, _ = _parse_bracket(val_str, "indirect.global.TotalSM_xsec", warnings)
                result["global"]["TotalSM_xsec"] = a
            else:
                result["global"]["TotalSM_xsec"] = _parse_num(val_str, "indirect.global.TotalSM_xsec", warnings)
        elif key == "Fermi_Likelihood":
            result["global"]["Fermi_Likelihood"] = _parse_num(val_str, "indirect.global.Fermi_Likelihood", warnings)
        elif key == "Fermi_pvalue":
            result["global"]["Fermi_pvalue"] = _parse_num(val_str, "indirect.global.Fermi_pvalue", warnings)
        elif key in ("Fermi_Likelihood(Thermal)", "Fermi_Likelihood_Thermal"):
            result["global"]["Fermi_Likelihood_Thermal"] = _parse_num(val_str, "indirect.global.Fermi_Likelihood_Thermal", warnings)
            result["global"]["thermal_emitted"] = True
        elif key in ("Fermi_pvalue(Thermal)", "Fermi_pvalue_Thermal"):
            result["global"]["Fermi_pvalue_Thermal"] = _parse_num(val_str, "indirect.global.Fermi_pvalue_Thermal", warnings)
            result["global"]["thermal_emitted"] = True

    return result


def _parse_spectral(lines: list, section_slice: slice, warnings: list) -> dict:
    """
    Parse the Gamma-line spectrum section.
    Per-peak aggregation by _<n> suffix (O8).
    """
    result = {
        "present": True,
        "experiments": [],
    }

    current_exp = None
    peaks_by_num = {}  # {n: {states, energy_GeV, flux, flux_UL, loglike_neg2, pvalue, error_code}}

    def _flush_experiment():
        if current_exp is not None:
            # Build peaks list sorted by num
            peaks = []
            for num in sorted(peaks_by_num.keys()):
                p = peaks_by_num[num]
                peaks.append({
                    "num": num,
                    "states": p.get("states"),
                    "energy_GeV": p.get("energy_GeV"),
                    "flux": p.get("flux"),
                    "flux_UL": p.get("flux_UL"),
                    "loglike_neg2": p.get("loglike_neg2"),
                    "pvalue": p.get("pvalue"),
                    "error_code": p.get("error_code", 0),
                })
            current_exp["peaks"] = peaks
            result["experiments"].append(current_exp)

    for line in lines[section_slice]:
        stripped = line.rstrip()

        if stripped == NO_PEAKS_LINE:
            if current_exp is not None:
                current_exp["no_peaks_out_of_range"] = True
                current_exp["peaks"] = []
                exp_name = current_exp.get("experiment_name", "unknown")
                warnings.append(_make_warning(
                    "NO_PEAKS_OUT_OF_DETECTION_RANGE",
                    f"spectral.{exp_name}.peaks",
                    f"No peaks found out of detection range for experiment '{exp_name}' (G16).",
                    "maddm_run_interface.py:3590-3595",
                ))
                result["experiments"].append(current_exp)
                current_exp = None
                peaks_by_num = {}
            continue

        if stripped.startswith('#'):
            exp_m = SPECTRAL_EXP_RE.match(stripped)
            if exp_m:
                # Flush previous experiment
                _flush_experiment()
                peaks_by_num = {}
                current_exp = {
                    "experiment_name": exp_m.group(1).replace(' ', '_'),
                    "arxiv_number": exp_m.group(2),
                    "ROI": None,
                    "Jfactor": None,
                    "astrophysical_parameters": None,  # G19 reserved
                    "no_peaks_out_of_range": False,
                    "peaks": [],
                }
            continue

        if not stripped:
            continue

        # ROI line: different format '%1.1f'
        roi_m = SPECTRAL_ROI_RE.match(stripped)
        if roi_m and current_exp is not None:
            current_exp["ROI"] = _parse_num(roi_m.group(1), "spectral.ROI", warnings)
            continue

        # J-factor line
        jf_m = SPECTRAL_JFACTOR_RE.match(stripped)
        if jf_m and current_exp is not None:
            current_exp["Jfactor"] = _parse_num(jf_m.group(1), "spectral.Jfactor", warnings)
            continue

        kv = _parse_kv(stripped)
        if not kv:
            continue
        key, val_str, comment = kv

        # Per-peak aggregation (O8)
        # peak_<n>(<states>) = <energy>  [optional # error: <code>]
        pm = _PEAK_KEY_RE.match(key)
        if pm:
            num = int(pm.group(1))
            states = pm.group(2)
            energy = _parse_num(val_str, f"spectral.peak_{num}.energy_GeV", warnings)
            error_code = 0
            if comment:
                ec_m = re.search(r'error:\s*(\d+)', comment)
                if ec_m:
                    error_code = int(ec_m.group(1))
            if num not in peaks_by_num:
                peaks_by_num[num] = {}
            peaks_by_num[num]["states"] = states
            peaks_by_num[num]["energy_GeV"] = energy
            peaks_by_num[num]["error_code"] = error_code
            continue

        # flux_<n> = [flux, flux_UL]
        flux_m = re.match(r'^flux_(\d+)$', key)
        if flux_m:
            num = int(flux_m.group(1))
            if val_str.startswith('['):
                a, b = _parse_bracket(val_str, f"spectral.flux_{num}", warnings)
            else:
                a = _parse_num(val_str, f"spectral.flux_{num}", warnings)
                b = None
            if num not in peaks_by_num:
                peaks_by_num[num] = {}
            peaks_by_num[num]["flux"] = a
            peaks_by_num[num]["flux_UL"] = b
            continue

        # -2*log(Likelihood)_<n>
        like_m = re.match(r'^-2\*log\(Likelihood\)_(\d+)$', key)
        if like_m:
            num = int(like_m.group(1))
            v = _parse_num(val_str, f"spectral.loglike_{num}", warnings)
            if num not in peaks_by_num:
                peaks_by_num[num] = {}
            peaks_by_num[num]["loglike_neg2"] = v
            continue

        # p-value_<n>
        pval_m = re.match(r'^p-value_(\d+)$', key)
        if pval_m:
            num = int(pval_m.group(1))
            v = _parse_num(val_str, f"spectral.pvalue_{num}", warnings)
            if num not in peaks_by_num:
                peaks_by_num[num] = {}
            peaks_by_num[num]["pvalue"] = v
            continue

    # Flush last experiment
    _flush_experiment()

    return result


def _parse_fluxes_source(lines: list, section_slice: slice, warnings: list) -> dict:
    """Parse the CR Flux at Earth section."""
    result = {
        "present": True,
        "method": None,
        "fluxes": {
            "neutrinos_e": None,
            "neutrinos_mu": None,
            "neutrinos_tau": None,
            "gammas": None,
            "positrons": None,  # G21 reserved
        },
    }

    for line in lines[section_slice]:
        stripped = line.rstrip()
        if stripped.startswith('#'):
            m = FLUXES_METHOD_RE.match(stripped)
            if m:
                result["method"] = m.group(1).strip()
            continue
        if not stripped:
            continue

        kv = _parse_kv(stripped)
        if not kv:
            continue
        key, val_str, _ = kv

        # Map Flux_<name> → fluxes.<name>
        if key == "Flux_neutrinos_e":
            result["fluxes"]["neutrinos_e"] = _parse_num(val_str, "fluxes_source.fluxes.neutrinos_e", warnings)
        elif key == "Flux_neutrinos_mu":
            result["fluxes"]["neutrinos_mu"] = _parse_num(val_str, "fluxes_source.fluxes.neutrinos_mu", warnings)
        elif key == "Flux_neutrinos_tau":
            result["fluxes"]["neutrinos_tau"] = _parse_num(val_str, "fluxes_source.fluxes.neutrinos_tau", warnings)
        elif key == "Flux_gammas":
            result["fluxes"]["gammas"] = _parse_num(val_str, "fluxes_source.fluxes.gammas", warnings)
        elif key == "Flux_positrons":
            # Would populate if producer emits; currently reserved (G21)
            result["fluxes"]["positrons"] = _parse_num(val_str, "fluxes_source.fluxes.positrons", warnings)

    return result


# ── Invariant checks ──────────────────────────────────────────────────────────

def _check_invariants(parsed: dict, warnings: list) -> None:
    """
    Check invariants I1–I6. Raises ParserError for hard violations.
    Appends FIELD_GATED warnings for soft gates.
    """
    relic = parsed["relic"]
    direct = parsed["direct"]
    indirect = parsed["indirect"]
    xsi = relic.get("xsi")

    # I2: relic.present → Omegah2 + ≥1 channel
    if relic["present"]:
        if relic["Omegah2"] is None and not any(
            True for _warns in warnings if _warns.get("field", "").startswith("relic.Omegah2")
        ):
            raise ParserError(
                "I2 violation: relic section present but Omegah2 is missing",
                section="relic",
            )
        if not relic["channels"]:
            raise ParserError(
                "I2 violation: relic section present but no channels found",
                section="relic",
            )

    # I3: direct.present → ≥1 result
    if direct["present"] and not direct["results"]:
        raise ParserError(
            "I3 violation: direct section present but no experiment rows found",
            section="direct",
        )

    # I1: indirect.present → exactly one of Total_xsec / TotalSM_xsec non-null
    if indirect["present"]:
        g = indirect["global"]
        tx = g["Total_xsec"]
        sm = g["TotalSM_xsec"]
        if tx is None and sm is None:
            raise ParserError(
                "I1 violation: indirect section present but both Total_xsec and TotalSM_xsec are null",
                section="indirect",
            )
        if tx is not None and sm is not None:
            raise ParserError(
                "I1 violation: indirect section has both Total_xsec and TotalSM_xsec non-null (XOR required)",
                section="indirect",
            )

    # I4: indirect.present AND xsi < 1.0 → thermal pair present
    # Converse: xsi >= 1.0 → thermal pair null + FIELD_GATED warning
    if indirect["present"]:
        g = indirect["global"]
        if xsi is not None and xsi >= 1.0:
            # Emit FIELD_GATED warning for each gated thermal field
            if not g["thermal_emitted"]:
                warnings.append(_make_warning(
                    "FIELD_GATED",
                    "indirect.global.Fermi_Likelihood_Thermal",
                    f"xsi >= 1 (xsi_value={xsi:.2e}); MadDM does not emit thermal-rescaled likelihood",
                    G13_SOURCE_REF,
                ))
                warnings.append(_make_warning(
                    "FIELD_GATED",
                    "indirect.global.Fermi_pvalue_Thermal",
                    f"xsi >= 1 (xsi_value={xsi:.2e}); MadDM does not emit thermal-rescaled p-value",
                    G13_SOURCE_REF,
                ))
            g["thermal_emitted"] = False
            g["Fermi_Likelihood_Thermal"] = None
            g["Fermi_pvalue_Thermal"] = None

    # I5: no_peaks_out_of_range → peaks == []
    for exp in parsed["spectral"]["experiments"]:
        if exp["no_peaks_out_of_range"] and exp["peaks"]:
            raise ParserError(
                f"I5 violation: experiment '{exp['experiment_name']}' has no_peaks_out_of_range=true but peaks list is non-empty",
                section="spectral",
            )


# ── Empty template ─────────────────────────────────────────────────────────────

def _empty_template() -> dict:
    """Return a fully-null all-sections-absent template."""
    return {
        "schema_version": "gamlike/v1",
        "_meta": {
            "source_file": "",
            "parser_version": PARSER_VERSION,
            "maddm_version": None,
            "parsed_at": "",
        },
        "relic": {
            "present": False,
            "Omegah2": None,
            "Omegah_Planck": None,
            "xsi": None,
            "x_f": None,
            "sigmav_xf": None,
            "initial_states": [],
            "channels": {},
            "channels_sum_pct": None,
        },
        "direct": {
            "present": False,
            "results": [],
        },
        "indirect": {
            "present": False,
            "sigmav_method": None,
            "continuum": {"present": False, "channels": {}},
            "lines": {"present": False, "channels": {}},
            "global": {
                "flux_method": None,
                "Total_xsec": None,
                "TotalSM_xsec": None,
                "Fermi_Likelihood": None,
                "Fermi_pvalue": None,
                "Fermi_Likelihood_Thermal": None,
                "Fermi_pvalue_Thermal": None,
                "thermal_emitted": False,
            },
        },
        "spectral": {
            "present": False,
            "experiments": [],
        },
        "fluxes_source": {
            "present": False,
            "method": None,
            "fluxes": {
                "neutrinos_e": None,
                "neutrinos_mu": None,
                "neutrinos_tau": None,
                "gammas": None,
                "positrons": None,
            },
        },
        "warnings": [],
    }


# ── Main parse function ────────────────────────────────────────────────────────

def parse_file(path: Path) -> dict:
    """
    Parse a MadDM_results.txt file. Returns the gamlike/v1 JSON dict.
    Raises ParserError on invariant violation (caller converts to exit 3).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    doc = _empty_template()
    doc["_meta"]["source_file"] = str(path.resolve())
    doc["_meta"]["parsed_at"] = datetime.datetime.utcnow().isoformat() + "Z"

    warnings = doc["warnings"]

    # Check for MadDM version
    maddm_ver_m = None
    for line in lines[:5]:
        m = re.search(r'MadDM v\.\s*([\d.]+)', line)
        if m:
            maddm_ver_m = m.group(1).strip()
            break
    doc["_meta"]["maddm_version"] = maddm_ver_m

    if maddm_ver_m and not maddm_ver_m.startswith("3."):
        warnings.append(_make_warning(
            "MADDM_VERSION_UNTESTED",
            "_meta.maddm_version",
            f"MadDM version '{maddm_ver_m}' is not tested with this parser (tested against 3.2). "
            "Output may differ.",
            "",
        ))

    # Detect sections
    sections = detect_sections(lines)

    # Unknown banners
    for banner in sections.get("_unknown_banners", []):
        warnings.append(_make_warning(
            "UNKNOWN_SECTION",
            f"unknown_section",
            f"Unrecognized section banner: '{banner}'. Content ignored (forward-compat).",
            "",
        ))

    # Parse each section
    if "relic" in sections:
        doc["relic"] = _parse_relic(lines, sections["relic"], warnings)

    if "direct" in sections:
        doc["direct"] = _parse_direct(lines, sections["direct"], warnings)

    if "indirect" in sections:
        doc["indirect"] = _parse_indirect(lines, sections["indirect"], warnings)

    if "spectral" in sections:
        doc["spectral"] = _parse_spectral(lines, sections["spectral"], warnings)

    if "fluxes_source" in sections:
        doc["fluxes_source"] = _parse_fluxes_source(lines, sections["fluxes_source"], warnings)

    # Invariant checks (may raise ParserError)
    _check_invariants(doc, warnings)

    return doc


# ── Markdown summary ──────────────────────────────────────────────────────────

def _render_md_summary(doc: dict) -> str:
    meta = doc["_meta"]
    relic = doc["relic"]
    direct = doc["direct"]
    indirect = doc["indirect"]
    spectral = doc["spectral"]
    fluxes = doc["fluxes_source"]
    warns = doc["warnings"]

    lines = [
        "### MadDM gamlike summary",
        f"Source: `{meta['source_file']}` (MadDM {meta['maddm_version']})",
        "",
    ]

    if relic["present"]:
        lines.append(
            f"- **Relic:** Ωh² = {relic['Omegah2']} "
            f"(Ωh²_Planck = {relic['Omegah_Planck']}, "
            f"ξ = {relic['xsi']}, x_f = {relic['x_f']})"
        )
        # Top 5 channels by pct
        flat = {}
        for finals in relic["channels"].values():
            for k, v in finals.items():
                if v is not None:
                    flat[k] = v
        top5 = sorted(flat.items(), key=lambda x: (x[1] or 0), reverse=True)[:5]
        if top5:
            top_str = ", ".join(f"{k}: {v:.2f}%" for k, v in top5)
            lines.append(f"  Top relic channels: {top_str}")
    else:
        lines.append("- **Relic:** not run")

    if direct["present"]:
        lines.append(f"- **Direct detection:** {len(direct['results'])} experiment(s)")
    else:
        lines.append("- **Direct detection:** not run")

    if indirect["present"]:
        g = indirect["global"]
        lines.append(
            f"- **Indirect detection:** Total_xsec={g['Total_xsec']}, "
            f"Fermi_pvalue={g['Fermi_pvalue']}, thermal={g['thermal_emitted']}"
        )
    else:
        lines.append("- **Indirect detection:** not run")

    if spectral["present"]:
        lines.append(f"- **Gamma-line spectrum:** {len(spectral['experiments'])} experiment(s)")
    else:
        lines.append("- **Gamma-line spectrum:** not run")

    if fluxes["present"]:
        lines.append(f"- **CR fluxes (source):** method={fluxes['method']}")
    else:
        lines.append("- **CR fluxes (source):** not run")

    lines.append("")
    warn_codes = [w["code"] for w in warns]
    if warn_codes:
        lines.append(f"Warnings: {len(warns)} [{', '.join(set(warn_codes))}]")
    else:
        lines.append("Warnings: none")

    return "\n".join(lines) + "\n"


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Parse MadDM_results.txt → gamlike/v1 JSON (v0 parser only; no physics interpretation).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  Parsed successfully; JSON written.
  2  Input file not found.
  3  Input file present but malformed (invariant violation).
""",
    )
    ap.add_argument(
        "results_path",
        metavar="<results-path>",
        help="Path to MadDM_results.txt",
    )
    ap.add_argument(
        "--out",
        metavar="<json-path>",
        default=None,
        help="Where to write gamlike.json (default: <results-path>.gamlike.json)",
    )
    ap.add_argument(
        "--md-summary",
        metavar="<md-path>",
        default=None,
        help="Where to write optional markdown summary (not written unless this flag is set)",
    )
    args = ap.parse_args()

    results_path = Path(args.results_path)
    if not results_path.exists():
        print(f"ERROR: input file not found: {results_path}", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.out) if args.out else results_path.with_suffix(results_path.suffix + ".gamlike.json")

    try:
        doc = parse_file(results_path)
    except ParserError as e:
        print(
            f"ERROR: malformed input (exit 3): {e} "
            f"[section={e.section!r}, line={e.line_num}]",
            file=sys.stderr,
        )
        sys.exit(3)

    out_path.write_text(
        json.dumps(doc, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    if args.md_summary:
        md = _render_md_summary(doc)
        Path(args.md_summary).write_text(md, encoding="utf-8")

    # Stdout: absolute path only (so callers can pipe)
    print(str(out_path.resolve()))


if __name__ == "__main__":
    main()
