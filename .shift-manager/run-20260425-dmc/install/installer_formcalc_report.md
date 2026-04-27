# FormCalc Installer Report — run-20260425-dmc

**Status:** `INSTALLED_WITH_WARNINGS`

The FormCalc 9.10 Mathematica package and FORM 4.3.1 binary are installed and operationally verified. The skill script's run failed at exit 28 (`FORM_BUILD_FAILED`) due to a script bug; the install was completed by manual workarounds without editing the skill, per manager directive. LoopTools 9.10 does not exist; the skill_env.yaml premise was wrong. The standalone LoopTools 2.16 (already installed) is the correct LoopTools for FormCalc 9.10.

---

## Per-component summary

### FormCalc 9.10
- **Version:** 9.10 (16 Jan 2023)
- **Install path (Wolfram app):** `/Users/yianni/Library/WolframEngine/Applications/FormCalc-9.10`
- **Install root (skill convention):** `/Users/yianni/.local/share/hep-ph-agents/formcalc-9.10/FormCalc-9.10`
- **Tarball SHA256:** `352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b` (matches pin)
- **Smoke result:** PASS — `Needs["FormCalc`"]` succeeds, `$FormCalcVersion = "FormCalc 9.10 (16 Jan 2023)"`, `$ReadForm` resolves to a built executable, `$ReadFormHandle` opens the MathLink (LinkObject established).
- **C-side helpers built:** `MacOSX-ARM64/{ReadForm, ReadData, ToForm, ToFortran, ToC, reorder, util.a, form, tform}` — all present (see Bug 5).

### FORM 4.3.1
- **Version:** `FORM 4.3.1 (Apr 11 2023, v4.3.1) 64-bits` (verified via `form -v`)
- **Install path:** `/Users/yianni/.local/share/hep-ph-agents/formcalc-9.10/form/arm64-macos/form` (and `tform`)
- **Tarball SHA256:** `f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce` (matches pin)
- **Smoke result:** PASS — `form -v` returns version banner; binary registered as `form_binary` in config.

### Bundled LoopTools 9.10 (claimed)
- **Result:** DOES NOT EXIST upstream. `https://feynarts.de/looptools/LoopTools-9.10.tar.gz` returns HTTP 404. Current LoopTools is 2.16, distributed separately from FormCalc. The claim in `skill_env.yaml` ("LoopTools 9.10 — bundled in FormCalc tarball") is factually wrong: the FormCalc-9.10 tarball contains no `LoopTools/` subdirectory. The script's behavior — emitting `WARN: LoopTools source directory not found in FormCalc tarball. Skipping LoopTools build.` — is therefore correct on the actual upstream layout, but the warn is misleading because no such directory was ever shipped.
- **Resolution:** The standalone LoopTools 2.16 already installed at `/Users/yianni/LoopTools/LoopTools-2.16/lib/libooptools.a` is the canonical FormCalc-compatible LoopTools. Recorded as `formcalc_looptools_lib` (separate key from `looptools_path`). Not overwritten.

---

## Config keys written (live in `/Users/yianni/.config/hep-ph-agents/config.json`)

New keys (12):

| Key | Value |
|---|---|
| `formcalc_path` | `/Users/yianni/Library/WolframEngine/Applications/FormCalc-9.10` |
| `formcalc_version` | `9.10` |
| `formcalc_installed_at` | `2026-04-25T20:36:24Z` |
| `formcalc_tarball_sha256` | `352bff193be4472ce38bb266fcccb653c3dee21c49c6df6c5b784ff8ad53029b` |
| `formcalc_gfortran_path` | `/opt/homebrew/bin/gfortran` |
| `formcalc_gfortran_version` | `GNU Fortran (Homebrew GCC 15.2.0_1) 15.2.0` |
| `form_binary` | `/Users/yianni/.local/share/hep-ph-agents/formcalc-9.10/form/arm64-macos/form` |
| `form_tform_binary` | `/Users/yianni/.local/share/hep-ph-agents/formcalc-9.10/form/arm64-macos/tform` |
| `form_version` | `4.3.1` |
| `form_tarball_sha256` | `f1f512dc34fe9bbd6b19f2dfef05fcb9912dfb43c8368a75b796ec472ee8bbce` |
| `formcalc_looptools_lib` | `/Users/yianni/LoopTools/LoopTools-2.16/lib/libooptools.a` |
| `formcalc_looptools_version` | `2.16` |
| `formcalc_looptools_note` | `FormCalc 9.10 does not bundle LoopTools; using standalone LoopTools 2.16 already installed (see looptools_path key)` |

