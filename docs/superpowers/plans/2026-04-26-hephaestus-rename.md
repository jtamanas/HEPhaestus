# HEPHaestus rename — execution plan

**Status:** *Drafted, ready to execute.* ModelSpec-v3 landed in commit
`aa35885` (2026-04-27). The plan was re-cataloged against post-v3 `HEAD`
using the same method (three haiku reconnaissance scouts + skeptical opus
verification). All previously-deferred v1 files are now deleted; new v3
surface (specs YAML, render templates, regenerated goldens) is folded in
below.

**Author of plan:** Drafted 2026-04-26 from three haiku reconnaissance scouts
plus an ornery opus skeptic review. Re-cataloged 2026-04-27 post-v3 — see
"Post-v3 additions" sub-section under Scope.

---

## Why

The project just got an actual GitHub home: **`jtamanas/hephaestus`**. The
marketplace, README, and CLAUDE.md headers were already retitled to
**HEPHaestus** (slug: `hephaestus`). This document captures the full
remaining surface that still references the legacy name `hep-ph-agents` so
we can cut over cleanly in one coordinated pass.

The branding choice: marketplace and product are **HEPHaestus**, the slug is
`hephaestus`, and the GitHub repo is `jtamanas/hephaestus`. The env-var
prefix `HEPPH_*` (HEP-phenomenology) stays — it names the *domain*, not the
project, and the cost to rename 61 vars × 546 references × 143 files is
unjustified for a cosmetic change.

---

## What to do *before* starting (pre-flight)

### 0. Take a full backup before the rewriter runs

A path-construction rewriter touching ~110-150 files plus `git mv` plus a
228 MB user-state migration is exactly the kind of operation that can
nuke a working tree if a regex or a typo goes sideways. Snapshot
**both** the repo and the user-state dirs first.

```bash
# 1. Repo snapshot — tar instead of cp so symlinks, perms, and the .git
#    dir survive cleanly. Excludes the heavy regenerable stuff.
ts=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p ~/backups/hephaestus-rename
tar --exclude='.git/objects/pack/*' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='node_modules' \
    --exclude='eval/plot_ab_test/outputs' \
    -czf ~/backups/hephaestus-rename/repo-${ts}.tgz \
    -C ~/Projects hep-ph-agents

# 2. User-state snapshot — small enough to just tar whole.
tar -czf ~/backups/hephaestus-rename/user-state-${ts}.tgz \
    -C ~ .config/hep-ph-agents .local/share/hep-ph-agents .cache/hep-ph-agents

# 3. Belt-and-braces: a clean git reference branch that survives any
#    accidental local rm. Push to the remote so it's off-machine.
git -C ~/Projects/hep-ph-agents tag pre-hephaestus-rename
git -C ~/Projects/hep-ph-agents push origin pre-hephaestus-rename

# 4. Verify the tarballs aren't truncated.
tar -tzf ~/backups/hephaestus-rename/repo-${ts}.tgz       >/dev/null && echo "repo backup OK"
tar -tzf ~/backups/hephaestus-rename/user-state-${ts}.tgz >/dev/null && echo "user-state backup OK"

# 5. Record the backup paths in the run log so future-you can find them.
echo "$ts repo=~/backups/hephaestus-rename/repo-${ts}.tgz user=~/backups/hephaestus-rename/user-state-${ts}.tgz tag=pre-hephaestus-rename" \
  >> ~/backups/hephaestus-rename/MANIFEST.txt
```

If anything goes wrong mid-rename:

- **Repo blown up?** `cd ~ && rm -rf Projects/hep-ph-agents && tar -xzf ~/backups/hephaestus-rename/repo-<ts>.tgz -C Projects/`
- **Just need a clean git state?** `git reset --hard pre-hephaestus-rename`
- **User-state orphaned?** `tar -xzf ~/backups/hephaestus-rename/user-state-<ts>.tgz -C ~`
- **Both?** Restore in that order (repo first, then user-state).

Don't delete the backups until the rename is verified green and the
follow-up work (week or two of normal use) shows nothing regressed.

### 1. Migrate the dev machine's existing 228 MB of installed state

