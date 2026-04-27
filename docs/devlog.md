# hep-ph-agents devlog

An ongoing log of decisions, sharp edges, and lessons from building this
plugin marketplace. Intended audience: practitioners who are becoming
Claude-Code–native and want to build their own skills and plugins.

Newest entries on top. Each entry is dated and scoped to one topic —
origin stories, design decisions, or a sharp edge we hit and patched.

---

## 2026-04-26 — 2HDM+a playtest round

**TL;DR.** Four parallel `/demo → 2hdm-a → {relic,dd,id,collider}`
playtests, each in its own worktree with an opus playtester + an ornery
reviewer until sign-off. **Relic PASS** — Ω h²=10.493759 reproduced
end-to-end at the off-resonance benchmark, matching benchmark central
to 4 sig figs without source changes. **DD BLOCKED** — 8 distinct
blockers mapped; the binding constraint is the missing `/looptools
eval` runtime skill, and SARAH `Vertex::ChargeViolating` warnings on
the TwoHdmAfix fixture (now evidence-verified) raise a
physics-correctness question that gates trustable DD output. **ID
BLOCKED** — `/gamlike` is the unblock (double, not triple — dark-su3
is excluded because it has no MadDM run); the work is largely a thin
formatter over `MadDM_results.txt`, not new physics. **Collider
placeholder by design** — locked in three places, byte-identical
across all three demo models. The cross-cutting finding with most
leverage: **`summary.json` is missing `schema_version` everywhere**, a
small infra debt that bit one workstream's verification claim and
silently affects all three demo models.

**What we ran.** Manager-delegated four workstreams in parallel — each
in an isolated worktree under `.claude/worktrees/`. Each workstream
ran `/demo` end-to-end (or as far as it could go) for one observable,
captured artifacts, wrote a narrative log, then handed off to an
ornery-reviewer subagent. Reviewers flagged concerns; playtesters
either fixed (round 2) or escalated. All four signed off. Final
artifacts (RUN_RESULTS, REVIEW_NOTES, sharp-edges, narrative log) are
preserved on each worktree's commit; the consolidated record is
synthesized into the main repo here. Worktrees and final commits:

| WS | Worktree | Final commit | Outcome |
|---|---|---|---|
| relic | `agent-aa0dba254bcf80001` | `542e130` | SUCCESS |
| dd | `agent-afc1d0ee1a5c3278b` | `aa38e45` (r2) | BLOCKED — 8 blockers |
| id | `agent-a1acbc7b9ecb28aa6` | `97d6a94` (r2) | BLOCKED — 4 real blockers + 4 follow-ups |
| collider | `agent-a9c67d36cdb20a0b4` | `c494507` | placeholder by design |

The full stitched narrative is in
`docs/2hdma-playtest-round-2026-04-26.md`; the consolidated sharp
edges live in
`plugins/hep-ph-toolkit/skills/2hdm-a/sharp-edges.md` (per project
memory, devlog is narrative; sharp edges live with the skill).

### Per-workstream summary

**Relic (PASS).** First end-to-end relic-density reproduction from this
repo without source changes, on a clean retry after a watchdog kill.
The prior WS-relic agent stalled at Step 4c MadDM launch — the harness
watchdog killed it after ~600s of "no stream progress" because
`subprocess.run(mg5_aMC --mode=maddm launch.mg5)` is one tool call's
worth of activity from the harness's perspective, and MadDM's compile
+ integrate is silent for ~2 minutes. The retry split the launch into
`run_maddm_phase{1,2}.sh` driver scripts, kicked each via `Bash
run_in_background=true`, and rode completion notifications. Each phase
finished in ~60-70s; total ~2.5 min wall-clock. The result —
**Ω h² = 10.493759** with channel breakdown wphp=49.62%, wmhm=49.62%,
bbx=0.65%, ccx=0.06%, tamtap=0.04% — matches benchmark central
(10.493) to 0.007%. Reviewer signed off with one MAJOR concern: the
emitted `summary.json` is missing `schema_version`, but that's
pre-existing infra debt (the SKILL.md template at line ~509 also
emits the unversioned form). See worktree
`agent-aa0dba254bcf80001`, commit `542e130`. Sharp edges:
SE-INFRA-4 (watchdog), SE-2HDMA-PATCH-1/2 (patcher), SE-2HDMA-MODEL-3
(stale headline).

