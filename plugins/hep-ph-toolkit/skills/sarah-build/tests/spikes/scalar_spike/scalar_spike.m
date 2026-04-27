Off[General::spell]

(*
  T05c spike — minimal 2HDM fixture exercising the scalar-mixing idiom
  from design-final.md §5.4. Goal: validate the exact Mathematica
  MatterSector shape

      {{phi1, phi2}, {hh, ZH}}

  loads cleanly through Start[] + CheckModel[] in a complete model,
  so the SCALAR_MIXING_TEMPLATE in scripts/sections/_idioms.py can
  emit it with confidence.

  Structurally this is THDM-II reduced to the pieces needed to exercise
  the scalar-mixing statement: two SU(2) Higgs doublets, SM fermions,
  SM gauge group. No Z2, no extra BSM fermions, no Type-II Yukawa split
  beyond what THDM-II already uses.
*)

Model`Name = "ScalarSpike";
Model`NameLaTeX = "Scalar-mixing spike (T05c)";
Model`Authors = "shift-manager/sarah-build T05c";
Model`Date = "2026-04-20";

(*-------------------------------------------*)
(*   Particle Content                         *)
(*-------------------------------------------*)

(* Gauge Groups — SM only *)
Gauge[[1]] = {B,   U[1], hypercharge, g1, False};
Gauge[[2]] = {WB,  SU[2], left,        g2, True};
Gauge[[3]] = {G,   SU[3], color,       g3, False};

(* Fermion Fields — standard three-generation SM *)
FermionFields[[1]] = {q, 3, {uL, dL},   1/6, 2,  3};
FermionFields[[2]] = {l, 3, {vL, eL},  -1/2, 2,  1};
FermionFields[[3]] = {d, 3, conj[dR],   1/3, 1, -3};
FermionFields[[4]] = {u, 3, conj[uR],  -2/3, 1, -3};
FermionFields[[5]] = {e, 3, conj[eR],     1, 1,  1};

(* Scalar Fields — two SU(2) Higgs doublets *)
ScalarFields[[1]] = {H1, 1, {H1p, H10}, 1/2, 2, 1};
ScalarFields[[2]] = {H2, 1, {H2p, H20}, 1/2, 2, 1};

(*----------------------------------------------*)
(*   DEFINITION                                 *)
(*----------------------------------------------*)

NameOfStates = {GaugeES, EWSB};

(* ----- Before EWSB ----- *)

DEFINITION[GaugeES][Additional] = {
  {LagHC,   {AddHC -> True}},
  {LagNoHC, {AddHC -> False}}
};

LagNoHC = -(M112 conj[H1].H1 + M222 conj[H2].H2
          + Lambda1 conj[H1].H1.conj[H1].H1
          + Lambda2 conj[H2].H2.conj[H2].H2
          + Lambda3 conj[H2].H2.conj[H1].H1
          + Lambda4 conj[H2].H1.conj[H1].H2);

LagHC = -(M12 conj[H1].H2
        + Lambda5/2 conj[H2].H1.conj[H2].H1
        + Yd conj[H1].d.q
        + Ye conj[H1].e.l
        - Yu H2.u.q);

(* ----- Gauge Sector ----- *)

DEFINITION[EWSB][GaugeSector] = {
  {{VB, VWB[3]}, {VP, VZ}, ZZ},
  {{VWB[1], VWB[2]}, {VWm, conj[VWm]}, ZW}
};

(* ----- VEVs ----- *)

DEFINITION[EWSB][VEVs] = {
  {H10, {v1, 1/Sqrt[2]}, {sigma1, \[ImaginaryI]/Sqrt[2]}, {phi1, 1/Sqrt[2]}},
  {H20, {v2, 1/Sqrt[2]}, {sigma2, \[ImaginaryI]/Sqrt[2]}, {phi2, 1/Sqrt[2]}}
};

(* ----- Mixings — the statement under test (design §5.4 scalar sub-block) ----- *)

DEFINITION[EWSB][MatterSector] = {
  (* CP-even scalar mixing: this is SCALAR_MIXING_TEMPLATE *)
  {{phi1, phi2}, {hh, ZH}},
  (* CP-odd scalar mixing *)
  {{sigma1, sigma2}, {Ah, ZA}},
  (* Charged scalar mixing *)
  {{conj[H1p], conj[H2p]}, {Hm, ZP}},
  (* SM fermion mixings *)
  {{{dL}, {conj[dR]}}, {{DL, Vd}, {DR, Ud}}},
  {{{uL}, {conj[uR]}}, {{UL, Vu}, {UR, Uu}}},
  {{{eL}, {conj[eR]}}, {{EL, Ve}, {ER, Ue}}}
};

(* ----- Dirac spinors ----- *)

DEFINITION[EWSB][DiracSpinors] = {
  Fd -> {DL, conj[DR]},
  Fe -> {EL, conj[ER]},
  Fu -> {UL, conj[UR]},
  Fv -> {vL, 0}
};

DEFINITION[EWSB][GaugeES] = {
  Fd1 -> {FdL, 0},
  Fd2 -> {0,   FdR},
  Fu1 -> {FuL, 0},
  Fu2 -> {0,   FuR},
  Fe1 -> {FeL, 0},
  Fe2 -> {0,   FeR}
};
