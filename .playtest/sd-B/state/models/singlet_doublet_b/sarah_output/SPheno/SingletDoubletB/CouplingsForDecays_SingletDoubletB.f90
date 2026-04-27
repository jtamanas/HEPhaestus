! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module CouplingsForDecays_SingletDoubletB
 
Use Control 
Use Settings 
Use Model_Data_SingletDoubletB 
Use Couplings_SingletDoubletB 
Use LoopCouplings_SingletDoubletB 
Use Tadpoles_SingletDoubletB 
 Use TreeLevelMasses_SingletDoubletB 
Use Mathematics, Only: CompareMatrices, Adjungate 
 
Use StandardModel 
Contains 
 
 
 
Subroutine CouplingsFor_Fu_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fu_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fu_decays_2B
 
Subroutine CouplingsFor_Fe_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fe_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fe_decays_2B
 
Subroutine CouplingsFor_Fd_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fd_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fd_decays_2B
 
Subroutine CouplingsFor_hh_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,cplHiggsPP,cplHiggsGG,cplHiggsZZvirt,cplHiggsWWvirt,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Complex(dp),Intent(out) :: cplHiggsPP,cplHiggsGG,cplHiggsZZvirt,cplHiggsWWvirt

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Complex(dp) :: coup 
Real(dp) :: vev, gNLO, NLOqcd, NNLOqcd, NNNLOqcd, AlphaSQ, AlphaSQhlf 
Real(dp) :: g1SM,g2SM,g3SM,vSM
Complex(dp) ::YuSM(3,3),YdSM(3,3),YeSM(3,3)
Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_hh_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
! Run always SM gauge couplings if present 
  Qin=sqrt(getRenormalizationScale()) 
  Call RunSMohdm(m_in,deltaM,g1SM,g2SM,g3SM,YuSM,YdSM,YeSM,vSM) 
   ! SM pole masses needed for diphoton/digluon rate 
   ! But only top and W play a role. 
   vSM=1/Sqrt((G_F*Sqrt(2._dp))) ! On-Shell VEV needed for loop 
   YuSM(3,3)=sqrt(2._dp)*mf_u(3)/vSM  ! On-Shell top needed in loop 
   ! Other running values kept to get H->ff correct 
Call SetMatchingConditions(g1SM,g2SM,g3SM,YuSM,YdSM,YeSM,vSM,vvSM,g1,g2,              & 
& g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.False.)

! Run always SM gauge couplings if present 
! alphaS(mH/2) for NLO corrections to diphoton rate 
Call RunSMgauge(m_in/2._dp,deltaM, g1,g2,g3) 
AlphaSQhlf=g3**2/(4._dp*Pi) 
! alphaS(mH) for digluon rate 
Call RunSMgauge(m_in,deltaM, g1,g2,g3) 
AlphaSQ=g3**2/(4._dp*Pi) 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
vev=1/Sqrt((G_F*Sqrt(2._dp)))
cplHiggsWWvirt = 1/vev 
cplHiggsZZvirt = 1*Sqrt(7._dp/12._dp-10._dp/9._dp*Sin(TW)**2+40._dp/27._dp*Sin(TW)**4)/vev 
 

!----------------------------------------------------
! Coupling ratios for HiggsBounds 
!----------------------------------------------------
 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
!----------------------------------------------------
! Scalar Higgs coupling ratios 
!----------------------------------------------------
 
If (HigherOrderDiboson) Then 
  gNLO = Sqrt(AlphaSQhlf*4._dp*Pi) 
Else  
  gNLO = -1._dp 
End if 
Call CoupHiggsToPhoton(m_in,i1,gNLO,coup)

cplHiggsPP = coup*Alpha 
CoupHPP = coup 
Call CoupHiggsToPhotonSM(m_in,gNLO,coup)

ratioPP = Abs(cplHiggsPP/(coup*Alpha)) 
  gNLO = -1._dp 
Call CoupHiggsToGluon(m_in,i1,gNLO,coup)

