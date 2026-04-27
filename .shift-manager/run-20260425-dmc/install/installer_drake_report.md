# Track 4 — DRAKE Installer Report

**Run:** `run-20260425-dmc`
**Date:** 2026-04-25
**Tool:** DRAKE (Dark matter Relic Abundance beyond Kinetic Equilibrium)
**Final state:** `MANUAL_DOWNLOAD_REQUIRED`

---

## 1. Skill location

The DRAKE install skill lives at **`plugins/monte-carlo-tools/skills/drake-install/`** (not under `plugins/constraints/` as the brief stated). The install logic is `scripts/install.sh`. Behavioural note: when the hepforge Anubis gate trips, the skill emits `{"status":"manual_download_required",...}` on stdout and **exits 0** (preferred interactive path), not exit 18. Exit 18 (`DRAKE_HEPFORGE_GATED`) is reserved for the non-interactive CI variant per SKILL.md §"Failure modes → blockers".

---

## 2. Probe results (defensive)

| Check | Result |
|---|---|
| `~/.config/hep-ph-agents/config.json` → `drake_path` | not present |
| `~/DRAKE/` | does not exist |
| `~/drake/` | does not exist |
| `~/.local/share/hep-ph-agents/drake/` | does not exist |
| `~/hep/drake/`, `~/software/drake/` | do not exist |
| `~/Tools/drake*` | no matches |
| `wolfram_engine_path` (prereq) | `/usr/local/bin/wolframscript` (set; v14.3.0) |
| `install.sh detect` | `{"status":"missing"}` exit 0 |

Wolfram Engine prerequisite is satisfied. DRAKE itself is not present anywhere on disk.

---

## 3. Install attempt

**Command run:**
```
/Users/yianni/Projects/hep-ph-agents/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh install
```
(default install target: `~/drake`; URL: `https://drake.hepforge.org/downloads/drake.zip`; pinned version: 1.0)

**Exit code:** `0` (status routed via stdout JSON, as designed).

**stdout:**
```json
{"status":"manual_download_required","message":"hepforge returned an Anubis bot-challenge page instead of the zipball.","user_instruction":"Open https://drake.hepforge.org/ in a browser, click Downloads, save the zipball, unpack it (e.g. to ~/drake), then rerun `/drake-install use-path ~/drake`."}
```

**stderr (full):**
```
[install_drake] DRAKE version: 1.0
[install_drake] Install target: /Users/yianni/drake
[install_drake] WARN: Low disk (1 GB). Install may succeed but space is tight.
[install_drake] Download attempt: https://drake.hepforge.org/downloads/drake.zip
[install_drake] WARN: Downloaded file looks like an Anubis challenge page, not a zipball.
```

**Outcome breakdown:**
- `curl` succeeded in fetching *something* (HTTP 200), so `dl_rc=0`.
- The downloaded artifact tripped `looks_like_anubis_challenge()` (small HTML containing Anubis/challenge markers), so the script discarded it, emitted the status JSON, and exited 0.
- Disk-tight warning was noted but did not abort (`check_disk` allowed the run; DRAKE's ~10 MB footprint fits in the available 1 GB).

No retry was performed (Anubis is deterministic). No other dependencies were touched (Wolfram Engine, MadDM, etc. were unaffected). Per skill contract, no config keys were written — `drake_path` will be set by the follow-up `use-path` invocation after manual download.

---

## 4. Final state

**`MANUAL_DOWNLOAD_REQUIRED`** — expected outcome. Anubis gate confirmed live as of 2026-04-25.

---

## 5. User next steps

DRAKE cannot be auto-installed because hepforge protects its download page with an Anubis JavaScript proof-of-work challenge that `curl`/`wget` cannot solve. Please complete these four steps interactively:

### Step 1 — Open the download page in a real browser

Visit:

> **https://drake.hepforge.org/**

Your browser will solve the Anubis PoW challenge automatically (takes a few seconds). Click the **Downloads** link in the sidebar.

Direct file URL once the gate is cleared:

> **https://drake.hepforge.org/downloads/drake.zip**

### Step 2 — Save and unpack the zipball

Save `drake.zip` to a working directory and unpack it. Suggested target (matches the skill's default scan path):

```bash
mkdir -p ~/drake
cd ~/drake
unzip ~/Downloads/drake.zip
```

The resulting tree must contain the file **`test/test.wls`** at the root that you point the skill at. If `unzip` produces a single nested directory (e.g. `~/drake/drake-1.0/test/test.wls`), use that nested path in step 3 — not `~/drake` itself.

To verify before continuing:
```bash
ls ~/drake/test/test.wls    # or ls ~/drake/<subdir>/test/test.wls
```

### Step 3 — Register the path with the skill

Run:

```bash
/Users/yianni/Projects/hep-ph-agents/plugins/monte-carlo-tools/skills/drake-install/scripts/install.sh use-path ~/drake
```

(Or, equivalently, `/drake-install use-path ~/drake` from inside Claude Code.)

This will:
1. Verify `test/test.wls` exists.
2. Run the canonical WIMP smoke test (`wolframscript test.wls WIMP bm_WIMP settings_WIMP`, runs in seconds).
3. Write `drake_path`, `drake_version` (`"1.0 (assumed)"`), and `drake_installed_at` to `~/.config/hep-ph-agents/config.json`.
4. Emit `{"status":"configured","path":"...","version":"..."}` on success.

### Step 4 — Possible follow-ups

- **`activation_required`** — if the smoke test reports this status, run `wolframscript --activate` once, then re-run `/drake-install detect`. The path will already be recorded in config, so no second `use-path` is needed.
- **`DRAKE_PATH_INVALID`** — `~/drake` does not contain `test/test.wls` directly. Adjust the path to point at the directory that does (likely a nested subdirectory created by `unzip`).
- **`DRAKE_SMOKE_TEST_FAILED`** — inspect `/tmp/drake_smoke.log`. Most often this is a Wolfram Engine activation issue.

### Version / integrity

| Item | Value |
|---|---|
| Pinned version | **1.0** (DRAKE has no formal release tags; `drake_version` is recorded as `"1.0 (assumed)"`) |
| Expected SHA256 | **none** — `HEPPH_DRAKE_SHA256` is `TODO` in the skill; no checksum verification will run. |
| Override version | `HEPPH_DRAKE_VERSION=<x> /drake-install install` |
| Override URL | `HEPPH_DRAKE_URL=<url> /drake-install install` |

DRAKE is pure Wolfram Language (~10 MB). No compilation, no other system dependencies. The only prerequisite (Wolfram Engine ≥ 13.1) is already configured at `/usr/local/bin/wolframscript` v14.3.0.

---

## 6. Constraints honored

- No worktree used.
- No git commits made.
- No bypass of the Anubis gate attempted.
- No other tools installed (DRAKE only; Wolfram Engine prereq was already present, not touched).
- No retry on the deterministic Anubis failure.
- Disk-tight warning logged but did not block (DRAKE's ~10 MB fits easily in available 1 GB).
- Time spent: well under budget.
