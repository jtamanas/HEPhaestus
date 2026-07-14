{"schema_version" -> 1, "model" -> "ToyDiracV", 
 "amp" -> FeynAmpList[Process -> {{F[1, {1}], FourMomentum[Incoming, 1], 
        MassFChi[1], {}}, {F[2, {1}], FourMomentum[Incoming, 2], MassFd[1], 
        {}}} -> {{F[1, {1}], FourMomentum[Outgoing, 1], MassFChi[1], {}}, 
       {F[2, {1}], FourMomentum[Outgoing, 2], MassFd[1], {}}}, 
    Model -> {"ToyDiracV"}, GenericModel -> {"Lorentz"}, 
    AmplitudeLevel -> {Classes}, ExcludeParticles -> {}, 
    ExcludeFieldPoints -> {}, LastSelections -> {}][
   FeynAmp[GraphID[Topology == 1, Generic == 1, Classes == 1, Number == 1], 
    Integral[], FermionChain[NonCommutative[DiracSpinor[
        FourMomentum[Outgoing, 1], MassFChi[1]]], 
      I*gchi*NonCommutative[DiracMatrix[Index[Lorentz, 1]], 
         ChiralityProjector[-1]] + I*gchi*NonCommutative[
         DiracMatrix[Index[Lorentz, 1]], ChiralityProjector[1]], 
      NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFChi[1]]]]*
     FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
        MassFd[1]]], I*gq*NonCommutative[DiracMatrix[Index[Lorentz, 2]], 
         ChiralityProjector[-1]] + I*gq*NonCommutative[
         DiracMatrix[Index[Lorentz, 2]], ChiralityProjector[1]], 
      NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], MassFd[1]]]]*
     MetricTensor[Index[Lorentz, 1], Index[Lorentz, 2]]*
     PropagatorDenominator[-FourMomentum[Incoming, 2] + 
       FourMomentum[Outgoing, 2], MV]]]}
