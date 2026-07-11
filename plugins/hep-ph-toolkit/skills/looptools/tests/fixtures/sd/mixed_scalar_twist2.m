(* R2 fixture — MIXED scalar + twist-2 content (STEP3-DESIGN.md Decision 6 R2).
   Both operator blocks present with known coefficients; the projector must
   recover EACH independently (no cross-contamination):
     C_scalar = 4 + 3 + 5 + 7 = 19   (chains F1,F4,F2,F3)
     C_twist2 = 11 + 13 + 17 + 19 = 60 (chains F5,F6,F7,F8)
   A spin-summed collapse cannot separate these; the coefficient-level
   projector must. *)
{
  "schema" -> "amp_reduced/v1",
  "process" -> "R2-fixture mixed",
  "subexpr" -> {Sub1 -> 4.0, Sub2 -> 11.0},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*SumOver[I3G5, 1]*(
      Sub1*F1 + 3.0*F4 + 5.0*F2 + 7.0*F3 +
      Sub2*F5 + 13.0*F6 + 17.0*F7 + 19.0*F8)]
}
