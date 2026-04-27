! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module BranchingRatios_SingletDoubletB 
 
Use Control 
Use Settings 
Use Couplings_SingletDoubletB 
Use Model_Data_SingletDoubletB 
Use LoopCouplings_SingletDoubletB 
Use Fu3Decays_SingletDoubletB 
Use Fe3Decays_SingletDoubletB 
Use Fd3Decays_SingletDoubletB 
Use TreeLevelDecays_SingletDoubletB 
Use OneLoopDecays_SingletDoubletB


 Contains 
 
Subroutine CalculateBR(CTBD,fac3,epsI,deltaM,kont,MAh,MAh2,MFChi,MFChi2,              & 
& MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,            & 
& MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,               & 
& yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,gPFu,gTFu,BRFu,gPFe,gTFe,BRFe,gPFd,gTFd,BRFd,            & 
& gPhh,gThh,BRhh,gPChi,gTChi,BRChi,gPChiM,gTChiM,BRChiM)

Real(dp), Intent(in) :: epsI, deltaM, fac3 
Integer, Intent(inout) :: kont 
Logical, Intent(in) :: CTBD 
Real(dp),Intent(inout) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(inout) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Real(dp),Intent(in) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp),Intent(in) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp),Intent(inout) :: vvSM

Real(dp),Intent(inout) :: gPFu(3,0),gTFu(3),BRFu(3,0),gPFe(3,0),gTFe(3),BRFe(3,0),gPFd(3,0),gTFd(3),            & 
& BRFd(3,0),gPhh(1,4),gThh,BRhh(1,4),gPChi(3,0),gTChi(3),BRChi(3,0),gPChiM(1,0),         & 
& gTChiM,BRChiM(1,0)

Complex(dp) :: cplHiggsPP,cplHiggsGG,cplPseudoHiggsPP,cplPseudoHiggsGG,cplHiggsZZvirt,               & 
& cplHiggsWWvirt

Real(dp) :: gTAh 
Complex(dp) :: coup 
Real(dp) :: vev 
Real(dp) :: gTVZ,gTVWp

Iname = Iname + 1 
NameOfUnit(Iname) = 'CalculateBR'
 
Write(*,*) "Calculating branching ratios and decay widths" 
gTVWp = gamW 
gTVZ = gamZ 
! One-Loop Decays 
If (OneLoopDecays) Then 
Call CalculateOneLoopDecays(gP1LFu,gP1LFe,gP1LFd,gP1Lhh,gP1LChi,gP1LChiM,             & 
& MFd,MFd2,MFu,MFu2,MFe,MFe2,MFChi,MFChi2,MFChiM,MFChiM2,MHp,MHp2,MAh,MAh2,              & 
& Mhh,Mhh2,MVZ,MVZ2,MVWp,MVWp2,ZDL,ZDR,ZUL,ZUR,ZEL,ZER,N,UM,UP,vvSM,g1,g2,               & 
& g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,epsI,deltaM,kont)

End if 


gPFu = 0._dp 
gTFu = 0._dp 
BRFu = 0._dp 
Call FuTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,               & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPFu(:,1:0),gTFu,BRFu(:,1:0))

Do i1=1,3
gTFu(i1) =Sum(gPFu(i1,:)) 
If (gTFu(i1).Gt.0._dp) BRFu(i1,: ) =gPFu(i1,:)/gTFu(i1) 
If (OneLoopDecays) Then 
gT1LFu(i1) =Sum(gP1LFu(i1,:)) 
If (gT1LFu(i1).Gt.0._dp) BR1LFu(i1,: ) =gP1LFu(i1,:)/gT1LFu(i1) 
End if
End Do 
 

gPFe = 0._dp 
gTFe = 0._dp 
BRFe = 0._dp 
Call FeTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,               & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPFe(:,1:0),gTFe,BRFe(:,1:0))

Do i1=1,3
gTFe(i1) =Sum(gPFe(i1,:)) 
If (gTFe(i1).Gt.0._dp) BRFe(i1,: ) =gPFe(i1,:)/gTFe(i1) 
If (OneLoopDecays) Then 
gT1LFe(i1) =Sum(gP1LFe(i1,:)) 
If (gT1LFe(i1).Gt.0._dp) BR1LFe(i1,: ) =gP1LFe(i1,:)/gT1LFe(i1) 
End if
End Do 
 

gPFd = 0._dp 
gTFd = 0._dp 
BRFd = 0._dp 
Call FdTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,               & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPFd(:,1:0),gTFd,BRFd(:,1:0))

Do i1=1,3
gTFd(i1) =Sum(gPFd(i1,:)) 
If (gTFd(i1).Gt.0._dp) BRFd(i1,: ) =gPFd(i1,:)/gTFd(i1) 
If (OneLoopDecays) Then 
gT1LFd(i1) =Sum(gP1LFd(i1,:)) 
If (gT1LFd(i1).Gt.0._dp) BR1LFd(i1,: ) =gP1LFd(i1,:)/gT1LFd(i1) 
End if
End Do 
 

