# Experimental Limit Data

This directory is for user-provided digitized exclusion curves. The limit data files are **not bundled** — download them from the public sources below.

## Expected File Format

CSV files with two columns, no header row:

```
# mass_GeV, limit_value
10.0, 1.0e-43
20.0, 5.0e-45
50.0, 1.2e-46
...
```

- Mass in GeV
- SI/SD limits in cm^2
- <sigma v> limits in cm^3/s
- Lines starting with `#` are treated as comments

## File Naming Convention

```
{Experiment}_{Observable}.csv
```

Examples: `LZ_SI.csv`, `XENONnT_SI.csv`, `FermiLAT_sigmav_bb.csv`, `PICO60_SD.csv`

## Where to Get Limit Data

### Direct Detection

- **LZ (LUX-ZEPLIN)**: Data release at https://lz.lbl.gov/results/ — download the 90% CL upper limit table
- **XENONnT**: Data at https://xenonnt.org/results — published limit tables in supplementary materials
- **PandaX-4T**: Supplementary data in Phys. Rev. Lett. 127, 261802 (2021)

### Indirect Detection

- **Fermi-LAT**: Limit tables in supplementary materials of Phys. Rev. Lett. 115, 231301 (2015). Also available via the Fermi Science Support Center.
- **MAGIC**: Published limits in JCAP 02, 039 (2016), supplementary tables
- **H.E.S.S.**: Published limits in Phys. Rev. Lett. 117, 111301 (2016)

### Digitized Limit Repositories

- **HEPData**: https://www.hepdata.net/ — many experimental results include digitized limit curves
- **GAMBIT DarkBit**: https://github.com/GambitBSM — includes digitized limit data for many experiments
- **DDCalc**: https://github.com/GambitBSM/DDCalc — direct detection limit data and calculator

## Usage

```python
from scripts.limits import load_limit

# Place your downloaded CSV in this directory, then:
lz = load_limit("LZ", "SI", data_dir="path/to/this/directory")
```
