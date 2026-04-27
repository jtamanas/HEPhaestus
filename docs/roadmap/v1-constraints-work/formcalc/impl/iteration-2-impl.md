# `/formcalc` + `/formcalc-install` — Iteration-2 Implementation Report

**Implementer:** Claude Sonnet 4.6 (iteration-2)
**Date:** 2026-04-19
**Branch:** `workstream-feyndiag-formcalc`
**Reviewer input:** iteration-1-review.md (Opus 4.7, verdict: NEEDS_FIXES)

---

## Commits added this iteration

```
56e0885 W12-fC: pin live FormCalc + FORM URLs with real SHA256
baf8078 W12-fC: route sidecar + build_key writes through Phase-0 atomic_write.sh
5d179aa W12-fC: iteration-1 report amendment — atomic_write.sh contract correction
74273a5 W12-fC: add iteration-1 opus reviewer report
```

---

## Fix A — Dead download URLs

**Finding:** FormCalc 10.0 does not exist upstream; the latest release is 9.10
(feynarts.de, 2024-10-11).  The NIKHEF binary URL for FORM 4.3.1 also returned
HTTP 404.

**Resolution:**

1. Probed all candidate URLs with `curl -sI`:
   - `https://feynarts.de/formcalc/FormCalc-9.10.tar.gz` → **HTTP 200**
   - `https://github.com/vermaseren/form/releases/download/v4.3.1/form-4.3.1.tar.gz`
     → 301 → github.com/form-dev/form → 302 → release-assets → **HTTP 200**

2. Downloaded both tarballs and computed SHA256:
   - FormCalc 9.10: `352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b`
   - FORM 4.3.1:    `f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce`

3. Updated all version pins (10.0 → 9.10 for FormCalc/LoopTools) and URL/SHA in:
   - `skill_env.yaml` — canonical source of truth
   - `install_formcalc.sh` — FORMCALC_VERSION default + URL + FORM_URL
   - `install_formcalc_full.sh` — same
   - `build_form.sh` — FORM_URL + FORM_SHA256
   - `run_formcalc.py` — config fallback defaults

4. Added `TestUpstreamURLs` class to `test_install_integration.py` (gated on
   `HEPPH_RUN_NETWORK_TESTS=1`) that issues HEAD requests against both URLs;
   will catch future drift.

**Evidence:**
```
$ curl -sIL https://feynarts.de/formcalc/FormCalc-9.10.tar.gz | head -1
HTTP/1.1 200 OK

$ curl -sIL https://github.com/vermaseren/form/releases/download/v4.3.1/form-4.3.1.tar.gz \
  | grep "^HTTP" | tail -1
HTTP/2 200

$ shasum -a 256 /tmp/formcalc_9.10.tar.gz
352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b  /tmp/formcalc_9.10.tar.gz

$ shasum -a 256 /tmp/form_4.3.1.tar.gz
f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce  /tmp/form_4.3.1.tar.gz
```

---

## Fix B — atomic_write.sh contract violation

**Finding:** `run_formcalc.py::_write_build_key_atomic` and
`write_sidecar.py::_write_atomic` each contained a local Python reimplementation
of the tmp+fsync+rename+dir-fsync pattern.  Plan §1.3 mandates use of
`plugins/shared/install-helpers/atomic_write.sh`.

**Resolution:**

- Added `_atomic_write_via_shell(dest, content)` to `run_formcalc.py`.  It
  writes a tiny wrapper script to a temp file (freeing stdin) that sources
  `_common.sh` + `atomic_write.sh`, then calls `atomic_write_stdin <dest>` with
  the content piped on stdin via `subprocess.run`.
- `_write_build_key_atomic` now calls `_atomic_write_via_shell` — two lines.
- `write_sidecar.py::_write_atomic` reimplemented identically via the same
  shell pattern.

**Evidence (grep for real call-sites, not comments):**
```
$ git grep -n 'atomic_write_stdin' plugins/hep-ph-toolkit/skills/formcalc*/scripts/*.py
run_formcalc.py:468:        f"atomic_write_stdin {dest!s}\n"
write_sidecar.py:76:        f"atomic_write_stdin {dest!s}\n"
```

**Tests updated:**
- `test_atomic_write_no_tmp_left_on_success` — glob extended to cover
  `.atomic_write_*` (Phase-0 helper naming) in addition to the old pattern.
- `test_write_build_key_uses_shell_helper` (new) — spy on
  `_atomic_write_via_shell` confirms it is called with correct `(dest, content)`.

**Test counts:** `64 passed, 4 skipped` (1 new test added; 2 extra skips from
new network-gated URL probe tests).

---

## Fix C — Iteration-1 report amendment

Appended an **Amendment** section to `iteration-1-impl.md` (end of the
Deviations block) stating:

> The `.build_key` and sidecar atomicity rows in the verification checklist were
> marked PASS based on Python-level tmp+fsync+rename, not on the Phase-0
> `atomic_write.sh` helper.  Iteration-2 routes these through the helper and
> corrects the claim.

---

## Megacommit C8–C11 (reviewer concern D)

The reviewer flagged `b5e511d` (21 files / 2033 insertions, C8-C11 merged) as
hurting bisectability.  This is a historical commit on the branch and **has not
been rebased or split** — rewriting would modify committed history.  The
reviewer accepted this as a deviation from plan §2 granularity.  Future work
should respect the plan's one-concern-per-commit discipline.

---

## Verification checklist

| Check | Status | Evidence |
|---|---|---|
| FormCalc URL returns HTTP 200 | PASS | `curl -sIL feynarts.de/formcalc/FormCalc-9.10.tar.gz` → 200 |
| FORM URL returns HTTP 200 (after redirects) | PASS | GitHub release 301→302→200 |
| FormCalc SHA256 pinned (not TODO) | PASS | `skill_env.yaml` `formcalc_sha256: 352bff19...` |
| FORM SHA256 pinned (not TODO) | PASS | `skill_env.yaml` `form_sha256: f1f512dc...` |
| `.build_key` routes through `atomic_write.sh` | PASS | `_atomic_write_via_shell` calls `atomic_write_stdin`; spy test confirms invocation |
| Sidecar routes through `atomic_write.sh` | PASS | `write_sidecar.py::_write_atomic` uses same shell helper |
| No modification to `atomic_write.sh` itself | PASS | `git diff HEAD -- plugins/shared/install-helpers/atomic_write.sh` → empty |
| iteration-1-impl.md amended | PASS | Amendment section appended |
| 63+ tests passing | PASS | `64 passed, 4 skipped` |

---

## Final test run

```
$ python3 -m pytest plugins/hep-ph-toolkit/skills/formcalc \
                     plugins/hep-ph-toolkit/skills/formcalc-install -q
64 passed, 4 skipped in 1.97s
```

Skips: 2 existing (Wolfram/network golden), 2 new (network URL probe tests).
