! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module FlavorKit_LFV_SingletDoubletB 
Use Control 
Use Settings 
Use Couplings_SingletDoubletB 
Use LoopCouplings_SingletDoubletB 
Use LoopMasses_SM_HC 
Use LoopFunctions 
Use LoopMasses_SingletDoubletB 
Use StandardModel 

 
 Contains 
 
Subroutine CalculateBox2L2d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,BOllddSLL,       & 
& BOllddSRR,BOllddSRL,BOllddSLR,BOllddVRR,BOllddVLL,BOllddVRL,BOllddVLR,BOllddTLL,       & 
& BOllddTLR,BOllddTRL,BOllddTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box2L2d 
! 'PreSARAH' output has been generated  at 12:42 on 13.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BOllddSLL 
Complex(dp), Intent(out) :: BOllddSRR 
Complex(dp), Intent(out) :: BOllddSRL 
Complex(dp), Intent(out) :: BOllddSLR 
Complex(dp), Intent(out) :: BOllddVRR 
Complex(dp), Intent(out) :: BOllddVLL 
Complex(dp), Intent(out) :: BOllddVRL 
Complex(dp), Intent(out) :: BOllddVLR 
Complex(dp), Intent(out) :: BOllddTLL 
Complex(dp), Intent(out) :: BOllddTLR 
Complex(dp), Intent(out) :: BOllddTRL 
Complex(dp), Intent(out) :: BOllddTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox2L2d' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
BOllddSLL=0._dp 
BOllddSRR=0._dp 
BOllddSRL=0._dp 
BOllddSLR=0._dp 
BOllddVRR=0._dp 
BOllddVLL=0._dp 
BOllddVRL=0._dp 
BOllddVLR=0._dp 
BOllddTLL=0._dp 
BOllddTLR=0._dp 
BOllddTRL=0._dp 
BOllddTRR=0._dp 
BOllddSLL=oo16pi2*BOllddSLL 
BOllddSRR=oo16pi2*BOllddSRR 
BOllddSRL=oo16pi2*BOllddSRL 
BOllddSLR=oo16pi2*BOllddSLR 
BOllddVRR=oo16pi2*BOllddVRR 
BOllddVLL=oo16pi2*BOllddVLL 
BOllddVRL=oo16pi2*BOllddVRL 
BOllddVLR=oo16pi2*BOllddVLR 
BOllddTLL=oo16pi2*BOllddTLL 
BOllddTLR=oo16pi2*BOllddTLR 
BOllddTRL=oo16pi2*BOllddTRL 
BOllddTRR=oo16pi2*BOllddTRR 
Iname=Iname-1

End Subroutine CalculateBox2L2d 

Subroutine CalculatePengS2L2d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& PSOllddSLL,PSOllddSRR,PSOllddSRL,PSOllddSLR,PSOllddVRR,PSOllddVLL,PSOllddVRL,          & 
& PSOllddVLR,PSOllddTLL,PSOllddTLR,PSOllddTRL,PSOllddTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS2L2d 
! 'PreSARAH' output has been generated  at 13:46 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSOllddSLL 
Complex(dp), Intent(out) :: PSOllddSRR 
Complex(dp), Intent(out) :: PSOllddSRL 
Complex(dp), Intent(out) :: PSOllddSLR 
Complex(dp), Intent(out) :: PSOllddVRR 
Complex(dp), Intent(out) :: PSOllddVLL 
Complex(dp), Intent(out) :: PSOllddVRL 
Complex(dp), Intent(out) :: PSOllddVLR 
Complex(dp), Intent(out) :: PSOllddTLL 
Complex(dp), Intent(out) :: PSOllddTLR 
Complex(dp), Intent(out) :: PSOllddTRL 
Complex(dp), Intent(out) :: PSOllddTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS2L2d' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
PSOllddSLL=0._dp 
PSOllddSRR=0._dp 
PSOllddSRL=0._dp 
PSOllddSLR=0._dp 
PSOllddVRR=0._dp 
PSOllddVLL=0._dp 
PSOllddVRL=0._dp 
PSOllddVLR=0._dp 
PSOllddTLL=0._dp 
PSOllddTLR=0._dp 
PSOllddTRL=0._dp 
PSOllddTRR=0._dp 
PSOllddSLL=oo16pi2*PSOllddSLL 
PSOllddSRR=oo16pi2*PSOllddSRR 
PSOllddSRL=oo16pi2*PSOllddSRL 
PSOllddSLR=oo16pi2*PSOllddSLR 
PSOllddVRR=oo16pi2*PSOllddVRR 
PSOllddVLL=oo16pi2*PSOllddVLL 
PSOllddVRL=oo16pi2*PSOllddVRL 
PSOllddVLR=oo16pi2*PSOllddVLR 
PSOllddTLL=oo16pi2*PSOllddTLL 
PSOllddTLR=oo16pi2*PSOllddTLR 
PSOllddTRL=oo16pi2*PSOllddTRL 
PSOllddTRR=oo16pi2*PSOllddTRR 
Iname=Iname-1

End Subroutine CalculatePengS2L2d 

Subroutine CalculatePengV2L2d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& PVOllddSLL,PVOllddSRR,PVOllddSRL,PVOllddSLR,PVOllddVRR,PVOllddVLL,PVOllddVRL,          & 
& PVOllddVLR,PVOllddTLL,PVOllddTLR,PVOllddTRL,PVOllddTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV2L2d 
! 'PreSARAH' output has been generated  at 13:50 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVOllddSLL 
Complex(dp), Intent(out) :: PVOllddSRR 
Complex(dp), Intent(out) :: PVOllddSRL 
Complex(dp), Intent(out) :: PVOllddSLR 
Complex(dp), Intent(out) :: PVOllddVRR 
Complex(dp), Intent(out) :: PVOllddVLL 
Complex(dp), Intent(out) :: PVOllddVRL 
Complex(dp), Intent(out) :: PVOllddVLR 
Complex(dp), Intent(out) :: PVOllddTLL 
Complex(dp), Intent(out) :: PVOllddTLR 
Complex(dp), Intent(out) :: PVOllddTRL 
Complex(dp), Intent(out) :: PVOllddTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV2L2d' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
PVOllddSLL=0._dp 
PVOllddSRR=0._dp 
PVOllddSRL=0._dp 
PVOllddSLR=0._dp 
PVOllddVRR=0._dp 
PVOllddVLL=0._dp 
PVOllddVRL=0._dp 
PVOllddVLR=0._dp 
PVOllddTLL=0._dp 
PVOllddTLR=0._dp 
PVOllddTRL=0._dp 
PVOllddTRR=0._dp 
PVOllddSLL=oo16pi2*PVOllddSLL
PVOllddSRR=oo16pi2*PVOllddSRR
PVOllddSRL=oo16pi2*PVOllddSRL
PVOllddSLR=oo16pi2*PVOllddSLR
PVOllddVRR=oo16pi2*PVOllddVRR
PVOllddVLL=oo16pi2*PVOllddVLL
PVOllddVRL=oo16pi2*PVOllddVRL
PVOllddVLR=oo16pi2*PVOllddVLR
PVOllddTLL=oo16pi2*PVOllddTLL
PVOllddTLR=oo16pi2*PVOllddTLR
PVOllddTRL=oo16pi2*PVOllddTRL
PVOllddTRR=oo16pi2*PVOllddTRR
Iname=Iname-1

End Subroutine CalculatePengV2L2d 

Subroutine CalculateTreeS2L2d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& TSOllddSLL,TSOllddSRR,TSOllddSRL,TSOllddSLR,TSOllddVRR,TSOllddVLL,TSOllddVRL,          & 
& TSOllddVLR,TSOllddTLL,TSOllddTLR,TSOllddTRL,TSOllddTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS2L2d 
! 'PreSARAH' output has been generated  at 13:50 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSOllddSLL 
Complex(dp), Intent(out) :: TSOllddSRR 
Complex(dp), Intent(out) :: TSOllddSRL 
Complex(dp), Intent(out) :: TSOllddSLR 
Complex(dp), Intent(out) :: TSOllddVRR 
Complex(dp), Intent(out) :: TSOllddVLL 
Complex(dp), Intent(out) :: TSOllddVRL 
Complex(dp), Intent(out) :: TSOllddVLR 
Complex(dp), Intent(out) :: TSOllddTLL 
Complex(dp), Intent(out) :: TSOllddTLR 
Complex(dp), Intent(out) :: TSOllddTRL 
Complex(dp), Intent(out) :: TSOllddTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS2L2d' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
TSOllddSLL=0._dp 
TSOllddSRR=0._dp 
TSOllddSRL=0._dp 
TSOllddSLR=0._dp 
TSOllddVRR=0._dp 
TSOllddVLL=0._dp 
TSOllddVRL=0._dp 
TSOllddVLR=0._dp 
TSOllddTLL=0._dp 
TSOllddTLR=0._dp 
TSOllddTRL=0._dp 
TSOllddTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS2L2d 

