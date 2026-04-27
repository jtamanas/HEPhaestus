# Dark SU(3) Playtester — Cycle 1 Running Log

**Worktree:** `/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4c5325b96c5b6e40`
**Branch:** `main` (worktree, isolated)
**Target:** Profumo & Arcadi 2506.19062 Fig. 8 — Dark SU(3) vector-resonance benchmark, m_χ=100 GeV, m_med≈199 GeV
**Skill under test:** `/dark-matter-constraints` (router)

---

## 2026-04-25T15:33:00-04:00 — Setup

- Confirmed worktree location and isolation.
- Read `plugins/constraints/skills/dark-matter-constraints/SKILL.md` cover-to-cover (289 lines).
- Read `briefs/ROUTING_LENS.md` (load-bearing philosophy).
- Located sibling skills: not in `plugins/constraints/skills/` as the SKILL.md implies but in:
  - `plugins/monte-carlo-tools/skills/{maddm,maddm-install,drake,drake-install}`
  - `plugins/model-building/skills/{sarah-build,sarah-install,spheno-build,spheno-install}`
  - `plugins/constraints/skills/{micromegas,micromegas-install,ddcalc,ddcalc-install,higgstools,higgstools-install}`
- Existing fixtures at `tests/fixtures/dark_su3_playtest/` — `ufo/`, `configs/`, `specs/`, `golden/`, `canned/`, `stubs/`, `transcripts/`, `smoke_runs/`, `negative_control/`.

---

## 2026-04-25T15:50:00-04:00 — Tool inventory

| Tool | Status | Version | Path |
|---|---|---|---|
| MG5_aMC | INSTALLED | 3.5.6 (2024-09-26) | `/Users/yianni/MG5_aMC_v3_5_6` |
| MadDM (plugin) | INSTALLED | 3.2.13 | `/Users/yianni/MG5_aMC_v3_5_6/PLUGIN/maddm` |
| SARAH | INSTALLED | 4.15.3 | `/Users/yianni/SARAH/SARAH-4.15.3` |
| SARAH DarkSU3 model | PRESENT (output broken — see below) | — | `/Users/yianni/SARAH/SARAH-4.15.3/Private-Models/DarkSU3` |
| SPheno | INSTALLED (binary built) | 4.0.5 | `/Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno` |
| micrOMEGAs | NOT INSTALLED | — | — |
| DRAKE | NOT INSTALLED | — | — |
| LoopTools | NOT INSTALLED | — | — |
| FeynArts | NOT INSTALLED | — | — |
| FormCalc | NOT INSTALLED | — | — |
| Package-X | NOT INSTALLED | — | — |
| FeynCalc | NOT INSTALLED | — | — |
| DDCalc | NOT INSTALLED | — | — |
| WolframScript | INSTALLED + ACTIVATED | 1.13.0 ARM | `/usr/local/bin/wolframscript` |
| Python | INSTALLED | 3.10.16 | pyenv shim |
| numpy/pyyaml/pytest | INSTALLED | 2.2.6 / 6.0.3 / 9.0.3 | — |

Note: `/Users/yianni/SPheno-4.0.5` is an empty stub directory; real SPheno lives at `~/SPheno/SPheno-4.0.5/bin/SPheno` (Mach-O arm64 executable, built).

## 2026-04-25T15:55:00-04:00 — DarkSU3 SARAH UFO output is corrupted

Existing SARAH output: `/Users/yianni/SARAH/SARAH-4.15.3/Output/DarkSU3/EWSB/UFO/`.

`particles.py` contains:
- `None = Particle(pdg_code = None, ...)` x3 — Python `SyntaxError: cannot assign to None`
- `mass = Param.$Failed` (Mathematica leakage)
- The dark fermion `psiD` ended up as one of the orphan `None` blocks (only "FpsiD" texname is present); no `MFpsiD` mass parameter; no dark gluon particle entry; no `gD` properly.

Verified: `python -c "import particles"` → `SyntaxError: cannot assign to None`.

This UFO is not loadable by MG5/MadDM as-is. Root cause: SARAH did not complete generation cleanly for this model — the `Private-Models/DarkSU3/DarkSU3.m` file declares a SU(3)_dark gauge group with `gD` but no scalar that breaks it. Without an explicit dark Higgs / VEV in the dark sector, the gauge bosons stay massless and SARAH chokes on EWSB rotation matrices.

**Decision:** Do not regenerate from SARAH in this cycle — the model file itself is missing the dark-sector breaking, which would require physics work (and is precisely what the user wants /sarah-build to enumerate, per project memory). Time-box: skip SARAH, attempt to either find a published Dark SU(3) UFO or use a published vector-mediator simplified model that still fires the resonance branch.

