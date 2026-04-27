# `/feynarts` — Final Design (Synthesizer)

Phase B, stage 1. Consumes either a SARAH state directory (post-hoc
`MakeFeynArts[]`) **or** a raw FeynArts `.mod` file. Emits a diagram PDF, a
`FeynAmpList.m` + `FeynAmpList.meta.json` sidecar pair for `/formcalc`, and a
`topologies.json` for future TikZ-Feynman hand-off. SARAH's output contract is
**frozen**: `/feynarts` never edits `/sarah-build` schema, templates, cache
keys, or goldens.

---

## 1. Plugin placement

**`plugins/feynman-diagrams/`** for the full Phase-B stack
(`/feynarts-install`, `/feynarts`, `/formcalc-install`, `/formcalc`,
`/formcalc-install`, `/formcalc`). `CLAUDE.md` names this category
"Diagram drawing & amplitude calculation" — amplitude calculation is literally
the label. Rejecting `plugins/model-building/` keeps that plugin focused on
SARAH/SPheno; rejecting a new `plugins/loop-computation/` avoids
over-proliferation. The existing placeholder `amplitude-calc` skill in
`feynman-diagrams/` is retired or becomes a thin dispatch doc.

Shared state (`blocker.schema.json` enum, cache-key discipline) moves from
`plugins/hep-ph-toolkit/skills/_shared/` to `plugins/shared/schemas/` in a
small preliminary PR before the three Phase-B skills land. `/feynarts` is the
first consumer of the new path.

---

## 2. `/feynarts-install`

**Version pin.** FeynArts **3.11** (2023). Override via
`HEPPH_FEYNARTS_VERSION`. URL
`https://feynarts.de/FeynArts-<VER>.tar.gz`. SHA256 `TODO` placeholder
honoured by `verify_checksum` in `plugins/shared/install-helpers/_common.sh`.

**Install location.** `$UserBaseDirectory/Applications/FeynArts-3.11/`.
Resolves to `~/Library/Wolfram/Applications/` on macOS and
`~/.WolframEngine/Applications/` on Linux — exactly the directory Wolfram
Engine auto-scans so `Needs["FeynArts`"]` works from any notebook *and* from
our own `wolframscript` drivers. Phase B standardizes every Mathematica
package (FeynArts, FormCalc, LoopTools) on this directory. SARAH's idiosyncratic
`~/SARAH/SARAH-<ver>/` layout is left alone; SARAH's `$Path` registration
continues to work via `AppendTo[$Path, "<sarah_path>/.."]`. The two
conventions coexist because SARAH is not a real Mathematica app; FeynArts is.

**Shared-install contract with `/sarah-install`.** SARAH's `MakeFeynArts[]`
requires FeynArts on `$Path` to resolve generic models (`Lorentz.gen`). Today
`/sarah-install` neither installs nor requires FeynArts because the non-goal
list (sarah-build/SKILL.md §Non-goals v1) excludes FeynArts output. Phase B
activates a second path: `/feynarts` runs `MakeFeynArts[]` itself against an
already-built SARAH state dir (§4). `/feynarts-install` documents in its
SKILL.md that any notebook-level `MakeFeynArts[]` (outside our skills) will
now succeed because FeynArts is reachable from `$UserBaseDirectory`.

**Subcommands.**

- `detect` — scan `$UserBaseDirectory/Applications/FeynArts*/` and
  `config.feynarts_path`. Emit `{"status":"configured"|"found"|"missing"|"ambiguous",…}`.
  If two installs resolve (e.g. a pre-existing system install plus ours),
  emit `FEYNARTS_AMBIGUOUS_INSTALL` fatal with both paths in `context`.
- `use-path <dir>` — register an existing install; smoke-test
  `Needs["FeynArts`"]; $FeynArtsVersion`. Writes
  `config.feynarts_path`, `config.feynarts_version`.
- `install [dir]` — disk probe → download → checksum → extract → smoke test →
  config merge. Default `dir` is the standard `$UserBaseDirectory/Applications/FeynArts-3.11/`.

**Config keys written.** `feynarts_path`, `feynarts_version`,
`feynarts_installed_at`, and `feynarts_generic_model_hash` =
`sha256(<feynarts_path>/Models/Lorentz.gen)`, required by `/feynarts` cache
composition (see §5).

