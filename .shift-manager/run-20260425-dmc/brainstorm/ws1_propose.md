# WS-1 Proposal — Output-contract verification deliverable

**Author:** proposer agent (3-agent brainstorm)
**Lens:** see `briefs/ROUTING_LENS.md`. Contract = code; audit narrative = doc.

---

## Section 1 — Deliverable shape

### Recommendation: a **two-artifact deliverable** — one machine-checked manifest plus one human-readable audit doc.

**Artifact A (load-bearing, code):**
A JSON contract manifest committed to the repo at:

```
plugins/constraints/skills/dark-matter-constraints/contracts/router_field_map.json
```

paired with an executable contract test at:

```
plugins/constraints/skills/dark-matter-constraints/tests/test_router_field_contract.py
```

The manifest is the single source of truth for "what JSON fields the router reads from each downstream tool, on which observable, with which provenance." It is structured (not prose) so the test can iterate over it.

The test does three things, deterministically and offline:

1. **Manifest ↔ router-SKILL.md sync.** Parse the Step 4 cross-check table out of `dark-matter-constraints/SKILL.md`. Assert every (observable, MadDM-field, micrOMEGAs-field) row in the SKILL.md table appears in the manifest with the same values, and vice versa. If anyone edits the SKILL.md table without updating the manifest (or the reverse), the test fails. This kills silent drift in the router itself.
2. **Manifest ↔ downstream-SKILL.md sync.** For each manifest entry, grep the downstream skill's SKILL.md for the field name. Each manifest entry carries a `defined_in:` pointer (file path + section anchor). The test asserts the field literal occurs at least once in that file (not necessarily at that exact line — line numbers drift). If a downstream skill renames a field without updating the manifest, the test fails.
3. **Manifest ↔ fixture sync.** For each downstream skill that has an output fixture in-repo, the test loads the fixture and asserts the field name is present at the documented path (e.g. top-level key in `summary.json`, or substring match in `MadDM_results.txt` / `stdout.log`). If the fixture changes shape, the test fails.

**Artifact B (narrative, doc):**
A markdown audit report at:

```
.shift-manager/run-20260425-dmc/state/ws1_audit_report.md
```

This is the human-readable audit findings. It explains *why* each field is in the manifest, what drift was found at audit time, what was fixed, and what remains as a known unknown for downstream WS to resolve. This file is not load-bearing for any test — it's for the manager and future humans reading the run history.

### Why this shape, under the routing lens

- **The contract IS code.** Per the lens table: "A contract between tools (field names, schemas, exit codes) → Deterministic helper (code)." A markdown-only deliverable fails the lens — drift can be reintroduced silently the moment WS-4 starts editing SKILL.md. A manifest + test makes drift loudly visible.
- **The audit narrative is a doc.** The *why* (which fields, why these and not others, why we fix the router instead of the downstream) is judgment-laden and not mechanically reproducible. That belongs in markdown.
- **Manifest stays thin.** It does NOT model "what value is correct" or "what the field means physically." It only encodes "this string appears here." That keeps it model-agnostic — the manifest doesn't know whether the value is from MSSM neutralino DM or DMsimp scalar mediator; it only enforces field-name presence.
- **Pure file-existence and string-presence checks.** Same risk class as `check_prereqs` in the lens table — explicitly listed as **safe for code**.

### Why NOT a router-level deterministic Python orchestrator

Already a non-goal per `ROUTING_LENS.md`. The manifest+test does *not* parse downstream output for the router; it only verifies that the strings the LLM-driven router will reach for actually exist where they're claimed to exist. The actual JSON parsing remains LLM-driven (per the lens, because parser shape varies by model class).

### What the manifest looks like (concrete schema)

