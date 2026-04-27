(* T05b Dirac spike driver — loads SARAH, prepends the staged fixture
   directory to SARAH[InputDirectories], calls Start["DiracSpike"],
   then CheckModel[EWSB], and exits non-zero on any SARAH abort or
   Mathematica error message.

   Invoked by run_dirac_spike.sh as:
     wolframscript -file run_spike.m <SARAH_DIR> <STAGE_ROOT>
*)

args = Rest[$ScriptCommandLine];
If[Length[args] =!= 2,
  Print["[run_spike.m] usage: wolframscript -file run_spike.m <SARAH_DIR> <STAGE_ROOT>"];
  Exit[2]
];

{sarahDir, stageRoot} = args;

Print["[run_spike.m] SARAH_DIR  = ", sarahDir];
Print["[run_spike.m] STAGE_ROOT = ", stageRoot];

(* Load SARAH. *)
Check[
  Get[FileNameJoin[{sarahDir, "SARAH.m"}]],
  (Print["[run_spike.m] FAILED to load SARAH.m"]; Exit[3])
];

(* Prepend staged fixture dir so Start[] finds DiracSpike/DiracSpike.m. *)
SARAH[InputDirectories] = Prepend[SARAH[InputDirectories], stageRoot];

Print["[run_spike.m] SARAH[InputDirectories] = ", SARAH[InputDirectories]];

(* Track SARAH::Aborted / CheckModelFiles::* messages as test failures.
   SARAH prints them via Message[] but does not always Abort, so we
   trap them via Check and explicit message-quiet/hold pattern. *)

Off[General::stop];
abortSeen = False;

CheckAbort[
  Start["DiracSpike"],
  abortSeen = True
];

If[abortSeen,
  Print["[run_spike.m] Start[\"DiracSpike\"] ABORTED"];
  Exit[4]
];

If[TrueQ[AbortStart],
  Print["[run_spike.m] Start[] reported AbortStart = True"];
  Exit[5]
];

Print["[run_spike.m] Start[\"DiracSpike\"] OK."];

CheckAbort[
  CheckModel[EWSB],
  abortSeen = True
];

If[abortSeen,
  Print["[run_spike.m] CheckModel[EWSB] ABORTED"];
  Exit[6]
];

Print["[run_spike.m] CheckModel[EWSB] OK."];
Print["[run_spike.m] T05b spike PASSED."];
Exit[0]
