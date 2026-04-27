! ------------------------------------------------------------------------------  
! This file was automatically created by SARAH version 4.15.3 
! SARAH References: arXiv:0806.0538, 0909.2863, 1002.0840, 1207.0906, 1309.7223,
!           1405.1434, 1411.0675, 1503.03098, 1703.09237, 1706.05372, 1805.07306  
! (c) Florian Staub, Mark Goodsell and Werner Porod 2020  
! ------------------------------------------------------------------------------  
! File created at 21:31 on 24.4.2026   
! ----------------------------------------------------------------------  
 
 
Module RGEs_SingletDoubletB 
 
Use Control 
Use Settings 
Use Model_Data_SingletDoubletB 
Use Mathematics 
 
Logical,Private,Save::OnlyDiagonal

Real(dp),Parameter::id3R(3,3)=& 
   & Reshape(Source=(/& 
   & 1,0,0,& 
 &0,1,0,& 
 &0,0,1& 
 &/),shape=(/3,3/)) 
Contains 


Subroutine GToParameters65(g,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM)

Implicit None 
Real(dp), Intent(in) :: g(65) 
Real(dp),Intent(out) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp),Intent(out) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer i1, i2, i3, i4, SumI 
 
Iname = Iname +1 
NameOfUnit(Iname) = 'GToParameters65' 
 
g1= g(1) 
g2= g(2) 
g3= g(3) 
Lam= Cmplx(g(4),g(5),dp) 
yh2= g(6) 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Yu(i1,i2) = Cmplx( g(SumI+7), g(SumI+8), dp) 
End Do 
 End Do 
 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Yd(i1,i2) = Cmplx( g(SumI+25), g(SumI+26), dp) 
End Do 
 End Do 
 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Ye(i1,i2) = Cmplx( g(SumI+43), g(SumI+44), dp) 
End Do 
 End Do 
 
yh1= g(61) 
MS= g(62) 
MPsi= g(63) 
m2SM= Cmplx(g(64),g(65),dp) 
Do i1=1,65 
If (g(i1).ne.g(i1)) Then 
 Write(*,*) "NaN appearing in ",NameOfUnit(Iname) 
 Write(*,*) "At position ", i1 
 Call TerminateProgram 
End if 
End do 
Iname = Iname - 1 
 
End Subroutine GToParameters65

Subroutine ParametersToG65(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,g)

Implicit None 
Real(dp), Intent(out) :: g(65) 
Real(dp), Intent(in) :: g1,g2,g3,yh2,yh1,MS,MPsi

Complex(dp), Intent(in) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer i1, i2, i3, i4, SumI 
 
Iname = Iname +1 
NameOfUnit(Iname) = 'ParametersToG65' 
 
g(1) = g1  
g(2) = g2  
g(3) = g3  
g(4) = Real(Lam,dp)  
g(5) = Aimag(Lam)  
g(6) = yh2  
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+7) = Real(Yu(i1,i2), dp) 
g(SumI+8) = Aimag(Yu(i1,i2)) 
End Do 
End Do 

Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+25) = Real(Yd(i1,i2), dp) 
g(SumI+26) = Aimag(Yd(i1,i2)) 
End Do 
End Do 

Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+43) = Real(Ye(i1,i2), dp) 
g(SumI+44) = Aimag(Ye(i1,i2)) 
End Do 
End Do 

g(61) = yh1  
g(62) = MS  
g(63) = MPsi  
g(64) = Real(m2SM,dp)  
g(65) = Aimag(m2SM)  
Iname = Iname - 1 
 
End Subroutine ParametersToG65

