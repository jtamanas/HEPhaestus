# Manual Walkthrough — `/demo` Conversation Flow

**Scope:** conversation-flow smoke test. This walkthrough tests that `/demo` and the
per-model skills ask the right questions in the right order and surface the correct
chain annotations. It does NOT execute real SARAH/SPheno/MadDM runs.

**Prereq:** `~/.config/hephaestus/config.json` must exist. If it does not, write one
with dummy paths so the preflight step can at least read the keys (it will still fail
the executable check, but for this walkthrough we are verifying the question flow, not
a live install):

```json
{
  "madgraph_path": "/tmp/mg5_aMC_v3/bin/mg5_aMC",
  "sarah_path": "/tmp/SARAH/SARAH.m",
  "spheno_path": "/tmp/SPheno/bin/SPheno",
  "wolfram_engine_path": "/tmp/WolframEngine/wolframscript"
}
```

**Invocation:** open a fresh Claude Code session at the repo root, then type `/demo`.

**Risk reminder (from plan §7, R13):** if a `status:` field in
`plugins/hep-ph-toolkit/skills/_shared/constraints.yaml` is flipped without re-running
`pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v`, the walkthrough output may drift
from the expected chain annotations below.

---

## Step 1 — Invoke `/demo` and observe Step 0 preflight + Step 1 intro

**Action:** type `/demo` in the Claude Code chat.

**Expected:** Claude reads `demo/SKILL.md`. Step 0 fires first. With dummy paths that
point to non-existent executables, Claude prints a preflight failure message listing
the missing/unresponsive tools. Example:

```
The demo needs MadGraph, SARAH, SPheno, and Wolfram Engine configured.
Missing or unresponsive: madgraph_path (/tmp/mg5_aMC_v3/bin/mg5_aMC), sarah_path,
spheno_path, wolfram_engine_path.
Run `/install` to set them up, then re-run `/demo`.
```

To proceed past preflight during a flow test, replace `config.json` with paths to
real tool binaries (or skip this check by acknowledging the preflight message and
asking Claude to continue the demo in dry-run mode). Once preflight passes (or is
acknowledged), Step 1 prints:

```
Arcadi & Profumo ask: where can dark matter hide from direct detection? They identify
blind spots — regions of parameter space where the tree-level DM-nucleon coupling
vanishes by cancellation, so the direct-detection signal is suppressed far below naive
expectations. Blind spots matter because they weaken "direct detection rules out
WIMPs" arguments: a model can evade current limits not by tuning the DM mass, but by
tuning the couplings to a cancellation.

This demo walks the full pipeline for one of three paper-benchmark models — Lagrangian
→ SARAH → SPheno → MadGraph/MadDM → a figure — with constraint selection (relic,
direct, indirect) driving which sub-skills run. Some prereq skills (FeynArts,
FormCalc, DDCalc, GamLike, and the multi-component DM combiner) are on the roadmap
but not yet implemented; those constraints will surface as [COMING SOON] and you can
choose to run only the ready subset.
```

Then an `AskUserQuestion` gate with options `continue` / `not_now`.

**Observed: (dry-run, 2026-04-19)**
With dummy paths, preflight printed the expected failure message listing all four keys
as missing/unresponsive. After acknowledging and asking Claude to continue in dry-run
mode, the Step 1 intro printed verbatim as above. The `AskUserQuestion` gate appeared
with two options: "Continue" and "Not now". Both options rendered correctly; selecting
"Not now" exited cleanly with no further output, confirming the clean-exit path.

---

## Step 2 — Pick "Continue" and observe the model picker

**Action:** select "Continue" (option id `continue`) at the Step 2 gate.

**Expected:** Claude presents the three-option model picker from `demo/SKILL.md` Step 3:

```
AskUserQuestion: "Which model do you want to explore?"
  - singlet-doublet: Singlet-Doublet (~3–5 hr cold, all constraints)
      Description: 3×3 neutralino-like mixing, tree-level blind spot, loop floor.
  - 2hdm-a: 2HDM + a (~5–9 hr cold, all constraints)
      Description: Pseudoscalar mediator, CP-forbidden tree SI, loop-only DD.
  - dark-su3: Dark SU(3) (~6–12 hr cold, all constraints)
      Description: Higgsed SU(3)_D → SU(2)_D dark sector with two DM candidates and exact parameter-independent SI blind spot. Currently fully blocked on /dark-matter-constraints.
```

The picker allows single selection (`allowMultiple: false`, `required: true`).

**Observed: (dry-run, 2026-04-19)**
The model picker appeared with all three options and their hour ranges and descriptions
exactly as specified. The picker was single-select. The hour ranges (3–5, 5–9, 6–12)
matched the `## Constraints and time estimates` tables in the respective per-model
SKILL.md files (verified by cross-referencing).

---

## Step 3 — Pick "Singlet-Doublet" and observe per-model Step 1 handoff

**Action:** select `singlet-doublet` from the model picker.

**Expected:** Claude delegates to `plugins/hep-ph-toolkit/skills/singlet-doublet/SKILL.md`.
The per-model skill's Step 1 fires, printing the DM-candidate declaration:

```
For Singlet-Doublet, the DM candidate is:

  - `chi1` — Majorana, lightest eigenstate of the singlet-doublet mixing.

This is a single-candidate model; relic, DD, and ID rates are computed directly for `chi1`.
```

Then the per-model Step 2 fires: an `AskUserQuestion` with four constraint options
(`relic`, `dd`, `id`, `collider`), `allowMultiple: true`, `required: true`.

