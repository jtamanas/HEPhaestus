# 2HDM+a playtest round — 2026-04-26 (full record)

Canonical aggregation of the four parallel-workstream playtests that
exercised `/demo → 2hdm-a → {relic,dd,id,collider}` end-to-end on
2026-04-26. Each workstream ran in an isolated worktree under
`.claude/worktrees/`; the original narrative logs are preserved
verbatim below with brief intros. For the rolled-up sharp edges, see
`plugins/hep-ph-toolkit/skills/2hdm-a/sharp-edges.md`. For the
higher-level framing, see the corresponding entry in
`docs/devlog.md`.

| WS | Worktree | Final commit | Outcome |
|---|---|---|---|
| relic | `.claude/worktrees/agent-aa0dba254bcf80001` | `542e130` | **SUCCESS** — Ω h² = 10.493759 reproduced via `/demo` end-to-end at off-resonance benchmark |
| dd | `.claude/worktrees/agent-afc1d0ee1a5c3278b` | `aa38e45` (r2) | BLOCKED — 8 distinct blockers mapped; `Vertex::ChargeViolating` warnings evidence-verified |
| id | `.claude/worktrees/agent-a1acbc7b9ecb28aa6` | `97d6a94` (r2) | BLOCKED — 4 real blockers; `/gamlike` is the unblock (double, not triple — dark-su3 excluded) |
| collider | `.claude/worktrees/agent-a9c67d36cdb20a0b4` | `c494507` | placeholder by design — locked in 3 places, byte-identical across all 3 demo models |

---

# Part 1 — WS-relic: 2HDM+a /demo relic playtest

Source: `agent-aa0dba254bcf80001/docs/2hdma-playtest-relic-2026-04-26.md`,
commit `542e130`. **Outcome: PASS.** Ω h² = 10.493759 at the
off-resonance benchmark `(M_χ=100, M_a=400, g_χ=1.0, tan β=10)`,
matching benchmark central 10.493 to 4 sig figs.

Synthetic answers (per memory `feedback_demo_playtest_noninteractive`):
- Step 2 gate "Ready to begin?" → `continue`
- Step 3 model picker → `2hdm-a`
- Per-model Step 2 constraint multi-select → `relic`
- Per-model Step 3 gate (READY) → `go`

## Step 0 — Preflight

config.json read OK (`~/.config/hep-ph-agents/config.json`); all required
keys present and non-empty: `madgraph_path`, `sarah_path`, `spheno_path`,
`wolfram_engine_path`. Tool versions: SARAH 4.15.3, MG5 3.5.6, MadDM
3.2.13, Wolfram 14.3.0, SPheno 4.0.5.

## Steps 1 / 2 / 3

Simulated (non-interactive). User chooses `continue → 2hdm-a → relic → go`.

## Step 4a — Deploy (idempotent)

`$SARAH_ROOT/Models/TwoHdmAfix/` already up-to-date with the 4 fixture .m
files. No copy needed.

## Step 4b — SARAH

Already built; UFO present at `$SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/`.
`grep -c chi vertices.py` returns 3 (the three chi-chibar-Ah[1,2,3]
vertices). SARAH lock not engaged.

## Step 4c — MadDM (relic) — RESUMED 2026-04-26 14:00 UTC

Prior agent stalled here and was watchdog-killed at 600s of stream silence
while waiting on a foreground subprocess. Resume strategy: split the MadDM
invocation into background scripts and poll via Monitor / short tail
commands so each tool call counts as stream activity.

**Phase 1 (output):** `mg5_aMC --mode=maddm setup.mg5` where setup.mg5 is

```
import model $SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO
define darkmatter chi
generate relic_density
output demo_output/2hdm-a/maddm_run/output
exit
```

Completed in ~60-70s. Wrote `Cards/param_card.dat`.

**Patcher:** `python3 plugins/hep-ph-toolkit/skills/2hdm-a/scripts/patch_paramcard.py
demo_output/2hdm-a/maddm_run/output --Mchi 100.0 --Ma-Ah2 400.0 --gchi 1.0 --tan-beta 10.0`

Sets `PHASES[1] = 1.0` (real part of PhasechiR), all 6 mixing matrices to
identity, BSM widths >= 1 GeV, MASS block for chi/Ah2/Ah3/hh1/hh2/Hm2, and
Hm1=Mw=80.4 GeV (charged-Higgs Goldstone alignment).

**Phase 2 (launch):** `mg5_aMC --mode=maddm launch.mg5` where launch.mg5 is

```
launch demo_output/2hdm-a/maddm_run/output -f
exit
```

