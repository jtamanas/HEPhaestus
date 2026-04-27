! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module CouplingsCT_SingletDoubletB
 
Use Control 
Use Settings 
Use Model_Data_SingletDoubletB 
Use Mathematics, Only: CompareMatrices, Adjungate 
 
Contains 
 
 Subroutine CalculateCouplingCT)

Implicit None 
Integer :: gt1, gt2, gt3, gt4, ct1, ct2, ct3, ct4

Iname = Iname + 1 
NameOfUnit(Iname) = 'CalculateCouplingCT'
 
Iname = Iname - 1 
End Subroutine CalculateCouplingCT

End Module CouplingsCT_SingletDoubletB 
