! Minimal TreeLevelMasses fixture reproducing the rank-1 MFChiM emission.
! The caller (TreeMasses) declares MFChiM/MFChiM2 as scalar; the callees
! (CalculateMFChiM, CalculateMFChiMEffPot) declare MFChiM(1) as rank-1.
! gfortran rejects this at the Call-sites with "Rank mismatch".
Module TreeLevelMasses_Rank1Fix

Use Control
Use Mathematics
Use Model_Data_Rank1Fix

Contains

Subroutine TreeMasses(MFChiM,MFChiM2,kont)
Implicit None
Real(dp),Intent(out) :: MFChiM,MFChiM2
Integer, Intent(inout) :: kont
Real(dp) :: MPsi
Complex(dp) :: UM(1,1), UP(1,1)
MPsi = 500._dp
Call CalculateMFChiM(MPsi,UM,UP,MFChiM,kont)
MFChiM2 = MFChiM**2
End Subroutine TreeMasses

Subroutine CalculateMFChiM(MPsi,UM,UP,MFChiM,kont)
Real(dp),Intent(in) :: MPsi
Integer, Intent(inout) :: kont
Real(dp), Intent(out) :: MFChiM(1)
Complex(dp), Intent(out) :: UM(1,1), UP(1,1)
Real(dp) :: MFChiM2(1)
Complex(dp) :: mat(1,1)
mat(1,1) = MPsi
! EigenSystem call elided in fixture; real file computes MFChiM2(1).
MFChiM2(1) = Abs(mat(1,1))**2
MFChiM = Sqrt( MFChiM2 )
End Subroutine CalculateMFChiM

Subroutine CalculateMFChiMEffPot(MPsi,UM,UP,MFChiM,kont)
Real(dp),Intent(in) :: MPsi
Integer, Intent(inout) :: kont
Real(dp), Intent(out) :: MFChiM(1)
Complex(dp), Intent(out) :: UM(1,1), UP(1,1)
Real(dp) :: MFChiM2(1)
Complex(dp) :: mat(1,1)
mat(1,1) = MPsi
MFChiM2(1) = Abs(mat(1,1))**2
MFChiM = Sqrt( MFChiM2 )
End Subroutine CalculateMFChiMEffPot

End Module TreeLevelMasses_Rank1Fix
