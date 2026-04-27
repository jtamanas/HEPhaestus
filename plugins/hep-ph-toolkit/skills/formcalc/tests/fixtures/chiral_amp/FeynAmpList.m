(* Fixture: amplitude with chirality projectors (ChiralityProjector) *)
FeynAmpList[
  GraphID[Process -> {F[1,{1}]} -> {F[1,{1}], V[1]}],
  FeynAmp[
    GraphID[Topology == 1, Generic == 1, Classes == 1],
    PropagatorDenominator[FourMomentum[Internal, 1], 0],
    (* Axial coupling: ChiralityProjector[+1] = right-handed projector *)
    I * coupling * DiracChain[
      Spinor[FourMomentum[Outgoing, 1], ME, 1],
      ChiralityProjector[+1],
      Spinor[-FourMomentum[Outgoing, 2], ME, 1]
    ]
  ]
]
