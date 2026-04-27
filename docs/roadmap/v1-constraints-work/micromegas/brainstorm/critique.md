# `/micromegas` — critique (SKEPTIC)

Author: critic agent
Date: 2026-04-19
Target: proposer brief at `docs/roadmap/v1-constraints-work/micromegas/brainstorm/proposal.md`

Proposer was asked for sharp positions. Below every place the proposal is wrong, fragile, or under-defended, followed by what the synthesizer should do. Quotes lifted verbatim from the proposal.

---

## 1. CalcHEP bundling is half-true and quietly network-dependent

> "micrOMEGAs ships its own vendored CalcHEP 3.8.x under `micromegas_<ver>/CalcHEP_src/` — the tarball `make` target builds it automatically."

This is factually misleading for 6.x. Since 6.0 the micrOMEGAs tarball bundles the CalcHEP *numeric backend sources* but the *model-importer* path ships as `CalcHEP_src` only after the first `make` sweeps in ancillary files; several tarballs since 6.0 additionally require `make` inside `Packages/` to fetch and build the SLHAplus / MicroOmegas-nmssmtools auxiliary modules. On a no-network host `make` succeeds *most* of the time in 6.1.x, but the proposer states confidently that CalcHEP is fully bundled — this has not been verified for 6.1.15 on a network-isolated macOS box, which is exactly the environment `HEPPH_RUN_NETWORK_TESTS=0` fixtures claim to cover. Synthesizer: require the installer to run `make` under `HEPPH_NO_NETWORK=1` in a sandboxed test and promote any download attempts to a fatal `MICROMEGAS_BUILD_NEEDS_NETWORK` blocker. Do **not** claim "bundled" without that test.

Separately: the proposal says "Do not gate on the user having an external CalcHEP install" but then later admits a system CalcHEP 3.9 could conflict. The combined position is unstable — either `use-path` accepts a split or it does not. Synthesizer should pick: accept split by allowing `--calchep-path <dir>` on `use-path`, because forcing a 1 GB second copy of CalcHEP is user-hostile when a working 3.9 already exists on the researcher's machine.

## 2. Version pin 6.1.15 — indefensible on the evidence given

> "Pinned version: `6.1.15` (latest stable 2025 release; supports arbitrary UFO input via the CalcHEP/LanHEP bridge it ships with)."

The proposer's own §5 Q7 admits "6.1.x has better UFO2 support but is younger" — which contradicts the headline claim of stability. micrOMEGAs 6.0.x is the longer-baked branch; 6.1.x is still mid-minor-bump territory. Worse, the proposal never says which UFO version `/sarah-build` emits today. SARAH 4.15 emits UFO 1.1 by default; UFO 2.0 is opt-in. If we are downstream of SARAH 4.15 UFO 1.x, 6.1.15's "better UFO2 support" is irrelevant and we should pin 6.0.5. Synthesizer: block until the proposer states explicitly what UFO version `/sarah-build` currently produces (check `plugins/hep-ph-toolkit/skills/sarah-build/` Jinja templates). The decision depends entirely on that fact.

## 3. DM candidate auto-detection is a trap for the target paper

> "Auto: parse SLHA `Block MASS`, pick the lightest particle among those marked stable in the UFO ... no decay widths in `DECAY` blocks, non-SM."

This fails for three realistic cases relevant to the stated target (arXiv:2506.19062, 2HDM+a):

1. **2HDM+a with heavy pseudoscalar `a`.** The `a` is lighter than the DM fermion in much of the blind-spot parameter space but is Z2-even and not a DM candidate. The heuristic of "lightest non-SM with no DECAY block" misfires because SPheno writes a DECAY block for every mass eigenstate, so "no DECAY" is not a stability signal. The proposer confused "no DECAY block" with "width=0 in DECAY block". Fix: parse width, not presence.
2. **Neutralino + sneutrino co-existence (general MSSM extensions).** The proposer's "lightest stable non-SM" picks one; nothing decides *between* two degenerate candidates. The recoverable-blocker path `DM_CANDIDATE_AMBIGUOUS` fires here, but then a scan halts every other row — not recoverable in practice.
3. **Inelastic DM / DM+mediator models** where the nominal DM is not the absolute lightest Z2-odd state (excited partner with slightly higher mass is the cosmologically relevant particle at freeze-out). The heuristic picks the wrong particle silently.

