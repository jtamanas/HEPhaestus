(* R2 fixture — MIXED scalar + twist-2 content (STEP3-DESIGN.md Decision 6 R2).

   NON-CIRCULAR (PR #32 fix): real FormCalc WeylChains (F1,F4 chi-scalar; F2,F3
   quark-scalar; F15,F16 quark-vector/twist-2), copied VERBATIM from the SD
   artifact.  Both operator blocks present; the numerical basis-vector projector
   must recover EACH independently (no cross-contamination):
     scalar:  O_S  = (F1+F4)(F2+F3)   -> C_scalar = 19
     twist-2: O_Tq = (F1+F4)(F15+F16) -> C_twist2 = 60
   A static spin-summed collapse cannot separate these (both -> c-numbers ~ m_chi
   m_q at rest); the coefficient-level solve must. *)
{
  "schema" -> "amp_reduced/v2",
  "process" -> "R2-fixture mixed (real chain defs)",
  "abbr" -> {
    F1 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 6, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F4 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 7, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F2 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 6, Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F3 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 7, Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F15 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 6, k[1], Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F16 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 7, k[1], Spinor[k[2], MassFd[I3G2], 1, 1, 0]]},
  "subexpr" -> {},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*(19.0*(F1 + F4)*(F2 + F3) + 60.0*(F1 + F4)*(F15 + F16))]
}