```json
{
  "schema_version": "router_field_map/v1",
  "router_skill": "plugins/constraints/skills/dark-matter-constraints/SKILL.md",
  "router_table_anchor": "Step 4 — Cross-check via micrOMEGAs",
  "fields": [
    {
      "observable": "Omega_h2",
      "downstream": "maddm",
      "field_name": "Omegah2",
      "defined_in_doc": "plugins/monte-carlo-tools/skills/maddm/SKILL.md#reading-maddm-output",
      "emitted_in_fixture": null,
      "fixture_path": null,
      "presence_check": "json_top_level_key",
      "value_kind": "float|null",
      "audit_status": "documented_no_fixture"
    },
    {
      "observable": "Omega_h2",
      "downstream": "micromegas",
      "field_name": "omega_h2",
      "defined_in_doc": "plugins/constraints/skills/micromegas/SKILL.md#reading-micromegas-output",
      "emitted_in_fixture": "tests/fixtures/stdout_synthetic.txt",
      "fixture_path": "<run_dir>/stdout.log [parsed line: 'Omega h^2 = ...']",
      "presence_check": "stdout_regex",
      "value_kind": "float|null",
      "audit_status": "DRIFT — field NOT in summary.json schema; only in parser narrative"
    },
    ...
  ]
}
```

The `presence_check` enum tells the test how to verify: `json_top_level_key`, `stdout_regex`, `slha_block`, `summary_json_key`, etc.

The `audit_status` enum captures resolution state: `verified`, `documented_no_fixture`, `DRIFT`, `MISSING_DOWNSTREAM_DOCS`, `model_class_dependent`.

---

## Section 2 — Scope: exactly which fields must be verified

The router currently lists 4 observables × 2 sources (MadDM / micrOMEGAs) at lines 136-141 of `dark-matter-constraints/SKILL.md`, plus DRAKE's Ωh² appears prose-only in Step 5. That's the audit scope. **Eight fields total in the cross-check + one DRAKE field + two prereq-related fields = eleven manifest entries.**

### Cross-check table (Step 4)

| # | Observable | Downstream | Router field name | Defined in (claimed) | Real-output check |
|---|------------|-----------|-------------------|----------------------|--------------------|
| 1 | Ωh² | maddm | `Omegah2` | `maddm/SKILL.md` "Reading MadDM output" → JSON example top-level key | Need real `MadDM_results.txt` from a run; verify line `Omegah2 = ...` exists. **No fixture in repo today.** |
| 2 | Ωh² | micromegas | `omega_h2` | `micromegas/SKILL.md` "Reading micrOMEGAs output" — claims this is parsed from stdout, but the documented `summary.json` schema (lines 226-239) does NOT list `omega_h2` as a key. **DRIFT FOUND.** | Real `stdout.log` from a micrOMEGAs run (or use existing `tests/fixtures/stdout_synthetic.txt`); verify regex `Omega h\^2 = ...`. Then **separately** verify whether `summary.json` actually carries `omega_h2` — currently the schema example does not. |
| 3 | σ_SI(p) | maddm | `sigma_si_proton` | `maddm/SKILL.md` JSON example | `MadDM_results.txt`; line `sigma_SI_proton = ...`. **No fixture.** |
| 4 | σ_SI(p) | micromegas | `sigma_si_proton_cm2` | `micromegas/SKILL.md` `summary.json` schema, line 232 | `summary_singletDM.json` fixture confirms presence. **VERIFIED.** |
| 5 | σ_SD(p) | maddm | `sigma_sd_proton` | `maddm/SKILL.md` JSON example | `MadDM_results.txt`; line `sigma_SD_proton = ...`. **No fixture.** |
| 6 | σ_SD(p) | micromegas | `sigma_sd_proton_cm2` | `micromegas/SKILL.md` `summary.json` schema, line 234 | `summary_singletDM.json` fixture confirms presence. **VERIFIED.** |
| 7 | ⟨σv⟩(v→0) | maddm | `sigmav_total` | `maddm/SKILL.md` JSON example | `MadDM_results.txt`; line matching `sigmav_xf = ...` (NB: doc says `sigmav_xf`, JSON example uses `sigmav_total` — **internal MadDM-doc drift**). **No fixture.** |
| 8 | ⟨σv⟩(v→0) | micromegas | `sigma_v_zero` | `micromegas/SKILL.md` "Reading micrOMEGAs output" prose; **NOT in `summary.json` schema example**. **DRIFT FOUND.** | Real `stdout.log`; line `sigma_v(v=0) = ...`. Audit must decide: does `sigma_v_zero` belong in `summary.json` or only in derived report? |

