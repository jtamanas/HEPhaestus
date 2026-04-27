# Phase-0 Constraints Shared Skeleton — Implementation Spec

**Author:** plan-synthesizer
**Date:** 2026-04-19
**Target branch:** `workstream-phase0-prep`
**Worktree path:** `~/Projects/hep-ph-agents-worktrees/phase0-prep/`
**PR title:** `Phase-0: constraints plugin scaffold + shared schemas + helper promotion`
**Scope:** pure infrastructure. Zero skill logic. Landed as a single workstream on `main` before any of the six v1 constraint workstreams (`/micromegas`, `/ddcalc`, `/higgstools`, `/feynarts`, `/formcalc`, `/formcalc`) branches.

This spec exists because each of the six v1 plan finals treats the same bundle of shared artefacts as "Phase-0 owned, assumed landed". A coding agent (sonnet) should be able to execute this end-to-end in an isolated worktree without further exploration.

---

## 0. Branch, worktree, commit-prefix conventions

- **Branch:** `workstream-phase0-prep`. Invoke `superpowers:using-git-worktrees` before creating.
- **Worktree:** `~/Projects/hep-ph-agents-worktrees/phase0-prep/`. Never edit `main` directly.
- **Base:** current `main` head (`41f8b5d` at planning time; rebase at PR open).
- **Commit prefix:** `W7-p0:` (W7 slot; `-p0` subtag distinguishes from sibling W7 workstreams that follow).
- **Commit-body convention:** no `Co-Authored-By:` lines unless the user explicitly requests them.
- **Merge strategy:** `superpowers:finishing-a-development-branch` → squash? no; merge-commit preferred so each atomic commit remains inspectable in bisect.

---

## 1. Files this commit must create (absolute paths, purpose, interface)

### 1.1 `plugins/constraints/` plugin scaffold

- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/.claude-plugin/plugin.json`
  - Purpose: plugin manifest. `skills: []` empty; later workstreams append entries in lexical order.
  - Required fields: `name: "constraints"`, `description`, `version: "0.1.0"`, `skills: []`.
- `/Users/yianni/Projects/hep-ph-agents/plugins/constraints/README.md`
  - Purpose: plugin overview (one paragraph + "Skills" header with empty table ready for append).
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
  - **Relative symlink** → `../../../model-building/skills/_shared/blocker.schema.json`. Do not copy. The canonical schema stays in `plugins/hep-ph-toolkit/skills/_shared/` to keep the 11 existing consumer refs working.

### 1.2 `plugins/hep-ph-toolkit/skills/_shared/` (new directory)

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
  - Relative symlink → `../../../model-building/skills/_shared/blocker.schema.json`.
  - Preserve `plugins/hep-ph-toolkit/skills/amplitude-calc/` and `plugins/hep-ph-toolkit/skills/draw-feynman/` unchanged; `plugin.json` skills list untouched in this Phase-0 commit (feynarts workstream appends its two skills later).

### 1.3 `plugins/shared/schemas/` (new directory) — canonical shared schemas

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/scattering.schema.json`
- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/processspec.schema.json`
- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/amp_reduced.meta.schema.json`

Exact schemas specified in §3.

### 1.4 `plugins/shared/install-helpers/wolfram/` (new directory) — promoted helpers

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/wolfram/detect_wolfram.sh`
  - Canonical content, promoted verbatim from `plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh`.
  - Public interface (unchanged): `detect_wolfram` function + `detect_wolfram_main` CLI — probes `wolframscript`, emits `{status, path, version}` JSON on stdout.
- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh`
  - Promoted verbatim from `sarah-install/scripts/`.
  - Public interface: `check_wolfram_activation` function — runs a trivial `Print[1]` wolframscript, parses stderr for activation prompts via `_activation_parse.py`, emits `{status: "activated"|"activation_required", prompt_line: "..."}` JSON.
- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/wolfram/_activation_parse.py`
  - Promoted verbatim. Importable `parse_activation(stderr: str) -> dict`.

**Backward-compat shims (keep `/sarah-install` tests green):**

Rewrite the three existing files at `plugins/hep-ph-toolkit/skills/sarah-install/scripts/` to be thin source-wrappers:

- `plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh`:
  ```sh
  #!/usr/bin/env bash
  # Back-compat shim — canonical version lives at plugins/shared/install-helpers/wolfram/detect_wolfram.sh
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  . "$SCRIPT_DIR/../../../../shared/install-helpers/wolfram/detect_wolfram.sh"
  ```
- `plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh`: identical pattern → canonical `check_wolfram_activation.sh`.
- `plugins/hep-ph-toolkit/skills/sarah-install/scripts/_activation_parse.py`: replaced by a re-export module:
  ```python
  # Back-compat shim. Canonical: plugins/shared/install-helpers/wolfram/_activation_parse.py
  import importlib.util, os
  _here = os.path.dirname(os.path.abspath(__file__))
  _canon = os.path.normpath(os.path.join(_here, "..", "..", "..", "..", "shared",
                                          "install-helpers", "wolfram", "_activation_parse.py"))
  spec = importlib.util.spec_from_file_location("_activation_parse_canon", _canon)
  mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
  globals().update({k: v for k, v in vars(mod).items() if not k.startswith("_")})
  ```

Shim choice = **option (a)** in the prompt (canonical under `plugins/shared/`, old path becomes thin re-export). `/sarah-install`'s existing tests exercise the old paths and must continue to pass without edit.

### 1.5 `plugins/shared/install-helpers/atomic_write.sh` (new)

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/atomic_write.sh`
- Sourceable shell library. Public interface:
  - `atomic_write <dest_path> <content_file>` — copies `<content_file>` contents to a tmp file alongside `<dest_path>`, `fsync`s the fd, `rename`s tmp → dest, `fsync`s the parent directory. Exits non-zero on any failure.
  - `atomic_write_stdin <dest_path>` — reads content from stdin, same atomicity.
- Implementation uses a Python heredoc (Python ≥ 3.10) identical in spirit to the tmp+fsync+rename+dir-fsync already used inside `config_merge` in `_common.sh`. Stdout silent on success; diagnostic via shared `log`/`err`/`warn` from `_common.sh` when sourced alongside it.

### 1.6 `plugins/shared/install-helpers/_common.sh` additions

Verification: current `_common.sh` uses exit codes 0, 1, 10–16, 20–25. Next free integers 26–29 are unused. Spec assigns:

- `EXIT_NO_CMAKE=26`
- `EXIT_NO_PYBIND=27`
- `EXIT_FORM_BUILD=28`
- `EXIT_LOOPTOOLS_BUILD=29`

Further additions:

- `HEPPH_NO_NETWORK` awareness in `download_with_retry`:
  - If `${HEPPH_NO_NETWORK:-0}` is `1`, skip all `curl` attempts.
  - Require `${HEPPH_OFFLINE_CACHE_DIR:?}` non-empty and `$HEPPH_OFFLINE_CACHE_DIR/$(basename "$dest")` readable; if so, `cp` it to `$dest` and return 0.
  - If absent from cache, emit a blocker JSON on stderr of the form
    `{"code":"<TOOL>_OFFLINE_CACHE_MISS","mode":"fatal","message":"...","context":{"url":"<url>","cache_dir":"<dir>","expected_basename":"..."}}` using the `<TOOL>` passed in as optional third positional arg (defaulting to `DOWNLOAD`), and exit `$EXIT_DOWNLOAD`.
  - New usage: `download_with_retry <url> <dest> [<tool_prefix>]`.

- `check_macos_sdk` function (added inline to `_common.sh` — not a standalone script, despite the `check_macos_sdk.sh` name used in plan finals; the standalone script is a one-line wrapper that sources `_common.sh` and calls the function):
  - Inspects `$(uname -m)`. On non-Darwin: prints `{"looptools_quad": true, "sdkroot": "", "ldflags": ""}` and returns 0.
  - On Darwin: probes `gfortran -print-file-name=libquadmath.dylib` and checks the returned path exists. Uses `xcrun --show-sdk-path` for `sdkroot`. Clang ≥ 15 / arm64 → `ldflags: "-Wl,-ld_classic"` else `""`. Arm64 + missing `libquadmath.dylib` → `"looptools_quad": false`.
  - Emits one-line JSON: `{"looptools_quad": <bool>, "sdkroot": "<path>", "ldflags": "<flags>"}`.

- Standalone wrapper:
  - `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/check_macos_sdk.sh` — five-line script sourcing `_common.sh` then calling `check_macos_sdk`. Interface: `./check_macos_sdk.sh` → stdout JSON; exit code is `check_macos_sdk`'s return value.

### 1.7 `.claude-plugin/marketplace.json` edit