Completed in ~2 minutes (deeply off-resonance, no Romberg hang).

**Result: Omega h^2 = 10.493759.**

| Channel | %     |
|---------|-------|
| wphp    | 49.62 |
| wmhm    | 49.62 |
| bbx     | 0.65  |
| ccx     | 0.06  |
| tamtap  | 0.04  |
| sum     | 99.99 |

Matches benchmark `off-resonance-2hdma-004/expectations.json` central
(10.493) within 0.0007 — well inside the ±5% pipeline tolerance (and the
±15% physics tolerance). SKILL.md headline (10.15) is the older iter-8
value; cycle-1 / current code emits 10.494 deterministically.

## Step 4d / 4f — Plot + summary

`demo_output/2hdm-a/summary.{pdf,png}` produced via `make_summary_plot.py`;
horizontal bar chart of channel contributions (top 6 visible).
`summary.json` written per schema (the round-1 emission was missing
`schema_version` — flagged by reviewer as cross-cutting infra debt; see
sharp-edges SE-INFRA-1).

## Outcome

Status: **PASS**. End-to-end relic-density pipeline reproduced without
code changes from `eb21aec` baseline. Sharp edge logged for the
watchdog stall pattern (SE-INFRA-4).

---

# Part 2 — WS-dd: 2HDM+a /demo direct-detection playtest (round 1 + round 2)

Source: `agent-afc1d0ee1a5c3278b/docs/2hdma-playtest-dd-2026-04-26.md`,
commit `aa38e45`. **Outcome: BLOCKED.** 8 distinct blockers mapped;
`Vertex::ChargeViolating` warnings evidence-verified in r2.

## Synthetic Q&A transcript

| Step | Question (skill prompt) | Synthetic answer |
|---|---|---|
| /demo Step 0 | "Preflight check: confirm config has the 4 required keys (sarah_root, model_dir, runs_dir, tools_dir) and executables exist?" | PASS — config.yaml shows all 4; `which wolframscript / sarah / madgraph` resolve |
| /demo Step 1 | "Paper-intro narration; press to continue" | (text-only acknowledgement) |
| /demo Step 2 demo gate | "continue / cancel" | `continue` |
| /demo Step 3 model picker | "Pick a model: 2hdm-a / dark-su3 / singlet-doublet / ..." | `2hdm-a` |
| /2hdm-a Step 1 | "Candidate declaration (display-only)" | (text-only acknowledgement) |
| /2hdm-a Step 2 constraint multi-select | "Pick constraints: relic / dd / id / collider" | `["dd"]` |
| /2hdm-a Step 3 BLOCKED gate | "dd is BLOCKED (missing /spec-authoring-incomplete, /feynarts, /formcalc). Choose: `run_ready` / `back` / `cancel`" — note: **no `go` option offered** when any constraint is blocked | `run_ready` (drops dd from the run set, proceeds with empty READY subset) |
| /2hdm-a Step 4 (auto-run) | (no question; skill auto-runs Step 4a-4f based on Step 3 outcome) | Step 4 walks 4a (deploy fixture) → 4e (DD/ID placeholder: write skipped to summary) → 4f (write `summary.json`); exits |

The Step-3 BLOCKED gate **is the artifact under test**: it is the
choke point. There is no "go anyway" branch in the skill, so the
playtest documents the refusal and forces the path forward manually
for the rest of the narrative.

## Refusal mechanism (the blocker gate)

**Stage:** /2hdm-a Step 3 gate.
**Symptom:** When user selects only DD, the gate offers `run_ready / back / cancel`,
not `go`. `run_ready` drops blocked constraints and proceeds with the READY subset
(empty when DD-only), so Step 4 reduces to "write summary.json with dd skipped".
**Category:** spec gap — the skill has no DD execution body. Step 4e is a placeholder
("DD and ID branches (BLOCKED). Record these as skipped in summary.json"). There is
no DD code in the skill at all.
**Clearing it:** would require *both* a DD execution body in the skill AND the
upstream chain (FeynArts → FormCalc → looptools-eval → DDCalc) to actually exist
and emit `scattering/v1` JSON.

## Blocker map (8 blockers)

### Blocker 1 — /2hdm-a Step 3 gate hard-refuses dd (constraint-gate refusal)
- **Source:** SKILL.md lines 162-175 (BLOCKED gate), 476-481 (Step 4e DD/ID
  placeholder); `_shared/constraints.yaml:722-734`
  (`spec_authoring_blockers.dd: ["spec-authoring-incomplete"]`).
