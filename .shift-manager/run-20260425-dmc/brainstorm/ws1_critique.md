# WS-1 Critique — Output-contract verification deliverable

**Reviewer:** critic agent (3-agent brainstorm)
**Subject:** `.shift-manager/run-20260425-dmc/brainstorm/ws1_propose.md`
**Lens:** `briefs/ROUTING_LENS.md`

---

## Overall verdict: **ACCEPT-WITH-CHANGES**

The proposal is solid in structure, the drift findings are real (I verified them against the source files), and the manifest+test+audit-doc decomposition is defensible under the routing lens. But the proposer **missed the single most important fact in the codebase**: micrOMEGAs already has a jsonschema (`plugins/shared/schemas/scattering.schema.json`) with `additionalProperties: false`, pinning `summary.json` to `scattering/v1`. That schema does NOT contain `omega_h2` or `sigma_v_zero`, and it cannot be amended without a version bump. This shifts the drift-fix calculus in §3a from "small docs update" to "schema version bump" and changes the whole shape of WS-4. The proposer also under-weights subcommand-specific output (`/micromegas relic` vs `scatter` vs `annihilate` produce different artifacts; only `scatter` writes the `scattering/v1` `summary.json`), and their drift policy is too consumer-friendly. Several structural things they get right: case-strict matching, treating audit findings as findings rather than auto-fixes, refusing to invent fields. Conditional accept; synthesizer must lock in 6 specific things below.

---

## §1 — Deliverable shape

**Where the proposer is right.** The "contract is code, narrative is doc" split honors the routing lens cleanly. Pure string-presence checks ARE the same risk class as `check_prereqs` (model-agnostic). Decoupling Artifact A's machine-checked manifest from Artifact B's human audit narrative means future contributors who edit the SKILL.md table without touching the manifest get a loud test failure — that's the right enforcement shape.

**Where I push back hard.**

1. **The proposer ignored the existing jsonschema.** `plugins/shared/schemas/scattering.schema.json` is a real JSON Schema 2020-12 file enforcing `additionalProperties: false` on `summary.json`. There is already a `tests/test_scattering_schema.py` test against it. The proposer's flat field-map manifest is **redundant with parts of this schema** for the scatter path, and **inconsistent with it** for relic/annihilate (where no schema exists). Recommendation: the manifest should *reference* `scattering.schema.json` for the scatter path rather than duplicate field names — otherwise we'll have two sources of truth that can drift from each other.

2. **The "single executable test, no manifest" alternative is stronger than they consider.** The proposer dismissed it implicitly. But: the test code itself can carry the field names as Python literals (or import them from a small Python module). That's still "code as the contract," and it has *fewer* moving parts than manifest+test+audit-doc. The downside the proposer flags ("manifest is the structured form the test iterates over") is real but not decisive — a Python `FIELDS = [...]` list does the same job. The smaller blast radius of a single-file Python contract is worth weighing.

3. **The "single audit doc, no executable" alternative.** Proposer dismisses because "drift can be reintroduced silently." That's correct under the routing lens — but it's worth saying so explicitly: a doc-only deliverable would be a **lens violation**, not just inferior. The proposal would be stronger if it called this out as a lens-driven elimination.

