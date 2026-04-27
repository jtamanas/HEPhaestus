! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module FlavorKit_QFV_SingletDoubletB 
Use Control 
Use Settings 
Use Couplings_SingletDoubletB 
Use LoopCouplings_SingletDoubletB 
Use LoopMasses_SM_HC 
Use LoopFunctions 
Use LoopMasses_SingletDoubletB 
Use StandardModel 

 
 Contains 
 
Subroutine CalculateBox2d2L(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,BOddllSLL,       & 
& BOddllSRR,BOddllSRL,BOddllSLR,BOddllVRR,BOddllVLL,BOddllVRL,BOddllVLR,BOddllTLL,       & 
& BOddllTLR,BOddllTRL,BOddllTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box2d2L 
! 'PreSARAH' output has been generated  at 16:40 on 10.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BOddllSLL 
Complex(dp), Intent(out) :: BOddllSRR 
Complex(dp), Intent(out) :: BOddllSRL 
Complex(dp), Intent(out) :: BOddllSLR 
Complex(dp), Intent(out) :: BOddllVRR 
Complex(dp), Intent(out) :: BOddllVLL 
Complex(dp), Intent(out) :: BOddllVRL 
Complex(dp), Intent(out) :: BOddllVLR 
Complex(dp), Intent(out) :: BOddllTLL 
Complex(dp), Intent(out) :: BOddllTLR 
Complex(dp), Intent(out) :: BOddllTRL 
Complex(dp), Intent(out) :: BOddllTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox2d2L' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
BOddllSLL=0._dp 
BOddllSRR=0._dp 
BOddllSRL=0._dp 
BOddllSLR=0._dp 
BOddllVRR=0._dp 
BOddllVLL=0._dp 
BOddllVRL=0._dp 
BOddllVLR=0._dp 
BOddllTLL=0._dp 
BOddllTLR=0._dp 
BOddllTRL=0._dp 
BOddllTRR=0._dp 
BOddllSLL=oo16pi2*BOddllSLL 
BOddllSRR=oo16pi2*BOddllSRR 
BOddllSRL=oo16pi2*BOddllSRL 
BOddllSLR=oo16pi2*BOddllSLR 
BOddllVRR=oo16pi2*BOddllVRR 
BOddllVLL=oo16pi2*BOddllVLL 
BOddllVRL=oo16pi2*BOddllVRL 
BOddllVLR=oo16pi2*BOddllVLR 
BOddllTLL=oo16pi2*BOddllTLL 
BOddllTLR=oo16pi2*BOddllTLR 
BOddllTRL=oo16pi2*BOddllTRL 
BOddllTRR=oo16pi2*BOddllTRR 
Iname=Iname-1

End Subroutine CalculateBox2d2L 

Subroutine CalculatePengS2d2L(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& PSOddllSLL,PSOddllSRR,PSOddllSRL,PSOddllSLR,PSOddllVRR,PSOddllVLL,PSOddllVRL,          & 
& PSOddllVLR,PSOddllTLL,PSOddllTLR,PSOddllTRL,PSOddllTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS2d2L 
! 'PreSARAH' output has been generated  at 15:40 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSOddllSLL 
Complex(dp), Intent(out) :: PSOddllSRR 
Complex(dp), Intent(out) :: PSOddllSRL 
Complex(dp), Intent(out) :: PSOddllSLR 
Complex(dp), Intent(out) :: PSOddllVRR 
Complex(dp), Intent(out) :: PSOddllVLL 
Complex(dp), Intent(out) :: PSOddllVRL 
Complex(dp), Intent(out) :: PSOddllVLR 
Complex(dp), Intent(out) :: PSOddllTLL 
Complex(dp), Intent(out) :: PSOddllTLR 
Complex(dp), Intent(out) :: PSOddllTRL 
Complex(dp), Intent(out) :: PSOddllTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS2d2L' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PSOddllSLL=0._dp 
PSOddllSRR=0._dp 
PSOddllSRL=0._dp 
PSOddllSLR=0._dp 
PSOddllVRR=0._dp 
PSOddllVLL=0._dp 
PSOddllVRL=0._dp 
PSOddllVLR=0._dp 
PSOddllTLL=0._dp 
PSOddllTLR=0._dp 
PSOddllTRL=0._dp 
PSOddllTRR=0._dp 
PSOddllSLL=oo16pi2*PSOddllSLL 
PSOddllSRR=oo16pi2*PSOddllSRR 
PSOddllSRL=oo16pi2*PSOddllSRL 
PSOddllSLR=oo16pi2*PSOddllSLR 
PSOddllVRR=oo16pi2*PSOddllVRR 
PSOddllVLL=oo16pi2*PSOddllVLL 
PSOddllVRL=oo16pi2*PSOddllVRL 
PSOddllVLR=oo16pi2*PSOddllVLR 
PSOddllTLL=oo16pi2*PSOddllTLL 
PSOddllTLR=oo16pi2*PSOddllTLR 
PSOddllTRL=oo16pi2*PSOddllTRL 
PSOddllTRR=oo16pi2*PSOddllTRR 
Iname=Iname-1

End Subroutine CalculatePengS2d2L 

Subroutine CalculatePengV2d2L(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& PVOddllSLL,PVOddllSRR,PVOddllSRL,PVOddllSLR,PVOddllVRR,PVOddllVLL,PVOddllVRL,          & 
& PVOddllVLR,PVOddllTLL,PVOddllTLR,PVOddllTRL,PVOddllTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV2d2L 
! 'PreSARAH' output has been generated  at 15:41 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVOddllSLL 
Complex(dp), Intent(out) :: PVOddllSRR 
Complex(dp), Intent(out) :: PVOddllSRL 
Complex(dp), Intent(out) :: PVOddllSLR 
Complex(dp), Intent(out) :: PVOddllVRR 
Complex(dp), Intent(out) :: PVOddllVLL 
Complex(dp), Intent(out) :: PVOddllVRL 
Complex(dp), Intent(out) :: PVOddllVLR 
Complex(dp), Intent(out) :: PVOddllTLL 
Complex(dp), Intent(out) :: PVOddllTLR 
Complex(dp), Intent(out) :: PVOddllTRL 
Complex(dp), Intent(out) :: PVOddllTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV2d2L' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
PVOddllSLL=0._dp 
PVOddllSRR=0._dp 
PVOddllSRL=0._dp 
PVOddllSLR=0._dp 
PVOddllVRR=0._dp 
PVOddllVLL=0._dp 
PVOddllVRL=0._dp 
PVOddllVLR=0._dp 
PVOddllTLL=0._dp 
PVOddllTLR=0._dp 
PVOddllTRL=0._dp 
PVOddllTRR=0._dp 
PVOddllSLL=oo16pi2*PVOddllSLL
PVOddllSRR=oo16pi2*PVOddllSRR
PVOddllSRL=oo16pi2*PVOddllSRL
PVOddllSLR=oo16pi2*PVOddllSLR
PVOddllVRR=oo16pi2*PVOddllVRR
PVOddllVLL=oo16pi2*PVOddllVLL
PVOddllVRL=oo16pi2*PVOddllVRL
PVOddllVLR=oo16pi2*PVOddllVLR
PVOddllTLL=oo16pi2*PVOddllTLL
PVOddllTLR=oo16pi2*PVOddllTLR
PVOddllTRL=oo16pi2*PVOddllTRL
PVOddllTRR=oo16pi2*PVOddllTRR
Iname=Iname-1

End Subroutine CalculatePengV2d2L 

Subroutine CalculateTreeS2d2L(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& TSOddllSLL,TSOddllSRR,TSOddllSRL,TSOddllSLR,TSOddllVRR,TSOddllVLL,TSOddllVRL,          & 
& TSOddllVLR,TSOddllTLL,TSOddllTLR,TSOddllTRL,TSOddllTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS2d2L 
! 'PreSARAH' output has been generated  at 15:41 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSOddllSLL 
Complex(dp), Intent(out) :: TSOddllSRR 
Complex(dp), Intent(out) :: TSOddllSRL 
Complex(dp), Intent(out) :: TSOddllSLR 
Complex(dp), Intent(out) :: TSOddllVRR 
Complex(dp), Intent(out) :: TSOddllVLL 
Complex(dp), Intent(out) :: TSOddllVRL 
Complex(dp), Intent(out) :: TSOddllVLR 
Complex(dp), Intent(out) :: TSOddllTLL 
Complex(dp), Intent(out) :: TSOddllTLR 
Complex(dp), Intent(out) :: TSOddllTRL 
Complex(dp), Intent(out) :: TSOddllTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS2d2L' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TSOddllSLL=0._dp 
TSOddllSRR=0._dp 
TSOddllSRL=0._dp 
TSOddllSLR=0._dp 
TSOddllVRR=0._dp 
TSOddllVLL=0._dp 
TSOddllVRL=0._dp 
TSOddllVLR=0._dp 
TSOddllTLL=0._dp 
TSOddllTLR=0._dp 
TSOddllTRL=0._dp 
TSOddllTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS2d2L 

Subroutine CalculateTreeV2d2L(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& TVOddllSLL,TVOddllSRR,TVOddllSRL,TVOddllSLR,TVOddllVRR,TVOddllVLL,TVOddllVRL,          & 
& TVOddllVLR,TVOddllTLL,TVOddllTLR,TVOddllTRL,TVOddllTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV2d2L 
! 'PreSARAH' output has been generated  at 15:41 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVOddllSLL 
Complex(dp), Intent(out) :: TVOddllSRR 
Complex(dp), Intent(out) :: TVOddllSRL 
Complex(dp), Intent(out) :: TVOddllSLR 
Complex(dp), Intent(out) :: TVOddllVRR 
Complex(dp), Intent(out) :: TVOddllVLL 
Complex(dp), Intent(out) :: TVOddllVRL 
Complex(dp), Intent(out) :: TVOddllVLR 
Complex(dp), Intent(out) :: TVOddllTLL 
Complex(dp), Intent(out) :: TVOddllTLR 
Complex(dp), Intent(out) :: TVOddllTRL 
Complex(dp), Intent(out) :: TVOddllTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV2d2L' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFe(gt3)  
MassEx32=MFe2(gt3) 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], ChargedLepton, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TVOddllSLL=0._dp 
TVOddllSRR=0._dp 
TVOddllSRL=0._dp 
TVOddllSLR=0._dp 
TVOddllVRR=0._dp 
TVOddllVLL=0._dp 
TVOddllVRL=0._dp 
TVOddllVLR=0._dp 
TVOddllTLL=0._dp 
TVOddllTLR=0._dp 
TVOddllTRL=0._dp 
TVOddllTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV2d2L 

Subroutine CalculateBox2d2nu(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,BOddvvVRR,               & 
& BOddvvVLL,BOddvvVRL,BOddvvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box2d2nu 
! 'PreSARAH' output has been generated  at 12:38 on 13.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BOddvvVRR 
Complex(dp), Intent(out) :: BOddvvVLL 
Complex(dp), Intent(out) :: BOddvvVRL 
Complex(dp), Intent(out) :: BOddvvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox2d2nu' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=0._dp  
MassEx42=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], Neutrino, bar[Neutrino]} 
 ! ------------------------------ 
 
BOddvvVRR=0._dp 
BOddvvVLL=0._dp 
BOddvvVRL=0._dp 
BOddvvVLR=0._dp 
BOddvvVRR=oo16pi2*BOddvvVRR 
BOddvvVLL=oo16pi2*BOddvvVLL 
BOddvvVRL=oo16pi2*BOddvvVRL 
BOddvvVLR=oo16pi2*BOddvvVLR 
Iname=Iname-1

End Subroutine CalculateBox2d2nu 

Subroutine CalculatePengS2d2nu(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,PSOddvvVRR,            & 
& PSOddvvVLL,PSOddvvVRL,PSOddvvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengS2d2nu 
! 'PreSARAH' output has been generated  at 19:19 on 4.3.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PSOddvvVRR 
Complex(dp), Intent(out) :: PSOddvvVLL 
Complex(dp), Intent(out) :: PSOddvvVRL 
Complex(dp), Intent(out) :: PSOddvvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengS2d2nu' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=0._dp  
MassEx42=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], Neutrino, bar[Neutrino]} 
 ! ------------------------------ 
 
PSOddvvVRR=0._dp 
PSOddvvVLL=0._dp 
PSOddvvVRL=0._dp 
PSOddvvVLR=0._dp 
PSOddvvVRR=oo16pi2*PSOddvvVRR 
PSOddvvVLL=oo16pi2*PSOddvvVLL 
PSOddvvVRL=oo16pi2*PSOddvvVRL 
PSOddvvVLR=oo16pi2*PSOddvvVLR 
Iname=Iname-1

End Subroutine CalculatePengS2d2nu 

Subroutine CalculatePengV2d2nu(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,PVOddvvVRR,            & 
& PVOddvvVLL,PVOddvvVRL,PVOddvvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process PengV2d2nu 
! 'PreSARAH' output has been generated  at 19:21 on 4.3.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: PVOddvvVRR 
Complex(dp), Intent(out) :: PVOddvvVLL 
Complex(dp), Intent(out) :: PVOddvvVRL 
Complex(dp), Intent(out) :: PVOddvvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculatePengV2d2nu' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=0._dp  
MassEx42=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], Neutrino, bar[Neutrino]} 
 ! ------------------------------ 
 
PVOddvvVRR=0._dp 
PVOddvvVLL=0._dp 
PVOddvvVRL=0._dp 
PVOddvvVLR=0._dp 
PVOddvvVRR=oo16pi2*PVOddvvVRR
PVOddvvVLL=oo16pi2*PVOddvvVLL
PVOddvvVRL=oo16pi2*PVOddvvVRL
PVOddvvVLR=oo16pi2*PVOddvvVLR
Iname=Iname-1

End Subroutine CalculatePengV2d2nu 

Subroutine CalculateTreeS2d2nu(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,TSOddvvVRR,            & 
& TSOddvvVLL,TSOddvvVRL,TSOddvvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS2d2nu 
! 'PreSARAH' output has been generated  at 19:21 on 4.3.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSOddvvVRR 
Complex(dp), Intent(out) :: TSOddvvVLL 
Complex(dp), Intent(out) :: TSOddvvVRL 
Complex(dp), Intent(out) :: TSOddvvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS2d2nu' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=0._dp  
MassEx42=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], Neutrino, bar[Neutrino]} 
 ! ------------------------------ 
 