- **Stale claim:** demo SKILL.md says `/feynarts`, `/formcalc`, `/ddcalc` are
  PLANNED; in fact all three have mature SKILL.md files (only `/gamlike` is
  fully missing).

### Blocker 2 — /feynarts logic bug: resolve_model precedes _run_make_feynarts
- **Symptom:** `FEYNARTS_SARAH_STATE_MISSING` blocker on first run.
- **Source:** `run_feynarts.py:130-178`. `resolve_model()` (line 132) is
  called before `_run_make_feynarts()` (line 163).
- **Fix:** restructure to call `_run_make_feynarts()` before `resolve_model()`
  when sarah_model is provided AND state-dir missing — ~10 lines.

### Blocker 3 — `flock` not available on macOS
- **Symptom:** `(eval):14: command not found: flock`. Exit code 127.
- **Source:** `2hdm-a/SKILL.md:247` (`flock -x -w 120 .../sarah.lock
  wolframscript ...`).
- **Effect:** documented SARAH-mutex behavior is silently a no-op on macOS.
  Two unrelated Wolfram kernels (SingletDoublet, DarkSU3) were observed
  running concurrently during the playtest (round-1 wrongly framed these
  as WS-* sibling agents; they were unrelated dev processes — corrected
  in r2).
- **Fix:** Homebrew util-linux + opt path `/opt/homebrew/opt/util-linux/sbin/flock`,
  or Python `fcntl.lockf` wrapper.

### Blocker 4 — /feynarts has no SARAH-particle alias resolution despite docstring
- **Source:** `resolve_process.py:5-6` docstring; `state_root` parameter at
  line 152 declared but never used.
- **Workaround:** raw FeynArts tuple form (`{{F[1,{...}], -F[1,{...}]}, ...}`)
  — but the SARAH-internal field index for `chi` and the DM PDG (9989932)
  aren't documented in /2hdm-a SKILL.md.
- **Fix:** implement the loader the docstring promises, OR auto-emit
  `tables/<sarah_model>.json` during `MakeFeynArts[]`. ~1-2 hours.

### Blocker 5 — No /looptools runtime skill: FormCalc → scattering/v1 bridge missing
- **The biggest single missing piece in the chain.**
- **Source:** `plugins/hep-ph-toolkit/skills/looptools-install/` exists
  (build/detect skill); `plugins/hep-ph-toolkit/skills/looptools/` does NOT
  exist. Only test fixture references `source: "looptools"`; no runtime
  emits it.
- **Fix:** implement `/looptools eval` (1 sprint, 5-10 days; r1's "1-3 days"
  was widened in r2 per reviewer MAJOR-5):

| Sub-task | Hours |
|---|---|
| 1a. Load `amp_reduced.m` (FormCalc PV heads) | 4-8 |
| 1b. Construct `chi N → chi N` kinematics at q²=0 | 4-8 |
| 1c. Substitute nucleon-quark form factors (default_2018 or A1) | 8-12 |
| 1d. Numerically evaluate A0i/B0i/C0i/D0i via LoopTools | 12-20 |
| 1e. Emit `scattering/v1` JSON with `source: "looptools"` | 4-8 |
| 1f. Schema validation + kinematic regression tests | 8-16 |
| 1g. End-to-end smoke test against `/ddcalc run` | 4-8 |
| **Subtotal** | **44-80 hr (5-10 days)** |

- **SARAH-side risk callout:** sub-task 1d's correctness depends on FeynArts
  emitting physics-correct vertices. If `Vertex::ChargeViolating`
  warnings (Blocker 6 below) reflect a real `ZA`/`ZP` rotation-matrix
  convention bug, sub-task 1d may produce numerically silent errors in
  Wilson coefficients. Vertex-by-vertex audit against a reference 2HDM+a
  UFO is a **prerequisite**, not folded into the 5-10 day estimate.

### Blocker 6 — SARAH `MakeFeynArts[]` writes to canonical SARAH path, not state-root
- **Symptom:** SARAH writes `TwoHdmAfixEWSB.mod` (33k bytes) to
  `$SARAH_ROOT/Output/TwoHdmAfix/EWSB/FeynArts/`. Nothing in the
  `feynarts_state` directory the template `SetDirectory[...]`'d to. Also a
  name mismatch (SARAH appends `EWSB`).
- **Workaround tested:** symlinking
  `$STATE_DIR/TwoHdmAfix.mod -> $SARAH_OUTPUT/.../TwoHdmAfixEWSB.mod`
  passes `resolve_model` but uncovers Blocker 7.
