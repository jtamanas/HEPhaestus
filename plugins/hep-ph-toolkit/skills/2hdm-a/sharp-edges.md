# 2HDM+a — sharp edges

Practitioner notes for friction the next agent will hit when running the
2HDM+a `/demo` chain. Per project memory `feedback_devlog_practice`:
sharp edges live with the skill; the devlog (`docs/devlog.md`) is
narrative and links here.

This file is a consolidated rollup of findings across the four
2026-04-26 playtest workstreams (relic / dd / id / collider). Trust
levels: **VERIFIED** = evidence captured in worktree;
**HYPOTHESIS** = needs follow-up.

---

## Model fixture and SARAH-emission edges

### SE-2HDMA-MODEL-1 — `Vertex::ChargeViolating` warnings on TwoHdmAfix during `MakeFeynArts[]` (VERIFIED)

**Surfaced:** WS-dd r1 (2026-04-26); evidence captured in WS-dd r2.
**Worktree:** `agent-afc1d0ee1a5c3278b`, commit `aa38e45`,
`demo_output/2hdm-a/dd_attempts/feynarts_v3/sarah.log` lines 121, 123, 129.

**Symptom.** `Start["TwoHdmAfix"]; MakeFeynArts[]` emits
`Vertex::ChargeViolating: Non-zero result for {Ah, conj[Hm], conj[VWp]} ...`
at sarah.log:121, the same on `{hh, conj[Hm], conj[VWp]}` at :123, and on
the quadrilinear `{Ah, conj[Hm], conj[VWp], VP}` at :129. SARAH also emits
preceding `Part::pkspec1` / `Part::partw` warnings (lines 54, 58, 65).

**Cause.** Charges on those vertices physically sum to zero
(0+1−1=0 trilinears; 0+1−1+0=0 quadrilinear with VP=photon). SARAH
flagging them as charge-violating is therefore most plausibly a
**convention mismatch in the hand-crafted `.m` files** — likely the `ZA`
rotation matrix for the 3-state Ah mixing
(`fixtures/sarah_model/TwoHdmAfix.m:102`, HYPOTHESIS) or a `ZP`
charged-Higgs sign. The `Part::*` warnings echo memory
`reference_sarah_failed_emission` (SARAH leaks `$Failed` / `Part[List]`).

**Fix.** Vertex-by-vertex audit against a reference 2HDM+a UFO before
trusting any FeynArts/FormCalc output for DD on this fixture. This is a
**prerequisite**, not folded into other DD work estimates.

**Avoid.** Do not assume the 33k-byte `.mod` SARAH emits is
physics-correct just because emission succeeds. Round-1 narrative
speculated the warnings might be silent failure modes preventing
emission; that was wrong (emission succeeds in 79 wall-seconds). The
warnings are a physics-correctness flag, not a tooling failure.

**Avoid (path):** these warnings appear on the `MakeFeynArts[]` path,
**not** on the `MakeUFO[]` path used by relic. The relic chain is
unaffected; only DD is gated by this.

---

### SE-2HDMA-MODEL-2 — Stale `[PLANNED]` markers for `/feynarts`, `/formcalc`, `/ddcalc` (VERIFIED)

Status: RESOLVED — Resolved 2026-04-26 in tier2/ws2-S3 commit <SHA>

**Surfaced:** WS-dd r1 (Blocker 8). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** `/demo` and `/2hdm-a` SKILL.md prose label `/feynarts`,
`/formcalc`, `/ddcalc` as `[PLANNED]` even though all three skills have
mature SKILL.md files (206 / 155 / 225 lines) plus `scripts/` and
`tests/`. `_shared/constraints.yaml` is half-stale: `ddcalc.status:
exists` but `feynarts.status: planned` and `formcalc.status: planned`.

**Cause.** Documentation drift; the constraints YAML was updated for
ddcalc but never for feynarts/formcalc, and SKILL.md prose was never
chased.

**Fix.**
- `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md:58,146,480` — flip prose.
- `plugins/hep-ph-toolkit/skills/demo/SKILL.md:39` — flip prose.
- `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` — flip
  `feynarts.status` and `formcalc.status` to `exists` (gate on
  `HEPPH_RUN_WOLFRAM_TESTS=1` smoke pass first).

**Avoid.** Drive these three statuses from one source. The current
duplication between SKILL.md prose and constraints.yaml has guaranteed
drift.

---

### SE-2HDMA-MODEL-3 — SKILL.md headline Ω h² ≈ 10.15 is stale (VERIFIED)

Status: RESOLVED — Resolved 2026-04-26 in tier2/ws2-S1 commit <SHA>

