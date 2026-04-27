# MadDM wrapper workarounds

A catalogue of the non-obvious tricks `/maddm-install` and `/maddm` have to
apply because MadDM 3.2.13 (the latest upstream release, tagged 2023-07-16)
has not been ported to Python 3 and lags the current MG5 API. Every entry
lists: **symptom** (what you see if it's missing), **cause** (why it has to
exist), **mitigation** (what we do), and **where** (file:line where the
workaround lives, or `—` for items we chose not to patch).

Mirrors the style of `plugins/hep-ph-toolkit/skills/sarah-build/references/sarah-workarounds.md`.
If a future MadDM release ports to Python 3 and catches up to MG5's API, the
install-time items here (§ Install-time) can be dropped in one commit; the
usage-time items (§ Usage patterns) remain relevant as long as MadDM's CLI
flow behaves the way it does.

---

## Install-time workarounds (applied by `/maddm-install`)

Each patch here is a candidate for an upstream PR against
`github.com/maddmhep/maddm`. When one lands, delete the helper, bump the
sentinel version, and note the tag it went live in. Sentinel:
`.hepph_maddm_patches_applied_v2` inside the plugin directory.

Version history:
- **v1** — patches 1–3 (2to3 sweep, detab, `write_source_makefile` API).
- **v2** — added patches 4–6 (`run.inc` touch, `custom_fcts` param,
  `dummy_fct_file` class attr). All three surface during
  `launch` → `compile` → `write_include_file` on a relic-only run.
  Same root cause: MG5 3.5.6 consolidated several methods onto base
  `RunCard` that were previously only on `RunCardLO`/`RunCardNLO`;
  `MadDMCard` extends base `RunCard` directly and is now missing
  several attributes the base expects to access.

### 1. `2to3 -w -n` over the plugin tree

- **Symptom:** `__import__('PLUGIN.maddm')` aborts at module load with
  `SyntaxError: Missing parentheses in call to 'print'` (first hit in
  `maddm_interface.py:235`). MG5 `--mode=maddm` cannot start at all.
- **Cause:** MadDM 3.2.13 source is pure Python 2. Print statements
  (`print header + "=" * ...`), except-as-comma (`except ImportError, error:`),
  raise-with-comma (`raise DMError, 'msg'`). Upstream has not ported; both
  `github.com/maddmhep/maddm@v3.2.13` and the MG5-hosted
  `madgraph.phys.ucl.ac.be/Downloads/maddm/maddm_V3.2.13.tar.gz` are
  byte-identical P2 trees. MG5 itself does not run `2to3` during
  `install maddm`.
- **Mitigation:** Run `2to3 -w -n <plugin_dir>` (or `python3 -m lib2to3
  -w -n` on 3.13+ where `2to3` is removed from the default install) as the
  first step of `apply_maddm_upstream_patches`.
- **Where:** `scripts/install.sh` → `patch_maddm_py3_2to3`.

### 2. `expandtabs(8)` on two files 2to3 leaves with mixed indentation

- **Symptom:** After `2to3`, two files still refuse to `ast.parse`:
  `TabError: inconsistent use of tabs and spaces in indentation` at
  `init.py:93` and `Templates/plotting.py:65`.
- **Cause:** MadDM's source mixes tabs and spaces inside a single suite.
  Python 2 accepted this silently; Python 3's tokenizer rejects it at
  parse time. `2to3` does not normalise indentation, only syntactic forms.
- **Mitigation:** Apply `str.expandtabs(8)` in-place to the two files.
  `init.py` is not imported at plugin load (only by specific install
  helpers), and `Templates/plotting.py` is loaded lazily for plot
  generation — so without this, the failures would surface much later
  than install time. Fixing them at install flips the failure mode to
  catch-at-install, which the ast.parse sweep in `probe_maddm.sh`
  enforces.
- **Where:** `scripts/install.sh` → `patch_maddm_detab_files`.

### 3. `MGoutput.py:178`: add the `model` argument to `write_source_makefile`

- **Symptom:** `output` aborts mid-directory-tree with
  `TypeError: ProcessExporterFortranSA.write_source_makefile() missing
  1 required positional argument: 'model'`.
- **Cause:** MG5 3.5.6 changed the signature of
  `ProcessExporterFortranMEGroup.write_source_makefile` from
  `(self, writer)` to `(self, writer, model)` (see
  `madgraph/iolibs/export_v4.py:2863`). MadDM's `ProcessExporterMadDM`
  subclasses it but still calls the base with one argument. The
  surrounding `copy_template(self, model)` already has `model` in scope,
  so the fix is a one-token insertion.