And Z2 parity itself: SARAH-emitted UFO records Z2 charge in `particles.py` under a non-standard attribute (`SARAH` exports it as `TeX` metadata, not a clean `Z2Odd=True` flag). Proposer's §5 Q3 concedes this but shrugs. Synthesizer: make explicit `dm_candidate` in `spec.yaml` **mandatory**, downgrade "auto" to a hint printed in the report, and delete the heuristic. The user's memory explicitly says "augment not replace — block on missing tool-drivers rather than fall back to analytic"; silent heuristic guessing of the DM candidate is the same anti-pattern.

## 4. CLI > spec.yaml > auto ordering is backwards

> "1. Explicit: `--dm-pdg <id>` CLI flag wins. 2. Spec annotation: `spec.yaml` may declare `dm_candidate: <field_name>` ..."

Reverse it. Spec.yaml is the reproducible source of truth — it is the file that `/sarah-build` and `/spheno-build` already consume. A transient CLI flag that overrides the spec for one run produces `summary.json` output that cannot be re-derived from the committed inputs. Scan outputs will carry a different DM candidate than the spec claims, and `/lagrangian-builder` reports will disagree with `summary.json`. Synthesizer: spec.yaml wins; CLI flag is only honoured when spec does not declare a candidate, and when used, it must be written back into a run-scoped override file. The existing SPheno scan pattern (params applied, then echoed to the run dir) is the template.

## 5. `scattering.json` schema does NOT match `/ddcalc`

Cross-reference with `docs/roadmap/v1-constraints-work/ddcalc/brainstorm/proposal.md` §2 — `/ddcalc` expects a top-level flat object with keys:

```
m_DM_GeV, sigma_SI_p_cm2, sigma_SI_n_cm2, sigma_SD_p_cm2, sigma_SD_n_cm2,
source, source_run, halo
```

The proposer's `summary.json` nests under `scatter.sigma_si_proton_cm2` with different key names (`sigma_si_proton_cm2` vs ddcalc's `sigma_SI_p_cm2`), no `source` field, and no `halo`. That means `/ddcalc` cannot consume `summary.json` directly — it needs a translator, which the proposal denies: "`/ddcalc` reads `summary.json` directly". Pick one: either `/micromegas` writes a `scattering.json` sidecar that matches ddcalc's schema exactly, or both proposals converge. Synthesizer must force this alignment; two proposers claiming "no shared state beyond the JSON file path" while writing incompatible JSON is the exact bug the Phase-A parallel build was meant to prevent. Also missing from proposer's schema: `m_DM_GeV` as a duplicated top-level mirror of `dm_candidate.mass_gev` — ddcalc expects it flat.

Additionally, the proposer's `source: "micromegas-6.2.3"` example contradicts its own 6.1.15 pin. Sloppy.

## 6. Plugin placement — conceptual win, practical pain

> "new plugin ... plugins/constraints/"

The argument is fine at the taxonomy level but the proposer ignores two concrete dependencies:

