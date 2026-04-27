# SAxDynkin leakage — investigation notes

Standing notes on SARAH's `SA\`Dynkin` / `SA\`DynL` / `SA\`Casimir` /
`SA\`MulFactor` leakage into emitted Fortran and the intermediate
Mathematica files. Supersedes the sparse mention in
`sarah-workarounds.md` § 6.

Reporting this as an open bug with partial diagnosis, not a solved fix.

---

## What the leakage looks like

At the Fortran layer (`sarah_output/SPheno/<Name>/RGEs_<Name>.f90`):

```fortran
betag11 = (g1p3*(39 + 4*$Failed*SAxMulFactor(2,hypercharge)))/10._dp
betag21 = (g2p3*(-21 + 4*SAxDynkin(2,left)*SAxMulFactor(2,left)))/6._dp
betag31 = (g3p3*(-21 + 2*SAxDynkin(2,color)*SAxMulFactor(2,color)))/3._dp
```

These symbols **are not valid Fortran** — `gfortran` aborts compile with
`Error: Symbol 'color'/'left' has no IMPLICIT type`. `SAx*` is SARAH's
naming pattern for `` SA`* `` symbols with backticks replaced by `x`
(applied by SARAH's own Fortran serialiser, not a hephaestus
helper).

The emitted Fortran is downstream of a Mathematica intermediate. The
same unevaluated symbols are present in the intermediates:

- `sarah_output/.../RGEs/BetaGauge.m` — gauge-coupling beta functions
- `sarah_output/.../RGEs/GijF.m`      — wavefunction-renormalisation
  anomalous dimensions per field

So this is not a Fortran-serialiser bug; it's a group-theory-table
resolution bug upstream of the writer.

---

## Bisection — known-clean vs known-broken builds

Several `Output/SingletDoublet.iter*-stale/` directories are preserved
under `$SARAH_PATH/Output/`. They were produced during the T15a cycle
on 2026-04-20 evening:

```
iter2-stale  (23:18)  SAxDynkin=0  $Failed=0  lines=881   CLEAN
iter3-stale  (23:19)  SAxDynkin=0  $Failed=0  lines=881   CLEAN
iter4-stale  (23:21)  SAxDynkin=0  $Failed=0  lines=881   CLEAN
iter5-stale  (23:26)  SAxDynkin=8  $Failed=8  lines=885   BROKEN
iter6-stale  (23:29)  SAxDynkin=8  $Failed=8  lines=885   BROKEN
pre-rerun    (06:43)  SAxDynkin=0  $Failed=0  lines=881   CLEAN
```

The break is introduced between iter4 and iter5 (a ~5-minute window)
and persists through iter6. `pre-rerun` is clean — presumably a
different spec path.

### Telltale diff

The iter4 → iter5 delta in `RGEs/GijF.m` is small and specific. Iter4
for the SM lepton doublet:

```mathematica
{{l[{1}][{i1}], l[{lef2}][{i2}]},
 (3*(g1^2 + 5*g2^2)*Xi*Kronecker[1, lef2]*Kronecker[i1, i2])/20
   + MatMul[Tp[Ye], conj[Ye]][i1, i2]/2, 0}
