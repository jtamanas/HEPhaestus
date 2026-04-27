#!/usr/bin/env wolframscript
(* probe_formcalc.wls — probe FormCalc version given a directory.
   Usage: wolframscript -script probe_formcalc.wls <dir>
   Prints $FormCalcVersion on stdout (bare string, no quotes) and exits 0.
   Exits non-zero and prints nothing on failure.
*)
Module[{dir, result},
  dir = If[Length[$ScriptCommandLine] >= 2,
    $ScriptCommandLine[[2]],
    ""
  ];
  If[dir =!= "",
    AppendTo[$Path, dir]
  ];
  result = Quiet[
    Check[
      Needs["FormCalc`"];
      $FormCalcVersion,
      $Failed
    ],
    {General::shdw, General::contextshadow}
  ];
  If[result === $Failed,
    Exit[1]
  ];
  Print[result];
  Exit[0]
]