- **Note on warnings (round-2 verified):** during this `MakeFeynArts[]` run,
  SARAH emitted `Part::pkspec1`, `Part::partw`,
  `Vertex::ChargeViolating`, and `FeynArts::NoNumber` warnings on
  TwoHdmAfix. The `Vertex::ChargeViolating` warnings target
  `{Ah, conj[Hm], conj[VWp]}`, `{hh, conj[Hm], conj[VWp]}`, and
  `{Ah, conj[Hm], conj[VWp], VP}` — vertices that ARE physically
  charge-conserving in 2HDM. Most plausible cause: a `ZA`/`ZP`
  rotation-matrix convention bug in the hand-crafted `.m` files. The
  warnings do **not** prevent the .mod from being written (33k bytes
  successfully emitted), but the .mod might still be wrong. See
  sharp-edges.md SE-2HDMA-MODEL-1 for the full evidence-backed analysis.
  Round-2 evidence: `dd_attempts/feynarts_v3/sarah.log` lines 121, 123, 129.

### Blocker 7 — `cache_key.py` crashes on empty gen_path
- **Symptom:** `IsADirectoryError: [Errno 21] Is a directory: '.'` from
  `_sha256_file('')` at `cache_key.py:25-29`.
- **Fix:** add `if not path: return _sha256_str("")` at top of
  `_sha256_file`. 1-line fix.

### Blocker 8 — Stale "[PLANNED]" markers in /demo and /2hdm-a SKILL.md
- **Source:** `demo/SKILL.md:39,73`; `2hdm-a/SKILL.md:58,144,480`. Constraints
  YAML is half-stale: `feynarts.status: planned`,
  `formcalc.status: planned`, `ddcalc.status: exists`.
- **Fix:** smoke-test FeynArts and FormCalc end-to-end (gated golden tests
  with `HEPPH_RUN_WOLFRAM_TESTS=1`); if pass, flip the constraints.yaml
  status fields and update the SKILL.md prose.

## Concurrency observations

Two unrelated Wolfram kernels were observed running on the system during
this run (NOT the parallel WS-* workstreams, which all targeted
2HDM+a): pid 33372 evaluating `Start["SingletDoublet"]; ... MakeUFO[];
MakeSPheno[]`; pid 34594 evaluating `Start["DarkSU3"]; ...
MakeUFO[]`. These were leftover dev processes from prior sessions on
unrelated models. The `flock`-no-op finding is platform-agnostic:
without `flock`, multiple SARAH sessions can run simultaneously on the
shared `$SARAH_ROOT/Output/<Model>/` path regardless of any documented
mutex protocol.

## Renderer-backport debt callout

Per `demo_output/2hdm-a/fix_loop/POST_MORTEM.md` §"Remaining debt"
item 1, the loop-only DD chain is also blocked on a `/sarah-build`
renderer backport: the 2hdm-a YAML spec cannot yet emit a
physics-correct UFO with the PortalDM idiom required for a Dirac
SM-singlet. The current relic path uses a hand-crafted SARAH model
fixture (`fixtures/sarah_model/TwoHdmAfix.m` etc.), not a
renderer-emitted UFO. For DD the same constraint applies: even when
the upstream tooling chain is complete, the SARAH model needs to be
the hand-crafted fixture. Renderer backport is tracked in the
POST_MORTEM as ~1-2 days of medium-effort work. For DD to be a
*first-class* /demo output (not just "works because we hand-crafted
the model"), the renderer backport is also a prerequisite — but it's
not the binding constraint today; Blocker 5 (missing /looptools) is.

## Stop condition

Hit 8 distinct blockers (target was 5+); diminishing returns.

## Prioritized punch list (r2 — re-ranked by unlock value, with parallelism)

| Rank | Blocker | Effort | Parallel with | Reason |
|---|---|---|---|---|
| 1 | **5** — `/looptools eval` runtime skill | **1 sprint (5-10 days)** | #2, #3, #4, #6, #7 | Binding constraint; FeynArts+FormCalc are dead-end without it |
| 2 | **7** — `cache_key.py` empty-gen guard | 1 line, ~5 min | #1, #3, #4, #6, #7 | Trivial; restores reproducibility for #2 verification |
| 3 | **2** — `/feynarts` cold-cache control flow | ~10 lines | #1, #4, #6, #7 | Restores documented auto-trigger |
| 4 | **6** — SARAH→FeynArts state-dir adapter | ~30 min | #1, #2, #3, #4, #6, #7 | Closes path mismatch |
| 5 | **4** — SARAH-particle alias loader | 1-2 hr | #1, #2, #3, #6, #7 | Saves users from raw FeynArts tuples |
| 6 | **1** — `/2hdm-a` Step 4 DD body + Step 3 "go" option | 2-4 hr | Drafting can run in parallel with #1; integration test depends on #1-#5 having landed | Final wiring |
| 7 | **3** — replace `flock` with portable mutex | ~1 hr | #1-#6 | Affects all SARAH paths, not just DD |
| 8 | **8** — flip status flags + SKILL.md prose | ~30 min | Lands LAST, after #1-#7 verified end-to-end | Documentation honesty |

**Critical-path observation:** #1 at 5-10 days is on the critical path.
Items #2-#5 are cheap and fan out: they can run in parallel with #1,
sharing no files. Recommended allocation: one engineer on #1 from day
0; another picks off #2-#5 in any order, then #6 (which needs #1-#5
done), then #3 polish, then #8.

