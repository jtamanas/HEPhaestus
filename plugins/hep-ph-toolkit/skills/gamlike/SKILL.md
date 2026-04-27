---
name: gamlike
version: "0.1.0"
description: "MadDM_results.txt → gamlike/v1 JSON parser (v0 — parser only; pull computation v1+)"
plugin: constraints
---

# `/gamlike` — MadDM results parser (v0)

**Scope claim (D2): This is a PARSING-ONLY skill. It does NOT compute likelihood pulls, exclusion verdicts, or any physics interpretation. The indirect-detection physics layer (pull computation) remains blocked on a future `[future: dm-pull (v1+)]` skill.**

v0 unblocks **the parsing layer** of indirect-detection workflows for 2HDM+a and singlet-doublet. It does NOT unblock the physics layer.

---

## CLI

```bash
python plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py \
    <results-path> [--out <json-path>] [--md-summary <md-path>]
```

### Arguments

| Argument | Meaning | Default |
|---|---|---|
| `<results-path>` | Path to `MadDM_results.txt` (required, positional) | — |
| `--out <json-path>` | Where to write the gamlike JSON output | `<results-path>.gamlike.json` |
| `--md-summary <md-path>` | Optional: write a markdown summary to this path | Not written unless flag set |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Parsed successfully; JSON written; stdout is the absolute path to the JSON |
| 2 | Input file not found |
| 3 | Input file present but malformed (invariant I1–I6 violation; see stderr for section + details) |

Codes 1, 4, 5 are unused in v0.

---

## Stable invocation path (D-DPATH)

The canonical parser path, committed to as stable:
```
plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py
```

Consumers compute this relative to the demo working directory (which is the repo root). Example:

```python
import json, subprocess, sys
from pathlib import Path

maddm_results_path = Path("demo_output/2hdm-a/maddm_run/output/run_01/MadDM_results.txt")
gamlike_json_path  = Path("demo_output/2hdm-a/gamlike.json")

subprocess.run([
    sys.executable,
    "plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py",
    str(maddm_results_path),
    "--out", str(gamlike_json_path),
], check=True)

gamlike = json.loads(gamlike_json_path.read_text())
```

No `extract_field.py` in the v0 consumer chain (Path X / O6). Use in-process `json.loads()` + nested dict access.

---

## Output JSON schema (`gamlike/v1`)

Schema document: `contracts/gamlike_v1.schema.json`

Full field reference: `references/maddm_output_schema.md`

### Top-level structure

```json
{
  "schema_version": "gamlike/v1",
  "_meta": { "source_file": "...", "parser_version": "...", "maddm_version": "...", "parsed_at": "..." },
  "relic": { "present": bool, "Omegah2": float|null, "xsi": float|null, "channels": {...}, ... },
  "direct": { "present": bool, "results": [...] },
  "indirect": { "present": bool, "global": { "Total_xsec": ..., "thermal_emitted": bool, ... }, ... },
  "spectral": { "present": bool, "experiments": [...] },
  "fluxes_source": { "present": bool, "method": ..., "fluxes": {...} },
  "warnings": [{"code": "...", "field": "...", "reason": "...", "source_ref": "..."}]
}
```

Key schema decisions:
- `relic.channels` is **nested by initial-state pair** (D4): `{<initial>: {<final>: <pct>}}`.
- `channels_sum_pct` is raw percent; consumer does `pct / total` normalization (D3).
- `indirect.global.Total_xsec` XOR `TotalSM_xsec` is non-null (invariant I1).
- `indirect.global.thermal_emitted` reflects whether G13 fired (`xsi < 1.0`).
- Reserved-null fields: `spectral.experiments[].astrophysical_parameters` (G19), `fluxes_source.fluxes.positrons` (G21).

---

## Conditional emission gates

Full enumeration: `references/conditional_emission_gates.md`

Each gate G1–G21 (from `maddm_run_interface.py:3444-3628`) is documented with its producer condition, source-line citation, and v0 handling.

