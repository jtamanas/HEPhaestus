# Install Skill Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the 11 standalone `*-install` skills into shared install references under `_shared/installs/<tool>/` and turn each runner skill into a self-healing preflight. Rewrite `/install` as a bundle front door driven by the same shared scripts.

**Architecture:** Each tool gets a directory `plugins/hep-ph-toolkit/_shared/installs/<tool>/` containing `INSTALL.md` (reference doc, no skill frontmatter), `detect.sh` (cheap config-fast-path then optional binary probe; exit 0 = ready), `install.sh` (returns 0 on success or a documented blocker code), and any helpers (e.g. `_activation_parse.py`). Each runner skill (e.g. `sarah-build`, `formcalc`, `maddm`) prepends a uniform `## Preflight` block that runs `detect.sh` and, on failure, loads the `INSTALL.md` and walks the user through it. `/install` is rewritten to drive the same `_shared/installs/<tool>/{detect,install}.sh` directly, with bundles defined in a table.

**Tech Stack:** bash 3+, POSIX shell, Python 3.10+, plugins/shared/install-helpers for atomic-write/config helpers, pytest for shared-helper tests. No new dependencies.

**Spec:** [docs/superpowers/specs/2026-04-28-install-skill-refactor-design.md](../specs/2026-04-28-install-skill-refactor-design.md)

**Spec note (config path):** the spec text says `~/.config/hephaestus/config.toml`; the actual code uses `~/.config/hephaestus/config.json` (see `plugins/shared/install-helpers/config_helpers.py:41`). All scripts in this plan use `config.json` to match reality. This is a spec typo, not a behavior change.

**Spec note (Wolfram + MG5):** the 11 tools enumerated in the spec do *not* include Wolfram Engine or MG5_aMC. Both stay where they are (`plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh`, `install_mg5.sh`); SARAH's `install.sh` and MadDM's `install.sh` continue to delegate to them as transitive prerequisites. The rewritten `/install` enumerates `_shared/installs/` only.

---

## File Structure

**New plugin-level directory tree:**

```
plugins/hep-ph-toolkit/_shared/installs/
├── README.md                            # one-screen overview of the contract
├── _detect_common.sh                    # shared fast-path helper (config + version check)
├── tests/
│   ├── test_detect_common.sh
│   └── fixtures/
└── <tool>/                              # one per tool (looptools, sarah, ...)
    ├── INSTALL.md                       # reference doc, no skill frontmatter
    ├── detect.sh                        # exit 0 if ready
    ├── install.sh                       # exit 0 on success
    ├── (tool-specific helpers)
    └── tests/
```

**Files modified:**

- Each runner skill `SKILL.md` (gain a `## Preflight` block, drop `/-install` references)
- `plugins/hep-ph-toolkit/skills/install/SKILL.md` (rewritten as bundle front door)
- `plugins/hep-ph-toolkit/skills/install/scripts/demo-install.sh` (delegated to `_shared/installs/<tool>/`)
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` (drop install orchestration)
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py` (drop install probing)
- `CLAUDE.md` (Skill Categories table)
- `README.md` (Skill Categories section)
- `.claude-plugin/marketplace.json` (no per-skill enumeration today; verify nothing breaks)
- `plugins/hep-ph-toolkit/.claude-plugin/plugin.json` (no per-skill enumeration today; verify)

**Files deleted (eleven directories):**

- `plugins/hep-ph-toolkit/skills/{ddcalc,drake,feynarts,feynrules,formcalc,higgstools,looptools,maddm,micromegas,sarah,spheno}-install/`

---

## Phase 1 — Foundation

The shared helper and the directory skeleton land first so per-tool migrations have something to plug into.

### Task 1: Shared detect-fast-path helper — failing test

**Files:**
- Create: `plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh`

This test drives the design of `_detect_common.sh`. It must support: (a) reading a tool entry from `config.json`, (b) checking that `<tool>_path` exists on disk, (c) checking that the recorded `<tool>_version` matches a caller-supplied pinned version, and (d) exiting 0 only when all three pass.

- [ ] **Step 1: Write the failing test**

```bash
# plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
#!/usr/bin/env bash
# Test the shared fast-path helper used by every <tool>/detect.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/../_detect_common.sh"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# Fixture: a fake tool installed at $TMP/install/bin
mkdir -p "$TMP/install/bin"
touch "$TMP/install/bin/footool"
chmod +x "$TMP/install/bin/footool"

write_config() {
  cat >"$XDG_CONFIG_HOME/hephaestus/config.json"
}

# 1) No config → fail (exit non-zero)
echo '{}' | write_config
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: empty config should not pass"; exit 1
fi

# 2) Config registers tool with matching path + version → pass (exit 0)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool", "footool_version": "1.0"}
EOF
if ! bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: matched config should pass"; exit 1
fi

# 3) Path on disk missing → fail
rm "$TMP/install/bin/footool"
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: missing binary should not pass"; exit 1
fi
touch "$TMP/install/bin/footool"; chmod +x "$TMP/install/bin/footool"

# 4) Version drift → fail (forces caller to fall through to slow probe)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool", "footool_version": "0.9"}
EOF
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: version drift should not pass"; exit 1
fi

# 5) Missing version field in config → fail (forces re-verification)
cat <<EOF | write_config
{"footool_path": "$TMP/install/bin/footool"}
EOF
if bash "$HELPER" footool "$TMP/install/bin/footool" 1.0; then
  echo "FAIL: missing version should not pass"; exit 1
fi

echo OK
```

- [ ] **Step 2: Run test to verify it fails**

```bash
bash plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
```

Expected: FAIL — `_detect_common.sh: No such file or directory`.

### Task 2: Shared detect-fast-path helper — implementation

**Files:**
- Create: `plugins/hep-ph-toolkit/_shared/installs/_detect_common.sh`
- Create: `plugins/hep-ph-toolkit/_shared/installs/README.md`

- [ ] **Step 1: Write the helper**

```bash
# plugins/hep-ph-toolkit/_shared/installs/_detect_common.sh
#!/usr/bin/env bash
# detect-fast-path helper used by every _shared/installs/<tool>/detect.sh.
#
# Usage:
#   bash _detect_common.sh <tool> <expected_path> <pinned_version>
#
# Exit 0 iff config.json registers <tool>_path == <expected_path> AND
# <tool>_version == <pinned_version> AND <expected_path> exists on disk.
# Otherwise exit 1 (caller falls through to slow binary probe).
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <tool> <expected_path> <pinned_version>" >&2
  exit 2
fi

tool="$1"
expected_path="$2"
pinned_version="$3"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
[ -f "$cfg" ] || exit 1

# Use python3 for JSON parsing (Python is a hephaestus prereq).
python3 - "$cfg" "$tool" "$expected_path" "$pinned_version" <<'PY' || exit 1
import json, os, sys
cfg_path, tool, expected_path, pinned_version = sys.argv[1:5]
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except Exception:
    sys.exit(1)
got_path = cfg.get(f"{tool}_path")
got_ver  = cfg.get(f"{tool}_version")
if got_path != expected_path:
    sys.exit(1)
if got_ver != pinned_version:
    sys.exit(1)
if not os.path.exists(expected_path):
    sys.exit(1)
sys.exit(0)
PY
```

- [ ] **Step 2: Write the README**

```markdown
# `_shared/installs/`

Reference docs and scripts for every external tool hephaestus drives. Each
`<tool>/` directory carries:

- `INSTALL.md` — what to install, prerequisites, blocker codes, smoke test.
  No skill frontmatter; this is a reference, not an invokable skill.
- `detect.sh` — cheap "is this tool ready" probe. Exit 0 = ready, non-zero =
  not ready. Two-tier: config fast path (~5 ms) then slow binary probe.
- `install.sh` — full installer. Returns 0 on success, documented non-zero
  codes on `activation_required`, `download_failed`, `build_failed`, etc.
  See the per-tool `INSTALL.md` for the code table.
- `tests/` — unit tests for the tool's scripts (kept beside the scripts).

Runner skills (`sarah-build`, `formcalc`, `maddm`, …) `bash detect.sh` at the
top of their `SKILL.md` and, on non-zero exit, load `INSTALL.md` into
context and walk the user through it. `/install` (the bundle front door)
drives the same scripts.

`_detect_common.sh` is the shared config fast-path helper used by every
`<tool>/detect.sh`. See `tests/test_detect_common.sh` for the contract.
```

- [ ] **Step 3: Run the test**

```bash
chmod +x plugins/hep-ph-toolkit/_shared/installs/_detect_common.sh
bash plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add plugins/hep-ph-toolkit/_shared/installs/_detect_common.sh \
        plugins/hep-ph-toolkit/_shared/installs/README.md \
        plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
git commit -m "feat(installs): add _shared/installs scaffold + detect fast-path helper"
```

---

## Phase 2 — Vertical slice: LoopTools

LoopTools is the simplest tool — no Wolfram, no Anubis, no long build. Land the full pattern end-to-end before fanning out.

### Task 3: Move LoopTools install scripts into `_shared/installs/looptools/`

**Files:**
- Move: `plugins/hep-ph-toolkit/skills/looptools-install/scripts/*` → `plugins/hep-ph-toolkit/_shared/installs/looptools/`
- Move: `plugins/hep-ph-toolkit/skills/looptools-install/tests/` → `plugins/hep-ph-toolkit/_shared/installs/looptools/tests/`

- [ ] **Step 1: Create the destination and move files (preserve git history)**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/looptools
git mv plugins/hep-ph-toolkit/skills/looptools-install/scripts/install.sh \
       plugins/hep-ph-toolkit/_shared/installs/looptools/install.sh
