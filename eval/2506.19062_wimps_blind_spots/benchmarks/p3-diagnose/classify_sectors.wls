#!/usr/bin/env wolframscript
(* D1 prep: classify each top-level term of amp_reduced.m into
   {triangle (T-channel C0i), direct box (D0i S), crossed box (D0i U)}.
   Pure symbolic — no LoopTools.  Reports partition + any mixed term. *)
amp = Get[$ScriptCommandLine[[2]]];
ampBody = If[MatchQ[amp,_List] && MemberQ[amp[[All,1]],"amp"], "amp"/.amp, amp];
terms = List @@ (ampBody /. Amp[_][x_] :> x /. Amp[_] -> Identity);
(* ampBody itself is Amp[ext][expr]; strip to the expr Plus *)
If[Head[ampBody]===Amp || (Head[ampBody]=!=Plus),
  ampBody2 = ampBody /. Amp[__][e_] :> e; , ampBody2 = ampBody];
If[Head[ampBody]===Amp[__], Null];
body = ampBody /. (h:Amp[__])[e_] :> e;
If[Head[body]=!=Plus, body = ampBody[[1]] ]; (* Amp[ext][Plus[...]] -> take arg *)
termsL = List @@ body;
Print["n top-level terms = ", Length[termsL]];
chan[t_, head_] := Union[Cases[t, head[_, c_, ___] :> c, Infinity]];
tab = Table[
  <|"i"->i,
    "C0i_ch"->chan[termsL[[i]], C0i],
    "D0i_ch"->chan[termsL[[i]], D0i],
    "B0i_ch"->chan[termsL[[i]], B0i],
    "hasC0i"->!FreeQ[termsL[[i]],C0i],
    "hasD0iS"->!FreeQ[termsL[[i]],D0i[_,S,___]],
    "hasD0iU"->!FreeQ[termsL[[i]],D0i[_,U,___]]|>,
  {i,Length[termsL]}];
sector[r_] := Which[
  r["hasD0iS"] && r["hasD0iU"], "MIXED-BOX-SU",
  r["hasD0iS"], "directBox",
  r["hasD0iU"], "crossedBox",
  r["hasC0i"], "triangle",
  True, "NO-LOOP-HEAD"];
secs = sector /@ tab;
Print["sector counts: ", Tally[secs]];
Print["terms with BOTH C0i and D0i: ",
  Count[tab, r_ /; r["hasC0i"] && (r["hasD0iS"]||r["hasD0iU"])]];
Print["distinct C0i channels overall: ", Union@@(#["C0i_ch"]&/@tab)];
Print["distinct D0i channels overall: ", Union@@(#["D0i_ch"]&/@tab)];
Print["distinct B0i channels overall: ", Union@@(#["B0i_ch"]&/@tab)];
(* B0i co-occurrence: which sectors carry B0i? *)
Print["B0i present in sectors: ",
  Tally[Pick[secs, (!FreeQ[#,B0i]&)/@termsL]]];
