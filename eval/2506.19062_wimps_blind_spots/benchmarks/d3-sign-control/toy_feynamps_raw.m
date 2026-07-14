{"schema_version" -> 1, "model" -> "ToyDiracH", 
 "amp" -> FeynAmpList[Process -> {{F[1, {1}], FourMomentum[Incoming, 1], 
        MassFChi[1], {}}, {F[2, {1}], FourMomentum[Incoming, 2], MassFd[1], 
        {}}} -> {{F[1, {1}], FourMomentum[Outgoing, 1], MassFChi[1], {}}, 
       {F[2, {1}], FourMomentum[Outgoing, 2], MassFd[1], {}}}, 
    Model -> {"ToyDiracH"}, GenericModel -> {"Lorentz"}, 
    AmplitudeLevel -> {Classes}, ExcludeParticles -> {}, 
    ExcludeFieldPoints -> {}, LastSelections -> {}][
   FeynAmp[GraphID[Topology == 1, Generic == 1, Classes == 1, Number == 1], 
    Integral[], -(FermionChain[NonCommutative[DiracSpinor[
         FourMomentum[Outgoing, 1], MassFChi[1]]], 
       I*gchi*NonCommutative[ChiralityProjector[-1]] + 
        I*gchi*NonCommutative[ChiralityProjector[1]], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFChi[1]]]]*
      FermionChain[NonCommutative[DiracSpinor[FourMomentum[Outgoing, 2], 
         MassFd[1]]], I*gq*NonCommutative[ChiralityProjector[-1]] + 
        I*gq*NonCommutative[ChiralityProjector[1]], 
       NonCommutative[DiracSpinor[FourMomentum[Incoming, 2], MassFd[1]]]]*
      PropagatorDenominator[-FourMomentum[Incoming, 2] + 
        FourMomentum[Outgoing, 2], Mhh])]]}
