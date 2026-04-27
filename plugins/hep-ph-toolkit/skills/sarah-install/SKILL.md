---
name: sarah-install
description: Detect, validate, or auto-install SARAH (the Mathematica-based BSM model builder). Handles existing installs, custom paths, and Wolfram Engine activation status.
---

## When to invoke

Use `/sarah-install` before running `/sarah-build` to ensure SARAH is present and
the Wolfram Engine is reachable.  The skill is idempotent: if SARAH is already
configured it returns `{"status":"configured"}` immediately without touching disk.

## Disk footprint

- **Tarball:** ~30 MB (SARAH-4.15.3 from HEPForge)
- **Installed tree:** ~71 MB at `~/SARAH/SARAH-4.15.3`
- **Build-time peak (transient):** ~80 MB (extraction only; no compile step)
- **Measured 2026-04-25 on macOS arm64.** Source: du measured 2026-04-25.

Typical invocation order:

1. `/sarah-install detect` — check current state (no side-effects).
2. `/sarah-install use-path <dir>` — register an existing SARAH directory.
3. `/sarah-install install` — full auto-install (requires Wolfram Engine).

---

## Decision flow

```
/sarah-install detect
       │
       ├── config has sarah_path + valid SARAH.m + version probe succeeds
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds SARAH.m
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

/sarah-install use-path <dir>
       │
       ├── <dir>/SARAH.m exists AND wolframscript configured
       │       ├── version probe succeeds → writes sarah_path, sarah_version,
       │       │   sarah_installed_at; {"status":"configured",...}        exit 0
       │       └── version probe fails → SARAH_SMOKE_TEST_FAILED blocker  exit 15
       │
       ├── <dir>/SARAH.m missing → SARAH_PATH_INVALID blocker             exit 16
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20

/sarah-install install [dir]
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20
       ├── disk check (need ≥1 GB free in $HOME)
       ├── download SARAH tarball (HEPPH_SARAH_VERSION or pinned 4.15.3)
       ├── verify_checksum (warns if SHA256 == "TODO"; does not abort)
       ├── extract to <dir>/SARAH-<version>/   (default: ~/SARAH)
       ├── register Wolfram $Path via init.m
       ├── version probe
       │   ├── succeeds → writes sarah_path, sarah_version, sarah_installed_at
       │   │   └── check_wolfram_activation.sh
       │   │       ├── status ok   → log "SARAH installed and ready."      exit 0
       │   │       └── status activation_required
       │   │               └── print {"status":"activation_required","user_instruction":"..."}
       │   │                   exit 0   (NOT a blocker; user must activate Wolfram)
       │   └── fails → SARAH_SMOKE_TEST_FAILED blocker                    exit 15
       └── download failed → SARAH_DOWNLOAD_FAILED blocker                exit 12
```

---

## JSON status contract

`detect` and `use-path` emit JSON on **stdout**.  `install` emits JSON on stdout
for the activation-required path only; all other outcomes are logged to stderr.

| `status` value | Meaning |
|---|---|
| `configured` | `sarah_path` set, `SARAH.m` present, version probe succeeded |
| `found` | SARAH found on disk via scan but not in config |
| `missing` | No SARAH found anywhere |
| `activation_required` | SARAH installed but Wolfram Engine needs activation |

Fields for `configured`:
```json
{"status":"configured","path":"/path/to/SARAH-4.15.3","version":"4.15.3"}
```

Fields for `activation_required`:
```json
{
  "status": "activation_required",
  "message": "Wolfram Engine is installed but needs activation.",
  "user_instruction": "Run `wolframscript --activate` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun /sarah-install."
}
```

---

## Activation handling (critical)

**`activation_required` is a status code, NOT a blocker.**

This diverges from spec §2, which lists `WOLFRAM_NEEDS_ACTIVATION` as a fatal
blocker.  The divergence is deliberate and documented in phase1-final §4: Wolfram
activation is a one-time user action that requires a browser; emitting a fatal
blocker would halt the entire pipeline permanently, whereas returning a structured
status allows the orchestrator (W5) to show the user the `user_instruction` and
wait.  The `install` subcommand exits 0 with `{"status":"activation_required"}`
so the caller can handle it gracefully.

Wolfram Engine detection is decoupled from hep-ph-demo via `detect_wolfram.sh`.
The activation probe uses `check_wolfram_activation.sh`, which pipes
`wolframscript -code '1+1'` output through `_activation_parse.py`.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | `user_instruction` |
|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | `wolfram_engine_path` not set or binary missing | Run `/install` → install Wolfram Engine |
| `SARAH_DOWNLOAD_FAILED` | `fatal` | `curl` failed twice | Check network; retry |
| `SARAH_SMOKE_TEST_FAILED` | `fatal` | Version probe returned empty after install | Check Wolfram Engine activation |
| `SARAH_PATH_INVALID` | `fatal` | `use-path <dir>` has no `SARAH.m` | Provide path to SARAH package dir |

`WOLFRAM_NEEDS_ACTIVATION` is **not** emitted as a blocker by this skill.  The
activation state is surfaced only via the `activation_required` status JSON.

---

## Config keys written

| Key | Value |
|---|---|
| `sarah_path` | Absolute path to SARAH package dir (contains `SARAH.m`) |
| `sarah_version` | Version string extracted by `probe_version` |
| `sarah_installed_at` | UTC ISO 8601 timestamp |

Keys **read** (must be set by `/install` or `/sarah-install use-path` for Wolfram):
`wolfram_engine_path` — path to the `wolframscript` binary.

---

## Version pin and override

Pinned version: **4.15.3** (set in `skill_env.yaml` and `SHARED.md §Env-var overrides`).

Override via environment:
```bash
HEPPH_SARAH_VERSION=4.14.0 /sarah-install install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-model-building.md`
- Spec: `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
- Implementation plan: `docs/superpowers/workstream-sarah-spheno/phase2-plan-final.md` §W1