Keys preserved (NOT overwritten):
- `looptools_path = /Users/yianni/LoopTools/LoopTools-2.16`
- `looptools_version = 2.16`
- `looptools_src_path = /Users/yianni/LoopTools/LoopTools-2.16`
- `looptools_gfortran_path`, `looptools_gfortran_version`, `looptools_quad`, `looptools_mathlink_available`, `looptools_installed_at`

Note: the script's `config_merge` would have written `looptools_lib` and `looptools_quad` from the bundled-LoopTools build — but since no LoopTools was built in this run, those writes never happened. Pre-existing keys remain intact.

Pre-install config backup: `.shift-manager/run-20260425-dmc/install/installers/config.json.pre-formcalc.bak`.

---

## Disk

| Phase | Free in $HOME |
|---|---|
| Pre-install | 28 GiB |
| Peak (during build) | ~28 GiB (no measurable dip; install footprint < 250 MiB) |
| Post-install | 28 GiB |

Footprints:
- `~/.local/share/hep-ph-agents/formcalc-9.10/`: 141 MB (FormCalc tree + form/arm64-macos/{form,tform})
- `~/Library/WolframEngine/Applications/FormCalc-9.10/`: 96 MB (Wolfram-app copy with built C-side helpers)

Well under the 3 GiB / 5 GiB skill budget.

---

## Bugs filed (skill defects, worked around — NOT patched per manager directive)

