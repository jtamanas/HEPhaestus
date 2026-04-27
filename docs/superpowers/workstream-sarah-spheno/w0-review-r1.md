# W0 Round-1 Review

**Worktree:** `wt-w0-shared-contracts` at `/Users/yianni/Projects/hep-ph-agents-worktrees/wt-w0-shared-contracts`
**Commits reviewed:** `559aeba` → `63c0a54` (6 commits, +4306 / -1 lines, 47 files)
**Test status:** 60/60 passing. Acceptance criteria 1, 2, 3, 5, 6 verified; criterion 4 verified conditionally (see Minor #5).

---

## 1. Deviation audit

### Deviation (a): path-depth 4 `../` vs plan-stated 3 `../`

**Severity:** minor / **plan bug, not implementation bug**.

**What's wrong:** The plan's Global Invariant §2.2 (line 59) claims hep-ph-demo scripts use 3 `../` levels: `"hep-ph-demo scripts... use `../../../shared/install-helpers/` — three levels, not four."` This is **factually wrong**. The hep-ph-demo install scripts live at `plugins/hep-ph-toolkit/skills/install/scripts/`. Reaching `plugins/shared/install-helpers/` requires going up through `scripts → install → skills → hep-ph-demo` = **4 levels**. The implementer correctly used 4 `../` in both `_common.sh` header comment and the shim (`plugins/hep-ph-toolkit/skills/install/scripts/_common.sh:10`).

**Evidence:** `bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all` runs without error, producing parseable JSON that matches baseline exactly.

**Where:** plan `phase2-plan-final.md:59` (plan bug); `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh:10` (correct).

**Fix (documentation only):** No fix needed in code. Plan §2.2 should be corrected post-merge — note in W0 merge commit message or in the next plan revision. The implementer's path is right.

---

### Deviation (b): `_title_part()` extended to uppercase ≤2-char alpha prefixes

**Severity:** justified / minor edge-case concerns.

**What's wrong:** The plan's item 10 specifies the provisional rule as:
```python
return "".join(w.capitalize() for w in name.split("_"))
```
which maps `dark_su3 → DarkSu3`. But acceptance criterion 3 demands `dark_su3 → DarkSU3`. The plan is self-contradictory. The implementer correctly prioritized the acceptance criterion and added a 1–2-char-alpha-prefix uppercase rule.

**Where:** `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py:38-58`.

**Edge-case audit** (I ran them):

| Input | Output | HEP-correct? | Notes |
|---|---|---|---|
| `dark_su3` | `DarkSU3` | yes | acceptance criterion |
| `singlet_doublet` | `SingletDoublet` | yes | |
| `dark_u1` | `DarkU1` | yes | len-1 alpha prefix |
| `dark_su2` | `DarkSU2` | yes | |
| `u1_prime` | `U1Prime` | yes | |
| `sm_extended_dark` | `SMExtendedDark` | yes | covered by `test_triple_segment` |
| `a_su2_b` | `ASU2B` | plausible | **no test coverage** |
| `two_hdm` | `TwoHdm` | **no, should be `TwoHDM`** | 3-char alpha "hdm" fails the ≤2 rule |
| `mssm` | `Mssm` | **no, should be `MSSM`** | 4-char alpha "mssm" fails the ≤2 rule |
| `nmssm` | `Nmssm` | **no, should be `NMSSM`** | same |

The last three rows are **known limitations** of the provisional rule. The file carries `# PROVISIONAL — verified by W3 Day-1 probe` and SHARED.md §X is reserved for W3's amendment. Per plan §1 risk #1, W3 is explicitly authorized to patch this in a one-commit amendment. So the deviation is structurally correct; **but** the `test_sarah_name.py` coverage is too narrow — it doesn't flag these as known-wrong. A future fixer should not "fix" them by tweaking the heuristic without W3 probe data.

**Fix (for test coverage, not code):** Add a documented-known-limitation test block that pins current (provisional) output for `mssm`, `nmssm`, `two_hdm`, and a multi-segment group like `a_su2_b`. Title the block `# TODO(W3): these are provisional outputs; W3 Day-1 probe pins the correct rule`. This freezes the contract for W3 to break.

---

### Deviation (c): hep-ph-demo committed into W0 branch

**Severity:** blocker-level scope concern, resolved as **justified / necessary bootstrap**.

**Verification:** On `main` at `f84c37c` (and at HEAD-of-main now), `plugins/hep-ph-demo/` is **entirely untracked** (confirmed via `git ls-tree -r main plugins/hep-ph-demo/` → empty; `git status` on main worktree shows `plugins/hep-ph-demo/` in "Untracked files"). The implementer committed 27 files in `559aeba` (W0 commit 0), including the four `install_*.sh` scripts and the `_common.sh` source that W0 was supposed to MODIFY.

**Plan contract check:** The W0 Files table (plan §W0) lists these hep-ph-demo scripts as `MODIFIED`. "Modified" presupposes the file exists on main. Since they didn't, the implementer had three options: (a) commit them into W0, (b) escalate to manager and ask whether to land them separately first, (c) fail. Choosing (a) was the right call — landing them separately would have blocked W0 for no physics reason and (b) introduces a serialization gate for a file set the plan already assumes is on main.

**Additional observation:** The `plugins/hep-ph-toolkit/skills/demo/` tree (281-line SKILL.md + `_figures/*.py`, `_cache.py`, `plot_figure.py`, `run_scan.py`) was **also** committed. This IS scope creep — those files are unrelated to the W0 install-helper refactor. But reverting them is no cheaper than keeping them, and they don't interact with any W1–W6 contract. Leave them.

**Where:** commit `559aeba`.

**Judgment:** LEAVE IN. Reverting the install-scripts part would break W0's regression gate (no baseline to regress against) and break every downstream workstream that expects `_common.sh` to be source-controlled.

**Fix (commit message hygiene only):** The `/` Manager should update the plan to note that hep-ph-demo is now tracked as of W0. No code change.

---

## 2. Plan compliance — per W0 work item

Walking §W0 items 1–19:

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Capture `detect-all` baseline before editing `_common.sh` | ✅ | Baseline file at `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json` (4 lines). Commit `559aeba` lands BEFORE `914e663` (fsync fix). **Verified ordering.** |
| 2 | Promote `_common.sh`, apply fsync fix inside the Python heredoc | ✅ | `plugins/shared/install-helpers/_common.sh:158-168` — the heredoc does `f.flush(); os.fsync(f.fileno())` then `os.rename`, then `os.fsync(dir_fd)`. Order is correct. (See §3 below for PID-reuse subtlety.) |
| 3 | Write `config_helpers.py` with full public API | ✅ | All names present: `STATE_ROOT`, `CONFIG_DIR`, `CONFIG_PATH`, `load_config`, `merge_config`, `register_model`, `get_model`, `MODEL_NAME_REGEX`. Uses `tempfile.mkstemp` (cleaner than bash `$$`). |
| 4 | Write README ≤80 lines | ✅ | 66 lines at `plugins/shared/install-helpers/README.md`. |
| 5 | Refactor hep-ph-demo installers + one-line shim | ✅ | Shim at `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` is 10 lines (mostly header comment). Each installer still sources `$SCRIPT_DIR/_common.sh` (i.e., the shim), preserving hep-ph-demo's local sourcing pattern. Commit `63c0a54` adds the shim-documentation comment lines. **Note:** the plan item 5 prescribes `. "$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"` — 3 levels — but the implementer's shim uses 4 levels. 4 is correct (see Deviation (a)). |
| 6 | Regression gate (zero diff) | ✅ | I re-ran `install.sh detect-all` against the baseline. `diff -q` exits 0. |
| 7 | SHARED.md with 7 sections + reserved appendix | ✅ | All sections present: state roots, model-name regex, timestamps, env-var table, cache keys, three-state blocker, config-key alignment, templates, §X reserved. |
| 8 | `modelspec.schema.json` | ✅ | All 10 required top-level fields (`spec_version`, `name`, `claim_source`, `sarah_version_required`, `gauge_groups`, `fermions`, `scalars`, `lagrangian`, `parameters`, `outputs`). `additionalProperties: false` (verified: `x_extension: foo` rejected). `gauge_groups[].kind` enum exactly `{hypercharge, left, color, dark, other}`. `outputs` items enum `{ufo, spheno}`. |
| 9 | `blocker.schema.json` with three-state `oneOf` | ✅ | `oneOf` with all three variants. Required fields per mode correct. `user_instruction` is allowed on fatal AND recoverable (plan §2.8 says optional on both — correct). **Verified mode-mixing rejected** (see §4 below). |
| 10 | `sarah_name.py` with `# PROVISIONAL` header | ✅ | Header comment present. See Deviation (b). |
| 11 | `config_migration.py --check`/`--apply` | ⚠️ | Implemented, but acceptance criterion 4 semantics is ambiguous — see Minor #5. |
| 12 | Four stub SKILL.md files | ✅ | All four exist with correct frontmatter shape (`name` + `description`, no `version`/`category`). Content points at spec + plan. Matches plan §W0 item 12 exactly. |
| 13 | `plugin.json` final length = 6 | ✅ | `python3 -c "…len==6…"` exits 0. `lagrangian-builder` and `rge-runner` preserved at slots 0/1. `version` bumped to `0.2.0`. |
| 14 | `test_modelspec_schema.py` | ✅ | Covers all five required cases + three extras. |
| 15 | `test_blocker_schema.py` | ✅ | All 6 fatal codes + 2 recoverable codes parametrized. Positive fixture per mode. Negative: missing caveats, empty caveats, empty reference_method, empty message, lowercase code. Mode-mixing not explicit but verified working (§4). |
| 16 | `test_sarah_name.py` | ⚠️ | See Deviation (b) for coverage gap on MSSM-family names. |
| 17 | `test_config_helpers.py` | ✅ | `test_config_unchanged_on_simulated_write_crash` is the fsync-discipline test; it monkeypatches `os.rename` to raise, asserts config unchanged and no orphaned tmp. Very meaningful. |
| 18 | Fixtures | ✅ | `dark_su3_spec.yaml`, `blocker_examples.json`, `detect_all_baseline.json` all present. |
| 19 | Acceptance sweep | ✅ | I ran criteria 1, 2, 3, 5, 6 myself; all pass. Criterion 4 passes after `--apply` (see Minor #5). |

---

## 3. Atomicity / fsync correctness

### `_common.sh::config_merge` (plugins/shared/install-helpers/_common.sh:131-171)

Order in the Python heredoc (lines 158-168):
```python
with open(tmp_path, "w") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")
    f.flush()                       # ← 1
    os.fsync(f.fileno())            # ← 2
os.rename(tmp_path, cfg_path)       # ← 3
dir_fd = os.open(os.path.dirname(os.path.abspath(cfg_path)), os.O_RDONLY)
try:
    os.fsync(dir_fd)                # ← 4
finally:
    os.close(dir_fd)
```
**Correct order.** `dir_fd` is explicitly closed in a `finally`. No leak.

**PID-reuse subtlety (minor):** The bash wrapper line 133 uses `local tmp="${CONFIG_FILE}.tmp.$$"`. Two concurrent bash callers with distinct PIDs will not collide, but across container boundaries or long-running sessions with PID wraparound, a stale `.tmp.$$` left by a crashed earlier writer could be overwritten. The `config_helpers.py` side uses `tempfile.mkstemp(dir=dir_path, suffix=".tmp")` which generates a unique suffix and opens with `O_EXCL`, avoiding this. **Recommendation:** tighten the bash side to also use `mktemp` rather than `.tmp.$$`. Not a blocker — only matters under pathological conditions. See Minor #3.

### `config_helpers.py::_atomic_write` (plugins/shared/install-helpers/config_helpers.py:85-115)

- `tempfile.mkstemp(dir=dir_path, suffix=".tmp")` — ✅ correct (same FS as final, race-free).
- `os.fdopen(fd, "w")` then `flush()` + `fsync(fileno())` — ✅.
- `os.rename(tmp_path, str(path))` — ✅.
- `os.open(dir_path, O_RDONLY)` + `fsync(dir_fd)` + `close(dir_fd)` in a `try/finally` — ✅.
- `except Exception: unlink(tmp_path); raise` — ✅ cleans orphans on ANY failure inside the critical section.

**Test coverage:** `test_config_unchanged_on_simulated_write_crash` monkeypatches `os.rename` to raise, verifies (a) the original config is intact and (b) no `.tmp` file is left behind. This is the exact guarantee the fsync discipline is supposed to provide.

---

## 4. Schema correctness audit (ran directly)

All three adversarial checks pass:

```
OK: mode-mix rejected                (status=reference_only + mode=fatal + code=FOO)
OK: bare code rejected               ({code: FOO} alone)
OK: fatal without code rejected      ({mode: fatal, message: x} missing code)
OK: additionalProperties false rejects x-extensions
OK: dark_su3 fixture validates
OK: outputs: [calchep] rejected
OK: empty outputs rejected (minItems 1)
OK: gauge_group kind=supercolor rejected
```

`user_instruction` is allowed on both fatal and recoverable branches and absent from reference_only. Matches spec §2.8 + §2.7. **Nit:** SHARED.md §Three-state blocker contract shows `user_instruction` only in the fatal example, not the recoverable example — consistent with schema but may mislead readers that recoverable can't carry it. Minor documentation.

**Spec §4 vs fixture:** The spec §4 example YAML OMITS `spec_version`; the plan REQUIRES it and the fixture correctly ADDS it. This is intentional (plan item 8 — mandatory field) but the spec file is stale. Out of W0's scope to fix; note for W5's spec-revision follow-up.

---

## 5. plugin.json integrity

Verified by direct read:
- `version` = `0.2.0` (bumped).
- `skills` length = 6 (verified).
- Slots 0/1: `lagrangian-builder`, `rge-runner` (preserved, unchanged).
- Slots 2–5: new entries in the correct `{name, path}` shape — no extra fields.

No integrity issues.

---

## 6. Test quality audit

Overall: these are **meaningful tests, not vanity**.

- **`test_modelspec_schema.py`**: 9 tests, mix of positive (valid fixture, `outputs: [ufo, spheno]`) and negative (missing `spec_version`, missing `name`, `2hdm`, uppercase name, unknown `kind`, `[calchep]`, `[]`). Covers all five plan-mandated cases plus extras. ✅
- **`test_blocker_schema.py`**: 21 parametrized tests across fatal/recoverable codes + negative cases (missing caveats, empty caveats, empty reference_method, empty message, lowercase code). Mode-mixing not explicitly tested but `oneOf` + `additionalProperties: false` makes it implicit (verified adversarially in §4). ✅ Consider adding an explicit mode-mix test for documentation value. Nit #2.
- **`test_config_helpers.py`**: 15 tests. `test_config_unchanged_on_simulated_write_crash` is the real atomic-write test. `test_no_orphaned_tmp_after_normal_write` pins the "clean on success" invariant. Both meaningful. Missing: a concurrent-writer test (two processes calling `merge_config` simultaneously). Hard to write robustly; not a blocker.
- **`test_sarah_name.py`**: 10 tests. Covers `dark_su3`, `singlet_doublet`, `2hdm`-ValueError, uppercase-ValueError, single-segment, triple-segment (`sm_extended_dark`), `u1`/`su2` groups, too-short name, regex constant. Does NOT pin the known-provisional-wrong outputs for `mssm`/`nmssm`/`two_hdm`. See Deviation (b) Fix. ⚠️

**All 60 tests pass in 0.26s.**

---

## 7. Baseline capture ordering

Commit log (chronological):
```
559aeba W0(0): add hep-ph-demo plugin + pre-refactor detect-all regression baseline
914e663 W0(1): promote _common.sh to shared; fix fsync bug; shim hep-ph-demo
0400a1f W0(2): add config_helpers.py + shared/install-helpers README
6ebbda4 W0(3): schemas, SHARED.md, _shared utilities, stub SKILL.md, plugin.json bump
0578dac W0(4): tests (60 passing) + fixtures
63c0a54 W0(5): add shim-documentation comments
```

Baseline is captured in commit 0; refactor happens in commit 1. **Ordering correct.** Post-refactor regression gate passes (zero diff). I verified in a fresh shell: `diff /tmp/detect_all_post.json baseline.json` → exit 0. ✅

---

## 8. Hidden breakage (hep-ph-demo entry points)

- `bash plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh detect` → prints `{"status":"missing"}` (expected on this machine). No sourcing error. ✅
- `bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all` → 4 JSON lines, all parseable (`json.loads` per line succeeds). ✅
- Shim-to-shared resolution: `$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh` exists from the shim's PWD. ✅

No hidden breakage.

---

## 9. Documentation

- **`plugins/hep-ph-toolkit/SHARED-model-building.md`** (190 lines): readable, actionable, well-structured with tables. **One issue:** the env-var table header says "Only the following variables are **implemented** (not promissory)." But during W0 only `HEPPH_STATE_ROOT`, `XDG_CONFIG_HOME`, and `NO_NETWORK` are read anywhere; `HEPPH_SARAH_VERSION` / `HEPPH_SPHENO_VERSION` have zero readers in W0 files (verified via grep — only hit is SHARED.md itself). They become implemented in W1/W2. **Minor** — either soften the language to "are planned for implementation" or add a "Consumed by" column note. See Minor #4.
- **`plugins/shared/install-helpers/README.md`** (66 lines): justified as a separate file. SHARED.md is model-building-plugin-scoped; this README is plugin-shared-scoped. Different audiences, different ownership invariants. Leave separate.
- **Content consistency:** SHARED.md §Model-name regex has an awkward self-correction in prose ("… `x` (too short at length 1 — wait: the regex requires at least 2 chars total …)"). Reads like an unedited thinking-out-loud. Minor style. See Minor #6.

---

## 10. Hep-ph-demo file enumeration

Committed in `559aeba` (27 files, 2630 insertions):
- `plugins/hep-ph-demo/.claude-plugin/plugin.json`
- `plugins/hep-ph-demo/README.md`
- `plugins/hep-ph-toolkit/skills/demo/SKILL.md`
- `plugins/hep-ph-toolkit/skills/demo/scripts/_cache.py`
- `plugins/hep-ph-toolkit/skills/demo/scripts/_figures/{__init__,a1,a2,a3,b1,b2,b3,c1,c2,c3}.py` (10 files)
- `plugins/hep-ph-toolkit/skills/demo/scripts/_runners.py`
- `plugins/hep-ph-toolkit/skills/demo/scripts/plot_figure.py`
- `plugins/hep-ph-toolkit/skills/demo/scripts/run_scan.py`
- `plugins/hep-ph-toolkit/skills/install/SKILL.md`
- `plugins/hep-ph-toolkit/skills/install/scripts/{_common.sh,check_config.py,install.sh,install_{mg5,sarah,spheno,wolfram}.sh}` (7 files)
- `plugins/hep-ph-toolkit/skills/install/skill_env.yaml`
- `plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json`

**On main at f84c37c:** all of the above are untracked (`git ls-tree -r main plugins/hep-ph-demo/` is empty).

**Judgment:** LEAVE IN. The install-scripts subtree is REQUIRED for W0's regression-gate contract. The demo subtree is incidental scope creep but removing it costs more than keeping it. See Deviation (c).

---

## Findings summary

| # | Severity | Where | What | Fix |
|---|---|---|---|---|
| B1 | — | — | None of the actual issues are blockers. | — |
| M1 | major | `plugins/hep-ph-toolkit/skills/_shared/tests/test_sarah_name.py` | Test suite does not pin known-provisional-wrong outputs for `mssm`, `nmssm`, `two_hdm`, `a_su2_b`. A future fixer could silently "fix" `_title_part` and break W3's probe expectations. | Add a `test_known_provisional_limitations` block that asserts current (provisional) outputs with a `# TODO(W3)` comment. |
| m1 | minor | `plugins/shared/install-helpers/_common.sh:133` | Bash `.tmp.$$` tmp filename has a theoretical PID-reuse race. Python side uses `tempfile.mkstemp` correctly. | Replace `local tmp="${CONFIG_FILE}.tmp.$$"` with `local tmp; tmp="$(mktemp "${CONFIG_FILE}.tmp.XXXXXX")"`. |
| m2 | minor | `plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema.py` | Mode-mixing (reference_only + code) is rejected by `oneOf` + `additionalProperties: false` but not explicitly tested. | Add `test_mode_mix_rejected`: a blocker with both `status: reference_only` and `mode: fatal`; assert rejection. |
| m3 | minor | `plugins/hep-ph-toolkit/SHARED-model-building.md:58-68` | "Only the following variables are **implemented** (not promissory)" — `HEPPH_SARAH_VERSION` / `HEPPH_SPHENO_VERSION` are not yet implemented anywhere in W0. True only after W1/W2 merge. | Soften header to "Advertised env-var overrides (consumers noted per-row; W0 does not itself read these two)" OR add a footnote "†HEPPH_SARAH_VERSION and HEPPH_SPHENO_VERSION are honored by W1/W2 installers; W0 defines and documents the contract." |
| n1 | nit | plan `phase2-plan-final.md:59` | Plan text "three levels, not four" is wrong — hep-ph-demo scripts need 4 `../`. Implementer used 4 correctly. | Update plan in a follow-up commit (NOT W0 fixer's job). |
| n2 | nit | `plugins/hep-ph-toolkit/SHARED-model-building.md:40-43` | Self-correcting prose: "… `x` (too short at length 1 — wait: the regex requires at least 2 chars …)". | Rewrite cleanly: "`x` (too short — the regex requires at least 2 characters: one leading `[a-z]` plus at least one `[a-z0-9_]`)." |
| n3 | nit | Plan acceptance criterion 4 | Ambiguous: `--check` exits 0 "on a machine whose config has existing hep-ph-demo keys" — but on a fresh machine with no config at all, `--check` exits 1 (because `models: {}` would be added). Behavior is consistent with plan item 11; criterion 4 is just narrowly phrased. | Not a fixer task; flag for plan revision. |
| n4 | nit | `plugins/hep-ph-toolkit/skills/demo/` subtree | Incidental scope creep in the W0(0) commit (181 KB of unrelated figure/scan scripts). | Leave in; reverting costs more than keeping. Flag in W0 merge-commit body. |

---

## Verdict

**APPROVE-WITH-FIXES.**

**Blockers:** 0.
**Majors:** 1 (M1 — test coverage for known-provisional `sarah_name` outputs).
**Minors the fixer should address:** m1, m2, m3.
**Nits the fixer can skip:** n1, n2, n3, n4.

The fixer's must-do list is: **M1 + m1 + m2 + m3**. Everything else is either documentation polish (n2), plan-level (n1, n3), or judgment-call (n4, already judged).

The implementation is solid: fsync discipline is correct, schemas validate adversarial inputs, the shim-and-promote pattern is clean, the regression baseline was captured in the correct order, 60 real tests pass, and all six acceptance criteria verify. The three implementer-flagged deviations (a/b/c) are each the correct call given the plan's ambiguities.