---

# Part 3 — WS-id: 2HDM+a /demo indirect-detection playtest (round 1 + round 2)

Source: `agent-a1acbc7b9ecb28aa6/docs/2hdma-playtest-id-2026-04-26.md`,
commit `97d6a94`. **Outcome: BLOCKED.** 4 real blockers + 2
opportunities/notes + 2 follow-up findings = 8 total observations.

## Synthetic interview replay

| Step | Gate | Synthetic answer | Observation |
|------|------|------------------|-------------|
| 0 | Preflight | n/a | All four config keys present and executables respond. PASS. |
| 1 | Paper intro | n/a | Static text. |
| 2 | "Ready to begin?" | `continue` | OK |
| 3 | Model picker | `2hdm-a` | OK; warning text says "currently BLOCKED" but per-model Step 3 owns the gate. |
| → per-model Step 1 | DM-candidate declaration | n/a | OK |
| → per-model Step 2 | Constraint multi-select | `["id"]` | Validation passes (non-collider option selected). |
| → per-model Step 3 | Time/prereq + gate | `go` (→ effectively `run_ready`) | All selected blocked → only `run_ready/back/cancel` offered, not `go`. **Convention mismatch** (B5). |
| → per-model Step 4 | Execute READY subset | (empty) | No execution branch defined for empty-READY case (B1). |

## Blocker catalogue

### B1 — Empty-READY execution path is undefined for ID-only selection
- **Source:** `2hdm-a/SKILL.md:200-203, 494-510`.
- **Severity:** minor (recoverable; schema accepts `ran=[]`).
- **Empty-READY summary validation (round 2 correction).** The round-1
  draft of `demo_output/2hdm-a/summary.json` was missing the required
  `schema_version` field, so direct validation against
  `_shared/summary.core.schema.json` returned `INVALID:
  'schema_version' is a required property` (exit 1). The round-1
  "verified locally" claim was untested — the validator was never
  actually run against the emitted file in round 1. Round 2 fix:
  added `"schema_version": "1"`, re-ran the validator: now `VALID`
  (exit 0) against `_shared/summary.core.schema.json` and against the
  model-specific `2hdm-a/summary.schema.json`.

### B2 — `time_budget.py` chain disagrees with SKILL ID chain
- For `--model 2hdm-a --constraints id`, helper prints:
  `/sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS] → /gamlike [PLANNED]`
- But SKILL ID chain table (line 59) reads:
  `fixture copy → /madgraph [EXISTS] → /maddm [EXISTS] → /gamlike [PLANNED]`
- **Cause:** no `chain_overrides.id` for `2hdm-a` in
  `_shared/constraints.yaml`; `dark-su3` has one (760+).
- **Severity:** medium — user-facing time table mismatch.
- **Fix:** add `2hdm-a.chain_overrides.{relic,id}` mirroring dark-su3
  pattern.

### B3 — `spec_authoring_blockers.id` is over-broad
- `constraints.yaml:724-725` lists `id: ["spec-authoring-incomplete"]`,
  but the *actual* blocker for ID is `/gamlike`. The SARAH fixture that
  unblocked relic also generates the UFO MadDM uses for `generate
  indirect_detection`.
- **Severity:** medium — misleading marker.
- **Fix:** remove `id` from `spec_authoring_blockers`; let
  `tools.gamlike.status: planned` carry the block.

### B4 — `/gamlike` and `/nulike` skill directories do not exist
- `find plugins -type d -name gamlike -o -type d -name nulike` returns
  no hits. `constraints.yaml:647-656` declares both with `status:
  planned` and time ranges, but no skill folder, no SKILL.md, no
  scripts directory.
- **Severity: definite blocker** — the documented chain endpoint is
  unimplementable as written.

