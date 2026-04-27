# Phase 2 — Implementation Plan (Final / Synthesizer)

**Status:** authoritative. Phase 3 coding agents execute directly from this document.
**Upstream references (do not duplicate):**
- Spec: `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
- Phase 1 strategy: `docs/superpowers/workstream-sarah-spheno/phase1-final.md`
- Drafter: `docs/superpowers/workstream-sarah-spheno/phase2-plan-draft.md`
- Reviewer: `docs/superpowers/workstream-sarah-spheno/phase2-review.md`
- Precedent scripts: `plugins/hep-ph-toolkit/skills/install/scripts/`

---

## 1. Executive summary

Seven workstreams: W0 (shared contracts + config migration), W1 (`/sarah-install`), W2 (`/spheno-install`), W3 (`/sarah-build`), W4 (`/spheno-build`), W5 (`/lagrangian-builder` orchestrator rewrite), W6 (`/madgraph` named-model resolver patch).

**Dispatch waves.**
- Round 0 (solo): W0 lands synchronously on `main` before any downstream worktree spawns.
- Round A (parallel): W1 + W2 from post-W0 `main`. Independent; either merges first.
- Round B (parallel): W3 + W4 + W6 from post-Round-A `main`. W4 develops against a committed placeholder fixture pre-W3; after W3 merges the manager re-dispatches W4's integration run against a regenerated fixture (explicit numbered checklist in §5). Merge order: W3 first, then W6 and W4 in either order.
- Round C (solo): W5 depends on everything. Its E2E on `dark_su3` is the project gate.

**Merge discipline.** Manager (this session's operator) is the sole writer on `main`. Only one ff-merge at a time. W0 is the exclusive owner of three shared files across the whole project: `plugins/model-building/.claude-plugin/plugin.json`, `plugins/shared/install-helpers/_common.sh`, and `plugins/shared/install-helpers/config_helpers.py`. `SHARED.md` is W0-primary with a reserved single-section appendix for W3's canonicalization-probe result.

**Biggest risks.**
1. SARAH name canonicalization: unverifiable without running SARAH. W3 Day-1 probe is the first task in W3; if the rule diverges, W0's provisional `sarah-name.py` is amended in a one-commit patch touching only `_shared/sarah-name.py` + its test.
2. Wolfram activation prompt string: unknown. W1 Day-1 probe pins the grep patterns; fixtures are captured before tests are finalized.
3. Cross-worktree state leak: a single shared `~/.config/hep-ph-agents/config.json` would corrupt parallel test runs. Global invariant (§2): every test shell sets `HEPPH_STATE_ROOT` and `XDG_CONFIG_HOME` to worktree-scoped tmpdirs.
4. Placeholder `spheno_sha256: TODO` — the shared `_common.sh::verify_checksum` already warns-not-aborts for TODO; we adopt that. Before v1 release we compute real checksums.
5. W4's committed fixture may drift. Hard policy: ≤10 MB gzipped, in-repo (reviewer Major #14 resolution).

**Day-1 probes (§6).** Six concrete probes, each with an owner, a command, a success criterion, and a go/no-go consequence.

---

## 2. Global invariants

Every workstream must obey these. Documented once, not repeated per workstream.

### 2.1 Python
- Minimum Python is **3.10**. Every Python script MUST assert this at entry:
  ```python
  import sys
  assert sys.version_info >= (3, 10), "hep-ph-agents requires Python >= 3.10"
  ```
  (adopts reviewer §G / Minor 22).
- Third-party deps permitted: `jsonschema`, `pyyaml`. No others without an explicit line item in this plan.
- All Python uses stdlib where possible.

### 2.2 Bash
- All scripts start with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Scripts source the promoted `_common.sh` per the W0 pattern:
  ```bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SHARED_COMMON="$SCRIPT_DIR/../../../../shared/install-helpers/_common.sh"
  if [ ! -f "$SHARED_COMMON" ]; then SHARED_COMMON="$SCRIPT_DIR/_common.sh"; fi
  . "$SHARED_COMMON"
  ```
  (The relative depth `../../../../shared/install-helpers/` is correct for a script at `plugins/hep-ph-toolkit/skills/<skill>/scripts/`. hep-ph-demo scripts, which live at `plugins/hep-ph-toolkit/skills/install/scripts/`, use `../../../shared/install-helpers/` — three levels, not four.)

### 2.3 State and config roots (test isolation)
- Normal user state root: `~/.local/share/hep-ph-agents/` (per spec §1 §3.4 of phase1-final).
- Normal user config: `~/.config/hep-ph-agents/config.json` (existing).
- **Test override (mandatory in every test shell and CI invocation):**
  ```bash
  export HEPPH_STATE_ROOT="$(mktemp -d -t hepph-state-XXXXXX)"
  export XDG_CONFIG_HOME="$(mktemp -d -t hepph-cfg-XXXXXX)"
  ```
  `HEPPH_STATE_ROOT` overrides the per-model state root (`~/.local/share/hep-ph-agents/models/` → `$HEPPH_STATE_ROOT/models/`). `XDG_CONFIG_HOME` already respected by `_common.sh`'s `CONFIG_DIR` and must be respected by the new Python mirror. Both variables are cleaned up on test teardown.
- `config_helpers.py` computes:
  ```python
  STATE_ROOT = Path(os.environ.get("HEPPH_STATE_ROOT")
                    or Path.home() / ".local/share/hep-ph-agents")
  CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME")
                    or Path.home() / ".config") / "hep-ph-agents"
  CONFIG_PATH = CONFIG_DIR / "config.json"
  ```
- Install scripts (W1, W2) read `HEPPH_STATE_ROOT` but do NOT write there for *base tool installs*. Base tool installs stay where `/install` put them (`$HOME/SARAH`, `$HOME/SPheno`). `HEPPH_STATE_ROOT` governs `models/` only. (Phase 1 §3.4.)

### 2.4 Env-var overrides (only these are implemented)
| Variable | Purpose | Consumed by | Default |
|---|---|---|---|
| `HEPPH_STATE_ROOT` | Test-isolation for per-model state | W3, W4, W5 Python | `~/.local/share/hep-ph-agents` |
| `XDG_CONFIG_HOME` | Test-isolation for config file | all | `~/.config` |
| `HEPPH_SARAH_VERSION` | Override pinned SARAH version | W1 `install_sarah.sh` | `4.15.3` |
| `HEPPH_SPHENO_VERSION` | Override pinned SPheno version | W2 `install_spheno.sh` | `4.0.5` |
| `NO_NETWORK` | Skip integration tests that need network | W1, W2, W5 integration | unset |

`HEPPH_SARAH_VERSION` and `HEPPH_SPHENO_VERSION` are **advertised in SHARED.md and implemented** in the respective install scripts. The pattern:
```bash
SARAH_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"
```
(Adopts reviewer Major #15.)

`HEPPH_WOLFRAM_KERNEL` is NOT implemented. Drop from any mention.

### 2.5 Timestamps
UTC ISO 8601 with `Z` suffix: `%Y-%m-%dT%H:%M:%SZ`. Shell: `date -u +%Y-%m-%dT%H:%M:%SZ`. Python: `datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`.

### 2.6 Atomic config writes (fsync)
Both `_common.sh::config_merge` (bash) and `config_helpers.py::merge_config` (Python) MUST fsync the file descriptor before rename AND fsync the containing directory after rename. This fixes the pre-existing bug at `_common.sh:136-140`. (Adopts reviewer Blocker #1.)

Bash version (inside the Python heredoc at the end of `config_merge`):
```python
with open(tmp_path, "w") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")
    f.flush()
    os.fsync(f.fileno())
os.rename(tmp_path, cfg_path)
dir_fd = os.open(os.path.dirname(cfg_path), os.O_RDONLY)
try:
    os.fsync(dir_fd)
finally:
    os.close(dir_fd)
```

Python version (`config_helpers.py::merge_config`): identical pattern on the fd, rename, parent-dir fsync.

### 2.7 Three-state blocker contract
Modes are `fatal`, `recoverable`, `reference_only`. `activation_required` is a **status code returned by `/sarah-install`**, not a blocker mode. All blockers emitted on stderr conform to `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.

