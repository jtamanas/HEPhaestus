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

  (* Load FormCalc.
     NB: this script references the symbol FeynAmpList below (nDiags test), so
     the kernel creates Global`FeynAmpList at parse time. When FormCalc pulls in
     FeynArts`, which also exports FeynAmpList, the kernel emits the *benign*
     General::shdw ("appears in multiple contexts") warning. A bare
     Check[Needs[...], fail] fires its error branch on ANY message and so used
     to report a false "Needs[FormCalc] failed" for a package that loaded fine.
     Quiet the shadow warning so Check only trips on genuine load errors, then
     confirm the package is actually present via $Packages. *)
  If[fcPath =!= "",
    AppendTo[$Path, fcPath]
  ];
  Check[
    Quiet[Needs["FormCalc`"], {General::shdw}],
    Print["run_calcfeynamp: Needs[FormCalc] failed"]; Exit[1]
  ];
  If[!MemberQ[$Packages, "FormCalc`"],
    Print["run_calcfeynamp: FormCalc package did not load"]; Exit[1]
  ];

  (* Set FORM binary *)
  If[formBinary =!= "",
    $FormCmd = formBinary
  ];

  (* Parse options *)
  fermionChainsOpt = If[fermionChainsStr === "weyl", Weyl, Dirac];
  dimensionOpt = If[dimensionStr === "4", 4, D];

  (* Read amplitude list.
     /feynarts generate writes a self-describing metadata wrapper:
       {"schema_version"->1, ..., "amp" -> FeynAmpList[proc][FeynAmp...]}
     (real generate output; see feynarts postprocess). Older/fixture inputs are
     a bare FeynAmpList[proc][FeynAmp...]. Get either, then extract the actual
     FeynAmpList object — feeding the whole metadata List to CalcFeynAmp trips
     DeclareProcess::syntax. Match the "amp" rule (string or symbol key), else
     fall back to any FeynAmpList[__][__] subexpression. *)
  Check[
    rawAmps = Get[feynampPath],
    Print["run_calcfeynamp: Get[FeynAmpList.m] failed"]; Exit[1]
  ];
  If[rawAmps === $Failed,
    Print["run_calcfeynamp: FeynAmpList failed to load"]; Exit[1]
  ];
  (* A FeynAmpList object appears in two shapes:
       curried  FeynAmpList[Process->..,..][FeynAmp..]  (real FeynArts output;
                Head is FeynAmpList[opts], Head[Head] is the FeynAmpList symbol)
       flat     FeynAmpList[GraphID[..], FeynAmp..]      (Head is the symbol). *)
  isFeynAmpList[x_] :=
    Head[x] === FeynArts`FeynAmpList || Head[Head[x]] === FeynArts`FeynAmpList;
  If[isFeynAmpList[rawAmps],
    amps = rawAmps,
    (* wrapped metadata: pull the "amp" value, or the first FeynAmpList found *)
    Module[{ampRule, faObj},
      ampRule = Cases[rawAmps,
        (Rule | RuleDelayed)[k_, v_] /;
          (k === "amp" || (Head[k] === Symbol && SymbolName[k] === "amp")) :> v,
        {0, Infinity}];
      faObj = If[ampRule =!= {},
        First[ampRule],
        First[Cases[rawAmps, x_ /; isFeynAmpList[x] :> x, {0, Infinity}], rawAmps]
      ];
      amps = faObj
    ]
  ];
  If[amps === $Failed || amps === {} || amps === Null,
    Print["run_calcfeynamp: FeynAmpList is empty or failed to load"]; Exit[1]
  ];
  If[!isFeynAmpList[amps],
    Print["run_calcfeynamp: could not extract a FeynAmpList object from input ",
      "(head: ", Head[amps], ")"]; Exit[1]
  ];

  (* Load kinematics *)
  If[FileExistsQ[kinematicsPath],
    Quiet[Check[Get[kinematicsPath], Null]]
  ];

  (* Count diagrams by counting FeynAmp entries — robust across both the curried
     and flat FeynAmpList shapes. Context-qualify FeynArts`FeynAmp so the bare
     token here does not create Global`FeynAmp at parse time. *)
  nDiags = Length[Cases[amps, x_ /; Head[x] === FeynArts`FeynAmp, {0, Infinity}]];

  (* Reduce.
     NB (γ₅): no γ₅-scheme option is forwarded to CalcFeynAmp. FormCalc 9.10
     computes with its native anticommuting γ₅ (NDR); it exposes no CalcFeynAmp
     option selecting a complete HV/BMHV/Larin scheme (only Gamma5Test, a
     consistency diagnostic, and Gamma5ToEps, an ε-tensor substitution inside
     closed fermion traces). run_formcalc.py therefore hard-errors on any
     --gamma5 other than naive (FORMCALC_G5_SCHEME_UNIMPLEMENTED) so the reduction
     here always genuinely is NDR — matching the sidecar's naive stamp.
     See STEP3-DESIGN.md Decision 1. *)
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