Subroutine CalculateTreeV2L2d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& TVOllddSLL,TVOllddSRR,TVOllddSRL,TVOllddSLR,TVOllddVRR,TVOllddVLL,TVOllddVRL,          & 
& TVOllddVLR,TVOllddTLL,TVOllddTLR,TVOllddTRL,TVOllddTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV2L2d 
! 'PreSARAH' output has been generated  at 13:50 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVOllddSLL 
Complex(dp), Intent(out) :: TVOllddSRR 
Complex(dp), Intent(out) :: TVOllddSRL 
Complex(dp), Intent(out) :: TVOllddSLR 
Complex(dp), Intent(out) :: TVOllddVRR 
Complex(dp), Intent(out) :: TVOllddVLL 
Complex(dp), Intent(out) :: TVOllddVRL 
Complex(dp), Intent(out) :: TVOllddVLR 
Complex(dp), Intent(out) :: TVOllddTLL 
Complex(dp), Intent(out) :: TVOllddTLR 
Complex(dp), Intent(out) :: TVOllddTRL 
Complex(dp), Intent(out) :: TVOllddTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV2L2d' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
TVOllddSLL=0._dp 
TVOllddSRR=0._dp 
TVOllddSRL=0._dp 
TVOllddSLR=0._dp 
TVOllddVRR=0._dp 
TVOllddVLL=0._dp 
TVOllddVRL=0._dp 
TVOllddVLR=0._dp 
TVOllddTLL=0._dp 
TVOllddTLR=0._dp 
TVOllddTRL=0._dp 
TVOllddTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV2L2d 

Subroutine CalculateBox2L2u(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,MFu,MFu2,BOlluuSLL,       & 
& BOlluuSRR,BOlluuSRL,BOlluuSLR,BOlluuVRR,BOlluuVLL,BOlluuVRL,BOlluuVLR,BOlluuTLL,       & 
& BOlluuTLR,BOlluuTRL,BOlluuTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box2L2u 
! 'PreSARAH' output has been generated  at 12:49 on 13.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BOlluuSLL 
Complex(dp), Intent(out) :: BOlluuSRR 
Complex(dp), Intent(out) :: BOlluuSRL 
Complex(dp), Intent(out) :: BOlluuSLR 
Complex(dp), Intent(out) :: BOlluuVRR 
Complex(dp), Intent(out) :: BOlluuVLL 
Complex(dp), Intent(out) :: BOlluuVRL 
Complex(dp), Intent(out) :: BOlluuVLR 
Complex(dp), Intent(out) :: BOlluuTLL 
Complex(dp), Intent(out) :: BOlluuTLR 
Complex(dp), Intent(out) :: BOlluuTRL 
Complex(dp), Intent(out) :: BOlluuTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox2L2u' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFu(gt3)  
MassEx32=MFu2(gt3) 
MassEx4=MFu(gt4)  
MassEx42=MFu2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], UpQuark, bar[UpQuark]} 
 ! ------------------------------ 
 
BOlluuSLL=0._dp 
BOlluuSRR=0._dp 
BOlluuSRL=0._dp 
BOlluuSLR=0._dp 
BOlluuVRR=0._dp 
BOlluuVLL=0._dp 
BOlluuVRL=0._dp 
BOlluuVLR=0._dp 
BOlluuTLL=0._dp 
BOlluuTLR=0._dp 
BOlluuTRL=0._dp 
BOlluuTRR=0._dp 
BOlluuSLL=oo16pi2*BOlluuSLL 
BOlluuSRR=oo16pi2*BOlluuSRR 
BOlluuSRL=oo16pi2*BOlluuSRL 
BOlluuSLR=oo16pi2*BOlluuSLR 
BOlluuVRR=oo16pi2*BOlluuVRR 
BOlluuVLL=oo16pi2*BOlluuVLL 
BOlluuVRL=oo16pi2*BOlluuVRL 
BOlluuVLR=oo16pi2*BOlluuVLR 
BOlluuTLL=oo16pi2*BOlluuTLL 
BOlluuTLR=oo16pi2*BOlluuTLR 
BOlluuTRL=oo16pi2*BOlluuTRL 
BOlluuTRR=oo16pi2*BOlluuTRR 
Iname=Iname-1

End Subroutine CalculateBox2L2u 

Subroutine CalculatePengS2L2u(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,MFu,MFu2,               & 
& PSOlluuSLL,PSOlluuSRR,PSOlluuSRL,PSOlluuSLR,PSOlluuVRR,PSOlluuVLL,PSOlluuVRL,          & 
& PSOlluuVLR,PSOlluuTLL,PSOlluuTLR,PSOlluuTRL,PSOlluuTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS2L2u 
! 'PreSARAH' output has been generated  at 15:41 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSOlluuSLL 
Complex(dp), Intent(out) :: PSOlluuSRR 
Complex(dp), Intent(out) :: PSOlluuSRL 
Complex(dp), Intent(out) :: PSOlluuSLR 
Complex(dp), Intent(out) :: PSOlluuVRR 
Complex(dp), Intent(out) :: PSOlluuVLL 
Complex(dp), Intent(out) :: PSOlluuVRL 
Complex(dp), Intent(out) :: PSOlluuVLR 
Complex(dp), Intent(out) :: PSOlluuTLL 
Complex(dp), Intent(out) :: PSOlluuTLR 
Complex(dp), Intent(out) :: PSOlluuTRL 
Complex(dp), Intent(out) :: PSOlluuTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS2L2u' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFu(gt3)  
MassEx32=MFu2(gt3) 
MassEx4=MFu(gt4)  
MassEx42=MFu2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], UpQuark, bar[UpQuark]} 
 ! ------------------------------ 
 
PSOlluuSLL=0._dp 
PSOlluuSRR=0._dp 
PSOlluuSRL=0._dp 
PSOlluuSLR=0._dp 
PSOlluuVRR=0._dp 
PSOlluuVLL=0._dp 
PSOlluuVRL=0._dp 
PSOlluuVLR=0._dp 
PSOlluuTLL=0._dp 
PSOlluuTLR=0._dp 
PSOlluuTRL=0._dp 
PSOlluuTRR=0._dp 
PSOlluuSLL=oo16pi2*PSOlluuSLL 
PSOlluuSRR=oo16pi2*PSOlluuSRR 
PSOlluuSRL=oo16pi2*PSOlluuSRL 
PSOlluuSLR=oo16pi2*PSOlluuSLR 
PSOlluuVRR=oo16pi2*PSOlluuVRR 
PSOlluuVLL=oo16pi2*PSOlluuVLL 
PSOlluuVRL=oo16pi2*PSOlluuVRL 
PSOlluuVLR=oo16pi2*PSOlluuVLR 
PSOlluuTLL=oo16pi2*PSOlluuTLL 
PSOlluuTLR=oo16pi2*PSOlluuTLR 
PSOlluuTRL=oo16pi2*PSOlluuTRL 
PSOlluuTRR=oo16pi2*PSOlluuTRR 
Iname=Iname-1

End Subroutine CalculatePengS2L2u 

Subroutine CalculatePengV2L2u(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,MFu,MFu2,               & 
& PVOlluuSLL,PVOlluuSRR,PVOlluuSRL,PVOlluuSLR,PVOlluuVRR,PVOlluuVLL,PVOlluuVRL,          & 
& PVOlluuVLR,PVOlluuTLL,PVOlluuTLR,PVOlluuTRL,PVOlluuTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV2L2u 
! 'PreSARAH' output has been generated  at 15:46 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVOlluuSLL 
Complex(dp), Intent(out) :: PVOlluuSRR 
Complex(dp), Intent(out) :: PVOlluuSRL 
Complex(dp), Intent(out) :: PVOlluuSLR 
Complex(dp), Intent(out) :: PVOlluuVRR 
Complex(dp), Intent(out) :: PVOlluuVLL 
Complex(dp), Intent(out) :: PVOlluuVRL 
Complex(dp), Intent(out) :: PVOlluuVLR 
Complex(dp), Intent(out) :: PVOlluuTLL 
Complex(dp), Intent(out) :: PVOlluuTLR 
Complex(dp), Intent(out) :: PVOlluuTRL 
Complex(dp), Intent(out) :: PVOlluuTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV2L2u' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFu(gt3)  
MassEx32=MFu2(gt3) 
MassEx4=MFu(gt4)  
MassEx42=MFu2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], UpQuark, bar[UpQuark]} 
 ! ------------------------------ 
 