**Blocker codes.** `WOLFRAM_KERNEL_ABSENT` (shared, fatal),
`FEYNARTS_DOWNLOAD_FAILED` (fatal), `FEYNARTS_SMOKE_TEST_FAILED` (fatal),
`FEYNARTS_PATH_INVALID` (fatal), `FEYNARTS_AMBIGUOUS_INSTALL` (fatal),
`FEYNARTS_ACTIVATION_REQUIRED` **(status, not blocker)** — mirrors
`/sarah-install`'s pattern so a fresh machine without Wolfram activation
surfaces as a JSON status on stdout rather than a fatal.

---

## 3. `/feynarts` — usage skill

**Subcommands.** Minimal: `generate` (the only v1 subcommand). `Paint[]`
output ships inline with `generate`; a separate `paint` subcommand is
deferred to v1.1 when `/draw-feynman` lands.

**Inputs — two model sources (SARAH-less path required):**

```
/feynarts generate \
  (--sarah-model <name> | --model-file <path> | --builtin <SM|SMQCD|THDM|MSSM>) \
  --initial "<particles>"  --final "<particles>" \
  [--loop-order 0|1]                               (default 0)
  [--exclude-topologies <class>[,<class>]]
  [--timeout <seconds>]                            (default 600)
  [--output-dir <dir>]
```

Model source precedence (mutually exclusive; reject multiple with
`FEYNARTS_MODEL_SOURCE_CONFLICT`):

