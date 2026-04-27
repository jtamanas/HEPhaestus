---
name: maddm-install
description: Detect, validate, or auto-install MadDM (the MadGraph5_aMC@NLO dark-matter plugin). Orchestrates MG5's native `install maddm` command with a git-clone fallback, and verifies the resulting plugin tree.
---

## When to invoke

Use `/maddm-install` before running the `/maddm` driver skill (relic density,
direct/indirect detection) to ensure the MadDM plugin is present under an
already-installed MG5. The skill is idempotent: if MadDM is already configured
it returns `{"status":"configured"}` immediately without touching disk.

## Disk footprint

- **Tarball:** ~5 MB (`maddm_V3.2.13.tar.gz` via `mg5_aMC install maddm` or GitHub clone)
- **Installed tree:** ~3.8 MB at `~/MG5_aMC_v3_5_6/PLUGIN/maddm`
- **Build-time peak (transient):** n/a (Python plugin; no compile step beyond patching)
- **Measured 2026-04-25 on macOS arm64.** Source: du measured 2026-04-25. Requires MG5 (~665 MB) pre-installed.

MadDM is **not a standalone tool** — it lives at `<MG5_ROOT>/PLUGIN/maddm/`
and piggybacks on the Python interpreter that MG5 uses. This skill therefore
assumes that `/install` (hep-ph-demo) has already populated `madgraph_path`
in the config, and it adds MadDM on top of that.

Typical invocation order:

1. `/maddm-install detect` — check current state (no side-effects).
2. `/maddm-install use-path <dir>` — register an existing MadDM plugin dir.
3. `/maddm-install install` — run `mg5_aMC -f <script>` with `install maddm`,
   falling back to git clone of `maddmhep/maddm` on failure.

---

## Decision flow

```
/maddm-install detect
       │
       ├── config has maddm_path + valid __init__.py + version probe succeeds
       │       └── {"status":"configured","path":"...","version":"..."}   exit 0
       │
       ├── config missing / invalid BUT scan_candidates() finds a MadDM tree
       │       └── {"status":"found","path":"..."}                        exit 0
       │
       └── nothing found
               └── {"status":"missing"}                                   exit 0

/maddm-install use-path <dir>
       │
       ├── <dir>/__init__.py exists AND <MG5_ROOT>/bin/maddm executable
       │       ├── probe_maddm.sh succeeds → writes maddm_path,
       │       │   maddm_version, maddm_installed_at;
       │       │   {"status":"configured",...}                            exit 0
       │       └── probe fails → MADDM_SMOKE_TEST_FAILED blocker          exit 15
       │
       └── <dir>/__init__.py missing → MADDM_PATH_INVALID blocker            exit 16

/maddm-install install [dir]
       │
       ├── madgraph_path not set → MADGRAPH_ABSENT blocker                exit 20
       ├── MG5 version < 2.6.2 → MADGRAPH_VERSION_TOO_OLD blocker         exit 20
       ├── gfortran missing → GFORTRAN_ABSENT blocker                     exit 25
       ├── disk check (need ≥1 GB free in <MG5_ROOT> filesystem)
       ├── Primary: echo "install maddm" | <MG5_ROOT>/bin/mg5_aMC
       │       ├── success → apply_maddm_upstream_patches
       │       └── failure → fall back to git clone
       ├── Fallback: git clone https://github.com/maddmhep/maddm
       │             <MG5_ROOT>/PLUGIN/maddm
       │       └── copy PLUGIN/maddm/maddm → <MG5_ROOT>/bin/maddm
       ├── Both failed → MADDM_DOWNLOAD_FAILED blocker                    exit 12
       ├── Python interpreter mismatch → MADDM_PYTHON_MISMATCH blocker    exit 20
       ├── apply_maddm_upstream_patches (see § Upstream patches):
       │     2to3 → detab init.py/plotting.py → MGoutput.py API patch
       │     → sentinel .hepph_maddm_patches_applied_v2
       │     └── patch step fails → MADDM_PATCH_FAILED blocker            exit 13
       └── probe (probe_maddm.sh: file checks + ast.parse sweep) succeeds
               → writes maddm_path, maddm_version, maddm_installed_at
               → {"status":"installed",...}                                exit 0
```

---

## JSON status contract

`detect` and `use-path` emit JSON on **stdout**. `install` emits the final
JSON on stdout; blockers and progress logs go to stderr.

| `status` value | Meaning |
|---|---|
| `configured` | `maddm_path` set, `__init__.py` present, probe succeeded |
| `found` | MadDM plugin tree scanned on disk but not in config |
| `missing` | No MadDM plugin found anywhere |
| `installed` | Fresh install completed successfully |

