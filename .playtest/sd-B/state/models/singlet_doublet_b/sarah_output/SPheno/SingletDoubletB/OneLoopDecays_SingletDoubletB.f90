! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module OneLoopDecays_SingletDoubletB 
Use Couplings_SingletDoubletB 
Use CouplingsCT_SingletDoubletB 
Use Model_Data_SingletDoubletB 
Use LoopCouplings_SingletDoubletB 
Use LoopMasses_SingletDoubletB 
Use RGEs_SingletDoubletB 
Use Tadpoles_SingletDoubletB 
Use Kinematics 
Use CouplingsForDecays_SingletDoubletB 
 
Use Wrapper_OneLoopDecay_Fu_SingletDoubletB 
Use Wrapper_OneLoopDecay_Fe_SingletDoubletB 
Use Wrapper_OneLoopDecay_Fd_SingletDoubletB 
Use Wrapper_OneLoopDecay_hh_SingletDoubletB 
Use Wrapper_OneLoopDecay_Chi_SingletDoubletB 
Use Wrapper_OneLoopDecay_ChiM_SingletDoubletB 

 
Contains 
 
Subroutine getZCouplings(ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP)

Implicit None

Complex(dp), Intent(in) :: ZRUVd(3,3),ZRUUd(3,3),ZRUVu(3,3),ZRUUu(3,3),ZRUVe(3,3),ZRUUe(3,3),ZRUN(3,3),          & 
& ZRUUM(1,1),ZRUUP(1,1)

Integer :: gt1, gt2
Complex(dp) :: ZRUVdc(3, 3) 
Complex(dp) :: ZRUUdc(3, 3) 
Complex(dp) :: ZRUVuc(3, 3) 
Complex(dp) :: ZRUUuc(3, 3) 
Complex(dp) :: ZRUVec(3, 3) 
Complex(dp) :: ZRUUec(3, 3) 
Complex(dp) :: ZRUNc(3, 3) 
Complex(dp) :: ZRUUMc(1, 1) 
Complex(dp) :: ZRUUPc(1, 1) 
ZRUVdc = Conjg(ZRUVd)
ZRUUdc = Conjg(ZRUUd)
ZRUVuc = Conjg(ZRUVu)
ZRUUuc = Conjg(ZRUUu)
ZRUVec = Conjg(ZRUVe)
ZRUUec = Conjg(ZRUUe)
ZRUNc = Conjg(ZRUN)
ZRUUMc = Conjg(ZRUUM)
ZRUUPc = Conjg(ZRUUP)
End Subroutine  getZCouplings 

Subroutine getGBCouplings(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,             & 
& MFChi2OS,MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,              & 
& MVZ2OS,MVWpOS,MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,               & 
& MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,              & 
& MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ)

Implicit None

Real(dp), Intent(in) :: MFdOS(3),MFd2OS(3),MFuOS(3),MFu2OS(3),MFeOS(3),MFe2OS(3),MFChiOS(3),MFChi2OS(3),      & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS

Complex(dp), Intent(in) :: ZDLOS(3,3),ZDROS(3,3),ZULOS(3,3),ZUROS(3,3),ZELOS(3,3),ZEROS(3,3),NOS(3,3),           & 
& UMOS(1,1),UPOS(1,1)

Real(dp), Intent(in) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp), Intent(in) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Integer :: gt1, gt2, gt3, i1, i2
End Subroutine  getGBCouplings 

Subroutine WaveFunctionRenormalisation(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,               & 
& MFe2OS,MFChiOS,MFChi2OS,MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,            & 
& Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,            & 
& UMOS,UPOS,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,             & 
& Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,              & 
& ZEL,ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,             & 
& dMS,dMPsi,dyh2,dYu,dYd,dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,             & 
& dZER,dN,dUM,dUP,ZfVG,ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,               & 
& ZfUR,ZfEL,ZfER,ZfChi,ZfChiM,ZfChiP,MLambda,deltaM,kont)

Implicit None 
Real(dp),Intent(inout) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(inout) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Real(dp),Intent(inout) :: vvSM

Real(dp),Intent(in) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp),Intent(in) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp),Intent(in) :: MFdOS(3),MFd2OS(3),MFuOS(3),MFu2OS(3),MFeOS(3),MFe2OS(3),MFChiOS(3),MFChi2OS(3),      & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS

Complex(dp),Intent(in) :: ZDLOS(3,3),ZDROS(3,3),ZULOS(3,3),ZUROS(3,3),ZELOS(3,3),ZEROS(3,3),NOS(3,3),           & 
& UMOS(1,1),UPOS(1,1)

Complex(dp) :: SigmaLFd(3,3,3),SigmaSLFd(3,3,3),SigmaSRFd(3,3,3),SigmaRFd(3,3,3),DerSigmaLFd(3,3,3), & 
& DerSigmaSLFd(3,3,3),DerSigmaSRFd(3,3,3),DerSigmaRFd(3,3,3),DerSigmaLirFd(3,3,3),       & 
& DerSigmaSLirFd(3,3,3),DerSigmaSRirFd(3,3,3),DerSigmaRirFd(3,3,3),SigmaLFu(3,3,3),      & 
& SigmaSLFu(3,3,3),SigmaSRFu(3,3,3),SigmaRFu(3,3,3),DerSigmaLFu(3,3,3),DerSigmaSLFu(3,3,3),& 
& DerSigmaSRFu(3,3,3),DerSigmaRFu(3,3,3),DerSigmaLirFu(3,3,3),DerSigmaSLirFu(3,3,3),     & 
& DerSigmaSRirFu(3,3,3),DerSigmaRirFu(3,3,3),SigmaLFe(3,3,3),SigmaSLFe(3,3,3),           & 
& SigmaSRFe(3,3,3),SigmaRFe(3,3,3),DerSigmaLFe(3,3,3),DerSigmaSLFe(3,3,3),               & 
& DerSigmaSRFe(3,3,3),DerSigmaRFe(3,3,3),DerSigmaLirFe(3,3,3),DerSigmaSLirFe(3,3,3),     & 
& DerSigmaSRirFe(3,3,3),DerSigmaRirFe(3,3,3),SigmaLFChi(3,3,3),SigmaSLFChi(3,3,3),       & 
& SigmaSRFChi(3,3,3),SigmaRFChi(3,3,3),DerSigmaLFChi(3,3,3),DerSigmaSLFChi(3,3,3),       & 
& DerSigmaSRFChi(3,3,3),DerSigmaRFChi(3,3,3),DerSigmaLirFChi(3,3,3),DerSigmaSLirFChi(3,3,3),& 
& DerSigmaSRirFChi(3,3,3),DerSigmaRirFChi(3,3,3),SigmaLFChiM(1,1,1),SigmaSLFChiM(1,1,1), & 
& SigmaSRFChiM(1,1,1),SigmaRFChiM(1,1,1),DerSigmaLFChiM(1,1,1),DerSigmaSLFChiM(1,1,1),   & 
& DerSigmaSRFChiM(1,1,1),DerSigmaRFChiM(1,1,1),DerSigmaLirFChiM(1,1,1),DerSigmaSLirFChiM(1,1,1),& 
& DerSigmaSRirFChiM(1,1,1),DerSigmaRirFChiM(1,1,1),SigmaLFv(3,3,3),SigmaSLFv(3,3,3),     & 
& SigmaSRFv(3,3,3),SigmaRFv(3,3,3),DerSigmaLFv(3,3,3),DerSigmaSLFv(3,3,3),               & 
& DerSigmaSRFv(3,3,3),DerSigmaRFv(3,3,3),DerSigmaLirFv(3,3,3),DerSigmaSLirFv(3,3,3),     & 
& DerSigmaSRirFv(3,3,3),DerSigmaRirFv(3,3,3),PiHp,DerPiHp,PiAh,DerPiAh,Pihh,             & 
& DerPihh,PiVG,DerPiVG,PiVP,DerPiVP,PiVZ,DerPiVZ,PiVWp,DerPiVWp,PiVPlight0,              & 
& DerPiVPlight0,PiVPheavy0,DerPiVPheavy0,PiVPlightMZ,DerPiVPlightMZ,PiVPheavyMZ,         & 
& DerPiVPheavyMZ