1. `--sarah-model <name>`: requires `$STATE_ROOT/models/<name>/` to exist
   from `/sarah-build` (UFO/SPheno branch — **no change to `/sarah-build`**).
   `/feynarts` launches its own `wolframscript` that `<<SARAH`; Start[<Name>];
   MakeFeynArts[]` post hoc and emits `<Name>.mod` / `<Name>.gen` under
   `$STATE_ROOT/models/<name>/feynarts_state/` (distinct path from any output
   `/sarah-build` owns). Also reads
   `$STATE_ROOT/models/<name>/sarah/particles.m` for the alias table (§4).
2. `--model-file <path>`: treat as a pre-authored `.mod`. Copy into the run
   dir, validate with `FEYNARTS_MODEL_FILE_INVALID` fatal on parse failure
   or missing sibling `.gen`.
3. `--builtin <name>`: one of FeynArts's shipped models (`SM.mod`,
   `SMQCD.mod`, `THDM.mod`, `MSSM.mod`) resolved under
   `<feynarts_path>/Models/`. No state dir required; suitable for textbook
   examples and the tree-level golden test.

**Process spec — dual syntax.**

- **Alias form (default):** `--initial "chi0 chi0" --final "A A"`. Space- or
  comma-separated. Names resolved via a lookup table: (a) for `--sarah-model`,
  `particles.m` emitted by `/sarah-build` (pdg → FeynArts index); (b) for
  `--builtin`, a small hand-curated alias file shipped with the skill
  (`tables/sm_aliases.json`, `tables/thdm_aliases.json`); (c) for
  `--model-file`, the user supplies `--alias-file <path>` or falls back to
  raw form.
- **Raw form (power users):** `--initial "F[1],-F[1]" --final "V[1],V[1]"`.
  Auto-detected by presence of `[` in the string. Passed verbatim.

The resolved FeynArts tuple is written as a comment at the top of `driver.m`
so users learn the indexing. Unknown names emit
`FEYNARTS_PROCESS_UNKNOWN_PARTICLE` fatal listing known aliases.

**Decision flow.**

1. Prereqs: `feynarts_path` set, `wolfram_engine_path` set, model source
   resolves.
2. Cache check. Key =
   `sha256(.mod bytes) + "|" + sha256(.gen bytes) + "|" + feynarts_version +
   "|" + sha256(process_spec_canonical + loop_order + exclude_topologies) +
   "|" + feynarts_generic_model_hash`. Persisted at
   `<run_dir>/.feynarts_key`. Hit ⇒ `{"status":"cached"}`.
3. Render `driver.m` from template (`str.format`, per repo §2.10).
4. Invoke `wolframscript` with `--timeout` (SIGKILL at expiry → `FEYNARTS_TIMEOUT`
   fatal).
   ```
   Needs["FeynArts`"];
   t   = CreateTopologies[<loop>, nIn -> nOut, ExcludeTopologies -> ...];
   ins = InsertFields[t, <proc>, Model -> "<Name>", GenericModel -> "Lorentz"];
   nDiag = Length[ins];
   If[nDiag == 0,    Exit with FEYNARTS_EMPTY_RESULT recoverable];
   If[nDiag > cap,   Exit with FEYNARTS_TOO_MANY_DIAGRAMS fatal];
   Paint[ins, ColumnsXRows -> Automatic(*see below*), DisplayFunction -> ...];
   amp = CreateFeynAmp[ins];
   Put[{"schema_version"->1, "feynarts_version"->"3.11",
        "model_hash"->"<sha256>", "amp"->amp}, "FeynAmpList.m"];
   ```
5. Post-process: assert `FeynAmpList.m` round-trips via `Get`; stat its size
   against cap; emit `FeynAmpList.meta.json` sidecar (§3); write
   `topologies.json`; compute PDF layout.
6. Write cache key + update config.

**Paint layout.** `ColumnsXRows -> {Ceiling[Sqrt[n]], Ceiling[n/Ceiling[Sqrt[n]]]}`
with pages capped at 16 diagrams per page; multi-page PDF when needed.

---

## 4. Data contracts

**Inputs consumed.**

- `$STATE_ROOT/models/<name>/sarah/particles.m` (alias lookup, when
  `--sarah-model`; read-only; `/sarah-build` already writes it).
- `$STATE_ROOT/models/<name>/` state root (existence check only — the
  post-hoc `MakeFeynArts[]` runs against the cached SARAH session, no write
  under `sarah/` or `sarah_output/`).

**Outputs produced.** Under
`$STATE_ROOT/models/<name>/feynarts_runs/<process_hash>/` (or
`$STATE_ROOT/feynarts_runs/<process_hash>/` when not model-scoped):

| File | Purpose |
|---|---|
| `driver.m` | Rendered wolframscript input |
| `feynarts_state/<Name>.mod` + `<Name>.gen` | Only when `--sarah-model` (fresh MakeFeynArts output) |
| `diagrams.pdf` | Paint preview, auto-layout |
| `topologies.json` | `{n_external, topologies:[{edges:[{from,to,kind,particle}], …}]}` — informal v1 schema, formalised when `/draw-feynman` lands |
| `FeynAmpList.m` | `Put[{schema_version, feynarts_version, model_hash, amp}]` — the `/formcalc` handoff |
| `FeynAmpList.meta.json` | Sidecar: `{schema_version:1, feynarts_version, model_hash, process_spec, loop_order, n_diagrams, produced_at, canonicalizer_version}` |
| `feynarts.log` | wolframscript stdout+stderr |
| `summary.json` | `{n_topologies, n_diagrams, process, loop_order, cached:bool, wall_clock_s}` |
| `.feynarts_key` | Cache key line |

**Filename decision (coordinated with `/formcalc`).** The handoff file is
`FeynAmpList.m`. `/formcalc` reads this filename. Reason: matches FeynArts
conventional naming and FormCalc documentation; reject `amplitude.m`.

**Version-skew gate.** `/formcalc` reads the sidecar first, compares
`feynarts_version` against its own pin, and emits
`FORMCALC_FEYNARTS_VERSION_SKEW` fatal on mismatch. Phase-B compatibility
matrix (FeynArts 3.11 ↔ FormCalc 10.0 ↔ LoopTools) is pinned in
`plugins/hep-ph-toolkit/SHARED-feynman.md`.

---

## 5. Caps, timeouts, blockers

**Caps.**

- `FEYNARTS_TOO_MANY_DIAGRAMS` fatal, checked **before** `CreateFeynAmp`
  (cheap — `Length[ins]`). Default cap **2000 diagrams** (manager-specified),
  override via `HEPPH_FEYNARTS_DIAGRAM_CAP`.
- `FEYNARTS_AMP_TOO_LARGE` fatal, checked after `Put` via file size. Default
  cap **200 MB**, override via `HEPPH_FEYNARTS_AMP_SIZE_CAP_MB`. Refuses to
  write the cache key so a subsequent run re-triggers.
- `FEYNARTS_TIMEOUT` fatal at `--timeout` expiry, default **600 s**.
- `FEYNARTS_EMPTY_RESULT` **recoverable**: `Length[ins] == 0` is a legitimate
  physics answer (process forbidden in that model). Scan-friendly.

**Full blocker list.**

| Code | Mode |
|---|---|
| `FEYNARTS_ABSENT` | fatal |
| `FEYNARTS_MODEL_SOURCE_CONFLICT` | fatal |
| `FEYNARTS_MODEL_FILE_INVALID` | fatal |
| `FEYNARTS_SARAH_STATE_MISSING` | fatal |
| `FEYNARTS_PROCESS_UNKNOWN_PARTICLE` | fatal |
| `FEYNARTS_PROCESS_INVALID` | fatal (FeynArts log `InsertFields::nofields`) |
| `FEYNARTS_TOO_MANY_DIAGRAMS` | fatal |
| `FEYNARTS_AMP_TOO_LARGE` | fatal |
| `FEYNARTS_AMP_INVALID` | fatal |
| `FEYNARTS_PAINT_FAILED` | fatal |
| `FEYNARTS_TIMEOUT` | fatal |
| `FEYNARTS_EMPTY_RESULT` | recoverable |
| `FEYNARTS_ACTIVATION_REQUIRED` | **status** (stdout JSON, not a blocker) |

**No `reference_only` branch.** Per "augment not replace": FeynArts is the
whole point; a Python analytic fallback would defeat the skill. Documented
explicitly in SKILL.md.

---

## 6. Tests

- **Unit** (always on): `render_driver.py` (template → text), alias resolver
  (PDG-name → FeynArts tuple against a fixture `particles.m`), cache-key
  composer, process-spec tokenizer, sidecar JSON round-trip.
- **Integration, gated `HEPPH_RUN_WOLFRAM_TESTS=1`** (local kernel, no network):
  - **Tree-level golden:** `--builtin SM --initial "e+ e-" --final "mu+ mu-"
    --loop-order 0`. Exactly 1 diagram. Assert
    `summary.json.n_diagrams == 1` and `FeynAmpList.m` round-trips via
    `Get`. Committed golden sidecar.
  - **1-loop FeynArts example:** `--builtin SM --initial "Z" --final "Z"
    --loop-order 1` self-energy. Matches FeynArts docs (~5 topologies, 14
    diagrams at SM-QCD+EW). Assert topology count within tolerance; full
    amplitude is too big to byte-compare so check structural invariants
    (presence of loop momenta, all `FeynAmp` heads valid).
- **Gated `HEPPH_RUN_NETWORK_TESTS=1`** (installer): `install` subcommand
  downloads FeynArts 3.11 into a tempdir, smoke-tests, tears down.
- **SARAH-path integration, gated `HEPPH_RUN_WOLFRAM_TESTS=1` + SARAH installed**:
  consume the existing W2/W3 `dark_su3` SARAH state, run `--sarah-model
  dark_su3 --initial "psiD psiDbar" --final "gD gD" --loop-order 0`, assert
  non-empty result. This test depends on SARAH state but **does not modify
  W2/W3 goldens** — it reads `sarah/particles.m` and the completed state
  directory, writes only under `feynarts_runs/`.

---

## 7. Open questions — resolved

1. **SARAH GenericModel clash.** `/feynarts`'s driver forces
   `GenericModel -> "Lorentz"` from our installed FeynArts tree, ignoring
   any `Lorentz.gen` that may ship with a user-side SARAH. Hash of our
   `Lorentz.gen` enters the cache key so a FeynArts upgrade invalidates.
2. **Process spec ergonomics.** Resolved — dual syntax (alias + raw).
3. **Cache granularity.** Resolved — per-`(model, process, loop-order)`
   keyed on `.mod` + `.gen` + FeynArts version + generic-model hash +
   canonicalised process string.
4. **Reference-only fallback.** Resolved — none.
5. **Paint layout.** Resolved — auto-compute with 16-per-page cap.
6. **`/lagrangian-builder` dispatch keywords.** Explicit list handed to W5
   follow-up: `{"one-loop amplitude", "tree amplitude", "Feynman diagrams",
   "σ_SI loop", "direct-detection loop", "generate amplitude"}`. Extension
   owned by the orchestrator workstream, not Phase B.

Remaining minor items (non-blocking): TikZ-Feynman topology-JSON schema
formalisation in v1.1; whether `--builtin` alias tables ship under
`plugins/hep-ph-toolkit/skills/feynarts/tables/` or a shared location.
Default: skill-local under `tables/`, promote to shared in v1.1 if
`/formcalc` needs the same lookup.
