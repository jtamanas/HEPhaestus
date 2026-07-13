#!/usr/bin/env wolframscript
(* run_dd_guard_check.wls — runtime driver for the SD-DD-EXPANSION-INCOMPLETE
   guard (PR #35 review F5 / amendment stage-0c): exercises ddAssertNoSurvivors —
   the SAME function run_eval_sd.wls calls — with an injected leftover tensor
   head, so the Exit[3] path is actually DRIVEN, not source-grepped.

   Needs only a Wolfram kernel (no LoopTools/FormCalc): the guard is pure
   structure, and the injected D0i head carries SYMBOLIC arguments — exactly the
   pre-mkNum stage the symbolic-side guard owns (numeric arguments would
   auto-evaluate through an Install[]ed MathLink and be invisible, which is the
   F5 blindness this split-stage design exists to close).

   Usage:
     wolframscript -script run_dd_guard_check.wls survivor   -> must Exit[3]
                                                              with the marker
     wolframscript -script run_dd_guard_check.wls clean      -> must Exit[0]
     wolframscript -script run_dd_guard_check.wls boxhead    -> must Exit[3]
                                        (inert symbolic ddBoxHead leftover)
     wolframscript -script run_dd_guard_check.wls symbolic-clean -> must Exit[0]
                                        (rewritten ddBoxHead with symbolic args
                                         is the EXPECTED pre-eval state; the
                                         symbolic-stage guard must NOT fire on
                                         it — regression for the live canonical
                                         false-positive caught in rework)
     wolframscript -script run_dd_guard_check.wls doubled    -> must Exit[3]
                                        (SD-DD-DOUBLED-OFFSET-UNSUPPORTED)
*)

Off[General::shdw]; Off[General::stop];

If[Length[$ScriptCommandLine] < 2,
  WriteString["stderr", "run_dd_guard_check: usage <survivor|clean|symbolic-clean|boxhead|doubled>\n"];
  Exit[1]];
$mode = $ScriptCommandLine[[2]];

$scriptDir = DirectoryName[
  If[$InputFileName =!= "" && $InputFileName =!= Null, $InputFileName, $ScriptCommandLine[[1]]]];
Get[FileNameJoin[{$scriptDir, "sd_dd_expansion.wl"}]];

Which[
  $mode === "survivor",
  (* a raw tensor D0i that escaped the rewrite, with SYMBOLIC args (pre-mkNum) *)
  Module[{expr},
    expr = 7 F1 F2 + g2^2 F5 F8 D0i[dd11, S, mq2, T, mchi2, mchi2, mq2, M1, M2, M3, M4];
    ddAssertNoSurvivors[expr, "symbolic-pre-eval-terms"];  (* must Exit[3] *)
    WriteString["stderr", "run_dd_guard_check: GUARD DID NOT FIRE (survivor mode)\n"];
    Exit[9]],

  $mode === "boxhead",
  (* an inert ddBoxHead whose arguments never went numeric (evaluated stage) *)
  Module[{expr},
    expr = 3 F1 F4 + F2 F3 ddBoxHead[dd23, S, mq2, T, mchi2, mchi2, mq2, M1, M2, M3, M4];
    ddAssertNoSurvivors[expr, "evaluated"];                (* must Exit[3] *)
    WriteString["stderr", "run_dd_guard_check: GUARD DID NOT FIRE (boxhead mode)\n"];
    Exit[9]],

  $mode === "symbolic-clean",
  (* the post-rewrite symbolic state: box tensors already intercepted into inert
     ddBoxHead heads (arguments still symbolic — they numericize only under
     mkNum).  The SYMBOLIC-stage guard must pass this: only raw D0i tensors are
     survivors there.  (The same expression at the "evaluated" stage IS a
     survivor — mode "boxhead" above.) *)
  Module[{expr},
    expr = 3 F1 F4 + F2 F3 ddBoxHead[dd23, S, mq2, T, mchi2, mchi2, mq2, M1, M2, M3, M4] +
           7 F1 F2 D0i[dd0, S, mq2, T, mchi2, mchi2, mq2, M1, M2, M3, M4];
    ddAssertNoSurvivors[expr, "symbolic-pre-eval-terms"];
    Print["run_dd_guard_check: rewritten symbolic state passed the symbolic-stage guard"];
    Exit[0]],

  $mode === "clean",
  (* scalar-box passthrough + triangles: NO survivors -> guard must NOT fire *)
  Module[{expr},
    expr = 7 F1 F2 D0i[dd0, S, mq2, T, mchi2, mchi2, mq2, M1, M2, M3, M4] +
           F2 F3 C0i[cc0, T, mchi2, mchi2, M1, M2, M3] + B0i[bb0, T, M1, M2];
    ddAssertNoSurvivors[expr, "symbolic-pre-eval-terms"];
    ddAssertNoSurvivors[expr, "evaluated"];
    Print["run_dd_guard_check: clean expression passed both stages"];
    Exit[0]],

  $mode === "doubled",
  (* a box signature whose offsets ALL coincide within tolerance for a subset:
     make every pinched pair coincident by setting all invariants equal so the
     rank-1 offsets are b1=b2=b3, and b0=0... b0 stays distinct, so pinch to the
     subset {2,3,4} at rank>=1 to hit the doubled-offset case directly. *)
  Module[{dargs},
    (* invariants chosen so the Gram is the all-ones matrix -> b1=b2=b3=1 exactly
       (p2s=p3s=s23=0 makes every off-diagonal k_i.k_j = 1); masses distinct *)
    dargs = {1., 0., 0., 1., 1., 0., 4., 9., 16., 25.};
    ddIntU[dargs, {2, 3, 4}, 1];                           (* must Exit[3] *)
    WriteString["stderr", "run_dd_guard_check: HARD-ERROR DID NOT FIRE (doubled mode)\n"];
    Exit[9]],

  True,
  WriteString["stderr", "run_dd_guard_check: unknown mode " <> $mode <> "\n"];
  Exit[1]]