Complex(dp) :: SigmaLFdDR(3,3,3),SigmaSLFdDR(3,3,3),SigmaSRFdDR(3,3,3),SigmaRFdDR(3,3,3),            & 
& DerSigmaLFdDR(3,3,3),DerSigmaSLFdDR(3,3,3),DerSigmaSRFdDR(3,3,3),DerSigmaRFdDR(3,3,3), & 
& DerSigmaLirFdDR(3,3,3),DerSigmaSLirFdDR(3,3,3),DerSigmaSRirFdDR(3,3,3),DerSigmaRirFdDR(3,3,3),& 
& SigmaLFuDR(3,3,3),SigmaSLFuDR(3,3,3),SigmaSRFuDR(3,3,3),SigmaRFuDR(3,3,3),             & 
& DerSigmaLFuDR(3,3,3),DerSigmaSLFuDR(3,3,3),DerSigmaSRFuDR(3,3,3),DerSigmaRFuDR(3,3,3), & 
& DerSigmaLirFuDR(3,3,3),DerSigmaSLirFuDR(3,3,3),DerSigmaSRirFuDR(3,3,3),DerSigmaRirFuDR(3,3,3),& 
& SigmaLFeDR(3,3,3),SigmaSLFeDR(3,3,3),SigmaSRFeDR(3,3,3),SigmaRFeDR(3,3,3),             & 
& DerSigmaLFeDR(3,3,3),DerSigmaSLFeDR(3,3,3),DerSigmaSRFeDR(3,3,3),DerSigmaRFeDR(3,3,3), & 
& DerSigmaLirFeDR(3,3,3),DerSigmaSLirFeDR(3,3,3),DerSigmaSRirFeDR(3,3,3),DerSigmaRirFeDR(3,3,3),& 
& SigmaLFChiDR(3,3,3),SigmaSLFChiDR(3,3,3),SigmaSRFChiDR(3,3,3),SigmaRFChiDR(3,3,3),     & 
& DerSigmaLFChiDR(3,3,3),DerSigmaSLFChiDR(3,3,3),DerSigmaSRFChiDR(3,3,3),DerSigmaRFChiDR(3,3,3),& 
& DerSigmaLirFChiDR(3,3,3),DerSigmaSLirFChiDR(3,3,3),DerSigmaSRirFChiDR(3,3,3),          & 
& DerSigmaRirFChiDR(3,3,3),SigmaLFChiMDR(1,1,1),SigmaSLFChiMDR(1,1,1),SigmaSRFChiMDR(1,1,1),& 
& SigmaRFChiMDR(1,1,1),DerSigmaLFChiMDR(1,1,1),DerSigmaSLFChiMDR(1,1,1),DerSigmaSRFChiMDR(1,1,1),& 
& DerSigmaRFChiMDR(1,1,1),DerSigmaLirFChiMDR(1,1,1),DerSigmaSLirFChiMDR(1,1,1),          & 
& DerSigmaSRirFChiMDR(1,1,1),DerSigmaRirFChiMDR(1,1,1),SigmaLFvDR(3,3,3),SigmaSLFvDR(3,3,3),& 
& SigmaSRFvDR(3,3,3),SigmaRFvDR(3,3,3),DerSigmaLFvDR(3,3,3),DerSigmaSLFvDR(3,3,3),       & 
& DerSigmaSRFvDR(3,3,3),DerSigmaRFvDR(3,3,3),DerSigmaLirFvDR(3,3,3),DerSigmaSLirFvDR(3,3,3),& 
& DerSigmaSRirFvDR(3,3,3),DerSigmaRirFvDR(3,3,3),PiHpDR,DerPiHpDR,PiAhDR,DerPiAhDR,      & 
& PihhDR,DerPihhDR,PiVGDR,DerPiVGDR,PiVPDR,DerPiVPDR,PiVZDR,DerPiVZDR,PiVWpDR,           & 
& DerPiVWpDR,PiVPlight0DR,DerPiVPlight0DR,PiVPheavy0DR,DerPiVPheavy0DR,PiVPlightMZDR,    & 
& DerPiVPlightMZDR,PiVPheavyMZDR,DerPiVPheavyMZDR

Complex(dp) :: SigmaLFdOS(3,3,3),SigmaSLFdOS(3,3,3),SigmaSRFdOS(3,3,3),SigmaRFdOS(3,3,3),            & 
& DerSigmaLFdOS(3,3,3),DerSigmaSLFdOS(3,3,3),DerSigmaSRFdOS(3,3,3),DerSigmaRFdOS(3,3,3), & 
& DerSigmaLirFdOS(3,3,3),DerSigmaSLirFdOS(3,3,3),DerSigmaSRirFdOS(3,3,3),DerSigmaRirFdOS(3,3,3),& 
& SigmaLFuOS(3,3,3),SigmaSLFuOS(3,3,3),SigmaSRFuOS(3,3,3),SigmaRFuOS(3,3,3),             & 
& DerSigmaLFuOS(3,3,3),DerSigmaSLFuOS(3,3,3),DerSigmaSRFuOS(3,3,3),DerSigmaRFuOS(3,3,3), & 
& DerSigmaLirFuOS(3,3,3),DerSigmaSLirFuOS(3,3,3),DerSigmaSRirFuOS(3,3,3),DerSigmaRirFuOS(3,3,3),& 
& SigmaLFeOS(3,3,3),SigmaSLFeOS(3,3,3),SigmaSRFeOS(3,3,3),SigmaRFeOS(3,3,3),             & 
& DerSigmaLFeOS(3,3,3),DerSigmaSLFeOS(3,3,3),DerSigmaSRFeOS(3,3,3),DerSigmaRFeOS(3,3,3), & 
& DerSigmaLirFeOS(3,3,3),DerSigmaSLirFeOS(3,3,3),DerSigmaSRirFeOS(3,3,3),DerSigmaRirFeOS(3,3,3),& 
& SigmaLFChiOS(3,3,3),SigmaSLFChiOS(3,3,3),SigmaSRFChiOS(3,3,3),SigmaRFChiOS(3,3,3),     & 
& DerSigmaLFChiOS(3,3,3),DerSigmaSLFChiOS(3,3,3),DerSigmaSRFChiOS(3,3,3),DerSigmaRFChiOS(3,3,3),& 
& DerSigmaLirFChiOS(3,3,3),DerSigmaSLirFChiOS(3,3,3),DerSigmaSRirFChiOS(3,3,3),          & 
& DerSigmaRirFChiOS(3,3,3),SigmaLFChiMOS(1,1,1),SigmaSLFChiMOS(1,1,1),SigmaSRFChiMOS(1,1,1),& 
& SigmaRFChiMOS(1,1,1),DerSigmaLFChiMOS(1,1,1),DerSigmaSLFChiMOS(1,1,1),DerSigmaSRFChiMOS(1,1,1),& 
& DerSigmaRFChiMOS(1,1,1),DerSigmaLirFChiMOS(1,1,1),DerSigmaSLirFChiMOS(1,1,1),          & 
& DerSigmaSRirFChiMOS(1,1,1),DerSigmaRirFChiMOS(1,1,1),SigmaLFvOS(3,3,3),SigmaSLFvOS(3,3,3),& 
& SigmaSRFvOS(3,3,3),SigmaRFvOS(3,3,3),DerSigmaLFvOS(3,3,3),DerSigmaSLFvOS(3,3,3),       & 
& DerSigmaSRFvOS(3,3,3),DerSigmaRFvOS(3,3,3),DerSigmaLirFvOS(3,3,3),DerSigmaSLirFvOS(3,3,3),& 
& DerSigmaSRirFvOS(3,3,3),DerSigmaRirFvOS(3,3,3),PiHpOS,DerPiHpOS,PiAhOS,DerPiAhOS,      & 
& PihhOS,DerPihhOS,PiVGOS,DerPiVGOS,PiVPOS,DerPiVPOS,PiVZOS,DerPiVZOS,PiVWpOS,           & 
& DerPiVWpOS,PiVPlight0OS,DerPiVPlight0OS,PiVPheavy0OS,DerPiVPheavy0OS,PiVPlightMZOS,    & 
& DerPiVPlightMZOS,PiVPheavyMZOS,DerPiVPheavyMZOS

Real(dp), Intent(in) :: MLambda, deltaM 

Integer, Intent(out) :: kont 
Real(dp),Intent(out) :: dg1,dg2,dg3,dMS,dMPsi,dyh2,dyh1,dvvSM

