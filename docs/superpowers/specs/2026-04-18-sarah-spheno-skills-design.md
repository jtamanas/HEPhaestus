# SARAH + SPheno skills — design

**Date:** 2026-04-18
**Status:** design approved, ready for implementation plan
**Scope:** four new skills (`/sarah-install`, `/sarah-build`, `/spheno-install`, `/spheno-build`) in `plugins/model-building/`, plus a rewrite of `/lagrangian-builder` as the orchestrator, plus a minimal resolver in `/madgraph` for named-model handoff.

---

## 1. Overview and data flow

### Goal
Turn a user's natural-language BSM model description into a compiled UFO + SLHA mass spectrum consumable by the existing `/madgraph` skill, by driving SARAH and SPheno end-to-end. No Python reimplementation of physics — skills drive the real tools (augment, don't replace).

### Roles
- **`/lagrangian-builder`** — user-facing orchestrator. Interviews the user, constructs a validated `ModelSpec`, then sequences `/sarah-install`, `/sarah-build`, `/spheno-install`, `/spheno-build` as needed. Owns the registry update and reports final `ufo_path` + `slha_path` back to the user.
- **`/sarah-install`** — one-shot setup; detects or installs Wolfram Engine + SARAH. Writes `wolfram_kernel`, `sarah_path`, `sarah_version` into the shared config.
- **`/sarah-build`** — given a `ModelSpec`, emits SARAH `.m` files from templates, invokes SARAH via `wolframscript`, produces UFO directory + SPheno Fortran source.
- **`/spheno-install`** — one-shot setup; verifies `gfortran`, fetches and compiles the base SPheno source tree.
- **`/spheno-build`** — compiles a model-specific SPheno binary (cached), runs it on a LesHouches input card, produces an SLHA spectrum. Scan-friendly.

### Big picture

```
User ──► /lagrangian-builder  (user-facing workflow)
            │
            │  interviews user ─► validates ModelSpec ─► orchestrates:
            │
            ├─ /sarah-install   (lazy — only if kernel missing)
            ├─ /spheno-install  (lazy — only if base missing)
            ├─ /sarah-build     (ModelSpec → UFO + SPheno source)
            └─ /spheno-build    (SPheno source → compiled binary → SLHA)
            │
            └─► registers models[<name>] in config.json
                and reports: "/madgraph use <name>"  ready
```

### Directory layout
All per-user state under a single root, to make listing and cleanup trivial:

```
~/.local/share/hep-ph-agents/
├── sarah/                         # base SARAH install (from /sarah-install)
├── spheno-base/                   # base SPheno source tree (from /spheno-install)
└── models/
    ├── dark_su3/
    │   ├── spec.yaml              # the ModelSpec these skills consumed
    │   ├── sarah/                 # rendered <Name>.m, parameters.m, particles.m
    │   ├── sarah_output/          # raw SARAH output (UFO/, SPheno/, ...)
    │   ├── ufo/                   # symlink to sarah_output/UFO/<Name>
    │   ├── spheno_bin/            # SPheno<Name> binary + .build_key
    │   └── runs/
    │       └── 2026-04-18T1230Z/
    │           ├── LesHouches.in
    │           ├── SPheno.spc     # SLHA spectrum
    │           └── summary.json   # parsed masses/widths/problems
    └── singlet_doublet/ ...
```

### Config schema (extension of existing `~/.config/hep-ph-agents/config.json`)

