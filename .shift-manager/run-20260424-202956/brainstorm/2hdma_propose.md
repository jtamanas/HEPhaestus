# 2HDM+a Playtest — Proposer

Author: brainstorm-proposer
Workstream: 2hdm-a (autonomous overnight playtest)
Sources read: `scoping/scope.md`, `plugins/hep-ph-demo/skills/2hdm-a/{SKILL.md,practitioner_script.md,scripts/patch_paramcard.py}`, `plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/`, devlog commit 4dfcf4c, pointer to `demo_output/2hdm-a/fix_loop/POST_MORTEM.md`.

---

## 1. Test design — hand-crafted only, do not chase the renderer

**Decision: validate the hand-crafted (fixture) path only. Hard-skip the renderer path for this run.**

Rationale: SKILL.md was already rewritten (commits leading to 4dfcf4c) to make the fixture path the *officially supported* relic-density route. Step 4a copies `plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model/` → `$SARAH_ROOT/Models/TwoHdmAfix/`. The renderer is documented as "loop B / pending" inside SKILL.md itself (lines 12–19). The user goal — "make sure they all work" — is satisfied if the *currently advertised* path produces a finite Ωh². Spending overnight cycles re-deriving the seven-site renderer patch is a different workstream (a fix loop) and would crowd out the simpler validation we actually need: that the fixture deploy + param-card patcher + MadDM phases pipeline still runs after recent refactors.

If the playtest agent has spare time after a green run, it MAY *attempt* `/sarah-build --model TwoHdmAfix` (no `--skip-render`) to capture the current renderer failure mode for the synthesizer — but only as a diagnostic data point, not as a success criterion.

## 2. Practitioner persona — augment Q2, leave Q1/Q3/Q4 alone

`practitioner_script.md` for 2hdm-a is well-written but Q2 has a known land-mine encoded as "scalars 1/2/3, fermions 1/2." A cold reader of the spec answers `a` (CP-odd singlet) literally — but SARAH collides `a` with the photon, so the fixture renames it `a0s` (see SKILL.md L97). Q2 should be augmented with a parenthetical: *"(if the renderer warns about reserved name `A`, alias to `a0` / `a0s`)"* — only as a comment for the playtest agent. **Do not modify the script file in this run** (mutation = scope creep). Instead, the playtest agent's prompt explicitly notes "if `/lagrangian-builder` Q3 surfaces a name collision on `a`, accept the renamer and continue."

Q3/Q4 are deltas; they passed in the iter-6→8 loops. Leave alone.

## 3. Invocation — hard-fail if fixture is missing, hard-fail if Wolfram absent

```bash
# Phase 0: preflight
python3 -c "import json,sys; c=json.load(open('config.json')); \
    [sys.exit(f'missing {k}') for k in ('sarah_path','madgraph_path','wolfram_engine_path') if not c.get(k)]"

# Phase 1: fixture deploy (idempotent diff-then-copy from SKILL.md L228-239)
bash <<'EOF'
SARAH_ROOT=$(python3 -c "import json; print(json.load(open('config.json'))['sarah_path'])")
DEST="$SARAH_ROOT/Models/TwoHdmAfix"; SRC="plugins/hep-ph-demo/skills/2hdm-a/fixtures/sarah_model"
if [ ! -d "$DEST" ] || ! diff -q "$SRC/TwoHdmAfix.m" "$DEST/TwoHdmAfix.m"; then
  mkdir -p "$DEST" && cp "$SRC"/*.m "$DEST/" && echo DEPLOYED
else echo UP_TO_DATE; fi
EOF

# Phase 2: SARAH build (skip-render path)
# Drive /sarah-build with --model TwoHdmAfix --skip-render
# OR fall back to direct math invocation if the skill rejects --skip-render:
#   math -run '<<SARAH`; Start["TwoHdmAfix"]; MakeUFO[]; Quit[]'