**DD (BLOCKED, 8 blockers).** The DD chain is wholly unreachable
today. The Step-3 BLOCKED gate has no "go anyway" branch — `run_ready`
proceeds with an empty READY subset, so Step 4 falls through to
"summary.json with dd skipped". The chain
`/feynarts → /formcalc → /looptools → /ddcalc` has skill folders for
the first two and last but **no `/looptools` runtime skill** (only
`/looptools-install`); no producer code emits `scattering/v1` JSON
with `source: "looptools"`. Round-1 also ran `MakeFeynArts[]` directly
on TwoHdmAfix and observed `Vertex::ChargeViolating` warnings on
`{Ah, conj[Hm], conj[VWp]}`, `{hh, conj[Hm], conj[VWp]}`, and
`{Ah, conj[Hm], conj[VWp], VP}` — vertices that are **physically
charge-conserving**, so the warning most plausibly indicates a
`ZA`/`ZP` rotation-matrix convention bug in the hand-crafted .m
files. Round-1 quoted those warnings without committing the SARAH log;
round-2 captured the log verbatim
(`dd_attempts/feynarts_v3/sarah.log` lines 121, 123, 129) — the
warnings are now evidence-verified. Other blockers found: cold-cache
control-flow bug in `/feynarts`; `cache_key.py` crash on empty
gen_path; SARAH writes `MakeFeynArts[]` output to canonical SARAH path
not state-root; missing SARAH-particle alias loader despite
docstring; `flock` not on macOS; stale `[PLANNED]` markers. Worktree
`agent-afc1d0ee1a5c3278b`, commit `aa38e45`. Sharp edges:
SE-2HDMA-MODEL-1 (chargeviolating), SE-2HDMA-FLOW-1/8/9/10/11/12,
SE-INFRA-3 (flock), SE-2HDMA-MODEL-2 (stale planned).

**ID (BLOCKED, 4 real blockers).** Round-1 over-counted blockers by
tallying a playtest-convention nit (B5: `go` vs `run_ready` alias) and
an opportunity finding (B6: MadDM subsumes most of /gamlike) alongside
real blockers. Round-2 honest split: 4 real blockers + 1 nit + 1
opportunity + 2 follow-up findings. The real headline: **`/gamlike`
is largely subsumed by MadDM 3.2.13.** MadDM ships dSph likelihoods
(Pass-8 6-yr), line-search likelihoods, J-factors, channel-wise
upper-limit tables, PPPC4DMID + Pythia8 spectra, and writes
`Fermi_Likelihood = …` rows to `MadDM_results.txt` whenever `set
indirect_detection ON`. A thin `/gamlike` formatter that parses those
rows would unblock 2HDM+a ID + singlet-doublet ID — **double-unblock,
not triple** (dark-su3 has no MadDM run because it's non-SM color, per
constraints.yaml:768-770). Round-1 missed the dark-su3 caveat; round-2
corrected. Round-1 also falsely claimed the empty-READY `summary.json`
"validates locally" without actually running the validator — direct
verification returned `INVALID: 'schema_version' is a required
property`; round-2 added the field, ran the validator (exit 0), and
disclosed the round-1 falsehood. Round-1 also contaminated the main
repo by writing a zero-byte `sarah.lock` to
`/Users/yianni/Projects/hep-ph-agents/.shift-manager/locks/sarah.lock`;
round-2 deleted it after `lsof` no-holder confirmation and
codified a "worktree agents must never touch main-repo .shift-manager"
rule. Worktree `agent-a1acbc7b9ecb28aa6`, commit `97d6a94`. Sharp
edges: SE-2HDMA-FLOW-3/4/5/6, SE-INFRA-1/2/5, SE-PLAYTEST-1/3.

**Collider (placeholder by design).** Static-only mapping, ~12 min on
station. The collider entry is a triple-locked no-op: the per-model
Step 2 multi-select offers it, but the Step 2 validator re-asks if
selected alone, the constraint registry has empty chain +
`placeholder: true`, and `time_budget.py` hard-codes a `BLOCKED —
missing: ['collider-not-implemented']` short-circuit. The same JSON
block is byte-identical across all three demo models'
SKILL.md. Test invariants at
`_shared/tests/test_skill_structure.py:200,327,412,521` lock the
four-id menu shape. No collider analysis tools (Pythia driver, Delphes,
MadAnalysis5, CheckMATE, Rivet, SModelS) are installed. The smallest
first-cut MVP is parton-level σ(pp → χχ̄ + j) at 13 TeV with the
existing TwoHdmAfix UFO — but a parton-level σ is a sanity check, not
an exclusion test (real ATLAS limits use detector-smeared MET shape).
Reviewer signed off with four minor reservations (LHC_TOOLING_MISSING
isn't actually dormant; `config.json` path inventory was sloppy; nearby
edge case `["dd", "collider"]` produces two BLOCKED rows with nothing
to run; "half-day" first-cut estimate is closer to a full day).
Worktree `agent-a9c67d36cdb20a0b4`, commit `c494507`. Sharp edges:
SE-2HDMA-COLLIDER-1/2, SE-2HDMA-FLOW-7.

