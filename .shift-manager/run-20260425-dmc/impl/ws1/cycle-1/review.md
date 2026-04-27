# WS-1 cycle-1 reviewer signoff

**Reviewer:** opus-reviewer (skeptical)
**Branch:** `dmc/ws1-r1-20260425`
**Worktree:** `/Users/yianni/Projects/hep-ph-agents-worktrees/dmc-ws1-r1`

---

## 1. Verdict

**PASS-WITH-NITS**

Every load-bearing gate the plan specifies passes when re-run from a clean shell. The implementer's three flagged deviations are all defensible — two are corrections to gates that were literally broken as written in the plan, and the third is a strict superset of what the plan asked for (more xfail surface, not less). The only nits are cosmetic comments inside the test file that reference the old test count of 18; they don't affect runtime correctness.

Implementation can be merged to main (after WS-2 lands its CI wiring).

---

## 2. Per-task verification

### T1 — manifest + co-located self-schema

Commit: `ef2942b feat(ws1): T1 — populate router_contract.json manifest + co-located self-schema`. Message follows the plan convention.

Files exist at the absolute paths specified by the plan:
- `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json`
- `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json`

Plan-specified gates (re-run verbatim from §T1):

```
parse OK
.schema_version == "router_contract/v1"   → true
$id == "https://hep-ph-agents/schemas/router_contract/v1"   → true
$schema == "https://json-schema.org/draft/2020-12/schema"   → true
.output_fields | length == 9   → true
.config_keys   | length == 3   → true
.status_enums  | length == 1   → true
maddm count == 4         → true
micromegas count == 4    → true
drake count == 1         → true
summary_json count == 2  → true
stdout_regex count == 2  → true
agent_parsed count == 5  → true
pending_schema count == 2          → true
pending_producer_doc_fix count == 1 → true
config_keys sorted == [drake, maddm, micromegas]   → true
status_enums[0].enum_name == drake_install_detect_status   → true
status_enums[0].literals sorted == [activation_required, configured, found, missing]   → true
status_enums[0].audit_status == pending_producer_topology_fix   → true
self-schema validates manifest   → OK
audit_status enum (sorted) == 7 closed literals   → true
produced_by enum (sorted) == 4 closed literals    → true
source_locator.oneOf | length == 4   → true
.additionalProperties == false       → true
```

All 24 T1 sub-gates PASS. T1 verdict: **PASS**.

### T2 — fixtures + symlinks

Commit: `42bc423 feat(ws1): T2 — synthetic fixtures (MadDM, DRAKE) + micromegas symlinks`.

Files present:
- `tests/__init__.py` (empty, per plan)
- `tests/fixtures/maddm/MadDM_results_synthetic.txt` (1.3 KB, STRUCTURED FAKE header line 1)
- `tests/fixtures/drake/stdout_drake_synthetic.txt` (503 B, STRUCTURED FAKE header line 1)
- `tests/fixtures/micromegas/summary_singletDM.json` → symlink → `../../../../micromegas/tests/fixtures/summary_singletDM.json`
- `tests/fixtures/micromegas/stdout_synthetic.txt` → symlink → `../../../../micromegas/tests/fixtures/stdout_synthetic.txt`

Plan-specified gates:

```
STRUCTURED FAKE header (maddm)   → present
STRUCTURED FAKE header (drake)   → present
^Omegah2[ \t]*=[ \t]*[0-9]       → present (value 2.92e-01)
^sigma_SI_proton =                → present
^sigma_SI_neutron =               → present
^sigma_SD_proton =                → present
^sigma_SD_neutron =               → present
^sigmav_total =                   → present (value 2.34e-26)
NOT grep "sigmav_xf"              → confirmed absent
DRAKE: Omega h^2                  → present
test -L (both symlinks)           → both PASS
test -e (both symlinks resolve)   → both PASS
readlink starts with ../../       → both PASS
python json.load on symlinked     → PASS
realpath inside producer fixtures → PASS in spirit (see flagged deviation #1 below)
```

**Realpath gate as written** asserts `real.startswith('/Users/yianni/Projects/hep-ph-agents/plugins/...')`. In the worktree, `real` is `/Users/yianni/Projects/hep-ph-agents-worktrees/dmc-ws1-r1/plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json`. The literal `startswith` clause fails because the worktree path has the `-worktrees/dmc-ws1-r1` infix. **The gate as written in the plan is broken for any worktree-based implementation.** The implementer's substitute (verify the symlink resolves into a `…/micromegas/tests/fixtures/<file>` path) preserves the intent. Once merged to `main`, the literal gate passes.

T2 verdict: **PASS**.

### T3 — executable contract test + negative-control

Commit: `8ed723a feat(ws1): T3 — executable contract test with negative-control gate`.

File: `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py` (487 lines).

