(* R2 fixture — PURE TWIST-2 content (STEP3-DESIGN.md Decision 6 R2).

   NON-CIRCULAR (PR #32 fix): the "abbr" chain definitions are the REAL FormCalc
   WeylChains of F1,F4 (chi-line scalar) and F15,F16 (quark-line VECTOR — a
   momentum insertion k[1], the twist-2 quark current), copied VERBATIM from the
   self-contained SD artifact.  Note F15,F16 (NOT the old "F5..F8"): FormCalc's
   real SD numbering puts the twist-2 quark-vector chains at F15,F16.  This fixture
   would FAIL under PR #31's hard-coded {F5..F8}=twist-2 block — which is exactly
   the point (that block map was wrong for this process).

   The twist-2 operator O_Tq = (chibar chi)(qbar gamma.P q) = (F1+F4)(F15+F16) at
   forward kinematics.  This amp = 60*(F1+F4)(F15+F16) must project to C_twist2=60,
   C_scalar=0 (the load-bearing R2 cross-talk check: a static spin-summed collapse
   would fold this into C_scalar). *)
{
  "schema" -> "amp_reduced/v2",
  "process" -> "R2-fixture pure-twist2 (real chain defs)",
  "abbr" -> {
    F1 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 6, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F4 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 7, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F15 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 6, k[1], Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F16 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 7, k[1], Spinor[k[2], MassFd[I3G2], 1, 1, 0]]},
  "subexpr" -> {},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*(60.0*(F1 + F4)*(F15 + F16))]
}