Complex(dp),Intent(out) :: dYu(3,3),dYd(3,3),dYe(3,3),dm2SM,dLam,dZDL(3,3),dZDR(3,3),dZUL(3,3),dZUR(3,3),        & 
& dZEL(3,3),dZER(3,3),dN(3,3),dUM(1,1),dUP(1,1)

Complex(dp),Intent(out) :: ZfVG,ZfHp,ZfvL(3,3),ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL(3,3),ZfDR(3,3),ZfUL(3,3),          & 
& ZfUR(3,3),ZfEL(3,3),ZfER(3,3),ZfChi(3,3),ZfChiM,ZfChiP

Real(dp) ::  g1D(66) 
Real(dp) :: p2 
Logical :: TwoLoopRGEsave 
Real(dp) ::MVG,MVP,MVG2,MVP2
Complex(dp) ::  Tad1Loop(1)
Integer :: i1,i2,i3 

MVG = MLambda 
MVP = MLambda 
MVG2 = MLambda**2 
MVP2 = MLambda**2 

!--------------------------
!Fd
!--------------------------
Do i1=1,3
p2 =MFd2(i1)
Call Sigma1LoopFd(p2,SigmaLFd(i1,:,:),SigmaRFd(i1,:,:),SigmaSLFd(i1,:,:)              & 
& ,SigmaSRFd(i1,:,:))

Call DerSigma1LoopFd(p2,DerSigmaLFd(i1,:,:),DerSigmaRFd(i1,:,:),DerSigmaSLFd(i1,:,:)  & 
& ,DerSigmaSRFd(i1,:,:))

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFd(p2,DerSigmaLFdDR(i1,:,:),DerSigmaRFdDR(i1,:,:),DerSigmaSLFdDR(i1,:,:)& 
& ,DerSigmaSRFdDR(i1,:,:))

p2 =MFd2OS(i1)
Call DerSigma1LoopFd(p2,DerSigmaLFdOS(i1,:,:),DerSigmaRFdOS(i1,:,:),DerSigmaSLFdOS(i1,:,:)& 
& ,DerSigmaSRFdOS(i1,:,:))

DerSigmaLFd(i1,:,:) = DerSigmaLFd(i1,:,:) - DerSigmaLFdDR(i1,:,:)! + DerSigmaLFdOS(i1,:,:)
DerSigmaRFd(i1,:,:) = DerSigmaRFd(i1,:,:) - DerSigmaRFdDR(i1,:,:)! + DerSigmaRFdOS(i1,:,:)
DerSigmaSLFd(i1,:,:) = DerSigmaSLFd(i1,:,:) - DerSigmaSLFdDR(i1,:,:)! + DerSigmaSLFdOS(i1,:,:)
DerSigmaSRFd(i1,:,:) = DerSigmaSRFd(i1,:,:) - DerSigmaSRFdDR(i1,:,:)! + DerSigmaSRFdOS(i1,:,:)
DerSigmaLirFd(i1,:,:) = + DerSigmaLFdOS(i1,:,:)
DerSigmaRirFd(i1,:,:) = + DerSigmaRFdOS(i1,:,:)
DerSigmaSLirFd(i1,:,:) = + DerSigmaSLFdOS(i1,:,:)
DerSigmaSRirFd(i1,:,:) = + DerSigmaSRFdOS(i1,:,:)
IRdivonly=.False. 
Else
DerSigmaLirFd(i1,:,:) = 0._dp
DerSigmaRirFd(i1,:,:) = 0._dp
DerSigmaSLirFd(i1,:,:) = 0._dp
DerSigmaSRirFd(i1,:,:) = 0._dp
End if
End do


!--------------------------
!Fu
!--------------------------
Do i1=1,3
p2 =MFu2(i1)
Call Sigma1LoopFu(p2,SigmaLFu(i1,:,:),SigmaRFu(i1,:,:),SigmaSLFu(i1,:,:)              & 
& ,SigmaSRFu(i1,:,:))

Call DerSigma1LoopFu(p2,DerSigmaLFu(i1,:,:),DerSigmaRFu(i1,:,:),DerSigmaSLFu(i1,:,:)  & 
& ,DerSigmaSRFu(i1,:,:))

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFu(p2,DerSigmaLFuDR(i1,:,:),DerSigmaRFuDR(i1,:,:),DerSigmaSLFuDR(i1,:,:)& 
& ,DerSigmaSRFuDR(i1,:,:))

p2 =MFu2OS(i1)
Call DerSigma1LoopFu(p2,DerSigmaLFuOS(i1,:,:),DerSigmaRFuOS(i1,:,:),DerSigmaSLFuOS(i1,:,:)& 
& ,DerSigmaSRFuOS(i1,:,:))

DerSigmaLFu(i1,:,:) = DerSigmaLFu(i1,:,:) - DerSigmaLFuDR(i1,:,:)! + DerSigmaLFuOS(i1,:,:)
DerSigmaRFu(i1,:,:) = DerSigmaRFu(i1,:,:) - DerSigmaRFuDR(i1,:,:)! + DerSigmaRFuOS(i1,:,:)
DerSigmaSLFu(i1,:,:) = DerSigmaSLFu(i1,:,:) - DerSigmaSLFuDR(i1,:,:)! + DerSigmaSLFuOS(i1,:,:)
DerSigmaSRFu(i1,:,:) = DerSigmaSRFu(i1,:,:) - DerSigmaSRFuDR(i1,:,:)! + DerSigmaSRFuOS(i1,:,:)
DerSigmaLirFu(i1,:,:) = + DerSigmaLFuOS(i1,:,:)
DerSigmaRirFu(i1,:,:) = + DerSigmaRFuOS(i1,:,:)
DerSigmaSLirFu(i1,:,:) = + DerSigmaSLFuOS(i1,:,:)
DerSigmaSRirFu(i1,:,:) = + DerSigmaSRFuOS(i1,:,:)
IRdivonly=.False. 
Else
DerSigmaLirFu(i1,:,:) = 0._dp
DerSigmaRirFu(i1,:,:) = 0._dp
DerSigmaSLirFu(i1,:,:) = 0._dp
DerSigmaSRirFu(i1,:,:) = 0._dp
End if
End do


!--------------------------
!Fe
!--------------------------
Do i1=1,3
p2 =MFe2(i1)
Call Sigma1LoopFe(p2,SigmaLFe(i1,:,:),SigmaRFe(i1,:,:),SigmaSLFe(i1,:,:)              & 
& ,SigmaSRFe(i1,:,:))

Call DerSigma1LoopFe(p2,DerSigmaLFe(i1,:,:),DerSigmaRFe(i1,:,:),DerSigmaSLFe(i1,:,:)  & 
& ,DerSigmaSRFe(i1,:,:))

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFe(p2,DerSigmaLFeDR(i1,:,:),DerSigmaRFeDR(i1,:,:),DerSigmaSLFeDR(i1,:,:)& 
& ,DerSigmaSRFeDR(i1,:,:))

p2 =MFe2OS(i1)
Call DerSigma1LoopFe(p2,DerSigmaLFeOS(i1,:,:),DerSigmaRFeOS(i1,:,:),DerSigmaSLFeOS(i1,:,:)& 
& ,DerSigmaSRFeOS(i1,:,:))

DerSigmaLFe(i1,:,:) = DerSigmaLFe(i1,:,:) - DerSigmaLFeDR(i1,:,:)! + DerSigmaLFeOS(i1,:,:)
DerSigmaRFe(i1,:,:) = DerSigmaRFe(i1,:,:) - DerSigmaRFeDR(i1,:,:)! + DerSigmaRFeOS(i1,:,:)
DerSigmaSLFe(i1,:,:) = DerSigmaSLFe(i1,:,:) - DerSigmaSLFeDR(i1,:,:)! + DerSigmaSLFeOS(i1,:,:)
DerSigmaSRFe(i1,:,:) = DerSigmaSRFe(i1,:,:) - DerSigmaSRFeDR(i1,:,:)! + DerSigmaSRFeOS(i1,:,:)
DerSigmaLirFe(i1,:,:) = + DerSigmaLFeOS(i1,:,:)
DerSigmaRirFe(i1,:,:) = + DerSigmaRFeOS(i1,:,:)
DerSigmaSLirFe(i1,:,:) = + DerSigmaSLFeOS(i1,:,:)
DerSigmaSRirFe(i1,:,:) = + DerSigmaSRFeOS(i1,:,:)
IRdivonly=.False. 
Else
DerSigmaLirFe(i1,:,:) = 0._dp
DerSigmaRirFe(i1,:,:) = 0._dp
DerSigmaSLirFe(i1,:,:) = 0._dp
DerSigmaSRirFe(i1,:,:) = 0._dp
End if
End do


