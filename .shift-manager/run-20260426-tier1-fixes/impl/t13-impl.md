# t13-impl: higgstools driver bug fixes

## FU-wsj-01 — slha_adapter._parse_coupling_block

**File**: `plugins/constraints/skills/higgstools/scripts/slha_adapter.py`  
**Line range edited**: 118–154 (before) → 118–212 (after, +58 lines net in function)

### Before (bug)
```python
try:
    row_num = int(parts[0])   # ValueError on "1.01380" (float coupling value)
    n_neutral = int(parts[1])
    n_charged = int(parts[2])
    cp_flag = int(parts[3])
    vals = [float(p) for p in parts[4:]]
except (ValueError, IndexError):
    continue  # silently skips ALL PDG-triplet rows → empty couplings → SlhaMissingBlocksError
```

### After (fix)
Format detection: try `int(parts[0])` → SPheno row-index path (existing behaviour).
On failure or if decimal present → PDG-triplet path. PDG-triplet parses
`coupling_val nPDG PDG1 PDG2 [PDG3]`, merges entries by Higgs PDG code, populates
named fields (ww/zz/gg/bb/tt/tautau) by PDG vertex matching. INFO-level log diagnostic
when falling through to PDG-triplet branch.

### Smoke results
```
pytest plugins/constraints/skills/higgstools/tests/test_slha_adapter.py -v
13 passed (incl. TestCouplingBlockFormatDetection::test_spheno_rowindex_format_no_raise PASS,
            TestCouplingBlockFormatDetection::test_pdg_triplet_format_no_raise PASS)
```

---

## FU-wsj-02 — legacy_driver.run_higgsbounds

**File**: `plugins/constraints/skills/higgstools/scripts/legacy_driver.py`  
**Line range edited**: 190–205 (before) → 190–210 (after, +9 lines net)

### Before (bug)
```python
cmd = [hb_bin, "LandH", str(n_neutral), str(n_charged), slha_file]
# Arg positions: whichanalyses=LandH, whichinput=n_neutral, nHneut=n_charged,
#                nHplus=slha_file  → WRONG: missing "SLHA" as whichinput
```

### After (fix)
```python
slha_abs = os.path.abspath(slha_file)
slha_dir = os.path.dirname(slha_abs)
cmd = [hb_bin, "LandH", "SLHA", str(n_neutral), str(n_charged), slha_abs]
# Correct: whichanalyses=LandH, whichinput=SLHA, nHneut=n_neutral, nHplus=n_charged,
#          prefix=absolute .slha path  (HB-5 SLHA mode uses full path as filename)
# subprocess.run(..., cwd=slha_dir) so HB can write output files alongside input
```

Note: `os.path.splitext` / stem was NOT used. HB-5 SLHA mode uses `infile1` directly
as the filename in `open(file, file=trim(infile1))` — the full path including `.slha`
extension is correct. Passing the bare stem (no extension) causes "problem opening
SLHA file" errors.

### HB smoke results
```
cmd: HiggsBounds LandH SLHA 3 1 /tmp/hb_2hdm/2hdm_type2_benchmark.slha
exit code: 0  (success / allowed)
HBresult: 1 (allowed)
obsratio: 0.0
```
obsratio=0 is expected: HB-5 native parsing requires `Block HiggsCouplingsBosons`
(new HB-5 format), not `Block HiggsBoundsInputHiggsCouplingsBosons` (old SPheno
format used in the 2HDM fixture). The fix validates the binary invocation is correct
and HB exits cleanly.
