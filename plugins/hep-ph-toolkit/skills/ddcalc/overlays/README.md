# DDCalc Overlays

Overlay bundles for new experiments are installed via `/ddcalc-install`:

```
/ddcalc-install install --with-overlay lz_xenonnt_pandax4t_2024
```

Each overlay bundle lives at:
```
plugins/hep-ph-toolkit/skills/ddcalc-install/overlays/<name>/
```

See that directory for:
- `manifest.yaml` — pinned upstream commit SHA, patch list, efficiency-table SHA256s, `overlay_sha`
- `patches/` — Fortran source patches for `src/DDExperiments.f90`, `include/DDExperiments.hpp`, `Makefile`, and new experiment modules
- `data/` — efficiency tables
- `*.NOTICE` — per-experiment attribution
- `ATTRIBUTIONS.md` — aggregate attribution

**v1 status:** The `lz_xenonnt_pandax4t_2024` overlay is DEFERRED to v1.1
(central-dispatcher registration pattern; see Step 0 verifications).
Native v1 supports: XENON1T_2018, LUX_2016, PandaX_2017, PICO_60_2019, DarkSide_50.