cplHiggsGG = coup*AlphaSQ 
CoupHGG = coup 
Call CoupHiggsToGluonSM(m_in,gNLO,coup)

If (HigherOrderDiboson) Then 
  NLOqcd = 12._dp*oo48pi2*(95._dp/4._dp - 7._dp/6._dp*NFlav(m_in))*g3**2 
  NNLOqcd = 0.0005785973353112832_dp*(410.52103034222284_dp - 52.326413200014684_dp*NFlav(m_in)+NFlav(m_in)**2 & 
 & +(2.6337085360233763_dp +0.7392866066030529_dp *NFlav(m_in))*Log(m_in**2/mf_u(3)**2))*g3**4 
  NNNLOqcd = 0.00017781840290519607_dp*(42.74607514668917_dp + 11.191050460173795_dp*Log(m_in**2/mf_u(3)**2) + Log(m_in**2/mf_u(3)**2)**2)*g3**6 
Else 
  NLOqcd = 0._dp 
  NNLOqcd = 0._dp 
  NNNLOqcd = 0._dp 
End if 
coup = coup*Sqrt(1._dp + NLOqcd+NNLOqcd+NNNLOqcd) 
cplHiggsGG = cplHiggsGG*Sqrt(1._dp + NLOqcd+NNLOqcd+NNNLOqcd) 
CoupHGG=cplHiggsGG 
ratioGG = Abs(cplHiggsGG/(coup*AlphaSQ)) 
If (i1.eq.1) Then 
CPL_A_H_Z = 0 
CPL_H_H_Z = 0._dp 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_hh_decays_2B
 
Subroutine CouplingsFor_Chi_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,          & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Chi_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Chi_decays_2B
 
Subroutine CouplingsFor_ChiM_decays_2B(m_in,i1,MAhinput,MAh2input,MFChiinput,         & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_ChiM_2B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_ChiM_decays_2B
 
Subroutine CouplingsFor_Fu_decays_3B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fu_3B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fu_decays_3B
 
Subroutine CouplingsFor_Fe_decays_3B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fe_3B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fe_decays_3B
 
Subroutine CouplingsFor_Fd_decays_3B(m_in,i1,MAhinput,MAh2input,MFChiinput,           & 
& MFChi2input,MFChiMinput,MFChiM2input,MFdinput,MFd2input,MFeinput,MFe2input,            & 
& MFuinput,MFu2input,Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,         & 
& MVZinput,MVZ2input,Ninput,PhaseFSinput,TWinput,ZDRinput,ZERinput,UMinput,              & 
& UPinput,ZURinput,ZDLinput,ZELinput,ZULinput,ZWinput,ZZinput,g1input,g2input,           & 
& g3input,Laminput,yh2input,Yuinput,Ydinput,Yeinput,yh1input,MSinput,MPsiinput,          & 
& m2SMinput,vvSMinput,deltaM)

Implicit None 

Real(dp), Intent(in) :: m_in 
Real(dp), Intent(in) :: deltaM 
Integer, Intent(in) :: i1 
Real(dp),Intent(in) :: g1input,g2input,g3input,yh2input,yh1input,MSinput,MPsiinput,vvSMinput

Complex(dp),Intent(in) :: Laminput,Yuinput(3,3),Ydinput(3,3),Yeinput(3,3),m2SMinput

Real(dp),Intent(in) :: MAhinput,MAh2input,MFChiinput(3),MFChi2input(3),MFChiMinput,MFChiM2input,             & 
& MFdinput(3),MFd2input(3),MFeinput(3),MFe2input(3),MFuinput(3),MFu2input(3),            & 
& Mhhinput,Mhh2input,MHpinput,MHp2input,MVWpinput,MVWp2input,MVZinput,MVZ2input,         & 
& TWinput,ZZinput(2,2)

Complex(dp),Intent(in) :: Ninput(3,3),PhaseFSinput,ZDRinput(3,3),ZERinput(3,3),UMinput(1,1),UPinput(1,1),       & 
& ZURinput(3,3),ZDLinput(3,3),ZELinput(3,3),ZULinput(3,3),ZWinput(2,2)

Real(dp) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer :: i2, i3, gt1, gt2, gt3, kont 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp) :: gSM(11), sinW2, dt, tz, Qin 
Iname = Iname + 1 
NameOfUnit(Iname) = 'Couplings_Fd_3B'
 
