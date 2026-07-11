(* Minimal self-contained amp_reduced.m fixture (amp_reduced/v2 writer format).
   Hand-built to mirror the shape run_calcfeynamp.wls now emits: a wrapped
   association carrying the reduced Amp[...] together with BOTH FormCalc
   abbreviation tables it references —

     "abbr"    = Abbr[]     : F## Dirac/Weyl-chain definitions
     "subexpr" = Subexpr[]  : Sub### coefficient-subexpression definitions
                              (both plain Sub### and indexed Sub###[i_,...] forms)

   Every F## and Sub### appearing in "amp" is defined below, so a fresh kernel
   Get[] resolves the whole tree via  amp //. Join[subexpr, abbr]  with nothing
   left dangling. This is the structural contract the hermetic test pins. *)
{"schema" -> "amp_reduced/v2",
 "amp" -> Amp[{{F[101], k[1], MassFchi, {}}} -> {{F[101], k[3], MassFchi, {}}}][
    Den[T, MassAh^2]*Mat[SUN1]*SumOver[I3G5, 3]*
      (gchi*C0i[cc0, MassFchi^2, T, MassFchi^2, MassFchi^2, MassAh^2, MassAh^2]*
         Sub7[I3G5]*(F1*pchiR - F4*Conjugate[pchiR])*Sub188)/(32*Pi^2)],
 "abbr" -> {F1 -> WeylChain[Spinor[k[1], MassFchi, 1], 6, Spinor[k[3], MassFchi, 1]],
            F4 -> WeylChain[Spinor[k[1], MassFchi, 1], 7, Spinor[k[3], MassFchi, 1]]},
 "subexpr" -> {Sub188 -> 3*(CTW*g2 + g1*STW),
               Sub7[i_] -> gchi*ZA[i, 3]^2*ZH[i, 2]}}
