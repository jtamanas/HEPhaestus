# Installing MadGraph5_aMC@NLO

This reference is loaded into context by any runner skill (e.g.
`/madgraph`) when its preflight reports MadGraph as missing or
mis-registered. `/install madgraph` and bundle entries (`profumo-paper`,
etc.) drive the same detect / install scripts.

## Pinned version

- **MadGraph5_aMC@NLO 3.5.6** (override with `HEPPH_MG5_VERSION`).
- Source: <https://launchpad.net/mg5amcnlo/3.0/3.5.x/+download/MG5_aMC_v3.5.6.tar.gz>

## Prerequisites

- Python 3.9+
- gfortran (used by tree-level/loop processes that compile MG5 templates)
- A C/C++ compiler (`gcc`/`g++`)
- ~3 GB free under `$HOME` (or `--install-dir`)

## Detection

`detect.sh` runs a two-tier check:

1. **Config fast path** — reads `~/.config/hephaestus/config.json`. Exit 0
   when `madgraph_path` exists on disk and `madgraph_version` matches the
   pin.
2. **Slow probe** — defers to `install_mg5.sh detect`, which parses the
   `--help` banner to extract the version string.

`HEPPH_FORCE_PROBE=1` skips the fast path.

## Install

`bash install.sh install [dir]` delegates to the canonical
`plugins/hep-ph-toolkit/skills/install/scripts/install_mg5.sh`. Default
install directory: `$HOME/MG5_aMC`.

The script:

1. Checks gfortran is on PATH.
2. Downloads + extracts the pinned tarball.
3. Symlinks `MG5_aMC -> MG5_aMC_v3_5_6`.
4. Runs a smoke test (`generate e+ e- > mu+ mu-`).
5. Records `madgraph_path` + `madgraph_version` in config atomically.

## Use-path (register an existing install)

`bash install.sh use-path /abs/path/to/mg5_aMC` validates the binary,
parses its version, and writes config.

## Side-effects

- Creates/overwrites `<install_dir>/MG5_aMC_v3_5_6/`.
- Maintains `<install_dir>/MG5_aMC` symlink at the active version.
- Writes config keys `madgraph_path`, `madgraph_version`,
  `madgraph_installed_at`.
- Does NOT modify shell rc files, `init.m`, or other dotfiles.

## Interaction with MadDM

`/maddm`'s install path (`_shared/installs/maddm/install.sh`) shells out
to MG5's own `install maddm` command, which pulls a compatible MG5 if
none is registered. That transitive path remains; `/install madgraph`
exists for users who want to seed MG5 explicitly first (e.g. for
`/madgraph` runs that don't go through MadDM).

## Blocker codes

| Code | Meaning |
|---|---|
| `MG5_DOWNLOAD_FAILED` | Tarball fetch / SHA verify failed |
| `MG5_BUILD_FAILED` | Smoke test exited non-zero |
| `MG5_PATH_INVALID` | `use-path` argument is not an executable mg5_aMC |

## Smoke test

```sh
$HOME/MG5_aMC/bin/mg5_aMC --help | head -5
```

Should print the MadGraph banner with version `3.5.6`.
