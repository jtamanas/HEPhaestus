#!/usr/bin/env wolframscript
(* wp1_gen.wls — W-P1 decisive discriminator (AMENDMENT8R4 R3): FeynArts
   tree-level chi q -> chi q via t-channel VECTOR exchange on ToyDiracV.
   A-priori (frozen, see ToyDiracV.mod header):
     M_phys = +gchi gq/(t - MV^2) (chibar gamma^mu chi)(qbar gamma_mu q).
   Writes wp1_amps.m in the wrapped {"amp"->FeynAmpList} shape
   run_calcfeynamp.wls consumes.  Also record whether the raw FeynAmp
   carries the same explicit leading pairing minus as D3's scalar toy
   (prediction: YES — the CreateFeynAmp pairing signature is
   operator-blind per the item-1 mechanism read). *)
Needs["FeynArts`"];
$WP1Dir = "/Users/yianni/.claude/jobs/c703354a/tmp/item4-r2/wp1";
AppendTo[FeynArts`$ModelPath, $WP1Dir];
SetOptions[InsertFields, Model -> "ToyDiracV"];

tops = CreateTopologies[0, 2 -> 2];
ins = InsertFields[tops,
  {F[1, {1}], F[2, {1}]} -> {F[1, {1}], F[2, {1}]},
  InsertionLevel -> {Classes}];
amps = CreateFeynAmp[ins];
nAmp = Length[Cases[amps, x_ /; Head[x] === FeynArts`FeynAmp, {0, Infinity}]];
Print["wp1_gen: FeynAmp count = ", nAmp];
Put[{"schema_version" -> 1, "model" -> "ToyDiracV", "amp" -> amps},
  FileNameJoin[{$WP1Dir, "wp1_amps.m"}]];
Print["wp1_gen: wrote wp1_amps.m"];
Exit[0]
