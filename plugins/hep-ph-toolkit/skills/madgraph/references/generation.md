# MadGraph Generation

The core MG5 workflow — from process definition through event output.

## Process Definition

### Basic syntax

```
generate <initial state> > <final state>
```

The `generate` command defines the primary process. Use `add process` for additional subprocesses (e.g., different jet multiplicities for matching):

```
generate p p > t t~
add process p p > t t~ j
add process p p > t t~ j j
```

### NLO syntax

Append `[QCD]` or `[QED]` to request next-to-leading-order corrections:

```
generate p p > t t~ [QCD]     # NLO QCD corrections to ttbar
generate p p > e+ e- [QED]    # NLO QED corrections to Drell-Yan
```

NLO requires MadLoop (bundled) and optionally `ninja` for faster tensor reduction. Install ninja:

```
MG5_aMC> install ninja
```

### Multiparticle labels

Default labels in the SM:

| Label | Definition |
|-------|-----------|
| `p` | `g u c d s u~ c~ d~ s~` |
| `j` | `g u c d s u~ c~ d~ s~` |
| `l+` | `e+ mu+ ta+` |
| `l-` | `e- mu- ta-` |
| `vl` | `ve vm vt` |
| `vl~` | `ve~ vm~ vt~` |

Define custom labels:

```
define ell = e+ e- mu+ mu-
generate p p > ell ell
```

### Model import

```
import model sm                    # Standard Model (default)
import model sm-no_b_mass          # SM with massless b quarks
import model mssm                  # MSSM with default restriction
import model mssm-full             # MSSM without restrictions
import model 2hdm-type2            # 2HDM Type-II
import model /path/to/MyModel_UFO  # Custom UFO model from path
```

Models with restrictions: the part after `-` is the restriction name, matching `restrict_<name>.dat` in the model directory.

### Excluding particles

Use `/` to exclude particles from internal propagators (s-channel):

```
generate p p > t t~ / a       # No photon in s-channel
generate p p > e+ e- / z      # Only photon exchange (no Z)
```

Use `$$` to exclude from all propagators (s-channel and t-channel):

```
generate p p > t j $$ w+ w-   # t-channel single top (no W propagators)
```

## Card Structure

### proc_card.dat

Defines the full process setup. Example for NLO tt̄:

```
import model sm
define p = g u c d s u~ c~ d~ s~
define j = g u c d s u~ c~ d~ s~
generate p p > t t~ [QCD]
output pp_ttbar_nlo
```

The `output` command creates the process directory with all needed code.

### param_card.dat

Sets physical parameters in SLHA (SUSY Les Houches Accord) block format. Each block contains numbered entries:

```
###################################
## INFORMATION FOR MASS
###################################
BLOCK MASS
      5  4.700000e+00  # MB
      6  1.725000e+02  # MT
     15  1.777000e+00  # MTA
     23  9.118760e+01  # MZ
     25  1.250000e+02  # MH

###################################
## INFORMATION FOR SMINPUTS
###################################
BLOCK SMINPUTS
     1  1.279000e+02  # aEWM1 (1/alpha_EW at MZ)
     2  1.166370e-05  # Gf (Fermi constant)
     3  1.180000e-01  # aS (alpha_s at MZ)
```

Key blocks:
- `MASS` — particle masses, keyed by PDG ID
- `SMINPUTS` — SM input parameters (α_EW⁻¹, G_F, α_s)
- `YUKAWA` — Yukawa couplings
- `DECAY` — particle widths and branching ratios
- For BSM: model-specific blocks (e.g., `NMIX`, `UMIX` for MSSM)

### run_card.dat

Configures the event generation run. Format: `value = parameter_name`:

```
100000 = nevents        ! Number of events
6800.0 = ebeam1         ! Beam 1 energy [GeV]
6800.0 = ebeam2         ! Beam 2 energy [GeV]
0      = lpp1           ! Beam 1 type (0=e, 1=p, -1=pbar)
1      = lpp1           ! Beam 1 type
1      = lpp2           ! Beam 2 type
331100 = lhaid          ! LHAPDF set ID
```

