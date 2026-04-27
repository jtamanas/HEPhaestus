(* particles.m — TwoHdmAfix particle definitions *)

ParticleDefinitions[GaugeES] = {

{VB,  { Description -> "B-Boson"}},
{VG,  { Description -> "Gluon"}},
{VWB, { Description -> "W-Bosons"}},
{gB,  { Description -> "B-Boson Ghost"}},
{gG,  { Description -> "Gluon Ghost"}},
{gWB, { Description -> "W-Boson Ghost"}},

{H10, {
     PDG -> {0},
     Width -> 0,
     Mass -> Automatic,
     LaTeX -> "H1^0",
     OutputName -> "H10"}},

{H20, {
     PDG -> {0},
     Width -> 0,
     Mass -> Automatic,
     LaTeX -> "H2^0",
     OutputName -> "H20"}},

{H1p, {
     PDG -> {0},
     Width -> 0,
     Mass -> Automatic,
     LaTeX -> "H1^+",
     OutputName -> "H1p"}},

{H2p, {
     PDG -> {0},
     Width -> 0,
     Mass -> Automatic,
     LaTeX -> "H2^+",
     OutputName -> "H2p"}},

{a0s, {
     PDG -> {9975327},
     Width -> Automatic,
     Mass -> LesHouches,
     LaTeX -> "a",
     OutputName -> "a0s"}},

{Fd1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "d_1", OutputName -> "Fd1"}},
{Fd2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "d_2", OutputName -> "Fd2"}},
{Fu1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "u_1", OutputName -> "Fu1"}},
{Fu2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "u_2", OutputName -> "Fu2"}},
{Fe1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "e_1", OutputName -> "Fe1"}},
{Fe2, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "e_2", OutputName -> "Fe2"}},
{Fv1, {PDG -> {0}, Width -> 0, Mass -> Automatic, LaTeX -> "nu_1", OutputName -> "Fv1"}},

{Fchi1, {
     FeynArtsNr -> 54,
     LaTeX -> "chi1",
     Mass -> LesHouches,
     OutputName -> "fchi1",
     PDG -> {9989933},
     Width -> Automatic}},

{Fchi2, {
     FeynArtsNr -> 56,
     LaTeX -> "chi2",
     Mass -> LesHouches,
     OutputName -> "fchi2",
     PDG -> {9989934},
     Width -> Automatic}}

};


ParticleDefinitions[EWSB] = {

{VP,   { Description -> "Photon"}},
{VZ,   { Description -> "Z-Boson"}},
{VG,   { Description -> "Gluon"}},
{VWp,  { Description -> "W+ - Boson"}},
{gP,   { Description -> "Photon Ghost"}},
{gWp,  { Description -> "Positive W+ - Boson Ghost"}},
{gWpC, { Description -> "Negative W+ - Boson Ghost"}},
{gZ,   { Description -> "Z-Boson Ghost"}},
{gG,   { Description -> "Gluon Ghost"}},

{Fd,   { Description -> "Down-Quarks"}},
{Fu,   { Description -> "Up-Quarks"}},
{Fe,   { Description -> "Leptons"}},
{Fv,   { Description -> "Neutrinos"}},

{hh, {
     Description -> "CP-even Higgs mass eigenstates",
     PDG -> {25, 35},
     Width -> Automatic,
     Mass -> LesHouches,
     LaTeX -> "h",
     OutputName -> "hh"}},

{Ah, {
     Description -> "CP-odd scalar mass eigenstates (incl. a0)",
     PDG -> {36, 9931569, 9949515},
     Width -> Automatic,
     Mass -> LesHouches,
     LaTeX -> "A",
     OutputName -> "Ah"}},

{Hm, {
     Description -> "Charged Higgs mass eigenstates",
     PDG -> {37, 9920911},
     Width -> Automatic,
     Mass -> LesHouches,
     LaTeX -> "H^-",
     OutputName -> "Hm"}},

{Fchi, {
     Description -> "Dirac DM fermion chi",
     FeynArtsNr -> 101,
     LaTeX -> "\\chi",
     Mass -> LesHouches,
     OutputName -> "chi",
     PDG -> {9989932},
     ElectricCharge -> 0,
     Width -> Automatic}}

};


WeylFermionAndIndermediate = {

{dR,  { LaTeX -> "d_R"}},
{eR,  { LaTeX -> "e_R"}},
{LL,  { LaTeX -> "l"}},
{uR,  { LaTeX -> "u_R"}},
{q,   { LaTeX -> "q"}},
{eL,  { LaTeX -> "e_L"}},
{dL,  { LaTeX -> "d_L"}},
{uL,  { LaTeX -> "u_L"}},
{vL,  { LaTeX -> "\\nu_L"}},

{DR,  { LaTeX -> "D_R"}},
{ER,  { LaTeX -> "E_R"}},
{UR,  { LaTeX -> "U_R"}},
{EL,  { LaTeX -> "E_L"}},
{DL,  { LaTeX -> "D_L"}},
{UL,  { LaTeX -> "U_L"}},

{chiL, { LaTeX -> "\\chi_L"}},
{chiR, { LaTeX -> "\\chi_R"}},
{ChiL, { LaTeX -> "\\Chi_L"}},
{ChiR, { LaTeX -> "\\Chi_R"}},

{H1,  { LaTeX -> "H_1"}},
{H1p, { LaTeX -> "H_1^+"}},
{H10, { LaTeX -> "H_1^0"}},
{H2,  { LaTeX -> "H_2"}},
{H2p, { LaTeX -> "H_2^+"}},
{H20, { LaTeX -> "H_2^0"}},
{a0s, { LaTeX -> "a"}},

{hh1, { LaTeX -> "h_1"}},
{hh2, { LaTeX -> "h_2"}},
{Ah1, { LaTeX -> "A_1"}},
{Ah2, { LaTeX -> "A_2"}},

{PhasechiR, { LaTeX -> "e^{i\\varphi_{\\chi_R}}"}}

};
