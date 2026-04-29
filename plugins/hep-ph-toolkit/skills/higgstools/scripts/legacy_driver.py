"""
legacy_driver.py — invoke HiggsBounds-5 + HiggsSignals-2 Fortran binaries via subprocess.

Parses stdout into a uniform result dict:
- HB per-channel: id, expref, obsratio, hb_result, reference
- HS native chi²/ndf fields (from HiggsSignals_get_Peak_Chisq output)

Produces:
- result.json
- per_channel.csv
- report.md
- input_dump.json

No analytic fallback. Raises HIGGSTOOLS_NUMERIC_CRASH (recoverable) on binary
segfault or unexpected exit code.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any

assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"


@dataclass
class ChannelResult:
    """Single HiggsBounds channel result."""
    id: int
    expref: str
    obsratio: float
    hb_result: int
    reference: str = ""


@dataclass
class HBResult:
    """Aggregated HiggsBounds result."""
    channels: list[ChannelResult]
    obsratio_max: float
    most_sensitive_channel: ChannelResult | None
    hb_version: str = "5.10.2"


@dataclass
class HSResult:
    """HiggsSignals result."""
    chi2_total: float
    chi2_rates: float
    chi2_masses: float
    ndf_rates: int
    ndf_masses: int
    p_value_rates: float
    p_value_masses: float
    hs_version: str = "2.6.2"


class HiggsToolsNumericCrash(Exception):
    """Raised when HB or HS binary crashes (segfault, non-zero exit)."""

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.code = "HIGGSTOOLS_NUMERIC_CRASH"
        self.mode = "recoverable"
        self.message = message
        self.context = context or {}


def _find_binary(build_dir: str, name: str) -> str:
    """Find HB or HS binary in build dir. Raises FileNotFoundError if absent."""
    candidates = [
        os.path.join(build_dir, "bin", name),
        os.path.join(build_dir, name),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    raise FileNotFoundError(
        f"{name} binary not found in {build_dir}. "
        f"Checked: {candidates}. Re-run bash _shared/installs/higgstools/install.sh install."
    )


def _parse_hb_output(stdout: str) -> list[ChannelResult]:
    """
    Parse HiggsBounds-5 per-channel output.

    Expected output format (one line per channel):
      <id>  <expref>  <obsratio>  <HBresult>  <reference>
    """
    channels = []
    # Look for the per-channel table in HB output
    # HB-5 prints: channel_id  experiment_ref  obsratio  HBresult  theory_ref
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Match lines with numeric ID, string, float, int pattern
        m = re.match(
            r"^\s*(\d+)\s+(\S+)\s+([0-9.eE+\-]+)\s+([01])\s*(\S*)",
            stripped,
        )
        if m:
            try:
                ch = ChannelResult(
                    id=int(m.group(1)),
                    expref=m.group(2),
                    obsratio=float(m.group(3)),
                    hb_result=int(m.group(4)),
                    reference=m.group(5) or "",
                )
                channels.append(ch)
            except (ValueError, IndexError):
                pass
    return channels


def _parse_hs_output(stdout: str) -> dict[str, Any]:
    """
    Parse HiggsSignals-2 output for chi2/ndf values.

    Looks for lines like:
      chi2 (total) = 89.357
      chi2 (rates) = 85.234
      chi2 (masses) = 4.123
      ndf (rates) = 80
      ndf (masses) = 5
    """
    result: dict[str, Any] = {
        "chi2_total": 0.0,
        "chi2_rates": 0.0,
        "chi2_masses": 0.0,
        "ndf_rates": 0,
        "ndf_masses": 0,
    }

    patterns = {
        "chi2_total":  r"chi2\s*\(\s*total\s*\)\s*=\s*([0-9.eE+\-]+)",
        "chi2_rates":  r"chi2\s*\(\s*rates\s*\)\s*=\s*([0-9.eE+\-]+)",
        "chi2_masses": r"chi2\s*\(\s*masses\s*\)\s*=\s*([0-9.eE+\-]+)",
        "ndf_rates":   r"ndf\s*\(\s*rates\s*\)\s*=\s*([0-9]+)",
        "ndf_masses":  r"ndf\s*\(\s*masses\s*\)\s*=\s*([0-9]+)",
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, stdout)
        if m:
            val = m.group(1)
            if key.startswith("ndf"):
                result[key] = int(val)
            else:
                result[key] = float(val)

    return result


def run_higgsbounds(
    hb_build: str,
    slha_file: str,
    n_neutral: int,
    n_charged: int,
    channels: str = "all",
) -> HBResult:
    """
    Run HiggsBounds-5 on the given SLHA file.

    Parameters
    ----------
    hb_build : str
        Path to HiggsBounds build directory.
    slha_file : str
        Path to SLHA2 input file.
    n_neutral : int
        Number of neutral Higgs bosons.
    n_charged : int
        Number of charged Higgs pairs (H+/H-).
    channels : str
        Channel filter: "all", "neutral", "charged", or CSV of IDs.

    Returns
    -------
    HBResult
        Parsed channel results.
    """
    hb_bin = _find_binary(hb_build, "HiggsBounds")

    # HB-5 SLHA invocation: HiggsBounds <whichanalyses> <whichinput> <nHneut> <nHplus> <prefix>
    # whichinput must be "SLHA"; prefix is the full path to the .slha file (including extension).
    # HB writes results back into the SLHA file, so CWD must contain the file or an absolute path
    # must be used.  We use the absolute path directly as prefix.
    slha_abs = os.path.abspath(slha_file)
    slha_dir = os.path.dirname(slha_abs)
    cmd = [hb_bin, "LandH", "SLHA", str(n_neutral), str(n_charged), slha_abs]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=slha_dir,
        )
    except subprocess.TimeoutExpired:
        raise HiggsToolsNumericCrash(
            f"HiggsBounds timed out after 120s for {slha_file}",
            context={"slha_file": slha_file},
        )
    except Exception as exc:
        raise HiggsToolsNumericCrash(
            f"HiggsBounds failed to start: {exc}",
            context={"slha_file": slha_file, "error": str(exc)},
        )

    if proc.returncode not in (0, 1):  # HB exits 1 for excluded
        raise HiggsToolsNumericCrash(
            f"HiggsBounds exited with code {proc.returncode}",
            context={
                "slha_file": slha_file,
                "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
            },
        )

    channel_results = _parse_hb_output(proc.stdout)

    # Determine most sensitive channel and obsratio_max
    obsratio_max = 0.0
    most_sensitive: ChannelResult | None = None
    for ch in channel_results:
        if ch.obsratio > obsratio_max:
            obsratio_max = ch.obsratio
            most_sensitive = ch

    return HBResult(
        channels=channel_results,
        obsratio_max=obsratio_max,
        most_sensitive_channel=most_sensitive,
    )


def run_higgssignals(
    hs_build: str,
    slha_file: str,
    dMh: dict[str, float] | None = None,
) -> HSResult:
    """
    Run HiggsSignals-2 on the given SLHA file.

    Parameters
    ----------
    hs_build : str
        Path to HiggsSignals build directory.
    slha_file : str
        Path to SLHA2 input file.
    dMh : dict or None
        Theoretical mass uncertainties per Higgs state.

    Returns
    -------
    HSResult
        Parsed chi2/ndf results from HS native output.
    """
    hs_bin = _find_binary(hs_build, "HiggsSignals")

    cmd = [hs_bin, "latestresults", "peak", "SLHA", "SLHA", slha_file]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise HiggsToolsNumericCrash(
            f"HiggsSignals timed out after 120s for {slha_file}",
            context={"slha_file": slha_file},
        )
    except Exception as exc:
        raise HiggsToolsNumericCrash(
            f"HiggsSignals failed to start: {exc}",
            context={"slha_file": slha_file, "error": str(exc)},
        )

    if proc.returncode != 0:
        raise HiggsToolsNumericCrash(
            f"HiggsSignals exited with code {proc.returncode}",
            context={
                "slha_file": slha_file,
                "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
            },
        )

    parsed = _parse_hs_output(proc.stdout)

    from p_value import compute_p_value
    p_rates = compute_p_value(parsed["chi2_rates"], parsed["ndf_rates"])
    p_masses = compute_p_value(parsed["chi2_masses"], parsed["ndf_masses"])

    return HSResult(
        chi2_total=parsed["chi2_total"],
        chi2_rates=parsed["chi2_rates"],
        chi2_masses=parsed["chi2_masses"],
        ndf_rates=parsed["ndf_rates"],
        ndf_masses=parsed["ndf_masses"],
        p_value_rates=p_rates,
        p_value_masses=p_masses,
    )


def write_outputs(
    output_dir: str,
    hb_result: HBResult | None,
    hs_result: HSResult | None,
    hb_allowed: bool,
    hs_consistent: bool,
    slha_file: str,
    backend: str = "legacy",
    dataset_version: str = "HB-5.10.2/HS-2.6.2",
) -> dict[str, Any]:
    """
    Write result.json, per_channel.csv, report.md, input_dump.json.

    Returns the result dict.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Build result dict
    result: dict[str, Any] = {
        "hb_allowed": hb_allowed,
        "hs_consistent": hs_consistent,
        "backend": backend,
        "dataset_version": dataset_version,
    }

    if hb_result is not None:
        result["obsratio_max"] = hb_result.obsratio_max
        if hb_result.most_sensitive_channel:
            ch = hb_result.most_sensitive_channel
            result["most_sensitive_channel"] = {
                "id": ch.id,
                "expref": ch.expref,
                "obsratio": ch.obsratio,
                "reference": ch.reference,
            }
        else:
            result["most_sensitive_channel"] = None

    if hs_result is not None:
        result["chi2_total"] = hs_result.chi2_total
        result["chi2_rates"] = hs_result.chi2_rates
        result["chi2_masses"] = hs_result.chi2_masses
        result["ndf_rates"] = hs_result.ndf_rates
        result["ndf_masses"] = hs_result.ndf_masses
        result["p_value_rates"] = hs_result.p_value_rates
        result["p_value_masses"] = hs_result.p_value_masses

    # Write result.json
    result_path = os.path.join(output_dir, "result.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    # Write per_channel.csv
    if hb_result is not None and hb_result.channels:
        csv_path = os.path.join(output_dir, "per_channel.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["id", "expref", "obsratio", "hb_result", "reference"]
            )
            writer.writeheader()
            for ch in hb_result.channels:
                writer.writerow(asdict(ch))

    # Write report.md
    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, "w") as f:
        f.write("# HiggsTools Constraint Report\n\n")
        f.write(f"**Backend:** {backend}  \n")
        f.write(f"**Dataset:** {dataset_version}  \n\n")
        if hb_result is not None:
            f.write("## HiggsBounds-5\n\n")
            f.write(f"- **hb_allowed:** {hb_allowed}  \n")
            f.write(f"- **obsratio_max:** {result.get('obsratio_max', 'N/A'):.4f}  \n")
            if hb_result.most_sensitive_channel:
                ch = hb_result.most_sensitive_channel
                f.write(f"- **Most sensitive channel:** {ch.id} ({ch.expref}), obsratio={ch.obsratio:.4f}  \n\n")
        if hs_result is not None:
            f.write("## HiggsSignals-2\n\n")
            f.write(f"- **hs_consistent:** {hs_consistent}  \n")
            f.write(f"- **chi2_total:** {hs_result.chi2_total:.3f}  \n")
            f.write(f"- **chi2_rates:** {hs_result.chi2_rates:.3f} (ndf={hs_result.ndf_rates})  \n")
            f.write(f"- **chi2_masses:** {hs_result.chi2_masses:.3f} (ndf={hs_result.ndf_masses})  \n")
            f.write(f"- **p_value_rates:** {hs_result.p_value_rates:.4f}  \n")
            f.write(f"- **p_value_masses:** {hs_result.p_value_masses:.4f}  \n\n")
        f.write(
            "> p-values assume the null hypothesis of SM + best-fit HS nuisance "
            "parameters; they are *not* a global goodness-of-fit — see HS manual §4.3.\n"
        )

    # Write input_dump.json
    input_dump = {
        "slha_file": slha_file,
        "backend": backend,
        "dataset_version": dataset_version,
    }
    input_dump_path = os.path.join(output_dir, "input_dump.json")
    with open(input_dump_path, "w") as f:
        json.dump(input_dump, f, indent=2, sort_keys=True)
        f.write("\n")

    return result
