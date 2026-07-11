(* R2 fixture — PURE SCALAR content (STEP3-DESIGN.md Decision 6 R2).
   Hand-built pre-reduced amplitude carrying ONLY the scalar-block chains
   {F1,F2,F3,F4}; NO twist-2 chains {F5..F8}.  The projector MUST recover
   C_scalar = 4 + 3 + 5 + 7 = 19 and C_twist2 = 0 (cross-talk).
   PV heads already replaced by plain numbers; a SumOver[.,1] + a subexpr
   abbreviation exercise the runner's expansion path. *)
{
  "schema" -> "amp_reduced/v1",
  "process" -> "R2-fixture pure-scalar",
  "subexpr" -> {Sub1 -> 4.0},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*SumOver[I3G5, 1]*(Sub1*F1 + 3.0*F4 + 5.0*F2 + 7.0*F3)]
}