Subroutine rge65(len, T, GY, F) 
Implicit None 
Integer, Intent(in) :: len 
Real(dp), Intent(in) :: T, GY(len) 
Real(dp), Intent(out) :: F(len) 
Integer :: i1,i2,i3,i4 
Integer :: j1,j2,j3,j4,j5,j6,j7 
Real(dp) :: q 
Real(dp) :: g1,betag11,betag12,Dg1,g2,betag21,betag22,Dg2,g3,betag31,betag32,         & 
& Dg3,yh2,betayh21,betayh22,Dyh2,yh1,betayh11,betayh12,Dyh1,MS,betaMS1,betaMS2,          & 
& DMS,MPsi,betaMPsi1,betaMPsi2,DMPsi
Complex(dp) :: Lam,betaLam1,betaLam2,DLam,Yu(3,3),betaYu1(3,3),betaYu2(3,3)           & 
& ,DYu(3,3),adjYu(3,3),Yd(3,3),betaYd1(3,3),betaYd2(3,3),DYd(3,3),adjYd(3,3)             & 
& ,Ye(3,3),betaYe1(3,3),betaYe2(3,3),DYe(3,3),adjYe(3,3),m2SM,betam2SM1,betam2SM2,Dm2SM
Complex(dp) :: YdadjYd(3,3),YeadjYe(3,3),YuadjYu(3,3),adjYdYd(3,3),adjYeYe(3,3),adjYuYu(3,3),        & 
& YdadjYdYd(3,3),YdadjYuYu(3,3),YeadjYeYe(3,3),YuadjYdYd(3,3),YuadjYuYu(3,3),            & 
& adjYdYdadjYd(3,3),adjYeYeadjYe(3,3),adjYuYuadjYu(3,3),YdadjYdYdadjYd(3,3),             & 
& YeadjYeYeadjYe(3,3),YuadjYuYuadjYu(3,3)

Complex(dp) :: TrYdadjYd,TrYeadjYe,TrYuadjYu,TrYdadjYdYdadjYd,TrYeadjYeYeadjYe,TrYuadjYuYuadjYu

Real(dp) :: g1p2,g1p3,g1p4,g2p2,g2p3,g2p4,g3p2,g3p3,MPsip2,MSp2,yh1p2,yh1p3,yh1p4,yh2p2,          & 
& yh2p3,yh2p4

Complex(dp) :: Lamp2

Iname = Iname +1 
NameOfUnit(Iname) = 'rge65' 
 
OnlyDiagonal = .Not.GenerationMixing 
q = t 
 
Call GToParameters65(gy,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM)

Call Adjungate(Yu,adjYu)
Call Adjungate(Yd,adjYd)
Call Adjungate(Ye,adjYe)
 YdadjYd = Matmul(Yd,adjYd) 
Forall(i2=1:3)  YdadjYd(i2,i2) =  Real(YdadjYd(i2,i2),dp) 
 YeadjYe = Matmul(Ye,adjYe) 
Forall(i2=1:3)  YeadjYe(i2,i2) =  Real(YeadjYe(i2,i2),dp) 
 YuadjYu = Matmul(Yu,adjYu) 
Forall(i2=1:3)  YuadjYu(i2,i2) =  Real(YuadjYu(i2,i2),dp) 
 adjYdYd = Matmul(adjYd,Yd) 
Forall(i2=1:3)  adjYdYd(i2,i2) =  Real(adjYdYd(i2,i2),dp) 
 adjYeYe = Matmul(adjYe,Ye) 
Forall(i2=1:3)  adjYeYe(i2,i2) =  Real(adjYeYe(i2,i2),dp) 
 adjYuYu = Matmul(adjYu,Yu) 
Forall(i2=1:3)  adjYuYu(i2,i2) =  Real(adjYuYu(i2,i2),dp) 
 YdadjYdYd = Matmul(Yd,adjYdYd) 
 YdadjYuYu = Matmul(Yd,adjYuYu) 
 YeadjYeYe = Matmul(Ye,adjYeYe) 
 YuadjYdYd = Matmul(Yu,adjYdYd) 
 YuadjYuYu = Matmul(Yu,adjYuYu) 
 adjYdYdadjYd = Matmul(adjYd,YdadjYd) 
 adjYeYeadjYe = Matmul(adjYe,YeadjYe) 
 adjYuYuadjYu = Matmul(adjYu,YuadjYu) 
 YdadjYdYdadjYd = Matmul(Yd,adjYdYdadjYd) 
Forall(i2=1:3)  YdadjYdYdadjYd(i2,i2) =  Real(YdadjYdYdadjYd(i2,i2),dp) 
 YeadjYeYeadjYe = Matmul(Ye,adjYeYeadjYe) 
Forall(i2=1:3)  YeadjYeYeadjYe(i2,i2) =  Real(YeadjYeYeadjYe(i2,i2),dp) 
 YuadjYuYuadjYu = Matmul(Yu,adjYuYuadjYu) 
