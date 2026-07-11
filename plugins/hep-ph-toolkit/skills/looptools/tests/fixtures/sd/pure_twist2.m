(* R2 fixture — PURE TWIST-2 content (STEP3-DESIGN.md Decision 6 R2).
   Hand-built pre-reduced amplitude carrying ONLY the twist-2-block chains
   {F5,F6,F7,F8}; NO scalar chains {F1..F4}.  The projector MUST recover
   C_twist2 = 11 + 13 + 17 + 19 = 60 and C_scalar = 0 (cross-talk).
   This is the fixture that catches the 2HDM+a static spin-summed collapse,
   which would fold this twist-2 content into a nonzero C_scalar. *)
{
  "schema" -> "amp_reduced/v1",
  "process" -> "R2-fixture pure-twist2",
  "subexpr" -> {Sub2 -> 11.0},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*SumOver[I3G5, 1]*(Sub2*F5 + 13.0*F6 + 17.0*F7 + 19.0*F8)]
}
