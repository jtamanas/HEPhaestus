! Minimal Model_Data fixture for the rank-1 Dirac demotion patch test.
! Mirrors the SARAH-emitted module-level mass decl shape: MFChiM is scalar,
! MFChi is rank-3, so the safety filter only touches MFChiM.
Module Model_Data_Rank1Fix

Use Control

Real(dp) :: MAh,MAh2,MFChi(3),MFChi2(3),MFChiM,MFChiM2,MFd(3),MFd2(3),MFe(3),MFe2(3),             &
& MFu(3),MFu2(3),Mhh,Mhh2,MHp,MHp2,MVWp,MVWp2,MVZ,MVZ2

Contains

Subroutine SetMatchingConditions(g1,g2,g3)
Real(dp), Intent(in) :: g1,g2,g3
MFChiM = 0._dp
MFChiM2 = 0._dp
End Subroutine SetMatchingConditions

End Module Model_Data_Rank1Fix