- Append one plugin entry after the `feynman-diagrams` entry (keeping the existing ordering stable otherwise):
  ```json
  {
    "name": "constraints",
    "source": "./plugins/constraints",
    "description": "Constraint-check skills — DM relic/scattering/signals, Higgs bounds/signals, loop integrals",
    "version": "0.1.0",
    "tags": ["constraints", "dark-matter", "direct-detection", "higgs", "loop-integrals"]
  }
  ```

### 1.8 `CLAUDE.md` edit

- Insert new row in the "Plugin Categories" table between "Theory" and "Tools":
  ```
  | Constraints | `constraints` | DM relic/scattering, Higgs exclusion, loop integrals |
  ```

### 1.9 Tests authored in this commit

- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema_symlink.py`
  - Assert that the symlink resolves, the loaded JSON equals byte-for-byte (after `json.load` round-trip) the canonical at `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`, and the schema itself passes `jsonschema.Draft202012Validator.check_schema`.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/tests/test_scattering_schema.py`
  - Self-validity: `Draft202012Validator.check_schema(schema)`.
  - Positive example: fully populated `scattering/v1` document.
  - Negative example: missing `m_dm_gev` rejected; `sigma_si_proton_cm2 = -1e-46` rejected.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/tests/test_processspec_schema.py`
  - Self-validity + the canonical example from the `/feynarts` plan final § Phase-0 item 4 validates; missing `particles` rejected; `loop_order = -1` rejected.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/schemas/tests/test_amp_reduced_meta_schema.py`
  - Self-validity + one positive fixture (`pv_heads: "formcalc-native"`) + one negative (missing `input_hashes.feynamplist_m`).

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/tests/test_exit_codes.sh`
  - Source `_common.sh`; assert the four new constants are defined and equal 26/27/28/29; assert no collision with any existing code by grepping `EXIT_` assignments.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/tests/test_no_network_mode.sh`
  - Stub `curl` to a failing no-op. Set `HEPPH_NO_NETWORK=1` and `HEPPH_OFFLINE_CACHE_DIR=$TMP_CACHE`. Pre-stage `$TMP_CACHE/foo.tar.gz`. Call `download_with_retry https://example/foo.tar.gz /tmp/out.tgz TEST`; assert exit 0 and byte-equal copy. Re-run with empty cache; assert exit `$EXIT_DOWNLOAD`, stderr contains `TEST_OFFLINE_CACHE_MISS`.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/tests/test_atomic_write.sh`
  - Write initial contents to a dest via `atomic_write`. Then spawn a subshell that calls `atomic_write dest new_content` under `kill -9` racing at fsync (use `timeout 0.001` as a crude proxy; accept either exit path). Assert the dest is byte-equal to **either** the old content **or** the fully new content — never partial.

- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/tests/test_check_macos_sdk.sh`
  - Prepend a temp dir to `$PATH` containing a `uname` shim that prints `arm64`; call `check_macos_sdk`; assert JSON output has `"ldflags":"-Wl,-ld_classic"`. Repeat with a `uname` shim printing `x86_64`; assert `"ldflags":""`. On non-Darwin CI, both tests are skipped via `[ "$(uname -s)" = Darwin ] || exit 0`.

No other test runners are added. Existing `pytest` discovery under `plugins/` picks up the new Python tests; the `.sh` tests run via `bash path/to/test.sh` and exit non-zero on failure.

---

## 2. Files this commit must modify

- `/Users/yianni/Projects/hep-ph-agents/.claude-plugin/marketplace.json` — add `constraints` entry (§1.7).
- `/Users/yianni/Projects/hep-ph-agents/CLAUDE.md` — add `Constraints` row (§1.8).
- `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/_common.sh` — append exit codes, add `HEPPH_NO_NETWORK` branch inside `download_with_retry`, append `check_macos_sdk` function (§1.6).
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh` — replace body with shim (§1.4).
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh` — replace body with shim.
- `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/_activation_parse.py` — replace body with re-export.

No other files in `plugins/` are touched.

---

## 3. Schema definitions (JSON Schema draft-2020-12) — canonical

Field-name canon extracted from the six plan finals. All three schemas share `"$schema": "https://json-schema.org/draft/2020-12/schema"` and an `$id` under `https://hep-ph-agents/schemas/`.

### 3.1 `scattering.schema.json`