`reference_only` payload shape (mirrors PR-D commit `f72e19e` per reviewer Blocker #25 and judgment-call #5):
```json
{
  "status": "reference_only",
  "reference_method": "<non-empty string>",
  "caveats": ["<non-empty list>"]
}
```
The `blocker.schema.json` schema for mode `reference_only` requires `reference_method: string` and `caveats: array[string]`, both non-empty. The `code`, `message`, `context` triplet common to `fatal` / `recoverable` is **not** required for `reference_only`; the canonical shape is the one the eval harness parses.

### 2.8 `user_instruction` semantics
A single string field with one meaning everywhere: "The exact shell command or action the user must take to unblock." Used by:
- Install-skill status JSON when `status: activation_required`.
- `fatal`-mode blockers that require a user action before retry.
Present as an **optional** field on both; required when the blocker or status is caused by a user-actionable gap (Wolfram activation, missing `gfortran`, missing Homebrew, etc.). Adopts reviewer Major #16.

### 2.9 Cache keys (input-only)
- W3 cache key file: `$STATE_ROOT/models/<name>/.sarah_build_key`. Contents: single line `sha256(spec.yaml bytes hex)=` + `sarah_version`. Example: `a3f2...=4.15.3`. No output-tree hashing.
- W4 cache key file: `$STATE_ROOT/models/<name>/spheno_bin/.build_key`. Contents: `sha256(spec.yaml) + sarah_version + spheno_version` in the same format.
- Missing key file or mismatch → rebuild. `--force` forces rebuild.

### 2.10 Templates
`str.format` only. No Jinja2. Lists are pre-joined in the calling Python to a single string token before `template.format(**tokens)`. No conditionals in templates.

### 2.11 Fixture policy (reviewer Major #14, resolved)
- In-repo fixtures: gzipped tarball, hard cap **10 MB compressed**. Plain tarball rejected. git-LFS rejected.
- If a fixture would exceed 10 MB compressed, split into representative sub-fixtures (e.g., `sarah_output_darksu3_core.tar.gz` + `sarah_output_darksu3_bsm.tar.gz`). No cloud-fetch fallback.
- Tests MUST untar into `tmp_path` before consumption:
  ```python
  import tarfile
  with tarfile.open(fixture_path, "r:gz") as tf:
      tf.extractall(tmp_path)
  ```
  Adopts reviewer Major #17.

### 2.12 Model-name regex
`^[a-z][a-z0-9_]{1,30}$`. Rejected at `validate_spec.py` and at `register_model()`. SARAH-name canonicalization: provisional rule `"".join(w.capitalize() for w in name.split("_"))`. Amended in W3 only if the Day-1 probe reveals divergence.

### 2.13 Plugin.json schema
Existing entries in `plugins/model-building/.claude-plugin/plugin.json` are `{"name": "<kebab>", "path": "./skills/<kebab>/SKILL.md"}`. No `category`, `version`, or `description` at the skill-entry level. W0 appends four new entries in this shape. Final `skills[]` length is **6** (existing: `lagrangian-builder`, `rge-runner`; new: `sarah-install`, `sarah-build`, `spheno-install`, `spheno-build`). Adopts reviewer Major #4.

### 2.14 No tool mocking in integration
Unit tests may mock log parsers and pure-Python utilities only. Integration tests invoke the real tool. If a test is marked integration and the tool is absent, `pytest.skip`.

### 2.15 Single-writer discipline on `main`
Only the manager (this session) performs merges. Workstream agents run in isolated worktrees; they never push to `main`. Merges are serial ff-merges (§5). If two wave-A PRs finish concurrently, manager merges W1 first, then rebases W2 on the new `main`, then merges.

---

## 3. Per-workstream plan

### W0 — Shared contracts + config migration

**Dependencies:** none. Blocks every other workstream.
**Worktree name:** `wt-w0-shared-contracts`
**Base branch:** `main`
**Lands:** synchronously, before any downstream worktree spawns.

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/_common.sh` | Promoted copy of hep-ph-demo `_common.sh`, with atomic-write fsync fix. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/config_helpers.py` | Python mirror of `config_get` / `config_merge`; atomic + fsync. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/shared/install-helpers/README.md` | Single source-of-truth note; source path pattern. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` | One-line shim: sources the promoted copy. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_sarah.sh` | No logic change; comment documents shim. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_spheno.sh` | Same. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_mg5.sh` | Same. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/install/scripts/install_wolfram.sh` | Same. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/SHARED-model-building.md` | Cross-skill normative conventions. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json` | JSON Schema for ModelSpec v1. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` | JSON Schema for three-state blocker contract. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` | SARAH-name canonicalizer CLI + library. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/config_migration.py` | Asserts existing keys untouched; ensures `models: {}`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md` | Stub. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` | Stub. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md` | Stub. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` | Stub. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/model-building/.claude-plugin/plugin.json` | Append four entries; bump `version` to `0.2.0`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_modelspec_schema.py` | Validates spec §4 `dark_su3` example + negative cases. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_blocker_schema.py` | One instance per mode, including `reference_only` per PR-D. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_sarah_name.py` | Unit test of canonicalizer. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/test_config_helpers.py` | Unit test of Python mirror. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` | Spec §4 example verbatim. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/blocker_examples.json` | One per mode. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json` | Pre-refactor `install.sh detect-all` output. |

#### Detailed work items (ordered)

1. **Capture regression baseline BEFORE touching `_common.sh`.** On clean `main` at the start of W0:
   ```bash
   cd /Users/yianni/Projects/hep-ph-agents
   bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all \
     > plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json
   ```
   Commit this file as part of W0's first commit. It is the regression ground truth. (Adopts reviewer Major #8.)

2. **Create `plugins/shared/install-helpers/` directory.** Copy `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` verbatim to `plugins/shared/install-helpers/_common.sh`. Then apply the fsync fix to `config_merge` per §2.6 (edit the Python heredoc: replace `mv "$tmp" "$CONFIG_FILE"` with the Python `os.rename` + `os.fsync` sequence executed from inside the heredoc; the heredoc must `import os` and perform the rename itself, not rely on the outer shell `mv`). The bash wrapper around the heredoc no longer does `mv`; the Python block handles atomic rename with fsync.

3. **Write `plugins/shared/install-helpers/config_helpers.py`.** Public API:
   - `STATE_ROOT: Path`, `CONFIG_DIR: Path`, `CONFIG_PATH: Path` (computed from env per §2.3).
   - `load_config() -> dict` — empty dict if file absent.
   - `merge_config(**kwargs) -> None` — atomic tmpfile + fsync + rename + parent-dir fsync; updates `last_configured` UTC; preserves unrelated keys.
   - `register_model(name: str, **fields) -> None` — upserts `config["models"][name]` and merges `fields` into the model's sub-dict; raises `ValueError` if `name` fails the regex in §2.12.
   - `get_model(name: str) -> dict | None`.
   - Module-level constant `MODEL_NAME_REGEX = re.compile(r"^[a-z][a-z0-9_]{1,30}$")`.

4. **Write `plugins/shared/install-helpers/README.md`** (single page, ≤80 lines). Document: the source path pattern, why this module exists (rule-of-three exceeded), and that only W0 edits `_common.sh` / `config_helpers.py`.

5. **Refactor hep-ph-demo installers** (`install_wolfram.sh`, `install_sarah.sh`, `install_spheno.sh`, `install_mg5.sh`). Replace the literal local-`_common.sh` source with the shared-path pattern from §2.2. Keep the local `_common.sh` as a **one-line shim** — a file whose only meaningful content is `. "$SCRIPT_DIR/../../../shared/install-helpers/_common.sh"` (adopts reviewer judgment-call #2: "shim; zero-cost preservation"). The shim ensures any unknown external consumer that directly sources `plugins/hep-ph-demo/.../_common.sh` continues to work.

6. **Regression gate.** After the refactor, rerun:
   ```bash
   bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all \
     > /tmp/detect_all_refactor.json
   diff -q /tmp/detect_all_refactor.json \
        plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json
   ```
   Zero diff required. Commit only after pass.

7. **Write `plugins/hep-ph-toolkit/SHARED-model-building.md`.** Sections:
   - State root (§2.3).
   - Model-name regex (§2.12).
   - Timestamps (§2.5).
   - Env-var overrides table (§2.4) — advertise **only** `HEPPH_STATE_ROOT`, `XDG_CONFIG_HOME`, `HEPPH_SARAH_VERSION`, `HEPPH_SPHENO_VERSION`, `NO_NETWORK`.
   - Cache-key recipe (§2.9).
   - Three-state blocker contract summary (§2.7); point at `blocker.schema.json`.
   - Config-key alignment table (spec-invented → hep-ph-demo existing).
   - Reserved appendix: "§X SARAH-name probe result (filled by W3)" — a single empty subsection where W3 writes its probe finding. This is the only location a non-W0 workstream edits SHARED.md.

8. **Write `plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json`.** JSON Schema draft 2020-12. Required top-level: `spec_version` (const `1`), `name` (matches model-name regex), `claim_source`, `sarah_version_required`, `gauge_groups`, `fermions`, `scalars`, `lagrangian`, `parameters`, `outputs`. Each `gauge_groups[].kind` enum `{hypercharge, left, color, dark, other}`. `outputs` items enum `{ufo, spheno}`. No `x-extensions`.

9. **Write `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json`.** Top-level `oneOf` on three mode variants.
   - `fatal` variant: required `code` (string, `^[A-Z][A-Z0-9_]+$`), `mode: "fatal"`, `message` (non-empty string); optional `context` (object), `user_instruction` (non-empty string).
   - `recoverable` variant: same as fatal, `mode: "recoverable"`.
   - `reference_only` variant: required `status: "reference_only"`, `reference_method` (non-empty string), `caveats` (array of string, minItems 1). Per §2.7 / reviewer Blocker #25.
   Known blocker codes enumerated in comments (not enforced by schema):
   - fatal: `SARAH_DOWNLOAD_FAILED`, `SARAH_SMOKE_TEST_FAILED`, `SARAH_OUTPUT_MISSING`, `ANOMALY_CANCELLATION_FAILED`, `MODELSPEC_INVALID`, `WOLFRAM_KERNEL_ABSENT`, `GFORTRAN_ABSENT`, `SPHENO_DOWNLOAD_FAILED`, `SPHENO_BASE_BUILD_FAILED`, `SPHENO_PATH_INVALID`, `SPHENO_COMPILE_FAILED`, `SPHENO_NO_OUTPUT`.
   - recoverable: `SPHENO_SPECTRUM_PROBLEM`, `SPHENO_RGE_NONCONVERGENT`.

10. **Write `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py`.** Single function `modelspec_name_to_sarah(name: str) -> str`. Provisional rule:
    ```python
    def modelspec_name_to_sarah(name: str) -> str:
        if not MODEL_NAME_REGEX.match(name):
            raise ValueError(f"invalid model name: {name!r}")
        return "".join(w.capitalize() for w in name.split("_"))
    ```
    CLI: `python3 sarah_name.py <name>` prints the SARAH name, exit 0 on success, exit 2 on regex failure. Top of file carries a `# PROVISIONAL — verified by W3 Day-1 probe` comment pointing at the SHARED.md appendix.

11. **Write `plugins/hep-ph-toolkit/skills/_shared/config_migration.py`.** Library + CLI. `--check` reads config; asserts existing `wolfram_engine_path`, `sarah_path`, `spheno_path` keys (if present) are not renamed; ensures `models: {}` exists; prints a diff; exits 0 if no changes needed else 1. `--apply` writes via `config_helpers.merge_config`. No rename logic — this is an adoption check, not a migrator.

12. **Write the four stub `SKILL.md` files.** Each:
    ```
    ---
    name: <kebab-name>
    description: <one-line>. (Stub — implemented in W<#>.)
    ---
    See the spec at `docs/superpowers/specs/2026-04-18-sarah-spheno-skills-design.md`
    and the phase-2 plan at `docs/superpowers/workstream-sarah-spheno/phase2-plan-final.md`.
    ```

13. **Modify `plugins/model-building/.claude-plugin/plugin.json`.** Append four entries; bump `version` to `0.2.0`; preserve existing `lagrangian-builder` and `rge-runner` entries. Final `skills[]` length MUST equal 6.

14. **Write `tests/test_modelspec_schema.py`.** Cases: valid `dark_su3` spec; missing `spec_version`; bad `name` regex; unknown `gauge_groups[].kind`; `outputs: [calchep]` rejected.

15. **Write `tests/test_blocker_schema.py`.** Validate one instance of each of the six SCREAMING codes per mode; one valid `reference_only` instance (PR-D canonical shape); one invalid `reference_only` missing `caveats` (must reject).

16. **Write `tests/test_sarah_name.py`.** Cases: `dark_su3 → DarkSU3`; `singlet_doublet → SingletDoublet`; `2hdm` → `ValueError` (regex rejects leading digit). No SARAH-dependent integration test here; the real-SARAH verification lives in W3's Day-1 probe.

17. **Write `tests/test_config_helpers.py`.** With `tmp_path` + `monkeypatch.setenv("XDG_CONFIG_HOME", ...)`: merge into empty; preserve unrelated; register_model regex enforcement; round-trip; fsync verified by asserting no orphaned `.tmp` file after simulated crash in middle of write (use `monkeypatch` to raise inside the `with open(...)` block; assert `config.json` unchanged).

18. **Write fixtures.** `dark_su3_spec.yaml` = verbatim copy of spec §4 YAML. `blocker_examples.json` = JSON array with one object per mode (fatal, recoverable, reference_only).

19. **Run full W0 acceptance sweep** (below) before opening PR.

#### Acceptance criteria

All exit-0 or the specified exact stdout. Re-runnable on a clean checkout.

1. `bash plugins/hep-ph-toolkit/skills/install/scripts/install.sh detect-all > /tmp/w0_sweep.json && diff -q /tmp/w0_sweep.json plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/detect_all_baseline.json` → zero diff.
2. `python3 -c "import json; s=json.load(open('plugins/model-building/.claude-plugin/plugin.json')); assert len(s['skills']) == 6, len(s['skills'])"` exits 0.
3. `python3 plugins/hep-ph-toolkit/skills/_shared/sarah_name.py dark_su3` prints exactly `DarkSU3`.
4. `python3 plugins/hep-ph-toolkit/skills/_shared/config_migration.py --check` exits 0 on a machine whose config has existing hep-ph-demo keys.
5. `python3 -m pytest plugins/hep-ph-toolkit/skills/_shared/tests/ -q` exits 0.
6. `python3 -c "import jsonschema, json, yaml; s=json.load(open('plugins/hep-ph-toolkit/skills/_shared/modelspec.schema.json')); d=yaml.safe_load(open('plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml')); jsonschema.validate(d, s)"` exits 0.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_modelspec_schema.py` | unit | no |
| `test_blocker_schema.py` | unit | no |
| `test_sarah_name.py` | unit | no |
| `test_config_helpers.py` | unit | no |
| `install.sh detect-all` regression | smoke | no (detects only; may skip on clean machine with no tools installed — then baseline + refactor both produce `missing` output, diff still zero) |

#### Reads from / writes to

- **Reads:** hep-ph-demo `_common.sh` (copied + patched).
- **Writes for others:**
  - `_common.sh`, `config_helpers.py`: W1, W2 source bash; W3, W4, W5 import Python.
  - `modelspec.schema.json`: W3 `validate_spec.py`, W5 interview.
  - `blocker.schema.json`: W1, W2, W3, W4.
  - `sarah_name.py`: W3 `render_templates.py`.
  - Fixtures: W3, W4.
  - Four stub `SKILL.md`: overwritten by W1, W2, W3, W4.

#### Risks / unresolved

- **hep-ph-demo shim vs delete.** Keeping the shim (reviewer judgment-call #2). Zero-cost preservation.
- **`config_helpers.py` as Python mirror vs shell-out.** Mirror chosen (reviewer judgment-call #1).

---

### W1 — `/sarah-install`

**Dependencies:** W0.
**Worktree name:** `wt-w1-sarah-install`
**Base branch:** `main` (post-W0 merge).

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/SKILL.md` | Full skill. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/install_sarah.sh` | `detect / use-path / install`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/check_wolfram_activation.sh` | Probes `wolframscript` for activation prompt. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/detect_wolfram.sh` | Inline detection of Wolfram Engine; decoupled from hep-ph-demo. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/_activation_parse.py` | Pure-Python helper: stdout string → status JSON. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/scripts/_blocker.sh` | `emit_blocker()` helper used by both scripts. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/skill_env.yaml` | `sarah_version`, `sarah_url`, `sarah_sha256: TODO`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/test_detect_config.sh` | Bash smoke: config → JSON. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/test_activation_parse.py` | Unit test on activation-prompt fixtures. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/fixtures/wolfram_activation_prompt.txt` | Captured activation-needed stdout. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-install/tests/fixtures/wolfram_ok.txt` | `1+1 → 2` happy-path stdout. |

#### Detailed work items

1. **Day-1 probe first (before fixture commit).** On macOS with Wolfram Engine installed but **not activated**, run `wolframscript -code '1+1' 2>&1 > /tmp/wolfram_probe.txt`. Record exit code and full stdout. Commit `/tmp/wolfram_probe.txt` verbatim as `tests/fixtures/wolfram_activation_prompt.txt`. Derive the activation-detection grep pattern from actual output (likely substrings: `activate`, `Wolfram ID`, `not activated` — but don't guess; read the file). If no unactivated Wolfram is available on Day 1, mark the `check_wolfram_activation.sh` patterns as "provisional pending probe" with a `# TODO(W1-Day1)` comment, commit conservative union of those three substrings, and mark the integration test as `skip` until probe completes. (Adopts reviewer Minor #18 and Minor #23: probe before grep.)

2. **Copy `install_sarah.sh`** from hep-ph-demo. Change the source line to the W0 shared pattern (§2.2 with 4 `../`). Preserve every existing function — especially `probe_version` at line 17-27 which uses `AppendTo[$Path, "$pkg_dir/.."]`. **Keep the `/..`.** This is the existing convention: `sarah_path` points to the package dir containing `SARAH.m`; `<<SARAH\`` requires the **parent** of that dir in `$Path` (SARAH's loader resolves the `SARAH\`` context from a sibling directory). The reviewer's Blocker #3 disagrees; see the Resolution Log (appendix) — rejected with reason.

3. **Apply `HEPPH_SARAH_VERSION` override** (reviewer Major #15):
   ```bash
   SARAH_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"
   SARAH_URL="https://sarah.hepforge.org/downloads/SARAH-${SARAH_VERSION}.tar.gz"
   ```

4. **Add `sarah_installed_at` write** on every successful install / use-path. UTC ISO 8601 via `date -u +%Y-%m-%dT%H:%M:%SZ`. Merge via `config_merge`.

5. **Write `scripts/_activation_parse.py`.** Pure-Python module + CLI.
   ```python
   def classify(stdout: str, exit_code: int) -> dict:
       """Return status JSON per the W1 contract."""
   ```
   Cases:
   - `exit_code == 0` and output contains `2` (after stripping) → `{"status":"ok"}`.
   - Output matches any of the grep patterns from the probe → `{"status":"activation_required","message":"<human-readable>","user_instruction":"Run `wolframscript --activate` in your terminal; it opens a browser for a free Wolfram ID signup. Then rerun /sarah-install."}`.
   - Else → `{"status":"error","detail":"<first 200 chars of stdout>"}`.
   CLI: read stdin, read exit code from `$?` via argv, print JSON.

6. **Write `scripts/check_wolfram_activation.sh`.** Reads `wolfram_engine_path` from config, runs `$ws -code '1+1' 2>&1`, captures stdout + exit code, pipes to `python3 _activation_parse.py`. Prints JSON to stdout. Exit 0 regardless (status is in JSON).

7. **Write `scripts/detect_wolfram.sh`.** Inline reimplementation of `install_wolfram.sh`'s `scan_candidates` + `probe_version` logic. Do not call hep-ph-demo scripts directly — decouple. (Reviewer judgment-call #6 analog: isolate cross-plugin boundaries.) Approx 40 lines.

8. **Write `scripts/_blocker.sh`.** Contains `emit_blocker code mode message [user_instruction]` bash function that prints a single-line JSON blocker to stderr, shaped per `blocker.schema.json`. Sourced by `install_sarah.sh`.

9. **Install-flow semantic change vs hep-ph-demo:** after `extract_and_register` + `register_path`, invoke `check_wolfram_activation.sh`. If status is `activation_required`, print the JSON status to **stdout** and `exit 0`. Do NOT exit with `$EXIT_WOLFRAM_ACTIVATION` (code 24 in `_common.sh:23`). The sense is: activation is a user-actionable status, not a fatal blocker. `SARAH_SMOKE_TEST_FAILED` still fatal.

10. **Write `skill_env.yaml`:**
    ```yaml
    sarah_version: "4.15.3"
    sarah_url: "https://sarah.hepforge.org/downloads/SARAH-4.15.3.tar.gz"
    sarah_sha256: "TODO"   # verify_checksum warns-not-aborts; update pre-v1 release
    ```

11. **Write `SKILL.md`.** Sections: "When to invoke", "Decision flow (detect / use-path / install)", "JSON status contract" (enumerate `configured`, `found`, `missing`, `activation_required`), "Activation handling (critical)", "Failure modes → blockers" (per spec §2: `WOLFRAM_KERNEL_ABSENT`, `SARAH_DOWNLOAD_FAILED`, `SARAH_SMOKE_TEST_FAILED` are fatal blockers; `WOLFRAM_NEEDS_ACTIVATION` is a **status** not a blocker — include an explicit note flagging the divergence from spec §2, citing phase1-final §4). SKILL.md MUST NOT exceed 400 lines (no hard gate; style guideline).

12. **Detect-and-reuse path.** In `cmd_detect`: reuse hep-ph-demo's detection. If `sarah_path` and `wolfram_engine_path` both point to valid artifacts and probe_version succeeds → `{"status":"configured","path":"<p>","version":"<v>"}` exit 0. Collapse the hep-ph-demo `found` and `configured` distinction into a single `configured` output once both are valid; keep `found` only when `sarah_path` unset but scan_candidates succeeds (reviewer Minor #20: document, not collapse — but retain distinct semantics with one-line clarification in SKILL.md).

13. **Write `test_detect_config.sh`.** Under `XDG_CONFIG_HOME=$(mktemp -d)`: create a fake config with `sarah_path` pointing to a dir containing `SARAH.m` (also faked); run `install_sarah.sh detect`; assert JSON has `status: configured` and the expected path. Then unset config, assert `status: missing`.

14. **Write `test_activation_parse.py`.** Loads `fixtures/wolfram_activation_prompt.txt`; asserts `classify(contents, exit_code=0)` returns `activation_required` with populated `user_instruction`. Loads `fixtures/wolfram_ok.txt`; asserts returns `ok`.

#### Acceptance criteria

1. `bash install_sarah.sh detect` with `XDG_CONFIG_HOME` pointing at an empty dir → stdout `{"status":"missing"}`, exit 0.
2. `bash install_sarah.sh detect` with config containing valid `sarah_path` + `wolfram_engine_path` → stdout `{"status":"configured","path":"<p>","version":"<v>"}`, exit 0.
3. Network simulated down (`curl` unreachable): `install` emits `SARAH_DOWNLOAD_FAILED` blocker JSON on stderr and exits `$EXIT_DOWNLOAD` (12).
4. With Wolfram Engine installed but not activated (matching the Day-1 fixture): `install` completes extraction, calls `check_wolfram_activation.sh`, prints `{"status":"activation_required","user_instruction":"<exact>"}` on stdout, exits 0. No blocker emitted.
5. After successful activated install: `wolframscript -code 'AppendTo[$Path,"<p>/.."]; <<SARAH\`; Start["SM"]; CheckModel[]'` exits 0.
6. After install, `python3 -c "from plugins.shared.install_helpers.config_helpers import load_config as lc; c=lc(); assert 'sarah_path' in c and 'sarah_version' in c and 'sarah_installed_at' in c"` exits 0. No `wolfram_kernel`, no `sarah_base_path` keys exist.
7. With pre-existing hep-ph-demo SARAH install present: `detect` returns `configured` (no reinstall).
8. `HEPPH_SARAH_VERSION=4.14.0 bash install_sarah.sh install` uses URL for 4.14.0.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_detect_config.sh` | smoke | no |
| `test_activation_parse.py` | unit | no |
| Full install on clean macOS | integration | **yes — Wolfram Engine + network** |
| Full install on clean Linux | integration | **yes** |
| Detect-and-reuse against hep-ph-demo install | integration | **yes (existing install)** |

#### Reads / writes

- **Reads:** W0 `_common.sh`, `blocker.schema.json`, `config_helpers.py`.
- **Writes:** `config.sarah_path`, `config.sarah_version`, `config.sarah_installed_at`, reads `config.wolfram_engine_path`, `config.wolfram_engine_version`.
- **Invoked by:** W3 precondition check, W5 orchestrator.

#### Risks

- Activation-prompt string unknown on Day 0. Pinned by Day-1 probe; fixtures and grep updated once.
- SKILL.md divergence from spec §2's blocker list: activation demoted to status. Flagged in SKILL.md with explicit citation.

---

### W2 — `/spheno-install`

**Dependencies:** W0. Parallel with W1.
**Worktree name:** `wt-w2-spheno-install`
**Base branch:** `main` (post-W0 merge).

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/SKILL.md` | Full skill. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/install_spheno.sh` | `detect / use-path / install`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/check_gfortran.sh` | Per-OS remediation. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/_blocker.sh` | `emit_blocker` helper. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/scripts/_make_log_parse.py` | Pure-Python: make.log → blocker context. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/skill_env.yaml` | Versions + URL + placeholder sha256. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/test_detect_derive_src.sh` | Smoke: derive `spheno_src_path`. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/test_make_log_tail.py` | Unit: last 40 lines + code classification. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/test_version_mismatch.sh` | Smoke: mismatch → install-fresh-alongside path. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_fail_lapack.log` | Canned. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_fail_generic.log` | Canned. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-install/tests/fixtures/make_ok.log` | Canned. |

#### Detailed work items

1. **Copy `install_spheno.sh`** from hep-ph-demo. Source shared `_common.sh` per §2.2.

2. **Apply `HEPPH_SPHENO_VERSION` override:**
   ```bash
   SPHENO_VERSION="${HEPPH_SPHENO_VERSION:-4.0.5}"
   SPHENO_URL="https://spheno.hepforge.org/downloads/SPheno-${SPHENO_VERSION}.tar.gz"
   ```

3. **Dual-key write.** Every successful install / use-path writes both:
   - `spheno_path` — binary at `<src>/bin/SPheno` (preserves hep-ph-demo compat).
   - `spheno_src_path` — source tree root (contains `Makefile`). New key.
   - `spheno_version`, `spheno_installed_at`.

4. **`use-path` semantics (reviewer judgment-call #3 — accept either).** Signature: `install_spheno.sh use-path <path>`. Behavior: inspect `<path>`.
   - If `<path>` is a file AND `<path>` is executable AND `basename <path> == SPheno`: treat as binary path; derive `src = dirname(dirname(path))`; assert `$src/Makefile` exists.
   - If `<path>` is a directory AND `<path>/Makefile` exists: treat as source tree; derive `bin = <path>/bin/SPheno`; assert executable.
   - Else → `SPHENO_PATH_INVALID` fatal blocker, exit `$EXIT_BAD_PATH` (16).
   Record both keys in config.

5. **Detect-and-reuse path.** If `spheno_path` already set by hep-ph-demo, derive `spheno_src_path = dirname(dirname(spheno_path))`, assert `Makefile` present, probe version, compare to `SPHENO_VERSION` pin.

6. **Version-mismatch policy — install fresh alongside** (adopts Phase 1 §8 Issue 10 / reviewer Blocker #6 / judgment-call #4). If detected version ≠ pin, emit status `{"status":"version_mismatch","existing_path":"<p>","existing_version":"<v>","pin":"<pin>","action":"installing_fresh_alongside"}` on stdout, exit 0, and continue with a fresh install to `$HOME/SPheno-${SPHENO_VERSION}/` (note the version suffix — never overwrite). Do not adopt the existing. After fresh install succeeds, `spheno_path` + `spheno_src_path` point to the fresh install; prior install untouched on disk.

7. **Write `scripts/check_gfortran.sh`.** Extracted from the installer. Exit 0 if present; exit `$EXIT_NO_GFORTRAN` (10) with per-OS `user_instruction` if absent, emitted as `GFORTRAN_ABSENT` fatal blocker.

8. **Write `scripts/_make_log_parse.py`.** Pure-Python. `parse(log_text: str) -> dict` returns:
   ```python
   {"code": "SPHENO_BASE_BUILD_FAILED",
    "mode": "fatal",
    "message": "<one-line summary>",
    "context": {"make_log_tail": "<last 40 lines, newline-joined>",
                "likely_cause": "lapack|generic"}}
   ```
   Detect LAPACK-missing via grep for `lapack|liblapack|-llapack` (case-insensitive); else `likely_cause: "generic"`.

9. **Emit `SPHENO_BASE_BUILD_FAILED`** on `make` failure by feeding `/tmp/spheno_make.log` contents to `_make_log_parse.py` and printing the returned JSON via `emit_blocker`.

10. **Write `skill_env.yaml`:**
    ```yaml
    spheno_version: "4.0.5"
    spheno_url: "https://spheno.hepforge.org/downloads/SPheno-4.0.5.tar.gz"
    spheno_sha256: "TODO"
    ```

11. **Write `SKILL.md`.** Structure: "When to invoke", "Decision flow", "gfortran precondition", "Dual-key rationale (spheno_path + spheno_src_path)", "Detect existing hep-ph-demo install", "Version-mismatch → install fresh alongside", "Failure modes → blockers".

12. **Write `test_detect_derive_src.sh`.** Create `$HEPPH_STATE_ROOT/fake-spheno/SPheno-4.0.5/{bin/SPheno,Makefile}` (touch-only for file tests; the binary need not be executable Fortran, just chmod +x). Set config `spheno_path=.../bin/SPheno`. Run `install_spheno.sh detect`. Assert stdout contains `"spheno_src_path":"<path-without-/bin/SPheno>"`.

13. **Write `test_make_log_tail.py`.** For each fixture, assert `parse` returns correct `code`, `mode`, `likely_cause`, and that `context.make_log_tail` equals last 40 lines joined by `\n`.

14. **Write `test_version_mismatch.sh`.** Stub out `curl` by placing a fake `curl` in PATH that returns a local tarball (or set `HEPPH_SPHENO_VERSION` mismatching a fake existing install). Assert stdout reports `version_mismatch` and `action: installing_fresh_alongside`.

#### Acceptance criteria

1. `bash install_spheno.sh detect` with empty config → `{"status":"missing"}`, exit 0.
2. With hep-ph-demo install present (real `spheno_path` set): `detect` emits `{"status":"configured","path":"<p>","src_path":"<derived>","version":"<v>"}`. `src_path` = `dirname(dirname(spheno_path))`.
3. `bash install_spheno.sh use-path <binary-path>` accepts binary form; records both keys.
4. `bash install_spheno.sh use-path <source-tree-dir>` accepts dir form; records both keys.
5. `install` on a clean box with `gfortran` present produces `$HOME/SPheno-4.0.5/{bin/SPheno,Makefile}` and writes both keys.
6. `install` with `gfortran` absent → `GFORTRAN_ABSENT` fatal blocker JSON on stderr, exit `$EXIT_NO_GFORTRAN` (10).
7. `make` failure → `SPHENO_BASE_BUILD_FAILED` with `context.make_log_tail` (last 40 lines) and `likely_cause` set.
8. `HEPPH_SPHENO_VERSION=4.0.4` on a machine with 4.0.5 already installed → stdout `status: version_mismatch; action: installing_fresh_alongside`; fresh install at `$HOME/SPheno-4.0.4/`; prior install untouched.
9. `test_detect_derive_src.sh` and `test_make_log_tail.py` and `test_version_mismatch.sh` all pass.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_detect_derive_src.sh` | smoke | no |
| `test_make_log_tail.py` | unit | no |
| `test_version_mismatch.sh` | smoke | no (curl stubbed) |
| Full install on clean macOS | integration | **yes — gfortran + network (5-15 min)** |
| Full install on clean Linux | integration | **yes** |
| Detect-and-reuse | integration | **yes (existing install)** |

#### Reads / writes

- **Reads:** W0 `_common.sh`, `blocker.schema.json`.
- **Writes:** `config.spheno_path`, `config.spheno_src_path` (new), `config.spheno_version`, `config.spheno_installed_at`.
- **Invoked by:** W4 precondition, W5 orchestrator.

#### Risks

- `use-path` accepting either form diverges from hep-ph-demo's binary-only semantics; documented in SKILL.md.
- SPheno compile wall time is environment-dependent; acceptance is informational, not numeric.

---

### W3 — `/sarah-build`

**Dependencies:** W0, W1 (for real Wolfram smoke).
**Worktree name:** `wt-w3-sarah-build`
**Base branch:** `main` (post-wave-A merge).

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/sarah-build/SKILL.md` | Full skill. |
| NEW | `.../sarah-build/templates/model.m` | `str.format` template for `<Name>.m`. |
| NEW | `.../sarah-build/templates/parameters.m` | Template. |
| NEW | `.../sarah-build/templates/particles.m` | Template. |
| NEW | `.../sarah-build/templates/SPheno.m` | Template. |
| NEW | `.../sarah-build/scripts/render_templates.py` | Validate + render. |
| NEW | `.../sarah-build/scripts/run_sarah.py` | Invokes `wolframscript`. |
| NEW | `.../sarah-build/scripts/parse_sarah_log.py` | Log patterns → blockers. |
| NEW | `.../sarah-build/scripts/validate_spec.py` | CLI validator. |
| NEW | `.../sarah-build/scripts/build.py` | Top-level driver. |
| NEW | `.../sarah-build/scripts/regenerate_goldens.py` | One-command golden regeneration. |
| NEW | `.../sarah-build/tests/test_render_templates.py` | Byte-for-byte golden. |
| NEW | `.../sarah-build/tests/test_parse_sarah_log.py` | Five log fixtures. |
| NEW | `.../sarah-build/tests/test_validate_spec.py` | Schema + semantic. |
| NEW | `.../sarah-build/tests/test_cache_key.py` | Cache-key stability. |
| NEW | `.../sarah-build/tests/goldens/dark_su3/DarkSU3.m` | Golden. |
| NEW | `.../sarah-build/tests/goldens/dark_su3/parameters.m` | Golden. |
| NEW | `.../sarah-build/tests/goldens/dark_su3/particles.m` | Golden. |
| NEW | `.../sarah-build/tests/goldens/dark_su3/SPheno.m` | Golden. |
| NEW | `.../sarah-build/tests/fixtures/log_anomaly.txt` | SARAH log with anomaly failure. |
| NEW | `.../sarah-build/tests/fixtures/log_undefined_field.txt` | "field X undefined". |
| NEW | `.../sarah-build/tests/fixtures/log_missing_output.txt` | Clean end but no UFO dir. |
| NEW | `.../sarah-build/tests/fixtures/log_warnings_only.txt` | Warnings + success. |
| NEW | `.../sarah-build/tests/fixtures/log_success.txt` | Clean success. |

#### Detailed work items

1. **Day-1 probe (FIRST task in W3, before any template work).** Run:
   ```
   wolframscript -code 'AppendTo[$Path, "<sarah_path>/.."]; <<SARAH`; Start["SM"]; Print[ModelName]'
   ```
   On success, also try `Start["DarkSU3"]` after copying a minimal `DarkSU3.m` produced by our provisional canonicalizer. Observe what name SARAH accepts / rejects. Record findings in SHARED.md reserved appendix. Two outcomes:
   - Provisional rule holds → proceed. Add a one-paragraph note citing the probe.
   - Provisional rule wrong → make a one-commit amend to `plugins/hep-ph-toolkit/skills/_shared/sarah_name.py` + `plugins/hep-ph-toolkit/skills/_shared/tests/test_sarah_name.py` ONLY. Do not touch anything else in `_shared/`. Rebase W3 worktree; continue.

2. **Write `scripts/validate_spec.py`.** CLI: `python3 validate_spec.py <spec.yaml>`. Uses `jsonschema` against `_shared/modelspec.schema.json`. Semantic checks on top:
   - All `fermions[].name`, `scalars[].name`, `parameters[].name` unique (collectively).
   - Every `fermions[].reps` / `scalars[].reps` key exists in `gauge_groups[].symbol`.
   - `hypercharge` is rational with small denominator (denominator ≤ 6). Reject float typos like `0.33333`. Implementation: parse `fractions.Fraction(value)` where input is `int`, `str` (e.g. `"1/3"`), or small float; if `Fraction(value).limit_denominator(6) != Fraction(value)` → reject.
   - `outputs` non-empty; subset of `{ufo, spheno}`.
   Exit 0 on valid; exit 1 with `MODELSPEC_INVALID` fatal blocker JSON on stderr.

3. **Concrete worked fermion_block example** (adopts reviewer Major #5). The `{fermion_block}` placeholder renders like:
   ```mathematica
   (* --- Fermions --- *)
   FermionFields[[1]] = {qL, 3, {uL, dL}, 1/6, 2, 3};
   FermionFields[[2]] = {lL, 3, {vL, eL}, -1/2, 2, 1};
   ```
   Ordering: one `FermionFields[[i]]` per spec-declared fermion, index 1..N in declaration order. Fields in each row: `{name, generations, components_list, hypercharge, SU(2) dim, SU(3) dim}`. The list-to-Mathematica conversion is pre-joined in `render_templates.py` — the template itself is just `{fermion_block}`.

4. **Write `scripts/render_templates.py`.** Function signature:
   ```python
   def render(spec: dict, out_dir: Path) -> None:
       """Write {<Name>.m, parameters.m, particles.m, SPheno.m} to out_dir."""
   ```
   - Canonicalize name via `sarah_name.modelspec_name_to_sarah(spec["name"])`.
   - Build pre-joined strings for each placeholder (see item 3 for `{fermion_block}`; similar blocks for scalars, gauge groups, parameters, mass terms, Yukawa terms, scalar potential).
   - Load each template, `.format(**tokens)`, write to `out_dir/<filename>`.
   - Placeholder tokens allowed: `{name}`, `{gauge_group_block}`, `{fermion_block}`, `{scalar_block}`, `{parameter_block}`, `{mass_term_block}`, `{yukawa_block}`, `{scalar_potential_block}`. No conditionals, no loops.

5. **Write the four `.m` templates.** Structure mirrors SARAH's shipped SM model template. Templates contain only `{placeholder}` tokens at the positions where content goes; everything else is literal Mathematica.

6. **Write `scripts/run_sarah.py`.** Function:
   ```python
   def run(spec_path: Path, model_dir: Path, force: bool = False) -> dict:
   ```
   - Read `config = config_helpers.load_config()`.
   - Compute cache key: `hashlib.sha256(spec_bytes).hexdigest() + "=" + config["sarah_version"]`.
   - If `(model_dir/".sarah_build_key").read_text() == key` AND `(model_dir/"sarah_output"/"UFO"/sarah_name).is_dir()` AND not `force`: return `{"status":"cached"}`.
   - Render via `render_templates.render(spec, model_dir / "sarah")`.
   - Build command — **matches existing hep-ph-demo convention**:
     ```python
     ws = config["wolfram_engine_path"]
     sarah_path = config["sarah_path"]
     code = (
         f'AppendTo[$Path, "{sarah_path}/.."]; '
         f'<<SARAH`; '
         f'Start["{sarah_name}"]; '
         f'CheckModel[];'
         + "".join(f'Make{o.upper()}[];' for o in spec["outputs"])
     )
     cmd = [ws, "-code", code]
     ```
     The `/..` is correct (see W1 item 2 and `install_sarah.sh:25`). Reviewer Blocker #3 rejected; see appendix.
   - Capture stdout + stderr to `model_dir/sarah_output/sarah.log`.
   - Parse log via `parse_sarah_log.parse`. On fatal pattern match → emit blocker, do NOT update cache key.
   - Assert `model_dir/sarah_output/UFO/<sarah_name>/` exists; else emit `SARAH_OUTPUT_MISSING` fatal.
   - Write cache key; create `model_dir/ufo` symlink → `sarah_output/UFO/<sarah_name>/`.

7. **Write `scripts/parse_sarah_log.py`.** `parse(log_text: str) -> list[dict]`. Pattern table:
   - `r"Anomalies are not cancelled"` → `ANOMALY_CANCELLATION_FAILED` (fatal). Context: look ahead 10 lines for `"coefficient.*="` lines; attach as `context.coefficients: list[str]`.
   - `r"Error:\s+field\s+(\w+)\s+undefined"` → `MODELSPEC_INVALID` (fatal). Context: `field_name: str`.
   - `r"Warning:"` → collected as non-fatal warnings, not blockers. Returned in the dict under key `warnings`.

8. **Write `scripts/build.py`.** Top-level CLI: `python3 build.py <spec.yaml> [--force]`. Reads spec, resolves `model_dir = STATE_ROOT / "models" / spec["name"]`, copies spec, calls `render_templates.render`, calls `run_sarah.run`, calls `config_helpers.register_model(name, spec=..., ufo=..., sarah_built_at=...)`. Prints status JSON.

9. **Write `scripts/regenerate_goldens.py`** (adopts reviewer judgment-call #7). One-command CLI: `python3 regenerate_goldens.py`. Reads `tests/fixtures/dark_su3_spec.yaml` (copied from W0 shared fixture at build time — symlink to avoid duplication: `tests/fixtures/dark_su3_spec.yaml -> ../../../_shared/tests/fixtures/dark_su3_spec.yaml`). Renders into `tests/goldens/dark_su3/`. Script commit message template: `W3: regenerate goldens — <human rationale>`.

10. **Write `test_render_templates.py`.** Asserts byte-for-byte match for each of four files against `tests/goldens/dark_su3/*.m`. Any change to templates requires rerunning `regenerate_goldens.py` and reviewer approval on the diff.

11. **Write `test_parse_sarah_log.py`.** Five tests, one per fixture: `log_anomaly → ANOMALY_CANCELLATION_FAILED`; `log_undefined_field → MODELSPEC_INVALID` with field name captured; `log_missing_output → []` (caller emits `SARAH_OUTPUT_MISSING`, parser doesn't); `log_warnings_only → warnings set, no fatal blockers`; `log_success → []`.

12. **Write `test_validate_spec.py`.** Negative cases: duplicate fermion names; `reps` references unknown gauge group; `hypercharge: 0.33333` (not a small-denominator rational); empty `outputs`; `outputs: [calchep]`.

13. **Write `test_cache_key.py`.** Same spec bytes + same `sarah_version` → same key. One-byte whitespace edit → different key. Version bump → different key.

14. **Write `SKILL.md`.** Sections: "When to invoke", "Inputs (ModelSpec YAML)", "Decision flow", "Cache semantics", "Failure modes → blockers", "Post-build artifacts (UFO symlink, SPheno source tree)". Point at templates and scripts.

#### Acceptance criteria

1. `python3 validate_spec.py plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` exits 0.
2. `python3 build.py plugins/hep-ph-toolkit/skills/_shared/tests/fixtures/dark_su3_spec.yaml` on a machine with W1 merged produces `$STATE_ROOT/models/dark_su3/sarah_output/UFO/DarkSU3/` AND `.../sarah_output/SPheno/DarkSU3/`. (Wall-time threshold is informational: typical ~5 min; no hard gate.)
3. Launch MG5 against the UFO via **script file** (NOT `-c`):
   ```bash
   echo "import model $(realpath $STATE_ROOT/models/dark_su3/ufo); display particles; exit" > /tmp/mg5_probe.mg5
   mg5_aMC /tmp/mg5_probe.mg5
   ```
   Exit 0. Bounded go/no-go: if fails, open issue against SARAH↔MG5 compat; W3 blocks on upstream fix but the skill itself does not (reviewer Minor #24 gate).
4. Byte-for-byte golden: `test_render_templates.py` passes.
5. `test_parse_sarah_log.py` passes on all five fixtures.
6. `test_cache_key.py` passes: identical inputs → identical key; whitespace change → different; version bump → different.
7. Rerunning `build.py` with unchanged spec and cache present: completes **without invoking `wolframscript`**, asserted by `assert "wolframscript" not in captured_stderr`. Wall-time is informational (adopts reviewer Minor #21: reframed as "skips template + wolframscript; asserted by log absence, not a numeric threshold").
8. `--force` on `build.py` invalidates cache and re-invokes SARAH.
9. `config.models["dark_su3"]` populated with keys `spec`, `ufo`, `sarah_built_at`.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_render_templates.py` | unit (golden) | no |
| `test_parse_sarah_log.py` | unit | no |
| `test_validate_spec.py` | unit | no |
| `test_cache_key.py` | unit | no |
| `build.py dark_su3` end-to-end | integration | **yes — SARAH + Wolfram** |
| UFO imports into MG5 via script file | integration smoke | **yes — MG5** |

#### Reads / writes

- **Reads:** W0 `modelspec.schema.json`, `blocker.schema.json`, `sarah_name.py`, `config_helpers.py`, `dark_su3_spec.yaml`, `blocker_examples.json`. W1 config (`sarah_path`, `wolfram_engine_path`).
- **Writes:** `config.models[<name>].spec`, `.ufo`, `.sarah_built_at`. Per-model state under `$STATE_ROOT/models/<name>/`. SARAH output tree consumed by W4.
- **Amends SHARED.md appendix** (only location outside W0 touching SHARED.md).

#### Risks

- SARAH-name probe result unknown. Contingency in item 1.
- UFO ↔ MG5 3.5.6 compat unverified. Acceptance item 3 is the gate.

---

### W4 — `/spheno-build`

**Dependencies:** W0, W2 (for real SPheno base). Pre-W3: develops against a committed placeholder SARAH-output fixture. Post-W3 merge: manager re-dispatches (§5).
**Worktree name:** `wt-w4-spheno-build`
**Base branch:** `main` (post-wave-A merge).

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/spheno-build/SKILL.md` | Full skill. |
| NEW | `.../spheno-build/scripts/run_spheno.py` | Top-level driver (compile + run + summary + scan). |
| NEW | `.../spheno-build/scripts/compile_model.py` | Stage 1 — cached compile. |
| NEW | `.../spheno-build/scripts/run_point.py` | Stage 2 — single LesHouches run. |
| NEW | `.../spheno-build/scripts/parse_slha.py` | SLHA → summary.json. |
| NEW | `.../spheno-build/scripts/leshouches_template.py` | Generates MODSEL/SMINPUTS/MINPAR/SPHENOINPUT. |
| NEW | `.../spheno-build/scripts/scan.py` | Sequential scan; factored for v2 parallelism. |
| NEW | `.../spheno-build/scripts/regenerate_fixture.py` | One-command fixture rebuild post-W3. |
| NEW | `.../spheno-build/tests/fixtures/sarah_output_darksu3.tar.gz` | Gzipped minimal SARAH-output fixture. Hard cap 10 MB. |
| NEW | `.../spheno-build/tests/fixtures/spheno_spc_clean.spc` | Canned clean SLHA. |
| NEW | `.../spheno-build/tests/fixtures/spheno_spc_problem.spc` | SLHA with `Block PROBLEM 1`. |
| NEW | `.../spheno-build/tests/fixtures/spheno_spc_rge.spc` | SLHA with `Block SPINFO 4`. |
| NEW | `.../spheno-build/tests/fixtures/spheno_spc_missing.spc` | No `Block MASS` — simulates no-output. |
| NEW | `.../spheno-build/tests/fixtures/scan_recoverable_trigger.spc` | Deterministic fixture that parses to status=recoverable. |
| NEW | `.../spheno-build/tests/test_parse_slha.py` | Parser unit tests. |
| NEW | `.../spheno-build/tests/test_leshouches_template.py` | MINPAR ordering + patch. |
| NEW | `.../spheno-build/tests/test_scan_expansion.py` | 45-point Cartesian. |
| NEW | `.../spheno-build/tests/test_compile_cache.py` | Cache-key stability. |
| NEW | `.../spheno-build/tests/test_scan_recoverable_row.py` | Deterministic: recoverable row emits recoverable status. |

#### Detailed work items

1. **Write `scripts/parse_slha.py`.** `parse(spc_path: Path) -> dict` extracts `masses` (from `Block MASS`, `{pdg_id: mass_gev}`), `widths` (from each `DECAY <pdg>` header line), `problems` (from `Block PROBLEM`, list of int codes), `mixing` (from `Block NMIX`, `UMIX`, etc., keyed by block name as dict-of-dicts), and `spinfo` (from `Block SPINFO`, index-to-string). The caller maps `spinfo[4]` presence to `SPHENO_RGE_NONCONVERGENT`; `problems` containing any of `{1,2,3}` maps to `SPHENO_SPECTRUM_PROBLEM`.

2. **Write `scripts/leshouches_template.py`.** `build(spec: dict, overrides: dict | None = None) -> str` produces the LesHouches input string. Explicit block enumeration (spec §5):
   - `Block MODSEL`: `1  0` (non-SUSY; only supported case for v1).
   - `Block SMINPUTS`: hardcoded table — `1 1.279340000E+02` (alpha_em^-1), `2 1.166380000E-05` (G_F), `3 1.184000000E-01` (alpha_s(MZ)), `4 9.118760000E+01` (MZ), `5 4.180000000E+00` (m_b(m_b)), `6 1.734000000E+02` (m_t), `7 1.776820000E+00` (m_tau).
   - `Block MINPAR`: one row per `spec.parameters`, using `default` (or `overrides[name]` if present), in declaration order (index 1..N).
   - `Block SPHENOINPUT`: copy verbatim from `$STATE_ROOT/models/<name>/sarah_output/SPheno/<Model>/Input_Files/LesHouches.in.<Model>` (the SPHENOINPUT block only).
   Function `patch_minpar(text: str, params: dict[str, float]) -> str` replaces by name-indexed lookup into the MINPAR block.

3. **Write `scripts/compile_model.py`.** Algorithm:
   - `spheno_src = config["spheno_src_path"]`; `sarah_name = sarah_name(spec["name"])`; `model_dir = STATE_ROOT / "models" / spec["name"]`.
   - Cache key: `sha256(spec.yaml) + "=" + sarah_version + "+" + spheno_version`.
   - Cache hit: `(model_dir/"spheno_bin"/".build_key").read_text() == key` AND `(model_dir/"spheno_bin"/f"SPheno{sarah_name}").exists()` AND not `--force` → return.
   - Copy `model_dir/sarah_output/SPheno/<sarah_name>/` into `$spheno_src/<sarah_name>/`.
   - `make -C $spheno_src Model=<sarah_name> -j{os.cpu_count()}`.
   - Capture stdout + stderr to `model_dir/spheno_bin/make.log`.
   - Nonzero exit OR `$spheno_src/bin/SPheno<sarah_name>` missing → `SPHENO_COMPILE_FAILED` fatal; `context.make_log_tail` = last 40 lines.
   - Move binary to `model_dir/spheno_bin/SPheno<sarah_name>`. Write cache key.

4. **Write `scripts/run_point.py`.** `run(model_name: str, input_card: Path, out_dir: Path) -> dict`. Invocation per spec §5:
   ```
   $MODEL_DIR/spheno_bin/SPheno<Name>  $out_dir/LesHouches.in  $out_dir/SPheno.spc
   ```
   Two positional arguments; no shell redirection. Classification:
   - Exit nonzero OR `SPheno.spc` absent → `SPHENO_NO_OUTPUT` (fatal).
   - `parse_slha.py` returns `problems` ∩ {1,2,3} non-empty → `SPHENO_SPECTRUM_PROBLEM` (recoverable).
   - `parse_slha.py` returns `spinfo[4]` present → `SPHENO_RGE_NONCONVERGENT` (recoverable).
   - Clean `Block MASS` present → success; write `summary.json`.

5. **Write `scripts/scan.py`.** Factored API:
   ```python
   def scan_worker(point: dict, workdir: Path, model_name: str) -> dict: ...
   def scan(model: str, axes: list[tuple[str, float, float, float]], scan_dir: Path) -> Path: ...
   ```
   Sequential loop (v2 parallelism wraps `scan_worker` with `ProcessPoolExecutor`). Writes:
   - `runs/scan_<TS>/scan_index.csv` — columns `index`, `<param1>`, `<param2>`, …, `status`, `blocker_code`, `slha_path`.
   - `runs/scan_<TS>/LesHouches.in.NNNN`, `SPheno.spc.NNNN`.
   Fatal only on SPheno crash (exit != 0 with no `.spc`); recoverable markers continue the scan.

6. **Write `scripts/run_spheno.py`.** CLI: `python3 run_spheno.py <model_name> [--params k=v,...] [--input-card <path>] [--scan name=start:stop:step=s]... [--force]`. Dispatches:
   - `--input-card` → copy verbatim into `runs/<TS>/LesHouches.in`, no templating.
   - No `--scan` → single run; with `--scan` → delegate to `scan.py`.
   - Registers `config.models[<name>].spheno_bin`, `.latest_slha`, `.latest_run`, `.spheno_built_at`.

7. **Placeholder fixture (pre-W3, committed).** Build a minimal `sarah_output_darksu3.tar.gz` tree by hand with just the Fortran sources required to link `make Model=DarkSU3`. Hard cap **10 MB gzipped** (reviewer Major #14 resolved). Commit the tarball to W4 worktree. Post-W3 merge, manager re-runs `regenerate_fixture.py` against real SARAH output (see §5 re-dispatch checklist).

8. **Write `scripts/regenerate_fixture.py`.** One-command CLI to regenerate `tests/fixtures/sarah_output_darksu3.tar.gz` from the current W3 output tree at `$STATE_ROOT/models/dark_su3/sarah_output/SPheno/DarkSU3/`. Compresses, asserts output ≤ 10 MB, overwrites the fixture. Logs a checksum summary.

9. **Deterministic recoverable-row fixture (reviewer Blocker #2 resolution).** Create `tests/fixtures/scan_recoverable_trigger.spc` by hand: a valid SLHA with `Block PROBLEM\n  1  1.0` embedded. Used by `test_scan_recoverable_row.py` to deterministically assert that such an SLHA is classified as recoverable — **no dependence on any physics accident of the real scan.** The 45-row integration acceptance (below) is a count assertion only, not a "at least one should be recoverable" assertion.

10. **Write `test_parse_slha.py`.** One test per `*.spc` fixture. Asserts dict shape matches expected values: `clean` → `problems=[]`, `masses` non-empty; `problem` → `problems=[1]`; `rge` → `spinfo[4]` present; `missing` → raises or returns `{"masses": {}}` signaling caller emit `SPHENO_NO_OUTPUT`.

11. **Write `test_leshouches_template.py`.** Assert MINPAR row order matches `spec.parameters` declaration order. Assert `patch_minpar(text, {"MpsiD": 300})` replaces by name-lookup, leaves others unchanged.

12. **Write `test_scan_expansion.py`.** `MpsiD=200:1000:step=100` → 9 values `[200, 300, ..., 1000]`. `gD=0.5:2.5:step=0.5` → 5 values `[0.5, 1.0, 1.5, 2.0, 2.5]`. Cartesian product → 45 dicts.

13. **Write `test_compile_cache.py`.** Same `(spec_bytes, sarah_version, spheno_version)` → same key. Version bump → different.

14. **Write `test_scan_recoverable_row.py`.** Monkeypatch `run_point.run` to short-circuit and load `scan_recoverable_trigger.spc` as the "output" for one fixed point in a 3-point synthetic scan. Assert `scan_index.csv` has that row with `status=recoverable` and `blocker_code=SPHENO_SPECTRUM_PROBLEM`. Deterministic.

15. **Write `SKILL.md`.** Sections per spec §5: "When to invoke", "Compile stage (cached)", "Run stage (single point)", "Scan mode", "Recoverable vs fatal contract", "LesHouches generation", "Config keys written".

#### Acceptance criteria

1. `python3 parse_slha.py tests/fixtures/spheno_spc_clean.spc` produces `summary.json` with `problems=[]` and non-empty `masses`.
2. `python3 parse_slha.py tests/fixtures/spheno_spc_problem.spc` → `problems=[1]`.
3. `python3 parse_slha.py tests/fixtures/spheno_spc_rge.spc` → `spinfo` dict with key `4`.
4. `test_scan_recoverable_row.py` passes: deterministic recoverable-row assertion (reviewer Blocker #2 satisfied).
5. `python3 run_spheno.py dark_su3 --params MpsiD=300` with real SARAH+SPheno (post-W3 re-dispatch) produces `runs/<TS>/SPheno.spc` with `Block MINPAR` reflecting `MpsiD=300`.
6. `python3 run_spheno.py dark_su3 --input-card my.dat`: `diff my.dat runs/<TS>/LesHouches.in` is empty.
7. `python3 run_spheno.py dark_su3 --scan MpsiD=200:1000:step=100 --scan gD=0.5:2.5:step=0.5` writes `runs/scan_<TS>/scan_index.csv` with exactly **45 data rows** (plus header). (No "at least one recoverable" assertion here; that's covered deterministically by #4.)
8. Rerunning compile with unchanged inputs: skips make, asserted by `assert "make" not in captured_stderr` (adopts reviewer Minor #21 framing). Wall-time informational.
9. `--force` on compile bypasses cache.
10. `config.models["dark_su3"].spheno_bin`, `.latest_slha`, `.latest_run` populated after a successful single run.
11. Fixture size: `du -h tests/fixtures/sarah_output_darksu3.tar.gz` ≤ 10 MB.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_parse_slha.py` | unit | no |
| `test_leshouches_template.py` | unit | no |
| `test_scan_expansion.py` | unit | no |
| `test_compile_cache.py` | unit | no |
| `test_scan_recoverable_row.py` | unit (monkeypatched) | no |
| Compile against committed fixture | integration | **yes — gfortran + SPheno base (W2)** |
| Full single-point run | integration | **yes** |
| 45-point scan | integration | **yes — minutes** |
| Re-dispatch against real W3 output | integration | **yes — after W3 merges** |

#### Reads / writes

- **Reads:** W0 `blocker.schema.json`, `config_helpers.py`, `sarah_name.py`, fixtures. W2 `spheno_src_path`. W3 SARAH output tree at `$STATE_ROOT/models/<name>/sarah_output/SPheno/<Name>/`.
- **Writes:** `config.models[<name>].spheno_bin`, `.latest_slha`, `.latest_run`, `.spheno_built_at`. Per-model SPheno binary + run outputs.

#### Risks

- Committed placeholder fixture drifts vs real W3 output until re-dispatch step. Mitigated by §5 checklist.
- Scan-row "recoverable presence" is NOT asserted at real-scan level (it's deterministic via fixture).

---

### W5 — `/lagrangian-builder` (orchestrator rewrite)

**Dependencies:** W0–W4, W6.
**Worktree name:** `wt-w5-lagrangian-builder`
**Base branch:** `main` (post-wave-B merge).

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/lagrangian-builder/SKILL.md` | **Rewrite in place** as orchestrator. |
| NEW | `.../lagrangian-builder/references/interview.md` | Interview script. |
| NEW | `.../lagrangian-builder/references/orchestration.md` | State diagram + skip conditions. |
| NEW | `.../lagrangian-builder/references/anomaly-ledger.md` | Reading `ANOMALY_CANCELLATION_FAILED`. |
| NEW | `.../lagrangian-builder/assets/modelspec-templates/dark_su3.yaml` | Reference. |
| NEW | `.../lagrangian-builder/assets/modelspec-templates/singlet_doublet.yaml` | Reference. |
| NEW | `.../lagrangian-builder/assets/modelspec-templates/two_hdm.yaml` | Reference (named `two_hdm` to satisfy regex). |
| NEW | `.../lagrangian-builder/scripts/check_state.py` | JSON status probe. |
| NEW | `.../lagrangian-builder/scripts/register_model.py` | Writes `config.models[<name>]`. |
| NEW | `.../lagrangian-builder/tests/integration/dark_su3_e2e.sh` | Cold → built → MG5-ready. |
| NEW | `.../lagrangian-builder/tests/test_check_state.py` | Unit. |
| NEW | `.../lagrangian-builder/tests/test_register_model.py` | Unit. |

**Note on lagrangian-builder:** this skill already exists in `plugins/hep-ph-toolkit/skills/lagrangian-builder/`. W5 **rewrites in place** (adopts reviewer Major #4 consequence: no double-registering in plugin.json). The existing entry in `plugin.json` remains; no skill-registration change.

#### Detailed work items

1. **Write `scripts/check_state.py`.** Reads config via `config_helpers.load_config()`. Returns JSON:
   ```json
   {
     "sarah_install": "configured|missing",
     "spheno_install": "configured|missing",
     "wolfram_install": "configured|missing",
     "model": {"status": "present|missing", "name": "<name-or-null>"}
   }
   ```
   CLI: `python3 check_state.py [--model <name>]`. Pure probe; no side effects. ~40 lines.

2. **Write `scripts/register_model.py`.** Thin CLI over `config_helpers.register_model`. Args: `<name> --spec <path> --ufo <path> [--latest-slha <path>] [--spheno-bin <path>] [--sarah-built-at <iso>] [--spheno-built-at <iso>]`. Writes atomically. ~30 lines.

3. **Write `SKILL.md`.** Orchestrator instructions; NOT a script. Structure:
   ```
   ## When to invoke
   ## Overview
   ## Step 1: Check state (→ scripts/check_state.py)
   ## Step 2: Interview user (→ references/interview.md)
   ## Step 3: Propose and validate ModelSpec (→ sarah-build/scripts/validate_spec.py)
   ## Step 4: Sequence installs + builds
       - If sarah_install=missing → invoke /sarah-install
         - If status=activation_required: pause with exact user_instruction, stop.
       - Invoke /sarah-build <spec.yaml>
       - If spheno_install=missing → invoke /spheno-install
       - Invoke /spheno-build <name>
   ## Step 5: Register model (→ scripts/register_model.py)
   ## Step 6: Report paths and next steps (/madgraph use <name>)
   ## Recoverable outcomes (SPHENO_SPECTRUM_PROBLEM, SPHENO_RGE_NONCONVERGENT)
   ## Fatal outcomes
   ```
   Each step is natural-language instructions to Claude (which has tool access), not a script invocation chain. No hard line limit (reviewer Major #7: style rule, not gate — removed).

4. **Write `references/interview.md`.** Prompts for gauge-group selection, fermion content, scalar content, mass terms. Outputs a draft ModelSpec YAML for user review.

5. **Write `references/orchestration.md`.** Complete state diagram in prose. Entry points, skip conditions (detected installs), exit conditions (registered model, paused on activation_required, fatal surfaced). Cites three-state PR-D contract and `blocker.schema.json`.

6. **Write `references/anomaly-ledger.md`.** How to read `ANOMALY_CANCELLATION_FAILED` blocker: present coefficients, propose schema fixes (alternate hypercharge, additional fermion). Operational; not a physics textbook.

7. **Write ModelSpec templates.** `dark_su3.yaml` (≤50 lines), `singlet_doublet.yaml` (≤60), `two_hdm.yaml` (≤60). All pass `validate_spec.py`.

8. **Write `tests/integration/dark_su3_e2e.sh`.** Script:
   - Backs up real config to `.bak`.
   - Exports `HEPPH_STATE_ROOT` + `XDG_CONFIG_HOME` to fresh tmpdirs.
   - Runs `/sarah-install` (skipped if detect→configured from hep-ph-demo).
   - Runs `/spheno-install` (same).
   - Runs `sarah-build/scripts/build.py assets/modelspec-templates/dark_su3.yaml`.
   - Runs `spheno-build/scripts/run_spheno.py dark_su3`.
   - Asserts `config.models.dark_su3.ufo` and `.latest_slha` exist on disk.
   - Wall-time bounds informational: cold target ≤ 15 min, cached ≤ 3 min.
   - Restores config from `.bak` on exit.
   - Network-gated via `[ -n "${NO_NETWORK:-}" ] && exit 0`.

9. **Write `test_check_state.py`.** Uses `monkeypatch.setenv("XDG_CONFIG_HOME", ...)` + tmp config file. Assert each combination of configured/missing returns correct JSON.

10. **Write `test_register_model.py`.** Tmp config. Assert `models[<name>]` populated correctly after CLI call.

#### Acceptance criteria

1. E2E on `dark_su3` from cold cache: integration script exits 0.
2. `activation_required` path: with Wolfram unactivated, SKILL.md flow surfaces the user_instruction and stops (verified by running E2E on an unactivated Wolfram box; if script exits with the activation status string in stdout, pass).
3. Any fatal blocker from any sub-skill surfaces the full JSON and stops the flow (deterministic sub-test: inject a fake blocker by temporarily aliasing a sub-script to one that emits a fatal; SKILL.md instructions should cause Claude to surface + halt).
4. After successful E2E, `python3 plugins/hep-ph-toolkit/skills/madgraph/scripts/resolve_named_model.py dark_su3 --key ufo` returns the UFO path; MG5 script-file invocation with that path exits 0.
5. `test_check_state.py` and `test_register_model.py` pass.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_check_state.py` | unit | no |
| `test_register_model.py` | unit | no |
| `dark_su3_e2e.sh` | integration | **yes — full chain** |

#### Reads / writes

- **Reads:** all other workstream outputs. W0 helpers.
- **Writes:** invokes other skills; `config.models[<name>]`.

#### Risks

- SKILL.md-driven orchestration relies on Claude to interpret status JSON. If a sub-skill returns a nonstandard shape, Claude improvises. Documented as intended (augment-not-replace).

---

### W6 — `/madgraph` named-model resolver

**Dependencies:** W0.
**Worktree name:** `wt-w6-madgraph-resolver`
**Base branch:** `main` (post-W0 merge). Parallel with W3, W4.

#### Files

| State | Absolute path | Purpose |
|---|---|---|
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/SKILL.md` | Insert "Named model resolution" subsection. |
| MODIFIED | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/references/generation.md` | 10-line callout. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/scripts/resolve_named_model.py` | CLI resolver. |
| NEW | `/Users/yianni/Projects/hep-ph-agents/plugins/hep-ph-toolkit/skills/madgraph/tests/test_resolve_named_model.py` | Unit. |

#### Detailed work items

1. **Write `resolve_named_model.py`.** CLI: `python3 resolve_named_model.py <name> --key {ufo,latest_slha,spheno_bin}`. **Inline 15-line config read** (reviewer judgment-call #6: no cross-plugin import):
   ```python
   import json, os, sys
   from pathlib import Path
   CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "hep-ph-agents" / "config.json"
   def main():
       if len(sys.argv) != 4 or sys.argv[2] != "--key":
           print("usage: resolve_named_model.py <name> --key {ufo,latest_slha,spheno_bin}", file=sys.stderr); sys.exit(3)
       name, key = sys.argv[1], sys.argv[3]
       if key not in {"ufo", "latest_slha", "spheno_bin"}: sys.exit(2)
       try:
           cfg = json.loads(CONFIG_PATH.read_text())
       except FileNotFoundError:
           print(f"config not found: {CONFIG_PATH}", file=sys.stderr); sys.exit(1)
       model = cfg.get("models", {}).get(name)
       if not model: print(f"model not registered: {name}", file=sys.stderr); sys.exit(1)
       value = model.get(key)
       if not value: print(f"key {key!r} not set for {name}", file=sys.stderr); sys.exit(2)
       print(value)
   if __name__ == "__main__": main()
   ```
   Total ~25 lines.

2. **Edit `madgraph/SKILL.md` Decision Tree.** Insert new section *before* "Install or configure MG5?":
   ```markdown
   ### Using a named hep-ph-agents model?
   If the user says `use <name>` or `--model <name>`, resolve paths first:
     UFO  = python3 scripts/resolve_named_model.py <name> --key ufo
     SLHA = python3 scripts/resolve_named_model.py <name> --key latest_slha
   Then write MG5 commands:
     import model <UFO>
     ... generate ... output ...
     launch (substitute <SLHA> for param_card on prompt)
   ```

3. **Edit `references/generation.md`.** Append "Named-model handoff" callout (~10 lines) pointing at SKILL.md.

4. **Write `test_resolve_named_model.py`.** Uses `monkeypatch.setenv("XDG_CONFIG_HOME", ...)` + tmp config containing `{"models": {"dark_su3": {"ufo": "/tmp/ufo", "latest_slha": "/tmp/slha"}}}`. Assert stdout is the exact path. Assert exit 1 on missing model; exit 2 on missing key.

5. **MG5 smoke test (Day-1 probe W6).** On a box with MG5 installed: create `/tmp/mg5_probe.mg5` containing:
   ```
   import model <ufo-from-resolver>
   generate p p > psiD psiD~
   output /tmp/mg5_test_out
   exit
   ```
   Run `mg5_aMC /tmp/mg5_probe.mg5` — **script file positional argument, not `-c`** (Phase 1 §8 Issue 12, spec §6). Assert exit 0. Pins the invocation form before writing any resolver docs.

#### Acceptance criteria

1. `python3 resolve_named_model.py dark_su3 --key ufo` with tmp config containing `models.dark_su3.ufo=/path/to/ufo` prints exactly `/path/to/ufo`. Exit 0.
2. Missing model → exit 1, error on stderr.
3. Missing key for existing model → exit 2, error on stderr.
4. MG5 script-file invocation with resolved UFO path exits 0 (after W3 produces real UFO).
5. `test_resolve_named_model.py` passes.

#### Tests

| Test | Type | Requires real tool? |
|---|---|---|
| `test_resolve_named_model.py` | unit | no |
| MG5 script-file smoke | integration | **yes — MG5 + W3 UFO** |

#### Reads / writes

- **Reads:** `config.models[<name>]` (inline, no cross-plugin import).
- **Writes:** nothing.

#### Risks

- MG5 invocation form must be `mg5_aMC <script_file>`, not `-c`. Pinned by W6 Day-1 probe. If an existing eval harness (`eval/harness/runners/claude_code.py` or `eval/.../mg5_batch.py`) already uses a different form, align with it; otherwise commit to the script-file form per spec §6.

---

## 4. Dispatch plan for Phase 3

### Wave structure

| Round | Worktrees | Dependencies | Parallelism |
|---|---|---|---|
| 0 | W0 | — | solo, blocking |
| A | W1, W2 | W0 on `main` | parallel |
| B | W3, W4, W6 | W1 and W2 on `main` | parallel |
| C | W5 | W3, W4, W6 on `main` | solo |

### Round 0 (solo, blocking)
- Worktree: `wt-w0-shared-contracts`.
- Implementer brief topic: "Execute W0 per phase2-plan-final §W0. Capture baseline, promote `_common.sh` with fsync fix, write `config_helpers.py`, schemas, stubs, update plugin.json to 6 skills." Sonnet.
- First reviewer's focus: does `install.sh detect-all` produce zero-diff against baseline? does plugin.json parse with 6 skills? does `modelspec.schema.json` validate the `dark_su3` example? is fsync actually called in `config_merge`?
- Gate: all W0 acceptance pass; regression-diff is zero; merge to `main`.

### Round A (parallel, post-W0 merge)
- Worktrees: `wt-w1-sarah-install`, `wt-w2-spheno-install`.
- W1 brief: "Port `install_sarah.sh`, source shared `_common.sh`, add `check_wolfram_activation.sh`, Day-1 probe activation prompt BEFORE finalizing grep. Implement `HEPPH_SARAH_VERSION` override. Emit `activation_required` as status, not blocker."
- W2 brief: "Port `install_spheno.sh`, dual-key writes (`spheno_path` + `spheno_src_path`), version-mismatch → install fresh alongside. Implement `HEPPH_SPHENO_VERSION` override. `use-path` accepts binary or source-tree."
- First reviewer's focus (both): config-key parity with hep-ph-demo; blocker JSON shape (schema validates); detect-and-reuse path against real hep-ph-demo install; `XDG_CONFIG_HOME` respected in tests.
- Gate: acceptance criteria pass; Day-1 probes complete; merge sequentially (W1 first alphabetically, then W2 rebased).

### Round B (parallel, post-Round-A merge)
- Worktrees: `wt-w3-sarah-build`, `wt-w4-spheno-build`, `wt-w6-madgraph-resolver`.
- W3 brief: "Day-1 probe SARAH-name canonicalization FIRST. Render templates with pre-joined blocks, run SARAH via `wolframscript -code`, parse log, goldens + `regenerate_goldens.py`. Use `AppendTo[$Path, '<sarah_path>/..']` — this is correct per existing hep-ph-demo convention."
- W4 brief: "Build against committed 10MB-gzipped SARAH-output fixture. After W3 merges, re-dispatch: regenerate fixture, re-run integration. Include deterministic `test_scan_recoverable_row.py`."
- W6 brief: "Small resolver (inline config read), SKILL.md edit, generation.md callout, test. Day-1 probe MG5 script-file invocation form."
- First reviewer's focus: W3 — SARAH-name probe result documented in SHARED.md appendix; template str.format discipline; cache key semantics. W4 — SLHA parser on fixtures; MINPAR patch; deterministic recoverable assertion. W6 — MG5 script-file form.
- Gate: acceptance criteria pass. Merge order: **W3 first** (unlocks W4 re-integration), then **W6 and W4 in either order** (adopts reviewer Major #9). W4 re-dispatch happens between W3 merge and W4 merge — see §5.

### Round C (solo, post-Round-B merge)
- Worktree: `wt-w5-lagrangian-builder`.
- Brief: "SKILL.md-driven orchestrator (rewrite existing skill in place; no new plugin.json entry). `check_state.py` + `register_model.py` are the only scripts. E2E `dark_su3_e2e.sh` is the gate."
- First reviewer's focus: SKILL.md readability; E2E success; activation-pause handling; no orchestration logic hidden in Python scripts.
- Gate: E2E passes cold and cached; manual verification of activation pause; merge.

### Done criteria
- Per-workstream: all acceptance criteria pass; reviewer approves; Day-1 probes complete; ff-merged to `main`.
- Whole project: all seven workstreams merged; `dark_su3_e2e.sh` passes; README (unchanged in this workstream) reflects six-skill `model-building` plugin.

---

## 5. Merge procedure

### Single-writer discipline
- Only the manager (this session) runs `git merge`. Workstream agents never push to `main`.
- One ff-merge at a time. If two wave-A PRs report "ready" concurrently, manager merges W1 first, then rebases W2 on updated `main`, then verifies W2 still passes, then merges W2.

### Standard merge procedure (per workstream)

From the manager's primary checkout at `/Users/yianni/Projects/hep-ph-agents`:

```bash
# 1. Ensure worktree is green.
cd <worktree-path>
git status   # should be clean
git log --oneline -n 5

# 2. Rebase onto fresh main.
git fetch origin
git rebase origin/main
# Resolve conflicts (rare; see conflict policy below).

# 3. Back to manager.
cd /Users/yianni/Projects/hep-ph-agents
git fetch
git checkout main
git merge --ff-only <branch-name>   # fail-loud if not ff-able

# 4. Post-merge verification.
# Run the workstream's acceptance sweep against the merged main.

# 5. Cleanup (only after verification).
git worktree remove <worktree-path>
git branch -d <branch-name>
```

### Conflict policy

Shared files that MULTIPLE workstreams might touch:

| File | Touched by |
|---|---|
| `plugins/shared/install-helpers/_common.sh` | W0 only (invariant) |
| `plugins/shared/install-helpers/config_helpers.py` | W0 only (invariant) |
| `plugins/model-building/.claude-plugin/plugin.json` | W0 only (invariant) |
| `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` | W0 only (shim) |
| `plugins/hep-ph-toolkit/SHARED-model-building.md` | W0 primary; W3 amends ONE appendix subsection |

- If a conflict arises in any of the W0-only files, **stop and escalate to manager**. An agent that violated the invariant produced the conflict.
- If a conflict arises in `SHARED.md`, merge manually: W0's sections are fixed; W3's appendix is additive.

### W4 re-dispatch checklist (post-W3 merge)

After W3 lands on `main`, before W4 merges:

1. `cd <wt-w4-spheno-build>`.
2. `git fetch origin && git rebase origin/main`.
3. `rm tests/fixtures/sarah_output_darksu3.tar.gz` (old placeholder).
4. Run W3 end-to-end on `dark_su3` locally: `python3 .../sarah-build/scripts/build.py .../modelspec-templates/dark_su3.yaml`. Produces real SARAH output under `$STATE_ROOT/models/dark_su3/sarah_output/`.
5. `python3 scripts/regenerate_fixture.py` — regenerates `tests/fixtures/sarah_output_darksu3.tar.gz` from the real SARAH output. Asserts ≤ 10 MB gzipped.
6. Re-run W4 integration tests end-to-end: compile, single run, 45-point scan. Assert all acceptance criteria.
7. Commit: `W4: regenerate SARAH-output fixture from merged W3`.
8. Rebase and merge per standard procedure.

Adopts reviewer Major #10.

---

## 6. Day-1 probes

Each probe has a command, success criterion, owner, go/no-go consequence.

| # | Probe | Workstream | Command (representative) | Success criterion | Owner | Go/no-go consequence |
|---|---|---|---|---|---|---|
| 1 | Wolfram activation prompt string | W1 | `wolframscript -code '1+1' 2>&1 > /tmp/probe.txt` on unactivated box | File non-empty; contains `activate`, `Wolfram ID`, or `not activated` substring | W1 implementer | Determines grep patterns; if no unactivated box available, grep patterns marked provisional; test marked skip; integration gate deferred |
| 2 | SARAH name canonicalization | W3 | `wolframscript -code 'AppendTo[$Path,"<p>/.."]; <<SARAH\`; Start["DarkSU3"]'` | Exit 0; no `Error: field undefined` | W3 implementer | Ratifies provisional rule; divergence triggers one-commit amend to `sarah_name.py` + test |
| 3 | SARAH UFO ↔ MG5 3.5.6 compat | W3 → W6 | `mg5_aMC /tmp/probe.mg5` with `import model <UFO>; display particles; exit` | Exit 0; no traceback | W3 implementer (capture); W6 reviewer (verify in W6) | W6 acceptance item 4. If fails: block on SARAH/MG5 upstream; not on this workstream |
| 4 | MG5 invocation form (script-file vs `-c`) | W6 | `mg5_aMC /tmp/probe.mg5` | Exit 0 | W6 implementer | Pins resolver docs to script-file form; inconsistent form blocks resolver smoke |
| 5 | SPheno base compile wall-time | W2 | `time bash install_spheno.sh install` on clean macOS | Install completes; record wall-time (informational) | W2 implementer | No gate; records reality for future budget-setting |
| 6 | Fixture tree size for `sarah_output_darksu3.tar.gz` | W4 | `du -sh tests/fixtures/sarah_output_darksu3.tar.gz` | ≤ 10 MB | W4 implementer | Re-gzip with `-9`; if still over, split into sub-fixtures (§2.11); if still over, block W4 until reduced. No git-LFS, no CI-fetch |

Adopts reviewer Major #8, Major #14, Minor #23, Minor #24.

---

## 7. Config migration plan

**No migration.** Adopt existing hep-ph-demo keys as-is:
- `sarah_path`, `sarah_version`, `sarah_installed_at` — used.
- `wolfram_engine_path`, `wolfram_engine_version` — used.
- `spheno_path`, `spheno_version`, `spheno_installed_at` — used.
- `madgraph_path`, `madgraph_version`, `python`, `last_configured` — unchanged.

Net-new keys introduced by this workstream:
- `spheno_src_path` — source-tree root. Added by W2.
- `models: {<name>: {spec, ufo, spheno_bin, latest_slha, latest_run, sarah_built_at, spheno_built_at}}` — added by W3 (`spec`, `ufo`, `sarah_built_at`) and W4 (`spheno_bin`, `latest_slha`, `latest_run`, `spheno_built_at`).

Spec §1's `wolfram_kernel`, `wolfram_kind`, `wolfram_version`, `spheno_base_path` are **NOT** introduced. Spec needs a follow-up fix-up commit (covered by W0 SHARED.md alignment table).

`config_migration.py --check` asserts these invariants and ensures `models: {}` exists. `--apply` writes.

---

## 8. Summary table

| ID | Name | Deps | Worktree | Wave |
|---|---|---|---|---|
| W0 | Shared contracts + config migration | — | `wt-w0-shared-contracts` | 0 |
| W1 | `/sarah-install` | W0 | `wt-w1-sarah-install` | A |
| W2 | `/spheno-install` | W0 | `wt-w2-spheno-install` | A |
| W3 | `/sarah-build` | W0, W1 | `wt-w3-sarah-build` | B |
| W4 | `/spheno-build` | W0, W2 (+ W3 re-dispatch) | `wt-w4-spheno-build` | B |
| W5 | `/lagrangian-builder` | W0–W4, W6 | `wt-w5-lagrangian-builder` | C |
| W6 | `/madgraph` resolver | W0 | `wt-w6-madgraph-resolver` | B |

Exclusive owners (no two workstreams edit):
- `plugins/shared/install-helpers/_common.sh` — W0.
- `plugins/shared/install-helpers/config_helpers.py` — W0.
- `plugins/model-building/.claude-plugin/plugin.json` — W0.
- `plugins/hep-ph-toolkit/skills/install/scripts/_common.sh` — W0 (shim).

Shared with narrow amendments:
- `plugins/hep-ph-toolkit/SHARED-model-building.md` — W0 primary; W3 amends ONE reserved appendix subsection.

---

## Appendix: Resolution log

Every numbered item in the reviewer's critique is resolved here with a decision and a reason.

### Blockers

**#1 — `config_merge` atomicity bug.**
**Adopted.** §2.6 mandates fsync-fd + rename + fsync-parent-dir in both bash and Python mirrors. Implementation specified for W0.

**#2 — W4 non-deterministic acceptance ("at least one recoverable").**
**Adopted.** §W4 item 9 introduces `scan_recoverable_trigger.spc` fixture + `test_scan_recoverable_row.py`; the 45-row scan acceptance is now a count assertion only.

**#3 — W3 `AppendTo[$Path]` has extra `/..`.**
**REJECTED.** The `/..` is NOT a bug. `sarah_path` points to the SARAH package directory containing `SARAH.m` (see `install_sarah.sh:15-16` comment, `install_sarah.sh:105-108` `use-path` validation). SARAH's `<<SARAH\`` loader resolves the `SARAH\`` Mathematica context from a sibling directory, so the **parent** of the package dir must be in `$Path`. The existing hep-ph-demo `probe_version` at `install_sarah.sh:25` uses exactly `AppendTo[$Path, "$pkg_dir/.."]`, and `register_path` at `install_sarah.sh:65-70` computes `parent = "$pkg_dir/.."` for the same reason. The drafter's plan matches the existing convention. Removing the `/..` would break the install by pointing `$Path` at the package dir itself instead of its parent. Reviewer's reading of this as a bug is incorrect — the `/..` is deliberate and verified against existing working code. **This rejection is the only blocker-level disagreement with the reviewer.**

### Major

**#4 — Plugin.json count 4 vs 6.** Adopted. §2.13 and W0 item 13 specify final count is 6. W5 rewrites `lagrangian-builder` in place; no sixth-skill double-registration.

**#5 — W3 placeholder tokens lack worked example.** Adopted. §W3 item 3 gives a concrete two-fermion `{fermion_block}` example.

**#6 — W2 version-mismatch regression.** Adopted. §W2 item 6: "install fresh alongside" per Phase 1 §8 Issue 10, no silent adoption.

**#7 — W5 "no script >80 lines" acceptance.** Adopted. §W5 item 3 removes the line-limit acceptance gate; kept as style guidance only (reviewer Major #7).

**#8 — W0 `install.sh detect-all` regression gate baseline.** Adopted. §W0 item 1: capture baseline into `tests/fixtures/detect_all_baseline.json` BEFORE any `_common.sh` edit; diff against post-refactor output.

**#9 — Dispatch merge order over-serialized.** Adopted. §5: W3 merges first; W6 and W4 merge in either order after W3.

**#10 — Re-dispatch step for W4 post-W3 not numbered.** Adopted. §5 W4 re-dispatch checklist, 8 numbered steps.

**#11 — No single-writer discipline on main.** Adopted. §2.15 and §5 — manager is sole writer; sequential ff-merges.

**#12 — Concurrent cache-key writes in wave B.** Adopted. §2.3 mandates `HEPPH_STATE_ROOT` worktree-scoped tmpdir for every test run.

**#13 — Global config.json leak across worktrees.** Adopted. §2.3 mandates `XDG_CONFIG_HOME` worktree-scoped tmpdir for every test run; documented in SHARED.md.

**#14 — Fixture size policy.** Adopted. §2.11: 10 MB gzipped in-repo cap; plain tarball rejected; git-LFS rejected; split-fixture fallback. §W4 item 7 enforces 10 MB.

**#15 — `HEPPH_SARAH_VERSION` advertised not honored.** Adopted. §2.4 and §W1 item 3: implemented in `install_sarah.sh` via `SARAH_VERSION="${HEPPH_SARAH_VERSION:-4.15.3}"`. Also adds `HEPPH_SPHENO_VERSION` in §W2 item 2.

**#16 — `user_instruction` semantic across status + fatal.** Adopted. §2.8: single definition for both uses.

**#17 — Fixture untar not specified.** Adopted. §2.11 mandates `tarfile.open(...).extractall(tmp_path)` idiom.

### Minor

**#18 — W1 activate grep over-broad.** Adopted. §W1 item 1: Day-1 probe pins exact string before grep is finalized; union of `activate|Wolfram ID|not activated` is conservative default until probe completes.

**#19 — W4 placeholder fixture pre-W3 lacks composition spec.** Adopted. §W4 item 7 specifies: "minimal Fortran sources required to link `make Model=DarkSU3`, hand-built, ≤ 10 MB gzipped." Post-W3, `regenerate_fixture.py` replaces with real output.

**#20 — W1 `found` vs `configured` states.** Adopted with clarification. §W1 item 12: `configured` = `sarah_path` set and valid; `found` = `sarah_path` unset but `scan_candidates` succeeds. Documented in SKILL.md.

**#21 — W3 ≤5s rerun gate.** Adopted. §W3 acceptance item 7: reframed to "skips template + wolframscript; asserted by log absence, not numeric threshold." Same reframing applied to §W4 acceptance item 8.

**#22 — Python 3 version pin missing.** Adopted. §2.1: Python ≥ 3.10 enforced at entry of every script.

**#23 — Day-1 probe sequencing: Wolfram activation before grep.** Adopted. §W1 item 1.

**#24 — SARAH UFO ↔ MG5 probe go/no-go gate.** Adopted. §W3 acceptance item 3 + §6 Day-1 probe #3: exit-0 on MG5 script-file invocation is the gate; if fails, block on upstream fix, not on this workstream.

**#25 — `blocker.schema.json` reference_only shape.** Adopted. §2.7 + §W0 item 9: mirrors PR-D commit `f72e19e` canonical shape — `status: "reference_only"`, non-empty `reference_method` string, non-empty `caveats` list. Verified against the `_is_reference_only` function in `eval/harness/outcome.py` as introduced by that commit.

### Judgment-call votes (7)

All adopted per reviewer's vote.

1. `config_helpers.py` Python mirror — **Python mirror** (not shell-out). Adopted in §W0.
2. `_common.sh` shim in hep-ph-demo — **shim** (not delete). Adopted in §W0 item 5.
3. W2 `use-path` semantics — **accept either; detect**. Adopted in §W2 item 4.
4. W2 version-mismatch — **install fresh alongside**. Adopted in §W2 item 6.
5. `reference_only` shape — **mirror commit `f72e19e`**. Adopted in §2.7.
6. W6 cross-plugin coupling — **inline 15-line config read**. Adopted in §W6 item 1.
7. Golden-file tests — **keep goldens; add one-command regeneration**. Adopted in §W3 item 9 (`regenerate_goldens.py`).

---

## Appendix: Worked `dark_su3` SARAH template outputs (for reviewer verification)

The following is for §W3 item 3 anchoring. When `render_templates.render(dark_su3_spec, out_dir)` runs, `out_dir/DarkSU3.m` contains (abbreviated):

```mathematica
(* DarkSU3 model — generated by /sarah-build *)
ModelName      = "DarkSU3";
NameOfStates   = {GaugeES, EWSB};

(* --- Gauge groups --- *)
Gauge[[1]] = {B,   U[1], hypercharge, g1, False, 1};
Gauge[[2]] = {WB,  SU[2], left,       g2, True,  1};
Gauge[[3]] = {G,   SU[3], color,      g3, False, 1};
Gauge[[4]] = {GD,  SU[3], dark,       gD, False, 1};

(* --- Fermions --- *)
FermionFields[[1]] = {qL, 3, {uL, dL}, 1/6, 2, 3, 1};
FermionFields[[2]] = {lL, 3, {vL, eL}, -1/2, 2, 1, 1};
FermionFields[[3]] = {psiD, 1, psiD,     0,   1, 1, 3};

(* --- Scalars --- *)
ScalarFields[[1]] = {H,    1, {Hp, H0}, 1/2, 2, 1, 1};
ScalarFields[[2]] = {phiD, 1, phiD,     0,   1, 1, 3};
...
```

Tokens used (canonical ordering in `render_templates.py`):
- `{name}` → `DarkSU3`
- `{gauge_group_block}` → the four `Gauge[[i]] = {...};` lines joined with `\n`.
- `{fermion_block}` → the three `FermionFields[[i]] = {...};` lines.
- `{scalar_block}` → the two `ScalarFields[[i]] = {...};` lines.
- `{parameter_block}`, `{mass_term_block}`, `{yukawa_block}`, `{scalar_potential_block}` — analogous.

Pre-joining is done by Python; templates have no conditionals or loops. Goldens are checked in byte-for-byte.

---

*End of Phase 2 plan (final).*