sinW2=1._dp-mW2/mZ2 
g1 = g1input 
g2 = g2input 
g3 = g3input 
Lam = Laminput 
yh2 = yh2input 
Yu = Yuinput 
Yd = Ydinput 
Ye = Yeinput 
yh1 = yh1input 
MS = MSinput 
MPsi = MPsiinput 
m2SM = m2SMinput 
vvSM = vvSMinput 
Qin=sqrt(getRenormalizationScale()) 
If (m_in.le.Qin) Then 
  If (m_in.le.mz) Then 
Call RunSMohdm(mz,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  Else 
Call RunSMohdm(m_in,deltaM, g1,g2,g3,Yu,Yd,Ye,vvSM) 
  End if 
End if 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

! --- Calculate running tree-level masses for loop induced couplings and Quark mixing matrices --- 
Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,.True.,kont)

If (ExternalZfactors) Then 
! --- Use the 1-loop mixing matrices calculated at M_SUSY in the vertices --- 
N = Ninput 
UM = UMinput 
UP = UPinput 
ZW = ZWinput 
ZZ = ZZinput 
End if 
If (PoleMassesInLoops) Then 
! --- Use the pole masses --- 
MAh = MAhinput 
MAh2 = MAh2input 
MFChi = MFChiinput 
MFChi2 = MFChi2input 
MFChiM = MFChiMinput 
MFChiM2 = MFChiM2input 
MFd = MFdinput 
MFd2 = MFd2input 
MFe = MFeinput 
MFe2 = MFe2input 
MFu = MFuinput 
MFu2 = MFu2input 
Mhh = Mhhinput 
Mhh2 = Mhh2input 
MHp = MHpinput 
MHp2 = MHp2input 
MVWp = MVWpinput 
MVWp2 = MVWp2input 
MVZ = MVZinput 
MVZ2 = MVZ2input 
End if 
Iname = Iname - 1 
 
End subroutine CouplingsFor_Fd_decays_3B
 
Function NFlav(m_in) 
Implicit None 
Real(dp), Intent(in) :: m_in 
Real(dp) :: NFlav 
If (m_in.lt.mf_d(3)) Then 
  NFlav = 4._dp 
Else If (m_in.lt.mf_u(3)) Then 
  NFlav = 5._dp 
Else 
  NFlav = 6._dp 
End if 
End Function

Subroutine RunSM(scale_out,deltaM,tb,g1,g2,g3,Yu, Yd, Ye, vd, vu) 
Implicit None
Real(dp), Intent(in) :: scale_out,deltaM, tb
Real(dp), Intent(out) :: g1, g2, g3, vd, vu
Complex(dp), Intent(out) :: Yu(3,3), Yd(3,3), Ye(3,3)
Real(dp) :: dt, gSM(14), gSM2(2), gSM3(3), mtopMS,  sinw2, vev, tz, alphaStop 
Integer :: kont

RunningTopMZ = .false.

Yd = 0._dp
Ye = 0._dp
Yu = 0._dp

If (.not.RunningTopMZ) Then

! Calculating alpha_S(m_top)
gSM2(1)=sqrt(Alpha_mZ*4*Pi) 
gSM2(2)=sqrt(AlphaS_mZ*4*Pi) 


tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM2,2,tz,0._dp,deltaM,dt,0._dp,RGEAlphaS,kont)



alphaStop = gSM2(2)**2/4._dp/Pi



! m_top^pole to m_top^MS(m_top) 

