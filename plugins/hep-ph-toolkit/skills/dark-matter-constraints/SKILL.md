---
name: dark-matter-constraints
description: Meta-skill — given a BSM model and a DM question (relic density, direct detection, indirect detection, or all), routes to the right underlying tool(s) (MadDM, micrOMEGAs, DRAKE), runs them, compares results where appropriate, and returns a merged answer with caveats. Does no physics itself.
---

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

**Branch — loop-only DD (CP-forbidden / anomaly-induced mediator).**
When `direct` is requested AND the model spec's
`dm_phenomenology.candidates[?].mediator_regime ∈ {loop-only-CP-forbidden, loop-only-anomaly-induced}`,
tree-level DD is ≈0 and physically meaningless (e.g. 2HDM+a: the mediator `a` is
CP-odd, so `σ_SI_tree ≈ 0`). For **direct detection only**, route DD through the
loop chain instead of `/maddm generate direct_detection`:

```
/feynarts generate → /formcalc reduce → /looptools eval → /ddcalc run --sigma-json
```

`/looptools eval` numerically evaluates the FormCalc-reduced one-loop amplitude
(charged-Higgs/W box + mediator triangle) and emits a `scattering/v1` JSON with
`source: "looptools"` and the four cross-section fields `sigma_si_proton_cm2`,
`sigma_si_neutron_cm2`, `sigma_sd_proton_cm2`, `sigma_sd_neutron_cm2`
(σ_SD is `null` in v1). Feed that JSON straight into the existing `/ddcalc`
consumer (Step 4 / the σ rows). The pre-dispatch availability check reads
`config.looptools_path` (and the LoopTools MathLink flag); if absent, emit the
upstream `/looptools` blocker and skip DD (relic/indirect still run).

Emit an informational notice `LOOP_DD_PATH` (recoverable, mirrors
`ANALYTIC_BACKEND_PATH`) documenting that DD ran through the loop chain rather
than tree-level MadDM. Keep `/maddm` for relic and indirect. The σ_SI is real
and EW-anchor-validated at the 2HDM+a benchmark (~40% vs an independent EW
box+triangle anchor; single point; box not folded into f_N, ≤1.7× upward if
folded later; σ_SD null in v1); the Tier-3 FormCalc/LoopTools smoke is gated off
by default (`HEPPH_RUN_WOLFRAM_TESTS=1`) but runs green on a tooled box. Tag the
DD row `[loop, validated, single-point]` and stamp
`model_source: "hand_crafted_sarah_model"` when the run is on a fixture.

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

**Step 4b.6 — Isoscalar sanity on σ_SI (model-file bug detector).** For
Higgs-portal / scalar-exchange Majorana DM, σ_SI is nearly isoscalar: **p/n ≈
0.97**. If *either* tool reports σ_SI(p)/σ_SI(n) far from 1 (a ~8× asymmetry) or
opposite-sign proton/neutron amplitudes, that is the fingerprint of an up/down
Yukawa **relative sign error** in the SARAH model export (suppresses σ_SI ~200×),
**not** physics and **not** a genuine tool disagreement. Cross-tool *agreement* on
a large asymmetry does not vindicate it — both tools inherit the same broken
export. Flag it as a model bug, point the user at the SARAH quark-sector Yukawa
signs (regenerate via `/sarah-build --force`), and do not report the suppressed
σ_SI or an exclusion verdict built from it. See `/ddcalc` SE-DD-3.

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

### Step 6 — Cosmology side-check (CLASS)

**Step ordering (D6):** The trust banner is emitted at the end of Step 1
(before Step 2). The actual `/class` dispatch runs as Step 6, after Steps 2-5;
results appear at the end of the merged report.

#### §4.1 Trigger

At Step 1 end, after validating the spec against `runner_spec/v1`:

```python
# scripts/should_invoke_class.py
def should_invoke_class(spec: dict) -> bool:
    cosmology = spec.get("cosmology")
    if cosmology is None:
        return False
    if isinstance(cosmology, str):  # legacy scalar form
        return cosmology != "standard_thermal"
    if isinstance(cosmology, dict):
        return cosmology.get("kind", "standard_thermal") != "standard_thermal"
    return False  # malformed — caught by RUNNER_SPEC_INVALID
```

If `should_invoke_class(spec)` returns `False` → skip Step 6 entirely, no banner.

#### §4.2 Trust banner (printed at Step 1 end, before Step 2)

```
NOTICE: spec.cosmology.kind = '<value>' (non-standard cosmology declared).

Steps 2-5 (MadDM / micrOMEGAs / DRAKE) compute Ωh² and related observables
under the *standard thermal Boltzmann* assumption. Their results below should
not be compared directly to Planck targets without an independent cosmology
run. Step 6 will invoke /class with the user-declared CLASS configuration and
report cosmological observables alongside.

v1 trusts the user's cosmology declaration. The router does NOT verify that
the BSM model's actual decay widths / N_eff contributions match the declared
cosmology. (v2 will add inference.)
```

#### §4.3 Pre-dispatch install + spec-completeness gate

