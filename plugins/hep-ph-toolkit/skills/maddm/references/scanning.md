# MadDM Parameter Scanning

Systematic exploration of BSM parameter space with MadDM.

> **Two scan paths — pick by model class.**
>
> * **Simplified-model UFOs** (a stock UFO whose couplings are plain
>   `set BLOCK PID` numbers, e.g. `DMsimp_s_spin0`): use `scan_grid.py` +
>   `generate_batch` below. Each point is one `set`-patched MadDM script.
> * **SARAH models** (singlet-doublet and friends, whose DD path is the
>   two-phase SLHA overlay + `complete_sarah_param_card` + `Block BSMPARAMS`
>   gate): use `scan_sarah_dd.py` (next section). `generate_batch` does NOT fit
>   these — `generate_maddm_script` never emits `set BLOCK PID` lines to patch,
>   and the spectrum has to be recomputed per point (SPheno/analytic), not just
>   text-substituted.

## SARAH-model DD scans: spectrum → DD per point

`scripts/scan_sarah_dd.py` is the composable driver for a 1-D scan where each
point recomputes the spectrum and then runs a real MadDM direct-detection.
It chains the pieces the singlet-doublet DD workflow already documents
(`singlet-doublet/references/maddm-invocation.md`), one point at a time:

```
spectrum (spheno-build --skip-compile --no-register)   ~0.3 s
  → per-point SPheno.spc under $STATE_ROOT
MadDM DD (generate_maddm_script split_for_param_overlay=True,               ~10 s
          overlay SLHA, complete_sarah_param_card, Block BSMPARAMS gate,
          FRESH output dir per point)
  → MadDM_results.txt
parse (gamlike parse_maddm_results.py) → σ_SI(p/n), σ_SD(p/n)
collect → scan_results.json + scan_results.csv
```

Three ergonomics it bakes in so you don't hand-roll them:

* **`--no-register` on every spectrum run.** A scan otherwise rewrites the
  global `latest_slha` pointer once per point and leaves it stuck at the last
  point — a trap for the next DD consumer that trusts `latest_slha`. Each
  point's SLHA is fed to its own DD run *by path*; the convenience cache is
  never moved. (Provenance semantics: `latest_slha` should move only on a
  single canonical-point run you want downstream to auto-pick-up; during a scan
  "latest" is ambiguous, so it must not move — see `spheno-build`'s
  `--no-register`.)