1. **`_shared/blocker.schema.json` and `_shared/sarah_name.py` live under `plugins/hep-ph-toolkit/skills/_shared/`.** The proposal hand-waves "the new `plugins/hep-ph-toolkit/skills/_shared/` can symlink or re-reference it. Better: ... move to `plugins/shared/schemas/` — but that refactor is out of scope". You cannot both (a) create a new plugin that depends on the schema and (b) declare the relocation out of scope. Either the refactor happens *first* (synthesizer's preferred path, relocate to `plugins/shared/schemas/blocker.schema.json`), or we co-locate under `model-building` and avoid the symlink.
2. **`marketplace.json` update is missing from the proposal.** Adding `plugins/constraints/` requires an entry in `.claude-plugin/marketplace.json` and a row in `CLAUDE.md`'s category table. The proposer mentions the table edit only in passing via the `/ddcalc` sibling proposal. Synthesizer: write both explicitly into the plan.

Preferred synthesizer verdict: create `plugins/constraints/` *and* relocate `_shared/` contracts to `plugins/shared/schemas/` in a pre-step (W0-style contract migration). Half-measures will rot.

## 7. Scope creep — `all` aggregate is unnecessary; SLHA-only relic-density case missed

> "`/micromegas all <model>` — run all four, emit aggregated JSON"

Dead weight. The four subcommands already produce a single `summary.json`; the orchestrator (Phase C) composes them. An `all` command that runs indirect-detection every time the user asks "what is Ωh²" wastes 10× compute on PPPC4DMID table interpolation the user did not ask for. Cut it.

**Missing case:** relic-density-only questions for MSSM-family models do not require UFO at all — micrOMEGAs ships precompiled MSSM/NMSSM/singletDM projects, and a pure SLHA pass through `MSSM/main` returns Ωh² in <1 s without CalcHEP conversion. For the paper's 2HDM+a this doesn't apply, but for the many *other* papers the user will run, the UFO-required path forces a 10-minute CalcHEP compile for each new model. Synthesizer: add a `--precompiled <project>` mode that bypasses UFO conversion when the model name matches a bundled micrOMEGAs project.

**Missing case:** **DM asymmetry** and **co-annihilation thresholds** are silently absent. The paper's blind-spot region sits near the Higgs-funnel coannihilation wall; `darkOmega` with `fast=1, Beps=1e-6` often reports spurious convergence near thresholds. The proposer's `OMEGA_UNCONVERGED` catches NaN but not the more common failure mode of wrong-by-100× results. micrOMEGAs has an `assignValW("Beps", 1e-4)` escape; the skill needs to expose it and to detect suspicious coannihilation-wall values (e.g. Ωh² changing by >20% between `Beps=1e-4` and `1e-6`). Asymmetric DM (`darkOmega2`, the two-component API) is not mentioned at all.

## 8. `reference_only` fallback contradicts the project memory

> "Default is to fatal out if micrOMEGAs is unreachable, per user's 'augment not replace' memory."

Then why is `--allow-analytic-fallback` present? The memory is a hard rule ("block on missing tool-drivers rather than fall back to analytic"). An opt-in flag creates cargo-culted use in CI configs and teaching notebooks. Delete it. If offline work is the motivation, the right answer is to make the installer work offline — not to reimplement the Boltzmann solve in Python. Synthesizer: remove `MICROMEGAS_ANALYTIC_FALLBACK` and `--allow-analytic-fallback` entirely from v1.

## 9. macOS build quirks — not addressed

Proposer says "macOS/Linux parity is clean" nowhere; it's silent. Known micrOMEGAs 6.x footguns on macOS: (a) Homebrew gfortran's `-ff2c` linkage mismatch with Xcode's `libc`, (b) SDK-version checks in `CalcHEP_src/getFlags` break on macOS 14+ unless `SDKROOT` is set, (c) `dyld` load of `libSLHAplus.dylib` needs `DYLD_LIBRARY_PATH` in the smoke-test environment. None of this is acknowledged. Synthesizer: require an explicit macOS smoke-test matrix entry and add `MICROMEGAS_MACOS_SDK_MISMATCH` to the blocker vocabulary.

## 10. Blocker set is incomplete

Missing codes the proposer should have enumerated:

- `MICROMEGAS_BUILD_NEEDS_NETWORK` (see §1).
- `CALCHEP_CONVERTER_VERSION_SKEW` — when cached CalcHEP-converted model was produced by a different micrOMEGAs version; proposer's §5 Q2 acknowledges the risk but does not create a blocker for it.
- `DM_CANDIDATE_COLOR_MISMATCH` — the proposer folds "charged or colored" into `DM_CANDIDATE_UNPHYSICAL` but those are different diagnoses; splitting helps the orchestrator message the user.
- `RELIC_BEPS_SENSITIVE` (recoverable) — Ωh² sensitive to numerical tolerance, typical at coannihilation wall (see §7).
- `PPPC_TABLES_MISSING` — indirect subcommand depends on shipped tables; if user installed via `use-path` on a stripped tree, tables absent.

## 11. Open-question quality audit

- Q1 (CalcHEP split): good, already attacked in §1; proposer's "I say no" is wrong.
- Q2 (cache key): **correct question, wrong framing.** The cache key absolutely needs `micromegas_version`; treating it as an open question is theatre. Fold into the design, not open questions.
- Q3 (DM auto-detect): good; my §3 answers it — make explicit spec mandatory.
- Q4 (reference_only): see §8; delete.
- Q5 (spectra HDF5 vs per-point `.dat`): **reasonable but the framing is off.** For 10³ scan points the right answer is neither — inline a coarse-binned spectrum (20 log-bins) in `summary.json` for downstream plotting and write the full spectrum to a single `spectra.h5` per scan (not per point). Proposer's binary choice missed the compromise.
- Q6 (`OMEGA_UNCONVERGED` recoverable vs fatal): the schema already supports three-state and mode-aware is trivial — this is not a live question.
- Q7 (6.1.15 vs 6.0.x): see §2. Real question, poorly posed; depends on a fact the proposer didn't check.

**Open questions proposer missed:**

- **Thermal relic assumption.** micrOMEGAs assumes standard cosmology. For non-thermal histories (early-matter-dominated, entropy injection — relevant to several 2HDM+a cosmologies) Ωh² is misleading without a caveat. Should `summary.json` carry a `cosmology: "standard-thermal"` tag for downstream interpretation?
- **Nucleon form-factor choice.** σ_SI depends strongly on `σ_πN` and strange-quark content. micrOMEGAs default (lattice 2018) differs from the Arcadi–Profumo paper's choice. Which set do we use, and do we expose it as a config key?
- **Reproducibility with random seeds.** micrOMEGAs freeze-out solver is deterministic, but the CalcHEP phase-space integrator uses a PRNG for some channels. Do we fix a seed? If so, where?
- **Multi-component DM.** `darkOmega2` path for two stable particles — out of scope or blocker code `MULTICOMPONENT_UNSUPPORTED`?
- **Concurrency safety.** `/spheno-build --scan` is serial (see skill doc line 86). Does `/micromegas` inherit that or run parallel? The project dir at `$STATE_ROOT/models/<name>/micromegas_project/` is shared state — parallel runs will trample each other.

---

## Synthesizer action list (ranked)

1. Force `scattering.json` schema alignment with `/ddcalc` **before** either skill ships.
2. Resolve UFO version fact → choose 6.0.5 vs 6.1.15 on evidence.
3. Delete `--allow-analytic-fallback` and the `MICROMEGAS_ANALYTIC_FALLBACK` blocker.
4. Make `dm_candidate` in `spec.yaml` mandatory; drop the silent auto-detect heuristic.
5. Reverse CLI > spec precedence to spec > CLI-with-audit.
6. Relocate `_shared/` schemas to `plugins/shared/schemas/` as a W0-style prework before `plugins/constraints/` lands.
7. Drop the `all` aggregate subcommand; add `--precompiled <project>` for the MSSM/singletDM fast path.
8. Expose `Beps` and add a sensitivity check for coannihilation-wall points.
9. Add the five missing blocker codes (§10).
10. Add macOS-specific smoke-test matrix and `MICROMEGAS_MACOS_SDK_MISMATCH`.
11. Declare concurrency policy (serial per the SPheno precedent, with a per-run project dir to avoid shared-state conflicts).
12. Answer the five new open questions above before implementation starts.

Word count: ~1480.