# Phase 3: vertex sanity check (canonical probe per devlog)
test "$(grep -c '"chi"' "$SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/particles.py")" -ge 1

# Phase 4: MG5 setup (writes Cards/), patch_paramcard.py, MG5 launch.
# Exact sequence from SKILL.md L286-326 — no improvisation.
```

**Degradation rule:** if Phase 1 or 2 hard-fails, **STOP**. Do not synthesize a fallback. Log `BLOCKER` and exit. The user said "make sure they all work" — partial credit is worse than a clear NO. The playtest is degraded *only* in the loose sense that SKILL.md itself bypasses `/lagrangian-builder` for this model; that's the contract, not a degradation.

## 4. Success criteria — quantitative

Primary signal (must hit all):

| Metric | Target | Tolerance | Source |
|---|---|---|---|
| `Ωh²` finite (not `-1.0`, not NaN) | finite float | strict | `MadDM_results.txt` |
| `Ωh²` near iter-8 reference | `10.15` | ±10% (i.e. 9.1–11.2) | `relic.json` |
| Dominant channel | `chichibar_bbx` | ≥40% | sigmav_channels |
| `relic.json` schema | matches SKILL.md L373-385 | strict | jsonschema validate |
| `summary.json` schema | matches `_shared/summary.schema.json` | strict | jsonschema validate |
| Param-card `PHASES[1]` | `1.000000e+00` | strict | grep on patched card |
| Param-card YUKAWAU/D/E split | three blocks present | strict | grep |
| Wall time | 3–8 min for off-resonance | soft | timing log |

The 10% band on Ωh² is generous; iter-8 should be reproducible bit-for-bit, but MadDM's Romberg can drift in the third decimal. Anything outside ±10% is a regression.

Required artifacts in `demo_output/2hdm-a/`:
- `relic.json` (with `relic_approx: false`, `model_source: "hand_crafted_sarah_model"`)
- `summary.json`
- `summary.{pdf,png}` (channel breakdown bar chart)
- `maddm_run/Cards/param_card.dat` (post-patch)
- `maddm_run/output/run_01/MadDM_results.txt`

Non-empty `headline` in summary.json is the user-visible success token.

## 5. Failure taxonomy — ranked by prior probability

Drawn from POST_MORTEM history (iters 0–8). High → low:

1. **Fixture-not-deployed / VERTICES_ZERO** (~30%). Symptom: `grep -c "chi" vertices.py` returns 0. Evidence: `$SARAH_ROOT/Output/TwoHdmAfix/EWSB/UFO/` listing, SARAH log tail. Most-likely cause: idempotent copy missed, or SARAH error before `MakeUFO[]`.
2. **Param-card patcher not invoked / PHASES[1]=0** (~20%). Symptom: `Omegah2 = -1.0` sentinel, all-NaN channels. Evidence: `param_card.dat` `PHASES` block, presence of patcher invocation in run log. **This is the historical #1 silent failure.**
3. **MG5 plugin loader / mode flag** (~15%). Symptom: `InvalidCmd: generate relic_density`. Evidence: MG5 stdout, confirm `--mode=maddm` flag was used.
4. **YUKAWA collision** (~10%). Symptom: `mdl_ryu211 is not defined` during MadDM EFT re-import. Evidence: parameters.m grep — fixture should already split into YUKAWAU/D/E. If this fires, the deployed fixture is *stale*, not current.
5. **Wolfram license-server timeout** (~10%, environment-dependent). Symptom: SARAH hangs at `<<SARAH``. Evidence: `sample <math-pid>`. Mitigation: run is offline, so this is a hard fail.
6. **On-resonance hang** (~5%). Should be impossible at the prescribed off-resonance benchmark (Ma=400, Mχ=100), but if config drift moved Ma toward 200 GeV, Romberg hangs >20 min. Evidence: timing log, `Ma` in patched param_card.
7. **Renderer-attempted-anyway** (~5%). The playtest agent ignores Step 4a and tries `/sarah-build` from YAML. Hard guardrail: prompt must include "USE FIXTURE PATH; do not invoke /lagrangian-builder for 2hdm-a."
8. **MadDM finds no DM candidate** (~3%). Symptom: `define darkmatter chi` errors. Evidence: UFO `particles.py` — confirm `chi` PDG 9989932, antiname `chibar`, `self_conj=False`.
9. **Plot overlap assertion** (~2%). Symptom: `check_overlaps` returns issues. Non-blocking for relic correctness but blocks `summary.{pdf,png}`.

