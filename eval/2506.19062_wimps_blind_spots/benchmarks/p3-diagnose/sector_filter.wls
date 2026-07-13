#!/usr/bin/env wolframscript
(* D1: split amp_reduced.m into three sector sub-amplitudes by zeroing PV heads.
   Heads present are only B0i/C0i/D0i (A0i=0). Partition:
     triangle    = keep C0i + B0i (all T-channel); zero D0i
     directBox   = keep D0i[_,S,_]; zero C0i, B0i, D0i[_,U,_]
     crossedBox  = keep D0i[_,U,_]; zero C0i, B0i, D0i[_,S,_]
   Applied to the ENTIRE amp association (amp body AND subexpr table).
   Usage: sector_filter.wls <amp_reduced.m> <sector> <out.m>
          sector in {triangle,directBox,crossedBox} *)
{ampPath, sector, outPath} = $ScriptCommandLine[[2;;4]];
amp = Get[ampPath];
rules = Switch[sector,
  "triangle",   {D0i[___] -> 0},
  "directBox",  {C0i[___] -> 0, B0i[___] -> 0, D0i[h_, U, r___] -> 0},
  "crossedBox", {C0i[___] -> 0, B0i[___] -> 0, D0i[h_, S, r___] -> 0},
  _, (Print["bad sector"]; Exit[2])];
filtered = amp /. rules;
(* sanity: count remaining heads *)
cnt[e_, h_] := Length[Cases[e, h[___], Infinity]];
Print[sector, ": remaining C0i=", cnt[filtered,C0i], " B0i=", cnt[filtered,B0i],
      " D0i=", cnt[filtered,D0i],
      " D0iS=", Length[Cases[filtered, D0i[_,S,___], Infinity]],
      " D0iU=", Length[Cases[filtered, D0i[_,U,___], Infinity]]];
Put[filtered, outPath];
Print["wrote ", outPath];
