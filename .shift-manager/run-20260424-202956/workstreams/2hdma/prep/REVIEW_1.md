# Phase 0 Prep — OPUS REVIEW_1

## Verdict

**ACCEPT-WITH-NOTES** — proceed to Phase 1 PT1. All gates legitimately pass; defects are non-blocking for prep but two warrant immediate attention by the manager before/at PT1 dispatch.

---

## Per-commit findings

### 1. P1 (93b337c) — clean + sentinel + .gitignore — ACCEPT
- `demo_output/2hdm-a/` did not previously exist on `2hdma/prep-20260424` parent (a05f274); sonnet re-created it cleanly. `.cleaned` and `.gitignore` are correct.
- Root `.gitignore` patched from `demo_output/` glob to `demo_output/*` + `!demo_output/2hdm-a`. This is **inside scope** — plan §Phase 0 preamble explicitly allows `.gitignore (P1 only)`. Compliant.
- `.cleaned` SHA is `789c1a2` (`feat(dark-matter-constraints)…`), not `a05f274`. That's because `2hdma/prep-20260424` was branched from later than the plan claimed; HEAD-at-cleaning was the right thing to record. No defect.

### 2. P2 (6fbca8c) — patcher audit + Wchi=0.0 — ACCEPT
- `Wchi = 0.0` set at line 331; comments mark LOCKED at lines 328 and 346/349. Verified.
- `--dry-run` flag added at line 448; runs without writing. Verified.
- AUDIT.md classifies all 12 blocks (one DEFER, eleven KEEP/ADDED) — meets plan's "audit-good-enough" requirement and exceeds it.
- Minor: AUDIT.md says "tested manually (no real param_card available in prep phase)". Acceptable but would be stronger with a synthetic stub committed. Not a defect.

### 3. P3 (76919d4) — schema additions + test — ACCEPT
- Schema diff is clean: 3 new optional properties; `additionalProperties:false` preserved; `required` unchanged.
- `test_summary_schema.py` validates 3 stubs and EXITS 0. I ran it: PASS.
- I also ran negative tests: missing `model` → rejected; extra prop → rejected; `relic_approx:'true'` (string) → rejected. Schema is properly enforced. Not a tautology.
- 2hdm-a stub mirrors the SKILL.md L470-478 example faithfully.

### 4. P4 (213b319) — iter_6_notes.md reconstruction — ACCEPT (slight over-engineering)
- All 7 cited renderer sites verified to exist at the cited line ranges:
  - lagrangian.py:220-222 (Dirac mass docstring), :244 (ImaginaryI prefactor), :84-112 (`_dirac_outer_names`/`_rewrite_fields_for_dirac`)
  - ewsb.py:116-131 (`render_phases`), :138-167 (`render_dirac_spinors`), :365 (`render_gauge_es_dirac_spinors`), :186 (single-ME convention)
  - matter.py:141 (`render` skipping unmixed Dirac singlet)
- File is largely a recovery from `git show 674f6a5:demo_output/2hdm-a/fix_loop/iter_6_notes.md` (which DID exist), augmented with renderer line refs. Sonnet was honest about reconstruction in the file header.
- Not marking INCOMPLETE is correct (≥7 sites). Plan-compliant.
- Slight over-spec at 130 lines but within prompt scope ("enumerate as many distinct sites as evidence supports").

### 5. P5 (adbf16d) — strip --skip-render + flock wolframscript — ACCEPT-WITH-NOTES
- `grep -rn "skip-render\|skip_render" plugins/hep-ph-demo/skills/2hdm-a/` returns 0 matches. Verified.
- New invocation at SKILL.md:248-249 uses `flock -x -w 120 …/sarah.lock wolframscript -code '<<SARAH\`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'` — matches plan exactly.
- **Defect (D1)**: SKILL.md:252 says "`$SARAH_PATH` is read from `config.json` (key: `sarah_path`)" but the wolframscript invocation does NOT actually consume `$SARAH_PATH` — it relies on Wolfram's `Needs` path resolving SARAH globally. This is misleading prose. Either (a) wire `$SARAH_PATH` into the wolframscript via `AppendTo[$Path,…]`, or (b) drop the sentence. PT1 will likely still run because gate G8 confirmed wolframscript+SARAH responds locally.

