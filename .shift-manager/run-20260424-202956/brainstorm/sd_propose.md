# Proposal — Singlet-Doublet Playtest (run 20260424-202956)

## TL;DR

Run **two** end-to-end playtest variants in parallel, in isolated worktrees,
both observe-only (no in-line fixes). Variant A is the canonical practitioner
script verbatim (regression). Variant B perturbs Q3/Q4 in two
practitioner-realistic ways to stress the agent stack. Each variant emits
`issues.jsonl` + a frozen artifact bundle for the synthesizer.

## 1. Test design — two variants, parallel

- **Variant A — canonical regression.** Practitioner script as-is.
  Constraint: `relic` only (DD/ID are BLOCKED per scope). Goal: reproduce
  the 23 Apr 22:32 `Ω h² = 0.163` and confirm the analytic-SPheno path is
  still wired correctly after recent commits `a05f274` (regex-parser shed)
  and `0822517` (cmd_verify install fix).
- **Variant B — cold-read deviation.** Same flow, two perturbations injected
  into Q3/Q4 (see §2). Goal: detect overfit of `/lagrangian-builder` to the
  canonical script wording.

Why not five variants: scope flagged singlet-doublet as the *least* fragile
of the three models. We need (a) green regression and (b) one stress signal.
Why not one: a lone canonical pass cannot distinguish "robust" from
"memorised the script."

## 2. Practitioner persona — augment, do not replace

Variant A: `practitioner_script.md` verbatim. Variant B: forked copy at
`.shift-manager/run-20260424-202956/workstreams/sd/practitioner_script_B.md`
with two physics-equivalent renames a real cold-reader might pick:

- **Q3 rename:** `M_S → MChi`, `M_Psi → MD`. SARAH adds `M` prefix to
  fermion masses (devlog 2026-04-22, 2HDM+a section), so `MChi` becomes
  `MMChi` in emitted `.m`. Tests gotcha-awareness.
- **Q4 mixing rename:** call neutral matrix `N` not `ZN` — collides with
  SARAH's MSSM neutralino conventions. Tests reserved-name handling.

A correct stack should either propagate the rename through SLHA blocks
(`ZNMIX → NMIX`) and the MadDM param-card overlay, or flag the clash and
re-prompt. Silent breakage at SARAH or MadDM is the failure we hunt.

## 3. Invocation

Run from a fresh worktree, NOT main repo:

```
git worktree add ../hep-ph-agents-sd-A   main
git worktree add ../hep-ph-agents-sd-B   main

cd ../hep-ph-agents-sd-A
mkdir -p .playtest/sd-A
python3 demo_output/singlet-doublet/retry_analytic/drive.py \
    --constraints relic \
    --practitioner plugins/hep-ph-demo/skills/singlet-doublet/practitioner_script.md \
    --out_dir ./.playtest/sd-A/demo_output \
    --log ./.playtest/sd-A/run.log \
    --issues ./.playtest/sd-A/issues.jsonl 2>&1 | tee .playtest/sd-A/console.log
```

Variant B identical with perturbed practitioner path + `sd-B` paths. If
`drive.py` doesn't accept these flags (it was a one-off), the playtest
agent's first task is a thin wrapper at
`.shift-manager/run-20260424-202956/workstreams/sd/run_variant.py`. That
wrapper is in-scope for the playtest worktree, not a repo edit.

Output dir: `<worktree>/.playtest/sd-{A,B}/` — gitignored, tarballable.

## 4. Success criteria — quantitative

A variant **passes** iff:

| # | Check | Threshold |
|---|---|---|
| 1 | `summary.json` exists, parses | file present |
| 2 | `summary.json.ran` contains `"relic"` | exact |
| 3 | `relic.json.status == "ok"` | exact |
| 4 | `relic.json.omega_h2` finite, in `[0.05, 0.40]` | range; canonical 0.163 lives inside, ±2.5× tol |
| 5 | **A only:** `omega_h2 == 0.163 ± 0.005` | regression-strict |
| 6 | `summary.{pdf,png}` exist, > 1 KB | size |
| 7 | `singlet_doublet_spec.yaml` exists; `validate_spec.py` exits 0 | exit code |
| 8 | Log contains `mg5_aMC --mode=maddm` (plugin path used, not bare MG5) | grep |
| 9 | Log does NOT contain `SAxDynkin`/`SAxCasimir` past `spheno-build` (analytic should bypass) | grep -v |
| 10 | Wallclock < 90 min | hard timeout |

