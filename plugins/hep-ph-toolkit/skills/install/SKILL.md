---
name: install
description: Bundle front door for hephaestus tool installs. Pick a use-case bundle (profumo-paper, dm-relic, dm-direct-detection, dm-indirect, one-loop, bsm-model-building) or a single tool by name, and the orchestrator drives the per-tool detect.sh + install.sh under `_shared/installs/<tool>/`. Invoke when the user says "install", "set up <tool>", "configure hephaestus", "what tools are available", or before starting a workflow that needs multiple tools.
---

# /install

Bundle front door for installing hephaestus's external tools. Every
successful per-tool install writes to a single unified config at
`~/.config/hephaestus/config.json` (or
`$XDG_CONFIG_HOME/hephaestus/config.json`). Downstream skills read that
config to locate every tool.

This skill does **not** carry tool-specific install logic. It enumerates
bundles and runs them by delegating directly to
`plugins/hep-ph-toolkit/_shared/installs/<tool>/{detect,install}.sh`
— the same scripts each runner skill's preflight uses. There is one
detect/install code path per tool, regardless of how it's invoked.

---

## Bundles

| Bundle              | Tools                                                     |
|---------------------|-----------------------------------------------------------|
| profumo-paper       | sarah, spheno, maddm, micromegas, looptools, formcalc     |
| dm-relic            | maddm, micromegas                                         |
| dm-direct-detection | micromegas, ddcalc                                        |
| dm-indirect         | maddm                                                     |
| one-loop            | looptools, formcalc, feynarts                             |
| bsm-model-building  | sarah, spheno, feynrules                                  |

The canonical bundle definitions live at
`scripts/bundles.json` and are enumerable at runtime — `/install` does
not hardcode the table above. Bumping a bundle is a one-line edit.

**Wolfram Engine** and **MG5_aMC@NLO** are not enumerated as bundle
entries. They are pulled in transitively: SARAH's `install.sh`
delegates to `scripts/install_wolfram.sh`, MadDM's delegates to
`scripts/install_mg5.sh`. Both legacy installers remain in
`scripts/` and are reused as-is.

---

## Invocation

```bash
# Bundle (multi-tool, declaration-order):
bash scripts/bundle_install.sh --bundle profumo-paper

# Single tool (matches today's mental model of /sarah-install et al.):
bash scripts/bundle_install.sh --tool sarah

# Ad-hoc tool list:
bash scripts/bundle_install.sh --tools looptools,formcalc
```

For each tool the orchestrator:

1. Runs `_shared/installs/<tool>/detect.sh`. **Exit 0** → log
   "[OK] <tool> already installed" and skip to the next tool.
2. **Exit non-zero** → run `_shared/installs/<tool>/install.sh`. The
   per-tool `INSTALL.md` documents the blocker codes the install can
   return; the agent loads it into context to walk the user through
   any interactive steps.
3. After install completes, re-run `detect.sh`. If it still fails,
   exit with the install script's exit code; the bundle halts.

### Bundle resumption is detect-driven

There is **no** stored "current step" cursor for a bundle. Re-invoking
`/install <bundle>` after a halt re-runs `detect.sh` for every tool;
tools that completed pass their fast path (~5 ms each) and are skipped,
so the bundle effectively resumes at the first tool whose `detect.sh`
still fails. Implications:

- `detect.sh` must be cheap on the fast path (it is: config lookup +
  on-disk path stat).
- Each `install.sh` must leave config in a consistent state on partial
  completion — no recorded path until the install verifies.
- Bundle order matters when later tools depend on earlier ones (e.g.
  `formcalc` after `looptools`); the table above fixes the order.

A test fixture in `scripts/tests/test_bundle_resume.sh` covers this
contract: pre-populate config with N-1 tools registered, leave one
missing, run the bundle, assert only the missing tool's `install.sh`
is invoked.

### Halts that are NOT failures

Two install scripts can return a non-zero "you must do something
out-of-band first" code that the runner should NOT retry:

