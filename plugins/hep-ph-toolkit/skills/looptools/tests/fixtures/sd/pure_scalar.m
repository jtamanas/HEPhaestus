(* R2 fixture — PURE SCALAR content (STEP3-DESIGN.md Decision 6 R2).

   NON-CIRCULAR (PR #32 fix): the chain definitions in "abbr" are the REAL
   FormCalc WeylChain definitions of F1,F4 (chi-line scalar) and F2,F3 (quark-line
   scalar), copied VERBATIM from the self-contained SD artifact
   reduce_chi1/amp_reduced.m.  The operator identity "F1,F4 are chi-scalar; F2,F3
   are quark-scalar" is established by the ACTUAL spinor structure via the
   numerical basis-vector solve — NOT by an assumed contiguous-index block (the
   circular assumption the PR #31 review flagged as F1 [MAJOR]).

   The physical amplitude is BILINEAR in the chains: (chi bilinear)(quark bilinear).
   The scalar operator O_S = (chibar chi)(qbar q) = (F1+F4)(F2+F3).  This amp
   = 19*(F1+F4)(F2+F3) must project to C_scalar=19, C_twist2=0, C_chi_vector=0,
   with a ~0 completeness residual (all content in the recognized set). *)
{
  "schema" -> "amp_reduced/v2",
  "process" -> "R2-fixture pure-scalar (real chain defs)",
  "abbr" -> {
    F1 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 6, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F4 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 7, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F2 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 6, Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F3 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 7, Spinor[k[2], MassFd[I3G2], 1, 1, 0]]},
  "subexpr" -> {},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*(19.0*(F1 + F4)*(F2 + F3))]
}