mtopMS = mf_u(3)*(1._dp - 4._dp/3._dp*alphaStop/Pi)


! Running m_top^MS(m_top) to M_Z 

gSM3(1)=gSM2(1) 
gSM3(2)=gSM2(2)
gSM3(3)=mtopMS

tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM3,3,0._dp,tz,deltaM,dt,0._dp,RGEtop,kont)


mf_u_mz_running = gSM3(3)


RunningTopMZ = .True.

End if

! Starting values at MZ

gSM(1)=sqrt(Alpha_mZ*4*Pi) 
gSM(2)=sqrt(AlphaS_mZ*4*Pi) 
gSM(3)= 0.486E-03_dp ! mf_l_mz(1) 
gSM(4)= 0.10272 !mf_l_mz(2) 
gSM(5)= 1.74624 !mf_l_mz(3) 
gSM(6)= 1.27E-03_dp ! mf_u_mz(1) 
gSM(7)= 0.619  ! mf_u_mz(2) 
gSM(8)= mf_u_mz_running ! m_top 
gSM(9)= 2.9E-03_dp !mf_d_mz(1) 
gSM(10)= 0.055 !mf_d_mz(2) 
gSM(11)= 2.85 ! mf_d_mz(3) 
 

! To get the running sin(w2) 
SinW2 = 0.22290_dp
gSM(12) = 5._dp/3._dp*Alpha_MZ/(1-sinW2)
gSM(13) = Alpha_MZ/Sinw2
gSM(14) = AlphaS_mZ

  nUp =2._dp 
  nDown =3._dp 
  nLep =3._dp 
 

If (scale_out.gt.sqrt(mz2)) Then

 ! From M_Z to Min(M_top,scale_out) 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(sqrt(mz2)/mf_u(3)) 
  dt=tz/50._dp 
 Else 
  tz=Log(sqrt(mz2)/scale_out) 
  dt=tz/50._dp 
 End if 

  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)


 ! From M_top to M_SUSY if M_top < M_SUSY 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(mf_u(3)/scale_out) 
  dt=tz/50._dp 
  nUp =3._dp 
  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)
 End if 
Else

 ! From M_Z down to scale_out
  tz=Log(scale_out/sqrt(mz2)) 
  dt=tz/50._dp 
  Call odeint(gSM,14,0._dp,tz,deltaM,dt,0._dp,rge11_SMa,kont)

End if

! Calculating Couplings 

 sinW2=1._dp-mW2/mZ2 
 vev=Sqrt(mZ2*(1._dp-sinW2)*SinW2/(gSM(1)**2/4._dp))
 vd=vev/Sqrt(1._dp+tb**2)
 vu=tb*vd
 
Yd(1,1) =gSM(9)*sqrt(2._dp)/vd 
Yd(2,2) =gSM(10)*sqrt(2._dp)/vd 
Yd(3,3) =gSM(11)*sqrt(2._dp)/vd 
Ye(1,1) =gSM(3)*sqrt(2._dp)/vd 
Ye(2,2)=gSM(4)*sqrt(2._dp)/vd 
Ye(3,3)=gSM(5)*sqrt(2._dp)/vd 
Yu(1,1)=gSM(6)*sqrt(2._dp)/vu 
Yu(2,2)=gSM(7)*sqrt(2._dp)/vu 
Yu(3,3)=gSM(8)*sqrt(2._dp)/vu 


g3 =gSM(2) 
g3running=gSM(2) 

g1 = sqrt(gSM(12)*4._dp*Pi*3._dp/5._dp)
g2 = sqrt(gSM(13)*4._dp*Pi)
! g3 = sqrt(gSM(3)*4._dp*Pi)

sinw2 = g1**2/(g1**2 + g2**2)

!g2=gSM(1)/sqrt(sinW2) 
!g1 = g2*Sqrt(sinW2/(1._dp-sinW2)) 

If (GenerationMixing) Then 

