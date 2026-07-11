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
mg5_bin   = config.get("madgraph_path", "mg5_aMC")  # top-level key, a path to bin/mg5_aMC

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
# complete_sarah_param_card also STRIPS MG5-indigestible blocks (SPheno's
# 1-loop DECAY1L) before returning — see the Gotcha below. Left in place they
# crash `launch -f` while mg5_aMC exits 0 and echoes the Planck constant, a
# silent failure; the report includes {"_stripped_indigestible": "DECAY1L"}.
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

# PHASES present-but-ZERO is the same silent-zero bug in a third disguise:
# a phase has unit modulus, so `Block PHASES  1  0.0` is SARAH's
# Set_All_Parameters_0 sentinel leaking into the SLHA. Every h-χ₁-χ₁-type
# coupling carries conjg(PhaseFS), so PhaseFS=0 kills the Higgs-portal sector
# on the RELIC branch too — the symptom is Ωh² ≈ 0.166 (χ₁χ₁→hh closed)
# instead of the correct ≈ 0.2916 (WW/Zh/ZZ/hh mix), which looks like a
# perfectly valid result. complete_sarah_param_card() coerces a present zero
# real phase to 1 and reports {"phases": "coerced present zero phase -> 1"};
# if you bypass the completion helper, check the card for a zero PHASES entry
# yourself before launch.

# Majorana-phase gate (fourth silent-value bug, found 2026-07-06): Block MASS
# carries |m|, so ZNMIX must satisfy ZN·M·ZNᵀ = diag(+|m|). The mass matrix at
# the canonical point has a NEGATIVE χ₂ eigenvalue (−523.03); its eigenvector
# row must be carried in IMZNMIX (row × i), with the real ZNMIX row zero. A
# card with |MASS| and a purely real ZNMIX is internally inconsistent: every
# χ₂ vertex gets a wrong phase, χ₂-exchange interference in χ₁χ₁→Zh flips,
# and the relic comes out ≈ 0.0717 with Zh ≈ 92% of σv instead of the correct
# ≈ 0.2916 with a physical WW 33% / Zh 20% / ZZ 18% / hh 12% / bb 11% mix. Tree-level
# direct detection is UNAFFECTED (only χ₁ vertices enter), so a correct σ_SI
# does not validate the relic. The spheno-build analytic writer emits the
# phase correctly since the 2026-07 fix; gate any hand-built card on it:
# if the relic lands near 0.07 with one ≳90% channel, inspect IMZNMIX.

# Mass-matrix sign gate (fifth silent-value bug, same day): ZNMIX must
# diagonalize SARAH's OWN mass matrix — for this model
# [[MS, −yh2·v/√2, +yh1·v/√2],[·, 0, −MPsi],[·, ·, 0]] (transcribed from the
# generated CalculateMFChi) — not the paper's all-plus Eq. 3 matrix. The two
# have identical eigenvalues, so MASSES CANNOT CATCH THIS; only the
# eigenvector component signs differ. Cards built from the paper matrix are
# internally inconsistent for any yh2 ≠ 0: the σ_SI blind spot shows up at
# θ = ±π/4 (yh1 = ±yh2) instead of the true θ = −0.152 (paper Eq. 8,
# MadDM-verified ~7-order dip). The 2026-07 analytic writer uses the SARAH
# matrix; gate hand-built cards by checking ZN·M_SARAH·ZNᵀ is diagonal.

# Phase 2: launch -f using the overlaid, completed card.
launch_proc = subprocess.run(
    [mg5_bin, "--mode=maddm", str(workdir / "launch.mg5")],
    cwd=workdir, capture_output=True, text=True,
)
# LOUD no-output guard: mg5_aMC can EXIT 0 while writing no results (e.g. a
# param-card crash inside `launch -f`), echoing the Planck constant
# `Omega h^2 = 1.2000e-01` on stdout as if computed. A returncode of 0 is NOT
# evidence of success — verify a results file was written before parsing
# stdout. Raises MADDM_LAUNCH_NO_OUTPUT (recoverable) when absent.
_load("maddm_run.py").assert_launch_produced_output(
    out_dir, returncode=launch_proc.returncode, stdout_tail=launch_proc.stdout,
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

> **DD-only rerun staleness — always use FRESH output dirs.** MadDM
> `direct_detection`-only reruns can serve a STALE/frozen SI value
> (bit-identical `2.4258…E-31 GeV⁻²` regardless of the couplings in the param
> card — same MD5 across genuinely different coupling points), because the
> DD-assembly path does not always re-read the param card. Verify the SI value
> *responds* to coupling changes: run into a fresh `output` dir each time
> (`rmtree` first, as the template below does) and, when validating a fix,
> confirm the SI number actually moved. Root-fixing the staleness is out of
> scope; this fresh-dir discipline is the workaround. (The T2 σ_SI sign-fix
> verification used separate `out-baseline`/`out-fixed` dirs for exactly this
> reason.)

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
# At this benchmark (θ=0, m_χ₁≈133 GeV, Higgs portal ON) the physical σ_SI(p) is
# O(1e-45 cm²) — tree level ~7.6e-45, MadDM-verified (see
# benchmarks/canonical-2026/expectations.json). Anything ≲1e-55 cm² at a
# non-blind-spot point means the Higgs channel is dead — STOP and inspect the
# param card, do not report the number.
# NOTE (up/down Higgs–Yukawa sign): an O(1e-47 cm²) reading with p/n ≈ 8 (or
# opposite-sign p/n) is NOT the vector floor but the relative-sign artifact
# between up-type (+m_q/v) and down-type (−m_q/v) h-quark couplings — a ~200x
# suppression that fakes isospin violation. Fixed at the ModelSpec level
# (−Yu H.u.q); if you see it, the UFO predates the fix. Gate p/n ∈ [0.9,1.1].
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
# Invoke run_ddcalc.py by FILE PATH, not `-m plugins.hep_ph_toolkit...`:
# `plugins/hep-ph-toolkit` has a hyphen, so it is not a valid dotted package
# path and `-m` raises ModuleNotFoundError (same hyphen gotcha noted for the
# maddm scripts above — run_ddcalc.py is a standalone CLI, so a direct path
# just works).
ddcalc_proc = subprocess.run(
    ["python3", "plugins/hep-ph-toolkit/skills/ddcalc/scripts/run_ddcalc.py",
     "run", "--sigma-json", str(sigma_json)],
    capture_output=True, text=True, check=True,
)
ddcalc_result = json.loads(ddcalc_proc.stdout)
```