**Surfaced:** WS-relic r1. **Worktree:** `agent-aa0dba254bcf80001`,
commit `542e130`. Verified deterministic emission of 10.493759 vs.
benchmark central 10.493.

**Symptom.** `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ~line 509
quotes `Ω h² ≈ 10.15` (the iter-8 value). Benchmark fixture at
`plugins/hep-ph-toolkit/skills/2hdm-a/benchmarks/off-resonance-2hdma-004/expectations.json`
was corrected to central 10.493 in commit `f28ff93` (T-SF-5 cycle-2);
the current code emits `10.493759` deterministically.

**Fix.** Two-line patch to SKILL.md headline; align example
`summary.json.headline` to either 10.493 (benchmark) or 10.494 (current
emission, rounded). Bundle with the `schema_version` propagation
(SE-INFRA-1).

**Avoid.** When the benchmark fixture changes, search SKILL.md for any
hand-quoted numerical value and update both together.

---

## Infrastructure / cross-platform edges

### SE-INFRA-1 — `summary.json` missing `schema_version: "1"` (VERIFIED, cross-model)

Status: RESOLVED — Resolved 2026-04-26 in tier2/ws2-S1 commit <SHA>

**Surfaced:** WS-id r1 (false-claimed-validated; corrected in r2);
WS-relic r1 reviewer flagged the same gap as pre-existing infra debt.
**Worktree (fix-applied):** `agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** `demo_output/<model>/summary.json` emitted by `/2hdm-a` is
missing the required `schema_version` field. Validating against
`plugins/hep-ph-toolkit/skills/_shared/summary.core.schema.json` returns
`INVALID: 'schema_version' is a required property` (exit 1). The
emission template in
`plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` ~line 509 omits the field;
WS-id r1 also emitted without it.

**Cause.** SKILL.md template predates the canonical core schema (commit
`63089d4`, T-SF-1..T-SF-8). Likely affects `singlet-doublet` and
`dark-su3` SKILL.md templates as well — cross-model.

**Fix.**
1. Add `"schema_version": "1",` at the top of every `summary.json`
   emission template across all per-model SKILL.md files.
2. Validate every `summary.json` emission against the per-model
   schema directly:
   ```bash
   python -c "import json, jsonschema; \
     jsonschema.validate( \
       json.load(open('<path>')), \
       json.load(open('plugins/hep-ph-toolkit/skills/2hdm-a/summary.schema.json')))"
   ```
   Assert exit 0 in tests.

**Avoid.** Never claim "verified locally" without actually running the
validator. WS-id r1 made this exact mistake — claim was load-bearing
and false.

---

### SE-INFRA-2 — Schema duality: legacy `summary.schema.json` vs canonical `summary.core.schema.json` (VERIFIED)

Status: RESOLVED — Resolved 2026-04-26 in tier2/ws2-S2 commit <SHA>

**Surfaced:** WS-id r2 (B8). **Worktree:** `agent-a1acbc7b9ecb28aa6`,
commit `97d6a94`.

**Symptom (historical).** Two summary schemas previously coexisted:
- `plugins/hep-ph-toolkit/skills/_shared/summary.core.schema.json` —
  canonical; requires `schema_version` (`const: "1"` at line 18).
- ~~`plugins/hep-ph-toolkit/skills/_shared/summary.schema.json`~~ (deleted
  in tier2/ws2-S2 commit `<SHA>`) — was the legacy schema; required
  keys list omitted `schema_version`; had `additionalProperties: false`.
  A canonical `summary.json` with `schema_version` therefore **failed**
  this legacy schema with `Additional properties are not allowed
  ('schema_version' was unexpected)`.

**Cause.** Core schema was introduced without retiring the legacy one.
`plugins/hep-ph-toolkit/skills/_shared/test_summary_schema.py` previously
validated stub payloads against the legacy schema; the per-model
schemas (e.g. `2hdm-a/summary.schema.json`) correctly composed the core
via `allOf` + `$ref`.

**Fix applied.** Deleted `_shared/summary.schema.json`; rewrote both
`test_summary_schema.py` files to validate via per-model dispatch
and against `summary.core.schema.json` directly. All callers
repointed to `<model>/summary.schema.json` or
`_shared/summary.core.schema.json` as appropriate.

**Avoid.** When validating `summary.json`, target the per-model
composed schema (`<model>/summary.schema.json`) which $refs the core
— that is the single right validation target.

---

### SE-INFRA-3 — `flock` not available on macOS; SARAH mutex is a no-op (FIXED in run-20260426-punchlist-tier2)

**Surfaced:** WS-dd r1 (Blocker 3). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** `/2hdm-a` SKILL.md Step 4b prescribes
`flock -x -w 120 .../sarah.lock wolframscript ...`. macOS does not ship
`flock`. Verbatim: `(eval):14: command not found: flock`, exit 127.

