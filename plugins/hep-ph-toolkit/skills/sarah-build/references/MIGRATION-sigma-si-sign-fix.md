# MIGRATION — up-Yukawa sign fix (σ_SI ~200× suppression / fake isospin violation)

**Affects:** anyone who built a local `singlet_doublet` (or `dark_su3`) model
export before this fix. **Action required:** regenerate the export.

## What was wrong

The up-type Higgs–quark Yukawa term in three repo ModelSpecs dropped its
leading minus:

```
lagrangian.hc:  { term: 'Yu H.u.q', ... }      # WRONG (was)
lagrangian.hc:  { term: '-Yu H.u.q', ... }     # RIGHT (now)
```

The SM Higgs couples to *every* quark with the **same** physical sign: mass and
coupling both descend from one Yukawa term `L ⊃ −(Y_q/√2)(v+h) q̄q`, giving
`g_hqq = −m_q/v` for up and down alike. The up- and down-type terms are written
with different SU(2) doublet structure, though — down as `conj[H].d.q`, up as
`H.u.q` — and that H-vs-`conj[H]` / doublet-ordering difference in the
antisymmetric SU(2) contraction is exactly what the up-type's **explicit leading
minus** compensates for. So the canonical, sign-matched form is `-Yu H.u.q`
(leading minus present) alongside the down-type `Yd conj[H].d.q`. Dropping that
leading minus makes the SARAH export emit up-type `+m_q/v` against down-type
`−m_q/v` — a **relative** sign error between up and down. (Full derivation:
`~/.claude/jobs/c703354a/tmp/sigma-si/adjudication/VERDICT.md`; the same contract
is stated in `skills/spheno-build/references/analytic-backend.md` under
"Quark-sector Higgs–Yukawa sign contract".)

Physics impact: with that relative sign, the coherent nucleon scalar sum
`A_N ∝ Σ_q (g_hqq/m_q) m_N f_Tq` degrades into a `(f_Tu − f_Td − …)`
near-cancellation. Tree-level σ_SI **collapses by ~200×** and the proton/neutron
amplitudes split (opposite-sign p/n), manufacturing a **fake isospin violation**.
For Majorana DM the only tree SI operator is scalar Higgs exchange, so there is
no second amplitude this could legitimately cancel against — a large or
opposite-sign p/n here is never physics, only this broken sign. The relic density
is UNAFFECTED (the h–quark scalar vertices do not drive χ₁χ₁ annihilation), so a
correct Ωh² does not catch it.

Fixed specs:
- `_shared/modelspec_v3/specs/singlet_doublet.yaml`
- `_shared/modelspec_v3/specs/dark_su3.yaml`
- `_shared/modelspec_v3/templates/sm.yaml` (SM template — fixes the whole class)

`_shared/modelspec_v3/specs/ssm.yaml` already had the correct `-Yu H.u.q` and
was unaffected.

## Why your local export is still wrong

The live model store at `~/.local/share/hephaestus/models/<name>/` was generated
from the **buggy** spec. This repo does **not** regenerate that store for you —
it is user-owned and treated read-only by the toolkit. You must rebuild it.

## How to regenerate

Re-run the build for each affected model. The build is normally reached via
`/sarah-build`; the underlying entry point is:

```
python3 plugins/hep-ph-toolkit/skills/sarah-build/scripts/build.py \
    plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml \
    --model-dir ~/.local/share/hephaestus/models/singlet_doublet --force
```

Repeat with `specs/dark_su3.yaml` / `--model-dir …/models/dark_su3` if you use
that model.

### ⚠️ The cache may SKIP the rebuild — use `--force`

`sarah-build` keys its cache on `sha256(spec_bytes)=sarah_version`, stamped in
`<model-dir>/.sarah_build_key`. Changing the spec text (the added minus) changes
that key, so a rebuild *should* trigger automatically. But to be certain — and
because a matching key **plus** an existing `sarah_output/UFO/<Name>/` tree makes
the build return `{"status": "cached"}` and skip rendering + `wolframscript`
entirely — always pass **`--force`** when applying this migration. `--force`
bypasses the cache check unconditionally (see `SKILL.md` §"Cache" and
`scripts/run_sarah.py`).

If you prefer a manual reset, delete the stale key before rebuilding:
`rm <model-dir>/.sarah_build_key` (then the next build re-renders).

## Verifying the fix landed

The regenerated `<Name>.m` `LagHC` line must read `… -Yu H.u.q …` (not
`… + Yu H.u.q …`). The committed goldens
(`tests/goldens/singlet_doublet/SingletDoublet.m`,
`tests/goldens/dark_su3/DarkSU3.m`) already show the correct `-Yu H.u.q`.