Key gates:
- **G13 (thermal pair):** `Fermi_Likelihood(Thermal)` / `Fermi_pvalue(Thermal)` emitted iff `xsi < 1.0`. Otherwise: `thermal_emitted: false`, both null, `FIELD_GATED` warning with `source_ref="maddm_run_interface.py:3572-3574"`.
- **G10/G11 (XOR):** `Total_xsec` (non-inclusive method) XOR `TotalSM_xsec` (inclusive). Both null → exit 3.
- **G16 (no peaks):** `# No peaks found: out of detection range.` → `peaks: []`, `no_peaks_out_of_range: true`, `NO_PEAKS_OUT_OF_DETECTION_RANGE` warning.

---

## Model-router integration (MR13)

`/gamlike` is wired into `/model-router` as the **`id` observable validator** (role=`validator`, priority_tiebreak=20). It is downstream of `maddm` (role=`primary`, priority=10); `maddm` still outranks `gamlike` for the `id` active chain.

`gamlike.status` in `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml`: `exists`

See `plugins/hep-ph-toolkit/skills/model-router/SKILL.md` for the router's role/priority framework.

---

## Consumer migration pattern

For 2HDM+a and singlet-doublet consumers (see `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md`):

```python
# Consumer-side normalization (D3): /gamlike emits raw pct; consumer normalizes.
relic = gamlike["relic"]
flat_channels = {}
for init_state, finals in relic["channels"].items():
    flat_channels.update(finals)  # flatten initial-state nesting

total = sum(v for v in flat_channels.values() if v is not None) or 1.0
fractions = {k: v / total for k, v in flat_channels.items() if v is not None}

gate_check = {"channels_sum_in_unity_range": 0.99 <= sum(fractions.values()) <= 1.01}
if not gate_check["channels_sum_in_unity_range"]:
    raise ValueError(f"channel_fractions out of [0.99,1.01]")
```

WS2 note: consumers should also add `summary["dm_indirect_detection_status"] = "parser-only"` (D21).

---

## Versioning (D7)

Schema stays on `gamlike/v1` for additive changes (new fields under existing objects). Bump to `gamlike/v2` only on:
- Field rename or removal
- Semantic change to an existing field
- Change to `additionalProperties: false` structure

The schema version is the literal string `"gamlike/v1"` everywhere (code, schema `$id`, tests, prose). No `v1.x` variants.

---

## Sharp edges

### R-XSI: xsi clamp
Producer clamps `xsi = min(Ωh²/Ωh²_Planck, 1.0)`. Values in output are always in (0, 1]. The parser uses `xsi >= 1.0` as the G13 gate (D16). The clamp means `xsi > 1.0` never appears in real output.

### Trailing whitespace (D14)
Producer emits trailing space before `\t #` comment on `xsi` and `sigmav_xf` lines (`:3475`, `:3477`). `Fermi_pvalue(Thermal)` line has trailing `\n ` (`:3574`). Parser's `\s*$` tolerates these.

### NaN/Inf normalization (D15)
Any `nan` or `inf` in a numeric field → JSON `null` + `FIELD_NAN`/`FIELD_INF` warning. The real singlet-doublet fixture has `nan %` for all channels (MadDM run failure). JSON output never uses `allow_nan=True`.

### xsi == 1.00e+00 boundary (D16)
`xsi >= 1.0` is a Python comparison (no FP slop). At exactly 1.0 (the clamped case), G13 does NOT fire.

### Reserved fields (G19, G21)
`spectral.experiments[].astrophysical_parameters` and `fluxes_source.fluxes.positrons` are always `null` in v0. Producer lines `:3580-3582` and `:3627-3628` are currently commented out.

### `--md-summary` is best-effort
The markdown summary is informational. Its format is NOT part of the byte-stable contract. B7 renderer bug (separate workstream) may affect how it renders.

### Singlet-doublet relic.json asymmetric upgrade (O4)
Post-WS1, singlet-doublet `relic.json` includes `channel_fractions` and `gate_check` fields that the pre-migration version lacked. WS2 must NOT assume these fields are absent.

### Pre-3.2 MadDM legacy alias (D8/U2)
`Omega h^2` (with space) is recognized as a legacy alias for `Omegah2`. No real pre-3.2 fixture is available; this is documentation-driven defensive parsing. A `MADDM_VERSION_UNTESTED` warning is emitted when the version header is unrecognized.

### pytest -W error (D-PYW)
Tests run with `pytest -W error --strict-markers`. The `jsonschema` library may emit deprecation warnings; these are suppressed via `pytest -p no:warnings` fallback in `run_tests.sh`.
