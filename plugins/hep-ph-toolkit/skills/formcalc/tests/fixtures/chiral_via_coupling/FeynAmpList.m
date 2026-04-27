(* Fixture: amplitude with chiral coupling via Mat[DiracChain[6|7, ...]] *)
FeynAmpList[
  GraphID[Process -> {F[1,{1}]} -> {F[1,{1}], V[1]}],
  FeynAmp[
    GraphID[Topology == 1, Generic == 1, Classes == 1],
    PropagatorDenominator[FourMomentum[Internal, 1], 0],
    (* Axial coupling matrix entry *)
    Mat[DiracChain[6, FermionChain1]] * someExpression
  ]
]
