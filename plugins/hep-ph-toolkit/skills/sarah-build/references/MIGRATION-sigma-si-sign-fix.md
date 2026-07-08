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

The renderer wraps every `hc` term as `LagHC = -( … )`
(`_shared/modelspec_v3/render/lagrangian.py`), so a bare `Yu H.u.q` renders to
an effective **+Yu** coupling — the **opposite sign** from the down-type
`-Yd conj[H].d.q` (effective −Yd). Both up and down couplings should be
−m_q/v.

Physics impact: the wrong relative up/down sign flips the sign of the up-quark
contribution to the spin-independent DM–nucleon amplitude. Because the proton
amplitude is a sum over quark contributions, the flip causes a near-cancellation
that **collapses tree-level σ_SI by ~200×** and manufactures a **fake isospin
violation** (spurious f_p ≠ f_n). Full reasoning:
`~/.claude/jobs/c703354a/tmp/sigma-si/adjudication/VERDICT.md`.

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