git mv plugins/hep-ph-toolkit/skills/looptools-install/scripts/probe_looptools.sh \
       plugins/hep-ph-toolkit/_shared/installs/looptools/probe_looptools.sh
git mv plugins/hep-ph-toolkit/skills/looptools-install/scripts/check_gfortran.sh \
       plugins/hep-ph-toolkit/_shared/installs/looptools/check_gfortran.sh
git mv plugins/hep-ph-toolkit/skills/looptools-install/scripts/_blocker.sh \
       plugins/hep-ph-toolkit/_shared/installs/looptools/_blocker.sh
git mv plugins/hep-ph-toolkit/skills/looptools-install/scripts/b0_test.F \
       plugins/hep-ph-toolkit/_shared/installs/looptools/b0_test.F
git mv plugins/hep-ph-toolkit/skills/looptools-install/tests \
       plugins/hep-ph-toolkit/_shared/installs/looptools/tests
```

- [ ] **Step 2: Fix relative-path references inside moved scripts**

Each script that referenced `../../../../shared/install-helpers/_common.sh` now lives one level shallower. Update the path: it should now be `../../../shared/install-helpers/_common.sh` (only three `../` instead of four, since we drop the `scripts/` layer).

```bash
# Audit which moved files reference _common.sh / atomic_write.sh
grep -rln "../../../../shared/install-helpers" plugins/hep-ph-toolkit/_shared/installs/looptools/
```

For each match, replace `../../../../shared/install-helpers` with `../../../shared/install-helpers`:

```bash
for f in plugins/hep-ph-toolkit/_shared/installs/looptools/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g' "$f"
  rm "$f.bak"
