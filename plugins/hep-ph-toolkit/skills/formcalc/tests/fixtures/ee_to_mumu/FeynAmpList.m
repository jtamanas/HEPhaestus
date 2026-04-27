(* FeynAmpList.m fixture for e+ e- -> mu+ mu-  (SM, tree-level)
   This is a simplified stub for unit tests.
   The real FeynAmpList.m is produced by /feynarts generate.
*)
FeynAmpList[
  GraphID[Process -> {-F[2,{1}], F[2,{1}]} -> {-F[2,{2}], F[2,{2}]}],
  FeynAmp[
    GraphID[Topology == 1, Generic == 1, Classes == 1],
    PropagatorDenominator[FourMomentum[Internal, 1], 0],
    (* QED vertex: e+e- -> gamma -> mu+mu- *)
    -I EL^2 / (FourMomentum[Outgoing,1] + FourMomentum[Outgoing,2])^2 *
    DiracChain[Spinor[-FourMomentum[Outgoing,1], ME, 1], 6+7, Spinor[FourMomentum[Outgoing,2], ME, 1]] *
    DiracChain[Spinor[-FourMomentum[Outgoing,3], MU, 1], 6+7, Spinor[FourMomentum[Outgoing,4], MU, 1]]
  ]
]