gPhh = 0._dp 
gThh = 0._dp 
BRhh = 0._dp 
Call hhTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,               & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPhh,gThh,BRhh)

Do i1=1,1
gThh =Sum(gPhh(i1,:)) 
If (gThh.Gt.0._dp) BRhh(i1,: ) =gPhh(i1,:)/gThh 
If (OneLoopDecays) Then 
gT1Lhh =Sum(gP1Lhh(i1,:)) 
If (gT1Lhh.Gt.0._dp) BR1Lhh(i1,: ) =gP1Lhh(i1,:)/gT1Lhh 
End if
End Do 
 

gPChi = 0._dp 
gTChi = 0._dp 
BRChi = 0._dp 
Call ChiTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,              & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPChi,gTChi,BRChi)

Do i1=1,3
gTFChi(i1) =Sum(gPFChi(i1,:)) 
If (gTFChi(i1).Gt.0._dp) BRFChi(i1,: ) =gPFChi(i1,:)/gTFChi(i1) 
If (OneLoopDecays) Then 
gT1LFChi(i1) =Sum(gP1LFChi(i1,:)) 
If (gT1LFChi(i1).Gt.0._dp) BR1LFChi(i1,: ) =gP1LFChi(i1,:)/gT1LFChi(i1) 
End if
End Do 
 

gPChiM = 0._dp 
gTChiM = 0._dp 
BRChiM = 0._dp 
Call ChiMTwoBodyDecay(-1,DeltaM,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,             & 
& MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,             & 
& ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,             & 
& m2SM,vvSM,gPChiM,gTChiM,BRChiM)

Do i1=1,1
gTFChiM =Sum(gPFChiM(i1,:)) 
If (gTFChiM.Gt.0._dp) BRFChiM(i1,: ) =gPFChiM(i1,:)/gTFChiM 
If (OneLoopDecays) Then 
gT1LFChiM =Sum(gP1LFChiM(i1,:)) 
If (gT1LFChiM.Gt.0._dp) BR1LFChiM(i1,: ) =gP1LFChiM(i1,:)/gT1LFChiM 
End if
End Do 
 

If (.Not.CTBD) Then 
If ((Enable3BDecaysF).and.(Calc3BodyDecay_Fu)) Then 
If (MaxVal(gTFu).Lt.MaxVal(fac3*Abs(MFu))) Then 
Call FuThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFu,gPFu(:,1:0),BRFu(:,1:0))

Else 
Call FuThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.True.,gTFu,gPFu(:,1:0),BRFu(:,1:0))

End If 
 
End If 
Else 
Call FuThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFu,gPFu(:,1:0),BRFu(:,1:0))

End If 
Do i1=1,3
gTFu(i1) =Sum(gPFu(i1,:)) 
If (gTFu(i1).Gt.0._dp) BRFu(i1,: ) =gPFu(i1,:)/gTFu(i1) 
End Do 
 

If (.Not.CTBD) Then 
If ((Enable3BDecaysF).and.(Calc3BodyDecay_Fe)) Then 
If (MaxVal(gTFe).Lt.MaxVal(fac3*Abs(MFe))) Then 
Call FeThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFe,gPFe(:,1:0),BRFe(:,1:0))

Else 
Call FeThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.True.,gTFe,gPFe(:,1:0),BRFe(:,1:0))

End If 
 
End If 
Else 
Call FeThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFe,gPFe(:,1:0),BRFe(:,1:0))

End If 
Do i1=1,3
gTFe(i1) =Sum(gPFe(i1,:)) 
If (gTFe(i1).Gt.0._dp) BRFe(i1,: ) =gPFe(i1,:)/gTFe(i1) 
End Do 
 

If (.Not.CTBD) Then 
If ((Enable3BDecaysF).and.(Calc3BodyDecay_Fd)) Then 
If (MaxVal(gTFd).Lt.MaxVal(fac3*Abs(MFd))) Then 
Call FdThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFd,gPFd(:,1:0),BRFd(:,1:0))

Else 
Call FdThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.True.,gTFd,gPFd(:,1:0),BRFd(:,1:0))

End If 
 
End If 
Else 
Call FdThreeBodyDecay(-1,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,               & 
& MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,              & 
& ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,            & 
& vvSM,epsI,deltaM,.False.,gTFd,gPFd(:,1:0),BRFd(:,1:0))

End If 
Do i1=1,3
gTFd(i1) =Sum(gPFd(i1,:)) 
If (gTFd(i1).Gt.0._dp) BRFd(i1,: ) =gPFd(i1,:)/gTFd(i1) 
End Do 
 

! No 3-body decays for hh  
! No 3-body decays for Chi  
! No 3-body decays for ChiM  
Iname = Iname - 1 
 
End Subroutine CalculateBR 
End Module BranchingRatios_SingletDoubletB 
 