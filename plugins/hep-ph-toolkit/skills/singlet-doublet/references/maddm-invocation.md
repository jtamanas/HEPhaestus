# MadDM invocation — two-phase SLHA overlay

Both the relic branch (Step 4c) and the direct-detection branch (Step 4e)
drive `/maddm` the same way, differing only in the `observables` list and the
parsing of the result. This file is the single source of that pattern; both
steps point here.

## Why two phases

`Cards/param_card.dat` is created by `output <out_dir>` and consumed by
`launch -f`. In a single MG5 session there is no gap between the two in which
to overlay the SPheno SLHA, so emit the session as two scripts via
`generate_maddm_script(..., split_for_param_overlay=True)` and run each with
`mg5_aMC --mode=maddm`.

`mg5_aMC --mode=maddm` is required — bare `mg5_aMC <script>` loads the base
interpreter without the MadDM plugin and `generate relic_density` raises
`InvalidCmd`. See `maddm/SKILL.md` Quick Reference.

## Shared inputs

- `ufo_path` = `config.models.singlet_doublet.ufo` (the
  `state_dir/SingletDoublet` symlink from `/sarah-build` — its basename
  matches the target directory, which MG5 `import model` requires).
- `dm_candidate` = `"chi1"` (lowercase — MG5 normalises UFO particle names on
  import; see `/maddm` §Gotchas).
- `param_card_source` = `config.models.singlet_doublet.latest_slha` (the SPheno
  `SPheno.spc` produced in Step 4b) — overlaid on `Cards/param_card.dat` before
  `launch` so MadDM reads the SLHA-formatted mass spectrum + mixing matrices
  (`MASS`, `BSMPARAMS`, `ZNMIX`, `UMMIX`, `UPMIX`, `HMIX`, `GAUGE`, `SMINPUTS`,
  `PHASES`) directly.

## `generate relic_density`, never a hand-written process

The `generate relic_density` entry assembles the full coannihilation set
(chi1+chi2, chi1+chi3, chi+ chi−, …). Do **not** substitute
`generate chi1 chi1~ > all all`, which silently drops coannihilators and biases
`Omega h^2` upward near thresholds.

## `chi1` is Majorana

UFO `particles.py` declares `chi1` with `antiname = 'chi1'` and
`self_conj = True`, so MadDM treats `chi1 chi1` and `chi1 chi1~` as the same
initial state; no extra flag is required.

## MadDM version-validation warning (expected, non-fatal)

When MadDM 3.2 is loaded with MG5 3.5.6, MadGraph emits:

```
Warning: PLUGIN.maddm has marked as NOT being validated with this version.
Validated last with version 2.9.9
```

This warning is cosmetic. MadDM 3.2 runs correctly with MG5 3.5.6 — the
observable is computed and `MadDM_results.txt` is written normally. Do NOT
treat this warning as an error or retry trigger; log it at DEBUG level and
continue.

## Two-phase template

Parametrised by `observables` (`["relic"]` for 4c, `["direct_detection"]` for
4e) and `out_dir`. The relic branch runs it against
`./demo_output/singlet-doublet/maddm_run/`; the DD branch against
`./demo_output/singlet-doublet/maddm_run_dd/` (which must be `rmtree`d first —
MG5 `output` refuses to overwrite).

```python
from scripts.maddm_run import generate_maddm_script
from pathlib import Path
import shutil, subprocess

setup_script, launch_script = generate_maddm_script(
    ufo_path=ufo_path,
    dm_candidate="chi1",
    out_dir=out_dir,
    observables=observables,          # ["relic"] or ["direct_detection"]
    split_for_param_overlay=True,
)
(workdir / "setup.mg5").write_text(setup_script)
(workdir / "launch.mg5").write_text(launch_script)

# Phase 1: import model, define DM, generate <observable>, output → writes Cards/param_card.dat.
subprocess.run(
    [mg5_bin, "--mode=maddm", str(workdir / "setup.mg5")],
    cwd=workdir, check=True,
)

# Overlay the SPheno SLHA (Step 4b) onto the card MG5 just wrote.
shutil.copy(slha_path, Path(out_dir) / "Cards" / "param_card.dat")

# Phase 2: launch -f using the overlaid card.
subprocess.run(
    [mg5_bin, "--mode=maddm", str(workdir / "launch.mg5")],
    cwd=workdir, check=True,
)
```

## Shared helper: parse_chi1_mass

`m_chi1` must be parsed from the SLHA `Block MASS` produced in Step 4b — never
hardcoded. The SARAH-assigned PDG id for `FChi_1` is model-specific (for
singlet-doublet it currently lands on `9958431`), so match on the `# FChi_1`
comment tail, not the numeric id.

