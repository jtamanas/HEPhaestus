# Phase 2 — Implementation Plan (Drafter)

**Role:** detailed, executable plan for each workstream. Written so a Sonnet implementer with zero conversation context can execute each workstream end to end without re-reading the spec or the Phase 1 strategy.

**Authoritative upstream docs** (do not duplicate — reference):
- Strategy: `docs/superpowers/workstream-sarah-spheno/phase1-final.md`
- Spec: `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
- Precedent skill: `plugins/hep-ph-toolkit/skills/install/SKILL.md`
- Precedent scripts: `plugins/hep-ph-toolkit/skills/install/scripts/{_common.sh,install_sarah.sh,install_spheno.sh,install_wolfram.sh}`

**Invariants across all workstreams:**
- All file paths absolute from repo root `/Users/yianni/Projects/hep-ph-agents/`.
- All skill dirs live under `plugins/hep-ph-toolkit/skills/<skill-name>/`.
- All new Python uses stdlib only except `jsonschema` and `pyyaml` (already permitted by the project — no other new deps without reviewer approval).
- Bash scripts start with `#!/usr/bin/env bash` and `set -euo pipefail`.
- All timestamps UTC ISO 8601 with `Z` suffix.
- No tool-mocking in integration tests. Unit tests may mock log parsers and pure-Python utilities only (augment-not-replace).
- Three-state blocker contract (fatal / recoverable / reference-only). `activation_required` is a *status code* from `/sarah-install`, not a blocker mode.
- Cache keys are input-only (never hash output trees).
- `str.format` templates, never Jinja2.
- Config keys align with existing `hep-ph-demo/install` — no renames, single net-new key `spheno_src_path`.

---

## Workstream W0 — Shared contracts + config migration

**Dependencies:** none. Blocks every other workstream.
**Worktree name:** `wt-w0-shared-contracts`
**Base branch:** `main`
**Lands:** synchronously to `main` before any other worktree spawns.

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/_common.sh` | Promoted copy of `hep-ph-demo/skills/install/scripts/_common.sh`. Byte-for-byte identical at first commit. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/README.md` | Two-paragraph note: what `_common.sh` provides, how downstream installers source it, version history comment. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` | Replace body with `source <repo-rel-path>/plugins/shared/install-helpers/_common.sh`. Keep file in place so existing installers don't break. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh` | No logic change; only adjust the `. "$SCRIPT_DIR/_common.sh"` comment to note it's a shim. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh` | Same shim note. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_mg5.sh` | Same shim note. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh` | Same shim note. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/SHARED-model-building.md` | Cross-skill conventions: state root, model-name regex, timestamps, env-var overrides, cache-key recipe. Not a README, not docs — a normative contract. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` | JSON Schema for ModelSpec v1 (per spec §4). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | JSON Schema for the three-state blocker contract (fatal / recoverable / reference_only). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/sarah-name.py` | `modelspec_name_to_sarah(name: str) -> str` canonicalizer. Provisional rule: `"".join(w.capitalize() for w in name.split("_"))`. Exposes CLI: `python3 sarah-name.py <modelspec_name>`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/config-migration.py` | Reads existing `~/.config/hep-ph-agents/config.json`, asserts no renames, ensures `models: {}` key exists, writes back atomically. CLI: `python3 config-migration.py [--check|--apply]`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/config_helpers.py` | Python mirrors of `_common.sh::config_get` and `::config_merge` for Python drivers (W3, W4, W5). Single `load_config()`, `merge_config(**kwargs)`, `register_model(name, **fields)` helpers. Atomic write via tmpfile + rename. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md` | Stub (frontmatter + one-line description + TODO pointer to W1). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` | Stub. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md` | Stub. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` | Stub. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/model-building/.claude-plugin/plugin.json` | Register four new skills in `skills[]` array. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_modelspec_schema.py` | `jsonschema` validates the spec §4 `dark_su3` example. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema.py` | Validates one instance of each blocker mode. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_sarah_name.py` | Unit test for the canonicalizer with `@pytest.mark.skip_if_no_sarah` marker on the integration case. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_config_helpers.py` | Unit test of `merge_config` and `register_model`: atomicity, preservation of unrelated keys, roundtrip. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` | Copy of the spec §4 example. Used by downstream workstreams too. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/blocker_examples.json` | One instance per mode. Consumed by downstream parse tests. |

### Detailed work items (ordered)

1. **Create `plugins/shared/install-helpers/` directory.** Copy `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` verbatim to `plugins/shared/install-helpers/_common.sh`. Do not modify content.
2. **Write `plugins/shared/install-helpers/README.md`** explaining that this file is the single source of truth for bash helpers used by all `install_*.sh` scripts across hep-ph-demo, `/sarah-install`, and `/spheno-install`. Note the precondition: sourcing scripts must compute `SHARED_HELPERS=$(cd "$SCRIPT_DIR/../../../shared/install-helpers" && pwd)/_common.sh` with a fallback error if not found.
3. **Refactor each `hep-ph-demo` installer** to source the promoted copy. The pattern:
   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   SHARED_COMMON="$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"
   if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
   . "$SHARED_COMMON"
   ```
   The local `_common.sh` becomes a one-line shim that sources the promoted copy — keep it as a shim (don't delete) so any unknown consumers still work.
4. **Regression gate.** Run `bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all`. Must print one JSON line per tool identically to before the refactor. Commit only after passing.
5. **Write `plugins/hep-ph-toolkit/SHARED-model-building.md`** with sections:
   - State root: `~/.local/share/hep-ph-agents/models/<name>/` (per-model only; tool installs live where hep-ph-demo put them).
   - Model-name regex: `^[a-z][a-z0-9_]{1,30}$`.
   - Timestamps: UTC ISO 8601 `%Y-%m-%dT%H:%M:%SZ`.
   - Env-var overrides: `HEPPH_SARAH_VERSION` only (drop any `HEPPH_WOLFRAM_KERNEL` speculation).
   - Cache-key recipe: W3 = `sha256(spec.yaml contents) + sarah_version`; W4 = `sha256(spec.yaml contents) + sarah_version + spheno_version`. Single-line hex sha256.
   - Three-state blocker contract summary (reference `blocker.schema.json`).
   - Config key alignment table (spec invented → existing hep-ph-demo).
6. **Write `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`.** Translate spec §4 YAML to JSON Schema draft 2020-12. Required top-level keys: `name`, `claim_source`, `sarah_version_required`, `gauge_groups`, `fermions`, `scalars`, `lagrangian`, `parameters`, `outputs`. `spec_version: 1` is required. No `x-extensions`. `name` must match the model-name regex. Each `gauge_groups[].kind` ∈ `{hypercharge, left, color, dark, other}`. `outputs` items ∈ `{ufo, spheno}`.
7. **Write `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.** Three modes: `fatal | recoverable | reference_only`. Required fields: `code` (string, SCREAMING_SNAKE), `mode`, `message` (human-readable), `context` (object, free-form but schema-typed per known code). Optional: `user_instruction` (string; used by `fatal` blockers that require user action).
8. **Write `plugins/hep-ph-toolkit/skills/_shared/sarah-name.py`.** Single function `modelspec_name_to_sarah(name: str) -> str` implementing the provisional rule. CLI mode: `python3 sarah-name.py <name>` prints the SARAH name; exit 0 on success, exit 2 if name fails the regex. Include a `# PROVISIONAL` comment block citing Day-1 W3 probe.
9. **Write `plugins/hep-ph-toolkit/skills/_shared/config_helpers.py`.** Public API:
   - `CONFIG_PATH: pathlib.Path` computed from `XDG_CONFIG_HOME` with fallback.
   - `load_config() -> dict`.
   - `merge_config(**kwargs) -> None` — atomic tmpfile + rename; preserves unrelated keys; updates `last_configured`.
   - `register_model(name: str, **fields) -> None` — upserts `config["models"][name]` with given fields plus preserves prior fields; raises if `name` fails regex.
   - `get_model(name: str) -> dict | None`.