```json
{
  "madgraph_path":     "/Users/.../MG5_aMC/bin/mg5_aMC",
  "madgraph_version":  "3.5.6",
  "python":            "/usr/bin/python3",

  "wolfram_kernel":    "/usr/local/bin/wolframscript",
  "wolfram_kind":      "engine",
  "wolfram_version":   "14.0.0",
  "sarah_path":        "/Users/.../hep-ph-agents/sarah",
  "sarah_version":     "4.15.3",
  "sarah_installed_at":"2026-04-18T12:00:00Z",

  "spheno_base_path":  "/Users/.../hep-ph-agents/spheno-base",
  "spheno_version":    "4.0.5",
  "spheno_installed_at":"2026-04-18T12:05:00Z",

  "models": {
    "dark_su3": {
      "spec":            ".../models/dark_su3/spec.yaml",
      "ufo":             ".../models/dark_su3/ufo",
      "spheno_bin":      ".../models/dark_su3/spheno_bin/SPhenoDarkSU3",
      "latest_slha":     ".../models/dark_su3/runs/2026-04-18T1230Z/SPheno.spc",
      "latest_run":      "2026-04-18T1230Z",
      "sarah_built_at":  "2026-04-18T12:20:00Z",
      "spheno_built_at": "2026-04-18T12:30:00Z"
    }
  }
}
```

---

## 2. Per-skill contracts

Common pattern for all four: `scripts/` directory with a shell or Python driver (mirroring `hep-ph-demo/skills/install/scripts/install_mg5.sh`), plus a short `SKILL.md` that documents the decision flow — not the physics.

### `/sarah-install`
- **Input:** none (or `--reinstall`).
- **Output:** `wolfram_kernel`, `wolfram_kind`, `wolfram_version`, `sarah_path`, `sarah_version`, `sarah_installed_at` written atomically into shared config. SARAH source tree at `~/.local/share/hep-ph-agents/sarah/`.
- **Driver:** `scripts/install_sarah.sh` with subcommands `detect | use-path <path> | install`.
- **Flow:** detect → (if missing Wolfram kernel) offer Wolfram Engine auto-install → (if missing SARAH) fetch + extract + smoke test → write config. Non-interactive activation step is surfaced as a dedicated `activation_required` status (see §3).
- **Failure modes (all fatal, no fallback):**
  - `WOLFRAM_KERNEL_ABSENT` — install failed or declined.
  - `WOLFRAM_NEEDS_ACTIVATION` — Wolfram Engine installed but not activated; message tells user to run `wolframscript -activate` once.
  - `SARAH_DOWNLOAD_FAILED` — network / hash mismatch.
  - `SARAH_SMOKE_TEST_FAILED` — SARAH installed but `Start["SM"]` fails.

### `/sarah-build`
- **Input:** path to a `ModelSpec` YAML (schema locked in §4).
- **Output:**
  - Rendered `.m` files under `models/<name>/sarah/`.
  - Raw SARAH output under `models/<name>/sarah_output/`, including `UFO/<Name>/` and `SPheno/<Name>/`.
  - `models/<name>/ufo` symlink.
  - Updated config: `models[<name>].spec`, `.ufo`, `.sarah_built_at`.
- **Driver:** `scripts/run_sarah.py` (template render + `wolframscript` invocation + log parse).
- **Failure modes:**
  - `MISSING_DEPENDENCY: sarah-install` (fatal; orchestrator lazy-installs).
  - `ANOMALY_CANCELLATION_FAILED` (fatal; structured with SARAH-reported coefficients).
  - `MODELSPEC_INVALID` (fatal; line number + Mathematica message).
  - `SARAH_OUTPUT_MISSING` (fatal).
- **Invoked by:** `/lagrangian-builder` after ModelSpec validation; or directly by user with `--spec path/to/spec.yaml`.

### `/spheno-install`
- **Input:** none (or `--reinstall`).
- **Output:** `spheno_base_path`, `spheno_version`, `spheno_installed_at` in config. SPheno base tree unpacked and compiled under `~/.local/share/hep-ph-agents/spheno-base/`.
- **Driver:** `scripts/install_spheno.sh` with `detect | use-path <path> | install` subcommands (matches `/sarah-install` and `hep-ph-demo install` shape).
- **Failure modes (all fatal):**
  - `GFORTRAN_ABSENT` — per-OS install message.
  - `SPHENO_DOWNLOAD_FAILED`.
  - `SPHENO_BASE_BUILD_FAILED` — last 40 lines of `make.log` in the blocker.
  - `SPHENO_PATH_INVALID` — user-supplied path doesn't contain a buildable SPheno tree (the `use-path` case).