### B5 — Gate option set for blocked path lacks `go`
- Step 3 offers `{run_ready, back, cancel}` when any selected
  constraint is BLOCKED — no `go`. Playtest convention "answer `go` to
  blocker gates" therefore aliases to `run_ready`.
- **Severity:** minor (convention-level), no behavior bug.
- **(Reclassified r2 as nit, not real blocker.)**

### B6 — Conceptual gap: `/gamlike` may be largely subsumed by MadDM 3.2.13

The interesting angle. Inventory of `/Users/yianni/MG5_aMC_v3_5_6/PLUGIN/maddm/`:
- `Fermi_Data/` — Pass-8 6-year dSph likelihoods.
- `Fermi_line_likelihoods/` — line-search likelihood tables (R3, R16, R41, R90 ROIs).
- `Jfactors/jfactors.dat` — J-factors per dSph target.
- `ExpData/MadDM_Fermi_Limit_<chan>.dat` channel-wise upper limits, plus HESS lines, LZ, XENON, PICO data.

In `maddm_run_interface.py`:

| Capability | Method/line | Notes |
|------------|-------------|-------|
| PPPC4DMID spectra loader | `class Spectra` (~265) | EW-correction variant supported |
| Pythia8 spectra path | `read_PPPCspectra()`, `_spectrum_pythia8.dat` writer (~2561, 3331) | Auto-runs Pythia8 when configured |
| Fermi dSph limit comparison | `~3546-3564` | Writes `Fermi_Likelihood = …` to `MadDM_results.txt` |
| Line-search likelihoods | `gamma_line_spectrum`, `merge_lines`, `~2390-2461` | Includes line-merging logic |
| Flux at Earth (e±, p̄, ν) | `calculate_fluxes`, `~2739` | Per-channel `dPhi/dE` |
| Per-spec text dumps | `save_spec_flux`, `~3320` | `<channel>_spectrum_<method>.dat`, `<channel>_dphide_<method>.dat` |

**Conclusion.** Wiring a placeholder `/gamlike` to "consume MadDM
spectra and emit a Fermi-LAT exclusion verdict" is feasible without
touching MadDM: just parse `MadDM_results.txt` for `Fermi_Likelihood`
and the per-channel limits, and attach a YAML/JSON to `summary.json`.

The "real" /gamlike (Snowmass GamLike code by Cirelli et al.) gives
finer-grained Galactic-center / extragalactic background analysis
than MadDM's dSph-only limit. That additional capability is not
blocking the 2HDM+a demo's ID story; the dSph upper limit alone is
the standard plot-axis exclusion.

### B7 — `time_budget.py:281` renders pseudo-marker tokens with literal `/`

Round-2 follow-up. `_shared/time_budget.py:281` does
`missing_strs = ", ".join(f"/{p}" for p in row.missing)` —
unconditional `/` prefix. When the helper injects a marker like
`spec-authoring-incomplete`, the renderer prints `BLOCKED — missing:
/spec-authoring-incomplete, /gamlike` with a literal slash that
masquerades as a fake skill name.

### B8 — Schema duality: legacy `_shared/summary.schema.json` lacks `schema_version`

Round-2 follow-up to fix #1. The repository ships **two** summary
schemas that conflict on `schema_version` requirements (legacy fails
canonical, with `additionalProperties: false`). Per-model schemas
correctly compose the core via `allOf` + `$ref`. `test_summary_schema.py`
validates stubs against the legacy. Out-of-scope to fix in r2.

## Stop condition

Reached **definite blocker** B4 (`/gamlike` literally absent) on the
documented path, and mapped 4 real blockers (B1-B4) before stopping
(≥5 mapped if you include opportunity B6 — but the honest count is 4
real blockers + 1 nit + 1 opportunity + 2 follow-up findings).

## Punch list (round-2 corrected)

| # | Item | Cost | Unblocks |
|---|------|------|----------|
| 1 | Ship `/gamlike` v0 — a thin MadDM-output formatter that parses `MadDM_results.txt` for `Fermi_Likelihood`, `flux_<n>` rows, and per-channel `<σv>` against `MadDM_Fermi_Limit_*.dat`; emits `gamlike.json` per ID run. | **1-2 days for shippable v0** (SKILL.md scaffold + JSON output schema + validation gates + `constraints.yaml` chain wiring + cross-model regression test + the `Fermi_Likelihood(Thermal)` xsi<1 conditional-emission gotcha + playtest pass) | **Double-unblock: 2HDM+a ID + singlet-doublet ID** (both run MadGraph/MadDM end-to-end). **Does NOT unblock dark-SU(3) ID** — see Caveat below. |
| 2 | Add `chain_overrides.{relic,id}` to 2hdm-a in `constraints.yaml` (mirror dark-su3 pattern). | 15 min | Truthful time-budget output. |
| 3 | Drop spurious `id: spec-authoring-incomplete` marker from 2hdm-a. | 5 min | Cleaner blocker reason text. |
| 4 | Add empty-READY section to SKILL Step 4 (1 paragraph + example summary.json). | 10 min | Documented path for ID-only / DD-only. |
| 5 | Document the playtest-convention `go` ↔ `run_ready` aliasing. | 10 min | Cleaner playtest replays. |
| 6 | Optional: bring real GamLike (Cirelli et al.) into scope as a v2 of `/gamlike`. | 1-2 days | Galactic-center + extragalactic exclusions beyond dSph. |