If (YukawaScheme.Eq.1) Then ! CKM into Yu
 If (TransposedYukawa) Then ! check, if superpotential is Yu Hu u q  or Yu Hu q u
   Yu= Matmul(Transpose(CKM),Transpose(Yu))
 Else 
   Yu=Transpose(Matmul(Transpose(CKM),Transpose(Yu)))
 End if 

Else ! CKM into Yd 
 
 If (TransposedYukawa) Then ! 
  Yd= Matmul(Conjg(CKM),Transpose(Yd))
 Else 
  Yd=Transpose(Matmul(Conjg(CKM),Transpose(Yd)))
 End if 

End if ! Yukawa scheme
End If ! Generatoin mixing


End Subroutine RunSM


Subroutine RunSMohdm(scale_out,deltaM,g1,g2,g3,Yu, Yd, Ye, v) 
Implicit None
Real(dp), Intent(in) :: scale_out,deltaM
Real(dp), Intent(out) :: g1, g2, g3, v
Complex(dp), Intent(out) :: Yu(3,3), Yd(3,3), Ye(3,3)
Real(dp) :: dt, gSM(14), gSM2(2), gSM3(3), mtopMS,  sinw2, vev, tz, alphaStop 
Integer :: kont

Yd = 0._dp
Ye = 0._dp
Yu = 0._dp

If (.not.RunningTopMZ) Then

! Calculating alpha_S(m_top)
gSM2(1)=sqrt(Alpha_mZ*4*Pi) 
gSM2(2)=sqrt(AlphaS_mZ*4*Pi) 


tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM2,2,tz,0._dp,deltaM,dt,0._dp,RGEAlphaS,kont)



alphaStop = gSM2(2)**2/4._dp/Pi



! m_top^pole to m_top^MS(m_top) 

mtopMS = mf_u(3)*(1._dp - 4._dp/3._dp*alphaStop/Pi)


! Running m_top^MS(m_top) to M_Z 

gSM3(1)=gSM2(1) 
gSM3(2)=gSM2(2)
gSM3(3)=mtopMS

tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM3,3,0._dp,tz,deltaM,dt,0._dp,RGEtop,kont)


mf_u_mz_running = gSM3(3)


RunningTopMZ = .True.

End if

! Starting values at MZ

gSM(1)=sqrt(Alpha_mZ*4*Pi) 
gSM(2)=sqrt(AlphaS_mZ*4*Pi) 
gSM(3)= 0.486E-03_dp ! mf_l_mz(1) 
gSM(4)= 0.10272 !mf_l_mz(2) 
gSM(5)= 1.74624 !mf_l_mz(3) 
gSM(6)= 1.27E-03_dp ! mf_u_mz(1) 
gSM(7)= 0.619  ! mf_u_mz(2) 
gSM(8)= mf_u_mz_running ! m_top 
gSM(9)= 2.9E-03_dp !mf_d_mz(1) 
gSM(10)= 0.055 !mf_d_mz(2) 
gSM(11)= 2.85 ! mf_d_mz(3) 
 

! To get the running sin(w2) 
SinW2 = 0.22290_dp
gSM(12) = 5._dp/3._dp*Alpha_MZ/(1-sinW2)
gSM(13) = Alpha_MZ/Sinw2
gSM(14) = AlphaS_mZ

  nUp =2._dp 
  nDown =3._dp 
  nLep =3._dp 
 

If (scale_out.gt.sqrt(mz2)) Then

 ! From M_Z to Min(M_top,scale_out) 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(sqrt(mz2)/mf_u(3)) 
  dt=tz/50._dp 
 Else 
  tz=Log(sqrt(mz2)/scale_out) 
  dt=tz/50._dp 
 End if 

  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)


 ! From M_top to M_SUSY if M_top < M_SUSY 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(mf_u(3)/scale_out) 
  dt=tz/50._dp 
  nUp =3._dp 
  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)
 End if 