Before invoking `/class`:

```
if config.class_path is unset OR not a valid path:
    emit CLASS_MISSING (recoverable)
    skip Step 6 entirely; record fixit "Run _shared/installs/class"
    continue with merged report (no cosmology side-check section)

if cosmology is dict but required-iff fields missing (per §2 matrix):
    emit COSMOLOGY_SPEC_INCOMPLETE (recoverable) with the missing field name
    skip Step 6 dispatch; merged report shows "Cosmology side-check: blocked"
```

Both gates are prose-side. `check_prereqs.py` is not modified in v1.

#### §4.4 Subcommand dispatch

For each subcommand in `spec.cosmology.invoke` (default `[background]`):

```bash
# If class_template is set:
TEMPLATE_DIR=$REPO_ROOT/plugins/hep-ph-toolkit/skills/class/templates
CONFIG_PATH=$(python scripts/materialize_template.py \
    --template "$TEMPLATE_DIR/${class_template}.yaml" \
    --overrides "$overrides_json" \
    --out "$tmp_dir/class_config.yaml")

# Otherwise:
CONFIG_PATH="$class_config"

/class <subcommand> <class_preset> \
    [--config "$CONFIG_PATH"] \
    [--bsm "$bsm_extension"] \
    --output-dir <unique per-subcommand dir>
```

`scripts/materialize_template.py` reads the template as raw text, substitutes
`{{key}}` placeholders with values from the overrides dict, and writes to a
tempdir. See `materialize_template.py` for error semantics.

Failure handling per invocation:
- `/class` exits non-zero → parse the structured blocker JSON emitted to stderr
  and propagate the upstream code as the blocker detail (e.g.
  `CLASS_INVOCATION_FAILED: upstream=CLASS_BSM_UNKNOWN_KIND`). Continue with
  remaining subcommands.
- `/class` exits 0 → validate `cosmology.json` in the run dir against
  `cosmology/v1`; harvest `summary`.

#### §4.5 Field harvesting

```bash
python .../scripts/extract_field.py \
    --json <run_dir>/cosmology.json \
    --key summary \
    --schema-version cosmology/v1
```

Returns the `summary` object as `value`. Agent walks the dict in prose
(matches Step 4b.1 precedent). Missing or null `summary.<key>` renders `—`
with a per-row note "(not computed by subcommand `<x>`)"; no blocker code.

#### §4.6 Report integration

New section appended to merged report after the existing DM table:

```markdown
### Cosmology side-check (CLASS)

Declaration: spec.cosmology.kind = '<value>'
CLASS preset: <class_preset>
Subcommands run: <invoke>

| Observable        | CLASS value | Planck 2018 target | |Δ| / σ | Status |
|-------------------|-------------|---------------------|---------|--------|
| H₀ [km/s/Mpc]     | ...         | 67.32 ± 0.54        | ...     | OK / FLAG / — |
| Ω_m h²            | ...         | 0.1430 ± 0.0011     | ...     | OK / FLAG / — |
| N_eff             | ...         | 3.046               | ...     | OK / FLAG / — |
| τ_reio            | ...         | 0.0543 ± 0.0073     | ...     | OK / FLAG / — |
| σ_8               | ...         | 0.811 ± 0.006       | ...     | OK / FLAG / — |

Targets loaded from `data/planck_targets.json` (citation: arXiv:1807.06209).

> Trust banner: see Step 1 notice (above). v1 does not cross-check the
> declaration against the BSM spectrum; verify the YAML reflects the model's
> actual cosmology.
```

`Status` rules:
- `—` if `summary.<key>` is null (subcommand did not compute it).
- `FLAG` if `|CLASS − Planck_central| / Planck_sigma > 3`. Where σ is unset
  (e.g. `N_eff` SM prediction), use 1% relative tolerance.
- `OK` otherwise.

`FLAG` is informational; never blocks the run.

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

> **micrOMEGAs is a direct-detection cross-check only for singlet-doublet — NOT a relic authority.** The native micrOMEGAs route builds from SARAH's `MakeCHep[]` CalcHEP export, which has no `IMZNMIX` slot, so Majorana phases are silently dropped. The resulting relic density is invalid for singlet-doublet (Ωh² ≈ 0.0742 vs the validated 0.2916) — do not report micrOMEGAs Ωh² for this model or compute Planck pulls from it. Use micrOMEGAs only as a σ_SI/σ_SD direct-detection cross-check; **MadDM is the relic authority.**

**Relic caveat for negative-Majorana-eigenvalue models.** Even off the proxy
path, a SARAH-CalcHEP export reads real `ZNMIX` only (no `IMZNMIX`), so it drops
the Majorana phase and returns an **invalid relic** for models with a negative
fermion eigenvalue. Keep **MadDM as the relic authority**; use the micrOMEGAs
cross-check for σ_SI/σ_SD only. See `/micromegas` SKILL.md #5.

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

### Primary DM pipeline codes (Steps 1-5)