4. **The jsonschema-as-typed-schema alternative is what's *actually* in this repo.** This is the option the proposer should have engaged with most seriously. Recommendation: Artifact A's manifest should be a *thin index pointing into existing schemas where they exist* (just `scattering.schema.json` today), and a flat field-map *only for tools that have no schema* (MadDM stdout, DRAKE stdout, micrOMEGAs `stdout.log` regex captures, micrOMEGAs relic/annihilate/indirect outputs that don't go into `summary.json`). That preserves the existing investment instead of duplicating it.

5. **Manifest drift between manifest and schema becomes its own contract risk.** If WS-1 ships a flat field-map listing `sigma_si_proton_cm2` and `scattering.schema.json` *also* lists `sigma_si_proton_cm2`, who's authoritative when one moves? The proposer doesn't say. Synthesizer must decide.

---

## §2 — Scope: which fields to verify

**Drift findings — I verified each independently:**

| # | Proposer's claim | Verdict | Evidence |
|---|------------------|---------|----------|
| 1 | micrOMEGAs `summary.json` schema lacks `omega_h2` | **CONFIRMED, and worse than proposer says** | `micromegas/SKILL.md` lines 226-239 + `scattering.schema.json` `additionalProperties: false`. The schema actively *forbids* the field; this is not a docs gap, it's a contract violation. |
| 2 | micrOMEGAs `summary.json` schema lacks `sigma_v_zero` | **CONFIRMED, same gravity as #1** | Same evidence. |
| 3 | MadDM internal doc drift (`sigmav_xf` narrative vs `sigmav_total` JSON example) | **CONFIRMED** | `maddm/SKILL.md` line 164 says `sigmav_xf`, line 176 emits `sigmav_total`. Router uses `sigmav_total`. |
| 4 | DRAKE Ωh² field unnamed in router | **CONFIRMED** | `dark-matter-constraints/SKILL.md` Step 5 (line 213) says only "collect its Ωh² output". `drake/SKILL.md` line 207 emits `omega_h2`. |
| 5 | No MadDM fixture in repo | **CONFIRMED** | `plugins/monte-carlo-tools/skills/maddm/` has no `tests/fixtures/`. |
| 6 | No DRAKE skill-level fixture | **CONFIRMED** | Same check. |

**New drift findings the proposer missed:**

7. **Scan-mode CSV column names disagree with router's field names.** `micromegas/SKILL.md` line 104 says scan CSV has `omega_h2, sigma_si_p, sigma_sd_p, sigma_v_0` — the router reads `sigma_si_proton_cm2`, `sigma_sd_proton_cm2`, etc. Scan-mode is v1.1 backlog (not implemented yet), but if it lands without coordination, the router can't read scan output. Add to manifest as `pending_v1.1_alignment_required`.

8. **Subcommand-specific output mapping is incomplete.** The proposer notes per-subcommand schema variance as a risk (§5.4) but doesn't act on it. Concretely: only `/micromegas scatter` writes a `scattering/v1` `summary.json`. `/micromegas relic` writes Ωh² where? `/micromegas annihilate` writes ⟨σv⟩ where? The router's Step 4 cross-check table assumes one location per field, but the actual artifacts may be split across `stdout.log`, `summary.json`, and per-subcommand outputs. WS-1 must enumerate this; the proposer punted.

9. **The router doesn't name the MadDM run-output artifact at all.** Step 2 says "Collect the MadDM output JSON (see `/maddm` SKILL.md §Reading MadDM output)" — but MadDM emits no JSON natively. The "JSON" is constructed by the agent. The contract therefore is between the router and the agent's parse of `MadDM_results.txt`. The proposer notes this in §5.1 but doesn't carry it into the manifest design. Recommendation: every MadDM manifest entry needs a `produced_by` field equal to `agent_parsed` to make this explicit. Otherwise WS-4 helpers will assume there's a MadDM file to open with `json.load`.

10. **`config.drake_path` is a config key, not an output field — the manifest is conflating two contracts.** Entries 10 and 11 in proposer's table are about config keys read by the router. That's a different contract class than "field emitted by tool X in artifact Y." Recommendation: either split the manifest into two sections (`output_fields` vs `config_keys`) or scope WS-1 to output fields only and put config-key contracts under a separate WS-1.5.

---

## §3 — Drift policy

**The "fix the router by default" rule is wrong.** Proposer's argument is "router is consumer; fix the consumer." Counter-arguments the proposer didn't engage with:

1. **The producer has the canonical contract.** In every modern API design, the *producer* owns the schema and consumers read from it. Auto-fixing the consumer (router) will mask producer regressions: if `/micromegas` ships v1.1 and silently changes a key from `sigma_si_proton_cm2` to `sigma_si_p` (matching the scan-CSV convention), the router will quietly bend to fit and the regression is invisible. **Fixing the router by default is the wrong instinct.**

2. **The audit may have caught a producer bug.** If `summary.json` lacks `omega_h2`, the right question is "should `summary.json` have `omega_h2`?" not "should the router stop reading it?" The fact that scan-mode CSV *does* include `omega_h2` (item 7 above) suggests the answer is yes — the producer has a gap. Auto-changing the consumer would paper over a real producer bug.

3. **The default should be "neither — flag for design decision."** The lens says contracts between tools are deterministic-helper territory; that means *both sides* of the contract are load-bearing. WS-1 should flag drift, not pick a side. The audit doc is the right place to record `DRIFT_DETECTED` with a recommended fix; the manager and WS-4 own the decision. The proposer's §3a half-acknowledges this in §3a's exception clause but then defaults the wrong way.

**Concretely**, for the two drift cases the proposer flagged:

- **micrOMEGAs `omega_h2` and `sigma_v_zero` in `summary.json`.** Proposer recommends "add these to the schema." But `scattering.schema.json` is named `scattering/v1` and has `additionalProperties: false`. Adding fields requires bumping to `scattering/v2` or splitting into a separate `relic/v1` and `annihilation/v1` schema (which is the more principled answer — `scattering` shouldn't carry annihilation fields). This is *not* a small docs update; it cascades to `/ddcalc` and any other consumer. Synthesizer must decide which schema-shape WS-4 commits to.

- **DRAKE field naming.** Proposer's recommendation (router names `omega_h2` explicitly) is the right call here, because DRAKE is producer-side already canonical (`drake/SKILL.md` line 207). The router is genuinely under-specified. **Agreed on this case.**

**§3b (documented but absent) — accept.** The `version_dependent_optional` annotation is correct. Just rename to something less verbose (`optional` with a `reason:` field).

**§3c (present but undocumented) — accept.** Conservative is right; an undocumented field could be model-class-specific.

---

## §4 — Model-agnosticism check

**The "unprovable from docs" framing is largely correct, but the cop-out objection has merit.** Here's the steel-man for "WS-1 should empirically check": MadDM's output format being model-agnostic is a *factual* claim about the binary's behavior. It can be verified empirically by running on two models with different topology — the proposer dismissed this for time reasons but didn't quote the actual cost.

**Practical assessment:** Running MadDM on `DMsimp_s_spin0` (simplified UFO, no SLHA) and on a small MSSM benchmark would take ~15-30 min compute time + install gates. WS-1's stated charter is to verify contracts, not run experiments — but the alternative is shipping WS-1 with `model_class_dependent` markers on every MadDM field, which forces WS-4 to keep MadDM parsing entirely in the LLM (per the lens). That may be the right end-state, but it's worth checking: a single empirical run could promote 3-4 fields from `model_class_dependent` to `verified_model_agnostic`, shrinking WS-4's LLM scope.

**Recommendation: WS-1 should include ONE empirical check, scoped narrowly:** run `/maddm relic` on `DMsimp_s_spin0` (smallest documented path), commit the output as a fixture, and verify field names against the synthetic fixture. That's enough to disprove the "field names depend on model class" hypothesis for at least one direction. If results differ from the synthetic, that's a Day 1 finding worth surfacing. If they match, we have one real fixture and reduced LLM scope downstream.

If the synthesizer rejects the empirical run (legitimate — install gates, time, blast radius), it must say so explicitly: WS-1 ships with no empirical validation of MadDM output schema, and WS-4 must keep the entire MadDM parser in the LLM.

**On micrOMEGAs schema versioning being "proof of model-agnosticism" (proposer §4 third bullet):** I disagree this is a proof. `scattering/v1` is pinned for the *scatter* subcommand. Proposer concedes this but the third bullet's claim is too strong as written. Synthesizer should soften: "schema versioning is *evidence* of model-agnosticism for the fields the schema covers, but does not extend to subcommands without their own schemas."

---

## §5 — Fixture strategy

**Proposer's recommendation: synthetic fixtures in WS-1, real ones retroactively in WS-3.** Three issues:

1. **Synthetic fixtures encode *belief*, not reality.** If the proposer hand-crafts a `MadDM_results_synthetic.txt` matching what `maddm/SKILL.md` documents, and later the real MadDM output uses slightly different formatting (e.g. the documented `Omegah2 = 2.92e-01` is actually written as `Omegah2  = 2.92E-01` with two spaces and capital E), the WS-1 test passes against the synthetic fixture and silently disagrees with reality. The proposer's mitigation ("string-presence matching only, not positional") helps but doesn't fully address this — regex shape (case sensitivity of `e` vs `E`, presence of leading whitespace) can vary too. A real MadDM run is the only way to disprove this class of bug.

2. **Fixture placement is contentious.** Proposer wants `plugins/monte-carlo-tools/skills/maddm/tests/fixtures/MadDM_results_synthetic.txt` (a new directory in the maddm skill). But the *purpose* of this fixture is to support the dark-matter-constraints router's contract test, not the maddm skill's own tests. There are three placement options:

   a. In the producer's `tests/fixtures/` (what the proposer suggests). Pros: co-located with the tool that documents the format. Cons: pollutes the producer skill with consumer-driven artifacts.

   b. In `dark-matter-constraints/tests/fixtures/` (consumer-side). Pros: clear ownership — these fixtures exist to support the router. Cons: the router skill grows fixture artifacts about every downstream tool.

   c. In `plugins/shared/test_fixtures/` or similar. Pros: neutral ground. Cons: discovery gets harder.

   The proposer picks (a) without acknowledging (b) or (c) exist. (b) is the strongest match for the lens — the contract is the *router's* contract, so the test artifacts belong with the router. Synthesizer must decide.

3. **WS-3 retroactive replacement is a future-tense promise.** If WS-3 slips or fires only on dark-SU(3) (a non-standard model class), the synthetic fixture stays forever, and we ship synthetic-only. Mitigation: WS-1 must include a milestone-style follow-up gate ("fixture status MUST be re-evaluated when WS-3 produces real run output; if WS-3 is descoped, a separate WS-1.x must produce real fixtures"). Proposer's §5.9 mentions this in passing but doesn't make it a tracked deliverable.

**My recommendation:** synthesizer should split the fixture decision into "WS-1 minimum" vs "stretch goal." WS-1 minimum: synthetic fixture for MadDM, synthetic for DRAKE, reuse existing real `summary_singletDM.json` for micrOMEGAs scatter, **plus** a tracked open-task for real MadDM and DRAKE fixtures with explicit gate criteria. Stretch goal (only if WS-1 cycle has slack): one empirical MadDM run on `DMsimp_s_spin0`, output committed as real fixture replacing synthetic.

---

## What the proposer missed (composite list)

A. **`scattering.schema.json` exists** and constrains the entire micrOMEGAs scatter contract. This is the most material miss.

B. **`tests/test_scattering_schema.py` already exists.** WS-1's contract test should not duplicate this; it should orchestrate above it.

C. **Subcommand-specific outputs (relic/scatter/annihilate/indirect) — only scatter has a schema.** Manifest must enumerate per-subcommand or explicitly scope to scatter.

D. **Scan-mode CSV column naming inconsistency** (`sigma_si_p` vs `sigma_si_proton_cm2`) is unaddressed.

E. **Versioning of upstream tools.** MadDM 3.2 vs 3.3, micrOMEGAs 6.0.5 vs 6.1, DRAKE versioned by `drake_version`. The manifest implicitly pins to "current" — what happens when one bumps? Proposer mentions this only for the manifest's own schema_version (§5.7), not for upstream tool versions.

F. **Error-state contracts.** When MadDM fails, what does `MadDM_results.txt` look like? Truncated? Absent? Containing a partial header? The router's prereq check assumes the file exists if the run succeeded — but a partial-success failure mode is undocumented. Same for micrOMEGAs `summary.json` when `OMEGA_UNCONVERGED` fires.

G. **`config.drake_path` is a config-key contract, not an output-field contract.** Different contract class; manifest design should reflect this.

H. **`/drake-install detect` `status` enum literals** (`"configured"`, `"found"`, `"missing"`, `"activation_required"`) are themselves a contract. Router Step 5 hard-codes them. They're produced by `/drake-install`, consumed by the router. This is its own contract row that the proposer mentions in §2 entry 11 but doesn't put in the manifest schema.

I. **Audit-doc location.** Proposer puts `ws1_audit_report.md` under `.shift-manager/run-20260425-dmc/state/`. This means after the run is reaped/archived, the audit findings vanish from the live tree. If WS-4 needs to reference them, they need to be promoted to a more permanent location. Recommendation: also write a sanitized version into `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` as a permanent artifact.

---

## Synthesizer must resolve

1. **Schema-vs-manifest authority.** Does Artifact A duplicate `scattering.schema.json` field names, or reference it? Pick one. (My recommendation: reference; manifest is a thin index.)

2. **Drift policy default.** Auto-fix router (proposer's default), auto-fix producer (my counter), or flag-only / no auto-fix (lens-aligned default). (My recommendation: flag-only; manager/WS-4 decide each case.)

3. **Schema migration scope for `omega_h2` and `sigma_v_zero`.** Is the fix a schema bump (`scattering/v2`), a new schema (`relic/v1` + `annihilation/v1`), or downgrade router to `stdout.log` regex? Three real choices; pick one. (My recommendation: separate `relic/v1` and `annihilation/v1` schemas; `scattering/v1` stays scoped to its name.)

4. **Empirical MadDM run in WS-1 scope or not.** If yes, run `/maddm relic` on `DMsimp_s_spin0` and commit the output. If no, document explicitly that WS-4 keeps the entire MadDM parser in the LLM (no helper). (My recommendation: include the empirical run as a stretch goal; ship synthetic if it slips.)

5. **Fixture placement convention.** Producer side (proposer), consumer side (lens-aligned), or shared. Pick once and apply uniformly. (My recommendation: consumer side — `dark-matter-constraints/tests/fixtures/` — because the contract is the router's.)

6. **Manifest scope: output fields only, or fields + config-keys + status-enums.** Three contract classes, currently jumbled. (My recommendation: split into three sections within one manifest, or three manifests; flat list is wrong.)

7. **Audit-doc permanence.** Lives in `.shift-manager/...` only (transient) or also in a permanent location like `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md`. (My recommendation: both — transient in run dir, permanent in router skill.)
