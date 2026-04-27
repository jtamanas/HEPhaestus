VERDICT: PASS
BASELINE_USED: 0.292
HARDCODED_REFERENCE: 0.292
WORKSTREAM: singlet-doublet
VARIANT: B

---

## Six-criterion evaluation table

| # | Criterion | Status | Notes |
|---|---|---|---|
| C1 | summary.json parseable; ran contains "relic"; relic.json.status=="ok" | N/A | Pipeline halted before demo_output written |
| C2 | omega_h2 finite in [0.10, 0.40] OR issues.jsonl has major entry with N+MSSM+collision hypothesis logged before MadDM | **PASS (alternate)** | sd-B-001: VERTICES_MISSING(yh1,yh2) logged at sarah-build phase, before MadDM. Hypothesis contains "N", "collision", "shadows Mathematica N[] precision function". Clash confirmed. |
| C3 | omega_h2 within ±0.01 of 0.292 OR major entry with N+clash hypothesis | **PASS (alternate)** | Same sd-B-001 satisfies alternate C3. Numeric omega_h2 not computed (MadDM not reached). |
| C4 | summary.{pdf,png} exist, >1KB | N/A | Plotting phase not reached |
| C5 | singlet_doublet_spec.yaml exists; validate_spec.py exits 0 | **PARTIAL** | Spec validates (exit=0) but sd-B-002 reveals this is a validation gap: N not caught as reserved. Criterion 5 passes technically (spec is valid) but the skill_prose issue is logged. |
| C6 | Wallclock ≤ 45 min | **PASS** | ~3 min total wall time |

---

## What happened (Variant B narrative)

The practitioner renamed the neutral Majorana mixing matrix from `ZN` to `N`
in Q4 of the /lagrangian-builder interview. The rendered SARAH model file
`SingletDoubletB.m` contains `{Chi, N}` at line 47 of `DEFINITION[EWSB][MatterSector]`.

The model-level `parameters.m` declares `{N, {... OutputName -> N, LesHouches -> NMIX}}`.

SARAH loaded this model and immediately encountered a name conflict: `N` is
**Mathematica's built-in numeric precision function** `N[expr, prec]`. Every
internal call to `N[]` for precision-controlled numeric computation in SARAH
failed with `N::precbd: Requested precision <xgen> is not a machine-sized real
number`. Over 200 such errors appear in sarah.log.

SARAH exited with exit code 0 (no fatal) but the cascading N[] failures caused:
1. All Higgs-portal Yukawa vertices (yh1, yh2) dropped from the UFO
2. UFO: 0 Chi-containing vertices (vs 32 in Variant A with ZN)
3. Malformed Fortran emitted in Couplings_SingletDoubletB.f90
   (StringJoin::string W<>None errors → End Module/Subroutine syntax broken)
4. SPheno compile: SPHENO_COMPILE_FAILED
5. MadDM: not reached

The failure was SILENT at the SARAH level (exit=0) and DETECTED by:
- `check_vertices.py` → VERTICES_MISSING(yh1) + VERTICES_MISSING(yh2)
- `check_mass_matrix.py` → exit=0 (mass matrix structure intact — N::precbd
  only affects the vertex engine and Fortran emitter, not mass matrix extraction)

---

## Key distinction from expected failure mode

The plan anticipated N clashing with "MSSM neutralino convention" (ZN is the
MSSM neutralino mixing matrix OutputName). The actual failure is more fundamental:
**N is Mathematica's built-in precision function**. The MSSM ZN clash (OutputName
collision with LesHouches NMIX) would likely be a soft/silent error at the SLHA
level. The Mathematica N[] shadowing is a hard computational error that breaks
SARAH's internal numerics.

The plan's prediction was directionally correct ("SARAH chokes on N") but
the mechanism is Mathematica N[] shadowing, not MSSM ZN OutputName collision.
Both are logged as sd-B-001 findings.

---

## Fix recommendations (OBSERVE-ONLY — not applied in Phase 1)

1. **validate_spec.py (sd-B-002)**: Add Mathematica built-in names to reserved
   set for mixing_matrix fields: {N, I, E, D, C, O, Pi, Plus, Times, True,
   False, List, Part, All, None, ...}. Priority: N, I, E, D, C, O at minimum
   (single-letter Mathematica builtins most likely to conflict with physicist
   naming conventions).

2. **build.py (sd-B-003)**: After SARAH exits 0, scan sarah.log for
   `N::precbd` or `StringJoin::string` error patterns. Emit warning or error
   JSON if count exceeds threshold (e.g., >10 occurrences of either).

3. **lagrangian-builder SKILL.md / singlet-doublet SKILL.md**: Add note in
   practitioner script or /lagrangian-builder references that matrix names
   N, I, E, D, C are Mathematica built-ins and must not be used as model
   symbols. The canonical SARAH convention for neutralino mixing is ZN (Z
   prefix distinguishes mixing matrices from Mathematica builtins and SLHA
   block names).

4. **interview.md §Q4**: Add a "Reserved names" sidebar warning that single-
   capital-letter symbols (N, I, E, D, C, O) are Mathematica builtins and
   will cause silent SARAH failures if used as mixing matrix names.

---

## Rename-leak assessment

The rename-leak question (does ZN→N change physics?) cannot be answered
numerically — the pipeline did not reach MadDM. Analytically:

- The physics spec is identical between A and B (same Lagrangian, same mass
  spectrum, same field content).
- The only difference is the symbol used for the 3×3 Majorana mixing matrix.
- If the rename had succeeded without collision, Ωh²(B) would equal Ωh²(A)
  to machine precision (the matrix is a SARAH internal; MadDM reads the
  physical particle masses and couplings, not the matrix symbol).
- The N::precbd failure mode means we cannot confirm this numerically.

Classification: the rename "leaked" in the sense that it broke the pipeline,
but via an unexpected mechanism (Mathematica N[] shadowing) rather than
silent physics contamination. The failure is LOUD (check_vertices catches it)
which is the preferred failure mode per plan §"Variant B failure interpretation":
"Surfaced collision = PASS; silent-broken = FAIL."