TSOddvvVRR=0._dp 
TSOddvvVLL=0._dp 
TSOddvvVRL=0._dp 
TSOddvvVLR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS2d2nu 

Subroutine CalculateTreeV2d2nu(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,TVOddvvVRR,            & 
& TVOddvvVLL,TVOddvvVRL,TVOddvvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV2d2nu 
! 'PreSARAH' output has been generated  at 19:21 on 4.3.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVOddvvVRR 
Complex(dp), Intent(out) :: TVOddvvVLL 
Complex(dp), Intent(out) :: TVOddvvVRL 
Complex(dp), Intent(out) :: TVOddvvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV2d2nu' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=0._dp  
MassEx42=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], Neutrino, bar[Neutrino]} 
 ! ------------------------------ 
 
TVOddvvVRR=0._dp 
TVOddvvVLL=0._dp 
TVOddvvVRL=0._dp 
TVOddvvVLR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV2d2nu 

Subroutine CalculateBox4d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,BO4dSLL,BO4dSRR,            & 
& BO4dSRL,BO4dSLR,BO4dVRR,BO4dVLL,BO4dVRL,BO4dVLR,BO4dTLL,BO4dTLR,BO4dTRL,BO4dTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Box4d 
! 'PreSARAH' output has been generated  at 11:39 on 10.6.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: BO4dSLL 
Complex(dp), Intent(out) :: BO4dSRR 
Complex(dp), Intent(out) :: BO4dSRL 
Complex(dp), Intent(out) :: BO4dSLR 
Complex(dp), Intent(out) :: BO4dVRR 
Complex(dp), Intent(out) :: BO4dVLL 
Complex(dp), Intent(out) :: BO4dVRL 
Complex(dp), Intent(out) :: BO4dVLR 
Complex(dp), Intent(out) :: BO4dTLL 
Complex(dp), Intent(out) :: BO4dTLR 
Complex(dp), Intent(out) :: BO4dTRL 
Complex(dp), Intent(out) :: BO4dTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateBox4d' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
BO4dSLL=0._dp 
BO4dSRR=0._dp 
BO4dSRL=0._dp 
BO4dSLR=0._dp 
BO4dVRR=0._dp 
BO4dVLL=0._dp 
BO4dVRL=0._dp 
BO4dVLR=0._dp 
BO4dTLL=0._dp 
BO4dTLR=0._dp 
BO4dTRL=0._dp 
BO4dTRR=0._dp 
BO4dSLL=oo16pi2*BO4dSLL 
BO4dSRR=oo16pi2*BO4dSRR 
BO4dSRL=oo16pi2*BO4dSRL 
BO4dSLR=oo16pi2*BO4dSLR 
BO4dVRR=oo16pi2*BO4dVRR 
BO4dVLL=oo16pi2*BO4dVLL 
BO4dVRL=oo16pi2*BO4dVRL 
BO4dVLR=oo16pi2*BO4dVLR 
BO4dTLL=oo16pi2*BO4dTLL 
BO4dTLR=oo16pi2*BO4dTLR 
BO4dTRL=oo16pi2*BO4dTRL 
BO4dTRR=oo16pi2*BO4dTRR 
Iname=Iname-1

