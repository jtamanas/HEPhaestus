# DRAKE Setup and Install Detection

## Prerequisites

DRAKE has two hard prerequisites:

1. **Wolfram Engine or Mathematica ≥ 13.1** — DRAKE is pure Wolfram Language.
   Install via `/install`. The `wolframscript` binary must be on `PATH` or registered
   at `wolfram_engine_path` in config.
2. **DRAKE source tree** — approximately 10 MB of Wolfram source files. Download from
   https://drake.hepforge.org/ (requires a browser; the site is behind an Anubis
   Proof-of-Work bot-protection gate that blocks `curl`/`wget`).

DRAKE does NOT require MadDM, micrOMEGAs, MadGraph, or any compiler toolchain.

---

## Install detection

Run `bash _shared/installs/drake/detect.sh` before any DRAKE workflow. The detect subcommand reads
`drake_path` from config and runs the canonical WIMP smoke test to confirm DRAKE is
operational.

```bash
# Invoked by the skill — not intended for direct user execution
bash "$DRAKE_INSTALL_SCRIPTS/install.sh" detect
```

Output JSON (stdout):

| `status` | Meaning | Action |
|----------|---------|--------|
| `configured` | `drake_path` set, `test/test.wls` present, WIMP smoke test passed | Proceed with `/drake` |
| `found` | DRAKE tree found on disk but not registered in config (or wolframscript absent) | Run `bash _shared/installs/drake/install.sh use-path <dir>` |
| `missing` | No DRAKE install found | Run `_shared/installs/drake/INSTALL.md` — see below |

Note: `activation_required` is emitted by the `use-path` subcommand (not `detect`) when
a smoke test fails only because Wolfram Engine needs activation. `detect` returns only
`configured`, `found`, or `missing`.

**`missing` and `found` are hard blockers for `/drake`. Do not proceed.**

---

## Config keys

| Key | Written by | Purpose |
|-----|-----------|---------|
| `drake_path` | `bash _shared/installs/drake/install.sh use-path` | Absolute path to DRAKE root (directory containing `test/test.wls`) |
| `drake_version` | `bash _shared/installs/drake/install.sh use-path` | Version string from `probe_drake.sh`; `"1.0 (assumed)"` if probe returns empty; `"1.0 (assumed, unverified)"` if smoke test only failed activation |
| `drake_installed_at` | `bash _shared/installs/drake/install.sh use-path` | UTC ISO 8601 timestamp |
| `wolfram_engine_path` | `/install` | Absolute path to `wolframscript` binary |

The `/drake` skill reads `drake_path` and `wolfram_engine_path`. If either is absent,
it emits `DRAKE_NOT_INSTALLED` or `DRAKE_WOLFRAM_ABSENT` (fatal) and stops.

---

## What "configured" means

`configured` status requires all three:
1. `drake_path` is set in config and points to a real directory
2. `$drake_path/test/test.wls` exists
3. The WIMP smoke test passes: `wolframscript test.wls WIMP bm_WIMP settings_WIMP`
   exits 0 and produces non-empty stdout

The smoke test runs in seconds. Log is written to `/tmp/drake_smoke.log`.

---

## Installing DRAKE

### Recommended path (hepforge Anubis gate)

The hepforge download server is protected by a JavaScript Proof-of-Work challenge.
`curl` and `wget` receive the challenge HTML instead of the zipball, which causes a
silent failure. The `bash _shared/installs/drake/install.sh install` subcommand detects this and emits
`{"status":"manual_download_required", ...}` with instructions.

Manual steps:
1. Open https://drake.hepforge.org/ in a browser.
2. Click **Downloads** and save the zipball (e.g. `drake.zip`).
3. Unpack it: `unzip drake.zip -d ~/drake`
4. Register with the skill: `bash _shared/installs/drake/install.sh use-path ~/drake`

The unpack target must be the DRAKE root directory — the one that directly contains
a `test/` subdirectory with `test.wls` inside it.

### Auto-install attempt

`bash _shared/installs/drake/install.sh install` will attempt `curl` download first. If the Anubis gate blocks
it, the subcommand exits 0 with `status: manual_download_required` (not a hard error).
The user is routed to the manual path above.

---

## Re-running the smoke test

```bash
bash "$DRAKE_INSTALL_SCRIPTS/install.sh" validate
```

Equivalent to running the canonical WIMP smoke test:

```bash
cd "$DRAKE_PATH/test"
wolframscript test.wls WIMP bm_WIMP settings_WIMP
```

Output is written to `/tmp/drake_smoke.log`. Non-empty stdout + exit 0 = pass.