Forall(i2=1:3)  YuadjYuYuadjYu(i2,i2) =  Real(YuadjYuYuadjYu(i2,i2),dp) 
 TrYdadjYd = Real(cTrace(YdadjYd),dp) 
 TrYeadjYe = Real(cTrace(YeadjYe),dp) 
 TrYuadjYu = Real(cTrace(YuadjYu),dp) 
 TrYdadjYdYdadjYd = Real(cTrace(YdadjYdYdadjYd),dp) 
 TrYeadjYeYeadjYe = Real(cTrace(YeadjYeYeadjYe),dp) 
 TrYuadjYuYuadjYu = Real(cTrace(YuadjYuYuadjYu),dp) 
 g1p2 =g1**2 
 g1p3 =g1**3 
 g1p4 =g1**4 
 g2p2 =g2**2 
 g2p3 =g2**3 
 g2p4 =g2**4 
 g3p2 =g3**2 
 g3p3 =g3**3 
 MPsip2 =MPsi**2 
 MSp2 =MS**2 
 yh1p2 =yh1**2 
 yh1p3 =yh1**3 
 yh1p4 =yh1**4 
 yh2p2 =yh2**2 
 yh2p3 =yh2**3 
 yh2p4 =yh2**4 
 Lamp2 =Lam**2 


If (TwoLoopRGE) Then 
End If 
 
 
!-------------------- 
! g1 
!-------------------- 
 
