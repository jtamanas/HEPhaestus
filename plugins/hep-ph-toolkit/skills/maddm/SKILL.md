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
unless the caller clears the directory first. Before Phase 1, do
`shutil.rmtree(out_dir, ignore_errors=True)` (or equivalent). Applies to
every `generate_maddm_script` caller, not just the split-for-overlay path.

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

## File Map

| Path | Description |
|------|-------------|
| `references/setup.md` | MadDM installation and UFO model requirements |
| `references/observables.md` | Relic density, DD, ID computation details |
| `references/scanning.md` | Parameter scans and experimental limit comparison |
| `scripts/maddm_run.py` | MadDM session script generator (`generate_maddm_script`) |
| `scripts/scan_grid.py` | Grid generation and batch orchestration |
| `scripts/limits.py` | Experimental exclusion curve loading and comparison |
| `assets/limit_data/README.md` | Pointers to public experimental limit data |

### Reading MadDM output

**Use `/gamlike` to parse `MadDM_results.txt`.** The canonical parser is `plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py`. It emits a `gamlike/v1` JSON document covering every section MadDM 3.2 writes. The agent-driven prose extraction documented below is retained for diagnostics; new consumers should call `/gamlike`.

#### Reading MadDM output (agent-driven, diagnostics only)

After `launch -f` completes, MadDM 3.2+ writes results to
`<out_dir>/output/run_01/MadDM_results.txt`. Open that file and extract:

- **Omega h^2**: line matching `Omegah2 = <value>` (MadDM 3.2+) or
  `Omega h^2 = <value>` (legacy). Example: `Omegah2                       = 2.92e-01`
- **Spin-independent cross-sections (per-nucleon)**: lines matching
  `SigmaN_SI_p = [<sigma>, <exp_limit>]` and `SigmaN_SI_n = [<sigma>, <exp_limit>]`
  (cm²). The bracket-pair is `[σ_DM_at_this_mass, σ_experiment_90CL_limit]`;
  the comment after `#` names the experiment used for the limit (e.g. `# Xenon1ton`).
  The router-canonical field name for the proton SigmaN_SI value is `sigma_si_proton`.
- **Spin-dependent cross-sections (per-nucleon)**: lines matching
  `SigmaN_SD_p = [<sigma>, <exp_limit>]` and `SigmaN_SD_n = [<sigma>, <exp_limit>]`
  (cm²). Same bracket convention as SI. The router-canonical field name for the
  proton SigmaN_SD value is `sigma_sd_proton`.
- **Total annihilation cross-section**: line matching
  `sigmav_xf = <value>` (cm³/s) inside the Relic Density section. (Earlier
  MadDM 3.2 outputs labeled this `sigmav_total`; treat the two as aliases.)
- **Per-channel percentages** (MadDM 3.2+): lines matching
  `%_chi1chi1_<channel> = <pct> %` (e.g. `%_chi1chi1_zz = 17.84 %`)

The canonical `gamlike/v1` shape for the DD section:

```json
"direct": {
  "present": true,
  "sigma_si_proton_cm2":  <float>,
  "sigma_si_neutron_cm2": <float>,
  "sigma_sd_proton_cm2":  <float>,
  "sigma_sd_neutron_cm2": <float>,
  "lim_si_proton_cm2":    <float>,
  "lim_si_neutron_cm2":   <float>,
  "lim_sd_proton_cm2":    <float>,
  "lim_sd_neutron_cm2":   <float>,
  "results": [
    {"name": "SigmaN_SI_p", "experiment_label": "Xenon1ton", "sig_cm2": ..., "lim_cm2": ...},
    ...
  ]
}
```

Each named field is `null` if MadDM's output omitted that nucleon line (rare;
fail loud rather than silently consuming `null` downstream). The `results` list
preserves the generic per-key transport, including the experiment label parsed
from the inline comment. Fail loudly if `MadDM_results.txt` is not found.

### Cross-Skill Dependencies

- **param_card manipulation**: Use `madgraph/scripts/card_io.py` — the SLHA parser is shared, not duplicated.
- **MG5 process generation**: If you need to generate DM signal events (not just compute observables), use the **madgraph** skill for process definition and the **maddm** skill for the DM-specific observables.
