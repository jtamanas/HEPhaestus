(* Fixture: amplitude with NO chirality projectors or gamma5 *)
FeynAmpList[
  GraphID[Process -> {-F[2,{1}], F[2,{1}]} -> {-F[2,{2}], F[2,{2}]}],
  FeynAmp[
    GraphID[Topology == 1, Generic == 1, Classes == 1],
    PropagatorDenominator[FourMomentum[Internal, 1], 0],
    (* Pure vector coupling — no chirality *)
    -I EL^2 / (FourMomentum[Outgoing,1] + FourMomentum[Outgoing,2])^2 *
    DiracChain[Spinor[p1, ME, 1], GS[k], Spinor[p2, ME, 1]] *
    DiracChain[Spinor[p3, MU, 1], GS[k], Spinor[p4, MU, 1]]
  ]
]