betag11  = 9._dp*(g1p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betag12 = 0

 
Dg1 = oo16pi2*( betag11 + oo16pi2 * betag12 ) 

 
Else 
Dg1 = oo16pi2* betag11 
End If 
 
 
!-------------------- 
! g2 
!-------------------- 
 
betag21  = -5._dp*(g2p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betag22 = 0

 
Dg2 = oo16pi2*( betag21 + oo16pi2 * betag22 ) 

 
Else 
Dg2 = oo16pi2* betag21 
End If 
 
 
!-------------------- 
! g3 
!-------------------- 
 
betag31  = -7._dp*(g3p3)

 
 
If (TwoLoopRGE) Then 
betag32 = 0

 
Dg3 = oo16pi2*( betag31 + oo16pi2 * betag32 ) 

 
Else 
Dg3 = oo16pi2* betag31 
End If 
 
 
!-------------------- 
! Lam 
!-------------------- 
 
betaLam1  = 27._dp*(g1p4)/100._dp + (9*g1p2*g2p2)/10._dp + 9._dp*(g2p4)               & 
& /4._dp + 12._dp*(Lamp2) - 12._dp*(TrYdadjYdYdadjYd) - 4._dp*(TrYeadjYeYeadjYe)         & 
&  - 12._dp*(TrYuadjYuYuadjYu) - 4._dp*(yh1p4) - 8*yh1p2*yh2p2 - 4._dp*(yh2p4)           & 
&  - (9*g1p2*Lam)/5._dp - 9*g2p2*Lam + 12*TrYdadjYd*Lam + 4*TrYeadjYe*Lam +              & 
&  12*TrYuadjYu*Lam + 4*yh1p2*Lam + 4*yh2p2*Lam

 
 
If (TwoLoopRGE) Then 
betaLam2 = 0

 
DLam = oo16pi2*( betaLam1 + oo16pi2 * betaLam2 ) 

 
Else 
DLam = oo16pi2* betaLam1 
End If 
 
 
Call Chop(DLam) 

!-------------------- 
! yh2 
!-------------------- 
 
betayh21  = (-9*g1p2*yh2)/20._dp - (9*g2p2*yh2)/4._dp + 3*TrYdadjYd*yh2 +             & 
&  TrYeadjYe*yh2 + 3*TrYuadjYu*yh2 + 4*yh1p2*yh2 + 5._dp*(yh2p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betayh22 = 0

 
Dyh2 = oo16pi2*( betayh21 + oo16pi2 * betayh22 ) 

 
Else 
Dyh2 = oo16pi2* betayh21 
End If 
 
 
!-------------------- 
! Yu 
!-------------------- 
 
betaYu1  = (-17._dp*(g1p2)/20._dp - 9._dp*(g2p2)/4._dp - 8._dp*(g3p2) +               & 
&  3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu) + yh1p2 + yh2p2)*Yu -               & 
&  (3*(YuadjYdYd - YuadjYuYu))/2._dp

 
 
If (TwoLoopRGE) Then 
betaYu2 = 0

 
DYu = oo16pi2*( betaYu1 + oo16pi2 * betaYu2 ) 

 
Else 
DYu = oo16pi2* betaYu1 
End If 
 
 
Call Chop(DYu) 

!-------------------- 
! Yd 
!-------------------- 
 
betaYd1  = (3*(YdadjYdYd - YdadjYuYu))/2._dp + Yd*(-1._dp/4._dp*g1p2 - 9._dp*(g2p2)   & 
& /4._dp - 8._dp*(g3p2) + 3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu)              & 
&  + yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaYd2 = 0

 
DYd = oo16pi2*( betaYd1 + oo16pi2 * betaYd2 ) 

 
Else 
DYd = oo16pi2* betaYd1 
End If 
 
 
Call Chop(DYd) 

!-------------------- 
! Ye 
!-------------------- 
 
betaYe1  = 3._dp*(YeadjYeYe)/2._dp + Ye*(-9._dp*(g1p2)/4._dp - 9._dp*(g2p2)           & 
& /4._dp + 3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu) + yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaYe2 = 0

 
DYe = oo16pi2*( betaYe1 + oo16pi2 * betaYe2 ) 

 
Else 
DYe = oo16pi2* betaYe1 
End If 
 
 
Call Chop(DYe) 

!-------------------- 
! yh1 
!-------------------- 
 
betayh11  = (-9*g1p2*yh1)/20._dp - (9*g2p2*yh1)/4._dp + 3*TrYdadjYd*yh1 +             & 
&  TrYeadjYe*yh1 + 3*TrYuadjYu*yh1 + 5._dp*(yh1p3)/2._dp + 4*yh1*yh2p2

 
 
If (TwoLoopRGE) Then 
betayh12 = 0

 
Dyh1 = oo16pi2*( betayh11 + oo16pi2 * betayh12 ) 

 
Else 
Dyh1 = oo16pi2* betayh11 
End If 
 
 
!-------------------- 
! MS 
!-------------------- 
 
betaMS1  = 8*MPsi*yh1*yh2 + 2*MS*(yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaMS2 = 0

 
DMS = oo16pi2*( betaMS1 + oo16pi2 * betaMS2 ) 

 
Else 
DMS = oo16pi2* betaMS1 
End If 
 
 
!-------------------- 
! MPsi 
!-------------------- 
 
betaMPsi1  = (-9*g1p2*MPsi + 5*(-9*g2p2*MPsi + 4*MS*yh1*yh2 + MPsi*(yh1p2 +           & 
&  yh2p2)))/10._dp

 
 
If (TwoLoopRGE) Then 
betaMPsi2 = 0

 
DMPsi = oo16pi2*( betaMPsi1 + oo16pi2 * betaMPsi2 ) 

 
Else 
DMPsi = oo16pi2* betaMPsi1 
End If 
 
 
!-------------------- 
! m2SM 
!-------------------- 
 
betam2SM1  = (-9*g1p2*m2SM)/10._dp - (9*g2p2*m2SM)/2._dp + 6*m2SM*TrYdadjYd +         & 
&  2*m2SM*TrYeadjYe + 6*m2SM*TrYuadjYu - 4*MPsip2*yh1p2 - 4*MSp2*yh1p2 + 2*m2SM*yh1p2 -  & 
&  8*MPsi*MS*yh1*yh2 - 4*MPsip2*yh2p2 - 4*MSp2*yh2p2 + 2*m2SM*yh2p2 + 6*m2SM*Lam

 
 
If (TwoLoopRGE) Then 
betam2SM2 = 0

 
Dm2SM = oo16pi2*( betam2SM1 + oo16pi2 * betam2SM2 ) 

 
Else 
Dm2SM = oo16pi2* betam2SM1 
End If 
 
 
Call Chop(Dm2SM) 

Call ParametersToG65(Dg1,Dg2,Dg3,DLam,Dyh2,DYu,DYd,DYe,Dyh1,DMS,DMPsi,Dm2SM,f)

Iname = Iname - 1 
 
End Subroutine rge65  

Subroutine GToParameters66(g,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM)

Implicit None 
Real(dp), Intent(in) :: g(66) 
Real(dp),Intent(out) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp),Intent(out) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer i1, i2, i3, i4, SumI 
 
Iname = Iname +1 
NameOfUnit(Iname) = 'GToParameters66' 
 
g1= g(1) 
g2= g(2) 
g3= g(3) 
Lam= Cmplx(g(4),g(5),dp) 
yh2= g(6) 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Yu(i1,i2) = Cmplx( g(SumI+7), g(SumI+8), dp) 
End Do 
 End Do 
 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Yd(i1,i2) = Cmplx( g(SumI+25), g(SumI+26), dp) 
End Do 
 End Do 
 
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
Ye(i1,i2) = Cmplx( g(SumI+43), g(SumI+44), dp) 
End Do 
 End Do 
 
yh1= g(61) 
MS= g(62) 
MPsi= g(63) 
m2SM= Cmplx(g(64),g(65),dp) 
vvSM= g(66) 
Do i1=1,66 
If (g(i1).ne.g(i1)) Then 
 Write(*,*) "NaN appearing in ",NameOfUnit(Iname) 
 Write(*,*) "At position ", i1 
 Call TerminateProgram 
End if 
End do 
Iname = Iname - 1 
 
End Subroutine GToParameters66

Subroutine ParametersToG66(g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM,g)

Implicit None 
Real(dp), Intent(out) :: g(66) 
Real(dp), Intent(in) :: g1,g2,g3,yh2,yh1,MS,MPsi,vvSM

Complex(dp), Intent(in) :: Lam,Yu(3,3),Yd(3,3),Ye(3,3),m2SM

Integer i1, i2, i3, i4, SumI 
 
Iname = Iname +1 
NameOfUnit(Iname) = 'ParametersToG66' 
 
g(1) = g1  
g(2) = g2  
g(3) = g3  
g(4) = Real(Lam,dp)  
g(5) = Aimag(Lam)  
g(6) = yh2  
Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+7) = Real(Yu(i1,i2), dp) 
g(SumI+8) = Aimag(Yu(i1,i2)) 
End Do 
End Do 

Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+25) = Real(Yd(i1,i2), dp) 
g(SumI+26) = Aimag(Yd(i1,i2)) 
End Do 
End Do 

