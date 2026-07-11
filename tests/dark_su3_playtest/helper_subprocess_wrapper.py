"""Component A — Helper subprocess capture wrapper for WS-3 Dark SU(3) playtest.

Two modes:
  stub  — monkey-patches subprocess.run for the four helper paths; returns
          canned responses keyed on (helper_name, scenario_id) derived from argv.
  real  — lets the real subprocess run; captures stdout/stderr/returncode.

Mode is set via WS3_HELPER_MODE env var (default: stub).
"""

from __future__ import annotations

import dataclasses
import os
import pathlib
import subprocess
import sys
import typing
import unittest.mock

# Python 3.10 bug: dataclasses with frozen=True call sys.modules.get(cls.__module__)
# during class creation. When a module is loaded via importlib.util.spec_from_file_location
# without prior sys.modules registration, __module__ is set but sys.modules doesn't contain
# the entry, causing AttributeError. Pre-register this module to fix it.
if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get(__name__, type(sys)(__name__))

# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------

KNOWN_HELPERS = frozenset(
    {"check_prereqs", "detect_drake", "extract_field", "verify_router_field_contract"}
)

HELPER_SCRIPT_SUFFIX = (
    "plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/"
)


@dataclasses.dataclass(frozen=True)
class HelperInvocation:
    """Frozen record of a single helper subprocess invocation.

    Declared with frozen=True for immutability (plan-final §T2 binding).
    slots=True is deliberately omitted: the Python 3.10 importlib
    spec_from_file_location path triggers a sys.modules lookup bug when
    frozen dataclasses with slots are created before the module is registered
    in sys.modules. frozen=True is the load-bearing invariant; slots are not.
    """

    helper_name: str       # one of KNOWN_HELPERS
    argv: list[str]        # full argv as captured (helper_path + args)
    returncode: int
    stdout: str
    stderr: str


# ---------------------------------------------------------------------------
# Stub response dispatcher
# ---------------------------------------------------------------------------

def _scenario_id_from_argv(argv: list[str]) -> str:
    """Derive a scenario_id string from argv flags for canned-file dispatch.

    Heuristics (in priority order):
      1. --scenario-id <id>  — explicit override for testing
      2. --config <path> containing 'pointA_configured' etc.
      3. --json <path> containing 'pointA' or 'pointB'
      4. fallback: 'default'
    """
    for i, arg in enumerate(argv):
        if arg == "--scenario-id" and i + 1 < len(argv):
            return argv[i + 1]
    for arg in argv:
        for keyword in (
            "pointA_configured",
            "pointA_missing",
            "pointA_activation_required",
            "pointA_unset",
            "pointA",
            "pointB",
        ):
            if keyword in arg:
                return keyword
    return "default"


def stub_response_for(
    helper: str, argv: list[str], canned_dir: pathlib.Path
) -> tuple[int, str, str]:
    """Pure function: maps (helper, argv) -> (returncode, stdout, stderr) using canned_dir.

    Canned file lookup strategy per helper:
      check_prereqs    -> canned/<point>/check_prereqs_ok.json
      detect_drake     -> canned/<point>/detect_drake_<scenario>.json
      extract_field    -> returns synthetic JSON keyed on --key arg
      verify_router    -> returns {"status": "ok"} JSON
    """
    import json

    scenario_id = _scenario_id_from_argv(argv)
    point = "pointA" if "pointA" in scenario_id or scenario_id == "default" else "pointB"

    if helper == "check_prereqs":
        canned_file = canned_dir / point / "check_prereqs_ok.json"
        if canned_file.exists():
            return 0, canned_file.read_text(), ""
        return 0, json.dumps({"status": "ok", "blockers": []}), ""

    if helper == "detect_drake":
        # Derive detect suffix from scenario
        for suffix in ("configured", "missing", "activation_required"):
            if suffix in scenario_id:
                canned_file = canned_dir / point / f"detect_drake_{suffix}.json"
                if canned_file.exists():
                    return 0, canned_file.read_text(), ""
        # Branch 1: drake_path absent - not called (but if called return missing)
        return 0, json.dumps({"status": "missing"}), ""

    if helper == "extract_field":
        # Derive key from argv
        key = "omega_h2"
        schema = "relic/v1"
        for i, arg in enumerate(argv):
            if arg == "--key" and i + 1 < len(argv):
                key = argv[i + 1]
            if arg == "--schema-version" and i + 1 < len(argv):
                schema = argv[i + 1]
        # Serve from canned files if available, else synthesize
        if key == "omega_h2" and schema == "relic/v1":
            canned_file = canned_dir / point / "relic.json"
            if canned_file.exists():
                data = json.loads(canned_file.read_text())
                return 0, json.dumps({"value": data.get("omega_h2", 0.118)}), ""
            return 0, json.dumps({"value": 0.118}), ""
        if key == "sigma_v_zero" and schema == "annihilation/v1":
            canned_file = canned_dir / point / "annihilation.json"
            if canned_file.exists():
                data = json.loads(canned_file.read_text())
                return 0, json.dumps({"value": data.get("sigma_v_zero", 2.31e-26)}), ""
            return 0, json.dumps({"value": 2.31e-26}), ""
        # Generic fallback
        return 0, json.dumps({"value": None}), ""

    if helper == "verify_router_field_contract":
        return 0, json.dumps({"status": "ok"}), ""

    # Unknown helper - return error
    return 1, "", f"unknown helper: {helper}"


