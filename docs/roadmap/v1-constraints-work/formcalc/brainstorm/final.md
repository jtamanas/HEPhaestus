# `/formcalc` — Final Design (Synthesizer)

This document locks the v1 design for `/formcalc-install` (installer) and
`/formcalc` (usage) given the Manager's cross-workstream decisions and the
proposer/critic round. Implementation lands in
`plugins/feynman-diagrams/` alongside `/feynarts` and `/formcalc`.

---

## 0. Scope lock

- **v1 is Mathematica-symbolic only.** `WriteSquaredME` / Fortran emission is
  out; defer to v1.1. This removes the runtime LoopTools-link blocker surface
  for the usage skill but LoopTools is **still built at install time** because
  `/formcalc`'s numeric-evaluation branch may link against it.
- **No `reference_only` fallback.** A missing or broken FormCalc is always a
  fatal blocker. The blocker schema's `reference_only` branch is not used by
  either skill.
- **Augment-not-replace enforcement:** γ₅ scheme must be passed explicitly by
  the user for any chiral amplitude (see §2.3). No silent defaults.

---

## 1. Install skill — `/formcalc-install`

### 1.1 Distribution reality

Per the critic's probe, the FormCalc 10.x tarball from `feynarts.de` vendors
the LoopTools source tree **but not FORM**. FormCalc ships a `tools/` bootstrap
that *can* fetch FORM if absent, but this is a network action on an independent
upstream (`github.com/vermaseren/form`). We therefore treat the three artefacts
as independently versioned:

| Artefact | Source | Version pin env var |
|---|---|---|
| FormCalc (Mathematica app) | `http://www.feynarts.de/formcalc/FormCalc-<ver>.tar.gz` | `HEPPH_FORMCALC_VERSION` (default `10.0`) |
| LoopTools (Fortran lib) | bundled inside FormCalc tarball, same tag | `HEPPH_LOOPTOOLS_VERSION` (default: FormCalc-bundled) |
| FORM (Vermaseren) | `github.com/vermaseren/form` release tarball | `HEPPH_FORM_VERSION` (default `4.3.1`) |

LoopTools shares the FormCalc tag by policy — the env var exists for override
only. Three version keys are written to `~/.config/hep-ph-agents/config.json`.

### 1.2 Install locations

| Artefact | Location |
|---|---|
| FormCalc Mathematica app | `$UserBaseDirectory/Applications/FormCalc-<ver>/` |
| LoopTools library | `$UserBaseDirectory/Applications/FormCalc-<ver>/LoopTools/lib[64]/libooptools.a` |
| FORM binary | `<install-root>/form/<arch>-<os>/form` (no `~/.local/bin` symlink) |