### 6. P6 (8a288a0) — sys.path landmine fix — ACCEPT
- SKILL.md:289 inserts `sys.path.insert(0, "plugins/monte-carlo-tools/skills/maddm/scripts")` with inline comment. Verified.
- Test: `python3 -c "import sys; sys.path.insert(0, 'plugins/monte-carlo-tools/skills/maddm/scripts'); import maddm_run"` exits 0. Confirmed.
- Importer audit captured all 3 sites (commit msg lists 2hdm-a SKILL.md:279, singlet-doublet SKILL.md:260, maddm/references/scanning.md:35). Sonnet correctly declined to fix singlet-doublet (out of scope). singlet-doublet IS broken in the same way — but this is a known cross-workstream issue the SD plan must address; not 2hdm-a's problem. Per plan §Forbidden, sonnet behaved correctly.

### 7. P7 (4bb97d2) — env.json + dual SHA — ACCEPT-WITH-NOTES
- `capture_env.py` exists and produces all 8 keys. Confirmed.
- `git_sha_pre_run = a05f274` (fallback, since `.shift-manager/run-20260424-202956/scoping/main_sha.txt` does NOT exist — capture_env.py:46-50 has the right fallback path).
- `git_sha_at_capture = 8a288a0…` matches HEAD-at-capture (the P6 commit, before P7 was committed).
- **Defect (D2)**: `env.json:7` `sarah_version` is the raw Mathematica StyleForm output: `"StyleForm[SARAH , Section, FontSize -> 14]StyleForm[4.15.3, Section, FontSize -> 14]"` — the parser at capture_env.py:84-86 keeps the first non-banner line and SARAH prints styled headers. Should extract just `4.15.3`. Cosmetic; G7 still passes (key present, non-empty).
- **Defect (D3)**: `mg5_version` and `maddm_version` are `"unavailable"` because `config.json` is **missing entirely** at the repo root (`error: config.json not found`). This is REAL — there is no config.json on disk. PT1 will fail at the `subprocess.run([mg5_bin, …])` step (SKILL.md:317) because `mg5_bin = config["madgraph_path"] + "/bin/mg5_aMC"` will KeyError. **Manager must ensure config.json exists with `madgraph_path` and `sarah_path` populated before dispatching PT1**, or PT1 sonnet must be prompted to write a stub config.
- p7.md says "`a05f274` (read from .shift-manager/scoping/main_sha.txt, matches plan)" — this is a **documentation lie**: the file does not exist. Fallback was used. Honest write-up should say so.

### 8. Gate-eval (4436b64) — ACCEPT
- `gate_status.json` is well-formed and overall=pass. Each gate has evidence string. See §G below for re-verification.

---

## Per-letter findings

### A. Scope-guard compliance — PASS
`git diff main..HEAD --name-only` produces 12 files, all inside allowed prefixes:
- 9 under `plugins/hep-ph-demo/skills/2hdm-a/` ✓
- 1 = `plugins/hep-ph-demo/skills/_shared/summary.schema.json` ✓
- 1 = `plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` (NEW) — plan §P3 explicitly authorized; treat as `_shared/**` extension, defensible
- 1 = `demo_output/2hdm-a/**` ✓ (multiple files)
- 1 = root `.gitignore` ✓ (plan preamble line "`.gitignore (P1 only)`")

No forbidden-prefix touches. Compliant.

### B. P4 iter_6_notes.md — PASS (real, not fabricated)
Verified above: all 7 sites exist at cited line ranges in current renderer. Reconstruction faithful to git source 674f6a5 plus renderer-grep augmentation. Not over-engineered; faithful to prompt.

### C. P3 schema test — PASS (substantive, not tautological)
Negative tests confirm schema rejects: missing required, additional prop, wrong type. Three stubs validate. Not a tautology.

### D. P5 wolframscript — PASS (with D1 caveat)
Invocation as-written will run if SARAH is in Wolfram's default `$Path`. G8 confirmed wolframscript responds. The misleading $SARAH_PATH prose (D1) is cosmetic.

### E. P6 sys.path fix — PASS
2hdm-a SKILL.md fix is correct and verified by the import. singlet-doublet has the same bug but is genuinely out of scope per plan §Forbidden. SD workstream must own that.

