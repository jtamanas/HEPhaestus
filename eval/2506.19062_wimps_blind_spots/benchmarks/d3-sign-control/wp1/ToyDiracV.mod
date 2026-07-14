(* ToyDiracV.mod — W-P1 (DESIGN-ITEM4-AMENDMENT8R4 R3): the DECISIVE
   H-A1 vs H-A2 discriminator toy.  Same Dirac chi/q pair as D3's
   ToyDiracH, now exchanging a real massive VECTOR so the tree amplitude
   carries TWIST-2-class content with analytically known sign:
       L_int = gchi Z_mu chibar gamma^mu chi + gq Z_mu qbar gamma^mu q
   (gchi, gq real POSITIVE; vertex values i*gchi*gamma^mu, i*gq*gamma^mu —
   FeynArts stores full vertex rules INCLUDING the i; FFV convention
   verified against SM.mod electron-photon C = I EL {{1},{1}} with the
   Lorentz.gen structure {gamma_mu om-, gamma_mu om+}.)

   A-PRIORI AMPLITUDE (hand Wick, frozen before the run):
     chi(k1) q(k2) -> chi(k3) q(k4), t-channel Z, qT = k3-k1, qT^2 = t:
       iM = [ubar(k3) i gchi gamma^mu u(k1)]
            * (-i)(g_mu_nu - qT_mu qT_nu/MV^2)/(t - MV^2)
            * [ubar(k4) i gq gamma^nu u(k2)]
     qT_mu (chibar gamma^mu chi) = 0 on shell (equal-mass conserved
     current), likewise on the quark line, so the qT qT / MV^2 piece and
     any Goldstone/gauge ambiguity drop EXACTLY (this also makes the
     Feynman-gauge FeynArts propagator physically exact for this toy):
       M_phys = + gchi gq/(t - MV^2) * (chibar gamma^mu chi)(qbar gamma_mu q)
              = - gchi gq/(MV^2 - t) * V.V
     Sanity anchor: like-sign vector charges REPEL (Born: V(q) =
     +g^2/(|q|^2+MV^2) > 0), the textbook opposite of D3's attractive
     scalar case.

   PRE-REGISTERED READ-OUT (frozen now; bars in wp1_project.wls header):
     sign(C_twist2_sum^pipeline) * sign(C_twist2_sum^analytic)
       = -1  (toy twist-2 FLIPS alongside D3's scalar flip)  -> H-A1
       = +1  (toy twist-2 AGREES while D3's scalar flipped)  -> H-A2  *)

IndexRange[ Index[G1] ] = Range[1];

M$ModelName = "ToyDiracV";

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

  V[1] == {
    SelfConjugate -> True,
    Mass -> MV,
    PropagatorLabel -> "Z'",
    PropagatorType -> Sine,
    PropagatorArrow -> None }
};

M$CouplingMatrices = {

  C[ -F[1, {j1}], F[1, {j2}], V[1] ] ==
    I gchi IndexDelta[j1, j2] {{1}, {1}},

  C[ -F[2, {j1}], F[2, {j2}], V[1] ] ==
    I gq IndexDelta[j1, j2] {{1}, {1}}
};

M$LastModelRules = {};
