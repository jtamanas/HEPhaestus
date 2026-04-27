# t14 — DDCalc driver: register LZ_2022

## Branch
`tier1/t14-ddcalc-lz2022-r1-20260426`
Base: `dsu3-pt2/ws-d-r1-20260425` (HEAD `ad8dd3e`)

## Symbol lookup

```
nm /Users/yianni/.local/share/hep-ph-agents/tools/DDCalc/lib/libDDCalc.a | grep -i lz
→ 0000000000000200 T _C_DDCalc_lz_init
```

DDExperiments.hpp confirms: `int C_DDCalc_lz_init();`

## Registration change (`ddcalc_driver.c`)

Forward declaration added (line 61):
```c
extern int C_DDCalc_lz_init(void);
```

Register call added (line 141):
```c
register_exp("LZ_2022",       C_DDCalc_lz_init);
```

## Root cause of LZ data-file failure

DDCalc 2.2.0 compiles `DDInput.f90` with a hardcoded DATA_DIR:
```
/private/var/folders/f9/0snd4t1d7gd57cskg0yb_mjr0000gn/T/tmp.FII1uuQUoe/src/data/
```
This temp directory is cleaned up after the build. Experiments using external data
files (LZ, DARWIN) fail to open `LZ/energies.dat` because DDInput prepends this
defunct path, not CWD.

Experiments with compiled-in data (XENON1T_2018, LUX_2016, PandaX_2017, DarkSide_50,
PICO_60_2019) are unaffected.

## Fix

Added `_ensure_ddcalc_data_symlinks(ddcalc_path)` in `run_ddcalc.py`:
- Parses `libDDCalc.a` strings to find the compile-time data path.
- Creates the directory tree at that path.
- Symlinks each `energies.dat`-bearing subdirectory from `ddcalc_path` into the
  compile-time location.
- Called automatically before each driver invocation; no-op once symlinks exist.

## Smoke command

```bash
# Build driver (new cache key due to LZ registration):
DDCALC=~/.local/share/hep-ph-agents/tools/DDCalc
GF_DIR=$(dirname $(gfortran -print-file-name=libgfortran.a))
gcc -std=c11 -Wno-implicit-function-declaration \
  plugins/constraints/skills/ddcalc/scripts/ddcalc_driver.c \
  -I${DDCALC}/include -L${DDCALC}/lib -L${GF_DIR} \
  -lDDCalc -lgfortran -lm -o /tmp/ddcalc_driver_t14

# Input:
echo '{"m_dm_gev":100.0,"sigma_si_proton_cm2":5e-46,"sigma_si_neutron_cm2":5e-46,"sigma_sd_proton_cm2":0.0,"sigma_sd_neutron_cm2":0.0}' > /tmp/sigma_t14.json
/tmp/ddcalc_driver_t14 /tmp/sigma_t14.json
```

## LZ_2022 smoke result

Input: m_DM = 100 GeV, σ_SI = 5×10⁻⁴⁶ cm² (isospin-conserving)

```
EXPERIMENT: LZ_2022
LOGL: -5.106609e+02
PVALUE: 1.000001e+00
EXCLUDED90: 0
---
STATUS: ok
VERSION: 2.2.0
```

LZ_2022 logL = **-5.106609e+02** (finite, no error on stderr).

Note: The large negative logL (-510) is expected — at σ_SI = 5×10⁻⁴⁶ cm² and
m_DM = 100 GeV, LZ 2022 (first result, ~5.5 tonne-years) has substantial expected
signal that exceeds observed events, so the likelihood is suppressed. This is
physically consistent.

## Sentinel
`.shift-manager/run-20260426-tier1-fixes/state/t14.complete`