### `/spheno-build`
- **Input:** `model_name` (must exist in `config.models`), optional `--params name=value,...` or `--input-card path`, optional `--scan name=start:stop:step=s` (repeatable).
- **Output:**
  - `models/<name>/spheno_bin/SPheno<Name>` (cached).
  - `models/<name>/runs/<TS>/{LesHouches.in, SPheno.spc, summary.json}`.
  - For scans: `models/<name>/runs/scan_<TS>/scan_index.csv` + numbered cards and spectra.
  - Config: `models[<name>].spheno_bin`, `.latest_slha`, `.latest_run`, `.spheno_built_at`.
- **Driver:** `scripts/run_spheno.py` (compile stage + run stage + SLHA parser).
- **Failure modes:**
  - `MISSING_DEPENDENCY: spheno-install | sarah-build` (fatal).
  - `SPHENO_COMPILE_FAILED` (fatal).
  - `SPHENO_SPECTRUM_PROBLEM` (**recoverable**, PR-D contract).
  - `SPHENO_RGE_NONCONVERGENT` (**recoverable**).
  - `SPHENO_NO_OUTPUT` (fatal).
- **Invoked by:** `/lagrangian-builder`; directly by user for scans.

---

## 3. `/sarah-install` — Wolfram Engine and activation

### Kernel probe order
```
wolframscript --version        # succeeds for either Mathematica or Engine
wolframscript -code '1+1'      # confirms kernel actually runs
```
If `wolframscript` is missing but `math` is present (old Mathematica), recommend upgrading — SARAH's headless flow needs `wolframscript`. Legacy `MathKernel -noprompt` is opt-in only via `--legacy-kernel`.

### Wolfram Engine install paths
- **macOS:** `brew install --cask wolfram-engine`. Binary at `/Applications/Wolfram Engine.app/...`; `wolframscript` symlinks into `/usr/local/bin/`.
- **Linux (Debian/Ubuntu):** fetch `.sh` from `https://www.wolfram.com/engine/` and run non-interactively: `sudo ./WolframEngine_*.sh -- -auto -verbose`.
- **Linux (other):** hard-block with the download link.
- **Windows native / WSL:** v1 scope is macOS + Linux; Windows gets a blocker with the download link.

### Activation step
Wolfram Engine requires a one-time free Wolfram ID login. We cannot automate this. Flow:

1. After install, probe with `wolframscript -code '1+1'`.
2. If the kernel prints an activation prompt, return the `activation_required` status with the exact instruction:
   > "Wolfram Engine is installed but not activated. Run `wolframscript -activate` in your terminal once; it will open a browser window for a free Wolfram ID signup. Then rerun `/sarah-install`."
3. `/lagrangian-builder` treats `activation_required` as a user-action-needed pause, not a failure.

We do not try to drive the browser, scrape credentials, or sign the user up. Licensing is the user's.

### SARAH version pinning
Pinned per hep-ph-agents release in `plugins/hep-ph-toolkit/skills/sarah-install/skill_env.yaml`. v1 target: SARAH 4.15.x. Pinning avoids UFO-format drift across minor versions. Override via `HEPPH_SARAH_VERSION` env var (at user risk).

### Explicit `/sarah-install` non-goals (v1)
- Docker-packaged SARAH.
- FeynRules side-by-side support (FeynRules is downstream-only per the memory rule).
- Windows native install.
- Silent auto-update (only `--reinstall` changes versions).

---

## 4. `/sarah-build` — ModelSpec → SARAH files → UFO + SPheno source

