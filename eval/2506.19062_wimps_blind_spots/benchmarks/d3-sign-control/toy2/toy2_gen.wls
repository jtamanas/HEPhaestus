#!/usr/bin/env wolframscript
(* toy2_gen.wls — AMENDMENT9-precondition item 2: single-fermion-chain
   known-sign confirmation toy. chi phi -> chi phi via t-channel h on
   ToyDiracH2. PRE-REGISTERED (see ToyDiracH2.mod header): faithful
   convention => raw FeynAmp has NO leading minus and the reduced Amp is
   -gchi mu (ubar u) Den[T,Mhh^2]. Writes toy2_amps.m in the wrapped
   {"amp"->FeynAmpList} shape run_calcfeynamp.wls consumes. *)
Needs["FeynArts`"];
$T2Dir = "/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/d3-toy2";
AppendTo[FeynArts`$ModelPath, $T2Dir];
SetOptions[InsertFields, Model -> "ToyDiracH2"];

tops = CreateTopologies[0, 2 -> 2];
ins = InsertFields[tops,
  {F[1, {1}], S[2]} -> {F[1, {1}], S[2]},
  InsertionLevel -> {Classes}];
amps = CreateFeynAmp[ins];
nAmp = Length[Cases[amps, x_ /; Head[x] === FeynArts`FeynAmp, {0, Infinity}]];
Print["toy2_gen: FeynAmp count = ", nAmp];
Put[{"schema_version" -> 1, "model" -> "ToyDiracH2", "amp" -> amps},
  FileNameJoin[{$T2Dir, "toy2_amps.m"}]];
Print["toy2_gen: wrote toy2_amps.m"];
Exit[0]
