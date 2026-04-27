"""exceptions_registry.py — loader for _shared/analytic_exceptions.yaml.

Public API:
    load_exceptions(registry_path: Path | None = None) -> RegistryView

RegistryView exposes:
    .all_active()           -> Iterable[ExceptionEntry]  (status == 'active')
    .by_id(id)              -> ExceptionEntry | None
    .by_model(model)        -> list[ExceptionEntry]
    .by_kind(kind)          -> list[ExceptionEntry]      (kind: 'analytic'|'proxy_run')

ExceptionEntry exposes:
    .id, .kind, .model, .status, .banner, .placements
    .signals_recorded
    .analytic_module  (analytic kind only; None for proxy_run)
    .proxy_model      (proxy_run kind only; None for analytic)
    .deprecated_in, .retired_in

Raises:
    ExceptionRegistryMalformed  — on schema or banner well-formedness failure.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Iterable, Literal, Optional

import yaml

# ---------------------------------------------------------------------------
# Default registry path (repo-relative, resolved from this file's location)
# ---------------------------------------------------------------------------

_HERE = pathlib.Path(__file__).parent
# scripts/ -> analytic-exception-detector/ -> skills/ -> hep-ph-toolkit/ -> plugins/ -> repo root
_REPO_ROOT = _HERE.parent.parent.parent.parent.parent
_DEFAULT_REGISTRY = _REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills" / "_shared" / "analytic_exceptions.yaml"

# ---------------------------------------------------------------------------
# Well-formedness regexes (synthesis §4.2)
# ---------------------------------------------------------------------------

_WF_ANALYTIC_FIRST = re.compile(
    r"\*\*REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET \([^)]+\)\.\*\*"
)
_WF_ANALYTIC_CLOSE = re.compile(
    r"MUST embed this banner verbatim — do not silently strip it\."
)
_WF_PROXY_FIRST = re.compile(
    r"\*\*PROXY-RUN DISCLOSURE\.\*\*"
)
_WF_PROXY_CLOSE = re.compile(
    r"tag every affected table row with `\[proxy\]`\."
)

_REQUIRED_SCHEMA_VERSION = 1


class ExceptionRegistryMalformed(Exception):
    """Raised when the registry file fails schema or banner well-formedness checks."""
    def __init__(self, entry_id: str, reason: str):
        self.entry_id = entry_id
        self.reason = reason
        super().__init__(f"analytic_exceptions.yaml entry '{entry_id}': {reason}")


# ---------------------------------------------------------------------------
# Entry dataclass
# ---------------------------------------------------------------------------

@dataclass
class ExceptionEntry:
    id: str
    kind: Literal["analytic", "proxy_run"]
    model: str
    status: Literal["active", "deprecated", "retired"]
    banner: str
    placements: dict[str, str]
    signals_recorded: list[str] = field(default_factory=list)
    analytic_module: Optional[str] = None   # analytic kind only
    proxy_model: Optional[str] = None       # proxy_run kind only
    deprecated_in: Optional[str] = None
    retired_in: Optional[str] = None


# ---------------------------------------------------------------------------
# RegistryView
# ---------------------------------------------------------------------------

class RegistryView:
    def __init__(self, entries: list[ExceptionEntry]):
        self._entries = entries

    def all_active(self) -> Iterable[ExceptionEntry]:
        return (e for e in self._entries if e.status == "active")

    def by_id(self, exception_id: str) -> Optional[ExceptionEntry]:
        for e in self._entries:
            if e.id == exception_id:
                return e
        return None

    def by_model(self, model_name: str) -> list[ExceptionEntry]:
        return [e for e in self._entries if e.model == model_name]

    def by_kind(self, kind: str) -> list[ExceptionEntry]:
        return [e for e in self._entries if e.kind == kind]


# ---------------------------------------------------------------------------
# Well-formedness check helpers
# ---------------------------------------------------------------------------

def _check_well_formedness(entry_id: str, kind: str, banner: str) -> None:
    """Raise ExceptionRegistryMalformed if banner does not meet synthesis §4.2 invariants."""
    if kind == "analytic":
        if not _WF_ANALYTIC_FIRST.search(banner):
            raise ExceptionRegistryMalformed(
                entry_id,
                "banner missing load-bearing first phrase: "
                "'**REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (<id>).**'"
            )
        if not _WF_ANALYTIC_CLOSE.search(banner):
            raise ExceptionRegistryMalformed(
                entry_id,
                "banner missing closing requirement: "
                "'MUST embed this banner verbatim — do not silently strip it.'"
            )
    elif kind == "proxy_run":
        if not _WF_PROXY_FIRST.search(banner):
            raise ExceptionRegistryMalformed(
                entry_id,
                "banner missing load-bearing first phrase: '**PROXY-RUN DISCLOSURE.**'"
            )
        if not _WF_PROXY_CLOSE.search(banner):
            raise ExceptionRegistryMalformed(
                entry_id,
                "banner missing closing requirement: "
                "'tag every affected table row with `[proxy]`.'"
            )
    else:
        raise ExceptionRegistryMalformed(entry_id, f"unknown kind: '{kind}'")


def _parse_entry(raw: dict, kind_key: str) -> ExceptionEntry:
    """Parse a raw dict from YAML into an ExceptionEntry, validating required fields."""
    entry_id = raw.get("id", "<unknown>")

    required = ["id", "kind", "model", "status", "banner", "placements"]
    for f in required:
        if f not in raw:
            raise ExceptionRegistryMalformed(entry_id, f"missing required field '{f}'")

    kind = raw["kind"]
    banner = raw["banner"]

    # Strip trailing whitespace from each banner line for normalization
    banner_normalized = "\n".join(line.rstrip() for line in banner.splitlines()) + "\n"

    _check_well_formedness(entry_id, kind, banner_normalized)

    return ExceptionEntry(
        id=raw["id"],
        kind=raw["kind"],
        model=raw["model"],
        status=raw["status"],
        banner=banner_normalized,
        placements=raw.get("placements", {}),
        signals_recorded=raw.get("signals_recorded", []),
        analytic_module=raw.get("analytic_module"),
        proxy_model=raw.get("proxy_model"),
        deprecated_in=raw.get("deprecated_in"),
        retired_in=raw.get("retired_in"),
    )


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------

def load_exceptions(registry_path: Optional[pathlib.Path] = None) -> RegistryView:
    """Load and validate analytic_exceptions.yaml; return a RegistryView.

    Args:
        registry_path: Optional override. Defaults to _shared/analytic_exceptions.yaml.

    Raises:
        ExceptionRegistryMalformed: on schema or well-formedness failure.
        FileNotFoundError: if the registry file does not exist.
    """
    path = registry_path if registry_path is not None else _DEFAULT_REGISTRY
    with open(path) as fh:
        data = yaml.safe_load(fh)

    # schema_version check
    sv = data.get("schema_version")
    if sv != _REQUIRED_SCHEMA_VERSION:
        raise ExceptionRegistryMalformed(
            "<registry>",
            f"schema_version must be {_REQUIRED_SCHEMA_VERSION}, got {sv!r}"
        )

    entries: list[ExceptionEntry] = []

    for raw in data.get("exceptions", []):
        entries.append(_parse_entry(raw, "analytic"))

    for raw in data.get("proxy_runs", []):
        entries.append(_parse_entry(raw, "proxy_run"))

    return RegistryView(entries)