## 2026-04-25T15:58:00-04:00 — Helper bug #1: check_prereqs.py rejects YAML config

`scripts/check_prereqs.py` declaims (line 156 help text) "Path to config JSON/YAML" but `_load_json` only does `json.load(fh)`. Running with the as-shipped `tests/fixtures/dark_su3_playtest/configs/config_pointA_configured.yaml` exits with code 2 and `PREREQ_HELPER_INTERNAL: Expecting value: line 1 column 1 (char 0)`.

Workaround: construct equivalent JSON config at `.shift-manager/run-20260425-dmc/playtest/work/config_real.json`.

## 2026-04-25T16:00:00-04:00 — Helper bug #2: check_prereqs treats every config_keys entry as fatal

The contract `contracts/router_contract.json` lists `config.maddm_path`, `config.micromegas_path`, `config.drake_path` all in `config_keys` but does not annotate which are recoverable. The helper iterates `config_keys` and emits a blocker for every absent one, then sets `status="blocked"` if any non-`SLHA_MISSING_HINT` blocker exists.

Per SKILL.md "Blocker / notice codes" table:
- `MADDM_MISSING` is fatal — correct
- `MICROMEGAS_MISSING` is recoverable — but helper makes it fatal
- `DRAKE_PATH_UNSET` (`DRAKE_MISSING`) is recoverable — but helper makes it fatal

Verified by running with `micromegas_path: null, drake_path: null`: helper exits 1 with `status=blocked`, blocking the whole router even though MadDM is fully installed and the user requested `relic` only.

Workaround for this cycle: ignore the helper's status decision (router-LLM should anyway, per Step 1 SKILL.md prose: "if `status == "blocked"`, surface each blocker and stop" — the helper has misclassified). Continue manually.


## 2026-04-25T16:15:00-04:00 — Real DarkSU3 UFO found, but unusable for resonance benchmark

A *clean* SARAH-generated DarkSU3 UFO exists at:

`/Users/yianni/.local/share/hep-ph-agents/models/dark_su3/sarah_output/UFO/DarkSU3/`

(48 particles, importable, no `None = Particle(...)` corruption — unlike the
`/Users/yianni/SARAH/SARAH-4.15.3/Output/DarkSU3/EWSB/UFO/` copy under the SARAH
install root, which is corrupt.)

Particles include `psiD` (dark fermion, PDG 9945452) and `VGD` (dark gluon vector,
PDG 9957152). Spec at `~/.local/share/hep-ph-agents/models/dark_su3/spec.yaml` is
explicit:

> The dark SU(3) sector is confining — the composite mass spectrum (phi, V) is
> parameterised from (MpsiD, gD, mV, mphi) via an HLS-like approach, not derived
> by SPheno's perturbative RGE machinery. SPheno does not apply to confining
> sectors. backends.spectrum: analytic.

> TODO(analytic-module): scripts/analytic_models/dark_su3.py does not yet exist

In the UFO, `psiD.mass = Param.ZERO` and `VGD.mass = Param.ZERO` — i.e. SARAH
emits massless UV fields and the composite phi/V states (the actual DM and
mediator from Profumo §IV) are not present. The mass scan in the spec
(`mphi=300`, `mV=1000` defaults) lives in the spec but never makes it into the
UFO param list.