```python
def parse_chi1_mass(slha_path: str | Path) -> float:
    """Return FChi_1 pole mass from an SPheno SLHA Block MASS."""
    in_mass = False
    for line in Path(slha_path).read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("Block MASS"):
            in_mass = True
            continue
        if in_mass and stripped.startswith("Block "):
            break
        if in_mass and stripped.endswith("# FChi_1"):
            return float(stripped.split()[1])
    raise RuntimeError(f"FChi_1 mass not found in {slha_path}")

m_chi1 = parse_chi1_mass(slha_path)
```

## Relic parsing (Step 4c)

`/gamlike` v0 is the canonical parser (stable path per D-DPATH); see
`plugins/hep-ph-toolkit/skills/gamlike/SKILL.md` for schema + invocation.

```python
import json, subprocess, sys
maddm_results_path = Path(out_dir) / "output" / "run_01" / "MadDM_results.txt"
gamlike_json_path  = Path(out_dir) / "gamlike.json"

subprocess.run([
    sys.executable,
    "plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py",
    str(maddm_results_path),
    "--out", str(gamlike_json_path),
], check=True)

gamlike = json.loads(gamlike_json_path.read_text())

results = {}
results["Omegah2"] = gamlike["relic"]["Omegah2"]

# Flatten nested channels (D4): /gamlike emits {<initial>: {<final>: <pct>}}.
# chi1chi1 is the Majorana initial state.
flat_channels = {}
for init_state, finals in gamlike["relic"]["channels"].items():
    for k, v in finals.items():
        if v is not None:
            flat_channels[k] = v

# Convert percent values to unit fractions (D3): consumer-side normalization.
total = sum(flat_channels.values()) or 1.0
fractions = {k: v / total for k, v in flat_channels.items()}

# Fail-fast gate: fractions must sum to [0.99, 1.01].
gate_check = {
    "channels_sum_in_unity_range": 0.99 <= sum(fractions.values()) <= 1.01
    if fractions else True,
}
if not gate_check["channels_sum_in_unity_range"]:
    raise ValueError(f"channel_fractions out of [0.99,1.01]: sum={sum(fractions.values())}")

results["channel_percentages"] = flat_channels
results["channel_fractions"]   = fractions  # asymmetric upgrade (O4): new field
results["gate_check"]          = gate_check  # asymmetric upgrade (O4): new field
results["sigmav_channels"]     = flat_channels  # legacy alias (raw %)

# WS2: emit summary["dm_indirect_detection_status"] = "parser-only"
```

## Direct-detection parsing (Step 4e)

`/gamlike` surfaces MadDM's four `SigmaN_*` per-nucleon σ as named fields. All
four are required by `scattering/v1`; if any are missing the upstream MadDM run
did not produce the canonical DD lines — fail loud.

```python
maddm_dd_results = dd_out_dir / "output" / "run_01" / "MadDM_results.txt"
gamlike_dd_json  = dd_out_dir / "gamlike.json"
subprocess.run([
    sys.executable,
    "plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py",
    str(maddm_dd_results),
    "--out", str(gamlike_dd_json),
], check=True)
gamlike_dd = json.loads(gamlike_dd_json.read_text())
direct = gamlike_dd["direct"]

missing = [k for k in (
    "sigma_si_proton_cm2", "sigma_si_neutron_cm2",
    "sigma_sd_proton_cm2", "sigma_sd_neutron_cm2",
) if direct.get(k) is None]
if missing:
    raise RuntimeError(
        f"gamlike.direct missing required nucleon σ fields: {missing}. "
        f"Check that MadDM's DD section emitted the SigmaN_SI_p/n and SigmaN_SD_p/n "
        f"lines in {maddm_dd_results}."
    )

scattering = {
    "schema_version":         "scattering/v1",
    "m_dm_gev":               m_chi1,                   # parsed via parse_chi1_mass
    "sigma_si_proton_cm2":    direct["sigma_si_proton_cm2"],
    "sigma_si_neutron_cm2":   direct["sigma_si_neutron_cm2"],
    "sigma_sd_proton_cm2":    direct["sigma_sd_proton_cm2"],
    "sigma_sd_neutron_cm2":   direct["sigma_sd_neutron_cm2"],
    "source":                 "maddm",
    "source_run":             str(dd_out_dir.resolve()),
    "halo":                   None,
    "nucleon_form_factors":   {"preset": "default_2018"},
}
sigma_json = dd_out_dir / "scattering.json"
sigma_json.write_text(json.dumps(scattering, indent=2))

# Dispatch /ddcalc for the per-experiment 90%-CL exclusion verdict.
ddcalc_proc = subprocess.run(
    ["python3", "-m", "plugins.hep_ph_toolkit.skills.ddcalc.scripts.run_ddcalc",
     "run", "--sigma-json", str(sigma_json)],
    capture_output=True, text=True, check=True,
)
ddcalc_result = json.loads(ddcalc_proc.stdout)
```
