ParticleDefinitions[GaugeES] = {
    {H0,  {PDG -> {0}, Width -> 0, Mass -> Automatic, FeynArtsNr -> 1, LaTeX -> "H^0", OutputName -> "H0"}},
    {Hp,  {PDG -> {0}, Width -> 0, Mass -> Automatic, FeynArtsNr -> 2, LaTeX -> "H^+", OutputName -> "Hp"}},

    {VB,  {Description -> "B-Boson"}},
    {VG,  {Description -> "Gluon"}},
    {VWB, {Description -> "W-Bosons"}},
    {gB,  {Description -> "B-Boson Ghost"}},
    {gG,  {Description -> "Gluon Ghost"}},
    {gWB, {Description -> "W-Boson Ghost"}},

    (* GaugeES-level single-Weyl Dirac spinors referenced by
       DEFINITION[GaugeES][DiracSpinors] in the spike .m.  Required by
       CheckModelFiles (T15a cycle-2 oracle tightening). *)
    {Fd1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "d_1", OutputName -> "Fd1"}},
    {Fd2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "d_2", OutputName -> "Fd2"}},
    {Fu1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "u_1", OutputName -> "Fu1"}},
    {Fu2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "u_2", OutputName -> "Fu2"}},
    {Fe1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "e_1", OutputName -> "Fe1"}},
    {Fe2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "e_2", OutputName -> "Fe2"}},
    {Fv1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "v_1", OutputName -> "Fv1"}},
    {Fs0, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "s_0", OutputName -> "Fs0"}},
    {FPsiDL0, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "\\psi^0_{D,L}", OutputName -> "FPsiDL0"}},
    {FPsiDL1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "\\psi^-_{D,L}", OutputName -> "FPsiDL1"}},
    {FPsiDR0, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "\\psi^0_{D,R}", OutputName -> "FPsiDR0"}},
    {FPsiDR1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "\\psi^-_{D,R}", OutputName -> "FPsiDR1"}}
};


ParticleDefinitions[EWSB] = {
    {hh,  {Description -> "Higgs", PDG -> {25}, PDG.IX -> {101000001}}},
    {Ah,  {Description -> "Pseudo-Scalar Higgs", PDG -> {0}, PDG.IX -> {0}, Mass -> {0}, Width -> {0}}},
    {Hp,  {Description -> "Charged Higgs", PDG -> {0}, PDG.IX -> {0}, Width -> {0}, Mass -> {0},
           LaTeX -> {"H^+", "H^-"}, OutputName -> {"Hp", "Hm"}, ElectricCharge -> 1}},

    {VP,  {Description -> "Photon"}},
    {VZ,  {Description -> "Z-Boson", Goldstone -> Ah}},
    {VG,  {Description -> "Gluon"}},
    {VWp, {Description -> "W+ - Boson", Goldstone -> Hp}},
    {gP,  {Description -> "Photon Ghost"}},
    {gWp, {Description -> "Positive W+ - Boson Ghost"}},
    {gWpC,{Description -> "Negative W+ - Boson Ghost"}},
    {gZ,  {Description -> "Z-Boson Ghost"}},
    {gG,  {Description -> "Gluon Ghost"}},

    {Fd,  {Description -> "Down-Quarks"}},
    {Fu,  {Description -> "Up-Quarks"}},
    {Fe,  {Description -> "Leptons"}},
    {Fv,  {Description -> "Neutrinos"}},

    (* BSM states *)
    {FChi,  {Description -> "Neutralino-like mixed fermion",
             PDG -> {1000022, 1000023, 1000025},
             PDG.IX -> {0, 0, 0},
             LaTeX -> "\\chi^0",
             OutputName -> "Chi",
             ElectricCharge -> 0}},
    {FChiM, {Description -> "Chargino-like Dirac fermion",
             PDG -> {1000024},
             PDG.IX -> {0},
             LaTeX -> "\\chi^-",
             OutputName -> "ChiM",
             ElectricCharge -> -1}}
};


WeylFermionAndIndermediate = {
    {H,       {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "H", OutputName -> ""}},

    {dR,   {LaTeX -> "d_R"}},
    {eR,   {LaTeX -> "e_R"}},
    {uR,   {LaTeX -> "u_R"}},
    {q,    {LaTeX -> "q"}},
    {l,    {LaTeX -> "l"}},
    {eL,   {LaTeX -> "e_L"}},
    {dL,   {LaTeX -> "d_L"}},
    {uL,   {LaTeX -> "u_L"}},
    {vL,   {LaTeX -> "\\nu_L"}},

    {DR,   {LaTeX -> "D_R"}},
    {ER,   {LaTeX -> "E_R"}},
    {UR,   {LaTeX -> "U_R"}},
    {EL,   {LaTeX -> "E_L"}},
    {DL,   {LaTeX -> "D_L"}},
    {UL,   {LaTeX -> "U_L"}},

    {S,        {LaTeX -> "S"}},
    {s0,       {LaTeX -> "s^0"}},
    {PsiDL,    {LaTeX -> "\\Psi_{D,L}"}},
    {PsiDR,    {LaTeX -> "\\Psi_{D,R}"}},
    {PsiD0L,   {LaTeX -> "\\psi^0_{D,L}"}},
    {PsiD0R,   {LaTeX -> "\\psi^0_{D,R}"}},
    {PsiDmL,   {LaTeX -> "\\psi^-_{D,L}"}},
    {PsiDmR,   {LaTeX -> "\\psi^-_{D,R}"}},
    {Chi,      {LaTeX -> "\\chi^0"}},
    {ChiM,     {LaTeX -> "\\chi^-"}}
};
