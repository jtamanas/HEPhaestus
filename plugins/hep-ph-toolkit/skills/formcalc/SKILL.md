---
name: formcalc
description: Reduce a FeynArts amplitude list with FormCalc 9.10. Produces amp_reduced.m and amp_reduced.meta.json sidecar conforming to amp_reduced.meta/v1. Gated on formcalc-install.
---

## When to invoke

Use `/formcalc reduce` after `/feynarts generate` to analytically reduce the
FeynArts amplitude list to loop integrals in FormCalc's native PV basis.
Produces `amp_reduced.m` (Mathematica) and `amp_reduced.meta.json` (sidecar).

Prerequisites:

1. `/formcalc-install` must have run (`formcalc_path`, `form_binary` in config).
2. Wolfram Engine must be activated.
3. `/feynarts generate` must have produced `FeynAmpList.m` + `FeynAmpList.meta.json`.

---

## Subcommands

### `reduce`

```
/formcalc reduce \
  --feynamp  <path/to/FeynAmpList.m> \
  --process  <path/to/ProcessSpec.json> \
  --output-dir <dir> \
  [--reg     {dimreg|cdr|thv}]          default: dimreg \
  [--gamma5  {naive|hv|bmhv|larin}]     required if amplitude contains γ₅ \
  [--fermion-chains {weyl|dirac}]        default: weyl \
  [--dimension {4|D}]                    default: D \
  [--force]
```

---

## γ₅ gate (static check, fatal)

Before dispatching the Wolfram driver, `run_formcalc.py` calls
`gamma5_static_check.wls` to detect γ₅ usage in `FeynAmpList.m`.
If chirality projectors or γ₅ are found **and** `--gamma5` is absent,
the skill emits `FORMCALC_G5_SCHEME_REQUIRED` and exits non-zero.

The check uses exact Wolfram `Cases[...]` pattern matching — no regex on text.

---

## FeynArts version gate

The skill reads the `feynarts_version` field in `FeynAmpList.meta.json`.
If the version is not in the supported set `{"3.11"}`, it emits
`FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` and exits non-zero.

---

## PV-heads policy

`/formcalc` emits FormCalc-native `A0i`, `B0i`, `C0i`, `D0i` in `amp_reduced.m`
and records `"pv_heads": "formcalc-native"` in the sidecar.  No renaming is
performed.  LoopTools evaluates these integrals numerically.

---

## Outputs

| File | Description |
|---|---|
| `amp_reduced.m` | FormCalc-reduced amplitude; loadable via `Get[]` |
| `amp_reduced.meta.json` | Sidecar conforming to `amp_reduced.meta/v1` |
| `run/<ts>/summary.json` | `{n_diagrams, wall_clock_s, cached, gamma5_scheme}` |

All outputs are written to `--output-dir` (default `$PWD/formcalc_output/`).

---

## State layout

```
<output-dir>/
  input/
    FeynAmpList.m          → symlink to input
    FeynAmpList.meta.json  → symlink to input sidecar
    ProcessSpec.json       → symlink to process spec
  amp_reduced.m
  amp_reduced.meta.json
  kinematics.m
  .build_key               (cache token — written last via atomic_write.sh)
  run/<ts>/
    summary.json
    form.log               (FORM stdout/stderr, if FORM was invoked)
```

---

## Cache

Cache key = `sha256` of:
1. SHA256 of `FeynAmpList.m` bytes
2. Canonical JSON of `ProcessSpec.json` (sorted keys)
3. `--reg` flag
4. `--gamma5` flag (or `"none"` if absent)
5. `formcalc_version` from config
6. `form_version` from config
7. `looptools_version` from config

Cache hit requires `amp_reduced.m`, `amp_reduced.meta.json`, and `.build_key`
all present and `.build_key` matching.  Deleting `amp_reduced.m` with
`.build_key` in place forces a miss.

---

## Caps and blockers

| Code | Mode | Trigger | Context fields |
|---|---|---|---|
| `FORMCALC_G5_SCHEME_REQUIRED` | `fatal` | γ₅ found in FeynAmpList but `--gamma5` absent | `hint` |
| `FORMCALC_FEYNARTS_VERSION_INCOMPATIBLE` | `fatal` | `feynarts_version` not in `{"3.11"}` | `found`, `supported` |
| `FORMCALC_PATH_INVALID` | `fatal` | `formcalc_path` not set or `FormCalc.m` missing | `path` |
| `FORMCALC_SMOKE_TEST_FAILED` | `fatal` | `form_binary` not executable | `form_binary` |
| `FORMCALC_DRIVER_FAILED` | `fatal` | `run_calcfeynamp.wls` exited non-zero | `exit_code` |
| `FORMCALC_SIDECAR_INVALID` | `fatal` | Sidecar fails schema validation | `errors` |
| `WOLFRAM_KERNEL_ABSENT` | `fatal` | `wolfram_engine_path` not set | — |

---

## No `reference_only` fallback

This skill does not fall back to analytic results.  Missing install →
`FORMCALC_PATH_INVALID`.  Hard failures are safer than silent approximations.

---

## Regulators

| `--reg` value | Maps to | Sidecar caveat |
|---|---|---|
| `dimreg` | `Dimension -> D` | — |
| `cdr` | `Dimension -> D` | `FORMCALC_REG_UNVALIDATED` |
| `thv` | `Dimension -> D` | `FORMCALC_REG_UNVALIDATED` |

`cdr` and `thv` are accepted by the parser and mapped to `dimreg` with a
caveat in v1.  Full CDR/tHV support is deferred to v1.1.

---

## Linkage

- Phase-0 schemas: `plugins/shared/schemas/amp_reduced.meta.schema.json`
- Phase-0 schemas: `plugins/shared/schemas/processspec.schema.json`
- Atomic-write helper: `plugins/shared/install-helpers/atomic_write.sh`
- Blocker schema: `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- Install prereq: `/formcalc-install`
- Upstream: `/feynarts` (provides `FeynAmpList.m` + `FeynAmpList.meta.json`)
- Downstream: LoopTools (evaluates `amp_reduced.m` PV integrals numerically)
