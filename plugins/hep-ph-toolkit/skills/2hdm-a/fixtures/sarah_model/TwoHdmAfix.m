Off[General::spell]

Model`Name = "TwoHdmAfix";
Model`NameLaTeX = "Two Higgs Doublet Model + pseudoscalar + Dirac DM fermion";
Model`Authors = "John Tamanas";
Model`Date = "2026-04-22";

(*-------------------------------------------*)
(*   Particle Content                        *)
(*-------------------------------------------*)

NameOfStates = {GaugeES, EWSB};

(* Gauge Fields *)

Gauge[[1]] = {B,  U[1], hypercharge, g1, False};
Gauge[[2]] = {WB, SU[2], left,       g2, True};
Gauge[[3]] = {G,  SU[3], color,      g3, False};

(* SM Fermions *)

FermionFields[[1]] = {q,  3, {uL, dL},  1/6, 2,  3};
FermionFields[[2]] = {LL, 3, {vL, eL}, -1/2, 2,  1};
FermionFields[[3]] = {d,  3, conj[dR],   1/3, 1, -3};
FermionFields[[4]] = {u,  3, conj[uR],  -2/3, 1, -3};
FermionFields[[5]] = {e,  3, conj[eR],     1, 1,  1};

(* DM Fermion — PortalDM idiom: two separate Weyl LH fields *)
(* ChiL is a LH Weyl; ChiR is a LH Weyl whose component is conj[chiR] *)

FermionFields[[6]] = {ChiL, 1, chiL,       0, 1, 1};  (* LH component *)
FermionFields[[7]] = {ChiR, 1, conj[chiR], 0, 1, 1};  (* RH wrapped in conj *)

(* Scalar Fields *)

ScalarFields[[1]] = {H1, 1, {H1p, H10}, 1/2, 2, 1};
ScalarFields[[2]] = {H2, 1, {H2p, H20}, 1/2, 2, 1};
ScalarFields[[3]] = {a0, 1, a0s,          0, 1, 1};   (* real singlet pseudoscalar *)

RealScalars = {a0};

(*----------------------------------------------*)
(*   DEFINITION                                 *)
(*----------------------------------------------*)

DEFINITION[GaugeES][Additional] = {
    {LagHC,   {AddHC -> True}},
    {LagNoHC, {AddHC -> False}}
};

(* Scalar potential — 2HDM + singlet pseudoscalar *)

LagNoHC = -(
    - mu1sq conj[H1].H1
    - mu2sq conj[H2].H2
    + lam1/2 conj[H1].H1.conj[H1].H1
    + lam2/2 conj[H2].H2.conj[H2].H2
    + lam3 conj[H1].H1.conj[H2].H2
    + lam4 conj[H1].H2.conj[H2].H1
    + 1/2 lam5r (conj[H1].H2.conj[H1].H2 + conj[H2].H1.conj[H2].H1)
    + 1/2 maSq a0s.a0s
    + 1/4 lam6 a0s.a0s.a0s.a0s
    + lam7 conj[H1].H1.a0s.a0s
    + lam8 conj[H2].H2.a0s.a0s
);

(* HC Lagrangian: SM Yukawa + m12 mixing + DM couplings *)
(* NOTE: DM mass uses field names ChiR.ChiL (PortalDM idiom, NOT component names) *)
(* CP-odd coupling uses \[ImaginaryI] prefactor for pseudoscalar *)

LagHC = -(
    yu2 H2.u.q
    + yd1 conj[H1].d.q
    + ye1 conj[H1].e.LL
    + m12sq conj[H1].H2
    + lamP conj[H1].H2.a0s
    + mchi ChiR.ChiL
    + \[ImaginaryI] gchi a0s.ChiR.ChiL
);

(* Gauge Sector *)

DEFINITION[EWSB][GaugeSector] = {
    {{VB, VWB[3]}, {VP, VZ}, ZZ},
    {{VWB[1], VWB[2]}, {VWp, conj[VWp]}, ZW}
};

(* VEVs *)

DEFINITION[EWSB][VEVs] = {
    {H10, {vd, 1/Sqrt[2]}, {Ah1, \[ImaginaryI]/Sqrt[2]}, {hh1, 1/Sqrt[2]}},
    {H20, {vu, 1/Sqrt[2]}, {Ah2, \[ImaginaryI]/Sqrt[2]}, {hh2, 1/Sqrt[2]}}
};

(* Matter Sector — SM mixing only; chi is NOT listed here (unmixed Dirac) *)

DEFINITION[EWSB][MatterSector] = {
    {{{dL}, {conj[dR]}}, {{DL, Vd}, {DR, Ud}}},
    {{{uL}, {conj[uR]}}, {{UL, Vu}, {UR, Uu}}},
    {{{eL}, {conj[eR]}}, {{EL, Ve}, {ER, Ue}}},
    {{hh1, hh2},         {hh,  ZH}},
    {{Ah1, Ah2, a0s},    {Ah,  ZA}},
    {{conj[H1p], conj[H2p]}, {Hm, ZP}}
};

(*------------------------------------------------------*)
(* Dirac-Spinors *)
(*------------------------------------------------------*)

(* Phase required by SARAH mass-diagonalizer for RH Weyl rephasing *)

DEFINITION[EWSB][Phases] = {
    {chiR, PhasechiR}
};

(* EWSB Dirac spinors *)

DEFINITION[EWSB][DiracSpinors] = {
    Fd   -> {DL,   conj[DR]},
    Fe   -> {EL,   conj[ER]},
    Fu   -> {UL,   conj[UR]},
    Fv   -> {vL,   0},
    Fchi -> {chiL, chiR}
};

(* GaugeES Dirac spinors *)

DEFINITION[GaugeES][DiracSpinors] = {
    Fd1   -> {dL,   0},
    Fd2   -> {0,    dR},
    Fu1   -> {uL,   0},
    Fu2   -> {0,    uR},
    Fe1   -> {eL,   0},
    Fe2   -> {0,    eR},
    Fv1   -> {vL,   0},
    Fchi1 -> {chiL, 0},
    Fchi2 -> {0,    chiR}
};