* **Fresh MG5 output dir per point** (`generate_maddm_script` `fresh=True`
  emits `!rm -rf` at RUN time, PR #15 semantics) — the frozen-SI-staleness
  discipline. Nothing is deleted at script-generation time.
* **Absolute, hyphen-free UFO path.** It resolves the UFO from the durable
  `$STATE_ROOT/models/<model>/<SarahName>` symlink (or a validated config
  `ufo` key), never a relative/hyphenated `demo_output/...` value that MG5
  rejects.

### How the scan variable reaches the spectrum

**By default the scan variable is fed to SPheno as a spectrum override under
its own name.** So the natural invocation `--scan MS=...` (with no matching
`--param`) varies `MS` directly, point by point — `MS` is a real BSMPARAMS
input, so each point's card carries that point's `MS`. If the scan variable
does *not* name a real spectrum input, SPheno's own `SPHENO_BAD_OVERRIDE` guard
rejects the point loudly (naming the valid inputs) — there is no silent-wrong
path where the value is dropped and every point runs the base card's default.

> **History:** an earlier version of this driver bound the scan variable into
> the `--param` eval namespace but never wrote it to the spectrum overrides, so
> `--scan MS=...` alone silently ran every point at the base card's default
> `MS` while still reporting `status: ok`. That is fixed — the scan variable is
> now fed directly. See test `test_natural_scan_var_reaches_spheno_and_varies`.

**`--param NAME=EXPR` — derived params.** `EXPR` is a math expression in the
scan variable *and any earlier `--param` output* (ordered chaining, next
paragraph). This is how one knob sets several spectrum inputs — the blind-spot
θ scan sets both Yukawas from θ.

**`--scan-drives-only` — pure-driver variables.** A scan variable that is *not*
itself a spectrum input (e.g. the mixing angle θ, which only appears inside
`yh1=cos(θ)`, `yh2=sin(θ)`) must be marked `--scan-drives-only`, which keeps it
out of the spectrum overrides while leaving it available to `--param` EXPRs.
Without the flag, feeding θ to SPheno trips the loud `SPHENO_BAD_OVERRIDE`
guard (θ has no BSMPARAMS index) — again, loud, never silent.

**Ordered chaining (a limitation, now lifted).** `--param` EXPRs are evaluated
in declaration order; each EXPR can reference the scan variable and any
*earlier* `--param` output. A forward reference to a name defined by a *later*
`--param` raises `NameError` loudly (evaluation is strictly ordered, so no cycle
is possible). Example: `--param a=MS*2 --param b=a+1` gives `b = 2*MS + 1`.

Namespace available to `EXPR`: the Python `math` module (`cos`, `sin`, `sqrt`,
`exp`, `log`, `pi`, ...) plus the scan variable and earlier `--param` outputs —
EXCEPT `nan`, `inf`, and the collision-prone short names `e`, `gamma`, `tau`,
which are removed so a typo'd bare name raises `NameError` loudly instead of
silently resolving to a math constant. A non-finite EXPR result (NaN/inf), or
any per-value EXPR error, marks that POINT failed (`stage: "param_eval"` in
`scan_results.json`) and the scan continues — the same discipline as the
downstream stage failures. A `--param` whose NAME equals the scan variable is
refused at argument-parse time (the scan axis already sets that name).

### Worked example A — a direct spectrum-parameter scan (MS mass scan)

Scan the singlet mass `MS` directly (a real BSMPARAMS input) at fixed
MPsi=500, single-Yukawa limit yh1=1, yh2=0 (θ=0) — the "bulk" branch shape of
2506.19062 Fig. 1. `MS` is fed automatically; no `--param MS=...` is needed (in
fact one would be refused as colliding with the scan axis):

```bash
python3 plugins/hep-ph-toolkit/skills/maddm/scripts/scan_sarah_dd.py \
    singlet_doublet \
    --scan MS=20:900:12 \
    --param MPsi=500 --param yh1=1 --param yh2=0 \
    --dm-candidate chi1 --dm-name Chi1 \
    --out-dir ./ms_scan
```

Each point's `m_dm_gev` (the χ1 mass) tracks the scanned `MS`, so σ_SI(p) traces
the bulk curve rising with mass — the points that sit above the LZ exclusion.

### Worked example B — the blind-spot θ scan (driver variable)

Fixed MS=150, MPsi=500, y=1; scan the mixing angle θ with yh1=cos θ,
yh2=sin θ (2506.19062 Eq. 6). θ is a pure driver (not a spectrum input), so
`--scan-drives-only`. σ_SI(p) dips ~9 orders at θ ≈ −0.152:

```bash
python3 plugins/hep-ph-toolkit/skills/maddm/scripts/scan_sarah_dd.py \
    singlet_doublet \
    --scan theta=-0.17:-0.135:8 --scan-drives-only \
    --param MS=150 --param MPsi=500 \
    --param 'yh1=cos(theta)' --param 'yh2=sin(theta)' \
    --dm-candidate chi1 --dm-name Chi1 \
    --out-dir ./scan_out
```

Output `scan_out/scan_results.csv` has one row per point:
`scan_var,value,MPsi,MS,yh1,yh2,m_dm_gev,sigma_si_proton_cm2,...`. Points that
already have a `result.json` are skipped, so an interrupted scan resumes.
Per-point MG5 process bloat is pruned after parsing (pass `--no-prune` to keep
it); kept artifacts are `Cards/param_card.dat`, `MadDM_results.txt`,
`gamlike.json`, `result.json`, and both MG5 logs. Feed the CSV to
`/exclusion-contour` or `/hep-plot` for a σ_SI-vs-θ curve.

For a **2-D** scan, run one `scan_sarah_dd.py` invocation per outer-axis value
into distinct `--out-dir`s and concatenate the CSVs (the driver is deliberately
1-D; a Cartesian product is a thin outer loop, not a new tool).

## Defining Parameter Grids (simplified-model UFOs)

### Using scan_grid.py

The `scripts/scan_grid.py` module generates parameter grids:

```python
from scripts.scan_grid import make_grid

# Scan DM mass vs. coupling
grid = make_grid({
    "MASS:9000006": (10.0, 1000.0, 50),     # DM mass: 10–1000 GeV, 50 points
    "DMINPUTS:1": (0.01, 4.0, 20),           # Coupling: 0.01–4.0, 20 points
}, spacing="log")  # Log spacing for mass, linear also available

print(f"Total grid points: {len(grid)}")  # 50 * 20 = 1000
```

### Spacing options

- `linear`: Uniform spacing between min and max
- `log`: Logarithmic spacing (requires positive min/max) — preferred for mass scans spanning orders of magnitude

## Batch Orchestration

### Generating batch scripts

Use `maddm_run.py` and `scan_grid.py` together:

```python
from scripts.maddm_run import generate_maddm_script
from scripts.scan_grid import make_grid, generate_batch

# Define the grid
grid = make_grid({
    "MASS:9000006": (10.0, 1000.0, 50),
    "DMINPUTS:1": (0.01, 4.0, 20),
}, spacing="log")

# Create a template script
template = generate_maddm_script(
    model="DMsimp_s_spin0",
    observables=["relic", "direct_detection"],
    params={"MASS:9000006": 100.0, "DMINPUTS:1": 1.0},  # placeholder values
)

# Generate one script per grid point
scripts = generate_batch(grid, template)

# Write to disk
for i, script in enumerate(scripts):
    with open(f"scan/point_{i:04d}.mg5", "w") as f:
        f.write(script)
```

### Parallelization strategies

**Sequential (simple)**:
```bash
for f in scan/point_*.mg5; do
    python3 "$MG5_DIR/bin/mg5_aMC" "$f"
done
```

**GNU Parallel**:
```bash
ls scan/point_*.mg5 | parallel -j 8 python3 "$MG5_DIR/bin/mg5_aMC" {}
```

**Cluster submission (HTCondor/SLURM)**:
Generate a job submission script per grid point, or use an array job:

```bash
# SLURM array job
#SBATCH --array=0-999
python3 "$MG5_DIR/bin/mg5_aMC" "scan/point_$(printf '%04d' $SLURM_ARRAY_TASK_ID).mg5"
```

## Collecting and Merging Results

### Reading output (agent-driven)

After all grid points complete, read `MadDM_results.txt` directly for each
point. MadDM 3.2+ writes results to
`<output_dir>/output/run_01/MadDM_results.txt`.

**Mandatory per point, before parsing anything:** call
`maddm_run.assert_launch_produced_output(output_dir, returncode=rc,
stdout_tail=stdout)` right after each launch returns. `mg5_aMC` can exit 0
having written no results while echoing the Planck constant
(`Omega h^2 = 1.2000e-01`) on stdout as if computed (see the DECAY1L gotcha in
`SKILL.md`); the guard raises `MADDM_LAUNCH_NO_OUTPUT` (recoverable) instead
of letting that echo enter your scan table. Use a fresh output dir per point
(`fresh=True`, the default) — the guard resolves the newest results file by
mtime, so a reused dir could satisfy it with a previous run's stale results.
(`scan_sarah_dd.py` performs the equivalent check itself, marking the point
`stage: "no_results_txt"`; this step is for hand-rolled loops like the one
below.)

```python
import re
from pathlib import Path

_BRACKET_RE = re.compile(r"\[\s*([\deE.+-]+)\s*,\s*([\deE.+-]+)\s*\]")
_SIGMAN_KEYS = {
    "SigmaN_SI_p": "sigma_si_proton",
    "SigmaN_SI_n": "sigma_si_neutron",
    "SigmaN_SD_p": "sigma_sd_proton",
    "SigmaN_SD_n": "sigma_sd_neutron",
}

results = []
for i, point in enumerate(grid):
    output_dir = f"scan/output_{i:04d}"
    results_file = Path(output_dir) / "output" / "run_01" / "MadDM_results.txt"
    text = results_file.read_text()
    obs = dict(point)  # start with parameter values

    # Omega h^2: line matching "Omegah2 = <value>" (MadDM 3.2+) or
    # "Omega h^2 = <value>" (legacy).
    for line in text.splitlines():
        if line.lstrip().startswith(("Omegah2", "Omega h^2")):
            obs["omega_h2"] = float(line.split("=", 1)[1].strip())
            break

    # Per-nucleon σ: MadDM 3.2 emits `SigmaN_SI_p = [sigma, exp_limit]` etc.
    # We capture only the first bracket element (the predicted σ at this mass).
    for line in text.splitlines():
        stripped = line.lstrip()
        for maddm_key, out_key in _SIGMAN_KEYS.items():
            if stripped.startswith(maddm_key):
                m = _BRACKET_RE.search(line)
                if m:
                    obs[out_key] = float(m.group(1))

    results.append(obs)
```

See [`reading-output.md`](reading-output.md) for the full field-extraction
patterns (including per-channel percentages). Do not use `parse_maddm_output` —
it is not defined in `maddm_run.py` and was removed.

### Result format

Each result dict contains the grid point parameters plus computed observables.
Per-nucleon σ values are the predicted cross-section at this DM mass (first
element of MadDM's `[sigma, exp_limit]` bracket pair):

```python
{
    "MASS:9000006": 100.0,
    "DMINPUTS:1": 1.0,
    "omega_h2": 0.12,
    "sigma_si_proton": 1.23e-46,
    "sigma_sd_proton": 4.56e-42,
}
```

### Saving to CSV

```python
import csv

fieldnames = list(results[0].keys())
with open("scan_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)
```

## Comparing Against Experimental Limits

### No exclusion CSV ships — two ways to get a limit curve

**`assets/limit_data/` is empty by design** — it ships only a `README.md`
pointing at the public data releases; no `LZ_SI.csv` (or any other curve) is
bundled. So `load_limit("LZ", "SI", data_dir="assets/limit_data/")` raises a
missing-file error out of the box. You have two options:

1. **Preferred — drive `/ddcalc`'s registered `LZ_2022` likelihood** (real
   compiled DDCalc data, not a digitization). To draw an LZ 90%-CL σ_SI(m)
   curve, bisect `sigma_si_proton_cm2` against `/ddcalc`'s own `p_value` output
   (crossing 0.1) on a mass grid — this is the same registered likelihood
   `/ddcalc` dispatches to for every DD verdict in this toolkit. See
   `ddcalc/SKILL.md`'s experiment registry and `run_ddcalc.py run`. (This is how
   the Fig. 1 reproduction built its LZ curve.)