!--------------------------
!FChi
!--------------------------
Do i1=1,3
p2 = MFChi2(i1)
Call Sigma1LoopFChi(p2,SigmaLFChi(i1,:,:),SigmaRFChi(i1,:,:),SigmaSLFChi(i1,:,:)      & 
& ,SigmaSRFChi(i1,:,:))

Call DerSigma1LoopFChi(p2,DerSigmaLFChi(i1,:,:),DerSigmaRFChi(i1,:,:),DerSigmaSLFChi(i1,:,:)& 
& ,DerSigmaSRFChi(i1,:,:))

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFChi(p2,DerSigmaLFChiDR(i1,:,:),DerSigmaRFChiDR(i1,:,:)             & 
& ,DerSigmaSLFChiDR(i1,:,:),DerSigmaSRFChiDR(i1,:,:))

p2 =MFChi2OS(i1)
Call DerSigma1LoopFChi(p2,DerSigmaLFChiOS(i1,:,:),DerSigmaRFChiOS(i1,:,:)             & 
& ,DerSigmaSLFChiOS(i1,:,:),DerSigmaSRFChiOS(i1,:,:))

DerSigmaLFChi(i1,:,:) = DerSigmaLFChi(i1,:,:) - DerSigmaLFChiDR(i1,:,:)! + DerSigmaLFChiOS(i1,:,:)
DerSigmaRFChi(i1,:,:) = DerSigmaRFChi(i1,:,:) - DerSigmaRFChiDR(i1,:,:)! + DerSigmaRFChiOS(i1,:,:)
DerSigmaSLFChi(i1,:,:) = DerSigmaSLFChi(i1,:,:) - DerSigmaSLFChiDR(i1,:,:)! + DerSigmaSLFChiOS(i1,:,:)
DerSigmaSRFChi(i1,:,:) = DerSigmaSRFChi(i1,:,:) - DerSigmaSRFChiDR(i1,:,:)! + DerSigmaSRFChiOS(i1,:,:)
DerSigmaLirFChi(i1,:,:) =  + DerSigmaLFChiOS(i1,:,:)
DerSigmaRirFChi(i1,:,:) =  + DerSigmaRFChiOS(i1,:,:)
DerSigmaSLirFChi(i1,:,:) = + DerSigmaSLFChiOS(i1,:,:)
DerSigmaSRirFChi(i1,:,:) = + DerSigmaSRFChiOS(i1,:,:)
IRdivonly=.False. 
Else
DerSigmaLirFChi(i1,:,:) =  0._dp
DerSigmaRirFChi(i1,:,:) =  0._dp
DerSigmaSLirFChi(i1,:,:) = 0._dp
DerSigmaSRirFChi(i1,:,:) = 0._dp
End if
End do


!--------------------------
!FChiM
!--------------------------
Do i1=1,1
p2 =MFChiM2
Call Sigma1LoopFChiM(p2,SigmaLFChiM,SigmaRFChiM,SigmaSLFChiM,SigmaSRFChiM)

Call DerSigma1LoopFChiM(p2,DerSigmaLFChiM,DerSigmaRFChiM,DerSigmaSLFChiM,             & 
& DerSigmaSRFChiM)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFChiM(p2,DerSigmaLFChiMDR,DerSigmaRFChiMDR,DerSigmaSLFChiMDR,       & 
& DerSigmaSRFChiMDR)

p2 =MFChiM2OS
Call DerSigma1LoopFChiM(p2,DerSigmaLFChiMOS,DerSigmaRFChiMOS,DerSigmaSLFChiMOS,       & 
& DerSigmaSRFChiMOS)

DerSigmaLFChiM = DerSigmaLFChiM - DerSigmaLFChiMDR! + DerSigmaLFChiMOS
DerSigmaRFChiM = DerSigmaRFChiM - DerSigmaRFChiMDR! + DerSigmaRFChiMOS
DerSigmaSLFChiM = DerSigmaSLFChiM - DerSigmaSLFChiMDR! + DerSigmaSLFChiMOS
DerSigmaSRFChiM = DerSigmaSRFChiM - DerSigmaSRFChiMDR! + DerSigmaSRFChiMOS
DerSigmaLirFChiM = + DerSigmaLFChiMOS
DerSigmaRirFChiM = + DerSigmaRFChiMOS
DerSigmaSLirFChiM = + DerSigmaSLFChiMOS
DerSigmaSRirFChiM = + DerSigmaSRFChiMOS
IRdivonly=.False. 
Else
DerSigmaLirFChiM = 0._dp
DerSigmaRirFChiM = 0._dp
DerSigmaSLirFChiM = 0._dp
DerSigmaSRirFChiM = 0._dp
End if
End do


!--------------------------
!Fv
!--------------------------
Do i1=1,3
p2 =0._dp
Call Sigma1LoopFv(p2,SigmaLFv(i1,:,:),SigmaRFv(i1,:,:),SigmaSLFv(i1,:,:)              & 
& ,SigmaSRFv(i1,:,:))

Call DerSigma1LoopFv(p2,DerSigmaLFv(i1,:,:),DerSigmaRFv(i1,:,:),DerSigmaSLFv(i1,:,:)  & 
& ,DerSigmaSRFv(i1,:,:))

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerSigma1LoopFv(p2,DerSigmaLFvDR(i1,:,:),DerSigmaRFvDR(i1,:,:),DerSigmaSLFvDR(i1,:,:)& 
& ,DerSigmaSRFvDR(i1,:,:))

p2 =0._dp
Call DerSigma1LoopFv(p2,DerSigmaLFvOS(i1,:,:),DerSigmaRFvOS(i1,:,:),DerSigmaSLFvOS(i1,:,:)& 
& ,DerSigmaSRFvOS(i1,:,:))

DerSigmaLFv(i1,:,:) = DerSigmaLFv(i1,:,:) - DerSigmaLFvDR(i1,:,:)! + DerSigmaLFvOS(i1,:,:)
DerSigmaRFv(i1,:,:) = DerSigmaRFv(i1,:,:) - DerSigmaRFvDR(i1,:,:)! + DerSigmaRFvOS(i1,:,:)
DerSigmaSLFv(i1,:,:) = DerSigmaSLFv(i1,:,:) - DerSigmaSLFvDR(i1,:,:)! + DerSigmaSLFvOS(i1,:,:)
DerSigmaSRFv(i1,:,:) = DerSigmaSRFv(i1,:,:) - DerSigmaSRFvDR(i1,:,:)! + DerSigmaSRFvOS(i1,:,:)
DerSigmaLirFv(i1,:,:) = + DerSigmaLFvOS(i1,:,:)
DerSigmaRirFv(i1,:,:) = + DerSigmaRFvOS(i1,:,:)
DerSigmaSLirFv(i1,:,:) = + DerSigmaSLFvOS(i1,:,:)
DerSigmaSRirFv(i1,:,:) = + DerSigmaSRFvOS(i1,:,:)
IRdivonly=.False. 
Else
DerSigmaLirFv(i1,:,:) = 0._dp
DerSigmaRirFv(i1,:,:) = 0._dp
DerSigmaSLirFv(i1,:,:) = 0._dp
DerSigmaSRirFv(i1,:,:) = 0._dp
End if
End do


!--------------------------
!Hp
!--------------------------
p2 = MHp2
Call Pi1LoopHp(p2,kont,PiHp)

Call DerPi1LoopHp(p2,kont,DerPiHp)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopHp(p2,kont,DerPiHpDR)

p2 = MHp2OS
Call DerPi1LoopHp(p2,kont,DerPiHpOS)

DerPiHp = DerPiHp-DerPiHpDR + DerPiHpOS
IRdivonly=.False. 
End if 
!--------------------------
!Ah
!--------------------------
p2 = MAh2
Call Pi1LoopAh(p2,kont,PiAh)

