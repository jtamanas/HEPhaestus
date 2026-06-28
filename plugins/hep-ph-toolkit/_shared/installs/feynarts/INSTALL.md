# FeynArts — Install Reference

Reference doc for installing **FeynArts 3.11** (the Mathematica-based
Feynman diagram generator). Driven by `detect.sh` and `install.sh` in
this directory; consumed by the `feynarts` runner skill's preflight
and by `/install`. Handles existing installs, custom paths, and
Wolfram Engine activation status.

## Version pin

`detect.sh` pins FeynArts to **3.11**. Override with
`HEPPH_FEYNARTS_VERSION=x.y`. When this pin bumps, `install.sh` must
remove or migrate the previous install tree
(e.g. `~/Library/WolframEngine/Applications/FeynArts-3.11` →
`...FeynArts-<new>`); the new version is only written to
`config.json` after the new install verifies, so a half-finished
upgrade does not leave the config pointing at a stale tree.

## Disk footprint

- **Tarball:** ~3 MB (`https://www.feynarts.de/FeynArts-3.11.tar.gz`)
- **Installed tree:** ~11 MB at `~/Library/WolframEngine/Applications/FeynArts-3.11`
- **Build-time peak (transient):** ~15 MB (extraction only; no compile step)
- **Measured 2026-04-25 on macOS arm64.** Source: run-20260425-dmc/installer_mathematica_report.md.

Typical invocation order:

1. `install.sh detect` — check current state (no side-effects).
2. `install.sh use-path <dir>` — register an existing FeynArts directory.
3. `install.sh install` — full auto-install (requires Wolfram Engine + network).

---

## Wolfram Engine version compatibility — critical

**FeynArts 3.11 and 3.12 deterministically crash the Wolfram Engine 14.x kernel
(`SIGSEGV`, exit 139) the moment FeynArts initializes a generic model.** This
is a **native Wolfram Engine regression**, not a FeynArts bug, and it is
**portable across machines** running a 14.x (or newer) engine. Document it here
so installers on other machines diagnose it in seconds instead of hours.

### Symptom — why the naive check is a FALSE GREEN

`Needs["FeynArts`"]` and `$FeynArtsVersion` **succeed** — the package loads
cleanly. The crash only happens later, when FeynArts parses the generic Lorentz
model (`Models/Lorentz.gen`) inside `InitializeModel[]` / `InsertFields[]`. So a
smoke test that only loads the package and prints the version reports **green
while the tool is in fact unusable**. Reproduced identically on the built-in
`SM`, the built-in `QED`, and a project model fixture — i.e. it is the generic
model parse, not any one model file.

Minimal reproduction (this WILL kill the kernel on a 14.x engine):

