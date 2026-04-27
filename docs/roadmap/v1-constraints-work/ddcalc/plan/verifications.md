# DDCalc Step-0 Verifications

**Date:** 2026-04-19
**Executor:** W9-dd workstream implementer

---

## §overlay-feasibility

### Source structure (DDCalc v2.2.0, GambitBSM/DDCalc@9364c02)

Experiment registration in DDCalc 2.2.0 uses the **central-dispatcher pattern**.
Three files must be edited to add any new experiment:

1. `src/DDExperiments.f90` — `USE <ExperimentModule>` statement added to the
   `DDExperiments` MODULE, plus an entry in the `AvailableAnalyses` function
   (present in 2.2.0 via the DDCalc CLI path).

2. `include/DDExperiments.hpp` — C extern declaration
   `int C_DDCalc_<experiment>_init();` plus a namespace wrapper inline.

3. `Makefile` — `analyses` variable listing (line 174-180) must include the
   new `.f90` filename for it to be compiled into `libDDCalc.a`.

**There is no drop-in-module mechanism.** Every new experiment requires editing
the three files listed above. A `git apply --3way` patch against multiple
simultaneously edited files is structurally fragile, especially for the
`Makefile` variable and the `USE` block in `DDExperiments.f90`, where patches
from different overlay bundles would conflict.

### DECISION: NATIVE-ONLY v1 (fallback triggered)

Per plan §2 decision gate: the central-dispatcher pattern makes patch-based
overlays structurally fragile for `git apply --3way`. The v1 implementation
ships with native DDCalc 2.2.0 experiments only. Overlay work (LZ WS2024,
XENONnT 2023, PandaX-4T 2021) is deferred to **v1.1 backlog**.

Consequence: Commit 7 is a stub manifest + NOTICE with `deferred: v1.1`.
The `/ddcalc run` skill will NOT emit `reference_only` status — this field
is removed from the output contract (per brainstorm §5, `DDCALC_REFERENCE_ONLY`
is forbidden). When a post-2022 experiment is requested, the skill emits
`DDCALC_OVERLAY_MISSING` (fatal) with context pointing to v1.1.

Note: `DDCALC_OVERLAY_NOT_SUPPORTED_V1` marker is recorded in `apply_overlay.sh`
for machine-readable discovery.

---

## §url-probe

**Primary:** `https://gitlab.com/ddcalc/ddcalc` — HTTP 302 → sign-in page.
Project is private on gitlab.com/ddcalc/ddcalc (API returns 404).

**Mirror 1:** `https://github.com/GambitBSM/DDCalc` — **HTTP 200.**
v2.2.0 tag: commit `9364c02dca3d23e75558e3238229a6fa41a8ec1a`.
Archive URL: `https://github.com/GambitBSM/DDCalc/archive/refs/tags/v2.2.0.tar.gz`

**Mirror 2:** `https://www.hepforge.org/downloads/DDCalc/DDCalc-2.2.0.tar.gz`
— HTTP 302 → unavailable (HEPForge Redmine decommissioned).

**Archive.org fallback:** `https://web.archive.org/web/2024/https://www.hepforge.org/downloads/DDCalc/DDCalc-2.2.0.tar.gz` — HTTP 404.

**Result:** GambitBSM GitHub mirror is the canonical download URL for v1.
Recorded in `skill_env.yaml` as `HEPPH_DDCALC_URL`.

---

## §sha256

```
URL:   https://github.com/GambitBSM/DDCalc/archive/refs/tags/v2.2.0.tar.gz
SHA256: b12d63f7baafc6ee43e090fa3d1df15d194bddb453b3d5173e895fb3ac517847
Fetch date: 2026-04-19
Fetch command: curl -sL <URL> -o /tmp/ddcalc_v220.tgz && shasum -a 256 /tmp/ddcalc_v220.tgz
```

Note: The extracted `src/DDConstants.f90` shows `VERSION_STRING = '2.1.0'` even
in the v2.2.0 tag. The tag was applied (February 2020) without updating the
internal version string. The HISTORY file confirms v2.2.0 adds PICO-60 (2019),
DarkSide-50 (S2-only), and CRESST-III. The version banner patch
(`patches/version_banner.patch`) is required.

---

## §banner-capture

The stock `DDCalc_test.f90` main program only prints:
```
 DDCalc successfully initialized
```
No version string is emitted. The `VERSION_STRING` constant in `DDConstants.f90`
is `'2.1.0'` (not updated at tag time). The smoke test therefore cannot parse
a version line from the stock binary.

**Action:** `patches/version_banner.patch` is required. The patch adds a single
`WRITE` statement to `src/DDCalc.f90`'s `DDCalc_InitWIMP` routine (the first
C-callable function invoked by the example driver) to print:
```
DDCalc 2.2.0
```
This matches the `DDCalc\s+v?([0-9.]+)` pattern used by `_smoke_test.sh`.

---

## §neutrino-fog-license

**Repository:** `https://github.com/cajohare/NeutrinoFog`
**Commit SHA:** `0df3d0cd2322602dc147a66d94055f7f64879d80` (2022-06-07)
**LICENSE:** MIT (Copyright (c) 2019 cajohare)
**Decision:** License is MIT — vendoring approved for v1.

**CSV file for SI Xenon floor (used in 2506.19062 Fig. 6/7):**
`data/WIMPLimits/SI/nufloor-Xe.txt`
Format: two-column whitespace-separated (m_DM [GeV], σ_SI [cm²])
1000 rows, m_DM range: 0.1 → 10000 GeV
SHA256: `da5eadf0df53d6a6d22835e4eecc9fe4d434decd9eed439310236893ed60f1fb`

Vendored to: `plugins/hep-ph-toolkit/skills/ddcalc/data/neutrino_fog_ohare_2021.csv`

**Citation:** C.A.J. O'Hare, "New Definition of the Neutrino Floor for Direct
Dark Matter Searches," Phys. Rev. Lett. 127, 251802 (2021),
arXiv:2109.03116. GitHub: cajohare/NeutrinoFog@0df3d0c.

---

## §nu-floor-curve-2506.19062

The paper 2506.19062 (Arcadi–Profumo 2025) uses the Xenon SI neutrino floor
from O'Hare 2021, which is the `data/WIMPLimits/SI/nufloor-Xe.txt` curve.
This is the "discovery limit" definition (n=2, n_σ=2 events above background),
corresponding to the `discovery_limit_90cl` definition in the output schema.
