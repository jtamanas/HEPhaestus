# t15-impl-2 — DRAKE regex fix + test.wls $Path patch

## Regex change

**Before** (wrong — DRAKE never prints this format):
```
Omega[\s_]*[hH]\^?2[^=]*=\s*[0-9]
```

**After** (correct — matches actual DRAKE stdout):
```
Oh2_(nBE|cBE|fBE)\s*=\s*([0-9eE.+\-]+)
```

Evidence: `/Users/yianni/drake/DRAKE_v1.0/test/test.wls` lines 41, 64, 75 show
DRAKE's actual Print statements:
```
Print[Stylef["Oh2_nBE = " <> ToString[Oh2nBE],Gray]];
Print[Stylef["Oh2_cBE = " <> ToString[Oh2cBE],ColorData[97,1]]];
Print[Stylef["Oh2_fBE = " <> ToString[Oh2fBE],Orange]];
```
DRAKE never prints `Omega h^2`. The old regex would never match.

### Files changed

1. `plugins/monte-carlo-tools/skills/drake/SKILL.md` — narrative section
   "Reading DRAKE output" updated (lines ~197-200)
2. `plugins/constraints/skills/dark-matter-constraints/contracts/router_contract.json`
   — `source_locator.pattern` for DRAKE row (was line 116)
3. `plugins/constraints/skills/dark-matter-constraints/tests/fixtures/drake/stdout_drake_synthetic.txt`
   — fixture rewritten to use Oh2_nBE/cBE/fBE format with realistic values
     from ws-h-impl-3 WIMP benchmark (Oh2_nBE = 0.12052366691892884)

## Vendored patch

File: `plugins/monte-carlo-tools/skills/drake/upstream-patches/test_wls_path.patch`

Contents: standard unified diff (`diff -u`) reconstructed from:
- Upstream original: stock DRAKE_v1.0/test/test.wls (reconstructed from known changes)
- Patched version: `/Users/yianni/drake/DRAKE_v1.0/test/test.wls` (as modified by ws-h-impl-3)

The patch applies two fixes:
1. **$Path fix**: Add `AppendTo[$Path, ".."]` and `AppendTo[$Path, "../src/"]` before
   `<<DRAKE`` so the Wolfram package loader finds DRAKE.wl.
2. **Global` context fix**: Assign `$ScriptCommandLine` values to `Global\`model`,
   `Global\`parameters`, `Global\`settings` (not bare symbols) to prevent
   `DRAKE\`Private\`` context shadowing after package load. Also applied to all
   downstream `Get[]` calls and the test_res_bm_ loader.

Upstream source: ws-h-impl-3 discovered this fix (dsu3-pt2/ws-h-r1-20260425,
commit 6aa5ab5). The patch was applied directly to the local DRAKE installation
outside the repo. No WS-H commit contains the diff itself.

To apply: `cd /path/to/DRAKE_v1.0 && patch -p1 < test_wls_path.patch`
(strip one prefix component since diff headers show `a/DRAKE_v1.0/test/test.wls`)
