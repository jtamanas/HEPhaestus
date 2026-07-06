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
  `launch` so MadDM reads the SLHA-formatted mass spectrum + mixing matrices.
  SPheno actually emits `MASS`, `SMINPUTS`, `MINPAR`, and the BSM mixing blocks
  `ZNMIX`/`IMZNMIX`/`UMMIX`/`UPMIX`/`IMUMMIX`/`IMUPMIX`. It does **not** emit
  `BSMPARAMS` (the BSM Yukawas yh1/yh2 — echoed only into `MINPAR` 26/27), the
  SM quark rotation matrices `UDLMIX`/`UDRMIX`/`UULMIX`/`UURMIX`, or
  `PHASES`/`IMPHASES`. Those gaps are load-bearing for direct detection (see the
  σ_SI reliability gate below) and must be repaired before `launch`, not assumed
  present — the overlay step below calls `complete_sarah_param_card` to do so.

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
# ── Setup (paths resolved once, reused by 4c/4e) ──────────────────────────
# $STATE_ROOT is the hephaestus state directory. It is NOT defined by this
# skill — it comes from install/SKILL.md: config lives at
# $XDG_CONFIG_HOME/hephaestus/config.json (default ~/.config/hephaestus/),
# and per-model artifacts under $STATE_ROOT = ~/.local/share/hephaestus.
import json, os, shutil, subprocess, sys
import importlib.util
from pathlib import Path

STATE_ROOT = Path(os.environ.get(
    "XDG_DATA_HOME", Path.home() / ".local/share")) / "hephaestus"
config = json.loads((Path(os.environ.get(
    "XDG_CONFIG_HOME", Path.home() / ".config"))
    / "hephaestus/config.json").read_text())
model_cfg = config["models"]["singlet_doublet"]
ufo_path  = model_cfg["ufo"]            # the state_dir/SingletDoublet symlink
slha_path = model_cfg["latest_slha"]    # SPheno.spc from Step 4b
mg5_bin   = config["madgraph"]["mg5_bin"] if "madgraph" in config else "mg5_aMC"

