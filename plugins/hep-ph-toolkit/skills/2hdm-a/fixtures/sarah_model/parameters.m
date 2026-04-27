(* parameters.m — TwoHdmAfix parameter definitions *)

ParameterDefinitions = {

{g1, { Description -> "Hypercharge-Coupling",
       Real -> True,
       LesHouches -> {gauge, 1},
       LaTeX -> "g_1",
       OutputName -> g1}},

{g2, { Description -> "Left-Coupling",
       Real -> True,
       LesHouches -> {gauge, 2},
       LaTeX -> "g_2",
       OutputName -> g2}},

{g3, { Description -> "Strong-Coupling",
       Real -> True,
       LesHouches -> {gauge, 3},
       LaTeX -> "g_3",
       OutputName -> g3}},

{AlphaS, { Description -> "Alpha Strong",
            Real -> True,
            Value -> 0.119,
            LesHouches -> {SMINPUTS, 3},
            LaTeX -> "\\alpha_S",
            OutputName -> aS}},

{e, { Description -> "electric charge",
      Real -> True,
      DependenceNum -> 2*Sqrt[Pi/aEWinv],
      LaTeX -> "e",
      OutputName -> el}},

{aEWinv, { Description -> "inverse weak coupling constant at mZ",
            Real -> True,
            Value -> 137.035999679,
            LesHouches -> {SMINPUTS, 1},
            LaTeX -> "\\alpha^{-1}",
            OutputName -> aEWinv}},

{Gf, { Description -> "Fermi's constant",
       Real -> True,
       Value -> 0.0000116639,
       LesHouches -> {SMINPUTS, 2},
       LaTeX -> "G_f",
       OutputName -> Gf}},

{ThetaW, { Description -> "Weinberg-Angle",
            Real -> True,
            DependenceNum -> ArcSin[Sqrt[1 - Mass[VWp]^2/Mass[VZ]^2]],
            DependenceSPheno -> ArcCos[Abs[ZZ[1,1]]],
            LaTeX -> "\\Theta_W",
            OutputName -> TW}},

{ZZ, { Description -> "Photon-Z Mixing Matrix",
       Real -> True,
       Dependence -> {{Cos[ThetaW], -Sin[ThetaW]}, {Sin[ThetaW], Cos[ThetaW]}},
       LaTeX -> "Z^{\\gamma Z}",
       OutputName -> ZZ}},

{ZW, { Description -> "W Mixing Matrix",
       Dependence -> {{1/Sqrt[2], 1/Sqrt[2]}, {\[ImaginaryI]/Sqrt[2], -\[ImaginaryI]/Sqrt[2]}},
       LaTeX -> "Z^W",
       OutputName -> ZW}},

{Vu, { Description -> "Left-Up-Mixing-Matrix",
       LesHouches -> UULMIX,
       LaTeX -> "U^u_L",
       OutputName -> ZUL}},

{Vd, { Description -> "Left-Down-Mixing-Matrix",
       LesHouches -> UDLMIX,
       LaTeX -> "U^d_L",
       OutputName -> ZDL}},

{Uu, { Description -> "Right-Up-Mixing-Matrix",
       LesHouches -> UURMIX,
       LaTeX -> "U^u_R",
       OutputName -> ZUR}},

{Ud, { Description -> "Right-Down-Mixing-Matrix",
       LesHouches -> UDRMIX,
       LaTeX -> "U^d_R",
       OutputName -> ZDR}},

{Ve, { Description -> "Left-Lepton-Mixing-Matrix",
       LesHouches -> UELMIX,
       LaTeX -> "U^e_L",
       OutputName -> ZEL}},

{Ue, { Description -> "Right-Lepton-Mixing-Matrix",
       LesHouches -> UERMIX,
       LaTeX -> "U^e_R",
       OutputName -> ZER}},

{Yu, { Description -> "Up-Yukawa-Coupling",
       DependenceNum -> Sqrt[2]/vd * {{Mass[Fu,1],0,0},{0,Mass[Fu,2],0},{0,0,Mass[Fu,3]}},
       LesHouches -> Yu,
       LaTeX -> "Y_u",
       OutputName -> Yu}},

{Yd, { Description -> "Down-Yukawa-Coupling",
       DependenceNum -> Sqrt[2]/vd * {{Mass[Fd,1],0,0},{0,Mass[Fd,2],0},{0,0,Mass[Fd,3]}},
       LesHouches -> Yd,
       LaTeX -> "Y_d",
       OutputName -> Yd}},

{Ye, { Description -> "Lepton-Yukawa-Coupling",
       DependenceNum -> Sqrt[2]/vd * {{Mass[Fe,1],0,0},{0,Mass[Fe,2],0},{0,0,Mass[Fe,3]}},
       LesHouches -> Ye,
       LaTeX -> "Y_e",
       OutputName -> Ye}},

(* 2HDM scalar potential parameters *)

{mu1sq, { Real -> True,
           LesHouches -> {THDMPOT, 1},
           LaTeX -> "\\mu_1^2",
           OutputName -> mu1sq}},

{mu2sq, { Real -> True,
           LesHouches -> {THDMPOT, 2},
           LaTeX -> "\\mu_2^2",
           OutputName -> mu2sq}},

{lam1, { Real -> True,
          LesHouches -> {THDMPOT, 3},
          LaTeX -> "\\lambda_1",
          OutputName -> lam1}},

{lam2, { Real -> True,
          LesHouches -> {THDMPOT, 4},
          LaTeX -> "\\lambda_2",
          OutputName -> lam2}},

{lam3, { Real -> True,
          LesHouches -> {THDMPOT, 5},
          LaTeX -> "\\lambda_3",
          OutputName -> lam3}},

{lam4, { Real -> True,
          LesHouches -> {THDMPOT, 6},
          LaTeX -> "\\lambda_4",
          OutputName -> lam4}},

{lam5r, { Real -> True,
           LesHouches -> {THDMPOT, 7},
           LaTeX -> "\\lambda_5",
           OutputName -> lam5r}},

{maSq, { Real -> True,
          LesHouches -> {THDMPOT, 8},
          LaTeX -> "m_a^2",
          OutputName -> maSq}},

{lam6, { Real -> True,
          LesHouches -> {THDMPOT, 9},
          LaTeX -> "\\lambda_6",
          OutputName -> lam6}},

{lam7, { Real -> True,
          LesHouches -> {THDMPOT, 10},
          LaTeX -> "\\lambda_7",
          OutputName -> lam7}},

{lam8, { Real -> True,
          LesHouches -> {THDMPOT, 11},
          LaTeX -> "\\lambda_8",
          OutputName -> lam8}},

{m12sq, { Real -> True,
           LesHouches -> {THDMPOT, 12},
           LaTeX -> "m_{12}^2",
           OutputName -> m12sq}},

{lamP, { Real -> True,
          LesHouches -> {THDMPOT, 13},
          LaTeX -> "\\lambda_P",
          OutputName -> lamP}},

(* DM sector parameters *)

{mchi, { Real -> True,
          LesHouches -> {DMSECTOR, 1},
          LaTeX -> "m_\\chi",
          OutputName -> mchi}},

{gchi, { Real -> True,
          LesHouches -> {DMSECTOR, 2},
          LaTeX -> "g_\\chi",
          OutputName -> gchi}},

{yu2, { Real -> False,
         LesHouches -> YUKAWAU,
         LaTeX -> "y_{u2}",
         OutputName -> yu2}},

{yd1, { Real -> False,
         LesHouches -> YUKAWAD,
         LaTeX -> "y_{d1}",
         OutputName -> yd1}},

{ye1, { Real -> False,
         LesHouches -> YUKAWAE,
         LaTeX -> "y_{e1}",
         OutputName -> ye1}},

(* VEVs *)

{vd, { Real -> True,
        LesHouches -> {HMIX, 102},
        LaTeX -> "v_d",
        OutputName -> vd}},

{vu, { Real -> True,
        LesHouches -> {HMIX, 103},
        LaTeX -> "v_u",
        OutputName -> vu}},

(* Phase for chi_R rephasing freedom — required by SARAH for Dirac mass diagonalization *)

{PhasechiR, { Real -> False,
               LesHouches -> {PHASES, 1},
               LaTeX -> "\\varphi_{\\chi_R}",
               OutputName -> pchiR}},

(* Mixing matrices *)

{ZH, { Description -> "CP-even scalar mixing matrix",
        Real -> True,
        LesHouches -> ZHMIX,
        LaTeX -> "Z^H",
        OutputName -> ZH}},

{ZA, { Description -> "CP-odd scalar mixing matrix",
        Real -> True,
        LesHouches -> ZAMIX,
        LaTeX -> "Z^A",
        OutputName -> ZA}},

{ZP, { Description -> "Charged Higgs mixing matrix",
        Real -> False,
        LesHouches -> ZPMIX,
        LaTeX -> "Z^P",
        OutputName -> ZP}}

};
