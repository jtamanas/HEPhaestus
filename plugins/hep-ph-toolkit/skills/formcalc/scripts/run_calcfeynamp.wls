#!/usr/bin/env wolframscript
(* run_calcfeynamp.wls — FormCalc amplitude reduction driver.
   Usage (called from run_formcalc.py):
     wolframscript -script run_calcfeynamp.wls \
       <feynamp_path> <kinematics_path> <output_dir> \
       <fc_path> <form_binary> <fermion_chains> <dimension> <run_dir>
   Writes:
     <output_dir>/amp_reduced.m
     <run_dir>/summary.json
*)
Module[{
    feynampPath, kinematicsPath, outputDir, fcPath, formBinary,
    fermionChainsStr, dimensionStr, runDir,
    fermionChainsOpt, dimensionOpt,
    amps, reduced, summary, nDiags,
    t0, t1, wallClock
  },

  (* Parse arguments *)
  If[Length[$ScriptCommandLine] < 9,
    Print["run_calcfeynamp.wls: insufficient arguments"];
    Exit[1]
  ];

  feynampPath    = $ScriptCommandLine[[2]];
  kinematicsPath = $ScriptCommandLine[[3]];
  outputDir      = $ScriptCommandLine[[4]];
  fcPath         = $ScriptCommandLine[[5]];
  formBinary     = $ScriptCommandLine[[6]];
  fermionChainsStr = $ScriptCommandLine[[7]];
  dimensionStr   = $ScriptCommandLine[[8]];
  runDir         = $ScriptCommandLine[[9]];

  (* Load FormCalc *)
  If[fcPath =!= "",
    AppendTo[$Path, fcPath]
  ];
  Check[
    Needs["FormCalc`"],
    Print["run_calcfeynamp: Needs[FormCalc] failed"]; Exit[1]
  ];

  (* Set FORM binary *)
  If[formBinary =!= "",
    $FormCmd = formBinary
  ];

  (* Parse options *)
  fermionChainsOpt = If[fermionChainsStr === "weyl", Weyl, Dirac];
  dimensionOpt = If[dimensionStr === "4", 4, D];

  (* Read amplitude list *)
  Check[
    amps = Get[feynampPath],
    Print["run_calcfeynamp: Get[FeynAmpList.m] failed"]; Exit[1]
  ];
  If[amps === $Failed || amps === {},
    Print["run_calcfeynamp: FeynAmpList is empty or failed to load"]; Exit[1]
  ];

  (* Load kinematics *)
  If[FileExistsQ[kinematicsPath],
    Quiet[Check[Get[kinematicsPath], Null]]
  ];

  (* Count diagrams *)
  nDiags = If[Head[amps] === FeynAmpList,
    Length[amps],
    Length[Flatten[{amps}, 1]]
  ];

  (* Reduce *)
  t0 = AbsoluteTime[];
  Check[
    reduced = CalcFeynAmp[amps,
      FermionChains -> fermionChainsOpt,
      Dimension -> dimensionOpt
    ],
    Print["run_calcfeynamp: CalcFeynAmp failed"]; Exit[1]
  ];
  t1 = AbsoluteTime[];
  wallClock = t1 - t0;

  (* Abbreviate *)
  Quiet[Check[Abbreviate[], Null]];

  (* Write output *)
  CreateDirectory[outputDir];
  Check[
    Put[reduced, FileNameJoin[{outputDir, "amp_reduced.m"}]],
    Print["run_calcfeynamp: Put[amp_reduced.m] failed"]; Exit[1]
  ];

  (* Write summary.json *)
  CreateDirectory[runDir];
  summary = "{" <>
    "\"n_diagrams\":" <> ToString[nDiags] <> "," <>
    "\"wall_clock_s\":" <> ToString[N[wallClock, 4]] <> "," <>
    "\"formcalc_version\":\"" <> ToString[$FormCalcVersion] <> "\"," <>
    "\"cached\":false" <>
  "}";
  Export[FileNameJoin[{runDir, "summary.json"}], summary, "Text"];

  Print["run_calcfeynamp: done (", nDiags, " diagrams, ", N[wallClock, 4], " s)"];
  Exit[0]
]
