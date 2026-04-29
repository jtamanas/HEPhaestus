# SARAH — Install Reference

Reference doc for installing **SARAH** (the Mathematica-based BSM model
builder). Driven by `detect.sh` and `install.sh` in this directory;
consumed by the `sarah-build` runner skill's preflight and by `/install`.
Idempotent: if SARAH is already configured the scripts return
`{"status":"configured"}` immediately without touching disk.

## Version pin

`detect.sh` pins SARAH to **4.15.3**. Override with
`HEPPH_SARAH_VERSION=x.y.z`. When the pin bumps, `install.sh` is
responsible for:
- Removing or migrating the previous install tree (e.g.
  `~/SARAH/SARAH-4.15.3` → `~/SARAH/SARAH-<new>`).
- **Cleaning the previous version's `init.m` entry**. `install.sh`
  guards its block with `BEGIN/END` markers
  (`(* hephaestus SARAH path BEGIN *)` / `(* hephaestus SARAH path END *)`)
  in `~/.WolframEngine/Kernel/init.m` (Linux) /
  `~/Library/WolframEngine/Kernel/init.m` (macOS). On every
  `install.sh install` it strips the old block — including the legacy
  single-line `(* hephaestus SARAH path *)` shape from earlier
  hephaestus versions — before appending the new entry, so a SARAH
  upgrade does not leave both parent dirs live on `$Path`.
- Writing the new version to `config.json` only after the install
  verifies, so a half-finished upgrade does not leave the config
  pointing at a stale path.

## Disk footprint

- **Tarball:** ~30 MB (SARAH-4.15.3 from HEPForge)
- **Installed tree:** ~71 MB at `~/SARAH/SARAH-4.15.3`
- **Build-time peak (transient):** ~80 MB (extraction only; no compile step)
- **Measured 2026-04-25 on macOS arm64.** Source: du measured 2026-04-25.

Typical invocation order:

1. `bash detect.sh` — check current state (no side-effects).
2. `bash install.sh use-path <dir>` — register an existing SARAH directory.
3. `bash install.sh install` — full auto-install (requires Wolfram Engine).

---

## Decision flow

```
bash detect.sh
       │
       ├── config has sarah_path + valid SARAH.m + version probe succeeds
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds SARAH.m
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

bash install.sh use-path <dir>
       │
       ├── <dir>/SARAH.m exists AND wolframscript configured
       │       ├── version probe succeeds → writes sarah_path, sarah_version,
       │       │   sarah_installed_at; {"status":"configured",...}        exit 0
       │       └── version probe fails → SARAH_SMOKE_TEST_FAILED blocker  exit 15
       │
       ├── <dir>/SARAH.m missing → SARAH_PATH_INVALID blocker             exit 16
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20

bash install.sh install [dir]
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
  "user_instruction": "Run `wolframscript --activate` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun _shared/installs/sarah."
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

Keys **read** (must be set by `/install` or `bash install.sh use-path` for Wolfram):
`wolfram_engine_path` — path to the `wolframscript` binary.

---

## Version pin and override

Pinned version: **4.15.3** (set in `skill_env.yaml` and `SHARED.md §Env-var overrides`).

Override via environment:
```bash
HEPPH_SARAH_VERSION=4.14.0 bash install.sh install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-model-building.md`
- Spec: `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
- Implementation plan: `docs/superpowers/workstream-sarah-spheno/phase2-plan-final.md` §W1