**Caveat: dark-SU(3) is excluded from /gamlike's reach** (round-2
correction). Per `_shared/constraints.yaml:768-770`: "Dark SU(3)_D is
non-SM color; MadGraph/MadDM cannot generate the coannihilation set."
Dark-SU(3)'s relic chain bypasses MadGraph/MadDM and runs through the
analytic `/dark-matter-constraints` backend; ID has no MadDM run at
all. So there is no `MadDM_results.txt` for `/gamlike` to parse on
dark-SU(3). Round-1 framed item 1 as a "triple-unblock" for all three
demo models — that was wrong; the correct framing is **double-unblock**
(2hdm-a + singlet-doublet only). Singlet-doublet's ID-side MadDM
emission of `Fermi_Likelihood` rows was not empirically verified.

---

# Part 4 — WS-collider: 2HDM+a collider observable playtest

Source: `agent-a9c67d36cdb20a0b4/docs/2hdma-playtest-collider-2026-04-26.md`,
commit `c494507`. **Outcome: placeholder by design.** Locked in 3
places, byte-identical across all 3 demo models.

## TL;DR

The 2HDM+a "collider" entry is a **menu placeholder** with a single
non-execution contract repeated in three places (per-model SKILL Step
2, the constraint registry in `_shared/constraints.yaml`, and
`time_budget.py`). It is selectable in the `AskUserQuestion`
multi-select but **cannot be the only selection** — the skill re-asks
if the user picks `collider` alone. If `collider` is selected
alongside a real constraint, **nothing collider-related runs**: the
resolver tags it `BLOCKED — missing: ['collider-not-implemented']`,
the printer emits `"Collider (coming soon — skipped)"`, and Step 4
silently has nothing to do with it. There is no sub-skill it tries to
invoke, no TODO function call, no crash path.

No collider analysis tools (Pythia driver beyond a config-doc skill,
Delphes, MadAnalysis5, CheckMATE, Rivet, SModelS) are installed.

## Recon: where "collider" lives

### 1. Per-model menu (`2hdm-a/SKILL.md` Step 2, lines 109-126)

```json
{
  "question": "Which constraints do you want computed for this model?",
  "options": [
    {"id": "relic",    "label": "Relic density",            "description": "Ω h² via MadDM (a-resonance region) — READY"},
    {"id": "dd",       "label": "Direct detection",         "description": "Loop-only σ_SI via MadGraph + FeynArts/FormCalc + DDCalc — BLOCKED"},
    {"id": "id",       "label": "Indirect detection",       "description": "Annihilation spectra via MadDM → GamLike / NuLike — BLOCKED"},
    {"id": "collider", "label": "Collider (coming soon)",   "description": "Placeholder — execution is a no-op"}
  ],
  "allowMultiple": true,
  "required": true
}
```

Followed by validator: "Validation: at least one non-collider option
must be selected. If the user selects `collider` only, re-ask with the
message: 'Collider is a placeholder in this iteration; nothing would
run. Please also select relic, DD, or ID.'"

The same block, byte-for-byte, lives in `singlet-doublet/SKILL.md`
(lines ~100/107) and `dark-su3/SKILL.md` (lines ~140/147).

### 2. Constraint registry (`_shared/constraints.yaml` lines 685-688)

```yaml
constraints:
  ...
  collider:
    chain: []
    placeholder: true
    message: "Collider constraints are not yet implemented; planned for a future release."
```

