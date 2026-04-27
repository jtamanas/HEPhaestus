# Feynman Diagrams plugin — shared conventions

## Version matrix

| Tool | Version | Status |
|---|---|---|
| FeynArts | **3.11** (pinned) | Installed via `/feynarts-install` |
| FormCalc | 10.0 | Reserved for `/formcalc` (Phase-B stage 2) |
| LoopTools | 2.1x | Used by `/formcalc` for Passarino-Veltman evaluation (Phase-B stage 3) |

Versions are pinned conservatively. Caps will be revisited in v1.1 once paper
benchmarks quantify real-world requirements.

---

## Env-var overrides

| Variable | Default | Consumer | Purpose |
|---|---|---|---|
| `FEYNARTS_DIAGRAM_CAP` | `2000` | `/feynarts` | Override diagram count cap (fatal if exceeded before CreateFeynAmp) |
| `FEYNARTS_AMP_SIZE_CAP_MB` | `200` | `/feynarts` | Override amp-file size cap in MB (fatal if exceeded after Put) |
| `FEYNARTS_DEFAULT_TIMEOUT_S` | `600` | `/feynarts` | Override wolframscript wall-clock timeout (SIGKILL on expiry) |
| `HEPPH_FEYNARTS_STATE_ROOT` | `~/.local/share/hephaestus` | `/feynarts` | Override state root for cache + SARAH model states |
| `HEPPH_FEYNARTS_VERSION` | `3.11` | `/feynarts-install` | Override FeynArts version to install |
| `HEPPH_NO_NETWORK` | `0` | `/feynarts-install` | Set to `1` to use offline cache (requires `HEPPH_OFFLINE_CACHE_DIR`) |

---

## Cross-plugin Wolfram helper reference

Shared Wolfram helpers live in `plugins/shared/install-helpers/wolfram/` and are
consumed by both `model-building/` and `feynman-diagrams/` plugins:

| File | Purpose |
|---|---|
| `detect_wolfram.sh` | Scan for `wolframscript` binary; emit path or empty |
| `check_wolfram_activation.sh` | Probe `wolframscript -code '1+1'`; classify stdout via `_activation_parse.py` |
| `_activation_parse.py` | Parse wolframscript output for activation/error/ok status |

Both `/feynarts-install` and `/sarah-install` call these helpers via absolute
paths derived from `$SCRIPT_DIR`. Do not copy these files.

---

## State directory layout

```
$HEPPH_FEYNARTS_STATE_ROOT/
├── cache/
│   └── feynarts/
│       └── <cache-key>/          # 64-char SHA256 hex
│           ├── FeynAmpList.m
│           ├── FeynAmpList.meta.json
│           ├── summary.json
│           ├── topologies.json
│           └── diagrams.pdf
└── models/
    └── <model-name>/
        └── feynarts_state/       # written by post-hoc MakeFeynArts[]
            ├── <model>.mod
            └── <model>.gen
```

---

## Cache key composition

The cache key is `sha256` of the `|`-joined concatenation of:

1. `sha256(<model>.mod)` — model particle content
2. `sha256(<model>.gen)` — generic model content
3. `sha256(feynarts_version)` — version string
4. `sha256(canonical processspec JSON)` — sorted keys + sorted `excludes`
5. `sha256(Models/Lorentz.gen)` — generic Lorentz model hash (`feynarts_generic_model_hash`)

Canonicaliser version: **1** (increment in `skill_env.yaml` when hash function changes
to invalidate all cached results).

---

## Blocker schema

All blockers conform to `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
(symlinked from `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`).

---

## No `reference_only` fallback

The `/feynarts` skill does not implement analytic fallbacks. Missing prerequisites
always result in fatal blockers, not silent approximations.

---

## Linkage to downstream tools

| Skill | Consumes | Produces |
|---|---|---|
| `/feynarts` | processspec/v1 | `FeynAmpList.m` + meta sidecar |
| `/formcalc` (Phase-B-2) | `FeynAmpList.m` | Fortran amplitudes + LoopTools PV evaluation |
