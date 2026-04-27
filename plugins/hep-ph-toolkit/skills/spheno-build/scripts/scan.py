"""
scan.py — Sequential Cartesian-product parameter scan for /spheno-build.

Usage (library):
    from scan import scan, expand_axis
    axes = [("MpsiD", 200.0, 1000.0, 100.0), ("gD", 0.5, 2.5, 0.5)]
    csv_path = scan("dark_su3", axes, scan_dir)

Usage (CLI):
    python3 scan.py <model_name> --scan MpsiD=200:1000:step=100 --scan gD=0.5:2.5:step=0.5
"""

import sys
assert sys.version_info >= (3, 10), "hephaestus requires Python >= 3.10"

import csv
import importlib.util as _ilu
import json
import os
import re
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
_SHARED_DIR = _SKILL_DIR.parent / "_shared"
_CONFIG_HELPERS = _SKILL_DIR.parent.parent.parent / "shared" / "install-helpers" / "config_helpers.py"


def _load_module(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_config_helpers():
    return _load_module("config_helpers", _CONFIG_HELPERS)


def _load_leshouches_template():
    return _load_module("leshouches_template", _SCRIPT_DIR / "leshouches_template.py")


def _load_run_point():
    return _load_module("run_point", _SCRIPT_DIR / "run_point.py")


def expand_axis(name: str, start: float, stop: float, step: float) -> list[float]:
    """Expand a scan axis to a list of values.

    Generates: start, start+step, ..., stop (inclusive if exactly reached).
    Uses integer-safe arithmetic to avoid floating-point drift.

    Args:
        name:  Parameter name (used for error messages).
        start: First value.
        stop:  Last value (inclusive if reached within half a step).
        step:  Step size (must be positive).

    Returns:
        Sorted list of float values.

    Raises:
        ValueError: if step <= 0 or start > stop.
    """
    if step <= 0:
        raise ValueError(f"scan axis {name!r}: step must be positive, got {step}")
    if start > stop:
        raise ValueError(f"scan axis {name!r}: start ({start}) > stop ({stop})")

    values: list[float] = []
    # Use integer counting to avoid FP accumulation
    n = 0
    while True:
        v = start + n * step
        if v > stop + step * 0.5:
            break
        if v <= stop + step * 1e-9:
            values.append(round(v, 12))
        n += 1
    return values


def _cartesian_product(axes: list[tuple[str, list[float]]]) -> list[dict[str, float]]:
    """Return the Cartesian product of axes as a list of parameter dicts.

    Axes are sorted by parameter name before expansion to ensure determinism.
    """
    if not axes:
        return [{}]

    sorted_axes = sorted(axes, key=lambda a: a[0])

    def _recurse(idx: int, partial: dict[str, float]) -> list[dict[str, float]]:
        if idx == len(sorted_axes):
            return [dict(partial)]
        name, values = sorted_axes[idx]
        result = []
        for v in values:
            partial[name] = v
            result.extend(_recurse(idx + 1, partial))
        return result

    return _recurse(0, {})


def scan_worker(
    point: dict[str, float],
    workdir: Path,
    model_name: str,
    spec: dict,
) -> dict:
    """Run SPheno for a single parameter point and return a result dict.

    Args:
        point:      Dict of parameter name → value for this grid point.
        workdir:    Per-point output directory (created by caller).
        model_name: Model name (snake_case).
        spec:       Loaded ModelSpec dict.

    Returns:
        Dict with keys: status, blocker_code, slha_path, timing_s.
    """
    lht_mod = _load_leshouches_template()
    rp_mod = _load_run_point()

    t0 = time.monotonic()

    # Build LesHouches card
    card_text = lht_mod.build(spec, overrides=point)

    # Append SPHENOINPUT if available
    config_helpers = _load_config_helpers()
    config = config_helpers.load_config()
    state_root = config_helpers.STATE_ROOT

    sarah_name_mod = _load_module("sarah_name", _SHARED_DIR / "sarah_name.py")
    try:
        sarah_name = sarah_name_mod.modelspec_name_to_sarah(model_name)
    except ValueError:
        sarah_name = model_name

    sphenoinput_dir = (
        state_root / "models" / model_name /
        "sarah_output" / "SPheno" / sarah_name / "Input_Files"
    )
    sphenoinput_file = sphenoinput_dir / f"LesHouches.in.{sarah_name}"
    if sphenoinput_file.exists():
        sphenoinput_block = _extract_sphenoinput_block(sphenoinput_file.read_text())
        if sphenoinput_block:
            card_text = card_text.rstrip() + "\n\n" + sphenoinput_block + "\n"

    # Write card to workdir
    lh_in = workdir / "LesHouches.in"
    lh_in.write_text(card_text)

    # Dispatch to the selected spectrum backend (spheno or analytic).
    disp_mod = _load_module("dispatcher", _SCRIPT_DIR / "dispatcher.py")
    params = {k: point[k] for k in point}
    result = disp_mod.dispatch(
        model_name=model_name,
        spec=spec,
        params=params,
        out_dir=workdir,
        config={},
    )

    timing_s = time.monotonic() - t0
    result["timing_s"] = round(timing_s, 3)
    return result


def _extract_sphenoinput_block(text: str) -> str:
    """Extract only the Block SPHENOINPUT section from a LesHouches file."""
    lines = text.splitlines()
    in_block = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        block_match = re.match(r"^Block\s+(\S+)", stripped, re.IGNORECASE)
        if block_match:
            if block_match.group(1).upper() == "SPHENOINPUT":
                in_block = True
                collected = [line]
            elif in_block:
                # End of SPHENOINPUT block
                break
        elif in_block:
            collected.append(line)
    return "\n".join(collected)


def scan(
    model: str,
    axes: list[tuple[str, float, float, float]],
    scan_dir: Path,
    spec: dict | None = None,
) -> Path:
    """Run a sequential Cartesian-product scan.

    Args:
        model:    Model name.
        axes:     List of (name, start, stop, step) tuples.
        scan_dir: Directory to write scan outputs.
        spec:     ModelSpec dict. If None, loaded from config.

    Returns:
        Path to the generated scan_index.csv.
    """
    scan_dir.mkdir(parents=True, exist_ok=True)

    # Load spec if not provided
    if spec is None:
        config_helpers = _load_config_helpers()
        state_root = config_helpers.STATE_ROOT
        spec_path = state_root / "models" / model / "spec.yaml"
        if not spec_path.exists():
            print(
                json.dumps({
                    "code": "SPHENO_NO_OUTPUT",
                    "mode": "fatal",
                    "message": f"spec.yaml not found at {spec_path}. Run /sarah-build first.",
                }),
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            import yaml
            with open(spec_path) as f:
                spec = yaml.safe_load(f)
        except ImportError:
            print("error: pyyaml required to load spec.yaml", file=sys.stderr)
            sys.exit(1)

    # Expand each axis
    expanded_axes: list[tuple[str, list[float]]] = []
    for name, start, stop, step in axes:
        values = expand_axis(name, start, stop, step)
        expanded_axes.append((name, values))

    # Compute Cartesian product
    points = _cartesian_product(expanded_axes)

    param_names = sorted(ax[0] for ax in expanded_axes)
    csv_path = scan_dir / "scan_index.csv"

    fieldnames = ["index"] + param_names + ["status", "blocker_code", "slha_path", "timing_s", "backend"]

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx, point in enumerate(points):
            point_dir = scan_dir / f"{idx:04d}"
            point_dir.mkdir(parents=True, exist_ok=True)

            try:
                result = scan_worker(point, point_dir, model, spec)
            except Exception as exc:
                result = {
                    "status": "error",
                    "blocker_code": "SPHENO_NO_OUTPUT",
                    "slha_path": None,
                    "timing_s": 0.0,
                }
                print(
                    json.dumps({
                        "code": "SPHENO_NO_OUTPUT",
                        "mode": "fatal",
                        "message": f"Unhandled exception at point {idx}: {exc}",
                    }),
                    file=sys.stderr,
                )

            row: dict = {"index": idx}
            row.update({k: point.get(k, "") for k in param_names})
            row["status"] = result.get("status", "error")
            row["blocker_code"] = result.get("blocker_code") or ""
            row["slha_path"] = result.get("slha_path") or ""
            row["timing_s"] = result.get("timing_s", 0.0)
            row["backend"] = result.get("backend") or ""
            writer.writerow(row)

    return csv_path


def parse_scan_arg(arg: str) -> tuple[str, float, float, float]:
    """Parse a --scan argument of the form NAME=start:stop:step=s.

    Returns (name, start, stop, step).
    """
    # Formats:
    #   MpsiD=200:1000:step=100
    #   gD=0.5:2.5:step=0.5
    m = re.fullmatch(
        r"([A-Za-z_][A-Za-z0-9_]*)=([^:]+):([^:]+):step=([^:]+)",
        arg.strip(),
    )
    if not m:
        raise ValueError(
            f"Cannot parse --scan argument {arg!r}. "
            "Expected format: NAME=start:stop:step=s"
        )
    name = m.group(1)
    start = float(m.group(2))
    stop = float(m.group(3))
    step = float(m.group(4))
    return name, start, stop, step


if __name__ == "__main__":
    import argparse
    import datetime

    parser = argparse.ArgumentParser(
        description="Run a Cartesian-product parameter scan with SPheno."
    )
    parser.add_argument("model_name", help="Model name (e.g. dark_su3)")
    parser.add_argument(
        "--scan", action="append", required=True, metavar="NAME=start:stop:step=s",
        dest="scan_args", help="Scan axis (repeatable)."
    )
    args = parser.parse_args()

    config_helpers_mod = _load_config_helpers()
    state_root = config_helpers_mod.STATE_ROOT
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    scan_out_dir = state_root / "models" / args.model_name / "runs" / f"scan_{ts}"

    parsed_axes = []
    for scan_arg in args.scan_args:
        parsed_axes.append(parse_scan_arg(scan_arg))

    csv_out = scan(args.model_name, parsed_axes, scan_out_dir)
    print(json.dumps({"status": "done", "scan_index_csv": str(csv_out)}))
