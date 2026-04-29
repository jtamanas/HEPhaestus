# FeynRules — Install Reference

Reference doc for installing **FeynRules 2.3.49** (the Mathematica
package for deriving Feynman rules from a Lagrangian and exporting
UFO/FeynArts/CalcHEP/Sherpa models). Driven by `detect.sh` and
`install.sh` in this directory; consumed by `/install` and
`/install bsm-model-building`.

## Status: no runner today

There is no `feynrules` runner skill in `plugins/hep-ph-toolkit/skills/`
today. `/lagrangian-builder` is SARAH-first; FeynRules is downstream
only. This install reference is reachable solely via `/install` (or
`/install bsm-model-building`) — there is no per-skill preflight
hop. If a future FeynRules runner skill is added, wire it to
`bash plugins/hep-ph-toolkit/_shared/installs/feynrules/detect.sh`
following the pattern established by `/spheno-build` and
`/looptools`.

## Version pin

`detect.sh` pins FeynRules to **2.3.49**. Override with
`HEPPH_FEYNRULES_VERSION=x.y.z`. When this pin bumps, `install.sh`
must remove or migrate the previous install tree
(e.g. `~/feynrules-current` → `~/feynrules-<new>`); the new version
is only written to `config.json` after the new install verifies, so
a half-finished upgrade does not leave the config pointing at a
stale tree.

## Disk footprint

- **Tarball:** ~20 MB estimated (`feynrules-current.tar.gz` from feynrules.irmp.ucl.ac.be)
- **Installed tree:** ~100 MB estimated at `~/feynrules-current/`
- **Build-time peak (transient):** ~1 GB (extraction + Wolfram kernel launch for version probe)
- **Estimated.** No `disk_min_gb` in `skill_env.yaml`; estimate from SKILL.md note "~50-200 MB" and upstream README.

Typical invocation order:

1. `install.sh detect` — check current state (no side-effects).
2. `install.sh use-path <dir>` — register an existing FeynRules directory.
3. `install.sh install` — full auto-install (requires Wolfram Engine).

### Downstream-only note

Within `hephaestus`, `/lagrangian-builder` is **SARAH-first**: FeynRules is
not in the primary enumeration/anomaly-check path. This install skill exists
for users who want to run FeynRules directly (e.g. authoring a bespoke `.fr`
file and exporting UFO). Do not treat FeynRules as the Lagrangian-builder
backend.

---

## Decision flow

```
install.sh detect
       │
       ├── config has feynrules_path + valid FeynRules.m/FeynRulesPackage.m +
       │   version probe succeeds
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds the package
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

install.sh use-path <dir>
       │
       ├── <dir>/FeynRules.m + <dir>/FeynRulesPackage.m exist AND
       │   wolframscript configured
       │       ├── version probe succeeds → writes feynrules_path,
       │       │   feynrules_version, feynrules_installed_at;
       │       │   {"status":"configured",...}                            exit 0
       │       └── version probe fails → FEYNRULES_SMOKE_TEST_FAILED     exit 15
       │
       ├── <dir>/FeynRules.m or FeynRulesPackage.m missing →
       │   FEYNRULES_PATH_INVALID blocker                                 exit 16
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20

install.sh install [dir]
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20
       ├── disk check (need >=1 GB free in $HOME; FeynRules itself is ~50-200 MB)
       ├── download FeynRules tarball (HEPPH_FEYNRULES_VERSION or pinned 2.3.49)
       ├── verify_checksum (warns if SHA256 == "TODO"; does not abort)
       ├── extract to <dir>/feynrules-current/ (default: ~/feynrules-current)
       ├── register Wolfram $Path via init.m (idempotent BEGIN/END markers)
       ├── version probe
       │   ├── succeeds → writes feynrules_path, feynrules_version,
       │   │   feynrules_installed_at
       │   │   └── check_wolfram_activation.sh
       │   │       ├── status ok   → log "FeynRules installed and ready." exit 0
       │   │       └── status activation_required
       │   │               └── print {"status":"activation_required",
       │   │                          "user_instruction":"..."}
       │   │                   exit 0   (NOT a blocker; user must activate Wolfram)
       │   └── fails → FEYNRULES_SMOKE_TEST_FAILED blocker                exit 15
       └── download failed → FEYNRULES_DOWNLOAD_FAILED blocker            exit 12
```

