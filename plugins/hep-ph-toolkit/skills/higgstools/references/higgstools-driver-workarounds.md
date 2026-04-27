# HiggsTools driver workarounds

A catalogue of sharp edges in `slha_adapter.py` and `legacy_driver.py`
surfaced during the WS-J playtest (`dsu3-pt2/ws-j-r1-20260425`) and
fixed in tier-1 patch T1.3 (branch `tier1/t13-higgstools-driver-r1-20260426`,
merged at commit `5355461`).

Every entry lists: **symptom**, **cause**, **fix** (with tier-1 status),
and the **FU-id**.

Mirrors the style of
`plugins/hep-ph-toolkit/skills/micromegas-install/references/micromegas-workarounds.md`.

---

## 1. SLHA coupling-block format auto-detection

- **FU-id:** FU-wsj-01

- **Status:** Fixed in tier-1 (T1.3, commit `5355461`).

- **Two formats exist:**

  | Producer | Format | Col-0 content |
  |---|---|---|
  | SPheno | Row-index format | Integer row index (`n_Higgs`, `n_neutral`, `n_charged`, CP, vals…) |
  | FeynHiggs / HiggsSignals example files | PDG-triplet format | Floating-point coupling value, followed by nPDG, PDG1, PDG2, PDG3 |

- **Symptom (before fix):** On a FeynHiggs-style SLHA (PDG-triplet
  block), `slha_adapter._parse_coupling_block` raised `ValueError` on
  line 1 (col-0 is a float, not an int), swallowed the error in a bare
  `except (ValueError, IndexError): continue`, and returned an empty
  dict. The driver then raised `SlhaMissingBlocksError` — even though
  the `HiggsBoundsInputHiggsCouplingsX` blocks were present. The block
  names were correct; the parser was wrong about the layout.

- **Root cause:** `_parse_coupling_block` hardcoded the SPheno
  row-index layout (col-0 = int row counter) without checking which
  convention the block uses. Both layouts are valid SLHA2; which one
  appears depends on the tool that generated the file.

- **Fix (T1.3):** `_parse_coupling_block` now probes col-0 of the
  first data row:
  - If `int(parts[0])` succeeds and the value is ≤ the expected number
    of Higgs states → SPheno row-index path.
  - Otherwise → PDG-triplet path (col-0 is the coupling value;
    remaining cols are `nPDG PDG1 PDG2 PDG3`).

  **Auto-detection contract for future SLHA emitters:**
  - SPheno row-index: first field on every data line is a small integer
    (≤ number of neutral/charged Higgs states). The integer is consumed
    as a row counter and must not collide with a coupling value that
    happens to round to a small integer.
  - PDG-triplet: first field is a floating-point coupling value. Lines
    with `|col-0| ≥ 10` are treated as PDG-triplet without ambiguity.
    Lines with `0.0 ≤ |col-0| < 10` are ambiguous; the parser uses the
    total column count (4 vs. 5+) as a tiebreaker.
  - If you are writing a new SLHA producer: emit the row-index format
    (SPheno convention) unless you specifically target the
    FeynHiggs/HS-example conventions. Do not emit bare coupling values
    as col-0 on blocks with ≤ 4 columns — that is the ambiguous region.

---

## 2. HB-5 SLHA mode requires full path with `.slha` extension, not a stem

- **FU-id:** FU-wsj-02

- **Status:** Fixed in tier-1 (T1.3, commit `5355461`).

- **Symptom (before fix):** `legacy_driver.run_higgsbounds` called the
  HB-5 binary as:

  ```bash
  HiggsBounds LandH <n_neutral> <n_charged> <prefix>
  ```

  The HB-5 binary signature is:

  ```
  HiggsBounds <whichanalyses> <whichinput> <nHneut> <nHplus> <prefix>
  ```

  Argument 3 (`whichinput`) was **omitted** — `n_neutral` was parsed by
  HB as `whichinput`, and `slha_file` (a full path) ended up in the
  wrong slot. Results were garbage or an immediate crash.

- **Two sub-issues collapsed into one fix:**
  1. The `whichinput` argument was missing entirely from the command
     line.
  2. The brief originally specified passing a *stem* (filename without
     extension) as `<prefix>`. HB-5 with `whichinput=SLHA` expects the
     **full path including the `.slha` extension**, not a stem. The
     `<prefix>.dat` resolution path applies only to the older
     table-input mode (`whichinput=hadr` / `whichinput=part`), not to
     SLHA mode.

- **Fix (T1.3):** `legacy_driver.py` now:
  1. Inserts `whichinput=SLHA` as the second positional argument.
  2. Sets `cwd=slha_dir` so relative paths resolve correctly.
  3. Passes `os.path.abspath(slha_file)` as `<prefix>` — the full path
     with `.slha` extension preserved.

  **Rule for future maintainers:** Never strip the `.slha` extension
  when calling HB-5 in SLHA mode. The `<prefix>` slot in SLHA mode is
  literally the full file path. Only in legacy table mode is `<prefix>`
  a stem.

---

## 3. 2HDM+a SPheno binary not built by default — fallback to FH example SLHA

- **FU-id:** FU-wsj-03

- **Status:** Known limitation; fallback accepted per scope
  (WS-J §3.3 / §6 line 21).

- **Symptom:** When the driver is pointed at a 2HDM+a model directory,
  no `SPheno` executable is found in
  `~/.local/share/hephaestus/models/two_hdm_a/` or its subdirs.
  The `runs/` directory does not exist. No spectrum SLHA is available.

- **Cause:** Building the 2HDM+a SPheno binary requires running SARAH
  (`/sarah-build`) to produce Fortran source and then compiling with
  `/spheno-build`. This step was not completed in the WS-J playtest
  scope.

- **Accepted fallback:** Use the FeynHiggs example SLHA shipped with
  the HiggsSignals tarball:

  ```
  ~/HiggsSignals-2.6.2/example_data/SLHA/SLHA_FHexample.fh.1
  ```

  This file contains the full `HiggsBoundsInputHiggsCouplingsX` blocks
  in PDG-triplet format and exercises the same code path that a real
  2HDM+a SPheno SLHA would. **Users should not interpret a successful
  run against this fallback as 2HDM+a phenomenology** — it is an MSSM
  benchmark point from FeynHiggs.

- **To get real 2HDM+a coverage:** Run `/sarah-build` for 2HDM+a, then
  `/spheno-build` with `WriteHiggsBoundsBlocks=True` in `SPheno.m`.

- **Driver behavior:** If `config.models[<name>].latest_slha` is absent
  and no `--slha` is passed, the driver emits a recoverable notice and
  skips. This is expected behavior, not a driver bug.