End Subroutine CalculateBox4d 

Subroutine CalculateTreeS4d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,TSO4dSLL,TSO4dSRR,        & 
& TSO4dSRL,TSO4dSLR,TSO4dVRR,TSO4dVLL,TSO4dVRL,TSO4dVLR,TSO4dTLL,TSO4dTLR,               & 
& TSO4dTRL,TSO4dTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeS4d 
! 'PreSARAH' output has been generated  at 11:24 on 15.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSO4dSLL 
Complex(dp), Intent(out) :: TSO4dSRR 
Complex(dp), Intent(out) :: TSO4dSRL 
Complex(dp), Intent(out) :: TSO4dSLR 
Complex(dp), Intent(out) :: TSO4dVRR 
Complex(dp), Intent(out) :: TSO4dVLL 
Complex(dp), Intent(out) :: TSO4dVRL 
Complex(dp), Intent(out) :: TSO4dVLR 
Complex(dp), Intent(out) :: TSO4dTLL 
Complex(dp), Intent(out) :: TSO4dTLR 
Complex(dp), Intent(out) :: TSO4dTRL 
Complex(dp), Intent(out) :: TSO4dTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeS4d' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
TSO4dSLL=0._dp 
TSO4dSRR=0._dp 
TSO4dSRL=0._dp 
TSO4dSLR=0._dp 
TSO4dVRR=0._dp 
TSO4dVLL=0._dp 
TSO4dVRL=0._dp 
TSO4dVLR=0._dp 
TSO4dTLL=0._dp 
TSO4dTLR=0._dp 
TSO4dTRL=0._dp 
TSO4dTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeS4d 