```bash
WS="$(command -v wolframscript)"                       # the global 14.x engine
FA="$(python3 -c 'import json,os;print(json.load(open(os.path.expanduser("~/.config/hephaestus/config.json")))["feynarts_path"])')"
"$WS" -code 'AppendTo[$Path,"'"$FA"'"]; Needs["FeynArts`"];
  Print["LOADED ", FeynArts`$FeynArtsVersion];
  ToExpression["InitializeModel[]"];          (* deferred — see note below *)
  Print["INIT_OK"]'
echo "exit=$?"        # 139 on WE 14.x; prints up to "loading generic model
                      # file .../Models/Lorentz.gen" then dies. INIT_OK never prints.
```

> **`ToExpression` is load-bearing.** In `wolframscript -code '...'` a bare
> `InitializeModel[]` is interned into ``Global` `` at *parse* time, before
> `Needs[]` runs, so it resolves to an undefined ``Global` `` symbol and returns
> unevaluated — FeynArts's real `InitializeModel` never executes and you get a
> *second* false green (`INIT_OK` prints, nothing crashed, nothing ran). Defer
> resolution with `ToExpression["InitializeModel[]"]` (or fully qualify as
> ``FeynArts`InitializeModel[]``) so the call binds after the package loads.
> This is the same parse-time-interning gotcha documented for the LoopTools
> `B0` verification.

### Root cause — a 14.x+ native regression, go BACK to the validated era

FeynArts is a 2019-era tool validated against **Mathematica/Wolfram Engine
12.x–13.x**. The crash is a **native regression introduced in the 14.x engine**;
it is *not* a tameable Wolfram-language stack overflow. **15.0 is newer than
14.x and is expected to crash the same way** — the fix is not "go forward", it
is "go back to the validated 12.x–13.x era".

### Non-fixes — do not waste time on these

- **Upgrading FeynArts 3.11 → 3.12 does NOT fix it.** Both versions crash
  identically; the bug is in the engine, not the package.
- **Clamping `$RecursionLimit` does NOT fix it**, and neither does raising the
  OS stack limit (`ulimit -s`). It is a native `SIGSEGV`, not a WL recursion
  overflow, so there is no WL- or shell-level knob that tames it.

### The fix is COEXISTENCE, not replacement

Keep the existing 14.x engine — the parts that work, **work**: FormCalc 9.10,
FORM 4.3.1, and LoopTools 2.16 are all confirmed functional on 14.3. **Do not
repoint or downgrade the global engine.** Instead, install an **older Wolfram
Engine used ONLY for FeynArts** and leave everything else on 14.x:

- **Recommended: Wolfram Engine 13.3.** Fallback: 12.3.
- Multiple engines coexist on macOS (each is a self-contained `.app`).
- `wolframscript -local <KERNELPATH>` selects a specific kernel binary, so
  FeynArts calls can target the older kernel while every other tool keeps using
  the 14.x one.

### User action prerequisite — obtaining the older engine (login + license gated)

The older engine **cannot be auto-installed** by this skill: the download is
behind a Wolfram account login and a (free) license activation. A human must:

1. Sign in at <https://www.wolfram.com/engine/> with a Wolfram ID and download
   the **13.3** (or 12.3) engine for this OS/arch.
2. Install it to a **non-default path** so it does not collide with the 14.x
   engine, e.g. macOS:
   ```
   /Applications/Wolfram Engine 13.3.app
   ```
3. Activate that specific kernel (free Wolfram ID license):
   ```bash
   "/Applications/Wolfram Engine 13.3.app/Contents/MacOS/WolframKernel" -activate
   # or: wolframscript -local "<KERNELPATH>" -activate
   # (the -local/-activate combination may not be supported in all versions;
   #  if it fails, use the direct WolframKernel -activate form shown above)
   ```

### Locating the older kernel binary (portable — do not hardcode)

```bash
# macOS (Spotlight): every installed WolframKernel, newest paths included.
mdfind -name WolframKernel | grep -i 'Wolfram Engine'

# macOS (fallback): scan the conventional app roots and pick the 13.x/12.x one.
find /Applications -maxdepth 4 -name WolframKernel 2>/dev/null | grep -iE '13|12'

# Linux: scan the conventional per-user engine roots.
find ~/.WolframEngine ~/.Mathematica -iname WolframKernel 2>/dev/null | grep -iE '13|12'
# The kernel binary on Linux typically lives at:
#   <EngineRoot>/Executables/WolframKernel
# e.g. ~/.WolframEngine/13.3/Executables/WolframKernel

# Confirm a candidate's version BEFORE wiring it in:
"<KERNELPATH>" -code 'Print[$VersionNumber]'      # want 13.3 / 12.3, not 14.x
```

The kernel binary lives at
`<WolframEngineRoot>.app/Contents/MacOS/WolframKernel` on macOS and at
`<WolframEngineRoot>/Executables/WolframKernel` on Linux.

### Wiring plan (documented; NOT yet implemented)

The intended remedy — deferred until a 13.3 engine is installed so it can be
tested end-to-end — is a **FeynArts-only kernel override**:

- A new config key **`feynarts_wolfram_kernel`** (env override
  `HEPPH_FEYNARTS_WOLFRAM_KERNEL`) holding the absolute path to the older
  `WolframKernel`.
- The FeynArts runner (`plugins/hep-ph-toolkit/skills/feynarts/scripts/run_feynarts.py`,
  where it currently resolves `wolfram_engine_path` and invokes
  `wolframscript -script ...`) passes that kernel through as
  `wolframscript -local <kernel> -script ...` **only for FeynArts calls**.
- The global **`wolfram_engine_path` is left untouched**, so the working
  FormCalc / LoopTools / FORM half stays on the 14.x engine. Only FeynArts is
  redirected to the validated older kernel.

`smoke_test_feynarts.sh` already honours `feynarts_wolfram_kernel` /
`HEPPH_FEYNARTS_WOLFRAM_KERNEL` (passes it as `-local`), so once the older
engine is installed the same hardened test verifies the coexistence fix without
further changes.

### Diagnosis at a glance

| Observation | Verdict |
|---|---|
| `Needs["FeynArts`"]` ok, `$FeynArtsVersion` prints, exit 0 | **Inconclusive** — does NOT prove FeynArts works (false green). |
| `InitializeModel[]` (via `ToExpression`) completes, `INIT_OK` prints, exit 0 | **Working.** |
| Output stops at `loading generic model file .../Lorentz.gen`, exit 139 (or any ≥128) | **WE-version regression.** Apply the coexistence fix. |

---

## Decision flow

```
install.sh detect
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

install.sh use-path <dir>
       │
       ├── <dir>/FeynArts.m exists AND wolframscript configured
       │       ├── version probe succeeds → writes feynarts_path, feynarts_version,
       │       │   feynarts_installed_at; {"status":"configured",...}      exit 0
       │       └── version probe fails → FEYNARTS_SMOKE_TEST blocker       exit 28
       │
       ├── <dir>/FeynArts.m missing → FEYNARTS_PATH_INVALID blocker        exit 27
       └── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker     exit 20

install.sh install
       │
       ├── wolfram_engine_path not set → WOLFRAM_KERNEL_ABSENT blocker     exit 20
       ├── disk check (need ≥1 GB free in $HOME)
       ├── download FeynArts-3.11.tar.gz from hepforge mirror
       ├── verify_checksum (warns if SHA256 == "TODO"; does not abort)
       ├── extract to $UserBaseDirectory/Applications/FeynArts-3.11/
       ├── smoke test (loads FeynArts AND runs InitializeModel[] — see
       │   "## Wolfram Engine version compatibility"; a load-only check is a
       │   false green)
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
{"status":"ambiguous","paths":["/path/one","/path/two"]}
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

**`FEYNARTS_ACTIVATION_REQUIRED` is a status code, NOT a blocker.**

This mirrors the pattern established by `_shared/installs/sarah`: Wolfram activation is a
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
| `FEYNARTS_SMOKE_TEST` | `fatal` | 28 | `InitializeModel[]` did not complete (no `FEYNARTS_INIT_OK` sentinel) and the kernel did not crash | Check Wolfram Engine activation |
| `FEYNARTS_ENGINE_INCOMPAT` | `fatal` | 31 | Kernel crashed (exit 139 / ≥128) during `InitializeModel[]` while parsing `Models/Lorentz.gen` — the WE 14.x+ regression | Install an older engine (13.3/12.3) for FeynArts only; set `feynarts_wolfram_kernel`. See "## Wolfram Engine version compatibility — critical" |
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
`install.sh`.

**Dev-only bypass (insecure):** set `HEPPH_FEYNARTS_SKIP_SHA256=1` to log a
warning and proceed without checksum verification:
```bash
HEPPH_FEYNARTS_SKIP_SHA256=1 install.sh install
```
This bypass must **not** be used in production or CI.

---

## Install directory convention

FeynArts is always installed to:

```
$UserBaseDirectory/Applications/FeynArts-3.11/
```

`$UserBaseDirectory` is resolved live by wolframscript, so the exact root
depends on the product:

| Product / OS | `$UserBaseDirectory/Applications` |
|---|---|
| macOS Wolfram Engine | `~/Library/WolframEngine/Applications/` |
| macOS Mathematica/Wolfram desktop | `~/Library/Wolfram/Applications/` (or legacy `~/Library/Mathematica/...`) |
| Linux Wolfram Engine | `~/.WolframEngine/Applications/` |
| Linux Mathematica | `~/.Mathematica/Applications/` |

The standalone scanner `_probe.sh` enumerates **all** of these roots — picking
the wrong sibling (`Wolfram` vs `WolframEngine`) is the classic false-"missing".

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
HEPPH_FEYNARTS_VERSION=3.10 install.sh install
```

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Wolfram helpers: `plugins/shared/install-helpers/wolfram/`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Shared conventions: `plugins/hep-ph-toolkit/SHARED-feynman.md`
