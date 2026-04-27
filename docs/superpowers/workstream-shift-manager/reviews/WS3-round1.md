# WS3 Round 1 Review — `2hdm-a` per-model skill

**Reviewer:** Opus skeptic (shift-manager pipeline)
**Date:** 2026-04-19
**Branch:** `ws3/2hdm-a` @ `da7f041` (on top of WS2 `0255333`)
**Worktree:** `/Users/yianni/Projects/hep-ph-agents.ws3-2hdm-a`
**Artifact under review:** `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` (433 lines)

---

## Verdict: APPROVED

All 13 mechanical done-criteria pass. Physics adaptation is genuine — the 2HDM+a DM phenomenology is re-written throughout (Dirac candidate, CP-odd mediator, s-channel `a`-resonance, CP-forbidden tree SI, `tan β`-dependent branching). No verbatim copy in physics-bearing sections. `plugin.json` and `test_skill_structure.py` untouched vs WS2 base.

---

## Mechanical check table

| # | Criterion | Command | Result |
|---|---|---|---|
| 1 | pytest green | `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` | **74 passed, 13 skipped** (13 = dark-su3 skipif — expected) |
| 2 | `plugin.json` untouched | `git diff 0255333..HEAD -- plugins/hep-ph-demo/.claude-plugin/plugin.json` | **no diff** |
| 3 | `test_skill_structure.py` untouched | `git diff 0255333..HEAD -- plugins/hep-ph-toolkit/skills/_shared/tests/test_skill_structure.py` | **no diff** |
| 4 | Only 2hdm-a dir touched by WS3 | `git diff 0255333..HEAD --stat` | `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md | 433 ++` — only file |
| 5 | Prose-directive regex, count | `grep -E '^>\s*Invoke\s+/' SKILL.md` | **4 matches** (lines 178, 198, 213, 215) |
| 6 | Prose-directive order | (same) | `/sarah-build → /spheno-build → /madgraph → /maddm` ✓ |
| 7 | `Dirac` present | `grep -c Dirac` | 10+ hits (lines 8, 29, 69, 172, 184, 213, 215, 234, 236, 246, 415) |
| 8 | `CP-odd` present | `grep -c CP-odd` | 7 hits (lines 8, 29, 69, 185, 186, 372, 415) |
| 9 | `loop-only` present | `grep -c loop-only` | 4 hits (lines 27, 240, 372, 394) |
| 10 | `a-resonance` / `a resonance` | `grep -Ec 'a-resonance|a resonance'` | 11 hits (lines 83, 172, 190, 202–204, 229, 303, 337, 363, 398) |
| 11 | `tan β` / `tan_beta` | `grep -Ec 'tan.?β\|tan_beta\|tan beta'` | **20 hits** |
| 12 | `σ_SI_tree ≈ 0` / `CP-forbidden` | `grep -E 'CP-forbidden\|σ_SI_tree'` | 6 hits (lines 8, 27, 84, 112, 239, 372, 394) |
| 13 | `demo_output/2hdm-a/summary.json` | `grep -c …` | 3 hits (lines 379, 402, 433) |
| 14 | `## Model metadata` YAML matches `constraints.yaml` `models.2hdm-a` | python yaml diff | **no key-or-value diff** |
| 15 | Commit prefix & no Co-Authored-By | `git log main..HEAD --format=%B | grep -c Co-Authored-By` | 0; single commit, `W3:` prefix |
| 16 | Section order identical to WS2 | `grep -n '^#' SKILL.md` both files | identical heading sequence (`When to invoke` · `Model metadata` · `Constraints and time estimates` · `Flow` · `Step 1` … `Step 4f` · `Error paths` · `File map`) |

---

## Schema contract audit

- **Frontmatter:** only `name` + `description` (lines 1–4). ✓
- **Section order:** 7 top-level `##` / step sections in exact same order as WS2. ✓
- **`## Model metadata` YAML:** keys `{display, dm_candidates, plot_axes, multi_component, time_overrides}` — matches `constraints.yaml` `models.2hdm-a` exactly. Note: WS3 done-criterion phrased as "matches `_shared/assets/two_hdm_a.yaml`" — but §4.3 of the final plan says the block duplicates `constraints.yaml` `models.<id>`. Implementer correctly followed §4.3. ✓
- **Step 2 AskUserQuestion:** ids `[relic, dd, id, collider]`, `allowMultiple: true`, `required: true` (lines 80–91). ✓
- **Step 3 tables:** `Relic [READY]`; `Direct detection [BLOCKED]` with missing `/feynarts /formcalc /package-x /ddcalc`; `Indirect detection [BLOCKED]` with missing `/gamlike` (lines 49–53, 104–117). ✓
- **Step 4 relic branch:** exactly 4 prose directives in order `/sarah-build → /spheno-build → /madgraph → /maddm` (lines 178, 198, 213, 215). DD/ID branches contain **zero** `> Invoke /` directives (BLOCKED-gated text only, §4e lines 368–373). ✓
- **summary.json path:** `./demo_output/2hdm-a/summary.json` present (lines 379, 402, 433), references `_shared/summary.schema.json`. Cancel path explicitly says "do NOT write `summary.json`" (line 404). ✓
- **Plotting guidance:** `mplhep` + ATLAS style + black data points + `plot_axes` metadata used for axes (lines 313–364). ✓