Subroutine CalculateTreeV4d(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,TVO4dSLL,TVO4dSRR,        & 
& TVO4dSRL,TVO4dSLR,TVO4dVRR,TVO4dVLL,TVO4dVRL,TVO4dVLR,TVO4dTLL,TVO4dTLR,               & 
& TVO4dTRL,TVO4dTRR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeV4d 
! 'PreSARAH' output has been generated  at 11:24 on 15.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVO4dSLL 
Complex(dp), Intent(out) :: TVO4dSRR 
Complex(dp), Intent(out) :: TVO4dSRL 
Complex(dp), Intent(out) :: TVO4dSLR 
Complex(dp), Intent(out) :: TVO4dVRR 
Complex(dp), Intent(out) :: TVO4dVLL 
Complex(dp), Intent(out) :: TVO4dVRL 
Complex(dp), Intent(out) :: TVO4dVLR 
Complex(dp), Intent(out) :: TVO4dTLL 
Complex(dp), Intent(out) :: TVO4dTLR 
Complex(dp), Intent(out) :: TVO4dTRL 
Complex(dp), Intent(out) :: TVO4dTRR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeV4d' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MFd(gt3)  
MassEx32=MFd2(gt3) 
MassEx4=MFd(gt4)  
MassEx42=MFd2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], DownQuark, bar[DownQuark]} 
 ! ------------------------------ 
 