### Cross-cutting findings

These showed up in multiple workstreams or affect work beyond 2hdm+a.
Each has an entry in the consolidated sharp-edges; severity and
recommended next action below.

**1. `summary.json` missing `schema_version` (cross-model).** WS-id r1
emitted the un-versioned form and falsely claimed it validated;
WS-relic emitted the same un-versioned form and the reviewer flagged
it as pre-existing infra debt. The SKILL.md template at
`2hdm-a/SKILL.md:~509` still emits without `schema_version`, and the
same is likely true for `singlet-doublet` and `dark-su3` SKILL.md
templates. Sharp edge: SE-INFRA-1. Severity: MAJOR (production
deliverables fail validation against canonical core schema). Next
action: small cross-model patch to all three SKILL.md templates;
bundle with the SKILL.md headline drift fix (SE-2HDMA-MODEL-3).
~½ day.

**2. macOS lacks `flock` (verified).** WS-dd MAJOR-2. The documented
SARAH "global mutex" at `.shift-manager/locks/sarah.lock` referenced
in `2hdm-a/SKILL.md:247` is a **no-op on this platform**. Two
unrelated Wolfram kernels were observed running SARAH simultaneously
during the playtest round. Sharp edge: SE-INFRA-3. Severity: MAJOR
(silent platform-specific concurrency hazard). Next action: install
homebrew util-linux and patch SKILL.md to call
`/opt/homebrew/opt/util-linux/sbin/flock` (versioned-stable opt path,
not Cellar; binary is in `sbin/`, not `bin/`) — OR replace flock with
a Python `fcntl.lockf` helper. ~½ day.

**3. Watchdog stall pattern (cross-skill meta-finding).** Both
WS-relic (MadDM launch) and WS-dd (SARAH probes) hit it. Opus
subagents that synchronously block on long-running subprocesses get
watchdog-killed at ~600s of stream silence because a single blocking
`subprocess.run` is one tool call's worth of activity. Mitigation:
split into `Bash run_in_background=true` + Monitor poll loop emitting
events every <60s. Sharp edges: SE-INFRA-4, SE-PLAYTEST-2. Severity:
MAJOR (kills agents on the relic happy path if invoked naively).
Next action: codify the pattern in the playtest-noninteractive memory
or a dedicated `playtest-conventions.md` referenced from each
chain-running SKILL.md.

**4. Cross-worktree contamination risk (verified, codified).** WS-id
r1 wrote `.shift-manager/locks/sarah.lock` to MAIN repo against
policy; WS-id r2 cleaned it up after `lsof` no-holder check. Sharp
edge SE-PLAYTEST-1 codifies the rule with 4 numbered DON'Ts. Severity:
MAJOR (manager-level concern; risks future sibling collisions).
Next action: enforce in playtest-noninteractive memory; future
playtest agents must read the rule before running.

**5. B7 renderer bug — `time_budget.py:281` literal `/` slash on
non-skill markers.** Pseudo-marker tokens (e.g.
`spec-authoring-incomplete`) get rendered with literal `/`,
producing fake-looking skill names like `/spec-authoring-incomplete`
in user-facing output. Sharp edge: SE-INFRA-5. Severity: MINOR (UX
defect, not functional). Next action: 5-15 min fix to the renderer.

**6. B8 schema duality conflict.** Legacy
`_shared/summary.schema.json` (no `schema_version`,
`additionalProperties: false`) conflicts with canonical
`_shared/summary.core.schema.json`. Discovered while fixing #1 in
WS-id r2. Sharp edge: SE-INFRA-2. Severity: MEDIUM (latent risk of
conflicting validation outcomes). Next action: delete or update the
legacy schema; repoint `test_summary_schema.py`.