Fields for `configured` / `installed`:
```json
{"status":"configured","path":"/path/to/MG5_aMC/PLUGIN/maddm","version":"3.2.13"}
```

---

## Failure modes → blockers

All blockers are emitted on **stderr** as single-line JSON conforming to
`plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

| Code | Mode | Trigger | `user_instruction` |
|---|---|---|---|
| `MADGRAPH_ABSENT` | `fatal` | `madgraph_path` not set in config | Run `/install` (hep-ph-demo) to install MG5 first, then retry `/maddm-install`. |
| `MADGRAPH_VERSION_TOO_OLD` | `fatal` | MG5 version probe returns `< 2.6.2` | Upgrade MG5 to 2.6.2 or later. MadDM 3.x pins a newer plugin API. |
| `MADDM_DOWNLOAD_FAILED` | `fatal` | Both `install maddm` (via mg5_aMC) and git-clone fallback failed | Check network connectivity to launchpad.net and github.com; retry. |
| `MADDM_PYTHON_MISMATCH` | `fatal` | MG5 runs Python 2 but MadDM requires Python 3.7+ (or vice versa) | Reinstall MG5 against a Python 3.7+ interpreter. |
| `GFORTRAN_ABSENT` | `fatal` | `gfortran` not on `$PATH` | macOS: `brew install gcc`. Debian/Ubuntu: `sudo apt-get install -y gfortran`. |
| `MADDM_SMOKE_TEST_FAILED` | `fatal` | `__init__.py` present but probe returned empty / launcher not executable, **or** the `python3 ast.parse` sweep found residual SyntaxErrors in the plugin tree | Inspect `<MG5_ROOT>/PLUGIN/maddm/` contents and `/tmp/maddm_install_mg5.log`; if the sweep flagged files, check whether upstream drift has introduced a pattern 2to3 doesn't cover. |
| `MADDM_PATH_INVALID` | `fatal` | `use-path <dir>` has no `__init__.py` | Provide the directory that contains `__init__.py` (typically `<MG5_ROOT>/PLUGIN/maddm/`). |
| `MADDM_PATCH_FAILED` | `fatal` | Post-install upstream patches (Python 2→3, MG5 3.5.6 API) failed. Most common cause: `2to3` missing on Python 3.13+ | See § Upstream patches below. Install `2to3` (`pip install 2to3` or use a 3.12 interpreter) and retry, **or** apply the three patches manually and re-run `/maddm-install validate`. |

---

## Upstream patches

MadDM 3.2.13 (the latest upstream release, tagged 2023-07-16) is distributed
as **Python 2** source and has not been ported. The official MG5 tarball at
`madgraph.phys.ucl.ac.be/Downloads/maddm/maddm_V3.2.13.tar.gz` is
byte-identical to `github.com/maddmhep/maddm@v3.2.13`; both fail to import
under any Python 3 interpreter. Additionally, MadDM 3.2.13 lags MG5 3.5.6
across four independent `banner.py`/`export_v4.py` API changes — the
signatures, attributes, and base-class fields it inherits from `RunCard`
and `ProcessExporterFortranMEGroup` were all refactored after the MadDM
v3.2.13 tag.

Six idempotent patches are applied by `apply_maddm_upstream_patches` after
a successful install (either path) and before the smoke probe:

| Patch helper | What it does | Upstream bug |
|---|---|---|
| `patch_maddm_py3_2to3` | Runs `2to3 -w -n <maddm_dir>` | MadDM 3.2.13 ships `print X`, `except E, e:`, `raise E, msg` throughout the tree |
| `patch_maddm_detab_files` | `expandtabs(8)` on `init.py` and `Templates/plotting.py` | Mixed tabs/spaces inside a single suite — legal in Python 2, `TabError` in Python 3. Only 2 files trip this; `2to3` can't resolve indentation mixtures |
| `patch_maddm_mg5_api` | `MGoutput.py:178`: `write_source_makefile(writer)` → `write_source_makefile(writer, model)` | MG5 3.5.6 added a `model` argument to `ProcessExporterFortranMEGroup.write_source_makefile` (see `madgraph/iolibs/export_v4.py:2863`). MadDM's subclass call wasn't updated |
| `patch_maddm_run_inc_touch` | `maddm_run_interface.py:3745`: touch empty `include/run.inc` before `maddm_card.write_include_file` | MG5 3.5.6 `banner.write_autodef` unconditionally reads `run.inc` (`banner.py:3437`) even when the card has no `autodef=True` params. MadDMCard has none, and MadDM output doesn't write `run.inc`, so the read raises `FileNotFoundError` and blocks the relic compute |
| `patch_maddm_custom_fcts` | `MadDMCard.default_setup`: register `custom_fcts` as an empty `str` list | MG5 3.5.6 `banner.write_include_file` reads `self["custom_fcts"]` (`banner.py:3345`); registered on `RunCardLO`/`RunCardNLO` but not base `RunCard`. MadDMCard extends `RunCard` directly and crashes with `KeyError: 'custom_fcts'` |
| `patch_maddm_dummy_fct_file` | `MadDMCard`: declare `dummy_fct_file = {}` class attribute | MG5 3.5.6 `banner.edit_dummy_fct_from_file` iterates `self.dummy_fct_file.values()` (`banner.py:3160`); same pattern as `custom_fcts` — on `RunCardLO`/`RunCardNLO` but not base `RunCard`. Crashes with `AttributeError` |

Each helper is idempotent: `2to3 -w -n` is a no-op on already-converted
source, `expandtabs(8)` is a fixed point, and the string-replacement
patches use exact substring matching (plus per-patch marker comments) so
running a second time won't double-patch. A sentinel file
`.hepph_maddm_patches_applied_v2` in the plugin root signals the
orchestrator to short-circuit; bump the version suffix when adding a new
patch to force re-run on upgrade.

The patches also apply when `use-path` registers an existing (unpatched)
install, and when `install` re-enters its idempotency fast-path on a
pre-patch-era tree — so users who ran `/maddm-install` before these
patches shipped get upgraded automatically on the next invocation, no
delete-and-reinstall required.

**Removal plan.** Each patch is a candidate for an upstream PR against
`github.com/maddmhep/maddm`. When a patch lands upstream, delete the
corresponding helper and bump the sentinel version. Track open PRs in
the code comments above each helper.

**Full rationale.** `references/maddm-workarounds.md` catalogues every
install-time patch here plus usage-time gotchas (`generate_maddm` isn't a
real command; `define darkmatter` wants a name not a PDG id; etc.) —
with symptom / cause / mitigation / where for each. Read it when
debugging a MadDM failure that's not in the blocker table, or when
considering whether to modernise.

---

## Config keys written

| Key | Value |
|---|---|
| `maddm_path` | Absolute path to the MadDM plugin dir (contains `__init__.py`) |
| `maddm_version` | Version string parsed from `<maddm_path>/version` (e.g. `3.2.13`) |
| `maddm_installed_at` | UTC ISO 8601 timestamp |

Keys **read** (must be set by `/install` before this skill can run):

| Key | Purpose |
|---|---|
| `madgraph_path` | Absolute path to the `mg5_aMC` binary — required to run `install maddm`. |

---

## Version pin and override

Pinned version: **3.2.13** (2023-07-16, from the canonical GitHub repo
`maddmhep/maddm`; Launchpad v3.2.1 is deprecated). Set in `skill_env.yaml`.

Override via environment:
```bash
HEPPH_MADDM_VERSION=3.2.0 /maddm-install install
```

The pin currently affects only the git-clone fallback (which checks out the
tagged release); the primary path lets MG5's `install maddm` decide the
version, since that is what the MG5 release expects to work with.

---

## Physics context

MadDM computes, in natural units (ℏ = c = 1):

- Relic density Ω h² via freeze-out of the Boltzmann equation dn/dt + 3Hn =
  -⟨σv⟩(n² - n_eq²), including co-annihilation channels.
- Spin-independent and spin-dependent nucleon cross-sections σ_SI^p, σ_SD^p
  (cm²), with loop corrections optional.
- Velocity-averaged annihilation cross-section ⟨σv⟩ (cm³/s) into user-specified
  final states, with s-wave / p-wave decomposition.

None of this physics is implemented in the install skill — it is a thin
orchestrator that shells out to `mg5_aMC` and validates file layout. See
`plugins/hep-ph-toolkit/skills/maddm/SKILL.md` for the driver skill that
actually computes observables.

---

## Linkage

- Shared Bash helpers: `plugins/shared/install-helpers/_common.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Upstream skill (must run first): `plugins/hep-ph-toolkit/skills/install/` (sets `madgraph_path`)
- Downstream skill (driver): `plugins/hep-ph-toolkit/skills/maddm/`
- gfortran check pattern reused from: `plugins/hep-ph-toolkit/skills/spheno-install/scripts/check_gfortran.sh`