### Step 5 (DRAKE)

| # | Observable | Downstream | Router field | Defined in | Real-output check |
|---|------------|-----------|--------------|------------|-------------------|
| 9 | Ωh² | drake | (router does not name a field — Step 5 just says "collect its Ωh² output") | `drake/SKILL.md` "Reading DRAKE output" emits result dict with key `omega_h2` (lowercase). | DRAKE produces unstructured Wolfram stdout; the lower-case `omega_h2` only appears in the agent-side result dict the LLM is told to construct. **No JSON file is written by DRAKE itself.** Audit must record this and propose either (a) router gets explicit field name `omega_h2` matching DRAKE's emitted dict, or (b) router stays prose and the LLM adjudicates each call. |

### Prereq-related fields (Step 1)

| # | Field | Type | Defined in |
|---|-------|------|-----------|
| 10 | `config.maddm_path` | bool/path | `maddm-install` |
| 11 | `config.drake_path` | path | `drake-install` (read in Step 5 Branch 1/Branch 2) — additionally, `/drake-install detect` `status` enum (`configured` / `found` / `missing`) is read by router Step 5 Branch 2. The enum literals must be in the manifest. |

### Canonical fixture story

There is **NO** in-repo MadDM run-output fixture today. `plugins/monte-carlo-tools/skills/maddm/` has no `tests/fixtures/` directory. This is itself an audit finding. WS-1 must either:
- (a) **Provoke a real MadDM run** on the smallest possible model (DMsimp_s_spin0 is documented in the SKILL and is the lightest path) and commit the resulting `MadDM_results.txt` as a checked-in fixture — yes, this means WS-1 has a small implementation cost; or
- (b) **Hand-craft a synthetic fixture** (matching the format the SKILL.md "Reading MadDM output" section documents) and clearly label it `STRUCTURED FAKE` — exactly the pattern micrOMEGAs already uses at `tests/fixtures/stdout_synthetic.txt`.

I recommend **(b)** for WS-1 specifically, with **(a)** deferred to WS-3 (the dark-SU(3) playtest will produce a real MadDM run anyway, and that run output should retroactively replace the synthetic fixture). Reasons: (i) we don't want WS-1 to block on MG5/MadDM install; (ii) the `STRUCTURED FAKE` pattern already exists and is acceptable to the codebase; (iii) the fixture's only purpose is to verify field-name presence, not numerical correctness — so a labeled synthetic is fit for purpose.

micrOMEGAs has both fixtures already:
- `tests/fixtures/stdout_synthetic.txt` — STRUCTURED FAKE labeled as such.
- `tests/fixtures/summary_singletDM.json` — golden `summary.json`.

DRAKE has no skill-level fixture (only `drake-install` does). Recommend WS-1 add a synthetic `tests/fixtures/stdout_drake_synthetic.txt` mimicking the WIMP smoke-test stdout shape; same labeling pattern.

### Out of scope for WS-1

- **Numerical correctness** of any value. The audit verifies field *names*, not values.
- **Schema for the router's merged output**. That is WS-4 territory once the inputs are pinned down.
- **Newly invented fields**. If the router currently doesn't reach for a field, WS-1 doesn't add one. WS-4 may.
- **Cross-validating Step 3 spectrum-analysis fields** (mass spectrum, mediator masses). Those come from SLHA / param_card, not from MadDM/μΩ/DRAKE JSON. Different contract; out of WS-1.

---

## Section 3 — Drift policy

When the audit finds a mismatch, three sub-cases. Decision rules:

### 3a. Router names a field that does not match downstream docs

**Default: fix the router.** The downstream skill is upstream of the router in the dependency graph (the router is the *consumer*). If a downstream tool documents `omega_h2_planck` and the router reads `Omega_h2_target`, the router is reading the wrong name — period. The fix is in the router.