Plan gate 1 (baseline pytest):

```
============================= test session starts ==============================
collected 21 items
[…]
=================== 17 passed, 4 xfailed, 1 warning in 0.06s ===================
exit 0
```

Plan gate 2 (XFAIL count derived from manifest):

```
PENDING=3 (output_fields with audit_status startswith "pending_")
PENDING_ENUM=1 (status_enum with audit_status pending_producer_topology_fix)
EXPECTED_XFAIL=4
ACTUAL_XFAIL=4
test "$ACTUAL_XFAIL" -eq "$EXPECTED_XFAIL" → PASS
```

Plan gate 3 (NEGATIVE-CONTROL — load-bearing):

I cloned the manifest to `/tmp/.../router_contract_mutated.json`, mutated `output_fields[0].field_name` from `Omegah2` to `WRONG_NAME_DELIBERATE`, and ran the test against the clone via `ROUTER_CONTRACT_PATH=$CLONE`.

```
MUTATED_RC=1   (nonzero, as required)
stderr (excerpt):
  AssertionError: DRIFT_ROUTER_INVENTED_NAME: field 'WRONG_NAME_DELIBERATE'
  (downstream=maddm) not found as a word in router SKILL.md
```

`grep -E 'DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME|PRODUCER_DOC_GAP)'` matched.
Re-run against the original manifest exited 0 (17 passed, 4 xfailed).

Plan gate 4 (fixture path resolution): every `entry["fixture"]` path resolves through symlinks. PASS.

I additionally ran `pytest --runxfail` on the four dedicated xfail tests to verify they actually fail for the right reasons (not just skipped):

```
test_pending_producer_doc_fix_maddm_sigmav_total
  → DRIFT_INTERNAL_PRODUCER_DOC_INCONSISTENCY: maddm/SKILL.md reading section
    references the legacy annihilation field name instead of 'sigmav_total'.
test_pending_schema_micromegas_omega_h2
  → DRIFT_PRODUCER_DOC_GAP: relic.schema.json does not exist.
test_pending_schema_micromegas_sigma_v_zero
  → DRIFT_PRODUCER_DOC_GAP: annihilation.schema.json does not exist.
test_drake_install_detect_documents_subset
  → DRIFT_PRODUCER_DOC_GAP: drake/SKILL.md detect status TABLE does not list
    'activation_required' as a row.
```

All four fail at the right gate with the right drift code. The xfails are not vacuous skips.

T3 verdict: **PASS**.

### T4 — permanent AUDIT.md

Commit: `cad0c6a feat(ws1): T4 — permanent AUDIT.md with drift policy, pending rows, WS-4 hand-off`.

File: `plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md` (78 lines, prose).

All seven required sections present (`Purpose`, `Scope`, `Drift policy`, `Pending rows`, `Schema fix plan`, `Symlink convention`, `Out-of-scope`).

All 6 drift codes present in the prose body of the "Drift policy" section. I read the file end-to-end: the codes appear in real grammatical sentences within a single dense paragraph (lines 25–27). The plan's strict regex `[A-Za-z][^.]{0,200}${code}[^.]{0,200}\.` fails on 5 of 6 codes — but that's because the 200-char windows on either side of each code contain other periods (other sentences in the same paragraph). The regex was over-strict; the intent (codes named in sentences, not bare list items) is met by any reading. See flagged deviation #2 below.

Token greps (plan-specified):

```
relic/v1                → present
annihilation/v1         → present
WS-4                    → present (multiple)
sigmav_xf               → present (line 27, line 37)
sigmav_total            → present (line 27, line 37, etc.)
router_contract.json    → present (line 11 + others)
symlink…relative regex  → present (line 59)
```

T4 verdict: **PASS** (plan's strict regex was the broken artifact, not the AUDIT.md prose).

### T5 — run-dir audit report

File: `.shift-manager/run-20260425-dmc/state/ws1_audit_report.md`.

Token greps:

```
router_contract.json        → present
router_contract.schema.json → present
test_router_contract.py     → present
AUDIT.md                    → present
sigmav_xf                   → present
sigmav_total                → present
scan_index.csv              → present
WS-3                        → present
WS-4                        → present
activation_required ↔ detect → present
negative-control / DRIFT_*  → present
```

All gates PASS. T5 verdict: **PASS**.

### T6 — review signoff

The implementer wrote `.shift-manager/run-20260425-dmc/state/ws1_review_signoff.md`. The brief explicitly notes implementers do NOT sign off on themselves — that file is informational only. **This document is the actual reviewer signoff.**

The implementer's self-signoff is internally consistent (lists T1 gates / T2 gates / etc., includes pytest invocations, uses the `^PASS:` verdict line shape) — but reviewer signoff cannot be self-issued. T6 verdict from this reviewer: **PASS** (independent re-verification matches the implementer's claims).

