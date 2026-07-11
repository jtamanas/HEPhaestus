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


class HiggsBoundsNoResultError(HiggsToolsNumericCrash):
    """HB ran (exit 0/1) but produced ZERO parsable results.

    Distinct from a crash: HiggsBounds-5 is known to exit 0 while doing no
    work (e.g. its Fortran buffer truncates file prefixes at ~100 chars, it
    prints "problem opening the SLHA file", and writes no HiggsBoundsResults
    block). Returning an empty result would make compute_hb_allowed([])
    vacuously True — a silent false "allowed". Subclasses
    HiggsToolsNumericCrash so existing recoverable-blocker handling applies,
    but with its own code so the failure is diagnosable.
    """

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message, context)
        self.code = "HIGGSTOOLS_HB_NO_RESULT"


class HiggsSignalsNoResultError(HiggsToolsNumericCrash):
    """HS ran (exit 0) but produced NO ``HiggsSignalsResults`` block.

    Exact HS-side analogue of :class:`HiggsBoundsNoResultError`. HiggsSignals-2
    writes its chi^2 into ``Block HiggsSignalsResults`` INSIDE the SLHA file
    (parallel to HB's ``HiggsBoundsResults``); nothing lands on stdout. Two
    known ways it exits 0 while doing no work:

    * wrong command-line argument count — HS-2.6.2 prints "Incorrect number of
      parameters given on command line" and does a Fortran STOP that exits 0;
    * unopenable input (truncated prefix, missing file).

    In every case the driver used to fall through to a hardcoded
    ``chi2_total=0.0 / ndf=0`` default, making ``hs_consistent =
    (0.0 - chi2_sm_ref) < delta`` vacuously True for EVERY model — a silent
    "consistent" for a point HS never touched. Raise instead so the failure is
    loud and diagnosable, mirroring the HB-side HIGGSTOOLS_HB_NO_RESULT guard.
    """

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message, context)
        self.code = "HIGGSTOOLS_HS_NO_RESULT"


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


