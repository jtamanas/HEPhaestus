---
name: feynarts-install
description: Detect, validate, or auto-install FeynArts 3.11 (the Mathematica-based Feynman diagram generator). Handles existing installs, custom paths, and Wolfram Engine activation status.
---

## When to invoke

Use `/feynarts-install` before running `/feynarts` to ensure FeynArts is present and
the Wolfram Engine is reachable.  The skill is idempotent: if FeynArts is already
configured it returns `{"status":"configured"}` immediately without touching disk.

## Disk footprint

- **Tarball:** ~3 MB (`https://www.feynarts.de/FeynArts-3.11.tar.gz`)
- **Installed tree:** ~11 MB at `~/Library/WolframEngine/Applications/FeynArts-3.11`
- **Build-time peak (transient):** ~15 MB (extraction only; no compile step)
- **Measured 2026-04-25 on macOS arm64.** Source: run-20260425-dmc/installer_mathematica_report.md.

Typical invocation order:

1. `/feynarts-install detect` — check current state (no side-effects).
2. `/feynarts-install use-path <dir>` — register an existing FeynArts directory.
3. `/feynarts-install install` — full auto-install (requires Wolfram Engine + network).

---

## Decision flow

```
/feynarts-install detect
       │
       ├── config has feynarts_path + valid FeynArts installation + version probe succeeds
       │       └── {"status":"configured","path":"...","version":"3.11"}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds FeynArts
       │       ├── single result → {"status":"found","path":"..."}         exit 0
       │       └── multiple results → {"status":"ambiguous","paths":[...]} exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                    exit 0

/feynarts-install use-path <dir>
       │
       ├── <dir>/FeynArts.m exists AND wolframscript configured
       │       ├── version probe succeeds → writes feynarts_path, feynarts_version,
       │       │   feynarts_installed_at; {"status":"configured",...}      exit 0
       │       └── version probe fails → FEYNARTS_SMOKE_TEST blocker       exit 28
       │
       ├── <dir>/FeynArts.m missing → FEYNARTS_PATH_INVALID blocker        exit 27
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker     exit 20

/feynarts-install install
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker     exit 20
       ├── disk check (need ≥1 GB free in $HOME)
       ├── download FeynArts-3.11.tar.gz from hepforge mirror
       ├── verify_checksum (warns if SHA256 == "TODO"; does not abort)
       ├── extract to $UserBaseDirectory/Applications/FeynArts-3.11/
       ├── smoke test (Needs["FeynArts`"]; $FeynArtsVersion)
       │   ├── succeeds → writes feynarts_path, feynarts_version,
       │   │   feynarts_installed_at, feynarts_generic_model_hash
       │   │   └── check_wolfram_activation.sh
       │   │       ├── status ok   → log "FeynArts installed and ready."   exit 0
       │   │       └── status activation_required
       │   │               └── print {"status":"activation_required","user_instruction":"..."}
       │   │                   exit 0   (NOT a blocker; user must activate Wolfram)
       │   └── fails → FEYNARTS_SMOKE_TEST blocker                         exit 28
       └── download failed → FEYNARTS_DOWNLOAD_FAILED blocker              exit 12
