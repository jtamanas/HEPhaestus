# Phase-0 Iteration-1 Implementation Report

**Author:** Claude Sonnet 4.6 (implementer agent)
**Date:** 2026-04-19
**Branch:** `workstream-phase0-prep`
**Spec:** `docs/roadmap/v1-constraints-work/phase0-spec.md`

---

## 1. Commits Landed

`git log --oneline main..workstream-phase0-prep`:

```
991243c W7-p0: promote Wolfram helpers to shared + back-compat shims
0ff5907 W7-p0: check_macos_sdk helper
e4d34e0 W7-p0: atomic_write.sh helper
97a7790 W7-p0: download_with_retry offline-cache mode
3ccfec5 W7-p0: _common.sh exit codes 26-29
819cf6d W7-p0: amp_reduced.meta/v1 schema + self-test
19266e0 W7-p0: processspec/v1 schema + self-test
47d3911 W7-p0: scattering/v1 schema + self-test
62daef6 W7-p0: shared blocker.schema symlinks for constraints + feynman-diagrams
fd43896 W7-p0: constraints plugin scaffold
bbe3eea W7-p0: marketplace + CLAUDE.md constraints entry
```

Total: 11 commits. All 11 match the `^W7-p0:` prefix. Matches spec §4 sequence exactly.

---

## 2. Verification Checklist (§5)

### §5.1 JSON / Schema Hygiene

| Check | Result |
|-------|--------|
| `python -m json.tool .claude-plugin/marketplace.json` | PASS |
| `python -m json.tool plugins/constraints/.claude-plugin/plugin.json` | PASS |
| `python -m json.tool plugins/shared/schemas/scattering.schema.json` | PASS |
| `python -m json.tool plugins/shared/schemas/processspec.schema.json` | PASS |
| `python -m json.tool plugins/shared/schemas/amp_reduced.meta.schema.json` | PASS |
| `jsonschema.Draft202012Validator.check_schema` for all 4 schemas | PASS |

### §5.2 Marketplace + Table

| Check | Result | Evidence |
|-------|--------|---------|
| `grep -c '"name": "constraints"' .claude-plugin/marketplace.json` | PASS | output: 1 |
| `grep -c '| Constraints |' CLAUDE.md` | PASS | output: 1 |

### §5.3 Symlinks

| Check | Result | Evidence |
|-------|--------|---------|
| `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | PASS | is symlink |
| `readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | PASS | `../../../model-building/skills/_shared/blocker.schema.json` |
| `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | PASS | is symlink |
| `readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | PASS | `../../../model-building/skills/_shared/blocker.schema.json` |

### §5.4 `_common.sh` Additions

| Check | Result |
|-------|--------|
| Exit codes 26-29 count = 4 | PASS |
| `grep -q 'HEPPH_NO_NETWORK'` | PASS |
| `grep -q 'HEPPH_OFFLINE_CACHE_DIR'` | PASS |
| `grep -q '^check_macos_sdk'` | PASS |
| `test -x plugins/shared/install-helpers/check_macos_sdk.sh` | PASS |
| `test -f plugins/shared/install-helpers/atomic_write.sh` | PASS |
| `bash -n atomic_write.sh && bash -n check_macos_sdk.sh` | PASS |

### §5.5 Wolfram Helper Promotion

| Check | Result | Notes |
|-------|--------|-------|
| `test -f plugins/shared/install-helpers/wolfram/detect_wolfram.sh` | PASS | |
| `test -f plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh` | PASS | |
| `test -f plugins/shared/install-helpers/wolfram/_activation_parse.py` | PASS | |
| Shim assertion: detect_wolfram.sh sources canonical | PASS | |
| Shim assertion: check_wolfram_activation.sh sources canonical | PASS | |
| `assert hasattr(_activation_parse, 'parse_activation')` | **FAIL (spec error — see §4)** | |
| `assert hasattr(_activation_parse, 'classify')` | PASS | Actual function name |

### §5.6 Tests

| Check | Result | Evidence |
|-------|--------|---------|
| `pytest plugins/shared/schemas/tests/ -v` | PASS | 21 passed |
| `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v` | PASS | 5 passed |
| `bash .../test_exit_codes.sh` | PASS | 3 PASS groups |
| `bash .../test_no_network_mode.sh` | PASS | 2 PASS |
| `bash .../test_atomic_write.sh` | PASS | 4 PASS |
| `bash .../test_check_macos_sdk.sh` | PASS | 2 PASS (Darwin) |
| `pytest plugins/hep-ph-toolkit/skills/sarah-install/ -v` | PASS | 21 passed, 1 skipped |
| `bash plugins/hep-ph-toolkit/skills/sarah-install/tests/*.sh` | PASS | 6 PASS |

### §5.7 Git Hygiene

| Check | Result | Evidence |
|-------|--------|---------|
| `git log --oneline main..HEAD | wc -l` = 11 | PASS | 11 |
| All subjects match `^W7-p0:` | PASS | 0 non-matching |
| No changes under hep-ph-demo/collider-pheno/etc. | PASS | |
| `git diff main -- plugins/feynman-diagrams/.claude-plugin/plugin.json` empty | PASS | |

---

## 3. Deviations from Spec

### 3.1 Canonical wolfram scripts: `_common.sh` sourcing path adjustment

**Spec §1.4:** "Promoted verbatim."

