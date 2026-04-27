# Dark SU(3) /dark-matter-constraints Playtest — Cycle 1 Report

**Date:** 2026-04-25
**Worktree:** `/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/agent-a4c5325b96c5b6e40`
**Target:** Arcadi & Profumo arXiv:2506.19062 Fig. 8, Dark SU(3) vector-resonance benchmark m_χ=100 GeV, m_med≈199 GeV
**Companion log:** `playtester_cycle1_log.md` (this directory)

---

## 1. Verdict — one paragraph

**Partial / blocked.** The `/dark-matter-constraints` router cannot complete an
end-to-end run on Profumo's Dark SU(3) benchmark on this machine, but the
blocker is upstream of the router: the SARAH-emitted UFO for Dark SU(3) is
unimportable by MG5 (invalid color tensor placeholders `f(dt1,dt2,dt3)` in
`vertices.py`), the dark fermion `psiD` is hard-coded `mass = ZERO`, and the
composite phi (DM) and V (mediator) states from Profumo §IV — which are the
*entire reason* this benchmark fires the DRAKE branch — are not elementary
fields in the UFO and so have no mass / coupling parameters to scan. The
spec.yaml at `~/.local/share/hep-ph-agents/models/dark_su3/spec.yaml` flags
this explicitly as `TODO(analytic-module): scripts/analytic_models/dark_su3.py
does not yet exist`, but neither the router nor any helper surfaces a blocker
for it. Running `/maddm` on a known-good UFO (SingletDoublet) on this same
machine produces a real `Omegah2 = 0.292` from a Boltzmann solve, so the MG5 +
MadDM 3.2.13 + SPheno 4.0.5 chain itself is fully functional. The router's
deterministic helpers (`check_prereqs`, `detect_drake`, `extract_field`,
`verify_router_field_contract`) all run and the unit suite (65/3xfailed/3xpassed)
is green. micrOMEGAs and DRAKE are not installed at all, so Step 4 and Step 5
of the SKILL.md cannot be exercised against real producers in this cycle even
on a working model.

---

## 2. Tool inventory

| Tool | Status | Version | Path |
|---|---|---|---|
| MG5_aMC | INSTALLED | 3.5.6 (2024-09-26) | `/Users/yianni/MG5_aMC_v3_5_6/bin/mg5_aMC` |
| MadDM (MG5 plugin) | INSTALLED | 3.2.13 | `/Users/yianni/MG5_aMC_v3_5_6/PLUGIN/maddm` |
| SARAH | INSTALLED | 4.15.3 | `/Users/yianni/SARAH/SARAH-4.15.3` |
| SPheno (binary built) | INSTALLED | 4.0.5 | `/Users/yianni/SPheno/SPheno-4.0.5/bin/SPheno` |
| Dark SU(3) SARAH model file | PRESENT | spec_version 1 | `/Users/yianni/.local/share/hep-ph-agents/models/dark_su3/spec.yaml` |
| Dark SU(3) UFO (canonical loc) | PRESENT but UNIMPORTABLE | — | `/Users/yianni/.local/share/hep-ph-agents/models/dark_su3/sarah_output/UFO/DarkSU3/` |
| Dark SU(3) UFO (SARAH out tree) | CORRUPT (`None = Particle(...)`) | — | `/Users/yianni/SARAH/SARAH-4.15.3/Output/DarkSU3/EWSB/UFO/` |
| micrOMEGAs | NOT INSTALLED | — | — |
| DRAKE | NOT INSTALLED | — | — |
| LoopTools | NOT INSTALLED | — | — |
| FeynArts | NOT INSTALLED | — | — |
| FormCalc | NOT INSTALLED | — | — |
| Package-X | NOT INSTALLED | — | — |
| FeynCalc | NOT INSTALLED | — | — |
| DDCalc | NOT INSTALLED | — | — |
| WolframScript | INSTALLED + ACTIVATED | 1.13.0 ARM | `/usr/local/bin/wolframscript` (returns `2` for `1+1`) |
| Python | INSTALLED | 3.10.16 | pyenv shim |
| numpy / pyyaml / pytest / jsonschema | INSTALLED | 2.2.6 / 6.0.3 / 9.0.3 / present | — |

