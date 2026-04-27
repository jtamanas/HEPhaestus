Off[General::spell]

(*
  T05b spike — minimal singlet-doublet-style Dirac MatterSector fixture.
  Exercises the canonical SARAH idiom for a chiral (L/R-paired) fermion
  mixing:

      {{{PsiDmL}, {conj[PsiDmR]}}, {{ChiM, ZChimL}, {ChiM, ZChimR}}}

  Base: non-SUSY SM.  Added content: one vector-like charged-lepton-like
  Dirac pair (SU(2) singlets, hypercharge +/-1, color singlets) that
  mixes purely among itself via a Dirac mass term.  This 1x1 charged
  sector reproduces the exact shape declared in design §5.4 and
  §5.6 of /tmp/shift-manager/sarah-build/design/design-final.md.
*)

Model`Name = "DiracSpike";
Model`NameLaTeX = "Dirac spike — minimal L/R paired MatterSector";
Model`Authors = "T05b spike";
Model`Date = "2026-04-20";


(*-------------------------------------------*)
(*   Particle Content                        *)
(*-------------------------------------------*)

(* Gauge Groups (non-SUSY: 5-entry Gauge[[i]]) *)

Gauge[[1]] = {B,   U[1], hypercharge, g1, False};
Gauge[[2]] = {WB, SU[2], left,        g2, True };
Gauge[[3]] = {G,  SU[3], color,       g3, False};


(* SM Matter Fields (verbatim from SM.m) *)

FermionFields[[1]] = {q, 3, {uL, dL},   1/6,  2,  3};
FermionFields[[2]] = {l, 3, {vL, eL}, -1/2,  2,  1};
FermionFields[[3]] = {d, 3, conj[dR],  1/3,  1, -3};
FermionFields[[4]] = {u, 3, conj[uR], -2/3,  1, -3};
FermionFields[[5]] = {e, 3, conj[eR],    1,  1,  1};


(* Extra vector-like pair — the Dirac spike content.
   EPL holds the left Weyl PsiDmL (hypercharge -1, SU(2) singlet,
   charge -1).  EPR holds the conjugate of the right Weyl PsiDmR
   (stored as conj[PsiDmR] per SARAH convention), so its effective
   hypercharge is +1.  Together they form one charged Dirac fermion. *)

FermionFields[[6]] = {EPL, 1, PsiDmL,      -1, 1, 1};
FermionFields[[7]] = {EPR, 1, conj[PsiDmR], 1, 1, 1};


(* Scalar Fields (SM Higgs only) *)

ScalarFields[[1]] = {H, 1, {Hp, H0}, 1/2, 2, 1};


(*----------------------------------------------*)
(*   DEFINITION                                 *)
(*----------------------------------------------*)

NameOfStates = {GaugeES, EWSB};

(* ----- Before EWSB ----- *)

DEFINITION[GaugeES][LagrangianInput] = {
  {LagHC,   {AddHC -> True }},
  {LagNoHC, {AddHC -> False}}
};

LagNoHC = -mu2 conj[H].H - 1/2 \[Lambda] conj[H].H.conj[H].H;

(* Dirac mass for the new pair.  EPR.EPL = conj[PsiDmR].PsiDmL. *)
LagHC = -(Yd conj[H].d.q + Ye conj[H].e.l + Yu u.q.H + mDm EPR.EPL);


(* Gauge Sector (verbatim from SM) *)

DEFINITION[EWSB][GaugeSector] = {
  {{VB, VWB[3]}, {VP, VZ},           ZZ},
  {{VWB[1], VWB[2]}, {VWp, conj[VWp]}, ZW}
};


(* ----- VEVs ----- *)

DEFINITION[EWSB][VEVs] = {
  {H0, {v, 1/Sqrt[2]}, {Ah, \[ImaginaryI]/Sqrt[2]}, {hh, 1/Sqrt[2]}}
};


(* ----- MatterSector -----
   The first three entries are the SM q/l/e rotations (verbatim SM
   idiom).  The fourth entry is the T05b spike target: a single
   L/R-paired Dirac mixing between PsiDmL and conj[PsiDmR], producing
   one charged mass eigenstate ChiM with left/right mixing matrices
   ZChimL / ZChimR.  This is the exact shape quoted in
   design-final.md §5.4 (Dirac sub-block) and §5.6. *)

DEFINITION[EWSB][MatterSector] = {
  {{{dL}, {conj[dR]}}, {{DL, Vd}, {DR, Ud}}},
  {{{uL}, {conj[uR]}}, {{UL, Vu}, {UR, Uu}}},
  {{{eL}, {conj[eR]}}, {{EL, Ve}, {ER, Ue}}},
  {{{PsiDmL}, {conj[PsiDmR]}}, {{ChiM, ZChimL}, {ChiM, ZChimR}}}
};


(*------------------------------------------------------*)
(* Dirac-Spinors                                        *)
(*------------------------------------------------------*)

DEFINITION[EWSB][DiracSpinors] = {
  Fd    -> {DL,    conj[DR]},
  Fe    -> {EL,    conj[ER]},
  Fu    -> {UL,    conj[UR]},
  Fv    -> {vL,    0},
  FChiM -> {ChiM,  conj[ChiM]}
};

DEFINITION[GaugeES][DiracSpinors] = {
  Fd1 -> {dL,     0},
  Fd2 -> {0,      dR},
  Fu1 -> {uL,     0},
  Fu2 -> {0,      uR},
  Fe1 -> {eL,     0},
  Fe2 -> {0,      eR},
  Fv1 -> {vL,     0},
  Fp1 -> {PsiDmL, 0},
  Fp2 -> {0,      PsiDmR}
};