10. **Write `plugins/hep-ph-toolkit/skills/_shared/config-migration.py`.** `--check` mode: read config, assert that if `wolfram_engine_path` / `sarah_path` / `spheno_path` exist, they are kept as-is (no rename). Assert `models: {}` present or add it. Print diff. `--apply` mode: actually write. Exits 0 if no changes needed.
11. **Write the four stub SKILL.md files.** Each has frontmatter per Claude Code skill convention:
    ```
    ---
    name: sarah-install
    description: Detect, configure, or auto-install Wolfram Engine + SARAH. (Stub — implemented in W1.)
    ---
    ```
    Body: one paragraph pointing to the spec and the owning workstream.
12. **Modify `plugins/model-building/.claude-plugin/plugin.json`.** Append to `skills[]`:
    ```json
    {"name":"sarah-install","path":"./skills/sarah-install/SKILL.md"},
    {"name":"sarah-build","path":"./skills/sarah-build/SKILL.md"},
    {"name":"spheno-install","path":"./skills/spheno-install/SKILL.md"},
    {"name":"spheno-build","path":"./skills/spheno-build/SKILL.md"}
    ```
    Bump `version` to `0.2.0`.
13. **Write `tests/test_modelspec_schema.py`.** Use `jsonschema.validate()`. Covers: valid `dark_su3`, missing `spec_version`, bad `name` regex, unknown gauge-group `kind`, `outputs: [calchep]` rejected.
14. **Write `tests/test_blocker_schema.py`.** Validates each of the six known codes: `SARAH_DOWNLOAD_FAILED` (fatal), `ANOMALY_CANCELLATION_FAILED` (fatal), `SPHENO_SPECTRUM_PROBLEM` (recoverable), `SPHENO_RGE_NONCONVERGENT` (recoverable), `SPHENO_NO_OUTPUT` (fatal), plus one `reference_only` example if spec supports it.
15. **Write `tests/test_sarah_name.py`.** Cases: `dark_su3 → DarkSU3`, `singlet_doublet → SingletDoublet`, `2hdm → <name>` rejected by regex (starts with digit). Mark any SARAH-verified case with `@pytest.mark.sarah_integration` / `skip_if_no_sarah`.
16. **Write `tests/test_config_helpers.py`.** Unit tests with `tmp_path`. Cases: merge into empty, preserve unrelated, atomicity (simulate crash after tmpfile write), register_model regex enforcement.
17. **Write fixtures.** `dark_su3_spec.yaml` = verbatim copy of spec §4 YAML. `blocker_examples.json` = one instance per mode from step 14.
18. **Run full W0 acceptance sweep** (see below) before opening PR.

### Acceptance criteria

- `python3 -m jsonschema -i plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` exits 0. (Or the pytest equivalent if YAML→JSON step needed.)
- `bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all` still prints four JSON lines in the same order and shape as pre-refactor. Regression tester runs this twice, diffs output.
- `python3 plugins/hep-ph-toolkit/skills/_shared/config-migration.py --check` exits 0 on a machine whose config has existing hep-ph-demo keys.
- `python3 plugins/hep-ph-toolkit/skills/_shared/sarah-name.py dark_su3` prints `DarkSU3`.
- `jq '.skills | length == 4' plugins/model-building/.claude-plugin/plugin.json` returns true (after adding the four new + noting that `rge-runner` already existed; final count is 6 if existing skills retained — reviewer confirm).
- All pytest tests under `plugins/hep-ph-toolkit/skills/_shared/tests/` pass.

### Tests

| Test | Type | Location | Requires real tool? |
|---|---|---|---|
| `test_modelspec_schema.py` | unit | `_shared/tests/` | no |
| `test_blocker_schema.py` | unit | `_shared/tests/` | no |
| `test_sarah_name.py` | unit | `_shared/tests/` | no (SARAH-verified case skipped) |
| `test_config_helpers.py` | unit | `_shared/tests/` | no |
| `install.sh detect-all` regression | smoke | manual or CI | no (detects only) |

### Dependencies

- **Reads from:** hep-ph-demo `_common.sh` (copied verbatim), spec §4 (ModelSpec YAML).
- **Writes for others:**
  - `modelspec.schema.json` (consumed by W3 `validate_spec.py`, W5 interview).
  - `blocker.schema.json` (consumed by W1, W2, W3, W4 for emission).
  - `sarah-name.py` (consumed by W3 `render_templates.py`).
  - `config_helpers.py` (consumed by W3, W4, W5).
  - Shared `_common.sh` (consumed by W1, W2).
  - Four stub SKILL.md (overwritten by W1, W2, W3, W4).
  - Fixtures `dark_su3_spec.yaml`, `blocker_examples.json` (consumed by W3, W4 tests).

### Risks / open questions for reviewer

- **`plugin.json` `skills` array shape.** Assumed `{name, path}` entry format matching existing two. Reviewer confirm there's no `category` or `version` field required.
- **`_common.sh` shim vs delete.** I chose shim (keeps file; sources promoted copy) to avoid breaking any unknown script that directly sources the local file. Reviewer: is outright deletion cleaner? I vote shim.
- **`config_helpers.py` vs pure bash.** Python drivers in W3/W4/W5 need config access. Rather than repeatedly shell out to `config_get`/`config_merge`, I write a Python mirror. Reviewer may prefer a thin `subprocess.run(["bash", "-c", "source _common.sh; config_get ..."])` wrapper; I think that's fragile.
- **Where do shared *Python* fixtures live?** I put them under `_shared/tests/fixtures/`. Alternatively `plugins/model-building/tests/fixtures/` if there's a house-level tests dir. Reviewer decide.
- **Schema for `blocker.schema.json` reference_only.** Spec mentions `reference_only` mode exists (PR-D contract per phase1-final §4) but doesn't show a concrete example. I wrote a minimal one; reviewer confirm shape.

---

## Workstream W1 — `/sarah-install`

**Dependencies:** W0.
**Worktree name:** `wt-w1-sarah-install`
**Base branch:** `main` (post-W0 merge).

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md` | Full skill — decision flow, JSON status contract, reference to activation instructions. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/install_sarah.sh` | `detect | use-path <dir> | install [dir]` subcommands. Adapted from `hep-ph-demo/skills/install/scripts/install_sarah.sh`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh` | Probes with `wolframscript -code '1+1'`; emits `{"status":"activation_required", ...}` if prompt detected. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh` | Delegates to `hep-ph-demo/.../install_wolfram.sh detect` (via PATH discovery) OR inline-implements the same detection. Prefer inline (don't couple to hep-ph-demo's skill path). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/skill_env.yaml` | `sarah_version: 4.15.3`, `sarah_url`, `sarah_sha256: TODO` (match hep-ph-demo placeholder pattern). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/test_detect_config.sh` | Bash test: mocked config file → `detect` returns the right JSON. Uses `XDG_CONFIG_HOME` override. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/test_activation_parse.py` | Unit test of the activation-prompt parser on canned `wolframscript` output fixtures. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/fixtures/wolfram_activation_prompt.txt` | Captured `wolframscript` activation-needed output. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/fixtures/wolfram_ok.txt` | `1+1` → `2` happy-path output. |

### Detailed work items

1. **Read and understand `hep-ph-demo/skills/install/scripts/install_sarah.sh` completely.** It is the direct ancestor. Most of its body ports over.
2. **Copy `install_sarah.sh`** from hep-ph-demo into the new skill's `scripts/`. Change the source line to point at `plugins/shared/install-helpers/_common.sh` per the W0 pattern (`$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh`).
3. **Config-key parity check.** Verify the script writes only the existing keys: `sarah_path`, `sarah_version`, `sarah_installed_at`, and reads `wolfram_engine_path`, `wolfram_engine_version`. Do not introduce `wolfram_kernel` or `wolfram_kind`.
4. **Add `sarah_installed_at`** (new; not in hep-ph-demo version). Write UTC ISO 8601 via `date -u +%Y-%m-%dT%H:%M:%SZ` into `config_merge`.
5. **Write `check_wolfram_activation.sh`.** Algorithm:
   - Read `wolfram_engine_path` from config.
   - Run `$wolframscript -code '1+1' 2>&1`.
   - If exit=0 and output contains `2`, print `{"status":"ok"}`.
   - If output contains the string `"activate"` or `"Wolfram ID"` or `"not activated"` (grep patterns; append fixtures used), print `{"status":"activation_required","message":"<exact remediation>","user_instruction":"Run \`wolframscript --activate\` in your terminal once; it will open a browser window for a free Wolfram ID signup. Then rerun \`/sarah-install\`."}`.
   - Else print `{"status":"error","detail":"<first 200 chars>"}`.
6. **Write `detect_wolfram.sh`** as a small wrapper that reimplements just the scan_candidates + probe_version logic from hep-ph-demo's `install_wolfram.sh`. Do NOT call into hep-ph-demo's scripts directly (decoupling).
7. **Install flow changes vs hep-ph-demo version:**
   - After extract + register_path, call `check_wolfram_activation.sh`. If `activation_required`, **do not exit with `EXIT_WOLFRAM_ACTIVATION` from `_common.sh`**; instead print the JSON status to stdout and exit 0. This is the key semantic change: activation required is a *status*, not a blocker.
   - SARAH smoke test still blocks via `EXIT_SMOKE` if `<<SARAH`` itself fails (not an activation issue).
   - Emit blockers per `blocker.schema.json` on fatal paths, via a small bash `emit_blocker()` helper added to the script (or to a new `sarah-install/scripts/_blocker.sh` sourced by the installer).