Do i1 = 1,3
Do i2 = 1,3
SumI = (i2-1) + (i1-1)*3
SumI = SumI*2 
g(SumI+43) = Real(Ye(i1,i2), dp) 
g(SumI+44) = Aimag(Ye(i1,i2)) 
End Do 
End Do 

g(61) = yh1  
g(62) = MS  
g(63) = MPsi  
g(64) = Real(m2SM,dp)  
g(65) = Aimag(m2SM)  
g(66) = vvSM  
Iname = Iname - 1 
 
End Subroutine ParametersToG66

Subroutine rge66(len, T, GY, F) 
Implicit None 
Integer, Intent(in) :: len 
Real(dp), Intent(in) :: T, GY(len) 
Real(dp), Intent(out) :: F(len) 
Integer :: i1,i2,i3,i4 
Integer :: j1,j2,j3,j4,j5,j6,j7 
Real(dp) :: q 
Real(dp) :: g1,betag11,betag12,Dg1,g2,betag21,betag22,Dg2,g3,betag31,betag32,         & 
& Dg3,yh2,betayh21,betayh22,Dyh2,yh1,betayh11,betayh12,Dyh1,MS,betaMS1,betaMS2,          & 
& DMS,MPsi,betaMPsi1,betaMPsi2,DMPsi,vvSM,betavvSM1,betavvSM2,DvvSM
Complex(dp) :: Lam,betaLam1,betaLam2,DLam,Yu(3,3),betaYu1(3,3),betaYu2(3,3)           & 
& ,DYu(3,3),adjYu(3,3),Yd(3,3),betaYd1(3,3),betaYd2(3,3),DYd(3,3),adjYd(3,3)             & 
& ,Ye(3,3),betaYe1(3,3),betaYe2(3,3),DYe(3,3),adjYe(3,3),m2SM,betam2SM1,betam2SM2,Dm2SM
Complex(dp) :: YdadjYd(3,3),YeadjYe(3,3),YuadjYu(3,3),adjYdYd(3,3),adjYeYe(3,3),adjYuYu(3,3),        & 
& YdadjYdYd(3,3),YdadjYuYu(3,3),YeadjYeYe(3,3),YuadjYdYd(3,3),YuadjYuYu(3,3),            & 
& adjYdYdadjYd(3,3),adjYeYeadjYe(3,3),adjYuYuadjYu(3,3),YdadjYdYdadjYd(3,3),             & 
& YeadjYeYeadjYe(3,3),YuadjYuYuadjYu(3,3)