Exception: if the router's name is *more conventional / clearer* and the downstream docs are sloppy, propose renaming the downstream emission too. But this is a discussion, not a unilateral edit. The audit report (Artifact B) flags it as `RENAME_DISCUSSION_NEEDED` and the manager decides.

Concretely, the audit found two cases of this class:
- (i) micrOMEGAs `summary.json` schema does NOT contain `omega_h2` or `sigma_v_zero`, but the router reads them. **Fix:** either add these keys to `micromegas/SKILL.md`'s `summary.json` schema (preferred — they're naturally part of "scattering+relic" output), or downgrade the router to read from `stdout.log` regex (worse — invites parse drift). Recommend the former; flag for WS-4 to action.
- (ii) DRAKE: router doesn't name a field, downstream `omega_h2` exists only in agent-emitted dict. **Fix:** router's Step 5 paragraph should explicitly name `omega_h2` to mirror MadDM's `Omegah2` and micrOMEGAs's `omega_h2` — making cross-tool comparison mechanically expressible.

### 3b. Field documented but absent from real run output

**Blocker for that field's row in the router's cross-check table, recoverable for the run as a whole.** If MadDM docs say `sigmav_total` but real `MadDM_results.txt` does not contain that string, then the router cannot reliably populate that column of its cross-check table. Three actions in order:
1. Audit doc records `DOCUMENTED_BUT_ABSENT` with the exact MadDM version that was checked.
2. Manifest entry's `audit_status` becomes `documented_but_absent`.
3. Test asserts the row is gated — either the field IS present in fixture, or the manifest must explicitly mark it `version_dependent_optional` and the router's cross-check table must mark that row "—" (already the convention for missing values per SKILL.md line 145).

Not a fatal blocker for the *router's* operation. The router already has `null` semantics. But it IS a fatal blocker for shipping WS-1 as "verified" — at minimum, the audit report calls it out for WS-4 to handle by either updating downstream docs to drop the claim, or upgrading the router to handle the absence explicitly.

### 3c. Field present in real run output but not documented

**Require docs update before adding to manifest.** If `MadDM_results.txt` contains `Omegah2_eff = ...` and no SKILL.md mentions it, the router does not silently accept it — the manifest only encodes documented fields. The audit report flags `UNDOCUMENTED_OUTPUT_FIELD` so downstream WS or maintainers can decide whether to (a) document it (move to manifest) or (b) intentionally ignore it.

This is the conservative policy. Reason: the routing lens emphasizes that helpers must be model-agnostic, and an undocumented field could be a model-class-specific artifact (e.g. an MSSM-only block). Pulling it into the contract without docs cementing its model-agnostic semantics risks WS-4 building helpers that quietly fail for other models.

---

## Section 4 — Model-agnosticism check

**Hard answer: I cannot guarantee model-agnosticism for ANY of the eight cross-check fields from documentation alone. This is itself an audit finding.**

What the docs say vs what they *don't* say:

