---
name: maddm
description: MadDM — dark matter relic density, direct detection cross-sections, indirect detection rates, parameter scans with experimental limit comparison
---

# MadDM

Interface for MadDM, a MadGraph5 plugin for dark matter phenomenology. Computes relic density (Omega h^2), spin-independent and spin-dependent nucleon cross-sections, and velocity-averaged annihilation cross-sections <sigma v>.

MadDM runs within a MG5 session — it is not a standalone tool. It requires a UFO model with a designated dark matter candidate. For the underlying MG5 setup and card manipulation, see the **madgraph** skill. (Parton showering of MG5 events is left to an external Pythia8 driver; a dedicated `pythia-config` skill is on the roadmap.)

## Preflight: MadDM

Before any other action, run:

    bash plugins/hep-ph-toolkit/_shared/installs/maddm/detect.sh

- **exit 0** → MadDM is installed and registered in config; proceed.
- **exit non-zero** → MadDM is missing or misconfigured. Load
  `plugins/hep-ph-toolkit/_shared/installs/maddm/INSTALL.md` into
  context and follow it. When the install completes, re-run `detect.sh`
  before proceeding. If it still fails, halt with the blocker code from
  the install reference.

Note: if MadDM is missing, `install.sh` invokes `MG5_aMC>install maddm`
which is a multi-minute interactive build — surface a clear notice to
the user before triggering it.

## Decision Tree

**What are you trying to do?**

### Install MadDM or set up a DM model?

Read: `references/setup.md`

Covers: `install maddm` command within MG5, UFO model requirements for DM candidates (PDG ID conventions, `DMParticle` flag), MadDM version compatibility with MG5 versions, required Python dependencies (numpy, scipy).

### Compute relic density, direct detection, or indirect detection?

Read: `references/observables.md`

Covers: freeze-out relic density calculation with co-annihilation, SI and SD nucleon cross-sections (tree-level and loop), velocity-averaged annihilation cross-section with channel decomposition (s-wave, p-wave), maddm_card.dat settings for each observable.

### Run parameter scans or compare to experimental limits?

Read: `references/scanning.md`

Covers: defining parameter grids in maddm_card.dat, batch orchestration and parallelization, collecting and merging results, comparing against LUX-ZEPLIN, XENONnT, PICO-60 (direct), Fermi-LAT, MAGIC (indirect).

## Quick Reference

### Running a MadDM session script

Always pass `--mode=maddm` when invoking `mg5_aMC` on a script that
issues `generate relic_density` / `generate direct_detection` /
`generate indirect_detection`:

```bash
mg5_aMC --mode=maddm <script.mg5>
```

Bare `mg5_aMC <script.mg5>` loads the base MG5 interpreter without the
MadDM plugin; the `generate relic_density` line then fails with
`InvalidCmd: The command "generate" has an error`. See
`_shared/installs/maddm/INSTALL.md` for the plugin-loader
mechanics.

**Mandatory after every launch:** verify the launch actually wrote results
before parsing anything from stdout —

```python
maddm_run.assert_launch_produced_output(
    out_dir, returncode=proc.returncode, stdout_tail=proc.stdout,
)
```

`mg5_aMC` can exit 0 having written no output while echoing the Planck
constant (`Omega h^2 = 1.2000e-01`) as if computed — see the DECAY1L gotcha
below. The guard raises `MADDM_LAUNCH_NO_OUTPUT` (recoverable) when no
`output/run_*/MadDM_results.txt` exists. Pair it with a fresh output dir
(`generate_maddm_script` default `fresh=True`): the check resolves the newest
results file by mtime, so a reused dir could satisfy it with a *previous*
run's stale results.

### Key Commands

| Command | Description |
|---------|-------------|
| `install maddm` | Install MadDM plugin in MG5 session |
| `import model <path>` | Load UFO model (basename of path must match target dir — see Gotchas) |
| `define darkmatter <name>` | Designate DM candidate (lowercase name — MG5 normalises) |
| `generate relic_density` | High-level entry: DM + coannihilators freeze-out — use this, not `generate <dm> <dm>~ > all all` |
| `generate direct_detection` | High-level entry: SI/SD cross-sections |
| `generate indirect_detection` | High-level entry: <sigma v> and spectra |
| `output <dir>` | Create output directory |
| `launch -f` | Run non-interactively with the cards in `<dir>/Cards/` |

### Observable Summary

