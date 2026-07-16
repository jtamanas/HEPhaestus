#!/usr/bin/env wolframscript
(* B6 inspection: characterise the internal-boson content of every D0i in a box
   sub-amplitude, to design an EXHAUSTIVE + NON-OVERLAPPING boson-channel
   partition. NO kernel (LoopTools); pure symbolic structural census.

   The 4 internal box propagator masses are the LAST 4 args of D0i
   (D0i[id, p1,p2,p3,p4,p12,p23, m1^2,m2^2,m3^2,m4^2]). Boson masses among
   {MassVWp,MassVZ,Masshh,MassAh,MassHp}; fermion masses {MassFChiM,MassFu,
   MassFd,MassFChi}. This script reports, per D0i occurrence, the multiset of
   BOSON masses it carries, and tallies the boson-combinations, so we can see
   whether any single D0i mixes two DIFFERENT bosons (which would make a
   by-boson partition overlap).

   Usage: b6_inspect_bosons.wls <amp_sector.m> *)
ampPath = $ScriptCommandLine[[2]];
amp = Get[ampPath];
bosons = {MassVWp, MassVZ, Masshh, MassAh, MassHp};
(* also probe for a distinct charged-Goldstone token, if any *)
extraTokens = {MassGp, MassSp, MassUp};
(* collect every D0i in the whole association *)
d0s = Cases[amp, D0i[args__] :> {args}, Infinity];
Print["total D0i occurrences = ", Length[d0s]];
(* boson multiset per D0i: which bosons appear anywhere in its arg list *)
bosonSet[args_] := Select[bosons, ! FreeQ[args, #] &];
sets = bosonSet /@ d0s;
Print["boson-combination tally (which bosons appear in each D0i):"];
Print[Tally[sets] // InputForm];
(* how many D0i carry NO boson mass at all (would be unpartitionable) *)
Print["D0i with NO boson mass (unassigned) = ", Count[sets, {}]];
(* how many carry MORE THAN ONE distinct boson (overlap risk) *)
Print["D0i with >1 distinct boson (mixed) = ", Count[sets, s_ /; Length[s] > 1]];
(* probe extra/Goldstone tokens anywhere in amp *)
Print["extra-token presence in whole amp:"];
Do[Print["  ", t, " -> ", ! FreeQ[amp, t]], {t, Join[extraTokens, bosons]}];
(* also: do boson masses appear ONLY inside D0i, or also in coefficients/Den? *)
Do[
  Module[{inD0i, total},
   total = Count[amp, tok, Infinity];
   inD0i = Total[Count[#, tok, Infinity] & /@ d0s];
   Print["  token ", tok, ": total occ = ", total, " ; inside-D0i occ = ", inD0i,
     " ; outside-D0i = ", total - inD0i]],
  {tok, bosons}];