**Cause.** `flock(1)` is BSD/Linux util-linux only. Apple's BSD base
omits it. The documented "global SARAH mutex" at
`.shift-manager/locks/sarah.lock` referenced by 2hdm-a/SKILL.md:247 is
silently a no-op on this platform. WS-dd observed two unrelated
Wolfram kernels (SingletDoublet and DarkSU3) running concurrently
during the playtest round — without `flock`, concurrent
`MakeUFO[]`/`MakeFeynArts[]` on the shared
`$SARAH_ROOT/Output/<Model>/` path can corrupt outputs.

**Resolution:** shipped portable Python file-lock helper at `bin/flock_run.sh`;
`2hdm-a/SKILL.md:247` rewritten to call it; lock path moved off the repo tree
to `${HEPPH_STATE_ROOT}/.locks/sarah_global.lock` for worktree safety.
See `bin/README.md` for the helper contract and lock-path convention.

**Avoid.** Don't ship a shell-level `flock` invocation in any
cross-platform skill prose. The macOS half of users gets no mutex
protection and won't see a warning.

---

### SE-INFRA-4 — Watchdog stalls on long synchronous subprocess calls (VERIFIED, cross-skill)

**Surfaced:** WS-relic r1 (the prior WS-relic agent was watchdog-killed
at Step 4c MadDM launch); WS-dd r1 separately surfaced the same
pattern probing SARAH. **Worktree:** `agent-aa0dba254bcf80001`, commit
`542e130`.

**Symptom.** A playtest agent that runs
`subprocess.run(mg5_aMC --mode=maddm launch.mg5)` (or any long SARAH
probe) as a foreground tool call gets killed by the harness watchdog
after ~600s of "no stream progress" — even though the subprocess is
making genuine progress.

**Cause.** The watchdog measures *tool-call activity*, not subprocess
wall time. A blocking `subprocess.run` is a single tool-call from the
harness's perspective; once it has been silent for the threshold, the
agent dies.

**Fix.** Split long-running subprocess calls into:
1. Short driver scripts (e.g. `run_maddm_phase1.sh`,
   `run_maddm_phase2.sh`).
2. Kick each off via `Bash run_in_background=true`.
3. Either block on the completion notification (counts as a tool-call
   tick), or run a Monitor `until -f $RESULTS_FILE` poll loop emitting
   one event every 30–60s.

WS-relic ran phase1 + patch + phase2 in ~2.5 min wall-clock with this
pattern; reference run at
`.claude/worktrees/agent-aa0dba254bcf80001/demo_output/2hdm-a/timing.log`.

**Avoid.** Never call `subprocess.run` synchronously for any
single-step MG5/MadDM/SARAH invocation that may exceed ~5 min, even if
the iter-8 driver code in SKILL.md does so. The driver is correct;
embedding it in an agent's foreground Bash call is not. This is a
meta-finding for all playtest agents — see "Playtest agent gotchas"
below.

---

### SE-INFRA-5 — `time_budget.py:281` renderer bug: literal `/` slash on non-skill markers (VERIFIED)

**Surfaced:** WS-id r2 (B7). **Worktree:**
`agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** `_shared/time_budget.py:281` does
`missing_strs = ", ".join(f"/{p}" for p in row.missing)` — unconditional
`/` prefix. When the helper injects a marker like
`spec-authoring-incomplete` from
`models.<m>.spec_authoring_blockers`, the renderer prints
`BLOCKED — missing: /spec-authoring-incomplete, /gamlike` — a literal
slash on a non-skill marker that masquerades as a fake skill name.

**Cause.** No special-case for markers that aren't keys under
`tools.*` in `constraints.yaml`.

**Fix.** In the renderer, detect markers absent from `tools.*` and
either skip the leading slash or render them on a separate
"Other prerequisites:" line. ~5–15 min when implemented.

**Avoid.** When grep-ing for `/spec-authoring-incomplete` to find an
implementation, you will find nothing — that's the bug, not your
search.

---

## Playtest agent gotchas

### SE-PLAYTEST-1 — Worktree agents must NEVER write to main-repo `.shift-manager/` (VERIFIED)

**Surfaced:** WS-id r1 contaminated main repo; WS-id r2 cleaned it up.
**Worktree:** `agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** WS-id r1 inadvertently materialized a zero-byte
`sarah.lock` at the **main repo's** canonical
`/Users/yianni/Projects/hephaestus/.shift-manager/locks/sarah.lock`
in addition to the worktree-local mirror. This violated the "don't
touch main-repo files" policy and risked sibling collisions.