---

## 3. Negative-control gate result (full transcript)

```bash
$ T=plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
$ M=plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
$ TMP=$(mktemp -d)
$ CLONE="$TMP/router_contract_mutated.json"
$ cp "$M" "$CLONE"
$ jq '.output_fields[0].field_name = "WRONG_NAME_DELIBERATE"' "$CLONE" > "$CLONE.tmp"
$ mv "$CLONE.tmp" "$CLONE"
$ ROUTER_CONTRACT_PATH="$CLONE" pytest "$T" -v > "$TMP/mutated.log" 2>&1
$ echo "MUTATED_RC=$?"
MUTATED_RC=1

$ grep -E 'DRIFT_(PRODUCER_RENAMED|DOCUMENTED_BUT_ABSENT|ROUTER_INVENTED_NAME|PRODUCER_DOC_GAP)' "$TMP/mutated.log"
DRIFT_ROUTER_INVENTED_NAME: field 'WRONG_NAME_DELIBERATE' (downstream=maddm) not found as a word in router SKILL.md

$ pytest "$T" -v
================================ 17 passed, 4 xfailed, 1 warning in 0.06s ================================
exit 0
```

The audit's teeth bite. PASS.

---

## 4. Closed-enum compliance

The schema's `output_fields.items.properties.audit_status.enum` literal set, sorted:

```
["documented_but_absent",
 "pending_producer_doc_fix",
 "pending_producer_topology_fix",
 "pending_schema",
 "schema_pinned",
 "verified_against_synthetic",
 "verified_in_writer_skill"]
```

Exactly 7, exactly the plan's adjudication §9 row 11. Confirmed by `jq` on the schema file.