Variant B may fail items 4/5 and still be informative — what matters is
that failure is *flagged*, not silent. So B's "pass" softens to: items
1, 2, 6, 7, 10 PLUS either (a) 3, 4, 8, 9 also pass (rename handled) OR
(b) `issues.jsonl` has a `severity: high` entry pinpointing the rename
clash before MadDM.

## 5. Failure taxonomy (by likelihood)

1. **MadDM `PLUGIN/` backup-dir crash** (very likely — scope notes
   non-idempotent cleanup). Evidence: `PLUGIN.maddm.broken-backup-...`
   traceback in `console.log`.
2. **`spheno_bin` config points to nonexistent binary** (medium — scope
   Open Q4). Evidence: `FileNotFoundError` at `spheno-build` phase.
3. **Wolfram license-server contact required** (medium — offline-night
   risk). Evidence: `wolfram` invocation hangs >60s.
4. **`/lagrangian-builder` YAML diverges from canonical reference**
   (medium — interview is "still proving itself out" per SKILL §4a).
   Evidence: diff vs `_archive/singlet_doublet.yaml`.
5. **MG5 `import model` resolves to wrong stub** (low — fixed in
   mg5-model-import-gotchas §1). Evidence: mass-spectrum mismatch.
6. **Param-card overlay race / wrong path** (low for SD; primarily a
   2HDM+a gotcha). Evidence: `Cards/param_card.dat` mtime predates
   `SPheno.spc`.
7. **`check_overlaps` plot assertion** (low). Evidence:
   `AssertionError: Overlaps detected`.
8. **ModelSpec schema drift** (low — versioned). Evidence:
   `MODELSPEC_INVALID` blocker JSON.
9. **B-only: SARAH `MMChi` collision** (designed-in). Evidence: SARAH
   log `Symbol MMChi already defined`.

For each: log captures ts, phase, exit code, stdout tail (200 lines),
stderr tail, any blocker JSON the skill emitted.