**7. `Vertex::ChargeViolating` warnings on TwoHdmAfix (verified).** WS-dd
r2 captured `dd_attempts/feynarts_v3/sarah.log` lines 121, 123, 129.
Charges sum to zero, so warnings appear puzzling — possibly a SARAH
false-positive on conjugate operators, possibly a real fixture bug
(hypothesis: `ZA` rotation matrix at TwoHdmAfix.m:102, or `ZP`
charged-Higgs sign). NOT seen in `MakeUFO[]` path (relic), so it's
specific to the `MakeFeynArts[]` code path. Sharp edge:
SE-2HDMA-MODEL-1. Severity: MAJOR (gates trustable DD output). Next
action: vertex-by-vertex audit against a reference 2HDM+a UFO before
relying on TwoHdmAfix for any DD work; this is a prerequisite for
`/looptools eval` to be physics-correct.

**8. SKILL.md headline drift: 10.15 → 10.493.**
`2hdm-a/SKILL.md:~509` still quotes the original Ω h² ≈ 10.15 from
iter-8; benchmark fixture was corrected to 10.493 in commit `f28ff93`.
Sharp edge: SE-2HDMA-MODEL-3. Severity: MINOR. Next action: two-line
patch.

**9. Stale `[PLANNED]` skill markers.** `/feynarts`, `/formcalc`,
`/ddcalc` all have mature SKILL.md (206/155/225 lines) but are still
labeled `[PLANNED]` in `2hdm-a/SKILL.md:58,146,480` and
`demo/SKILL.md:39`. Sharp edge: SE-2HDMA-MODEL-2. Severity: MINOR
(documentation drift). Next action: smoke-test under
`HEPPH_RUN_WOLFRAM_TESTS=1`; flip statuses + prose. ~30 min.

**10. Step-3 model picker label is stale.**
`plugins/hep-ph-toolkit/skills/demo/SKILL.md:72` still labels 2hdm-a as
"(currently BLOCKED — spec authoring incomplete)" while
constraints.yaml + 2hdm-a SKILL.md declare relic READY. Anyone
following `/demo` literally would be told it's blocked. Sharp edge:
SE-2HDMA-FLOW-2. Severity: MINOR. Next action: two-line fix.

### Follow-up punch list (ranked by leverage)

Items 1 and 2 unblock the most user-visible features; items 3 and 4
are infra debt with cross-cutting impact; items 5 is pure docs.
Notes on parallelization included where relevant.

1. **`/gamlike` v0** (1-2 days). Thin MadDM-output formatter parsing
   `MadDM_results.txt`. **Double-unblocks** 2HDM+a ID + singlet-doublet
   ID (dark-su3 excluded — non-SM color, no MadDM run). Conditional
   emission gotcha: `Fermi_Likelihood(Thermal)` only emits when `xsi
   < 1` (`maddm_run_interface.py:3573`). **Parallelizable with #2-#5**
   (different files, different plugin).

2. **`/looptools eval` runtime skill** (1 sprint, 5-10 days; r2-revised
   from "1-3 days"). The biggest DD unlock. Sub-tasks 1a-1g sum to
   44-80 hr. **Depends on SARAH-side resolution of #6**
   (`Vertex::ChargeViolating`) for trustable physics output — vertex
   audit is a prerequisite, not folded into the estimate.
   **Parallelizable with #1, #3, #4, #5** (different files).

3. **schema_version propagation** (cross-model, ~½ day). Fix template
   in all three per-model SKILL.md (`2hdm-a`, `singlet-doublet`,
   `dark-su3`); regenerate emitted `summary.json` in each
   `demo_output/<model>/`; consolidate B8 schema duality (delete or
   update legacy `_shared/summary.schema.json`). **Parallelizable
   with #1, #2, #4, #5**.

4. **flock portability fix** (~½ day). Either install homebrew
   util-linux and patch `2hdm-a/SKILL.md:247` to call
   `/opt/homebrew/opt/util-linux/sbin/flock` (and check that
   `singlet-doublet` and `dark-su3` SKILL.md don't have parallel bare
   `flock` invocations), OR replace with Python `fcntl.lockf` helper.
   Document the chosen fix in SKILL.md. **Parallelizable with #1, #2,
   #3, #5**.

5. **Stale label / marker cleanup** (15 min). SKILL.md headline drift
   (10.15 → 10.493); stale `[PLANNED]` markers on
   `/feynarts`, `/formcalc`, `/ddcalc`; Step-3 model picker label.
   Pure docs. Bundle with #3 above. **Parallelizable with all**.

