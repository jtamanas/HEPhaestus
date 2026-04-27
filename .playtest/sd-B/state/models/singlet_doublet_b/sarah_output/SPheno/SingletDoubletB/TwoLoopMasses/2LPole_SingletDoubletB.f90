! ------------------------------------------------------------------------------ 
! This file was automatically created by SARAH version 4.15.3 
! Two Loop diagrammatic calculation of Higgs masses (c) Mark Goodsell 2015-20 
! References: arXiv: 1503.03098, 1604.05335, 1706.05372  
! ------------------------------------------------------------------------------  

Module Pole2L_SingletDoubletB 
 
Use Control 
Use Settings 
Use Couplings_SingletDoubletB 
Use AddLoopFunctions 
Use LoopFunctions 
Use Mathematics 
Use MathematicsQP 
Use Model_Data_SingletDoubletB 
Use StandardModel 
Use TreeLevelMasses_SingletDoubletB 
Use Pole2LFunctions
Contains 
 
Subroutine CalculatePi2S(p2,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,               & 
& m2SM,kont,tad2L,Pi2S,Pi2P)

Implicit None 
Real(dp),Intent(in) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(in) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Real(dp),Intent(in) :: vvSM

Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp), Intent(in) :: p2
Integer, Intent(inout):: kont
Integer :: gE1,gE2,i,i1,i2,i3,i4,i5 
Real(dp) :: Qscale,prefactor,funcvalue
complex(dp) :: cplxprefactor,A0m
Real(dp)  :: temptad(1)
Real(dp)  :: tempcont(1,1)
Real(dp)  :: tempcontah(1,1)
Real(dp)  :: runningval(1,1)
Real(dp), Intent(out) :: tad2l(1)
Real(dp), Intent(out) :: Pi2S(1,1)
Real(dp), Intent(out) :: Pi2P(1,1)
complex(dp) :: coup1,coup2,coup3,coup4
complex(dp) :: coup1L,coup1R,coup2l,coup2r,coup3l,coup3r,coup4l,coup4r
real(dp) :: epsFmass
real(dp) :: epscouplings
Real(dp)  :: tempcouplingvector(1)
Real(dp)  :: tempcouplingmatrix(1,1)
Real(dp)  :: tempcouplingmatrixah(1,1)
logical :: nonzerocoupling
real(dp) :: delta2Ltadpoles(1)
real(dp)  :: delta2Lmasses(1,1)
real(dp)  :: delta2Lmassesah(1,1)
Real(dp)  :: tad1LG(1)
complex(dp) :: tad1LmatrixHp(1,1)
complex(dp) :: tad1LmatrixAh(1,1)
complex(dp) :: tad1Lmatrixhh(1,1)


tad2l(:)=0
Pi2S(:,:)=0
Pi2P(:,:)=0
Qscale=getrenormalizationscale()
epsfmass=0._dp
epscouplings=1.0E-6_dp
Call TreeMassesEffPot(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,              & 
& MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,              & 
& UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,           & 
& .True.,kont)

If (Abs(MHp2/Qscale).lt.TwoLoopRegulatorMass) MHp2=Qscale*TwoLoopRegulatorMass
If (Abs(MAh2/Qscale).lt.TwoLoopRegulatorMass) MAh2=Qscale*TwoLoopRegulatorMass
If (Abs(Mhh2/Qscale).lt.TwoLoopRegulatorMass) Mhh2=Qscale*TwoLoopRegulatorMass
Call CouplingsFor2LPole3)

Call CouplingsFor2LPole4)

! ----------------------------------
! ------- 1L GAUGELESS TADPOLE DIAGRAMS --------
! ----------------------------------
delta2Ltadpoles(:)=0._dp
delta2Lmasses(:,:)=0._dp
delta2LmassesAh(:,:)=0._dp
tad1LG(:)=0._dp
if(include1l2lshift) then
temptad(:) = 0._dp 
tad1LG=temptad*oo16Pi2
! ----------------------------
! ----------------------------------
! ------- 1L2L SHIFTS --------
! ----------------------------------
delta2Ltadpoles=delta2Ltadpoles*oo16Pi2
delta2Lmasses=delta2Lmasses*oo16Pi2
delta2LmassesAh=delta2LmassesAh*oo16Pi2
! ----------------------------
end if ! include1l2lshift
! ----------------------------------
! ------- TADPOLE DIAGRAMS --------
! ----------------------------------
temptad(:)=0._dp
tempcouplingvector(:)=0._dp
! ----------------------------
! ---- Final tadpole result --
temptad=(temptad*oo16Pi2*oo16Pi2)+delta2ltadpoles
tad2L=temptad
! ----------------------------

! ------------------------------------
! ------- CP EVEN MASS DIAGRAMS ------
! ------------------------------------
tempcont(:,:)=0._dp
tempcouplingmatrix(:,:)=0._dp
Pi2S(1,1)=tempcont(1,1)*oo16Pi2*oo16Pi2+delta2lmasses(1,1)

! -----------------------------------
! ------- CP ODD MASS DIAGRAMS ------
! -----------------------------------
tempcontah(:,:)=0._dp
tempcouplingmatrixah(:,:)=0._dp
Pi2P(1,1)=tempcontah(1,1)*oo16Pi2*oo16Pi2+delta2lmassesah(1,1)
End Subroutine CalculatePi2S
End Module Pole2L_SingletDoubletB 
 
