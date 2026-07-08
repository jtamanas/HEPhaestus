# Golden-test conventions — a golden that isn't compared verifies nothing

The `singlet_doublet` up-Yukawa sign bug (`'Yu H.u.q'` where the physical
`−m_q/v` coupling requires `'-Yu H.u.q'`; one dropped leading minus in
`_shared/modelspec_v3/specs/singlet_doublet.yaml`) collapsed tree σ_SI ~200×
and faked isospin violation (opposite-sign proton/neutron amplitudes). It
survived **every** suite in the repo. This file records why, and the
convention that would have caught it.

The up-Yukawa sign drift is a sibling of the PR #1 SARAH quark-sector bug class.
The spec fix itself ships with the σ_SI sign-fix change (PR #5), which also adds a
`MIGRATION-sigma-si-sign-fix.md` note to this `references/` dir — not present on
this branch, so do not follow that filename as a link yet.

---

## The gap

**Symptom.** A one-character sign error in a ModelSpec YAML rendered a wrong
coupling into the emitted UFO/SPheno/CalcHEP model, yet `validate_goldens.py`
passed, the render tests passed, and the schema validator passed. The defect
only surfaced downstream, as a physically-wrong σ_SI adjudicated across two
Monte-Carlo tools.

**Cause.** The golden layer never byte-compared rendered output against the
committed goldens. `scripts/validate_goldens.py` (see `/sarah-build` SKILL.md
§"Golden-file validation") *stages the goldens themselves*, runs
`Start[...] + CheckModel[] + Make*[]`, greps stdout/stderr for a fixed set of
forbidden SARAH error patterns (`ModelFile::MissingModel`, `ModelFile::Aborted`,
`CheckModel::*Abort*`, `MatterSector::parseError`), and checks the UFO/SPheno
trees exist on disk. Every one of those checks is a *liveness* check — "SARAH
accepted this and produced something" — not a *content* check. A sign flip is
still structurally valid SARAH input: `CheckModel[]` passes, emission completes,
no error pattern fires, trees appear. The oracle was blind to it by construction
because it validated the goldens instead of validating `render(spec)` **against**
the goldens.

The repo's own goldens already encoded the correct `'-Yu H.u.q'`. Three specs
had drifted away from them. Nothing in the suite ever put the two side by side.

---

## The convention

**A golden test that does not byte-compare (or AST-compare) `render(spec)`
against the committed golden verifies nothing about content.** It can only tell
you the toolchain still runs. State which of the two you are buying:

- **Liveness / smoke** — "SARAH still accepts this and emits a tree." Fine, but
  label it as such; it does not protect coupling signs, matrix entries, or any
  numeric/structural content.
- **Content / regression** — "the renderer still produces exactly the reviewed
  bytes." Requires diffing `render(spec)` against the golden. This is the only
  layer that catches a spec drift like the up-Yukawa sign.

**Rule.** For any golden intended as a content regression:

1. Compute `render(spec)` from the *current* spec (not the staged golden).
2. Compare it to the committed golden by **byte equality**, or by AST/structural
   equality when whitespace/ordering is legitimately non-deterministic (SARAH
   `.m` idioms, dict ordering). Never accept "SARAH ran and emitted a file" as a
   content assertion.
3. Where a numeric contract exists (a coupling sign, a mass-matrix entry), assert
   it directly in addition to the byte diff — the byte diff catches *unintended*
   drift, the numeric assertion documents the *intended* value so a reviewer
   updating the golden must consciously re-bless the number.

**Watch for the inverted oracle.** If a "golden validator" reads its inputs from
the same `tests/goldens/<model>/` tree it is meant to validate, it is checking
the goldens against the toolchain, not the renderer against the goldens. That is
a liveness check wearing a regression check's name.