TVO4dSLL=0._dp 
TVO4dSRR=0._dp 
TVO4dSRL=0._dp 
TVO4dSLR=0._dp 
TVO4dVRR=0._dp 
TVO4dVLL=0._dp 
TVO4dVRL=0._dp 
TVO4dVLR=0._dp 
TVO4dTLL=0._dp 
TVO4dTLR=0._dp 
TVO4dTRL=0._dp 
TVO4dTRR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeV4d 

Subroutine CalculateA2q(gt1,gt2,gt3,OnlySM,MAh,MAh2,MFd,MFd2,Join(List()              & 
& ,Part(1,1)),OAh2qSL,OAh2qSR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process A2q 
! 'PreSARAH' output has been generated  at 11:59 on 3.4.2014 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MAh,MAh2,MFd(3),MFd2(3)

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OAh2qSL 
Complex(dp), Intent(out) :: OAh2qSR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateA2q' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=MAh  
MassEx32=MAh2 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], PseudoScalar} 
 ! ------------------------------ 
 
OAh2qSL=0._dp 
OAh2qSR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1R = Conjg(1)
coup1L = Conjg(1)
! Amplitude 
  OAh2qSL=OAh2qSL+ 0.
  OAh2qSR=OAh2qSR+ 0.
 End if 


 OAh2qSL=oo16pi2*OAh2qSL 