### Responsibility boundary (augment-not-replace)
| Step | Who |
|------|-----|
| Interview user → natural-language model description | `/lagrangian-builder` |
| Structural validation (names unique, reps well-formed, numeric charges) | Claude (template-level) |
| **Anomaly cancellation** (SU(N)³, mixed, Witten, gravitational) | **SARAH** (`CheckModel[]`) |
| **Operator enumeration** (all gauge-invariant Yukawa / scalar terms) | **SARAH** |
| Mass matrices, RGE, vertices | **SARAH** |
| UFO + SPheno source export | **SARAH** exporters |
| ModelSpec → `.m` template rendering | Claude |
| SARAH log parsing into structured blockers | Claude |

Skill **blocks hard** if SARAH is missing. No Python fallback for anomalies, enumeration, or any other "SARAH" column entry.

### ModelSpec schema (locked for v1)

```yaml
name: dark_su3
claim_source: "user session 2026-04-18"
sarah_version_required: ">=4.15,<4.16"

gauge_groups:
  - {symbol: B,  group: U1,  kind: hypercharge, coupling: g1, gauge_boson: B0, gaugino: null}
  - {symbol: WB, group: SU2, kind: left,        coupling: g2, gauge_boson: W,  gaugino: null}
  - {symbol: G,  group: SU3, kind: color,       coupling: g3, gauge_boson: g,  gaugino: null}
  - {symbol: GD, group: SU3, kind: dark,        coupling: gD, gauge_boson: gD0,gaugino: null}

fermions:
  - name: psiDL
    reps: {WB: 1, G: 1, GD: 3}
    hypercharge: 0
    generations: 1
    chirality: left
  - name: psiDR
    reps: {WB: 1, G: 1, GD: 3}
    hypercharge: 0
    generations: 1
    chirality: right

scalars: []

lagrangian:
  mass_terms:
    - {fields: [psiDL, psiDR], coefficient: MpsiD, hermitian_conjugate: true}
  yukawa_terms: []
  scalar_potential: []

parameters:
  - {name: MpsiD, latex: "M_{\\psi_D}", real: true, positive: true, default: 500.0}
  - {name: gD,    latex: "g_D",         real: true, positive: true, default: 1.0}

outputs: [ufo, spheno]
```

No free-form Mathematica escape hatch. Features outside the schema require a schema expansion, not raw `.m` injection.

### `.m` rendering
One Jinja template per SARAH file, living in `plugins/hep-ph-toolkit/skills/sarah-build/templates/`:
- `model.m.j2` → `<Name>.m`
- `parameters.m.j2`
- `particles.m.j2`
- `SPheno.m.j2`

Templates are pure string-fill. Anything conditional beyond spin dispatch belongs in SARAH, not the templates — enforced by review.

