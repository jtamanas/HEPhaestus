#!/usr/bin/env wolframscript
(* toy_gen.wls — D3: FeynArts tree-level chi q -> chi q via h exchange on the
   ToyDiracH model; writes toy_amps.m in the wrapped {"amp"->FeynAmpList}
   shape run_calcfeynamp.wls consumes. *)
Needs["FeynArts`"];
AppendTo[FeynArts`$ModelPath, "/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/d3"];
SetOptions[InsertFields, Model -> "ToyDiracH"];
$D3Dir = "/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/d3";

tops = CreateTopologies[0, 2 -> 2];
ins = InsertFields[tops,
  {F[1, {1}], F[2, {1}]} -> {F[1, {1}], F[2, {1}]},
  InsertionLevel -> {Classes}];
amps = CreateFeynAmp[ins];
nAmp = Length[Cases[amps, x_ /; Head[x] === FeynArts`FeynAmp, {0, Infinity}]];
Print["toy_gen: FeynAmp count = ", nAmp];
Put[{"schema_version" -> 1, "model" -> "ToyDiracH", "amp" -> amps},
  FileNameJoin[{$D3Dir, "toy_amps.m"}]];
Print["toy_gen: wrote toy_amps.m"];
Exit[0]
