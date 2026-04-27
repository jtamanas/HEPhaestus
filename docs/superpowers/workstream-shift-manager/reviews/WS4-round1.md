# WS4 Round 1 Review — `dark-su3` per-model skill

**Verdict:** APPROVED

**Scope:** branch `ws4/dark-su3` @ commit `3fde886` in worktree `/Users/yianni/Projects/hep-ph-agents.ws4-dark-su3`. New file: `plugins/hep-ph-toolkit/skills/dark-su3/SKILL.md` (415 lines). Parent: WS2 `0255333`.

---

## 1. Mechanical done-criteria

| # | Criterion | Command / location | Result |
|---|---|---|---|
| 1 | Test suite green | `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` | **74 passed, 13 skipped** |
| 2 | `TestDarkSU3` moved skipped→passed | Full pytest listing | **13/13 PASSED** (`test_metadata_display`, `dm_candidates`, `plot_axes`, `multi_component`, `multi_component_prereq`, `time_overrides`, `step2_json_option_ids`, `step2_json_flags`, `step3_blocked_branch_ids`, `summary_json_path`, `physics_adaptation_words`, `dark_matter_constraints_in_chains`, `no_run_ready_zero_constraints_message`) |
| 3 | 13 skipped are `Test2HdmA` only | Pytest -v output | ✅ all 13 skipped belong to `Test2HdmA` (expected — WS3 has not merged) |
| 4 | `grep -c "scalar dark pion"` ≥ 1 | — | **5** |
| 5 | `grep -c "vector dark meson"` ≥ 1 | — | **5** |
| 6 | `grep -ci "blind spot"` ≥ 1 | — | **8** |
| 7 | `grep -ci "confining"` ≥ 1 | — | **8** |
| 8 | `grep -ci "multi-component"` ≥ 1 | — | **5** |
| 9 | `grep -c "dark-matter-constraints"` ≥ 3 | — | **31** |
| 10 | `grep -c "No selected constraints are currently runnable"` ≥ 1 | — | **2** |
| 11 | `grep -c "demo_output/dark-su3/summary.json"` ≥ 1 | — | **3** |
| 12 | `plugin.json` + `test_skill_structure.py` untouched vs WS2 parent | `git diff 0255333..HEAD --stat` | **only SKILL.md changed** (415 insertions, 1 file) |
| 13 | No `.py` files added under `_shared/` | same | ✅ zero |
| 14 | `Co-Authored-By` absent | `git log main..HEAD --format=%B \| grep -c Co-Authored-By` | **0** |
| 15 | Commit prefix `W4:` | `git log -1 --format=%s` | `W4: dark-su3 per-model skill — multi-component DM, all-blocked UX` ✅ |
| 16 | Prose-directive regex, relic branch | `grep -nE '^>\s*Invoke\s+/[a-z0-9-]+\b'` scoped to relic sub-branch | **EXACTLY 4** (L202 `/sarah-build`, L208 `/spheno-build`, L220 `/madgraph`, L222 `/maddm`) — matches §4.4 order |
| 17 | Prose-directive count, DD + ID branches | same | 0 in each (BLOCKED branches use documentary prose, not directives — consistent with §3 WS4 "document the N=2 execution path by reference") |
| 18 | `## Model metadata` YAML matches `constraints.yaml::models.dark-su3` | `diff` | ✅ identical on all keys (`display`, `dm_candidates`, `plot_axes`, `multi_component`, `multi_component_prereq`, `time_overrides`); only indentation + one inline comment differ — all enforced by `test_metadata_*` which passes |
| 19 | 2 entries in `dm_candidates` (φ + V) | L30–32 of SKILL.md | ✅ `phi` spin 0, `V` spin 1 |
| 20 | 7 sections in WS2 order | `grep -n '^## '` | ✅ `When to invoke` → `Model metadata` → `Constraints and time estimates` → `Flow` → `Error paths` → `File map` (6 H2 + H1 title = 7 sections, same as singlet-doublet) |
| 21 | Frontmatter = `name` + `description` only | L1–4 | ✅ |
| 22 | Step 2 AskUserQuestion ids [relic, dd, id, collider]; `allowMultiple: true`; `required: true` | L96–106 | ✅ |
| 23 | Step 3 blocked-gate ids [run_ready, back, cancel]; `allowMultiple: false`; `required: true` | L146–154 | ✅ |

