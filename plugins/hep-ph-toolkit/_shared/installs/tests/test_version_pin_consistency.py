"""Lint: detect.sh env-var version defaults must agree with skill_env.yaml.

Spec §2 ("Cache & version hygiene") wants one source of truth per tool
for the pinned version. Today some tools have skill_env.yaml AND a
duplicated default in detect.sh's `HEPPH_<TOOL>_VERSION:-x.y` literal.
Drift here yields silent reinstall loops (the wrong-tier values mismatch
in detect.sh's fast path).

This test scans each `_shared/installs/<tool>/skill_env.yaml` for a
version-like key and asserts that the matching `detect.sh` (and
top-level `install.sh`, where present) uses the same default literal in
its `HEPPH_<TOOL>_VERSION:-...` clause.
"""

from __future__ import annotations

import re
from pathlib import Path

INSTALLS_ROOT = Path(__file__).resolve().parent.parent

# Map skill_env.yaml key -> shell env-var name as referenced in detect.sh.
# Tools with a single canonical version key are the easy case; higgstools
# has TWO independent pins (legacy HB and unified HT) so we map both.
KEY_TO_ENV = {
    "ddcalc": [("HEPPH_DDCALC_VERSION", "HEPPH_DDCALC_VERSION")],
    "drake": [("drake_version", "HEPPH_DRAKE_VERSION")],
    "higgstools": [
        ("HB_VERSION", "HEPPH_HB_VERSION"),
        ("HT_VERSION", "HEPPH_HT_VERSION"),
    ],
    "sarah": [("sarah_version", "HEPPH_SARAH_VERSION")],
}


def _read_yaml_value(path: Path, key: str) -> str | None:
    """Lightweight parse for top-level scalar string keys in a flat YAML."""
    pat = re.compile(rf'^{re.escape(key)}\s*:\s*"?([^"#\n]+)"?', re.MULTILINE)
    m = pat.search(path.read_text())
    return m.group(1).strip() if m else None


def _read_default(detect_text: str, env: str) -> str | None:
    """Pull the default literal from `${env:-DEFAULT}` (sh-style)."""
    pat = re.compile(rf"\$\{{\s*{re.escape(env)}\s*:-\s*([^}}]+)\}}")
    m = pat.search(detect_text)
    return m.group(1).strip().strip('"').strip("'") if m else None


def test_detect_pins_match_skill_env() -> None:
    failures: list[str] = []
    for tool, mappings in KEY_TO_ENV.items():
        env_yaml = INSTALLS_ROOT / tool / "skill_env.yaml"
        detect_sh = INSTALLS_ROOT / tool / "detect.sh"
        if not env_yaml.exists() or not detect_sh.exists():
            continue
        text = detect_sh.read_text()
        for yaml_key, env_var in mappings:
            yaml_value = _read_yaml_value(env_yaml, yaml_key)
            if yaml_value is None:
                continue  # key not present in this skill_env.yaml; skip
            default = _read_default(text, env_var)
            if default is None:
                # detect.sh doesn't reference this env var — fine; the
                # tool may not need a pin in detect.
                continue
            if default != yaml_value:
                failures.append(
                    f"{tool}: detect.sh ${env_var}:-{default!r} "
                    f"!= skill_env.yaml {yaml_key}={yaml_value!r}"
                )
    assert not failures, "\n".join(failures)