- **Mitigation:** In-place substitution of
  `self.write_source_makefile(writers.FortranWriter(filename))` →
  `self.write_source_makefile(writers.FortranWriter(filename), model)`
  at `MGoutput.py:178`. Idempotent: the exact substring only appears
  in the unpatched form.
- **Where:** `scripts/install.sh` → `patch_maddm_mg5_api`.

### 4. `maddm_run_interface.py:3745`: touch `include/run.inc` before `write_include_file`

- **Symptom:** After `generate relic_density` + `output` succeed,
  `launch` prints `INFO: Start computing relic` then aborts with
  `FileNotFoundError: [Errno 2] No such file or directory:
  '<output>/include/run.inc'`.
- **Cause:** MG5 3.5.6's `banner.RunCard.write_include_file`
  unconditionally calls `write_autodef` (banner.py:3343), which
  unconditionally opens `<output_dir>/run.inc` (banner.py:3437) — *even
  when* the card has no `autodef=True` params. `MadDMCard` has zero
  such params and MadDM's output tree never writes `run.inc` (it has
  its own `maddm.inc`, `dm_info.inc`, etc.), so the open raises.
  The loop body would be a no-op if reached; the bug is that the read
  happens before the iteration check. See full trace in the
  `/Users/yianni/MG5_aMC_v3_5_6/MG5_debug` dump from the initial
  investigation.
- **Mitigation:** Touch an empty `include/run.inc` in MadDM's
  `compile()` before the `write_include_file` call. `write_autodef`
  then reads an empty string, finds no `! added by autodef` markers,
  iterates over zero params, and returns cleanly.
- **Alternative (not applied):** patch MG5's `banner.py:3437` to skip
  the read when `filetocheck[incname]` is empty. Cleaner as an
  upstream MG5 fix, but touches more install surface (banner.py is
  imported by every MG5 command) and we can't patch MG5 from
  `/maddm-install`.
- **Where:** `scripts/install.sh` → `patch_maddm_run_inc_touch`.

### 5. `MadDMCard.default_setup`: register `custom_fcts` param

- **Symptom:** After patch 4 lands, `launch` gets further then aborts
  with `KeyError: 'custom_fcts'` in `banner.py:3345`, inside
  `write_include_file` → `edit_dummy_fct_from_file(self["custom_fcts"],
  ...)`.
- **Cause:** MG5 3.5.6 moved the `custom_fcts` param out of
  `RunCardLO`/`RunCardNLO` (banner.py:3995, 5409) and now accesses
  `self["custom_fcts"]` unconditionally in the base `RunCard`'s
  `write_include_file`. `MadDMCard` extends `RunCard` directly, so the
  key is missing.
- **Mitigation:** Register the param as an empty `str`-typed list with
  `include=False` inside `MadDMCard.default_setup`, matching the
  LO/NLO default. MadDM doesn't support custom fct overrides, so empty
  is correct.
- **Where:** `scripts/install.sh` → `patch_maddm_custom_fcts`.

### 6. `MadDMCard`: declare `dummy_fct_file = {}` class attribute

- **Symptom:** After patches 4 and 5, `launch` aborts with
  `AttributeError: 'MadDMCard' object has no attribute 'dummy_fct_file'`
  in `banner.py:3160`, inside `edit_dummy_fct_from_file`'s cleanup
  loop (`all_files = set(self.dummy_fct_file.values())`).
