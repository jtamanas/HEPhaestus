# Critique — Singlet-Doublet Playtest Proposal

Position: proposal has a load-bearing factual error (wrong baseline
number) and a load-bearing fictional artifact (`drive.py` flag
surface). Two-variant structure and JSONL approach are sound; the
operational core needs rework.

## 1. Verified facts (file:line)

- **`HEPPH_STATE_ROOT` is the env var, not `STATE_ROOT`.**
  Defined `plugins/model-building/SHARED.md:18-22`; honoured by
  `sarah-build/scripts/build.py:82`,
  `spheno-build/scripts/run_point.py:95`,
  `spheno-build/scripts/compile_model.py:724`.
  PASS for isolation — but proposer wrote `STATE_ROOT=...` raw in §8;
  unread. Must be `HEPPH_STATE_ROOT=...`.
- **SARAH same-model lock real.** `sarah-build/scripts/run_sarah.py:176-196`
  (`_sarah_build_lock`) — per-model fcntl on
  `$sarah_path/Private-Models/<Name>/`. Distinct model names ARE
  parallel-safe at SARAH. PASS.
- **MadDM `PLUGIN.maddm.broken-backup-*` failure documented:**
  `monte-carlo-tools/skills/maddm-install/references/maddm-workarounds.md:363-372`.
  PASS.
- **Wolfram offline-capability NOT verifiable from repo.**
  `plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh`
  is an activation-status classifier (runs `wolframscript -code '1+1'`).
  Once activated, runs offline; staleness check needed at launch.
  PARTIAL.
- **`drive.py` flag surface FAIL.** See §2a.
- **`0.163 ± 0.005` baseline FAIL.** See §2b.

## 2. Factual errors

### 2a. `drive.py --flags` is fiction (CRITICAL)
`demo_output/singlet-doublet/retry_analytic/drive.py:108-117`:
```python
if len(sys.argv) != 6:
    print("usage: drive.py <idx> <MS> <MPsi> <y> <theta_rad>", ...)
```
5 positional args. Does NOT accept `--constraints`, `--practitioner`,
`--out_dir`, `--log`, `--issues`. Does NOT exercise
`/lagrangian-builder`, `/sarah-build`, or `/spheno-build` — UFO path
hardcoded at line 25. The actual playtest entrypoint is the `/demo`
skill (`plugins/hep-ph-demo/skills/demo/SKILL.md`) executed by Claude
in a session. The proposer's §3 invocation will fail at argparse, then
the "thin wrapper" escape hatch silently expands to "rewrite the
playtest harness." Not acceptable as written.

### 2b. Regression target `0.163` is stale by 18 hours (CRITICAL)
Latest `demo_output/singlet-doublet/relic.json` (run 2026-04-24T02:33Z)
reads `omega_h2: 0.292` at the same `(MS=150, MPsi=500, y=1, θ=0)`
benchmark. `relic_2.json` and `relic_playtest.json` agree at 0.292.
`0.163` is from `docs/devlog.md` 2026-04-22 — superseded. A `0.163 ±
0.005` strict regression FAILS on a fresh canonical run TODAY.
`±0.005` is also unjustified ad-hoc — analytic-bypass + deterministic
two-phase relic should have variance < 0.001 (fp drift only).

### 2c. Path typos
Proposer writes `demo_output/singlet_doublet/` (§6, §9). Actual is
hyphenated: `demo_output/singlet-doublet/`. Breaks literal
greps/checks.

### 2d. Q3/Q4 names misquoted
`practitioner_script.md:48,61` says `MS` and `ZN` (no underscores).
Proposer's "M_S → MChi, M_Psi → MD" is against a spelling that doesn't
exist.

## 3. Design challenges

**Variant B (perturbed renames) — REVISE.** `MS → MChi` re-tests a
KNOWN documented gotcha (scope.md:25, 2HDM+a POST_MORTEM:
`Mchi → mchi` SARAH M-prefix collision). That's a regression test, not
a "cold-read deviation" — drop the cold-reader narrative. Keep
`ZN → N` (genuine MSSM-conventions collision). For a real cold-read
test, perturb physics-irrelevant prose in Q1/Q2, not parameter names.

**Observe-only stance — REJECT as written, REVISE.** User said "spin up
agents to resolve issues." Proposer's stance is fine for the playtest
session but doesn't satisfy the shift-level directive. Make the
two-phase contract explicit: playtest IS observe-only AND synthesizer
has standing authority to dispatch fix subagents per `issues.jsonl`
entry. Don't drop the user's directive on the floor.

**Two-variant split — KEEP.** Sound. Don't add C/D/E.

## 4. Quantitative challenges

- **Item 4 range `[0.05, 0.40]`:** too loose AND too tight.
  Planck is 0.12 ±5%. 0.40 is 3× over; 0.532 (`relic_4.json`) is
  excluded. Use practitioner bar: `omega_h2 ∈ [0.10, 0.40]` AND within
  factor-2 of stored canonical (now 0.292). Or drop range; rely on
  item 3 + item 5.
- **Item 5:** fix value to 0.292, tighten to `±0.01`. If empirical
  variance exceeds, that's itself a finding.
