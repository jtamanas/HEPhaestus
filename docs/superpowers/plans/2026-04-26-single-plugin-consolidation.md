# Single-Plugin Consolidation Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the 11 category plugins under `plugins/` into a single plugin `hep-ph-toolkit` while preserving every skill, hook, script, shared helper, test, and cross-reference.

**Architecture:**
- Create `plugins/hep-ph-toolkit/` with one manifest, one `skills/` tree containing the union of all 47 functional skills (no name collisions verified — only `_shared` repeats across plugins).
- Merge the four per-plugin `skills/_shared/` directories into one. Existing cross-plugin symlinks (`plugins/{constraints,feynman-diagrams}/skills/_shared/blocker.schema.json` → model-building) collapse naturally; the obsolete symlink-validation test is removed.
- Merge the three identical `hooks/hooks.json` files and the three near-identical `scripts/install-followup.sh` files into one hook + one script with a unioned `INSTALL_SKILLS_REGEX` covering every `*-install` skill across the merged plugin.
- Rewrite cross-plugin references with a Python rewriter (NOT sed) that handles BOTH the slash-form (`plugins/<oldname>/skills/...`) AND the pathlib split-form (`"plugins" / "<oldname>"`, `_plugins / "<oldname>"`) found extensively in `*.py`. Scope: every file under `plugins/`, plus top-level docs (`README.md`, `ROADMAP.md`, `FOLLOWUPS.md`, `workflow_work.md`), plus `tools/tests/`. Excludes `.git/`, `.shift-manager/`, `.claude/`, `demo_output/` (historical state).
- Replace `.claude-plugin/marketplace.json` with a single-entry index. Delete the 11 old plugin directories. Leave `plugins/shared/` untouched.

**Tech Stack:** bash, `git mv`, `find`, Python 3 (rewriter + JSON/YAML validation), `pytest`.

---

## Preconditions

- Working tree currently has ~1800 modified/deleted files (mostly `.shift-manager/run-*` deletions). Stash before starting so refactor commits are reviewable.
- All work happens on branch `refactor/single-plugin`, branched off `main`.
- Execute from `/Users/yianni/Projects/hep-ph-agents`.

---

## Task 0: Branch, stash, baseline

**Files:** none (git state only)

- [ ] **Step 1: Stash existing working-tree drift**

```bash
git stash push -u -m "pre-single-plugin-refactor stash"
```

Expected: stash created; `git status` reports clean tree.

- [ ] **Step 2: Verify clean tree**

```bash
git status --short
```

Expected: empty output.

- [ ] **Step 3: Create feature branch**

```bash
git checkout -b refactor/single-plugin
```

Expected: switched to new branch.

- [ ] **Step 4: Snapshot baseline test collection (names, not just count)**

```bash
mkdir -p /tmp/refactor
pytest --collect-only -q 2>&1 | grep -E '::' | sort > /tmp/refactor/pre_collect.txt
wc -l /tmp/refactor/pre_collect.txt
```

Expected: prints number of test items. Save the count.

- [ ] **Step 5: Snapshot baseline run (non-gated tests only)**

```bash
pytest -q -m "not smoke and not integration" --no-header 2>&1 | tail -5 | tee /tmp/refactor/pre_run.txt
```

Expected: a pass/fail summary. Record passed/failed counts.

- [ ] **Step 6: Empty marker commit**

```bash
git commit --allow-empty -m "refactor: start single-plugin consolidation"
```

---

## Task 1: Create the new plugin skeleton

**Files:**
- Create: `plugins/hep-ph-toolkit/.claude-plugin/plugin.json`
- Create: `plugins/hep-ph-toolkit/skills/.gitkeep`
- Create: `plugins/hep-ph-toolkit/hooks/.gitkeep`
- Create: `plugins/hep-ph-toolkit/scripts/.gitkeep`

- [ ] **Step 1: Create directories**

```bash
mkdir -p plugins/hep-ph-toolkit/.claude-plugin \
         plugins/hep-ph-toolkit/skills \
         plugins/hep-ph-toolkit/hooks \
         plugins/hep-ph-toolkit/scripts
```

- [ ] **Step 2: Write the plugin manifest**

Create `plugins/hep-ph-toolkit/.claude-plugin/plugin.json` with:

```json
{
  "name": "hep-ph-toolkit",
  "description": "All-in-one toolkit for high-energy physics phenomenology — Feynman diagrams, amplitudes, BSM model building, RGE, dark-matter constraints, Higgs bounds, Monte Carlo event generation (MadGraph/MadDM/micrOMEGAs/DRAKE/Pythia), ROOT analysis, plotting, LaTeX paper drafting, arXiv research, plus workflow skills for model-to-tool routing and analytic-exception detection.",
  "version": "0.1.0"
}
```

Note: do NOT add a `skills` array — Claude Code auto-discovers skills under `skills/`. The old `workflow/.claude-plugin/plugin.json` listed skills explicitly; we drop that pattern for consistency.

- [ ] **Step 3: Add `.gitkeep` placeholders**

```bash
touch plugins/hep-ph-toolkit/skills/.gitkeep \
      plugins/hep-ph-toolkit/hooks/.gitkeep \
      plugins/hep-ph-toolkit/scripts/.gitkeep
```

- [ ] **Step 4: Verify manifest parses**

```bash
python3 -c "import json; json.load(open('plugins/hep-ph-toolkit/.claude-plugin/plugin.json'))"
```

Expected: no output (success).

- [ ] **Step 5: Commit**

```bash
git add plugins/hep-ph-toolkit
git commit -m "refactor(toolkit): create hep-ph-toolkit plugin skeleton"
```