- **MadDM `Omegah2`** — documented in `maddm/SKILL.md` as a single top-level key in the JSON the agent emits after parsing `MadDM_results.txt`. The MadDM SKILL.md does NOT distinguish output shape between MSSM (full SLHA) vs simplified-UFO (param_card) runs. The format may be stable across model classes — MadDM 3.2 does write `Omegah2 = <value>` in `MadDM_results.txt` regardless of how masses were sourced — but I cannot prove this from the docs. The router's `dark-matter-constraints/SKILL.md` Step 1 explicitly handles MSSM-vs-simplified asymmetry for the spectrum input (`latest_slha` required for MSSM-class only), which suggests the maintainers know the input side bifurcates by model class. Whether the *output* side bifurcates is unstated. **WS-1 audit finding: docs don't certify model-agnosticism of MadDM output schema.**
- **MadDM cross-section fields** (`sigma_si_proton`, `sigma_sd_proton`, `sigmav_total`) — same caveat. Additionally, DD output requires `direct_detection = ON` in `maddm_card.dat`; for relic-only runs these will be `null`. The router already handles this with `—` semantics, but the manifest must mark these `optional_per_observable`.
- **micrOMEGAs `summary.json` schema** — explicitly versioned (`scattering/v1`) per `micromegas/SKILL.md` line 227. Schema versioning is a model-agnosticism PROOF — the contract is pinned. But the missing `omega_h2` and `sigma_v_zero` (audit finding 3a above) means the schema doesn't currently cover the full router cross-check; that gap must be closed before model-agnosticism can be claimed.
- **micrOMEGAs subcommand-specific schemas** — `relic`, `scatter`, `annihilate`, `indirect` likely emit different `summary.json` shapes (`relic` vs `scatter` need different fields). The SKILL.md only shows one schema example. **WS-1 audit finding: per-subcommand `summary.json` schemas need to be enumerated. The router reads from up to four micrOMEGAs subcommands and assumes the same field naming conventions apply across them.**
- **DRAKE** — no JSON contract at all; the agent constructs the result dict from unstructured Wolfram stdout. This is *less* model-agnostic in the worst sense: every BSM model the user brings could produce different stdout patterns from DRAKE, and the router's "comparison" is heuristic at best. The lens explicitly flags this (DRAKE result emission is LLM-side, not deterministic). The audit can confirm only that `omega_h2` is the *intended* key in the agent-emitted dict — not that any deterministic helper can extract it.

### What the audit's deliverable tells WS-4

WS-4 should make these **deterministic helpers**:

- `verify_router_field_contract()` — runs the manifest test (Section 1, Artifact A). Pure I/O + string match. Safe for code.
- `check_summary_json_schema_version(path, expected_version)` — for micrOMEGAs `summary.json`, asserts `schema_version == "scattering/v1"` (or future versions). Safe for code.
- `extract_field(json_path, key, default=None)` — flat top-level key extraction with `null` semantics. Safe for code IFF schema is versioned (so `null` means "absent" not "not yet implemented for this model").

WS-4 should keep these in **LLM**:

- `read_maddm_output()` — until the fixture story (Section 2) is closed and we can prove field names are stable across MSSM/simplified/multi-component model classes, this stays LLM. The lens explicitly listed this as risk-of-non-agnostic.
- `read_drake_output()` — DRAKE produces unstructured Wolfram stdout. No contract to enforce. LLM territory.
- `compare_dm()` (the actual numerical comparison logic) — only safe for code IF the canonical schema accommodates all observables; the audit's own evidence (multi-component DM, MSSM full SLHA) is that it doesn't, today. So `compare_dm` accepts a manifest-validated dict and computes rel-diff only for the rows the manifest says exist. The "which rows exist" stays LLM-driven; the "compute rel-diff" can be code.

This is the bridge from WS-1's deliverable to WS-4's helper boundary.

---

## Section 5 — Risks / unknowns

Things that may bite WS-1 implementation; flag for the critic.

1. **MadDM emits no JSON natively.** The "JSON" the router reads is constructed by the calling agent after parsing `MadDM_results.txt` (per `maddm/SKILL.md` line 168 onward). So the router-MadDM contract is technically a contract between the router and *the LLM-agent's parsing of MadDM*, not between the router and MadDM itself. This is upstream of the audit but bears on it: if WS-4 ever moves the MadDM parser to a deterministic helper, the contract changes shape entirely. WS-1 should record this as `contract_topology_pending`.

2. **Internal MadDM doc drift exists already.** `maddm/SKILL.md` line 165 says "line matching `sigmav_xf = <value>`"; line 176 (the JSON example) says `sigmav_total`. These do not match. The router uses `sigmav_total`. Audit must reconcile.

3. **Capitalization sensitivity.** Field names mix conventions: MadDM `Omegah2` (camel, no underscore) vs micrOMEGAs `omega_h2` (snake) vs DRAKE agent-dict `omega_h2`. The router cross-check table must dispatch by string-equality, not case-insensitive — that's what makes drift detectable. The manifest test must be case-strict.

