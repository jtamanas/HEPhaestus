(* ToyDiracH.mod — D3 synthetic external-sign control (AMENDMENT8 Ruling 2).
   Minimal Dirac toy: chi (F[1], mass MassFChi[j]) and a down-type quark
   stand-in (F[2], mass MassFd[j]) coupled to one real scalar h (S[1], mass
   Mhh) with PURE SCALAR Yukawas:
       L_int = gchi h chibar chi + gq h qbar q      (gchi, gq real POSITIVE)
   A-PRIORI SIGN (the external anchor): integrating out h in the t-channel
   gives L_eff = + (gchi gq / (Mhh^2 - t)) (chibar chi)(qbar q); for
   same-sign couplings the Yukawa potential is ATTRACTIVE and the O_S
   coefficient is POSITIVE: C_scalar = + gchi gq / Mhh^2 (+O(t)).
   FeynArts vertex convention (matches SM.mod h-f-fbar): C = I * (coefficient
   in L), so both chirality components are I*g * {{1},{1}}.
   Mass symbols MassFChi/MassFd are chosen so sd_projection.wl's chain
   taxonomy ($chiMassQ/$quarkMassQ) recognizes the lines unchanged. *)

IndexRange[ Index[G1] ] = Range[1];

M$ModelName = "ToyDiracH";

M$Information = {};

M$ClassesDescription = {

  F[1] == {
    SelfConjugate -> False,
    Indices -> {Index[G1]},
    Mass -> MassFChi,
    PropagatorLabel -> "chi",
    PropagatorType -> Straight,
    PropagatorArrow -> Forward },

  F[2] == {
    SelfConjugate -> False,
    Indices -> {Index[G1]},
    Mass -> MassFd,
    PropagatorLabel -> "q",
    PropagatorType -> Straight,
    PropagatorArrow -> Forward },

  S[1] == {
    SelfConjugate -> True,
    Mass -> Mhh,
    PropagatorLabel -> "h",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None }
};

M$CouplingMatrices = {

  C[ -F[1, {j1}], F[1, {j2}], S[1] ] ==
    I gchi IndexDelta[j1, j2] {{1}, {1}},

  C[ -F[2, {j1}], F[2, {j2}], S[1] ] ==
    I gq IndexDelta[j1, j2] {{1}, {1}}
};

M$LastModelRules = {};
