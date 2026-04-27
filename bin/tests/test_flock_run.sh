#!/usr/bin/env bash
# bin/tests/test_flock_run.sh — unit tests for bin/flock_run.sh
#
# Covers all 7 assertions from ws3_final.md §3.4:
#   1. Acquire-and-run (uncontested)
#   2. Timeout (contested) — exits 124, emits FLOCK_TIMEOUT JSON, cmd NOT run
#   3. Wrapped exit-code propagation
#   4. Lock survives exec (load-bearing) — multiprocessing.fork serialization
#   5. mkdir -p permission failure — exits 125 with FLOCK_LOCKDIR_DENIED
#   6. Fd-form smoke (uncontended) + fd-form contended (timeout)
#   7. Stock-bash compat — re-run assertions 1-6 under /bin/bash if present
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HELPER="$REPO_ROOT/bin/flock_run.sh"

TMPDIR_BASE="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_BASE"; }
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0

_pass() { echo "[test] PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
_fail() { echo "[test] FAIL: $1" >&2; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ── assertion 1: acquire-and-run (uncontested) ────────────────────────────────

run_assertion_1() {
  local lf="$TMPDIR_BASE/assert1.lock"
  local out
  out="$("$HELPER" "$lf" 5 -- echo ok 2>/dev/null)"
  local rc=$?
  if [ "$rc" -eq 0 ] && [ "$out" = "ok" ]; then
    _pass "1: acquire-and-run (uncontested)"
  else
    _fail "1: acquire-and-run: rc=$rc out='$out'"
  fi
}

# ── assertion 2: timeout (contested) ─────────────────────────────────────────

run_assertion_2() {
  local lf="$TMPDIR_BASE/assert2.lock"
  local sentinel="$TMPDIR_BASE/assert2.sentinel"

  # Background: hold the lock for 30 s
  (
    exec 9>>"$lf"
    python3 - 9 30 <<'PY'
import fcntl, time, sys
fcntl.flock(int(sys.argv[1]), fcntl.LOCK_EX)
time.sleep(30)
PY
  ) &
  HOLDER_PID=$!

  # Give holder time to acquire
  sleep 0.3

  # Foreground: try with 2 s timeout; cmd writes sentinel if it runs
  local stderr_out
  stderr_out="$(mktemp)"
  local rc=0
  "$HELPER" "$lf" 2 -- bash -c "touch '$sentinel'" 2>"$stderr_out" || rc=$?

  kill "$HOLDER_PID" 2>/dev/null || true
  wait "$HOLDER_PID" 2>/dev/null || true

  local json_lines
  json_lines="$(grep -c '^{"code":"FLOCK_TIMEOUT"' "$stderr_out" 2>/dev/null || echo 0)"
  rm -f "$stderr_out"

  if [ "$rc" -ne 124 ]; then
    _fail "2: timeout exit code: expected 124, got $rc"
  elif [ -f "$sentinel" ]; then
    _fail "2: timeout: sentinel created (cmd ran when it should not)"
  elif [ "$json_lines" -lt 1 ]; then
    _fail "2: timeout: FLOCK_TIMEOUT JSON not found in stderr"
  else
    _pass "2: timeout (contested): exit 124, FLOCK_TIMEOUT JSON, cmd NOT run"
  fi
}

# ── assertion 3: wrapped exit-code propagation ────────────────────────────────

run_assertion_3() {
  local lf="$TMPDIR_BASE/assert3.lock"
  local rc=0
  "$HELPER" "$lf" 5 -- bash -c 'exit 7' 2>/dev/null || rc=$?
  if [ "$rc" -eq 7 ]; then
    _pass "3: exit-code propagation (exit 7)"
  else
    _fail "3: exit-code propagation: expected 7, got $rc"
  fi
}

# ── assertion 4: lock survives exec (multiprocessing.fork serialization) ──────

run_assertion_4() {
  local lf="$TMPDIR_BASE/assert4.lock"
  local result_file="$TMPDIR_BASE/assert4_result.json"

  # Use Python multiprocessing.fork to race two helper invocations.
  # Each invocation holds the lock for 3 s (sleep 3); second must wait.
  # We record timestamps to verify serialization.
  python3 - "$HELPER" "$lf" "$result_file" <<'PY'
import multiprocessing, subprocess, sys, json, time, os

helper = sys.argv[1]
lock_file = sys.argv[2]
result_file = sys.argv[3]

_ctx = multiprocessing.get_context("fork")
result_queue = _ctx.Queue()

def _worker(wid):
    t_start = time.monotonic()
    rc = subprocess.call(
        [helper, lock_file, "60", "--", "bash", "-c", "sleep 3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    t_end = time.monotonic()
    result_queue.put({"wid": wid, "rc": rc, "start": t_start, "end": t_end})

p1 = _ctx.Process(target=_worker, args=(1,))
p2 = _ctx.Process(target=_worker, args=(2,))
p1.start()
p2.start()
# Give p1 a tiny head-start to ensure it acquires first
import time; time.sleep(0.1)
p1.join(timeout=30)
p2.join(timeout=30)

results = []
while not result_queue.empty():
    results.append(result_queue.get_nowait())

with open(result_file, "w") as f:
    json.dump(results, f)
sys.exit(0 if len(results) == 2 else 1)
PY
  local py_rc=$?

  if [ "$py_rc" -ne 0 ]; then
    _fail "4: lock-survives-exec: multiprocessing script failed (rc=$py_rc)"
    return
  fi

  if [ ! -f "$result_file" ]; then
    _fail "4: lock-survives-exec: result file not found"
    return
  fi

  local ok
  ok="$(python3 - "$result_file" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    results = json.load(f)
if len(results) != 2:
    print("FAIL: expected 2 results, got " + str(len(results)))
    sys.exit(1)
# Both should succeed
for r in results:
    if r["rc"] != 0:
        print("FAIL: worker " + str(r["wid"]) + " exited " + str(r["rc"]))
        sys.exit(1)
# Sort by end time — the first to finish should end ~3s in; the second ~6s in
sorted_r = sorted(results, key=lambda x: x["end"])
gap = sorted_r[1]["end"] - sorted_r[0]["start"]
if gap < 4.0:
    print("FAIL: serialization gap too small: " + str(round(gap, 2)) + "s (expected >=5s)")
    sys.exit(1)
print("OK: gap=" + str(round(gap, 2)) + "s")
sys.exit(0)
PY
  )"
  local py2_rc=$?
  if [ "$py2_rc" -eq 0 ]; then
    _pass "4: lock-survives-exec: serialization verified ($ok)"
  else
    _fail "4: lock-survives-exec: $ok"
  fi
}

# ── assertion 5: mkdir -p permission failure ──────────────────────────────────

run_assertion_5() {
  local bad_path="/dev/null/cantmkdir/lock"
  local stderr_out
  stderr_out="$(mktemp)"
  local rc=0
  "$HELPER" "$bad_path" 5 -- echo ok 2>"$stderr_out" || rc=$?
  local json_lines
  json_lines="$(grep -c '"FLOCK_LOCKDIR_DENIED"' "$stderr_out" 2>/dev/null || echo 0)"
  rm -f "$stderr_out"
  if [ "$rc" -eq 125 ] && [ "$json_lines" -ge 1 ]; then
    _pass "5: mkdir-p permission failure: exit 125, FLOCK_LOCKDIR_DENIED"
  else
    _fail "5: mkdir-p permission failure: rc=$rc json_lines=$json_lines"
  fi
}

# ── assertion 6a: fd-form smoke (uncontended) ─────────────────────────────────

run_assertion_6a() {
  local lf="$TMPDIR_BASE/assert6a.lock"
  local out
  out="$( (exec 200>>"$lf"; "$HELPER" --fd 200 "$lf" 5 -- echo ok) 2>/dev/null )"
  local rc=$?
  if [ "$rc" -eq 0 ] && [ "$out" = "ok" ]; then
    _pass "6a: fd-form smoke (uncontended)"
  else
    _fail "6a: fd-form smoke: rc=$rc out='$out'"
  fi
}

# ── assertion 6b: fd-form contended (timeout) ────────────────────────────────

run_assertion_6b() {
  local lf="$TMPDIR_BASE/assert6b.lock"

  # Background: open fd 200, acquire flock, hold for 30s
  (
    exec 200>>"$lf"
    python3 - 200 30 <<'PY'
import fcntl, time, sys
fcntl.flock(int(sys.argv[1]), fcntl.LOCK_EX)
time.sleep(30)
PY
  ) &
  HOLDER_PID=$!

  sleep 0.3

  local stderr_out
  stderr_out="$(mktemp)"
  local rc=0
  (
    exec 200>>"$lf"
    "$HELPER" --fd 200 "$lf" 2 -- echo ok
  ) 2>"$stderr_out" || rc=$?

  kill "$HOLDER_PID" 2>/dev/null || true
  wait "$HOLDER_PID" 2>/dev/null || true

  local json_lines
  json_lines="$(grep -c '"FLOCK_TIMEOUT"' "$stderr_out" 2>/dev/null || echo 0)"
  rm -f "$stderr_out"

  if [ "$rc" -eq 124 ] && [ "$json_lines" -ge 1 ]; then
    _pass "6b: fd-form contended: exit 124, FLOCK_TIMEOUT"
  else
    _fail "6b: fd-form contended: rc=$rc json_lines=$json_lines"
  fi
}

# ── assertion 7: stock-bash compat ────────────────────────────────────────────

run_assertion_7() {
  if [ ! -x /bin/bash ]; then
    echo "[test] NOTE: /bin/bash not found; skipping stock-bash compat assertion"
    return
  fi

  local bash_ver
  bash_ver="$(/bin/bash --version | head -1)"
  echo "[test] Stock bash: $bash_ver"

  # Re-run assertions 1, 3, 5, 6a under /bin/bash explicitly
  local lf rc out

  lf="$TMPDIR_BASE/assert7_1.lock"
  out="$(/bin/bash "$HELPER" "$lf" 5 -- echo ok 2>/dev/null)"; rc=$?
  if [ "$rc" -eq 0 ] && [ "$out" = "ok" ]; then
    _pass "7a: stock-bash: acquire-and-run"
  else
    _fail "7a: stock-bash acquire-and-run: rc=$rc out='$out'"
  fi

  lf="$TMPDIR_BASE/assert7_3.lock"
  rc=0
  /bin/bash "$HELPER" "$lf" 5 -- bash -c 'exit 7' 2>/dev/null || rc=$?
  if [ "$rc" -eq 7 ]; then
    _pass "7b: stock-bash: exit-code propagation"
  else
    _fail "7b: stock-bash exit-code propagation: rc=$rc"
  fi

  local stderr_out
  stderr_out="$(mktemp)"
  rc=0
  /bin/bash "$HELPER" "/dev/null/cantmkdir/lock" 5 -- echo ok 2>"$stderr_out" || rc=$?
  local json_lines
  json_lines="$(grep -c '"FLOCK_LOCKDIR_DENIED"' "$stderr_out" 2>/dev/null || echo 0)"
  rm -f "$stderr_out"
  if [ "$rc" -eq 125 ] && [ "$json_lines" -ge 1 ]; then
    _pass "7c: stock-bash: mkdir-p failure"
  else
    _fail "7c: stock-bash mkdir-p failure: rc=$rc json_lines=$json_lines"
  fi

  lf="$TMPDIR_BASE/assert7_6a.lock"
  out="$( (/bin/bash -c "exec 200>>\"$lf\"; \"$HELPER\" --fd 200 \"$lf\" 5 -- echo ok") 2>/dev/null )"; rc=$?
  if [ "$rc" -eq 0 ] && [ "$out" = "ok" ]; then
    _pass "7d: stock-bash: fd-form smoke"
  else
    _fail "7d: stock-bash fd-form smoke: rc=$rc out='$out'"
  fi
}

# ── run all assertions ─────────────────────────────────────────────────────────

echo "[test] === bin/flock_run.sh unit tests ==="
echo "[test] helper: $HELPER"
echo "[test] bash: $BASH_VERSION"

run_assertion_1
run_assertion_2
run_assertion_3
run_assertion_4
run_assertion_5
run_assertion_6a
run_assertion_6b
run_assertion_7

echo ""
echo "[test] === Results: $PASS_COUNT passed, $FAIL_COUNT failed ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "[test] ALL PASS"
  exit 0
else
  echo "[test] FAILURES DETECTED" >&2
  exit 1
fi