### F. P7 env.json content — FAIL latent (D3)
mg5/maddm `"unavailable"` is because config.json is missing on disk. **Phase 1 will hard-fail at the MG5 invocation step unless config.json is created with `madgraph_path` and `sarah_path`**. Manager-blocking before PT1 dispatch. Not a prep-gate failure (G7 only requires key presence).

### G. Gate G1–G10 re-verification — ALL PASS
- G1: `.cleaned` exists, `fix_loop/POST_MORTEM.md` absent. ✓
- G2: AUDIT.md exists with "Wchi" string; patch_paramcard.py has `Wchi = 0.0`. ✓
- G3: I ran `python3 plugins/hep-ph-demo/skills/_shared/test_summary_schema.py` — exit 0, all PASS. ✓
- G4: iter_6_notes.md exists, no INCOMPLETE prefix, 7 sites. ✓
- G5: `grep -rn "skip-render\|skip_render"` returns 0 matches. ✓
- G6: import works (verified). ✓
- G7: env.json has all 8 keys. ✓ (D2/D3 are content-quality issues, not key-presence)
- G8: relies on local Wolfram Engine — gate-evaluator's claim accepted on faith (I did not re-run wolframscript).
- G9: `$SARAH_ROOT/Models/TwoHdmAfix/` either absent or matches fixture — gate-evaluator's claim accepted on faith.
- G10: `git status --porcelain` from worktree — clean. ✓

### H. Plan deviations — minor only
- R1/R2/R3 sign-off docs at `.shift-manager/run-20260424-202956/plan/` rather than under `workstreams/2hdma/prep/`. Plan §R1/R2/R3 explicitly says `.shift-manager/run-20260424-202956/plan/`, so this is **plan-compliant**, not a deviation. (Initial concern from review prompt was unfounded.)
- p7.md misstates main_sha.txt was read; actually fallback was used. Cosmetic doc lie.
- No tasks skipped. No unauthorized scope expansion.

---

## Concrete defect list

| ID | File:line | Severity | Fix |
|----|-----------|----------|-----|
| D1 | `plugins/hep-ph-demo/skills/2hdm-a/SKILL.md:252` | minor | Either remove the "`$SARAH_PATH` is read from config.json" sentence (since flock invocation doesn't use it) OR change the invocation to `wolframscript -code 'AppendTo[$Path, "$SARAH_PATH"]; <<SARAH\`; …'`. PT1 may still work without this fix if SARAH is on Wolfram's default $Path. |
| D2 | `demo_output/2hdm-a/playtest_log/env.json:7` (sarah_version) | minor | `capture_env.py:78` queries `Print[$SARAHVersion]` but SARAH styles its banner. Replace with `wolframscript -code '<<SARAH\`; Print[ToString[$SARAHVersion]]'` and strip StyleForm wrappers, or use `StringReplace[…, "StyleForm["~~__~~"]" -> ""]`. |
| D3 | repo root `config.json` | **blocker for PT1** (not for prep) | **Manager must create or verify `config.json` with at least `madgraph_path` and `sarah_path` keys before dispatching PT1**, or update the PT1 prompt to require sonnet to bootstrap config.json. As-is, PT1 step 4 will KeyError on `config["madgraph_path"]`. |
| D4 | `…/workstreams/2hdma/prep/p7.md:8` | trivial | "read from main_sha.txt, matches plan" is false; main_sha.txt does not exist. Fallback was used. Cosmetic write-up correction only. |

---

## Green-light statement

**Phase 0 prep is ACCEPTED.** All 10 gates legitimately pass. The diff is fully scope-compliant. Renderer-debt enumeration in iter_6_notes.md is verified-real. Schema test is substantive. Wchi=0.0 is set with citation. Dual SHA captured.

**Manager pre-PT1 checklist** (do before dispatching PT1, derived from defects above):
1. Verify or create `config.json` at repo root with `madgraph_path` and `sarah_path` populated. (Defect D3 will hard-fail PT1 otherwise.)
2. Optional: nudge PT1 sonnet to fix D2 (sarah_version cleanup) opportunistically.
3. Optional: nudge PT1 sonnet to fix D1 ($SARAH_PATH prose).

If config.json cannot be produced, halt and dispatch a worktree-medic + config-bootstrap sonnet before PT1.

Proceed to Phase 1 PT1.