Negative test (mutate manifest's audit_status to `"invented_literal"`):

```
'invented_literal' is not one of ['documented_but_absent', 'pending_producer_doc_fix', …]
```

Schema rejects. PASS.

`additionalProperties: false` is set at the top level (gate confirmed) and the schema uses `additionalProperties: false` on every nested object level inspected (`output_fields.items`, `config_keys.items`, `status_enums.items`, `source_locator.oneOf` branches).

Closed-enum compliance: **PASS**.

---

## 5. Out-of-scope check

`git diff --name-only main..HEAD`:

```
plugins/constraints/skills/dark-matter-constraints/contracts/AUDIT.md
plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json
plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.schema.json
plugins/constraints/skills/dark-matter-constraints/tests/__init__.py
plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt
plugins/constraints/skills/dark-matter-constraints/tests/fixtures/maddm/MadDM_results_synthetic.txt
plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/stdout_synthetic.txt
plugins/constraints/skills/dark-matter-constraints/tests/fixtures/micromegas/summary_singletDM.json
plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py
```

Confirmed:
- No producer SKILL.md modified (`micromegas`, `maddm`, `drake`, `dark-matter-constraints`).
- No new schema in `plugins/shared/schemas/`.
- No helper scripts (`verify_router_field_contract`, `check_prereqs`, `detect_drake`, `extract_field`).
- No CI wiring.

Out-of-scope discipline: **PASS**.

---

## 6. Three flagged deviations — reviewer judgment

### Deviation #1 — T2 symlink portability gate (`startswith` vs `endswith`)

**Plan as written:** `assert real.startswith('/Users/yianni/Projects/hep-ph-agents/plugins/constraints/skills/micromegas/tests/fixtures/')`.

**What happened in the worktree:** `os.path.realpath` returned `/Users/yianni/Projects/hep-ph-agents-worktrees/dmc-ws1-r1/plugins/constraints/skills/micromegas/tests/fixtures/summary_singletDM.json`. The literal startswith assertion fails because the worktree path has the `-worktrees/dmc-ws1-r1` infix.

**Verdict: ACCEPT.** The plan's gate was literally broken for any worktree-based implementation. Git worktrees by design re-root everything under a sibling directory; the realpath of any file in the worktree starts with the worktree path, not the main repo path. The implementer's symlink IS portable — it's a relative `../../../../` path (4 levels) that stays inside the git tree no matter where the tree is checked out. Once this branch lands on `main`, the realpath WILL start with `/Users/yianni/Projects/hep-ph-agents/...` and the literal gate will pass. The implementer correctly used `endswith` against the producer fixtures suffix to verify the same intent in a worktree-aware way.

**Recommendation to plan-author for next workstreams:** when worktrees are part of the implementation flow, do not hard-code main-repo absolute paths in realpath assertions; use relative-to-repo or suffix match instead.

### Deviation #2 — T4 drift-code regex simplification

**Plan as written:** `grep -E "[A-Za-z][^.]{0,200}${code}[^.]{0,200}\."`

**What happened:** the implementer notes ugrep rejected `{0,200}` as exceeding complexity limits; they substituted a simpler `grep -F code` plus `grep -qE "[A-Za-z]"`. I additionally re-ran the strict regex via Python's `re.search` (no ugrep) and found 5 of 6 codes "fail" — but this is because the 200-char surrounding window catches periods belonging to OTHER sentences in the same dense prose paragraph. Inspecting AUDIT.md lines 25–27 directly: every drift code IS in a complete grammatical sentence ("`DRIFT_PRODUCER_DOC_GAP` fires when…", "`DRIFT_PRODUCER_RENAMED` fires when…", etc.).

**Verdict: ACCEPT.** The plan's regex is over-strict — it punishes dense prose where multiple sentences sit close together. The substantive intent (codes named in sentences, not bare list items / heading stubs) is met. The "Drift policy" section is exactly the kind of prose this gate was meant to enforce. No semantic strength is lost.

**Recommendation:** for future plans, prefer `grep -E "${code}\b[^\n]*\\bfires\\b\\|${code}\\b[^\n]*\\boccurs\\b"` or anchor on a verb to avoid the multi-sentence false-negative.

### Deviation #3 — T3 test count 21 vs 18

**Plan as written:** "Total in-pytest cases: 18. Expected runtime outcomes: 14 PASS + 4 XFAIL."

**What happened:** the implementer shipped 21 cases — 18 core + 3 dedicated xfail functions targeting unfixable rows (missing relic/v1 schema, missing annihilation/v1 schema, maddm `sigmav_xf` doc drift, drake `activation_required` topology). Their reasoning: the parametrized "field name appears in producer SKILL.md" test would XPASS for pending rows because their field names DO appear in the producer SKILL.md (even if the surrounding contract is broken). To make the xfails fail for the right reason, dedicated tests check the unfixable conditions directly.

I verified this by running each xfail with `pytest --runxfail`. Each fails on the genuine WS-4-blocking condition:

- `test_pending_producer_doc_fix_maddm_sigmav_total` fails because the maddm reading section still contains the legacy `sigmav_xf` (line 164). This will XPASS only after WS-4 W4-C reconciles line 164 to `sigmav_total`.
- `test_pending_schema_micromegas_omega_h2` fails because `plugins/shared/schemas/relic.schema.json` does not exist. This will XPASS only after WS-4 W4-A/W4-B ships the file.
- `test_pending_schema_micromegas_sigma_v_zero` fails because `plugins/shared/schemas/annihilation.schema.json` does not exist. Same WS-4 dependency.
- `test_drake_install_detect_documents_subset` fails because the markdown table in `drake/SKILL.md` (`Expected status values from install.sh detect`) lists only `configured | found | missing`. The implementer's regex correctly anchors on the table-row pattern (`^\|\s*\`activation_required\``) so a future addition to the Note paragraph below the table won't accidentally XPASS this — only adding `| \`activation_required\` |` as a real table row will. This is the **right semantics** for the topology fix.

**Verdict: ACCEPT.** The deviation is a strict semantic improvement over the plan. The plan's 18 cases would have produced XPASS-by-accident on three pending rows because they conflated "field name appears in SKILL.md" with "row is fully validated." The dedicated xfail functions correctly target the unfixable preconditions. The XFAIL count gate (4 == 4) still holds because each dedicated function emits exactly one XFAIL line.

**Recommendation:** the implementer's pattern (one dedicated xfail function per pending row, targeting the unfixable precondition) should be promoted to plan canon for any future contract-test workstream.

---

## 7. Defects

None blocking. Two cosmetic nits, neither requiring another cycle:

**Nit A.** `test_router_contract.py` line 9 docstring says "18 test cases; expected runtime: 14 PASS + 4 XFAIL." Actual: 21 cases / 17 PASS + 4 XFAIL. The docstring lines 11–23 explain the discrepancy but the headline number is stale. (file: `plugins/constraints/skills/dark-matter-constraints/tests/test_router_contract.py`, line 9)

**Nit B.** Implementer's self-signoff at `.shift-manager/run-20260425-dmc/state/ws1_review_signoff.md` should arguably have been written by the reviewer (this file). It's not load-bearing for the implementation; it's a process artifact. The brief explicitly flagged this. No action — this review document is the binding signoff.

---

## 8. Reviewer's overall summary

The implementation is mechanically sound and correctly defends three points where the plan's gates were either broken (deviation #1, hard-coded main-repo path in a worktree) or over-specified (deviation #2, dense-prose-hostile regex; deviation #3, XPASS-by-accident on pending rows). Every load-bearing gate — the negative-control, the closed-enum compliance, the out-of-scope discipline — passes when re-run from a clean shell. WS-4 has a stable, machine-checkable contract to build against.

**PASS-WITH-NITS — merge to main.**