2. **Digitized CSV** — download a curve from the public sources in
   `assets/limit_data/README.md`, drop it in a directory as `LZ_SI.csv`
   (columns `mass_GeV, limit_value`, no header), and point `load_limit` at that
   directory. Only then does the snippet below work.

### Loading a (user-provided) digitized limit CSV

Use `scripts/limits.py` — this requires you to have placed a CSV per option 2:

```python
from scripts.limits import load_limit, is_excluded, overlay_on_limit

# Load the LZ SI limit (from a CSV you downloaded and placed yourself)
lz_limit = load_limit("LZ", "SI", data_dir="path/to/your/limit_csvs/")
```

Limit files are CSV with columns: `mass_GeV, limit_value`. See `assets/limit_data/README.md` for where to obtain them.

### Checking exclusion

```python
# Check a single point
point = {"mass": 100.0, "value": 1.23e-46}
print(is_excluded(point, lz_limit))  # True or False

# Check all scan results
for r in results:
    r["excluded_LZ"] = is_excluded(
        {"mass": r["MASS:9000006"], "value": r["sigma_si_proton"]},
        lz_limit,
    )
```

### Preparing exclusion plots

```python
plot_data = overlay_on_limit(
    [{"mass": r["MASS:9000006"], "value": r["sigma_si_proton"]} for r in results],
    lz_limit,
)

# plot_data contains: limit_mass, limit_value, allowed_mass, allowed_value,
#                     excluded_mass, excluded_value
# Feed to matplotlib or the hep-plotting plugin for visualization
```

### Available Experiments

#### Direct detection (SI)

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| LZ (LUX-ZEPLIN) | SI | Phys. Rev. Lett. 131, 041002 (2023) |
| XENONnT | SI | Phys. Rev. Lett. 131, 041003 (2023) |
| PandaX-4T | SI | Phys. Rev. Lett. 127, 261802 (2021) |

#### Direct detection (SD)

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| PICO-60 | SD (proton) | Phys. Rev. D 100, 022001 (2019) |
| LZ | SD (neutron) | Phys. Rev. Lett. 131, 041002 (2023) |

#### Indirect detection

| Experiment | Observable | Reference |
|-----------|-----------|-----------|
| Fermi-LAT | <sigma v> (bb, WW, tautau channels) | Phys. Rev. Lett. 115, 231301 (2015) |
| MAGIC | <sigma v> (dSphs) | JCAP 02, 039 (2016) |
| H.E.S.S. | <sigma v> (GC) | Phys. Rev. Lett. 117, 111301 (2016) |
