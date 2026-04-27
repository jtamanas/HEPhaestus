# Phase 2 — Plan Review (Opus reviewer)

## Blockers
1. **`config_merge` atomicity bug, promoted as-is.** `_common.sh:136-140` writes tmpfile + `mv`; no fsync of fd or containing dir. W0 promotes this to `plugins/shared/install-helpers/_common.sh` and creates a Python mirror `config_helpers.py`. Fix in both: `fsync(fd); rename; fsync(parent_dir)`. 5 lines Python, 3 lines bash.
2. **W4 non-deterministic acceptance (line 503):** "at least one row should naturally mark status=recoverable" — depends on physics accident. Replace: fixture-driven recoverable test + deterministic 45-row assertion.
3. **W3 `AppendTo[$Path]` has extra `/..`** (line 356-364). `sarah_path` already points to dir with `SARAH.m`; extra `/..` lands in wrong dir. Drop it. Cross-check `install_sarah.sh:110`.

## Major
4. **Plugin.json count mismatch:** line 121 says `length == 4`, parenthetical admits 6. Gate must be `length == 6`; W5 rewrites lagrangian-builder in place.
5. **W3 item 4 placeholder tokens** lack any concrete example; implementer needs one worked fermion_block (2-fermion example) to anchor Mathematica syntax.
6. **W2 version-mismatch policy regression.** Phase 1 §8 decided "install fresh alongside"; drafter walked to "warn and continue." Silent drift detonates in W4. Revert to Phase 1 rule.
7. **W5 acceptance "no script >80 lines"** is style, not gate. Remove or move to style conventions.
8. **W0 `install.sh detect-all` regression gate** needs pre-refactor baseline captured on clean main; drafter did not spell out the capture step.
9. **Dispatch merge order over-serialized.** W3/W4/W6 do not need to merge in strict order after W3. Rule: W3 first (unlocks integration); W6 and W4 land in either order.
10. **Re-dispatch step for W4 post-W3** mentioned but not broken into numbered steps. Manager needs: rebase worktree, remove old fixture tarball, re-run W3 on dark_su3, retar fixture, re-run integration.
11. **No single-writer discipline on main.** Add: manager serializes ff-merges; W1/W2 merge sequentially even if both pass concurrently.
12. **Concurrent cache-key writes in wave B.** W3 and W4 both touch `models/<name>/`. Mandate `HEPPH_STATE_ROOT` env override for per-worktree state during integration tests.
13. **Global config.json leak across worktrees.** `~/.config/hep-ph-agents/config.json` is user-global. Mandate `XDG_CONFIG_HOME=/tmp/hepph-$worktree-$$` for all test runs; document in SHARED.md.
14. **Fixture size cap too optimistic.** 2 MB compressed may hold for dark_su3 only; singlet_doublet/2hdm may overflow. Pick a policy now: (a) accept larger fixture, (b) git-LFS, or (c) out-of-repo CI-fetched tarball. Do not defer.
15. **Env-var `HEPPH_SARAH_VERSION` advertised but not honored.** Either implement `SARAH_VERSION=${HEPPH_SARAH_VERSION:-4.15.3}` in `install_sarah.sh` or remove from SHARED.md.
16. **`user_instruction` shared semantic** across status JSON and fatal blockers — document as one consistent field.
17. **Fixture untar not specified.** W4 tests must `tarfile.open(fixture).extractall(tmp_path)` before each test.

## Minor
18. **W1 `activate` grep pattern is over-broad.** Probe for exact activation prompt first; then write grep.
19. **W4 placeholder fixture pre-W3** lacks composition spec — cite an existing SARAH-produced tree as reference.
20. **W1 `found` vs `configured` states** — collapse or document.
21. **W3 `≤5s` rerun gate** — tie to hardware pin or reframe as "skips template+wolframscript; asserted by log absence."
22. **Python 3 version pin missing.** Assert `python3 >= 3.10`.
23. **Day-1 probe sequencing** — Wolfram activation probe must precede grep implementation, not follow.
24. **SARAH UFO ↔ MG5 probe lacks go/no-go gate.**
25. **blocker.schema.json basis** — reference PR-D commit `f72e19e` diff for canonical shape; mark provisional otherwise.

## Judgment-call votes
1. `config_helpers.py` Python mirror — **Python mirror**; shell-out coupling bloats test prereqs.
2. `_common.sh` shim in hep-ph-demo — **shim**; zero-cost preservation.
3. W2 `use-path` semantics — **accept either, detect binary vs src tree**; record both keys.
4. W2 version-mismatch — **install fresh alongside** (Phase 1 rule).
5. `reference_only` shape — **mirror commit `f72e19e`**; provisional otherwise with `# TODO(PR-D)`.
6. W6 cross-plugin coupling — **inline 15-line config read**; no imports across plugins.
7. Golden-file tests — **keep goldens, add one-command regeneration script**.

## Top 5 for synthesizer
1. Fix `config_merge` atomicity in both bash + Python now, in W0.
2. Eliminate non-deterministic acceptance; reframe W3/W4 wall-clock thresholds.
3. Manager owns merges, serializes, numbered re-dispatch checklist; mandate `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME` overrides.
4. Fix W3's `AppendTo[$Path]` bug before W3 agent sees it.
5. Revert W2 version-mismatch to Phase 1's "install fresh alongside."

## Spec coverage verified complete
All required `use-path`, SPheno invocation signature, SLHA blocks enumerated, three-state blocker respected, no `.contracts/` subdir, activation_required as status (not blocker).