**Cause.** The shift-manager "probe + create at canonical path if
absent" convention is written for in-tree (main-repo) callers. From a
worktree, the canonical path is shared infra owned by the manager and
whoever currently owns the workspace.

**Fix (rules for worktree-scoped playtest agents).**
1. Always probe `.shift-manager/locks/*` read-only before writing.
2. Never `touch` / `open(..., 'w')` / `flock` against
   `<repo-root>/.shift-manager/locks/*`.
3. Materialize lock stubs only at
   `<worktree-root>/.shift-manager/locks/*`.
4. If you genuinely need cross-worktree coordination, route it through
   a manager handshake — never unilaterally write to shared paths.

WS-id r2 deletion was safe because: `lsof` returned no holder, mtime
unchanged from r1 creation (09:49:29Z), file was empty. Audit line in
`timing.log`:
`r2_main_repo_lock_deleted path=… holder_check=lsof_no_holder
mtime_was=09:49:29 size_was=0`.

**Avoid.** Even empty stub files at a shared path count as
contamination.

---

### SE-PLAYTEST-2 — Long synchronous subprocess calls trip the watchdog

See SE-INFRA-4. This is the single biggest meta-finding for future
2HDM+a playtest agents on the relic and DD chains. Both WS-relic
(MadDM) and WS-dd (SARAH probes) hit it.

---

### SE-PLAYTEST-3 — Always run validators before claiming schema-compliance

WS-id r1 wrote `summary.json` and claimed it "validates against
`summary.schema.json` (verified locally)" without running the
validator. Direct verification returned `INVALID`. See SE-INFRA-1 for
the underlying schema gap; this entry is the playtest-discipline
lesson: **never claim validation without a captured exit code.**
Record validator runs in `timing.log` (e.g. WS-id r2's
`r2_validator_run_core_schema exit_code=0 result=VALID`).

---

## Skill-flow / gate edges

### SE-2HDMA-FLOW-1 — DD path Step-3 BLOCKED gate has no "go anyway" (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 1); also relevant to ID-only via
WS-id (B5). **Worktree:** `agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** Selecting only `dd` (or only `id`) at /2hdm-a Step 2 hits
the Step 3 BLOCKED gate, which offers `{run_ready, back, cancel}`. There
is no "go anyway" branch (the `go` option only appears in the
all-READY branch at SKILL.md line 183). `run_ready` proceeds with the
READY subset, which is empty for blocked-only selections — so Step 4
falls straight through to "write summary.json with everything
skipped".

**Cause.** Skill design — intentional refusal — combined with no DD
execution body in Step 4e (5-line placeholder at SKILL.md:476-481).

**Fix.** Two paths:
1. Wire a real DD execution body (depends on `/looptools eval`
   landing; see SE-2HDMA-FLOW-3).
2. Until then, document the empty-READY fallthrough explicitly in
   Step 4f and offer a `/dev-override` debug path.

**Avoid.** Don't try to drive the DD chain through `/demo` today —
hand-roll the FeynArts/FormCalc/looptools/ddcalc invocations. See the
WS-dd narrative log (worktree `docs/2hdma-playtest-dd-2026-04-26.md`)
for the punch list.

---

### SE-2HDMA-FLOW-2 — Step-3 model picker label says 2hdm-a is BLOCKED (VERIFIED, stale)

Status: RESOLVED — Resolved 2026-04-26 in tier2/ws2-S3 commit <SHA>

**Surfaced:** WS-relic reviewer (MINOR-2). **Worktree:**
`agent-aa0dba254bcf80001`, commit `542e130`.

**Symptom.** `plugins/hep-ph-toolkit/skills/demo/SKILL.md:72` labels
2hdm-a as `"(currently BLOCKED — spec authoring incomplete)"` in the
Step-3 model picker. But `_shared/constraints.yaml` and
`2hdm-a/SKILL.md` declare relic READY today.

**Cause.** Pre-existing label drift; never updated when relic flipped
to ready.

**Fix.** Two-line patch: drop the BLOCKED suffix; label as
`"2hdm-a (relic READY; DD/ID BLOCKED)"`.

**Avoid.** Anyone following `/demo` literally would see "BLOCKED" on
2hdm-a and skip past — the working relic chain is hidden behind a
stale label.

---

### SE-2HDMA-FLOW-3 — `/gamlike` is the (double, not triple) ID-unblock for 2HDM+a (VERIFIED) — **Status: RESOLVED**

**Surfaced:** WS-id r1 (B6 opportunity); r1 said triple-unblock; r2
correctly downgraded to double-unblock (dark-su3 excluded). **Worktree:**
`agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom (the unblock).** `/gamlike` is documented in
`constraints.yaml:647–656` with `status: planned` but no skill folder
(`find plugins -type d -name gamlike` returns nothing). It blocks ID
on 2HDM+a, singlet-doublet (conditional). It does **not** block
dark-su3 — see Caveat below.