---

## JSON status contract

`detect` and `use-path` emit JSON on **stdout**. `install` emits JSON on stdout
for the activation-required path only; all other outcomes are logged to stderr.

| `status` value | Meaning |
|---|---|
| `configured` | `feynrules_path` set, `FeynRules.m` + `FeynRulesPackage.m` present, version probe succeeded |
| `found` | FeynRules found on disk via scan but not in config |
| `missing` | No FeynRules found anywhere |
| `activation_required` | FeynRules installed but Wolfram Engine needs activation |

Fields for `configured`:
```json
{"status":"configured","path":"/home/you/feynrules-current","version":"2.3.49"}
```

Fields for `activation_required`:
```json
{
  "status": "activation_required",
  "message": "Wolfram Engine is installed but needs activation.",
  "user_instruction": "Run `wolframscript --activate` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun install.sh."
}
```

---

## Activation handling (critical)

**`activation_required` is a status code, NOT a blocker.**

This mirrors `_shared/installs/sarah` and diverges from the spec listing
`WOLFRAM_NEEDS_ACTIVATION` as a fatal blocker. The divergence is deliberate:
Wolfram activation is a one-time user action that requires a browser; emitting
a fatal blocker would halt the entire pipeline permanently, whereas returning
a structured status allows the orchestrator to show the user the
`user_instruction` and wait. The `install` subcommand exits 0 with
`{"status":"activation_required"}` so the caller can handle it gracefully.

Wolfram Engine detection is decoupled via `detect_wolfram.sh` (sibling copy).
The activation probe uses `check_wolfram_activation.sh`, which pipes
`wolframscript -code '1+1'` output through `_activation_parse.py`.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | `user_instruction` |
|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | `wolfram_engine_path` not set or binary missing | Run `/install` → install Wolfram Engine |
| `FEYNRULES_DOWNLOAD_FAILED` | `fatal` | `curl` failed twice | Check network; retry |
| `FEYNRULES_SMOKE_TEST_FAILED` | `fatal` | Version probe returned empty after install | Check Wolfram Engine activation |
| `FEYNRULES_PATH_INVALID` | `fatal` | `use-path <dir>` has no `FeynRules.m` or `FeynRulesPackage.m` | Provide path to FeynRules package dir |

`WOLFRAM_NEEDS_ACTIVATION` is **not** emitted as a blocker by this skill. The
activation state is surfaced only via the `activation_required` status JSON.

Exit codes (shared with sarah-install for caller consistency):
- `12` download failure
- `15` smoke test failure
- `16` bad path
- `20` prerequisite absent (Wolfram)

---

## Config keys written

| Key | Value |
|---|---|
| `feynrules_path` | Absolute path to FeynRules package dir (contains `FeynRules.m` + `FeynRulesPackage.m`) |
| `feynrules_version` | Version string extracted by `probe_version` (e.g. `2.3.49`) |
| `feynrules_installed_at` | UTC ISO 8601 timestamp |

Keys **read** (must be set by `/install` or `bash _shared/installs/sarah/install.sh use-path` for Wolfram):
`wolfram_engine_path` — path to the `wolframscript` binary.

---

## Version pin and override

Pinned version: **2.3.49** (set in `skill_env.yaml`; hardcoded
`FR$VersionNumber = "2.3.49"` in `FeynRulesPackage.m`; release date
29 September 2021).

Override via environment:
```bash
HEPPH_FEYNRULES_VERSION=2.3.43 install.sh install
```

Default upstream tarball (single rolling "current" build):
`http://feynrules.irmp.ucl.ac.be/downloads/feynrules-current.tar.gz`.
GitHub mirror: `https://github.com/FeynRules/FeynRules` (tag `fr-2.3.49`).

### Mathematica compatibility

FeynRules enforces `$VersionNumber >= 6` (hard floor). Practical floor is
Mathematica / Wolfram Engine 12.1+. For 12.2+ a compatibility shim exists:
`SetOptions[ValueQ, Method -> "Legacy"]`. If the smoke test fails with a
`ValueQ` deprecation warning, prepend this line to the probe.

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-model-building.md`
- Sibling: `plugins/hep-ph-toolkit/_shared/installs/sarah/` (structural parent)
- Downstream consumer: hand-written `.fr` files → UFO export; NOT used by
  `/lagrangian-builder` (SARAH-first).