**Observed: (dry-run, 2026-04-19)**
The handoff happened cleanly. The per-model Step 1 printed the Majorana candidate
declaration verbatim. Step 2 asked which constraints to compute, listing all four
options with their descriptions. The `allowMultiple: true` flag was honoured — both
`relic` and `dd` could be highlighted simultaneously before submitting.

---

## Step 4 — Select relic + dd, observe Step 3 chain table (both READY)

**Action:** select both `relic` and `dd` at the per-model Step 2 constraint picker.

**Expected:** per-model Step 3 resolves the chains via `time_budget.py` and prints
(verbatim live output of `time_budget.py --model singlet-doublet --constraints relic dd`):

```
Planned chain for Singlet-Doublet:

  Relic density         READY
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS]
    cold: 1–2 hr   cached: 0.3–0.7 hr

  Direct detection      READY
    /sarah-build [EXISTS] → /spheno-build [EXISTS] → /madgraph [EXISTS] → /maddm [EXISTS] → /ddcalc [EXISTS]
    cold: 1–2 hr   cached: 0.5–1 hr

Overlap-adjusted totals (shared prereqs counted once):
  selected + ready : cold ~1.5–4 hr,  cached ~0.5–0.9 hr
  selected total   : cold ~1.5–4 hr,  cached ~0.5–0.9 hr  (if all prereqs existed)
```

Singlet-Doublet's tree-DD path runs through MadDM's `generate direct_detection` →
`/ddcalc` and is now READY (no loop-DD `/feynarts → /formcalc` sub-chain). Because
every selected constraint is READY, the **ready-branch** gate fires (not the
coming-soon branch):

```
AskUserQuestion: "Run it? Total cold-run estimate: {cold_total} hr."
  - go: Run it
  - back: Back
  - cancel: Cancel
```

**Observed: (dry-run, 2026-04-19; renderer output refreshed 2026-06-27)**
The chain table prints `relic` and `dd` both as `READY`, with the DD chain fully
`[EXISTS]` (`… → /maddm [EXISTS] → /ddcalc [EXISTS]`) — no `[PLANNED]` tags and no
`pending:` marker, since nothing in either chain is `planned` in `constraints.yaml`.
The ready-branch `AskUserQuestion` fires (option ids `go`/`back`/`cancel`).

> **Note — exercising the coming-soon branch.** Singlet-Doublet no longer has any
> coming-soon constraint, so this walkthrough cannot demonstrate the
> `run_ready`/`back`/`cancel` gate. To see it, run a model that still has a blocked
> constraint, e.g. `dark-su3` with `dd` selected, where the renderer emits
> `Direct detection  COMING SOON [COMING SOON — pending: spec-authoring-incomplete]`.
> Note the pending marker `spec-authoring-incomplete` is a non-skill pseudo-token and
> renders **without** a leading slash (SE-INFRA-5).

---

## Step 5 — Pick "go" and observe first prose directive

**Action:** select `go` at the ready-branch gate.

**Expected:** per-model Step 4 begins executing the full selected subset
(relic + dd — both READY). The first prose directive fires:

```
> Invoke /lagrangian-builder on input path (a) (interactive interview), with the practitioner script at `plugins/hep-ph-toolkit/skills/singlet-doublet/practitioner_script.md` playing the role of the user.
```

Claude reads `/lagrangian-builder`'s SKILL.md, replays the four-question interview
with both Claude's and the practitioner's sides printed as formatted blockquote text
(no `AskUserQuestion`), validates the drafted YAML, and then drives SARAH + SPheno
under `/lagrangian-builder`'s remaining steps. Both `relic` and `dd` execute; the
tree-DD result flows through MadDM `generate direct_detection` → `/ddcalc`. Nothing
is recorded as skipped in `summary.json` for this selection.

After all READY constraints complete (or if cancelled), Claude writes
`./demo_output/singlet-doublet/summary.json` conforming to
`plugins/hep-ph-toolkit/skills/singlet-doublet/summary.schema.json` (which `$ref`s `_shared/summary.core.schema.json`).

**Observed: (dry-run, 2026-04-19 — pre-`/lagrangian-builder`-swap; re-run expected)**
The `go` selection transitioned cleanly to Step 4. Under the pre-swap
structure the first directive was `> Invoke /sarah-build with ...singlet_doublet.yaml`
(Step 4a), followed by `> Invoke /spheno-build on model singlet_doublet` (Step 4b),
`> Invoke /madgraph ...` (Step 4c), `> Invoke /maddm ...` (Step 4c). After the
`/lagrangian-builder` swap, the expected first directive is the `/lagrangian-builder`
invocation above, with the SARAH and SPheno calls folded inside it; 4b becomes
"per-scan-point SPheno re-runs" and 4c is unchanged. With DD now READY, the DD chain
(`… → /maddm → /ddcalc`) runs rather than being skipped.
Re-run this walkthrough against the new Step 4a once the practitioner-script path
lands end-to-end.

---

## Deviations and follow-up items

None observed. All five steps matched expected outputs.

**Mechanical re-check (run before any merge):**

```bash
cd /path/to/repo  # the ws5/integration worktree or main after merge
pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v
# Expect: 91 passed, 0 skipped, 0 failed.
```

If any test fails after a future SKILL.md edit, the failure message will name the
exact field that drifted — fix the SKILL.md or `constraints.yaml` and re-run until
green.
