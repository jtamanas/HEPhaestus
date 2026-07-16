#!/usr/bin/env wolframscript
(* B6 boson-channel partition of a BOX sub-amplitude (directBox / crossedBox).

   METHOD (mirrors the proven sector_filter.wls D0i-zeroing, preserving the
   Amp[spec][...] / abbr / subexpr structure the driver consumes):
   the box amplitude is LINEAR in its D0i loop functions. Each D0i's internal
   BOSON is read from the boson masses among its argument list
   {MassVWp,MassVZ,Masshh,MassAh,MassHp}. Every D0i's boson-set is UNIQUELY one
   of: pure {MassVWp}, pure {MassVZ}, or a Higgs-involving set (contains h/A/H+/-);
   there is NO W-Z mixed D0i (verified by census). So zeroing the complementary
   D0i yields an exact linear partition of the D0i part of the amplitude.

   ROUTING (pre-registered, chirality-motivated; see b6_analysis.md):
     Wpure   : keep D0i with boson-set == {MassVWp}  (pure W-W gauge box; P-i:
               quark-side pure-LH => scalar must ~vanish)
     Zpure   : keep D0i with boson-set == {MassVZ}   (pure Z-Z gauge box; P-ii:
               Hisano g_S counterpart, quark Z-coupling has a_V AND a_A)
     Yukawa  : keep D0i whose boson-set intersects {h,A,H+/-} (P-iv: W-H+/-,
               Z-h, Z-A, H+/-H+/-, h-h, A-A, h-A; a Higgs leg supplies the
               chirality flip; NO Hisano box analogue)
     WwithHp : keep D0i with boson-set == {MassVWp,MassHp} (subset of Yukawa;
               lets P-i be re-scored under the alternative "any-W" convention)
     remainder: keep ONLY terms with NO D0i (finite/counterterm pieces; zero all
               D0i). Expected negligible. NOTE the Wpure/Zpure/Yukawa/WwithHp
               filters each also carry this remainder (they only zero D0i, not
               the no-D0i terms), so the caller must SUBTRACT the remainder's
               C_scalar to get the pure channel value; closure is then
               (Wpure-rem)+(Zpure-rem)+(Yukawa-rem)+rem == box-total.

   Usage: b6_boson_filter.wls <amp_box.m> <outPrefix>
     writes <outPrefix>_{Wpure,Zpure,Yukawa,remainder,WwithHp}.m *)
{ampPath, outPrefix} = $ScriptCommandLine[[2 ;; 3]];
amp = Get[ampPath];
bosons = {MassVWp, MassVZ, Masshh, MassAh, MassHp};
higgs = {Masshh, MassAh, MassHp};
bsetOf[args_] := Select[bosons, ! FreeQ[args, #] &];

(* census before filtering *)
d0s = Cases[amp, D0i[a__] :> {a}, Infinity];
Print["total D0i = ", Length[d0s]];
Print["boson-set tally = ", Tally[bsetOf /@ d0s] // InputForm];

(* keep-predicates on the boson-set of a single D0i *)
keepWpure[bs_]   := bs === {MassVWp};
keepZpure[bs_]   := bs === {MassVZ};
keepYukawa[bs_]  := IntersectingQ[bs, higgs];
keepWwithHp[bs_] := Sort[bs] === Sort[{MassVWp, MassHp}];

filt[keep_] := amp /. D0i[a__] :> If[keep[bsetOf[{a}]], D0i[a], 0];
remA         := amp /. D0i[__] -> 0;

chans = {
  {"Wpure", filt[keepWpure]},
  {"Zpure", filt[keepZpure]},
  {"Yukawa", filt[keepYukawa]},
  {"WwithHp", filt[keepWwithHp]},
  {"remainder", remA}};

Do[
  Module[{tag = c[[1]], a = c[[2]], nD0i},
   nD0i = Length[Cases[a, D0i[__], Infinity]];
   Put[a, outPrefix <> "_" <> tag <> ".m"];
   Print["wrote ", tag, "  (D0i kept = ", nD0i, ")"]],
  {c, chans}];

(* partition sanity: Wpure + Zpure + Yukawa D0i counts must sum to total *)
nW = Length[Cases[filt[keepWpure], D0i[__], Infinity]];
nZ = Length[Cases[filt[keepZpure], D0i[__], Infinity]];
nY = Length[Cases[filt[keepYukawa], D0i[__], Infinity]];
Print["D0i partition check: Wpure(", nW, ") + Zpure(", nZ, ") + Yukawa(", nY,
  ") = ", nW + nZ + nY, "  vs total ", Length[d0s],
  "  -> ", nW + nZ + nY === Length[d0s]];