- **Cause:** Same pattern as patch 5 — `dummy_fct_file` is a class
  attribute on `RunCardLO`/`RunCardNLO` (banner.py:3913, 5290) but
  not base `RunCard`. The cleanup loop runs even when `filelist` is
  empty (because it checks for *previously*-edited backups, not just
  the current call's filelist), so patch 5 alone doesn't short-circuit
  it.
- **Mitigation:** Declare `dummy_fct_file = {}` at class level on
  `MadDMCard`. MadDM doesn't override any MadEvent dummy functions,
  so an empty dict is correct.
- **Where:** `scripts/install.sh` → `patch_maddm_dummy_fct_file`.

### 7. Probe `__init__.py`, not `maddm.py`

- **Symptom:** Probe emits `MADDM_PATH_INVALID` on a fresh, otherwise-
  healthy upstream install.
- **Cause:** Our probe was authored expecting a `maddm.py` entry file.
  Upstream's plugin layout is `__init__.py` (module entry, loaded by
  MG5's `__import__('PLUGIN.maddm')`) plus a `maddm` *shell-script launcher*
  without a `.py` extension. No `maddm.py` file has ever existed in
  upstream, so the probe would have failed on every real install; this
  means the probe had never been end-to-end tested.
- **Mitigation:** Replace all 12 `maddm.py` references across `install.sh`,
  `probe_maddm.sh`, and `SKILL.md` with `__init__.py`. Fix was applied as
  part of the install-script rewrite.
- **Where:** `scripts/probe_maddm.sh`, `scripts/install.sh`, `SKILL.md`.

### 8. `<MG5_ROOT>/bin/maddm` launcher shim is optional

- **Symptom:** Probe emits `MADDM_SMOKE_TEST_FAILED` claiming
  `<MG5_ROOT>/bin/maddm` is missing or non-executable, but the plugin
  itself is fine.
- **Cause:** The canonical MadDM entry is `mg5_aMC --mode=maddm`, which
  doesn't need a dedicated launcher. The `bin/maddm` shim is a
  convenience only: our git-clone fallback path copies `PLUGIN/maddm/maddm`
  (the upstream-provided shell script) into `bin/` for direct
  invocation, but MG5's native `install maddm` flow doesn't create one,
  and `use-path` against an existing install may or may not have it.
- **Mitigation:** Downgrade the probe check from hard-fail to a single-
  line note on stderr. The ast.parse sweep (check 4 in the probe)
  remains authoritative for whether the plugin loads.
- **Where:** `scripts/probe_maddm.sh` — the "Check 2" block.

### 9. `ast.parse` sweep in the probe

- **Symptom:** Install reports success, but `mg5_aMC --mode=maddm` fails
  days later at import time with a fresh `SyntaxError` we didn't see
  coming.
- **Cause:** 2to3 handles all *known* Python 2 idioms but can be defeated
  by future upstream drift (e.g. f-string requirements on a pre-3.6
  residue, walrus operators, positional-only markers). Without a
  post-install sweep we learn about these only at runtime.
- **Mitigation:** `probe_maddm.sh` walks all `.py` files under the
  plugin dir (skipping `EffOperators/{COMPLEX,REAL}/`, which are
  generator artefacts — regenerated UFO model helpers — not loaded on
  plugin import) and calls `python3 -c 'import ast; ast.parse(...)'` on
  each. Any failure becomes `MADDM_SMOKE_TEST_FAILED`. Skips under a
  hard-coded 10-line cap so a catastrophic breakage doesn't flood the
  blocker payload.
- **Where:** `scripts/probe_maddm.sh` — the "Check 4" block.

---

## Usage patterns (non-obvious; not install-script-fixable)

These are things a downstream `/maddm` driver (or a Claude following
`/maddm` SKILL.md directly) needs to know. They would require changes to
the MG5 CLI or MadDM's own command dispatch to fix, not to the install.

### 10. `generate_maddm` is not a real command

- **Symptom:** Script line `generate_maddm` prints `Command not
  recognized, please try again` (as a warning, not an error), the
  script continues, and `output` later behaves as if no processes
  were generated — auto-adding relic + DD + ID + indirect_spectral_features
  in sequence, which then explodes on the first one the model can't
  support (see § 9 below).
- **Cause:** The command `generate_maddm` does not exist in
  `maddm_interface.py` (no `do_generate_maddm`). An earlier MadDM
  version may have had it, or it may have been aspirational
  documentation. Whatever the source, our `/maddm` reference skill and
  the `generate_maddm_script` helper in
  `plugins/hep-ph-toolkit/skills/maddm/scripts/maddm_run.py` both
  still reference it. MG5's base interpreter treats "unknown command"
  as a warning, not an error, so the script flow plows past it.
- **Mitigation:** Use `generate relic_density` directly when relic is
  the only observable needed (populates `_curr_amps`, skips auto-add).
  Use `generate direct_detection` / `generate indirect_detection`
  individually for those. If all three are wanted, chain
  `generate relic_density` + `add direct_detection` + `add
  indirect_detection` — but never `add indirect_spectral_features`
  unless the model supports loop-induced γγ/γZ/γh (see § 9).
- **Where:** — (usage-level; `maddm/scripts/maddm_run.py` still emits
  `generate_maddm`; worth updating).

### 11. `define darkmatter` takes a particle *name*, not a PDG id

- **Symptom:** `define darkmatter 9958431` fails with `DMError: 9958431
  is not a valid particle for the model.` at interactive-interpreter
  time.
- **Cause:** MadDM's `define darkmatter` parser expects a particle name
  (or `auto`) from the MG5-converted particle list, not a PDG id. This
  contrasts with MG5's built-in multiparticle `define` which accepts
  PDG ids freely.
- **Mitigation:** Pass the post-MG5-conversion name, e.g. `define
  darkmatter chi1`. Note MG5 lowercases UFO particle names during its
  "Change particles name to pass to MG5 convention" step — the UFO's
  `Chi1 = Particle(...)` becomes `chi1` in the MG5 namespace.
- **Where:** — (usage-level; relevant for any `/maddm` caller).

### 12. `add indirect_spectral_features` crashes on models without loop-induced γγ/γZ/γh

- **Symptom:** `IndexError: list index out of range` from deep inside
  MadDM's spectral-feature amplitude parser, after messages like
  "The current model SingletDoublet__REAL does not allow to generate
  loop corrections of type ['QCD']" and "ERROR: No amplitudes generated
  from process Process: chi1 chi1 > a h".
- **Cause:** Indirect spectral features (sharp γ-line signatures for
  indirect detection) are computed from loop-induced annihilation into
  two-body states containing a photon. Models whose UFO doesn't declare
  the relevant loop amplitudes — i.e. most tree-level BSM extensions
  including our SingletDoublet — have an empty amplitude list, which
  the downstream code indexes without checking.
- **Mitigation:** Don't issue `add indirect_spectral_features` unless
  the UFO was generated with loop support (NLO UFO from SARAH's
  `MakeUFO[Options -> "NLO"]`, or a dedicated loop-model). For the
  relic-only use case, `generate relic_density` alone is enough and
  doesn't trigger this path.
- **Where:** — (upstream bug, not patched; would need defensive checks
  in MadDM's `_has_spectral` path).

### 13. `output` triggers a blocking interactive install prompt for indirect-detection deps

- **Symptom:** First-ever `output` invocation pauses for 5–10 minutes
  while MG5 downloads pythia8, mg5amc_py8_interface, PPPC4DMID — even
  though the user only asked for relic density. The step after that
  tries to install `dragon` (cosmic-ray propagation, for indirect
  detection), which pulls `fitsio` from `heasarc.gsfc.nasa.gov`, which
  frequently times out with `curl: (56) Recv failure: Connection reset
  by peer` → `InvalidCmd: Installation of dragon failed`.
- **Cause:** `AskMadDMInstaller` (`maddm_interface.py:1863`) defaults all
  four optional deps to `install`. In non-interactive script mode there
  is no prompt to see, so the defaults apply. `output` runs this
  installer before the process-tree write, and any failed dep aborts
  the whole `output`.
- **Mitigation:** Use `generate relic_density` directly (per § 7). When
  `_curr_amps` is pre-populated, `do_output` skips the auto-add chain,
  and the installer is only reached for actual indirect-detection
  output — so a relic-only flow never hits this. If indirect *is*
  needed, answer `dragon off` and `dragon_data off` at the prompt
  (supply them as input-script lines following `output`; `mg5_aMC`'s
  interactive prompts consume from stdin in script mode). Pythia8 and
  PPPC4DMID are still installed but they're ~200 MB of downloads that
  do succeed.
- **Where:** — (upstream installer design; not patched).

### 14. `launch` echoes Planck constants that look like your result

- **Symptom:** During `launch`, MadDM prints `INFO: Omega h^2 =
  1.2000e-01 +- 1.2000e-03` *before* any compute happens. Looks
  exactly like the output format you were waiting for.
- **Cause:** That line is the *observed* Planck 2018 constraint MadDM
  loads from `ExpData/` for later comparison, not a computed result.
  The actual result, if the compute succeeds, is printed later with
  the same format but different numeric value.
- **Mitigation:** Awareness. The distinguishing cue is the preceding
  `INFO: Loaded experimental constraints. To change, use the set
  command` line. Anything after `INFO: Start computing relic` is a
  computed observable; anything between "Loaded experimental
  constraints" and "Start computing relic" is the constraint table.
- **Where:** — (upstream log prose; noted for log-parser authors).

---

## Known upstream bugs we worked around but chose not to patch

### 15. `import maddm_interface` needs the maddm dir on `sys.path`

- **Symptom:** `ModuleNotFoundError: No module named 'maddm_interface'`
  at `PLUGIN/maddm/__init__.py:3`.
- **Cause:** The plugin's `__init__.py` uses an unqualified absolute
  import (`import maddm_interface as maddm_interface`), which only
  resolves if the `maddm/` directory itself is on `sys.path`. This is a
  Python 2 idiom that Python 3 rejects more strictly. The fix would be
  either a relative import (`from . import maddm_interface`) or a
  `sys.path` shim.
- **Mitigation:** MG5 3.5.6's `--mode=maddm` loader sets up `sys.path`
  correctly via `__import__('PLUGIN.maddm')` in `bin/mg5_aMC:168`, so
  the import works when entered through MG5. Running MadDM outside MG5
  still fails. We did not patch because the failure mode is narrow and
  the fix is non-trivial across the ~20-module plugin.
- **Where:** — (work around by always invoking via `mg5_aMC
  --mode=maddm`, never `python3 -c 'import PLUGIN.maddm'`).

### 16. Two `SyntaxWarning: "is" with a literal` under Python 3.12+

- **Symptom:** `maddm_run_interface.py:3403` and `:3590` emit a
  `SyntaxWarning` at import time: `"is" with a literal. Did you mean
  "=="?`
- **Cause:** Both lines are `if len(energy_peaks) is 0:` — comparing an
  integer to a literal via `is`, which is implementation-dependent
  (CPython interns small ints but nothing guarantees it). Python 3.12
  started flagging this at compile time.
- **Mitigation:** None applied. The warning is noisy but harmless (CPython
  does intern 0). Would trivially fix to `== 0` but it's one more patch
  to carry for negligible benefit. Candidate for bundling into the
  upstream PR from § 1.
- **Where:** — (cosmetic; not patched).

### 17. Perl `Use of uninitialized value $interaction` warnings

- **Symptom:** During `output`, the Perl helper
  `output/Indirect_tree_cont/bin/internal/gen_cardhtml-pl` emits ~10
  lines of `Use of uninitialized value $interaction in split at …`
  followed by `… in scalar chomp …` and `… in concatenation …`.
- **Cause:** `gen_cardhtml-pl` (inherited from MG5 templates, not
  MadDM-specific) iterates over a `$interaction` that's empty for
  relic-only runs. Warnings are cosmetic; the HTML cards still
  generate correctly.
- **Mitigation:** None. Passing `2>/dev/null` suppresses; we don't.
- **Where:** — (cosmetic; MG5-level, not MadDM).

### 18. Dotted sibling in `PLUGIN/` breaks MG5's plugin loader

- **Symptom:** At MG5 launch (any `--mode`, including `mg5_aMC` and
  `maddm.py`), a red message appears:
  `error detected in plugin: maddm.broken-backup-2026-04-22` followed by
  `No module named 'PLUGIN.maddm.broken-backup-2026-04-22'`. Subsequent
  commands involving MadDM behave as if the plugin never loaded.
- **Cause:** MG5's plugin discovery (`bin/mg5_aMC:~168`,
  `__import__('PLUGIN.<name>')`) iterates entries in
  `<MG5_ROOT>/PLUGIN/` and treats every entry name as a dotted Python
  module path. A directory whose name contains a `.` (e.g. a backup
  sidecar from `/maddm-install` like
  `maddm.broken-backup-2026-04-22/`) is misparsed as
  `PLUGIN.maddm.broken-backup-2026-04-22` — a submodule of `maddm` that
  doesn't exist — and the import raises `ModuleNotFoundError` before
  any actual plugin code runs.
- **Mitigation:** Don't leave dotted backup directories in
  `<MG5_ROOT>/PLUGIN/`. If `/maddm-install` (or a manual reapply)
  creates one, move it out of `PLUGIN/` entirely — e.g. to
  `<MG5_ROOT>/_archived/` — rather than renaming within `PLUGIN/`. A
  leading underscore or dash in the dir name is not enough: MG5's
  listing is unfiltered.
- **Where:** — (install hygiene; `/maddm-install` should write backups
  outside `PLUGIN/`).

---

## Pointer: runtime observables and experimental constraints

The `/maddm` SKILL at
`plugins/hep-ph-toolkit/skills/maddm/SKILL.md` documents the happy-
path CLI flow and expected output parsing. It does **not** document
the workarounds above, deliberately — consumers of the SKILL want the
forward-flowing recipe, not the reasons each step exists. When items
here are fixed upstream or become install-script-defaults, delete from
this doc rather than migrating to SKILL.md.
