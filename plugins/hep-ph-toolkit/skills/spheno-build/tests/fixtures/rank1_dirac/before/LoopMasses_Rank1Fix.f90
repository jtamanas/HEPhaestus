! Minimal LoopMasses fixture reproducing the rank-1 private cache +
! OneLoop<Mass> Intent(out) pattern for a single-eigenstate Dirac mass.
Module LoopMasses_Rank1Fix

Use Control
Use Model_Data_Rank1Fix

Real(dp), Private :: MFChiM_1L(1), MFChiM2_1L(1)

Contains

Subroutine CalculateOneLoopMasses(MFChiM,MFChiM2,kont)
Implicit None
Real(dp), Intent(inout) :: MFChiM,MFChiM2
Integer, Intent(inout) :: kont
Complex(dp) :: UM_1L(1,1), UP_1L(1,1)
Real(dp) :: MPsi, MHp
MPsi = 500._dp
MHp = 125._dp
Call OneLoopFChiM(MPsi,MHp,MFChiM,MFChiM2,MFChiM_1L,MFChiM2_1L,UM_1L,UP_1L,kont)
MFChiM = MFChiM_1L
MFChiM2 = MFChiM2_1L
End Subroutine CalculateOneLoopMasses

Subroutine OneLoopFChiM(MPsi,MHp,MFChiM,MFChiM2,MFChiM_1L,MFChiM2_1L,UM_1L,UP_1L,ierr)
Real(dp), Intent(in) :: MPsi,MHp,MFChiM,MFChiM2
Integer, Intent(inout) :: ierr
Integer :: il
Real(dp), Intent(out) :: MFChiM_1L(1),MFChiM2_1L(1)
Complex(dp), Intent(out) :: UM_1L(1,1), UP_1L(1,1)
Real(dp) :: MFChiM_t(1), MFChiM2_t(1)
il = 1
MFChiM2_t(il) = MPsi**2
MFChiM2_1L(il) = MFChiM2_t(il)
MFChiM_1L(il) = Sqrt(MFChiM2_1L(il))
If (Abs(MFChiM2_1L(il)).lt.1.0E-30_dp) ierr = -1
UM_1L = 0._dp
UP_1L = 0._dp
End Subroutine OneLoopFChiM

End Module LoopMasses_Rank1Fix