def _parse_hb_slha_results(slha_text: str) -> HBResult | None:
    """Parse the ``Block HiggsBoundsResults`` HB-5 writes back into the SLHA.

    In SLHA mode HiggsBounds-5 does NOT print per-channel results to stdout —
    it appends a ``HiggsBoundsResults`` block to the input file. Rows are
    ``<rank> <key> <value>`` with keys 1=channel id, 2=HBresult, 3=obsratio,
    4=ncombined, 5=||text description||. Rank 0 is the GLOBAL result (HB-5's
    verdict = the most statistically sensitive channel); ranks >= 1 are the
    sensitivity-ordered channel list. Note the global obsratio is that of the
    most SENSITIVE channel, not the numeric max across channels — a less
    sensitive channel may carry a higher raw obsratio.

    Returns None when the block is absent (e.g. HB never ran on this file),
    so callers can fall back to stdout parsing.
    """
    in_block = False
    ranked: dict[int, dict[str, Any]] = {}
    for line in slha_text.splitlines():
        stripped = line.strip()
        if re.match(r"^Block\s+HiggsBoundsResults\b", stripped, re.IGNORECASE):
            in_block = True
            continue
        if re.match(r"^(Block|DECAY)\s+", stripped, re.IGNORECASE):
            in_block = False
            continue
        if not in_block or not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"^(\d+)\s+(\d+)\s+(\S.*?)(?:\s*#.*)?$", stripped)
        if not m:
            continue
        rank, key, value = int(m.group(1)), int(m.group(2)), m.group(3).strip()
        entry = ranked.setdefault(rank, {})
        try:
            if key == 1:
                entry["id"] = int(value)
            elif key == 2:
                entry["hb_result"] = int(value)
            elif key == 3:
                entry["obsratio"] = float(value)
            elif key == 4:
                entry["ncombined"] = int(value)
            elif key == 5:
                entry["description"] = value.strip("|").strip()
        except ValueError:
            continue

    if not ranked:
        return None

    def _to_channel(e: dict[str, Any]) -> ChannelResult:
        return ChannelResult(
            id=e.get("id", 0),
            expref=e.get("description", ""),
            obsratio=e.get("obsratio", 0.0),
            hb_result=e.get("hb_result", 0),
            reference=e.get("description", ""),
        )

    channels = [
        _to_channel(ranked[r]) for r in sorted(ranked) if r >= 1 and "id" in ranked[r]
    ]
    global_entry = ranked.get(0)
    if global_entry and "obsratio" in global_entry:
        most_sensitive = _to_channel(global_entry)
        obsratio = global_entry["obsratio"]
    elif channels:
        # No rank-0 row: fall back to the top-sensitivity channel (rank 1).
        most_sensitive = channels[0]
        obsratio = channels[0].obsratio
    else:
        return None

    return HBResult(
        channels=channels,
        obsratio_max=obsratio,
        most_sensitive_channel=most_sensitive,
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


def _parse_hs_slha_results(slha_text: str) -> HSResult | None:
    """Parse the ``Block HiggsSignalsResults`` HS-2 writes back into the SLHA.

    HiggsSignals-2 in SLHA mode does NOT print its chi^2 to stdout — it appends
    a ``HiggsSignalsResults`` block to the input file (exactly parallel to how
    HiggsBounds-5 writes ``HiggsBoundsResults``). Rows are ``<key> <value>``;
    the keys we consume (HS-2.6.2 layout, verified against a live run on the
    canonical singlet_doublet SPheno.spc)::

        4  Number of signal strength peak observables
        5  Number of STXS signal rate observables
        6  Number of LHC Run-1 signal rate observables
        7  Number of Higgs mass observables
        8  Number of observables (total)
       15  chi^2 (signal strength) (total)      -> chi2_rates
       16  chi^2 (Higgs mass) (total)           -> chi2_masses
       17  chi^2 (total)                        -> chi2_total

    ndf_rates is the count of signal-strength observables (keys 4+5+6),
    ndf_masses the count of Higgs-mass observables (key 7). Rows 0/1 carry
    ``||text||`` version/dataset strings and are skipped.

    Returns None when the block is absent (e.g. HS never ran, or exited 0 on
    bad args writing nothing), so callers can raise the loud no-result blocker.
    If the file happens to contain more than one such block (HS appends on each
    invocation), the LAST one wins — it is the most recent run's verdict.
    """
    fields: dict[int, float] = {}
    in_block = False
    found = False
    for line in slha_text.splitlines():
        stripped = line.strip()
        if re.match(r"^Block\s+HiggsSignalsResults\b", stripped, re.IGNORECASE):
            in_block = True
            found = True
            fields = {}  # last block wins
            continue
        if re.match(r"^(Block|DECAY)\b", stripped, re.IGNORECASE):
            in_block = False
            continue
        if not in_block or not stripped or stripped.startswith("#"):
            continue
        # Numeric rows only: "<key>  <value>  # comment". Skip ||text|| rows.
        m = re.match(r"^(\d+)\s+([0-9.eE+\-]+)\s*(?:#.*)?$", stripped)
        if not m:
            continue
        try:
            fields[int(m.group(1))] = float(m.group(2))
        except ValueError:
            continue

    if not found or 17 not in fields:
        return None

    chi2_total = fields.get(17, 0.0)
    chi2_rates = fields.get(15, 0.0)
    chi2_masses = fields.get(16, 0.0)
    ndf_rates = int(fields.get(4, 0) + fields.get(5, 0) + fields.get(6, 0))
    ndf_masses = int(fields.get(7, 0))

    from p_value import compute_p_value

    return HSResult(
        chi2_total=chi2_total,
        chi2_rates=chi2_rates,
        chi2_masses=chi2_masses,
        ndf_rates=ndf_rates,
        ndf_masses=ndf_masses,
        p_value_rates=compute_p_value(chi2_rates, ndf_rates) if ndf_rates else float("nan"),
        p_value_masses=compute_p_value(chi2_masses, ndf_masses) if ndf_masses else float("nan"),
    )


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
    # whichinput must be "SLHA"; prefix is the path to the .slha file (including
    # extension). HB writes results back into the SLHA file.
    #
    # CRITICAL: pass the BASENAME as the prefix and run with cwd=slha_dir.
    # HB-5's Fortran command-line buffer truncates the prefix at ~100 chars;
    # with an absolute path over that limit HB prints "problem opening the
    # SLHA file", runs on garbage input, EXITS 0, and writes no
    # HiggsBoundsResults block — the vacuous obsratio_max=0.0 silent pass.
    # Real state-root run paths (~/.local/share/hephaestus/models/<m>/runs/
    # <ts>/SPheno.spc, 102 chars) exceed the limit, so absolute-path
    # invocation is broken in production, not just in pathological cases.
    #
    # Note: with cwd=slha_dir, HB also sees SPheno's own datafiles
    # (effC.dat, BR_*.dat, MH_GammaTot.dat) in the run dir; with
    # whichinput=SLHA these are inert (HB reads only the SLHA blocks).
    slha_abs = os.path.abspath(slha_file)
    slha_dir = os.path.dirname(slha_abs)
    slha_base = os.path.basename(slha_abs)
    cmd = [hb_bin, "LandH", "SLHA", str(n_neutral), str(n_charged), slha_base]

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

    # HB-5 in SLHA mode writes its results INTO the SLHA file (Block
    # HiggsBoundsResults); stdout carries only BR diagnostics and no
    # obsratios. Parsing stdout here used to yield a vacuous
    # obsratio_max = 0.0 / most_sensitive_channel = None while the
    # allow/exclude verdict looked fine. Read the block back from the file;
    # fall back to the legacy stdout table parse only if HB somehow wrote no
    # block (older HB builds / non-SLHA whichinput).
    try:
        slha_after = open(slha_abs).read()
    except OSError:
        slha_after = ""
    slha_result = _parse_hb_slha_results(slha_after)
    if slha_result is not None:
        return slha_result

    channel_results = _parse_hb_output(proc.stdout)

    if not channel_results:
        # ZERO results from both the SLHA block and stdout. Do NOT return an
        # empty HBResult: compute_hb_allowed([]) is vacuously True, i.e. a
        # silent "allowed" verdict from a run that produced nothing — the
        # exact silent-failure class this toolkit exists to kill. Raise a
        # blocker instead (HB is known to exit 0 even when it could not open
        # its input, e.g. the >100-char prefix truncation).
        raise HiggsBoundsNoResultError(
            "HiggsBounds produced no parsable results: no HiggsBoundsResults "
            "block was written into the SLHA file and stdout contained no "
            "per-channel table. HB is known to exit 0 even on unusable input "
            "(e.g. a truncated file prefix), so an empty result must not be "
            "reported as 'allowed'.",
            context={
                "slha_file": slha_file,
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
                "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
            },
        )

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
    n_neutral: int,
    n_charged: int,
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
    n_neutral : int
        Number of neutral Higgs bosons (nHzero).
    n_charged : int
        Number of charged Higgs pairs (nHplus).
    dMh : dict or None
        Theoretical mass uncertainties per Higgs state. Accepted for API
        parity with the unified backend; HS-2's command line takes the mass
        pdf choice (arg 2) rather than per-state dMh, so this is not currently
        mapped onto the invocation.

    Returns
    -------
    HSResult
        Parsed chi2/ndf results read back from the SLHA
        ``Block HiggsSignalsResults`` HS-2 appends to the input file.

    Raises
    ------
    HiggsSignalsNoResultError
        When HS exits 0 but writes no results block (wrong argument count,
        unopenable input, etc.) — the silent-no-op class this guard kills.
    """
    hs_bin = _find_binary(hs_build, "HiggsSignals")

    # HS-2.6.2 SLHA invocation (6 positional args):
    #   HiggsSignals <expdata> <pdf> <whichinput> <nHzero> <nHplus> <prefix>
    # The as-shipped driver passed 5 args ("latestresults peak SLHA SLHA
    # <prefix>"), so HS printed "Incorrect number of parameters given on
    # command line" and did a Fortran STOP that EXITS 0 — the returncode!=0
    # guard never fired, and the function fell through to a hardcoded
    # chi2_total=0.0 default, making hs_consistent vacuously True for EVERY
    # model. expdata=latestresults, pdf=2 (gaussian mass uncertainty); results
    # land in Block HiggsSignalsResults inside the SLHA file, NOT on stdout.
    #
    # Basename + cwd, same as run_higgsbounds: the HB/HS Fortran command-line
    # buffer truncates file prefixes at ~100 chars (real state-root run paths
    # exceed that), silently running on unopenable input.
    slha_abs = os.path.abspath(slha_file)
    slha_dir = os.path.dirname(slha_abs)
    slha_base = os.path.basename(slha_abs)
    cmd = [hs_bin, "latestresults", "2", "SLHA",
           str(n_neutral), str(n_charged), slha_base]

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

    # HS-2 writes its chi^2 into Block HiggsSignalsResults INSIDE the SLHA
    # file; stdout carries only BR diagnostics. Read the block back. If it is
    # absent, HS did no work despite exiting 0 (the classic wrong-arg-count
    # STOP, or unopenable input) — raise a loud blocker instead of fabricating
    # a chi2=0 "consistent". Detect the specific bad-arg banner for a clearer
    # message when present.
    try:
        slha_after = open(slha_abs).read()
    except OSError:
        slha_after = ""
    hs_result = _parse_hs_slha_results(slha_after)
    if hs_result is not None:
        return hs_result

    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    bad_args = "incorrect number of parameters" in combined.lower()
    detail = (
        " HiggsSignals reported 'Incorrect number of parameters given on "
        "command line' — the invocation argument count is wrong."
        if bad_args else ""
    )
    raise HiggsSignalsNoResultError(
        "HiggsSignals produced no results: no HiggsSignalsResults block was "
        "written into the SLHA file." + detail + " HS-2 exits 0 even when it "
        "does no work (bad argument count, unopenable input), so an empty "
        "result must not be reported as a vacuous 'consistent'.",
        context={
            "slha_file": slha_file,
            "cmd": cmd,
            "returncode": proc.returncode,
            "bad_arg_count": bad_args,
            "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-500:] if proc.stderr else "",
        },
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