**Deviation:** The canonical `detect_wolfram.sh` and `check_wolfram_activation.sh` in `plugins/shared/install-helpers/wolfram/` had their `SHARED_COMMON` path updated from `../../../../shared/install-helpers/_common.sh` (relative to the old location 4 levels deep) to `../_common.sh` (correct relative path from the new location `plugins/shared/install-helpers/wolfram/`).

**Reasoning:** A pure verbatim copy would have broken `config_get` because the old path assumed the file lived under `plugins/hep-ph-toolkit/skills/sarah-install/scripts/`. The "promoted verbatim" intent is that the function behaviour is preserved, not that literal broken paths are copied unchanged.

### 3.2 Spec §5.5 verification check: `parse_activation` vs `classify`

**Spec §1.4 says:** "Importable `parse_activation(stderr: str) -> dict`."  
**Spec §5.5 check:** `assert hasattr(_activation_parse, 'parse_activation')`

**Actual code:** The function in `_activation_parse.py` is named `classify(stdout: str, exit_code: int) -> dict`, not `parse_activation`. This has been the name since the file was originally authored. The spec contains an error — it documents a function name that does not exist in the codebase.

**Resolution:** The file was promoted verbatim (with the function still named `classify`). The shim correctly re-exports `classify` and all other public names. The §5.5 assertion `assert hasattr(_activation_parse, 'parse_activation')` fails; the equivalent correct check `assert hasattr(_activation_parse, 'classify')` passes.

**Recommendation for reviewer:** Update spec §1.4 and §5.5 to reference `classify` instead of `parse_activation`, or add a `parse_activation = classify` alias to the canonical file in a follow-up commit.

### 3.3 `_activation_parse.py` shim: `if __name__ == "__main__"` addition

The spec's Python shim template used `globals().update(...)` without a `__main__` guard. The shim as written in spec §1.4 would not work as a standalone CLI script. Added `if __name__ == "__main__": mod.main()` so direct invocation still works (used by the bash tests' `test_cli_ok` / `test_cli_activation` test cases via `python3 _activation_parse.py <exit_code>`).

### 3.4 Marketplace.json base state

The main checkout has an uncommitted modification to `.claude-plugin/marketplace.json` (git status shows `M .claude-plugin/marketplace.json`). The worktree started from HEAD where `marketplace.json` does not yet include the `hep-ph-demo` entry that is visible as uncommitted in main. This is a pre-existing state; no action taken. The worktree's marketplace.json correctly has the `constraints` entry appended after `feynman-diagrams` as specified.

---

## 4. TODOs / XXXs Left Behind

- `plugins/hep-ph-toolkit/skills/sarah-install/scripts/_activation_parse.py` inherits the `TODO(W1-Day1)` comment from the original file, which was promoted to the canonical location. This TODO predates Phase-0 and belongs to the W1 workstream.
- The `plugins/constraints/README.md` Skills table has a placeholder row; downstream workstreams append real entries.
- `plugins/constraints/.claude-plugin/plugin.json` has `"skills": []`; each downstream workstream appends its entries in lexical order.

---

## 5. Known Risks / Reviewer Notes

1. **`parse_activation` spec discrepancy** (§3.2 above): The §5.5 spec check will fail as written. A reviewer should decide whether to add a `parse_activation = classify` alias or update the spec. No downstream code currently calls `parse_activation`; the six constraint workstream plans reference `classify`.

2. **`_activation_parse.py` shim double-`__main__` guard:** When the shim is imported (not executed), `__name__ != "__main__"` so the `mod.main()` line is skipped. When executed directly, `mod.__name__` is `_activation_parse_canon` (not `__main__`), so the canonical `if __name__ == "__main__"` guard also does not trigger. The shim's `if __name__ == "__main__": mod.main()` correctly bridges this — verified by the `test_cli_ok` and `test_cli_activation` tests passing.

3. **`check_wolfram_activation.sh` shim behavior:** The canonical `check_wolfram_activation.sh` sources `detect_wolfram.sh` via `$SCRIPT_DIR/detect_wolfram.sh`. When the shim at `sarah-install/scripts/check_wolfram_activation.sh` is sourced, it re-sources the canonical file, which sets `SCRIPT_DIR` to the wolfram/ directory. This means the inner `. "$SCRIPT_DIR/detect_wolfram.sh"` correctly finds the canonical detect_wolfram.sh. The 6 bash tests all pass confirming this.

4. **`atomic_write_stdin` uses a temp file:** The implementation writes stdin to a temp file then calls `_atomic_write_impl`. On machines with restricted `/tmp`, this may fail. The temp file is cleaned up on normal and error paths.

5. **`check_macos_sdk` `looptools_quad` on non-arm64 Darwin:** On x86_64 Darwin, the function returns `"looptools_quad": true` without probing gfortran. This is the specified behaviour (quad only becomes false for arm64 + missing libquadmath). Reviewers from the LoopTools workstream should confirm this is correct.

---

## 6. Full Test Summary

```
pytest plugins/shared/schemas/tests/          — 21 passed
pytest plugins/hep-ph-toolkit/skills/_shared/tests/  — 5 passed
pytest plugins/hep-ph-toolkit/skills/sarah-install/  — 21 passed, 1 skipped
bash test_exit_codes.sh                        — PASS (6 assertions)
bash test_no_network_mode.sh                   — PASS (2 assertions)
bash test_atomic_write.sh                      — PASS (4 assertions)
bash test_check_macos_sdk.sh                   — PASS (2 assertions, Darwin-only)
bash test_detect_config.sh                     — PASS (6 assertions)
Total Python tests: 47 passed, 1 skipped
Total bash tests: 20 assertions, all PASS
```