# `plugins/hep-ph-toolkit` has a hyphen, so the maddm scripts are NOT
# importable as a dotted package path (`from scripts.maddm_run import …`
# raises ModuleNotFoundError). Load the module by file path instead.
def _load(mod_path):
    p = f"plugins/hep-ph-toolkit/skills/maddm/scripts/{mod_path}"
    spec = importlib.util.spec_from_file_location(Path(mod_path).stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

generate_maddm_script = _load("maddm_run.py").generate_maddm_script

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

# Overlay the SPheno SLHA (Step 4b) onto the card MG5 just wrote, then repair
# the SARAH quark-mixing/phase gaps — the same silent-zero bug suppresses any
# Yukawa-mediated relic subchannel, not just the DD Higgs t-channel, so run the
# completion on BOTH branches. SPheno omits the SM quark rotation matrices
# (UDLMIX/UDRMIX/UULMIX/UURMIX) and the field-redefinition phase (PHASES)
# whenever they are the identity/unity; the UFO reads the missing entries as
# *external* params defaulting to 0 — the ZERO matrix, not the identity — which
# collapses the rotated Higgs-quark Yukawa ZDL†·Yd·ZDR and pins σ_SI at the
# ~1e-58 cm² Z-exchange (vector) floor. See maddm/scripts/slha_complete.py.
card = Path(out_dir) / "Cards" / "param_card.dat"
shutil.copy(slha_path, card)
completed_blocks = _load("slha_complete.py").complete_sarah_param_card(card, ufo_path)

# The BSM Yukawas yh1/yh2 carry physics, so the completion helper does NOT
# fabricate them — they must already be Block BSMPARAMS 3/4 in slha_path. As of
# the spheno-build fix the analytic SLHA writer emits BSMPARAMS from each
# param's spec `les_houches` mapping, so a spec-built .spc carries them. If you
# overlay an SLHA from a source that only echoes yh1/yh2 into MINPAR, add Block
# BSMPARAMS here from the benchmark spec before launch, or MG5 reads yh1=0 and
# σ_SI collapses to the vector floor.
if "block bsmparams" not in card.read_text().lower():
    raise RuntimeError(
        f"{card} has no Block BSMPARAMS — yh1/yh2 will default to 0 and σ_SI "
        f"will be unphysical. Overlay BSMPARAMS from the benchmark spec."
    )

# Phase 2: launch -f using the overlaid, completed card.
subprocess.run(
    [mg5_bin, "--mode=maddm", str(workdir / "launch.mg5")],
    cwd=workdir, check=True,
)
```

## Shared helper: parse the DM mass by PDG id

`m_chi1` must be parsed from the SLHA `Block MASS` produced in Step 4b — never
hardcoded. The SARAH-assigned PDG id for the DM candidate is model-specific (for
singlet-doublet `Chi1` currently lands on `9958431`), so resolve it from the
UFO's `particles.py` and match column 1 of `Block MASS`. Do **not** match on the
trailing comment: real SPheno.spc rows are commented `# pdg=<id>`, not
`# FChi_1`, so a comment-tail match raises spuriously.

```python
def dm_pdg_from_ufo(ufo_path: str | Path, name: str = "Chi1") -> int:
    """Return the PDG id the UFO assigns to a particle by name."""
    import re
    text = (Path(ufo_path) / "particles.py").read_text()
    # Match a Particle(pdg_code=<id>, ... name = '<name>' ...) declaration.
    for m in re.finditer(r"pdg_code\s*=\s*(-?\d+)\s*,\s*\n\s*name\s*=\s*'([^']+)'", text):
        if m.group(2) == name:
            return int(m.group(1))
    raise RuntimeError(f"particle {name!r} not found in {ufo_path}/particles.py")


def parse_mass_by_pdg(slha_path: str | Path, pdg: int) -> float:
    """Return a pole mass from an SPheno SLHA Block MASS by numeric PDG id."""
    in_mass = False
    for line in Path(slha_path).read_text().splitlines():
        stripped = line.split("#")[0].strip()
        if line.strip().lower().startswith("block mass"):
            in_mass = True
            continue
        if in_mass and line.strip().lower().startswith("block "):
            break
        if in_mass and stripped:
            parts = stripped.split()
            if len(parts) >= 2 and int(parts[0]) == pdg:
                return float(parts[1])
    raise RuntimeError(f"pdg {pdg} not found in Block MASS of {slha_path}")

m_chi1 = parse_mass_by_pdg(slha_path, dm_pdg_from_ufo(ufo_path, "Chi1"))
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

# ── σ_SI RELIABILITY GATE (run BEFORE trusting any SigmaN value) ──────────
# A near-zero σ_SI here is almost always an artifact, not physics. Two
# independent failure modes both produce a σ_SI ~1e-58 cm² "vector floor"
# that looks superficially allowed:
#   (1) missing SM quark-rotation blocks (UDLMIX/UDRMIX/…) → Higgs t-channel
#       zeroed at the quark vertex (fixed by complete_sarah_param_card above);
#   (2) missing Block BSMPARAMS / PHASES → h-χ₁-χ₁ vertex zeroed.
# NOTE: grepping the MadDM/MG5 log for "parameter mdl_yh1 not found" is NOT a
# sufficient gate — patching yh1 alone leaves σ_SI at the floor because the
# quark-vertex coupling is the dominant zero. Gate on the *value* instead.
#
# At this benchmark (θ=0, m_χ₁≈133 GeV, Higgs portal ON) the physical σ_SI is
# O(1e-47 cm²). Anything ≲1e-55 cm² at a non-blind-spot point means the Higgs
# channel is dead — STOP and inspect the param card, do not report the number.
VECTOR_FLOOR_CM2 = 1e-55
si_p = direct.get("sigma_si_proton_cm2")
if si_p is not None and abs(si_p) < VECTOR_FLOOR_CM2:
    raise RuntimeError(
        f"σ_SI_p={si_p:.2e} cm² is at/below the Z-exchange vector floor "
        f"({VECTOR_FLOOR_CM2:.0e}) at a non-blind-spot benchmark — the Higgs "
        f"t-channel is zeroed. Verify the completed param card {card} "
        f"contains populated Block UDLMIX/UDRMIX (identity), Block PHASES "
        f"(unit), and Block BSMPARAMS (yh1). Completion inserted: "
        f"{completed_blocks}. Do NOT record this σ_SI — it is unphysical."
    )

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
    "m_dm_gev":               m_chi1,                   # parsed via parse_mass_by_pdg
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