The dev box (Yianni's machine) has populated user-state directories that
the rename would silently orphan:

- `~/.config/hep-ph-agents/config.json` (5.4 KB, populated)
- `~/.local/share/hep-ph-agents/` (~228 MB: FormCalc 9.10 = 141 MB, models
  = 65 MB, tools/DDCalc = 1.8 MB, runs, backups)
- `~/.cache/hep-ph-agents/` (empty)

**Run before any rewriter touches the repo:**

```bash
mv ~/.config/hep-ph-agents      ~/.config/hephaestus
mv ~/.local/share/hep-ph-agents ~/.local/share/hephaestus
mv ~/.cache/hep-ph-agents       ~/.cache/hephaestus
```

Then verify with `/install` (preflight scan should still find every tool;
nothing should re-trigger a download). If anything fails, restore via the
inverse `mv` and treat it as a path-construction bug.

### 2. ~~Decide the Authors-string question~~ — resolved

V3 has landed. The renderer at `_shared/modelspec_v3/render/header.py`
reads the `authors` field from each ModelSpec and emits it into the SARAH
`Model\`Authors = "..."` line. All five v3 specs currently bake
`authors: 'hep-ph-agents'`. Update happens as a normal in-scope change
(see "Post-v3 additions" item 9 below) — no separate decision gate.

---

## Scope

### In scope (handled by this rename)

1. **File renames** in `styles/`:
   - `hep-ph-agents-analytic.mplstyle` → `hephaestus-analytic.mplstyle`
   - `hep-ph-agents-slate.mplstyle` → `hephaestus-slate.mplstyle`
   - `hep-ph-agents-tikz.sty` → `hephaestus-tikz.sty`

2. **Inside-file edits in the renamed `.sty`:**
   - `styles/hep-ph-agents-tikz.sty:9` — `\ProvidesPackage{hep-ph-agents-tikz}` → `\ProvidesPackage{hephaestus-tikz}` (LaTeX warns when filename and `\ProvidesPackage` arg disagree)

3. **Style-file consumers (load these in tandem with item 1):**
   - `eval/test_tikz.tex:10` — `\usepackage{hep-ph-agents-tikz}` → `\usepackage{hephaestus-tikz}`
   - `styles/hep_ph_style.py:128` — dynamic loader `_STYLE_DIR / f"hep-ph-agents-{context}.mplstyle"` → `f"hephaestus-{context}.mplstyle"` (matches the renamed `.mplstyle` files; missing this turns every `hep_ph_style.use_style(...)` call into FileNotFoundError)
   - `styles/hep_ph_style.py:2` — module docstring "hep-ph-agents style helpers" → "hephaestus style helpers"
   - `plugins/hep-ph-toolkit/skills/theory-data-comparison/SKILL.md:91` — update `styles/hep-ph-agents-analytic.mplstyle` reference
   - `plugins/hep-ph-toolkit/skills/demo/scripts/plot_figure.py:10` — update `hep-ph-agents analytic context` comment
   - `plugins/hep-ph-toolkit/skills/demo/scripts/plot_figure.py:155` — update `Ensure the hep-ph-agents repo` error message
   - `plugins/hep-ph-toolkit/skills/draw-feynman/SKILL.md:46` — `styles/hep-ph-agents-tikz.sty` reference

4. **Repo-slug bug fix** (`install-followup.sh`):
   - `plugins/hep-ph-toolkit/scripts/install-followup.sh:42` — `'hep-ph-agents'` → `'jtamanas/hephaestus'`. (`gh` requires `OWNER/REPO`; the bare slug fallback was already broken.)

5. **Stale local plugin IDs in `.claude/settings.json`** (untracked file, dev-machine only):
   - Lines 4-13 reference pre-consolidation plugin names like `hep-ph-demo@hep-ph-agents`. Replace with the single current entry: `hep-ph-toolkit@hephaestus`.
   - Line 16 `extraKnownMarketplaces.hep-ph-agents` → `extraKnownMarketplaces.hephaestus`.

6. **Repo-relative path comments:**
   - `tools/check_plan.py:37` — `# tools/../ = hep-ph-agents/` → `# tools/../ = hephaestus/`
   - `plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/two_hdm.yaml:4` — `hep-ph-agents starter template` → `hephaestus starter template`
   - `plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/archived/dark_su3_confining.yaml:4` — same

7. **Doc / SKILL.md textual mentions** of the project name (~12 spots — list at end):
   - `plugins/hep-ph-toolkit/skills/install/SKILL.md` lines 3, 8, 123
   - `plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md:858-859`
   - `plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/register_model.py:43`
   - `plugins/hep-ph-toolkit/skills/install/scripts/check_config.py:2`
   - `plugins/hep-ph-toolkit/skills/feynarts/scripts/run_feynarts.py:58`
   - `plugins/hep-ph-toolkit/skills/sarah-build/references/saxdynkin-investigation.md:25`

8. **Runtime user-state path rename** (`~/.config/hep-ph-agents/` → `~/.config/hephaestus/`):
   - 13 path-construction sites — most critical: `plugins/shared/install-helpers/config_helpers.py` (4 occurrences, used by many; also docstring at `:3` and CLI description at `:170`)
   - ~38 test fixtures with literal `/ "hep-ph-agents"` in temp-config setup
   - 4 docs (`plugins/hep-ph-toolkit/SHARED-feynman.md`, `SHARED-model-building.md`, `bin/README.md`, `plugins/hep-ph-toolkit/skills/install/SKILL.md`)
   - Also: `bin/config_write_locked.sh`, `bin/_smoke_config_write_locked.sh`, `plugins/hep-ph-toolkit/skills/install/skill_env.yaml:55`, `plugins/hep-ph-toolkit/skills/_shared/blocker_catalog.yaml:3` (skeptic's missed-file list)
   - The ~30 files with version-assert boilerplate (`assert sys.version_info >= (3, 10), "hep-ph-agents requires Python >= 3.10"`) — confirmed survivors include `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py:32`, `plugins/hep-ph-toolkit/skills/_shared/config_migration.py:21`, and ~28 more under `plugins/hep-ph-toolkit/skills/**/scripts/`.
   - `plugins/hep-ph-toolkit/skills/_shared/config_migration.py:2,120` — module docstring "Adoption check for hep-ph-agents config.json" and CLI description (its sole purpose is to detect/migrate the legacy config-dir; rewriter must not break the *intent* — keep the legacy-detection logic, only relabel the strings).

### Post-v3 additions (new surface introduced by ModelSpec-v3)

9. **ModelSpec-v3 spec/template `authors` fields** — 5 YAML files, line 5 in each:
   - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/2hdm_a.yaml:5`
   - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/dark_su3.yaml:5`
   - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml:5`
   - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/ssm.yaml:5`
   - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/sm.yaml:5`
   - All read `authors: 'hep-ph-agents'` → change to `authors: 'hephaestus'`. The `authors` value is propagated by `render/header.py` into `Model\`Authors = "..."` in every emitted SARAH `.m`.

10. **ModelSpec-v3 render templates** — embedded `hep-ph-agents` in generated comment headers:
    - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/header.py:7` — `* Generated by hep-ph-agents /sarah-build from ModelSpec.` (template string)
    - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/parameters.py:8` — same pattern
    - `plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/render/particles.py:8` — same pattern
    - These are baked into every regeneration run; rewriter must update all three.

11. **SARAH golden fixtures regenerated by v3** — must be re-regenerated *after* items 9 and 10 are applied so the new `authors` and comment strings flow through. Four directories:
    - `plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/2hdm_a/{2hdmA.m, parameters.m, particles.m, SPheno.m}`
    - `plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/2hdm_a_fixed/{TwoHdmAfix.m, parameters.m, particles.m, SPheno.m}`
    - `plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/dark_su3/{DarkSU3.m, parameters.m, particles.m, SPheno.m}`
    - `plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/singlet_doublet/{SingletDoublet.m, parameters.m, particles.m, SPheno.m}`
    - **Don't manually edit.** Run the v3 regen path (whatever Task 19 of the v3 plan put in place — likely `python -m _shared.modelspec_v3.cli render <spec> > <golden>` or a sarah-build helper). Eyeball the resulting diff: only the `Generated by ...` comment and `Authors` line should change.

12. **Existing v1-baked fixture** (was deferred; now should be regenerated):
    - `plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/TwoHdmAfix.m:5` — still ships with `Model\`Authors = "hep-ph-agents";`. This is a per-skill fixture used by `2hdm-a` smoke/playtest paths. Regenerate via the v3 chain (or hand-edit if regen is non-trivial) so it matches the new `authors` value.

13. **Generated-code comments outside modelspec_v3 render** — sweep:
    - Mathematica/Fortran installer markers in `plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh` (lines ~127, 128, 175 emit `(* hep-ph-agents SARAH path *)` into SARAH's `init.m`)
    - `plugins/hep-ph-toolkit/skills/feynrules-install/scripts/install_feynrules.sh:41-42` emit `(* hep-ph-agents:feynrules-install BEGIN/END *)` markers
    - `plugins/hep-ph-toolkit/skills/maddm-install/scripts/install.sh` — `# hep-ph-agents: ...` comments (3 places)
    - These markers identify our injection blocks for clean removal on uninstall — the *rename of the marker string* must be coordinated with any uninstall code that greps for the old string. Check both ends before flipping.

14. **`LICENSE:178`** — `Copyright 2025 hep-ph-agents contributors` → `Copyright 2025 hephaestus contributors` (or `Copyright 2025-2026 HEPHaestus contributors` if year-bumping is desirable while we're touching it).

15. **JSON Schema `$id` URIs** — same decision as before (out of scope; URNs that don't resolve), but inventory updated post-v3:
    - `plugins/shared/schemas/{annihilation,relic,processspec,amp_reduced.meta,scattering}.schema.json` (5 schemas, `$id: https://hep-ph-agents/schemas/...`)
    - `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
    - `plugins/hep-ph-toolkit/skills/dark-matter-constraints/contracts/router_contract.schema.json`
    - **Skip.** Changing canonical `$id` URIs is a versioning event independent of the cosmetic rename. (Confirmed: v3's `_shared/modelspec_v3/schema.json` has *no* `$id` field, so it's not in this list.)

### Out of scope — DO NOT TOUCH

| Surface | Why skip |
|---|---|
| `HEPPH_*` env vars (61 vars, 546 refs, 143 files) | Domain prefix, not project name. Renaming is high-cost cosmetic with real test-isolation breakage risk. |
| JSON Schema `$id` URIs (9 schemas) | URNs that don't need to resolve. Changing canonical schema identifiers is a versioning event. |
| `.playtest/` (entire directory) | Intentional commit history — frozen snapshots of `[sd-playtest-A]` / `[sd-playtest-B]` runs. No production code or test loads from `.playtest/`. Renaming would rewrite captured history. |
| `.shift-manager/` (entire directory) | Same — captured shift logs. |
| `eval/plot_ab_test/outputs/` | Gitignored (`eval/plot_ab_test/.gitignore:2`). Regenerable artifacts. |
| `docs/` historical planning artifacts | Decision logs. Preserve the world-as-it-was. |
| Hard-coded absolute paths in 2 `gamlike` test fixtures | Already brittle (machine-specific). Refactor to relative paths is a separate concern. |
| Local clone directory `/Users/yianni/Projects/hep-ph-agents` | Local-only; user's call to `mv` whenever convenient. |

### Deferred — *resolved by v3 commit aa35885*

All v1 files the original draft deferred have been deleted by ModelSpec-v3.
Verified post-v3 (2026-04-27) — none of these paths exist on disk:

- `plugins/hep-ph-toolkit/skills/sarah-build/scripts/sections/` (entire dir, including `model_header.py` and the 6 section renderers)
- `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`
- `plugins/hep-ph-toolkit/skills/_shared/validate_one.py`
- `plugins/hep-ph-toolkit/skills/_shared/tests/test_validate_one_dispatch.py`
- `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/{singlet_doublet,dark_su3,2hdm_a}_spec.yaml`
- `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/ws1/`

The new emit point — `_shared/modelspec_v3/render/{header,parameters,particles}.py`
plus the 5 spec/template YAMLs — is now folded into "Post-v3 additions"
(items 9–12 above) as in-scope work. The 4 SARAH golden directories (which
v3 regenerated to match its new render) need a fresh regeneration after the
spec authors and render comments are updated.

---

## Execution order (commit boundaries)

Each step ends in a `git commit`. Order matters — split so any failure is
easy to revert.

**Pre-flight (manual, do once on dev box):**
- `mv` the three user-state directories. Verify `/install` preflight scan still finds tools.

### Commit 1 — Branding files (low risk)

- `git mv styles/hep-ph-agents-analytic.mplstyle styles/hephaestus-analytic.mplstyle`
- `git mv styles/hep-ph-agents-slate.mplstyle    styles/hephaestus-slate.mplstyle`
- `git mv styles/hep-ph-agents-tikz.sty          styles/hephaestus-tikz.sty`
- Edit `styles/hephaestus-tikz.sty:9` `\ProvidesPackage` arg.
- Edit `styles/hep_ph_style.py:128` (dynamic `f"hep-ph-agents-{context}"` → `f"hephaestus-{context}"`) and `:2` docstring.
- Update consumers: `eval/test_tikz.tex:10`, `theory-data-comparison/SKILL.md:91`, `demo/scripts/plot_figure.py:10,155`, `draw-feynman/SKILL.md:46`.
- Run `pytest plugins/hep-ph-toolkit/skills/theory-data-comparison/` and any plot tests; eyeball-render `eval/test_tikz.tex` if a TeX toolchain is handy.
- Smoke check: `python -c "from styles.hep_ph_style import use_style; use_style('analytic')"` (must not raise FileNotFoundError).

### Commit 2 — Repo-slug bug fix + dev-only settings

- Edit `plugins/hep-ph-toolkit/scripts/install-followup.sh:42` (the bare `'hep-ph-agents'` → `'jtamanas/hephaestus'`).
- Update `.claude/settings.json` (untracked dev cruft — note that this commit affects no tracked files; clean it up directly).
- No tests to run for this commit; `gh issue create --repo jtamanas/hephaestus` is the runtime check.

### Commit 3 — Repo-relative comments + modelspec-template comments

- `tools/check_plan.py:37`
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/two_hdm.yaml:4`
- `plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/archived/dark_su3_confining.yaml:4`
- Doc/SKILL.md textual mentions (the ~12 spots in scope item 7).

### Commit 4 — Runtime path rename (the big sweep)

A Python rewriter that handles, in order:

1. `Path / "hep-ph-agents"` (and `pathlib.Path(...) / "hep-ph-agents"`) → `Path / "hephaestus"`
2. `"hep-ph-agents"` as a quoted dirname in path-construction context (e.g. `os.path.join(..., "hep-ph-agents", ...)`)
3. `"~/.config/hep-ph-agents"`, `"~/.local/share/hep-ph-agents"`, `"~/.cache/hep-ph-agents"` literals (rare; mostly in docstrings)
4. `${XDG_CONFIG_HOME:-$HOME/.config}/hep-ph-agents/...` shell-form patterns
5. The version-assert boilerplate `"hep-ph-agents requires Python >= 3.10"` → `"hephaestus requires Python >= 3.10"` (cosmetic, ~30 files)

Files **excluded** from the rewriter:
- `plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/` — handled by Commit 5 (regenerate, don't text-patch)
- `plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/TwoHdmAfix.m` — same (regenerate)
- All JSON Schema `$id` URIs (see Scope item 15 — out of scope)

Always-excluded directories (already-historical or untouched-by-policy):
- `.git/`, `.shift-manager/`, `.playtest/`, `.claude/worktrees/`,
  `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.gstack/`,
  `.superpowers/`, `eval/plot_ab_test/outputs/`, `docs/`

After the rewriter:
- `git diff --stat` to sanity-check file count (~110-150 expected post-v3 — slightly higher than the pre-v3 estimate because v3 added ~10 new files in `_shared/modelspec_v3/` and ~30 of the version-assert assertions live there).
- Run `pytest plugins/` end-to-end. Expect zero new failures vs the pre-rename baseline. (NB: the 4 golden-comparison tests under `sarah-build/tests/` will fail until Commit 5 regenerates — leave them red across this commit.)
- Eyeball at least one rewritten test fixture (e.g. `plugins/hep-ph-toolkit/skills/spheno-install/tests/test_detect_derive_src.sh`) to confirm the rewriter handled both `mkdir -p "$cfg_dir/hep-ph-agents"` and the `cfg = '$cfg_dir/hep-ph-agents/config.json'` here-doc pattern.

### Commit 5 — ModelSpec-v3 specs, render comments, and golden regen

This commit must follow Commit 4 (so any rewriter side-effects are
already settled before the goldens are regenerated).

- Edit the 5 spec YAMLs (`specs/{2hdm_a,dark_su3,singlet_doublet,ssm}.yaml` + `templates/sm.yaml`): line 5, `authors: 'hep-ph-agents'` → `authors: 'hephaestus'`.
- Edit the 3 render templates: `render/header.py:7`, `render/parameters.py:8`, `render/particles.py:8` (the `* Generated by hep-ph-agents /sarah-build ...` strings).
- Regenerate the 4 SARAH golden directories under `sarah-build/tests/goldens/` using whatever helper v3 ships (per the v3 plan, the orchestrator at `_shared/modelspec_v3/render/orchestrator.py` plus the test runner). `git diff --stat` should show only header-comment + Authors-line changes.
- Regenerate `plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/TwoHdmAfix.m` from the v3 chain (or hand-patch line 5 if regen is gated on an external run; flag it in the commit message).
- Re-run `pytest plugins/hep-ph-toolkit/skills/sarah-build/` — should be green.
- Re-run any `2hdm-a` smoke test that loads `TwoHdmAfix.m`.

### Commit 6 — Installer markers + LICENSE

- Update marker strings emitted by installers (Scope item 13):
  - `plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh` — `(* hep-ph-agents SARAH path *)` markers (lines ~127, 128, 175)
  - `plugins/hep-ph-toolkit/skills/feynrules-install/scripts/install_feynrules.sh:41-42` — `(* hep-ph-agents:feynrules-install BEGIN/END *)` markers
  - `plugins/hep-ph-toolkit/skills/maddm-install/scripts/install.sh` — `# hep-ph-agents: ...` markers (3 places)
  - **Important:** if the corresponding uninstall paths grep for the old marker string, update them in the same commit. (Check `uninstall.sh` and any clean-up scripts for `grep 'hep-ph-agents'` patterns.)
- `LICENSE:178` — `Copyright 2025 hep-ph-agents contributors` → `Copyright 2025 hephaestus contributors`.
- Verification: re-run a tool install (or dry-run) to confirm the new marker shows up cleanly in the SARAH `init.m` / FeynRules sources, and that uninstall finds it.

### Commit 7 — Documentation + README

- `plugins/hep-ph-toolkit/SHARED-model-building.md` — runtime path table (lines 12, 13, 14, 19, 21, 65)
- `plugins/hep-ph-toolkit/SHARED-feynman.md:23` — env-var override-path comment
- `bin/README.md:88,99,114` — runtime path examples
- `plugins/hep-ph-toolkit/skills/install/SKILL.md:10` — config path callout
- `plugins/hep-ph-toolkit/skills/_shared/blocker_catalog.yaml` — header comment "hep-ph-agents project"
- `plugins/hep-ph-toolkit/skills/demo/SKILL.md:3,18` — `"show me hep-ph-agents"` user-trigger phrase + config.json path mention. (Decision: keep `"show me hep-ph-agents"` as a *legacy alias* in the trigger list so users with the old muscle memory still hit `/demo`. Add `"show me hephaestus"` alongside.)
- `CLAUDE.md` — strip the "legacy hep-ph-agents" callout block once the runtime paths are renamed (it currently exists to explain the mismatch — delete it).
- `README.md:56` — the line about `hep-ph-agents-tikz.sty` style package — point to `hephaestus-tikz.sty`.

---

## Post-rename verification

```bash
# 1. No stale runtime path refs survive in production code
git grep -E '\.config/hep-ph-agents|\.local/share/hep-ph-agents|\.cache/hep-ph-agents' \
  -- ':!docs/' ':!.playtest/' ':!.shift-manager/' ':!.claude/'

# 2. No stale "hep-ph-agents" literals survive (v3 cleared the deferral list)
git grep -nE '"hep-ph-agents"' \
  -- ':!docs/' ':!.playtest/' ':!.shift-manager/' ':!.claude/' \
     ':!plugins/shared/schemas/' \
     ':!plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json' \
     ':!plugins/hep-ph-toolkit/skills/dark-matter-constraints/contracts/'
# Schema $id URIs are deliberately excluded — out of scope (URNs).

# 3. Style-file consumers all point at the new files
git grep -E 'hep-ph-agents-(tikz|analytic|slate)'
# Expect: zero hits.

# 4. SARAH `Authors` line in goldens reflects the rename
git grep -nE 'Model`Authors' plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/ \
  plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/
# Expect: every match shows `Authors = "hephaestus";`.

# 5. modelspec_v3 specs all read `authors: 'hephaestus'`
git grep -nE "^\s*authors:" plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/ \
  plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/templates/
# Expect: every match is 'hephaestus'.

# 6. Marketplace / plugin metadata still parses
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/hep-ph-toolkit/.claude-plugin/plugin.json')); print('json OK')"

# 7. Smoke-test /install on the dev box
#    (manual): /install --tool madgraph  (should detect, not reinstall)

# 8. Full test suite
pytest plugins/ -x -q
```

---

## Appendix — full file inventory (for reference)

Post-v3 re-cataloging (2026-04-27) found **227 tracked files** mentioning
`hep-ph-agents` outside `.playtest/`, `.shift-manager/`, `docs/`, and
`.claude/` (down from 280 pre-v3 — v3's deletion of the v1 sections/
renderer and its tests removed roughly 50 files from the surface). Updated
breakdown:

- ~75 `.py` files (path construction + version-assert boilerplate)
- ~38 test-fixture files (`/ "hep-ph-agents"` in temp-config setup)
- 3 style files (`styles/{hep-ph-agents-analytic,hep-ph-agents-slate}.mplstyle` + `hep-ph-agents-tikz.sty`)
  - Note: 2 regenerable copies in `eval/plot_ab_test/outputs/` are gitignored and not in the rewriter scope.
- 7 JSON schema files (`$id` URIs — out of scope)
- ~15 SKILL.md / docstring textual mentions
- **5 modelspec_v3 spec/template YAMLs** (`authors:` field — new in v3)
- **3 modelspec_v3 render templates** (`render/{header,parameters,particles}.py` — new in v3)
- **16 SARAH golden `.m` files** under `sarah-build/tests/goldens/` (4 directories × 4 files each — regenerated by v3, regenerate again post-rename)
- 1 v1-baked fixture: `plugins/hep-ph-toolkit/skills/2hdm-a/fixtures/sarah_model/TwoHdmAfix.m`
- 6+ shell installer scripts emitting Mathematica/Fortran markers
- ~8 doc files in `plugins/hep-ph-toolkit/SHARED-*.md`, `bin/README.md`, etc.
- Misc: `install-followup.sh`, `tools/check_plan.py`, modelspec templates, `blocker_catalog.yaml`, `skill_env.yaml`, `LICENSE:178`

The rewriter targets ~110-150 files (Commit 4) plus surgical edits in
Commits 1, 2, 3, 5, 6, 7. The rest are out of scope (env vars, schemas,
history).

---

## Method note (for the next time)

This plan was assembled twice — once 2026-04-26 (pre-v3) and re-cataloged
2026-04-27 (post-v3). Both passes used the same recipe:

1. **Three parallel haiku Explore scouts** on focused, non-overlapping
   slices: (a) runtime user-state paths + path-construction code,
   (b) file/dir names + LaTeX + identifiers + doc-text, (c) env vars
   + config keys + schema fields + plugin IDs.
2. **Standard search excludes** for every scout: `.git/`,
   `.claude/worktrees/`, `.shift-manager/`, `.playtest/`, `.pytest_cache/`,
   `.ruff_cache/`, `__pycache__/`, `.gstack/`, `.superpowers/`, `docs/`,
   `eval/results_*.json`, `eval/plot_ab_test/outputs/`.
3. **Structured report format**: `file:line` + one-line context, grouped
   by category, with file-count summaries.
4. **Skeptical opus follow-up** with explicit "be ornery, verify claims,
   don't rubber-stamp" instruction — used `Bash` and `Read` to spot-check
   the scout output. The first-pass scouts undercount by ~4× without this
   step.
5. **Cross-check against in-flight plans** to identify deferred files —
   anything currently being deleted or rewritten by another plan must not
   be in the rewriter scope.

If a future refactor (post-rename) touches modelspec or sarah-build again,
re-run the same recipe to catch new project-name surface that gets baked
in. The recipe is cheap (15 minutes for the scouts, 10 for the skeptic)
and reliably catches what blind grep misses.