### Headless SARAH invocation
`scripts/run_sarah.py`:
```python
cmd = [
    config["wolfram_kernel"], "-code",
    f'AppendTo[$Path, "{config["sarah_path"]}"]; '
    f'<<SARAH`; '
    f'Start["{spec["name"]}"]; '
    f'CheckModel[];'
    + "".join(f'Make{o.upper()}[];' for o in spec["outputs"])
]
```
Stdout → `models/<name>/sarah_output/sarah.log`. Return code propagated. SARAH exits 0 on physics errors, so we also parse the log:

| Pattern | Blocker |
|---------|---------|
| `Anomalies are not cancelled` or non-zero `CheckAnomalies[]` output | `ANOMALY_CANCELLATION_FAILED` (fatal) |
| `Error: field <X> undefined` | `MODELSPEC_INVALID` (fatal) |
| Missing `UFO/<Name>/` after run | `SARAH_OUTPUT_MISSING` (fatal) |
| `Warning: ...` | collected, non-fatal |

Parser: `scripts/parse_sarah_log.py`.

### Rebuild caching
Key: `sha256(spec.yaml) + sarah_version`. Stored at `models/<name>/.build_key`. No-op if key matches and `sarah_output/` exists; `--force` overrides. Rationale: `/lagrangian-builder` iteration loops often re-invoke with identical specs.

### `/sarah-build` non-goals (v1)
- `MakeCalcHEP[]`, `MakeWHIZARD[]`, `MakeFeynArts[]`, `MakeLaTeX[]` exporters.
- SUSY `superpotential:` block — Lagrangian-level entry only.
- Parallel SARAH runs (single kernel).

---

## 5. `/spheno-build` — compile, run, scan

### Stage 1: compile (idempotent, cached)
```
MODEL=$(basename $SARAH_OUT)
cp -r $SARAH_OUT/SPheno/$MODEL $SPHENO_BASE/$MODEL
cd $SPHENO_BASE && make Model=$MODEL -j$(nproc)
mv $SPHENO_BASE/bin/SPheno$MODEL $MODEL_DIR/spheno_bin/
```
Cache key: `sha256(sarah_output/SPheno/<Model>/) + spheno_version` at `models/<name>/spheno_bin/.build_key`. Skipped on match.

Failures:
- `make` error → `SPHENO_COMPILE_FAILED` + last 40 lines of `make.log`. Fatal.
- Missing `sarah_output/SPheno/<Model>/` → `MISSING_DEPENDENCY: sarah-build`. Fatal.

### Stage 2: run (scan-friendly)
```
TS=$(date -u +%Y-%m-%dT%H%MZ)
mkdir models/<name>/runs/$TS
cp $TEMPLATE_LH $TS/LesHouches.in
$MODEL_DIR/spheno_bin/SPheno$MODEL $TS/LesHouches.in $TS/SPheno.spc
```
`config.models[<name>].latest_slha` points to the newest successful run.

### Scans
```
/spheno-build dark_su3 --scan MpsiD=100:1000:step=50 --scan gD=0.3:3.0:step=0.3
```
Produces `models/<name>/runs/scan_<TS>/` with:
```
scan_index.csv              # one row per point: params, status, path to SLHA
LesHouches.in.0001  SPheno.spc.0001  ...
```
Sequential execution in v1 (parallelism in v2 — SPheno is not parallel-safe with shared outputs).

### Recoverable-failure contract (PR-D three-state)
| Condition | Blocker | Mode |
|-----------|---------|------|
| Exit ≠ 0 or no `SPheno.spc` | `SPHENO_NO_OUTPUT` | fatal |
| `Block PROBLEM` code 1/2/3 | `SPHENO_SPECTRUM_PROBLEM` | **recoverable** |
| `Block SPINFO 4` (RGE non-convergent) | `SPHENO_RGE_NONCONVERGENT` | **recoverable** |
| Clean `Block MASS` for all BSM states | success | — |

Recoverable blockers let scans continue (rows marked bad in `scan_index.csv`) and let `/lagrangian-builder` offer a parameter nudge without re-running SARAH.

### LesHouches input generation
If caller provides a file → used verbatim. Otherwise templated from ModelSpec:
- `Block MODSEL` — per-spec boilerplate (SUSY flag).
- `Block SMINPUTS` — PDG defaults.
- `Block MINPAR` — one entry per `spec.parameters`, using `default` values, in declaration order.
- `Block SPHENOINPUT` — copied from `sarah_output/SPheno/<Model>/Input_Files/`.

`--params name=value,...` patches `Block MINPAR` before the run.

### SLHA parsing
`scripts/parse_slha.py` extracts `masses`, `widths`, `problems`, `mixing` into `runs/<TS>/summary.json`. Raw `SPheno.spc` is source of truth.

### `/spheno-build` non-goals (v1)
- Parallel scans.
- micrOMEGAs / HiggsBounds / HiggsSignals handoff.
- Automatic parameter tuning to clear `Block PROBLEM`.

---

## 6. Handoff to `/madgraph` + v1 scope summary

### What `/madgraph` gains
A single resolver step at the top of its SKILL.md flow:

> Before generating, check whether the user named a model (e.g. "use `dark_su3`" or `--model dark_su3`). If so, resolve `config.models[<name>].ufo` → `import model <path>` and `config.models[<name>].latest_slha` → `param_card`. Otherwise fall back to the existing path-based flow.

No new protocol. Path-based invocation remains fully supported (e.g., the existing `eval/2506.19062_.../ufo/` stub).

### End-to-end user experience

```
User:  /lagrangian-builder

