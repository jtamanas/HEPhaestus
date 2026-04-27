# MadGraph Analysis

Working with MG5 output: LHE parsing, banner files, cross-sections, and parameter scanning.

## LHE File Structure

MG5 produces Les Houches Event (LHE) files — XML format defined by the Les Houches Accord.

### Overall structure

```xml
<LesHouchesEvents version="3.0">
  <header>
    <!-- MG5 banner with input cards and run metadata -->
  </header>
  <init>
    <!-- Beam info, process cross-sections -->
    2212 2212 6.800000e+03 6.800000e+03 ...
    xsec  xerr  xmax  process_id
  </init>
  <event>
    <!-- Per-event: particle listing -->
    nparticles  proc_id  weight  scale  aqed  aqcd
    pdgid status mother1 mother2 color1 color2 px py pz energy mass lifetime spin
    ...
  </event>
  <!-- More <event> blocks -->
</LesHouchesEvents>
```

### `<init>` block

The first line has beam info:
```
IDBMUP(1) IDBMUP(2) EBMUP(1) EBMUP(2) PDFGUP(1) PDFGUP(2) PDFSUP(1) PDFSUP(2) IDWTUP NPRUP
```

Subsequent lines (one per subprocess):
```
XSECUP  XERRUP  XMAXUP  LPRUP
```

- `XSECUP` — cross-section in pb
- `XERRUP` — Monte Carlo integration error in pb
- `XMAXUP` — maximum weight
- `LPRUP` — subprocess ID

### `<event>` block

First line: `nparticles  process_id  weight  scale  alpha_QED  alpha_QCD`

Particle lines (one per particle):
```
PDG_ID  status  mother1  mother2  color1  color2  px  py  pz  energy  mass  lifetime  spin
```

Status codes:
- `-1` — initial state
- `1` — final state
- `2` — intermediate resonance

Momenta are in GeV, lifetime in mm/c.

## Banner Files

MG5 writes a banner file (`<run_name>_<tag>_banner.txt`) in the Events directory. It contains:

1. The input proc_card, param_card, and run_card (embedded verbatim)
2. Cross-section results
3. Run metadata (MG5 version, timestamp, random seed)

### Extracting info from banner

The banner is plain text with XML-like tags:

```
<MGGenerationInfo>
#  Number of Events        : 100000
#  Integrated weight (pb)  : 8.317e+02
</MGGenerationInfo>
```

Cross-section is in the `Integrated weight` line, in picobarns.

## Cross-Section Extraction

### From stdout

During generation, MG5 prints:
```
  === Results Summary for run: run_01 tag: tag_1 ===
     Cross-section :   831.7 +- 2.1 pb
     Nb of events  :   100000
```

### From LHE file

Use `scripts/lhe_parser.py`:

```python
from scripts.lhe_parser import extract_cross_section
xsec, error = extract_cross_section("Events/run_01/unweighted_events.lhe.gz")
print(f"σ = {xsec:.1f} ± {error:.1f} pb")
```

### From banner

```python
import re
with open("Events/run_01/run_01_tag_1_banner.txt") as f:
    banner = f.read()
match = re.search(r"Integrated weight \(pb\)\s*:\s*([\d.eE+-]+)", banner)
xsec_pb = float(match.group(1))
```

## Parameter Scanning

Systematic exploration of parameter space by generating events at multiple param_card points.

### Strategy

1. Define the parameter grid (which SLHA block entries to vary and their ranges)
2. Generate a param_card for each grid point
3. Run MG5 at each point (same proc_card and run_card)
4. Collect cross-sections and/or event files from each point

### Using scripts/card_io.py

```python
from scripts.card_io import read_param_card, update_param, write_param_card

base_card = read_param_card("param_card.dat")

# Scan top mass from 170 to 175 GeV in 6 steps
for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    card = dict(base_card)  # shallow copy (deep copy blocks if needed)
    update_param(card, "mass", 6, mt)
    write_param_card(card, f"param_card_mt{mt:.0f}.dat")
```

### Batch submission

Use `scripts/mg5_batch.py` to generate launch scripts for each grid point:

```python
from scripts.mg5_batch import generate_launch_script

for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    script = generate_launch_script(
        proc_dir="pp_ttbar",
        param_card=f"param_card_mt{mt:.0f}.dat",
        nevents=50000,
        seed=int(mt * 100),
        run_name=f"scan_mt{mt:.0f}",
    )
    with open(f"launch_mt{mt:.0f}.sh", "w") as f:
        f.write(script)
```

### Collecting results

After all runs complete, extract cross-sections:

```python
from scripts.lhe_parser import extract_cross_section

results = []
for mt in [170.0, 171.0, 172.0, 173.0, 174.0, 175.0]:
    lhe_path = f"pp_ttbar/Events/scan_mt{mt:.0f}/unweighted_events.lhe.gz"
    xsec, err = extract_cross_section(lhe_path)
    results.append({"mt": mt, "xsec": xsec, "error": err})
```
