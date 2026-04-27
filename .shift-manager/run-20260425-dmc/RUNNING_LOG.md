# Manager Running Log — run-20260425-dmc

Repo HEAD at start: `179ed37`
Remote: none (local-only, per user constraint)

## 2026-04-25 — Run kickoff

- User invoked /shift-manager for /dark-matter-constraints work.
- Workstream order locked: WS-1 → WS-4 → (WS-2 ∥ WS-3).
- Brief written: `briefs/ROUTING_LENS.md` (load-bearing for all subagents).
- Convention: each subagent writes its full output to disk; manager only carries summaries.
- Iteration policy (impl): 3 sonnet-opus cycles, then opus-opus until done.

## 2026-04-25 — Phase 2: Dark SU(3) live playtest

- Scaffolding (WS-1..WS-4) all merged to main. Bell-ring 4/4 pass, 65 router tests green.
- User directive: "running playtests for dark SU(3) to catch anything still not working there. I'm not sure if we've run any of the tools for it yet, the playtest will tell us. Have an opus subagent try to playtest dark SU(3) in a worktree. If it runs into issues, have it try to get past them but log what it does. Skeptical opus reviews. Manager-only role. Fully autonomous, AFK."
- Plan: opus playtester runs in worktree; opus skeptic reviews; iterate until either (a) playtest converges with verdict, or (b) skeptic accepts the gap log as the deliverable when blockers are environmental.
- Target: Profumo Fig. 8 Dark SU(3) vector-resonance benchmark (m_χ=100, m_med≈199, single point first; expand only if it works).
- Output dir: `.shift-manager/run-20260425-dmc/playtest/` for both agents' reports.
- Cycle-1 result: partial/blocked. SARAH-emitted Dark SU(3) UFO unimportable to MG5 (color-tensor placeholders). micrOMEGAs and DRAKE not installed at all. MadDM chain validated on Singlet-Doublet cross-check. Two `check_prereqs.py` bugs filed.

## 2026-04-25 — Phase 3: Install-stack agents

- User pivot: "rather than continuing on with this, can you actually spin up some agents to check all of the required packages (by reading the workflow skills stemming from /demo) and have it try installing them"
- Reasoning: cycle-1 revealed env-blocked state; no point reviewing a playtest of an uninstalled stack. Get the tools real first.
- Plan:
  1. Scout opus reads `plugins/hep-ph-demo/skills/{demo,install,_shared}/` and any sibling skills they route to. Produces `MANIFEST.md` listing every required package with status (installed / missing / partially-installed), declared install procedure, and dependency graph.
  2. Once manifest lands, fan out installer opus agents per independent track in parallel.
- Output dir: `.shift-manager/run-20260425-dmc/install/`

### Phase 3 closeout

| Tool | Status | Path / version |
|---|---|---|
| DDCalc | INSTALLED (cosmetic bug) | `~/.local/share/hep-ph-agents/tools/DDCalc` v2.2.0 |
| LoopTools | INSTALLED (smoke-parser bug, output verified) | `~/LoopTools/LoopTools-2.16` v2.16 |
| FeynArts | INSTALLED (path bug, mv-workaround) | `~/Library/WolframEngine/Applications/FeynArts-3.11` v3.11 |
| micrOMEGAs | FAILED (known arm64 CalcHEP `getFlags` bug, lines 242–244 of skill) | partial tree at `~/micrOMEGAs/micromegas_6.1.15/` (150 MB) |
| DRAKE | MANUAL_DOWNLOAD_REQUIRED (Anubis gate) | not installed |
| FormCalc | DEFERRED (~3 GB disk + Package-X dead) | not attempted |
| Package-X | DEFERRED (upstream `UPSTREAM_UNREACHABLE_2026_04`) | not attempted |
| FeynCalc / 2HDMC / FeynRules / HiggsTools / pythia | DEFERRED (no install skill or out-of-scope) | n/a |

Disk: 1.5 GiB → 6.6 GiB free (cleanup + 0.5 GiB net install). Target was 12 GiB; sandbox + deferred user actions kept us short of the bigger reclaimables.

Skill-script bugs filed for upstream fix:
- DDCalc MD-D1 — `_smoke_test.sh` log line pollutes `DETECTED_VERSION`, writes multi-line `ddcalc_version` to config (cosmetic).
- LoopTools — `probe_looptools.sh` heredoc/pipe stdin collision in full-smoke parser.
- FeynArts — `install_feynarts.sh:46` newline-collapse → installs to `WolframEngineNull/`.
- FeynArts — three scripts have `SCRIPT_DIR` clobber when sourcing `detect_wolfram.sh`.
- micrOMEGAs — known arm64 CalcHEP `getFlags` bug; needs vendored patch under `patches/`.

Workaround sentinels left in tree (delete once skills patched):
- `plugins/shared/install-helpers/wolfram/_blocker.sh` (symlink)
- `plugins/shared/install-helpers/wolfram/smoke_test_feynarts.sh` (symlink)

User action items:
1. Free additional disk if FormCalc is wanted (≥ 3 GiB; reclaimables: vm_bundles 7 GB after quitting Claude, CoreSimulator 7 GB, DVTDownloads 2 GB).
2. Clear DRAKE Anubis gate manually: `https://drake.hepforge.org/` → save zipball → `/drake-install use-path <dir>`.
3. Provide a Package-X 2.1.1 tarball offline (upstream dead) and set `HEPPH_PACKAGE_X_SKIP_URL_CHECK=1`.
4. Decide on micrOMEGAs path forward: vendor a CalcHEP arm64 patch, or formally mark micrOMEGAs cross-check `SKIPPED_PLATFORM_BLOCKED` in `/dark-matter-constraints`.