done
```

- [ ] **Step 3: Run the moved tests to confirm they still pass**

```bash
cd plugins/hep-ph-toolkit/_shared/installs/looptools && \
  for t in tests/*.sh tests/*.bats; do [ -f "$t" ] && echo "RUN $t" && bash "$t" 2>&1 | tail -10; done
```

Expected: all green (or, if any tests have hardcoded `skills/looptools-install/scripts/` paths, fail with clear "no such file" — fix them in step 4).

- [ ] **Step 4: Patch any tests that hardcoded the old script path**

```bash
grep -rln "skills/looptools-install" plugins/hep-ph-toolkit/_shared/installs/looptools/tests/ \
  | xargs -I{} sed -i.bak 's|skills/looptools-install/scripts|_shared/installs/looptools|g; s|skills/looptools-install|_shared/installs/looptools|g' {} \
  && find plugins/hep-ph-toolkit/_shared/installs/looptools/tests/ -name '*.bak' -delete
```

Re-run tests; expect green.

- [ ] **Step 5: Commit the relocation**

```bash
git add plugins/hep-ph-toolkit/_shared/installs/looptools/
git commit -m "refactor(installs): move looptools install scripts to _shared/installs/looptools/"
```

### Task 4: Convert `looptools-install/SKILL.md` → `_shared/installs/looptools/INSTALL.md`

**Files:**
- Move: `plugins/hep-ph-toolkit/skills/looptools-install/SKILL.md` → `plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md`

- [ ] **Step 1: Move the file**

```bash
git mv plugins/hep-ph-toolkit/skills/looptools-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
```

- [ ] **Step 2: Strip skill frontmatter and "When to invoke" section**

Open `plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md` and:

1. Delete the YAML frontmatter block from the very first `---` through the second `---` (inclusive), and the blank line after.
2. Delete the `## When to invoke` section and its bullet list (typically 4–6 bullets, until the next `---` or `## Decision flow` heading).
3. Change the H1 from `# /looptools-install` to `# LoopTools — Install Reference`.
4. Anywhere the doc says "this skill" or "/looptools-install", replace with "this reference" or "LoopTools install".
5. Update internal `scripts/<name>` references to `<name>` (since scripts are now flat alongside `INSTALL.md`).

```bash
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
sed -i.bak 's|scripts/check_gfortran.sh|check_gfortran.sh|g; s|scripts/install.sh|install.sh|g; s|scripts/probe_looptools.sh|probe_looptools.sh|g; s|scripts/_blocker.sh|_blocker.sh|g; s|scripts/b0_test.F|b0_test.F|g' plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
rm plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md.bak
```

Then manually edit to drop `## When to invoke` and rewrite the H1.

- [ ] **Step 3: Verify the file renders cleanly**

```bash
head -30 plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
```

Expected: no YAML frontmatter at top, H1 reads `# LoopTools — Install Reference`, no "When to invoke" section.

- [ ] **Step 4: Commit**

```bash
git add plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
git commit -m "refactor(installs): convert looptools SKILL.md to INSTALL.md reference"
```

### Task 5: Add `detect.sh` for LoopTools

**Files:**
- Create: `plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh`

The existing `probe_looptools.sh` is the slow-path binary probe. The new `detect.sh` wraps the fast path then falls through to the probe.

- [ ] **Step 1: Write the failing test**

```bash
# plugins/hep-ph-toolkit/_shared/installs/looptools/tests/test_detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT="$SCRIPT_DIR/../detect.sh"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# 1) No config → exit 1
echo '{}' > "$XDG_CONFIG_HOME/hephaestus/config.json"
if bash "$DETECT"; then echo "FAIL: empty config"; exit 1; fi

# 2) Config registers a path that does not exist on disk → exit 1
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "$TMP/nope", "looptools_version": "2.16"}
EOF
if bash "$DETECT"; then echo "FAIL: missing binary"; exit 1; fi

echo OK
```

- [ ] **Step 2: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh
#!/usr/bin/env bash
# Detect whether LoopTools is installed and registered. Exit 0 if ready.
#
# Two-tier check:
#   1. Config fast path: looptools_path + looptools_version match the pin.
#   2. Slow probe: only if HEPPH_FORCE_PROBE=1 or fast path missed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."

# Pinned version. Bump in lockstep with INSTALL.md.
PINNED_VERSION="${HEPPH_LOOPTOOLS_VERSION:-2.16}"

# Read the recorded path from config without touching disk further.
cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("looptools_path",""))
except Exception: pass' "$cfg")"
fi

# Fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" looptools "$recorded_path" "$PINNED_VERSION"; then
  if [ -z "${HEPPH_FORCE_PROBE:-}" ]; then
    exit 0
  fi
fi

# Slow path: nothing in config, version drift, or HEPPH_FORCE_PROBE=1.
[ -n "$recorded_path" ] || exit 1
bash "$SCRIPT_DIR/probe_looptools.sh" "$recorded_path" >/dev/null 2>&1
```

- [ ] **Step 3: Run the test**

```bash
chmod +x plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh
bash plugins/hep-ph-toolkit/_shared/installs/looptools/tests/test_detect.sh
```

Expected: `OK`.

- [ ] **Step 4: Document the version pin in `INSTALL.md`**

Append a `## Version pin` section near the top of `_shared/installs/looptools/INSTALL.md`:

```markdown
## Version pin

`detect.sh` pins LoopTools to **2.16**. Override with
`HEPPH_LOOPTOOLS_VERSION=x.y`. When this pin bumps, `install.sh` must
remove or migrate the previous install tree (e.g. `~/LoopTools/LoopTools-2.16`
→ `~/LoopTools/LoopTools-<new>`); old version-locked entries in
`init.m` or shell rc files (none for LoopTools) must also be cleaned up.
The new version is only written to `config.json` after the new install
verifies, so a half-finished upgrade does not leave the config pointing
at a stale binary.
```

- [ ] **Step 5: Commit**

```bash
git add plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh \
        plugins/hep-ph-toolkit/_shared/installs/looptools/tests/test_detect.sh \
        plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md
git commit -m "feat(installs/looptools): add detect.sh + version-pin doc"
```

### Task 6: Wire `formcalc` runner preflight to LoopTools (and the other consumers)

LoopTools is consumed by `formcalc` (and indirectly by anything that compiles FormCalc-generated Fortran). Add the preflight block to `formcalc/SKILL.md`.

**Files:**
- Modify: `plugins/hep-ph-toolkit/skills/formcalc/SKILL.md`

- [ ] **Step 1: Inspect the current preflight**

```bash
grep -n "Prerequisites\|formcalc-install\|looptools-install" plugins/hep-ph-toolkit/skills/formcalc/SKILL.md | head
```

- [ ] **Step 2: Add the LoopTools preflight block**

Insert after the existing "Prerequisites" section, before "Subcommands":

```markdown
## Preflight: LoopTools

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh

- **exit 0** → LoopTools is installed and registered in config; proceed.
- **exit non-zero** → LoopTools is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/looptools/INSTALL.md` into
  context and follow it. When the install completes, re-run `detect.sh`
  before proceeding. If it still fails, halt with the blocker code from
  the install reference.
```

(FormCalc itself gets its own preflight in Task 18; that block lives separately.)

- [ ] **Step 3: Drop stale `/looptools-install` references in the error/blocker tables**

```bash
grep -n "looptools-install\|/looptools-install" plugins/hep-ph-toolkit/skills/formcalc/SKILL.md
```

For each hit, replace `/looptools-install` with `_shared/installs/looptools/INSTALL.md`.

- [ ] **Step 4: Commit**

```bash
git add plugins/hep-ph-toolkit/skills/formcalc/SKILL.md
git commit -m "feat(formcalc): self-heal LoopTools dependency via preflight"
```

### Task 7: Delete `skills/looptools-install/`

**Files:**
- Delete: `plugins/hep-ph-toolkit/skills/looptools-install/`

- [ ] **Step 1: Confirm the directory is now empty of unique content**

```bash
ls plugins/hep-ph-toolkit/skills/looptools-install/
```

Expected: only `skill_env.yaml` remains (everything else moved or deleted in Tasks 3–4).

- [ ] **Step 2: Inspect `skill_env.yaml` and decide its fate**

```bash
cat plugins/hep-ph-toolkit/skills/looptools-install/skill_env.yaml
```

If it is generic ("inherits from default"), delete the directory. If it has tool-specific env vars, copy them into `_shared/installs/looptools/INSTALL.md` under a `## Environment` section, then delete.

- [ ] **Step 3: Delete the skill directory**

```bash
git rm -r plugins/hep-ph-toolkit/skills/looptools-install
```

- [ ] **Step 4: Repo-wide grep for stale references**

```bash
grep -rn "looptools-install\|/looptools-install" \
  plugins/ docs/ README.md CLAUDE.md 2>/dev/null \
  | grep -v "docs/superpowers/specs\|docs/superpowers/plans"
```

For each remaining hit (excluding the spec and this plan), replace with `_shared/installs/looptools/INSTALL.md`.

- [ ] **Step 5: Smoke-test the slice end-to-end**

Set up a clean config and confirm `formcalc`'s preflight runs `detect.sh`:

```bash
# Simulated cold start: config exists but lacks looptools_path
TMP="$(mktemp -d)"; XDG_CONFIG_HOME="$TMP/xdg" mkdir -p "$TMP/xdg/hephaestus"
echo '{}' > "$TMP/xdg/hephaestus/config.json"
XDG_CONFIG_HOME="$TMP/xdg" bash plugins/hep-ph-toolkit/_shared/installs/looptools/detect.sh; echo "exit=$?"
```

Expected: `exit=1` (LoopTools not configured — runner will load `INSTALL.md`).

- [ ] **Step 6: Commit the slice**

```bash
git add -A
git commit -m "refactor(installs): delete skills/looptools-install (replaced by _shared/installs/looptools)"
```

---

## Phase 3 — Per-tool migration template (apply to the 8 non-SARAH tools)

Tasks 8–17 each follow the **same six steps** as Tasks 3–7 applied to one tool. Each task below is self-contained: it lists the exact source/destination paths, the new `detect.sh` (where one must be written), and the runners that gain a preflight block.

**Order:** spheno → maddm → micromegas → formcalc → feynarts → feynrules → ddcalc → higgstools → drake. Each is independent; finish one fully (move scripts → INSTALL.md → detect.sh → preflight wiring → delete) before starting the next.

> **Per-tool checklist (always run, in order):**
>
> 1. `git mv` every script under `skills/<tool>-install/scripts/*` → `_shared/installs/<tool>/<script>` (flat).
> 2. `git mv skills/<tool>-install/tests/ → _shared/installs/<tool>/tests/`.
> 3. Patch `../../../../shared/install-helpers` → `../../../shared/install-helpers` in every moved `.sh`/`.py` (one fewer level).
> 4. Patch hardcoded `skills/<tool>-install/scripts/` → `_shared/installs/<tool>/` in tests.
> 5. `git mv skills/<tool>-install/SKILL.md → _shared/installs/<tool>/INSTALL.md`; strip YAML frontmatter and `## When to invoke`; rewrite H1 to `# <Tool> — Install Reference`; replace inline `scripts/<name>` paths with `<name>`.
> 6. Add `detect.sh` if absent (see per-tool note below). Add `## Version pin` section to `INSTALL.md` documenting the pinned version, the env-var override, and the upgrade contract (remove old tree, rewrite dotfiles if any, atomic config update post-verify).
> 7. Add a `## Preflight: <Tool>` block to each runner skill that depends on this tool. Drop stale `/<tool>-install` rows from the runner's error/blocker tables.
> 8. Delete `skills/<tool>-install/`. Repo-wide grep for stale `/<tool>-install` references; rewrite to `_shared/installs/<tool>/INSTALL.md`.
> 9. Run any moved tests; smoke `detect.sh` against a clean `XDG_CONFIG_HOME`.
> 10. Commit.

### Task 8: SPheno migration

**Source scripts:** `_blocker.sh`, `_make_log_parse.py`, `check_gfortran.sh`, `install_spheno.sh`.

**Destination:** `_shared/installs/spheno/`.

**`detect.sh` status:** No standalone detect script exists today; one must be written. The slow probe runs `<spheno>/bin/SPheno --version` (or, if no `--version`, checks for the binary's existence and reads `version.h` in the source tree).

- [ ] **Step 1: Run the per-tool checklist (steps 1–6) for SPheno.** Use:

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/spheno
git mv plugins/hep-ph-toolkit/skills/spheno-install/scripts/install_spheno.sh \
       plugins/hep-ph-toolkit/_shared/installs/spheno/install.sh
git mv plugins/hep-ph-toolkit/skills/spheno-install/scripts/check_gfortran.sh \
       plugins/hep-ph-toolkit/_shared/installs/spheno/check_gfortran.sh
git mv plugins/hep-ph-toolkit/skills/spheno-install/scripts/_blocker.sh \
       plugins/hep-ph-toolkit/_shared/installs/spheno/_blocker.sh
git mv plugins/hep-ph-toolkit/skills/spheno-install/scripts/_make_log_parse.py \
       plugins/hep-ph-toolkit/_shared/installs/spheno/_make_log_parse.py
git mv plugins/hep-ph-toolkit/skills/spheno-install/tests \
       plugins/hep-ph-toolkit/_shared/installs/spheno/tests
git mv plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/spheno/INSTALL.md
for f in plugins/hep-ph-toolkit/_shared/installs/spheno/*.sh \
         plugins/hep-ph-toolkit/_shared/installs/spheno/*.py; do
  [ -f "$f" ] && sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g' "$f" && rm "$f.bak"
done
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/spheno/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/spheno/INSTALL.md.bak
```

Then manually drop the `## When to invoke` block, rewrite the H1, replace inline `scripts/<name>` with `<name>`.

- [ ] **Step 2: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/spheno/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_SPHENO_VERSION:-4.0.5}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("spheno_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" spheno "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
[ -n "$recorded_path" ] || exit 1
# Slow probe: SPheno binary present and runs.
[ -x "$recorded_path/bin/SPheno" ] || exit 1
"$recorded_path/bin/SPheno" --version >/dev/null 2>&1 || \
  [ -f "$recorded_path/version.h" ]
```

- [ ] **Step 3: Wire `spheno-build` preflight**

Add `## Preflight: SPheno` block to `plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` invoking `_shared/installs/spheno/detect.sh`. Drop any `/spheno-install` references in its tables.

- [ ] **Step 4: Delete `skills/spheno-install/`**

```bash
git rm -r plugins/hep-ph-toolkit/skills/spheno-install
```

- [ ] **Step 5: Repo-wide grep + replace**

```bash
grep -rn "spheno-install\|/spheno-install" plugins/ README.md CLAUDE.md 2>/dev/null \
  | grep -v "docs/superpowers/specs\|docs/superpowers/plans\|^\s*#"
```

For each non-spec hit, replace with `_shared/installs/spheno/INSTALL.md`.

(Special note: `lagrangian-builder/SKILL.md` has many `/spheno-install` references. **Do not fix those here** — Task 18 rewrites the entire `lagrangian-builder` install-orchestration block as a single edit. Skip it for now.)

- [ ] **Step 6: Run tests, smoke `detect.sh`, commit**

```bash
bash -n plugins/hep-ph-toolkit/_shared/installs/spheno/detect.sh
chmod +x plugins/hep-ph-toolkit/_shared/installs/spheno/detect.sh
git add -A
git commit -m "refactor(installs): migrate spheno to _shared/installs/spheno"
```

### Task 9: MadDM migration

**Source scripts:** `_blocker.sh`, `install.sh`, `probe_maddm.sh`, plus the carried fixtures `MG5_debug`, `nsqso_born.inc`, `py.py`.

**Destination:** `_shared/installs/maddm/`.

**`detect.sh` status:** Spec §Non-goals lists MadDM as needing genuinely new detect work because install delegates to `MG5_aMC>install maddm` (interactive multi-minute build). The new `detect.sh` must:
- Fast-path: read `maddm_path` + `maddm_version` from config.
- Slow-path: assert `<MG5>/PLUGIN/maddm/maddm_run.py` exists.
- Never trigger an install probe that itself runs MG5 (cost: minutes).

- [ ] **Step 1: Run the per-tool checklist (steps 1–6) for MadDM.**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/maddm
git mv plugins/hep-ph-toolkit/skills/maddm-install/scripts/install.sh \
       plugins/hep-ph-toolkit/_shared/installs/maddm/install.sh
git mv plugins/hep-ph-toolkit/skills/maddm-install/scripts/probe_maddm.sh \
       plugins/hep-ph-toolkit/_shared/installs/maddm/probe_maddm.sh
git mv plugins/hep-ph-toolkit/skills/maddm-install/scripts/_blocker.sh \
       plugins/hep-ph-toolkit/_shared/installs/maddm/_blocker.sh
for fixture in MG5_debug nsqso_born.inc py.py; do
  [ -f "plugins/hep-ph-toolkit/skills/maddm-install/scripts/$fixture" ] && \
    git mv "plugins/hep-ph-toolkit/skills/maddm-install/scripts/$fixture" \
           "plugins/hep-ph-toolkit/_shared/installs/maddm/$fixture"
done
git mv plugins/hep-ph-toolkit/skills/maddm-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/maddm/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/maddm/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/maddm/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/maddm/*.sh; do
  [ -f "$f" ] && sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|scripts/||g' "$f" && rm "$f.bak"
done
```

Manually edit `INSTALL.md` to drop `## When to invoke` and rewrite the H1.

- [ ] **Step 2: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/maddm/detect.sh
#!/usr/bin/env bash
# MadDM detect: cheap. Never invokes MG5 install (it's a multi-minute build).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_MADDM_VERSION:-3.2}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("maddm_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" maddm "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
[ -n "$recorded_path" ] || exit 1
# Slow path: MadDM plugin tree exists. Do NOT call MG5.
[ -f "$recorded_path/maddm_run.py" ] || [ -f "$recorded_path/maddm.py" ]
```

- [ ] **Step 3: Add the `Self-healing UX contract` warning to `INSTALL.md`**

Append:

```markdown
## Self-healing UX contract

`install.sh` invokes `MG5_aMC>install maddm`, which is itself an interactive
multi-minute build (downloads plugin, compiles event-generator scaffolding,
runs MG5 sanity tests). The first runner-driven preflight on a clean
machine therefore triggers a long, visible operation by design. The runner
must:

1. Print a clear "MadDM not installed; this will take ~3–8 minutes" notice
   *before* invoking `install.sh`.
2. Stream `install.sh` output (or its log file) so the user sees progress.
3. Halt with `MADDM_INSTALL_INTERACTIVE_REQUIRED` if the install needs
   interactive input that the runner cannot provide non-interactively.
```

- [ ] **Step 4: Wire `maddm` runner preflight**

Add `## Preflight: MadDM` to `plugins/hep-ph-toolkit/skills/maddm/SKILL.md`. Include the long-run notice from step 3.

- [ ] **Step 5: Delete `skills/maddm-install/`, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/maddm-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/maddm/detect.sh
grep -rn "maddm-install" plugins/ README.md CLAUDE.md 2>/dev/null
# replace each non-spec hit with _shared/installs/maddm/INSTALL.md
git add -A
git commit -m "refactor(installs): migrate maddm to _shared/installs/maddm + long-run UX contract"
```

### Task 10: micrOMEGAs migration

**Source scripts:** `_blocker.sh`, `_macos_env.sh`, `_netguard.sh`, `_patches.sh`, `_smoke.sh`, `check_toolchain.sh`, `detect.sh` (already exists), `install_impl.sh`, `install_micromegas.sh`, `use_path.sh`, `validate.sh`.

**Destination:** `_shared/installs/micromegas/`.

**`detect.sh` status:** already exists in source; reuse. Add the fast-path wrapper at the top.

- [ ] **Step 1: Run the per-tool checklist (steps 1–6) for micrOMEGAs**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/micromegas
for f in _blocker.sh _macos_env.sh _netguard.sh _patches.sh _smoke.sh \
         check_toolchain.sh detect.sh install_impl.sh install_micromegas.sh \
         use_path.sh validate.sh; do
  git mv "plugins/hep-ph-toolkit/skills/micromegas-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/micromegas/$f"
done
# Rename install_micromegas.sh → install.sh for symmetry with other tools
git mv plugins/hep-ph-toolkit/_shared/installs/micromegas/install_micromegas.sh \
       plugins/hep-ph-toolkit/_shared/installs/micromegas/install.sh
git mv plugins/hep-ph-toolkit/skills/micromegas-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/micromegas/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/micromegas/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/micromegas/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/micromegas/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|install_micromegas.sh|install.sh|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Wrap the existing detect.sh in a fast-path**

The existing `detect.sh` does the slow binary probe directly. Rename it `_probe.sh` and write a new `detect.sh`:

```bash
git mv plugins/hep-ph-toolkit/_shared/installs/micromegas/detect.sh \
       plugins/hep-ph-toolkit/_shared/installs/micromegas/_probe.sh
```

```bash
# plugins/hep-ph-toolkit/_shared/installs/micromegas/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_MICROMEGAS_VERSION:-6.0.5}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("micromegas_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" micromegas "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
exec bash "$SCRIPT_DIR/_probe.sh" "$@"
```

Update any callers that invoked the old `detect.sh` to use `_probe.sh` if they wanted the slow probe directly (likely none — `detect.sh` was the public API).

- [ ] **Step 3: Wire `micromegas` runner preflight**

Add `## Preflight: micrOMEGAs` to `plugins/hep-ph-toolkit/skills/micromegas/SKILL.md`. The `dark-matter-constraints` meta-skill stays ignorant — its leaf delegations to `/micromegas` self-heal.

- [ ] **Step 4: Delete `skills/micromegas-install/`, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/micromegas-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/micromegas/detect.sh
grep -rn "micromegas-install" plugins/ README.md CLAUDE.md 2>/dev/null
# replace each non-spec hit
git add -A
git commit -m "refactor(installs): migrate micromegas to _shared/installs/micromegas"
```

### Task 11: FormCalc migration

**Source scripts:** `build_form.sh`, `build_looptools.sh`, `install_formcalc.sh`, `install_formcalc_full.sh`, `probe_formcalc.wls`, `smoke_test.wls`.

**Destination:** `_shared/installs/formcalc/`.

**`detect.sh` status:** None exists; write one. Slow probe runs the `.wls` script via `wolframscript`.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/formcalc
for f in build_form.sh build_looptools.sh install_formcalc_full.sh \
         probe_formcalc.wls smoke_test.wls; do
  git mv "plugins/hep-ph-toolkit/skills/formcalc-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/formcalc/$f"
done
# Rename install_formcalc.sh → install.sh
git mv plugins/hep-ph-toolkit/skills/formcalc-install/scripts/install_formcalc.sh \
       plugins/hep-ph-toolkit/_shared/installs/formcalc/install.sh
git mv plugins/hep-ph-toolkit/skills/formcalc-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/formcalc/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/formcalc/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/formcalc/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/formcalc/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/formcalc/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FORMCALC_VERSION:-9.10}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("formcalc_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" formcalc "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
[ -n "$recorded_path" ] || exit 1
# Slow path: Wolfram-driven probe (cold ~2–6 s).
command -v wolframscript >/dev/null 2>&1 || exit 1
wolframscript -file "$SCRIPT_DIR/probe_formcalc.wls" "$recorded_path" >/dev/null 2>&1
```

- [ ] **Step 3: `formcalc` runner already gained a LoopTools preflight in Task 6**

Add a second preflight block, `## Preflight: FormCalc`, immediately after the LoopTools one. Both must pass before any `reduce` invocation.

- [ ] **Step 4: Delete `skills/formcalc-install/`, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/formcalc-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/formcalc/detect.sh
grep -rn "formcalc-install" plugins/ README.md CLAUDE.md 2>/dev/null
# replace each non-spec hit with _shared/installs/formcalc/INSTALL.md
git add -A
git commit -m "refactor(installs): migrate formcalc to _shared/installs/formcalc"
```

### Task 12: FeynArts migration

**Source scripts:** `_blocker.sh`, `detect_feynarts.sh`, `install_feynarts.sh`, `smoke_test_feynarts.sh`, `use_path_feynarts.sh`.

**Destination:** `_shared/installs/feynarts/`.

**`detect.sh` status:** `detect_feynarts.sh` already exists; rename to `detect.sh` and wrap with fast path.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/feynarts
git mv plugins/hep-ph-toolkit/skills/feynarts-install/scripts/install_feynarts.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/install.sh
git mv plugins/hep-ph-toolkit/skills/feynarts-install/scripts/detect_feynarts.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/_probe.sh
git mv plugins/hep-ph-toolkit/skills/feynarts-install/scripts/smoke_test_feynarts.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/smoke_test.sh
git mv plugins/hep-ph-toolkit/skills/feynarts-install/scripts/use_path_feynarts.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/use_path.sh
git mv plugins/hep-ph-toolkit/skills/feynarts-install/scripts/_blocker.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/_blocker.sh
git mv plugins/hep-ph-toolkit/skills/feynarts-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/feynarts/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/feynarts/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/feynarts/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/feynarts/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|detect_feynarts.sh|_probe.sh|g; s|install_feynarts.sh|install.sh|g; s|smoke_test_feynarts.sh|smoke_test.sh|g; s|use_path_feynarts.sh|use_path.sh|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Write `detect.sh` wrapping `_probe.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/feynarts/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FEYNARTS_VERSION:-3.11}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("feynarts_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" feynarts "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
exec bash "$SCRIPT_DIR/_probe.sh" "$@"
```

- [ ] **Step 3: Wire `feynarts` runner preflight**

Add `## Preflight: FeynArts` to `plugins/hep-ph-toolkit/skills/feynarts/SKILL.md`.

- [ ] **Step 4: Delete, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/feynarts-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/feynarts/detect.sh
grep -rn "feynarts-install" plugins/ README.md CLAUDE.md 2>/dev/null
git add -A
git commit -m "refactor(installs): migrate feynarts to _shared/installs/feynarts"
```

### Task 13: FeynRules migration

**Source scripts:** `_activation_parse.py`, `_blocker.sh`, `check_wolfram_activation.sh`, `detect_wolfram.sh`, `install.sh`, `install_feynrules.sh`, `probe_feynrules.sh`.

**Destination:** `_shared/installs/feynrules/`.

**`detect.sh` status:** None canonical; compose from `probe_feynrules.sh` + Wolfram check.

**Per the spec:** FeynRules has no runner skill today, so **no preflight wiring is added**. The skill will become reachable only via `/install feynrules` and `/install bsm-model-building` after Task 19 lands.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/feynrules
for f in _activation_parse.py _blocker.sh check_wolfram_activation.sh \
         detect_wolfram.sh install_feynrules.sh probe_feynrules.sh; do
  git mv "plugins/hep-ph-toolkit/skills/feynrules-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/feynrules/$f"
done
git mv plugins/hep-ph-toolkit/skills/feynrules-install/scripts/install.sh \
       plugins/hep-ph-toolkit/_shared/installs/feynrules/install.sh
git mv plugins/hep-ph-toolkit/skills/feynrules-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/feynrules/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/feynrules/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/feynrules/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/feynrules/*.sh \
         plugins/hep-ph-toolkit/_shared/installs/feynrules/*.py; do
  [ -f "$f" ] && sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

**Special handling:** `install.sh` and `install_feynrules.sh` may both exist. Determine which is the canonical entrypoint (compare `head -20` of each); rename the canonical one to `install.sh` and remove the duplicate (or keep `install_feynrules.sh` as a helper and delete an empty `install.sh`).

- [ ] **Step 2: Compose `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/feynrules/detect.sh
#!/usr/bin/env bash
# FeynRules detect: requires Wolfram + FeynRules sub-package present.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_FEYNRULES_VERSION:-2.3.49}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("feynrules_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" feynrules "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
[ -n "$recorded_path" ] || exit 1
# Slow path: existing probe.
exec bash "$SCRIPT_DIR/probe_feynrules.sh" "$recorded_path"
```

- [ ] **Step 3: Note the no-runner status in `INSTALL.md`**

Append to `_shared/installs/feynrules/INSTALL.md`:

```markdown
## Status: no runner today

Unlike SARAH, SPheno, etc., FeynRules has no runner skill today. It is
reachable only via `/install feynrules` and `/install bsm-model-building`.
When the rebuilt `lagrangian-builder` lands (out of scope for this
refactor), it will gain a `## Preflight: FeynRules` block following the
same pattern as `sarah-build`.
```

- [ ] **Step 4: Delete, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/feynrules-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/feynrules/detect.sh
grep -rn "feynrules-install" plugins/ README.md CLAUDE.md 2>/dev/null
git add -A
git commit -m "refactor(installs): migrate feynrules to _shared/installs/feynrules (no runner yet)"
```

### Task 14: DDCalc migration

**Source scripts:** `_blocker.sh`, `_probe_url.sh`, `_smoke_test.sh`, `apply_overlay.sh`, `detect_ddcalc.sh`, `install_ddcalc.sh`, `use_path.sh`.

**Destination:** `_shared/installs/ddcalc/`.

**`detect.sh` status:** `detect_ddcalc.sh` exists; rename to `_probe.sh`, wrap with fast path.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/ddcalc
git mv plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/install_ddcalc.sh \
       plugins/hep-ph-toolkit/_shared/installs/ddcalc/install.sh
git mv plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/detect_ddcalc.sh \
       plugins/hep-ph-toolkit/_shared/installs/ddcalc/_probe.sh
for f in _blocker.sh _probe_url.sh _smoke_test.sh apply_overlay.sh use_path.sh; do
  git mv "plugins/hep-ph-toolkit/skills/ddcalc-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/ddcalc/$f"
done
git mv plugins/hep-ph-toolkit/skills/ddcalc-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/ddcalc/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/ddcalc/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/ddcalc/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/ddcalc/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|detect_ddcalc.sh|_probe.sh|g; s|install_ddcalc.sh|install.sh|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Write `detect.sh` (fast-path wrapper)**

```bash
# plugins/hep-ph-toolkit/_shared/installs/ddcalc/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_DDCALC_VERSION:-2.2.0}"
cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("ddcalc_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" ddcalc "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
exec bash "$SCRIPT_DIR/_probe.sh" "$@"
```

- [ ] **Step 3: Wire `ddcalc` runner preflight**

Add `## Preflight: DDCalc` to `plugins/hep-ph-toolkit/skills/ddcalc/SKILL.md`.

- [ ] **Step 4: Delete, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/ddcalc-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/ddcalc/detect.sh
grep -rn "ddcalc-install" plugins/ README.md CLAUDE.md 2>/dev/null
git add -A
git commit -m "refactor(installs): migrate ddcalc to _shared/installs/ddcalc"
```

### Task 15: HiggsTools migration

**Source scripts:** `_blocker.sh`, `cache_sm_reference.py`, `detect_higgstools.sh`, `install_higgstools.sh`, `smoke_test.sh`.

**Destination:** `_shared/installs/higgstools/`.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/higgstools
git mv plugins/hep-ph-toolkit/skills/higgstools-install/scripts/install_higgstools.sh \
       plugins/hep-ph-toolkit/_shared/installs/higgstools/install.sh
git mv plugins/hep-ph-toolkit/skills/higgstools-install/scripts/detect_higgstools.sh \
       plugins/hep-ph-toolkit/_shared/installs/higgstools/_probe.sh
for f in _blocker.sh cache_sm_reference.py smoke_test.sh; do
  git mv "plugins/hep-ph-toolkit/skills/higgstools-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/higgstools/$f"
done
git mv plugins/hep-ph-toolkit/skills/higgstools-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/higgstools/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/higgstools/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/higgstools/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/higgstools/*.sh \
         plugins/hep-ph-toolkit/_shared/installs/higgstools/*.py; do
  [ -f "$f" ] && sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|detect_higgstools.sh|_probe.sh|g; s|install_higgstools.sh|install.sh|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/higgstools/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_HIGGSTOOLS_VERSION:-5.10.2}"
cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("higgstools_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" higgstools "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
exec bash "$SCRIPT_DIR/_probe.sh" "$@"
```

- [ ] **Step 3: Wire `higgstools` runner preflight**

Add `## Preflight: HiggsTools` to `plugins/hep-ph-toolkit/skills/higgstools/SKILL.md`.

- [ ] **Step 4: Delete, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/higgstools-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/higgstools/detect.sh
grep -rn "higgstools-install" plugins/ README.md CLAUDE.md 2>/dev/null
git add -A
git commit -m "refactor(installs): migrate higgstools to _shared/installs/higgstools"
```

### Task 16: DRAKE migration

**Source scripts:** `_blocker.sh`, `check_wolfram.sh`, `install.sh`, `probe_drake.sh`.

**Destination:** `_shared/installs/drake/`.

**Special:** the spec calls out DRAKE's hepforge Anubis bot-protection gate. `install.sh` exits 18 (`manual_download_required`); the runner preflight **must halt rather than self-heal** and surface the manual-download path.

- [ ] **Step 1: Per-tool checklist**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/drake
for f in _blocker.sh check_wolfram.sh install.sh probe_drake.sh; do
  git mv "plugins/hep-ph-toolkit/skills/drake-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/drake/$f"
done
git mv plugins/hep-ph-toolkit/skills/drake-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/drake/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/drake/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/drake/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/drake/*.sh; do
  sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Add explicit Anubis-halt notice in `INSTALL.md`**

Append:

```markdown
## Anubis bot-protection gate

DRAKE is hosted at hepforge behind an Anubis bot-protection challenge that
cannot be solved non-interactively. When `install.sh` hits the gate it
exits **18** (`manual_download_required`) with the manual-download URL in
its blocker payload.

**Runner contract:** `/drake`'s preflight, on `detect.sh` exit non-zero,
runs `install.sh` once. If `install.sh` exits 18, the runner halts with a
clear "open this URL, save the tarball to `~/Downloads/drake-*.zip`, then
re-invoke" message. **The runner does NOT retry, and does NOT self-heal
this exit code.** See the spec §Non-goals caveat.
```

- [ ] **Step 3: Write `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/drake/detect.sh
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_DRAKE_VERSION:-1.1}"
cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("drake_path",""))
except Exception: pass' "$cfg")"
fi
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" drake "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi
[ -n "$recorded_path" ] || exit 1
exec bash "$SCRIPT_DIR/probe_drake.sh" "$recorded_path"
```

- [ ] **Step 4: Wire `drake` runner preflight with explicit manual-download halt**

Add to `plugins/hep-ph-toolkit/skills/drake/SKILL.md`:

```markdown
## Preflight: DRAKE

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/drake/detect.sh

- **exit 0** → DRAKE is installed and registered; proceed.
- **exit non-zero** → load
  `plugins/hep-ph-toolkit/_shared/installs/drake/INSTALL.md` and follow
  it. If `install.sh` exits **18** (`manual_download_required`),
  **halt**: print the manual-download URL from the blocker payload, ask
  the user to download the tarball to `~/Downloads/`, then re-invoke
  `/drake`. Do not retry the install non-interactively.
```

- [ ] **Step 5: Delete, grep, smoke, commit**

```bash
git rm -r plugins/hep-ph-toolkit/skills/drake-install
chmod +x plugins/hep-ph-toolkit/_shared/installs/drake/detect.sh
grep -rn "drake-install" plugins/ README.md CLAUDE.md 2>/dev/null
git add -A
git commit -m "refactor(installs): migrate drake to _shared/installs/drake + Anubis halt contract"
```

---

## Phase 4 — SARAH migration + lagrangian-builder cleanup

This is the most consumer-heavy migration. Multiple skills currently delegate to `/sarah-install`; `lagrangian-builder` orchestrates `/sarah-install` and `/spheno-install` together. Both come out in this phase.

### Task 17: SARAH migration with composite `detect.sh`

**Source scripts:** `_activation_parse.py`, `_blocker.sh`, `check_wolfram_activation.sh`, `detect_wolfram.sh`, `install_sarah.sh`.

**Destination:** `_shared/installs/sarah/`.

**`detect.sh` status:** Spec §Non-goals: SARAH detection today is split across `install_sarah.sh`, `detect_wolfram.sh`, `check_wolfram_activation.sh`, and `_activation_parse.py`, returning `configured | found | missing | activation_required`. The new `detect.sh` must compose:
1. config-read (sarah_path + sarah_version)
2. Wolfram reachability (`detect_wolfram.sh` returns `configured`)
3. Wolfram activation (`check_wolfram_activation.sh` does not return `activation_required`)
4. SARAH version probe (existing helper inside `install_sarah.sh`)

into a single binary exit code (0 = ready, non-zero = not ready).

- [ ] **Step 1: Per-tool checklist (move scripts + INSTALL.md)**

```bash
mkdir -p plugins/hep-ph-toolkit/_shared/installs/sarah
for f in _activation_parse.py _blocker.sh check_wolfram_activation.sh \
         detect_wolfram.sh install_sarah.sh; do
  git mv "plugins/hep-ph-toolkit/skills/sarah-install/scripts/$f" \
         "plugins/hep-ph-toolkit/_shared/installs/sarah/$f"
done
# Rename install_sarah.sh → install.sh
git mv plugins/hep-ph-toolkit/_shared/installs/sarah/install_sarah.sh \
       plugins/hep-ph-toolkit/_shared/installs/sarah/install.sh
git mv plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md \
       plugins/hep-ph-toolkit/_shared/installs/sarah/INSTALL.md
sed -i.bak '/^---$/,/^---$/d' plugins/hep-ph-toolkit/_shared/installs/sarah/INSTALL.md && rm plugins/hep-ph-toolkit/_shared/installs/sarah/INSTALL.md.bak
for f in plugins/hep-ph-toolkit/_shared/installs/sarah/*.sh \
         plugins/hep-ph-toolkit/_shared/installs/sarah/*.py; do
  [ -f "$f" ] && sed -i.bak 's|../../../../shared/install-helpers|../../../shared/install-helpers|g; s|install_sarah.sh|install.sh|g' "$f" && rm "$f.bak"
done
```

Manually drop `## When to invoke`, rewrite H1.

- [ ] **Step 2: Write the composite `detect.sh`**

```bash
# plugins/hep-ph-toolkit/_shared/installs/sarah/detect.sh
#!/usr/bin/env bash
# SARAH detect: composes config-read + Wolfram reachability + activation
# parse + version probe into a single exit code.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED="$SCRIPT_DIR/.."
PINNED_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"

cfg_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hephaestus"
cfg="$cfg_dir/config.json"
recorded_path=""
if [ -f "$cfg" ]; then
  recorded_path="$(python3 -c 'import json,sys
try:
  with open(sys.argv[1]) as f: d=json.load(f)
  print(d.get("sarah_path",""))
except Exception: pass' "$cfg")"
fi

# Tier 1: config fast path
if [ -n "$recorded_path" ] && bash "$SHARED/_detect_common.sh" sarah "$recorded_path" "$PINNED_VERSION"; then
  [ -z "${HEPPH_FORCE_PROBE:-}" ] && exit 0
fi

# Tier 2a: Wolfram reachable
wolfram_status="$(bash "$SCRIPT_DIR/detect_wolfram.sh" 2>/dev/null \
  | python3 -c 'import json,sys
try:
  print(json.load(sys.stdin).get("status",""))
except Exception: pass')"
[ "$wolfram_status" = "configured" ] || exit 1

# Tier 2b: Wolfram activation
activation="$(bash "$SCRIPT_DIR/check_wolfram_activation.sh" 2>/dev/null \
  | python3 -c 'import json,sys
try:
  print(json.load(sys.stdin).get("status",""))
except Exception: pass')"
[ "$activation" != "activation_required" ] || exit 1

# Tier 2c: SARAH path on disk + version probe
[ -n "$recorded_path" ] || exit 1
[ -d "$recorded_path" ] || exit 1
# install.sh exposes a verify_sarah_version() function we reuse via subshell;
# fall back to checking the SARAH/SARAH-<version>/Models directory exists.
[ -d "$recorded_path/Models" ] || [ -d "$recorded_path/SARAH-$PINNED_VERSION/Models" ]
```

- [ ] **Step 3: Smoke `detect.sh`**

```bash
chmod +x plugins/hep-ph-toolkit/_shared/installs/sarah/detect.sh
TMP="$(mktemp -d)"; XDG_CONFIG_HOME="$TMP/xdg" mkdir -p "$TMP/xdg/hephaestus"
echo '{}' > "$TMP/xdg/hephaestus/config.json"
XDG_CONFIG_HOME="$TMP/xdg" bash plugins/hep-ph-toolkit/_shared/installs/sarah/detect.sh
echo "exit=$?"
```

Expected: `exit=1` (no Wolfram configured, fast path fails).

- [ ] **Step 4: Wire `sarah-build` runner preflight**

Add `## Preflight: SARAH` to `plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md`. Drop the existing line "Never invoke if `/sarah-install` has not run". Drop any `/sarah-install` references in the error/blocker tables.

- [ ] **Step 5: Delete `skills/sarah-install/`, grep, smoke**

```bash
git rm -r plugins/hep-ph-toolkit/skills/sarah-install
grep -rn "sarah-install" plugins/ README.md CLAUDE.md 2>/dev/null \
  | grep -v "docs/superpowers/specs\|docs/superpowers/plans"
```

`lagrangian-builder/SKILL.md` will still have many hits — that's Task 18.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(installs): migrate sarah to _shared/installs/sarah with composite detect.sh"
```

### Task 18: `lagrangian-builder` cleanup

**Files:**
- Modify: `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md`
- Modify: `plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py`

The spec lists exactly which lines/blocks to rip out:
- `check_state.py`'s install-state probing (the install_status / wolfram_status fields)
- The Step 2 sub-skill orchestration block (lines 78, 162, 170, 179–193, 736–738, 807–832 per the spec)
- The "Sub-skill: SARAH install" footer reference
- The equivalent SPheno block

The replacement is one line per tool: "Step 2: invoke `/sarah-build` (it self-heals if SARAH/Wolfram missing)." Same for SPheno.

- [ ] **Step 1: Print the current orchestration sections so the engineer can see what's being removed**

```bash
sed -n '70,200p' plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md
sed -n '700,840p' plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md
```

- [ ] **Step 2: Remove the Step 2 sub-skill orchestration block**

Open `lagrangian-builder/SKILL.md`. Replace the entire orchestration block — from the line that introduces `## Step 2: Install SARAH if missing` (around line 162 in the current file) through the end of `## Step 4: Install SPheno if missing` (around line 305) — with this concise block:

```markdown
## Step 2: Ensure SARAH is ready

Invoke `/sarah-build`. Its preflight runs
`_shared/installs/sarah/detect.sh` and, if SARAH or Wolfram are missing,
loads `_shared/installs/sarah/INSTALL.md` and walks the user through
the install. `lagrangian-builder` carries no install logic of its own.

## Step 3: Render the SARAH model and run

Continue with `/sarah-build`'s `render` and `run` subcommands as before.

## Step 4: Ensure SPheno is ready

Invoke `/spheno-build`. Same self-healing contract as Step 2.
```

(Adjust step numbers in the rest of the doc — the original Step 5+ become Step 5+ unchanged.)

- [ ] **Step 3: Remove the `Sub-skill: SARAH install` and `Sub-skill: SPheno install` rows from the footer reference table (around line 901–903)**

```bash
grep -n "Sub-skill: SARAH install\|Sub-skill: SPheno install" \
  plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md
```

Delete each matching row.

- [ ] **Step 4: Remove the `WOLFRAM_KERNEL_ABSENT`, `SARAH_DOWNLOAD_FAILED`, `SARAH_SMOKE_TEST_FAILED`, `GFORTRAN_ABSENT`, `SPHENO_BASE_BUILD_FAILED` rows from the error table (lines 736–743)**

These all pointed to deleted skills. Remove the table rows; if other skills genuinely need to surface these errors, they can refer to `_shared/installs/<tool>/INSTALL.md`.

- [ ] **Step 5: Strip install probing from `check_state.py`**

Open `plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py`. Remove anything that probes SARAH/SPheno/Wolfram install state (the `sarah_install`, `spheno_install`, `wolfram_status` fields and their helper functions). What remains is the model-registration probe and any spec validation. If after stripping the file is empty or near-empty, delete it and the table-row reference at line 870 of `SKILL.md`.

- [ ] **Step 6: Run any existing lagrangian-builder tests**

```bash
find plugins/hep-ph-toolkit/skills/lagrangian-builder/tests -name 'test_*.py' -o -name 'test_*.sh' | head
# If pytest is available:
python3 -m pytest plugins/hep-ph-toolkit/skills/lagrangian-builder/tests -x -q 2>&1 | tail -20
```

If tests fail because they reference the dropped install probes, update the tests to match the new (smaller) `check_state.py` API.

- [ ] **Step 7: Commit**

```bash
git add plugins/hep-ph-toolkit/skills/lagrangian-builder/
git commit -m "refactor(lagrangian-builder): drop install orchestration; runners self-heal"
```

---

## Phase 5 — Rewrite `/install` as a bundle front door

### Task 19: New `/install` orchestrator script

**Files:**
- Create: `plugins/hep-ph-toolkit/skills/install/scripts/bundle_install.sh`
- Create: `plugins/hep-ph-toolkit/skills/install/scripts/bundles.json`
- Create: `plugins/hep-ph-toolkit/skills/install/scripts/tests/test_bundle_resume.sh`
- Modify: `plugins/hep-ph-toolkit/skills/install/SKILL.md`
- Delete (after verification): `plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh`, `install_spheno.sh` (duplicates of `_shared/installs/<tool>/install.sh`)
- Keep: `plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh`, `install_mg5.sh` (transitive prereqs, not in `_shared/installs/`)

- [ ] **Step 1: Write the bundle definition file**

```json
// plugins/hep-ph-toolkit/skills/install/scripts/bundles.json
{
  "profumo-paper": {
    "description": "Reproduce arXiv:2506.19062 end-to-end (relic + DD + ID + one-loop).",
    "tools": ["sarah", "spheno", "maddm", "micromegas", "looptools", "formcalc"]
  },
  "dm-relic": {
    "description": "DM relic density (Ωh²): MadDM primary, micrOMEGAs validator.",
    "tools": ["maddm", "micromegas"]
  },
  "dm-direct-detection": {
    "description": "DM direct-detection cross-sections + DDCalc likelihood.",
    "tools": ["micromegas", "ddcalc"]
  },
  "dm-indirect": {
    "description": "DM indirect-detection (γ-ray, ν, e+) — MadDM driver.",
    "tools": ["maddm"]
  },
  "one-loop": {
    "description": "One-loop scalar/tensor integrals (LoopTools + FormCalc + FeynArts).",
    "tools": ["looptools", "formcalc", "feynarts"]
  },
  "bsm-model-building": {
    "description": "BSM Lagrangian → spectrum + decays. SARAH primary; FeynRules optional.",
    "tools": ["sarah", "spheno", "feynrules"]
  }
}
```

- [ ] **Step 2: Write the failing resume-test fixture**

```bash
# plugins/hep-ph-toolkit/skills/install/scripts/tests/test_bundle_resume.sh
#!/usr/bin/env bash
# Verify bundle resumption is detect-driven, not state-stored:
# pre-populate config with N-1 tools registered + on-disk; the bundle
# loop must invoke install.sh ONLY for the missing tool.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCH="$SCRIPT_DIR/../bundle_install.sh"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$XDG_CONFIG_HOME/hephaestus"

# Stub install.sh / detect.sh trees.
STUB_INSTALLS="$TMP/installs"
mkdir -p "$STUB_INSTALLS/looptools" "$STUB_INSTALLS/formcalc" "$STUB_INSTALLS/feynarts"
TOUCH_LOG="$TMP/installs.log"

for tool in looptools formcalc feynarts; do
  cat > "$STUB_INSTALLS/$tool/detect.sh" <<EOF
#!/usr/bin/env bash
[ -f "\$XDG_CONFIG_HOME/hephaestus/config.json" ] || exit 1
python3 -c 'import json,sys
with open(sys.argv[1]) as f:d=json.load(f)
sys.exit(0 if d.get("${tool}_path") else 1)' "\$XDG_CONFIG_HOME/hephaestus/config.json"
EOF
  cat > "$STUB_INSTALLS/$tool/install.sh" <<EOF
#!/usr/bin/env bash
echo "INSTALLED $tool" >> "$TOUCH_LOG"
python3 -c 'import json,sys,os
p=sys.argv[1]
d={}
if os.path.exists(p):
  with open(p) as f:d=json.load(f)
d["${tool}_path"]="/fake/$tool"
d["${tool}_version"]="0"
with open(p,"w") as f:json.dump(d,f)' "\$XDG_CONFIG_HOME/hephaestus/config.json"
EOF
  chmod +x "$STUB_INSTALLS/$tool/detect.sh" "$STUB_INSTALLS/$tool/install.sh"
done

# Pre-populate config with looptools + formcalc; leave feynarts missing.
cat > "$XDG_CONFIG_HOME/hephaestus/config.json" <<EOF
{"looptools_path": "/fake/looptools", "formcalc_path": "/fake/formcalc"}
EOF

HEPPH_INSTALLS_ROOT="$STUB_INSTALLS" bash "$ORCH" \
  --tools looptools,formcalc,feynarts >/dev/null

# Only feynarts should have been installed.
INSTALLED="$(cat "$TOUCH_LOG" 2>/dev/null || true)"
if [ "$INSTALLED" != "INSTALLED feynarts" ]; then
  echo "FAIL: expected only feynarts; got [$INSTALLED]"; exit 1
fi
echo OK
```

Run it: `bash plugins/hep-ph-toolkit/skills/install/scripts/tests/test_bundle_resume.sh` → FAIL (no `bundle_install.sh` yet).

- [ ] **Step 3: Write `bundle_install.sh`**

```bash
# plugins/hep-ph-toolkit/skills/install/scripts/bundle_install.sh
#!/usr/bin/env bash
# /install bundle orchestrator. Drives _shared/installs/<tool>/{detect,install}.sh
# directly. No sub-skill dispatching.
#
# Usage:
#   bundle_install.sh --bundle <name>
#   bundle_install.sh --tool <name>
#   bundle_install.sh --tools <a,b,c>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLS_ROOT="${HEPPH_INSTALLS_ROOT:-$(cd "$SCRIPT_DIR/../../../_shared/installs" && pwd)}"
BUNDLES_FILE="$SCRIPT_DIR/bundles.json"

usage() { echo "usage: $0 [--bundle <name>] [--tool <name>] [--tools a,b,c]" >&2; exit 2; }

mode=""; arg=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) mode=bundle; arg="$2"; shift 2;;
    --tool)   mode=tool;   arg="$2"; shift 2;;
    --tools)  mode=tools;  arg="$2"; shift 2;;
    -h|--help) usage;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
[ -n "$mode" ] || usage

resolve_tools() {
  case "$mode" in
    bundle) python3 -c 'import json,sys
with open(sys.argv[1]) as f:b=json.load(f)
if sys.argv[2] not in b:
  sys.stderr.write("unknown bundle: "+sys.argv[2]+"\n");sys.exit(2)
print(",".join(b[sys.argv[2]]["tools"]))' "$BUNDLES_FILE" "$arg";;
    tool)  echo "$arg";;
    tools) echo "$arg";;
  esac
}

tools_csv="$(resolve_tools)"
IFS=',' read -ra tools <<<"$tools_csv"

for tool in "${tools[@]}"; do
  detect="$INSTALLS_ROOT/$tool/detect.sh"
  install="$INSTALLS_ROOT/$tool/install.sh"
  if [ ! -x "$detect" ] || [ ! -x "$install" ]; then
    echo "ERROR: missing scripts for tool '$tool' under $INSTALLS_ROOT/$tool/" >&2
    exit 3
  fi
  if bash "$detect" >/dev/null 2>&1; then
    echo "✓ $tool already installed"
    continue
  fi
  echo "→ installing $tool"
  if ! bash "$install"; then
    code=$?
    echo "✗ $tool install failed (exit $code) — see $INSTALLS_ROOT/$tool/INSTALL.md" >&2
    exit "$code"
  fi
  if ! bash "$detect" >/dev/null 2>&1; then
    echo "✗ $tool: install.sh exited 0 but detect.sh still fails — see INSTALL.md" >&2
    exit 4
  fi
  echo "✓ $tool installed"
done
echo "all tools ready"
```

- [ ] **Step 4: Run the resume test**

```bash
chmod +x plugins/hep-ph-toolkit/skills/install/scripts/bundle_install.sh
bash plugins/hep-ph-toolkit/skills/install/scripts/tests/test_bundle_resume.sh
```

Expected: `OK`.

- [ ] **Step 5: Rewrite `install/SKILL.md`**

Replace the entire `## Tool directory` and `## Bundle flow` sections with a concise table + invocation contract:

```markdown
## Bundles

| Bundle              | Tools                                                  |
|---------------------|--------------------------------------------------------|
| profumo-paper       | sarah, spheno, maddm, micromegas, looptools, formcalc  |
| dm-relic            | maddm, micromegas                                      |
| dm-direct-detection | micromegas, ddcalc                                     |
| dm-indirect         | maddm                                                  |
| one-loop            | looptools, formcalc, feynarts                          |
| bsm-model-building  | sarah, spheno, feynrules                               |

## Invocation

```
# Bundle:
bash scripts/bundle_install.sh --bundle profumo-paper

# Single tool (matches today's /sarah-install mental model):
bash scripts/bundle_install.sh --tool sarah

# Ad-hoc tool list:
bash scripts/bundle_install.sh --tools looptools,formcalc
```

For each tool, the loop:
1. Runs `_shared/installs/<tool>/detect.sh`. Exit 0 → skip.
2. Otherwise runs `_shared/installs/<tool>/install.sh`. On `activation_required`
   (Wolfram, exit code documented in `_shared/installs/sarah/INSTALL.md`) or
   `manual_download_required` (DRAKE Anubis, exit 18, see
   `_shared/installs/drake/INSTALL.md`), the bundle halts and the user
   resumes by re-invoking the same command — already-installed tools
   pass `detect.sh` on the second pass and are skipped.

## Tools (by directory)

The available tools are exactly the directories under
`plugins/hep-ph-toolkit/_shared/installs/`. There is no separate
hardcoded enumeration. Wolfram Engine and MG5_aMC are NOT in
`_shared/installs/`; they are transitive prerequisites pulled in by SARAH
(`_shared/installs/sarah/install.sh` → `install_wolfram.sh`) and MadDM
(`_shared/installs/maddm/install.sh` → `install_mg5.sh`).
```

Strip the obsolete `## Disk footprint`, `## Per-tool installers`, and `## Wolfram walkthrough` sections — their content lives in the per-tool `INSTALL.md` files now. Keep any top-level disclaimer / safety notes.

- [ ] **Step 6: Audit and clean up `install/scripts/` for now-duplicate scripts**

```bash
# Compare install/scripts/install_sarah.sh vs _shared/installs/sarah/install.sh
diff plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh \
     plugins/hep-ph-toolkit/_shared/installs/sarah/install.sh | head -40
diff plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh \
     plugins/hep-ph-toolkit/_shared/installs/spheno/install.sh | head -40
```

If the `_shared/installs/<tool>/install.sh` is feature-complete (likely yes — it was the canonical per-skill installer), delete the duplicate in `install/scripts/`:

```bash
git rm plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh \
       plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh
```

If the duplicates differ in behavior (e.g. install/scripts version had additional bundle-context logic), reconcile manually — the safest path is to call the canonical script and pass any extra flags as args.

- [ ] **Step 7: Audit `demo-install.sh` and `_common.sh`**

```bash
grep -n "install_sarah\|install_spheno" plugins/hep-ph-toolkit/skills/install/scripts/*.sh
```

Update `demo-install.sh` so that for any tool in `_shared/installs/`, it delegates via `bundle_install.sh --tool <name>` rather than calling the legacy per-tool script. Wolfram and MG5 (which remain in `install/scripts/`) keep their existing direct-call paths.

- [ ] **Step 8: Commit**

```bash
git add plugins/hep-ph-toolkit/skills/install/
git commit -m "feat(install): rewrite as bundle front door driven by _shared/installs/<tool>"
```

---

## Phase 6 — Repo-wide cleanup

### Task 20: Update `CLAUDE.md` and `README.md` Skill Categories

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `plugins/hep-ph-toolkit/.claude-plugin/plugin.json` (only if it enumerates skills — it currently does not)
- Modify: `.claude-plugin/marketplace.json` (only if it enumerates skills — it currently does not)

- [ ] **Step 1: Update the Skill Categories table in `CLAUDE.md`**

Drop every `*-install` entry from the table. The current rows that need editing:

- "Feynman / amplitudes" — drop `feynarts-install`, `formcalc-install`
- "BSM model building" — drop `feynrules-install`, `looptools-install`, `sarah-install`, `spheno-install`
- "Constraints" — drop `ddcalc-install`, `higgstools-install`, `micromegas-install`
- "Monte Carlo" — drop `drake-install`, `maddm-install`

Then add a new row **above** the Onboarding row:

```markdown
| Installs (reference) | `_shared/installs/<tool>/` for {ddcalc, drake, feynarts, feynrules, formcalc, higgstools, looptools, maddm, micromegas, sarah, spheno} — driven by runners and `/install` |
```

- [ ] **Step 2: Make the matching update in `README.md`**

```bash
grep -n "Skill Categories\|feynarts-install\|sarah-install\|spheno-install" README.md | head
```

Edit each row of the README's Skill Categories section identically to step 1.

- [ ] **Step 3: Verify manifests don't enumerate the deleted skills**

```bash
grep -n "ddcalc-install\|drake-install\|feynarts-install\|feynrules-install\|formcalc-install\|higgstools-install\|looptools-install\|maddm-install\|micromegas-install\|sarah-install\|spheno-install" \
  .claude-plugin/marketplace.json plugins/hep-ph-toolkit/.claude-plugin/plugin.json
```

Expected: zero matches (the manifests describe the plugin at a high level, not per-skill). If any match, remove that line/tag.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md README.md plugins/hep-ph-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "docs: drop *-install skill names from categories; reference _shared/installs"
```

### Task 21: Final repo-wide grep + smoke

**Files:**
- Read-only: every file under `plugins/`, `docs/` (excluding spec + this plan), `README.md`, `CLAUDE.md`

- [ ] **Step 1: Run a clean repo-wide grep**

```bash
grep -rn "/sarah-install\|/spheno-install\|/looptools-install\|/formcalc-install\|/feynarts-install\|/feynrules-install\|/maddm-install\|/micromegas-install\|/ddcalc-install\|/higgstools-install\|/drake-install" \
  plugins/ docs/ README.md CLAUDE.md 2>/dev/null \
  | grep -v "docs/superpowers/specs/2026-04-28-install-skill-refactor-design\|docs/superpowers/plans/2026-04-29-install-skill-refactor"
```

Expected: zero hits.

- [ ] **Step 2: Confirm every runner SKILL.md has its preflight block**

```bash
for skill in sarah-build spheno-build maddm micromegas formcalc feynarts ddcalc higgstools drake; do
  echo -n "$skill: "
  grep -l "## Preflight" plugins/hep-ph-toolkit/skills/$skill/SKILL.md >/dev/null \
    && echo "OK" || echo "MISSING"
done
```

Expected: all `OK`.

- [ ] **Step 3: Confirm every `_shared/installs/<tool>/` has the four required files**

```bash
for tool in ddcalc drake feynarts feynrules formcalc higgstools looptools maddm micromegas sarah spheno; do
  for f in INSTALL.md detect.sh install.sh; do
    [ -e "plugins/hep-ph-toolkit/_shared/installs/$tool/$f" ] \
      || echo "MISSING: $tool/$f"
  done
done
```

Expected: zero output.

- [ ] **Step 4: Run every `_shared/installs/<tool>/detect.sh` against an empty config**

```bash
TMP="$(mktemp -d)"; export XDG_CONFIG_HOME="$TMP/xdg"
mkdir -p "$TMP/xdg/hephaestus"; echo '{}' > "$TMP/xdg/hephaestus/config.json"
for tool in ddcalc drake feynarts feynrules formcalc higgstools looptools maddm micromegas sarah spheno; do
  bash plugins/hep-ph-toolkit/_shared/installs/$tool/detect.sh >/dev/null 2>&1 \
    && echo "UNEXPECTED PASS: $tool" \
    || echo "$tool: not-ready (correct)"
done
```

Expected: every line says `not-ready (correct)` (no tool should report ready against a blank config).

- [ ] **Step 5: Run all moved tests**

```bash
for d in plugins/hep-ph-toolkit/_shared/installs/*/tests; do
  [ -d "$d" ] || continue
  echo "=== $d ==="
  for t in "$d"/test_*.sh; do
    [ -f "$t" ] && bash "$t" 2>&1 | tail -3
  done