`$UserBaseDirectory` is resolved by a one-shot `wolframscript` probe (same
pattern `/sarah-install` uses for `$Path` registration). FORM is referenced by
absolute path stored as `form_binary` in config; the FormCalc driver `.wls`
sets `SetEnvironment["FORM" -> <form_binary>]` (confirm symbol name in smoke
test — FormCalc's own `$FormCmd` may be the right lever). No `PATH` pollution.

### 1.3 Subcommands

Mirrors `/sarah-install` exactly:

| Subcommand | Purpose | Key exits |
|---|---|---|
| `detect` | Scan candidates + config; emit `{status: configured\|found\|missing}` JSON on stdout | 0 |
| `use-path <dir>` | Register existing install; smoke test | 0 / 15 / 16 / 20 |
| `install [dir]` | Full install: Wolfram probe → disk → download × 3 → checksum → extract → LoopTools `make` → FORM `configure && make` → register `$Path` via `init.m` → smoke test | 0 / 11 / 12 / 13 / 14 / 15 / 20 / 23 |

**Prerequisites (fatal, ordered):**
`wolfram_engine_path` (`WOLFRAM_KERNEL_ABSENT`, exit 20) → `gfortran`
(`GFORTRAN_ABSENT`, exit 10) → `make`/`cc` → ≥ 3 GB free (`check_disk 3 5`).

**`HEPPH_NO_NETWORK=1` support.** When set, `install` skips all `curl` calls
and requires that `$HEPPH_OFFLINE_CACHE/{formcalc,form,looptools}/<ver>.tar.gz`
pre-exist. Missing cache → fatal `FORMCALC_OFFLINE_CACHE_MISS`. This matches
the pattern other installers will gain in W0.

### 1.4 macOS / Apple Silicon `libquadmath`

LoopTools' quad-precision library (`libooptools-quad.a`) requires
`libquadmath`, which Apple clang does **not** ship. Install-time platform
probe:

- `darwin` + `arm64`: probe for `libquadmath.dylib` in Homebrew `gcc` prefix
  (`brew --prefix gcc`). If absent, disable quad-precision build
  (`./configure --without-quad` or equivalent), log a warning, and record
  `looptools_quad: false` in config. Do **not** fail — double-precision is
  enough for v1.
- `linux`: quad is expected to work; if build fails, fatal
  `LOOPTOOLS_QUADMATH_ABSENT` with `user_instruction` pointing at
  distro-specific `libquadmath-dev` (or `sudo apt install libquadmath0
  gfortran-multilib`).

### 1.5 Blocker codes (all fatal unless noted)

Added to the shared blocker-schema known-codes enum:

- `FORMCALC_DOWNLOAD_FAILED` (exit 12)
- `FORMCALC_SMOKE_TEST_FAILED` (exit 15)
- `FORMCALC_PATH_INVALID` (exit 16)
- `FORM_DOWNLOAD_FAILED` (exit 12)
- `FORM_BUILD_FAILED` (exit 23)
- `FORM_VERSION_MISMATCH` (**recoverable** — pre-existing `form` on `PATH`
  doesn't match our pin; skill ignores and uses its own)
- `LOOPTOOLS_BUILD_FAILED` (exit 23)
- `LOOPTOOLS_QUADMATH_ABSENT` (exit 23, linux only)
- `FORMCALC_OFFLINE_CACHE_MISS` (exit 12)

`activation_required` is a **status**, not a blocker (inherited from
`/sarah-install`). `/formcalc-install install` exits 0 with
`{"status":"activation_required",...}` if Wolfram needs activation.

### 1.6 Smoke test

Two stages, both required:

1. **Mathematica load:** `Needs["FormCalc\`"]; Print[$FormCalcVersion]`.
2. **FORM round-trip:** a tiny `CalcFeynAmp` on a hard-coded one-diagram QED
   amplitude (drawn inline in the `.wls`). Asserts FORM was actually invoked
   (`form.log` non-empty, contains `Time = `).

Either stage failing → `FORMCALC_SMOKE_TEST_FAILED`.

### 1.7 Config keys written

`formcalc_path`, `formcalc_version`, `formcalc_installed_at`, `form_binary`,
`form_version`, `looptools_path`, `looptools_lib`, `looptools_version`,
`looptools_quad` (bool).

---

## 2. Usage skill — `/formcalc`

### 2.1 Subcommands

v1 ships **one action**: `reduce`. A `verify` subcommand is deferred — the
integration golden test is the verification in v1.

```
/formcalc reduce <model_name> \
  --process <process_id>        # references /feynarts output dir
  --reg {dimreg,dimred}         # default: dimreg (see §2.3)
  --gamma5 {naive,hv,bmhv,larin}  # REQUIRED if amplitude has chiral traces
  --fermion-chain {chiral,non-chiral}  # default: chiral
  [--force]                     # ignore cache
```

`dimreg` and `dimred` are the v1-supported regulators (covers the Arcadi–
Profumo paper plus MSSM users). `cdr` and `thv` (`--reg thv` for 't
Hooft-Veltman) are accepted but mapped to `dimreg` with a recorded caveat in
the sidecar until we validate them against a golden.

### 2.2 State layout

Under `$STATE_ROOT/models/<name>/formcalc/<process_id>/`:

```
.build_key                 # sha256(inputs); see §5
input/FeynAmpList.m        # symlink to /feynarts output
input/ProcessSpec.json     # symlink to shared spec
kinematics.m               # derived from ProcessSpec
amp_raw.m                  # CreateFeynAmp output (intermediate, for debug)
amp_reduced.m              # canonical output (abbreviations inlined)
amp_reduced.meta.json      # sidecar contract (§3.2)
run/<ts>/summary.json      # PV-func counts, timing, FORM log pointer
run/<ts>/form.log
run/<ts>/wolfram.log
run/<ts>/blockers.jsonl
```

### 2.3 γ₅ scheme — fatal, not recoverable

Per Manager decision. Pipeline logic:

1. Before `CalcFeynAmp`, run a static pass over the FeynAmpList counting
   γ₅-sensitive traces (FormCalc exposes `FermionChains` / `DiracTrace` that
   we inspect symbolically). If zero, `--gamma5` is optional.
2. If the amplitude has **any** γ₅-sensitive trace and `--gamma5` was not
   passed, emit fatal `FORMCALC_G5_SCHEME_REQUIRED` with `user_instruction`:

   > The amplitude contains γ₅-sensitive traces. Pass `--gamma5
   > {naive|hv|bmhv|larin}` explicitly. For an anomaly-free chain (e.g. full
   > SM fermion multiplet in the loop), `naive` is standard. For a single
   > chiral fermion trace, use `hv` (Breitenlohner–Maison / 't Hooft-Veltman)
   > or `bmhv` for full rigor. See FormCalc §3.

3. The chosen scheme is written into `amp_reduced.meta.json.gamma5` and into
   the cache key.

### 2.4 Blockers

| Code | Mode | Trigger |
|---|---|---|
| `FORMCALC_INPUT_MISSING` | fatal | `FeynAmpList.m` or `ProcessSpec.json` absent |
| `FORMCALC_G5_SCHEME_REQUIRED` | fatal | chiral trace + no `--gamma5` |
| `FORMCALC_KERNEL_ERROR` | fatal | `wolframscript` non-zero exit |
| `FORM_EXECUTION_FAILED` | fatal | FORM subprocess non-zero, parsed from `form.log` |
| `FORMCALC_NO_OUTPUT` | fatal | `amp_reduced.m` not produced despite zero exit |
| `FORMCALC_IR_DIVERGENT` | recoverable | PV reduction flagged `B0[0,0,0]` etc.; `/formcalc` handles |
| `FORMCALC_REG_UNVALIDATED` | recoverable | `--reg {cdr,thv}` used; mapped to dimreg, caveat recorded |

No `reference_only` branch. No recoverable γ₅.

---

## 3. Data contracts

### 3.1 Upstream (from `/feynarts`)

Two files, both symlinked into `input/`:

- `FeynAmpList.m` — Mathematica `FeynAmpList[...]` expression, the upstream
  canonical name. `/formcalc` reads this with `<<`.
- `ProcessSpec.json` — shared schema at
  `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json`. Fields:
  `process_id`, `feynarts_tuple`, `incoming[]`, `outgoing[]`,
  `kinematic_limit` (e.g. `{q2: 0, v: 0}`), `mandelstam` (derived),
  `loop_order`. All three skills (`/feynarts`, `/formcalc`, `/formcalc`) read
  this same file. Hash of its canonical JSON form is folded into the cache
  key.

### 3.2 Downstream (to `/formcalc`)

Per Manager decision: **two files, no magic header comments**. The sidecar is
the contract.

**`amp_reduced.m`** — Mathematica-readable expression with abbreviations
**inlined** (no `Abb1`/`Pair1` opacity surviving to disk) and PV heads in
FormCalc-native form (`A0i`, `B0i`, `C0i`, `D0i`). `/formcalc` **does not**
rename to LoopTools's `PVA`/`PVB`/…; that translation is owned by `/formcalc`
via a versioned rule set keyed on `meta.formcalc_version`. Rationale: keeps
`/formcalc` output legible for Mathematica users reading FormCalc docs, and
prevents a second translation if someone consumes `amp_reduced.m` directly.

**`amp_reduced.meta.json`** — sidecar. Schema:

```json
{
  "schema_version": 1,
  "producer": "formcalc",
  "formcalc_version": "10.0",
  "form_version": "4.3.1",
  "looptools_version": "10.0",
  "process_id": "chi_N_to_chi_N",
  "gamma5": "naive",
  "regularization": "dimreg",
  "fermion_chain": "chiral",
  "abbreviations_inlined": true,
  "pv_heads": ["B0i", "C0i"],
  "kinematic_limit": {"q2": 0, "v": 0},
  "ir_flags": [],
  "caveats": []
}
```

`/formcalc` **must** read the sidecar and assert-match
`schema_version`, `regularization`, `gamma5`. Mismatch → fatal in `/formcalc`.

---

## 4. Kinematics input format

Defined by `processspec.schema.json` (§3.1). Example file for the paper's σ_SI
(χN → χN at small q²):

```yaml
# ProcessSpec v1 — written by /feynarts, read by /formcalc and /looptools
process_id: chi_N_to_chi_N
feynarts_tuple: "{F[DM], F[N]} -> {F[DM], F[N]}"
incoming:
  - {label: chi, pdg: 5100022, mass_symbol: MDM}
  - {label: N,   pdg: 2112,    mass_symbol: MN}
outgoing:
  - {label: chi, pdg: 5100022, mass_symbol: MDM}
  - {label: N,   pdg: 2112,    mass_symbol: MN}
mandelstam:
  s: "(MDM + MN)^2"     # threshold; paper assumes v -> 0
  t: "-Q2"
  u: "2*MDM^2 + 2*MN^2 - s - t"
kinematic_limit: {q2: 0, v: 0}
loop_order: 1
```

`/formcalc`'s `prepare_kinematics.py` renders `kinematics.m` (FormCalc's
`OnShell`, `Mandelstam`, `Neglect` assignments) from this. No
`--mandel-invariants` flag — the spec file is the single source of truth.

`/feynarts`'s raw-tuple process-spec and `/formcalc`'s `<process_id>` reconcile
here: the tuple is stored in `feynarts_tuple` inside the JSON; the `process_id`
is the short alias used everywhere else.

---

## 5. Caching

Per Manager: cache on **input**, not output (FormCalc abbreviation naming is
not deterministic across Mathematica patch releases).

```
build_key = sha256(
    FeynAmpList.m  ||
    canonical_json(ProcessSpec.json)  ||
    --reg || --gamma5 || --fermion-chain ||
    formcalc_version || form_version
)
```

Written to `.build_key` in the process directory. On `/formcalc reduce`:

1. Compute `build_key`.
2. If `.build_key` matches and `amp_reduced.m` + `amp_reduced.meta.json` both
   exist, log `cache hit` and exit 0.
3. `--force` bypasses.

Matches `/spheno-build`'s `.build_key` discipline.

---

## 6. Test matrix

Three gates (critic's recommendation):

- `HEPPH_RUN_WOLFRAM_TESTS=1` — local Wolfram kernel, no network.
- `HEPPH_RUN_NETWORK_TESTS=1` — downloads (installer).
- `HEPPH_RUN_SLOW_TESTS=1` — integration (> 30 s).

### 6.1 Unit (always run)

- Argument parser (`--reg`, `--gamma5`, `--fermion-chain` validation).
- ProcessSpec JSON schema validation.
- `prepare_kinematics.py` → `kinematics.m` rendering (golden string match).
- Cache-key hash stability across reruns.
- Sidecar writer emits schema-valid JSON.
- Blocker emission: γ₅-required path emits exact fatal JSON.

### 6.2 Integration (gated `HEPPH_RUN_WOLFRAM_TESTS=1` + `HEPPH_RUN_SLOW_TESTS=1`)

**Golden: e⁺e⁻ → μ⁺μ⁻ at tree level (QED).**

Pipeline: `/feynarts` draws two s-channel γ + Z diagrams (Z dropped at
high-E → γ-only variant for the textbook limit) → `/formcalc reduce
--reg dimreg` → assert:

1. `amp_reduced.m` is non-empty, loads into Mathematica without error.
2. `amp_reduced.meta.json` validates against sidecar schema.
3. Compute |M|² symbolically via a test `.wls` helper; in the
   `s ≫ m_e, m_μ` limit and summed over final / averaged over initial spins,
   result must match the textbook `|M|² = e⁴(1 + cos²θ)`. Tolerance: exact
   symbolic equality after `Simplify`.

### 6.3 Installer tests (gated `HEPPH_RUN_NETWORK_TESTS=1`)

- `install` end-to-end on a scratch `$UserBaseDirectory`. Asserts
  `formcalc_path`, `form_binary`, `looptools_lib` all resolve.
- Offline mode: `HEPPH_NO_NETWORK=1` with missing cache → exact
  `FORMCALC_OFFLINE_CACHE_MISS` fatal.
- macOS-ARM platform branch: `looptools_quad: false` recorded.

### 6.4 Fixtures

Under `plugins/hep-ph-toolkit/skills/formcalc/tests/fixtures/`:
`ee_to_mumu/FeynAmpList.m`, `ee_to_mumu/ProcessSpec.json`, expected
`amp_reduced.meta.json` (sans timestamps), expected `|M|²` symbolic string.

---

## 7. Open questions (defaults picked, flagged for planners)

1. **FORM version pin.** Default `4.3.1` (latest stable as of FormCalc 10.0).
   Planner should confirm against FormCalc 10.0 release notes; override via
   `HEPPH_FORM_VERSION`.
2. **LoopTools bundled vs upstream.** Default: use bundled (FormCalc 10.0
   ships LoopTools 2.16). Override env var exists but untested path.
3. **Sidecar schema location.** Proposed:
   `plugins/hep-ph-toolkit/skills/_shared/amp_reduced.meta.schema.json`.
   Planner to confirm placement alongside `processspec.schema.json`.
4. **ProcessSpec ownership.** Written by `/feynarts`, read by `/formcalc` and
   `/formcalc`. Schema file location per §3; planner to assign PR for the
   schema addition.
5. **`cdr`/`thv` regulator support.** v1 accepts the flag but warns-and-maps
   to `dimreg`. Planner to decide whether to drop the flag entirely in v1 or
   keep for forward compatibility (recommendation: keep, it's a no-op in the
   parser).
6. **Pre-existing `form` on PATH.** Current default: ignore and use our own.
   Alternative (rejected for v1): adopt if version matches pin, which requires
   a `FORM_VERSION_MISMATCH` recoverable path. Revisit if users complain
   about the disk footprint.
7. **`/formcalc` rename rule ownership.** `B0i` → `PVB[0,0,…]` translation
   lives in `/formcalc`, keyed on `meta.formcalc_version`. Requires
   `/formcalc` to maintain a translation table per FormCalc major version.
   Alternative (rejected): do the rename in `/formcalc`; rejected because it
   would tie `/formcalc`'s output format to LoopTools's head names and break
   consumers reading `amp_reduced.m` directly from Mathematica docs.
8. **Fortran emission (deferred to v1.1).** Tracking item: when added,
   introduce `--output-mode` flag with `symbolic` (v1 default) and `fortran`
   (new); loop-order-zero + `fortran` rejected as
   `FORMCALC_TREE_FORTRAN_REJECTED` to preserve the `/madgraph` boundary.

---

## 8. Artefact checklist for implementation PR

- `plugins/hep-ph-toolkit/skills/formcalc-install/SKILL.md` +
  `scripts/install_formcalc.sh`, `probe_formcalc.wls`, `skill_env.yaml`.
- `plugins/hep-ph-toolkit/skills/formcalc/SKILL.md` +
  `scripts/run_formcalc.py`, `prepare_kinematics.py`,
  `run_calcfeynamp.wls`, `parse_summary.py`.
- `plugins/hep-ph-toolkit/skills/_shared/processspec.schema.json` (new,
  shared).
- `plugins/hep-ph-toolkit/skills/_shared/amp_reduced.meta.schema.json`
  (new, `/formcalc` → `/formcalc` contract).
- Extend `plugins/hep-ph-toolkit/skills/_shared/blocker.schema.json` known-
  codes enum with the §1.5 + §2.4 codes (or relocate enum to a shared
  location since it is no longer model-building-only — flag for planner).
- `plugins/feynman-diagrams/.claude-plugin/plugin.json` skills list update.
- `.claude-plugin/marketplace.json` version bump.
- Fixtures per §6.4.
