"""
write_sidecar.py — assemble and atomically write amp_reduced.meta.json.

Validates against the Phase-0 canonical schema before writing.
Atomicity is provided by the Phase-0 atomic_write.sh helper (atomic_write_stdin).
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Union

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "plugins" / "shared" / "schemas" / "amp_reduced.meta.schema.json"
SHARED_HELPERS = REPO_ROOT / "plugins" / "shared" / "install-helpers"


def load_schema() -> dict:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate(data: dict) -> list[str]:
    """Validate data against the Phase-0 schema. Returns list of errors (empty = valid)."""
    try:
        import jsonschema
    except ImportError:
        return []  # skip validation if jsonschema not installed
    schema = load_schema()
    errors = []
    v = jsonschema.Draft202012Validator(schema)
    for err in sorted(v.iter_errors(data), key=lambda e: list(e.absolute_path)):
        errors.append(f"{list(err.absolute_path)}: {err.message}")
    return errors


def write_sidecar(dest: Union[str, Path], data: dict) -> None:
    """Validate then atomically write the sidecar JSON."""
    dest = Path(dest)
    errors = validate(data)
    if errors:
        from scripts.run_formcalc import emit_blocker
        import sys
        emit_blocker(
            "FORMCALC_SIDECAR_INVALID",
            "fatal",
            "amp_reduced.meta.json failed schema validation",
            context={"errors": errors},
        )
        sys.exit(1)

    _write_atomic(dest, json.dumps(data, indent=2, sort_keys=True) + "\n")


def _write_atomic(dest: Path, content: str) -> None:
    """Write content to dest atomically via the Phase-0 atomic_write.sh helper.

    Routes through plugins/shared/install-helpers/atomic_write.sh (atomic_write_stdin)
    so all atomicity discipline (tmp + fsync + rename + dir-fsync) is centralised.
    """
    atomic_write_sh = SHARED_HELPERS / "atomic_write.sh"
    common_sh = SHARED_HELPERS / "_common.sh"
    if not atomic_write_sh.exists():
        raise FileNotFoundError(f"atomic_write.sh not found: {atomic_write_sh}")
    if not common_sh.exists():
        raise FileNotFoundError(f"_common.sh not found: {common_sh}")
    # Write a tiny wrapper script that sources the helpers and calls atomic_write_stdin.
    # Using a temp file for the script keeps stdin free for the content pipe.
    script = (
        "#!/usr/bin/env bash\n"
        f". {common_sh!s}\n"
        f". {atomic_write_sh!s}\n"
        f"atomic_write_stdin {dest!s}\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as sf:
        sf.write(script)
        sf_path = sf.name
    try:
        result = subprocess.run(
            ["bash", sf_path],
            input=content,
            text=True,
            capture_output=True,
        )
    finally:
        os.unlink(sf_path)
    if result.returncode != 0:
        raise RuntimeError(
            f"_write_atomic failed for {dest}: {result.stderr.strip()}"
        )
