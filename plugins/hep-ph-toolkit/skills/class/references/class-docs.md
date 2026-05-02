# CLASS v3.3.4 — Reference Documents

## Primary references

- **CLASS paper I**: Lesgourgues 2011, arXiv:1104.2933
  "The Cosmic Linear Anisotropy Solving System (CLASS)"

- **CLASS paper II**: Blas, Lesgourgues, Tram 2011, JCAP 07 (2011) 034, arXiv:1104.2933
  "The Cosmic Linear Anisotropy Solving System (CLASS). Part II: Approximation schemes"

- **CLASS v2 + classy**: Lesgourgues & Tram 2014, JCAP 09 (2014) 032, arXiv:1312.2697
  "Fast lensed-CMB power spectra with CLASS"

- **Repository**: https://github.com/lesgourg/class_public (tag v3.3.4)

## Pin information

| Key          | Value                                      |
|--------------|--------------------------------------------|
| `class_tag`  | `v3.3.4`                                   |
| `class_commit` | `e85808324f51fc694d12e3ed7439552a3c3f9540` |
| `classy` pip | `pip install "git+https://github.com/lesgourg/class_public@v3.3.4#subdirectory=python"` |

## Preset sources

| Preset           | Reference                                             |
|------------------|-------------------------------------------------------|
| `planck18`       | Planck 2018 results VI, arXiv:1807.06209, Table 2     |
| `planck18_act`   | ACT DR4, Aiola+ 2020, arXiv:2007.07288, Table 4       |

## BSM extension references

| Extension kind     | Key reference                                      |
|--------------------|----------------------------------------------------|
| `dcdm`             | Poulin+ 2016, JCAP 04 (2016) 027, arXiv:1602.02155 |
| `idm_baryon`       | Chen+ 2002, arXiv:astro-ph/0201503                 |
| `idm_dr`           | Buen-Abad+ 2018, arXiv:1708.09406                  |
| `idm_photon`       | Wilkinson+ 2014, arXiv:1407.6990                   |
| `exotic_injection` | Finkbeiner & Weiner 2012, arXiv:1209.5575 (CLASS 3.x implementation) |
| `ncdm_extra`       | Lesgourgues & Pastor 2006, Phys. Rept. 429, 307    |

## CLASS ini file documentation

The canonical CLASS parameter reference is maintained in the repository:
  `https://github.com/lesgourg/class_public/blob/v3.3.4/explanatory.ini`

Key sections relevant to HEPhaestus use:
- `explanatory.ini §"Background parameters"` — H0, omega_b, omega_cdm, etc.
- `explanatory.ini §"Output parameters"` — output, lensing, l_max_scalars, z_pk
- `explanatory.ini §"Non-cold dark matter"` — ncdm, DCDM
- `explanatory.ini §"Dark matter-baryon interactions"` — idm_b, idm_dr

## Output format

TSV files (`.dat`) produced by parse_outputs.py follow the convention:
- First line: `# col_a col_b col_c ...` (space-separated column names)
- Data lines: space-separated values in `f"{x:.10e}"` format
- No trailing whitespace; one trailing newline

## Known issues

- **macOS arm64 + libomp**: OpenMP may be absent. CLASS builds single-threaded;
  `class_openmp_enabled=0` is set in config. CMB runs at lmax≥2000 may be slow.
- **classy import path**: classy must be installed into `config["python"]` (the
  same Python binary recorded at install time). If the active Python differs,
  `CLASS_NOT_CONFIGURED` or `CLASS_RUNTIME_FAILURE` may be emitted.