Field-name source of truth: `/micromegas` plan §2 + `/ddcalc` plan §0 + `/formcalc` plan §1 step 11.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/scattering/v1",
  "title": "DM–nucleon scattering cross-sections (scattering/v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "m_dm_gev",
    "sigma_si_proton_cm2", "sigma_si_neutron_cm2",
    "sigma_sd_proton_cm2", "sigma_sd_neutron_cm2",
    "source", "source_run", "nucleon_form_factors"
  ],
  "properties": {
    "schema_version": {"const": "scattering/v1"},
    "m_dm_gev":            {"type": "number", "exclusiveMinimum": 0},
    "sigma_si_proton_cm2": {"type": "number", "minimum": 0},
    "sigma_si_neutron_cm2":{"type": "number", "minimum": 0},
    "sigma_sd_proton_cm2": {"type": "number", "minimum": 0},
    "sigma_sd_neutron_cm2":{"type": "number", "minimum": 0},
    "source":     {"enum": ["micromegas", "looptools"]},
    "source_run": {"type": "string", "minLength": 1},
    "halo": {
      "oneOf": [
        {"type": "null"},
        {
          "type": "object",
          "additionalProperties": false,
          "required": ["model", "v0_km_per_s", "vesc_km_per_s", "rho0_gev_per_cm3"],
          "properties": {
            "model":            {"enum": ["shm"]},
            "v0_km_per_s":      {"type": "number", "exclusiveMinimum": 0},
            "vesc_km_per_s":    {"type": "number", "exclusiveMinimum": 0},
            "rho0_gev_per_cm3": {"type": "number", "exclusiveMinimum": 0}
          }
        }
      ]
    },
    "nucleon_form_factors": {
      "type": "object",
      "additionalProperties": false,
      "required": ["preset"],
      "properties": {
        "preset": {"enum": ["default_2018", "A1"]}
      }
    }
  }
}
```

### 3.2 `processspec.schema.json`

Field-name source: `/feynarts` plan §0 item 4 (verbatim example) + `/formcalc` + `/formcalc`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/processspec/v1",
  "title": "Process specification (processspec/v1)",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "particles", "loop_order", "kinematic_limit", "excludes"],
  "properties": {
    "schema_version": {"const": "processspec/v1"},
    "particles": {
      "type": "object",
      "additionalProperties": false,
      "required": ["in", "out"],
      "properties": {
        "in":  {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/particle"}},
        "out": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/particle"}}
      }
    },
    "loop_order":      {"type": "integer", "minimum": 0, "maximum": 2},
    "kinematic_limit": {"enum": ["general", "heavy_mediator", "on_shell", "soft"]},
    "excludes":        {"type": "array", "items": {"type": "string"}},
    "mandelstam": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "s": {"type": "string"}, "t": {"type": "string"}, "u": {"type": "string"}
      }
    }
  },
  "$defs": {
    "particle": {
      "type": "object",
      "additionalProperties": false,
      "required": ["label", "pdg", "mass_symbol"],
      "properties": {
        "label":       {"type": "string", "minLength": 1},
        "pdg":         {"type": "integer"},
        "mass_symbol": {"type": "string", "minLength": 1}
      }
    }
  }
}
```

### 3.3 `amp_reduced.meta.schema.json`