---

## Task 2: Move skills from the eight non-`_shared` plugins

**Files:**
- Move: `plugins/{arxiv-research,collider-pheno,hep-data-analysis,hep-plotting,latex-hep,workflow,monte-carlo-tools}/skills/*` → `plugins/hep-ph-toolkit/skills/`
- Move: `plugins/hep-ph-demo/skills/*` EXCEPT `_shared/` → `plugins/hep-ph-toolkit/skills/`

These eight source plugins have no `_shared/` skill collisions to worry about.

- [ ] **Step 1: List all skills, sanity-check no duplicate names**

```bash
find plugins -mindepth 3 -maxdepth 3 -type d -path '*/skills/*' \
  | awk -F/ '{print $NF}' | sort | uniq -c | sort -rn | head -10
```

Expected: only `_shared` appears more than once (4 times). Every other skill name is unique.

- [ ] **Step 2: Move skills from arxiv-research**

```bash
git mv plugins/arxiv-research/skills/arxiv-search plugins/hep-ph-toolkit/skills/
git mv plugins/arxiv-research/skills/literature-review plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 3: Move skills from collider-pheno**

```bash
git mv plugins/collider-pheno/skills/cross-section plugins/hep-ph-toolkit/skills/
git mv plugins/collider-pheno/skills/signal-background plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 4: Move skills from hep-data-analysis**

```bash
git mv plugins/hep-data-analysis/skills/root-analysis plugins/hep-ph-toolkit/skills/
git mv plugins/hep-data-analysis/skills/statistical-tools plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 5: Move skills from hep-plotting**

```bash
git mv plugins/hep-plotting/skills/exclusion-contour plugins/hep-ph-toolkit/skills/
git mv plugins/hep-plotting/skills/hep-plot plugins/hep-ph-toolkit/skills/
git mv plugins/hep-plotting/skills/theory-data-comparison plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 6: Move skills from latex-hep**

```bash
git mv plugins/latex-hep/skills/feynman-tikz plugins/hep-ph-toolkit/skills/
git mv plugins/latex-hep/skills/hep-paper-draft plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 7: Move skills from workflow**

```bash
git mv plugins/workflow/skills/analytic-exception-detector plugins/hep-ph-toolkit/skills/
git mv plugins/workflow/skills/model-router plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 8: Move skills from monte-carlo-tools**

```bash
git mv plugins/monte-carlo-tools/skills/drake plugins/hep-ph-toolkit/skills/
git mv plugins/monte-carlo-tools/skills/drake-install plugins/hep-ph-toolkit/skills/
git mv plugins/monte-carlo-tools/skills/maddm plugins/hep-ph-toolkit/skills/
git mv plugins/monte-carlo-tools/skills/maddm-install plugins/hep-ph-toolkit/skills/
git mv plugins/monte-carlo-tools/skills/madgraph plugins/hep-ph-toolkit/skills/
git mv plugins/monte-carlo-tools/skills/pythia-config plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 9: Move skills from hep-ph-demo (excluding `_shared`)**

```bash
git mv plugins/hep-ph-demo/skills/2hdm-a plugins/hep-ph-toolkit/skills/
git mv plugins/hep-ph-demo/skills/_test_model_x plugins/hep-ph-toolkit/skills/
git mv plugins/hep-ph-demo/skills/dark-su3 plugins/hep-ph-toolkit/skills/
git mv plugins/hep-ph-demo/skills/demo plugins/hep-ph-toolkit/skills/
git mv plugins/hep-ph-demo/skills/install plugins/hep-ph-toolkit/skills/
git mv plugins/hep-ph-demo/skills/singlet-doublet plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 10: Drop the placeholder, verify count**

```bash
rm plugins/hep-ph-toolkit/skills/.gitkeep
ls plugins/hep-ph-toolkit/skills/ | wc -l
```

Expected: 25 (2+2+2+3+2+2+6+6).

- [ ] **Step 11: Commit**

```bash
git add -A plugins/
git commit -m "refactor(toolkit): move skills from arxiv-research, collider-pheno, hep-data-analysis, hep-plotting, latex-hep, workflow, monte-carlo-tools, and hep-ph-demo (non-_shared)"
```

---

## Task 3: Move skills and merge `_shared` from the four `_shared`-bearing plugins

**Files:**
- Move: non-`_shared` skills under `constraints/skills/`, `feynman-diagrams/skills/`, `model-building/skills/` → `plugins/hep-ph-toolkit/skills/`
- Merge: four `skills/_shared/` dirs → `plugins/hep-ph-toolkit/skills/_shared/`
- Delete: obsolete `test_blocker_schema_symlink.py` (consolidation makes it irrelevant)

- [ ] **Step 1: Move non-`_shared` skills from constraints**

```bash
git mv plugins/constraints/skills/dark-matter-constraints plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/ddcalc plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/ddcalc-install plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/gamlike plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/higgstools plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/higgstools-install plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/micromegas plugins/hep-ph-toolkit/skills/
git mv plugins/constraints/skills/micromegas-install plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 2: Move non-`_shared` skills from feynman-diagrams**

```bash
git mv plugins/feynman-diagrams/skills/amplitude-calc plugins/hep-ph-toolkit/skills/
git mv plugins/feynman-diagrams/skills/draw-feynman plugins/hep-ph-toolkit/skills/
git mv plugins/feynman-diagrams/skills/feynarts plugins/hep-ph-toolkit/skills/
git mv plugins/feynman-diagrams/skills/feynarts-install plugins/hep-ph-toolkit/skills/
git mv plugins/feynman-diagrams/skills/formcalc plugins/hep-ph-toolkit/skills/
git mv plugins/feynman-diagrams/skills/formcalc-install plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 3: Move non-`_shared` skills from model-building**

