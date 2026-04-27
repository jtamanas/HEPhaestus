#!/usr/bin/env wolframscript
(* gamma5_static_check.wls — exact γ₅ / chirality projector detection.
   Usage: wolframscript -script gamma5_static_check.wls <FeynAmpList.m>
   Exit 0: no γ₅ / chirality projectors found (safe to proceed without --gamma5).
   Exit 1: γ₅ / chirality projectors found (--gamma5 required).
   Exit 2: error (file not found, etc.).
*)
Module[{file, held, chiralHits, couplingAxialHits, hasChiral},
  file = If[Length[$ScriptCommandLine] >= 2,
    $ScriptCommandLine[[2]],
    ""
  ];

  If[file === "" || !FileExistsQ[file],
    Print["gamma5_static_check: file not found: " <> ToString[file]];
    Exit[2]
  ];

  (* Read the amplitude list, holding evaluation *)
  held = Quiet[
    Check[
      Import[file, "Package"],
      $Failed
    ]
  ];
  If[held === $Failed,
    (* Fallback: read as raw expression with Hold *)
    held = Quiet[
      Check[
        ToExpression[ReadString[file], InputForm, Hold],
        $Failed
      ]
    ]
  ];
  If[held === $Failed,
    Print["gamma5_static_check: failed to read " <> file];
    Exit[2]
  ];

  (* Exact algorithm per plan §1.3 *)
  chiralHits = Cases[
    held,
    (ChiralityProjector | gamma5 |
      _Symbol?(Function[s, Context[s] === "System`" && (s === 6 || s === 7)])),
    Infinity
  ];

  couplingAxialHits = Cases[
    held,
    Mat[DiracChain[6 | 7, ___]],
    Infinity
  ];

  hasChiral = Length[chiralHits] > 0 || Length[couplingAxialHits] > 0;

  If[hasChiral,
    Print["gamma5_static_check: chirality/gamma5 found (" <>
      ToString[Length[chiralHits]] <> " direct, " <>
      ToString[Length[couplingAxialHits]] <> " via coupling)"];
    Exit[1],
    (* else *)
    Print["gamma5_static_check: no gamma5 found"];
    Exit[0]
  ]
]