done
bash plugins/hep-ph-toolkit/_shared/installs/tests/test_detect_common.sh
bash plugins/hep-ph-toolkit/skills/install/scripts/tests/test_bundle_resume.sh
```

Expected: every test ends with `OK` (or its native pass marker).

- [ ] **Step 6: Update the spec status to `Implemented`**

```bash
sed -i.bak '0,/\*\*Status:\*\* Design.*/s||**Status:** Implemented (2026-04-29)|' docs/superpowers/specs/2026-04-28-install-skill-refactor-design.md
rm docs/superpowers/specs/2026-04-28-install-skill-refactor-design.md.bak
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "chore(installs): final repo-wide cleanup; mark spec implemented"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Tasks |
|--------------|-------|
| §1 Layout (`_shared/installs/<tool>/` skeleton) | Tasks 1, 2, then per-tool 3–17 |
| §2 Preflight contract (`detect.sh`, `install.sh`, `INSTALL.md`) | Tasks 1, 2 (foundation); per-tool tasks add a `## Version pin` section |
| §2 Cache & version hygiene | Embedded in each tool's `## Version pin` section + `_detect_common.sh` enforcing version-match |
| §3 Per-tool migration checklist (six steps) | Tasks 3–7 (looptools); 8–17 (the other 10) |
| §3 Repo-wide cleanup | Tasks 20, 21 (CLAUDE.md, README, marketplace.json, plugin.json, lagrangian-builder is Task 18) |
| §3 Order of work (looptools first, SARAH last) | Task ordering matches: looptools 3–7, then 8–16, SARAH 17, lagrangian 18 |
| §4 `/install` rewrite + bundle execution loop | Task 19 (`bundle_install.sh` + `bundles.json` + resume test) |
| §4 Test fixture for resume | Task 19 step 2 (`test_bundle_resume.sh`) |
| §Caveats: SARAH composite detect, DRAKE Anubis halt, MadDM long-run | SARAH detect.sh in Task 17 step 2; DRAKE halt in Task 16 step 2/4; MadDM long-run notice in Task 9 step 3 |
| §FeynRules has no runner | Called out in Task 13 step 3 (status note in INSTALL.md, no preflight wired) |

**Placeholder scan:** every step contains either an exact command, an exact file path, or a complete code block. Per-tool steps in Tasks 8–17 are mechanically explicit (full `git mv` lists, full `detect.sh` source); the only deliberate "manual edit" steps are H1 rewrites and dropping the `## When to invoke` section, which are unambiguous string operations on the file just listed. No "TBD" or "TODO" strings.

**Type/path consistency:**
- All runner skills use the same path scheme `plugins/hep-ph-toolkit/_shared/installs/<tool>/{detect,install}.sh`.
- All `detect.sh` scripts use the same fast-path call signature `bash "$SHARED/_detect_common.sh" <tool> <expected_path> <pinned_version>`.
- All version env-var overrides follow `HEPPH_<TOOL>_VERSION`.
- The `bundle_install.sh` script in Task 19 step 3 reads from `INSTALLS_ROOT="${HEPPH_INSTALLS_ROOT:-...}"`, and the test in step 2 sets `HEPPH_INSTALLS_ROOT` accordingly — consistent.
- Config field names follow `<tool>_path` and `<tool>_version` everywhere (matches existing `config_helpers.py` convention).

Plan is internally consistent and covers the spec.