# ---------------------------------------------------------------------------
# HelperSubprocessWrapper
# ---------------------------------------------------------------------------

class HelperSubprocessWrapper:
    """Intercepts subprocess.run calls for the four WS-4 helper scripts.

    Usage::

        wrapper = HelperSubprocessWrapper(mode="stub", canned_dir=Path("..."))
        wrapper.install()
        try:
            # run test that invokes helpers
            pass
        finally:
            wrapper.restore()
        invocations = wrapper.invocations
    """

    def __init__(
        self,
        mode: typing.Literal["stub", "real"],
        canned_dir: pathlib.Path,
    ) -> None:
        self._mode = mode
        self._canned_dir = canned_dir
        self._invocations: list[HelperInvocation] = []
        self._original_run: typing.Any = None
        self._patcher: typing.Any = None

    def install(self) -> None:
        """Monkey-patch subprocess.run for the four helper paths.

        Each install() starts a fresh capture: the retry loop reuses one
        wrapper across attempts (install/restore per attempt), and evidence
        captured on attempt N-1 must not let attempt N pass a matcher.
        """
        if self._patcher is not None:
            return  # already installed

        self._invocations = []
        wrapper = self

        def _patched_run(args, **kwargs):  # noqa: ANN001
            argv = list(args) if not isinstance(args, str) else args.split()
            helper_name = _resolve_helper_name(argv)

            if helper_name is None or wrapper._mode == "real":
                # real mode or non-helper call: passthrough
                result = subprocess.__orig_run__(args, **kwargs)  # type: ignore[attr-defined]
                if helper_name is not None:
                    wrapper._invocations.append(
                        HelperInvocation(
                            helper_name=helper_name,
                            argv=argv,
                            returncode=result.returncode,
                            stdout=result.stdout or "",
                            stderr=result.stderr or "",
                        )
                    )
                return result

            # stub mode
            rc, out, err = stub_response_for(helper_name, argv, wrapper._canned_dir)
            wrapper._invocations.append(
                HelperInvocation(
                    helper_name=helper_name,
                    argv=argv,
                    returncode=rc,
                    stdout=out,
                    stderr=err,
                )
            )
            mock_result = unittest.mock.MagicMock()
            mock_result.returncode = rc
            mock_result.stdout = out
            mock_result.stderr = err
            return mock_result

        # Store original and install patch
        subprocess.__orig_run__ = subprocess.run  # type: ignore[attr-defined]
        self._patcher = unittest.mock.patch("subprocess.run", side_effect=_patched_run)
        self._patcher.start()

    def restore(self) -> None:
        """Restore original subprocess.run."""
        if self._patcher is not None:
            self._patcher.stop()
            self._patcher = None
        if hasattr(subprocess, "__orig_run__"):
            del subprocess.__orig_run__  # type: ignore[attr-defined]

    @property
    def invocations(self) -> list[HelperInvocation]:
        """Return ordered list of captured helper invocations (read-only copy)."""
        return list(self._invocations)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_helper_name(argv: list[str]) -> str | None:
    """Return the helper name if argv[0..1] matches a known helper script path."""
    for arg in argv[:3]:  # check first 3 args (python, -m, or script path)
        for helper in KNOWN_HELPERS:
            if arg.endswith(f"{helper}.py") or arg.endswith(f"scripts/{helper}"):
                return helper
    return None