OAh2qSR=oo16pi2*OAh2qSR 
Iname=Iname-1

End Subroutine CalculateA2q 

Subroutine CalculateTreeSdulv(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,TSOdulvSLL,TSOdulvSRR,TSOdulvSRL,TSOdulvSLR,TSOdulvVRR,TSOdulvVLL,            & 
& TSOdulvVRL,TSOdulvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeSdulv 
! 'PreSARAH' output has been generated  at 15:42 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TSOdulvSLL 
Complex(dp), Intent(out) :: TSOdulvSRR 
Complex(dp), Intent(out) :: TSOdulvSRL 
Complex(dp), Intent(out) :: TSOdulvSLR 
Complex(dp), Intent(out) :: TSOdulvVRR 
Complex(dp), Intent(out) :: TSOdulvVLL 
Complex(dp), Intent(out) :: TSOdulvVRL 
Complex(dp), Intent(out) :: TSOdulvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeSdulv' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFu(gt2)  
MassEx22=MFu2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[UpQuark], Neutrino, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TSOdulvSLL=0._dp 
TSOdulvSRR=0._dp 
TSOdulvSRL=0._dp 
TSOdulvSLR=0._dp 
TSOdulvVRR=0._dp 
TSOdulvVLL=0._dp 
TSOdulvVRL=0._dp 
TSOdulvVLR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeSdulv 

Subroutine CalculateTreeVdulv(gt1,gt2,gt3,gt4,OnlySM,MFd,MFd2,MFe,MFe2,               & 
& MFu,MFu2,TVOdulvSLL,TVOdulvSRR,TVOdulvSRL,TVOdulvSLR,TVOdulvVRR,TVOdulvVLL,            & 
& TVOdulvVRL,TVOdulvVLR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process TreeVdulv 
! 'PreSARAH' output has been generated  at 15:42 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),MFe(3),MFe2(3),MFu(3),MFu2(3)

Integer,Intent(in) :: gt1, gt2,gt3,gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx4, MassEx12,MassEx22,MassEx32,MassEx42 
Complex(dp), Intent(out) :: TVOdulvSLL 
Complex(dp), Intent(out) :: TVOdulvSRR 
Complex(dp), Intent(out) :: TVOdulvSRL 
Complex(dp), Intent(out) :: TVOdulvSLR 
Complex(dp), Intent(out) :: TVOdulvVRR 
Complex(dp), Intent(out) :: TVOdulvVLL 
Complex(dp), Intent(out) :: TVOdulvVRL 
Complex(dp), Intent(out) :: TVOdulvVLR 
Complex(dp) :: vertex1L, vertex1R, vertex2L, vertex2R 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateTreeVdulv' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFu(gt2)  
MassEx22=MFu2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
MassEx4=MFe(gt4)  
MassEx42=MFe2(gt4) 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[UpQuark], Neutrino, bar[ChargedLepton]} 
 ! ------------------------------ 
 
TVOdulvSLL=0._dp 
TVOdulvSRR=0._dp 
TVOdulvSRL=0._dp 
TVOdulvSLR=0._dp 
TVOdulvVRR=0._dp 
TVOdulvVLL=0._dp 
TVOdulvVRL=0._dp 
TVOdulvVLR=0._dp 
Iname=Iname-1

End Subroutine CalculateTreeVdulv 