```

Iter5 for the same field:

```mathematica
{{2[{1}][{i1}], 2[{lef2}][{i2}]},
 g3^2*Xi*SA`Casimir[2, color]*Kronecker[1, lef2]*Kronecker[i1, i2]
  + g2^2*Xi*SA`Casimir[2, left]*Kronecker[1, lef2]*Kronecker[i1, i2]
  + (3*g1^2*Xi*SA`DynL[2, hypercharge]^2*Kronecker[1, lef2]*Kronecker[i1, i2])/5
  + MatMul[Tp[Ye], conj[Ye]][i1, i2]/2, 0}
```

Two concurrent changes:

1. The **SM lepton-doublet field symbol `l` has been replaced by the
   integer `2`** (the field name in position 1 of the entry). No other
   field (`q`, `PsiDL`, etc.) is affected.
2. The **scalar Dynkin and Casimir factors are unevaluated** —
   `SA\`DynL[2, hypercharge]^2`, `SA\`Casimir[2, left]`,
   `SA\`Casimir[2, color]` — instead of reducing to rational numbers
   (for `l`: `C_2(left_doublet) = 3/4`, `DynL(hyper)^2 = (1/2)^2 = 1/4`,
   `C_2(color_singlet) = 0`).

Similar unevaluated forms propagate up into `BetaGauge.m`:

```
iter4: {{g1, (9*g1^3)/2, 0}, {g2, (-5*g2^3)/2, 0}, {g3, -7*g3^3, 0}}
iter5: {{g1, (g1^3*(39 + 4*SA`DynL[2, hypercharge]^2*SA`MulFactor[2, hypercharge]))/10, 0},
        {g2, (g2^3*(-21 + 4*SA`Dynkin[2, left]*SA`MulFactor[2, left]))/6, 0},
        {g3, (g3^3*(-21 + 2*SA`Dynkin[2, color]*SA`MulFactor[2, color]))/3, 0}}
```

---

## Where SARAH populates its Dynkin table

`SARAH-4.15.3/Package/init.m`:

- **~1197–1208**: gauge/gaugino adjoint reps. Fires for every gauge
  group. Populates `SA\`Dynkin[V<gauge>, <kind>]` by name.
- **~1250–1253**: matter-field reps via `SA\`CasimirList`. Loops over
  `SA\`CasimirList[[i]]` and writes three keys per entry: by
  `getBlank[getBlank[SFields[[i]]]]`, by `Fields[[i,3]]` (component
  list), by `"S"<>ToString[Fields[[i,3]]]`.
- **838–839** (commented out in 4.15.3): older matter-field `SA\`DynL`
  population. Disabled upstream — not available as a fallback.

Lookup-time rewrite: `SARAH-4.15.3/Package/RGEs/mathRGEs.m:300`

```mathematica
SA`Dynkin[a_, b_] := SA`Dynkin[getBlankSF[a], b]
    /; (FreeQ[a, List] == False && FreeQ[a, Symbol] == False)
```

Note the guard: if `a` is a bare integer (no `List` head, no `Symbol`
in its tree — both `FreeQ` return `True` → guard `== False` fails),
the rewrite does **not** fire. So `SA\`Dynkin[2, left]` stays as-is
forever — there is no fallback to "2 means the SU(2) fundamental."

This matches the iter5 output: once the field symbol `l` is replaced
by `2`, the lookup has no name to canonicalise and the Dynkin stays
symbolic.

---

## Leading hypotheses (not yet confirmed)

### H1 — `SA\`CasimirList` is empty or mis-populated for our model

If the loop at init.m:1250 iterates over an empty or wrong-shape
`SA\`CasimirList`, the matter-field Dynkin table is never written.
Every later `SA\`Dynkin[...]` lookup then returns unevaluated.

Test: dump `SA\`CasimirList` at the end of `Start["SingletDoublet"]`
and compare clean vs broken spec.

### H2 — A rewrite rule in our rendered template globally rewrites `l`

In Mathematica, `l → 2` would literally flip every occurrence of the
symbol `l` in every expression. Could happen if something in our
`SingletDoublet.m`, `parameters.m`, or `particles.m` assigns `l = 2`
or writes `l -> 2` at global scope. Grepping the current
`~/.local/share/hephaestus/models/singlet_doublet/sarah/*.m` files
does not reveal an obvious assignment, but a dummy-index
`Sum[..., {l, 1, N}]` loop leaking `l` into Global context is a
plausible vehicle.

Test: after `Start["SingletDoublet"]`, evaluate `?l` in the kernel
and check if `l` has an `OwnValue`.

### H3 — `CheckModelFiles::MissingParameter` silently degrades
matter-rep registration

Gotcha #6 in `sarah-build/SKILL.md` documents a similar "silent
degradation" where a missing `ParameterDefinitions` entry causes
downstream emission to use `Param.$Failed`. The iter5 output **does**
contain `$Failed` in the hypercharge slot
(`39 + 4*$Failed*SAxMulFactor(2,hypercharge)`) — strong suggestion
that the same class of failure is producing the `SAx*` leakage too.

Test: run SARAH with `SARAH`Verbose = True` and grep the log for
`CheckModelFiles::MissingParameter` or `Param.$Failed` that got past
the render guards.

---

## Recommended reproducer (empirical bisection)

Rather than continue reading the SARAH Mathematica, the fastest path
to a root cause is an empirical bisection from a known-clean model to
our broken one:

1. Start with SARAH's shipped `Models/SM+VL/PortalDM/`. Confirm it
   emits a clean `RGEs_SM+VL-PortalDM.f90` (no `SAx*`, no `$Failed`).
2. Apply one change at a time toward our singlet-doublet template:
   - rename `PSIL`/`PSIR` → `PsiDd`/`PsiDu` (single-Weyl Hu/Hd)
   - rename singlet `S` → `FS`
   - add `Global[[1]] = {Z[2], DMParity}` + per-field parity column
   - split single Yukawa `y` → `yh1`, `yh2` (two contractions)
   - add the `mass_eigenstate_rh` / `UM, UP` distinct-ME convention
3. Run `make_output.sh` after each change. The change that first
   introduces `SA\`Dynkin[N, ...]` symbolic output is the trigger.

Our `/sarah-build` test harness already has the scaffolding
(`tests/test_e2e_sarah.py`, `scripts/regenerate_fixture.py`) to drive
this — adapt them rather than hand-run.

Each candidate change corresponds to a commit in the
`fix/sarah-singlet-doublet-hud-formulation` branch (master-sha: 05aba54).
Walking the git history on that branch in chronological order is the
same bisection.

---

## What's already protected downstream

`plugins/hep-ph-toolkit/skills/sarah-build/scripts/scan_outputs.py`
(committed 2026-04-21 22:45 EDT) greps emitted `.f90` and `.py` for
the `SAxDynkin(`, `SAxDynL(`, `SAxMulFactor(`, `SAxCasimir(`, and
`$Failed` patterns. On hit it raises `SARAH_OUTPUT_CORRUPT` fatal
before `/sarah-build` stamps the cache. Builds before that commit
(e.g. our currently cached `2026-04-22T00:59:00Z` build) predate the
scanner, which is why the cache got stamped despite leakage — a
`/sarah-build --force` on the same spec today would correctly block.

So the pipeline no longer *trusts* a leaky emission; it just doesn't
yet know how to prevent it at emission time.

---

## Cross-references

- `sarah-workarounds.md` § 6 — pattern catalog + scanner hook.
- `SKILL.md` § "Gotchas (SARAH-idiom discrepancies)" #4 — single-letter
  BSM field names, the only already-known path to `l`-like shadowing
  (but `l` itself is an SM field, not a BSM one — so #4 alone doesn't
  explain this).
- Memory (auto-memory): `reference_sarah_failed_emission.md` —
  predecessor note declaring the trigger shape "TBD". This doc is
  intended to supersede that memory entry once the trigger is pinned
  down.

---

## 2026-04-22 follow-up — H1 and H2 empirically falsified

Spent a session probing SARAH's kernel state directly with a staged
`Private-Models/SingletDoublet/` copy of the current assets and a
pair of `wolframscript` driver files. Results below. Bisection plan
from § "Recommended reproducer" was NOT executed — the empirical
probes and a race-condition timeline argument turned out to be more
productive than walking PortalDM forward.

### What the kernel probes said

Driver: `Start["SingletDoublet"]` → optionally `MakeSPheno[ReadLists->False]`
→ print state. Both with and without an RGE pass:

- `OwnValues[l] = {}`, `DownValues[l] = {}`, `ValueQ[l] = False`,
  `Context[l] = "SARAH`"`. **`l` is NOT globally shadowed** — the
  symbol has no assignment at any observable point in the pipeline.
  Kills H2.
- `SA\`Dynkin[l, left] :> 1/2`, `SA\`Casimir[l, left] :> 3/4`,
  `SA\`DynL[l, hypercharge] :> -1/2` are all present in `DownValues`.
  Same for `q`, `PsiDd`, etc. **The matter-rep Dynkin table IS
  populated for `l`.** Kills H1.
- `SA\`CasimirList = {}` (length 0), matching the broken run. This
  turns out to be a red herring — the table gets populated through
  `init.m:1250`'s immediate assignments, not through
  `CasimirList`. So H1's specific mechanism was wrong in addition to
  its conclusion being wrong.

### The cache is leaky but fresh builds are clean

Tested the current assets end-to-end:

```
cached:   ~/.local/share/hephaestus/models/singlet_doublet/
            sarah_output/SPheno/SingletDoublet/RGEs_SingletDoublet.f90
          stamped 2026-04-22 06:38 — 1006 lines — 10 SAx*/$Failed hits
fresh:    wolframscript MakeSPheno[ReadLists->False] from the same
          staged inputs, Output/SingletDoublet/ wiped first
          —  1002 lines — 0 SAx*/$Failed hits, CLEAN
```

The leak is **not deterministic for the current assets**. Reran
twice in the same kernel with accumulated `Output/SingletDoublet/`
state (no wipe between runs): still clean. Seeded
`Output/SingletDoublet/` with a full copy of the known-broken
`iter5-stale` tree before running a fresh build: the fresh compute
overwrites the intermediates, still clean.

### The timeline implicates a concurrent-build race

```
2026-04-20 23:18  iter2-stale        CLEAN
2026-04-20 23:19  iter3-stale        CLEAN
2026-04-20 23:21  iter4-stale        CLEAN
2026-04-20 23:26  iter5-stale        LEAKY
2026-04-20 23:29  iter6-stale        LEAKY
2026-04-22 06:38  cached build       LEAKY    ← current cache
2026-04-22 06:43  pre-rerun          CLEAN
2026-04-22 07:38  commit 88ebf38     "serialise same-model builds
                                      with per-model flock"
```

The 06:38 leaky build stamped the cache one hour **before** flock
serialisation landed. iter5/iter6 at ~5-minute cadence on 2026-04-20
match the shape of concurrent `/sarah-build` invocations (e.g. by
overlapping test runs or a demo retry loop) re-staging
`Private-Models/SingletDoublet/` mid-read or double-writing
`Output/SingletDoublet/`.

The same-model race reproducer I tried (spawn two `wolframscript`
processes with identical staged input, second starts 2s after the
first) did NOT reproduce. So the race is either more subtle — e.g.
different-model interference where `stage()` or the writer touches
shared SARAH install state — or involves an input that differs
between racing builds (possible if the spec was being edited while a
previous build was still running).

### Operational consequences

- The scanner at `scan_outputs.py` catches the leak at emission
  time. The only reason the 06:38 leaky cache exists is that it
  predates the scanner AND predates flock. Current code would block
  it.
- **Recommendation: `/sarah-build --force` on singlet_doublet to
  invalidate the leaky cache.** Empirically produces a clean build
  on the same assets, and the scanner now gates caching.
- H1 and H2 from the original investigation are falsified. H3
  (silent `Param.$Failed` degradation) was not directly tested but
  is consistent with the remaining open question — the `$Failed`
  token in `iter5-stale/RGEs/BetaGauge.m` has no obvious source from
  a kernel with clean state.
- The empirical bisection from PortalDM → our template is still a
  valid path if a deterministic reproducer becomes needed, but
  given that fresh builds are clean, it's not worth doing unless
  the leak resurfaces in a build produced after flock landed.
