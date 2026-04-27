(* T05b spike — parameter definitions for DiracSpike. *)

ParameterDefinitions = {

  {g1,     {Description -> "Hypercharge-Coupling"}},
  {g2,     {Description -> "Left-Coupling"}},
  {g3,     {Description -> "Strong-Coupling"}},
  {AlphaS, {Description -> "Alpha Strong"}},
  {e,      {Description -> "electric charge"}},

  {Gf,     {Description -> "Fermi's constant"}},
  {aEWinv, {Description -> "inverse weak coupling constant at mZ"}},

  {Yu, {Description  -> "Up-Yukawa-Coupling",
        DependenceNum -> Sqrt[2]/v * {{Mass[Fu,1], 0, 0},
                                      {0, Mass[Fu,2], 0},
                                      {0, 0, Mass[Fu,3]}}}},
  {Yd, {Description  -> "Down-Yukawa-Coupling",
        DependenceNum -> Sqrt[2]/v * {{Mass[Fd,1], 0, 0},
                                      {0, Mass[Fd,2], 0},
                                      {0, 0, Mass[Fd,3]}}}},
  {Ye, {Description  -> "Lepton-Yukawa-Coupling",
        DependenceNum -> Sqrt[2]/v * {{Mass[Fe,1], 0, 0},
                                      {0, Mass[Fe,2], 0},
                                      {0, 0, Mass[Fe,3]}}}},

  {mu2,        {Description -> "SM Mu Parameter", OutputName -> m2SM}},
  {\[Lambda],  {Description -> "SM Higgs Selfcouplings",
                DependenceNum -> Mass[hh]^2 / v^2}},
  {v,          {Description -> "EW-VEV",
                DependenceNum -> Sqrt[4*Mass[VWp]^2 / g2^2],
                OutputName -> vvSM}},
  {mH2,        {Description -> "SM Higgs Mass Parameter"}},

  {ThetaW,     {Description   -> "Weinberg-Angle",
                DependenceNum -> ArcSin[Sqrt[1 - Mass[VWp]^2/Mass[VZ]^2]]}},

  {ZZ, {Description -> "Photon-Z Mixing Matrix"}},
  {ZW, {Description -> "W Mixing Matrix",
        Dependence  -> 1/Sqrt[2] {{1, 1}, {\[ImaginaryI], -\[ImaginaryI]}}}},

  {Vu, {Description -> "Left-Up-Mixing-Matrix"}},
  {Vd, {Description -> "Left-Down-Mixing-Matrix"}},
  {Uu, {Description -> "Right-Up-Mixing-Matrix"}},
  {Ud, {Description -> "Right-Down-Mixing-Matrix"}},
  {Ve, {Description -> "Left-Lepton-Mixing-Matrix"}},
  {Ue, {Description -> "Right-Lepton-Mixing-Matrix"}},

  (* ---- Dirac spike additions ---- *)
  {mDm,    {Description -> "Dirac mass for spike vectorlike pair",
            LaTeX -> "m_{\\Psi D}", OutputName -> mDm,
            Real -> False}},
  {ZChimL, {Description -> "Left-mixing matrix for charged Dirac spike",
            LaTeX -> "Z^{\\chi^-}_L", OutputName -> ZChimL,
            Real -> False}},
  {ZChimR, {Description -> "Right-mixing matrix for charged Dirac spike",
            LaTeX -> "Z^{\\chi^-}_R", OutputName -> ZChimR,
            Real -> False}}

};
