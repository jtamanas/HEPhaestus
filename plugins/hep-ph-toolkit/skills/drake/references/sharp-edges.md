# DRAKE Sharp Edges

Playtest-surfaced gotchas from the Dark SU(3) run (2026-04-25). Each entry names the
symptom, explains the root cause, and states the fix or workaround.

---

## SE-D-1 — Stock `test.wls` `$Path` issue (FU-WS-H-2)

**Symptom:** `wolframscript test.wls WIMP bm_WIMP settings_WIMP` exits 0 but prints
`Get::noopen: Cannot open DRAKE\``. DRAKE functions (`Oh2nBE`, `Stylef`, etc.) are
undefined. Runtime column in the MatrixForm row shows `0.` seconds.

**Root cause:** DRAKE_v1.0's stock `test.wls` invokes `<<DRAKE\`` before the DRAKE
root directory is on `$Path`. When `wolframscript` is launched from `$DRAKE_PATH/test/`,
the working directory is `test/`; `DRAKE.wl` lives one level up. Wolfram resolves
package names against `$Path`, which does not include `..` by default, so the `Get`
silently fails.

**Fix:** Apply `upstream-patches/test_wls_path.patch` before first use. The patch
inserts `AppendTo[$Path, ".."];` immediately before the `<<DRAKE\`` line in `test.wls`.
This is already vendored under
`plugins/hep-ph-toolkit/skills/drake/upstream-patches/test_wls_path.patch`.
The `scripts/run_drake.py` helper auto-applies this patch at first run if it has not
been applied yet.

**Do not** skip this patch and instead try to work around it by patching the
`Print` calls in `test.wls` — doing so would print literal unevaluated symbols
(`Oh2_nBE = Oh2nBE`) rather than computed values, and a regex match would silently
read nothing.

**Fixed in tier-1** (T1.5, landed on main at `5355461`).

---

## SE-D-2 — Preset bleed-through looks like a real solve (FU-WS-H-2)

**Symptom:** The MatrixForm output shows a `calculated` row with plausible-looking Ωh²
values (e.g. `0.12052366691892849`) even though DRAKE never loaded. The numbers match
the `preset` row to 17 significant digits.

**Root cause:** `test.wls` builds the `calculatedresult` list before loading
`test_res_bm_WIMP.wl`. Because `Oh2nBE`, `Oh2cBE`, `Oh2fBE` are undefined when DRAKE
fails to load, Wolfram stores the *symbols* in the list (not values). When
`Get["./test/test_res_bm_WIMP.wl"]` later executes, it assigns
`Oh2nBE = 0.12052...` (the hardcoded preset reference value). When `MatrixForm` prints,
the symbols in `calculatedresult` resolve to the preset values — byte-for-byte identical
to the preset row. Runtime is reported as `0.` seconds because no solver ran.

**Tell:** `runtime0 = 0.` (or below 0.5 s) in the MatrixForm `runtime` column. A real
nBE/cBE/fBE solve on the WIMP benchmark takes ~6 s on typical hardware.

**Sanity check rule:** before accepting any Ωh² value from a DRAKE run, verify that
the runtime entry is > 0 (at minimum > 0.5 s for the WIMP benchmark). If runtime is
`0.`, the package failed to load and all values are preset bleed-through.

---

## SE-D-3 — DRAKE never prints "Omega h^2" (FU-WS-H-1, FU-wsk-02)

**Symptom:** Regex patterns matching `Omega h^2`, `OmegaH2`, `Omega_h2`, or similar
fail to extract any value from DRAKE's stdout, even after a successful run.

**Root cause:** DRAKE prints relic density as `Oh2_nBE`, `Oh2_cBE`, and `Oh2_fBE`
(subscript-style labels). The string `Omega h^2` does not appear anywhere in the DRAKE
source tree. This was verified by `grep -rn "Omega" $DRAKE_PATH` — only internal
variable names and comments use the word "Omega"; no `Print` statement emits it.

**Fix:** Use the acceptance regex:
```
Oh2_(nBE|cBE|fBE)\s*=\s*([0-9eE.+\-]+)
```
Extract three values (`Oh2_nBE`, `Oh2_cBE`, `Oh2_fBE`) and report all three.
`Oh2_nBE` is the non-equilibrium Boltzmann result (most accurate for resonance regimes).

This regex was updated in T1.5 (landed on main at `5355461`). Do not revert to
patterns containing `Omega` — they will never match DRAKE stdout.