**Inventory finding.** Most of "compute the gamma-ray exclusion" is
*already done by MadDM 3.2.13* with `set indirect_detection ON`:

- `Fermi_Data/likelihoods/` — Pass-8 6-yr dSph likelihoods
- `Fermi_line_likelihoods/` — line-search likelihoods (R3, R16, R41,
  R90 ROIs)
- `Jfactors/jfactors.dat` — dSph J-factors
- `ExpData/MadDM_Fermi_Limit_<chan>.dat` — channel-wise <σv> upper
  limits (bb, cc, ee, gg, hh, mumu, qq, tautau, tt, WW, ZZ)
- `maddm_run_interface.py:save_summary_single()` writes
  `Fermi_Likelihood = …` rows + `flux_<n>` UL rows to
  `MadDM_results.txt` (lines 3546–3616)

**Cause (the blocker).** `/gamlike` is a formatter gap, not a missing
physics tool. A thin MadDM-output formatter would unblock 2HDM+a ID +
singlet-doublet ID.

**Fix.** Ship `/gamlike v0` (1–2 days, not the round-1 "30 lines / ½
day" estimate which was an inert-prototype number). Real v0 needs:
SKILL.md scaffold; `gamlike.json` schema with `schema_version` +
`allOf` core composition; validation gates (likelihood sign, thermal
vs non-thermal, J-factor units, channel name normalization);
`constraints.yaml` chain wiring; cross-model regression test (2hdm-a +
singlet-doublet); the `Fermi_Likelihood(Thermal)` xsi<1
conditional-emission gotcha (`maddm_run_interface.py:3573` — emits
only when `xsi < 1`); playtest pass + ornery review.

**Caveat.** Per `_shared/constraints.yaml:768–770` — "Dark SU(3)_D is
non-SM color; MadGraph/MadDM cannot generate the coannihilation set."
Dark-su3 has no `MadDM_results.txt` for `/gamlike` to parse. So the
unblock is **double**, not triple. Singlet-doublet's MadDM-ID emission
of `Fermi_Likelihood` rows was not empirically verified in WS-id r1
(static-only run); double-unblock is conditional on each model's
MadDM run actually emitting those rows.

**Avoid.** When a model declares an analytic-backend `chain_override`,
all downstream MadDM-dependent tools become unreachable for that model
regardless of constraint. Cross-read the `reason` field before
asserting an unblock.

**Resolution.** `/gamlike` v0 shipped on `tier2/ws1-gamlike-v0-20260426`
(see `plugins/hep-ph-toolkit/skills/gamlike/SKILL.md`). Parser-only; pull-computation
deferred to v1+. SE closed.

---

### SE-2HDMA-FLOW-4 — `time_budget.py` chain disagrees with SKILL.md ID/relic chain (VERIFIED)

**Surfaced:** WS-id r1 (B2). **Worktree:**
`agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** `python3 plugins/hep-ph-toolkit/skills/_shared/time_budget.py
--model 2hdm-a --constraints id` prints
`/sarah-build → /spheno-build → /madgraph → /maddm → /gamlike` (default
chain), while `2hdm-a/SKILL.md:59` reads
`fixture copy → /madgraph → /maddm → /gamlike`.

**Cause.** No `chain_overrides` block exists for `2hdm-a` in
`constraints.yaml:703–735`. `dark-su3` has one (lines 760+); `2hdm-a`
silently inherits defaults despite SKILL.md narrating a fixture-bypass
path.

**Fix.** Add `chain_overrides.relic` and `chain_overrides.id` for
2hdm-a in `constraints.yaml`, mirroring the dark-su3 pattern. ~15 min.

**Avoid.** Don't read time-budget output as authoritative when SKILL
prose narrates fixture-bypass without a YAML override.

---

### SE-2HDMA-FLOW-5 — `spec_authoring_blockers.id` is over-broad (VERIFIED)

**Surfaced:** WS-id r1 (B3). **Worktree:**
`agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** `_shared/constraints.yaml:724–725` lists
`id: ["spec-authoring-incomplete"]` for 2hdm-a. The real ID blocker is
`/gamlike`, not spec authoring.

**Cause.** Marker duplicated from DD (where it does apply: loop-only
DD requires the renderer backport for a physics-correct UFO). For ID,
the same SARAH fixture that unblocks relic also generates the UFO
MadDM uses for `generate indirect_detection` — spec authoring is not
the bottleneck.

**Fix.** Remove `id` line from `spec_authoring_blockers`; let
`tools.gamlike.status: planned` carry the block. ~5 min. Also fixes
the user-visible `/spec-authoring-incomplete` slash-rendered marker
(see SE-INFRA-5).

---

### SE-2HDMA-FLOW-6 — Empty-READY summary.json path is undocumented (VERIFIED)

**Surfaced:** WS-id r1 (B1). **Worktree:**
`agent-a1acbc7b9ecb28aa6`, commit `97d6a94`.

**Symptom.** `2hdm-a/SKILL.md` Step 4 only describes the relic-density
execution branch. When user selects `[id]` exclusively → `run_ready`
returns empty READY → skill silently falls through to Step 4f with
`ran=[]`. Schema accepts it (after SE-INFRA-1 fix), but SKILL prose
doesn't spell it out and the example summary.json shows
`ran=["relic"]` only.

**Fix.** Add a one-paragraph "Empty READY subset" callout + example
summary.json with `ran=[]` to SKILL.md Step 4f. ~10 min.

---

### SE-2HDMA-FLOW-7 — `[dd, collider]` / `[id, collider]` produce two BLOCKED rows with nothing to run (VERIFIED, edge case)

**Surfaced:** WS-collider reviewer (concern 4). **Worktree:**
`agent-a9c67d36cdb20a0b4`, commit `c494507`.

**Symptom.** Step 2 validator only forbids `collider`-only selection.
But `["dd", "collider"]` and `["id", "collider"]` pass the validator
yet produce two BLOCKED rows in the time-budget output (one from
`spec_authoring_blockers.dd/id`, one from the
`collider-not-implemented` short-circuit). Step 4 has nothing to
execute either.

**Fix.** Light-touch sentence in SKILL.md Step 2 description; bigger
fix is to broaden the validator or audit the multi-select edge cases.

**Severity:** minor; user-discoverable nearby gotcha.

---

### SE-2HDMA-FLOW-8 — `/feynarts` cold-cache invocation always errors (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 2). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** `/feynarts generate --sarah-model TwoHdmAfix ...` exits
with `FEYNARTS_SARAH_STATE_MISSING` on first run.

**Cause.** Control-flow bug:
`plugins/hep-ph-toolkit/skills/feynarts/scripts/run_feynarts.py:132`
calls `resolve_model()` before `_run_make_feynarts()` at line 163. The
first-run cold-cache branch in `_resolve_sarah_model`
(`resolve_model.py:102-109`) raises the error unconditionally if the
state-dir is missing. Auto-trigger of `MakeFeynArts[]` is unreachable
from cold-cache.

**Fix.** Restructure `run_feynarts.run()` to call
`_run_make_feynarts()` before `resolve_model()` when `sarah_model` is
provided AND state-dir is missing — OR special-case the
`FEYNARTS_SARAH_STATE_MISSING` exception by retrying after auto-trigger.
~10 lines.

---

### SE-2HDMA-FLOW-9 — `cache_key.py` crashes on empty gen_path (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 7). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** Past `resolve_model` (after symlinking around
SE-2HDMA-FLOW-10), `/feynarts generate` raises:
```
IsADirectoryError: [Errno 21] Is a directory: '.'
File ".../scripts/cache_key.py", line 26, in _sha256_file
    with open(p, "rb") as f:
```