Stub directory `/Users/yianni/SPheno-4.0.5/` is empty (0B); the real SPheno
build lives at `~/SPheno/SPheno-4.0.5/`.

A previous SingletDoublet end-to-end run is preserved at
`/Users/yianni/Projects/hep-ph-agents/.claude/worktrees/from-main/demo_output/singlet-doublet/`
and was used as a witness that MG5+MadDM is functional.

---

## 3. Step-by-step trace against SKILL.md

| Step | Status | Reason |
|---|---|---|
| Step 1 — `check_prereqs.py` | PASS (with caveats) | Helper runs and reports correctly on Dark SU(3) ufo_path; but mis-classifies `MICROMEGAS_MISSING` and `DRAKE_PATH_UNSET` as fatal (see Bug 1, 2). |
| Step 2 — `/maddm` on Dark SU(3) | FAIL (upstream UFO defect) | MG5 raises `NameError: name 'dt1' is not defined` on `import model`. Cannot reach `define darkmatter` / `generate relic_density`. |
| Step 2 alt — `/maddm` on SingletDoublet | PASS | Ran cleanly to `Omegah2 = 2.92e-01` after SLHA overlay. Validates the rest of the router downstream. |
| Step 3 — spectrum / coannihilation / resonance trigger | NOT REACHED for Dark SU(3) | UFO has no mediator mass / no DM mass in param list, so trigger arithmetic is undefined. The trigger logic in SKILL.md is LLM-prose only — fine, just nothing to triage. |
| Step 4 — micrOMEGAs cross-check | NOT REACHED (and not reachable) | micrOMEGAs not installed. Helper would have emitted `MICROMEGAS_MISSING` at Step 1; per SKILL.md this is recoverable, but the helper currently flips `status` to `blocked` (Bug 2). |
| Step 4b — `extract_field.py` smoke | PASS | Confirmed against canned fixtures: `relic.json/omega_h2`, `summary.json/sigma_si_proton_cm2`, `annihilation.json/sigma_v_zero` all return correct values with correct schema dispatch. |
| Step 5 — `detect_drake.py` | PASS (correctly emits DRAKE_MISSING) | With `drake_path: null`, returns `{"branch":"branch1_unset","status":"missing","router_action":"emit_DRAKE_MISSING"}`. WolframScript 1.13.0 IS activated on this machine (`1+1 → 2`), so an installed DRAKE *would* run. |
| Output / merged report | NOT EMITTED | Nothing useful to merge from a single working observable on a different model. |

---

## 4. Quantitative results

### Dark SU(3) (target benchmark)
None. Run blocked at MG5 import.

### SingletDoublet (router-plumbing witness, m_χ ≈ 100 GeV from prior SLHA)
| Observable | MadDM | micrOMEGAs | DRAKE |
|---|---|---|---|
| Ωh² | 2.92e-01 (overabundant) | not run | not run |
| ⟨σv⟩(x_f) | 8.42e-27 cm³/s | — | — |
| x_f | 20 | — | — |
| σ_SI(p) | not requested (relic-only) | — | — |
| σ_SD(p) | not requested | — | — |

Channel decomposition (top contributions): wpwm 33.6%, zh 20.0%, zz 17.8%, hh
12.2%, bbx 10.8%. Sensible for a singlet-doublet near m_χ ≈ 100 GeV.

These numbers are not for the paper benchmark — they're a smoke test that the
MadDM half of the router runs correctly when handed a clean UFO + a non-trivial
param_card.

---

## 5. Comparison to Profumo Fig. 8

**No comparison achievable in this cycle.** Reason: cannot produce a number
from any of the three intended tools for the Dark SU(3) model.

What we know qualitatively:
- Profumo Fig. 8 plots Ωh² vs m_χ for the resonance benchmark; the on-resonance
  point m_χ=100 GeV / m_med=199 GeV (Δ/(2m_χ)=0.5%) sits in the dip where
  s-channel V exchange efficiently depletes χ down to thermal-relic Ωh² ≈ 0.12.
- The paper warns that the velocity-expansion approximation used by MadDM
  fails near narrow resonances — exactly the regime where they invoke DRAKE.
  Without DRAKE installed and without phi/V as elementary UFO fields, neither
  estimate is reachable.