Subroutine CalculateGamma2Q(gt1,gt2,gt3,OnlySM,MFd,MFd2,Join(List(),Part(1,1))        & 
& ,OA2qSL,OA2qSR,OA2qVL,OA2qVR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Gamma2Q 
! 'PreSARAH' output has been generated  at 15:35 on 16.12.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OA2qSL 
Complex(dp), Intent(out) :: OA2qSR 
Complex(dp), Intent(out) :: OA2qVL 
Complex(dp), Intent(out) :: OA2qVR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateGamma2Q' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {bar[BottomQuark], BottomQuark, Photon} 
 ! ------------------------------ 
 
OA2qSL=0._dp 
OA2qSR=0._dp 
OA2qVL=0._dp 
OA2qVR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1L = Conjg(1)
coup1R = Conjg(1)
! Amplitude 
  OA2qSL=OA2qSL+ 0.
  OA2qSR=OA2qSR+ 0.
  OA2qVL=OA2qVL+ 0.
  OA2qVR=OA2qVR+ 0.
 End if 


 OA2qSL=oo16pi2*OA2qSL 
OA2qSR=oo16pi2*OA2qSR 
OA2qVL=oo16pi2*OA2qVL 
OA2qVR=oo16pi2*OA2qVR 
Iname=Iname-1

End Subroutine CalculateGamma2Q 

Subroutine CalculateGluon2Q(gt1,gt2,gt3,OnlySM,MFd,MFd2,Join(List(),Part(1,1))        & 
& ,OG2qSL,OG2qSR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process Gluon2Q 
! 'PreSARAH' output has been generated  at 11:48 on 2.2.2015 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3)

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OG2qSL 
Complex(dp), Intent(out) :: OG2qSR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateGluon2Q' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=0._dp  
MassEx32=0._dp 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {bar[BottomQuark], BottomQuark, Gluon} 
 ! ------------------------------ 
 
OG2qSL=0._dp 
OG2qSR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1L = Conjg(1)
coup1R = Conjg(1)
! Amplitude 
  OG2qSL=OG2qSL+ 0.
  OG2qSR=OG2qSR+ 0.
 End if 


 OG2qSL=oo16pi2*OG2qSL 
OG2qSR=oo16pi2*OG2qSR 
Iname=Iname-1

End Subroutine CalculateGluon2Q 

Subroutine CalculateH2q(gt1,gt2,gt3,OnlySM,MFd,MFd2,Mhh,Mhh2,Join(List()              & 
& ,Part(1,1)),OH2qSL,OH2qSR)

! ---------------------------------------------------------------- 
! Code based on automatically generated SARAH extensions by 'PreSARAH' 
! Expressions for amplitudes are obtained by FeynArts/FormCalc 
! Based on user input for process H2q 
! 'PreSARAH' output has been generated  at 10:50 on 14.1.2016 
! ---------------------------------------------------------------- 
 
Implicit None 
Real(dp),Intent(in) :: MFd(3),MFd2(3),Mhh,Mhh2

Complex(dp),Intent(in) :: Join(List(),Part(1,1))

Integer,Intent(in) :: gt1, gt2,gt3 
Integer :: gt4 
Logical, Intent(in) :: OnlySM 
Integer :: iprop, i1, i2, i3, i4 
Real(dp) :: MassEx1,MassEx2,MassEx3,MassEx12,MassEx22,MassEx32 
Complex(dp), Intent(out) :: OH2qSL 
Complex(dp), Intent(out) :: OH2qSR 
Real(dp) ::  MP, MP2, IMP2, IMP, MFin, MFin2, IMFin, IMFin2, Finite  
Real(dp) ::  MS1, MS12, MS2, MS22, MF1, MF12, MF2, MF22, MV1, MV12, MV2, MV22  
Complex(dp) ::  chargefactor  
Complex(dp) ::  coup1L, coup1R, coup2L, coup2R, coup3L, coup3R, coup3, coup4L, coup4R 

Complex(dp) ::  int1,int2,int3,int4,int5,int6,int7,int8 

Iname=Iname+1 
NameOfUnit(Iname)='CalculateH2q' 

Finite=1._dp 
MassEx1=MFd(gt1)  
MassEx12=MFd2(gt1) 
MassEx2=MFd(gt2)  
MassEx22=MFd2(gt2) 
MassEx3=Mhh  
MassEx32=Mhh2 
! ------------------------------ 
 ! Amplitudes for external states 
 ! {DownQuark, bar[DownQuark], HiggsBoson} 
 ! ------------------------------ 
 
OH2qSL=0._dp 
OH2qSR=0._dp 
!---------------------------------------- 
! Tree Contributions                      
!---------------------------------------- 
chargefactor = 1 
If ((OnlySM).or.(.not.OnlySM)) Then 
coup1R = Conjg(1)
coup1L = Conjg(1)
! Amplitude 
  OH2qSL=OH2qSL+ 0.
  OH2qSR=OH2qSR+ 0.
 End if 


 OH2qSL=oo16pi2*OH2qSL 
OH2qSR=oo16pi2*OH2qSR 
Iname=Iname-1

End Subroutine CalculateH2q 

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
End Module FlavorKit_QFV_SingletDoubletB 
