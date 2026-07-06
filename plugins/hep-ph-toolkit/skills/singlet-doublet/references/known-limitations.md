# Known limitations

Confirmed limitations discovered during playtest shifts, cross-referenced to
the responsible plugin owners. These do not block the canonical θ=0 run; they
bound where the pipeline has been proven and record fixes owed by other
plugins.

## 1. Reserved Mathematica symbol names in mixing matrices (sd-A-003)

**Owner plugin**: `model-building` (handoff id `sd-A-003`).

During Variant B of the singlet-doublet playtest, the practitioner renamed the
neutral Majorana mixing matrix from `ZN` to `N` in the `/lagrangian-builder` Q4
interview. Because `N` is Mathematica's built-in numeric precision function
(`N[expr, prec]`), every internal call to `N[]` inside SARAH failed with:

```
N::precbd: Requested precision <xgen> is not a machine-sized real number
```

Over 200 such errors appeared in `sarah.log`. SARAH exited with exit code 0 (no
fatal signal), but the cascading `N::precbd` failures silently dropped all
Higgs-portal Yukawa vertices (`yh1`, `yh2`) from the UFO, broke the Fortran
emitter, and caused SPheno to fail compilation. MadDM was never reached.

**Variant A** (using `ZN`) ran end-to-end successfully; **Variant B** (using
`N`) failed at the SARAH phase. The failure is loud — `check_vertices.py`
detects `VERTICES_MISSING(yh1)` and `VERTICES_MISSING(yh2)` — but the
validate-spec step did not block it upstream.

**Fix required (sd-A-003)**: `validate_spec.py` must add Mathematica built-in
names to the reserved set for `mixing_matrix` fields. At minimum:
`{N, I, E, D, C, O}` (single-capital-letter Mathematica built-ins). The
canonical SARAH convention for neutralino mixing is `ZN`; the `Z`-prefix
distinguishes mixing matrices from Mathematica built-ins and SLHA block names.
Additionally, `interview.md` §Q4 should add a "Reserved names" sidebar warning,
and `build.py` should scan `sarah.log` post-exit for `N::precbd` /
`StringJoin::string` patterns and emit a warning JSON if the count exceeds a
threshold (e.g. >10 occurrences).

## 2. `/lagrangian-builder` JIT interview not yet validated for all Yukawa contractions (sd-A-001)

**Owner plugin**: `lagrangian-builder` (handoff id `sd-A-001`).

Step 4a drives `/lagrangian-builder` in interactive JIT mode using the
pre-written practitioner script; the generated YAML is validated by
`validate_spec.py` and compared against the canonical reference at
`plugins/hep-ph-toolkit/skills/_shared/modelspec_v3/specs/singlet_doublet.yaml`.
However:

- The interview has only been validated for the single-Yukawa limit
  `(y_h1, y_h2) = (y cosθ, y sinθ)` at `θ = 0`.
- At `θ ≠ 0` both SU(2)×U(1) contractions are active simultaneously; the
  practitioner script does not cover this case.
- No regression test guards against future `/lagrangian-builder`
  interview-logic changes silently altering the generated spec.

**Fix required (sd-A-001)**: `lagrangian-builder` should provide a
machine-readable golden fixture for this model so the generated YAML can be
diffed automatically. Until then, any re-run at `θ ≠ 0` must be treated as
exploratory only.
