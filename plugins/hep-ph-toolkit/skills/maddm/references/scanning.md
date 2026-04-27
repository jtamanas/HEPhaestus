# MadDM Parameter Scanning

Systematic exploration of BSM parameter space with MadDM.

## Defining Parameter Grids

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

```python
from pathlib import Path

results = []
for i, point in enumerate(grid):
    output_dir = f"scan/output_{i:04d}"
    results_file = Path(output_dir) / "output" / "run_01" / "MadDM_results.txt"
    text = results_file.read_text()
    obs = dict(point)  # start with parameter values

    # Extract Omega h^2: line matching "Omegah2 = <value>" (MadDM 3.2+)
    # or "Omega h^2 = <value>" (legacy)
    for line in text.splitlines():
        if "Omegah2" in line or "Omega h^2" in line:
            obs["omega_h2"] = float(line.split("=")[1].strip())
            break

    # Extract sigma_SI_proton, sigma_SI_neutron, sigma_SD_proton, sigma_SD_neutron
    # lines matching "sigma_SI_proton = <value>" etc.
    for line in text.splitlines():
        for key in ("sigma_SI_proton", "sigma_SI_neutron",
                    "sigma_SD_proton", "sigma_SD_neutron"):
            if line.strip().startswith(key):
                obs[key.lower()] = float(line.split("=")[1].strip())

    results.append(obs)
```

See `maddm/SKILL.md` §"Reading MadDM output (agent-driven)" for the full
field-extraction patterns (including per-channel percentages). Do not use
`parse_maddm_output` — it is not defined in `maddm_run.py` and was removed.

### Result format

Each result dict contains the grid point parameters plus computed observables:

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

### Loading limit data

Use `scripts/limits.py`:

```python
from scripts.limits import load_limit, is_excluded, overlay_on_limit

# Load the LZ SI limit
lz_limit = load_limit("LZ", "SI", data_dir="assets/limit_data/")
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