Field-name source: `/formcalc` plan §1 + `/formcalc` plan §0.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://hep-ph-agents/schemas/amp_reduced.meta/v1",
  "title": "FormCalc reduced-amplitude sidecar (amp_reduced.meta/v1)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "formcalc_version", "form_version", "looptools_version",
    "gamma5_scheme", "pv_heads", "abbreviations_manifest",
    "input_hashes", "kinematic_limit", "ir_flags", "produced_at",
    "wolfram_version_major_minor"
  ],
  "properties": {
    "schema_version":    {"const": "amp_reduced.meta/v1"},
    "formcalc_version":  {"type": "string", "minLength": 1},
    "form_version":      {"type": "string", "minLength": 1},
    "looptools_version": {"type": "string", "minLength": 1},
    "gamma5_scheme":     {"enum": ["naive", "hv", "bmhv", "larin"]},
    "pv_heads":          {"const": "formcalc-native"},
    "abbreviations_manifest": {"type": "string"},
    "input_hashes": {
      "type": "object",
      "additionalProperties": false,
      "required": ["feynamplist_m"],
      "properties": {
        "feynamplist_m":   {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "processspec_json":{"type": "string", "pattern": "^[a-f0-9]{64}$"}
      }
    },
    "kinematic_limit": {"enum": ["general", "heavy_mediator", "on_shell", "soft"]},
    "ir_flags": {
      "type": "object",
      "additionalProperties": false,
      "required": ["ir_divergent", "uv_regularized"],
      "properties": {
        "ir_divergent":  {"type": "boolean"},
        "uv_regularized":{"type": "boolean"}
      }
    },
    "caveats":     {"type": "array", "items": {"type": "string"}},
    "produced_at": {"type": "string", "format": "date-time"},
    "wolfram_version_major_minor": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+$"}
  }
}
```

If any downstream plan final requires a field not present above, **do not invent** — open a follow-up discussion; v1 schemas are locked at these field lists.

---

## 4. Implementation sequence — 11 atomic commits

Atomicity rule: after each commit, `pytest` against the commit's own new tests passes **and** the pre-existing `/sarah-install` test suite still passes.

1. **C1 — worktree + marketplace + CLAUDE.md.** Create branch. Append `constraints` row to `.claude-plugin/marketplace.json`. Insert row in `CLAUDE.md`. Verify: `python -m json.tool .claude-plugin/marketplace.json`. Commit: `W7-p0: marketplace + CLAUDE.md constraints entry`.

2. **C2 — constraints plugin scaffold.** Create `plugins/constraints/.claude-plugin/plugin.json` (empty skills array), `plugins/constraints/README.md`. Commit: `W7-p0: constraints plugin scaffold`.

3. **C3 — canonical blocker.schema.json symlinks.** Create `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` symlink; create `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` symlink. Verify: `readlink` both. Commit: `W7-p0: shared blocker.schema symlinks for constraints + feynman-diagrams`.

4. **C4 — scattering.schema.json + self-test.** Author `plugins/shared/schemas/scattering.schema.json`; author `plugins/shared/schemas/tests/test_scattering_schema.py`. Commit: `W7-p0: scattering/v1 schema + self-test`.

5. **C5 — processspec.schema.json + self-test.** Commit: `W7-p0: processspec/v1 schema + self-test`.

6. **C6 — amp_reduced.meta.schema.json + self-test.** Commit: `W7-p0: amp_reduced.meta/v1 schema + self-test`.

7. **C7 — exit code additions + test_exit_codes.sh.** Append `EXIT_NO_CMAKE`, `EXIT_NO_PYBIND`, `EXIT_FORM_BUILD`, `EXIT_LOOPTOOLS_BUILD` to `_common.sh`; add `test_exit_codes.sh`. Commit: `W7-p0: _common.sh exit codes 26-29`.

8. **C8 — HEPPH_NO_NETWORK branch in download_with_retry + test.** Modify `download_with_retry` to accept optional tool prefix, honour `HEPPH_NO_NETWORK=1` + `HEPPH_OFFLINE_CACHE_DIR`. Add `test_no_network_mode.sh`. Commit: `W7-p0: download_with_retry offline-cache mode`.

9. **C9 — atomic_write.sh + test.** Author `atomic_write.sh` + `test_atomic_write.sh`. Commit: `W7-p0: atomic_write.sh helper`.

10. **C10 — check_macos_sdk function + wrapper script + test.** Append `check_macos_sdk` to `_common.sh`; author standalone `check_macos_sdk.sh` wrapper; add `test_check_macos_sdk.sh`. Commit: `W7-p0: check_macos_sdk helper`.

11. **C11 — Wolfram helper promotion + shims + blocker-symlink test.** Move `detect_wolfram.sh`, `check_wolfram_activation.sh`, `_activation_parse.py` to `plugins/shared/install-helpers/wolfram/`. Rewrite sarah-install path versions as shims (§1.4). Add `plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema_symlink.py`. Run the full `/sarah-install` test suite to confirm zero regressions. Commit: `W7-p0: promote Wolfram helpers to shared + back-compat shims`.

Each commit leaves the tree green. C11 is the only commit touching `plugins/model-building/`; that blast radius is by design and is the only risky step — the verification checklist (§5) includes an explicit `/sarah-install` regression gate.

---

## 5. Verification checklist (exact shell commands)

Run from repo root `/Users/yianni/Projects/hep-ph-agents/`.

### 5.1 JSON / schema hygiene

- [ ] `python -m json.tool .claude-plugin/marketplace.json > /dev/null`
- [ ] `python -m json.tool plugins/constraints/.claude-plugin/plugin.json > /dev/null`
- [ ] `python -m json.tool plugins/shared/schemas/scattering.schema.json > /dev/null`
- [ ] `python -m json.tool plugins/shared/schemas/processspec.schema.json > /dev/null`
- [ ] `python -m json.tool plugins/shared/schemas/amp_reduced.meta.schema.json > /dev/null`
- [ ] `python -c "import json, jsonschema; [jsonschema.Draft202012Validator.check_schema(json.load(open(p))) for p in ['plugins/shared/schemas/scattering.schema.json','plugins/shared/schemas/processspec.schema.json','plugins/shared/schemas/amp_reduced.meta.schema.json','plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json']]"`

### 5.2 Marketplace + table

- [ ] `grep -c '"name": "constraints"' .claude-plugin/marketplace.json` equals `1`.
- [ ] `grep -c '| Constraints |' CLAUDE.md` equals `1`.

### 5.3 Symlinks

- [ ] `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- [ ] `readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` prints `../../../model-building/skills/_shared/blocker.schema.json`.
- [ ] `test -L plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`
- [ ] `readlink plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` prints `../../../model-building/skills/_shared/blocker.schema.json`.