Claude: What BSM physics do you want to explore?
User:   Add a dark SU(3) gauge symmetry to the SM with one Dirac fermion
        in the fundamental, SM-singlet, mass ~500 GeV.

[Claude runs the interview, proposes a ModelSpec, gets approval, calls
 /sarah-install (lazy), /sarah-build, /spheno-install (lazy), /spheno-build.
 ~2–3 minutes end-to-end.]

Claude: Model `dark_su3` is built.
          UFO:  ~/.local/share/hep-ph-agents/models/dark_su3/ufo
          SLHA: ~/.local/share/hep-ph-agents/models/dark_su3/runs/.../SPheno.spc
        No anomaly or spectrum issues. Ready for /madgraph.

User:   /madgraph use dark_su3
        generate p p > psiD psiD~

[Events generated.]
```

### v1 IN
1. `/sarah-install` with Wolfram Engine auto-install (macOS + Linux).
2. `/sarah-build` with the ModelSpec schema at §4, UFO + SPheno source outputs.
3. `/spheno-install` with gfortran check and base SPheno compile.
4. `/spheno-build` with compile caching, sequential scans, recoverable-failure contract.
5. Config schema extension with per-model registry.
6. `/madgraph` resolver for `use <model_name>`.
7. `/lagrangian-builder` rewritten as orchestrator; interview + anomaly ledger with SARAH as the anomaly engine.

### v1 OUT
- Parallel scans.
- SARAH exporters beyond UFO + SPheno (CalcHEP, WHIZARD, FeynArts, LaTeX).
- micrOMEGAs, HiggsBounds, HiggsSignals chaining.
- SUSY `superpotential:` block.
- Windows / WSL native.
- Docker-packaged SARAH.
- NLO UFO generation (SARAH NLOCT).
- Auto-tuning to clear `Block PROBLEM`.
- Non-gauge discrete symmetries beyond SARAH's `DEFINITION[EWSB]`.
- Multiple concurrent Wolfram kernels.

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Wolfram ID activation confuses users | Dedicated `activation_required` status + exact terminal instruction |
| SARAH version drift breaks UFO import | Version pin in `skill_env.yaml`; UFO-import check in smoke test |
| Silent `Block PROBLEM` points in scans | `scan_index.csv` marks them; orchestrator summarizes "N of M points unphysical" |
| User invokes `/sarah-build` before installing SPheno | Lazy orchestrator install; direct invocation blocks with clear message |
| Templates grow conditional logic that encodes physics | Templates are pure string-fill; review-checklist gate |

### Relation to in-flight work
- **PR-D three-state blocker contract** — `/sarah-build` and `/spheno-build` both emit fatal / recoverable / reference-only blockers.
- **`augment_not_replace` valves** — all four skills fall cleanly in the "drives a real tool" category; no valves needed.
- **`hep-ph-demo/skills/install/` pattern** — `/sarah-install` and `/spheno-install` mirror its `detect | use-path | install` structure, its JSON status contract, and its `AskUserQuestion` UX.
- **`/lagrangian-builder` rebuild** — this spec *is* that rebuild, plus the two install skills and the SPheno compile-and-run skill.

---

## Implementation ordering

Suggested sequencing for the implementation plan:

1. `/sarah-install` (unblocks everything else).
2. `/spheno-install` (independent; can go in parallel with 1).
3. `/sarah-build` (depends on 1).
4. `/spheno-build` (depends on 2 + 3).
5. `/madgraph` resolver patch (depends on 4 for smoke test).
6. `/lagrangian-builder` rewrite (depends on all of the above for end-to-end test).

Each step lands with its own smoke test (SM for SARAH, a single point run for SPheno, `chi1 q > chi1 q` for MG5) so regressions are localized.
