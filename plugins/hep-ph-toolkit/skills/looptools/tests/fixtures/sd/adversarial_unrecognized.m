(* R2 fixture — ADVERSARIAL, deliberately UNRECOGNIZED chain (STEP3-DESIGN.md
   Decision 6 R2, red-first).

   The projector's completeness guard (F2 review fix) must FAIL LOUDLY on
   amplitude content it cannot map to the recognized operator set — it must NOT
   silently drop it (the exact silent-fall-through the PR #31 review flagged).

   This fixture's "abbr" carries, alongside real chi/quark scalar chains, a chain
   F19 with a RANK-2 structure: TWO momentum insertions (k[1], k[2]) between the
   spinors.  Every recognized SD chain is rank 0 (scalar bilinear) or rank 1
   (single insertion -> vector/twist-2); a rank-2 double insertion is outside the
   {chi|quark|mixed} x {rank 0|1} taxonomy the projector knows how to classify.
   The projector's fail-fast structural guard (unrecognizedChains) MUST name F19
   and refuse (ok=False, reason=UNRECOGNIZED-CHAIN-STRUCTURE) rather than fit
   garbage.  A green (ok=True) result here is a RED-FIRST failure of the guard. *)
{
  "schema" -> "amp_reduced/v2",
  "process" -> "R2-fixture adversarial unrecognized (rank-2 chain)",
  "abbr" -> {
    F1 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 6, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F4 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 7, Spinor[k[1], MassFChi[1], 1, 1, 0]],
    F2 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 6, Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F3 -> WeylChain[Spinor[k[4], MassFd[I3G4], 1, 2, 0], 7, Spinor[k[2], MassFd[I3G2], 1, 1, 0]],
    F19 -> WeylChain[Spinor[k[3], MassFChi[1], 1, 2, 0], 6, k[1], k[2], Spinor[k[1], MassFChi[1], 1, 1, 0]]},
  "subexpr" -> {},
  "amp" -> Amp[{{F[5, {1}], k[1], MassFChi[1], {}},
                {F[4, {I3G2}], k[2], MassFd[I3G2], {}}} ->
               {{F[5, {1}], k[3], MassFChi[1], {}},
                {F[4, {I3G4}], k[4], MassFd[I3G4], {}}}][
    Mat[SUN1]*(19.0*(F1 + F4)*(F2 + F3) + 5.0*F19*(F2 + F3))]
}
