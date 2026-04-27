! Minimal InputOutput fixture reproducing the rank-1 guard bug:
! MFChiM is module-scalar (see Model_Data_Rank1Fix) but this file
! writes the subscripted-scalar guard shape that gfortran rejects
! at compile time. See test body for the exact shape we patch.
Module InputOutput_Rank1Fix

Use Control
Use Model_Data_Rank1Fix

Contains

Subroutine WriteSLHA()
Implicit None
Complex(dp) :: UM(1,1), UP(1,1)
! The ``"# MFChiM(1) "`` label is a comment string; patch must not touch it.
Write(*,*) 9984071, MFChiM, "# MFChiM(1) "
If (MFChiM(1).Gt.0._dp) Then
Write(*,*) "UM11_r = ", Real(UM(1,1),dp)
End if
If (MFChiM(1).Gt.0._dp) Then
Write(*,*) "UP11_r = ", Real(UP(1,1),dp)
End if
End Subroutine WriteSLHA

End Module InputOutput_Rank1Fix