| Observable | Symbol | Units | Experimental reference |
|-----------|--------|-------|----------------------|
| Relic density | Omega h^2 | dimensionless | 0.1200 +/- 0.0012 (Planck 2018) |
| SI proton xsec | sigma_SI^p | cm^2 | ~10^-47 at 30 GeV (LZ 2022) |
| SD proton xsec | sigma_SD^p | cm^2 | ~10^-42 (PICO-60) |
| Annihilation xsec | <sigma v> | cm^3/s | ~3e-26 (thermal relic) |

### Common DM UFO Models

| Model | Description | DM candidate (PDG ID) |
|-------|-------------|----------------------|
| `DMsimp_s_spin0` | Simplified, scalar mediator | chi (9000006) |
| `DMsimp_s_spin1` | Simplified, vector mediator | chi (9000006) |
| `DMscalar` | Real scalar DM + Higgs portal | S (9000006) |
| `Inert_Doublet` | Inert doublet model | H0 (35) |
| `MSSM_SLHA2` | MSSM (neutralino DM) | n1 (1000022) |

### Key maddm_card.dat Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `dm_candidate` | PDG ID of DM particle | auto-detected |
| `relic_density` | Compute Omega h^2 | ON |
| `direct_detection` | Compute sigma_SI, sigma_SD | OFF |
| `indirect_detection` | Compute <sigma v> | OFF |
| `loop` | Include loop corrections for DD | OFF |
| `sigmav_method` | `madevent` or `reshuffling` | `madevent` |

## Gotchas

### MG5 lowercases UFO particle names on `import model`

MG5 logs "Change particles name to pass to MG5 convention" when loading a
UFO and silently converts every particle name to lowercase for the rest of
the session. A UFO that declares `Chi1 = Particle(...)` is addressable only
as `chi1` after import, so `define darkmatter Chi1` raises
`DMError: Chi1 is not a valid particle for the model`. Use lowercase names
in every post-import command (`define darkmatter`, `generate`, etc.).
`generate_maddm_script` lowercases string `dm_candidate` automatically;
hand-written MG5 sessions must do it explicitly.

### Use `generate relic_density`, not `generate <dm> <dm>~ > all all`

MadDM 3.2's high-level `generate relic_density` entry assembles the full
annihilation + coannihilation set automatically — including same-sign
initial states (e.g. `chi1 chi2`, `chip chim` for models with charged
partners). A bare MG5 process generation like
`generate chi1 chi1~ > all all` only covers chi1 self-annihilation and
drops every coannihilation channel, biasing Omega h^2 upward by factors
of 2–10× in regions where the next-lightest BSM state is within
~T_f ≈ m_chi/20 of the DM candidate. Always prefer the high-level entry.
`generate_maddm_script` emits it; if you author a session by hand, use
`generate relic_density` for relic, `generate direct_detection` for DD,
`generate indirect_detection` for ID.

### Pass a UFO path whose basename matches the target directory basename

MG5's `import model <path>` uses the path's basename to re-resolve the
model directory against its parent, not to follow a symlink target. A
symlink named `ufo` pointing to `sarah_output/UFO/SingletDoublet/` makes
MG5 look for `sarah_output/UFO/ufo/`, which does not exist. `/sarah-build`
now emits a `state_dir/<sarah_name>` symlink (basename matches target)
rather than `state_dir/ufo`; pass `config.models[<name>].ufo` directly, or
use the realpath under `sarah_output/UFO/<sarah_name>/`.

### `output <dir>` refuses to overwrite an existing directory

If `<dir>` already exists, MG5 aborts Phase 1 rather than clobbering it,
so a rerun of the two-phase overlay pattern fails on the second invocation
unless the directory is cleared first. `generate_maddm_script` (fresh=True,
the default) emits the cleanup as a `!rm -rf <out_dir>` shell-escape line
*inside* the returned script, immediately before `output <out_dir>` — MG5's
cmd interpreter runs a `!`-prefixed line as a raw shell command. The
deletion therefore happens when the script is **run** by `mg5_aMC`, not when
it is generated; generating a script never touches the filesystem. Applies
to every `generate_maddm_script` caller, not just the split-for-overlay path
(the cleanup line lives in the setup half there, since that's the half
ending in `output`).

### Frozen-SI DD-rerun staleness — recompute fresh, then gate on the value

MadDM `direct_detection`-only reruns can serve a **stale / frozen** σ_SI: the
DD-assembly path does not always re-read the param card, and a reused `output`
dir keeps the previously compiled DD matrix elements, so σ_SI stays
**bit-identical across genuinely different coupling points** — the canonical
symptom is a σ_SI frozen at the sentinel `2.4258097266847696E-31 GeV⁻²`
regardless of the Higgs-portal coupling. This is an upstream MadDM
DD-assembly bug, not a param-card content problem (contrast the zeroed-Higgs
gotcha below, which *is* a card problem).