### Bug FC-1: `$UserBaseDirectory` newline-collapse (the FeynArts MD-bug repeated)
**File:** `plugins/feynman-diagrams/skills/formcalc-install/scripts/install_formcalc_full.sh:114-117`
**Defect:** `wolframscript -code 'Print[$UserBaseDirectory]' | tr -d '\r\n'` collapses both the path AND the trailing `Null` (Print's return value) onto one line, yielding `/Users/yianni/Library/WolframEngineNull`. Same defect class as the FeynArts skill bug previously identified.
**Effect on this run:** install registered FormCalc at `/Users/yianni/Library/WolframEngineNull/Applications/FormCalc-9.10` and appended `WolframEngineNull/...` paths to init.m.
**Workaround:** symlink `~/Library/WolframEngineNull -> ~/Library/WolframEngine` created at install time so both path strings resolve identically. After install, edited `~/Library/WolframEngine/Kernel/init.m` to use the canonical path so downstream Wolfram sessions don't see a duplicated context. Symlink retained as a sentinel so any rerun of the buggy script still lands in the right place.
**Recommended fix (for skill author, when patching is permitted):** use `wolframscript -code 'Print[$UserBaseDirectory]'` followed by `head -1 | tr -d '\r'` — i.e. take only the first line. Or use `WriteString[$Output, $UserBaseDirectory]` to suppress the `Null`.

### Bug FC-2: `LOOPTOOLS_VERSION` and `looptools_version` premise wrong
**File:** `plugins/feynman-diagrams/skills/formcalc-install/skill_env.yaml:6` and `scripts/install_formcalc.sh:33` & `install_formcalc_full.sh:35`.
**Defect:** Both env yaml and scripts assume FormCalc bundles a LoopTools whose version equals the FormCalc version (`LOOPTOOLS_VERSION="${FORMCALC_VERSION}"` → `9.10`). LoopTools is distributed separately from FormCalc and is currently at version 2.16. There is no LoopTools 9.10. Furthermore, FormCalc-9.10's tarball contains no `LoopTools/` subdirectory — `install_formcalc_full.sh:144-151`'s search loop will always fail.
**Effect on this run:** `[install] WARN: LoopTools source directory not found in FormCalc tarball. Skipping LoopTools build.`
**Workaround:** wrote `formcalc_looptools_lib` and `formcalc_looptools_version` (= `2.16`) pointing at the existing standalone LoopTools 2.16 install. Did NOT touch `looptools_path`/`looptools_version`.
**Recommended fix:** drop the bundled-LoopTools claim. Either (a) split LoopTools into its own download step (URL: `https://feynarts.de/looptools/LoopTools-2.16.tar.gz`) and version-pin separately, or (b) document that `formcalc-install` is a no-op for LoopTools and require `looptools-install` to have run first; read `looptools_lib` from config.

### Bug FC-3: `build_form.sh` looks in wrong source subdirectory for FORM 4.3.1
**File:** `plugins/feynman-diagrams/skills/formcalc-install/scripts/build_form.sh:104`
**Defect:** Searches `$FORM_SRC_DIR/src/form`, `$FORM_SRC_DIR/form`, `$FORM_SRC_DIR/bin/form` — none of which exist in FORM 4.3.1's tarball. The actual binary builds to `$FORM_SRC_DIR/sources/form` (and `sources/tform`). Build succeeds, but the script then aborts with `FORM_BUILD_FAILED` because the binary is "missing", and the work_dir is wiped by the `trap 'rm -rf "$WORK_DIR"' EXIT`.
**Effect on this run:** install_formcalc_full.sh exited 28 (`FORM_BUILD_FAILED`); a clean FORM build was thrown away.
**Workaround:** rebuilt FORM 4.3.1 manually outside the trap, copied `sources/form` → `<install_root>/form/arm64-macos/form` and `sources/tform` → `<install_root>/form/arm64-macos/tform`. Verified `form -v` reports `FORM 4.3.1 (Apr 11 2023, v4.3.1) 64-bits`.
**Recommended fix:** add `"$FORM_SRC_DIR/sources/form"` and `"$FORM_SRC_DIR/sources/tform"` to the search list (first), and copy both binaries.

### Bug FC-4: `install_formcalc_full.sh` never runs FormCalc's `./compile` script
**File:** `plugins/feynman-diagrams/skills/formcalc-install/scripts/install_formcalc_full.sh` — missing step.
**Defect:** FormCalc's README says: "run ./compile to compile the C programs needed by FormCalc." The skill skips this. The result is that FormCalc loads but `Install[$ReadForm]` fails with `ReadForm::notcompiled` because the binaries aren't at `<appdir>/<$SystemID>/` — they're shipped only at `<appdir>/bin/<$SystemID>/`. This is a hard requirement: without ReadForm, no FORM-driven amplitude computation is possible.
**Effect on this run:** the skill's own `smoke_test.wls` would have shown `ReadForm::notcompiled` and the FormCalc kernel would only do tree-level symbolic work (no FORM bridge). I observed this on the first smoke pass.
**Workaround:** ran `DEST=MacOSX-ARM64 MCC="<engine_mcc_path>" bash ./compile` manually inside the FormCalc app dir. Built `ReadForm`, `ToForm`, `ToFortran`, `ToC`, `ReadData`, `reorder`, `util.a`, plus copied `form` and `tform` — all into `<appdir>/MacOSX-ARM64/`. This is what FormCalc expects (`$FormCalcBin = ToFileName[{$FormCalcDir, $SystemID}]`).
**Recommended fix:** after the FormCalc tarball is registered to the Applications dir and BEFORE the smoke test, run:
```bash
MCC="$(find "$WOLFRAM_BIN_PARENT/.." -name mcc -path '*CompilerAdditions*' 2>/dev/null | head -1)"
(cd "$APP_DIR" && DEST="$SYSTEM_ID" MCC="$MCC" bash ./compile)
```
where `SYSTEM_ID` is detected by mapping `uname` → `MacOSX-ARM64`/`MacOSX-x86-64`/`Linux-x86-64` (or via `wolframscript -code 'Print[$SystemID]'`, taking care to suppress `Null`).

### Bug FC-5: bundled smoke_test.wls uses a degenerate process (1→1, tree)
**File:** `plugins/feynman-diagrams/skills/formcalc-install/scripts/smoke_test.wls:38-41`
**Defect:** `CreateTopologies[0, 1 -> 1, ExcludeTopologies -> Internal]` for a photon (V[1]) self-energy at tree-level returns ZERO topologies (the SM has no tree V→V). With zero topologies, InsertFields/CreateFeynAmp return empty `FeynAmpList` objects whose `CalcFeynAmp` head is `Amp` only by accident. The test currently passes vacuously without ever calling FORM — the `SMOKE_WARN: form.log exists but contains no 'Time = ' marker` branch is unreachable because no `form.log` is produced.
**Severity:** lower — the smoke test as written DID exit 0 in our manual test. But it doesn't validate FORM is invoked. Recommend a 2→2 process such as `{F[2,{1}], -F[2,{1}]} -> {F[2,{2}], -F[2,{2}]}` (e- e+ → mu- mu+) which has 1 tree topology and exercises the FORM bridge.

### Bug FC-6 (CROSS-SKILL, observed during smoke): FeynArts InsertFields SIGSEGV with Wolfram Engine 14.3.0
**Where observed:** `Needs["FeynArts`"]; CreateTopologies[0, 2 -> 2]; InsertFields[..., Model -> "SM"]` reproducibly crashes the Wolfram kernel with SIGSEGV (exit 139) immediately after `loading generic model file .../Lorentz.gen`.
**Reproducer:** isolated FeynArts-only script (no FormCalc) — same crash. Independent of this install.
**Implication:** even with FormCalc, FORM, LoopTools, and FeynArts all installed and individually loadable, a real loop calculation that depends on FeynArts model loading will not run on this Wolfram Engine version. This is upstream FeynArts ↔ Wolfram Engine 14.3 incompatibility, not a FormCalc install defect. Should be filed against the `feynarts-install` skill or escalated to `/install` (Wolfram Engine).

---

## Workaround sentinels

For the closeout, the manager should list:

1. **Symlink:** `/Users/yianni/Library/WolframEngineNull` → `/Users/yianni/Library/WolframEngine`
   - Created at install time as Bug FC-1 workaround.
   - Retained — removing it would break any rerun of `install_formcalc.sh install` until the script bug is patched.
   - Removal command (when bug is fixed): `rm /Users/yianni/Library/WolframEngineNull`.

2. **Edit:** `/Users/yianni/Library/WolframEngine/Kernel/init.m` — line for FormCalc rewritten to use canonical path; FeynArts $Path append also added (FeynArts skill never registered itself on $Path; symptom surfaced during FormCalc smoke). This is a config edit, not a skill edit.

3. **Manual binaries:** FormCalc C-side helpers built in `~/Library/WolframEngine/Applications/FormCalc-9.10/MacOSX-ARM64/` are the fruit of a manual `./compile` run, not the skill. A re-run of `install_formcalc.sh install` would not reproduce them; it would copy the FormCalc tarball over the existing dir and lose them.

No new files under `plugins/shared/install-helpers/wolfram/` were needed; the symlink was sufficient and matches the established sentinel pattern.

---

## Recommendation: loop-SI chain readiness

**Status: not runnable end-to-end on this host as of 2026-04-25.**

Component table:

| Component | State | Comment |
|---|---|---|
| FeynArts 3.11 | INSTALLED but **CRASHES on InsertFields** | SIGSEGV when loading `Lorentz.gen`. Pre-existing, surfaces only with non-trivial process. Blocking. |
| FormCalc 9.10 | INSTALLED, package + C-helpers + ReadForm MathLink all OK | Operational from the FormCalc side. |
| FORM 4.3.1 | INSTALLED, `form -v` works | Operational. |
| LoopTools 2.16 (standalone) | INSTALLED previously | Library available for FormCalc to link against. |
| Package-X | UPSTREAM-DEAD | Unchanged from prior shifts: tarball must come from the user. The chain remains gated on this regardless of the FormCalc result. |

**Net move:** FormCalc + FORM + LoopTools is the first time these three are simultaneously present and self-test-passing on this host. That is real progress on the FormCalc side of the chain. **However**, the chain is not closer to runnable end-to-end because:

1. The previous gate (Package-X tarball missing) is unchanged.
2. A new gate has surfaced: FeynArts InsertFields crashes the Wolfram Engine 14.3 kernel during model loading. Without InsertFields, no FeynAmpList is produced, and FormCalc has nothing to chew on. This blocks BOTH the FormCalc-driven and the Package-X-driven paths.

**Suggested next moves (manager):**
- File a bug against `/feynarts-install` (or `/install`) for the InsertFields SIGSEGV. Likely fix paths: pin to a Wolfram Engine version known compatible with FeynArts 3.11 (13.x?), or apply the FeynArts patch from `https://feynarts.de` if one exists for 14.x.
- Patch the skill-script bugs FC-1 through FC-5 in a follow-up shift; the workarounds here are not robust against re-runs.
- Continue waiting on user-supplied Package-X tarball.

---

## Provenance

- Install log (full): `.shift-manager/run-20260425-dmc/install/installers/installer_formcalc.log`
- Pre-install config backup: `.shift-manager/run-20260425-dmc/install/installers/config.json.pre-formcalc.bak`
- This report: `.shift-manager/run-20260425-dmc/install/installer_formcalc_report.md`
- Time-box: 120 min budget; actual wall: ≈ 7 min (well under).
