{"schema_version" -> 1, "model" -> "ToyDiracH2", 
 "amp" -> FeynAmpList[Process -> {{F[1, {1}], FourMomentum[Incoming, 1], 
        MassFChi[1], {}}, {S[2], FourMomentum[Incoming, 2], MassPhi, {}}} -> 
      {{F[1, {1}], FourMomentum[Outgoing, 1], MassFChi[1], {}}, 
       {S[2], FourMomentum[Outgoing, 2], MassPhi, {}}}, 
    Model -> {"ToyDiracH2"}, GenericModel -> {"Lorentz"}, 
    AmplitudeLevel -> {Classes}, ExcludeParticles -> {}, 
    ExcludeFieldPoints -> {}, LastSelections -> {}][
   FeynAmp[GraphID[Topology == 1, Generic == 1, Classes == 1, Number == 1], 
    Integral[], I*mu*FermionChain[NonCommutative[
       DiracSpinor[FourMomentum[Outgoing, 1], MassFChi[1]]], 
      I*gchi*NonCommutative[ChiralityProjector[-1]] + 
       I*gchi*NonCommutative[ChiralityProjector[1]], 
      NonCommutative[DiracSpinor[FourMomentum[Incoming, 1], MassFChi[1]]]]*
     PropagatorDenominator[-FourMomentum[Incoming, 2] + 
       FourMomentum[Outgoing, 2], Mhh]]]}