- A future-cycle deliverable: implement `analytic_models.dark_su3` (the
  `TODO(analytic-module)` flagged in the spec) that translates (MpsiD, gD, mV,
  mphi) into a phi+V effective UFO whose param_card is scannable.

---

## 6. Bug / gap list

1. **`check_prereqs.py` rejects YAML config.** (a) Helper opens config with
   `json.load` only despite advertising "JSON/YAML" in `--help`. (b)
   `plugins/constraints/skills/dark-matter-constraints/scripts/check_prereqs.py:30`
   (`_load_json`). (c) Severity: **major** — every shipped fixture in
   `tests/fixtures/dark_su3_playtest/configs/` is YAML, so no shipped config
   actually feeds the helper. (d) Fix scope: helper. Either accept YAML via
   `yaml.safe_load` when path ends `.yaml`/`.yml`, or ship JSON-only fixtures
   and update the README.

2. **`check_prereqs.py` mis-classifies recoverable codes as fatal.** (a)
   Iterates every `config_keys` entry from `router_contract.json` and treats
   absence as a `blocker`; sets `status="blocked"` if any non-`SLHA_MISSING_HINT`
   blocker exists. SKILL.md says `MICROMEGAS_MISSING`, `DRAKE_PATH_UNSET`,
   `DRAKE_MISSING` are *recoverable* notices, not fatal. (b)
   `scripts/check_prereqs.py:140-141` (`hard_blockers = [b for b in blockers
   if b["code"] != "SLHA_MISSING_HINT"]`). (c) Severity: **blocker** for the
   router's intended workflow — a user with MadDM but no micrOMEGAs/DRAKE will
   be told "blocked" at Step 1 even though SKILL.md prose says continue. (d)
   Fix scope: contract + helper. `router_contract.json` should annotate each
   `config_keys` entry with `severity: fatal | recoverable`; helper should
   compute `hard_blockers` from that annotation, not from a hard-coded
   `SLHA_MISSING_HINT` list.

3. **No blocker code exists for "UFO is structurally invalid".** (a) The
   Dark SU(3) UFO emits `f(dt1,dt2,dt3)` color tensors that MG5 cannot parse.
   The router silently delegates to `/maddm` and inherits the cryptic
   `NameError: name 'dt1' is not defined`. No prereq guard runs the UFO
   through `import particles` to detect this before invoking MG5. (b) Helper
   surface — would belong in `check_prereqs.py` or a new `validate_ufo.py`.
   (c) Severity: **major** — every confining-sector or extended-color-group
   user will hit this; the cryptic error is downstream-surface, not router-
   surface. (d) Fix scope: new helper `validate_ufo.py` that does
   `python -c "import particles; import vertices"` against `ufo_path`, plus
   a router-contract code `UFO_IMPORT_INVALID` mapped to `/sarah-build` fixit.

4. **No blocker code for "ANALYTIC_MODULE_MISSING / spec backend stub".** (a)
   `dark_su3/spec.yaml` declares `backends.spectrum: analytic;
   analytic_module: analytic_models.stub_unimplemented` but neither
   `/sarah-build` nor `/dark-matter-constraints` checks whether the analytic
   module exists; the router happily takes the (massless, broken) UFO and
   hands it to MadDM. (b) Cross-skill — affects the router AND `/sarah-build`.
   (c) Severity: **major** for confining sectors, low otherwise. (d) Fix
   scope: add a `spec.backends.spectrum == "analytic"` branch to
   `check_prereqs.py` (model-agnostic check: file existence of
   `analytic_module`); add `ANALYTIC_MODULE_MISSING` row to SKILL.md blocker
   table.