Call DerPi1LoopAh(p2,kont,DerPiAh)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopAh(p2,kont,DerPiAhDR)

p2 = MAh2OS
Call DerPi1LoopAh(p2,kont,DerPiAhOS)

DerPiAh = DerPiAh-DerPiAhDR + DerPiAhOS
IRdivonly=.False. 
End if 
!--------------------------
!hh
!--------------------------
p2 = Mhh2
Call Pi1Loophh(p2,kont,Pihh)

Call DerPi1Loophh(p2,kont,DerPihh)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1Loophh(p2,kont,DerPihhDR)

p2 = Mhh2OS
Call DerPi1Loophh(p2,kont,DerPihhOS)

DerPihh = DerPihh-DerPihhDR + DerPihhOS
IRdivonly=.False. 
End if 
!--------------------------
!VG
!--------------------------
p2 = MVG2
Call Pi1LoopVG(p2,kont,PiVG)

Call DerPi1LoopVG(p2,kont,DerPiVG)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopVG(p2,kont,DerPiVGDR)

p2 = 0.
Call DerPi1LoopVG(p2,kont,DerPiVGOS)

DerPiVG = DerPiVG-DerPiVGDR + DerPiVGOS
IRdivonly=.False. 
End if 
!--------------------------
!VP
!--------------------------
p2 = MVP2
Call Pi1LoopVP(p2,kont,PiVP)

Call DerPi1LoopVP(p2,kont,DerPiVP)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopVP(p2,kont,DerPiVPDR)

p2 = 0.
Call DerPi1LoopVP(p2,kont,DerPiVPOS)

DerPiVP = DerPiVP-DerPiVPDR + DerPiVPOS
IRdivonly=.False. 
End if 
!--------------------------
!VZ
!--------------------------
p2 = MVZ2
Call Pi1LoopVZ(p2,kont,PiVZ)

Call DerPi1LoopVZ(p2,kont,DerPiVZ)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopVZ(p2,kont,DerPiVZDR)

p2 = MVZ2OS
Call DerPi1LoopVZ(p2,kont,DerPiVZOS)

DerPiVZ = DerPiVZ-DerPiVZDR + DerPiVZOS
IRdivonly=.False. 
End if 
!--------------------------
!VWp
!--------------------------
p2 = MVWp2
Call Pi1LoopVWp(p2,kont,PiVWp)

Call DerPi1LoopVWp(p2,kont,DerPiVWp)

If ((ShiftIRdiv).and.(OSkinematics)) Then 
IRdivonly=.True. 
Call DerPi1LoopVWp(p2,kont,DerPiVWpDR)

p2 = MVWp2OS
Call DerPi1LoopVWp(p2,kont,DerPiVWpOS)

DerPiVWp = DerPiVWp-DerPiVWpDR + DerPiVWpOS
IRdivonly=.False. 
End if 
!--------------------------
! Additional Self-Energies for Photon
!--------------------------
p2 = 0._dp
OnlyLightStates = .True. 
Call Pi1LoopVP(p2,kont,PiVPlight0)

Call DerPi1LoopVP(p2,kont,DerPiVPlight0)

OnlyLightStates = .False. 
p2 = 0._dp
OnlyHeavyStates = .True. 
Call Pi1LoopVP(p2,kont,PiVPheavy0)

Call DerPi1LoopVP(p2,kont,DerPiVPheavy0)

OnlyHeavyStates = .False. 
p2 = MVZ2
OnlyLightStates = .True. 
Call Pi1LoopVP(p2,kont,PiVPlightMZ)

Call DerPi1LoopVP(p2,kont,DerPiVPlightMZ)

OnlyLightStates = .False. 
p2 = MVZ2
OnlyHeavyStates = .True. 
Call Pi1LoopVP(p2,kont,PiVPheavyMZ)

Call DerPi1LoopVP(p2,kont,DerPiVPheavyMZ)

OnlyHeavyStates = .False. 
! -----------------------------------------------------------
! Calculate now all wave-function renormalisation constants 
! -----------------------------------------------------------


!  ######    VG    ###### 
ZfVG = -DerPiVG


!  ######    Hp    ###### 
ZfHp = -DerPiHp


!  ######    vL    ###### 
Do i1=1,3
  Do i2=1,3
   If (i1.eq.i2) Then 
     ZfvL(i1,i2) = -SigmaRFv(i2,i1,i2) 
   Else 
     ZfvL(i1,i2) = 0._dp 
   End if 
  End Do 
End Do 


!  ######    Ah    ###### 
ZfAh = -DerPiAh


!  ######    hh    ###### 
Zfhh = -DerPihh


!  ######    VP    ###### 
ZfVP = -DerPiVP


!  ######    VZ    ###### 
ZfVZ = -DerPiVZ


!  ######    VWp    ###### 
ZfVWp = -DerPiVWp