### 5.4 `_common.sh` additions

- [ ] `grep -E '^EXIT_(NO_CMAKE|NO_PYBIND|FORM_BUILD|LOOPTOOLS_BUILD)=(26|27|28|29)$' plugins/shared/install-helpers/_common.sh | wc -l` equals `4`.
- [ ] `grep -q 'HEPPH_NO_NETWORK' plugins/shared/install-helpers/_common.sh`
- [ ] `grep -q 'HEPPH_OFFLINE_CACHE_DIR' plugins/shared/install-helpers/_common.sh`
- [ ] `grep -q '^check_macos_sdk' plugins/shared/install-helpers/_common.sh`
- [ ] `test -x plugins/shared/install-helpers/check_macos_sdk.sh`
- [ ] `test -f plugins/shared/install-helpers/atomic_write.sh`
- [ ] `bash -n plugins/shared/install-helpers/atomic_write.sh && bash -n plugins/shared/install-helpers/check_macos_sdk.sh`

### 5.5 Wolfram helper promotion

- [ ] `test -f plugins/shared/install-helpers/wolfram/detect_wolfram.sh`
- [ ] `test -f plugins/shared/install-helpers/wolfram/check_wolfram_activation.sh`
- [ ] `test -f plugins/shared/install-helpers/wolfram/_activation_parse.py`
- [ ] Shim assertion: `grep -q 'shared/install-helpers/wolfram/detect_wolfram.sh' plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh`
- [ ] Shim assertion: `grep -q 'shared/install-helpers/wolfram/check_wolfram_activation.sh' plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh`
- [ ] `python -c "import sys; sys.path.insert(0, 'plugins/hep-ph-toolkit/skills/sarah-install/scripts'); import _activation_parse; assert hasattr(_activation_parse, 'parse_activation')"`

### 5.6 Tests

- [ ] `pytest plugins/shared/schemas/tests/ -v`
- [ ] `pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -v`
- [ ] `bash plugins/shared/install-helpers/tests/test_exit_codes.sh`
- [ ] `bash plugins/shared/install-helpers/tests/test_no_network_mode.sh`
- [ ] `bash plugins/shared/install-helpers/tests/test_atomic_write.sh`
- [ ] `bash plugins/shared/install-helpers/tests/test_check_macos_sdk.sh`
- [ ] **Regression gate** — `/sarah-install` suite passes unchanged: `pytest plugins/hep-ph-toolkit/skills/sarah-install/ -v` **and** `bash plugins/hep-ph-toolkit/skills/sarah-install/tests/*.sh` (any existing).

### 5.7 Git hygiene

- [ ] `git log --oneline main..HEAD | wc -l` equals `11` (one per atomic commit in §4).
- [ ] Every commit subject matches `^W7-p0: `: `git log --pretty=%s main..HEAD | grep -cv '^W7-p0: '` equals `0`.
- [ ] `git diff main --stat` shows zero changes under `plugins/hep-ph-demo/`, `plugins/collider-pheno/`, `plugins/monte-carlo-tools/`, `plugins/hep-data-analysis/`, `plugins/latex-hep/`, `plugins/arxiv-research/`, `plugins/hep-plotting/`.
- [ ] `git diff main -- plugins/feynman-diagrams/.claude-plugin/plugin.json` is empty (Phase-0 does not touch the feynman-diagrams manifest; feynarts workstream owns that append).

