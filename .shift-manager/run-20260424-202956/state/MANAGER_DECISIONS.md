# Manager Decisions Log

## 2026-04-24 ~22:50 — flock unavailability on macOS

**Finding**: `which flock` returns "not found" on this macOS host. All cross-workstream locking
strategies in plans (`.shift-manager/run-.../locks/sarah.lock`, `maddm.lock`, schema lock,
`dsu3_shared_lines.lock`, SARAH FIFO queue) were silently no-ops because the `flock(1)` binary
does not exist.

**Evidence**:
- Manager-side `which flock` ran 2026-04-24 22:51, output "flock not found".
- SD-A playtest sonnet logged `sd-A-004` independently.

**Risk during this run**:
- All four playtest sonnets ran concurrently against shared SARAH `Models/`, MG5 `PLUGIN/`,
  and `_shared/summary.schema.json`. With locks broken, contention could have caused
  silent corruption (interleaved writes to a shared model dir, partial schema reads).
- Empirically, all four workstreams produced coherent artifacts (Ωh² values within plan ranges
  where applicable, no truncated JSON observed). The variants that *needed* SARAH used distinct
  model names (Variant A: SingletDoublet; Variant B: SingletDoublet_B; 2HDM+a: TwoHdmAfix), so
  they did not collide on the SARAH `Models/` filesystem.
- 2HDM+a P3 schema patch landed before SD/Dark-SU(3) were reading it, so the schema-edit lock
  not working did not cause read-during-write corruption in practice.

**Decision**: ACCEPT the current run despite broken locks. No evidence of corruption.
- For overnight remainder: I will NOT inject a brew install or sw_vers for `flock` (out of scope;
  could break other workflows).
- The SD-A and SD-B issue logs already capture this; it will appear in the final run report
  as a "next-session improvement."

**Forward action**: Plans should be revised in a future run to use `python3 -c "import fcntl; ..."`
or a portable POSIX file-lock helper. Out of scope for this run.

## 2026-04-24 ~21:50 — Schema sentinel race

**Finding**: 2HDM+a P3 patched `_shared/summary.schema.json` but did not write the
`state/schema_v1_1.ready` sentinel. SD prep P3 polled, timed out (~63s, plan demanded 1800s
but sonnet truncated), G9 evaluated as WARN.

**Decision**: Manager wrote the sentinel post-hoc. SD G9 stays WARN per plan-sanctioned
warning rule. No re-evaluation needed.

## 2026-04-24 ~21:18 — `rm -rf` sandbox guard

**Finding**: Sandbox blocks `rm -rf` on home paths. Plans authored as if `rm -rf` were available.

**Decision**: All "clean stale" plan steps remap to `mv` to
`.shift-manager/run-20260424-202956/quarantine/`. Sonnet prompts updated. Worked uniformly
across all three workstreams' Phase 0.

## 2026-04-24 ~22:55 — API 529 overload retries

**Finding**: Anthropic API returned 529 (overloaded) on two opus-reviewer agents
(SD-A reviewer and Dark-SU(3) PT1 reviewer) within ~10 minutes of each other.

**Decision**: Re-dispatched both with shorter prompts. Workstream proceeds; no other rate-limit
mitigation applied. If a 3rd 529 hits, switch to sonnet reviewers as a fallback.

## 2026-04-24 ~23:35 — Fallback to sonnet reviewers triggered

**Finding**: 4th opus 529 in a row (SD fix R1 reviewer). 2HDM+a PT1 reviewer is on its 2nd retry.

**Decision**: SD fix R1 reviewer redispatched as sonnet (a32e5bbe5a7a937f0). 2HDM+a PT1
opus retry still in flight; if it fails, switch that one to sonnet as well. The sonnet review
trades depth for completion; flagged in run report as protocol deviation forced by API.