Else

 ! From M_Z down to scale_out
  If (abs(scale_out - sqrt(mz2)).gt.1.0E-3_dp) Then 
   tz=Log(scale_out/sqrt(mz2)) 
   dt=tz/50._dp 
   Call odeint(gSM,14,0._dp,tz,deltaM,dt,0._dp,rge11_SMa,kont)
  End if
End if

! Calculating Couplings 

 sinW2=1._dp-mW2/mZ2 
 vev=Sqrt(mZ2*(1._dp-sinW2)*SinW2/(gSM(1)**2/4._dp))
 v = vev
 
Yd(1,1) =gSM(9)*sqrt(2._dp)/v 
Yd(2,2) =gSM(10)*sqrt(2._dp)/v 
Yd(3,3) =gSM(11)*sqrt(2._dp)/v 
Ye(1,1) =gSM(3)*sqrt(2._dp)/v 
Ye(2,2)=gSM(4)*sqrt(2._dp)/v 
Ye(3,3)=gSM(5)*sqrt(2._dp)/v 
Yu(1,1)=gSM(6)*sqrt(2._dp)/v 
Yu(2,2)=gSM(7)*sqrt(2._dp)/v 
Yu(3,3)=gSM(8)*sqrt(2._dp)/v 


g3 =gSM(2) 
g3running=gSM(2) 

g1 = sqrt(gSM(12)*4._dp*Pi*3._dp/5._dp)
g2 = sqrt(gSM(13)*4._dp*Pi)
! g3 = sqrt(gSM(3)*4._dp*Pi)

sinw2 = g1**2/(g1**2 + g2**2)

g2=gSM(1)/sqrt(sinW2) 
g1 = g2*Sqrt(sinW2/(1._dp-sinW2)) 

If (GenerationMixing) Then 

If (YukawaScheme.Eq.1) Then ! CKM into Yu
 If (TransposedYukawa) Then ! check, if superpotential is Yu Hu u q  or Yu Hu q u
   Yu= Matmul(Transpose(CKM),Transpose(Yu))
 Else 
   Yu=Transpose(Matmul(Transpose(CKM),Transpose(Yu)))
 End if 

Else ! CKM into Yd 
 
 If (TransposedYukawa) Then ! 
  Yd= Matmul(Conjg(CKM),Transpose(Yd))
 Else 
  Yd=Transpose(Matmul(Conjg(CKM),Transpose(Yd)))
 End if 

End if ! Yukawa scheme
End If ! Generation mixing



End Subroutine RunSMohdm

Subroutine RunSMgauge(scale_out,deltaM,g1,g2,g3) 
Implicit None
Real(dp), Intent(in) :: scale_out,deltaM
Real(dp), Intent(out) :: g1, g2, g3
Complex(dp) :: Yu(3,3), Yd(3,3), Ye(3,3)
Real(dp) :: v, dt, gSM(14), gSM2(2), gSM3(3), mtopMS,  sinw2, vev, tz, alphaStop 
Integer :: kont

Yd = 0._dp
Ye = 0._dp
Yu = 0._dp

RunningTopMZ = .false.

If (.not.RunningTopMZ) Then

! Calculating alpha_S(m_top)
gSM2(1)=sqrt(Alpha_mZ*4*Pi) 
gSM2(2)=sqrt(AlphaS_mZ*4*Pi) 


tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM2,2,tz,0._dp,deltaM,dt,0._dp,RGEAlphaS,kont)



alphaStop = gSM2(2)**2/4._dp/Pi



! m_top^pole to m_top^MS(m_top) 

mtopMS = mf_u(3)*(1._dp - 4._dp/3._dp*alphaStop/Pi)


! Running m_top^MS(m_top) to M_Z 

gSM3(1)=gSM2(1) 
gSM3(2)=gSM2(2)
gSM3(3)=mtopMS

tz=Log(sqrt(mz2)/mf_u(3)) 
dt=tz/50._dp 
Call odeint(gSM3,3,0._dp,tz,deltaM,dt,0._dp,RGEtop,kont)


mf_u_mz_running = gSM3(3)


