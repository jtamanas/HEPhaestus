{"schema_version" -> 1, "feynarts_version" -> "3.11", 
 "model" -> "TwoHdmAfix", "process" -> 
  "{F[101],F[3,{1}]}->{F[101],F[3,{1}]}", 
 "amp" -> FeynAmpList[Process -> {{F[101], FourMomentum[Incoming, 1], 
        MassFchi, {}}, {F[3, {1, Index[Colour, 2]}], FourMomentum[Incoming, 
         2], MassFu[1], {}}} -> {{F[101], FourMomentum[Outgoing, 1], 
        MassFchi, {}}, {F[3, {1, Index[Colour, 4]}], FourMomentum[Outgoing, 
         2], MassFu[1], {}}}, Model -> {"TwoHdmAfix"}, 
    GenericModel -> {"Lorentz"}, AmplitudeLevel -> {Classes}, 
    ExcludeParticles -> {}, ExcludeFieldPoints -> {}, LastSelections -> {}][
   FeynAmp[GraphID[Topology == 1, Generic == 1, Classes == 1, Number == 1], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (I*IndexSum[Conjugate[ZUL[Index[I3Gen, 7], j2]]*
            IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*
              ZUR[Index[I3Gen, 7], j1], {j1, 3}]*ZUL[1, j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFu[Index[I3Gen, 7]]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZUR[Index[I3Gen, 7], j1]]*yu2[j1, j2], 
              {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]]*
           ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 7], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSlash[FourMomentum[Incoming, 2] - 
           FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 6]]], 
       (I*IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[Index[I3Gen, 
                 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], Masshh[Index[I2Gen, 5]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassFu[Index[I3Gen, 7]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[I3Gen, 7], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External])/Pi^4], FeynAmp[GraphID[Topology == 1, Generic == 1, 
     Classes == 2, Number == 2], Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], -((IndexSum[Conjugate[ZUL[Index[I3Gen, 8], j2]]*
             IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*
              ZUR[Index[I3Gen, 8], j1], {j1, 3}]*ZUL[1, j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 6], 2])/
         Sqrt[2], NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFu[Index[I3Gen, 8]]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 7], j2]]*
             IndexSum[Conjugate[ZUR[Index[I3Gen, 8], j1]]*yu2[j1, j2], 
              {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]]*
           ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 7], j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 8], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSlash[FourMomentum[Incoming, 2] - 
           FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 7]]], 
       -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[
                ZUR[Index[I3Gen, 7], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 7], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 6], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassAh[Index[I3Gen, 6]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[Index[I3Gen, 7]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassFu[Index[I3Gen, 8]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[I3Gen, 8], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External])/Pi^4], FeynAmp[GraphID[Topology == 1, Generic == 1, 
     Classes == 3, Number == 3], Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (-I)*IndexSum[IndexSum[Conjugate[yd1[j1, j2]]*
             ZDR[Index[I3Gen, 7], j1], {j1, 3}]*ZUL[1, j2], {j2, 3}]*
         NonCommutative[ChiralityProjector[1]]*ZP[Index[I2Gen, 5], 1] - 
        I*IndexSum[Conjugate[ZDL[Index[I3Gen, 7], j2]]*
           IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
         NonCommutative[ChiralityProjector[-1]]*ZP[Index[I2Gen, 5], 2], 
       NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFd[Index[I3Gen, 7]]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZDL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZDR[Index[I3Gen, 7], j1]]*yd1[j1, j2], 
              {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]]*
           ZA[Index[I3Gen, 5], 1])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yd1[j1, j2]]*ZDR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZDL[Index[I3Gen, 7], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 1])/
         Sqrt[2], NonCommutative[DiracSlash[FourMomentum[Incoming, 2] - 
           FourMomentum[Internal, 1]] + MassFd[Index[I3Gen, 6]]], 
       (-I)*Conjugate[ZP[Index[I2Gen, 5], 1]]*IndexSum[Conjugate[ZUL[1, j2]]*
           IndexSum[Conjugate[ZDR[Index[I3Gen, 6], j1]]*yd1[j1, j2], 
            {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]] - 
        I*Conjugate[ZP[Index[I2Gen, 5], 2]]*IndexSum[
          IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
           ZDL[Index[I3Gen, 6], j2], {j2, 3}]*NonCommutative[
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], 
        MassHm[Index[I2Gen, 5]]], PropagatorDenominator[
        -FourMomentum[Incoming, 2] + FourMomentum[Internal, 1], 
        MassFd[Index[I3Gen, 6]]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], 
        MassFd[Index[I3Gen, 7]]]]*PropagatorDenominator[
       -FourMomentum[Incoming, 2] + FourMomentum[Outgoing, 2], 
       MassAh[Index[I3Gen, 5]]]*SumOver[Index[I2Gen, 5], 2]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 2, Classes == 1, Number == 4], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
            IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 6], 2])/
         Sqrt[2] + (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZH[Index[I2Gen, 6], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 6]]], 
       (I*IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[Index[I3Gen, 
                 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], Masshh[Index[I2Gen, 5]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], Masshh[Index[I2Gen, 6]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I2Gen, 6], 2]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*((-I)*lamP*ZA[Index[I3Gen, 5], 3]*ZH[Index[I2Gen, 5], 2]*
        ZH[Index[I2Gen, 6], 1] - I*lamP*ZA[Index[I3Gen, 5], 3]*
        ZH[Index[I2Gen, 5], 1]*ZH[Index[I2Gen, 6], 2]))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 2, Classes == 2, Number == 5], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 2])/
          Sqrt[2]) + (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZA[Index[I3Gen, 7], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 6]]], 
       (I*IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[Index[I3Gen, 
                 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], Masshh[Index[I2Gen, 5]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 7]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[I3Gen, 7], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*((-I)*lam1*vd*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 1] - I*lam5r*vu*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 1] - 
       I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 1] - 
       I*lam4*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 1] + I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 1] - 
       (2*I)*lam7*vd*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 7], 3]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam4*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 2] + I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 2] - I*lam5r*vd*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 2] - 
       I*lam2*vu*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 2] - (2*I)*lam8*vu*ZA[Index[I3Gen, 5], 3]*
        ZA[Index[I3Gen, 7], 3]*ZH[Index[I2Gen, 5], 2]))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 2, Classes == 3, Number == 6], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
            IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZH[Index[I2Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 6]]], 
       -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[
                ZUR[Index[I3Gen, 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 7], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassAh[Index[I3Gen, 7]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], Masshh[Index[I2Gen, 5]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[I3Gen, 7], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*((-I)*lam1*vd*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 1] - I*lam5r*vu*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 1] - 
       I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 1] - 
       I*lam4*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 1] + I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 1] - 
       (2*I)*lam7*vd*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 7], 3]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam4*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 2] + I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 1]*
        ZH[Index[I2Gen, 5], 2] - I*lam5r*vd*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 2]*ZH[Index[I2Gen, 5], 2] - 
       I*lam2*vu*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 2]*
        ZH[Index[I2Gen, 5], 2] - (2*I)*lam8*vu*ZA[Index[I3Gen, 5], 3]*
        ZA[Index[I3Gen, 7], 3]*ZH[Index[I2Gen, 5], 2]))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 2, Classes == 4, Number == 7], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 8], 2])/
          Sqrt[2]) + (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZA[Index[I3Gen, 8], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFu[Index[I3Gen, 6]]], 
       -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[
                ZUR[Index[I3Gen, 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 7], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassAh[Index[I3Gen, 7]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 8]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[I3Gen, 8], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*((-I)*lamP*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 7], 2]*
        ZA[Index[I3Gen, 8], 1] - I*lamP*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 7], 3]*ZA[Index[I3Gen, 8], 1] - 
       I*lamP*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 7], 1]*
        ZA[Index[I3Gen, 8], 2] - I*lamP*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 3]*ZA[Index[I3Gen, 8], 2] - 
       I*lamP*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 7], 1]*
        ZA[Index[I3Gen, 8], 3] - I*lamP*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 7], 2]*ZA[Index[I3Gen, 8], 3]))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 2, Classes == 5, Number == 8], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (-I)*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
         IndexSum[IndexSum[Conjugate[yd1[j1, j2]]*ZDR[Index[I3Gen, 6], j1], 
            {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
           1]]*ZP[Index[I2Gen, 6], 1] - I*IndexDelta[Index[Colour, 2], 
          Index[Colour, 4]]*IndexSum[Conjugate[ZDL[Index[I3Gen, 6], j2]]*
           IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
         NonCommutative[ChiralityProjector[-1]]*ZP[Index[I2Gen, 6], 2], 
       NonCommutative[DiracSlash[FourMomentum[Internal, 1]] + 
         MassFd[Index[I3Gen, 6]]], (-I)*Conjugate[ZP[Index[I2Gen, 5], 1]]*
         IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[
            Conjugate[ZDR[Index[I3Gen, 6], j1]]*yd1[j1, j2], {j1, 3}], 
          {j2, 3}]*NonCommutative[ChiralityProjector[-1]] - 
        I*Conjugate[ZP[Index[I2Gen, 5], 2]]*IndexSum[
          IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
           ZDL[Index[I3Gen, 6], j2], {j2, 3}]*NonCommutative[
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFd[Index[I3Gen, 6]]], PropagatorDenominator[
        -FourMomentum[Incoming, 2] + FourMomentum[Internal, 1], 
        MassHm[Index[I2Gen, 5]]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], 
        MassHm[Index[I2Gen, 6]]]]*PropagatorDenominator[
       -FourMomentum[Incoming, 2] + FourMomentum[Outgoing, 2], 
       MassAh[Index[I3Gen, 5]]]*SumOver[Index[I2Gen, 5], 2]*
      SumOver[Index[I2Gen, 6], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External]*
      (-1/2*(lam4*vu*Conjugate[ZP[Index[I2Gen, 6], 2]]*ZA[Index[I3Gen, 5], 1]*
         ZP[Index[I2Gen, 5], 1]) + 
       (lam5r*vu*Conjugate[ZP[Index[I2Gen, 6], 2]]*ZA[Index[I3Gen, 5], 1]*
         ZP[Index[I2Gen, 5], 1])/2 + 
       (lam4*vd*Conjugate[ZP[Index[I2Gen, 6], 2]]*ZA[Index[I3Gen, 5], 2]*
         ZP[Index[I2Gen, 5], 1])/2 - 
       (lam5r*vd*Conjugate[ZP[Index[I2Gen, 6], 2]]*ZA[Index[I3Gen, 5], 2]*
         ZP[Index[I2Gen, 5], 1])/2 - I*lamP*Conjugate[ZP[Index[I2Gen, 6], 2]]*
        ZA[Index[I3Gen, 5], 3]*ZP[Index[I2Gen, 5], 1] + 
       (lam4*vu*Conjugate[ZP[Index[I2Gen, 6], 1]]*ZA[Index[I3Gen, 5], 1]*
         ZP[Index[I2Gen, 5], 2])/2 - 
       (lam5r*vu*Conjugate[ZP[Index[I2Gen, 6], 1]]*ZA[Index[I3Gen, 5], 1]*
         ZP[Index[I2Gen, 5], 2])/2 - 
       (lam4*vd*Conjugate[ZP[Index[I2Gen, 6], 1]]*ZA[Index[I3Gen, 5], 2]*
         ZP[Index[I2Gen, 5], 2])/2 + 
       (lam5r*vd*Conjugate[ZP[Index[I2Gen, 6], 1]]*ZA[Index[I3Gen, 5], 2]*
         ZP[Index[I2Gen, 5], 2])/2 - I*lamP*Conjugate[ZP[Index[I2Gen, 6], 1]]*
        ZA[Index[I3Gen, 5], 3]*ZP[Index[I2Gen, 5], 2]))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 3, Classes == 1, Number == 9], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], ((-1/6*I)*CTW*g1 - (I/2)*g2*STW)*
         NonCommutative[DiracMatrix[Index[Lorentz, 2]], ChiralityProjector[
           -1]] - ((2*I)/3)*CTW*g1*NonCommutative[DiracMatrix[
           Index[Lorentz, 2]], ChiralityProjector[1]], 
       NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFu[1]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*yu2[
                j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[
             -1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Incoming, 2] - FourMomentum[Internal, 1]] + 
         MassFu[1]], ((-1/6*I)*CTW*g1 - (I/2)*g2*STW)*NonCommutative[
          DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[-1]] - 
        ((2*I)/3)*CTW*g1*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], 0], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[1]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], MassFu[1]]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 3, Classes == 2, Number == 10], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], ((-1/2*I)*CTW*g2 + (I/6)*g1*STW)*
         NonCommutative[DiracMatrix[Index[Lorentz, 2]], ChiralityProjector[
           -1]] + ((2*I)/3)*g1*STW*NonCommutative[DiracMatrix[
           Index[Lorentz, 2]], ChiralityProjector[1]], 
       NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFu[1]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*yu2[
                j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[
             -1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Incoming, 2] - FourMomentum[Internal, 1]] + 
         MassFu[1]], ((-1/2*I)*CTW*g2 + (I/6)*g1*STW)*NonCommutative[
          DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[-1]] + 
        ((2*I)/3)*g1*STW*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], MassVZ], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[1]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], MassFu[1]]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 3, Classes == 3, Number == 11], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], ((-I)*g2*IndexSum[Conjugate[ZDL[Index[I3Gen, 7], j1]]*
           ZUL[1, j1], {j1, 3}]*NonCommutative[DiracMatrix[
           Index[Lorentz, 2]], ChiralityProjector[-1]])/Sqrt[2], 
       NonCommutative[DiracSlash[-FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 2]] + MassFd[Index[I3Gen, 7]]], 
       -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZDL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZDR[Index[I3Gen, 7], j1]]*yd1[j1, j2], 
              {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]]*
           ZA[Index[I3Gen, 5], 1])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yd1[j1, j2]]*ZDR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZDL[Index[I3Gen, 7], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 1])/
         Sqrt[2], NonCommutative[DiracSlash[FourMomentum[Incoming, 2] - 
           FourMomentum[Internal, 1]] + MassFd[Index[I3Gen, 6]]], 
       ((-I)*g2*IndexSum[Conjugate[ZUL[1, j1]]*ZDL[Index[I3Gen, 6], j1], 
          {j1, 3}]*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[-1]])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 
        MassVWp], PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFd[Index[I3Gen, 6]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassFd[Index[I3Gen, 7]]]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 3, Classes == 4, Number == 12], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (-I)*g3*NonCommutative[DiracMatrix[Index[Lorentz, 2]], 
          ChiralityProjector[-1]]*SUNT[Index[Gluon, 5], Index[Colour, 4], 
          Index[Colour, 5]] - I*g3*NonCommutative[DiracMatrix[
           Index[Lorentz, 2]], ChiralityProjector[1]]*SUNT[Index[Gluon, 5], 
          Index[Colour, 4], Index[Colour, 5]], NonCommutative[
        DiracSlash[-FourMomentum[Internal, 1] + FourMomentum[Outgoing, 2]] + 
         MassFu[1]], -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[
              Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Incoming, 2] - FourMomentum[Internal, 1]] + 
         MassFu[1]], (-I)*g3*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[-1]]*SUNT[Index[Gluon, 5], Index[Colour, 5], 
          Index[Colour, 2]] - I*g3*NonCommutative[DiracMatrix[
           Index[Lorentz, 1]], ChiralityProjector[1]]*SUNT[Index[Gluon, 5], 
          Index[Colour, 5], Index[Colour, 2]], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 0], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[1]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], MassFu[1]]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[Colour, 5], 3]*SumOver[Index[Gluon, 5], 8]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 4, Classes == 1, Number == 13], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], ((-1/2*I)*CTW*g2*IndexDelta[Index[Colour, 2], 
            Index[Colour, 4]] + (I/6)*g1*STW*IndexDelta[Index[Colour, 2], 
            Index[Colour, 4]])*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[-1]] + ((2*I)/3)*g1*STW*
         IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
         NonCommutative[DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[
           1]], NonCommutative[DiracSlash[FourMomentum[Internal, 1]] + 
         MassFu[1]], (I*IndexSum[Conjugate[ZUL[1, j2]]*
            IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
          NonCommutative[ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/
         Sqrt[2] + (I*IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZH[Index[I2Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFu[1]], PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], Masshh[Index[I2Gen, 5]]], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassVZ]]*
      FourVector[-2*FourMomentum[Incoming, 2] + FourMomentum[Internal, 1] + 
        FourMomentum[Outgoing, 2], Index[Lorentz, 2]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*(-1/2*(CTW*g2*ZA[Index[I3Gen, 5], 1]*ZH[Index[I2Gen, 5], 
          1]) - (g1*STW*ZA[Index[I3Gen, 5], 1]*ZH[Index[I2Gen, 5], 1])/2 - 
       (CTW*g2*ZA[Index[I3Gen, 5], 2]*ZH[Index[I2Gen, 5], 2])/2 - 
       (g1*STW*ZA[Index[I3Gen, 5], 2]*ZH[Index[I2Gen, 5], 2])/2))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 4, Classes == 2, Number == 14], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], ((-I)*g2*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
         IndexSum[Conjugate[ZDL[Index[I3Gen, 6], j1]]*ZUL[1, j1], {j1, 3}]*
         NonCommutative[DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[
           -1]])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFd[Index[I3Gen, 6]]], 
       (-I)*Conjugate[ZP[Index[I2Gen, 5], 1]]*IndexSum[Conjugate[ZUL[1, j2]]*
           IndexSum[Conjugate[ZDR[Index[I3Gen, 6], j1]]*yd1[j1, j2], 
            {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[-1]] - 
        I*Conjugate[ZP[Index[I2Gen, 5], 2]]*IndexSum[
          IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
           ZDL[Index[I3Gen, 6], j2], {j2, 3}]*NonCommutative[
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFd[Index[I3Gen, 6]]], PropagatorDenominator[
        -FourMomentum[Incoming, 2] + FourMomentum[Internal, 1], 
        MassHm[Index[I2Gen, 5]]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], MassVWp]]*
      FourVector[-2*FourMomentum[Incoming, 2] + FourMomentum[Internal, 1] + 
        FourMomentum[Outgoing, 2], Index[Lorentz, 2]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External]*
      ((g2*ZA[Index[I3Gen, 5], 1]*ZP[Index[I2Gen, 5], 1])/2 + 
       (g2*ZA[Index[I3Gen, 5], 2]*ZP[Index[I2Gen, 5], 2])/2))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 5, Classes == 1, Number == 15], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*
              yu2[j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[
           ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/Sqrt[2] + 
        (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZH[Index[I2Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Internal, 1]] + MassFu[1]], 
       ((-1/2*I)*CTW*g2 + (I/6)*g1*STW)*NonCommutative[
          DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[-1]] + 
        ((2*I)/3)*g1*STW*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[1]], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 2], MassFu[1]]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], MassFu[1]], 
       PropagatorDenominator[-FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassVZ], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], 
        Masshh[Index[I2Gen, 5]]]]*FourVector[-FourMomentum[Incoming, 2] - 
        FourMomentum[Internal, 1] + 2*FourMomentum[Outgoing, 2], 
       Index[Lorentz, 2]]*MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[Colour, 2], 3, External]*SumOver[Index[Colour, 4], 3, 
       External]*(-1/2*(CTW*g2*ZA[Index[I3Gen, 5], 1]*ZH[Index[I2Gen, 5], 
          1]) - (g1*STW*ZA[Index[I3Gen, 5], 1]*ZH[Index[I2Gen, 5], 1])/2 - 
       (CTW*g2*ZA[Index[I3Gen, 5], 2]*ZH[Index[I2Gen, 5], 2])/2 - 
       (g1*STW*ZA[Index[I3Gen, 5], 2]*ZH[Index[I2Gen, 5], 2])/2))/Pi^4], 
   FeynAmp[GraphID[Topology == 1, Generic == 5, Classes == 2, Number == 16], 
    Integral[FourMomentum[Internal, 1]], 
    ((-1/16*I)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 5], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], (-I)*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
         IndexSum[IndexSum[Conjugate[yd1[j1, j2]]*ZDR[Index[I3Gen, 6], j1], 
            {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
           1]]*ZP[Index[I2Gen, 5], 1] - I*IndexDelta[Index[Colour, 2], 
          Index[Colour, 4]]*IndexSum[Conjugate[ZDL[Index[I3Gen, 6], j2]]*
           IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
         NonCommutative[ChiralityProjector[-1]]*ZP[Index[I2Gen, 5], 2], 
       NonCommutative[DiracSlash[FourMomentum[Internal, 1]] + 
         MassFd[Index[I3Gen, 6]]], 
       ((-I)*g2*IndexSum[Conjugate[ZUL[1, j1]]*ZDL[Index[I3Gen, 6], j1], 
          {j1, 3}]*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
          ChiralityProjector[-1]])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFd[Index[I3Gen, 6]]], PropagatorDenominator[
        -FourMomentum[Incoming, 2] + FourMomentum[Internal, 1], MassVWp], 
       PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 2], MassHm[Index[I2Gen, 5]]]]*
      FourVector[-FourMomentum[Incoming, 2] - FourMomentum[Internal, 1] + 
        2*FourMomentum[Outgoing, 2], Index[Lorentz, 2]]*
      MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External]*
      ((g2*Conjugate[ZP[Index[I2Gen, 5], 1]]*ZA[Index[I3Gen, 5], 1])/2 + 
       (g2*Conjugate[ZP[Index[I2Gen, 5], 2]]*ZA[Index[I3Gen, 5], 2])/2))/
     Pi^4], FeynAmp[GraphID[Topology == 2, Generic == 1, Classes == 1, 
     Number == 17], Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          2], MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*yu2[
                j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[
             -1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 1], 
         MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 6], 3], NonCommutative[MassFchi + 
         DiracSlash[-FourMomentum[Internal, 1] + FourMomentum[Outgoing, 1]]], 
       gchi*Conjugate[pchiR]*NonCommutative[ChiralityProjector[-1]]*
         ZA[Index[I3Gen, 5], 3] - gchi*pchiR*NonCommutative[
          ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 3], 
       NonCommutative[MassFchi + DiracSlash[-FourMomentum[Incoming, 2] - 
           FourMomentum[Internal, 1] + FourMomentum[Outgoing, 1] + 
           FourMomentum[Outgoing, 2]]], gchi*Conjugate[pchiR]*
         NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 6], 3], NonCommutative[DiracSpinor[
         FourMomentum[Incoming, 1], MassFchi]]]*FeynAmpDenominator[
       PropagatorDenominator[FourMomentum[Internal, 1], 
        MassAh[Index[I3Gen, 6]]], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1], MassFchi], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1] - 
         FourMomentum[Outgoing, 2], MassFchi]]*PropagatorDenominator[
       FourMomentum[Incoming, 2] - FourMomentum[Outgoing, 2], 
       MassAh[Index[I3Gen, 5]]]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 2, Generic == 2, Classes == 1, Number == 18], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          2], MassFu[1]]], (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*
              yu2[j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[
           ChiralityProjector[-1]]*ZH[Index[I2Gen, 5], 2])/Sqrt[2] + 
        (I*IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZH[Index[I2Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 1], 
         MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 6], 3], NonCommutative[MassFchi + 
         DiracSlash[FourMomentum[Internal, 1]]], 
       gchi*Conjugate[pchiR]*NonCommutative[ChiralityProjector[-1]]*
         ZA[Index[I3Gen, 5], 3] - gchi*pchiR*NonCommutative[
          ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 3], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFchi]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFchi], PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 1], MassAh[Index[I3Gen, 6]]], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1] - 
         FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]]*
      PropagatorDenominator[FourMomentum[Incoming, 2] - 
        FourMomentum[Outgoing, 2], Masshh[Index[I2Gen, 5]]]*
      SumOver[Index[I2Gen, 5], 2]*SumOver[Index[I3Gen, 5], 3]*
      SumOver[Index[I3Gen, 6], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External]*
      ((-I)*lam1*vd*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 6], 1]*
        ZH[Index[I2Gen, 5], 1] - I*lam5r*vu*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 6], 1]*ZH[Index[I2Gen, 5], 1] - 
       I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 6], 2]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 6], 2]*ZH[Index[I2Gen, 5], 1] - 
       I*lam4*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 6], 2]*
        ZH[Index[I2Gen, 5], 1] + I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 6], 2]*ZH[Index[I2Gen, 5], 1] - 
       (2*I)*lam7*vd*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 6], 3]*
        ZH[Index[I2Gen, 5], 1] - I*lam3*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 6], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam4*vu*ZA[Index[I3Gen, 5], 1]*ZA[Index[I3Gen, 6], 1]*
        ZH[Index[I2Gen, 5], 2] + I*lam5r*vu*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 6], 1]*ZH[Index[I2Gen, 5], 2] - 
       I*lam5r*vd*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 6], 1]*
        ZH[Index[I2Gen, 5], 2] - I*lam5r*vd*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 6], 2]*ZH[Index[I2Gen, 5], 2] - 
       I*lam2*vu*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 6], 2]*
        ZH[Index[I2Gen, 5], 2] - (2*I)*lam8*vu*ZA[Index[I3Gen, 5], 3]*
        ZA[Index[I3Gen, 6], 3]*ZH[Index[I2Gen, 5], 2]))/Pi^4], 
   FeynAmp[GraphID[Topology == 2, Generic == 2, Classes == 2, Number == 19], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          2], MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[ZUR[1, j1]]*yu2[
                j1, j2], {j1, 3}], {j2, 3}]*NonCommutative[ChiralityProjector[
             -1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2]) + 
        (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], {j1, 3}]*
            ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[1]]*
          ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSpinor[FourMomentum[Incoming, 2], MassFu[1]]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 1], 
         MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 7], 3], NonCommutative[MassFchi + 
         DiracSlash[FourMomentum[Internal, 1]]], 
       gchi*Conjugate[pchiR]*NonCommutative[ChiralityProjector[-1]]*
         ZA[Index[I3Gen, 6], 3] - gchi*pchiR*NonCommutative[
          ChiralityProjector[1]]*ZA[Index[I3Gen, 6], 3], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFchi]]]*
      FeynAmpDenominator[PropagatorDenominator[FourMomentum[Internal, 1], 
        MassFchi], PropagatorDenominator[FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 1], MassAh[Index[I3Gen, 7]]], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1] - 
         FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 6]]]]*
      PropagatorDenominator[FourMomentum[Incoming, 2] - 
        FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External]*
      ((-I)*lamP*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 6], 2]*
        ZA[Index[I3Gen, 7], 1] - I*lamP*ZA[Index[I3Gen, 5], 2]*
        ZA[Index[I3Gen, 6], 3]*ZA[Index[I3Gen, 7], 1] - 
       I*lamP*ZA[Index[I3Gen, 5], 3]*ZA[Index[I3Gen, 6], 1]*
        ZA[Index[I3Gen, 7], 2] - I*lamP*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 6], 3]*ZA[Index[I3Gen, 7], 2] - 
       I*lamP*ZA[Index[I3Gen, 5], 2]*ZA[Index[I3Gen, 6], 1]*
        ZA[Index[I3Gen, 7], 3] - I*lamP*ZA[Index[I3Gen, 5], 1]*
        ZA[Index[I3Gen, 6], 2]*ZA[Index[I3Gen, 7], 3]))/Pi^4], 
   FeynAmp[GraphID[Topology == 3, Generic == 1, Classes == 1, Number == 20], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 7], 3], NonCommutative[MassFchi + 
         DiracSlash[-FourMomentum[Incoming, 2] - FourMomentum[Internal, 1] + 
           FourMomentum[Outgoing, 1] + FourMomentum[Outgoing, 2]]], 
       gchi*Conjugate[pchiR]*NonCommutative[ChiralityProjector[-1]]*
         ZA[Index[I3Gen, 5], 3] - gchi*pchiR*NonCommutative[
          ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 3], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 6], j2]]*
             IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 7], 2])/
          Sqrt[2]) + (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 6], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZA[Index[I3Gen, 7], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Incoming, 2] + FourMomentum[Internal, 1]] + 
         MassFu[Index[I3Gen, 6]]], 
       -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[
                ZUR[Index[I3Gen, 6], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 6], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassAh[Index[I3Gen, 5]]], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1], MassFu[Index[I3Gen, 6]]], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1] - FourMomentum[Outgoing, 2], 
        MassAh[Index[I3Gen, 7]]], PropagatorDenominator[
        FourMomentum[Incoming, 2] + FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 1] - FourMomentum[Outgoing, 2], MassFchi]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4], 
   FeynAmp[GraphID[Topology == 4, Generic == 1, Classes == 1, Number == 21], 
    Integral[FourMomentum[Internal, 1]], 
    ((I/16)*FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 
          1], MassFchi]], gchi*Conjugate[pchiR]*NonCommutative[
          ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 3] - 
        gchi*pchiR*NonCommutative[ChiralityProjector[1]]*
         ZA[Index[I3Gen, 6], 3], NonCommutative[MassFchi + 
         DiracSlash[FourMomentum[Internal, 1]]], 
       gchi*Conjugate[pchiR]*NonCommutative[ChiralityProjector[-1]]*
         ZA[Index[I3Gen, 5], 3] - gchi*pchiR*NonCommutative[
          ChiralityProjector[1]]*ZA[Index[I3Gen, 5], 3], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFchi]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFu[1]]], -((IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
           IndexSum[Conjugate[ZUL[Index[I3Gen, 7], j2]]*
             IndexSum[Conjugate[ZUR[1, j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 5], 2])/
          Sqrt[2]) + (IndexDelta[Index[Colour, 2], Index[Colour, 4]]*
          IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[Index[I3Gen, 7], j1], 
             {j1, 3}]*ZUL[1, j2], {j2, 3}]*NonCommutative[ChiralityProjector[
            1]]*ZA[Index[I3Gen, 5], 2])/Sqrt[2], NonCommutative[
        DiracSlash[FourMomentum[Incoming, 2] + FourMomentum[Internal, 1] - 
           FourMomentum[Outgoing, 1]] + MassFu[Index[I3Gen, 7]]], 
       -((IndexSum[Conjugate[ZUL[1, j2]]*IndexSum[Conjugate[
                ZUR[Index[I3Gen, 7], j1]]*yu2[j1, j2], {j1, 3}], {j2, 3}]*
           NonCommutative[ChiralityProjector[-1]]*ZA[Index[I3Gen, 6], 2])/
          Sqrt[2]) + (IndexSum[IndexSum[Conjugate[yu2[j1, j2]]*ZUR[1, j1], 
             {j1, 3}]*ZUL[Index[I3Gen, 7], j2], {j2, 3}]*
          NonCommutative[ChiralityProjector[1]]*ZA[Index[I3Gen, 6], 2])/
         Sqrt[2], NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], 
         MassFu[1]]]]*FeynAmpDenominator[PropagatorDenominator[
        FourMomentum[Internal, 1], MassFchi], PropagatorDenominator[
        FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1], 
        MassAh[Index[I3Gen, 6]]], PropagatorDenominator[
        FourMomentum[Incoming, 2] + FourMomentum[Internal, 1] - 
         FourMomentum[Outgoing, 1], MassFu[Index[I3Gen, 7]]], 
       PropagatorDenominator[FourMomentum[Incoming, 2] + 
         FourMomentum[Internal, 1] - FourMomentum[Outgoing, 1] - 
         FourMomentum[Outgoing, 2], MassAh[Index[I3Gen, 5]]]]*
      SumOver[Index[I3Gen, 5], 3]*SumOver[Index[I3Gen, 6], 3]*
      SumOver[Index[I3Gen, 7], 3]*SumOver[Index[Colour, 2], 3, External]*
      SumOver[Index[Colour, 4], 3, External])/Pi^4]]}