Two defenses, both live in the `maddm` skill:

1. **Fresh recompute by default (prevention).**
   `scripts/maddm_run.py::generate_maddm_script` emits a `!rm -rf <out_dir>`
   shell-escape line into the session script itself, right before
   `output <out_dir>`, so the output dir is cleared when the script **runs**
   (via `mg5_aMC`) — not when it is generated. Generating the script is a
   pure, side-effect-free operation on the filesystem; only executing it
   deletes anything, and only immediately before the `output` step that needs
   a clean directory. Every run recompiles from the current param card. Pass
   `fresh=False` only when you deliberately want to reuse an existing dir and
   accept the staleness risk — no cleanup line is emitted in that case. The
   standalone `prepare_output_dir(out_dir, fresh=True)` helper (a plain
   `shutil.rmtree`) still exists for callers driving their own imperative MG5
   session instead of handing a generated script to `mg5_aMC`.

2. **Loud staleness guard (detection).**
   `scripts/staleness.py::detect_stale_dd(si_value, previous_si=…,
   previous_params_hash=…, current_params_hash=…)` flags staleness when the
   parsed σ_SI equals the frozen sentinel, or is bit-identical to a prior run
   whose param-card fingerprint differs. When stale it returns (and
   `check_and_emit` prints on stderr) the recoverable blocker
   **`MADDM_STALE_DD_RESULT`** (registered in
   `_shared/blocker_catalog.yaml`), whose `user_instruction` points back to the
   fresh-output-dir workaround. Always confirm σ_SI *responds* to coupling
   changes before trusting it.

3. **SLHA provenance check (right-card gate).**
   Before a `direct_detection` run, call
   `scripts/maddm_run.py::check_slha_provenance(model, slha_path,
   observables=["direct_detection"])` on the SLHA/param card you are about to
   overlay onto `Cards/param_card.dat`. It fingerprints that card and compares
   it against the `latest_slha` provenance recorded for the model by
   `spheno-build` / `lagrangian-builder` (via
   `config_helpers.register_latest_slha`), and prints a loud `WARNING:` (naming
   both paths + sha256 and a "re-run SPheno / register the spectrum"
   remediation) when the card is not the model's latest registered spectrum —
   the most common cause of a DD number that describes the wrong point. It is
   **non-fatal by default** (returns a result dict, never raises; skips
   non-DD-only runs; stays quiet on an exact match and on pre-guard configs it
   cannot verify), so it is backward compatible. Pass `fatal=True` to raise
   `SlhaProvenanceMismatch` instead. This complements — does not replace — the
   value-level staleness guard above: provenance catches the *wrong card going
   in*, staleness catches a *stale value coming out*.

### SARAH/SPheno SLHA silently zeroes the DD Higgs channel

When the UFO comes from SARAH and the SLHA from SPheno, the SPheno spectrum
frequently **omits** the SM quark rotation matrices (`UDLMIX`/`UDRMIX`/
`UULMIX`/`UURMIX`) and the field-redefinition phase (`PHASES`/`IMPHASES`) —
it only prints a mixing block when it is non-trivial. The UFO declares these
as *external* parameters defaulting to `0.`, so after the SLHA overlay
MadGraph reads `0` for every missing entry. For a rotation matrix that is the
**zero** matrix, not the identity: it collapses the rotated Higgs-quark Yukawa
`ZDL†·Yd·ZDR` to zero and deletes the entire Higgs t-channel from
`generate direct_detection`. The symptom is a spin-independent cross-section
frozen at the ~1e-58 cm² spin-independent *vector floor* (pure Z exchange),
independent of the model's Higgs-portal coupling — while σ_SD looks normal.

Fix: after overlaying the SLHA onto `Cards/param_card.dat` and **before**
`launch -f`, call
`maddm/scripts/slha_complete.py::complete_sarah_param_card(card, ufo_path)`.
It reads the UFO's external blocks and fills absent rotation matrices with the
identity (imaginary partner zero) and absent phases with unity, leaving blocks
SPheno did write untouched. Gate on the value, not the log: a `mdl_… not found`
warning is neither necessary nor sufficient — patching one coupling can clear
the warning while σ_SI stays on the floor. See
`singlet-doublet/SKILL.md` step 4e for the reference wiring and the σ_SI gate.

### SPheno's `DECAY1L` block crashes `launch -f` while it exits 0 (silent no-op)