#### Beam configuration

| Field | Description |
|-------|-------------|
| `ebeam1`, `ebeam2` | Beam energies in GeV. For 13.6 TeV LHC: 6800 each |
| `lpp1`, `lpp2` | Beam type: 0 = electron/positron, 1 = proton, -1 = antiproton |
| `lhaid` | LHAPDF PDF set ID |

#### Kinematic cuts

| Field | Description | Typical value |
|-------|-------------|---------------|
| `ptj` | Min jet pT [GeV] | 20.0 |
| `ptl` | Min lepton pT [GeV] | 10.0 |
| `etaj` | Max jet \|η\| | 5.0 |
| `etal` | Max lepton \|η\| | 2.5 |
| `drjj` | Min ΔR(j,j) | 0.4 |
| `drll` | Min ΔR(l,l) | 0.4 |
| `drjl` | Min ΔR(j,l) | 0.4 |
| `mmll` | Min m(l+l−) [GeV] | 10.0 |
| `ptjmax`, `ptlmax` | Max pT cuts (use -1 for no cut) | -1 |

#### Scale choices

| Field | Description |
|-------|-------------|
| `fixed_ren_scale` | `.true.` = use `scale` value; `.false.` = dynamic |
| `fixed_fac_scale` | `.true.` = use `dsqrt_q2fact1` value; `.false.` = dynamic |
| `scale` | Fixed renormalization scale [GeV] |
| `dsqrt_q2fact1`, `dsqrt_q2fact2` | Fixed factorization scales [GeV] |
| `dynamical_scale_choice` | Dynamic scale: `-1` (default = sum of mass/pT), `1` (sqrt(ŝ)), `2` (sum of transverse mass), `3` (HT/2), `4` (HT/4) |
| `scalefact` | Multiplicative factor on dynamic scale | 1.0 |

#### Matching/merging (for multi-jet samples)

| Field | Description |
|-------|-------------|
| `ickkw` | `0` = no matching, `1` = MLM matching, `3` = FxFx merging (NLO) |
| `xqcut` | Matching scale [GeV] (MLM). Typically 20–30 GeV for LHC |
| `alpsfact` | α_s factor in CKKW scale | 1 |

## Launch Workflow

### Interactive launch

```
MG5_aMC> launch <process_dir>
```

MG5 will prompt:
1. Edit param_card? (1 = yes, enter = no)
2. Edit run_card? (2 = yes, enter = no)
3. Start generation

### Scripted launch (non-interactive)

Write commands to a file and pipe them:

```bash
cat << 'EOF' > launch_commands.txt
launch my_process
set nevents 100000
set ebeam1 6800
set ebeam2 6800
set lhaid 331100
done
EOF
python3 /path/to/mg5_aMC launch_commands.txt
```

### Card replacement

Replace cards entirely by specifying paths during launch:

```
launch my_process
/path/to/my_param_card.dat
/path/to/my_run_card.dat
done
```

MG5 identifies the card type by content, not by filename.

### Multi-run

Run the same process multiple times with different seeds:

```
launch my_process -n run_01
set iseed 12345
done
launch my_process -n run_02
set iseed 12346
done
```

Each run produces its own `Events/run_XX/` subdirectory.

---

## Named-model handoff

> When a model has been built by the hephaestus tool-chain (SARAH → SPheno →
> UFO), its paths are stored in `~/.config/hephaestus/config.json` under
> `models.<name>`.  Use the resolver before writing any MG5 script:
>
> ```bash
> python3 scripts/resolve_named_model.py dark_su3 --key ufo
> python3 scripts/resolve_named_model.py dark_su3 --key latest_slha
> ```
>
> Substitute the returned paths into `import model <UFO>` and the
> `param_card.dat` slot of `launch`.  See the Decision Tree in `SKILL.md`
> (section "Using a named hephaestus model?") for the full flow and an
> example script-file invocation (`mg5_aMC /tmp/my_script.mg5`).
