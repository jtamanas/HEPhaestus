# Reading MadDM output (agent-driven, diagnostics only)

The canonical parser is `/gamlike`
(`plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py`), which
emits a `gamlike/v1` JSON document covering every section MadDM 3.2 writes. New
consumers should call it. The manual prose extraction below is retained for
diagnostics — reach for it when `/gamlike` is unavailable or you are debugging a
malformed `MadDM_results.txt`.

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
- **Total annihilation cross-section**: line matching `sigmav_xf = <value>`
  (cm³/s) inside the Relic Density section. (Earlier MadDM 3.2 outputs labeled
  this `sigmav_total`; treat the two as aliases.)
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
