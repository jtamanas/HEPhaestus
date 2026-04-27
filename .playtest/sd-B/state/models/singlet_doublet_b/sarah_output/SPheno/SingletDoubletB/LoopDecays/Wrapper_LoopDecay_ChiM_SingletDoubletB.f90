! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module Wrapper_OneLoopDecay_ChiM_SingletDoubletB
Use Model_Data_SingletDoubletB 
Use Kinematics 
Use OneLoopDecay_ChiM_SingletDoubletB 
Use Control 
Use Settings 

 
Contains

 
Subroutine OneLoopDecay_ChiM(MFdOS,MFd2OS,MFuOS,MFu2OS,MFeOS,MFe2OS,MFChiOS,          & 
& MFChi2OS,MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,              & 
& MVZ2OS,MVWpOS,MVWp2OS,ZDLOS,ZDROS,ZULOS,ZUROS,ZELOS,ZEROS,NOS,UMOS,UPOS,               & 
& MAh,MAh2,MFChi,MFChi2,MFChiM,MFChiM2,MFd,MFd2,MFe,MFe2,MFu,MFu2,Mhh,Mhh2,              & 
& MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,N,PhaseFS,TW,ZDR,ZER,UM,UP,ZUR,ZDL,ZEL,ZUL,               & 
& ZW,ZZ,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,dg1,dg2,dg3,dMS,dMPsi,           & 
& dyh2,dYu,dYd,dYe,dyh1,dm2SM,dLam,dvvSM,dZDL,dZDR,dZUL,dZUR,dZEL,dZER,dN,               & 
& dUM,dUP,ZfVG,ZfHp,ZfvL,ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL,ZfDR,ZfUL,ZfUR,ZfEL,             & 
& ZfER,ZfChi,ZfChiM,ZfChiP,ZRUVd,ZRUUd,ZRUVu,ZRUUu,ZRUVe,ZRUUe,ZRUN,ZRUUM,               & 
& ZRUUP,MLambda,em,gs,deltaM,kont,gP1LChiM)

Implicit None 
Real(dp),Intent(in) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(in) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Real(dp),Intent(in) :: vvSM

Real(dp),Intent(in) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             & 
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2,TW,ZZ(2,2)

Complex(dp),Intent(in) :: N(3,3),PhaseFS,ZDR(3,3),ZER(3,3),UM(1,1),UP(1,1),ZUR(3,3),ZDL(3,3),ZEL(3,3),          & 
& ZUL(3,3),ZW(2,2)

Real(dp),Intent(in) :: dg1,dg2,dg3,dMS,dMPsi,dyh2,dyh1,dvvSM

Complex(dp),Intent(in) :: dYu(3,3),dYd(3,3),dYe(3,3),dm2SM,dLam,dZDL(3,3),dZDR(3,3),dZUL(3,3),dZUR(3,3),        & 
& dZEL(3,3),dZER(3,3),dN(3,3),dUM(1,1),dUP(1,1)

Real(dp), Intent(in) :: em, gs 
Complex(dp),Intent(in) :: ZfVG,ZfHp,ZfvL(3,3),ZfAh,Zfhh,ZfVP,ZfVZ,ZfVWp,ZfDL(3,3),ZfDR(3,3),ZfUL(3,3),          & 
& ZfUR(3,3),ZfEL(3,3),ZfER(3,3),ZfChi(3,3),ZfChiM,ZfChiP

Real(dp),Intent(in) :: MFdOS(3),MFd2OS(3),MFuOS(3),MFu2OS(3),MFeOS(3),MFe2OS(3),MFChiOS(3),MFChi2OS(3),      & 
& MFChiMOS,MFChiM2OS,MHpOS,MHp2OS,MAhOS,MAh2OS,MhhOS,Mhh2OS,MVZOS,MVZ2OS,MVWpOS,MVWp2OS

Complex(dp),Intent(in) :: ZDLOS(3,3),ZDROS(3,3),ZULOS(3,3),ZUROS(3,3),ZELOS(3,3),ZEROS(3,3),NOS(3,3),           & 
& UMOS(1,1),UPOS(1,1)

Complex(dp),Intent(in) :: ZRUVd(3,3),ZRUUd(3,3),ZRUVu(3,3),ZRUUu(3,3),ZRUVe(3,3),ZRUUe(3,3),ZRUN(3,3),          & 
& ZRUUM(1,1),ZRUUP(1,1)

Real(dp), Intent(in) :: MLambda, deltaM 
Real(dp), Intent(out) :: gP1LChiM(1,0) 
Integer, Intent(out) :: kont 
Real(dp) :: MVG,MVP,MVG2,MVP2, helfactor, phasespacefactor 
Integer :: i1,i2,i3,i4, isave, gt1, gt2, gt3 

Complex(dp) :: ZRUVdc(3, 3) 
Complex(dp) :: ZRUUdc(3, 3) 
Complex(dp) :: ZRUVuc(3, 3) 
Complex(dp) :: ZRUUuc(3, 3) 
Complex(dp) :: ZRUVec(3, 3) 
Complex(dp) :: ZRUUec(3, 3) 
Complex(dp) :: ZRUNc(3, 3) 
Complex(dp) :: ZRUUMc(1, 1) 
Complex(dp) :: ZRUUPc(1, 1) 
Write(*,*) "Calculating one-loop decays of ChiM " 
kont = 0 
MVG = MLambda 
MVP = MLambda 
MVG2 = MLambda**2 
MVP2 = MLambda**2 

ZRUVdc = Conjg(ZRUVd)
ZRUUdc = Conjg(ZRUUd)
ZRUVuc = Conjg(ZRUVu)
ZRUUuc = Conjg(ZRUUu)
ZRUVec = Conjg(ZRUVe)
ZRUUec = Conjg(ZRUUe)
ZRUNc = Conjg(ZRUN)
ZRUUMc = Conjg(ZRUUM)
ZRUUPc = Conjg(ZRUUP)

 ! Counter 
isave = 1 

End Subroutine OneLoopDecay_ChiM

End Module Wrapper_OneLoopDecay_ChiM_SingletDoubletB