!  ######    DL    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFd(i1).eq.MFd(i2))) Then 
     ZfDL(i1,i2) = -SigmaRFd(i2,i1,i2) &
      & -MFd2(i1)*(DerSigmaRFd(i2,i1,i2) + DerSigmaLFd(i2,i1,i2))&
      & -MFd(i1)*(DerSigmaSRFd(i2,i1,i2)+DerSigmaSLFd(i2,i1,i2))
     If (OSkinematics) Then 
     ZfDL(i1,i2) = ZfDL(i1,i2) &
      & -MFd2OS(i1)*(DerSigmaRirFd(i2,i1,i2) + DerSigmaLirFd(i2,i1,i2))&
      & -MFdOS(i1)*(DerSigmaSRirFd(i2,i1,i2)+DerSigmaSLirFd(i2,i1,i2))
     Else 
     ZfDL(i1,i2) = ZfDL(i1,i2) &
      & -MFd2(i1)*(DerSigmaRirFd(i2,i1,i2) + DerSigmaLirFd(i2,i1,i2))&
      & -MFd(i1)*(DerSigmaSRirFd(i2,i1,i2)+DerSigmaSLirFd(i2,i1,i2))
     End if 
   Else 
     ZfDL(i1,i2) = 2._dp/(MFd2(i1) - MFd2(i2))* &
      & (MFd2(i2)*SigmaRFd(i2,i1,i2) + MFd(i1)*MFd(i2)*SigmaLFd(i2,i1,i2) + MFd(i1)*SigmaSRFd(i2,i1,i2) + MFd(i2)*SigmaSLFd(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    DR    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFd(i1).eq.MFd(i2))) Then 
     ZfDR(i1,i2) = -SigmaLFd(i2,i1,i2) &
      & -MFd2(i1)*(DerSigmaLFd(i2,i1,i2) + DerSigmaRFd(i2,i1,i2))&
      & -MFd(i1)*(DerSigmaSLFd(i2,i1,i2)+DerSigmaSRFd(i2,i1,i2))
     If (OSkinematics) Then 
     ZfDR(i1,i2) = ZfDR(i1,i2) &
      & -MFd2OS(i1)*(DerSigmaLirFd(i2,i1,i2) + DerSigmaRirFd(i2,i1,i2))&
      & -MFdOS(i1)*(DerSigmaSLirFd(i2,i1,i2)+DerSigmaSRirFd(i2,i1,i2))
     Else 
     ZfDR(i1,i2) = ZfDR(i1,i2) &
      & -MFd2(i1)*(DerSigmaLirFd(i2,i1,i2) + DerSigmaRirFd(i2,i1,i2))&
      & -MFd(i1)*(DerSigmaSLirFd(i2,i1,i2)+DerSigmaSRirFd(i2,i1,i2))
     End if 
   Else 
     ZfDR(i1,i2) = 2._dp/(MFd2(i1) - MFd2(i2))* &
      & (MFd2(i2)*SigmaLFd(i2,i1,i2) + MFd(i1)*MFd(i2)*SigmaRFd(i2,i1,i2) + MFd(i1)*SigmaSLFd(i2,i1,i2) + MFd(i2)*SigmaSRFd(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    UL    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFu(i1).eq.MFu(i2))) Then 
     ZfUL(i1,i2) = -SigmaRFu(i2,i1,i2) &
      & -MFu2(i1)*(DerSigmaRFu(i2,i1,i2) + DerSigmaLFu(i2,i1,i2))&
      & -MFu(i1)*(DerSigmaSRFu(i2,i1,i2)+DerSigmaSLFu(i2,i1,i2))
     If (OSkinematics) Then 
     ZfUL(i1,i2) = ZfUL(i1,i2) &
      & -MFu2OS(i1)*(DerSigmaRirFu(i2,i1,i2) + DerSigmaLirFu(i2,i1,i2))&
      & -MFuOS(i1)*(DerSigmaSRirFu(i2,i1,i2)+DerSigmaSLirFu(i2,i1,i2))
     Else 
     ZfUL(i1,i2) = ZfUL(i1,i2) &
      & -MFu2(i1)*(DerSigmaRirFu(i2,i1,i2) + DerSigmaLirFu(i2,i1,i2))&
      & -MFu(i1)*(DerSigmaSRirFu(i2,i1,i2)+DerSigmaSLirFu(i2,i1,i2))
     End if 
   Else 
     ZfUL(i1,i2) = 2._dp/(MFu2(i1) - MFu2(i2))* &
      & (MFu2(i2)*SigmaRFu(i2,i1,i2) + MFu(i1)*MFu(i2)*SigmaLFu(i2,i1,i2) + MFu(i1)*SigmaSRFu(i2,i1,i2) + MFu(i2)*SigmaSLFu(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    UR    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFu(i1).eq.MFu(i2))) Then 
     ZfUR(i1,i2) = -SigmaLFu(i2,i1,i2) &
      & -MFu2(i1)*(DerSigmaLFu(i2,i1,i2) + DerSigmaRFu(i2,i1,i2))&
      & -MFu(i1)*(DerSigmaSLFu(i2,i1,i2)+DerSigmaSRFu(i2,i1,i2))
     If (OSkinematics) Then 
     ZfUR(i1,i2) = ZfUR(i1,i2) &
      & -MFu2OS(i1)*(DerSigmaLirFu(i2,i1,i2) + DerSigmaRirFu(i2,i1,i2))&
      & -MFuOS(i1)*(DerSigmaSLirFu(i2,i1,i2)+DerSigmaSRirFu(i2,i1,i2))
     Else 
     ZfUR(i1,i2) = ZfUR(i1,i2) &
      & -MFu2(i1)*(DerSigmaLirFu(i2,i1,i2) + DerSigmaRirFu(i2,i1,i2))&
      & -MFu(i1)*(DerSigmaSLirFu(i2,i1,i2)+DerSigmaSRirFu(i2,i1,i2))
     End if 
   Else 
     ZfUR(i1,i2) = 2._dp/(MFu2(i1) - MFu2(i2))* &
      & (MFu2(i2)*SigmaLFu(i2,i1,i2) + MFu(i1)*MFu(i2)*SigmaRFu(i2,i1,i2) + MFu(i1)*SigmaSLFu(i2,i1,i2) + MFu(i2)*SigmaSRFu(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    EL    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFe(i1).eq.MFe(i2))) Then 
     ZfEL(i1,i2) = -SigmaRFe(i2,i1,i2) &
      & -MFe2(i1)*(DerSigmaRFe(i2,i1,i2) + DerSigmaLFe(i2,i1,i2))&
      & -MFe(i1)*(DerSigmaSRFe(i2,i1,i2)+DerSigmaSLFe(i2,i1,i2))
     If (OSkinematics) Then 
     ZfEL(i1,i2) = ZfEL(i1,i2) &
      & -MFe2OS(i1)*(DerSigmaRirFe(i2,i1,i2) + DerSigmaLirFe(i2,i1,i2))&
      & -MFeOS(i1)*(DerSigmaSRirFe(i2,i1,i2)+DerSigmaSLirFe(i2,i1,i2))
     Else 
     ZfEL(i1,i2) = ZfEL(i1,i2) &
      & -MFe2(i1)*(DerSigmaRirFe(i2,i1,i2) + DerSigmaLirFe(i2,i1,i2))&
      & -MFe(i1)*(DerSigmaSRirFe(i2,i1,i2)+DerSigmaSLirFe(i2,i1,i2))
     End if 
   Else 
     ZfEL(i1,i2) = 2._dp/(MFe2(i1) - MFe2(i2))* &
      & (MFe2(i2)*SigmaRFe(i2,i1,i2) + MFe(i1)*MFe(i2)*SigmaLFe(i2,i1,i2) + MFe(i1)*SigmaSRFe(i2,i1,i2) + MFe(i2)*SigmaSLFe(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    ER    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFe(i1).eq.MFe(i2))) Then 
     ZfER(i1,i2) = -SigmaLFe(i2,i1,i2) &
      & -MFe2(i1)*(DerSigmaLFe(i2,i1,i2) + DerSigmaRFe(i2,i1,i2))&
      & -MFe(i1)*(DerSigmaSLFe(i2,i1,i2)+DerSigmaSRFe(i2,i1,i2))
     If (OSkinematics) Then 
     ZfER(i1,i2) = ZfER(i1,i2) &
      & -MFe2OS(i1)*(DerSigmaLirFe(i2,i1,i2) + DerSigmaRirFe(i2,i1,i2))&
      & -MFeOS(i1)*(DerSigmaSLirFe(i2,i1,i2)+DerSigmaSRirFe(i2,i1,i2))
     Else 
     ZfER(i1,i2) = ZfER(i1,i2) &
      & -MFe2(i1)*(DerSigmaLirFe(i2,i1,i2) + DerSigmaRirFe(i2,i1,i2))&
      & -MFe(i1)*(DerSigmaSLirFe(i2,i1,i2)+DerSigmaSRirFe(i2,i1,i2))
     End if 
   Else 
     ZfER(i1,i2) = 2._dp/(MFe2(i1) - MFe2(i2))* &
      & (MFe2(i2)*SigmaLFe(i2,i1,i2) + MFe(i1)*MFe(i2)*SigmaRFe(i2,i1,i2) + MFe(i1)*SigmaSLFe(i2,i1,i2) + MFe(i2)*SigmaSRFe(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    Chi    ###### 
Do i1=1,3
  Do i2=1,3
   If ((i1.eq.i2).or.(MFChi(i1).eq.MFChi(i2))) Then 
     ZfChi(i1,i2) = -SigmaRFChi(i2,i1,i2) &
      & -MFChi2(i1)*(DerSigmaRFChi(i2,i1,i2) + DerSigmaLFChi(i2,i1,i2))&
      & -MFChi(i1)*(DerSigmaSRFChi(i2,i1,i2)+DerSigmaSLFChi(i2,i1,i2))
     If (OSkinematics) Then 
     ZfChi(i1,i2) = ZfChi(i1,i2) &
      & -MFChi2OS(i1)*(DerSigmaRirFChi(i2,i1,i2) + DerSigmaLirFChi(i2,i1,i2))&
      & -MFChiOS(i1)*(DerSigmaSRirFChi(i2,i1,i2)+DerSigmaSLirFChi(i2,i1,i2))
     Else 
     ZfChi(i1,i2) = ZfChi(i1,i2) &
      & -MFChi2(i1)*(DerSigmaRirFChi(i2,i1,i2) + DerSigmaLirFChi(i2,i1,i2))&
      & -MFChi(i1)*(DerSigmaSRirFChi(i2,i1,i2)+DerSigmaSLirFChi(i2,i1,i2))
     End if 
   Else 
     ZfChi(i1,i2) = 2._dp/(MFChi2(i1) - MFChi2(i2))* &
      & (MFChi2(i2)*SigmaRFChi(i2,i1,i2) + MFChi(i1)*MFChi(i2)*SigmaLFChi(i2,i1,i2) + MFChi(i1)*SigmaSRFChi(i2,i1,i2) + MFChi(i2)*SigmaSLFChi(i2,i1,i2))
   End if 
  End Do 
End Do 


!  ######    ChiM    ###### 
ZfChiM = -SigmaRFChiM + &
& -MFChiM*(MFChiM*DerSigmaRFChiM+MFChiM*DerSigmaLFChiM+DerSigmaSRFChiM+DerSigmaSLFChiM)
If (OSkinematics) Then 
ZfChiM = ZfChiM &
& + -MFChiMOS*(MFChiMOS*DerSigmaRirFChiM+MFChiMOS*DerSigmaLirFChiM+(DerSigmaSRirFChiM+DerSigmaSLirFChiM))
Else 
ZfChiM = ZfChiM &
& + -MFChiM*(MFChiM*DerSigmaRirFChiM+MFChiM*DerSigmaLirFChiM+(DerSigmaSRirFChiM+DerSigmaSLirFChiM))
End if 


!  ######    ChiP    ###### 
ZfChiP = -SigmaLFChiM + &
& -MFChiM*(MFChiM*DerSigmaLFChiM+MFChiM*DerSigmaRFChiM+DerSigmaSLFChiM+DerSigmaSRFChiM)
If (OSkinematics) Then 
ZfChiP = ZfChiP &
& + -MFChiMOS*(MFChiMOS*DerSigmaLirFChiM+MFChiMOS*DerSigmaRirFChiM+(DerSigmaSLirFChiM+DerSigmaSRirFChiM))
Else 
ZfChiP = ZfChiP &
& + -MFChiM*(MFChiM*DerSigmaLirFChiM+MFChiM*DerSigmaRirFChiM+(DerSigmaSLirFChiM+DerSigmaSRirFChiM))
End if 
! -----------------------------------------------------------
! Setting the Counter-Terms 
! -----------------------------------------------------------
! ----------- getting the divergent pieces ---------

 
 ! --- GUT normalize gauge couplings --- 
g1 = Sqrt(5._dp/3._dp)*g1 
! ----------------------- 
 
Call ParametersToG66(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,g1D)

TwoLoopRGEsave=TwoLoopRGE 
TwoLoopRGE=.False. 
Call rge66(66,0._dp,g1D,g1D) 
TwoLoopRGE=TwoLoopRGEsave 
Call GToParameters66(g1D,dg1,dg2,dg3,dLam,dyh2,dYu,dYd,dYe,dyh1,dMS,dMPsi,            & 
& dm2SM,dvvSM)


 
 ! --- Remove GUT-normalization of gauge couplings --- 
dg1 = Sqrt(3._dp/5._dp)*dg1 
! ----------------------- 
 

 
 ! --- Remove GUT-normalization of gauge couplings --- 
g1 = Sqrt(3._dp/5._dp)*g1 
! ----------------------- 
 
dg1 = 0.5_dp*divergence*dg1 
dg2 = 0.5_dp*divergence*dg2 
dg3 = 0.5_dp*divergence*dg3 
dMS = 0.5_dp*divergence*dMS 
dMPsi = 0.5_dp*divergence*dMPsi 
dyh2 = 0.5_dp*divergence*dyh2 
dYu = 0.5_dp*divergence*dYu 
dYd = 0.5_dp*divergence*dYd 
dYe = 0.5_dp*divergence*dYe 
dyh1 = 0.5_dp*divergence*dyh1 
dm2SM = 0.5_dp*divergence*dm2SM 
dLam = 0.5_dp*divergence*dLam 
dvvSM = 0.5_dp*divergence*dvvSM 
dZDL = 0._dp 
dZDR = 0._dp 
dZUL = 0._dp 
dZUR = 0._dp 
dZEL = 0._dp 
dZER = 0._dp 
dN = 0._dp 
dUM = 0._dp 
dUP = 0._dp 
If (CTinLoopDecays) Then 
dCosTW = ((PiVWp/MVWp**2 - PiVZ/mVZ**2)*Cos(TW))/2._dp 
dSinTW = -(dCosTW*1/Tan(TW)) 
dg2 = (g2*(derPiVPheavy0 + PiVPlightMZ/MVZ**2 - (-(PiVWp/MVWp**2) + PiVZ/MVZ**2)*1/Tan(TW)**2 + (2*PiVZVP*Tan(TW))/MVZ**2))/2._dp 
dg1 = dSinTW*g2*1/Cos(TW) + dg2*Tan(TW) - dCosTW*g2*1/Cos(TW)*Tan(TW) 
End if 
 
dN = 0.25_dp*MatMul(ZfChi- Conjg(Transpose(ZfChi)),N)
dZDR = 0.25_dp*MatMul(ZfDR- Conjg(Transpose(ZfDR)),ZDR)
dZER = 0.25_dp*MatMul(ZfER- Conjg(Transpose(ZfER)),ZER)
dUM = 0.25_dp*MatMul(ZfChiM- Conjg(Transpose(ZfChiM)),UM)
dUP = 0.25_dp*MatMul(ZfChiP- Conjg(Transpose(ZfChiP)),UP)
dZUR = 0.25_dp*MatMul(ZfUR- Conjg(Transpose(ZfUR)),ZUR)
dZDL = 0.25_dp*MatMul(ZfDL- Conjg(Transpose(ZfDL)),ZDL)
dZEL = 0.25_dp*MatMul(ZfEL- Conjg(Transpose(ZfEL)),ZEL)
dZUL = 0.25_dp*MatMul(ZfUL- Conjg(Transpose(ZfUL)),ZUL)


! -----------------------------------------------------------
! Calculating the CT vertices 
! -----------------------------------------------------------
Call CalculateCouplingCT)

End Subroutine WaveFunctionRenormalisation 
Subroutine CalculateOneLoopDecays(gP1LFu,gP1LFe,gP1LFd,gP1Lhh,gP1LChi,gP1LChiM,       & 
& MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,MFChiMOS,MFChiM2OS,            & 
& MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS,ZDLOS,              & 
& ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,               & 
& Ye,yh1,MS,MPsi,m2SM,epsI,deltaM,kont)

Implicit None 
Real(dp), Intent(in) :: epsI, deltaM 
Integer, Intent(inout) :: kont 
Real(dp) :: MLambda, em, gs, vSM, sinW2, g1SM, g2SM 
Integer :: divset, i1 
Complex(dp) :: divvalue, YuSM(3,3), YdSM(3,3), YeSM(3,3) 
Real(dp),Intent(inout) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(inout) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Real(dp),Intent(inout) :: vvSM

Real(dp) :: dg1,dg2,dg3,dMS,dMPsi,dyh2,dyh1,dvvSM

Complex(dp) :: dYu(3,3),dYd(3,3),dYe(3,3),dm2SM,dLam,dZDL(3,3),dZDR(3,3),dZUL(3,3),dZUR(3,3),        & 
& dZEL(3,3),dZER(3,3),dN(3,3),dUM(1,1),dUP(1,1)

Complex(dp) :: ZfVG,ZfHp,ZfvL(3,3),ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL(3,3),ZfDR(3,3),ZfUL(3,3),          & 
& ZfUR(3,3),ZfEL(3,3),ZfER(3,3),ZfChi(3,3),ZfChiM,ZfChiP

Real(dp),Intent(in) :: MFdOS(3),MFd2OS(3),MFuOS(3),MFu2OS(3),MFeOS(3),MFe2OS(3),MFChiOS(3),MFChi2OS(3),      & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS

Complex(dp),Intent(in) :: ZDLOS(3,3),ZDROS(3,3),ZULOS(3,3),ZUROS(3,3),ZELOS(3,3),ZEROS(3,3),NOS(3,3),           & 
& UMOS(1,1),UPOS(1,1)

Real(dp) :: p2, q2, q2_save 
Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Complex(dp) :: ZRUVd(3,3),ZRUUd(3,3),ZRUVu(3,3),ZRUUu(3,3),ZRUVe(3,3),ZRUUe(3,3),ZRUN(3,3),          & 
& ZRUUM(1,1),ZRUUP(1,1)

Real(dp), Intent(out) :: gP1LFu(3,0) 
Real(dp), Intent(out) :: gP1LFe(3,0) 
Real(dp), Intent(out) :: gP1LFd(3,0) 
Real(dp), Intent(out) :: gP1Lhh(1,4) 
Real(dp), Intent(out) :: gP1LChi(3,0) 
Real(dp), Intent(out) :: gP1LChiM(1,0) 
Iname = Iname + 1 
NameOfUnit(Iname) = 'CalculateOneLoopDecays'
 
Write(*,*) "Calculating one loop decays" 
! Regulator mass for gluon/photon 
MLambda = Mass_Regulator_PhotonGluon 
divset=SetDivonlyAdd(INT(divonly_save)) 
divvalue=SetDivergenceAdd(divergence_save) 
If (.not.CalculateOneLoopMasses) Then 
 If (OSkinematics) Then 
  Write(*,*) "Loop masses not calculated: tree-level masses used for kinematics" 
  OSkinematics = .false. 
 End if
 If (ExternalZfactors) Then 
  Write(*,*) "Loop masses not calculated: no U-factors are applied" 
  ExternalZfactors = .false. 
 End if
End if

If (Extra_scale_loopDecays) Then 
q2_save = GetRenormalizationScale() 
q2 = SetRenormalizationScale(scale_loopdecays **2) 
End if 
If ((OSkinematics).or.(ExternalZfactors)) ShiftIRdiv = .true. 
If (ewOSinDecays) Then 
sinW2=1._dp-mW2/mZ2 
g1SM=sqrt(4*Pi*Alpha_MZ/(1-sinW2)) 
g2SM=sqrt(4*Pi*Alpha_MZ/Sinw2) 
vSM=sqrt(mz2*4._dp/(g1SM**2+g2SM**2)) 
vvSM=vSM 
g1=g1SM 
g2=g2SM 
 If (yukOSinDecays) Then !! Allow OS Yukawas only together with vSM 
    YuSM = 0._dp 
    YdSM = 0._dp 
    YuSM = 0._dp 
   Do i1=1,3 
      YuSM(i1,i1)=sqrt(2._dp)*mf_u(i1)/vSM 
      YeSM(i1,i1)=sqrt(2._dp)*mf_l(i1)/vSM 
      YdSM(i1,i1)=sqrt(2._dp)*mf_d(i1)/vSM 
    End Do 
   If(GenerationMixing) Then 
    YuSM = Transpose(Matmul(Transpose(CKM),Transpose(YuSM))) 
   End if 
Ye=YeSM 
Yd=YdSM 
Yu=YuSM 
 End if 
End if 
! -------------------------------------------- 
! General information needed in the following 
! -------------------------------------------- 

! DR parameters 
Call SolveTadpoleEquations(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,           & 
& (/ ZeroC /))

Call TreeMasses(MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,             & 
& ZUR,ZDL,ZEL,ZUL,ZW,ZZ,vvSM,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,GenerationMixing,kont)

! Stabilize numerics 
If (Abs(MHp).lt.1.0E-15_dp) MHp=0._dp
If (Abs(MHp2).lt.1.0E-30_dp) MHp2=0._dp
If (Abs(MAh).lt.1.0E-15_dp) MAh=0._dp
If (Abs(MAh2).lt.1.0E-30_dp) MAh2=0._dp
If (Abs(Mhh).lt.1.0E-15_dp) Mhh=0._dp
If (Abs(Mhh2).lt.1.0E-30_dp) Mhh2=0._dp
Where (Abs(MFd).lt.1.0E-15_dp) MFd=0._dp
Where (Abs(MFd2).lt.1.0E-30_dp) MFd2=0._dp
Where (Abs(MFu).lt.1.0E-15_dp) MFu=0._dp
Where (Abs(MFu2).lt.1.0E-30_dp) MFu2=0._dp
Where (Abs(MFe).lt.1.0E-15_dp) MFe=0._dp
Where (Abs(MFe2).lt.1.0E-30_dp) MFe2=0._dp
Where (Abs(MFChi).lt.1.0E-15_dp) MFChi=0._dp
Where (Abs(MFChi2).lt.1.0E-30_dp) MFChi2=0._dp
If (Abs(MFChiM).lt.1.0E-15_dp) MFChiM=0._dp
If (Abs(MFChiM2).lt.1.0E-30_dp) MFChiM2=0._dp
If (UseZeroRotationMatrices) Then  ! Rotation matrices calculated for p2=0
ZRUVd = MatMul(ZDLOS_0, Conjg(Transpose(ZDL)))
ZRUUd = MatMul(ZDROS_0, Conjg(Transpose(ZDR)))
ZRUVu = MatMul(ZULOS_0, Conjg(Transpose(ZUL)))
ZRUUu = MatMul(ZUROS_0, Conjg(Transpose(ZUR)))
ZRUVe = MatMul(ZELOS_0, Conjg(Transpose(ZEL)))
ZRUUe = MatMul(ZEROS_0, Conjg(Transpose(ZER)))
ZRUN = MatMul(NOS_0, Conjg(Transpose(N)))
ZRUUM = MatMul(UMOS_0, Conjg(Transpose(UM)))
ZRUUP = MatMul(UPOS_0, Conjg(Transpose(UP)))
Else If (UseP2Matrices) Then   ! p2 dependent matrix 
ZRUVd = MatMul(ZDLOS_p2, Conjg(Transpose(ZDL)))
ZRUUd = MatMul(ZDROS_p2, Conjg(Transpose(ZDR)))
ZRUVu = MatMul(ZULOS_p2, Conjg(Transpose(ZUL)))
ZRUUu = MatMul(ZUROS_p2, Conjg(Transpose(ZUR)))
ZRUVe = MatMul(ZELOS_p2, Conjg(Transpose(ZEL)))
ZRUUe = MatMul(ZEROS_p2, Conjg(Transpose(ZER)))
ZRUN = MatMul(NOS_p2, Conjg(Transpose(N)))
ZRUUM = MatMul(UMOS_p2, Conjg(Transpose(UM)))
ZRUUP = MatMul(UPOS_p2, Conjg(Transpose(UP)))
Else  ! Rotation matrix for lightest state
ZRUVd = MatMul(ZDLOS, Conjg(Transpose(ZDL)))
ZRUUd = MatMul(ZDROS, Conjg(Transpose(ZDR)))
ZRUVu = MatMul(ZULOS, Conjg(Transpose(ZUL)))
ZRUUu = MatMul(ZUROS, Conjg(Transpose(ZUR)))
ZRUVe = MatMul(ZELOS, Conjg(Transpose(ZEL)))
ZRUUe = MatMul(ZEROS, Conjg(Transpose(ZER)))
ZRUN = MatMul(NOS, Conjg(Transpose(N)))
ZRUUM = MatMul(UMOS, Conjg(Transpose(UM)))
ZRUUP = MatMul(UPOS, Conjg(Transpose(UP)))
End if 
! Couplings 
Call AllCouplingsReallyAll)

