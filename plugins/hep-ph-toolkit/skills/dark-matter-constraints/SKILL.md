---
name: dark-matter-constraints
description: Meta-skill — given a BSM model and a DM question (relic density, direct detection, indirect detection, or all), routes to the right underlying tool(s) (MadDM, micrOMEGAs, DRAKE), runs them, compares results where appropriate, and returns a merged answer with caveats. Does no physics itself.
---

> Forward-compat: if a future ModelSpec sets cosmology to a value other than 'standard_thermal', also invoke /class for cosmological side-checks. Not currently exercised.

# /dark-matter-constraints

Pure router / meta-skill. Routes to MadDM, micrOMEGAs, and/or DRAKE; compares results; returns a merged answer with caveats. Does no physics itself.

---

## Invocation

```
/dark-matter-constraints <model> [observables] [options]
```

| Argument | Meaning |
|----------|---------|
| `<model>` | Model name in `config.models` (`ufo_path` required) |
| `[observables]` | `relic`, `direct`, `indirect`, or `all` (default: `all`) |
| `--spec <yaml>` | Path to `spec.yaml` with `dm_candidate` |
| `--skip-crosscheck` | Suppress micrOMEGAs cross-check |
| `--skip-drake` | Suppress DRAKE (emits resonance-regime warning) |
| `--drake` | Force DRAKE regardless of resonance geometry |

---

## Decision tree

This is the canonical routing logic. Follow it exactly and in order.

### Step 1 — Prerequisite check

```bash
python "$REPO_ROOT/plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/check_prereqs.py" \
    --config <config_path> --model <model>
```

Parse JSON. If `status == "blocked"`, surface each blocker and stop. `SLHA_MISSING_HINT` is informational.

### Step 2 — Default pipeline: MadDM (always) — UNLESS analytic-only branch fires

**Branch — analytic-only (multi-component, analytic spectrum backend).**
When the model spec satisfies BOTH:

1. `multi_component: true` (per `_shared/constraints.yaml` `models.<m>.multi_component`)
2. `backends.spectrum == "analytic"` (per the model's ModelSpec YAML)

then `/maddm` is **skipped entirely** and the router consumes the
`/spheno-build` analytic backend's outputs directly:

| Field | Source artifact | Locator |
|-------|-----------------|---------|
| Per-component Ωh² (e.g. `Omega_V_h2`, `Omega_Psi_h2`) | `<spheno_run>/diagnostics.json` | direct key lookup |
| Total Ωh² | sum of per-component Ωh² in `diagnostics.json` | router computes |
| Higgs mixing matrix (MHHMIX) | `<spheno_run>/summary.json` `mixing.MHHMIX` | direct key lookup |
| Per-channel diagnostics (`blind_spot_*`, `sigmav_approx`, etc.) | `<spheno_run>/diagnostics.json` | direct key lookup |

Rationale: dark SU(N) sectors with non-SM color cannot be represented in
MadGraph/MadDM (no UFO/CalcHEP encoding for the dark color group), so MadDM
cannot generate the coannihilation set. The analytic spectrum backend's
diagnostics are the authoritative source for relic density in this branch.

Emit an informational notice `ANALYTIC_BACKEND_PATH` (recoverable, not fatal)
documenting that `/maddm` was skipped and the analytic numbers are reported
directly. Skip Steps 3-5 (cross-check via micrOMEGAs and DRAKE both require
MadDM-compatible cross-sections, which the analytic-only branch does not
produce). Jump straight to "Merged output format" with the analytic numbers
in the MadDM column relabeled as `[analytic]`.

**Mandatory regression-anchor disclosure (analytic-only branch).** When the
analytic-only branch fires, the merged report MUST embed the verbatim banner
for the active exception entry from `plugins/hep-ph-toolkit/skills/_shared/analytic_exceptions.yaml`
**before** the results table — not buried in a caveats footnote. Downstream
readers must see, at a glance, that the analytic Ωh² values are
regression-anchors for the analytic pipeline — **not** a physics prediction
or a paper-fidelity result. Quoting the analytic numbers without the
disclosure is a contract violation.

For dark-su3 (exception `dsu3-002`), the required verbatim banner is:

> **REGRESSION-ANCHOR ONLY — NOT A PHYSICS TARGET (dsu3-002).** Dark-SU(3)
> relic density runs through the analytic backend (`analytic_models.dark_su3`)
> and currently uses `<sigma v>` approximations (`sigmav_approx=True`). The
> emitted Ωh² values are roughly **25000× the Planck target** and must be read
> as regression anchors for the analytic pipeline, **not** as a physics
> prediction or a paper-fidelity result. Paper fidelity (Ω_tot h² ≈ 0.12) is
> out of reach this iteration and requires the upgrade roadmap in
> `analytic_models.dark_su3` (full Boltzmann integration + multi-component
> weighting in `/dark-matter-constraints`). Any downstream report that quotes
> these numbers MUST embed this banner verbatim — do not silently strip it.

If `multi_component: true` but `backends.spectrum != "analytic"`: continue to
the default MadDM pipeline below (multi-component DM with a UFO-compatible
spectrum can still go through MadDM per-component).

**Default pipeline.**
Invoke `/maddm` for the requested observables. Rationale: MadDM's MG5/UFO path
handles exotic Lorentz and color structures, loop-induced annihilation channels,
and same-sign coannihilation initial states correctly. micrOMEGAs' CalcHEP path
can silently mishandle non-standard Lorentz/color structures without raising an
error.

Subcommand mapping:

| Observable requested | `/maddm` invocation |
|----------------------|---------------------|
| `relic` | `generate relic_density` |
| `direct` | `generate direct_detection` |
| `indirect` | `generate indirect_detection` |
| `all` | all three in sequence |

Collect the MadDM output JSON (see `/maddm` SKILL.md §Reading MadDM output).

### Step 3 — Spectrum analysis: detect cross-check triggers

After MadDM completes (or while reading the SLHA spectrum / param_card), parse
the particle mass spectrum to detect:

**Trigger A — Coannihilation:** any BSM particle with mass within 10% of m_χ
(i.e. |m_i − m_χ| / m_χ ≤ 0.10).

**Trigger B — Near-threshold resonance (relic):** any s-channel mediator with
mass within 10% of 2·m_χ, measured as:

```
|m_med − 2·m_χ| / (2·m_χ) ≤ 0.10
```

This 10% window is chosen to catch the broad "resonance shoulder" region where
micrOMEGAs' coannihilation bookkeeping provides an independent cross-check on
the velocity-expansion-based relic density. The denominator is `2·m_χ`
throughout — this is the half-width of the resonance in units of the threshold
momentum, not in units of the mediator mass.

If either trigger fires, proceed to Step 4. Otherwise skip to Step 5.

### Step 4 — Cross-check via micrOMEGAs (conditional)

If `--skip-crosscheck`: emit `CROSSCHECK_SKIPPED` (recoverable) and jump to Step 5.
If micrOMEGAs absent: emit `MICROMEGAS_MISSING` (recoverable) and continue.
Subcommands: `relic`→`micromegas relic`, `direct`→`micromegas scatter`,
`indirect`→`micromegas annihilate` + `micromegas indirect`.

| Observable | MadDM field | micrOMEGAs field | Disagreement threshold | Action |
|------------|-------------|------------------|------------------------|--------|
| Ωh² | `Omegah2` | `omega_h2` | > 10% relative | **FLAG to user** |
| σ_SI(p) | `sigma_si_proton` | `sigma_si_proton_cm2` | > 10% relative | **FLAG to user** |
| σ_SD(p) | `sigma_sd_proton` | `sigma_sd_proton_cm2` | > 10% relative | **FLAG to user** |
| ⟨σv⟩(v→0) | `sigmav_total` | `sigma_v_zero` | > 10% relative | **FLAG to user** |

### Step 4b — Disagreement comparison (calls canonical `/gamlike` parser)

For each row in the cross-check table below, acquire both values then compute
the relative difference in prose:

**Step 4b.1 — MadDM side.** Call the canonical `/gamlike` parser and read
fields by nested dict access (no agent-parses-prose):

```bash
python plugins/hep-ph-toolkit/skills/gamlike/scripts/parse_maddm_results.py \
    <maddm_run>/MadDM_results.txt \
    --out <maddm_run>/MadDM_results.txt.gamlike.json
```

Then in-process:

```python
import json
data = json.loads(open("<maddm_run>/MadDM_results.txt.gamlike.json").read())
omega_h2 = data["relic"]["Omegah2"]
```

**Step 4b.2 — micrOMEGAs side.** Run `scripts/extract_field.py` with the
appropriate schema (`relic.json`+`relic/v1` for Ωh²,
`annihilation.json`+`annihilation/v1` for ⟨σv⟩(v→0),
`summary.json`+`scattering/v1` for σ_SI/σ_SD):

```bash
python "$REPO_ROOT/plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/extract_field.py" \
    --json "<mo_run>/<file>" --key "<canonical_name>" --schema-version "<id>"
```

If `extract_field` exits 1 with `KEY_ABSENT`, treat as null and render `—`.

**Step 4b.3 — Compute.** `rel_diff = abs(a - b) / max(abs(a), abs(b))` if
both non-null. Flag at `> 0.10` by default. Expert may override the threshold.

**Step 4b.4 — Skip rules.** Skip the row when the model class makes the
comparison meaningless: multi-component DM (sum vs per-component pairing is
undefined), asymmetric DM (⟨σv⟩ ≈ 0 by design — flag would be cosmetic),
Majorana DM with σ_SD-only schemas (null vs 0 distinction is a producer rule).
Render `—` and explain the skip in one sentence.

**Step 4b.5 — Do NOT** silently average, pick a winner, or paper over a flag.
If you cannot adjudicate, surface both values and the disagreement to the user.

The MadDM side calls `parse_maddm_results.py` for deterministic JSON extraction;
the micrOMEGAs side calls `extract_field`. The judgment (skip rules, threshold,
render-vs-flag) remains the LLM's own.

### Step 5 — DRAKE invocation (narrow-resonance)

Invoke `/drake` when: (1) relic requested, (2) `|m_med − 2·m_χ| / (2·m_χ) ≤ 0.05`,
(3) `--skip-drake` not set. If `--skip-drake` fires: emit `DRAKE_SKIPPED` (recoverable).

```bash
python "$REPO_ROOT/plugins/hep-ph-toolkit/skills/dark-matter-constraints/scripts/detect_drake.py" \
    --config <config_path>
```

- **Branch 1 — config.drake_path absent:** emit `DRAKE_MISSING` (recoverable) with
  resonance warning (MadDM Ωh² may be inaccurate near 2·m_χ; install via `_shared/installs/drake`).
- **Branch 2 — config.drake_path set:** dispatch on `status`: `"configured"` → invoke `/drake`
  and extract `omega_h2` (lowercase):
  `scripts/extract_field.py --json <drake_run>/relic.json --key omega_h2 --schema-version relic/v1`.
  Flag `DRAKE_MADDM_DISAGREEMENT` if Ωh² differs > 10%. `"missing"` / `"found"` → `DRAKE_MISSING`.
  `"activation_required"` → `DRAKE_ACTIVATION_REQUIRED` (`wolframscript --activate`).
  `"unparseable"` → `DRAKE_UNAVAILABLE`. Do not abort on any recoverable outcome.

---

## Tool failure modes (required reading)

This skill deliberately does not hide these from the user. Each tool has distinct
failure modes that affect when you should trust its results.

### MadDM (primary)

- Correctly handles exotic Lorentz/color structures via the MG5/UFO path.
- Uses `generate relic_density` to assemble the full coannihilation set
  automatically. A bare process generation (`generate chi chi~ > all all`) drops
  coannihilation channels — the high-level entry is mandatory.
- Does NOT solve the coupled Boltzmann equation. The velocity expansion
  `⟨σv⟩ = a + b·v²` is used; fails near narrow s-channel resonances and when
  Sommerfeld enhancement is significant.
- Loop-induced DD cross-sections require `loop = ON` in `maddm_card.dat` (off
  by default); results at tree level may miss blind-spot cancellations.

### micrOMEGAs (cross-check only)

> **PROXY-RUN DISCLOSURE.** micrOMEGAs run on proxy model (SingletDM
> stand-in for singlet-doublet because CalcHEP `.mdl` files were not
> generated by SARAH). Results do not apply to the target model. Do not
> report proxy values as native predictions; do not compute relic pulls
> against Planck using proxy numbers; do not apply LZ-SD or PICO cuts to
> proxy σ_SD; tag every affected table row with `[proxy]`.

- CalcHEP path can silently mishandle non-standard Lorentz/color structures.
  Results for exotic mediators (higher-spin, colored DM, etc.) should be
  treated with skepticism without independent validation.
- Pre-wired experimental likelihood library and mature coannihilation
  bookkeeping are the primary reasons to use it as a cross-check.
- Same velocity-expansion limitation as MadDM for resonance regimes.

### DRAKE (narrow-resonance only)

- Solves the coupled Boltzmann equation numerically. Does not use the velocity
  expansion — the correct approach near resonances and for Sommerfeld enhancement.
- Requires user-provided Wolfram cross-section functions `sv[s_]` and `gam[x_]`.
  Does not import cross sections from MadDM or micrOMEGAs output automatically.
- Not a dependency of MadDM or micrOMEGAs; completely independent computation path.
- VRES and SE pre-implemented models (shipped with DRAKE) cover the most common
  resonance/Sommerfeld cases. Verify that the shipped model matches your BSM
  spectrum before using.

---

## Merged output format

After all invoked skills complete, emit a single merged report:

```
## Dark matter constraints: <model>

### Tools invoked
- MadDM [maddm_run_dir]
- micrOMEGAs [micromegas_run_dir]  (cross-check: coannihilation/near-resonance trigger)
- DRAKE [drake_run_dir]            (narrow-resonance regime)

### Results
| Observable      | MadDM  | micrOMEGAs | DRAKE  | Status    |
|-----------------|--------|------------|--------|-----------|
| Ωh²             | ...    | ...        | ...    | OK / FLAG |
| σ_SI(p) [cm²]  | ...    | ...        | —      | OK / FLAG |
| σ_SD(p) [cm²]  | ...    | ...        | —      | OK / FLAG |
| ⟨σv⟩ [cm³/s]   | ...    | ...        | —      | OK        |

Planck 2018 target: Ωh² = 0.1200 ± 0.0012
(Planck Collaboration 2018, arXiv:1807.06209, Table 2, TT,TE,EE+lowE+lensing)

### Flags
CROSSCHECK_DISAGREEMENT: Ωh² — MadDM: 0.135, micrOMEGAs: 0.118 (rel. diff 14.4%)
User adjudication required before proceeding.

### Caveats
[List any DRAKE_MISSING, DRAKE_UNAVAILABLE, MICROMEGAS_MISSING, or --skip-* warnings here]
```

Omit columns for tools that were not invoked. Replace `—` with the value if
the tool was run for that observable. If a FLAG row is present, the word
"ADJUDICATION REQUIRED" must appear prominently before the caveats section.

---

## Blocker / notice codes

| Code | Mode | Trigger | User instruction |
|------|------|---------|-----------------|
| `MADDM_MISSING` | fatal | MadDM not found in MG5 or `config.maddm_path` absent (default pipeline only — not raised on the analytic-only branch) | Run `_shared/installs/maddm` |
| `ANALYTIC_BACKEND_PATH` | recoverable (informational) | Step 2 analytic-only branch fired: `multi_component: true` AND `backends.spectrum == "analytic"`. MadDM skipped; relic numbers consumed directly from `<spheno_run>/diagnostics.json` + `summary.json` (`mixing.MHHMIX`). Steps 3-5 also skipped. | None — informational. Verify analytic-module assumptions in caveats. |
| `UFO_MISSING` | fatal | `config.models[<model>].ufo_path` absent | Run `/sarah-build` |
| `SLHA_MISSING` | fatal | `/maddm` runtime fails with a spectrum-related error and `latest_slha` is absent | Run `/spheno-build` |
| `MICROMEGAS_MISSING` | recoverable | micrOMEGAs not installed; cross-check triggered but skipped | Run `_shared/installs/micromegas`; cross-check results unavailable |
| `CROSSCHECK_SKIPPED` | recoverable | `--skip-crosscheck` passed by user; Step 4 bypassed | Cross-check results unavailable; rerun without flag to enable |
| `DRAKE_MISSING` | recoverable | `config.drake_path` absent (Branch 1), or `bash _shared/installs/drake/detect.sh` returns `"missing"` / `"found"` (Branch 2) | Run `_shared/installs/drake`; MadDM Ωh² may be inaccurate |
| `DRAKE_UNAVAILABLE` | recoverable | `config.drake_path` set (Branch 2) but `bash _shared/installs/drake/detect.sh` invocation failed or returned unparseable output | Run `_shared/installs/drake`; resonance-regime accuracy warning applies |
| `DRAKE_ACTIVATION_REQUIRED` | recoverable | Wolfram Engine not activated | Run `wolframscript --activate`; DRAKE skipped |
| `DRAKE_SKIPPED` | recoverable | `--skip-drake` passed by user; narrow-resonance regime detected but DRAKE bypassed | Resonance-regime accuracy warning applies; rerun without flag to enable DRAKE |
| `CROSSCHECK_DISAGREEMENT` | recoverable | MadDM vs micrOMEGAs > 10% on any observable | User must adjudicate before proceeding |
| `DRAKE_MADDM_DISAGREEMENT` | recoverable | DRAKE vs MadDM Ωh² > 10% | User must adjudicate |

---

## Config keys read (not written)

> **MIRROR — see `contracts/router_contract.json` `config_keys` for canonical contract.**

This skill writes no config keys — it is a router. It reads:

| Key | Source skill |
|-----|-------------|
| `config.models[<model>].ufo_path` | `/sarah-build` |
| `config.models[<model>].latest_slha` | `/spheno-build` (required only when `/maddm` itself requires it) |
| `config.models[<model>].spec_yaml` | User-authored |
| `config.micromegas_path` | `_shared/installs/micromegas` |
| `config.maddm_path` | `_shared/installs/maddm` |
| `config.drake_path` | `_shared/installs/drake` |

---

## Cross-skill dependencies

| Skill | Role | Required? |
|-------|------|-----------|
| `/maddm` | Primary DM observable driver | Always (fatal if absent) |
| `/micromegas` | Cross-check for coannihilation / near-resonance spectra | Conditional (Step 4) |
| `/drake` | Narrow-resonance relic density | Conditional (Step 5) |
| `_shared/installs/maddm` | MadDM install / detect | Prerequisite check |
| `_shared/installs/micromegas` | micrOMEGAs install / detect | Prerequisite check (Step 4) |
| `_shared/installs/drake` | DRAKE availability check | Step 5 availability check (optional; `config.drake_path` checked first) |
| `/sarah-build` | UFO model generation | Prerequisite (provides `ufo_path`) |
| `/spheno-build` | SLHA spectrum generation | Conditional prerequisite (provides `latest_slha` when needed by `/maddm`) |

---

## What this skill does NOT do

- It does not reimplement freeze-out, relic density integrals, cross-section
  formulae, or experimental bound comparisons in Python.
- It does not interpolate between tool results or silently discard disagreements.
- It does not invoke micrOMEGAs or DRAKE routinely — only when the spectrum
  analysis in Step 3/Step 5 triggers them.
- It does not evaluate whether kinetic decoupling is early, whether the velocity
  expansion converges, or any other physics criterion. Resonance geometry is
  used as a proxy for regime detection; anything more requires the user to set
  `--drake` explicitly.
- It does not generate plots or exclusion contours — hand off to `/hep-plotting`
  after collecting the merged JSON output.
- The `compare_dm` comparison logic (Step 4b) is deliberately NOT a deterministic
  helper. Model-class skip rules (multi-component DM, asymmetric DM, Majorana null
  σ_SD), threshold judgment, and rel-diff rendering are LLM-owned per the routing
  lens. Only `extract_field` is a deterministic primitive called from within Step 4b.

---

## Sharp edges (playtest-surfaced, 2026-04-25)

Findings from the WS-K e2e playtest and T1.1 tier-1 fix. Cite FU-ids when
filing follow-ups.

### 1. `extract_field.py` strict schema rejected legitimate producer extensions

- **FU-id:** FU-wsk-01
- **Status:** Fixed in tier-1 (T1.1, branch `tier1/t11-extract-field-r1-20260426`,
  merged at commit `f413a67`).
- **Symptom:** `extract_field.py --schema-version relic/v1` exits 1 with
  `SCHEMA_MISMATCH` on any JSON that carries extra top-level keys such as
  `proxy_run` or `_meta`. The call succeeds on canned fixtures but fails on
  real producer output (e.g. micrOMEGAs JSONs emitted by `/micromegas`).
- **Cause:** The relic, scattering, and annihilation schemas all carried
  `"additionalProperties": false`. Any producer that appends bookkeeping keys
  (proxy flags, metadata, version stamps) causes schema validation to reject the
  file before the requested field is extracted.
- **Fix (T1.1):** `additionalProperties` relaxed to `true` in all three schemas.
  A `_resolve_type` helper was added to walk `oneOf`/`anyOf` unions for
  polymorphic field resolution. The extracted field value is unchanged; only the
  validation gate is widened.
- **Rule for schema authors:** Do **not** re-introduce `"additionalProperties": false`
  on the top-level router-contract schemas. Producer extensions are expected and
  must not break field extraction. If you need strict validation for a specific
  internal key set, apply `additionalProperties: false` only on a nested
  sub-object, not at the root.

### 2. Proxy-model handling — `proxy_run: true` flag in upstream JSONs

- **FU-id:** FU-wsg-01 (originated in WS-G; propagated to WS-K as
  `NOTE_FOR_WS-K` convention)
- **Status:** Behavioral contract; no code change required. Router report
  writers must honor it.
- **Context:** When an upstream WS runs micrOMEGAs on a proxy model (e.g.
  `/micromegas` falls back to a SingletDM proxy because the target model —
  singletDoublet — has no CalcHEP-compatible files), the output JSONs carry a
  top-level `proxy_run: true` flag and a `_meta.proxy_model` description.
- **Router obligations when `proxy_run: true` is present:**
  1. Do **not** report proxy relic density or scattering cross-sections as
     native-model predictions.
  2. Do **not** compute relic pulls (|Ωh² − 0.120| / σ) against the Planck
     target using proxy numbers.
  3. Do **not** apply LZ-SD or PICO cuts to proxy σ_SD values.
  4. Tag **every** affected table row with `[proxy]`.
  5. Emit the verbatim caveat block from the WS-G `NOTE_FOR_WS-K` convention:
     `"micrOMEGAs run on proxy model (<description>); results do not apply to
     the target model."` This must appear before the caveats section.
- **Failure mode if ignored:** The router silently treats a proxy prediction as
  a real-model constraint. This produces incorrect exclusion verdicts and
  misleads downstream `/hep-plotting` contour generation.

### 3. NC stream size: expected O(few k tokens) per point, not 200k

- **FU-id:** FU-wsk-misc
- **Status:** Scope-language note; no code change.
- **Background:** Scope §3.3 WS-K specified NC streams ">200k tokens." The
  WS-K playtest produced ~16 KB / 3-4k tokens total across five stream files for
  a two-point run. This is not a router defect: the streams are summary-level
  (decision + provenance per step), not trace-level (raw binary stdout). With
  relic density FAILED upstream (MadDM Ωh²=−1 sentinel), there are no Boltzmann
  solver traces to stream.
- **Correct expectation:** O(few k tokens per point) for a summary-mode router
  run. To reach O(100k tokens), the streams would need to include raw upstream
  artifacts (full `MadDM_results.txt`, `maddm.out`, complete DRAKE stdout, full
  micrOMEGAs `stdout.log`). Future scope language should distinguish
  "summary-mode NC stream" from "trace-mode NC stream." The 200k-token target
  was almost certainly written for a multi-cycle MadDM-converged-Boltzmann
  scenario.