6. **`Vertex::ChargeViolating` investigation** (1-2 days). Physics
   question. Vertex-by-vertex audit of TwoHdmAfix against a reference
   2HDM+a UFO. Hypothesis to test: `ZA` rotation matrix convention at
   `TwoHdmAfix.m:102` for the 3-state Ah mixing, or a `ZP` charged-Higgs
   sign. **Gates #2 partially** (without this, `/looptools eval` may
   produce numerically silent errors in Wilson coefficients).

7. **B7 renderer bug** (~15 min). `_shared/time_budget.py:281` —
   strip leading `/` from non-skill markers. **Parallelizable with
   all**.

---

## 2026-04-22 — 2HDM+a relic works end-to-end (autonomous 8-iteration loop)

**Headline.** `Ωh² = 10.15` (finite, off-resonance, expectedly overabundant)
for the 2HDM + pseudoscalar mediator benchmark at
`Mχ=100, Ma=400, gχ=1.0, tan β=10`. The full chain runs:
SARAH → UFO → MG5 → MadDM → `MadDM_results.txt`. First end-to-end 2HDM+a
result from this repo.

**How.** Autonomous playtest→fixer loop across eight branches
(`fix-loop/2hdm-iter-{0..8}`). Each iteration spawned a read-only playtest
agent to surface one blocker, then a fixer agent on a new branch. Two
ornery-opus counsel calls cut through dead-ends:

- Iter 2→3: "most 'renderer bugs' are spec-level or phantom. Fix the YAML first."
- Iter 5→6: "the hand-written golden is broken. Use SARAH's own
  `SM+VL/PortalDM/` as the canonical Dirac-singlet idiom."

The second counsel was the crux — the single-paired-field idiom
`{chi, 1, {chiL, chiR}, ...}` is silently broken in stock SARAH, which
bit iterations 2 through 5. Staub's own PortalDM uses two LH Weyls with
`conj[]` on the R field + a `DEFINITION[EWSB][Phases]` entry + a
`\[ImaginaryI]` prefactor on CP-odd Yukawas. Nothing in the web
literature states this as plainly as the bundled `.m` file itself.

**Sharp edges caught on the way.** Full catalogue in
`demo_output/2hdm-a/fix_loop/POST_MORTEM.md`, but the highlights:

- SARAH prefixes `M` on mass-eigenstate names → uppercase spec params
  like `Mchi` silently fail. Use `mchi`.
- SARAH has `A` as a gauge boson; a CP-odd singlet named `a` collides.
  Rename to `a0` in the spec.
- `DEFINITION[EWSB][Phases]` is required for unmixed Dirac fermions.
  Without it, `MakeUFO[]` silently drops the particle.
- MG5's auto-generated `param_card.dat` defaults Dirac rephasing
  parameters (`pchiR = rpchiR + i·ipchiR`) to `0+0i`. Every chi-chi-Ah
  vertex has these as a factor, so Ωh² comes out as the sentinel `-1`
  with all-NaN channels until `PHASES[1] = 1.0` is patched in.
- YUKAWA LHA block collision: three Yukawa matrices share `[1,1]`,
  MG5's `parameter_dict` keeps only the last → MadDM's EFT re-import
  fails with `mdl_ryu211 is not defined`. Split blocks into
  `YUKAWAU/YUKAWAD/YUKAWAE`.
- On-resonance (`2Mχ ≈ Ma`) hangs MadDM's Romberg integration
  indefinitely. Debug off-resonance first.

**What's NOT fixed.** The working `.m` files at
`/Users/yianni/SARAH/SARAH-4.15.3/Models/TwoHdmAfix/` were hand-crafted
to match the PortalDM idiom, not emitted by `/sarah-build`. Seven
renderer sites in `plugins/hep-ph-toolkit/skills/sarah-build/scripts/
sections/` + `render_templates.py` still need the PortalDM translation
logic. Enumerated in `iter_6_notes.md`. Medium effort; benefits every
future SARAH model with a Dirac singlet DM. The old broken golden at
`plugins/.../tests/goldens/2hdm_a/` should be replaced by the working
iter-6 version at `2hdm_a_fixed/`.

**Debugging techniques that paid off.**

- Running SARAH directly on the golden `.m` as a baseline test (Stage:
  suspected-our-bug → actual-bug: golden-is-wrong). The same pattern
  applies to any emitter: if the ground-truth reference also fails,
  the reference is wrong.
- `grep -c "chi" vertices.py` as the canonical "is the UFO usable" probe.
- `sample <pid> 3` on hung Fortran — shows whether it's in legitimate
  numerical integration or waiting on stdin.