em = 1 
gs = 1(1,1) 
Call CouplingsColoredQuartics)

If (externalZfactors) Then 
Call getZCouplings(ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP)

End if 
Call getGBCouplings(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,          & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ)

! Write intilization of all counter terms 
Call WaveFunctionRenormalisation(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,              & 
& MFChiOS,MFChi2OS,MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,            & 
& MVZOS,MVZ2OS,MVWpOS,MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,              & 
& UPOS,MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,              & 
& Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,              & 
& ZUL,ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,             & 
& dMPsi,dyh2,dYu,dYd,dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,            & 
& dN,dUM,dUP,ZfVG,ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,               & 
& ZfEL,ZfER,ZfChi,ZfChiM,ZfChiP,MLambda,deltaM,kont)

! -------------------------------------------- 
! The decays at one-loop 
! -------------------------------------------- 

! Fu
If (CalcLoopDecay_Fu) Then 
Call OneLoopDecay_Fu(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,         & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1LFu)

End if 
! Fe
If (CalcLoopDecay_Fe) Then 
Call OneLoopDecay_Fe(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,         & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1LFe)

End if 
! Fd
If (CalcLoopDecay_Fd) Then 
Call OneLoopDecay_Fd(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,         & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1LFd)

End if 
! hh
If (CalcLoopDecay_hh) Then 
Call OneLoopDecay_hh(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,         & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1Lhh)

End if 
! Chi
If (CalcLoopDecay_Chi) Then 
Call OneLoopDecay_Chi(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,        & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1LChi)

End if 
! ChiM
If (CalcLoopDecay_ChiM) Then 
Call OneLoopDecay_ChiM(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,MFChi2OS,       & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,         & 
& MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,MAh,MAh2,MFChi,              & 
& MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,MHp,MHp2,MVWp,               & 
& MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,ZW,ZZ,g1,g2,g3,              & 
& Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,dyh2,dYu,dYd,             & 
& dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,dUM,dUP,ZfVG,               & 
& ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,ZfER,ZfChi,               & 
& ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,ZRUUP,MLambda,            & 
& em,gs,deltaM,kont,gP1LChiM)

End if 
If (Extra_scale_loopDecays) Then 
q2 = SetRenormalizationScale(q2_save) 
End if 
Iname = Iname - 1 
 
End Subroutine CalculateOneLoopDecays  
 
 
End Module OneLoopDecays_SingletDoubletB 
 