```

---

## JSON status contract

`detect` and `use-path` emit JSON on **stdout**.  `install` emits JSON on stdout
for the activation-required path only; all other outcomes are logged to stderr.

| `status` value | Meaning |
|---|---|
| `configured` | `feynarts_path` set, `FeynArts.m` present, version probe succeeded |
| `found` | FeynArts found on disk via scan but not in config |
| `ambiguous` | Multiple FeynArts installations found; user must select one |
| `missing` | No FeynArts found anywhere |
| `activation_required` | FeynArts installed but Wolfram Engine needs activation |

Fields for `configured`:
```json
{"status":"configured","path":"/path/to/FeynArts-3.11","version":"3.11"}
```

Fields for `found`:
```json
{"status":"found","path":"/path/to/FeynArts-3.11"}
```

Fields for `ambiguous`:
```json
{"status":"ambiguous","paths":["/path/one","path/two"]}
```

Fields for `activation_required`:
```json
{
  "status": "activation_required",
  "message": "Wolfram Engine is installed but needs activation.",
  "user_instruction": "Run `wolframscript --activate` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun /feynarts-install."
}
```

---

## Activation handling (critical)

**`FEYNARTS_ACTIVATION_REQUIRED` is a status code, NOT a blocker.**

This mirrors the pattern established by `/sarah-install`: Wolfram activation is a
one-time user action that requires a browser.  Emitting a fatal blocker would halt
the pipeline permanently.  Instead, the `install` subcommand exits 0 with
`{"status":"activation_required"}` so the orchestrator can surface the
`user_instruction` and wait for the user to activate.

The activation probe uses `check_wolfram_activation.sh` (from
`plugins/shared/install-helpers/wolfram/`), which pipes
`wolframscript -code '1+1'` output through `_activation_parse.py`.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Exit | Trigger | `user_instruction` |
|---|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | 20 | `wolfram_engine_path` not set or binary missing | Run `/install` → install Wolfram Engine |
| `FEYNARTS_DOWNLOAD_FAILED` | `fatal` | 12 | `curl` failed twice | Check network; retry |
| `FEYNARTS_SMOKE_TEST` | `fatal` | 28 | Version probe returned empty after install | Check Wolfram Engine activation |
| `FEYNARTS_PATH_INVALID` | `fatal` | 27 | `use-path <dir>` has no `FeynArts.m` | Provide path to FeynArts package dir |
| `FEYNARTS_AMBIGUOUS` | `fatal` | 29 | Multiple FeynArts installs found | Run `use-path <dir>` with explicit dir |
| `FEYNARTS_SHA256_NOT_PINNED` | `fatal` | 30 | `sha256: "TODO"` in `skill_env.yaml` and bypass not set | Compute real checksum (see below) |

`activation_required` is **not** emitted as a blocker by this skill.  The
activation state is surfaced only via the status JSON (see above).

### SHA256 checksum pinning

The FeynArts tarball SHA256 must be pinned before production use.  While it
remains `"TODO"`, the install script emits `FEYNARTS_SHA256_NOT_PINNED` and
exits 30.

**To compute the real checksum (15 min, requires a validated tarball):**
```bash
curl -L https://www.feynarts.de/FeynArts-3.11.tar.gz -o /tmp/FeynArts-3.11.tar.gz
sha256sum /tmp/FeynArts-3.11.tar.gz   # Linux
# or: shasum -a 256 /tmp/FeynArts-3.11.tar.gz  # macOS
```
Then update `sha256` in `skill_env.yaml` and `EXPECTED_SHA256` in
`install_feynarts.sh`.

**Dev-only bypass (insecure):** set `HEPPH_FEYNARTS_SKIP_SHA256=1` to log a
warning and proceed without checksum verification:
```bash
HEPPH_FEYNARTS_SKIP_SHA256=1 /feynarts-install install
```
This bypass must **not** be used in production or CI.

---

## Install directory convention

FeynArts is always installed to:

```
$UserBaseDirectory/Applications/FeynArts-3.11/
```

On macOS this expands to `~/Library/Wolfram/Applications/FeynArts-3.11/`.
On Linux (Wolfram Engine) it expands to `~/.WolframEngine/Applications/FeynArts-3.11/`.

This follows the same `$UserBaseDirectory/Applications/` convention used by SARAH.
Do **not** install to `~/FeynArts/` or any path outside `$UserBaseDirectory`.

---

## Config keys written

| Key | Value |
|---|---|
| `feynarts_path` | Absolute path to FeynArts package dir (contains `FeynArts.m`) |
| `feynarts_version` | Version string extracted by smoke test (`"3.11"`) |
| `feynarts_installed_at` | UTC ISO 8601 timestamp |
| `feynarts_generic_model_hash` | `sha256(Models/Lorentz.gen)` — cache-key input for `/feynarts` |

Keys **read**:
- `wolfram_engine_path` — path to the `wolframscript` binary (set by `/install`).
- `feynarts_path` — read back on detect/use-path flows.

---

## Version pin and override

Pinned version: **3.11** (set in `skill_env.yaml`).

Override via environment:
```bash
HEPPH_FEYNARTS_VERSION=3.10 /feynarts-install install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Wolfram helpers: `plugins/shared/install-helpers/wolfram/`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-feynman.md`