- Reading SARAH's bundled `Models/` directory instead of re-deriving
  idioms. `SM+VL/PortalDM/` and `SM+VL/CPoddS/` are authoritative.

**Artifacts.** Full narrative at
`demo_output/2hdm-a/fix_loop/POST_MORTEM.md`. Per-iteration reports
`iter_{0..8}_*.md` in the same directory. The param-card patcher that
unlocked the finite number is 60 lines at
`demo_output/2hdm-a/fix_loop/iter_8_patch_paramcard.py`.

---

## 2026-04-22 — Playtest agent surfaces `/demo` friction in one pass

**The move.** Ran `/demo` end-to-end by giving Claude a single prompt —
*"Can you playtest the demo as if you were the user practitioner? Try to
get the relic density of a singlet-doublet model"* — and letting it
stand in for the physicist at every interactive gate. No scaffolding,
no checklist, no "also report these six things." Just a role and a
goal.

**What came back.** A numbered debrief with six ranked friction points.
Four were real and actionable:

1. **Pitch ≠ deliverable.** `/demo`'s opening hooks on direct-detection
   blind spots, but the only ready constraint is relic. Bait-and-switch
   feeling — not severe but not nothing. (Resolves when FeynArts /
   FormCalc / DDCalc ship.)
2. **Cache blindness.** Config had fresh SARAH/SPheno/SLHA stamps from
   the same day; the time gate still quoted cold hours. (Leaving this
   — `/demo` is meant to run cold.)
3. **Gratuitous scan spec.** `singlet-doublet/SKILL.md` §4b prescribed
   ≥3 benchmark points and a θ-sweep; the demo intent is one point.
   Patched: 4b/4c/4d rewritten to single-point, channel-breakdown
   figure instead of (m_χ, sin 2θ) scatter.
4. **Hardcoded masses.** The §4c record template wrote `m_chi1` as a
   literal. Patched: example now parses SPheno `Block MASS · # FChi_1`
   into the record.

And the two rejected — scripted `/lagrangian-builder` interview is
theater by design; MadDM "parameter not found" warnings for unset BSM
widths are expected and fine.