---

## 6. Explicit non-goals

Phase-0 does **not**:

- Author any of the six constraint skills (`/micromegas-install`, `/micromegas`, `/ddcalc-install`, `/ddcalc`, `/higgstools-install`, `/higgstools`, `/feynarts-install`, `/feynarts`, `/formcalc-install`, `/formcalc`, `/formcalc-install`, `/formcalc`). Skill logic is owned by its dedicated workstream.
- Edit `plugins/feynman-diagrams/.claude-plugin/plugin.json` or `plugins/feynman-diagrams/README.md`. The `/feynarts` workstream appends `feynarts-install` + `feynarts` entries there.
- Modify `/sarah-install`, `/spheno-build`, `/sarah-build`, `/lagrangian-builder`, `/madgraph` SKILL.md contents or script behaviour. The Wolfram-helper promotion (§1.4) preserves the old paths as thin shims so `/sarah-install`'s scripts and tests see identical behaviour.
- Move `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`. The canonical blocker schema stays where it is; `plugins/constraints/` and `plugins/feynman-diagrams/` get **symlinks** into it. Relocation is out of scope per manager decision reflected in `/micromegas` plan §5 and `/feynarts` plan §0 item 1.
- Promote `blocker.schema.json` to `plugins/shared/schemas/`.
- Add CI configuration changes.
- Touch `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` (the one-line shim described at the top of the canonical file) — the canonical file is the only `_common.sh` edited; the shim is unchanged.
- Add `HEPPH_RUN_WOLFRAM_TESTS` / `HEPPH_RUN_NETWORK_TESTS` gating scaffolds beyond what the new tests themselves require. All tests added here are always-on (no env gates) — gated integration tests belong to the six downstream workstreams.
- Author example/fixture documents consumed by the downstream skills (e.g. `sigma_json_sample.json`, `ee_to_mumu/FeynAmpList.m`). Those live under the relevant skill's `tests/fixtures/`.
- Pre-populate `skills[]` arrays in `plugins/constraints/.claude-plugin/plugin.json` for any of the six skills. Each downstream workstream adds its own two entries.
- Create `SHARED.md` files under any plugin. Downstream workstreams (notably `/feynarts`) create those when they need them.
- Add a `version: 0.2.0` bump to `plugins/feynman-diagrams/.claude-plugin/plugin.json` or to its marketplace entry. The `/feynarts`, `/formcalc`, `/formcalc` workstreams each bump once when they append their skills.

---

## 7. Risks + mitigations

- **Risk:** the Wolfram-helper shim breaks `/sarah-install`'s sourcing because `SCRIPT_DIR` resolution differs between sourced vs. executed scripts.
  - **Mitigation:** the shim uses `BASH_SOURCE[0]` (not `$0`), which is correct in both contexts. The regression gate (§5.6 final bullet) is the objective pass/fail. If that suite regresses, revert C11 and revisit with option (b) in the prompt — leave both paths, have the new path re-export from the old.
- **Risk:** schema field-name drift between this spec and future micro-revisions of plan finals.
  - **Mitigation:** the three schemas in §3 are the canonical source of truth; downstream plans reference them by `$id`, not by re-authoring fields. Any downstream workstream finding a genuine missing field raises a v1.0.1 Phase-0 amendment PR — not a local workaround.
- **Risk:** `atomic_write.sh` crash-test is inherently racy; the assertion is "either old-bytes or full-new-bytes", not "both crash modes exercised".
  - **Mitigation:** the loop runs ~20 iterations; any observed partial write fails the test. This is the same discipline `config_merge` already uses in `_common.sh`.

---

## 8. Output summary for a coding agent

A sonnet-class agent executing this spec should:

1. Read §0 + §4. Create worktree + branch.
2. Execute commits C1–C11 in order, running `§5` verifications **between** commits (at minimum §5.6 after C4/C5/C6/C7/C8/C9/C10/C11).
3. On C11, run the full `/sarah-install` regression suite before committing.
4. Open PR with §5 as the PR body checklist.

Total estimate: 11 commits, 0 skill logic, 0 downstream workstream edits, ~3 hours wall-clock for a sonnet agent including verification. Zero ambiguity on field names, paths, commit order, or out-of-scope edges.

End of Phase-0 spec. Word count: ~2550.