A spectrum from `--backend spheno` carries a **1-loop `DECAY1L`** block (loop-
corrected partial widths, e.g. for the top and the Higgs) alongside the tree-
level `DECAY`. MG5's `param_card.dat` reader does not recognise `DECAY1L` as a
block keyword and crashes parsing its BR sub-lines
(`InvalidParam : line was ['l', '6', '1.38499650e+00']`). The crash happens
**inside `launch -f`**, but the enclosing `mg5_aMC --mode=maddm` process still
**exits 0** and stdout still prints `INFO: Omega h^2 = 1.2000e-01 +- 1.2000e-03`
— **that line is MadDM echoing the Planck reference constant loaded before the
crash, not a computed relic density.** No `output/run_01/` is created. Reading
stdout for `Omega h^2 = …` without checking that `MadDM_results.txt` exists
silently reports the Planck fiducial (0.1200) as the model's relic density — a
nasty trap because 0.1200 looks like a "landed on the relic band" success.

Two-layer fix, both in place:
- **Strip:** `complete_sarah_param_card` (and the standalone
  `slha_complete.strip_maddm_indigestible_blocks`) now removes any `DECAY1L`
  block before overlay, so every documented recipe that routes through the
  card-prep step is fixed automatically. SPheno legitimately emits `DECAY1L`;
  only MG5 can't digest it.
- **Loud guard:** after the launch subprocess returns, call
  `maddm_run.assert_launch_produced_output(out_dir, returncode=rc, stdout_tail=…)`.
  It raises `MADDM_LAUNCH_NO_OUTPUT` (recoverable) when no
  `output/run_*/MadDM_results.txt` exists — protecting the whole no-output
  class, not just `DECAY1L`. A returncode of 0 is **not** evidence of success.

## File Map

| Path | Description |
|------|-------------|
| `references/setup.md` | MadDM installation and UFO model requirements |
| `references/observables.md` | Relic density, DD, ID computation details |
| `references/scanning.md` | Parameter scans and experimental limit comparison |
| `references/reading-output.md` | Diagnostics-only manual parse of `MadDM_results.txt` (prefer `/gamlike`) |
| `scripts/maddm_run.py` | MadDM session script generator (`generate_maddm_script`); launch-no-output guard (`assert_launch_produced_output`, `MADDM_LAUNCH_NO_OUTPUT`) |
| `scripts/slha_complete.py` | SARAH param-card completion (`complete_sarah_param_card`) + MG5-indigestible-block strip (`strip_maddm_indigestible_blocks`, e.g. `DECAY1L`) |
| `scripts/staleness.py` | Frozen-SI DD-rerun staleness detector (`detect_stale_dd`, `MADDM_STALE_DD_RESULT`) |
| `scripts/scan_grid.py` | Grid generation and batch orchestration |
| `scripts/limits.py` | Experimental exclusion curve loading and comparison |
| `assets/limit_data/README.md` | Pointers to public experimental limit data |

### Reading MadDM output

**Use `/gamlike` to parse `MadDM_results.txt`.** The canonical parser is
`plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py`; it emits
a `gamlike/v1` JSON document covering every section MadDM 3.2 writes. For
diagnostics when `/gamlike` is unavailable, the agent-driven prose extraction
(field-by-field line patterns + the `gamlike/v1` DD JSON shape) is in
[`references/reading-output.md`](references/reading-output.md).

The router-canonical output field names this skill produces (kept inline here so
the `/dark-matter-constraints` router-field contract resolves them against the
producer SKILL.md; full extraction detail lives in `references/reading-output.md`):

- **Ωh²** — line matching `Omegah2 = <value>` (MadDM 3.2+) or `Omega h^2 = <value>`
  (legacy). Router-canonical field name: `Omegah2`.
- **Spin-independent proton cross-section** — from `SigmaN_SI_p = [<sigma>, <lim>]`
  (cm²). Router-canonical field name: `sigma_si_proton`.
- **Spin-dependent proton cross-section** — from `SigmaN_SD_p = [<sigma>, <lim>]`
  (cm²). Router-canonical field name: `sigma_sd_proton`.
- **Total annihilation cross-section** — line matching `sigmav_xf = <value>`
  (cm³/s) in the Relic Density section. (Earlier MadDM 3.2 outputs labeled this
  `sigmav_total`; treat the two as aliases — the `sigmav_total` canonical rename
  is still pending in the router contract.)

### Cross-Skill Dependencies

- **param_card manipulation**: Use `madgraph/scripts/card_io.py` — the SLHA parser is shared, not duplicated.
- **MG5 process generation**: If you need to generate DM signal events (not just compute observables), use the **madgraph** skill for process definition and the **maddm** skill for the DM-specific observables.