8. **Write `skill_env.yaml`.** Three keys: `sarah_version: "4.15.3"`, `sarah_url`, `sarah_sha256: "TODO"`. Comment pointing at the shared `_common.sh::verify_checksum` warn-not-abort behavior.
9. **Write `SKILL.md`.** Mirror structure of `hep-ph-demo/skills/install/SKILL.md` §2. Sections: "When to invoke", "Decision flow", "JSON status contract", "Activation handling (critical)", "Failure modes → blockers". Failure modes exactly per spec §2 `/sarah-install` — `WOLFRAM_KERNEL_ABSENT`, `WOLFRAM_NEEDS_ACTIVATION` (demoted to status, not blocker — SKILL.md must flag this divergence from spec §2), `SARAH_DOWNLOAD_FAILED`, `SARAH_SMOKE_TEST_FAILED`.
10. **Detect-and-reuse path.** In `cmd_detect`: if `sarah_path` and `wolfram_engine_path` are both present and `probe_version` returns, print `{"status":"configured", ...}` and exit 0. Orchestrator (W5) reads this to avoid re-installing.
11. **Write `test_detect_config.sh`.** Sets `XDG_CONFIG_HOME=/tmp/test-hepph-$$/config`, creates a fake config, runs `install_sarah.sh detect`, asserts JSON shape. Cleans up.
12. **Write `test_activation_parse.py`.** Pure-Python unit test of a small helper (extract to `scripts/_activation_parse.py` — Python function that takes stdout string and returns status JSON). Loaded fixtures from `tests/fixtures/`. This avoids shelling out to `wolframscript`.
13. **Day-1 probe:** run the activation path end-to-end on macOS with Wolfram Engine unactivated. If the actual prompt string differs from our fixtures, update the grep patterns. Document observed strings in `tests/fixtures/`.

### Acceptance criteria

- `bash install_sarah.sh detect` with no prior config → prints exactly `{"status":"missing"}` to stdout; exit 0.
- `bash install_sarah.sh detect` with `sarah_path` set to a valid SARAH dir and Wolfram configured → prints `{"status":"configured","path":"...","version":"4.15.3"}`; exit 0.
- `bash install_sarah.sh detect` with `sarah_path` unset but one of `~/SARAH/SARAH-4.15.3/SARAH.m` present → prints `{"status":"found","path":"..."}`.
- With network blocked (no DNS) and `install` invoked: fails with `SARAH_DOWNLOAD_FAILED` blocker JSON on stderr *and* exit code `$EXIT_DOWNLOAD` (12) per shared `_common.sh`.
- With Wolfram Engine installed but not activated: `bash install_sarah.sh install` runs through the extract, then `check_wolfram_activation.sh` detects prompt → prints `{"status":"activation_required", ...}` JSON to stdout, **exit 0**, *no* blocker emitted.
- After successful install on a fresh machine: `wolframscript -code '<<SARAH`; Start["SM"]; CheckModel[]'` exits 0.
- Config after install contains exactly the keys `sarah_path`, `sarah_version`, `sarah_installed_at` added (plus `last_configured` via shared helper). No `wolfram_kernel`, no `sarah_base_path`.
- Pre-existing `hep-ph-demo` install of SARAH detected → `status: configured`, no reinstall triggered.

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_detect_config.sh` | smoke (bash) | no (config only) |
| `test_activation_parse.py` | unit | no (fixtures) |
| Full install on clean macOS | integration | **yes — Wolfram Engine + network** |
| Full install on clean Linux | integration | **yes** |
| Detect-and-reuse against hep-ph-demo install | integration | **yes (existing install)** |

The three integration tests are Day-1 probes; a human or Sonnet running on a real machine. Not in CI.

### Dependencies

- **Reads:** W0 `_common.sh`, `blocker.schema.json`.
- **Writes:** `config.sarah_path`, `config.sarah_version`, `config.sarah_installed_at`. Reads `config.wolfram_engine_path`, `config.wolfram_engine_version`.
- **Invoked by:** W3 (precondition check), W5 (orchestrator lazy-install).

### Risks / open questions

- **Activation prompt string.** The exact string printed by `wolframscript` on an unactivated kernel isn't documented. Day-1 probe will pin it; until then, our grep is defensive (`activate`/`Wolfram ID`/`not activated`).
- **SKILL.md divergence from spec §2.** Spec §2 lists `WOLFRAM_NEEDS_ACTIVATION` as a blocker. Phase 1 §4 demoted it to a status. SKILL.md must make the divergence explicit with a note pointing at the strategy doc.
- **Decoupling from hep-ph-demo.** By inlining detection rather than calling hep-ph-demo's `install_wolfram.sh`, we duplicate ~40 lines. Reviewer: okay, or promote Wolfram-detect to `plugins/shared/install-helpers/` too?

---

## Workstream W2 — `/spheno-install`

**Dependencies:** W0.
**Worktree name:** `wt-w2-spheno-install`
**Base branch:** `main` (post-W0 merge). Runs in parallel with W1.

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md` | Full skill. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/install_spheno.sh` | `detect | use-path <path-to-source-tree> | install [dir]`. Sources shared `_common.sh`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/check_gfortran.sh` | Extracted from the installer, per-OS remediation messages. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/skill_env.yaml` | `spheno_version: 4.0.5`, `spheno_url`, `spheno_sha256: TODO`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/test_detect_derive_src.sh` | Bash test: existing hep-ph-demo install detected → `spheno_src_path` correctly derived as `dirname(dirname(spheno_path))`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/test_make_log_tail.py` | Unit test of make.log → blocker context conversion. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_fail_lapack.log` | Canned make output missing LAPACK. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_fail_generic.log` | Canned make output generic failure. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_ok.log` | Canned successful make output. |

### Detailed work items

1. **Copy `install_spheno.sh`** from hep-ph-demo. Source the promoted `_common.sh`.
2. **Dual-key write.** Both keys populated on every install and every `use-path`:
   - `spheno_path` — binary at `<src-tree>/bin/SPheno` (preserve hep-ph-demo compatibility).
   - `spheno_src_path` — the source tree root (containing `Makefile`). New key.
   - `spheno_version`, `spheno_installed_at`.