**Cause.**
`plugins/hep-ph-toolkit/skills/feynarts/scripts/cache_key.py:21-29` —
`_sha256_file('')` constructs `Path('')` → `'.'` (cwd). `Path('.').exists()`
is True; `open('.', 'rb')` raises `IsADirectoryError`. The docstring
claims "or sha256 of empty string if file not found"; the code doesn't
guard against the empty-string case.

**Fix.** Add `if not path: return _sha256_str("")` at top of
`_sha256_file`. 1-line fix.

---

### SE-2HDMA-FLOW-10 — SARAH `MakeFeynArts[]` writes to canonical path, not state-root (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 6). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** SARAH writes `TwoHdmAfixEWSB.mod` (33k),
`Substitutions-TwoHdmAfixEWSB.m`, and `ParticleNamesFeynArts.dat` to
`$SARAH_ROOT/Output/TwoHdmAfix/EWSB/FeynArts/`. Nothing lands in the
`feynarts_state` directory the template `SetDirectory[...]`'d to.
`/feynarts` then can't find `TwoHdmAfix.mod` (also a name mismatch:
SARAH appends `EWSB`, /feynarts wants the bare name).

**Cause.** SARAH's `MakeFeynArts[]` ignores `$Path` for its output
dir; SARAH always writes to `$SARAH_ROOT/Output/<Model>/EWSB/FeynArts/`.