---

## 2. Multi-component inline-math audit

Ran `grep -nE "Σ|\\\\sum|Ω_tot|f_i\s*=|n_i\^2|halo"` and `grep -n "f_i"` and `grep -n "Ω_tot\|Ω_phi\|Ω_V\|weighted"` across SKILL.md. Matches:

| Line | Text (truncated) | Classification |
|---|---|---|
| 78 | `This is a multi-component model. Per-candidate observables must be combined using relic-weighted fractions` **`f_i = Ω_i / Ω_tot`**`. Multi-component weighting is handled by the planned /dark-matter-constraints meta-skill…` | **Allowed single pointer sentence** per §1.3 ("beyond a single pointer sentence" is the reject threshold). One `f_i =` use; no surrounding derivation. |
| 224 | "Both produce `Omega h²` values: `Ω_phi h²` and `Ω_V h²`. **Multi-component weighting is handled by the planned `/dark-matter-constraints` meta-skill**…" | Deferral only — no derivation, no formula. |
| 271 | "Multi-component combination of `Ω_phi h²` and `Ω_V h²` into total `Ω_tot h²` and relic-weighted fractions **is the responsibility of `/dark-matter-constraints [PLANNED]`**." | Naming the outputs + deferral. No inline derivation. |
| 279 | "combined using relic-weighted fractions — **the combination rule is the responsibility of `/dark-matter-constraints [PLANNED]`**." | Naming + deferral. |
| 293 | "combines the per-candidate fluxes using `f_i`-weighted rates and compares against Fermi-LAT and IceCube limits" | Naming only; action is attributed to `/dark-matter-constraints`. |

**Verdict:** `Σ` appears 0×; `\sum` appears 0×; `halo` appears 0×; `n_i²` appears 0×. `f_i = Ω_i / Ω_tot` appears exactly once (L78), which is the explicit allowance in the implementer prompt + §1.3. All other references are either (a) attributing work to `/dark-matter-constraints`, (b) naming outputs (`Ω_phi h²`, `Ω_V h²`, `Ω_tot h²`) without combining them. No inline derivation of `Σ f_i σ_i`, no halo-distribution assumption, no coherence discussion. **WITHIN the one-pointer allowance.**

---

## 3. BLOCKED UX flow audit

**Step 3 state (SKILL.md L119–138):**
- Relic density: `BLOCKED — missing: /dark-matter-constraints` ✅
- Direct detection: `BLOCKED — missing: /feynarts, /formcalc, /package-x, /ddcalc, /dark-matter-constraints` ✅
- Indirect detection: `BLOCKED — missing: /gamlike, /dark-matter-constraints` ✅