## 6. Issue-logging format — JSON Lines (`issues.jsonl`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "ts", "severity", "phase", "symptom",
               "evidence_paths", "blocking", "variant"],
  "properties": {
    "id":             {"type": "string", "pattern": "^sd-[AB]-[0-9]{3}$"},
    "ts":             {"type": "string", "format": "date-time"},
    "severity":       {"enum": ["low", "medium", "high", "critical"]},
    "phase":          {"enum": ["preflight", "lagrangian-builder",
                                "sarah-build", "spheno-build", "madgraph",
                                "maddm", "plot", "summary", "harness"]},
    "symptom":        {"type": "string", "maxLength": 280},
    "evidence_paths": {"type": "array", "items": {"type": "string"}},
    "log_excerpt":    {"type": "string", "maxLength": 4000},
    "hypothesis":     {"type": "string", "maxLength": 500},
    "blocking":       {"type": "boolean"},
    "variant":        {"enum": ["A", "B"]},
    "expected_fix_scope": {"enum": ["skill-prose", "tool-driver",
                                     "config", "external-tool", "unknown"]}
  }
}
```

`severity: critical` reserved for items that prevented `summary.json`.
`blocking: true` = run halted; `false` = logged and continued.
`expected_fix_scope` lets the fix agent route without re-reading transcripts.

## 7. Fix-loop authorization — observe + log only

Strictly observe. The playtest agent does **not** edit repo code or
`config.json`, even in its worktree. Reasons:

- Shift-manager's fix-loop agent is the designated mutator; two writers
  race.
- Variant B is *designed* to fail; in-line fixing destroys signal about
  whether `/lagrangian-builder` handles renames.
- A harness wrapper under `.playtest/sd-X/` is not a repo edit.

Exception: a known-fixed issue that recurs because cleanup is
non-idempotent (e.g., MadDM PLUGIN backup) may be cleaned with the
documented one-shot
(`mv $MG5_PATH/PLUGIN/maddm.broken-backup-* /tmp/`) and logged as
`expected_fix_scope: tool-driver, blocking: false`. The recurrence is
the issue.

## 8. Parallelism — yes, with isolation

A and B run concurrently. Shared-state risks to neutralise:

- **`$STATE_ROOT/models/singlet_doublet/`** — SARAH UFO + SPheno cache.
  Each variant exports `STATE_ROOT=<worktree>/.playtest/sd-X/state`
  before launching. Cold rebuild ~5–8 min × 2; acceptable.
- **`$MG5_PATH/PLUGIN/`** — single shared MG5. Cleanup is global.
  Serialise the *first* MadDM launch with a flock on
  `$MG5_PATH/.playtest.lock`; subsequent launches per variant are fine.
- **`/Users/yianni/SARAH/`** — single shared install. SARAH writes
  `Output/<modelname>/`. Variants use distinct model names
  (`SingletDoublet_A`, `SingletDoublet_B`) by patching the YAML's
  `model_name` at harness time, not in the practitioner script.
- **Wolfram license seat** — if single-seat, SARAH calls serialise
  naturally; log it but don't fail.

## 9. Artifact contract (frozen — synthesizer relies on these paths)

```
.playtest/sd-X/
├── run.log                       # full-fidelity, ts-prefixed
├── console.log                   # raw stdout+stderr from drive.py
├── issues.jsonl                  # §6 schema, append-only
├── timing.json                   # {phase: wallclock_seconds}
├── env.json                      # config.json snapshot, tool versions, $STATE_ROOT
├── practitioner_script.used.md   # exact bytes played back
├── demo_output/singlet-doublet/  # singlet_doublet_spec.yaml, relic.json,
│                                 #   summary.json, summary.{pdf,png}, maddm_run/
└── result.json                   # {variant, passed: bool, criteria: {1: true, ...}}
```

`result.json` + `issues.jsonl` together are sufficient for the
synthesizer to plan the fix-loop without grepping logs.

## 10. Time budget

Cold both times (isolated `$STATE_ROOT`). Per variant:

- preflight + interview replay: 5–10 min
- `/sarah-build` (Wolfram cold): 8–12 min
- `/spheno-build` analytic: 1–2 min (Fortran path skipped)
- `/madgraph` UFO import: 2–5 min
- `/maddm` two-phase relic: 8–15 min
- plot + summary: < 1 min
- **per variant: 25–45 min**

Both in parallel: **≈ 45 min** if Wolfram allows; ≈ 75 min if it
serialises. Hard ceiling 90 min/variant. A repeat A run costs ~30 min
for flakiness signal — only worth it if A passes first try and budget
remains; otherwise route budget to synthesizer.

---

## Confidence and unknowns

**Verified this session:**
- scope.md success criteria, status, known issues
- `practitioner_script.md` Q1–Q4 deltas
- `singlet-doublet/SKILL.md` Step 4a–4f contracts
- devlog 2026-04-22: six gotchas, analytic-bypass recipe path,
  `Ω h² = 0.163` baseline at the `(150, 500, 1, 0)` benchmark
- existence of `demo_output/singlet-doublet/retry_analytic/drive.py`

**Guessing:**
- `drive.py` accepts (or can be cheaply wrapped to accept) the flags
  `--constraints`, `--practitioner`, `--out_dir`, `--log`, `--issues`.
  Did not read its contents.
- `STATE_ROOT` is honoured by `/sarah-build` and `/spheno-build`
  (assumed from SKILL §File map; not confirmed in code).
- Wolfram is multi-seat locally. If it phones home for licence checks,
  the offline-night risk in scope Open Q4 bites — playtest agent
  should verify with a 5-second `wolfram -version` smoke first.
- `validate_spec.py` lives at a stable path on `PYTHONPATH` (SKILL §4a
  names it but no path).
- `_archive/singlet_doublet.yaml` is the right diff target for B's YAML;
  did not open it.
- The `±0.005` regression tolerance is from one prior run, not a
  distribution. Relic is deterministic given a fixed param card so the
  number should be reproducible; if MadDM has hidden stochasticity,
  loosen to `±0.02`.