5. **SARAH DarkSU3 output corruption (upstream).** (a) `/Users/yianni/SARAH/
   SARAH-4.15.3/Output/DarkSU3/EWSB/UFO/particles.py` contains 3x
   `None = Particle(pdg_code = None, ...)` blocks (Python `SyntaxError`) plus
   `mass = Param.$Failed` literal Mathematica leakage. The dark fermion
   `psiD` is silently merged into one of the `None` blocks. (b) Upstream of
   router; SARAH model file at `/Users/yianni/SARAH/SARAH-4.15.3/Private-Models/
   DarkSU3/DarkSU3.m` declares the SU(3)_dark gauge group with no scalar to
   break it, then EWSB rotation fails. (c) Severity: **major** for the
   DarkSU3 model specifically; symptomatic of the `/sarah-build` →
   `/dark-matter-constraints` handoff being unverified. (d) Fix scope:
   `/sarah-build` should ship a post-build smoke check `python -c "import
   particles, vertices"` and refuse to claim success if it fails. The
   different (clean) UFO at `~/.local/share/hep-ph-agents/models/dark_su3/`
   exists, suggesting two SARAH passes happened — we should not have a stale
   broken copy under `~/SARAH/Output/`.

6. **SKILL.md sibling-skill paths are aspirational.** (a) SKILL.md repeatedly
   refers to `/maddm`, `/micromegas`, `/drake`, `/sarah-build`, `/spheno-build`
   without any indication that they live in *different* plugins
   (`monte-carlo-tools`, `model-building`, `constraints`). A new user invoking
   `/dark-matter-constraints` cannot grep `plugins/constraints/skills/` for
   `/maddm`. (b) `plugins/constraints/skills/dark-matter-constraints/SKILL.md`
   §"Cross-skill dependencies" table. (c) Severity: **minor** — discoverability
   only. (d) Fix scope: add plugin-qualified paths in the table, e.g.
   `monte-carlo-tools/skills/maddm` next to `/maddm`.

7. **`pytest` install on this machine has a broken `py` module.** (a)
   `python -m pytest ...` fails with `AttributeError: module 'py' has no
   attribute 'path'`. (b) System-wide pyenv environment, not the repo. (c)
   Severity: **minor** — `pytest <args>` (calling the binary directly) works
   and the suite passes 65/3xfail/3xpass. (d) Fix scope: out of repo —
   user pyenv hygiene.

8. **The `tests/fixtures/dark_su3_playtest/ufo/darkSU3/` "sentinel" makes the
   helpers happy but tells the LLM nothing.** (a) `check_prereqs` is
   satisfied by an empty directory existing; the directory matches the
   contract's `path_or_bool` check via `os.path.exists`. So the ufo_path
   guard is no guard — it doesn't tell the user the UFO is empty / corrupt /
   missing critical files. (b) `scripts/check_prereqs.py:115-126`. (c)
   Severity: **major** in conjunction with bug 3. (d) Fix scope: the
   helper's UFO check should at minimum verify presence of `particles.py` /
   `vertices.py` / `__init__.py`, and ideally do a Python import smoke test
   in a sub-process. Both are mechanical, model-agnostic, and safe per the
   ROUTING_LENS — no physics judgment required.

9. **Step 5 Branch 2 contract drift documented but not fixed.** (a)
   `contracts/router_contract.json` `status_enums` entry for
   `drake_install_detect_status` notes "router Step 5 Branch 2 reads
   activation_required from detect — topology mismatch. WS-4 W4-E must
   reconcile." This is a 3xpassed test, so the verifier knows. (b)
   `contracts/router_contract.json:155`. (c) Severity: **minor** in this
   cycle (DRAKE not installed anyway), would be **major** if a user has
   DRAKE installed but unactivated. (d) Fix scope: producer skill
   `/drake-install` should add `activation_required` to its detect output,
   or router should read from `use-path` instead.

10. **No router-level "dry run" mode exists.** A user cannot ask the router
    "what would you do for this model + spec, given my installed tools?"
    without committing to the side-effects. Helps would be useful for
    onboarding (which is exactly when the helpers + sibling skills are most
    likely to be misaligned). Severity: **minor**, fix scope: SKILL.md prose
    addition + tiny helper.

---

## 7. What's needed to finish

Concrete punch list, roughly ordered by impact:

### To run /dark-matter-constraints end-to-end on Profumo's Dark SU(3) Fig. 8