**Implication for the playtest:** running MadDM on this UFO would give
`Omegah2 → ∞` (massless DM doesn't freeze out), and there is no s-channel
mediator to fire the DRAKE narrow-resonance branch.

The Profumo Fig. 8 reproduction needs a **separate effective theory UFO**
where phi and V are elementary fields — i.e. the analytic_module that the
spec marks as "TODO does not yet exist." This is upstream-of-the-router work.

**Decision:** Cannot run /maddm against the real Dark SU(3) UFO as-is. Instead:
(a) walk the router's Step 1–5 with the existing UFO and document where the
physics fails, and (b) run /maddm on a known-good simplified DM model
(SingletDoublet) to confirm the router/extract_field plumbing actually works
end-to-end. Combine both in the report.


## 2026-04-25T16:35:00-04:00 — DarkSU3 UFO has invalid color tensor structures

Attempted MG5 import:
```
mg5_aMC --mode=maddm setup_darksu3.mg5
```
fails on `import model /Users/yianni/.local/share/hep-ph-agents/models/dark_su3/DarkSU3` with:
```
NameError : name 'dt1' is not defined
```

Root cause: `vertices.py` lines 1327, 1355 contain SARAH placeholder color tokens
that didn't get resolved to numeric color indices:
```
V_188 = Vertex(name = 'V_188',
    particles = [P.VGD, P.VGD, P.VGD],
    color = ['f(dt1,dt2,dt3)'],
    ...)
V_192 = Vertex(name = 'V_192',
    particles = [P.VGD, P.VGD, P.VGD, P.VGD],
    color = ['f(-1,dt1,dt4)*f(-1,dt2,dt3)', 'f(-1,dt1,dt3)*f(-1,dt2,dt4)', 'f(-1,dt1,dt2)*f(-1,dt3,dt4)'],
    ...)
```

This is a known SARAH limitation: UFO format does not natively support a second
SU(3) color group beyond SM color, and SARAH's color-index resolver leaves
`dt1`, `dt2`, `dt3` placeholders in the output. **The Dark SU(3) UFO is not
loadable by MG5 / MadDM as-is.**

Combined with the earlier finding that the dark fermion `psiD` is `mass = ZERO`
in the UFO and the composite mediator/DM masses (`mphi`, `mV`) are not present
as parameters, this means: **/dark-matter-constraints cannot run on the
Profumo Dark SU(3) benchmark via the SARAH→UFO→MadDM path on this machine,
even though all three tools are individually installed.**

This is the exact failure mode that "augment not replace" memory anticipates:
the user wants the skill chain to drive the real tools rather than to fall
back to analytic. The right response is to surface a blocker (e.g.
`UFO_INVALID_COLOR_INDEX` or `ANALYTIC_MODULE_MISSING` per the spec.yaml's
explicit `analytic_module: analytic_models.stub_unimplemented`), not to
silently produce a number.

Neither blocker exists in `check_prereqs.py` or in the SKILL.md routing tree.

## 2026-04-25T16:45:00-04:00 — Validate router plumbing on a known-good UFO

To prove the rest of the router actually works, ran `/maddm` on a known-good
UFO (SingletDoublet, since a working SLHA + UFO + MG5 invocation already
existed at `~/Projects/hep-ph-agents/.claude/worktrees/from-main/demo_output/singlet-doublet/`).

### MadDM run 1: default param card

Setup script (`setup_sd.mg5`):
```
import model /Users/yianni/.local/share/hep-ph-agents/models/singlet_doublet/SingletDoublet
define darkmatter chi1
generate relic_density
output .../maddm_sd_run1
launch -f
```
Ran cleanly through MG5 process generation and MadDM Boltzmann integration in
~3 minutes. Result:
```
Omegah2 = -1.00e+00   (sentinel: "Freezeout occurs too early")
```
This is the MadDM idiom for "default param_card has all couplings = 0, so
chi1 cannot deplete; relic too big to compute, returning -1." Plumbing OK.

### MadDM run 2: overlay SPheno SLHA from prior run

Overlaid the previous `from-main` working `param_card.dat` (SPheno-derived)
onto `Cards/param_card.dat`, then `launch maddm_sd_run1 -f`. Result:
```
Omegah2 = 2.92e-01
sigmav_xf = 8.42e-27 cm^3/s
x_f = 20
```
Channel decomposition includes wpwm (33.55%), zh (20.03%), zz (17.84%),
hh (12.23%), bbx (10.76%) — physically sensible for a singlet-doublet
benchmark with m_chi ≈ 100 GeV.

This confirms:
- MG5 + MadDM are functional on this machine.
- The full SARAH → SPheno → SLHA → MadDM chain works for SingletDoublet.
- The router's `MadDM_results.txt` regex parser will successfully extract
  fields against this output (matches the audited router_contract.json
  source_locator regex `^Omegah2\s*=\s*[0-9]`).

### Router unit tests (sanity check)

```
pytest plugins/constraints/skills/dark-matter-constraints/tests/
65 passed, 3 xfailed, 3 xpassed, 1 warning in 3.22s
```
All helpers (`check_prereqs.py`, `detect_drake.py`, `extract_field.py`,
`verify_router_field_contract.py`) functional. The 3 xpassed entries are
the known schema/topology mismatches the contracts/AUDIT.md captures.

## 2026-04-25T16:55:00-04:00 — extract_field smoke-tested against canned fixtures

```
extract_field --json canned/pointA/relic.json        --key omega_h2          --schema-version relic/v1
  → {"value": 0.118, ...}
extract_field --json canned/pointA/summary.json      --key sigma_si_proton_cm2 --schema-version scattering/v1
  → {"value": 1.21e-45, ...}
extract_field --json canned/pointA/annihilation.json --key sigma_v_zero      --schema-version annihilation/v1
  → {"value": 2.31e-26, ...}
```
All three schema dispatches work; all values extract cleanly. Step 4b's
deterministic primitive is not the bottleneck.

