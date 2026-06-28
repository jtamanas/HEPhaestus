Needs["FeynArts`"];
(* Ensure FeynArts is found under the active kernel's user-base
   (the feynarts_wolfram_kernel override may run a different engine). *)
$Path = DeleteDuplicates[Prepend[$Path, $UserBaseDirectory <> "/Applications"]];
(* For SARAH/file models the .mod lives outside FeynArts' Models/ dir;
   prepend its directory to $ModelPath so InsertFields can resolve it. *)
faModelDir = "{model_dir}";
If[faModelDir =!= "", $ModelPath = DeleteDuplicates[Prepend[$ModelPath, faModelDir]]];
SetDirectory["{run_dir}"];
t   = CreateTopologies[{loop_order}, {n_in} -> {n_out}, ExcludeTopologies -> {{{excludes_m}}}];
ins = InsertFields[t, {process_tuple}, Model -> "{model_name}", GenericModel -> "Lorentz"];
nDiag = Length[ins];
If[nDiag == 0,
  Print["FEYNARTS_EMPTY_RESULT"]; Exit[0]];
If[nDiag > {diagram_cap},
  Print["FEYNARTS_TOO_MANY_DIAGRAMS ", nDiag]; Exit[2]];
Paint[ins, ColumnsXRows -> Automatic, DisplayFunction -> (Export["diagrams.pdf", #] &)];
amp = CreateFeynAmp[ins];
Put[{{"schema_version" -> 1, "feynarts_version" -> "{feynarts_version}",
     "model_hash" -> "{model_hash}", "amp" -> amp}}, "FeynAmpList.m"];
Print["FEYNARTS_OK ", nDiag];
Exit[0];