All three BLOCKED, each chain appends `/dark-matter-constraints [PLANNED]` (matches done-criterion #5 of §WS4).

**Blocked-branch gate (L144–155):** fires with `{run_ready, back, cancel}`, `allowMultiple: false`, `required: true`. Hypothetical READY gate documented at L160–170 but noted as unreachable until `/dark-matter-constraints` ships. ✅

**`run_ready` handling (L176–180):**

```
On `run_ready` when zero constraints are ready: print the following message and return to Step 2:

No selected constraints are currently runnable. Re-select constraints or Cancel.
```

Matches §WS4 done-criterion verbatim. The "loop back to Step 2" action is explicit. L182 reiterates: "every constraint chain includes `/dark-matter-constraints [PLANNED]`, so `run_ready` finds nothing executable and exits gracefully with the message above." ✅

**On `cancel` (L172):** "Do NOT write `summary.json`." ✅ matches §WS4 done-criterion.

---

## 4. Physics copy-paste audit (vs `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md`)

| Section | Dark SU(3) content | Verdict |
|---|---|---|
| Frontmatter `description` | Names `phi` (scalar dark pion) + `V` (vector dark meson); cites "exact parameter-independent SI blind spot"; surfaces all-BLOCKED + `/dark-matter-constraints` gating | **Adapted** — no Majorana / Higgs-portal residue |
| Title + opening paragraph (L6–12) | "confining dark sector with SU(3) dark color", two DM candidates, composite states from dark confinement, multi-component deferral | **Adapted** |
| `## Model metadata` (L22–42) | 2 dm_candidates; log-log `(m_V, m_phi)` axes; `multi_component: true`; `multi_component_prereq: dark-matter-constraints`; time overrides | **Adapted** (singlet-doublet has 1 candidate, linear axes, `multi_component: false`) |
| Constraints table (L46–61) | All 3 rows BLOCKED on `/dark-matter-constraints` | **Adapted** (singlet-doublet has relic READY) |
| Step 1 DM-candidate declaration (L69–86) | Two-bullet declaration (phi + V); one pointer sentence `f_i = Ω_i / Ω_tot`; then 3-paragraph physics note on phi (exact SM-singlet cancellation), V (resonance region near `m_V ~ 2 m_phi`, paper Fig. 8), confining sector (SARAH HLS-like UV Lagrangian, Dirac `psi_D` in SU(3)_D fundamental) | **Adapted** — matches synthesis §3 multi-candidate variant |
| Step 2 multi-select (L90–108) | Identical ids/flags to WS2 (by design — this is the contract) | **Schema-identical by design** (§4 requirement; not copy-paste of physics) |
| Step 3 gate (L112–182) | All-BLOCKED tree; `run_ready`-with-zero handling explicit | **Adapted** |
| Step 4a SARAH (L198–204) | `/sarah-build` on `dark_su3.yaml`; HLS-like approach; `psi_D` in SU(3)_D fundamental; params `MpsiD, mV, mphi` | **Adapted** (singlet-doublet: `MS/MD/yh` + blind-spot condition `MS*MD + (y_h v/√2)² = 0`) |
| Step 4b SPheno (L206–216) | `SPheno.spc.dark_su3`; 4 benchmark points spanning resonance region including `m_V ~ 2 m_phi` | **Adapted** (singlet-doublet scans blind-spot region with 3 points) |
| Step 4c MadGraph + MadDM (L218–271) | **Two separate MadDM sessions** (phi + V); each with distinct MG5 generate lines (`phi phi~ > all all`; `V V > all all` + add process); per-candidate card with `dm_candidate phi/V`; DRAKE fallback if resonance narrow (cites memory `project_dm_tool_roles`); parses two `relic_density.dat` files | **Adapted** — fundamentally different from singlet-doublet's single Majorana session with SDMIX block + `self_conj = True` check |
| Step 4 DD branch (L275–283) | Blind-spot on phi (exact, no loop signal — SM-gauge singlet); V has tree SI; combination deferred | **Adapted** (singlet-doublet's DD is blocked on FormCalc/Package-X loop tools with CP-even scalar exchange physics) |
| Step 4 ID branch (L287–295) | Per-candidate spectra, velocity-dependent `<σv>` warning for V near resonance, DRAKE guidance | **Adapted** |
| Step 4d Plotting (L299–351) | mplhep ATLAS; black points per `feedback_data_point_color`; scatter on log-log `(m_V, m_phi)`; Planck band highlight; `m_V = 2 m_phi` resonance diagonal | **Adapted** (uses model's `plot_axes` — same pattern as WS2 but different axes) |
| Step 4e summary.json (L355–384) | `./demo_output/dark-su3/summary.json`; example with `"model": "dark-su3"`; cancel-no-write path explicit | **Adapted** |
| Error paths (L390–401) | SARAH anomaly note ("one Dirac fermion in fundamental of SU(3)_D — anomaly-free by construction"); MadDM phi UFO import; V resonance DRAKE fallback; `/dark-matter-constraints` not-available row | **Adapted** (no Majorana-specific rows) |
| File map (L407–415) | Per-candidate relic JSONs (`relic_phi_<n>.json`, `relic_V_<n>.json`); `summary.png` + `summary.json` | **Adapted** |

**No section reads as singlet-doublet copy-paste.** Every section carries dark-SU(3)-specific physics. Blind-spot discussion (L82) explicitly contrasts the exact parameter-independent cancellation with singlet-doublet's tuned condition — direct evidence of deliberate adaptation, not mechanical substitution.

---

## 5. Schema contract audit

| Contract | Status |
|---|---|
| Frontmatter = `name` + `description` only | ✅ L1–4 |
| 7 sections in order | ✅ (H1 + 6 H2, matches WS2) |
| Step 2 AskUserQuestion ids `[relic, dd, id, collider]` | ✅ L97–102 |
| Step 2 `allowMultiple: true`, `required: true` | ✅ L103–104 |
| Step 2 collider-only validation message | ✅ L108 |
| `## Model metadata` 2 entries in `dm_candidates` | ✅ L30–32 (`phi` + `V`) |
| Metadata matches `constraints.yaml::models.dark-su3` | ✅ byte-equal modulo indentation + one inline comment; `test_metadata_*` tests pass |
| `multi_component: true` | ✅ L36 |
| `multi_component_prereq: dark-matter-constraints` | ✅ L37 |
| `summary.json` path per §4.1 | ✅ `./demo_output/dark-su3/summary.json` appears at L357, L382, and in file map L415 |
| summary.json schema conformance (example) | ✅ L368–380 conforms to `_shared/summary.schema.json` (model enum, ran, skipped_constraints, artifacts_dir, headline) |
| Plotting: mplhep + ATLAS + black | ✅ L305–344 (`hep.style.use("ATLAS")`, `c='black'`, references memory `feedback_data_point_color`) |
| Axis labels from `plot_axes` metadata | ✅ L332–337 (`m_V`, `m_phi`, ranges, log scale) |
| `plugin.json` untouched vs WS2 parent | ✅ `git diff 0255333..HEAD -- …/plugin.json` → empty |
| `test_skill_structure.py` untouched vs WS2 parent | ✅ same |
| No `combine_multi_dm.py` / new `.py` files | ✅ scoped diff: only SKILL.md |
| Commit `W4:` prefix, no Co-Authored-By | ✅ |

---

## 6. Augment-not-replace compliance

Per memory `feedback_augment_not_replace` and plan §1.1 decision D2a: no inline physics combination in SKILL.md; defer to `/dark-matter-constraints` [PLANNED]. ✅

Per memory `project_dm_tool_roles`: MadDM primary, DRAKE for narrow resonances, micrOMEGAs as validator. ✅ L247 cites DRAKE for narrow resonances; L295 cites DRAKE for velocity-dependent `<σv>`; L399 error-path references DRAKE + cites memory explicitly.

---

## 7. Final note on "could-I-drive-MG5-from-this" attestation (§1.6 A2.2)

The Step 4c block (L218–271) provides concrete MG5 prompts for two separate sessions (`import model dark_su3-UFO`; `generate phi phi~ > all all` / `generate V V > all all` + `add process V~ V~ > all all`; `output …`; `launch …`), explicit card settings (`set dm_candidate phi/V`, `set relic_density ON`, etc.), output-file paths to parse (`Events/run_01/MadDM_output/relic_density.dat`), and the multi-component deferral to `/dark-matter-constraints`. A trained operator could drive MG5+MadDM from this text to produce `Ω_phi h²` and `Ω_V h²` at each benchmark point; combination into `Ω_tot` is correctly deferred. **Attestation passes.**

---

## Verdict

**APPROVED.** All 23 mechanical criteria pass; zero inline multi-component derivation beyond the single L78 pointer sentence; BLOCKED UX flow matches §WS4 + §1.6 A4.1 exactly; physics content fully adapted with no singlet-doublet residue; schema contract clean. Ready to merge `ws4/dark-su3` after WS3 merges (order irrelevant per §1.5 — disjoint directories).