1. **Implement `analytic_models/dark_su3.py`** that takes (MpsiD, gD, mV, mphi)
   and emits an effective UFO with phi (scalar DM, PDG TBD) and V (vector
   mediator, PDG TBD) as elementary fields, plus a SLHA-style spectrum block.
   Spec.yaml flags this `TODO`. Likely a few-hundred-line Python file
   (FeynRules-equivalent of the chiral effective theory). Time estimate: 1–2
   days, requires HEP+SARAH skill.
2. **Fix the `dt1`/`dt2`/`dt3` color tensor problem in SARAH output** (or
   document that confining sectors must use the analytic backend, period).
   Likely SARAH version-dependent; may need a workaround in `/sarah-build`
   to post-process vertices.py and rewrite `f(dt1,...)` as `1` (treats dark
   gauge bosons as effectively SM-color singlets — phenomenologically OK
   when computing relic of the *composites*, not the UV fields). Time: 0.5
   day.
3. **Install micrOMEGAs.** Project memory tags it as the validator. Standard
   install via `/micromegas-install`. Time: 30 min wall clock.
4. **Install DRAKE.** Required for the resonance benchmark per SKILL.md
   Step 5; and per `project_dm_tool_roles` is the *whole point* of this
   benchmark. Time: 30 min if Wolfram Engine is already activated (it is).

### To make the router robust on this machine

5. **Bug 1 (YAML config)** — 30 min helper edit.
6. **Bug 2 (recoverable vs fatal)** — annotate `router_contract.json` and
   patch `check_prereqs.py`; ~1 hour.
7. **Bug 3 / Bug 8 (UFO import smoke check)** — new helper
   `validate_ufo.py` plus contract row; ~2 hours.
8. **Bug 4 (analytic_module guard)** — coordinate with `/sarah-build`; ~1 hour.
9. **Bug 6 (sibling-skill paths)** — SKILL.md prose edit; 15 min.
10. **Re-run cycle 1 once 1–4 + 5–8 are done** — should produce real
    Ωh² (MadDM), Ωh² (micrOMEGAs cross-check), Ωh² (DRAKE narrow-resonance
    Boltzmann solve), and a comparison plot vs Profumo Fig. 8. Time: ~1 day
    once prerequisites are in place.

### To validate the report skeptically

- Pre-empt a reviewer asking "why didn't you just run /sarah-build to
  regenerate the UFO?" — answer: the `dt1` color-index issue is intrinsic
  to UFO + SARAH for second-SU(3) gauge groups; rerunning SARAH will
  reproduce the same defect. Verified by inspecting the *clean*
  `~/.local/share/.../DarkSU3/` UFO (which is already a successful SARAH
  build, evidenced by 48 particles with no `None` orphans) — it *still*
  contains the broken `f(dt1,...)` lines. So this isn't a build hiccup, it's
  a structural limitation that needs a workaround.
- Pre-empt "did you really need micrOMEGAs / DRAKE to ship the report?" —
  answer: no, but the user's stated goal (Profumo Fig. 8 reproduction) is
  *only* a meaningful test if DRAKE is involved, since the resonance
  benchmark is the reason DRAKE was chosen at all. A relic-only Dark SU(3)
  number from MadDM alone would be physically wrong (velocity-expansion
  fails in the resonance band) and the router would silently emit it
  without flagging the regime issue (Step 5 requires DRAKE_MISSING to be
  surfaced as a notice — that part works, but the user has no fallback).

---

## 8. Handoff

Log of every event with timestamps lives at
`.shift-manager/run-20260425-dmc/playtest/playtester_cycle1_log.md` (sibling
file). Working artifacts under `.../playtest/work/`:

- `config_real.json`, `config_darksu3.json`, `config_singletdoublet.json` —
  JSON configs constructed because the YAML fixtures don't load.
- `setup_darksu3.mg5` — failing MG5 setup script (reproduces bug 3).
- `setup_sd.mg5`, `launch_sd.mg5` — passing SingletDoublet scripts.
- `maddm_sd_run1/output/run_01/MadDM_results.txt` (Omegah2=-1 sentinel)
- `maddm_sd_run1/output/run_02/MadDM_results.txt` (Omegah2=0.292 with SLHA
  overlay) — the MadDM-half-works witness.

No edits made to any SKILL.md, helper, or contract file in this cycle, per
the task constraints. All findings filed against the report rather than
patched in place.