PVOlluuSLL=0._dp 
PVOlluuSRR=0._dp 
PVOlluuSRL=0._dp 
PVOlluuSLR=0._dp 
PVOlluuVRR=0._dp 
PVOlluuVLL=0._dp 
PVOlluuVRL=0._dp 
PVOlluuVLR=0._dp 
PVOlluuTLL=0._dp 
PVOlluuTLR=0._dp 
PVOlluuTRL=0._dp 
PVOlluuTRR=0._dp 
PVOlluuSLL=oo16pi2*PVOlluuSLL
PVOlluuSRR=oo16pi2*PVOlluuSRR
PVOlluuSRL=oo16pi2*PVOlluuSRL
PVOlluuSLR=oo16pi2*PVOlluuSLR
PVOlluuVRR=oo16pi2*PVOlluuVRR
PVOlluuVLL=oo16pi2*PVOlluuVLL
PVOlluuVRL=oo16pi2*PVOlluuVRL
PVOlluuVLR=oo16pi2*PVOlluuVLR
PVOlluuTLL=oo16pi2*PVOlluuTLL
PVOlluuTLR=oo16pi2*PVOlluuTLR
PVOlluuTRL=oo16pi2*PVOlluuTRL
PVOlluuTRR=oo16pi2*PVOlluuTRR
Iname=Iname-1

End Subroutine CalculatePengV2L2u 

Subroutine CalculateTreeS2L2u(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,MFu,MFu2,               & 
& TSOlluuSLL,TSOlluuSRR,TSOlluuSRL,TSOlluuSLR,TSOlluuVRR,TSOlluuVLL,TSOlluuVRL,          & 
& TSOlluuVLR,TSOlluuTLL,TSOlluuTLR,TSOlluuTRL,TSOlluuTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS2L2u 
! 'PreSARAH' output has been generated  at 15:46 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSOlluuSLL 
Complex(dp), Intent(out) :: TSOlluuSRR 
Complex(dp), Intent(out) :: TSOlluuSRL 
Complex(dp), Intent(out) :: TSOlluuSLR 
Complex(dp), Intent(out) :: TSOlluuVRR 
Complex(dp), Intent(out) :: TSOlluuVLL 
Complex(dp), Intent(out) :: TSOlluuVRL 
Complex(dp), Intent(out) :: TSOlluuVLR 
Complex(dp), Intent(out) :: TSOlluuTLL 
Complex(dp), Intent(out) :: TSOlluuTLR 
Complex(dp), Intent(out) :: TSOlluuTRL 
Complex(dp), Intent(out) :: TSOlluuTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS2L2u' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFu(gt3)  
MassEx32=MFu2(gt3) 
MassEx4=MFu(gt4)  
MassEx42=MFu2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], UpQuark, bar[UpQuark]} 
 ! ------------------------------ 
 
TSOlluuSLL=0._dp 
TSOlluuSRR=0._dp 
TSOlluuSRL=0._dp 
TSOlluuSLR=0._dp 
TSOlluuVRR=0._dp 
TSOlluuVLL=0._dp 
TSOlluuVRL=0._dp 
TSOlluuVLR=0._dp 
TSOlluuTLL=0._dp 
TSOlluuTLR=0._dp 
TSOlluuTRL=0._dp 
TSOlluuTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS2L2u 

Subroutine CalculateTreeV2L2u(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,MFu,MFu2,               & 
& TVOlluuSLL,TVOlluuSRR,TVOlluuSRL,TVOlluuSLR,TVOlluuVRR,TVOlluuVLL,TVOlluuVRL,          & 
& TVOlluuVLR,TVOlluuTLL,TVOlluuTLR,TVOlluuTRL,TVOlluuTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV2L2u 
! 'PreSARAH' output has been generated  at 15:46 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVOlluuSLL 
Complex(dp), Intent(out) :: TVOlluuSRR 
Complex(dp), Intent(out) :: TVOlluuSRL 
Complex(dp), Intent(out) :: TVOlluuSLR 
Complex(dp), Intent(out) :: TVOlluuVRR 
Complex(dp), Intent(out) :: TVOlluuVLL 
Complex(dp), Intent(out) :: TVOlluuVRL 
Complex(dp), Intent(out) :: TVOlluuVLR 
Complex(dp), Intent(out) :: TVOlluuTLL 
Complex(dp), Intent(out) :: TVOlluuTLR 
Complex(dp), Intent(out) :: TVOlluuTRL 
Complex(dp), Intent(out) :: TVOlluuTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV2L2u' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFu(gt3)  
MassEx32=MFu2(gt3) 
MassEx4=MFu(gt4)  
MassEx42=MFu2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], UpQuark, bar[UpQuark]} 
 ! ------------------------------ 
 
TVOlluuSLL=0._dp 
TVOlluuSRR=0._dp 
TVOlluuSRL=0._dp 
TVOlluuSLR=0._dp 
TVOlluuVRR=0._dp 
TVOlluuVLL=0._dp 
TVOlluuVRL=0._dp 
TVOlluuVLR=0._dp 
TVOlluuTLL=0._dp 
TVOlluuTLR=0._dp 
TVOlluuTRL=0._dp 
TVOlluuTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV2L2u 