| Code | Mode | Trigger | User instruction |
|------|------|---------|-----------------|
| `MADDM_MISSING` | fatal | MadDM not found in MG5 or `config.maddm_path` absent (default pipeline only — not raised on the analytic-only branch) | Run `_shared/installs/maddm` |
| `ANALYTIC_BACKEND_PATH` | recoverable (informational) | Step 2 analytic-only branch fired: `multi_component: true` AND `backends.spectrum == "analytic"`. MadDM skipped; relic numbers consumed directly from `<spheno_run>/diagnostics.json` + `summary.json` (`mixing.MHHMIX`). Steps 3-5 also skipped. | None — informational. Verify analytic-module assumptions in caveats. |
| `LOOP_DD_PATH` | recoverable (informational) | Step 2 loop-only DD sub-branch fired: `direct` requested AND `dm_phenomenology.candidates[?].mediator_regime ∈ {loop-only-CP-forbidden, loop-only-anomaly-induced}`. DD routed through `/feynarts → /formcalc → /looptools eval → /ddcalc` instead of tree-level MadDM (tree SI ≈ 0). | None — informational. σ_SI is real + EW-anchor-validated (~40% vs the independent EW box+triangle anchor) at the 2HDM+a benchmark, 2026-06-28 (single point; box not folded into f_N); the Tier-3 smoke is gated off by default but green on a tooled box; relic/indirect still run via MadDM. |
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

### Step 6 cosmology side-check codes (D7 / §5)

| Code | Mode | Trigger | Producer | User instruction |
|------|------|---------|----------|-----------------|
| `RUNNER_SPEC_INVALID` | recoverable | `--spec` YAML fails `runner_spec/v1` schema validation | router prose, Step 1 end | Fix the YAML per the schema-validator error message. |
| `CLASS_MISSING` | recoverable | Step 6 entered AND `config.class_path` unset / invalid | router prose, Step 6 entry | Run `_shared/installs/class`; cosmology side-check unavailable. |
| `COSMOLOGY_SPEC_INCOMPLETE` | recoverable | `kind == non_standard` AND a required-iff field missing | router prose, Step 6 entry | Add the named missing field per the runner-spec schema. |
| `CLASS_INVOCATION_FAILED` | recoverable | `/class` exited non-zero (or exited 0 but `cosmology.json` absent) | router prose, Step 6 dispatch | Inspect `<run_dir>/stderr.log`; `upstream=<code>` in the detail field identifies the `/class` blocker. |

**Banner (NOT a blocker code; printed in report):**
"Non-standard cosmology declared — Steps 2-5 use standard-thermal Boltzmann…" (per D6 + §4.2).

**Deferred to v2:** `COSMOLOGY_INFERENCE`, `COSMOLOGY_INCONSISTENT`, `SLHA_PARSER_MISSING`.
No fatal codes — the cosmology side-check never blocks a primary run.

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
| `config.class_path` | `_shared/installs/class` (Step 6; only read when `cosmology.kind != 'standard_thermal'`) |
| `config.looptools_path` | `_shared/installs/looptools` (Step 2 loop-only DD sub-branch; only read when `dm_phenomenology.candidates[?].mediator_regime ∈ {loop-only-CP-forbidden, loop-only-anomaly-induced}`) |

---

## Cross-skill dependencies

| Skill | Role | Required? |
|-------|------|-----------|
| `/maddm` | Primary DM observable driver | Always (fatal if absent) |
| `/micromegas` | Cross-check for coannihilation / near-resonance spectra | Conditional (Step 4) |
| `/drake` | Narrow-resonance relic density | Conditional (Step 5) |
| `/class` | Cosmology side-check (H0, Omega_m_h2, N_eff, sigma_8, …) | Conditional (Step 6; only when `cosmology.kind != 'standard_thermal'`) |
| `_shared/installs/maddm` | MadDM install / detect | Prerequisite check |
| `_shared/installs/micromegas` | micrOMEGAs install / detect | Prerequisite check (Step 4) |
| `_shared/installs/drake` | DRAKE availability check | Step 5 availability check (optional; `config.drake_path` checked first) |
| `_shared/installs/class` | CLASS install / detect | Step 6 availability check (optional; `config.class_path` checked first) |
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

**v1 cosmology inference gap (scenario c — D5):**
v1 does not infer cosmology from the BSM spectrum. If the runner spec declares
`cosmology: standard_thermal` but the model is actually non-standard (long-lived
BSM states, ΔN_eff, freeze-in), the router trusts the declaration and skips the
cosmology side-check. v2 will add an SLHA-based inference pass that raises
`COSMOLOGY_INCONSISTENT`.

**Producer-internal cosmology flag (D1):**
The `cosmology` field inside `relic.json` (the `relic/v1` schema, produced by
MadDM / micrOMEGAs / DRAKE) is a *producer-internal* flag meaning "this relic
density was computed under the standard-thermal Boltzmann assumption." It is not
a record of the runner-spec `cosmology` declaration. The two layers carry
different shapes because they describe different things: the producer field is an
audit stamp about the solver assumption; the runner-spec `cosmology` block is a
user instruction to the router. Do not confuse them.

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
