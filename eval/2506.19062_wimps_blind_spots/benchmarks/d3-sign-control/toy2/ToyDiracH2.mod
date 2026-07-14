(* ToyDiracH2.mod — AMENDMENT9-precondition item 2: known-sign FormCalc
   overall-i/normalization confirmation toy (SINGLE fermion chain).
   Fields: chi (F[1], MassFChi), real scalar h (S[1], Mhh), real scalar
   phi (S[2], MassPhi). Interactions:
       L_int = gchi h chibar chi + (mu/2) h phi phi
   (vertex values: i*gchi*(om- + om+), i*mu — FeynArts stores full vertex
   rules INCLUDING the i, verified against SM.mod in D3.)
   PRE-REGISTERED A-PRIORI SIGN for chi phi -> chi phi, t-channel h exchange
   (the ONLY diagram):
       iM = (i gchi ubar u) * (i/(t - Mhh^2)) * (i mu)
       =>  M_phys = - gchi mu / (t - Mhh^2) * (ubar u)
                  = + gchi mu / (Mhh^2 - t) * (ubar u)      (ATTRACTIVE)
   In FormCalc Den[T, Mhh^2] = 1/(T - Mhh^2) language:
       M_phys = - gchi * mu * Den[T, Mhh^2] * (ubar u).
   PREDICTIONS:
     (a) If FormCalc's Amp == M_phys with NO spurious constant on
         single-chain amplitudes (i.e. the D3 minus is specific to the
         two-distinct-fermion-line ordering boundary), the reduced Amp's
         Den-coefficient is NEGATIVE (-gchi mu (F-chain) Den[T,Mhh^2]) and
         the raw FeynAmp has NO explicit leading minus.
     (b) If FeynArts/FormCalc carries a GLOBAL -1 on all amplitudes, the
         Den-coefficient is POSITIVE (and the raw FeynAmp has a leading
         minus) — which would flip twist-2 as well, feeding the
         before-conviction twist-2 gate instead. *)

IndexRange[ Index[G1] ] = Range[1];

M$ModelName = "ToyDiracH2";

M$Information = {};

M$ClassesDescription = {

  F[1] == {
    SelfConjugate -> False,
    Indices -> {Index[G1]},
    Mass -> MassFChi,
    PropagatorLabel -> "chi",
    PropagatorType -> Straight,
    PropagatorArrow -> Forward },

  S[1] == {
    SelfConjugate -> True,
    Mass -> Mhh,
    PropagatorLabel -> "h",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None },

  S[2] == {
    SelfConjugate -> True,
    Mass -> MassPhi,
    PropagatorLabel -> "phi",
    PropagatorType -> ScalarDash,
    PropagatorArrow -> None }
};

M$CouplingMatrices = {

  C[ -F[1, {j1}], F[1, {j2}], S[1] ] ==
    I gchi IndexDelta[j1, j2] {{1}, {1}},

  C[ S[1], S[2], S[2] ] ==
    I mu {{1}}
};

M$LastModelRules = {};
