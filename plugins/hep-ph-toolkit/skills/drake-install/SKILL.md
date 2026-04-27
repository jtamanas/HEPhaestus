---
name: drake-install
description: Detect, validate, or install DRAKE (Dark matter Relic Abundance beyond Kinetic Equilibrium) — a Wolfram Language package for solving the coupled Boltzmann equation. Handles the hepforge Anubis bot-protection gate by routing users through a manual-download path.
---

## When to invoke

Use `/drake-install` before invoking any DRAKE-driven workflow (narrow
resonance relic density, Sommerfeld enhancement, early kinetic decoupling —
typically the optional extension branch of `/dark-matter-constraints`).
DRAKE is pure Wolfram Language; the only system prerequisite is a reachable
Wolfram Engine or Mathematica ≥ 13.1.

## Disk footprint

- **Tarball:** ~1 MB (`DRAKE_v1.0.zip` — manual download from https://drake.hepforge.org/)
- **Installed tree:** ~5 MB estimated at `~/drake`
- **Build-time peak (transient):** n/a (Wolfram package; no compile step)
- **Estimated.** Source: user-provided 2026-04-25. Note: hepforge Anubis gate blocks automated download; manual download via browser required.

DRAKE is **not** a dependency of, nor dependent on, MadDM or micrOMEGAs.
Cross sections (`sv[s_]`, `gam[x_]`) are supplied by the user as Wolfram
functions — DRAKE does not import them from other tools.

Typical invocation order:

1. `/drake-install detect` — check current state (no side-effects).
2. `/drake-install use-path <dir>` — register a user-downloaded DRAKE tree.
3. `/drake-install install` — attempt auto-install (likely blocked by the
   hepforge Anubis gate; routes the user through manual download).

---

## Decision flow

```
/drake-install detect
       │
       ├── config has drake_path + valid test/test.wls + smoke test passes
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds test/test.wls
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

/drake-install use-path <dir>
       │
       ├── <dir>/test/test.wls exists AND wolframscript configured
       │       ├── smoke test passes → writes drake_path, drake_version,
       │       │   drake_installed_at; {"status":"configured",...}        exit 0
       │       ├── smoke test fails activation check
       │       │       → print {"status":"activation_required", ...}      exit 0 (NOT a blocker)
       │       └── smoke test fails otherwise → DRAKE_SMOKE_TEST_FAILED   exit 15
       │
       ├── <dir>/test/test.wls missing → DRAKE_PATH_INVALID blocker       exit 16
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20

/drake-install install [dir]
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker    exit 20
       ├── disk check (need ~50 MB free in $HOME — DRAKE itself is ~10 MB)
       ├── attempt download_with_retry from hepforge
       │   ├── success → extract, run smoke test, configure
       │   └── FAIL (Anubis bot-challenge is the common case)
       │           └── print {"status":"manual_download_required",
       │                      "user_instruction":"Open https://drake.hepforge.org/
       │                                          in a browser, download the
       │                                          zipball, unpack it, then run
       │                                          /drake-install use-path <dir>"}
       │               exit 18 (DRAKE_HEPFORGE_GATED)
       └── extraction/smoke failures follow the same pattern as sarah-install.
```

---

## JSON status contract

`detect`, `use-path`, and `install` all emit JSON on **stdout** for
success-ish outcomes (`configured`, `found`, `missing`, `activation_required`,
`manual_download_required`). Fatal blockers go to **stderr** as single-line
JSON.

| `status` value | Meaning |
|---|---|
| `configured` | `drake_path` set, `test/test.wls` present, smoke test passed |
| `found` | DRAKE tree found on disk via scan but not in config (or wolframscript absent) |
| `missing` | No DRAKE install found anywhere |
| `activation_required` | DRAKE installed but Wolfram Engine needs activation |
| `manual_download_required` | hepforge download blocked (Anubis); user must fetch manually |

Fields for `configured`:
```json
{"status":"configured","path":"/path/to/drake","version":"1.0"}
```

Fields for `manual_download_required`:
```json
{
  "status": "manual_download_required",
  "message": "Automated download from hepforge was blocked by bot-protection (Anubis PoW challenge).",
  "user_instruction": "Open https://drake.hepforge.org/ in a browser, click Downloads, save the zipball, unpack it (e.g. to ~/drake), then rerun `/drake-install use-path ~/drake`."
}
```

Fields for `activation_required`: same shape as sarah-install.

---

## Activation handling

**`activation_required` is a status code, NOT a blocker.** Same rationale
and contract as sarah-install: the install script exits 0, emits the status
JSON with a `user_instruction`, and leaves the user to run
`wolframscript --activate`.

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | Exit | `user_instruction` |
|---|---|---|---|---|
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | `wolfram_engine_path` not set / binary missing | 20 | Run `/install` → install Wolfram Engine |
| `DRAKE_DOWNLOAD_FAILED` | `fatal` | `curl` failed for non-Anubis reasons (DNS, offline) | 12 | Check network; retry |
| `DRAKE_HEPFORGE_GATED` | `fatal` | Download page returned an Anubis challenge | 18 | Open `https://drake.hepforge.org/` in a browser, download the zipball, rerun with `use-path` |
| `DRAKE_SMOKE_TEST_FAILED` | `fatal` | WIMP benchmark returned non-zero / empty stdout | 15 | Check Wolfram Engine activation; inspect `/tmp/drake_smoke.log` |
| `DRAKE_PATH_INVALID` | `fatal` | `use-path <dir>` has no `test/test.wls` | 16 | Provide the unpacked DRAKE root (contains `test/` and the model files) |

**Note**: `manual_download_required` is emitted in preference to
`DRAKE_HEPFORGE_GATED` when we can confidently route the user through manual
download (status JSON on stdout, exit 0). The fatal `DRAKE_HEPFORGE_GATED`
blocker is reserved for cases where download fails *and* we want to halt the
pipeline (e.g., non-interactive CI). In the default interactive flow the
status path is preferred.

---

## Config keys written

| Key | Value |
|---|---|
| `drake_path` | Absolute path to DRAKE root (contains `test/test.wls`) |
| `drake_version` | Version string — always `"1.0 (assumed)"` until DRAKE publishes a changelog |
| `drake_installed_at` | UTC ISO 8601 timestamp |

Keys **read** (must be set by `/install` or a prior `use-path`):
`wolfram_engine_path` — path to the `wolframscript` binary.

---

## Version pin and override

Pinned version: **1.0** (set in `skill_env.yaml`).

DRAKE has no formal version strings in its source — the authors have not
tagged releases since the initial public release tied to arXiv:2103.01944
(2021-03-02, revised 2021-08-04). The `drake_version` field is therefore
recorded as `"1.0 (assumed)"` to flag that the value is unverified.

Override via environment:
```bash
HEPPH_DRAKE_VERSION=1.0 /drake-install install
```

---

## Smoke test

Canonical WIMP benchmark (paper §A.3):

```
wolframscript test.wls WIMP bm_WIMP settings_WIMP
```

Runs in seconds. Non-zero exit or empty stdout = failure. Captured at
`/tmp/drake_smoke.log`.

Pre-implemented models shipped with DRAKE (useful for downstream
`/dark-matter-constraints`):

- `ScalarSingletDM`
- `WIMP` (used by the smoke test)
- `VRES` (narrow resonance — relevant for 2506.19062 Fig. 8)
- `SE` (Sommerfeld)
- `TH` (threshold / forbidden)

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Related sibling: `plugins/hep-ph-toolkit/skills/maddm-install`
  (MadDM is the primary relic-density driver; DRAKE is complementary, not a
  dependency)
- Profumo eval target: `eval/2506.19062_wimps_blind_spots/` (DRAKE is the
  optional extension on Fig. 8 resonance)

---

## Notable caveats

1. **Hepforge Anubis gate**. The DRAKE project site
   (`https://drake.hepforge.org/`) is behind a Proof-of-Work JavaScript
   challenge (Anubis). `curl` and `wget` receive a challenge page instead of
   the zipball and the download appears to succeed but contains HTML. This
   skill treats the gate as a first-class outcome: the `install` subcommand
   detects the failure and emits `manual_download_required` with a clear
   `user_instruction` rather than pretending the install succeeded. Users
   are routed through `use-path` after downloading in a browser.

2. **No formal DRAKE version string**. The authors describe DRAKE as "under
   continuous development" but publish no tags, changelog, or version
   constant in the source. We pin `1.0` and record `"1.0 (assumed)"` in
   config.

3. **DRAKE does NOT depend on MadDM or micrOMEGAs**. The paper explicitly
   positions DRAKE as complementary. Cross sections are user-provided
   Wolfram functions. No coupling to other tools is required (or supported)
   in this install skill.

4. **Mathematica/Wolfram Engine is the only prerequisite.** No compilers,
   no external libraries, ~10 MB of Wolfram source files. The heavy lift
   belongs to `/install` (Wolfram Engine itself, ~6 GB).