---

## Physics copy-paste audit (per section)

| Section | Verdict | Evidence |
|---|---|---|
| Intro (lines 6–10) | **ADAPTED** | Rewrites around Dirac `chi`, CP-odd `a`, CP-forbidden tree SI, loop-only DD, `a`-resonance relic with `tan β` dependence — no shared prose with WS2's mixing-matrix blind-spot framing. |
| Step 1 DM-candidate (lines 63–71) | **ADAPTED** | Single Dirac candidate `chi` via CP-odd mediator; WS2 had single Majorana `chi1` as mixing eigenstate. Wording differs beyond name. |
| Step 2 options (lines 80–91) | **PARTIAL ADAPT — acceptable** | Structural JSON identical (required by schema); `relic` description gains `(a-resonance region)`, `dd` gains `Loop-only σ_SI … (tree SI is CP-forbidden)`. Non-physics plumbing is expected to match. |
| Step 3 chain table (lines 49–55, 101–122) | **ADAPTED** | Adds DD-branch "tree-level SI is CP-forbidden (`σ_SI_tree ≈ 0`); the loop subchain is the primary DD signal" note (line 112). DD time range bumped to 3–6 hr (matches `time_overrides.dd`). |
| Step 4a SARAH block (lines 176–193) | **ADAPTED** | Bullet list rewritten: `chiL/chiR` Dirac pair, `H1/H2/a` scalar content, CP-odd Yukawa `i g_chi a chibar chi`, type-II 2HDM structure, portal `λ_P |H1†H2| a`. Zero sentences shared with WS2's `S/DL/DR + y_h H DL S` content. |
| Step 4b SPheno (lines 196–208) | **ADAPTED** | Benchmark-point tuples are 2HDM+a parameters (`Mchi, Ma, gchi, tanb`); at least one on-resonance, one off-resonance, one at large `tan β`. WS2 had `(MS, MD, yh)` blind-spot sweep. |
| Step 4c MadGraph/MadDM (lines 211–305) | **STRONGLY ADAPTED** | `add process chi chi~ > a > all all` (s-channel explicitly), `self_conj = False` Dirac comments, dedicated "Dirac candidate flag" paragraph explaining the Majorana → Dirac switch (lines 246–247), dedicated "a-resonance scan strategy" paragraph on `m_a ≈ 2 m_chi` with `tan β`-dependent `a → bb̄/tt̄` partial widths (line 266). `param_card.dat` block is `THDMA` with `tanb/gchi/lamP` — not WS2's `SDMIX`. |
| Step 4d plotting (lines 309–365) | **ADAPTED** | `a`-resonance line `axvline(2 * m_chi_fixed)` plus log-log scale on `(m_a, tan β)`. WS2 had linear `(m_chi, sin 2θ)` with blind-spot `axhline(0)`. |
| Step 4e DD/ID BLOCKED (lines 368–373) | **ADAPTED** | DD paragraph rewrites the suppression as CP-symmetric (structural) vs WS2's parameter-tuned blind-spot — explicitly contrasts the two models: "the direct-detection suppression is a structural feature of the model's CP symmetry, not a fine-tuned cancellation" (line 372). Also adds `tan β`-dependent ID phenomenology (`a → bb̄` at large `tan β`, `a → tt̄` at small). |
| Step 4f summary.json (lines 377–404) | **PARTIAL ADAPT — acceptable** | Schema-bound JSON structure identical (required); `skipped_constraints[0].reason` rewritten to reference loop-only/CP-forbidden. |
| Error paths (lines 408–420) | **ADAPTED** | `ANOMALY_CANCELLATION_FAILED` row specialises to "adds a Dirac singlet `chi`… and a CP-odd singlet `a`"; `Omega h^2 absent` row adds "on-resonance points are numerically sensitive — try a point away from `m_a ≈ 2 m_chi`". |
| File map (lines 424–433) | **ADAPTED** | Model path `two_hdm_a`, output dir `demo_output/2hdm-a/`, plot caption `(m_a, tan_beta)`. |

No section is substantively verbatim-copied from WS2. The non-physics plumbing sections that share shape (Step 2 JSON schema, Step 3 blocked/ready AskUserQuestion, Step 4f summary.json envelope) are required-to-match by §4.1–4.4 contracts.

---

## No inline physics math in Python

Step 4d Python block (lines 315–356) is pure plotting: `hep.style.use("ATLAS")`, `ax.scatter`, `ax.axvline`, `ax.set_xlim/ylim/xscale/yscale`, `hep.atlas.label`, `fig.savefig`. No cross-section formulas, no partial widths, no relic computation. ✓

---

## Commits

```
da7f041 W3: 2hdm-a per-model skill — Dirac DM via pseudoscalar mediator
```

- Prefix `W3:` ✓
- No `Co-Authored-By:` line ✓
- Message body matches template (Dirac + CP-odd MadDM guidance, loop-only DD, `a`-resonance relic, `tan-beta` dependence, relic READY / dd+id BLOCKED).

---

## Optional polish (non-blocking)

None — merge as-is. WS4 review is independent.