Complex(dp) :: TrYdadjYd,TrYeadjYe,TrYuadjYu,TrYdadjYdYdadjYd,TrYeadjYeYeadjYe,TrYuadjYuYuadjYu

Real(dp) :: g1p2,g1p3,g1p4,g2p2,g2p3,g2p4,g3p2,g3p3,MPsip2,MSp2,yh1p2,yh1p3,yh1p4,yh2p2,          & 
& yh2p3,yh2p4

Complex(dp) :: Lamp2

Iname = Iname +1 
NameOfUnit(Iname) = 'rge66' 
 
OnlyDiagonal = .Not.GenerationMixing 
q = t 
 
Call GToParameters66(gy,g1,g2,g3,Lam,yh2,Yu,Yd,Ye,yh1,MS,MPsi,m2SM,vvSM)

Call Adjungate(Yu,adjYu)
Call Adjungate(Yd,adjYd)
Call Adjungate(Ye,adjYe)
 YdadjYd = Matmul(Yd,adjYd) 
Forall(i2=1:3)  YdadjYd(i2,i2) =  Real(YdadjYd(i2,i2),dp) 
 YeadjYe = Matmul(Ye,adjYe) 
Forall(i2=1:3)  YeadjYe(i2,i2) =  Real(YeadjYe(i2,i2),dp) 
 YuadjYu = Matmul(Yu,adjYu) 
Forall(i2=1:3)  YuadjYu(i2,i2) =  Real(YuadjYu(i2,i2),dp) 
 adjYdYd = Matmul(adjYd,Yd) 
Forall(i2=1:3)  adjYdYd(i2,i2) =  Real(adjYdYd(i2,i2),dp) 
 adjYeYe = Matmul(adjYe,Ye) 
Forall(i2=1:3)  adjYeYe(i2,i2) =  Real(adjYeYe(i2,i2),dp) 
 adjYuYu = Matmul(adjYu,Yu) 
Forall(i2=1:3)  adjYuYu(i2,i2) =  Real(adjYuYu(i2,i2),dp) 
 YdadjYdYd = Matmul(Yd,adjYdYd) 
 YdadjYuYu = Matmul(Yd,adjYuYu) 
 YeadjYeYe = Matmul(Ye,adjYeYe) 
 YuadjYdYd = Matmul(Yu,adjYdYd) 
 YuadjYuYu = Matmul(Yu,adjYuYu) 
 adjYdYdadjYd = Matmul(adjYd,YdadjYd) 
 adjYeYeadjYe = Matmul(adjYe,YeadjYe) 
 adjYuYuadjYu = Matmul(adjYu,YuadjYu) 
 YdadjYdYdadjYd = Matmul(Yd,adjYdYdadjYd) 
Forall(i2=1:3)  YdadjYdYdadjYd(i2,i2) =  Real(YdadjYdYdadjYd(i2,i2),dp) 
 YeadjYeYeadjYe = Matmul(Ye,adjYeYeadjYe) 
Forall(i2=1:3)  YeadjYeYeadjYe(i2,i2) =  Real(YeadjYeYeadjYe(i2,i2),dp) 
 YuadjYuYuadjYu = Matmul(Yu,adjYuYuadjYu) 
Forall(i2=1:3)  YuadjYuYuadjYu(i2,i2) =  Real(YuadjYuYuadjYu(i2,i2),dp) 
 TrYdadjYd = Real(cTrace(YdadjYd),dp) 
 TrYeadjYe = Real(cTrace(YeadjYe),dp) 
 TrYuadjYu = Real(cTrace(YuadjYu),dp) 
 TrYdadjYdYdadjYd = Real(cTrace(YdadjYdYdadjYd),dp) 
 TrYeadjYeYeadjYe = Real(cTrace(YeadjYeYeadjYe),dp) 
 TrYuadjYuYuadjYu = Real(cTrace(YuadjYuYuadjYu),dp) 
 g1p2 =g1**2 
 g1p3 =g1**3 
 g1p4 =g1**4 
 g2p2 =g2**2 
 g2p3 =g2**3 
 g2p4 =g2**4 
 g3p2 =g3**2 
 g3p3 =g3**3 
 MPsip2 =MPsi**2 
 MSp2 =MS**2 
 yh1p2 =yh1**2 
 yh1p3 =yh1**3 
 yh1p4 =yh1**4 
 yh2p2 =yh2**2 
 yh2p3 =yh2**3 
 yh2p4 =yh2**4 
 Lamp2 =Lam**2 