| Tool  | Code | Meaning                                                  | Resolution |
|-------|------|----------------------------------------------------------|------------|
| sarah | activation_required (status JSON; exit 0) | Wolfram Engine needs interactive activation | User runs `wolframscript --activate`, then re-invokes `/install <bundle>` |
| drake | 18 (`manual_download_required`) | hepforge Anubis bot-protection blocked the download | User downloads tarball via browser, saves to `~/Downloads/` or `~/drake/`, then re-invokes |

In both cases the bundle halts, the user takes the action, then the
detect-driven resume picks up where it left off.

---

## Tool inventory

The available tools are exactly the directories under
`plugins/hep-ph-toolkit/_shared/installs/`. There is no separate
hardcoded enumeration here. As of 2026-04-29 the eleven tools are:

```
ddcalc      drake       feynarts    feynrules   formcalc
higgstools  looptools   maddm       micromegas  sarah       spheno
```

Plus two transitive prerequisites that live in `scripts/`:
`install_wolfram.sh` (pulled in by `sarah/install.sh`,
`feynrules/install.sh`, `drake/install.sh`) and `install_mg5.sh`
(pulled in by `maddm/install.sh`).

Each `_shared/installs/<tool>/` carries:

- `INSTALL.md` — reference doc (no skill frontmatter): what to install,
  prerequisites, blocker codes, smoke test.
- `detect.sh` — fast-path config check then optional slow binary
  probe. Exit 0 = ready.
- `install.sh` — full installer. Returns 0 on success, documented
  non-zero codes on activation_required, manual_download_required,
  download_failed, build_failed, etc.
- `tests/` — unit tests for the per-tool scripts.

---

## Disk footprint (approximate)

For full-bundle planning. All measurements were made on macOS arm64,
2026-04-25.

| Tool | Tarball | Installed | Path |
|---|---|---|---|
| Wolfram Engine 14.3.0 | ~3 GB DMG | ~7.6 GB | `/Applications/Wolfram Engine.app` |
| SARAH 4.15.3 | ~30 MB | ~71 MB | `~/SARAH/SARAH-4.15.3` |
| SPheno 4.0.5 | ~10 MB | ~69 MB | `~/SPheno/SPheno-4.0.5` |
| MadGraph5 3.5.6 | ~80 MB | ~665 MB | `~/MG5_aMC_v3_5_6` |
| MadDM 3.2 | ~5 MB | ~50 MB | `<MG5>/PLUGIN/maddm` |
| micrOMEGAs 6.0.5 | ~30 MB | ~150 MB | `~/micrOMEGAs/micromegas_6.0.5` |
| LoopTools 2.16 | ~600 KB | ~13 MB | `~/LoopTools/LoopTools-2.16` |
| FormCalc 9.10 | ~5 MB | ~40 MB | `~/FormCalc/FormCalc-9.10` |
| FeynArts 3.11 | ~2 MB | ~10 MB | `~/FeynArts/FeynArts-3.11` |
| FeynRules 2.3.49 | ~3 MB | ~20 MB | `~/FeynRules/feynrules-current` |
| DDCalc 2.2.0 | ~5 MB | ~30 MB | `~/DDCalc/DDCalc-v2.2.0` |
| HiggsTools 5.10.2 | ~10 MB | ~60 MB | `~/HiggsBounds-5/build` |
| DRAKE 1.0 | ~1 MB | ~5 MB | `~/drake` |

The `profumo-paper` bundle (sarah, spheno, maddm, micromegas,
looptools, formcalc) totals roughly **9 GB** including Wolfram + MG5
transitively. Recommend ~12 GB free for a clean install.

---

## Migration note (2026-04-29)

The eleven `*-install` skills (`/sarah-install`, `/spheno-install`,
etc.) were collapsed into `_shared/installs/<tool>/` references with
self-healing runners in [the install skill refactor][refactor]. Their
prior invocation URLs are gone; references to `/<tool>-install` in
historical docs should be read as "see
`_shared/installs/<tool>/INSTALL.md`".

[refactor]: ../../../../docs/superpowers/specs/2026-04-28-install-skill-refactor-design.md