```bash
git mv plugins/model-building/skills/feynrules-install plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/lagrangian-builder plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/looptools-install plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/rge-runner plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/sarah-build plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/sarah-install plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/spheno-build plugins/hep-ph-toolkit/skills/
git mv plugins/model-building/skills/spheno-install plugins/hep-ph-toolkit/skills/
```

- [ ] **Step 4: Move model-building's `_shared` to the toolkit (canonical schemas)**

```bash
git mv plugins/model-building/skills/_shared plugins/hep-ph-toolkit/skills/_shared
```

- [ ] **Step 5: Delete `__pycache__` directories everywhere under `plugins/`**

```bash
find plugins -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

- [ ] **Step 6: Inspect and merge `tests/conftest.py` collision**

The toolkit `_shared/tests/conftest.py` (from model-building) is a superset of hep-ph-demo's: both add the parent `_shared/` to `sys.path`; model-building's also adds `plugins/shared/install-helpers/`. The model-building version is correct as-is post-move because `Path(__file__).parents[4]` from the new location `plugins/hep-ph-toolkit/skills/_shared/tests/conftest.py` still resolves to `plugins/`. Drop the duplicate from hep-ph-demo:

```bash
diff plugins/hep-ph-toolkit/skills/_shared/tests/conftest.py plugins/hep-ph-demo/skills/_shared/tests/conftest.py | head -30
rm plugins/hep-ph-demo/skills/_shared/tests/conftest.py
```

Expected: diff prints something (they differ); the `rm` succeeds.

- [ ] **Step 7: Merge constraints' `_shared` into toolkit `_shared`**

`constraints/skills/_shared/` contains `__init__.py`, `tests/__init__.py`, `tests/test_blocker_schema_symlink.py`, and a redundant `blocker.schema.json` symlink.

```bash
git mv plugins/constraints/skills/_shared/__init__.py plugins/hep-ph-toolkit/skills/_shared/__init__.py
git mv plugins/constraints/skills/_shared/tests/__init__.py plugins/hep-ph-toolkit/skills/_shared/tests/__init__.py
# Delete the obsolete symlink-validation test (the symlink it validated no longer exists post-consolidation).
git rm plugins/constraints/skills/_shared/tests/test_blocker_schema_symlink.py
# Delete the redundant symlink itself.
rm plugins/constraints/skills/_shared/blocker.schema.json
# Empty skeleton remains:
rmdir plugins/constraints/skills/_shared/tests
rmdir plugins/constraints/skills/_shared
```

Expected: directories removed without error.

- [ ] **Step 8: Delete the redundant feynman-diagrams `_shared` symlink**

```bash
rm plugins/feynman-diagrams/skills/_shared/blocker.schema.json
rmdir plugins/feynman-diagrams/skills/_shared
```

- [ ] **Step 9: Verify hep-ph-demo `_shared` has no top-level filename collision with toolkit `_shared`**

```bash
ls plugins/hep-ph-toolkit/skills/_shared/ | grep -v '^tests$' | grep -v '^assets$' | grep -v __pycache__ | sort > /tmp/refactor/toolkit_shared.txt
ls plugins/hep-ph-demo/skills/_shared/ | grep -v '^tests$' | grep -v '^assets$' | grep -v __pycache__ | sort > /tmp/refactor/demo_shared.txt
echo "Top-level collisions:"
comm -12 /tmp/refactor/toolkit_shared.txt /tmp/refactor/demo_shared.txt
```

Expected: no output after "Top-level collisions:".

- [ ] **Step 10: Verify no test-filename collision in `_shared/tests/` either**

```bash
ls plugins/hep-ph-toolkit/skills/_shared/tests/ | grep -v conftest.py | grep -v __init__.py | sort > /tmp/refactor/toolkit_tests.txt
ls plugins/hep-ph-demo/skills/_shared/tests/ | sort > /tmp/refactor/demo_tests.txt
echo "Test collisions:"
comm -12 /tmp/refactor/toolkit_tests.txt /tmp/refactor/demo_tests.txt
```

Expected: no output. If output appears, STOP and merge by hand.

- [ ] **Step 11: Move every top-level file from hep-ph-demo `_shared` into toolkit `_shared`**

```bash
for f in plugins/hep-ph-demo/skills/_shared/*; do
  base=$(basename "$f")
  if [ "$base" = "tests" ] || [ "$base" = "__pycache__" ] || [ "$base" = "assets" ]; then
    continue
  fi
  git mv "$f" "plugins/hep-ph-toolkit/skills/_shared/$base"
done
git mv plugins/hep-ph-demo/skills/_shared/assets plugins/hep-ph-toolkit/skills/_shared/assets
```

- [ ] **Step 12: Move remaining hep-ph-demo `_shared/tests/` files**

```bash
for f in plugins/hep-ph-demo/skills/_shared/tests/*; do
  base=$(basename "$f")
  git mv "$f" "plugins/hep-ph-toolkit/skills/_shared/tests/$base"
done
ls plugins/hep-ph-demo/skills/_shared/tests/ 2>/dev/null
rmdir plugins/hep-ph-demo/skills/_shared/tests
rmdir plugins/hep-ph-demo/skills/_shared
```

Expected: `ls` empty, `rmdir`s succeed.

- [ ] **Step 13: Move hep-ph-demo's TOP-LEVEL `_shared/` (different dir!) to the toolkit root**

This dir contains `validate_one.py` and its tests. Treat as plugin-level shared, not skills-level.

```bash
git mv plugins/hep-ph-demo/_shared plugins/hep-ph-toolkit/_shared
```

After move: `plugins/hep-ph-toolkit/_shared/validate_one.py`, `parents[3]` still resolves to repo root (parents[0]=_shared, parents[1]=hep-ph-toolkit, parents[2]=plugins, parents[3]=repo). The hardcoded `"plugins" / "hep-ph-demo" / "skills"` inside the file gets rewritten in Task 5.

- [ ] **Step 14: Skill count sanity check**

```bash
ls plugins/hep-ph-toolkit/skills/ | wc -l
```

Expected: 48 (47 functional + 1 `_shared`).

- [ ] **Step 15: Commit**

```bash
git add -A plugins/
git commit -m "refactor(toolkit): merge constraints/feynman-diagrams/hep-ph-demo/model-building skills and consolidate _shared"
```

---

## Task 4: Merge hooks and scripts

**Files:**
- Move: `plugins/hep-ph-demo/{hooks,scripts}/*` → `plugins/hep-ph-toolkit/{hooks,scripts}/`
- Modify: `plugins/hep-ph-toolkit/scripts/install-followup.sh` (union the regex)
- Delete: `plugins/{model-building,monte-carlo-tools}/{hooks,scripts}/`

The three source `hooks.json` files are byte-identical (verified). The three `install-followup.sh` files differ only in the `INSTALL_SKILLS_REGEX=` line. The merged regex must list every `*-install` skill across the consolidated plugin (including `ddcalc-install` and `higgstools-install` from `constraints/`, which never had a hook).

- [ ] **Step 1: Confirm the three hooks.json are identical**

```bash
diff plugins/hep-ph-demo/hooks/hooks.json plugins/model-building/hooks/hooks.json
diff plugins/hep-ph-demo/hooks/hooks.json plugins/monte-carlo-tools/hooks/hooks.json
```

Expected: both diffs empty.

- [ ] **Step 2: Confirm the three install-followup.sh differ ONLY on the regex line**

```bash
diff plugins/hep-ph-demo/scripts/install-followup.sh plugins/model-building/scripts/install-followup.sh
diff plugins/hep-ph-demo/scripts/install-followup.sh plugins/monte-carlo-tools/scripts/install-followup.sh
```

Expected: each diff shows only the `INSTALL_SKILLS_REGEX=` line.

- [ ] **Step 3: Enumerate every install-skill that exists in the consolidated plugin**

```bash
ls plugins/hep-ph-toolkit/skills/ | grep -E '^(install|.*-install)$' | sort
```

Expected (10 names): `ddcalc-install`, `drake-install`, `feynarts-install`, `formcalc-install`, `higgstools-install`, `install`, `looptools-install`, `maddm-install`, `micromegas-install`, `sarah-install`, `spheno-install`. (Note: `feynarts-install` and `formcalc-install` weren't in any prior hook — they SHOULD be in the merged hook for consistency.)

- [ ] **Step 4: Move hep-ph-demo's hooks/scripts to the toolkit; drop placeholders**

```bash
rm -f plugins/hep-ph-toolkit/hooks/.gitkeep plugins/hep-ph-toolkit/scripts/.gitkeep
git mv plugins/hep-ph-demo/hooks/hooks.json plugins/hep-ph-toolkit/hooks/hooks.json
git mv plugins/hep-ph-demo/scripts/install-followup.sh plugins/hep-ph-toolkit/scripts/install-followup.sh
```

- [ ] **Step 5: Update the regex in the toolkit's install-followup.sh**

Replace the line `INSTALL_SKILLS_REGEX='^(install)$'` with:

```bash
INSTALL_SKILLS_REGEX='^(install|feynrules-install|looptools-install|sarah-install|spheno-install|drake-install|maddm-install|micromegas-install|ddcalc-install|higgstools-install|feynarts-install|formcalc-install)$'
```

- [ ] **Step 6: Syntax-check the merged script**

```bash
bash -n plugins/hep-ph-toolkit/scripts/install-followup.sh
```

Expected: no output.

- [ ] **Step 7: Assert source hooks/scripts dirs hold only the expected files, then delete**

```bash
for p in model-building monte-carlo-tools; do
  for sub in hooks scripts; do
    expected=1
    actual=$(ls "plugins/$p/$sub" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$actual" != "$expected" ]; then
      echo "ABORT: plugins/$p/$sub has $actual files, expected $expected"
      exit 1
    fi
  done
done
echo "All source hooks/scripts dirs hold the expected single-file content."

rm plugins/model-building/hooks/hooks.json
rm plugins/model-building/scripts/install-followup.sh
rm plugins/monte-carlo-tools/hooks/hooks.json
rm plugins/monte-carlo-tools/scripts/install-followup.sh
rmdir plugins/model-building/hooks plugins/model-building/scripts
rmdir plugins/monte-carlo-tools/hooks plugins/monte-carlo-tools/scripts
rmdir plugins/hep-ph-demo/hooks plugins/hep-ph-demo/scripts 2>/dev/null || true
```

- [ ] **Step 8: Commit**

```bash
git add -A plugins/
git commit -m "refactor(toolkit): merge hooks and install-followup script with unioned install-skill regex"
```

---

## Task 5: Rewrite cross-plugin path references with a Python rewriter

**Files modified:** every file under `plugins/`, plus `README.md`, `ROADMAP.md`, `FOLLOWUPS.md`, `workflow_work.md`, `tools/tests/test_check_plan.py`, `tools/tests/fixtures/plan-amended.md`, and any other top-level docs that contain matching paths. **Excludes** `.git/`, `.shift-manager/`, `.claude/`, `demo_output/`, `docs/superpowers/plans/` (these last two represent historical state that should not be rewritten).

**Why a Python rewriter, not sed:** the codebase uses BOTH the slash-form (`plugins/<oldname>/skills/...`) and the pathlib split-form (`"plugins" / "<oldname>"`, `_plugins / "<oldname>" / "skills"`). Confirmed counts at plan-write time: 444 occurrences across 152 files for slash-form; 69+ split-form occurrences across `*.py` alone. Sed cannot reliably handle the split-form because the segments are separate string literals.

The rewriter applies these transformations:

| Pattern | Replacement |
|---|---|
| `plugins/<old>/skills/` (slash) | `plugins/hep-ph-toolkit/skills/` |
| `plugins/hep-ph-demo/_shared/` (slash) | `plugins/hep-ph-toolkit/_shared/` |
| `plugins/hep-ph-demo/skills/` (slash) | `plugins/hep-ph-toolkit/skills/` |
| `"plugins" / "<old>"` (pathlib) | `"plugins" / "hep-ph-toolkit"` |
| `"<old>" / "skills"` (pathlib, anchored) | `"hep-ph-toolkit" / "skills"` |
| `"hep-ph-demo" / "_shared"` (pathlib) | `"hep-ph-toolkit" / "_shared"` |

`<old>` ∈ {arxiv-research, collider-pheno, constraints, feynman-diagrams, hep-data-analysis, hep-ph-demo, hep-plotting, latex-hep, model-building, monte-carlo-tools, workflow}.

- [ ] **Step 1: Create the rewriter script**

Create `/tmp/refactor/rewrite_paths.py`:

```python
#!/usr/bin/env python3
"""Rewrite cross-plugin paths from old per-plugin layout to plugins/hep-ph-toolkit."""
import os
import re
import sys
from pathlib import Path

OLD_NAMES = [
    "arxiv-research", "collider-pheno", "constraints", "feynman-diagrams",
    "hep-data-analysis", "hep-ph-demo", "hep-plotting", "latex-hep",
    "model-building", "monte-carlo-tools", "workflow",
]
INCLUDE_EXT = {".md", ".py", ".json", ".yaml", ".yml", ".sh", ".txt"}
EXCLUDE_DIRS = {".git", ".shift-manager", ".claude", "demo_output", "node_modules", "__pycache__"}
EXCLUDE_PATH_SUBSTRINGS = ["docs/superpowers/plans/"]  # don't rewrite plan history


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    if path.suffix not in INCLUDE_EXT:
        return True
    str_path = str(path)
    for sub in EXCLUDE_PATH_SUBSTRINGS:
        if sub in str_path:
            return True
    return False


def rewrite(text: str) -> tuple[str, int]:
    n = 0
    # Slash-form: plugins/<old>/skills/  →  plugins/hep-ph-toolkit/skills/
    for old in OLD_NAMES:
        pat = f"plugins/{old}/skills/"
        new = "plugins/hep-ph-toolkit/skills/"
        cnt = text.count(pat)
        text = text.replace(pat, new)
        n += cnt
    # Slash-form: plugins/hep-ph-demo/_shared/  →  plugins/hep-ph-toolkit/_shared/
    pat = "plugins/hep-ph-demo/_shared/"
    new = "plugins/hep-ph-toolkit/_shared/"
    n += text.count(pat); text = text.replace(pat, new)
    # Pathlib split-form: "plugins" / "<old>"  →  "plugins" / "hep-ph-toolkit"
    for old in OLD_NAMES:
        pat = re.compile(r'"plugins"\s*/\s*"' + re.escape(old) + r'"')
        new_text, cnt = pat.subn('"plugins" / "hep-ph-toolkit"', text)
        n += cnt; text = new_text
    # Pathlib split-form: "<old>" / "skills"  →  "hep-ph-toolkit" / "skills"
    # (catches `_plugins / "<old>" / "skills"` and similar)
    for old in OLD_NAMES:
        pat = re.compile(r'"' + re.escape(old) + r'"\s*/\s*"skills"')
        new_text, cnt = pat.subn('"hep-ph-toolkit" / "skills"', text)
        n += cnt; text = new_text
    # Pathlib split-form: "hep-ph-demo" / "_shared"  →  "hep-ph-toolkit" / "_shared"
    pat = re.compile(r'"hep-ph-demo"\s*/\s*"_shared"')
    new_text, cnt = pat.subn('"hep-ph-toolkit" / "_shared"', text)
    n += cnt; text = new_text
    return text, n


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    total_files = 0
    total_subs = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        # Walk path parts against excludes
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.suffix not in INCLUDE_EXT:
            continue
        if any(sub in str(rel) for sub in EXCLUDE_PATH_SUBSTRINGS):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        new_text, n = rewrite(text)
        if n > 0:
            path.write_text(new_text, encoding="utf-8")
            total_files += 1
            total_subs += n
            print(f"  {rel}: {n} substitutions")
    print(f"\nRewrote {total_subs} occurrences across {total_files} files.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the rewriter on the entire repo**

```bash
python3 /tmp/refactor/rewrite_paths.py /Users/yianni/Projects/hep-ph-agents | tee /tmp/refactor/rewriter.log | tail -30
```

Expected: prints per-file substitution counts, ending with "Rewrote N occurrences across M files." Both numbers > 0.

- [ ] **Step 3: Verify no slash-form leftovers anywhere except excluded paths**

```bash
grep -rE 'plugins/(arxiv-research|collider-pheno|constraints|feynman-diagrams|hep-data-analysis|hep-ph-demo|hep-plotting|latex-hep|model-building|monte-carlo-tools|workflow)/' \
  --include='*.md' --include='*.py' --include='*.json' --include='*.yaml' --include='*.yml' --include='*.sh' --include='*.txt' \
  --exclude-dir='.git' --exclude-dir='.shift-manager' --exclude-dir='.claude' --exclude-dir='demo_output' --exclude-dir='__pycache__' \
  . | grep -v 'docs/superpowers/plans/' | head -20
```

Expected: empty output. (If any matches print, inspect — they may be inside CHANGELOG-like history that should be preserved; decide case-by-case.)

- [ ] **Step 4: Verify no pathlib split-form leftovers**

```bash
grep -rE '"(arxiv-research|collider-pheno|constraints|feynman-diagrams|hep-data-analysis|hep-ph-demo|hep-plotting|latex-hep|model-building|monte-carlo-tools|workflow)"' \
  --include='*.py' \
  --exclude-dir='.git' --exclude-dir='.shift-manager' --exclude-dir='.claude' --exclude-dir='demo_output' --exclude-dir='__pycache__' \
  . | grep -v 'docs/superpowers/plans/' | head -20
```

Expected: empty output.

- [ ] **Step 5: Manual fix-up — `model-router/tests/conftest.py`**

This conftest hardcodes `_PLUGIN_ROOT / "hep-ph-demo" / "skills" / "_shared"`. The rewriter changes the inner string to `"hep-ph-toolkit" / "skills"` but the resulting line `_PLUGIN_ROOT / "hep-ph-toolkit" / "skills" / "_shared"` is still wrong: `_PLUGIN_ROOT = _SKILL_DIR.parents[2]` resolves to `plugins/hep-ph-toolkit/skills/` post-move, so prepending another `hep-ph-toolkit/skills` yields a non-existent path.

Open `plugins/hep-ph-toolkit/skills/model-router/tests/conftest.py` and replace the block (around lines 26–31):

```python
# Also add hep-ph-demo/_shared to sys.path so time_budget is importable
# (needed for mock_constraints_yaml fixture patching)
_PLUGIN_ROOT = _SKILL_DIR.parents[2]  # plugins/workflow/ -> plugins/
_HEP_PH_DEMO_SHARED = _PLUGIN_ROOT / "hep-ph-toolkit" / "skills" / "_shared"
if str(_HEP_PH_DEMO_SHARED) not in sys.path:
    sys.path.insert(0, str(_HEP_PH_DEMO_SHARED))
```

with:

```python
# Add the toolkit's _shared/ to sys.path so time_budget is importable
# (needed for mock_constraints_yaml fixture patching).
# _SKILL_DIR.parents[2] resolves to plugins/hep-ph-toolkit/skills/
_TOOLKIT_SKILLS = _SKILL_DIR.parents[2]
_SHARED = _TOOLKIT_SKILLS / "_shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
```

- [ ] **Step 6: Manual fix-up — `validate_one.py` docstring sanity**

After the rewriter, `plugins/hep-ph-toolkit/_shared/validate_one.py` should have `SKILLS_DIR = REPO_ROOT / "plugins" / "hep-ph-toolkit" / "skills"` (split-form rewrite), and the docstring references should be `plugins/hep-ph-toolkit/skills/...`. Spot-check:

```bash
grep -n 'plugins' plugins/hep-ph-toolkit/_shared/validate_one.py | head -10
```

Expected: every match shows `plugins/hep-ph-toolkit/...` or `"plugins" / "hep-ph-toolkit"`. If not, edit by hand.

- [ ] **Step 7: Spot-check a few rewritten files**

```bash
grep -n 'plugins' plugins/hep-ph-toolkit/skills/maddm-install/SKILL.md | head -10
grep -n 'plugins' plugins/hep-ph-toolkit/skills/drake/scripts/run_drake.py | head -10
grep -n 'plugins' plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/check_prereqs.py | head -10
grep -n 'plugins' plugins/hep-ph-toolkit/skills/analytic-exception-detector/scripts/exceptions_registry.py | head -10
grep -n 'plugins' README.md | head -5
```

Expected: every match references `hep-ph-toolkit`, no old plugin names.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor(toolkit): rewrite cross-plugin path references (slash-form + pathlib split-form) and patch model-router conftest"
```

---

## Task 6: Replace marketplace.json with single-plugin entry

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Overwrite the marketplace manifest**

Replace `.claude-plugin/marketplace.json` with:

```json
{
  "name": "hep-ph-agents",
  "description": "Claude Code plugin marketplace for high-energy physics phenomenology — Feynman diagrams, collider analysis, model building, Monte Carlo tools, dark-matter constraints, plotting, and more.",
  "owner": {
    "name": "hep-ph-agents",
    "url": "https://github.com/yianni/hep-ph-agents"
  },
  "plugins": [
    {
      "name": "hep-ph-toolkit",
      "source": "./plugins/hep-ph-toolkit",
      "description": "All-in-one toolkit for high-energy physics phenomenology — Feynman diagrams, amplitudes, BSM model building, RGE, dark-matter constraints, Higgs bounds, Monte Carlo event generation (MadGraph/MadDM/micrOMEGAs/DRAKE/Pythia), ROOT analysis, plotting, LaTeX paper drafting, arXiv research, plus workflow skills for model-to-tool routing and analytic-exception detection.",
      "version": "0.1.0",
      "tags": [
        "feynman", "diagrams", "amplitudes", "qft", "formcalc", "looptools", "form", "passarino-veltman",
        "constraints", "dark-matter", "direct-detection", "higgs", "loop-integrals",
        "collider", "lhc", "cross-section", "phenomenology",
        "bsm", "lagrangian", "rge", "symmetry", "sarah", "spheno", "feynrules",
        "madgraph", "maddm", "micromegas", "drake", "pythia", "monte-carlo", "event-generation",
        "root", "statistics", "analysis", "hepdata",
        "latex", "tikz", "feynmf", "publishing",
        "arxiv", "literature", "citations", "inspire",
        "plotting", "matplotlib", "mplhep", "exclusion", "contour",
        "workflow", "routing", "model-router", "exception-detector",
        "onboarding", "demo", "tutorial"
      ]
    }
  ]
}
```

- [ ] **Step 2: Validate JSON**

```bash
python3 -c "import json; m=json.load(open('.claude-plugin/marketplace.json')); assert len(m['plugins'])==1 and m['plugins'][0]['name']=='hep-ph-toolkit'; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "refactor(marketplace): replace 11-plugin index with single hep-ph-toolkit entry"
```

---

## Task 7: Delete the eleven old plugin directories

**Files:**
- Delete: `plugins/{arxiv-research,collider-pheno,constraints,feynman-diagrams,hep-data-analysis,hep-ph-demo,hep-plotting,latex-hep,model-building,monte-carlo-tools,workflow}/`

- [ ] **Step 1: Verify each old plugin dir holds only manifest+readme leftovers**

```bash
for p in arxiv-research collider-pheno constraints feynman-diagrams hep-data-analysis hep-ph-demo hep-plotting latex-hep model-building monte-carlo-tools workflow; do
  echo "--- $p ---"
  find "plugins/$p" -type f -o -type l | sort
done
```

Expected: each dir shows ONLY `plugin.json` (in `.claude-plugin/`), `README.md`, and (for feynman-diagrams and model-building) `SHARED.md`. If anything else appears, STOP and investigate before deleting.

- [ ] **Step 2: Delete the eleven directories**

```bash
git rm -r plugins/arxiv-research \
          plugins/collider-pheno \
          plugins/constraints \
          plugins/feynman-diagrams \
          plugins/hep-data-analysis \
          plugins/hep-ph-demo \
          plugins/hep-plotting \
          plugins/latex-hep \
          plugins/model-building \
          plugins/monte-carlo-tools \
          plugins/workflow
```

- [ ] **Step 3: Verify only the new plugin and `shared/` remain**

```bash
ls plugins/
```

Expected: `hep-ph-toolkit  shared`.

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor: remove eleven old plugin directories, replaced by hep-ph-toolkit"
```

---

## Task 8: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (root)

- [ ] **Step 1: Replace the "Plugin Categories" section**

Locate the `## Plugin Categories` section in `CLAUDE.md`. Replace it with:

```markdown
## Plugin Layout

This marketplace exposes a single plugin, `hep-ph-toolkit`, which contains all skills organised by topic. Top-level skill categories:

| Category | Skills |
|----------|--------|
| Onboarding & demo | `2hdm-a`, `dark-su3`, `demo`, `install`, `singlet-doublet`, `_test_model_x` |
| Feynman / amplitudes | `amplitude-calc`, `draw-feynman`, `feynarts`, `feynarts-install`, `formcalc`, `formcalc-install` |
| Collider | `cross-section`, `signal-background` |
| BSM model building | `feynrules-install`, `lagrangian-builder`, `looptools-install`, `rge-runner`, `sarah-build`, `sarah-install`, `spheno-build`, `spheno-install` |
| Constraints | `dark-matter-constraints`, `ddcalc`, `ddcalc-install`, `gamlike`, `higgstools`, `higgstools-install`, `micromegas`, `micromegas-install` |
| Monte Carlo | `drake`, `drake-install`, `maddm`, `maddm-install`, `madgraph`, `pythia-config` |
| Analysis | `root-analysis`, `statistical-tools` |
| Publishing | `feynman-tikz`, `hep-paper-draft` |
| Research | `arxiv-search`, `literature-review` |
| Plotting | `exclusion-contour`, `hep-plot`, `theory-data-comparison` |
| Workflow | `analytic-exception-detector`, `model-router` |

Cross-skill helpers live in `plugins/hep-ph-toolkit/skills/_shared/` (matrix lookup, blocker schema, taxonomy). Plugin-level helpers (`validate_one.py`) live in `plugins/hep-ph-toolkit/_shared/`. Plugin-agnostic install helpers and JSON schemas live in `plugins/shared/`.
```

- [ ] **Step 2: Verify CLAUDE.md has no stale plugin-name references**

```bash
grep -nE '(arxiv-research|collider-pheno|^\| `?constraints`?|feynman-diagrams|hep-data-analysis|hep-ph-demo|hep-plotting|latex-hep|model-building|monte-carlo-tools|^\| `?workflow`?)' CLAUDE.md
```

Expected: empty (or only false positives where the word "constraints" or "workflow" appears as a category, which is fine).

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md plugin-categories table for single-plugin layout"
```

---

## Task 9: Verify (collection diff + import smoke + JSON/YAML validation)

**Files:** none (verification only)

- [ ] **Step 1: Test collection — diff by NAME, not just count**

```bash
pytest --collect-only -q 2>&1 | grep -E '::' | sort > /tmp/refactor/post_collect.txt

# Apply the same path rewrite to the baseline so we can compare apples-to-apples.
python3 - <<'PY'
import re
old_names = ["arxiv-research","collider-pheno","constraints","feynman-diagrams",
             "hep-data-analysis","hep-ph-demo","hep-plotting","latex-hep",
             "model-building","monte-carlo-tools","workflow"]
src = open("/tmp/refactor/pre_collect.txt").read()
for o in old_names:
    src = src.replace(f"plugins/{o}/skills/", "plugins/hep-ph-toolkit/skills/")
src = src.replace("plugins/hep-ph-demo/_shared/", "plugins/hep-ph-toolkit/_shared/")
open("/tmp/refactor/pre_collect_rewritten.txt", "w").write(src)
PY

echo "=== diff (lines starting with < are MISSING post-refactor; > are NEW) ==="
diff /tmp/refactor/pre_collect_rewritten.txt /tmp/refactor/post_collect.txt | head -40
echo "==="
diff /tmp/refactor/pre_collect_rewritten.txt /tmp/refactor/post_collect.txt | grep -c '^[<>]' || echo "0"
```

Expected: zero lines starting with `<` (no tests dropped). Lines starting with `>` are OK (e.g., the deleted `test_blocker_schema_symlink.py` should appear as removed in the `<` set — that's intentional). Adjust expectations: ONE `<` line is expected for `test_blocker_schema_symlink.py`. If more, investigate.

- [ ] **Step 2: Run non-gated tests**

```bash
pytest -q -m "not smoke and not integration" --no-header 2>&1 | tail -10 | tee /tmp/refactor/post_run.txt
```

Compare with `/tmp/refactor/pre_run.txt`. Expected: no NEW failures. (Pass count may decrease by one due to removed symlink test.)

- [ ] **Step 3: Validate every JSON and YAML in the toolkit**

```bash
python3 - <<'PY'
import pathlib, json, sys
try:
    import yaml
except ImportError:
    yaml = None
errors = []
for p in pathlib.Path('plugins/hep-ph-toolkit').rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts:
        continue
    if p.suffix == '.json':
        try: json.loads(p.read_text())
        except Exception as e: errors.append((str(p), str(e)))
    elif yaml and p.suffix in ('.yaml', '.yml'):
        try: yaml.safe_load(p.read_text())
        except Exception as e: errors.append((str(p), str(e)))
for path, err in errors:
    print(f"{path}: {err}")
print(f"errors={len(errors)}")
PY
```

Expected: `errors=0`.

- [ ] **Step 4: Smoke-import every `_shared` Python module**

```bash
python3 -c "
import sys
sys.path.insert(0, 'plugins/hep-ph-toolkit/skills/_shared')
import matrix_lookup, status_resolve, time_budget, ws1_axis_reader, taxonomy, sarah_name, config_migration
print('OK skills/_shared')
"
```

Expected: `OK skills/_shared`.

- [ ] **Step 5: Smoke-test `validate_one.py`**

```bash
python3 plugins/hep-ph-toolkit/_shared/validate_one.py 2>&1 | head -5 || true
```

Expected: prints usage error (exit 2) — confirms the script is at least importable and reaches its argument parser without ImportError.

- [ ] **Step 6: Commit fixes if Steps 1–5 surfaced any issues**

```bash
git diff --stat
# If diff is empty:
echo "No fixes required."
# Otherwise:
git commit -am "fix(toolkit): post-consolidation regressions surfaced by Task 9 verification"
```

---

## Task 10: Final review and stash pop

**Files:** none

- [ ] **Step 1: Review the commit narrative**

```bash
git log --oneline main..HEAD
git diff --stat main..HEAD | tail -5
```

Expected: ~7 commits forming a coherent story; stat shows ~50 dir moves + manifest changes.

- [ ] **Step 2: Inspect the final tree**

```bash
ls plugins/
ls plugins/hep-ph-toolkit/
echo "Skill count: $(ls plugins/hep-ph-toolkit/skills/ | wc -l)"
```

Expected: `plugins/` shows `hep-ph-toolkit  shared`. `plugins/hep-ph-toolkit/` shows `_shared  .claude-plugin  hooks  scripts  skills`. Skill count: 48.

- [ ] **Step 3: Restore the user's stash (warn about possible conflicts)**

```bash
git stash pop stash@{0} || echo "WARN: stash pop produced conflicts; resolve manually. The stash is preserved at stash@{0}."
```

The pre-existing dirty state was mostly `.shift-manager/run-*` deletions; conflicts are unlikely on this branch but possible.

- [ ] **Step 4: Print final status**

```bash
echo "Branch: $(git branch --show-current)"
echo "Commits ahead of main: $(git rev-list --count main..HEAD)"
echo "Working tree dirty files: $(git status --short | wc -l | tr -d ' ')"
echo "Ready for review/merge."
```

---

## Notes on what is NOT in scope

- `plugins/shared/` (top-level, with `install-helpers/` and `schemas/`) is unchanged — already plugin-agnostic.
- `.shift-manager/`, `.claude/`, `demo_output/`, and `docs/superpowers/plans/` are excluded from the path rewrite — they represent historical state.
- `git log --follow` continues to work because we used `git mv` throughout.
- Per-skill `tests/conftest.py` files are unchanged; their `parents[N]` paths still resolve because each skill's depth from the repo root is preserved (was `plugins/<old>/skills/<skill>/...`, now `plugins/hep-ph-toolkit/skills/<skill>/...` — same depth).
- The deleted `test_blocker_schema_symlink.py` validated a cross-plugin symlink that no longer exists post-consolidation; it has no replacement.