4. **Per-subcommand schema variance for micrOMEGAs.** `relic`, `scatter`, `annihilate`, `indirect` likely emit different `summary.json` keys. The skill SKILL.md only documents one schema. WS-1 should enumerate by sub-command — and may discover documented gaps in the process. Risk: the audit balloons in scope when this is unrolled.

5. **DRAKE has no JSON output and no in-repo fixture.** The contract here is fundamentally weaker than for the other two tools. The audit must explicitly state this rather than paper over it. WS-1's deliverable should NOT pretend there's a DRAKE contract on par with MadDM/micrOMEGAs.

6. **Router's Step 5 narrative does not name a DRAKE field.** Audit finding noted in Section 2. The fix (giving DRAKE comparisons an explicit field name `omega_h2`) is small but nontrivial — it changes router prose and will need WS-4 attention.

7. **Manifest schema versioning.** The manifest itself needs `schema_version: "router_field_map/v1"`. If WS-4 changes shape, the manifest version must bump in lockstep. Risk: future WS forget to bump.

8. **The cross-check table at lines 136-141 is markdown.** Parsing it for the test (Section 1, sync check #1) requires a stable parse. Acceptable approach: anchor on the literal heading `### Step 4 — Cross-check via micrOMEGAs` and walk to the next horizontal rule. Risk: anyone reformatting Step 4's prose breaks the test parser. Mitigation: the test should fail with a clear message ("could not locate Step 4 cross-check table — has the heading been renamed?") rather than silently miss rows.

9. **Fixture provenance.** Synthetic fixtures committed today might be replaced by real-run fixtures in WS-3. If WS-1's manifest test is keyed on synthetic field positions ("must appear at byte offset X"), it'll break. Mitigation: the test does string-presence matching only, not positional matching.

10. **Configurability of MadDM output filename.** `maddm/SKILL.md` line 156 says results are at `<out_dir>/output/run_01/MadDM_results.txt`. The `run_01` is automatic; downstream runs become `run_02`, etc. The audit must verify the manifest never hardcodes `run_01` — it's the `MadDM_results.txt` basename that's stable, not the directory name.

11. **micrOMEGAs `omega_h2` field potentially being added later.** Section 3a's recommended fix is to add `omega_h2` and `sigma_v_zero` to the documented `summary.json` schema. If WS-4 implements this fix, the manifest should anticipate it — perhaps by marking those entries `pending_schema_update` in the audit report and `documented_in_skill_md_prose_only` in the manifest. WS-4 then closes the loop.

12. **The audit may surface drift the team disagrees on.** E.g. someone may push back: "the router shouldn't read from `summary.json`; it should read from `stdout.log`." That's a legitimate design discussion but is OUT of scope for WS-1, which only documents the current state. Audit must not silently make the call. Flag every such case as `DESIGN_DECISION_NEEDED` and let the manager triage.

---

## Appendix — proposed file layout

```
plugins/constraints/skills/dark-matter-constraints/
├── SKILL.md                                            (existing; minor edits in WS-4)
├── contracts/
│   └── router_field_map.json                           (NEW — WS-1)
└── tests/
    ├── __init__.py                                     (NEW)
    └── test_router_field_contract.py                   (NEW — WS-1)

plugins/monte-carlo-tools/skills/maddm/
└── tests/
    └── fixtures/
        └── MadDM_results_synthetic.txt                 (NEW — WS-1, STRUCTURED FAKE)

plugins/monte-carlo-tools/skills/drake/
└── tests/
    └── fixtures/
        └── stdout_drake_synthetic.txt                  (NEW — WS-1, STRUCTURED FAKE)

plugins/constraints/skills/micromegas/
└── tests/fixtures/                                     (existing, no changes needed)

.shift-manager/run-20260425-dmc/state/
└── ws1_audit_report.md                                 (NEW — WS-1, narrative)
```

Total new files: 5 (one JSON manifest, one Python test, two synthetic fixtures, one audit doc). No edits to downstream SKILL.md content in WS-1 itself — those edits are flagged for WS-4.