- **Item 8 `mg5_aMC --mode=maddm`:** drive.py uses
  `/Users/yianni/MG5_aMC/bin/maddm.py` (line 24). Realign grep target
  after a dry-run; current shape unverified.
- **Items 1+3 collapse:** parseable `summary.json` with status==ok
  implies item 1+2. Drop item 1.
- **10 → 6 checks:** parses, status ok, value in tightened range,
  matches canonical (A only), plot exists+sized, validate_spec exits 0.
- **90-min ceiling:** Wolfram seat is realistically 1-local. Proposer's
  "75-min if serialised" understates. Realistic combined wallclock
  60–80 min. Make 90 min the TOTAL ceiling, not per-variant.

## 5. Missed failure modes

1. **Stale `demo_output/singlet-doublet/`** has 5+ `maddm_run*` dirs +
   `relic_{1..4}.json` + `summary_playtest.json` from prior runs. The
   `/demo` skill reads `./demo_output/<model>/summary.json`
   (SKILL.md:94) — interleaving risk. **Mitigation:** move aside to
   `demo_output/singlet-doublet.preplaytest-<TS>/` before launch.
2. **Global `config.json`** (`~/.config/hep-ph-agents/config.json`)
   tracks `models[]` registry. Worktrees do NOT isolate it.
   `register_model()` from A could overwrite B's slot. **Mitigation:**
   per-variant `XDG_CONFIG_HOME`, OR distinct registry names
   (`singlet_doublet_A`/`_B`).
3. **Wolfram silent license-server retry.** Activation re-checks
   periodically; with offline-night, blocks SARAH minutes per call.
   Mitigation: 5-second `wolfram -version` smoke at launch.
4. **MadDM/MG5 version drift.** No pin between baseline (Apr 22) and
   now. Capture `mg5_aMC --version` + MadDM plugin SHA in `env.json`.
5. **Hardcoded UFO path under `~/.local/share/hep-ph-agents/`** —
   bypassing `HEPPH_STATE_ROOT` lets variants stomp each other's UFO
   cache. Confirm env var is exported BEFORE any tool runs.

## 6. Concrete `issues.jsonl` examples

Proposer's schema is structurally OK. Make it concrete with two
worked examples for the synthesizer to pattern-match:

```json
{"id":"sd-A-001","ts":"2026-04-24T20:42:11Z","severity":"medium",
 "phase":"madgraph","symptom":"PLUGIN.maddm.broken-backup-* import failure on first MG5 launch",
 "evidence_paths":[".playtest/sd-A/console.log",".playtest/sd-A/run.log:L1342-1380"],
 "log_excerpt":"error detected in plugin: maddm.broken-backup-2026-04-22\nNo module named 'PLUGIN.maddm.broken-backup-2026-04-22'",
 "hypothesis":"Hyphen-containing sibling dir under $MG5_PATH/PLUGIN/ misparsed as submodule (maddm-workarounds.md:363-372).",
 "blocking":false,"variant":"A","expected_fix_scope":"tool-driver",
 "remediation_hint":"mv $MG5_PATH/PLUGIN/maddm.broken-backup-* /tmp/",
 "tool_versions":{"mg5":"3.5.7","maddm":"git@abc123"}}
```

```json
{"id":"sd-B-003","ts":"2026-04-24T21:11:07Z","severity":"high",
 "phase":"sarah-build","symptom":"SARAH MMChi symbol redefinition after Q3 rename",
 "evidence_paths":[".playtest/sd-B/state/models/singlet_doublet_B/sarah_output/sarah.log"],
 "log_excerpt":"Symbol MMChi already defined in context...",
 "hypothesis":"SARAH M-prefix collision (POST_MORTEM 2hdm-a iter 4); validate-interview should reject MChi.",
 "blocking":true,"variant":"B","expected_fix_scope":"skill-prose",
 "remediation_hint":"Add MChi to lagrangian-builder reserved-names list."}
```

Add: `remediation_hint` (≤500 chars, optional), `tool_versions`
(object, optional). Drop `$schema` line — JSONL doesn't carry per-line
schema; put it once in `result.json`.

## 7. Summary — what survives, what changes

**Survives:** two-variant A/B, JSONL schema (with concrete examples),
failure taxonomy §5, frozen artifact contract §9 paths (modulo
hyphen), 90-min ceiling.

**Must change:**
1. Drop fictional `drive.py --flags`. Harness IS Claude executing
   `/demo` in a session, pointed at the variant's practitioner script.
2. Fix regression: **0.292**, not 0.163; tolerance `±0.01` or
   "matches latest stored `summary.json` within 5%."
3. `STATE_ROOT` → `HEPPH_STATE_ROOT`; per-variant `XDG_CONFIG_HOME`.
4. Move stale `demo_output/singlet-doublet/` aside before launch.
5. Reframe Variant B as known-gotcha regression. Keep `ZN→N`; drop
   or downgrade `MS→MChi` (re-tests scope.md:25).
6. Collapse 10 checks to 6; fix item 4 range; verify item 8 grep
   target after a dry-run.
7. Authorise synthesizer to spawn fix agents per the user directive.
