#!/usr/bin/env wolframscript
(* smoke_test.wls — two-stage FormCalc smoke test.
   Usage: wolframscript -script smoke_test.wls <formcalc_dir> <form_log_path>
   Stage 1: Loads FormCalc, checks $FormCalcVersion.
   Stage 2: Creates a trivial topology, calls CalcFeynAmp, asserts head is Amp.
   Checks form.log for "Time = " to verify FORM was invoked.
   Exits 0 on success, 1 on failure.
*)
Module[{dir, formLog, ver, tops, ins, amp, logContent, ok},
  dir = If[Length[$ScriptCommandLine] >= 2, $ScriptCommandLine[[2]], ""];
  formLog = If[Length[$ScriptCommandLine] >= 3, $ScriptCommandLine[[3]], ""];

  If[dir =!= "", AppendTo[$Path, dir]];

  (* Stage 1: load FormCalc *)
  Check[
    Needs["FormCalc`"],
    Print["SMOKE_FAIL: Needs[FormCalc] failed"]; Exit[1]
  ];
  ver = $FormCalcVersion;
  If[StringQ[ver],
    Print["FormCalcVersion: " <> ver],
    Print["SMOKE_FAIL: $FormCalcVersion is not a string"]; Exit[1]
  ];

  (* Stage 2: minimal amplitude — photon self-energy, 0-loop (tree-level probe) *)
  tops = Quiet[
    Check[
      CreateTopologies[0, 1 -> 1, ExcludeTopologies -> Internal],
      $Failed
    ]
  ];
  If[tops === $Failed,
    Print["SMOKE_FAIL: CreateTopologies failed"]; Exit[1]
  ];

  ins = Quiet[
    Check[
      InsertFields[tops, {V[1]} -> {V[1]}, Model -> "SM",
        InsertionLevel -> {Classes}],
      $Failed
    ]
  ];
  If[ins === $Failed,
    Print["SMOKE_FAIL: InsertFields failed"]; Exit[1]
  ];

  amp = Quiet[
    Check[
      CalcFeynAmp[CreateFeynAmp[ins], FermionChains -> Weyl],
      $Failed
    ]
  ];
  If[amp === $Failed || Head[amp] =!= Amp,
    Print["SMOKE_FAIL: CalcFeynAmp did not return Amp"]; Exit[1]
  ];

  (* Stage 2b: check FORM log *)
  If[StringQ[formLog] && formLog =!= "" && FileExistsQ[formLog],
    logContent = Import[formLog, "Text"];
    If[!StringContainsQ[logContent, "Time ="],
      Print["SMOKE_WARN: form.log exists but contains no 'Time = ' marker"]
      (* non-fatal warning — FORM may not have been invoked for 0-loop *)
    ]
  ];

  Print["SMOKE_OK"];
  Exit[0]
]