**Fix.** Either (a) post-copy the SARAH-emitted .mod from
`$SARAH_ROOT/Output/<Model>/EWSB/FeynArts/` into `$STATE_DIR/`, OR (b)
update `resolve_sarah_model` to look at the SARAH-canonical path. (a)
is more cache-friendly; (b) requires `sarah_path` in the cache key.
~30 min.

**Workaround tested.** Symlinking
`$STATE_DIR/TwoHdmAfix.mod -> $SARAH_OUTPUT/.../TwoHdmAfixEWSB.mod`
passes `resolve_model` but uncovers SE-2HDMA-FLOW-9.

---

### SE-2HDMA-FLOW-11 — `/feynarts` lacks SARAH-particle alias loader despite docstring (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 4). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** Calling
`/feynarts generate --process "chi q -> chi q" --sarah-model TwoHdmAfix`
would raise `FEYNARTS_ABSENT: unknown particle: 'chi'` even past
SE-2HDMA-FLOW-8. `chi` is not in `_PARTICLE_META` and there is no
`tables/TwoHdmAfix.json`.

**Cause.**
`plugins/hep-ph-toolkit/skills/feynarts/scripts/resolve_process.py`
docstring (lines 5–6) claims `$STATE_ROOT/models/<name>/sarah/particles.m`
is consulted. No code reads particles.m. `state_root` parameter is
declared at line 152 but never used — dead argument.

**Fix.** Implement the SARAH-particles.m loader the docstring promises,
OR auto-emit `tables/<sarah_model>.json` during `MakeFeynArts[]` from
SARAH's `particles.m`. Estimated 1–2 hours.

**Workaround.** Use raw FeynArts tuple form
(`{{F[1,{...}], -F[1,{...}]}, ...}`) — but the SARAH-internal field
index for `chi` and the DM PDG (9989932) aren't documented in
`/2hdm-a` SKILL.md.

---

### SE-2HDMA-FLOW-12 — No `/looptools eval` runtime skill (VERIFIED)

**Surfaced:** WS-dd r1 (Blocker 5). **Worktree:**
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`.

**Symptom.** Past FeynArts → past FormCalc, nothing exists to consume
`amp_reduced.m` and emit `scattering/v1` JSON. This is the **biggest
single missing piece** in the DD chain.

**Cause.**
- `plugins/hep-ph-toolkit/skills_shared/installs/looptools/` exists (build/detect
  skill).
- `plugins/hep-ph-toolkit/skills/looptools/` does NOT exist (runtime
  eval skill).
- `grep -rl '"source": "looptools"'` matches only one fixture; no
  producer code anywhere.
- `plugins/shared/schemas/scattering.schema.json` accepts
  `source: "looptools"`, but no runtime emits it.

**Fix.** Implement `/looptools eval` (1 sprint, 5–10 days; r1's "1–3
days" was widened in r2 per reviewer MAJOR-5):

| Sub-task | Hours |
|---|---|
| 1a. Load `amp_reduced.m` (FormCalc PV heads) | 4–8 |
| 1b. Construct `chi N → chi N` kinematics at q²=0 | 4–8 |
| 1c. Substitute nucleon-quark form factors (default_2018 or A1) | 8–12 |
| 1d. Numerically evaluate A0i/B0i/C0i/D0i via LoopTools (Fortran link or wolframscript drive) | 12–20 |
| 1e. Emit `scattering/v1` JSON with `source: "looptools"` | 4–8 |
| 1f. Schema validation + kinematic regression tests | 8–16 |
| 1g. End-to-end smoke test against `/ddcalc run` | 4–8 |
| **Subtotal** | **44–80 hr (5–10 days)** |

**SARAH-side risk.** Sub-task 1d's correctness depends on
FeynArts emitting physics-correct vertices — see SE-2HDMA-MODEL-1
(`Vertex::ChargeViolating`). A vertex-by-vertex audit against a
reference 2HDM+a UFO is a **prerequisite**, not folded into the 5–10
day estimate.

**Reference:** GAMBIT's `DarkBit_BSM_models/MicrOmegas` adapter.

---

## Patcher / driver-script edges

### SE-2HDMA-PATCH-1 — `patch_paramcard` writes DMSECTOR(1) outside its block (VERIFIED, cosmetic)

**Surfaced:** WS-relic r1. **Worktree:** `agent-aa0dba254bcf80001`,
commit `542e130`.

**Symptom.** When DMSECTOR initially has only DMSECTOR(2), the patcher
inserts DMSECTOR(1) after the `## INFORMATION FOR EFFBLOCK` comment
header but before `Block effblock`. SLHA parsers don't care (still
inside dmsector until the next `Block`/`DECAY` keyword), and MASS PDG
9989932 also pins mchi.

