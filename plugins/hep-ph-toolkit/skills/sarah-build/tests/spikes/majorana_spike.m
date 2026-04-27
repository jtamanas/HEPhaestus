Off[General::spell]

(*
 * T05a spike: minimal singlet-doublet-style model exercising the design
 * §5.4 "Majorana fermion mixing" shape in DEFINITION[EWSB][MatterSector]
 * plus the corresponding DEFINITION[EWSB][Phases] entry.
 *
 * Fields (mirrors singlet_doublet spec, BSM part only):
 *   - S       : Majorana singlet Weyl (y=0), contributes a {S, PhaseS} to [Phases]
 *   - PsiDL   : LH SU(2) doublet with components {PsiD0L, PsiDmL}, y=-1/2
 *   - PsiDR   : LH SU(2) doublet with components {PsiD0R, PsiDmR}, y=+1/2
 *     (written as conj[{PsiD0R, PsiDmR}] in FermionFields per SARAH convention)
 *
 * EWSB mixings:
 *   - Neutral Majorana sector: mix {S, PsiD0L, conj[PsiD0R]} -> Chi with ZChi
 *   - Charged Dirac sector:    {PsiDmL} x {conj[PsiDmR]} -> ChiM with ZChimL/ZChimR
 *)

Model`Name      = "Spike";
Model`NameLaTeX = "Singlet-Doublet Majorana MatterSector spike";
Model`Authors   = "T05a spike";
Model`Date      = "2026-04-20";


(*-------------------------------------------*)
(*   Particle Content                        *)
(*-------------------------------------------*)

(* Gauge Groups *)
Gauge[[1]] = {B,   U[1], hypercharge, g1, False};
Gauge[[2]] = {WB,  SU[2], left,       g2, True};
Gauge[[3]] = {G,   SU[3], color,      g3, False};

(* SM matter *)
FermionFields[[1]] = {q, 3, {uL, dL},  1/6, 2,  3};
FermionFields[[2]] = {l, 3, {vL, eL}, -1/2, 2,  1};
FermionFields[[3]] = {d, 3, conj[dR],  1/3, 1, -3};
FermionFields[[4]] = {u, 3, conj[uR], -2/3, 1, -3};
FermionFields[[5]] = {e, 3, conj[eR],    1, 1,  1};

(* BSM matter: singlet + doublet pair *)
FermionFields[[6]] = {S,     1, s0,                 0, 1, 1};                     (* Majorana singlet *)
FermionFields[[7]] = {PsiDL, 1, {PsiD0L, PsiDmL},  -1/2, 2, 1};                   (* LH doublet *)
FermionFields[[8]] = {PsiDR, 1, {conj[PsiD0R], conj[PsiDmR]},  1/2, 2, 1};        (* RH doublet (conjugated Weyls) *)

(* Scalar: SM Higgs only *)
ScalarFields[[1]] = {H, 1, {Hp, H0}, 1/2, 2, 1};


(*----------------------------------------------*)
(*   DEFINITION                                 *)
(*----------------------------------------------*)

NameOfStates = {GaugeES, EWSB};

(* ----- Before EWSB ----- *)

DEFINITION[GaugeES][LagrangianInput] = {
    {LagHC,  {AddHC -> True}},
    {LagNoHC, {AddHC -> False}}
};

LagNoHC = -mu2 conj[H].H - 1/2 \[Lambda] conj[H].H.conj[H].H;

(* SM Yukawas + BSM mass/Yukawa.  Signs: PortalDM.m:87 convention for -Yu. *)
LagHC = -(
      Yd conj[H].d.q + Ye conj[H].e.l - Yu H.u.q
    + 1/2 MS S.S
    + MD PsiDL.PsiDR
    + yhL H.PsiDL.S + yhR conj[H].PsiDR.S
);


(* Gauge Sector *)
DEFINITION[EWSB][GaugeSector] = {
    {{VB, VWB[3]}, {VP, VZ}, ZZ},
    {{VWB[1], VWB[2]}, {VWp, conj[VWp]}, ZW}
};

(* VEVs: SM Higgs VEV only *)
DEFINITION[EWSB][VEVs] = {
    {H0, {v, 1/Sqrt[2]}, {Ah, \[ImaginaryI]/Sqrt[2]}, {hh, 1/Sqrt[2]}}
};

(* ⚑ FROZEN CONTRACT (T05a):
 *   Majorana MatterSector idiom — single-pair form (NMSSM/DiracNMSSM).
 *   Dirac MatterSector idiom    — double-pair form (SM q/l/e + singlet-doublet
 *                                 charged sector; PortalDM/SM.m).
 *)
DEFINITION[EWSB][MatterSector] = {
    (* --- SM q/l/e (verbatim from SM.m) --- *)
    {{{dL}, {conj[dR]}}, {{DL, Vd}, {DR, Ud}}},
    {{{uL}, {conj[uR]}}, {{UL, Vu}, {UR, Uu}}},
    {{{eL}, {conj[eR]}}, {{EL, Ve}, {ER, Ue}}},

    (* --- Majorana neutral sector (3 Weyls -> 3 mass eigenstates) --- *)
    {{s0, PsiD0L, conj[PsiD0R]}, {Chi, ZChi}},

    (* --- Dirac charged sector (LH x RH -> pair of mixing matrices) --- *)
    {{{PsiDmL}, {conj[PsiDmR]}}, {{ChiM, ZChimL}, {ChiM, ZChimR}}}
};


(* Phases: the Majorana-chirality Weyls each get a phase.
 * Per design §5.3 and critic KILL-2: one entry per chirality:majorana Weyl.
 * The singlet-doublet has exactly one Majorana Weyl (the singlet S-component s0).
 *)
DEFINITION[EWSB][Phases] = {
    {s0, PhaseS}
};


(*------------------------------------------------------*)
(* Dirac-Spinors                                         *)
(*------------------------------------------------------*)

DEFINITION[EWSB][DiracSpinors] = {
    Fd     -> {DL,   conj[DR]},
    Fe     -> {EL,   conj[ER]},
    Fu     -> {UL,   conj[UR]},
    Fv     -> {vL,   0},
    FChi   -> {Chi,  conj[Chi]},
    FChiM  -> {ChiM, conj[ChiM]}
};

DEFINITION[GaugeES][DiracSpinors] = {
    Fd1   -> {dL, 0},
    Fd2   -> {0,  dR},
    Fu1   -> {uL, 0},
    Fu2   -> {0,  uR},
    Fe1   -> {eL, 0},
    Fe2   -> {0,  eR},
    Fv1   -> {vL, 0},
    Fs0   -> {s0, 0},
    FPsiDL0 -> {PsiD0L, 0},
    FPsiDL1 -> {PsiDmL, 0},
    FPsiDR0 -> {0, PsiD0R},
    FPsiDR1 -> {0, PsiDmR}
};