If (TwoLoopRGE) Then 
End If 
 
 
!-------------------- 
! g1 
!-------------------- 
 
betag11  = 9._dp*(g1p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betag12 = 0

 
Dg1 = oo16pi2*( betag11 + oo16pi2 * betag12 ) 

 
Else 
Dg1 = oo16pi2* betag11 
End If 
 
 
!-------------------- 
! g2 
!-------------------- 
 
betag21  = -5._dp*(g2p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betag22 = 0

 
Dg2 = oo16pi2*( betag21 + oo16pi2 * betag22 ) 

 
Else 
Dg2 = oo16pi2* betag21 
End If 
 
 
!-------------------- 
! g3 
!-------------------- 
 
betag31  = -7._dp*(g3p3)

 
 
If (TwoLoopRGE) Then 
betag32 = 0

 
Dg3 = oo16pi2*( betag31 + oo16pi2 * betag32 ) 

 
Else 
Dg3 = oo16pi2* betag31 
End If 
 
 
!-------------------- 
! Lam 
!-------------------- 
 
betaLam1  = 27._dp*(g1p4)/100._dp + (9*g1p2*g2p2)/10._dp + 9._dp*(g2p4)               & 
& /4._dp + 12._dp*(Lamp2) - 12._dp*(TrYdadjYdYdadjYd) - 4._dp*(TrYeadjYeYeadjYe)         & 
&  - 12._dp*(TrYuadjYuYuadjYu) - 4._dp*(yh1p4) - 8*yh1p2*yh2p2 - 4._dp*(yh2p4)           & 
&  - (9*g1p2*Lam)/5._dp - 9*g2p2*Lam + 12*TrYdadjYd*Lam + 4*TrYeadjYe*Lam +              & 
&  12*TrYuadjYu*Lam + 4*yh1p2*Lam + 4*yh2p2*Lam

 
 
If (TwoLoopRGE) Then 
betaLam2 = 0

 
DLam = oo16pi2*( betaLam1 + oo16pi2 * betaLam2 ) 

 
Else 
DLam = oo16pi2* betaLam1 
End If 
 
 
Call Chop(DLam) 

!-------------------- 
! yh2 
!-------------------- 
 
betayh21  = (-9*g1p2*yh2)/20._dp - (9*g2p2*yh2)/4._dp + 3*TrYdadjYd*yh2 +             & 
&  TrYeadjYe*yh2 + 3*TrYuadjYu*yh2 + 4*yh1p2*yh2 + 5._dp*(yh2p3)/2._dp

 
 
If (TwoLoopRGE) Then 
betayh22 = 0

 
Dyh2 = oo16pi2*( betayh21 + oo16pi2 * betayh22 ) 

 
Else 
Dyh2 = oo16pi2* betayh21 
End If 
 
 
!-------------------- 
! Yu 
!-------------------- 
 
betaYu1  = (-17._dp*(g1p2)/20._dp - 9._dp*(g2p2)/4._dp - 8._dp*(g3p2) +               & 
&  3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu) + yh1p2 + yh2p2)*Yu -               & 
&  (3*(YuadjYdYd - YuadjYuYu))/2._dp

 
 
If (TwoLoopRGE) Then 
betaYu2 = 0

 
DYu = oo16pi2*( betaYu1 + oo16pi2 * betaYu2 ) 

 
Else 
DYu = oo16pi2* betaYu1 
End If 
 
 
Call Chop(DYu) 

!-------------------- 
! Yd 
!-------------------- 
 
betaYd1  = (3*(YdadjYdYd - YdadjYuYu))/2._dp + Yd*(-1._dp/4._dp*g1p2 - 9._dp*(g2p2)   & 
& /4._dp - 8._dp*(g3p2) + 3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu)              & 
&  + yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaYd2 = 0

 
DYd = oo16pi2*( betaYd1 + oo16pi2 * betaYd2 ) 

 
Else 
DYd = oo16pi2* betaYd1 
End If 
 
 
Call Chop(DYd) 

!-------------------- 
! Ye 
!-------------------- 
 
betaYe1  = 3._dp*(YeadjYeYe)/2._dp + Ye*(-9._dp*(g1p2)/4._dp - 9._dp*(g2p2)           & 
& /4._dp + 3._dp*(TrYdadjYd) + TrYeadjYe + 3._dp*(TrYuadjYu) + yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaYe2 = 0

 
DYe = oo16pi2*( betaYe1 + oo16pi2 * betaYe2 ) 

 
Else 
DYe = oo16pi2* betaYe1 
End If 
 
 
Call Chop(DYe) 

!-------------------- 
! yh1 
!-------------------- 
 
betayh11  = (-9*g1p2*yh1)/20._dp - (9*g2p2*yh1)/4._dp + 3*TrYdadjYd*yh1 +             & 
&  TrYeadjYe*yh1 + 3*TrYuadjYu*yh1 + 5._dp*(yh1p3)/2._dp + 4*yh1*yh2p2

 
 
If (TwoLoopRGE) Then 
betayh12 = 0

 
Dyh1 = oo16pi2*( betayh11 + oo16pi2 * betayh12 ) 

 
Else 
Dyh1 = oo16pi2* betayh11 
End If 
 
 
!-------------------- 
! MS 
!-------------------- 
 
betaMS1  = 8*MPsi*yh1*yh2 + 2*MS*(yh1p2 + yh2p2)

 
 
If (TwoLoopRGE) Then 
betaMS2 = 0

 
DMS = oo16pi2*( betaMS1 + oo16pi2 * betaMS2 ) 

 
Else 
DMS = oo16pi2* betaMS1 
End If 
 
 
!-------------------- 
! MPsi 
!-------------------- 
 
betaMPsi1  = (-9*g1p2*MPsi + 5*(-9*g2p2*MPsi + 4*MS*yh1*yh2 + MPsi*(yh1p2 +           & 
&  yh2p2)))/10._dp

 
 
If (TwoLoopRGE) Then 
betaMPsi2 = 0

 
DMPsi = oo16pi2*( betaMPsi1 + oo16pi2 * betaMPsi2 ) 

 
Else 
DMPsi = oo16pi2* betaMPsi1 
End If 
 
 
!-------------------- 
! m2SM 
!-------------------- 
 
betam2SM1  = (-9*g1p2*m2SM)/10._dp - (9*g2p2*m2SM)/2._dp + 6*m2SM*TrYdadjYd +         & 
&  2*m2SM*TrYeadjYe + 6*m2SM*TrYuadjYu - 4*MPsip2*yh1p2 - 4*MSp2*yh1p2 + 2*m2SM*yh1p2 -  & 
&  8*MPsi*MS*yh1*yh2 - 4*MPsip2*yh2p2 - 4*MSp2*yh2p2 + 2*m2SM*yh2p2 + 6*m2SM*Lam

 
 
If (TwoLoopRGE) Then 
betam2SM2 = 0

 
Dm2SM = oo16pi2*( betam2SM1 + oo16pi2 * betam2SM2 ) 

 
Else 
Dm2SM = oo16pi2* betam2SM1 
End If 
 
 
Call Chop(Dm2SM) 

!-------------------- 
! vvSM 
!-------------------- 
 
betavvSM1  = (vvSM*(9._dp*(g1p2) + 45._dp*(g2p2) - 60._dp*(TrYdadjYd) -               & 
&  20._dp*(TrYeadjYe) - 60._dp*(TrYuadjYu) + 3*g1p2*Xi + 15*g2p2*Xi - 20._dp*(yh1p2)     & 
&  - 20._dp*(yh2p2)))/20._dp

 
 
If (TwoLoopRGE) Then 
betavvSM2 = 0

 
DvvSM = oo16pi2*( betavvSM1 + oo16pi2 * betavvSM2 ) 

 
Else 
DvvSM = oo16pi2* betavvSM1 
End If 
 
 
Call ParametersToG66(Dg1,Dg2,Dg3,DLam,Dyh2,DYu,DYd,DYe,Dyh1,DMS,DMPsi,Dm2SM,DvvSM,f)

Iname = Iname - 1 
 
End Subroutine rge66  

End Module RGEs_SingletDoubletB 
 
