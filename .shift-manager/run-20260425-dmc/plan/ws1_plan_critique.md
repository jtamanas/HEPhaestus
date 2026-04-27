# WS-1 Plan Critique — Output-contract verification

**Critic:** plan-critic agent
**Inputs read end-to-end:** `briefs/ROUTING_LENS.md`, `brainstorm/ws1_synthesis.md`, `plan/ws1_plan_draft.md`, `plugins/shared/schemas/scattering.schema.json`, `plugins/shared/schemas/tests/test_scattering_schema.py`, `plugins/constraints/skills/dark-matter-constraints/SKILL.md` (Step 4/Step 5 regions), `plugins/constraints/skills/micromegas/SKILL.md` (output contract regions), `plugins/monte-carlo-tools/skills/maddm/SKILL.md` (Reading MadDM output), `plugins/monte-carlo-tools/skills/drake/SKILL.md` (detect status enum).

---

## 1. Verdict

**ACCEPT-WITH-CHANGES.**

The plan is well-structured, lens-aligned, and faithful to the synthesis. The critical-path (T1→T3→T4→T5) is sound. But the plan has **three consequential defects** that the synthesizer must resolve before implementation:

1. **The 11-entry count is wrong by construction** — it commits the manifest to neutron rows that the router does not actually consume (entries 10/11). The synthesis flagged this as a tension; the plan blindly inherited the count without re-adjudicating.
2. **T8 is mis-classified** — "scope notes for producer doc edits" is *spec* work that belongs in the synthesis output (already there at synthesis §4), not as a separate WS-1 plan task. As drafted T8 either duplicates synthesis §4 or invents new edits, and its gates re-grep the live producer SKILLs from the worktree (which may diverge).
3. **The negative-control gate (T5 #4) is broken as written** — `cp` then `jq > /tmp/mutated.json` (same target) destroys the file before jq reads it, and the gate never re-validates the test against the *original* manifest after the mutated test passes, leaving open the possibility that the test simply always fails.

Several gates are also too loose (`wc -l ≥ 80`, `grep -c "^## " ≥ 6`) or too brittle (sorted-array literal jq comparisons that fail on a single missing comma). Owner assignment for T3 underestimates the schema-pointer-resolution judgment required.

---

## 2. Per-task review

### T1 — Skeleton manifest
**Sentence:** Author empty-shell `router_contract.json` with three sections.
**Objection:** Should merge with T3. T1's deliverable is an empty file with three empty arrays — there is no judgment, no risk, no parallelism unblocked by separating it. The drafter justifies T1 as "land first so T2 can write a schema *for* it without speculation" but T2 doesn't need a populated manifest to exist; it only needs the *shape* (which is in synthesis §1). T1+T3 collapse to one task at no cost. **Recommendation: merge T1 into T3.**

### T2 — Manifest self-schema
**Sentence:** Write `router_contract.schema.json` and a mirror pytest file for it.
**Objection:** Generally sound but **out-of-scope creep**. Putting `router_contract.schema.json` under `plugins/shared/schemas/` is a producer-side commit — `shared/schemas/` is the home of cross-tool *physics* schemas (`scattering`, `processspec`, `amp_reduced.meta`). The router's manifest schema is a router-internal contract. **Recommendation: place it next to the manifest at `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json`** (or under `dark-matter-constraints/tests/`). Keep `plugins/shared/schemas/` reserved for cross-tool physics contracts.

Also: gate #3's `sort == [...] | sort` is not how jq compares arrays — `(.required | sort) == ["a","b"]` is the correct form; the drafter's expression is ambiguous and may pass when it shouldn't.

### T3 — Populate manifest entries
**Sentence:** Fill in 11 output_fields + 3 config_keys + 1 status_enum.
**Objection (load-bearing):** The drafter's own gate #5 betrays uncertainty: "verify count = 5 — Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩(v→0) — actually 4; if 4: assert 4. Implementer reconciles §2a table count with this gate before commit." A plan that ships a gate it cannot resolve at draft time is shipping the indecision into implementation.

Counting the router's actual Step 4 cross-check table (lines 136–141 of `dark-matter-constraints/SKILL.md`) yields **4 rows × 2 producers = 8 router-consumed cross-tool fields, plus 1 DRAKE Ωh² = 9**. The synthesis's 11-entry count was reached by adding the two micrOMEGAs *neutron* rows (entries 10/11) on the grounds that "the schema requires them." That is conflating two contracts: (a) the router-vs-producer cross-check contract (4 rows × 2 producers + 1 DRAKE), and (b) the producer-side `scattering/v1` schema completeness contract (which the existing `test_scattering_schema.py` already covers). The router does not surface neutron rows; including them in the *router* contract manifest is scope leakage from physics-schema territory.

Recommendation: **manifest carries 9 output_fields**, not 11. The neutron rows are noted in `AUDIT.md` as "schema-required, router-not-consumed; add when WS-4 surfaces them" rather than emitted as manifest entries today. If the synthesizer overrules and keeps 11, then both gates #4 and #5 must reflect that explicitly with no "actually 4" hedge.

**Owner class:** `opus-implementer` is correct. The schema-pointer resolution (`/properties/sigma_si_proton_cm2`) and `model_class_certification` enum population both require reading synthesis §6.4 carefully. Sonnet would mechanically copy the example.

### T4 — Fixtures
**Sentence:** Create synthetic MadDM/DRAKE fixtures + symlinks for micrOMEGAs.
**Objection:** Two real risks the plan understates.

(a) **Symlink portability.** No existing fixture in the repo uses cross-skill symlinks (verified by checking `plugins/constraints/skills/micromegas/tests/fixtures/` — all regular files). This is a new convention. The 5-`../` relative path is fragile and breaks under git worktree if the worktree path differs. **Recommendation:** make the convention explicit — add a one-line note in `AUDIT.md` ("symlinks are the consumer-fixture convention from WS-1 forward; if portability fails on any platform, switch to git-tracked copies and accept the duplication") and verify the symlinks resolve from a worktree at gate time, not just from main.

(b) **Gate #8 (`grep -Ei 'sigmav_total\s*='`) is right physics but wrong adjudication.** `maddm/SKILL.md` line 164 documents `sigmav_xf` as the parsed field name; the synthesis decides `sigmav_total` is canonical. Having T4 commit a synthetic that uses `sigmav_total` while the producer doc still says `sigmav_xf` means the contract test will then *fail* at T5 against the producer SKILL.md grep (T5 §5.3 #10) — exactly the `DRIFT_PRODUCER_DOC_GAP` classification, which is correct, but T5 has it as a hard fail not an xfail. **Recommendation:** the synthetic uses `sigmav_total` *and* T3's manifest entry for that row carries `audit_status: pending_producer_doc_fix` (a new literal — needs adding to T2's enum) so the test xfails it cleanly until WS-4 lands the producer doc edit. This is the same pattern as `pending_schema`.

### T5 — Executable contract test
**Sentence:** Write `test_router_contract.py` covering 18 assertions.
**Objections:**

(a) **Negative-control gate is broken.** Gate #4 reads:
```
cp router_contract.json /tmp/mutated.json && jq '...' < router_contract.json > /tmp/mutated.json
```
The `cp` is wasted (jq overwrites the same target). More importantly, the gate doesn't verify the test *passes* on the original manifest *after* the mutation experiment — a test that always fails would pass this gate. **Recommendation:** restructure as two gates — (i) baseline pass on shipped manifest, (ii) deliberate mutation produces FAIL with the right `DRIFT_*` code in stderr.

(b) **Gate #6 (`time` < 5s)** is implementer-machine-dependent and adds zero value. Drop.

(c) **Gate #5 (`grep` for forbidden imports) is nonsensical** — the regex `^import (?!(json|...))` uses a Python regex extension that GNU grep without `-P` does not honor; on macOS BSD grep this silently does the wrong thing. **Recommendation:** replace with `python -c "import ast; ..." ` AST check, or just drop — pytest passing is sufficient.

(d) **The `pending_schema` xfail policy is correct but `len(...) == 2` is too tight.** If T3 adds a third pending row (e.g. the `sigmav_total` doc-fix case above), this gate breaks. **Recommendation:** assert `len(pending_schema_rows) == jq-count-of-pending-rows-in-manifest`, dynamically.

### T6 — Permanent AUDIT.md
**Sentence:** Write committed contract narrative.
**Objection:** Gate #2 (`wc -l ≥ 80`) is the canonical too-loose gate. A 90-line file of empty bullets passes; a 70-line dense file fails. **Recommendation:** replace with content-shape gates (e.g. each of the 6 named sections has at least one paragraph; each drift code is named in a sentence not a list item; the `WS-4` handoff appears in a paragraph not a heading).

### T7 — Run-dir audit report
**Sentence:** Write transient operational log.
**Objection:** Mostly fine. Gate #6 (`grep -F "scan_index.csv"`) is fine. Gate #2 (`wc -l ≥ 50`) has the same too-loose flaw as T6 #2. Owner-class `opus-implementer` is overkill — this is mechanical narration of T1–T6 outputs. **Recommendation:** sonnet, 1 cycle.

### T8 — Producer doc-edit scope notes
**Sentence:** Append "WS-4 doc edits queued" section to AUDIT.md.
**Objection (load-bearing):** This task is the largest scope-discipline risk in the plan. Synthesis §4 already enumerates the four producer doc edits in narrative form. T8 as drafted re-derives them with verbatim `old text`/`new text` blocks, which:
1. Duplicates synthesis §4 (single-source-of-truth violation).
2. Risks diverging from synthesis §4 if the implementer paraphrases.
3. Re-greps the live producer SKILL.md *from a worktree*, where files may have diverged from the synthesis-time hashes (pre-flight risk #6 calls this out but T8 doesn't gate on it).
4. Produces edits that WS-4 may not adopt verbatim — synthesizing a "verbatim edit" is itself judgment WS-4 owns.

**Recommendation:** either (a) **drop T8 entirely**; AUDIT.md (T6) names the four edits at the level synthesis §4 already pinned, and WS-4's plan-drafter does the verbatim-edit derivation against the worktree at WS-4 time, or (b) reduce T8 to "verify synthesis §4's four edits still apply against the current SKILL.md hashes, append the four hashes to AUDIT.md as sigchecks." Option (a) is cleaner.

### T9 — Plan-internal review
**Sentence:** Reviewer re-runs every gate and signs off.
**Objection:** Gate #1 (re-run every gate from clean shell) is mechanically expensive — depending on cycle counting policy this could double the WS-1 cycle budget. Also the reviewer is `opus-reviewer`, but every gate is mechanically checkable, so a sonnet reviewer running the gates and an opus reviewer adjudicating *interpretive* findings would be more efficient. **Recommendation:** split T9 into T9a (sonnet, mechanical gate replay) + T9b (opus, interpretive sign-off), or accept it as-is and bump cycle estimate to 2.

---

## 3. Gate audit

| Gate | Issue | Replacement |
|---|---|---|
| T1 #6 (`output_fields \| length == 0`) | Asserts skeleton — but T3 immediately overwrites; gate is checked at wrong time | Drop T1; merge into T3 |
| T2 #3 (`required \| sort == [...] \| sort`) | jq syntax ambiguity | `(.properties.output_fields.items.required \| sort) == ["audit_status",...] ` |
| T2 #5–#6 (audit_status enum literals) | Hard-codes 3 specific literals; misses `pending_producer_doc_fix` if T4 needs it | Lift the enum to a single source in synthesis (§3 + new literal) and assert `enum == that exact list, sorted` |
| T3 #5 ("4 or 5, implementer picks") | A gate the drafter cannot resolve at draft time | Pin to **4** MadDM rows; surface the count/total decision in "Synthesizer must resolve" |
| T3 #4 (`5 distinct observables`) | Couples the gate to the disputed neutron-row inclusion | Recompute after the count decision |
| T4 #8 (synthetic uses `sigmav_total`) | Forces a `DRIFT_PRODUCER_DOC_GAP` that T5 hard-fails | Either xfail that row (`pending_producer_doc_fix`) or fix producer doc in WS-1 — synthesizer chooses |
| T4 (no symlink-portability gate) | Symlinks are a new convention; gate must verify worktree resolution | Add: `realpath fixtures/micromegas/summary_singletDM.json | xargs test -f` from a fresh worktree |
| T5 #4 (negative-control) | Broken shell pipeline + no positive-control re-check | (i) baseline `pytest` pass, (ii) jq-mutate to a separate path, (iii) `ROUTER_CONTRACT_PATH=mutated pytest` fails with `DRIFT_*` in output |
| T5 #5 (forbidden imports regex) | PCRE-only on macOS BSD grep | Drop or replace with AST-based assertion in the test itself |
| T5 #6 (5s budget) | Machine-dependent; zero physics value | Drop |
| T5 #11 (`len(pending_schema_rows) == 2`) | Hard-codes count; breaks if scope shifts | `len(pending_schema_rows) == jq '[.output_fields[] \| select(.audit_status=="pending_schema")] \| length' router_contract.json` |
| T6 #2 (`wc -l ≥ 80`) | Too loose | Per-section content gate; no line floor |
| T6 #3 (`grep -c "^## " ≥ 6`) | Too loose; 6 empty headings pass | Each named section has a non-empty paragraph (grep for required tokens *under* each section, not just heading count) |
| T7 #2 (`wc -l ≥ 50`) | Too loose | Same fix as T6 |
| T8 #2–#3 (verbatim grep against live SKILL.md) | Brittle to whitespace/version drift; assumes synthesis-time file hashes | Capture `git rev-parse HEAD:plugins/.../SKILL.md` at synthesis time, gate T8 on hash match — OR drop T8 per §2 above |

---

## 4. Open-issue adjudications

### Issue 1 — Manifest entry count (4 MadDM + 6 micrOMEGAs + 1 DRAKE = 11)

**Synthesizer's tally (11) is wrong for the router contract.** Counting the actual Step 4 cross-check table in `dark-matter-constraints/SKILL.md` (lines I read live):
- 4 observable rows (Ωh², σ_SI(p), σ_SD(p), ⟨σv⟩)
- × 2 producers (MadDM + micrOMEGAs) = 8 cross-tool field entries
- + 1 DRAKE Ωh² entry (Step 5 Branch 2)
- = **9 entries**, not 11.

The synthesis added the two micrOMEGAs *neutron* fields (entries 10/11 in §2a) on the rationale that `scattering/v1` requires them. But:

(a) The router-vs-producer cross-check is over fields the *router actually surfaces*. The router does not surface neutron values; Step 4's table is proton-only. Adding manifest entries for unsurfaced fields conflates *router contract* with *schema completeness*.

(b) `scattering/v1` schema completeness is already test-covered by `test_scattering_schema.py` — that's the existing producer-side guard. WS-1's manifest has a different job: name the fields the router currently reads and could break on rename/disappearance.

(c) Synthesis's risk #8 explicitly flags the tension ("WS-4 must decide whether to add neutron rows to the user table"). That's a WS-4 decision; until WS-4 surfaces neutron rows in the router, the manifest shouldn't pre-commit.

**Adjudication: 9 entries (4+4+1).** AUDIT.md notes the neutron rows as "schema-required, router-not-consumed, promote to manifest if WS-4 surfaces them."

If the synthesizer disagrees and keeps 11, T3 gates #1, #4, #5 all need to be re-derived consistently and the `model_class_certification` for the neutron rows must be defined (currently undefined — `scatter_subcommand_only` would apply but isn't asserted).

### Issue 2 — DRAKE `activation_required` topology: hard-fail or soft-warn?

**Argue for hard-fail.** The drafter chose soft-warn (T5 §5.5 #17 emits a `pytest` WARNING). I disagree with the soft-warn for three reasons:

1. **The lens demands loud contracts.** Synthesis §3 rule ladder: "The test never silently passes when reality and manifest disagree." A `pytest` WARNING is the mildest form of "loud" — it's filtered by default in CI, easily missed in `pytest -q`, and does not propagate to a non-zero exit. Soft-warn is a silent pass dressed up.

2. **The drift is real, not theoretical.** `drake/SKILL.md` line 84–86 explicitly documents that `detect` returns only `configured|found|missing`, while the router's Step 5 Branch 2 hard-codes a fourth literal `activation_required`. That is the exact kind of `DRIFT_PRODUCER_DOC_GAP` the synthesis says should fail loudly. Treating it as a warning here while treating `omega_h2`/`sigma_v_zero` (also producer-doc-gap) as `pending_schema` xfail is inconsistent.

3. **The fix is scoped.** Either WS-4 extends `/drake-install detect` to emit `activation_required` (small producer-side change) or the router splits its branch table by subcommand (small router-side change). The contract test should hard-fail (or xfail with explicit `WS-4` reason) to force the choice into a logged `MANAGER_DECISIONS.md` decision rather than letting it linger as a perpetual warning.

**Adjudication: xfail (not warn, not pass).** Use the same `pending_*` pattern as the schema-pending rows. New literal: `pending_producer_topology_fix`. xfail reason cites `drake/SKILL.md` lines 84–86 explicitly. WS-4 promotes to `verified_in_writer_skill` after reconciling.

---

## 5. Sequencing recommendations

The drafter's chain T1→T2→T3→T4→T5→{T6,T7}→T8→T9 is mostly right but **misses real parallelism opportunities** within each implementation cycle:

1. **T1 collapses into T3.** No reason to ship an empty file as a separate cycle. Saves 1 cycle.

2. **T2 (manifest self-schema) and T3 (manifest entries) can run in one cycle.** Same file family, same opus-implementer, mutually informing. Author the schema and the populated manifest together so the schema is shaped by what the entries actually need, not speculation. Saves 1 cycle.

3. **T6 and T7 are parallel** (drafter notes this). Can be one cycle if same implementer.

4. **T8 dropped or merged into T6** (per §2 above). Saves 1 cycle.

5. **Producer SKILL.md edits are explicitly out-of-scope for WS-1 — so the "could producer edits run in parallel with manifest" question is moot here**, but flagged for WS-4: WS-4's producer edits and WS-4's helper authoring CAN run in parallel because they touch different files. Note that for WS-1, not WS-4.

**Revised plan: 5 tasks, ~7 cycles.**
- T1 (was T2+T3): manifest + self-schema, populated, opus, 2-3 cycles
- T2 (was T4): fixtures + symlinks, sonnet, 1 cycle
- T3 (was T5): contract test, opus, 2-3 cycles
- T4 (was T6+T7): AUDIT.md + audit_report.md, opus, 1-2 cycles
- T5 (was T9): review signoff, opus, 1 cycle

Drop T8 entirely (synthesis §4 is the source of truth for WS-4 edits; WS-4 plan-drafter re-derives from current files at WS-4 time).

---

## 6. Synthesizer must resolve

One-liners. The synthesizer must lock each of these before the plan is final.

1. **Manifest entry count: 9 or 11?** (§4 issue 1). My recommendation: 9.
2. **DRAKE `activation_required`: warn, hard-fail, or xfail-as-`pending_producer_topology_fix`?** (§4 issue 2). My recommendation: xfail.
3. **`sigmav_xf` vs `sigmav_total`: synthetic uses which?** If `sigmav_total`, that row needs `audit_status: pending_producer_doc_fix` and a new enum literal in T2. My recommendation: `sigmav_total` + xfail.
4. **`router_contract.schema.json` location: `plugins/shared/schemas/` or `dark-matter-constraints/contracts/`?** My recommendation: contracts/.
5. **T1 merge into T3?** My recommendation: yes.
6. **T2 (self-schema) and T3 (entries) merge?** My recommendation: yes.
7. **T8 fate: drop, slim, or keep?** My recommendation: drop.
8. **T9 owner: opus, sonnet, or split?** My recommendation: opus, 1 cycle, accept gate-replay cost.
9. **Symlink portability: gate or note?** My recommendation: gate (verify resolution from worktree path).
10. **Loose-gate pattern (`wc -l`, `grep -c heading`): replace policy?** My recommendation: every narrative-doc gate replaced with content-token grep, no line floor.
11. **`audit_status` enum: which literals are mandatory in T2?** My recommendation: `verified_against_synthetic`, `schema_pinned`, `documented_but_absent`, `verified_in_writer_skill`, `pending_schema`, `pending_producer_doc_fix`, `pending_producer_topology_fix`. Pin in synthesis §3.
12. **Cycle budget: 12 (drafter) or 7 (this critique's revised plan)?** My recommendation: 7–8.