**Why this worked.** The agent was naive about what the skill was
supposed to do, so it noticed everything a careful first-time user
would notice — and nothing a maintainer wouldn't question. The
practitioner voice ("As a practitioner I'd expect…", "I'd be a little
confused that the intro pitches…") was load-bearing: it kept the
report grounded in user experience rather than implementation
critique. It also produced a live run to `Ω h² = 0.292` on the
single-Yukawa limit without hand-holding — which is the regression
check the demo is supposed to be.

**How to repeat it.** Launch an Opus subagent with the user's original
prompt *verbatim*, no context leakage from previous runs. The subagent
has to re-read the skills cold and make its own decisions about when
to ask, when to run, when to flag. Anything you pre-tell it about the
demo poisons the playtest — it'll defend what it's been told rather
than notice it.

**What we'd never have caught ourselves.** The scan spec (#3) had sat
in the skill since it was drafted; re-reading it as the maintainer I'd
have glossed past "run at least three benchmark points" because I know
why it was written that way. The playtest agent doesn't — it executed
the single-point reading, finished in five minutes, and then politely
asked at the summary why the skill kept talking about scans.
Maintainer eyes don't re-read demos as first-time users; playtest
agents do.

---

## 2026-04-22 — Paper-driven interview for `/lagrangian-builder`

**What this should feel like.** A physicist opens Claude Code, asks
*"what's the relic density of DM in a singlet-doublet model?"*, the
pipeline runs, a number comes back. That's the product. Nobody should
be asked to "enumerate the SU(2)×U(1)-invariant operators admitted by
their field content" — doing the group theory is what the tool is for.

**What the current interview asks.** A twelve-ish question checklist
closer to filling in a SARAH `.m` file than to describing a model. It
works for a Claude instance that's already read the SARAH manual; it
fails for the physicist the tool is for.

**Why it matters now.** After yesterday's first relic number from
singlet-doublet, I went back to check: could Claude actually reproduce
that spec from the written interview, cold? No. The demo's
`singlet_doublet.yaml` has seven non-obvious features — two-left-Weyl
doublet topology, a `Z2 DMParity` that prevents SARAH silently dropping
Higgs-portal Yukawas, two SU(2)×U(1) Yukawa contractions instead of one,
an `FS` field name chosen because `S` collides with a SARAH internal
symbol, and so on — and the interview guides the user to none of them.

**First instinct was wrong.** I drafted a list of gates: "does your
paper define a Z2?", "if your doublet mixes with a singlet, use two
left-Weyls." None generalize. Z2 is DM-specific. Two-left-Weyl is
singlet-doublet-specific. A Dark-SU(3) physicist reading that interview
gets asked questions that don't apply to them at all.

**The right shape.** Given field content + gauge groups, the set of
renormalizable invariant operators and the set of post-VEV mixing
sectors are *deterministic*. The physicist should not enumerate either.
Claude should. The interview drops from twelve questions to four:

1. What are you studying?
2. What are the new fields and gauge groups?
3. *"Here's my best guess at the renormalizable Lagrangian given those
   fields. Please edit."* Claude enumerates; the user deletes forbidden
   terms. Discrete symmetries are **inferred** from the deletion
   pattern, not asked about.
4. *"Here are the mass eigenstates I detected post-EWSB. Confirm the
   rotations."* Claude detects mixable sectors; user renames and
   confirms.

All SARAH-idiomatic knowledge (LagHC vs LagNoHC, reserved names,
two-Weyl topology) stays inside Claude — referenced at draft time,
surfaced to the user only if it needs confirming. It lives in a new
`references/sarah-gotchas.md`, not in the physicist-facing interview.

**The hard part: Claude is now doing analytical work.** Enumerating
invariants is group theory. A wrong enumeration silently breaks the
pipeline three stages later — exactly the failure mode we already hit
with singlet-doublet (a zero Higgs-portal vertex that took seven tries
to surface). The mitigation is **fast feedback**, not **perfect
first-draft**:

- Post-SARAH: `check_vertices.py` compares the UFO vertex set against
  the spec's declared terms. A dropped vertex is a known-signature
  silent failure. Feeds back to Q3.
- Post-SARAH: `check_mass_matrix.py` flags `OnlyZero` degeneracies
  and rank-deficient blocks. Feeds back to Q4.
- Post-SPheno: `check_spectrum.py` range-checks the computed masses.
  NaN or zero where a spec parameter was nonzero → feeds back to Q3
  or parameter defaults.
- Post-observable: the downstream tool reports whether the result is
  physically sane (Ωh² > 0, σ ≥ 0, BR ∈ [0,1]).

Each checkpoint emits a structured blocker. Claude correlates it with
the gotchas doc, patches the spec, retries. The physicist sees the
loop — it isn't hidden — and the preamble sets the expectation up
front: *"I may need 2–3 passes; here's what failure looks like and
how I'll recover."*

**What this buys.** The same four-question interview works for
singlet-doublet, 2HDM, and dark SU(3) — no model-specific gates. The
first-draft YAML doesn't have to be perfect, only correctable. And
Claude stays fast at its analytical work because every stage has a
concrete "did that work?" answer it can act on without waiting for a
human.

**Next.** Draft `sarah-gotchas.md`, wire `check_vertices.py` /
`check_mass_matrix.py` / `check_spectrum.py` into
`lagrangian-builder/SKILL.md`'s main loop, swap `/demo`'s
singlet-doublet step 4a from the pre-built YAML to a
`/lagrangian-builder` invocation. Only after all three land does the
new interview get exercised for real.

---

## 2026-04-22 — First end-to-end `/demo` success (singlet-doublet relic)

**What ran.** Playtested `/demo` → Singlet-Doublet → relic density,
acting as the user. All three of the paper's benchmark models were
exercised. Singlet-Doublet produced a computed
`Ω h² = 0.163` (overabundant vs Planck 0.120) at the
`(M_S, M_Ψ, y, θ) = (150, 500, 1, 0)` benchmark —
the first end-to-end number from the full chain. 2HDM+a and
Dark SU(3) are still blocked and were recorded as such.

**What got in the way.** Six sharp edges, all captured in skill-level
references:

- **SPheno can't compile the SARAH-emitted RGEs.** `gfortran` aborts
  on `SAxDynkin(2,color)` / `SAxCasimir(2,left)` symbols that SARAH
  left unevaluated. This is the long-standing "SARAH leaks internal
  symbols into Fortran" bug. Workaround: route around SPheno via
  `/spheno-build`'s analytic backend, which was already registered
  for `singlet_doublet`. Recipe:
  `plugins/hep-ph-toolkit/skills/spheno-build/references/analytic-bypass-recipe.md`.
- **`config.json.models.singlet_doublet.spheno_bin` pointed to a
  binary that doesn't exist** — `/spheno-build`'s failed compile left
  the registry entry behind while never producing the binary.
  `/demo`'s preflight does not probe this path. Worth adding.
- **MG5's plugin loader trips on a dotted sibling dir in
  `PLUGIN/`.** A `maddm.broken-backup-2026-04-22/` backup that
  `/maddm-install` left behind gets parsed as
  `PLUGIN.maddm.broken-backup-2026-04-22` and aborts plugin discovery.
  Moving it out of `PLUGIN/` (to `_archived/`) fixes it.
  Documented in
  `plugins/hep-ph-toolkit/skills/maddm-install/references/maddm-workarounds.md`
  § 18.
- **`import model SingletDoublet__REAL` silently resolves to an
  unrelated stub UFO** in `$MG5_HOME/models/`. Full-path import of
  the SARAH-output UFO is the only reliable route. Documented in the
  new
  `plugins/hep-ph-toolkit/skills/madgraph/references/mg5-model-import-gotchas.md`
  § 1.
- **`generate_maddm` is a command that doesn't exist**, so
  `do_output` auto-adds relic + DD + ID + `indirect_spectral_features`
  — the last of which crashes on tree-level-only UFOs. Fix: call
  `generate relic_density` explicitly before `output`. Already in
  the maddm-workarounds catalogue § 10, 12.
- **`define darkmatter <pdg>` fails**; it needs the lowercased
  particle name (`chi1`). Already in the maddm-workarounds catalogue
  § 11.

**What this tells us about `/demo`.** The happy path in the skill
prose assumes every step of SARAH → SPheno → MG5+MadDM works. Today
only the analytic-bypass variant works, and nowhere does the skill
describe that variant. Two small prose changes would make the skill
self-aware:

1. `/demo` Step 0 preflight: in addition to executables responding,
   validate any `spheno_bin` path in `config.json.models.*` actually
   exists on disk.
2. `singlet-doublet` Step 4b: if `/spheno-build`'s SPheno backend
   fails with `SPHENO_COMPILE` (or the cache shows a failed compile),
   fall back to the analytic backend automatically and note the
   fallback in the headline. The demo user should not need to know
   the SAxDynkin story to finish the run.

Playtest driver preserved at
`demo_output/singlet-doublet/retry_analytic/drive.py`.

---

## 2026-04-22 — How this began

**Goal.** Build a suite of skills so a physicist can ask Claude Code things
like *"what's the relic density of a singlet-doublet model?"* and get a
real answer, computed with the tools the field already uses. After some
searching, the HEP tools for this already exist (SARAH, SPheno, MadGraph,
MadDM, micrOMEGAs, …) — so the job is not to replace them but to wrap
them in skills descriptive enough that the model knows when to reach for
which one.

**Benchmarks first.** To know whether these skills are actually useful,
I needed a ground-truth target. My old advisor Stefano Profumo has a
paper on the singlet-doublet model that's perfect: the formulas and
numerical results are all published. I had Claude Code pull the paper,
extract the equations and quantities, and stand up an eval harness where
agents are prompted with and without the tools to reproduce the paper's
results with no human in the loop. With that in place, we have an
environment where Claude can, in principle, improve the very tools it's
using.

**Onboarding before breadth.** Before wiring up the full physicist's
toolkit, I wanted a real user. That means UX and onboarding aren't
optional. `/demo` is a pre-paved path: take a paper already in the
benchmarks and walk through reproducing it end-to-end using the tool
the practitioner is most familiar with. I am not assuming users have any
prior Claude Code experience.

**Sharp edges everywhere.** Getting these tools to work surfaced every
ugly corner I remember from five years ago when I set them up by hand —
brittle Fortran toolchains, version-sensitive Mathematica packages,
cryptic failure modes, undocumented environment assumptions. Claude
Code has been remarkable at debugging and patching around them in the
moment. The risk is that Claude gets *so* good at patching that the
underlying sharp edges stay hidden forever. That's bad for the field.

**The log's job.** Individual sharp edges and their workarounds are
logged *inside each skill's folder*, so future Claude Code instances
working on that skill see them in-context. This devlog is the
higher-level narrative: origin, design decisions, cross-cutting
lessons, and pointers into those per-skill notes. Over time, it should
also track which sharp edges deserve to be engineered away permanently
(better packaging, modernization, upstream fixes) rather than papered
over run after run.

**Constraints.** Compute is the tight one right now.