RunningTopMZ = .True.

End if

! Starting values at MZ

gSM(1)=sqrt(Alpha_mZ*4*Pi) 
gSM(2)=sqrt(AlphaS_mZ*4*Pi) 
gSM(3)= 0.486E-03_dp ! mf_l_mz(1) 
gSM(4)= 0.10272 !mf_l_mz(2) 
gSM(5)= 1.74624 !mf_l_mz(3) 
gSM(6)= 1.27E-03_dp ! mf_u_mz(1) 
gSM(7)= 0.619  ! mf_u_mz(2) 
gSM(8)= mf_u_mz_running ! m_top 
gSM(9)= 2.9E-03_dp !mf_d_mz(1) 
gSM(10)= 0.055 !mf_d_mz(2) 
gSM(11)= 2.85 ! mf_d_mz(3) 
 

! To get the running sin(w2) 
SinW2 = 0.22290_dp
gSM(12) = 5._dp/3._dp*Alpha_MZ/(1-sinW2)
gSM(13) = Alpha_MZ/Sinw2
gSM(14) = AlphaS_mZ

  nUp =2._dp 
  nDown =3._dp 
  nLep =3._dp 
 

If (scale_out.gt.sqrt(mz2)) Then

 ! From M_Z to Min(M_top,scale_out) 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(sqrt(mz2)/mf_u(3)) 
  dt=tz/50._dp 
 Else 
  tz=Log(sqrt(mz2)/scale_out) 
  dt=tz/50._dp 
 End if 

  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)


 ! From M_top to M_SUSY if M_top < M_SUSY 
 If (scale_out.gt.mf_u(3)) Then 
  tz=Log(mf_u(3)/scale_out) 
  dt=tz/50._dp 
  nUp =3._dp 
  Call odeint(gSM,14,tz,0._dp,deltaM,dt,0._dp,rge11,kont)
 End if 
Else

 ! From M_Z down to scale_out
  tz=Log(scale_out/sqrt(mz2)) 
  dt=tz/50._dp 
  Call odeint(gSM,14,0._dp,tz,deltaM,dt,0._dp,rge11_SMa,kont)

End if

! Calculating Couplings 

 sinW2=1._dp-mW2/mZ2 
 vev=Sqrt(mZ2*(1._dp-sinW2)*SinW2/(gSM(1)**2/4._dp))
 v = vev
 
Yd(1,1) =gSM(9)*sqrt(2._dp)/v 
Yd(2,2) =gSM(10)*sqrt(2._dp)/v 
Yd(3,3) =gSM(11)*sqrt(2._dp)/v 
Ye(1,1) =gSM(3)*sqrt(2._dp)/v 
Ye(2,2)=gSM(4)*sqrt(2._dp)/v 
Ye(3,3)=gSM(5)*sqrt(2._dp)/v 
Yu(1,1)=gSM(6)*sqrt(2._dp)/v 
Yu(2,2)=gSM(7)*sqrt(2._dp)/v 
Yu(3,3)=gSM(8)*sqrt(2._dp)/v 


g3 =gSM(2) 
g3running=gSM(2) 

g1 = sqrt(gSM(12)*4._dp*Pi*3._dp/5._dp)
g2 = sqrt(gSM(13)*4._dp*Pi)
! g3 = sqrt(gSM(3)*4._dp*Pi)

sinw2 = g1**2/(g1**2 + g2**2)

g2=gSM(1)/sqrt(sinW2) 
g1 = g2*Sqrt(sinW2/(1._dp-sinW2)) 

If (GenerationMixing) Then 
If (TransposedYukawa) Then ! check, if superpotential is Yu Hu u q  or Yu Hu q u
 Yu= Matmul(Transpose(CKM),Transpose(Yu))
Else 
 Yu=Transpose(Matmul(Transpose(CKM),Transpose(Yu)))
End if 
End If


End Subroutine RunSMgauge
End Module CouplingsForDecays_SingletDoubletB