**Cause.** `patch_paramcard.py:_set_block_value` scans forward from the
matching `Block <name>` header and inserts before the next
`Block`/`DECAY` line, ignoring comment-only lines.

**Fix.** Make `_set_block_value` skip comment-only lines when locating
the end of a block, so DMSECTOR(1) inserts cleanly inside `Block
dmsector`.

**Severity:** cosmetic only; not blocking.

---

### SE-2HDMA-PATCH-2 — Param-card overlay must occur between `output` and `launch -f` (PRE-EXISTING)

**Surfaced:** WS-relic r1 (re-affirming pre-existing finding).

**Symptom.** A single-session script with both `output` and `launch -f`
gives MG5 no opportunity to yield control between them, so a
param_card patch run "before launch" inside the same MG5 session is a
no-op.

**Documented at** `maddm_run.py:generate_maddm_script(...,
split_for_param_overlay=True)`. SKILL.md Step 4c does the split inline.

**Avoid.** Any session-orchestration shape that doesn't separate the
two MG5 invocations will silently lose the patch. This is also the
shape that makes the watchdog-safe split-script approach
(SE-INFRA-4) the *correct* approach.

---

## Collider placeholder edges

### SE-2HDMA-COLLIDER-1 — Collider menu entry is a triple-locked no-op (VERIFIED)

**Surfaced:** WS-collider r1. **Worktree:** `agent-a9c67d36cdb20a0b4`,
commit `c494507`.

**Symptom.** Step 2 multi-select offers `{"id": "collider", "label":
"Collider (coming soon)", "description": "Placeholder — execution is
a no-op"}`. The label looks live but every downstream path is a hard
short-circuit.

**Lock points (all three must be unlocked together to make collider real).**
1. `plugins/hep-ph-toolkit/skills/2hdm-a/SKILL.md` Step 2 validator
   (line 125) re-asks if user picks `collider`-only.
2. `plugins/hep-ph-toolkit/skills/_shared/constraints.yaml:685–688` —
   `collider: { chain: [], placeholder: true, message: ... }`.
3. `plugins/hep-ph-toolkit/skills/_shared/time_budget.py:115–125` —
   hard-coded `if cid == "collider": ... missing=['collider-not-implemented']`
   short-circuit before the general resolver runs.

The same JSON block is byte-identical in `singlet-doublet/SKILL.md`
and `dark-su3/SKILL.md`. Test invariants at
`_shared/tests/test_skill_structure.py:200,327,412,521` lock the
four-id menu shape.

**Lower-friction options.**
- **Quietest:** demote to a footnote in another constraint's
  description; drop from the `options` array until a chain exists.
- **Honest:** make the entry visibly disabled; if AskUserQuestion
  doesn't support disabled options, prefix `[BLOCKED]` like the
  `/demo` Step 1 prereq description.
- **Real fix:** wire a parton-level σ(pp → χχ̄ + j) driver. Mapping
  in worktree narrative
  `docs/2hdma-playtest-collider-2026-04-26.md` § "Suggested
  first-cut".

**Severity:** minor (UX paper-cut, not a correctness issue).

**Note.** `LHC_TOOLING_MISSING` in
`_shared/blocker_catalog.yaml:173–184` is **not** dormant — it is
referenced as the blocker for axis_predicate
`A7.extra_colored_matter == true AND collider observables selected`
in `plugins/hep-ph-toolkit/skills/_shared/blocker_class_map.yaml:146`.
It just doesn't fire in-scope today.

---

### SE-2HDMA-COLLIDER-2 — No real collider observable named anywhere for 2HDM+a (VERIFIED)

**Surfaced:** WS-collider r1.

**Symptom.** Despite Step 1 prose pointing to Arcadi & Profumo
arXiv:2506.19062 §III as the physics target, no collider observable
is named in SKILL.md, `practitioner_script.md`, or
`benchmarks/off-resonance-2hdma-004/expectations.json`. The natural
collider companion (mono-jet, mono-Z, t̄ + a → t̄χχ̄) is absent.

**Caveat (parton-level vs. detector-level).** The "smallest first-cut"
candidate σ(pp → χχ̄ + j, p_T(j) > 100 GeV) at √s=13 TeV with the
existing `TwoHdmAfix` UFO is a sensible MVP — it's the same approach
as Bauer et al. 1701.07427 §4. But real ATLAS limits (e.g.
ATLAS-EXOT-2018-06) are quoted on the showered + detector-smeared MET
shape, not parton σ. A parton-level σ is a "lower-bar sanity check",
not an exclusion test. Future implementer should not claim exclusion
from parton-level σ.

**Severity:** minor.

**Owner.** WS-collider next round.

---