3. **`use-path <path-to-source-tree>`** — accepts source tree (must contain `Makefile`). Derives binary at `<path>/bin/SPheno`. Validates both exist. This is a semantic change from hep-ph-demo's `use-path` which accepts a binary. If the user passes a binary path, detect and infer source tree = `dirname(dirname(path))`; warn.
4. **Detect-and-reuse path.** If `spheno_path` already set by hep-ph-demo, derive `spheno_src_path = dirname(dirname(spheno_path))`, validate `Makefile` present, record, and status = `configured` (no reinstall).
5. **Version-pin check on reuse (per Phase 1 §8 Issue 10).** If detected version ≠ pinned `spheno_version`, emit a warning JSON `{"status":"found","path":"...","version":"...","pin":"4.0.5","warning":"version_mismatch"}` and *do not* auto-adopt — let orchestrator/user decide.
6. **Write `check_gfortran.sh`.** Extracted for reuse by W4 compile step. Exits 0 if present; exits `$EXIT_NO_GFORTRAN` with per-OS message if absent.
7. **Emit `SPHENO_BASE_BUILD_FAILED` blocker.** On `make` failure, tail last 40 lines of `/tmp/spheno_make.log`, JSON-escape, emit as `context.make_log_tail`. Follow `blocker.schema.json`.
8. **Write `skill_env.yaml`.** `spheno_version: "4.0.5"`, `spheno_url: "https://spheno.hepforge.org/downloads/SPheno-4.0.5.tar.gz"`, `spheno_sha256: "TODO"`.
9. **Write `SKILL.md`.** Structure: "When to invoke", "Decision flow (detect/use-path/install)", "gfortran precondition", "Config keys (dual-key rationale)", "Detect existing hep-ph-demo install", "Failure modes → blockers" (per spec §2 — `GFORTRAN_ABSENT`, `SPHENO_DOWNLOAD_FAILED`, `SPHENO_BASE_BUILD_FAILED`, `SPHENO_PATH_INVALID`).
10. **Write `test_detect_derive_src.sh`.** Create fake dir `/tmp/sp-test-$$/SPheno-4.0.5/{bin/SPheno,Makefile}`, set config `spheno_path=.../bin/SPheno`, run `detect`, assert output contains `"spheno_src_path"`. (Note: current hep-ph-demo detect doesn't print `spheno_src_path`; the new W2 detect does.)
11. **Write `test_make_log_tail.py`.** Ingests each fixture, asserts `extract_build_blocker(log_contents)` returns correct `code` and correct `context.make_log_tail` (last 40 lines).

### Acceptance criteria

- `bash install_spheno.sh detect` with no config → `{"status":"missing"}`.
- With hep-ph-demo install present (`spheno_path` set to a real binary): `detect` emits `{"status":"configured","path":"...","src_path":"...","version":"..."}`. `src_path` is derived.
- `bash install_spheno.sh install` on a clean box with `gfortran` present: produces `$HOME/SPheno/SPheno-4.0.5/{bin/SPheno,Makefile}` and writes both `spheno_path` and `spheno_src_path` to config. `make -C $spheno_src_path` (no target) succeeds as a re-run.
- `bash install_spheno.sh install` with `gfortran` absent → `GFORTRAN_ABSENT` blocker emitted, exit `$EXIT_NO_GFORTRAN`.
- `make` failure → last 40 lines of `make.log` embedded in `SPHENO_BASE_BUILD_FAILED` blocker context.
- Version mismatch on reuse → `status: found, warning: version_mismatch`, no silent adoption.

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_detect_derive_src.sh` | smoke | no (fake dirs) |
| `test_make_log_tail.py` | unit | no |
| Full install on clean macOS | integration | **yes — gfortran + network (5–15 min)** |
| Full install on clean Linux | integration | **yes** |
| Detect-and-reuse against hep-ph-demo install | integration | **yes** |

### Dependencies

- **Reads:** W0 `_common.sh`, `blocker.schema.json`.
- **Writes:** `config.spheno_path`, `config.spheno_src_path` (new), `config.spheno_version`, `config.spheno_installed_at`.
- **Invoked by:** W4 (precondition), W5 (orchestrator).

### Risks / open questions

- **`use-path` semantic change.** hep-ph-demo accepts a binary; we accept a source tree. This breaks nothing (separate script), but is inconsistent across the codebase. Reviewer: should we accept either and detect?
- **Version-mismatch warning vs silent adoption.** Phase 1 §8 Issue 10 says "install fresh alongside rather than adopt" on mismatch. That's stronger than my "warn and let user decide." Reviewer: confirm which.
- **SPheno compile time.** 5–15 min guess. Integration test will surface actual figure.

---

## Workstream W3 — `/sarah-build`

**Dependencies:** W0, W1 (for real Wolfram smoke).
**Worktree name:** `wt-w3-sarah-build`
**Base branch:** `main` (post-wave-A merge).

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` | Full skill. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/templates/model.m` | `str.format` template for `<Name>.m`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/templates/parameters.m` | Template. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/templates/particles.m` | Template. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/templates/SPheno.m` | Template. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/scripts/render_templates.py` | Validates ModelSpec + renders templates. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/scripts/run_sarah.py` | Invokes `wolframscript`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/scripts/parse_sarah_log.py` | Log pattern → blocker parser. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/scripts/validate_spec.py` | Standalone CLI validator. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py` | Top-level driver combining render + run + parse. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/test_render_templates.py` | Golden test: `dark_su3` spec → deterministic `.m` output. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/test_parse_sarah_log.py` | Five fixtures × fatal patterns. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/test_validate_spec.py` | Schema + semantic validation cases. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/test_cache_key.py` | Cache key stability under whitespace changes (should differ; sha256 is sensitive). Version bump → new key. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/dark_su3/DarkSU3.m` | Golden expected output. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/dark_su3/parameters.m` | Golden. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/dark_su3/particles.m` | Golden. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/goldens/dark_su3/SPheno.m` | Golden. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/fixtures/log_anomaly.txt` | SARAH log with anomaly failure. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/fixtures/log_undefined_field.txt` | Log with "field X undefined". |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/fixtures/log_missing_output.txt` | Log ending cleanly but no UFO dir. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/fixtures/log_warnings_only.txt` | Warnings but success. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/tests/fixtures/log_success.txt` | Clean success log. |

### Detailed work items

1. **Day-1 probe (BEFORE any other work).** On a machine with W1 merged and SARAH installed, run:
   ```
   wolframscript -code 'AppendTo[$Path, "<sarah_path>/.."]; <<SARAH`; Start["SM"]; Print[ModelName]'
   ```
   Verify that `Start["DarkSU3"]` canonicalization matches `sarah-name.py`'s output. If not, patch `sarah-name.py` in a separate tiny commit that touches only `_shared/sarah-name.py` and `_shared/tests/test_sarah_name.py`. Record findings in a note appended to `plugins/hep-ph-toolkit/SHARED-model-building.md`.
2. **Write `scripts/validate_spec.py`.** CLI: `python3 validate_spec.py <spec.yaml>`. Validates against `_shared/modelspec.schema.json` via `jsonschema`. Semantic checks: (a) all names in `fermions`/`scalars`/`parameters` are unique; (b) every `gauge_groups[].symbol` referenced in `fermions[].reps` exists; (c) `hypercharge` integer or half-integer ×2 (i.e., numerator of rational with small denominator — catch typos like `0.33333`); (d) `outputs` non-empty. Exit 0 on valid, 1 with JSON blocker on invalid.
3. **Write `scripts/render_templates.py`.** Function `render(spec: dict, out_dir: Path) -> None`. Uses `sarah-name.py` for canonicalization. Pre-joins lists (gauge groups → `{"B, GaugeAbelian,...},\n{WB, GaugeNonAbelian,...}`) and passes as strings to `str.format`. Writes `out_dir/{<Name>.m, parameters.m, particles.m, SPheno.m}`.
4. **Write the four templates (`.m` files with `{placeholder}` tokens).** Tokens allowed: `{name}`, `{gauge_group_block}`, `{fermion_block}`, `{scalar_block}`, `{parameter_block}`, `{mass_term_block}`, `{yukawa_block}`, `{scalar_potential_block}`. No conditionals, no loops — pre-joined by Python. Reference the SM template shipped with SARAH for structure.
5. **Write `scripts/run_sarah.py`.** Function `run(spec_path: Path, model_dir: Path, force: bool=False) -> dict`. Steps:
   - Compute cache key: `sha256(spec.yaml bytes) + config.sarah_version`.
   - If `model_dir/.sarah_build_key` matches AND `model_dir/sarah_output/UFO/<Name>/` exists: return `{"status":"cached"}` unless `force`.
   - Render templates into `model_dir/sarah/`.
   - Build command:
     ```python
     cmd = [
       config["wolfram_engine_path"], "-code",
       f'AppendTo[$Path, "{config["sarah_path"]}/.."]; '
       f'<<SARAH`; '
       f'Start["{sarah_name}"]; '
       f'CheckModel[];'
       + "".join(f'Make{o.upper()}[];' for o in spec["outputs"])
     ]
     ```
     Note: `sarah_path` points to dir containing `SARAH.m`; SARAH wants its parent in `$Path`. Match existing `install_sarah.sh:32` convention.
   - stdout → `model_dir/sarah_output/sarah.log`.
   - Parse log via `parse_sarah_log.py`. On fatal pattern match → emit blocker, don't update cache key.
   - Validate `sarah_output/UFO/<Name>/` exists, else emit `SARAH_OUTPUT_MISSING` blocker.
   - Write cache key; create `model_dir/ufo` symlink → `sarah_output/UFO/<Name>/`.
   - Return status dict.
6. **Write `scripts/parse_sarah_log.py`.** Function `parse(log_text: str) -> list[dict]`. Pattern table (spec §4):
   - `r"Anomalies are not cancelled"` → `ANOMALY_CANCELLATION_FAILED` (fatal) with coefficients extracted from nearby lines.
   - `r"Error:\s+field\s+(\w+)\s+undefined"` → `MODELSPEC_INVALID` (fatal), captured field name in context.
   - `r"Warning:"` → collected as non-fatal warnings (not blockers).
7. **Write `scripts/build.py`.** Top-level CLI: `python3 build.py <spec.yaml> [--force]`. Reads `spec.yaml`, derives `model_dir = ~/.local/share/hep-ph-agents/models/<name>/`, copies spec to `model_dir/spec.yaml`, calls `render_templates.render`, calls `run_sarah.run`, calls `config_helpers.register_model(name, spec=..., ufo=..., sarah_built_at=...)`. Returns JSON status.
8. **Write golden tests.** `test_render_templates.py` runs render on `dark_su3_spec.yaml` fixture, compares byte-for-byte to `tests/goldens/dark_su3/*.m`. Any template change requires regenerating goldens with reviewer approval.
9. **Write `test_parse_sarah_log.py`** with five fixtures (anomaly, undefined field, missing output, warnings-only, success). Each asserts correct blocker code + mode.
10. **Write `test_validate_spec.py`.** Negative cases: duplicate fermion names; `reps` references unknown gauge group; bad hypercharge; empty `outputs`.
11. **Write `test_cache_key.py`.** Unit test: same spec → same key. Whitespace edit → different key. Version bump → different key.

### Acceptance criteria

- `python3 validate_spec.py tests/fixtures/dark_su3_spec.yaml` exits 0.
- `python3 build.py tests/fixtures/dark_su3_spec.yaml` on a machine with W1 merged produces `~/.local/share/hep-ph-agents/models/dark_su3/sarah_output/UFO/DarkSU3/` AND `.../sarah_output/SPheno/DarkSU3/` within ~5 minutes.
- `mg5_aMC` launched with a script file containing `import model <ufo_path>; display particles; exit` exits 0 (per Phase 1 Issue 12 — script file, not `-c`).
- Golden templates render byte-for-byte for `dark_su3`.
- Non-anomaly-free test spec → `ANOMALY_CANCELLATION_FAILED` fatal blocker with coefficients in `context`.
- Re-running `build.py` with unchanged spec completes in ≤5 s (cache hit; per Phase 1 §2 W3). `--force` invalidates cache.
- `config.models["dark_su3"]` populated with `spec`, `ufo`, `sarah_built_at`.

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_render_templates.py` | unit (golden) | no |
| `test_parse_sarah_log.py` | unit | no |
| `test_validate_spec.py` | unit | no |
| `test_cache_key.py` | unit | no |
| `build.py dark_su3` end-to-end | integration | **yes — SARAH + Wolfram** |
| UFO imports into MG5 | integration smoke | **yes — MG5** |

### Dependencies

- **Reads:** W0 `modelspec.schema.json`, `blocker.schema.json`, `sarah-name.py`, `config_helpers.py`, fixtures. W1 install artifacts (`sarah_path`, `wolfram_engine_path` in config).
- **Writes:** `config.models[<name>].spec`, `.ufo`, `.sarah_built_at`. Per-model state under `~/.local/share/hep-ph-agents/models/<name>/`. SARAH output tree consumed by W4.

### Risks / open questions

- **SARAH name canonicalization.** Day-1 probe (item 1). Could reveal the provisional rule is wrong for edge cases like `2hdm` (rejected by regex anyway) or mixed-case inputs. If the probe reveals a SARAH convention we didn't anticipate (e.g., "first char uppercase, rest as-written"), the reviewer needs to weigh in before template work proceeds.
- **UFO ↔ MG5 3.5.6 compat.** Not independently verified. Integration smoke is the test of record.
- **Golden test brittleness.** Byte-for-byte goldens on `.m` templates will churn with every template tweak. Mitigation: goldens live in their own dir, reviewer-blessed diffs go through PR review.
- **Where `sarah-output` goes during cache miss.** I write to `model_dir/sarah_output/` directly (not a tmpfile). On failure, partial output remains — fine for debugging, but means `cached` detection must verify UFO dir exists, not just that the dir is nonempty.

---

## Workstream W4 — `/spheno-build`

**Dependencies:** W0, W2 (for real SPheno base). W3 output tree structure known from spec, but early W4 dev uses committed fixtures.
**Worktree name:** `wt-w4-spheno-build`
**Base branch:** `main` (post-wave-A merge).
**Re-integration step:** after W3 merges, manager re-dispatches W4 integration run against *real* SARAH output. Planned; not glossed.

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` | Full skill. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/run_spheno.py` | Compile + run + summary stages. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/compile_model.py` | Stage 1 — idempotent compile with cache. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/run_point.py` | Stage 2 — single LesHouches run. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/parse_slha.py` | SLHA → summary.json. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/leshouches_template.py` | Generates `MODSEL`/`SMINPUTS`/`MINPAR`/`SPHENOINPUT` blocks. Explicit enumeration per spec §5. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/scripts/scan.py` | Sequential scan driver. Factored to allow v2 parallelism. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/fixtures/sarah_output_darksu3.tar.gz` | Gzipped minimal SARAH output fixture. Hard cap 2 MB compressed. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/fixtures/spheno_spc_clean.spc` | Canned clean SLHA spectrum. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/fixtures/spheno_spc_problem.spc` | SLHA with `Block PROBLEM 1`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/fixtures/spheno_spc_rge.spc` | SLHA with `Block SPINFO 4`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/fixtures/spheno_spc_missing.spc` | No `Block MASS` — simulates no-output path. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/test_parse_slha.py` | Parser unit tests. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/test_leshouches_template.py` | MINPAR correctness with `--params` patch. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/test_scan_expansion.py` | Unit test of scan grid expansion (`100:1000:step=100` × `0.5:2.5:step=0.5` → 45 points). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/tests/test_compile_cache.py` | Cache key stability (unit; doesn't invoke make). |

### Detailed work items

1. **Write `scripts/parse_slha.py`.** `parse(spc_path: Path) -> dict` extracts:
   - `masses` — `Block MASS` entries: `{pdg_id: mass_gev}`.
   - `widths` — `DECAY` entries: `{pdg_id: width_gev}`.
   - `problems` — `Block PROBLEM` codes (list of int).
   - `mixing` — `Block NMIX`, `Block UMIX`, etc., keyed by block name.
   - Also reads `Block SPINFO` for RGE non-convergent flag.
   Return dict written to `runs/<TS>/summary.json`.
2. **Write `scripts/leshouches_template.py`.** Given `spec: dict`, produces a LesHouches input string. Explicit block enumeration:
   - `Block MODSEL` — SUSY=0 for v1 (non-SUSY models only).
   - `Block SMINPUTS` — PDG defaults (hardcoded table: alpha_em, G_F, alpha_s(MZ), MZ, m_b(m_b), m_t, m_tau).
   - `Block MINPAR` — one row per `spec.parameters`, using `default`, in declaration order (index 1..N).
   - `Block SPHENOINPUT` — copied verbatim from `sarah_output/SPheno/<Model>/Input_Files/LesHouches.in.<Model>.

   `patch_minpar(text, params: dict)` — replace values in `Block MINPAR` by name-lookup from spec.
3. **Write `scripts/compile_model.py`.** Algorithm:
   - `spheno_src = config["spheno_src_path"]`; `model = sarah_name(spec["name"])`.
   - Compute cache key: `sha256(spec.yaml) + sarah_version + spheno_version`.
   - If `model_dir/spheno_bin/.build_key` matches AND `model_dir/spheno_bin/SPheno<Model>` exists → cached, return.
   - Copy `model_dir/sarah_output/SPheno/<Model>/` into `$spheno_src/<Model>/`.
   - `make -C $spheno_src Model=<Model> -j$(python3 -c 'import os;print(os.cpu_count())')`.
   - Capture stdout+stderr to `model_dir/spheno_bin/make.log`.
   - If nonzero exit OR `$spheno_src/bin/SPheno<Model>` missing → `SPHENO_COMPILE_FAILED` blocker (fatal), tail 40 lines into context.
   - Move binary into `model_dir/spheno_bin/SPheno<Model>`. Write cache key.
4. **Write `scripts/run_point.py`.** `run(model_name, input_card_path, out_dir) -> dict`. Exact invocation (per Phase 1 §2 W4 / spec §5):
   ```
   $MODEL_DIR/spheno_bin/SPheno$MODEL  $out_dir/LesHouches.in  $out_dir/SPheno.spc
   ```
   Two positional args. No redirection. On return:
   - Exit nonzero or `SPheno.spc` absent → `SPHENO_NO_OUTPUT` (fatal).
   - `Block PROBLEM` codes 1/2/3 → `SPHENO_SPECTRUM_PROBLEM` (recoverable).
   - `Block SPINFO 4` → `SPHENO_RGE_NONCONVERGENT` (recoverable).
   - Else clean → parse via `parse_slha.py`, write `summary.json`.
5. **Write `scripts/scan.py`.** `scan(model, axes: list[tuple[str, start, stop, step]]) -> path`. Cartesian product. Single-threaded loop (factor `scan_worker(point, workdir)` out so v2 can wrap with `ProcessPoolExecutor`). Writes:
   - `runs/scan_<TS>/scan_index.csv` — columns: `index, <param1>, <param2>, ..., status, blocker_code, slha_path`.
   - `runs/scan_<TS>/LesHouches.in.NNNN`, `SPheno.spc.NNNN`.
   Recoverable blockers marked in `status` but scan continues. Fatal on any single point aborts only if exit != 0 (SPheno crash, not physics issue).
6. **Write `scripts/run_spheno.py`.** Top-level CLI wrapping the three stages:
   - `python3 run_spheno.py <model_name> [--params k=v,...] [--input-card path] [--scan name=start:stop:step=s]...` (scan repeatable).
   - If `--input-card` → use verbatim (no templating).
   - Else templated from ModelSpec + `--params` patch.
   - Without `--scan` → single run; with `--scan` → delegate to `scan.py`.
   - Registers `config.models[<name>].spheno_bin`, `.latest_slha`, `.latest_run`, `.spheno_built_at`.
7. **Write `tests/fixtures/sarah_output_darksu3.tar.gz`.** Created on the first real W3 integration run. Pre-W3-merge, the committer produces a *placeholder* fixture — a minimal tree with just the Fortran sources that `make Model=DarkSU3` needs, small enough to compile. 2 MB cap. After W3 merges, manager's re-dispatch step regenerates it from real output.
8. **Write `test_parse_slha.py`.** One test per fixture. Asserts dict shape matches expected.
9. **Write `test_leshouches_template.py`.** Asserts `Block MINPAR` order matches spec declaration order. Asserts `patch_minpar` replaces by name lookup.
10. **Write `test_scan_expansion.py`.** Parse `MpsiD=200:1000:step=100` → 9 values. Parse `gD=0.5:2.5:step=0.5` → 5 values. Cartesian → 45.
11. **Write `test_compile_cache.py`.** Same inputs → same cache key. Version bump → different.
12. **Write `SKILL.md`.** Structure per spec §5: compile stage, run stage, scan, recoverable-failure contract, LesHouches generation.

### Acceptance criteria

- `python3 parse_slha.py tests/fixtures/spheno_spc_clean.spc` prints `summary.json` matching expected.
- `python3 parse_slha.py tests/fixtures/spheno_spc_problem.spc` flags `problems=[1]`.
- `python3 parse_slha.py tests/fixtures/spheno_spc_rge.spc` flags SPINFO 4.
- `python3 run_spheno.py dark_su3 --params MpsiD=300` with real SARAH+SPheno produces `runs/<TS>/SPheno.spc` with `MpsiD=300` reflected in `Block MINPAR`.
- `python3 run_spheno.py dark_su3 --input-card my.dat` uses the file verbatim (diff `my.dat` vs `runs/<TS>/LesHouches.in` → identical).
- `python3 run_spheno.py dark_su3 --scan MpsiD=200:1000:step=100 --scan gD=0.5:2.5:step=0.5` writes `runs/scan_<TS>/scan_index.csv` with 45 rows. At least one row should naturally mark `status=recoverable` (high `MpsiD` tends to trip `Block PROBLEM` in toy models — confirm empirically).
- Rerunning compile with unchanged inputs skips in ≤2 s (cache hit).
- `--force` on compile bypasses cache.
- `config.models["dark_su3"].spheno_bin`, `.latest_slha`, `.latest_run` populated after a successful single run.

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_parse_slha.py` | unit | no |
| `test_leshouches_template.py` | unit | no |
| `test_scan_expansion.py` | unit | no |
| `test_compile_cache.py` | unit | no |
| Compile against committed fixture | integration | **yes — gfortran + SPheno base (W2)** |
| Full single-point run | integration | **yes** |
| 45-point scan | integration | **yes — minutes** |
| Re-dispatch against real W3 output | integration | **yes — after W3 merges** |

### Dependencies

- **Reads:** W0 `blocker.schema.json`, `config_helpers.py`, `sarah-name.py`, fixtures. W2 `spheno_src_path`. W3 SARAH output tree at `model_dir/sarah_output/SPheno/<Model>/`.
- **Writes:** `config.models[<name>].spheno_bin`, `.latest_slha`, `.latest_run`, `.spheno_built_at`. Per-model spheno binary, run outputs.

### Risks / open questions

- **Committed fixture drift.** Even capped at 2 MB compressed, a pre-W3 fixture committed to W4's worktree will silently drift when W3 regenerates. The re-dispatch step mitigates; reviewer may prefer blocking W4 on W3 entirely (serial wave-B). Phase 1 §6 step 4 permits parallel with explicit re-dispatch — I follow that.
- **Scan status semantics.** I call `recoverable` those points with `Block PROBLEM 1/2/3` or `SPINFO 4`. Spec §5 and Phase 1 §2 agree. Reviewer: should a scan row with both fatal (SPheno crash) and recoverable markers abort or continue? I propose: abort *only* on SPheno crash (exit != 0 with no `.spc`), continue on all physics problems.
- **"At least one recoverable row" acceptance.** I claim empirically that the `MpsiD=200:1000 × gD=0.5:2.5` grid will naturally produce one. If not, we weaken to "test passes regardless of count." Reviewer flag.

---

## Workstream W5 — `/lagrangian-builder` (orchestrator rewrite)

**Dependencies:** W0, W1, W2, W3, W4, W6.
**Worktree name:** `wt-w5-lagrangian-builder`
**Base branch:** `main` (post-wave-B merge).

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` | Rewrite as orchestrator. SKILL.md-driven, not a script state machine. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/references/interview.md` | Interview script (natural language → ModelSpec). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/references/orchestration.md` | Detailed flow: check_state → install-if-missing → build → register. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/references/anomaly-ledger.md` | How to read SARAH's anomaly report; how to surface to user. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/dark_su3.yaml` | Reference ModelSpec. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/singlet_doublet.yaml` | Reference ModelSpec. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/assets/modelspec-templates/2hdm.yaml` | Reference ModelSpec (named `two_hdm` to satisfy regex). |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/check_state.py` | Small status probe. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/scripts/register_model.py` | Writes `config.models[<name>]` via W0 helper. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/tests/integration/dark_su3_e2e.sh` | Cold-config → built `dark_su3` → MG5-ready. Network-gated. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/tests/test_check_state.py` | Unit test of `check_state.py` with mocked config. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/tests/test_register_model.py` | Unit test of `register_model.py`. |

### Detailed work items

1. **Write `check_state.py`.** Pure-Python. Reads config via W0 `config_helpers.load_config()`. Returns to stdout as JSON:
   ```json
   {
     "sarah_install": "configured|missing",
     "spheno_install": "configured|missing",
     "wolfram_install": "configured|missing",
     "model": {"status":"present|missing", "name":"dark_su3"}
   }
   ```
   CLI: `python3 check_state.py [--model <name>]`. This is a probe, not an orchestrator.
2. **Write `register_model.py`.** Single side-effect: `config_helpers.register_model(name, spec=..., ufo=..., latest_slha=..., spheno_bin=..., sarah_built_at=..., spheno_built_at=...)`. CLI: `python3 register_model.py <name> --spec <path> --ufo <path> [--latest-slha <path>] ...`.
3. **Write `SKILL.md`.** Structure (the heart of the workstream):
   ```
   ## When to invoke
   ## Overview
   ## Step 1: Check state (→ `scripts/check_state.py`)
   ## Step 2: Interview user (→ `references/interview.md`)
   ## Step 3: Propose and validate ModelSpec
   ## Step 4: Sequence installs + builds
       - If `sarah_install=missing`, invoke `/sarah-install`. If it returns `activation_required`, pause with exact user_instruction and stop.
       - Invoke `/sarah-build <spec.yaml>`.
       - If `spheno_install=missing`, invoke `/spheno-install`.
       - Invoke `/spheno-build <name>`.
   ## Step 5: Register model (→ `scripts/register_model.py`)
   ## Step 6: Report paths and next steps ("/madgraph use <name>")
   ## Recoverable outcomes
   ## Fatal outcomes
   ```
   Critical note: no step is a script. Each step is an instruction to Claude to invoke a named tool (other skill, python script, or prompt).
4. **Write `references/interview.md`.** Prompts for gauge group selection, fermion content, scalar content, mass terms. Outputs a draft ModelSpec YAML for user review.
5. **Write `references/orchestration.md`.** The complete state diagram, in prose. Entry points, skip conditions (detected installs), exit conditions (registered model, or paused on activation_required, or fatal blocker surfaced). Cite PR-D three-state contract.
6. **Write `references/anomaly-ledger.md`.** How to read `ANOMALY_CANCELLATION_FAILED` blocker, present the coefficients to the user, propose schema fixes (different hypercharge, extra fermion). Not a physics textbook — operational guide.
7. **Write `assets/modelspec-templates/{dark_su3,singlet_doublet,two_hdm}.yaml`.** Each ≤50 lines, all passing `validate_spec.py`.
8. **Write `tests/integration/dark_su3_e2e.sh`.** Script wipes `~/.config/hep-ph-agents/config.json.bak` if exists, backs up real config, starts from cold:
   - Runs `/sarah-install` (skip if already configured via hep-ph-demo).
   - Runs `/spheno-install` (same).
   - Runs W3 build on `dark_su3.yaml`.
   - Runs W4 build.
   - Asserts `config.models.dark_su3.ufo` and `.latest_slha` exist and files on disk.
   - Times: cold <15 min (per Phase 1), cache hit <3 min.
   - Restores config.
   Network-gated (skip if `NO_NETWORK=1`).
9. **Write `test_check_state.py`.** Mocked config files → correct JSON shape.
10. **Write `test_register_model.py`.** Tmpfile config → after register, `models[<name>]` populated correctly.

### Acceptance criteria

- E2E on `dark_su3` from cold cache: first run <15 min on reference hardware (M-series / Linux dev box). Rerun with cache <3 min.
- `activation_required` from `/sarah-install` surfaces as a pause with the exact instruction string from spec §3. User runs `wolframscript --activate`, reruns orchestrator, flow resumes.
- Any `fatal` blocker surfaces with the full `blocker.schema.json` JSON and stops the flow.
- After successful E2E, `/madgraph use dark_su3` (W6) resolves to the correct UFO + latest SLHA and imports cleanly into MG5.
- `SKILL.md` under 400 lines. References carry the weight.
- No script in `scripts/` exceeds 80 lines. Anything longer should be decomposed or moved to a proper skill.

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_check_state.py` | unit | no |
| `test_register_model.py` | unit | no |
| `dark_su3_e2e.sh` | integration | **yes — full chain** |

### Dependencies

- **Reads:** EVERYTHING. All other workstreams' outputs. W0 helpers.
- **Writes:** Invokes other skills. Registers model. Updates `config.models[<name>]`.

### Risks / open questions

- **SKILL.md-driven orchestration limits.** If a downstream skill returns a nonstandard status shape, SKILL.md has no way to react beyond "ask Claude to interpret." This is the point (augment-not-replace) but may bite us on error paths. Reviewer: confirm the approach.
- **Interview prompt quality.** `interview.md` is Claude-readable, not user-facing UX. Quality is hard to test. Reviewer may want to reference an existing skill interview as a model.

---

## Workstream W6 — `/madgraph` named-model resolver

**Dependencies:** W0 (config schema).
**Worktree name:** `wt-w6-madgraph-resolver`
**Base branch:** `main` (post-W0 merge). Runs in parallel with W3, W4.

### Files to create / modify

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/SKILL.md` | Insert "Named model resolution" subsection at top of Decision Tree. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/references/generation.md` | 10-line callout on `/madgraph use <name>`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/scripts/resolve_named_model.py` | CLI resolver. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/tests/test_resolve_named_model.py` | Unit test. |

### Detailed work items

1. **Write `resolve_named_model.py`.** CLI: `python3 resolve_named_model.py <name> --key {ufo,latest_slha,spheno_bin}`. Reads `config.models[<name>]`, prints the requested path to stdout. Exit 0 if found, 1 if model missing, 2 if key missing. ~30 lines.
2. **Edit `SKILL.md` Decision Tree.** Insert new section before "Install or configure MG5?":
   ```
   ### Using a named hep-ph-agents model?
   If the user says `use <name>` or `--model <name>`, resolve paths first:
     UFO    = python3 scripts/resolve_named_model.py <name> --key ufo
     SLHA   = python3 scripts/resolve_named_model.py <name> --key latest_slha
   Then write MG5 commands:
     import model <UFO>
     ... generate ... output ...
     launch (substitute <SLHA> for param_card on prompt)
   ```
3. **Edit `references/generation.md`.** Add a "Named-model handoff" callout (10 lines) at the end, pointing back to SKILL.md.
4. **Write `test_resolve_named_model.py`.** Tmpfile config with `models.dark_su3.ufo=/tmp/ufo_dummy`. Asserts stdout is the exact path.
5. **Smoke test with MG5.** On a machine with MG5 installed: run `mg5_aMC <script_file>` where the script contains `import model $(python3 resolve_named_model.py dark_su3 --key ufo); generate p p > psiD psiD~; output /tmp/test_out; exit`. Expect clean exit. Key point per Phase 1 Issue 12: MG5 takes a script file positional argument, not `-c`.

### Acceptance criteria

- `python3 resolve_named_model.py dark_su3 --key ufo` with `config.models.dark_su3.ufo=/path/to/ufo` prints exactly `/path/to/ufo`. Exit 0.
- Missing model → exit 1, error on stderr.
- MG5 script-file invocation with resolved UFO path exits 0 (after W3 produces a real UFO).

### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_resolve_named_model.py` | unit | no |
| MG5 script-file smoke | integration | **yes — MG5 + W3 UFO** |

### Dependencies

- **Reads:** W0 `config_helpers.py` (optional — may inline small read, since W6 lives under `monte-carlo-tools/`, not `model-building/`).
- **Writes:** nothing.

### Risks / open questions

- **Cross-plugin import.** If `resolve_named_model.py` imports from `plugins/hep-ph-toolkit/skills/_shared/config_helpers.py`, cross-plugin coupling emerges. Alternative: inline 15-line config read. Reviewer decide; I slightly favor inlining for isolation.
- **MG5 invocation form.** Phase 1 §8 Issue 12 says `mg5_aMC <script_file>`, not `-c`. Our smoke test must use this. Planning phase should double-check by reading existing `plugins/hep-ph-toolkit/skills/madgraph/` scripts or `eval/` examples — `mg5_batch.py` may already show the idiom.

---

## Cross-cutting sections

### Dispatch plan for Phase 3

**Round 0 (synchronous on `main`):**
- `wt-w0-shared-contracts` — implementer brief: "Execute W0 per `phase2-plan-final.md` §W0. Order: promote `_common.sh`, write schemas and helpers, write stubs, update `plugin.json`, write tests. Run regression gate on `install.sh detect-all`." First review focus: does `_common.sh` shim break hep-ph-demo? Does `modelspec.schema.json` accept the `dark_su3` example? Are the four stub SKILL.md files syntactically valid?
- Acceptance gate: all W0 acceptance criteria pass; `install.sh detect-all` shows no diff; merge to `main`.

**Round A (parallel, post-W0 merge):**
- `wt-w1-sarah-install` — brief: "Execute W1 per plan. Port `install_sarah.sh` from hep-ph-demo, source shared `_common.sh`, add `check_wolfram_activation.sh`, emit `activation_required` as *status*, not blocker. Run Day-1 probe for activation prompt on unactivated Wolfram. Write tests under `sarah-install/tests/`."
- `wt-w2-spheno-install` — brief: "Execute W2 per plan. Port `install_spheno.sh`, add dual `spheno_path` + `spheno_src_path` writes. Detect-and-reuse hep-ph-demo install must derive `spheno_src_path`. Write tests."
- First review focus (both): config-key parity with hep-ph-demo; blocker JSON shape; detect-and-reuse path.
- Acceptance gate: acceptance criteria pass; Day-1 probes run on real hardware; merge independent.

**Round B (parallel, post-Round-A merge):**
- `wt-w3-sarah-build` — brief: "Execute W3 per plan. Day-1 probe for SARAH name canonicalization FIRST. Then render templates, run SARAH, parse log, write tests and goldens. Any canonicalization fix is a one-commit amend to `_shared/sarah-name.py`."
- `wt-w4-spheno-build` — brief: "Execute W4 per plan. Use committed SARAH-output fixture for pre-W3 dev; after W3 merges, manager re-dispatches integration run. Implement compile cache, run, scan, SLHA parser. Emit recoverable blockers per contract."
- `wt-w6-madgraph-resolver` — brief: "Execute W6 per plan. Small resolver + SKILL.md edit + generation.md edit + test. Smoke test against real UFO (may wait for W3)."
- First review focus (W3): SARAH name probe result; template `str.format` discipline (no conditionals); cache key. (W4): SLHA parser correctness; MINPAR patch; recoverable blocker contract. (W6): MG5 script-file form; cross-plugin coupling.
- Acceptance gate: acceptance criteria pass; W4 re-dispatch after W3 merge; merge in order W3 → W6 → W4 (to let W4 re-integration land last).

**Round C (synchronous, post-Round-B merge):**
- `wt-w5-lagrangian-builder` — brief: "Execute W5 per plan. SKILL.md-driven orchestrator, two tiny Python helpers. Full E2E `dark_su3` cold run is the gate."
- First review focus: SKILL.md readability; E2E success; activation-pause handling; no orchestration logic hidden in Python.
- Acceptance gate: E2E passes cold and hot; activation pause works correctly; merge.

**Declaring "done":**
- Per-workstream: all acceptance criteria in the workstream's §Acceptance pass, reviewer approves, Day-1 probes complete (if applicable), merged to `main` via local merge (no remote push unless explicitly requested).
- Whole-project: all six workstreams merged; `dark_su3_e2e.sh` passes; top-level README lists `/lagrangian-builder` → `/madgraph` flow.

### Merge procedure

Per workstream, once acceptance passes:

```
# From the worktree dir
cd <worktree-path>
git fetch origin
git rebase origin/main         # if main has moved
# resolve any rebase conflicts (rare — see conflict policy below)
git push origin <branch-name>  # only if user requested remote
# Manager side:
cd /Users/yianni/Projects/hep-ph-agents
git fetch
git checkout main
git merge --ff-only <branch-name>  # prefer ff; if not possible, inspect
```

If ff-only fails:
```
git merge --no-ff <branch-name>  # create merge commit, only after reviewing git log
```

**Cleanup:**
```
git worktree remove <worktree-path>  # only after merge verified on main
git branch -d <branch-name>
```

**Conflict policy (shared files):**

The only files any two workstreams both plausibly touch are:
- `plugins/hep-ph-toolkit/SHARED-model-building.md` (W0 writes; W3 may amend its SARAH-name probe result)
- `plugins/model-building/.claude-plugin/plugin.json` (W0 only — explicit invariant)
- `plugins/shared/install-helpers/_common.sh` (W0 only — explicit invariant)

If a rebase conflict arises in `SHARED.md`:
1. Open in editor. Merge both changes manually (they should be additive).
2. `git add plugins/hep-ph-toolkit/SHARED-model-building.md`.
3. `git rebase --continue`.
4. Re-run any test that depends on SHARED.md conventions.

If a conflict arises in `plugin.json`: only W0 should be editing it; anyone else hitting a conflict here has violated an invariant. Stop and escalate to manager.

If a conflict arises in `_common.sh`: same — W0-only invariant. Stop and escalate.

If a conflict arises in a per-skill dir that supposedly only one workstream owns: something has gone wrong with worktree hygiene. Escalate.

### Day-1 probes

Probes that require running real tools, per Phase 1 §7. Each assigned to a specific workstream with clear owner and gate:

| Probe | Workstream | When | Owner | Blocks what |
|---|---|---|---|---|
| SARAH name canonicalization vs `sarah-name.py` | W3 | First task in W3, before templates | W3 implementer | All W3 template work |
| Wolfram activation prompt string exact content | W1 | Before final test fixture commit | W1 implementer | `check_wolfram_activation.sh` grep patterns |
| SPheno base compile time on reference macOS | W2 | First install run | W2 implementer | None (informational) |
| SARAH UFO 4.15.3 ↔ MG5 3.5.6 compatibility | W3 → W6 | After W3 first successful build | W3 implementer, W6 reviewer | W6 acceptance |
| `mg5_aMC` script-file vs `-c` invocation form | W6 | Before writing the resolver smoke test | W6 implementer | W6 smoke test |
| Fixture tree size for `sarah_output_darksu3/` | W4 | After committing placeholder; after W3 re-dispatch | W4 implementer | Repo hygiene (hard cap 2 MB gzipped) |

### Config migration plan

**No migration.** Per Phase 1 §8 Issue 1 resolution: adopt existing hep-ph-demo keys as-is.

Concrete statements for planners who may second-guess:
- `wolfram_engine_path`, `wolfram_engine_version` — existing; used as-is.
- `sarah_path` (points to SARAH package dir containing `SARAH.m`, e.g. `$HOME/SARAH/SARAH-4.15.3`) — existing; used as-is. **Do NOT relocate to `~/.local/share/hep-ph-agents/sarah/`.** The relocation in spec §1 is abandoned.
- `sarah_version`, `sarah_installed_at` — existing / amended (`installed_at` may be new in hep-ph-demo but same shape).
- `spheno_path` (binary) — existing; preserved.
- `spheno_src_path` — **new. Only net-new top-level key this workstream introduces.**
- `spheno_version`, `spheno_installed_at` — as SARAH.
- `models: {}` — new nested key. Always present post-migration; `config-migration.py` ensures it.
- `madgraph_path`, `madgraph_version`, `python`, `last_configured` — unchanged.

`config-migration.py` exists to assert this and to add `models: {}` if missing. It is not a rename tool.

---

## Summary (for implementers)

| ID | Name | Depends on | Worktree |
|---|---|---|---|
| W0 | Shared contracts + config migration | — | `wt-w0-shared-contracts` |
| W1 | `/sarah-install` | W0 | `wt-w1-sarah-install` |
| W2 | `/spheno-install` | W0 | `wt-w2-spheno-install` |
| W3 | `/sarah-build` | W0, W1 | `wt-w3-sarah-build` |
| W4 | `/spheno-build` | W0, W2, W3 (for re-integration) | `wt-w4-spheno-build` |
| W5 | `/lagrangian-builder` | W0–W4, W6 | `wt-w5-lagrangian-builder` |
| W6 | `/madgraph` resolver | W0 | `wt-w6-madgraph-resolver` |

Waves: W0 → {W1,W2} → {W3,W4,W6} (with W4 re-dispatch after W3) → {W5}.

Touchpoint invariants (no two workstreams should both edit these):
- `plugins/shared/install-helpers/_common.sh` — W0 only.
- `plugins/model-building/.claude-plugin/plugin.json` — W0 only.
- `plugins/hep-ph-toolkit/SHARED-model-building.md` — W0 primary, W3 may amend (probe result only).
- `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` — W0 only (shim).

When in doubt, this plan is binding; spec is the upstream source; Phase 1 strategy is the tiebreaker on disputes between spec and this plan.