Subroutine CalculateBox4L(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,BO4lSLL,BO4lSRR,            & 
& BO4lSRL,BO4lSLR,BO4lVRR,BO4lVLL,BO4lVRL,BO4lVLR,BO4lTLL,BO4lTLR,BO4lTRL,BO4lTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box4L 
! 'PreSARAH' output has been generated  at 13:18 on 13.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BO4lSLL 
Complex(dp), Intent(out) :: BO4lSRR 
Complex(dp), Intent(out) :: BO4lSRL 
Complex(dp), Intent(out) :: BO4lSLR 
Complex(dp), Intent(out) :: BO4lVRR 
Complex(dp), Intent(out) :: BO4lVLL 
Complex(dp), Intent(out) :: BO4lVRL 
Complex(dp), Intent(out) :: BO4lVLR 
Complex(dp), Intent(out) :: BO4lTLL 
Complex(dp), Intent(out) :: BO4lTLR 
Complex(dp), Intent(out) :: BO4lTRL 
Complex(dp), Intent(out) :: BO4lTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox4L' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
BO4lSLL=0._dp 
BO4lSRR=0._dp 
BO4lSRL=0._dp 
BO4lSLR=0._dp 
BO4lVRR=0._dp 
BO4lVLL=0._dp 
BO4lVRL=0._dp 
BO4lVLR=0._dp 
BO4lTLL=0._dp 
BO4lTLR=0._dp 
BO4lTRL=0._dp 
BO4lTRR=0._dp 
BO4lSLL=oo16pi2*BO4lSLL 
BO4lSRR=oo16pi2*BO4lSRR 
BO4lSRL=oo16pi2*BO4lSRL 
BO4lSLR=oo16pi2*BO4lSLR 
BO4lVRR=oo16pi2*BO4lVRR 
BO4lVLL=oo16pi2*BO4lVLL 
BO4lVRL=oo16pi2*BO4lVRL 
BO4lVLR=oo16pi2*BO4lVLR 
BO4lTLL=oo16pi2*BO4lTLL 
BO4lTLR=oo16pi2*BO4lTLR 
BO4lTRL=oo16pi2*BO4lTRL 
BO4lTRR=oo16pi2*BO4lTRR 
Iname=Iname-1

End Subroutine CalculateBox4L 

Subroutine CalculatePengS4L(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,PSO4lSLL,PSO4lSRR,        & 
& PSO4lSRL,PSO4lSLR,PSO4lVRR,PSO4lVLL,PSO4lVRL,PSO4lVLR,PSO4lTLL,PSO4lTLR,               & 
& PSO4lTRL,PSO4lTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS4L 
! 'PreSARAH' output has been generated  at 15:36 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSO4lSLL 
Complex(dp), Intent(out) :: PSO4lSRR 
Complex(dp), Intent(out) :: PSO4lSRL 
Complex(dp), Intent(out) :: PSO4lSLR 
Complex(dp), Intent(out) :: PSO4lVRR 
Complex(dp), Intent(out) :: PSO4lVLL 
Complex(dp), Intent(out) :: PSO4lVRL 
Complex(dp), Intent(out) :: PSO4lVLR 
Complex(dp), Intent(out) :: PSO4lTLL 
Complex(dp), Intent(out) :: PSO4lTLR 
Complex(dp), Intent(out) :: PSO4lTRL 
Complex(dp), Intent(out) :: PSO4lTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS4L' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PSO4lSLL=0._dp 
PSO4lSRR=0._dp 
PSO4lSRL=0._dp 
PSO4lSLR=0._dp 
PSO4lVRR=0._dp 
PSO4lVLL=0._dp 
PSO4lVRL=0._dp 
PSO4lVLR=0._dp 
PSO4lTLL=0._dp 
PSO4lTLR=0._dp 
PSO4lTRL=0._dp 
PSO4lTRR=0._dp 
PSO4lSLL=oo16pi2*PSO4lSLL 
PSO4lSRR=oo16pi2*PSO4lSRR 
PSO4lSRL=oo16pi2*PSO4lSRL 
PSO4lSLR=oo16pi2*PSO4lSLR 
PSO4lVRR=oo16pi2*PSO4lVRR 
PSO4lVLL=oo16pi2*PSO4lVLL 
PSO4lVRL=oo16pi2*PSO4lVRL 
PSO4lVLR=oo16pi2*PSO4lVLR 
PSO4lTLL=oo16pi2*PSO4lTLL 
PSO4lTLR=oo16pi2*PSO4lTLR 
PSO4lTRL=oo16pi2*PSO4lTRL 
PSO4lTRR=oo16pi2*PSO4lTRR 
Iname=Iname-1

End Subroutine CalculatePengS4L 

Subroutine CalculatePengV4L(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,PVO4lSLL,PVO4lSRR,        & 
& PVO4lSRL,PVO4lSLR,PVO4lVRR,PVO4lVLL,PVO4lVRL,PVO4lVLR,PVO4lTLL,PVO4lTLR,               & 
& PVO4lTRL,PVO4lTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV4L 
! 'PreSARAH' output has been generated  at 15:37 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVO4lSLL 
Complex(dp), Intent(out) :: PVO4lSRR 
Complex(dp), Intent(out) :: PVO4lSRL 
Complex(dp), Intent(out) :: PVO4lSLR 
Complex(dp), Intent(out) :: PVO4lVRR 
Complex(dp), Intent(out) :: PVO4lVLL 
Complex(dp), Intent(out) :: PVO4lVRL 
Complex(dp), Intent(out) :: PVO4lVLR 
Complex(dp), Intent(out) :: PVO4lTLL 
Complex(dp), Intent(out) :: PVO4lTLR 
Complex(dp), Intent(out) :: PVO4lTRL 
Complex(dp), Intent(out) :: PVO4lTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV4L' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PVO4lSLL=0._dp 
PVO4lSRR=0._dp 
PVO4lSRL=0._dp 
PVO4lSLR=0._dp 
PVO4lVRR=0._dp 
PVO4lVLL=0._dp 
PVO4lVRL=0._dp 
PVO4lVLR=0._dp 
PVO4lTLL=0._dp 
PVO4lTLR=0._dp 
PVO4lTRL=0._dp 
PVO4lTRR=0._dp 
PVO4lSLL=oo16pi2*PVO4lSLL
PVO4lSRR=oo16pi2*PVO4lSRR
PVO4lSRL=oo16pi2*PVO4lSRL
PVO4lSLR=oo16pi2*PVO4lSLR
PVO4lVRR=oo16pi2*PVO4lVRR
PVO4lVLL=oo16pi2*PVO4lVLL
PVO4lVRL=oo16pi2*PVO4lVRL
PVO4lVLR=oo16pi2*PVO4lVLR
PVO4lTLL=oo16pi2*PVO4lTLL
PVO4lTLR=oo16pi2*PVO4lTLR
PVO4lTRL=oo16pi2*PVO4lTRL
PVO4lTRR=oo16pi2*PVO4lTRR
Iname=Iname-1

End Subroutine CalculatePengV4L 

Subroutine CalculateTreeS4L(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,TSO4lSLL,TSO4lSRR,        & 
& TSO4lSRL,TSO4lSLR,TSO4lVRR,TSO4lVLL,TSO4lVRL,TSO4lVLR,TSO4lTLL,TSO4lTLR,               & 
& TSO4lTRL,TSO4lTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS4L 
! 'PreSARAH' output has been generated  at 15:37 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSO4lSLL 
Complex(dp), Intent(out) :: TSO4lSRR 
Complex(dp), Intent(out) :: TSO4lSRL 
Complex(dp), Intent(out) :: TSO4lSLR 
Complex(dp), Intent(out) :: TSO4lVRR 
Complex(dp), Intent(out) :: TSO4lVLL 
Complex(dp), Intent(out) :: TSO4lVRL 
Complex(dp), Intent(out) :: TSO4lVLR 
Complex(dp), Intent(out) :: TSO4lTLL 
Complex(dp), Intent(out) :: TSO4lTLR 
Complex(dp), Intent(out) :: TSO4lTRL 
Complex(dp), Intent(out) :: TSO4lTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS4L' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TSO4lSLL=0._dp 
TSO4lSRR=0._dp 
TSO4lSRL=0._dp 
TSO4lSLR=0._dp 
TSO4lVRR=0._dp 
TSO4lVLL=0._dp 
TSO4lVRL=0._dp 
TSO4lVLR=0._dp 
TSO4lTLL=0._dp 
TSO4lTLR=0._dp 
TSO4lTRL=0._dp 
TSO4lTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS4L 

Subroutine CalculateTreeV4L(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,TVO4lSLL,TVO4lSRR,        & 
& TVO4lSRL,TVO4lSLR,TVO4lVRR,TVO4lVLL,TVO4lVRL,TVO4lVLR,TVO4lTLL,TVO4lTLR,               & 
& TVO4lTRL,TVO4lTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV4L 
! 'PreSARAH' output has been generated  at 15:37 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVO4lSLL 
Complex(dp), Intent(out) :: TVO4lSRR 
Complex(dp), Intent(out) :: TVO4lSRL 
Complex(dp), Intent(out) :: TVO4lSLR 
Complex(dp), Intent(out) :: TVO4lVRR 
Complex(dp), Intent(out) :: TVO4lVLL 
Complex(dp), Intent(out) :: TVO4lVRL 
Complex(dp), Intent(out) :: TVO4lVLR 
Complex(dp), Intent(out) :: TVO4lTLL 
Complex(dp), Intent(out) :: TVO4lTLR 
Complex(dp), Intent(out) :: TVO4lTRL 
Complex(dp), Intent(out) :: TVO4lTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV4L' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TVO4lSLL=0._dp 
TVO4lSRR=0._dp 
TVO4lSRL=0._dp 
TVO4lSLR=0._dp 
TVO4lVRR=0._dp 
TVO4lVLL=0._dp 
TVO4lVRL=0._dp 
TVO4lVLR=0._dp 
TVO4lTLL=0._dp 
TVO4lTLR=0._dp 
TVO4lTRL=0._dp 
TVO4lTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV4L 

Subroutine CalculateBox4Lcross(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,BO4lSLLcross,          & 
& BO4lSRRcross,BO4lSRLcross,BO4lSLRcross,BO4lVRRcross,BO4lVLLcross,BO4lVRLcross,         & 
& BO4lVLRcross,BO4lTLLcross,BO4lTLRcross,BO4lTRLcross,BO4lTRRcross)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box4Lcross 
! 'PreSARAH' output has been generated  at 13:21 on 13.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BO4lSLLcross 
Complex(dp), Intent(out) :: BO4lSRRcross 
Complex(dp), Intent(out) :: BO4lSRLcross 
Complex(dp), Intent(out) :: BO4lSLRcross 
Complex(dp), Intent(out) :: BO4lVRRcross 
Complex(dp), Intent(out) :: BO4lVLLcross 
Complex(dp), Intent(out) :: BO4lVRLcross 
Complex(dp), Intent(out) :: BO4lVLRcross 
Complex(dp), Intent(out) :: BO4lTLLcross 
Complex(dp), Intent(out) :: BO4lTLRcross 
Complex(dp), Intent(out) :: BO4lTRLcross 
Complex(dp), Intent(out) :: BO4lTRRcross 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox4Lcross' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
BO4lSLLcross=0._dp 
BO4lSRRcross=0._dp 
BO4lSRLcross=0._dp 
BO4lSLRcross=0._dp 
BO4lVRRcross=0._dp 
BO4lVLLcross=0._dp 
BO4lVRLcross=0._dp 
BO4lVLRcross=0._dp 
BO4lTLLcross=0._dp 
BO4lTLRcross=0._dp 
BO4lTRLcross=0._dp 
BO4lTRRcross=0._dp 
BO4lSLLcross=oo16pi2*BO4lSLLcross 
BO4lSRRcross=oo16pi2*BO4lSRRcross 
BO4lSRLcross=oo16pi2*BO4lSRLcross 
BO4lSLRcross=oo16pi2*BO4lSLRcross 
BO4lVRRcross=oo16pi2*BO4lVRRcross 
BO4lVLLcross=oo16pi2*BO4lVLLcross 
BO4lVRLcross=oo16pi2*BO4lVRLcross 
BO4lVLRcross=oo16pi2*BO4lVLRcross 
BO4lTLLcross=oo16pi2*BO4lTLLcross 
BO4lTLRcross=oo16pi2*BO4lTLRcross 
BO4lTRLcross=oo16pi2*BO4lTRLcross 
BO4lTRRcross=oo16pi2*BO4lTRRcross 
Iname=Iname-1

End Subroutine CalculateBox4Lcross 

Subroutine CalculatePengS4Lcross(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,PSO4lSLLcross,       & 
& PSO4lSRRcross,PSO4lSRLcross,PSO4lSLRcross,PSO4lVRRcross,PSO4lVLLcross,PSO4lVRLcross,   & 
& PSO4lVLRcross,PSO4lTLLcross,PSO4lTLRcross,PSO4lTRLcross,PSO4lTRRcross)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS4Lcross 
! 'PreSARAH' output has been generated  at 15:52 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSO4lSLLcross 
Complex(dp), Intent(out) :: PSO4lSRRcross 
Complex(dp), Intent(out) :: PSO4lSRLcross 
Complex(dp), Intent(out) :: PSO4lSLRcross 
Complex(dp), Intent(out) :: PSO4lVRRcross 
Complex(dp), Intent(out) :: PSO4lVLLcross 
Complex(dp), Intent(out) :: PSO4lVRLcross 
Complex(dp), Intent(out) :: PSO4lVLRcross 
Complex(dp), Intent(out) :: PSO4lTLLcross 
Complex(dp), Intent(out) :: PSO4lTLRcross 
Complex(dp), Intent(out) :: PSO4lTRLcross 
Complex(dp), Intent(out) :: PSO4lTRRcross 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS4Lcross' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PSO4lSLLcross=0._dp 
PSO4lSRRcross=0._dp 
PSO4lSRLcross=0._dp 
PSO4lSLRcross=0._dp 
PSO4lVRRcross=0._dp 
PSO4lVLLcross=0._dp 
PSO4lVRLcross=0._dp 
PSO4lVLRcross=0._dp 
PSO4lTLLcross=0._dp 
PSO4lTLRcross=0._dp 
PSO4lTRLcross=0._dp 
PSO4lTRRcross=0._dp 
PSO4lSLLcross=oo16pi2*PSO4lSLLcross 
PSO4lSRRcross=oo16pi2*PSO4lSRRcross 
PSO4lSRLcross=oo16pi2*PSO4lSRLcross 
PSO4lSLRcross=oo16pi2*PSO4lSLRcross 
PSO4lVRRcross=oo16pi2*PSO4lVRRcross 
PSO4lVLLcross=oo16pi2*PSO4lVLLcross 
PSO4lVRLcross=oo16pi2*PSO4lVRLcross 
PSO4lVLRcross=oo16pi2*PSO4lVLRcross 
PSO4lTLLcross=oo16pi2*PSO4lTLLcross 
PSO4lTLRcross=oo16pi2*PSO4lTLRcross 
PSO4lTRLcross=oo16pi2*PSO4lTRLcross 
PSO4lTRRcross=oo16pi2*PSO4lTRRcross 
Iname=Iname-1

End Subroutine CalculatePengS4Lcross 

Subroutine CalculatePengV4Lcross(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,PVO4lSLLcross,       & 
& PVO4lSRRcross,PVO4lSRLcross,PVO4lSLRcross,PVO4lVRRcross,PVO4lVLLcross,PVO4lVRLcross,   & 
& PVO4lVLRcross,PVO4lTLLcross,PVO4lTLRcross,PVO4lTRLcross,PVO4lTRRcross)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV4Lcross 
! 'PreSARAH' output has been generated  at 15:56 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVO4lSLLcross 
Complex(dp), Intent(out) :: PVO4lSRRcross 
Complex(dp), Intent(out) :: PVO4lSRLcross 
Complex(dp), Intent(out) :: PVO4lSLRcross 
Complex(dp), Intent(out) :: PVO4lVRRcross 
Complex(dp), Intent(out) :: PVO4lVLLcross 
Complex(dp), Intent(out) :: PVO4lVRLcross 
Complex(dp), Intent(out) :: PVO4lVLRcross 
Complex(dp), Intent(out) :: PVO4lTLLcross 
Complex(dp), Intent(out) :: PVO4lTLRcross 
Complex(dp), Intent(out) :: PVO4lTRLcross 
Complex(dp), Intent(out) :: PVO4lTRRcross 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV4Lcross' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PVO4lSLLcross=0._dp 
PVO4lSRRcross=0._dp 
PVO4lSRLcross=0._dp 
PVO4lSLRcross=0._dp 
PVO4lVRRcross=0._dp 
PVO4lVLLcross=0._dp 
PVO4lVRLcross=0._dp 
PVO4lVLRcross=0._dp 
PVO4lTLLcross=0._dp 
PVO4lTLRcross=0._dp 
PVO4lTRLcross=0._dp 
PVO4lTRRcross=0._dp 
PVO4lSLLcross=oo16pi2*PVO4lSLLcross
PVO4lSRRcross=oo16pi2*PVO4lSRRcross
PVO4lSRLcross=oo16pi2*PVO4lSRLcross
PVO4lSLRcross=oo16pi2*PVO4lSLRcross
PVO4lVRRcross=oo16pi2*PVO4lVRRcross
PVO4lVLLcross=oo16pi2*PVO4lVLLcross
PVO4lVRLcross=oo16pi2*PVO4lVRLcross
PVO4lVLRcross=oo16pi2*PVO4lVLRcross
PVO4lTLLcross=oo16pi2*PVO4lTLLcross
PVO4lTLRcross=oo16pi2*PVO4lTLRcross
PVO4lTRLcross=oo16pi2*PVO4lTRLcross
PVO4lTRRcross=oo16pi2*PVO4lTRRcross
Iname=Iname-1

End Subroutine CalculatePengV4Lcross 

Subroutine CalculateTreeS4Lcross(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,TSO4lSLLcross,       & 
& TSO4lSRRcross,TSO4lSRLcross,TSO4lSLRcross,TSO4lVRRcross,TSO4lVLLcross,TSO4lVRLcross,   & 
& TSO4lVLRcross,TSO4lTLLcross,TSO4lTLRcross,TSO4lTRLcross,TSO4lTRRcross)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS4Lcross 
! 'PreSARAH' output has been generated  at 15:56 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSO4lSLLcross 
Complex(dp), Intent(out) :: TSO4lSRRcross 
Complex(dp), Intent(out) :: TSO4lSRLcross 
Complex(dp), Intent(out) :: TSO4lSLRcross 
Complex(dp), Intent(out) :: TSO4lVRRcross 
Complex(dp), Intent(out) :: TSO4lVLLcross 
Complex(dp), Intent(out) :: TSO4lVRLcross 
Complex(dp), Intent(out) :: TSO4lVLRcross 
Complex(dp), Intent(out) :: TSO4lTLLcross 
Complex(dp), Intent(out) :: TSO4lTLRcross 
Complex(dp), Intent(out) :: TSO4lTRLcross 
Complex(dp), Intent(out) :: TSO4lTRRcross 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS4Lcross' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TSO4lSLLcross=0._dp 
TSO4lSRRcross=0._dp 
TSO4lSRLcross=0._dp 
TSO4lSLRcross=0._dp 
TSO4lVRRcross=0._dp 
TSO4lVLLcross=0._dp 
TSO4lVRLcross=0._dp 
TSO4lVLRcross=0._dp 
TSO4lTLLcross=0._dp 
TSO4lTLRcross=0._dp 
TSO4lTRLcross=0._dp 
TSO4lTRRcross=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS4Lcross 

Subroutine CalculateTreeV4Lcross(gt1,gt2,gt3,gt4,OnlySM,MFe,MFe2,TVO4lSLLcross,       & 
& TVO4lSRRcross,TVO4lSRLcross,TVO4lSLRcross,TVO4lVRRcross,TVO4lVLLcross,TVO4lVRLcross,   & 
& TVO4lVLRcross,TVO4lTLLcross,TVO4lTLRcross,TVO4lTRLcross,TVO4lTRRcross)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV4Lcross 
! 'PreSARAH' output has been generated  at 15:56 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVO4lSLLcross 
Complex(dp), Intent(out) :: TVO4lSRRcross 
Complex(dp), Intent(out) :: TVO4lSRLcross 
Complex(dp), Intent(out) :: TVO4lSLRcross 
Complex(dp), Intent(out) :: TVO4lVRRcross 
Complex(dp), Intent(out) :: TVO4lVLLcross 
Complex(dp), Intent(out) :: TVO4lVRLcross 
Complex(dp), Intent(out) :: TVO4lVLRcross 
Complex(dp), Intent(out) :: TVO4lTLLcross 
Complex(dp), Intent(out) :: TVO4lTLRcross 
Complex(dp), Intent(out) :: TVO4lTRLcross 
Complex(dp), Intent(out) :: TVO4lTRRcross 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV4Lcross' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TVO4lSLLcross=0._dp 
TVO4lSRRcross=0._dp 
TVO4lSRLcross=0._dp 
TVO4lSLRcross=0._dp 
TVO4lVRRcross=0._dp 
TVO4lVLLcross=0._dp 
TVO4lVRLcross=0._dp 
TVO4lVLRcross=0._dp 
TVO4lTLLcross=0._dp 
TVO4lTLRcross=0._dp 
TVO4lTRLcross=0._dp 
TVO4lTRRcross=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV4Lcross 

Subroutine CalculateGamma2l(gt1,gt2,gt3,OnlySM,MFe,MFe2,Join(List(),Part(1,1))        & 
& ,OA2lSL,OA2lSR,OA1L,OA1R)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Gamma2l 
! 'PreSARAH' output has been generated  at 15:56 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OA2lSL 
Complex(dp), Intent(out) :: OA2lSR 
Complex(dp), Intent(out) :: OA1L 
Complex(dp), Intent(out) :: OA1R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateGamma2l' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {bar[ChargedLepton], ChargedLepton, Photon} 
 ! ------------------------------ 
 
OA2lSL=0._dp 
OA2lSR=0._dp 
OA1L=0._dp 
OA1R=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1L = Conjg(1)
coup1R = Conjg(1)
! Amplitude 
  OA2lSL=OA2lSL+ 0.
  OA2lSR=OA2lSR+ 0.
  OA1L=OA1L+ 0.
  OA1R=OA1R+ 0.
 End if 


 OA2lSL=oo16pi2*OA2lSL 
OA2lSR=oo16pi2*OA2lSR 
OA1L=oo16pi2*OA1L 
OA1R=oo16pi2*OA1R 
Iname=Iname-1

End Subroutine CalculateGamma2l 

Subroutine CalculateH2l(gt1,gt2,gt3,OnlySM,MFe,MFe2,Mhh,Mhh2,Join(List()              & 
& ,Part(1,1)),OH2lSL,OH2lSR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process H2l 
! 'PreSARAH' output has been generated  at 10:48 on 14.1.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),Mhh,Mhh2

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OH2lSL 
Complex(dp), Intent(out) :: OH2lSR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateH2l' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=Mhh  
MassEx32=Mhh2 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], HiggsBoson} 
 ! ------------------------------ 
 
OH2lSL=0._dp 
OH2lSR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1R = Conjg(1)
coup1L = Conjg(1)
! Amplitude 
  OH2lSL=OH2lSL-157.91367041742973*coup1L
  OH2lSR=OH2lSR-157.91367041742973*coup1R
 End if 


 OH2lSL=oo16pi2*OH2lSL 
OH2lSR=oo16pi2*OH2lSR 
Iname=Iname-1

End Subroutine CalculateH2l 

Subroutine CalculateLeptonEDMgminus2(gt1,gt2,gt3,OnlySM,MFe,MFe2,Join(List()          & 
& ,Part(1,1)),DP2lSL,DP2lSR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process LeptonEDMgminus2 
! 'PreSARAH' output has been generated  at 15:58 on 6.5.2021 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3)

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: DP2lSL 
Complex(dp), Intent(out) :: DP2lSR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateLeptonEDMgminus2' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {bar[ChargedLepton], ChargedLepton, Photon} 
 ! ------------------------------ 
 
DP2lSL=0._dp 
DP2lSR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1L = Conjg(1)
coup1R = Conjg(1)
! Amplitude 
  DP2lSL=DP2lSL+ 0.
  DP2lSR=DP2lSR+ 0.
 End if 


 DP2lSL=oo16pi2*DP2lSL 
DP2lSR=oo16pi2*DP2lSR 
Iname=Iname-1

End Subroutine CalculateLeptonEDMgminus2 

Subroutine CalculateZ2l(gt1,gt2,gt3,OnlySM,MFe,MFe2,MVZ,MVZ2,Join(List()              & 
& ,Part(1,1)),OZ2lSL,OZ2lSR,OZ2lVL,OZ2lVR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Z2l 
! 'PreSARAH' output has been generated  at 10:49 on 14.1.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFe(3),MFe2(3),MVZ,MVZ2

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OZ2lSL 
Complex(dp), Intent(out) :: OZ2lSR 
Complex(dp), Intent(out) :: OZ2lVL 
Complex(dp), Intent(out) :: OZ2lVR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateZ2l' 

Finite=1._dp 
MassEx1=MFe(gt1)  
MassEx12=MFe2(gt1) 
MassEx2=MFe(gt2)  
MassEx22=MFe2(gt2) 
MassEx3=MVZ  
MassEx32=MVZ2 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {ChargedLepton, bar[ChargedLepton], Zboson} 
 ! ------------------------------ 
 
OZ2lSL=0._dp 
OZ2lSR=0._dp 
OZ2lVL=0._dp 
OZ2lVR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1L = Conjg(1)
coup1R = Conjg(1)
! Amplitude 
  OZ2lSL=OZ2lSL+ 0.
  OZ2lSR=OZ2lSR+ 0.
  OZ2lVL=OZ2lVL+ 157.91367041742973*coup1L
  OZ2lVR=OZ2lVR+ 157.91367041742973*coup1R
 End if 


 OZ2lSL=oo16pi2*OZ2lSL 
OZ2lSR=oo16pi2*OZ2lSR 
OZ2lVL=oo16pi2*OZ2lVL 
OZ2lVR=oo16pi2*OZ2lVR 
Iname=Iname-1

End Subroutine CalculateZ2l 

Real(dp) Function C00g(m1, m2, m3)
Implicit None
Real(dp), Intent(in) :: m1, m2, m3
Real(dp) :: eps=1E-10_dp, large = 1E+5_dp

C00g = C00_3m(m1,m2,m3)

End Function C00g

Real(dp) Function C0g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C0

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C0g=-1/(2._dp*m1) + (-1 + r)/(6._dp*m1) - (-1 + r)**2/(12._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C0g=-(1/m1)
     Else 
        C0g=(-1 + r - r*Log(r))/(m1*(-1 + r)**2)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C0g=-1/(2._dp*m2) + (-1 + r)/(3._dp*m2) - (-1 + r)**2/(4._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C0g=1._dp
     Else 
        C0g=(1 - r + Log(r))/(m2*(-1 + r)**2)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C0g=-1/(2._dp*m1) + (-1 + r)/(3._dp*m1) - (-1 + r)**2/(4._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C0g=1._dp
     Else 
        C0g=(1 - r + Log(r))/(m1*(-1 + r)**2)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C0g=-1/(2._dp*m2) + (-1 + r)/(6._dp*m2) - (-1 + r)**2/(12._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C0g=-(1/m2)
     Else 
        C0g=(-1 + r - r*Log(r))/(m2*(-1 + r)**2)
     End if 
  End if 

Else!! Different masses are not possible! 
   C0g =0._dp 
End if 
 
End Function C0g 


Real(dp) Function C1g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C1

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C1g=1/(6._dp*m1) - (-1 + r)/(24._dp*m1) + (-1 + r)**2/(60._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1g=1/(4._dp*m1)
     Else 
        C1g=(-1 + (4 - 3*r)*r + 2*r**2*Log(r))/(4._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1g=1/(6._dp*m2) - (-1 + r)/(8._dp*m2) + (-1 + r)**2/(10._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1g=large
     Else 
        C1g=(3 - 4*r + r**2 + 2*Log(r))/(4._dp*m2*(-1 + r)**3)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C1g=1/(6._dp*m1) - (-1 + r)/(8._dp*m1) + (-1 + r)**2/(10._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1g=large
     Else 
        C1g=(3 - 4*r + r**2 + 2*Log(r))/(4._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1g=1/(6._dp*m2) - (-1 + r)/(24._dp*m2) + (-1 + r)**2/(60._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1g=1/(4._dp*m2)
     Else 
        C1g=(-1 + (4 - 3*r)*r + 2*r**2*Log(r))/(4._dp*m2*(-1 + r)**3)
     End if 
  End if 

Else!! Different masses are not possible! 
   C1g =0._dp 
End if 
 
End Function C1g 


Real(dp) Function C2g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C2

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C2g=1/(6._dp*m1) - (-1 + r)/(12._dp*m1) + (-1 + r)**2/(20._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2g=1/(2._dp*m1)
     Else 
        C2g=(-1 + r**2 - 2*r*Log(r))/(2._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2g=1/(6._dp*m2) - (-1 + r)/(12._dp*m2) + (-1 + r)**2/(20._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2g=1/(2._dp*m2)
     Else 
        C2g=(-1 + r**2 - 2*r*Log(r))/(2._dp*m2*(-1 + r)**3)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C2g=1/(6._dp*m1) - (-1 + r)/(8._dp*m1) + (-1 + r)**2/(10._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2g=large
     Else 
        C2g=(3 - 4*r + r**2 + 2*Log(r))/(4._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2g=1/(6._dp*m2) - (-1 + r)/(24._dp*m2) + (-1 + r)**2/(60._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2g=1/(4._dp*m2)
     Else 
        C2g=(-1 + (4 - 3*r)*r + 2*r**2*Log(r))/(4._dp*m2*(-1 + r)**3)
     End if 
  End if 

Else!! Different masses are not possible! 
   C2g =0._dp 
End if 
 
End Function C2g 


Real(dp) Function C11g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C11

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C11g=-1/(12._dp*m1) + (-1 + r)/(60._dp*m1) - (-1 + r)**2/(180._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C11g=-1/(9._dp*m1)
     Else 
        C11g=((-1 + r)*(2 + r*(-7 + 11*r)) - 6*r**3*Log(r))/(18._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C11g=-1/(12._dp*m2) + (-1 + r)/(15._dp*m2) - (-1 + r)**2/(18._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C11g=large
     Else 
        C11g=(-((-1 + r)*(11 + r*(-7 + 2*r))) + 6*Log(r))/(18._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C11g=-1/(12._dp*m1) + (-1 + r)/(15._dp*m1) - (-1 + r)**2/(18._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C11g=large
     Else 
        C11g=(-((-1 + r)*(11 + r*(-7 + 2*r))) + 6*Log(r))/(18._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C11g=-1/(12._dp*m2) + (-1 + r)/(60._dp*m2) - (-1 + r)**2/(180._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C11g=-1/(9._dp*m2)
     Else 
        C11g=((-1 + r)*(2 + r*(-7 + 11*r)) - 6*r**3*Log(r))/(18._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C11g =0._dp 
End if 
 
End Function C11g 


Real(dp) Function C12g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C12

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C12g=-1/(24._dp*m1) + (-1 + r)/(60._dp*m1) - (-1 + r)**2/(120._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12g=-1/(12._dp*m1)
     Else 
        C12g=(-((-1 + r)*(-1 + r*(5 + 2*r))) + 6*r**2*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12g=-1/(24._dp*m2) + (-1 + r)/(40._dp*m2) - (-1 + r)**2/(60._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12g=-1/(6._dp*m2)
     Else 
        C12g=-(2 + r*(3 + (-6 + r)*r) + 6*r*Log(r))/(12._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C12g=-1/(24._dp*m1) + (-1 + r)/(30._dp*m1) - (-1 + r)**2/(36._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12g=large
     Else 
        C12g=(-((-1 + r)*(11 + r*(-7 + 2*r))) + 6*Log(r))/(36._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12g=-1/(24._dp*m2) + (-1 + r)/(120._dp*m2) - (-1 + r)**2/(360._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12g=-1/(18._dp*m2)
     Else 
        C12g=((-1 + r)*(2 + r*(-7 + 11*r)) - 6*r**3*Log(r))/(36._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C12g =0._dp 
End if 
 
End Function C12g 


Real(dp) Function C22g(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C22

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C22g=-1/(12._dp*m1) + (-1 + r)/(20._dp*m1) - (-1 + r)**2/(30._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C22g=-1/(3._dp*m1)
     Else 
        C22g=-(2 + r*(3 + (-6 + r)*r) + 6*r*Log(r))/(6._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C22g=-1/(12._dp*m2) + (-1 + r)/(30._dp*m2) - (-1 + r)**2/(60._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C22g=-1/(6._dp*m2)
     Else 
        C22g=(-((-1 + r)*(-1 + r*(5 + 2*r))) + 6*r**2*Log(r))/(6._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C22g=-1/(12._dp*m1) + (-1 + r)/(15._dp*m1) - (-1 + r)**2/(18._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C22g=large
     Else 
        C22g=(-((-1 + r)*(11 + r*(-7 + 2*r))) + 6*Log(r))/(18._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C22g=-1/(12._dp*m2) + (-1 + r)/(60._dp*m2) - (-1 + r)**2/(180._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C22g=-1/(9._dp*m2)
     Else 
        C22g=((-1 + r)*(2 + r*(-7 + 11*r)) - 6*r**3*Log(r))/(18._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C22g =0._dp 
End if 
 
End Function C22g 


Real(dp) Function C2C12C22(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C12 + C2 + C22

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C2C12C22=1/(24._dp*m1) - (-1 + r)/(60._dp*m1) + (-1 + r)**2/(120._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2C12C22=1/(12._dp*m1)
     Else 
        C2C12C22=((-1 + r)*(-1 + r*(5 + 2*r)) - 6*r**2*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2C12C22=1/(24._dp*m2) - (-1 + r)/(40._dp*m2) + (-1 + r)**2/(60._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2C12C22=1/(6._dp*m2)
     Else 
        C2C12C22=(2 + r*(3 + (-6 + r)*r) + 6*r*Log(r))/(12._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C2C12C22=1/(24._dp*m1) - (-1 + r)/(40._dp*m1) + (-1 + r)**2/(60._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2C12C22=1/(6._dp*m1)
     Else 
        C2C12C22=(2 + r*(3 + (-6 + r)*r) + 6*r*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2C12C22=1/(24._dp*m2) - (-1 + r)/(60._dp*m2) + (-1 + r)**2/(120._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2C12C22=1/(12._dp*m2)
     Else 
        C2C12C22=((-1 + r)*(-1 + r*(5 + 2*r)) - 6*r**2*Log(r))/(12._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C2C12C22 =0._dp 
End if 
 
End Function C2C12C22 


Real(dp) Function C1C12C11(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C1 + C11 + C12

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C1C12C11=1/(24._dp*m1) - (-1 + r)/(120._dp*m1) + (-1 + r)**2/(360._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1C12C11=1/(18._dp*m1)
     Else 
        C1C12C11=(-((-1 + r)*(2 + r*(-7 + 11*r))) + 6*r**3*Log(r))/(36._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1C12C11=1/(24._dp*m2) - (-1 + r)/(30._dp*m2) + (-1 + r)**2/(36._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1C12C11=large
     Else 
        C1C12C11=((-1 + r)*(11 + r*(-7 + 2*r)) - 6*Log(r))/(36._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C1C12C11=1/(24._dp*m1) - (-1 + r)/(40._dp*m1) + (-1 + r)**2/(60._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1C12C11=1/(6._dp*m1)
     Else 
        C1C12C11=(2 + r*(3 + (-6 + r)*r) + 6*r*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1C12C11=1/(24._dp*m2) - (-1 + r)/(60._dp*m2) + (-1 + r)**2/(120._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1C12C11=1/(12._dp*m2)
     Else 
        C1C12C11=((-1 + r)*(-1 + r*(5 + 2*r)) - 6*r**2*Log(r))/(12._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C1C12C11 =0._dp 
End if 
 
End Function C1C12C11 


Real(dp) Function C0C1C2(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C0 + C1 + C2

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C0C1C2=-1/(6._dp*m1) + (-1 + r)/(24._dp*m1) - (-1 + r)**2/(60._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C0C1C2=-1/(4._dp*m1)
     Else 
        C0C1C2=(1 - 4*r + 3*r**2 - 2*r**2*Log(r))/(4._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C0C1C2=-1/(6._dp*m2) + (-1 + r)/(8._dp*m2) - (-1 + r)**2/(10._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C0C1C2=large
     Else 
        C0C1C2=-(3 - 4*r + r**2 + 2*Log(r))/(4._dp*m2*(-1 + r)**3)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C0C1C2=-1/(6._dp*m1) + (-1 + r)/(12._dp*m1) - (-1 + r)**2/(20._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C0C1C2=-1/(2._dp*m1)
     Else 
        C0C1C2=(1 - r**2 + 2*r*Log(r))/(2._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C0C1C2=-1/(6._dp*m2) + (-1 + r)/(12._dp*m2) - (-1 + r)**2/(20._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C0C1C2=-1/(2._dp*m2)
     Else 
        C0C1C2=(1 - r**2 + 2*r*Log(r))/(2._dp*m2*(-1 + r)**3)
     End if 
  End if 

Else!! Different masses are not possible! 
   C0C1C2 =0._dp 
End if 
 
End Function C0C1C2 


Real(dp) Function C12C11C2(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  2 C11 + 2 C12 - C2

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C12C11C2=-5/(12._dp*m1) + (3*(-1 + r))/(20._dp*m1) - (7*(-1 + r)**2)/(90._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C11C2=-8/(9._dp*m1)
     Else 
        C12C11C2=((-1 + r)*(16 + r*(-29 + 7*r)) - 6*r*(3 + 2*(-3 + r)*r)*Log(r))/(18._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C11C2=-5/(12._dp*m2) + (4*(-1 + r))/(15._dp*m2) - (7*(-1 + r)**2)/(36._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C11C2=large
     Else 
        C12C11C2=(-((-1 + r)*(7 + r*(-29 + 16*r))) + 6*(2 + 3*(-2 + r)*r)*Log(r))/(18._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C12C11C2=-5/(12._dp*m1) + (13*(-1 + r))/(40._dp*m1) - (4*(-1 + r)**2)/(15._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C11C2=large
     Else 
        C12C11C2=-((-1 + r)*(31 + r*(-26 + 7*r)) + 6*(-3 + r)*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C11C2=-5/(12._dp*m2) + (11*(-1 + r))/(120._dp*m2) - (-1 + r)**2/(30._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C11C2=-7/(12._dp*m2)
     Else 
        C12C11C2=((-1 + r)*(7 + r*(-26 + 31*r)) + 6*(1 - 3*r)*r**2*Log(r))/(12._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C12C11C2 =0._dp 
End if 
 
End Function C12C11C2 


Real(dp) Function C12C22C1(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  -C1 + 2 C12 + 2 C22

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C12C22C1=-5/(12._dp*m1) + (7*(-1 + r))/(40._dp*m1) - (-1 + r)**2/(10._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C22C1=-13/(12._dp*m1)
     Else 
        C12C22C1=((-1 + r)*(13 + (-2 + r)*r) - 6*r*(4 + (-3 + r)*r)*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C22C1=-5/(12._dp*m2) + (29*(-1 + r))/(120._dp*m2) - (-1 + r)**2/(6._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C22C1=large
     Else 
        C12C22C1=(-((-1 + r)*(1 + r*(-2 + 13*r))) + 6*(1 + r*(-3 + 4*r))*Log(r))/(12._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C12C22C1=-5/(12._dp*m1) + (13*(-1 + r))/(40._dp*m1) - (4*(-1 + r)**2)/(15._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C22C1=large
     Else 
        C12C22C1=-((-1 + r)*(31 + r*(-26 + 7*r)) + 6*(-3 + r)*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C22C1=-5/(12._dp*m2) + (11*(-1 + r))/(120._dp*m2) - (-1 + r)**2/(30._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C22C1=-7/(12._dp*m2)
     Else 
        C12C22C1=((-1 + r)*(7 + r*(-26 + 31*r)) + 6*(1 - 3*r)*r**2*Log(r))/(12._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C12C22C1 =0._dp 
End if 
 
End Function C12C22C1 


Real(dp) Function C12C22(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C12 + C22

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C12C22=-1/(8._dp*m1) + (-1 + r)/(15._dp*m1) - (-1 + r)**2/(24._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C22=-5/(12._dp*m1)
     Else 
        C12C22=(-5 + (9 - 4*r)*r**2 + 6*(-2 + r)*r*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C22=-1/(8._dp*m2) + (7*(-1 + r))/(120._dp*m2) - (-1 + r)**2/(30._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C22=-1/(3._dp*m2)
     Else 
        C12C22=(-4 + 9*r - 5*r**3 + 6*r*(-1 + 2*r)*Log(r))/(12._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C12C22=-1/(8._dp*m1) + (-1 + r)/(10._dp*m1) - (-1 + r)**2/(12._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C12C22=large
     Else 
        C12C22=(-((-1 + r)*(11 + r*(-7 + 2*r))) + 6*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C12C22=-1/(8._dp*m2) + (-1 + r)/(40._dp*m2) - (-1 + r)**2/(120._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C12C22=-1/(6._dp*m2)
     Else 
        C12C22=((-1 + r)*(2 + r*(-7 + 11*r)) - 6*r**3*Log(r))/(12._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C12C22 =0._dp 
End if 
 
End Function C12C22 


Real(dp) Function C2C12(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C12 + C2

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C2C12=1/(8._dp*m1) - (-1 + r)/(15._dp*m1) + (-1 + r)**2/(24._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2C12=5/(12._dp*m1)
     Else 
        C2C12=(5 + r**2*(-9 + 4*r) - 6*(-2 + r)*r*Log(r))/(12._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2C12=1/(8._dp*m2) - (7*(-1 + r))/(120._dp*m2) + (-1 + r)**2/(30._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2C12=1/(3._dp*m2)
     Else 
        C2C12=(4 - 9*r + 5*r**3 + 6*(1 - 2*r)*r*Log(r))/(12._dp*m2*(-1 + r)**4)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C2C12=1/(8._dp*m1) - (11*(-1 + r))/(120._dp*m1) + (13*(-1 + r)**2)/(180._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C2C12=large
     Else 
        C2C12=((-1 + r)*(16 + r*(-29 + 7*r)) + 6*(-2 + 3*r)*Log(r))/(36._dp*m1*(-1 + r)**4)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C2C12=1/(8._dp*m2) - (-1 + r)/(30._dp*m2) + (-1 + r)**2/(72._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C2C12=7/(36._dp*m2)
     Else 
        C2C12=(-((-1 + r)*(7 + r*(-29 + 16*r))) + 6*r**2*(-3 + 2*r)*Log(r))/(36._dp*m2*(-1 + r)**4)
     End if 
  End if 

Else!! Different masses are not possible! 
   C2C12 =0._dp 
End if 
 
End Function C2C12 


Real(dp) Function C1C2(m1in,m2in,m3in) 
Real(dp),Intent(in)::m1in,m2in,m3in 
Real(dp)::eps=1E-10_dp,large=0._dp,epsR=1E-03_dp 
Real(dp)::m1,m2,r 

!  C1 + C2

If (Abs(m1in-m2in)/Abs(m1in+m2in).lt.eps) Then! m1==m2 
 m1=m1in
 m2=m3in
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then  ! Taylor
        C1C2=1/(3._dp*m1) - (-1 + r)/(8._dp*m1) + (-1 + r)**2/(15._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1C2=3/(4._dp*m1)
     Else 
        C1C2=-(3 - 4*r + r**2 - 2*(-2 + r)*r*Log(r))/(4._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1C2=1/(3._dp*m2) - (5*(-1 + r))/(24._dp*m2) + (3*(-1 + r)**2)/(20._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1C2=large
     Else 
        C1C2=(1 - 4*r + 3*r**2 + (2 - 4*r)*Log(r))/(4._dp*m2*(-1 + r)**3)
    End if 
   End if 

Else if (Abs(m2in-m3in)/Abs(m2in+m3in).lt.eps) Then! m2==m3 
 m1=m1in 
 m2=m3in 
   If (m1.gt.m2) Then 
     r=m2/m1 
     If ((1._dp-r).lt.epsR) Then 
        C1C2=1/(3._dp*m1) - (-1 + r)/(4._dp*m1) + (-1 + r)**2/(5._dp*m1)
     Elseif (Abs(r).lt.eps) Then 
        C1C2=large
     Else 
        C1C2=(3 - 4*r + r**2 + 2*Log(r))/(2._dp*m1*(-1 + r)**3)
     End if 
   Else 
     r=m1/m2 
     If ((1._dp-r).lt.epsR) Then 
        C1C2=1/(3._dp*m2) - (-1 + r)/(12._dp*m2) + (-1 + r)**2/(30._dp*m2)
     Elseif (Abs(r).lt.eps) Then 
        C1C2=1/(2._dp*m2)
     Else 
        C1C2=(-1 + (4 - 3*r)*r + 2*r**2*Log(r))/(2._dp*m2*(-1 + r)**3)
     End if 
  End if 

Else!! Different masses are not possible! 
   C1C2 =0._dp 
End if 
 
End Function C1C2 
End Module FlavorKit_LFV_SingletDoubletB 