Empty chain, explicit `placeholder: true`. Every prereq's
`role.collider` is `none` (13 prereqs each declaring "I do not
contribute to collider").

### 3. Time-budget resolver (`_shared/time_budget.py` lines 80, 115-125)

```python
'collider' is accepted (placeholder — always skipped with a note).

if cid == "collider":
    row = ConstraintRow(
        constraint="collider",
        status="BLOCKED",
        missing=["collider-not-implemented"],
        chain_annotated=[],
        cold=[0.0, 0.0],
        cached=[0.0, 0.0],
    )
    report.rows.append(row)
    continue
```

Hard-coded short-circuit. The printer (line 275) emits `"Collider
(coming soon — skipped)"`.

### 4. /demo non-goal (line 121)

```
- No collider execution. The collider option in per-model Step 2 is a placeholder only.
```

### 5. Blocker catalog (`_shared/blocker_catalog.yaml` lines 173-184)

`LHC_TOOLING_MISSING` exists; reviewer flagged it is **not** dormant —
it is referenced as the blocker for axis_predicate
`A7.extra_colored_matter == true AND collider observables selected`
in `plugins/hep-ph-toolkit/skills/_shared/blocker_class_map.yaml:146`.
Just doesn't fire in-scope today.

## Investigation answers

**Q: Is "collider" actually in the 2hdm-a constraint multi-select menu?**
A: Yes, as id `collider`. Step 2's validator forbids `collider`-only
selection (re-asks).

**Q: If selected (alongside e.g. relic), what does the skill do?**
A: Nothing collider-specific. `summary.json` schema accepts `collider`
in `skipped_constraints[*].id`. No sub-skill invocation. No crash.

**Q: Documented expected tool chain (MadGraph → Pythia → Delphes →
ATLAS/CMS recast)?**
A: Not in the 2HDM+a SKILL or its `expectations.json`. Closest pointer
is `LHC_TOOLING_MISSING` blocker code, which name-checks **CheckMATE**
and **MadAnalysis5**.

**Q: Are any of those tools present?**
A: No. `config.json` has the relic/DD chain tools (MG5, MadDM, SARAH,
SPheno, Wolfram); no Pythia, Delphes, MadAnalysis, CheckMATE, Rivet,
SModelS. (Reviewer noted r1 over-enumerated `config.json` paths —
FeynArts/FormCalc/LoopTools/DDCalc paths are tracked elsewhere, not in
`config.json`. Tools-absent inventory is accurate; tools-present claim
was sloppy.)

**Q: Smallest real collider observable that *could* be wired up?**
A: σ(pp → χχ̄ + j) at 13 TeV, parton-level, MadGraph-only, no detector
simulation. All needed tools already exist (the same UFO Step 4b builds
for relic). Output is a number (cross-section in fb) and an LHE file.

## Suggested first-cut wiring (mapping only — DO NOT implement here)

If a future iteration unblocks collider, the smallest coherent change set:

1. **Pick the observable**: parton-level σ(pp → χ χ̄ + j, p_T(j) > 100
   GeV) at √s = 13 TeV with the existing `TwoHdmAfix` UFO.
2. **Add a chain in `constraints.yaml`**:
   ```yaml
   collider:
     chain: [sarah-build, madgraph]
     default_time:
       cold:   [0.5, 1.5]
       cached: [0.1, 0.3]
     # remove: placeholder: true / message: ...
   ```
3. **Add a Step 4-level branch in 2HDM+a SKILL** that drives MG5 with a
   `generate p p > chi chi~ j` script (analogous to Step 4c but a
   single `launch` rather than the MadDM two-phase output→patch→launch).
   Reuse `patch_paramcard.py` for the param_card.
4. **Add `collider.json` to the `summary.json` artifact contract**.
5. **Lift the Step 2 validator**: drop "must include a non-collider
   choice".
6. **Remove the `time_budget.py` short-circuit** (lines 115-125).

Detector-level / recast comes later and requires installer skills for
Pythia, Delphes, and either MadAnalysis5 or SModelS.

## Caveat (parton-level vs. detector-level)

Real ATLAS limits (e.g. ATLAS-EXOT-2018-06) are quoted on the showered
+ detector-smeared MET shape, not parton σ. A parton-level σ is a
"lower-bar sanity check", not an exclusion test. Future implementer
should not claim exclusion from parton-level σ.

## Stop reason

Mapping is sufficient — the placeholder contract is fully understood
from static reading. No execution attempt was warranted (selecting
`collider` is explicitly defined as a no-op). Total time on station:
~12 min.

---

# Cross-cutting findings (synthesis)

For the rolled-up sharp edges and recommended next actions, see:
- `plugins/hep-ph-toolkit/skills/2hdm-a/sharp-edges.md` — consolidated
  sharp-edges log (groups: model fixture, infrastructure, playtest
  agent gotchas, skill-flow / gate, patcher, collider).
- `docs/devlog.md` — narrative entry "2HDM+a playtest round —
  2026-04-26" (top-level cross-cutting findings + follow-up punch
  list).