For each: capture full stdout/stderr, the offending file, and a 20-line context window in `demo_output/2hdm-a/playtest_log/`.

## 6. Issue JSON schema

Predicted to match the sibling SD workstream:

```json
{
  "issue_id": "2hdma-NNN",
  "severity": "blocker | major | minor | nit",
  "phase": "preflight | fixture_deploy | sarah_build | mg5_setup | param_patch | mg5_launch | parse | plot | summary",
  "symptom": "one-line human description",
  "expected": "what should have happened",
  "observed": "what actually happened (verbatim error if available)",
  "evidence_path": ["abs path 1", "abs path 2"],
  "hypothesis": "best guess at root cause",
  "blocking": true,
  "auto_repro_command": "shell snippet to reproduce in <60s, or null",
  "fix_owner_hint": "renderer | spec | skill_prose | tool_install | unknown",
  "captured_at": "ISO-8601",
  "playtest_iteration": 0
}
```

Issues land in `demo_output/2hdm-a/playtest_log/issues.jsonl` (one per line, append-only). Synthesizer/fix agent reads this. `fix_owner_hint` is the routing hint to the next agent.

## 7. Fix-loop authorization — strictly observe + log

**No fix-loop authorization for the 2hdm-a workstream during this run.** Justification: the user said "make sure they all work" + "issues resolved", but the *advertised* path (fixture-based) already works as of iter-8. The renderer-backport is an explicitly separate loop. If the playtest agent starts editing `plugins/model-building/skills/sarah-build/scripts/sections/` overnight, it risks breaking singlet-doublet (which uses the same renderer). Asymmetric downside.

If a *new* fixture-path regression surfaces (e.g. someone reorganized `_shared/`), the playtest agent MAY fix the surface symptom in `plugins/hep-ph-demo/skills/2hdm-a/` only — not in shared infra. Gate: if `git diff --name-only` after fix touches anything outside `plugins/hep-ph-demo/skills/2hdm-a/` or `demo_output/2hdm-a/`, abort the fix and log it as a `blocker` issue instead.

## 8. Parallelism risk — moderate, manageable

Shared state vs. singlet-doublet and dark-su3:

- `$SARAH_ROOT/Models/TwoHdmAfix/` — **2hdm-a only** (singlet-doublet uses different model dir; dark-su3 is analytic, doesn't touch SARAH).
- `$SARAH_ROOT/Output/TwoHdmAfix/` — **2hdm-a only**. SARAH `MakeUFO[]` writes here. **Risk if a second 2hdm-a process spawns** (it won't, only one workstream owns this model).
- `demo_output/2hdm-a/` — **2hdm-a only**.
- `config.json` at repo root — **read-shared, must not be modified**. Playtest agent prompt: "config.json is read-only."
- Wolfram kernel — **Mathematica license is per-machine, often single-seat**. If SD and 2hdm-a both hit `<<SARAH`` simultaneously, one will block. Recommendation: synthesizer should serialize SARAH-using workstreams (SD and 2hdm-a) and run dark-su3 (analytic, no SARAH) in parallel to either.
- MG5 install dir — read-shared. Per-run output dirs are isolated (`demo_output/<model>/maddm_run/`).

**Action for synthesizer:** request that SD and 2hdm-a's SARAH steps not overlap. The SARAH+UFO emit is ~2 min; serialize that, parallelize everything else.

## 9. Artifact contract

Output tree (all paths absolute or repo-relative as listed):

```
demo_output/2hdm-a/
├── relic.json                          # SKILL.md L373 schema
├── summary.json                        # _shared/summary.schema.json
├── summary.pdf
├── summary.png
├── maddm_run/
│   ├── setup.mg5
│   ├── launch.mg5
│   ├── Cards/param_card.dat            # post-patcher
│   └── output/run_01/MadDM_results.txt
└── playtest_log/
    ├── run.log                         # full transcript, tee'd
    ├── timing.json                     # phase: seconds
    ├── issues.jsonl                    # §6 schema
    ├── env.json                        # config.json snapshot, tool versions
    └── verdict.md                      # PASS|FAIL + 5-line summary
```

`verdict.md` is the human-readable top-line. First line: `VERDICT: PASS` or `VERDICT: FAIL`. Synthesizer agent reads this first.

## 10. Time budget

| Phase | Est. wall (cold) | Est. wall (cached) |
|---|---|---|
| Preflight + fixture deploy | 5 s | 2 s |
| SARAH `MakeUFO[]` | 90–180 s | same (no caching) |
| MG5 `output` (Phase 1) | 60–120 s | 60–120 s |
| Param-card patch | 1 s | 1 s |
| MG5 `launch` + MadDM relic | 180–300 s | 180–300 s |
| Parse + plot + summary | 10 s | 10 s |
| **Total off-resonance** | **6–11 min** | **6–11 min** |

Budget allocation: **15 min hard cap** for one full pass. With one retry on transient failure: **30 min**. Compared to SKILL.md's stated "1–2 hr cold" estimate, we're well inside — that estimate includes user-think-time at the interview, which the practitioner script collapses to seconds.

If wall exceeds 20 min on a single MadDM `launch`, suspect on-resonance hang and abort — `kill -ABRT` + `sample` for evidence per devlog technique.

---

## Confidence and unknowns

**High confidence (≥80%)**: fixture path will produce finite Ωh² near 10.15 if the environment is unchanged since iter-8 (22 Apr). The recipe is fully specified in SKILL.md and was reproduced once.

**Medium confidence (50–70%)**: the param-card patcher invocation is correctly wired into the `/maddm` skill (or driven inline per SKILL.md L312-320). The post-mortem says the patcher was a 60-line debug script in `demo_output/.../fix_loop/iter_8_patch_paramcard.py`; SKILL.md now points at `plugins/hep-ph-demo/skills/2hdm-a/scripts/patch_paramcard.py` which is committed. I did not verify content equivalence — I only confirmed it exists. **Skeptic should challenge whether this script reproduces the iter-8 behavior exactly.**

**Unknowns:**

- Whether `/sarah-build --skip-render` is actually implemented as a flag, or whether SKILL.md L245 is aspirational. If aspirational, fall back to direct `math -run` invocation.
- Whether `_shared/summary.schema.json` exists and validates the documented `summary.json` shape — not checked.
- Whether parallel SARAH invocations actually race on the Wolfram kernel, or whether SARAH 4.15.3 spawns its own process per `Start[...]` call. Would prefer empirical confirmation before greenlighting parallel runs.
- The renderer's *current* failure mode: scope doc says "7 patch sites" but doesn't enumerate; iter_6_notes.md is referenced but I did not open it. If skeptic disagrees with §1, this is the file to consult.

**One opinion worth flagging:** the user said "make sure all 3 work" and "issues resolved." These are in tension for 2hdm-a because the *honest* status is "advertised path works; renderer is debt." I'm choosing to report this honestly rather than chase the renderer overnight. If the synthesizer prefers the renderer be attempted, it should explicitly authorize a separate iter-9 fix loop with its own scope.

Confidence and unknowns.
